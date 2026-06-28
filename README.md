# Assignment Anthrasync

**Overview**

An interactive Hybrid RAG assistant consisting of a FastAPI backend for retrieval and reasoning, and a Streamlit frontend for querying, diagnostics, and source inspection.

**Quick Start (Local)**

- **Install dependencies:** `python -m pip install -r requirements.txt`
- **Set secrets (Windows PowerShell):** `setx OPENAI_API_KEY "your_api_key"` and `setx HF_TOKEN "your_huggingface_token"`
- **Run backend:** `uvicorn backend.api:app --reload --host 0.0.0.0 --port 8000`
- **Run frontend (local):** `streamlit run frontend/app_ui.py`

**Deploy Frontend to Streamlit Cloud**

- The frontend requires `streamlit` and `httpx`. A minimal frontend requirements file is available at [frontend/requirements.txt](frontend/requirements.txt).
- Streamlit Cloud expects a single `requirements.txt` at the repo root by default. You can either:
  - Copy the contents of `frontend/requirements.txt` into the root `requirements.txt`, or
  - When creating the Streamlit app, point it to the `frontend` folder and add `frontend/requirements.txt` in the app settings.
- Deploy steps (example):

```bash
# 1. Commit and push your repo to GitHub
git add .
git commit -m "Add frontend Streamlit app and requirements"
git push

# 2. In Streamlit Cloud, create a new app, connect the GitHub repo and branch
# 3. Set the app file to `frontend/app_ui.py` and ensure requirements include Streamlit and httpx
```

**Approach & Design**

- **Goal:** Provide a minimal, secure RAG UI that queries an external FastAPI backend and shows answer, sources, and retrieval diagnostics.
- **Frontend responsibilities:** Send user queries to the backend `/ask` endpoint, display the assistant answer, show retrieval metrics and source documents, and provide a backend health check.
- **Backend responsibilities:** Ingest documents, build indexes, handle retrieval (BM25 + dense), perform any reranking or safety checks, and expose `/ask` and `/health` endpoints.

**Architecture Diagram**

```mermaid
flowchart LR
   User[User Browser] -->|Interacts| Streamlit[Streamlit Frontend]\n+  Streamlit -->|POST /ask| Backend[FastAPI Backend]\n+  Backend -->|Retrieves| VectorDB[(Chroma / SQLite)]
   Backend -->|Calls| LLM[(LLM / LLM provider)]
   Backend -->|Returns answer and diagnostics| Streamlit
```

**Files & Structure**

- **Project root:**
  - [backend](backend) — FastAPI implementation and RAG engine
  - [frontend](frontend) — Streamlit UI
  - [knowledge_base](knowledge_base) — Put source PDFs here
  - [pdf.py](pdf.py) — PDF generator (design docs)
  - [requirements.txt](requirements.txt) — Combined runtime deps for the project

- **Key files:**
  - [backend/api.py](backend/api.py) — FastAPI routes
  - [backend/rag_engine.py](backend/rag_engine.py) — Retrieval and reasoning logic
  - [frontend/app_ui.py](frontend/app_ui.py) — Streamlit app for the UI
  - [frontend/requirements.txt](frontend/requirements.txt) — Minimal frontend deps for Streamlit Cloud

**Deployment Notes**

- For Streamlit Cloud deploy, ensure `streamlit` and `httpx` are available in the app requirements. If your root `requirements.txt` already includes backend dependencies (e.g., sentence-transformers, chroma, openai, pydantic), you may prefer to keep a slim `frontend/requirements.txt` and paste its contents into the root `requirements.txt` used by Streamlit Cloud.
- The frontend reads a backend URL from the sidebar. For production, deploy the backend (e.g., on Render, Fly, Railway, or a Hugging Face Space) and enter the public URL in the Streamlit app.

**Backend Deployment**

- **Required environment variables**
  - `OPENAI_API_KEY` — API key for the LLM provider used by the backend
  - `HF_TOKEN` — (optional) Hugging Face token to avoid anonymous download limits
  - `CHROMA_PERSIST_PATH` or persistent folder for the Chroma/SQLite store (this project uses `chromastore/`)

- **Endpoints to expose**
  - `POST /ask` — main query endpoint (expects JSON {"question": "..."})
  - `GET /health` — health/readiness check used by the frontend

- **Run with Uvicorn (simple)**

```bash
# Development / small deployment
uvicorn backend.api:app --host 0.0.0.0 --port 8000 --workers 1
```

- **Docker (recommended for predictable deploys)**

Build and run the included Dockerfile (the repo contains a `Dockerfile` in the project root):

```bash
# Build the image
docker build -t anthrasync-backend .

# Run (Linux/macOS)
docker run -e OPENAI_API_KEY="<your_key>" -e HF_TOKEN="<hf_token>" -p 8000:8000 \
  -v $(pwd)/chromastore:/app/chromastore anthrasync-backend

# Run (PowerShell)
docker run -e OPENAI_API_KEY="<your_key>" -e HF_TOKEN="<hf_token>" -p 8000:8000 \
  -v ${PWD}/chromastore:/app/chromastore anthrasync-backend
```

- **Cloud hosting options**
  - Render / Railway / Fly: Create a new web service, connect your GitHub repo, set environment variables (`OPENAI_API_KEY`, `HF_TOKEN`), and point the service to run `uvicorn backend.api:app --host 0.0.0.0 --port 8000` (or use the Dockerfile).
  - Managed vector DBs: If you need horizontal scaling, consider moving Chroma to a managed vector DB or using a hosted embeddings/index service rather than the local SQLite-backed `chromastore/` folder.

- **Networking & security**
  - Ensure CORS is configured to allow your frontend origin (or configure the frontend to use the same domain and a reverse proxy).
  - Use HTTPS in production (Cloud providers or a reverse proxy like Traefik/nginx will handle TLS).
  - Protect your API with authentication if exposing it publicly (API key, JWT, or network-based restrictions).

- **Scaling tips**
  - For higher concurrency increase `--workers` for `uvicorn` or use an ASGI process manager.
  - Offload heavy LLM calls to async workers or a queue if you expect long-running requests.

**Usage Examples**

- Local dev: `streamlit run frontend/app_ui.py`
- Production: Configure the Streamlit Cloud app to use `frontend/app_ui.py` as the entrypoint and include required packages.

**Notes & Tips**

- The Streamlit UI uses `httpx` to talk to the backend and a 60s request timeout to accommodate longer reasoning flows.
- The default `DEFAULT_API_URL` in `frontend/app_ui.py` points to a placeholder — update it to your deployed backend.

---

If you'd like, I can also merge the frontend requirements into the root `requirements.txt`, commit the change, and help configure the Streamlit Cloud app settings.

**Tech Stack**

- **Language:** Python 3.10+
- **Web / API:** `FastAPI`, `uvicorn`
- **Frontend:** `Streamlit`
- **HTTP client:** `httpx`
- **Indexing / Vector DB:** `chromadb` (local SQLite persist in `chromastore/`)
- **Embeddings / Models:** `sentence-transformers`, OpenAI via `openai`
- **Retrieval:** `rank_bm25` for lexical retrieval and dense retrieval via vector embeddings
- **Utilities:** `python-dotenv`, `pypdf`, `fpdf`/`fpdf2`

These packages are also listed in `requirements.txt` for reproducibility.

**What are `tmp_rag_inspect.py` and `tmp_rag_test.py`?**

- `tmp_rag_inspect.py` — A lightweight inspection script that constructs the `HybridRAGSystem` from `backend.rag_engine`, then prints summary information for debugging: number of loaded documents, a sample of document and chunk contents, the query rewrite/optimization output, and the top BM25 and dense retrieval results for a sample query. Use this when you want to inspect how documents are parsed, chunked, and what each retrieval method returns.

- `tmp_rag_test.py` — A quick end-to-end smoke test for the RAG engine. It loads environment variables (via `.env`), validates the presence of `OPENAI_API_KEY`, constructs the `HybridRAGSystem`, issues a sample `ask()` call, and prints the returned keys and answer. Useful for validating that the engine, embeddings, and model calls are functioning in your environment.
