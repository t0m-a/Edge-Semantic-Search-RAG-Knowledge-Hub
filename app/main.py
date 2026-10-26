import os
import re
import time
import uuid
from pathlib import Path
import pandas as pd
import streamlit as st
from fastembed import TextEmbedding
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PayloadSchemaType,
    PointStruct,
    VectorParams,
)
from ingest import (
    KNOWLEDGE_BASE_DIR,
    chunk_markdown,
    clone_or_pull_repo,
    ensure_kb_directories,
    index_files_into_qdrant,
    scan_markdown_files,
    sync_knowledge_base,
)

# --- CONFIGURATION ---
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION", "knowledge_hub")
CACHE_DIR = os.getenv("FASTEMBED_CACHE_PATH", "/app/model_cache")
MODEL_NAME = "BAAI/bge-small-en-v1.5"
VECTOR_DIM = 384

# LLM RAG Configuration
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_BASE_URL = os.getenv(
    "LLM_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/"
)
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-3.8-flash")

DEFAULT_CATEGORIES = [
    c.strip()
    for c in os.getenv(
        "DEFAULT_CATEGORIES",
        "Network,Cloud,Infrastructure,Database,Security,Python,Documentation",
    ).split(",")
    if c.strip()
]

st.set_page_config(
    page_title="Edge Semantic Search & RAG Hub",
    page_icon="⚡",
    layout="wide",
)


# --- CACHED INITIALIZATION ---
@st.cache_resource(show_spinner="Loading quantized ONNX embedding model on ARM64 CPU...")
def load_embedder():
    return TextEmbedding(model_name=MODEL_NAME, cache_dir=CACHE_DIR, threads=4)


@st.cache_resource
def get_qdrant_client():
    return QdrantClient(
        host=QDRANT_HOST,
        port=QDRANT_PORT,
        api_key=QDRANT_API_KEY if QDRANT_API_KEY else None,
        https=False,
    )


@st.cache_resource
def get_llm_client():
    if not LLM_API_KEY:
        return None
    return OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)


def ensure_collection(client: QdrantClient):
    collections = [c.name for c in client.get_collections().collections]
    if COLLECTION_NAME not in collections:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=VECTOR_DIM, distance=Distance.COSINE),
        )
    # Create a keyword index on 'category' for fast filtered HNSW searches
    client.create_payload_index(
        collection_name=COLLECTION_NAME,
        field_name="category",
        field_schema=PayloadSchemaType.KEYWORD,
    )


@st.cache_resource(show_spinner="Auto-syncing /app/knowledge_base into Qdrant...")
def auto_feed_knowledge_base(_client: QdrantClient, _embedder: TextEmbedding) -> dict:
    """
    Automatically feeds Qdrant from /app/knowledge_base on container startup.
    Pulls downstream git repos and indexes any files while preserving existing Qdrant categories.
    """
    ensure_kb_directories(KNOWLEDGE_BASE_DIR)
    return sync_knowledge_base(
        client=_client,
        embedder=_embedder,
        kb_root=KNOWLEDGE_BASE_DIR,
        default_category="Documentation",
        pull_git=True,
        force_category=False,
        only_missing=False,
    )


def get_active_categories(client: QdrantClient) -> list[str]:
    """Merges default categories with all unique categories currently inside Qdrant."""
    discovered = set(DEFAULT_CATEGORIES)
    pts, _ = client.scroll(
        collection_name=COLLECTION_NAME,
        limit=1000,
        with_payload=["category"],
        with_vectors=False,
    )
    for pt in pts:
        if pt.payload and "category" in pt.payload:
            discovered.add(pt.payload["category"])
    return sorted(discovered)


def get_kb_inventory(kb_root: Path = KNOWLEDGE_BASE_DIR) -> dict:
    """Returns counts and lists of local notes and cloned git repositories in knowledge_base."""
    notes_dir, repos_dir = ensure_kb_directories(kb_root)
    note_files = scan_markdown_files(notes_dir)
    repos = []
    if repos_dir.exists():
        for d in sorted(repos_dir.iterdir()):
            if d.is_dir() and (d / ".git").exists():
                repos.append(
                    {
                        "name": d.name,
                        "path": str(d),
                        "md_count": len(scan_markdown_files(d)),
                    }
                )
    return {
        "note_files": note_files,
        "repos": repos,
        "total_md_files": len(scan_markdown_files(kb_root)),
    }


# --- INITIALIZE SERVICES IN STRICT ORDER ---
embedder = load_embedder()
qdrant = get_qdrant_client()
llm_client = get_llm_client()
ensure_collection(qdrant)
boot_sync_stats = auto_feed_knowledge_base(qdrant, embedder)
ALL_CATEGORIES = get_active_categories(qdrant)
kb_inventory = get_kb_inventory(KNOWLEDGE_BASE_DIR)

# --- SAMPLE PLAYBOOKS FOR RECRUITER DEMO ---
SAMPLE_PLAYBOOKS = [
    {
        "title": "BGP Peer Session Flapping & Route Dampening",
        "category": "Network",
        "source": "NOC-Runbook-01.md",
        "content": "When an upstream BGP neighbor session flaps repeatedly, verify physical interface CRC errors first, check MTU mismatches (ensure 1500 or 9000 jumbo frames match across interfaces), and inspect hold-timer expiration logs before clearing soft BGP routes.",
    },
    {
        "title": "Cloudflare Tunnel 502 Bad Gateway Recovery",
        "category": "Cloud",
        "source": "Edge-Ingress-04.md",
        "content": "A 502 Bad Gateway error on a Cloudflare Tunnel indicates cloudflared can reach Cloudflare's edge, but cannot reach the local origin container. Verify both containers share the same Docker bridge network and reference the container service name rather than localhost.",
    },
    {
        "title": "Linux Host Out-Of-Memory (OOM) Killer Triage",
        "category": "Infrastructure",
        "source": "SysAdmin-Playbook-12.md",
        "content": "Inspect kernel ring buffer via dmesg -T | grep -i oom to identify which process exceeded cgroup memory limits. On edge nodes like Raspberry Pi, enforce hard mem_limit caps in Docker Compose and enable on-disk vector payloads.",
    },
    {
        "title": "PostgreSQL Connection Pool Exhaustion",
        "category": "Database",
        "source": "DBA-Incident-08.md",
        "content": "If application workers time out waiting for database connections, deploy PgBouncer in transaction pooling mode, audit idle_in_transaction_session_timeout settings, and terminate stalled PIDs via pg_terminate_backend.",
    },
    {
        "title": "SSH Brute-Force & Zero Trust Hardening",
        "category": "Security",
        "source": "SecOps-Standard-03.md",
        "content": "Eliminate public port 22 exposure on edge routers. Route administrative SSH traffic exclusively through Cloudflare Zero Trust Access policies with short-lived certificates or hardware FIDO2 keys.",
    },
]


def ingest_chunks(records: list[dict], preserve_category: bool = True):
    """
    Vectorizes and upserts chunk records into Qdrant using deterministic UUIDv5 IDs.
    If preserve_category=True, existing categories in Qdrant (e.g., from Category Update UI)
    are preserved on re-ingestion.
    """
    if not records:
        return

    prepared = []
    for idx, r in enumerate(records):
        point_id = r.get("id") or str(
            uuid.uuid5(uuid.NAMESPACE_DNS, f"{r['source']}:{r['title']}:{idx}")
        )
        prepared.append({**r, "id": point_id})

    if preserve_category:
        try:
            existing_pts = qdrant.retrieve(
                collection_name=COLLECTION_NAME,
                ids=[p["id"] for p in prepared],
                with_payload=["category"],
                with_vectors=False,
            )
            existing_cats = {
                str(pt.id): (pt.payload or {}).get("category") for pt in existing_pts
            }
            for p in prepared:
                if existing_cats.get(p["id"]):
                    p["category"] = existing_cats[p["id"]]
        except Exception:
            pass

    texts = [f"{r['title']}: {r['content']}" for r in prepared]
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
        for r, vec in zip(prepared, vectors)
    ]
    qdrant.upsert(collection_name=COLLECTION_NAME, points=points)


def save_note_to_kb(filename: str, category: str, title: str, content: str) -> Path:
    """Persists a Markdown document inside /app/knowledge_base/notes/<category>/."""
    notes_dir, _ = ensure_kb_directories(KNOWLEDGE_BASE_DIR)
    safe_cat = re.sub(r"[^A-Za-z0-9._-]+", "_", category.strip()) or "Documentation"
    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", Path(filename).name)
    if not safe_name.lower().endswith((".md", ".mdx", ".txt")):
        safe_name += ".md"

    target_folder = notes_dir / safe_cat
    target_folder.mkdir(parents=True, exist_ok=True)
    target_path = target_folder / safe_name

    if not content.lstrip().startswith("---"):
        formatted = f"---\ncategory: {category}\n---\n\n# {title}\n\n{content.strip()}\n"
    else:
        formatted = content

    target_path.write_text(formatted, encoding="utf-8")
    return target_path


def build_rag_messages(user_query: str, hits: list) -> list[dict]:
    """Formats retrieved Qdrant hits into numbered context blocks for strict citation."""
    context_blocks = []
    for idx, hit in enumerate(hits, start=1):
        p = hit.payload
        block = (
            f"[{idx}] Title: {p.get('title', 'Untitled')} | "
            f"Source: {p.get('source', 'Unknown')} | "
            f"Category: {p.get('category', 'Uncategorized')} | "
            f"Similarity: {hit.score:.4f}\n"
            f"Content: {p.get('content', '')}"
        )
        context_blocks.append(block)

    formatted_context = "\n\n".join(context_blocks)

    system_prompt = (
        "You are a Senior Infrastructure & SRE Technical Assistant. "
        "Answer the user's question using ONLY the numbered context chunks provided below.\n"
        "Rules:\n"
        "1. Cite every factual statement inline using bracketed numbers like [1] or [2] that correspond to the source chunk.\n"
        "2. End your response with a brief '### References' list mapping each used [number] to its Source and Title.\n"
        "3. If the provided context does not contain enough information to answer the question, state clearly that the knowledge base does not cover that topic—never invent facts."
    )

    user_prompt = (
        f"### Retrieved Knowledge Base Context:\n{formatted_context}\n\n"
        f"### User Question:\n{user_query}"
    )

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


# --- SIDEBAR TELEMETRY ---
with st.sidebar:
    st.title("⚡ Edge Node Telemetry")
    st.caption("Hardware: Raspberry Pi 5 (ARM64)")
    info = qdrant.get_collection(COLLECTION_NAME)
    col1, col2 = st.columns(2)
    col1.metric("Vectors Stored", info.points_count)
    col2.metric("Dimensions", VECTOR_DIM)

    col3, col4 = st.columns(2)
    col3.metric("KB Files", kb_inventory["total_md_files"])
    col4.metric("Git Repos", len(kb_inventory["repos"]))

    st.markdown(f"**Embedder:** `{MODEL_NAME}` (ONNX)")
    st.markdown(f"**LLM Engine:** `{LLM_MODEL if LLM_API_KEY else 'Not Configured'}`")
    st.markdown(f"**Active Categories:** `{len(ALL_CATEGORIES)}`")
    st.divider()

    if st.button("🔄 Sync knowledge_base & Git", use_container_width=True):
        with st.spinner("Pulling downstream Git repos & indexing knowledge_base..."):
            sync_stats = sync_knowledge_base(
                client=qdrant,
                embedder=embedder,
                kb_root=KNOWLEDGE_BASE_DIR,
                default_category="Documentation",
                pull_git=True,
                force_category=False,
                only_missing=False,
            )
        st.success(
            f"Synced {sync_stats['files_processed']} files ({sync_stats['chunks_indexed']} chunks, "
            f"{sync_stats['categories_preserved']} categories preserved) in {sync_stats['elapsed_ms']:.0f} ms!"
        )
        st.rerun()

    if st.button("🚀 Load Sample NOC/SRE Playbooks", use_container_width=True):
        with st.spinner("Vectorizing & indexing playbooks on Pi 5 CPU..."):
            t0 = time.perf_counter()
            for pb in SAMPLE_PLAYBOOKS:
                save_note_to_kb(pb["source"], pb["category"], pb["title"], pb["content"])
            ingest_chunks(SAMPLE_PLAYBOOKS, preserve_category=True)
            elapsed = (time.perf_counter() - t0) * 1000
        st.success(f"Indexed {len(SAMPLE_PLAYBOOKS)} playbooks in {elapsed:.1f} ms!")
        st.rerun()

# --- MAIN UI ---
st.title("🔍 Edge Semantic Search & RAG Knowledge Hub")
st.markdown(
    "Self-hosted on a **Raspberry Pi 5** using **Qdrant (Rust)** and **FastEmbed (Quantized ONNX)** behind **Cloudflare Zero Trust**."
)

tab_search, tab_ingest, tab_analytics = st.tabs(
    ["🔎 Semantic Retrieval & RAG", "📥 Ingest & Git Sync", "📊 Vector Collection Explorer"]
)

with tab_search:
    c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
    with c1:
        query = st.text_input(
            "Ask a technical question or describe an incident symptom:",
            placeholder="e.g., How do I fix a broken gateway tunnel between containers?",
        )
    with c2:
        category_filter = st.selectbox(
            "Filter Category",
            ["All"] + ALL_CATEGORIES,
        )
    with c3:
        min_score = st.slider("Min Cosine Score", 0.30, 0.95, 0.45, 0.05)
    with c4:
        st.write("")
        enable_rag = st.toggle(
            "🤖 AI Answer", value=True, help="Synthesize an answer with LLM citations"
        )

    if query:
        t_start = time.perf_counter()
        query_vector = list(embedder.embed([query]))[0].tolist()
        t_embed = (time.perf_counter() - t_start) * 1000

        q_filter = None
        if category_filter != "All":
            q_filter = Filter(
                must=[
                    FieldCondition(
                        key="category", match=MatchValue(value=category_filter)
                    )
                ]
            )

        t_qdrant_start = time.perf_counter()
        results = qdrant.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_vector,
            query_filter=q_filter,
            limit=5,
            score_threshold=min_score,
        )
        t_search = (time.perf_counter() - t_qdrant_start) * 1000

        st.caption(
            f"⏱️ **ONNX CPU Embedding:** `{t_embed:.1f} ms` | **Qdrant Rust Lookup:** `{t_search:.1f} ms` | **Retrieved Chunks:** `{len(results)}`"
        )

        if not results:
            st.warning(
                "No semantic matches above threshold. Try lowering the Min Cosine Score or loading sample playbooks from the sidebar."
            )
        else:
            if enable_rag:
                if not llm_client:
                    st.info(
                        "💡 Set `LLM_API_KEY` in `/opt/edge-rag-hub/.env` and recreate `rag-ui` to enable live AI answer synthesis."
                    )
                else:
                    rag_messages = build_rag_messages(query, results)
                    with st.container(border=True):
                        st.subheader("🤖 Synthesized Answer (Grounded in Qdrant Vectors)")
                        try:
                            stream = llm_client.chat.completions.create(
                                model=LLM_MODEL,
                                messages=rag_messages,
                                temperature=0.1,
                                stream=True,
                            )
                            st.write_stream(stream)
                        except Exception as e:
                            st.error(f"LLM API Error: {e}")

                        with st.expander("🔬 Inspect Augmented RAG Prompt Sent to LLM"):
                            st.code(rag_messages[1]["content"], language="markdown")

            st.subheader("📚 Retrieved Source Vectors")
            for idx, hit in enumerate(results, start=1):
                p = hit.payload
                with st.container(border=True):
                    h_col1, h_col2 = st.columns([4, 1])
                    h_col1.subheader(f"[{idx}] 📄 {p.get('title', 'Untitled')}")
                    h_col2.metric("Cosine Similarity", f"{hit.score:.4f}")
                    st.markdown(
                        f"**Category:** `{p.get('category')}` | **Source:** `{p.get('source')}` | **Indexed:** `{p.get('indexed_at')}`"
                    )
                    st.write(p.get("content"))
                    with st.expander("Inspect Raw Qdrant Vector Payload"):
                        st.json({"point_id": hit.id, "score": hit.score, "payload": p})

with tab_ingest:
    st.subheader("Add Technical Documentation or Incident Notes")
    with st.form("ingest_form", clear_on_submit=True):
        doc_title = st.text_input("Document / Playbook Title")
        col_cat1, col_cat2 = st.columns(2)
        with col_cat1:
            selected_cat = st.selectbox("Select Existing Category", ALL_CATEGORIES)
        with col_cat2:
            custom_cat = st.text_input(
                "Or Create New Category (optional)",
                placeholder="e.g., DevSecOps, Automation, Homelab",
            )
        doc_source = st.text_input("Source Filename / Reference", value="Manual-Entry.md")
        doc_body = st.text_area("Content (Markdown or plain text)", height=150)
        persist_to_kb = st.checkbox(
            "Save Markdown file into /app/knowledge_base/notes/ for automatic persistence",
            value=True,
        )
        submitted = st.form_submit_button("Vectorize & Store in Qdrant")

        if submitted and doc_title and doc_body:
            final_category = custom_cat.strip() if custom_cat.strip() else selected_cat
            t0 = time.perf_counter()
            if persist_to_kb:
                saved_path = save_note_to_kb(doc_source, final_category, doc_title, doc_body)
                index_files_into_qdrant(
                    client=qdrant,
                    embedder=embedder,
                    files=[saved_path],
                    kb_root=KNOWLEDGE_BASE_DIR,
                    default_category=final_category,
                    explicit_category=final_category,
                    force_category=True,
                )
            else:
                ingest_chunks(
                    [
                        {
                            "title": doc_title,
                            "category": final_category,
                            "source": doc_source,
                            "content": doc_body,
                        }
                    ],
                    preserve_category=False,
                )
            ms = (time.perf_counter() - t0) * 1000
            st.success(f"Stored vector under '{final_category}' in {ms:.1f} ms!")
            st.rerun()

    st.divider()
    col_u1, col_u2 = st.columns(2)

    with col_u1:
        st.subheader("📂 Upload Markdown Files (.md)")
        uploaded_files = st.file_uploader(
            "Drag and drop Markdown notes (saved to knowledge_base/notes)",
            type=["md", "mdx", "txt"],
            accept_multiple_files=True,
        )
        upload_cat = st.selectbox("Tag Category", ALL_CATEGORIES, key="up_cat")
        upload_custom_cat = st.text_input(
            "Or New Category for Upload (optional)", key="up_custom_cat"
        )
        force_up_cat = st.checkbox(
            "Overwrite category if document was already customized in Qdrant",
            value=False,
            key="force_up_cat",
        )
        if st.button("Vectorize Uploaded Files", use_container_width=True) and uploaded_files:
            target_cat = (
                upload_custom_cat.strip() if upload_custom_cat.strip() else upload_cat
            )
            notes_dir, _ = ensure_kb_directories(KNOWLEDGE_BASE_DIR)
            safe_cat_dir = notes_dir / re.sub(r"[^A-Za-z0-9._-]+", "_", target_cat)
            safe_cat_dir.mkdir(parents=True, exist_ok=True)

            saved_paths = []
            for uf in uploaded_files:
                raw_text = uf.read().decode("utf-8", errors="ignore")
                dest_path = safe_cat_dir / Path(uf.name).name
                dest_path.write_text(raw_text, encoding="utf-8")
                saved_paths.append(dest_path)

            stats = index_files_into_qdrant(
                client=qdrant,
                embedder=embedder,
                files=saved_paths,
                kb_root=KNOWLEDGE_BASE_DIR,
                default_category=target_cat,
                explicit_category=target_cat,
                force_category=force_up_cat,
            )
            st.success(
                f"Saved {len(saved_paths)} file(s) to knowledge_base & indexed "
                f"{stats['chunks_indexed']} chunks under '{target_cat}'!"
            )
            st.rerun()

    with col_u2:
        st.subheader("🐙 Downstream Git Sync & Repo Ingestion")
        repo_url = st.text_input(
            "GitHub Repository HTTPS URL", placeholder="https://github.com/owner/repo"
        )
        repo_cat = st.selectbox("Repo Category", ALL_CATEGORIES, key="gh_cat")
        repo_custom_cat = st.text_input(
            "Or New Category for Repo (optional)", key="gh_custom_cat"
        )
        force_repo_cat = st.checkbox(
            "Overwrite existing Qdrant category updates on re-sync",
            value=False,
            key="force_repo_cat",
        )
        if st.button("Clone / Pull & Index Repository", use_container_width=True) and repo_url:
            target_repo_cat = (
                repo_custom_cat.strip() if repo_custom_cat.strip() else repo_cat
            )
            with st.spinner("Cloning/pulling repository into knowledge_base/repos & vectorizing..."):
                try:
                    repo_path = clone_or_pull_repo(
                        repo_url, KNOWLEDGE_BASE_DIR / "repos"
                    )
                    md_files = scan_markdown_files(repo_path)
                    stats = index_files_into_qdrant(
                        client=qdrant,
                        embedder=embedder,
                        files=md_files,
                        kb_root=KNOWLEDGE_BASE_DIR,
                        default_category=target_repo_cat,
                        explicit_category=target_repo_cat,
                        force_category=force_repo_cat,
                    )
                    st.success(
                        f"Synced '{repo_path.name}': {stats['chunks_indexed']} chunks from "
                        f"{stats['files_processed']} files ({stats['categories_preserved']} categories preserved)!"
                    )
                    st.rerun()
                except Exception as e:
                    st.error(f"Git sync failed: {e}")

    st.divider()
    st.subheader("🗄️ Automatic `knowledge_base` Folder & Downstream Git Status")
    col_kb1, col_kb2 = st.columns([2, 1])
    with col_kb1:
        st.markdown(
            f"**Host Mount:** `/opt/edge-rag-hub/knowledge_base` → **Container:** `{KNOWLEDGE_BASE_DIR}`  \n"
            f"**Local Markdown Notes (`notes/`):** `{len(kb_inventory['note_files'])}` files | "
            f"**Downstream Cloned Repos (`repos/`):** `{len(kb_inventory['repos'])}` repositories"
        )
        if kb_inventory["repos"]:
            st.dataframe(
                pd.DataFrame(kb_inventory["repos"]),
                use_container_width=True,
                hide_index=True,
            )
    with col_kb2:
        if st.button(
            "🔄 Pull All Downstream Git Repos & Re-Index KB",
            use_container_width=True,
            key="btn_full_kb_sync",
        ):
            with st.spinner("Running git pull --ff-only across all repos and indexing knowledge_base..."):
                sync_stats = sync_knowledge_base(
                    client=qdrant,
                    embedder=embedder,
                    kb_root=KNOWLEDGE_BASE_DIR,
                    default_category="Documentation",
                    pull_git=True,
                    force_category=False,
                    only_missing=False,
                )
            st.success(
                f"Indexed {sync_stats['chunks_indexed']} chunks across {sync_stats['files_processed']} files "
                f"(preserved {sync_stats['categories_preserved']} existing category updates)!"
            )
            if sync_stats.get("git_results"):
                st.json(sync_stats["git_results"])
            st.rerun()

with tab_analytics:
    pts, _ = qdrant.scroll(collection_name=COLLECTION_NAME, limit=250, with_payload=True)
    if pts:
        records = []
        for p in pts:
            payload = p.payload or {}
            records.append(
                {
                    "id": str(p.id),
                    "title": payload.get("title", "Untitled"),
                    "category": payload.get("category", "Uncategorized"),
                    "source": payload.get("source", "Unknown"),
                    "indexed_at": payload.get("indexed_at", ""),
                }
            )
        df = pd.DataFrame(records)
        st.dataframe(
            df[["id", "title", "category", "source", "indexed_at"]],
            use_container_width=True,
            hide_index=True,
        )

        st.divider()
        col_upd_doc, col_upd_cat = st.columns(2)

        with col_upd_doc:
            st.subheader("✏️ Update Individual Document Category")
            doc_options = {
                f"{r['title']} ({r['category']}) — [{r['id'][:8]}]": r for r in records
            }
            selected_doc_label = st.selectbox(
                "Select Document",
                options=list(doc_options.keys()),
                key="upd_doc_select",
            )
            selected_doc = doc_options[selected_doc_label]

            new_doc_cat = st.selectbox(
                "New Category",
                options=ALL_CATEGORIES,
                index=ALL_CATEGORIES.index(selected_doc["category"])
                if selected_doc["category"] in ALL_CATEGORIES
                else 0,
                key="upd_doc_cat",
            )
            custom_doc_cat = st.text_input(
                "Or Enter Custom Category (optional)",
                placeholder="e.g., DevSecOps, Automation",
                key="upd_doc_custom_cat",
            )
            if st.button(
                "Update Document Category", key="btn_upd_doc", use_container_width=True
            ):
                target_doc_cat = (
                    custom_doc_cat.strip() if custom_doc_cat.strip() else new_doc_cat
                )
                qdrant.set_payload(
                    collection_name=COLLECTION_NAME,
                    payload={"category": target_doc_cat},
                    points=[selected_doc["id"]],
                )
                st.success(
                    f"Updated '{selected_doc['title']}' category to '{target_doc_cat}'!"
                )
                st.rerun()

        with col_upd_cat:
            st.subheader("🏷️ Bulk Update Category")
            present_categories = sorted({r["category"] for r in records})
            old_cat = st.selectbox(
                "Select Category to Rename / Reassign",
                options=present_categories,
                key="upd_bulk_old_cat",
            )
            new_bulk_cat = st.selectbox(
                "Assign to Existing Category",
                options=ALL_CATEGORIES,
                index=ALL_CATEGORIES.index(old_cat)
                if old_cat in ALL_CATEGORIES
                else 0,
                key="upd_bulk_new_cat",
            )
            custom_bulk_cat = st.text_input(
                "Or Enter New Category Name (optional)",
                placeholder="e.g., Core-Network, SRE",
                key="upd_bulk_custom_cat",
            )
            if st.button("Update Category", key="btn_upd_cat", use_container_width=True):
                target_bulk_cat = (
                    custom_bulk_cat.strip() if custom_bulk_cat.strip() else new_bulk_cat
                )
                qdrant.set_payload(
                    collection_name=COLLECTION_NAME,
                    payload={"category": target_bulk_cat},
                    points=Filter(
                        must=[
                            FieldCondition(
                                key="category", match=MatchValue(value=old_cat)
                            )
                        ]
                    ),
                )
                st.success(
                    f"Updated all documents in '{old_cat}' to '{target_bulk_cat}'!"
                )
                st.rerun()
    else:
        st.info(
            "Collection is currently empty. Click 'Load Sample NOC/SRE Playbooks' in the sidebar."
        )
