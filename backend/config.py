import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
KNOWLEDGE_PATH = Path(os.getenv("KNOWLEDGE_PATH", ROOT / "knowledge_base1"))
CHROMA_PERSIST_DIR = Path(os.getenv("CHROMA_PERSIST_DIR", ROOT / "chromastore"))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
HUGGINGFACE_TOKEN = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_TOKEN")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://openrouter.ai/api/v1")
EMBEDDING_MODEL = "text-embedding-3-small"
LLM_MODEL = "gpt-4o-mini"
RAG_CHUNK_SIZE = 400
RAG_CHUNK_OVERLAP = 90
BM25_TOP_K = 6
DENSE_TOP_K = 6
RERANK_TOP_K = 1
ENABLE_VECTOR_STORE_PERSISTENCE = os.getenv("ENABLE_VECTOR_STORE_PERSISTENCE", "true").lower() in ("1", "true", "yes")
REBUILD_VECTOR_STORE_ON_STARTUP = os.getenv("REBUILD_VECTOR_STORE_ON_STARTUP", "false").lower() in ("1", "true", "yes")
FALLBACK_ANSWER = (
    "I am sorry, but the provided documentation does not contain enough information to answer your question."
)

SECURITY_PATTERNS = [
    r"\bpassword\b",
    r"\bmaster token\b",
    r"\bconnection string\b",
    r"\bsecret\b",
    r"sk-[A-Za-z0-9_-]{20,}",
    r"\b\w+-\w+-\w+\.internal\b",
]

SENSITIVE_QUERY_PATTERNS = [
    r"\bcredential(s)?\b",
    r"\bpass(word)?\b",
    r"\bsecret(s)?\b",
    r"\btoken\b",
    r"\bapi[_-]?key\b",
    r"\bconnection string\b",
]

OUTPUT_REDACTION_PATTERNS = [
    r"sk-[A-Za-z0-9_-]{20,}",
    r"postgresql://\S+",
    r"api[-_]key\b",
    r"(?:aws|azure|gcp)[-_ ]?secret\b",
    r"https?://[\w\.-]+\.internal[:\w/]*",
    r"\b\w+-\w+-\w+\.internal\b",
    r"(?i)\b(?:user(?:name)?|pass(?:word)?|secret|token|credential|api[_-]?key|connection string|ssh[-_]key|private key)\b\s*[:=]\s*['\"]?[^'\"]+['\"]?",
]

PROMPT_CONFIG = {
    "system": (
        "You are a security-aware enterprise retrieval assistant. Use only the provided context and do not hallucinate. "
        "If the context does not fully answer the question, respond exactly with the fallback answer."
    ),
    "query_rewrite": (
        "Rewrite the user query into a concise retrieval query for the document store. "
        "Remove filler words and keep only the essential terms. Do not add words like 'query' or change the meaning."
    ),
}
