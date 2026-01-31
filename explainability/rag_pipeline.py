import faiss
import json
import numpy as np
from sentence_transformers import SentenceTransformer
from pathlib import Path

try:
    from explainability.llm_explainer import LLMExplainer
except ImportError:
    from llm_explainer import LLMExplainer

BASE_DIR = Path(__file__).parent
VECTOR_STORE_PATH = BASE_DIR / "vector_store" / "index.faiss"
DOC_STORE_PATH = BASE_DIR / "vector_store" / "docs.json"

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


class RAGPipeline:
    def __init__(self, enable_rag: bool = True):
        self.llm = LLMExplainer()
        self.enable_rag = enable_rag

        if enable_rag and VECTOR_STORE_PATH.exists():
            self.embedder = SentenceTransformer(EMBEDDING_MODEL)
            self.index = faiss.read_index(str(VECTOR_STORE_PATH))
            self.documents = json.loads(DOC_STORE_PATH.read_text())
        else:
            # Safe fallback for tests
            self.embedder = None
            self.index = None
            self.documents = {}

    def retrieve_context(self, query: str, top_k: int = 5) -> str:
        if not self.enable_rag or self.index is None:
            return ""

        query_vec = self.embedder.encode([query]).astype("float32")
        _, indices = self.index.search(query_vec, top_k)

        return "\n".join(
            self.documents.get(str(idx), "")
            for idx in indices[0]
        )

    def explain_transaction(self, transaction: dict, model_signals: dict) -> str:
        query = "anomalous financial transaction detected"
        context = self.retrieve_context(query)

        return self.llm.explain(
            transaction=transaction,
            model_signals=model_signals,
            retrieved_context=context,
        )
