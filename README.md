
# 🚀 AnthraSync – Interactive Hybrid RAG Assistant

<p align="center">

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=for-the-badge&logo=openai&logoColor=white)
![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector_DB-blue?style=for-the-badge)
![BM25](https://img.shields.io/badge/BM25-Hybrid_Search-orange?style=for-the-badge)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Cloud](https://img.shields.io/badge/Cloud-Deployment-4285F4?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

</p>

> An interactive **Hybrid Retrieval-Augmented Generation (Hybrid RAG)** assistant built with **FastAPI**, **Streamlit**, **ChromaDB**, **BM25**, and **OpenAI**.

---

# 🌐 Live Links

- 🎨 **Frontend (Streamlit Cloud):** https://an-enterprise-knowledge-assistant-kpxlbzqiabwxpovzybejr3.streamlit.app
- ⚙️ **Backend API (Docker + Cloud):** https://eshwar109-assignment-anthra.hf.space

---

# 📖 Overview

AnthraSync combines **BM25 lexical search** and **Dense Vector Retrieval** to deliver accurate, explainable, and source-backed answers from enterprise documents.

## ✨ Features

- 🤖 Hybrid Retrieval (BM25 + Dense Search)
- 📚 PDF Knowledge Base
- ⚡ FastAPI Backend
- 🎨 Streamlit Frontend
- 🔍 Retrieval Diagnostics
- 📄 Source Citation
- ❤️ Health Monitoring
- ☁️ Dockerized Backend Deployment

---

# 🏗 Architecture

```mermaid
flowchart LR
User --> Streamlit
Streamlit -->|POST /ask| FastAPI
FastAPI --> BM25
FastAPI --> ChromaDB
FastAPI --> OpenAI
BM25 --> Hybrid
ChromaDB --> Hybrid
Hybrid --> Answer
Answer --> Streamlit
```

---

# 🛠 Tech Stack

| Category | Technology |
|---|---|
| Language | Python 3.10+ |
| Backend | FastAPI, Uvicorn |
| Frontend | Streamlit |
| LLM | OpenAI |
| Embeddings | sentence-transformers |
| Vector DB | ChromaDB |
| Retrieval | BM25 + Dense Search |
| Deployment | Docker + Cloud |

---

# 📂 Project Structure

```text
AnthraSync/
├── backend/
│   ├── api.py
│   ├── rag_engine.py
├── frontend/
│   ├── app_ui.py
│   └── requirements.txt
├── knowledge_base/
├── chromastore/
├── Dockerfile
├── requirements.txt
└── README.md
```

---

# ⚙️ Quick Start

## Clone

```bash
git clone https://github.com/YOUR_USERNAME/AnthraSync.git
cd AnthraSync
```

## Install Dependencies (uv)

```bash
uv sync
```

or

```bash
uv pip install -r requirements.txt
```

## Environment Variables

```env
OPENAI_API_KEY=your_openai_api_key
HF_TOKEN=your_huggingface_token
```

## Run Backend

```bash
uv run uvicorn backend.api:app --reload --host 0.0.0.0 --port 8000
```

## Run Frontend

```bash
uv run streamlit run frontend/app_ui.py
```

---

# ☁️ Deployment

## Frontend

Deploy to **Streamlit Cloud** using:

- Entry point: `frontend/app_ui.py`

## Backend

The backend is packaged using **Docker** and deployed to a cloud server.

### Build

```bash
docker build -t anthrasync-backend .
```

### Run

```bash
docker run -d \
-e OPENAI_API_KEY="<your_key>" \
-e HF_TOKEN="<hf_token>" \
-p 8000:8000 \
-v $(pwd)/chromastore:/app/chromastore \
anthrasync-backend
```

---

# 📡 API

| Method | Endpoint |
|---|---|
| GET | `/health` |
| POST | `/ask` |

Example

```json
{
  "question":"Explain Hybrid RAG"
}
```

---

# 🔐 Environment Variables

| Variable | Purpose |
|---|---|
| OPENAI_API_KEY | OpenAI API |
| HF_TOKEN | HuggingFace Token |
| CHROMA_PERSIST_PATH | Chroma Storage |

---

# 🧪 Testing & Diagnostics

### 🔍 tmp_rag_inspect.py

- Inspect parsed documents
- View chunks
- Debug BM25 & Dense retrieval

### ✅ tmp_rag_test.py

- Validate environment variables
- Test embeddings
- Verify OpenAI connectivity
- End-to-end RAG test

---

# 🚀 Future Improvements

- 💬 Chat Memory
- 🌍 Multi Knowledge Bases
- 📈 Analytics Dashboard
- 🎙 Voice Search
- 📱 Mobile UI
- 🧠 Agentic RAG

---

# 👨‍💻 Author

**T. Eshwar T**

- 💼 LinkedIn: www.linkedin.com/in/eshwarofficial
- 🐙 GitHub: https://github.com/Eshwar-129

---

⭐ If you like this project, consider starring the repository!
