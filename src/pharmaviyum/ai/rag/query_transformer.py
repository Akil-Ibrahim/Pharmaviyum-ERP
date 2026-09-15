"""
Query Transformation for Enhanced Retrieval.

Best practice 2026:
- HyDE (Hypothetical Document Embeddings): LLM generates hypothetical answer,
  then we embed that instead of the raw query → better semantic match
- Multi-query retrieval: Generate multiple query variations → union of results
- Query decomposition: Break complex queries into sub-queries
- Language-aware transformations for SEA/MENA markets
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel

from src.pharmaviyum.core.logging import logger


class QueryVariation(BaseModel):
    """A transformed version of the original query."""

    original_query: str
    transformed_query: str
    transformation_type: Literal["hyde", "multi_query", "decomposition", "original"]
    language: str = "en"
    confidence: float = 1.0


class QueryTransformer:
    """
    Transforms user queries to improve retrieval quality.

    Strategies:
    1. HyDE: Generate hypothetical document, embed it instead of query
    2. Multi-query: Generate 2-3 variations (synonyms, rephrasing)
    3. Decomposition: Split complex queries into sub-queries
    """

    def __init__(self, llm):
        """
        Args:
            llm: LLM instance for query generation (can be fast model like Qwen 1.5B)
        """
        self.llm = llm

    async def transform_with_hyde(
        self,
        query: str,
        context: dict[str, Any] | None = None,
    ) -> QueryVariation:
        """
        HyDE: Generate hypothetical document that answers the query,
        then use that document's embedding for retrieval.

        Why it works:
        - Query: "What is the dosage of Paracetamol?"
        - HyDE doc: "Paracetamol dosage for adults is 500mg-1000mg every 4-6 hours..."
        - The HyDE doc embedding is closer to actual documents than query embedding
        """
        context = context or {}
        language = context.get("language", "en")

        # Language-specific prompt
        lang_instruction = {
            "vi": "Trả lời bằng tiếng Việt.",
            "ar": "أجب باللغة العربية.",
            "th": "ตอบเป็นภาษาไทย.",
            "id": "Jawab dalam bahasa Indonesia.",
            "en": "Answer in English.",
        }.get(language, "Answer in English.")

        prompt = f"""You are a pharmaceutical knowledge assistant.
{lang_instruction}

Generate a brief, factual paragraph (2-3 sentences) that would answer this question.
Do NOT say "I don't know" — make your best educated guess based on pharmaceutical knowledge.

Question: {query}

Hypothetical answer:"""

        try:
            response = await self.llm.ainvoke(prompt)
            hypothetical_doc = response.content.strip()

            logger.debug(
                f"HyDE transformation: {query[:50]}... → {hypothetical_doc[:80]}..."
            )

            return QueryVariation(
                original_query=query,
                transformed_query=hypothetical_doc,
                transformation_type="hyde",
                language=language,
                confidence=0.85,
            )
        except Exception as e:
            logger.warning(f"HyDE transformation failed: {e}")
            # Fallback to original query
            return QueryVariation(
                original_query=query,
                transformed_query=query,
                transformation_type="original",
                language=language,
                confidence=1.0,
            )

    async def generate_multi_query(
        self,
        query: str,
        num_variations: int = 3,
        context: dict[str, Any] | None = None,
    ) -> list[QueryVariation]:
        """
        Generate multiple query variations to improve recall.

        Example:
        - Original: "drug interactions between Warfarin and Aspirin"
        - Variation 1: "Warfarin Aspirin interaction risks"
        - Variation 2: "Can I take Warfarin with Aspirin safely?"
        - Variation 3: "Warfarin and Aspirin combined effects"
        """
        context = context or {}
        language = context.get("language", "en")

        lang_instruction = {
            "vi": "Viết bằng tiếng Việt.",
            "ar": "اكتب باللغة العربية.",
            "th": "เขียนเป็นภาษาไทย.",
            "id": "Tulis dalam bahasa Indonesia.",
            "en": "Write in English.",
        }.get(language, "Write in English.")

        prompt = f"""You are a query optimization assistant for pharmaceutical search.
{lang_instruction}

Generate {num_variations} different ways to ask the same question.
Each variation should use different wording, synonyms, or sentence structure.
Keep the medical meaning identical.

Original question: {query}

Generate {num_variations} variations (one per line, no numbering):"""

        try:
            response = await self.llm.ainvoke(prompt)
            variations_text = response.content.strip().split("\n")

            variations = [
                QueryVariation(
                    original_query=query,
                    transformed_query=v.strip(),
                    transformation_type="multi_query",
                    language=language,
                    confidence=0.9,
                )
                for v in variations_text[:num_variations]
                if v.strip()
            ]

            # Always include original
            variations.insert(
                0,
                QueryVariation(
                    original_query=query,
                    transformed_query=query,
                    transformation_type="original",
                    language=language,
                    confidence=1.0,
                ),
            )

            logger.debug(f"Generated {len(variations)} query variations")
            return variations

        except Exception as e:
            logger.warning(f"Multi-query generation failed: {e}")
            return [
                QueryVariation(
                    original_query=query,
                    transformed_query=query,
                    transformation_type="original",
                    language=language,
                    confidence=1.0,
                )
            ]

    async def decompose_query(
        self,
        query: str,
        context: dict[str, Any] | None = None,
    ) -> list[QueryVariation]:
        """
        Decompose complex queries into sub-queries.

        Example:
        - Original: "What are the interactions between Warfarin and Aspirin, and what are the alternatives?"
        - Sub-query 1: "Warfarin Aspirin drug interactions"
        - Sub-query 2: "Warfarin Aspirin alternatives"
        """
        context = context or {}
        language = context.get("language", "en")

        # Only decompose if query is complex (contains "and", "or", multiple questions)
        if not any(
            kw in query.lower() for kw in [" and ", " or ", " also ", " additionally "]
        ):
            return [
                QueryVariation(
                    original_query=query,
                    transformed_query=query,
                    transformation_type="original",
                    language=language,
                    confidence=1.0,
                )
            ]

        lang_instruction = {
            "vi": "Viết bằng tiếng Việt.",
            "ar": "اكتب باللغة العربية.",
            "th": "เขียนเป็นภาษาไทย.",
            "id": "Tulis dalam bahasa Indonesia.",
            "en": "Write in English.",
        }.get(language, "Write in English.")

        prompt = f"""You are a query decomposition assistant.
{lang_instruction}

Break this complex question into 2-3 simpler sub-questions.
Each sub-question should be answerable independently.

Complex question: {query}

Sub-questions (one per line, no numbering):"""

        try:
            response = await self.llm.ainvoke(prompt)
            subqueries_text = response.content.strip().split("\n")

            subqueries = [
                QueryVariation(
                    original_query=query,
                    transformed_query=sq.strip(),
                    transformation_type="decomposition",
                    language=language,
                    confidence=0.85,
                )
                for sq in subqueries_text[:3]
                if sq.strip()
            ]

            logger.debug(f"Decomposed query into {len(subqueries)} sub-queries")
            return subqueries

        except Exception as e:
            logger.warning(f"Query decomposition failed: {e}")
            return [
                QueryVariation(
                    original_query=query,
                    transformed_query=query,
                    transformation_type="original",
                    language=language,
                    confidence=1.0,
                )
            ]
