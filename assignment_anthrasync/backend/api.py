import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from backend.rag_engine import HybridRAGSystem


@asynccontextmanager
async def lifespan(app: FastAPI):
    global rag_engine
    rag_engine = await asyncio.to_thread(HybridRAGSystem)
    try:
        yield
    finally:
        rag_engine = None


app = FastAPI(
    title="Aethera Sync Hybrid RAG API",
    description="FastAPI backend for hybrid retrieval augmented generation with query rewriting, BM25, dense retrieval, and reranking.",
    version="0.1.0",
    lifespan=lifespan,
)

class AskRequest(BaseModel):
    question: str

class AskResponse(BaseModel):
    query: str
    optimized_query: str
    answer: str
    context_documents: list
    metrics: dict

rag_engine: HybridRAGSystem | None = None


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "message": "Aethera Sync RAG API is ready."}


@app.post("/ask", response_model=AskResponse)
async def ask(request: AskRequest) -> AskResponse:
    if rag_engine is None:
        raise HTTPException(status_code=503, detail="RAG engine is not initialized yet.")

    try:
        response = await rag_engine.ask_async(request.question)
        return AskResponse(**response)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Internal error: {exc}")
