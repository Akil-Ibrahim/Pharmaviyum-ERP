"""
Hybrid Retriever combining Vector (semantics) and Keyword (exact drug names) search.
Uses Reciprocal Rank Fusion (RRF) to merge results.
"""
from rag.retrievers.keyword import KeywordRetriever

class HybridRetriever:
    def __init__(self, vector_retriever, keyword_retriever: KeywordRetriever, rrf_k: int = 60):
        self.vector_retriever = vector_retriever
        self.keyword_retriever = keyword_retriever
        self.rrf_k = rrf_k

    def retrieve(self, query: str, top_k: int = 5) -> list:
        vector_results = self.vector_retriever.similarity_search(query, k=top_k)
        keyword_results = self.keyword_retriever.retrieve(query, top_k=top_k)

        rrf_scores = {}
        for rank, doc in enumerate(vector_results):
            rrf_scores[doc] = rrf_scores.get(doc, 0) + 1 / (self.rrf_k + rank + 1)
        for rank, doc in enumerate(keyword_results):
            rrf_scores[doc] = rrf_scores.get(doc, 0) + 1 / (self.rrf_k + rank + 1)

        ranked_results = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        return [doc for doc, score in ranked_results[:top_k]]
