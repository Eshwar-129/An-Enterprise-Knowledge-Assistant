import asyncio
import logging
import os
import re
import time
import json
from typing import Any, Dict, List, Optional
from backend.config import SENSITIVE_QUERY_PATTERNS

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from rank_bm25 import BM25Okapi

from backend.config import (
    BM25_TOP_K,
    CHROMA_PERSIST_DIR,
    DENSE_TOP_K,
    EMBEDDING_MODEL,
    ENABLE_VECTOR_STORE_PERSISTENCE,
    FALLBACK_ANSWER,
    HUGGINGFACE_TOKEN,
    LLM_MODEL,
    OPENAI_API_BASE,
    OPENAI_API_KEY,
    OUTPUT_REDACTION_PATTERNS,
    PROMPT_CONFIG,
    RAG_CHUNK_OVERLAP,
    RAG_CHUNK_SIZE,
    RERANK_TOP_K,
    REBUILD_VECTOR_STORE_ON_STARTUP,
    SECURITY_PATTERNS,
    KNOWLEDGE_PATH,
)

try:
    from sentence_transformers import CrossEncoder
except ImportError:
    CrossEncoder = None

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class HybridRAGSystem:
    def __init__(self, knowledge_path: str = str(KNOWLEDGE_PATH)):
        self.knowledge_path = knowledge_path
        if OPENAI_API_KEY is None:
            raise ValueError("OPENAI_API_KEY is not set. Please configure it in the .env file.")

        self.embedding_model = OpenAIEmbeddings(
            model=EMBEDDING_MODEL,
            openai_api_key=OPENAI_API_KEY,
            openai_api_base=OPENAI_API_BASE,
        )
        self.llm = ChatOpenAI(
            model_name=LLM_MODEL,
            temperature=0.0,
            openai_api_key=OPENAI_API_KEY,
            openai_api_base=OPENAI_API_BASE,
        )
        
        # Dedicated judge LLM for evaluation (JSON mode)
        self.judge_llm = ChatOpenAI(
            model_name=LLM_MODEL,
            temperature=0.0,
            openai_api_key=OPENAI_API_KEY,
            openai_api_base=OPENAI_API_BASE,
            model_kwargs={"response_format": {"type": "json_object"}}
        )

        if HUGGINGFACE_TOKEN:
            os.environ.setdefault("HF_TOKEN", HUGGINGFACE_TOKEN)
            
        self.cross_encoder = self._load_cross_encoder()
        self.documents = self._load_documents()
        self.chunks = self._split_documents(self.documents)
        self.vector_store = self._build_vector_store(self.chunks)
        self.bm25_index = self._build_bm25(self.chunks)

    def _load_cross_encoder(self) -> Optional[Any]:
        if CrossEncoder is None:
            logger.warning("sentence-transformers is not installed; cross-encoder reranking will fall back.")
            return None
        try:
            return CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
        except Exception as exc:
            logger.warning("Cross-encoder initialization failed: %s", exc)
            return None

    def _load_documents(self) -> List[Document]:
        if os.path.isdir(self.knowledge_path):
            try:
                loader = PyPDFDirectoryLoader(self.knowledge_path)
                documents = loader.load()
                if documents:
                    logger.info("Loaded %s PDF documents from %s", len(documents), self.knowledge_path)
                    return documents
            except Exception as exc:
                logger.warning("Unable to load PDFs: %s. Falling back to sample content.", exc)

        logger.warning("No PDF documents found. Falling back to a sample internal document.")
        sample_text = (
            "Aethera Sync Systems operates an enterprise retrieval assistant that combines lexical BM25 search "
            "with dense embeddings, strong query rewriting, and answer guardrails to produce faithful responses."
        )
        return [Document(page_content=sample_text, metadata={"source": "internal_sample"})]

    def _split_documents(self, documents: List[Document]) -> List[Document]:
        splitter = RecursiveCharacterTextSplitter(chunk_size=RAG_CHUNK_SIZE, chunk_overlap=RAG_CHUNK_OVERLAP)
        chunks = splitter.split_documents(documents)
        logger.info("Split documents into %s retrieval chunks.", len(chunks))
        return chunks

    def _vector_store_exists(self) -> bool:
        if not ENABLE_VECTOR_STORE_PERSISTENCE:
            return False
        return CHROMA_PERSIST_DIR.exists() and any(CHROMA_PERSIST_DIR.iterdir())

    def _build_vector_store(self, chunks: List[Document]) -> Chroma:
        chroma_dir = str(CHROMA_PERSIST_DIR)
        if self._vector_store_exists() and not REBUILD_VECTOR_STORE_ON_STARTUP:
            try:
                return Chroma(persist_directory=chroma_dir, embedding_function=self.embedding_model)
            except Exception as exc:
                logger.warning("Failed to load persisted Chroma store: %s. Rebuilding.", exc)

        vector_store = Chroma.from_documents(chunks, self.embedding_model, persist_directory=chroma_dir)
        try:
            vector_store.persist()
        except Exception as exc:
            logger.warning("Could not persist Chroma vector store: %s", exc)
        return vector_store

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r"\w+", text.lower())

    def _filter_query_terms(self, text: str) -> str:
        stopwords = {
            "what", "is", "the", "a", "an", "of", "in", "on", "for", "to", "and", "or",
            "by", "with", "from", "that", "this", "these", "those", "be", "are", "do", "does",
            "how", "why", "when", "which", "who", "whom", "whose", "please",
        }
        terms = [token for token in self._tokenize(text) if token not in stopwords]
        return " ".join(terms) if terms else text

    def _build_bm25(self, chunks: List[Document]) -> BM25Okapi:
        tokenized_corpus = [self._tokenize(chunk.page_content) for chunk in chunks]
        return BM25Okapi(tokenized_corpus)

    def _validate_query(self, query: str) -> None:
        for pattern in SECURITY_PATTERNS:
            if re.search(pattern, query, flags=re.IGNORECASE):
                raise ValueError("The query contains a high-risk security token and cannot be processed.")

        for pattern in SENSITIVE_QUERY_PATTERNS:
            if re.search(pattern, query, flags=re.IGNORECASE):
                raise ValueError("The query requests sensitive credential information and cannot be answered.")

    def _redact_output(self, text: str) -> str:
        """
        Check if the text contains confidential information.
        If it does, return a proper denial message instead of [REDACTED].
        """
        has_confidential = False
        for pattern in OUTPUT_REDACTION_PATTERNS:
            if re.search(pattern, text, flags=re.IGNORECASE):
                has_confidential = True
                break
        
        if has_confidential:
            return "We cannot provide this information due to security and confidentiality policies."
        
        return text

    def _call_llm(self, messages: List[Any]) -> str:
        llm_result = self.llm.generate([messages])
        if llm_result.generations and llm_result.generations[0]:
            return llm_result.generations[0][0].text.strip()
        raise ValueError("LLM did not return a response.")

    def _rewrite_query(self, raw_query: str) -> str:
        simplified = self._filter_query_terms(raw_query)
        if simplified and simplified != raw_query:
            return simplified

        sys_prompt = (
            "You are an AI search optimizer. Rewrite the user's query into a concise retrieval query for the document store. "
            "Remove filler words and keep only the essential terms. Output ONLY the optimized query string. "
            "For example, 'what is the company name' -> 'company name'."
        )
        messages = [
            SystemMessage(content=sys_prompt),
            HumanMessage(content=f"Optimize this query: {raw_query}"),
        ]
        return self._call_llm(messages)

    def _retrieve_bm25_with_score(self, query: str, k: int = BM25_TOP_K) -> List[tuple[Document, float]]:
        tokens = self._tokenize(query)
        scores = self.bm25_index.get_scores(tokens)
        scored = sorted(
            [(self.chunks[i], float(scores[i])) for i in range(len(scores))],
            key=lambda item: item[1],
            reverse=True,
        )
        return scored[:k]

    def _retrieve_dense_with_score(self, query: str, k: int = DENSE_TOP_K) -> List[tuple[Document, float]]:
        raw_results = self.vector_store.similarity_search_with_score(query, k=k)
        return [(doc, float(score)) for doc, score in raw_results]

    def _merge_scored_documents(self, results: List[List[tuple[Document, float]]], max_items: int = 15, k: int = 60) -> List[Document]:
        """Merges disparate search results using Reciprocal Rank Fusion (RRF)."""
        rrf_scores: Dict[tuple, float] = {}
        docs_map: Dict[tuple, Document] = {}

        for result_list in results:
            for rank, (doc, _score) in enumerate(result_list):
                fingerprint = (doc.metadata.get("source"), str(doc.metadata.get("page", "")))
                
                if fingerprint not in rrf_scores:
                    rrf_scores[fingerprint] = 0.0
                    docs_map[fingerprint] = doc
                    
                # RRF Formula
                rrf_scores[fingerprint] += 1.0 / (k + rank)

        merged = sorted(rrf_scores.items(), key=lambda item: item[1], reverse=True)
        return [docs_map[fp] for fp, _score in merged][:max_items]

    def _document_query_overlap(self, doc: Document, tokens: List[str]) -> int:
        content_tokens = self._tokenize(doc.page_content)
        return sum(1 for token in tokens if token in content_tokens)

    def _prioritize_query_overlap(self, documents: List[Document], query: str, max_items: int = 5) -> List[Document]:
        tokens = self._tokenize(query)
        scored = [(self._document_query_overlap(doc, tokens), doc) for doc in documents]
        scored = sorted(scored, key=lambda item: (item[0],), reverse=True)
        filtered = [doc for overlap, doc in scored if overlap > 0]
        if filtered:
            return filtered[:max_items]
        return documents[:max_items]

    def _rerank(self, query: str, documents: List[Document], top_k: int = RERANK_TOP_K) -> List[Document]:
        if not documents:
            return []

        if self.cross_encoder is not None:
            try:
                pairs = [(query, doc.page_content) for doc in documents]
                scores = self.cross_encoder.predict(pairs)
                ranked = sorted(zip(scores, documents), key=lambda item: item[0], reverse=True)
                return [doc for _, doc in ranked][:top_k]
            except Exception as exc:
                logger.warning("Cross-encoder reranking failed: %s", exc)

        # Fallback to standard dense similarity
        query_embedding = self.embedding_model.embed_query(query)
        scored = []
        for doc in documents:
            doc_embedding = getattr(doc, "embedding", None)
            if doc_embedding is None:
                doc_embedding = self.embedding_model.embed_query(doc.page_content)
            similarity = self._cosine_similarity(query_embedding, doc_embedding)
            scored.append((similarity, doc))
            
        ranked = sorted(scored, key=lambda item: item[0], reverse=True)
        return [doc for _, doc in ranked][:top_k]

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        from math import sqrt
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = sqrt(sum(x * x for x in a))
        norm_b = sqrt(sum(y * y for y in b))
        return dot / (norm_a * norm_b + 1e-12)

    def _compose_context(self, documents: List[Document]) -> str:
        parts = []
        for idx, doc in enumerate(documents, start=1):
            parts.append(
                f"Context {idx} ({doc.metadata.get('source', 'unknown')}):\n{doc.page_content.strip()}"
            )
        return "\n---\n".join(parts)

    def _sanitize_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(metadata, dict):
            return {"source": str(metadata)}

        allowed_fields = ["source", "page_label", "page", "total_pages"]
        return {key: metadata[key] for key in allowed_fields if key in metadata}

    def _format_prompt(self, query: str, context_text: str) -> str:
        return f"""You are a precise, reliable enterprise knowledge assistant. Your primary directive is to answer the user's question based strictly on the provided Context.

### Context Documents:
{context_text}

### User Question:
{query}

### Strict Instructions:
1. **Analyze:** Carefully read the Context Documents above.
2. **Extract:** Identify only the explicit facts that directly address the User Question.
        3. **Synthesize:** Construct a clear, professional, and direct response using ONLY the extracted facts.
        4. **Exact Answer Required:** If the Context Documents contain the answer, respond with that explicit answer and nothing else.
        5. **No Outside Knowledge:** Do NOT include any information, opinions, code, or context that is not explicitly stated in the text above. Do not attempt to guess or deduce.
        6. **Partial Matches:** If the context only partially answers the question, provide the information that is available and clearly state that the rest of the information is not present in the documents.
        7. **Total Missing Information:** If the Context Documents do not contain the answer to the User Question at all, you MUST ignore all other instructions and reply with EXACTLY this string: '{FALLBACK_ANSWER}'
"""

    async def ask_async(self, query: str) -> Dict[str, Any]:
        return await asyncio.to_thread(self.ask, query)

    def ask(self, query: str) -> Dict[str, Any]:
        self._validate_query(query)
        start_time = time.perf_counter()
        optimized_query = self._rewrite_query(query)

        dense_scored = self._retrieve_dense_with_score(optimized_query)
        bm25_scored = self._retrieve_bm25_with_score(optimized_query)
        
        # Now uses RRF to merge scores accurately
        merged_docs = self._merge_scored_documents([dense_scored, bm25_scored], max_items=15)
        prioritized = self._prioritize_query_overlap(merged_docs, optimized_query, max_items=6)
        ranked = self._rerank(optimized_query, prioritized)
        context_text = self._compose_context(ranked)

        messages = [
            SystemMessage(content=PROMPT_CONFIG.get("system", "You are a helpful assistant.")),
            HumanMessage(content=self._format_prompt(query, context_text)),
        ]
        
        response_text = self._call_llm(messages)
        answer = self._redact_output(response_text)
        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
        evaluation_metrics = self.evaluate(query, answer, ranked)

        return {
            "query": query,
            "optimized_query": optimized_query,
            "answer": answer,
            "context_documents": [self._sanitize_metadata(doc.metadata) for doc in ranked],
            "metrics": {
                **evaluation_metrics,
                "retrieval_count": len(ranked),
                "query_tokens": len(self._tokenize(optimized_query)),
                "elapsed_ms": elapsed_ms,
            },
        }

    def evaluate(self, query: str, answer: str, contexts: List[Document]) -> Dict[str, float]:
        """
        Uses an LLM-as-a-judge to evaluate the response instead of strict token math.
        """
        context_text = " ".join(doc.page_content for doc in contexts)
        
        # If the system triggered the fallback, metrics are inherently 0 (or N/A)
        if answer.strip() == FALLBACK_ANSWER.strip():
            return {"faithfulness": 0.0, "relevance": 0.0, "context_recall": 0.0}

        evaluation_prompt = f"""
        You are an expert grading system for an AI Retrieval-Augmented Generation (RAG) pipeline.
        Evaluate the following Question, Answer, and Context. 
        
        Score the following 3 metrics on a scale from 0.0 to 1.0:
        1. "faithfulness": Is the Answer supported entirely by the Context? (1.0 = yes, 0.0 = hallucination)
        2. "relevance": Does the Answer directly address the User Question? (1.0 = highly relevant, 0.0 = irrelevant)
        3. "context_recall": Does the Context contain enough information to fully answer the Question? (1.0 = yes, 0.0 = missing crucial info)
        
        Question: {query}
        Answer: {answer}
        Context: {context_text}
        
        Output valid JSON only with the keys "faithfulness", "relevance", and "context_recall" mapping to float values.
        """
        
        try:
            eval_result = self.judge_llm.invoke([HumanMessage(content=evaluation_prompt)])
            scores = json.loads(eval_result.content)
            return {
                "faithfulness": float(scores.get("faithfulness", 0.0)),
                "relevance": float(scores.get("relevance", 0.0)),
                "context_recall": float(scores.get("context_recall", 0.0)),
            }
        except Exception as e:
            logger.warning(f"LLM Evaluation failed, returning defaults: {e}")
            return {"faithfulness": 0.0, "relevance": 0.0, "context_recall": 0.0}