import argparse
import os
import re
import subprocess
import time
import uuid
from pathlib import Path
from fastembed import TextEmbedding
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PayloadSchemaType, PointStruct, VectorParams

# Inherit container environment variables automatically
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION", "knowledge_hub")
CACHE_DIR = os.getenv("FASTEMBED_CACHE_PATH", "/app/model_cache")
KNOWLEDGE_BASE_DIR = Path(os.getenv("KNOWLEDGE_BASE_DIR", "/app/knowledge_base"))
KNOWLEDGE_BASE_GIT_URL = os.getenv("KNOWLEDGE_BASE_GIT_URL", "").strip()
GITHUB_PAT = os.getenv("GITHUB_PAT", "").strip()
MODEL_NAME = "BAAI/bge-small-en-v1.5"
VECTOR_DIM = 384
MAX_CHARS_PER_CHUNK = 1500

SKIP_DIRS = {".git", "node_modules", "venv", ".venv", "__pycache__", ".obsidian"}


def ensure_kb_directories(kb_root: Path = KNOWLEDGE_BASE_DIR) -> tuple[Path, Path]:
    """Ensures /app/knowledge_base/notes and /app/knowledge_base/repos exist."""
    notes_dir = kb_root / "notes"
    repos_dir = kb_root / "repos"
    notes_dir.mkdir(parents=True, exist_ok=True)
    repos_dir.mkdir(parents=True, exist_ok=True)
    return notes_dir, repos_dir


def extract_frontmatter_category(text: str) -> str | None:
    """Extracts an optional 'category:' field from YAML frontmatter before stripping."""
    fm_match = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n", text, flags=re.DOTALL)
    if not fm_match:
        return None
    frontmatter = fm_match.group(1)
    cat_match = re.search(r"^\s*category\s*:\s*['\"]?([^'\"\r\n#]+)['\"]?", frontmatter, flags=re.MULTILINE | re.IGNORECASE)
    if cat_match:
        val = cat_match.group(1).strip()
        if val:
            return val
    return None


def chunk_markdown(text: str, fallback_title: str) -> list[dict]:
    """Splits Markdown by #, ##, ### headers and sub-chunks long sections."""
    # Strip optional YAML frontmatter
    text = re.sub(r"^---\r?\n.*?\r?\n---\r?\n", "", text, flags=re.DOTALL)

    header_pattern = re.compile(r"^(#{1,3})\s+(.+)$", re.MULTILINE)
    matches = list(header_pattern.finditer(text))

    sections = []
    if not matches:
        stripped = text.strip()
        if stripped:
            sections.append((fallback_title, stripped))
    else:
        # Capture text before the first heading if present
        if matches[0].start() > 0:
            intro = text[: matches[0].start()].strip()
            if len(intro) > 40:
                sections.append((f"{fallback_title} - Overview", intro))

        for i, match in enumerate(matches):
            heading_title = match.group(2).strip()
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            body = text[start:end].strip()
            if len(body) > 30:
                sections.append((f"{fallback_title} — {heading_title}", body))

    # Sub-chunk any section that exceeds MAX_CHARS_PER_CHUNK
    final_chunks = []
    for title, body in sections:
        if len(body) <= MAX_CHARS_PER_CHUNK:
            final_chunks.append({"title": title, "content": body})
        else:
            paragraphs = body.split("\n\n")
            buffer = ""
            part = 1
            for p in paragraphs:
                if len(buffer) + len(p) + 2 <= MAX_CHARS_PER_CHUNK:
                    buffer = f"{buffer}\n\n{p}".strip()
                else:
                    if buffer:
                        final_chunks.append({"title": f"{title} (Part {part})", "content": buffer})
                        part += 1
                    buffer = p[:MAX_CHARS_PER_CHUNK]
            if buffer:
                final_chunks.append({"title": f"{title} (Part {part})", "content": buffer})

    return final_chunks


def _inject_pat_if_needed(repo_url: str) -> str:
    """Injects GITHUB_PAT into HTTPS GitHub URLs when configured for private repos."""
    if GITHUB_PAT and repo_url.startswith("https://github.com/") and "@" not in repo_url:
        return repo_url.replace("https://github.com/", f"https://{GITHUB_PAT}@github.com/", 1)
    return repo_url


def clone_or_pull_repo(repo_url: str, target_root: Path) -> Path:
    """Clones a repository into target_root or pulls latest downstream changes (--ff-only)."""
    target_root.mkdir(parents=True, exist_ok=True)
    clean_url = repo_url.strip()
    repo_name = clean_url.rstrip("/").split("/")[-1].replace(".git", "")
    repo_path = target_root / repo_name
    auth_url = _inject_pat_if_needed(clean_url)

    if (repo_path / ".git").exists():
        print(f"🔄 Pulling latest downstream changes for {repo_name}...")
        subprocess.run(["git", "-C", str(repo_path), "pull", "--ff-only"], check=True)
    else:
        print(f"📥 Cloning {clean_url} into {repo_path}...")
        subprocess.run(["git", "clone", "--depth", "1", auth_url, str(repo_path)], check=True)
    return repo_path


def sync_downstream_git_repos(kb_root: Path = KNOWLEDGE_BASE_DIR) -> list[dict]:
    """
    Pulls downstream changes (git pull --ff-only) across all git repositories
    inside knowledge_base (root, notes/, and repos/*).
    If KNOWLEDGE_BASE_GIT_URL is set and notes/ is not yet a git repo, clones it.
    """
    notes_dir, repos_dir = ensure_kb_directories(kb_root)
    results = []

    if KNOWLEDGE_BASE_GIT_URL and not (notes_dir / ".git").exists():
        try:
            clone_or_pull_repo(KNOWLEDGE_BASE_GIT_URL, kb_root)
        except Exception as e:
            results.append({"repo": KNOWLEDGE_BASE_GIT_URL, "status": "error", "output": str(e)})

    candidate_dirs = [kb_root, notes_dir]
    if repos_dir.exists():
        candidate_dirs.extend(sorted([d for d in repos_dir.iterdir() if d.is_dir()]))

    seen_git_dirs = set()
    for d in candidate_dirs:
        git_marker = d / ".git"
        if git_marker.exists() and d.resolve() not in seen_git_dirs:
            seen_git_dirs.add(d.resolve())
            try:
                res = subprocess.run(
                    ["git", "-C", str(d), "pull", "--ff-only"],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                results.append(
                    {
                        "repo": d.name,
                        "path": str(d),
                        "status": "updated",
                        "output": (res.stdout or res.stderr).strip() or "Already up to date.",
                    }
                )
            except subprocess.CalledProcessError as e:
                results.append(
                    {
                        "repo": d.name,
                        "path": str(d),
                        "status": "error",
                        "output": (e.stderr or e.stdout or str(e)).strip(),
                    }
                )
    return results


def scan_markdown_files(root_dir: Path) -> list[Path]:
    """Recursively scans root_dir for Markdown and plain-text knowledge files."""
    if not root_dir.exists():
        return []
    md_files = []
    for path in sorted(root_dir.rglob("*")):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.is_file() and path.suffix.lower() in {".md", ".mdx", ".txt"}:
            md_files.append(path)
    return md_files


def infer_file_category(file_path: Path, kb_root: Path, raw_text: str, default_category: str, explicit_category: str | None = None) -> str:
    """
    Determines initial category for a file:
    1. Explicit category override (if provided)
    2. YAML frontmatter 'category:' field inside the Markdown file
    3. Subfolder name under knowledge_base/notes/<CategoryName>/file.md
    4. Fallback default_category
    """
    if explicit_category:
        return explicit_category
    fm_cat = extract_frontmatter_category(raw_text)
    if fm_cat:
        return fm_cat
    try:
        rel = file_path.relative_to(kb_root)
        parts = rel.parts
        # e.g. notes/<Category>/<file.md> -> use <Category>
        if len(parts) >= 3 and parts[0] == "notes":
            return parts[1]
    except ValueError:
        pass
    return default_category


def index_files_into_qdrant(
    client: QdrantClient,
    embedder: TextEmbedding,
    files: list[Path],
    kb_root: Path = KNOWLEDGE_BASE_DIR,
    default_category: str = "Documentation",
    explicit_category: str | None = None,
    force_category: bool = False,
    only_missing: bool = False,
) -> dict:
    """
    Chunks and indexes files into Qdrant using deterministic UUIDv5 point IDs.
    Preserves any existing 'category' payload in Qdrant (such as UI Category Updates)
    unless force_category=True is explicitly requested.
    """
    t0 = time.perf_counter()
    records = []

    for file_path in files:
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            print(f"Skipping {file_path}: {e}")
            continue

        try:
            rel_source = str(file_path.relative_to(kb_root)).replace("\\", "/")
        except ValueError:
            rel_source = file_path.name

        file_cat = infer_file_category(
            file_path=file_path,
            kb_root=kb_root,
            raw_text=content,
            default_category=default_category,
            explicit_category=explicit_category,
        )

        chunks = chunk_markdown(content, fallback_title=file_path.stem)
        for idx, c in enumerate(chunks):
            # Deterministic UUIDv5 prevents duplicate points on re-runs
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{rel_source}:{c['title']}:{idx}"))
            records.append(
                {
                    "id": point_id,
                    "title": c["title"],
                    "category": file_cat,
                    "source": rel_source,
                    "content": c["content"],
                }
            )

    if not records:
        return {
            "files_processed": len(files),
            "chunks_total": 0,
            "chunks_indexed": 0,
            "categories_preserved": 0,
            "elapsed_ms": (time.perf_counter() - t0) * 1000,
        }

    batch_size = 64
    chunks_indexed = 0
    categories_preserved = 0

    for i in range(0, len(records), batch_size):
        batch = records[i : i + batch_size]
        batch_ids = [r["id"] for r in batch]

        # Retrieve existing points in Qdrant to preserve manual/bulk Category Updates
        existing_map = {}
        try:
            existing_pts = client.retrieve(
                collection_name=COLLECTION_NAME,
                ids=batch_ids,
                with_payload=["category"],
                with_vectors=False,
            )
            for pt in existing_pts:
                existing_map[str(pt.id)] = (pt.payload or {}).get("category")
        except Exception:
            existing_map = {}

        if only_missing:
            batch = [r for r in batch if r["id"] not in existing_map]
            if not batch:
                continue

        for r in batch:
            existing_cat = existing_map.get(r["id"])
            if existing_cat and not force_category:
                r["category"] = existing_cat
                categories_preserved += 1

        texts = [f"{r['title']}: {r['content']}" for r in batch]
        vectors = list(embedder.embed(texts))
        now_utc = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())

        points = [
            PointStruct(
                id=r["id"],
                vector=vec.tolist(),
                payload={
                    "title": r["title"],
                    "category": r["category"],
                    "source": r["source"],
                    "content": r["content"],
                    "indexed_at": now_utc,
                },
            )
            for r, vec in zip(batch, vectors)
        ]
        client.upsert(collection_name=COLLECTION_NAME, points=points)
        chunks_indexed += len(points)
        print(f"   Indexed {min(i + batch_size, len(records))}/{len(records)} chunks...")

    return {
        "files_processed": len(files),
        "chunks_total": len(records),
        "chunks_indexed": chunks_indexed,
        "categories_preserved": categories_preserved,
        "elapsed_ms": (time.perf_counter() - t0) * 1000,
    }


def sync_knowledge_base(
    client: QdrantClient,
    embedder: TextEmbedding,
    kb_root: Path = KNOWLEDGE_BASE_DIR,
    default_category: str = "Documentation",
    pull_git: bool = False,
    force_category: bool = False,
    only_missing: bool = False,
) -> dict:
    """
    End-to-end feeder for /app/knowledge_base:
    1. Ensures /app/knowledge_base/notes and /app/knowledge_base/repos exist.
    2. Optionally pulls downstream git updates across all git repos in knowledge_base.
    3. Scans and indexes all Markdown/text files while preserving existing Qdrant categories.
    """
    ensure_kb_directories(kb_root)
    git_results = sync_downstream_git_repos(kb_root) if pull_git else []
    files = scan_markdown_files(kb_root)
    index_stats = index_files_into_qdrant(
        client=client,
        embedder=embedder,
        files=files,
        kb_root=kb_root,
        default_category=default_category,
        explicit_category=None,
        force_category=force_category,
        only_missing=only_missing,
    )
    index_stats["git_results"] = git_results
    return index_stats


def main():
    parser = argparse.ArgumentParser(description="Ingest GitHub repos and knowledge_base files into Qdrant.")
    parser.add_argument("--github", type=str, help="HTTPS URL of the GitHub repository to clone/pull and index")
    parser.add_argument("--dir", type=str, default=str(KNOWLEDGE_BASE_DIR), help="Directory of Markdown files to index")
    parser.add_argument("--category", type=str, default="Documentation", help="Default category tag in Qdrant")
    parser.add_argument(
        "--sync-all",
        action="store_true",
        help="Pull downstream git updates across knowledge_base and index all notes & repos",
    )
    parser.add_argument(
        "--force-category",
        action="store_true",
        help="Overwrite existing category payloads in Qdrant instead of preserving UI category updates",
    )
    args = parser.parse_args()

    ensure_kb_directories(KNOWLEDGE_BASE_DIR)

    client = QdrantClient(
        host=QDRANT_HOST,
        port=QDRANT_PORT,
        api_key=QDRANT_API_KEY if QDRANT_API_KEY else None,
        https=False,
    )

    collections = [c.name for c in client.get_collections().collections]
    if COLLECTION_NAME not in collections:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=VECTOR_DIM, distance=Distance.COSINE),
        )
    client.create_payload_index(
        collection_name=COLLECTION_NAME,
        field_name="category",
        field_schema=PayloadSchemaType.KEYWORD,
    )

    embedder = TextEmbedding(model_name=MODEL_NAME, cache_dir=CACHE_DIR, threads=4)

    if args.sync_all:
        print(f"🔄 Syncing downstream Git repositories & indexing {KNOWLEDGE_BASE_DIR}...")
        stats = sync_knowledge_base(
            client=client,
            embedder=embedder,
            kb_root=KNOWLEDGE_BASE_DIR,
            default_category=args.category,
            pull_git=True,
            force_category=args.force_category,
            only_missing=False,
        )
        for gr in stats.get("git_results", []):
            print(f"   [Git {gr['status'].upper()}] {gr['repo']}: {gr['output']}")
        print(
            f"✅ Sync complete! Processed {stats['files_processed']} files, "
            f"indexed {stats['chunks_indexed']} chunks "
            f"(preserved {stats['categories_preserved']} existing category tags) "
            f"in {stats['elapsed_ms'] / 1000:.2f}s."
        )
        return

    explicit_cat = args.category
    if args.github:
        target_dir = clone_or_pull_repo(args.github, KNOWLEDGE_BASE_DIR / "repos")
    else:
        target_dir = Path(args.dir)

    files = scan_markdown_files(target_dir)
    if not files:
        print(f"⚠️ No .md or .txt files found in {target_dir}")
        return

    print(f"📄 Found {len(files)} files in {target_dir}. Vectorizing on Raspberry Pi 5 CPU...")
    stats = index_files_into_qdrant(
        client=client,
        embedder=embedder,
        files=files,
        kb_root=KNOWLEDGE_BASE_DIR,
        default_category=args.category,
        explicit_category=explicit_cat if args.github else None,
        force_category=args.force_category,
        only_missing=False,
    )
    print(
        f"✅ Done! Indexed {stats['chunks_indexed']} chunks from {stats['files_processed']} files "
        f"(preserved {stats['categories_preserved']} existing category tags) "
        f"in {stats['elapsed_ms'] / 1000:.2f}s."
    )


if __name__ == "__main__":
    main()
