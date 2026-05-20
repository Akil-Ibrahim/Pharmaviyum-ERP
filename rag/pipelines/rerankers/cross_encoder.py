"""
Cross-Encoder Reranker optimized for local inference.
Re-ranks retrieved drug instructions for higher precision.
"""
from sentence_transformers import CrossEncoder

class LocalCrossEncoderReranker:
    def __init__(self, model_name: str = "BAAI/bge-reranker-base"):
        self.model = CrossEncoder(model_name)

    def rerank(self, query: str, documents: list[str], top_k: int = 3) -> list[tuple[str, float]]:
        pairs = [(query, doc) for doc in documents]
        scores = self.model.predict(pairs)
        ranked_docs = sorted(zip(documents, scores), key=lambda x: x[1], reverse=True)
        return ranked_docs[:top_k]
