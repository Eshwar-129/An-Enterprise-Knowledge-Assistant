import os
from dotenv import load_dotenv
load_dotenv()
from backend.rag_engine import HybridRAGSystem

engine = HybridRAGSystem()
print('Documents loaded:', len(engine.documents))
for i, doc in enumerate(engine.documents):
    print(f'DOC {i} source={doc.metadata.get("source")}', 'page=', doc.metadata.get('page'))
    print(doc.page_content[:800].replace('\n',' '))
    print('---')
print('Chunks:', len(engine.chunks))
for i, chunk in enumerate(engine.chunks[:15]):
    print(f'CHUNK {i} source={chunk.metadata.get("source")} page={chunk.metadata.get("page")}')
    print(chunk.page_content.replace('\n',' '))
    print('---')

query = 'what is the company name'
optimized = engine._rewrite_query(query)
print('Optimized query:', optimized)
print('BM25 results:')
for doc, score in engine._retrieve_bm25_with_score(optimized):
    print(score, doc.metadata.get('source'), repr(doc.page_content[:200].replace('\n',' ')))
print('Dense results:')
for doc, score in engine._retrieve_dense_with_score(optimized):
    print(score, doc.metadata.get('source'), repr(doc.page_content[:200].replace('\n',' ')))
PY