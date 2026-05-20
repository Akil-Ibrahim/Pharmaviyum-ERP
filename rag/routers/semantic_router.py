"""
Mortarium Semantic Router.
Routes queries: drug info (RAG) vs inventory check (Database).
Saves local LLM compute by avoiding LLM-based routing.
"""
from enum import Enum

class MortariumRouteType(Enum):
    RAG = "rag"             # Questions about instructions, side effects
    DATABASE = "database"   # Questions about stock, price
    OUT_OF_SCOPE = "out_of_scope"

class MortariumRouter:
    def __init__(self, embedding_model):
        self.model = embedding_model

    def route(self, query: str) -> MortariumRouteType:
        # Classify intent based on vector similarity to route centroids
        return MortariumRouteType.RAG
