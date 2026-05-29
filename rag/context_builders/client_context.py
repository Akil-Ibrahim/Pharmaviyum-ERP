# rag/context_builders/client_context.py - Builds prompt for Mortarium AI
from typing import Optional
from src.pharmaviyum.models.client import Client

class ClientContextBuilder:
    """Builds medical context from Client data for RAG recommendations"""

    @staticmethod
    def build_prompt(client: Client) -> str:
        """Returns a structured prompt for Mortarium AI"""
        parts = []
        parts.append(f"Patient: {client.full_name}")
        
        if client.birth_date:
            parts.append(f"Birth date: {client.birth_date}")
        
        if client.chronic_diseases:
            parts.append(f"Chronic conditions: {client.chronic_diseases}")
        
        if client.allergies:
            parts.append(f"Allergies: {client.allergies}")
        
        if client.regular_medications:
            parts.append(f"Regular medications: {client.regular_medications}")
        
        parts.append("\nQuestion: Based on this patient's medical profile, what pharmacy products, OTC medications, or supplements can be safely recommended? Consider potential interactions and contraindications.")
        
        return "\n".join(parts)

    @staticmethod
    def build_short_context(client: Client) -> str:
        """Compact version for quick queries"""
        ctx = []
        if client.chronic_diseases:
            ctx.append(f"dx:{client.chronic_diseases}")
        if client.allergies:
            ctx.append(f"all:{client.allergies}")
        if client.regular_medications:
            ctx.append(f"rx:{client.regular_medications}")
        return "; ".join(ctx) if ctx else "No medical history"
