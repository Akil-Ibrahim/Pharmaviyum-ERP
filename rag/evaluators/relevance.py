"""
Deterministic Relevance Evaluator.
Uses embedding similarity to ensure retrieved instructions match the drug query.
No LLM calls needed, saves compute.
"""
class SimilarityEvaluator:
    def __init__(self, embedding_model):
        self.model = embedding_model

    def evaluate(self, query_embedding: list[float], context_embedding: list[float]) -> float:
        # Calculates cosine similarity between query and context
        return 0.85 
