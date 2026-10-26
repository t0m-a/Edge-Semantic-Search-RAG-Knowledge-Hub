import os
import subprocess
import time
import uuid
import pandas as pd
import streamlit as st
from fastembed import TextEmbedding
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

# --- CONFIGURATION ---
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION", "knowledge_hub")
CACHE_DIR = os.getenv("FASTEMBED_CACHE_PATH", "/app/model_cache")
MODEL_NAME = "BAAI/bge-small-en-v1.5"
VECTOR_DIM = 384

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

# --- INITIALIZE SERVICES IN ORDER ---
embedder = load_embedder()
qdrant = get_qdrant_client()
ensure_collection(qdrant)
ALL_CATEGORIES = get_active_categories(qdrant)

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

def ingest_chunks(records):
    texts = [f"{r['title']}: {r['content']}" for r in records]
    vectors = list(embedder.embed(texts))
    points = [
        PointStruct(
            id=str(uuid.uuid4()),
            vector=vec.tolist(),
            payload={
                "title": r["title"],
                "category": r["category"],
                "source": r["source"],
                "content": r["content"],
                "indexed_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            },
        )
        for r, vec in zip(records, vectors)
    ]
    qdrant.upsert(collection_name=COLLECTION_NAME, points=points)

# --- SIDEBAR TELEMETRY ---
with st.sidebar:
    st.title("⚡ Edge Node Telemetry")
    st.caption("Hardware: Raspberry Pi 5 (ARM64)")
    info = qdrant.get_collection(COLLECTION_NAME)
    col1, col2 = st.columns(2)
    col1.metric("Vectors Stored", info.points_count)
    col2.metric("Dimensions", VECTOR_DIM)
    st.markdown(f"**Model:** `{MODEL_NAME}` (ONNX)")
    st.markdown(f"**Active Categories:** `{len(ALL_CATEGORIES)}`")
    st.divider()
    if st.button("🚀 Load Sample NOC/SRE Playbooks", use_container_width=True):
        with st.spinner("Vectorizing & indexing playbooks on Pi 5 CPU..."):
            t0 = time.perf_counter()
            ingest_chunks(SAMPLE_PLAYBOOKS)
            elapsed = (time.perf_counter() - t0) * 1000
        st.success(f"Indexed {len(SAMPLE_PLAYBOOKS)} playbooks in {elapsed:.1f} ms!")
        st.rerun()

# --- MAIN UI ---
st.title("🔍 Edge Semantic Search & RAG Knowledge Hub")
st.markdown(
    "Self-hosted on a **Raspberry Pi 5** using **Qdrant (Rust)** and **FastEmbed (Quantized ONNX)** behind **Cloudflare Zero Trust**."
)

tab_search, tab_ingest, tab_analytics = st.tabs(
    ["🔎 Semantic Retrieval", "📥 Ingest Knowledge", "📊 Vector Collection Explorer"]
)

with tab_search:
    c1, c2, c3 = st.columns([3, 1, 1])
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
        min_score = st.slider("Min Cosine Score", 0.30, 0.95, 0.50, 0.05)

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
            f"⏱️ **ONNX CPU Embedding:** `{t_embed:.1f} ms` | **Qdrant Rust Lookup:** `{t_search:.1f} ms` | **Matches:** `{len(results)}`"
        )

        if not results:
            st.warning("No semantic matches above threshold. Try lowering the Min Cosine Score or loading sample playbooks from the sidebar.")
        for hit in results:
            p = hit.payload
            with st.container(border=True):
                h_col1, h_col2 = st.columns([4, 1])
                h_col1.subheader(f"📄 {p.get('title', 'Untitled')}")
                h_col2.metric("Cosine Similarity", f"{hit.score:.4f}")
                st.markdown(f"**Category:** `{p.get('category')}` | **Source:** `{p.get('source')}` | **Indexed:** `{p.get('indexed_at')}`")
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
        submitted = st.form_submit_button("Vectorize & Store in Qdrant")

        if submitted and doc_title and doc_body:
            final_category = custom_cat.strip() if custom_cat.strip() else selected_cat
            t0 = time.perf_counter()
            ingest_chunks(
                [
                    {
                        "title": doc_title,
                        "category": final_category,
                        "source": doc_source,
                        "content": doc_body,
                    }
                ]
            )
            ms = (time.perf_counter() - t0) * 1000
            st.success(f"Stored vector under '{final_category}' in {ms:.1f} ms!")
            st.rerun()

    st.divider()
    col_u1, col_u2 = st.columns(2)

    with col_u1:
        st.subheader("📂 Upload Markdown Files (.md)")
        uploaded_files = st.file_uploader(
            "Drag and drop Markdown notes", type=["md", "txt"], accept_multiple_files=True
        )
        upload_cat = st.selectbox("Tag Category", ALL_CATEGORIES, key="up_cat")
        upload_custom_cat = st.text_input("Or New Category for Upload (optional)", key="up_custom_cat")
        if st.button("Vectorize Uploaded Files") and uploaded_files:
            from ingest import chunk_markdown
            target_cat = upload_custom_cat.strip() if upload_custom_cat.strip() else upload_cat
            batch_records = []
            for uf in uploaded_files:
                raw_text = uf.read().decode("utf-8", errors="ignore")
                for c in chunk_markdown(raw_text, fallback_title=uf.name):
                    batch_records.append({
                        "title": c["title"],
                        "category": target_cat,
                        "source": uf.name,
                        "content": c["content"],
                    })
            ingest_chunks(batch_records)
            st.success(f"Indexed {len(batch_records)} sections under '{target_cat}'!")
            st.rerun()

    with col_u2:
        st.subheader("🐙 Ingest Public GitHub Repo")
        repo_url = st.text_input("GitHub Repository HTTPS URL", placeholder="https://github.com/owner/repo")
        repo_cat = st.selectbox("Repo Category", ALL_CATEGORIES, key="gh_cat")
        repo_custom_cat = st.text_input("Or New Category for Repo (optional)", key="gh_custom_cat")
        if st.button("Clone & Index Repository") and repo_url:
            target_repo_cat = repo_custom_cat.strip() if repo_custom_cat.strip() else repo_cat
            with st.spinner("Cloning repository and vectorizing Markdown docs..."):
                res = subprocess.run(
                    ["python", "ingest.py", "--github", repo_url, "--category", target_repo_cat],
                    capture_output=True,
                    text=True,
                )
            if res.returncode == 0:
                st.success(f"Repository indexed under '{target_repo_cat}'!")
                st.code(res.stdout)
                st.rerun()
            else:
                st.error(res.stderr)

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
            if st.button("Update Document Category", key="btn_upd_doc", use_container_width=True):
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
        st.info("Collection is currently empty. Click 'Load Sample NOC/SRE Playbooks' in the sidebar.")
