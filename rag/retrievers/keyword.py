"""
Keyword retriever using BM25 algorithm.
Crucial for exact drug name matches (e.g., "Amoxiclav", "Ibuprofen").
"""
from rank_bm25 import BM25Okapi

class KeywordRetriever:
    def __init__(self):
        self.bm25 = None
        self.documents = []

    def index_documents(self, documents: list[str]):
        tokenized_corpus = [doc.lower().split() for doc in documents]
        self.bm25 = BM25Okapi(tokenized_corpus)
        self.documents = documents

    def retrieve(self, query: str, top_k: int = 5) -> list[str]:
        if not self.bm25:
            raise ValueError("BM25 index is not initialized. Call index_documents first.")
        tokenized_query = query.lower().split()
        doc_scores = self.bm25.get_top_n(tokenized_query, self.documents, n=top_k)
        return doc_scores
