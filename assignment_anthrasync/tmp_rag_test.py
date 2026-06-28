import os
from dotenv import load_dotenv
load_dotenv()
print('OPENAI_API_KEY present:', bool(os.getenv('OPENAI_API_KEY')))
from backend.rag_engine import HybridRAGSystem

try:
    engine = HybridRAGSystem()
    print('Engine constructed')
    result = engine.ask('What does Aethera Sync Systems do?')
    print('Result keys:', result.keys())
    print('Answer:', result['answer'])
except Exception as exc:
    import traceback
    traceback.print_exc()
    print('Exception:', type(exc).__name__, exc)
