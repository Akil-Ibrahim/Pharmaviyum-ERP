"""Contextual compression for the RAG pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.pharmaviyum.ai.llm_utils import response_text
from src.pharmaviyum.core.logging import logger

from .schemas import RetrievalResult


@dataclass
class CompressedContext:
    """Compressed context ready for LLM consumption."""

    compressed_text: str
    original_chunks: int
    compressed_chunks: int
    sentences_kept: int
    sentences_removed: int
    tokens_saved_estimate: int
    reordering_applied: bool


class ContextualCompressor:
    """Compress retrieved evidence while preserving deterministic citation IDs."""

    def __init__(
        self,
        llm,
        max_sentences_per_chunk: int = 3,
        relevance_threshold: float = 0.5,
        enable_lost_in_middle_mitigation: bool = True,
    ):
        self.llm = llm
        self.max_sentences = max_sentences_per_chunk
        self.threshold = relevance_threshold
        self.enable_lim = enable_lost_in_middle_mitigation

    async def compress(
        self,
        query: str,
        retrieved: list[RetrievalResult],
        context: dict[str, Any] | None = None,
    ) -> CompressedContext:
        if not retrieved:
            return CompressedContext("", 0, 0, 0, 0, 0, False)

        context = context or {}
        language = context.get("language", "en")
        compressed_results = []
        total_sentences_kept = 0
        total_sentences_removed = 0
        original_tokens = 0
        compressed_tokens = 0

        for result in retrieved:
            original_tokens += len(result.chunk.content) // 4
            sentences = self._split_sentences(result.chunk.content)
            if len(sentences) <= self.max_sentences:
                compressed_results.append((result, result.chunk.content))
                total_sentences_kept += len(sentences)
                compressed_tokens += len(result.chunk.content) // 4
                continue

            scored_sentences = await self._score_sentences(query, sentences, language)
            filtered = [
                (sentence, score)
                for sentence, score in scored_sentences
                if score >= self.threshold
            ][: self.max_sentences]
            if not filtered:
                filtered = scored_sentences[:2]
            compressed_content = " ".join(sentence for sentence, _ in filtered)
            compressed_results.append((result, compressed_content))
            total_sentences_kept += len(filtered)
            total_sentences_removed += len(sentences) - len(filtered)
            compressed_tokens += len(compressed_content) // 4

        if self.enable_lim and len(compressed_results) > 2:
            compressed_results = self._apply_lost_in_middle_ordering(compressed_results)
            reordering_applied = True
        else:
            reordering_applied = False

        compressed_text = self._build_compressed_text(compressed_results)
        tokens_saved = original_tokens - compressed_tokens
        return CompressedContext(
            compressed_text=compressed_text,
            original_chunks=len(retrieved),
            compressed_chunks=len(compressed_results),
            sentences_kept=total_sentences_kept,
            sentences_removed=total_sentences_removed,
            tokens_saved_estimate=tokens_saved,
            reordering_applied=reordering_applied,
        )

    async def _score_sentences(
        self, query: str, sentences: list[str], language: str
    ) -> list[tuple[str, float]]:
        sentences_text = "\n".join(
            f"[{i}] {sentence}" for i, sentence in enumerate(sentences)
        )
        lang_instruction = {
            "vi": "Trả lời bằng tiếng Việt.",
            "ar": "أجب باللغة العربية.",
            "th": "ตอบเป็นภาษาไทย.",
            "id": "Jawab dalam bahasa Indonesia.",
            "en": "Answer in English.",
        }.get(language, "Answer in English.")
        prompt = f"""You are a relevance scoring assistant.
{lang_instruction}

Rate each sentence's relevance to the query from 0.0 to 1.0.
Query: {query}

Sentences:
{sentences_text}

Return a JSON array of [sentence_index, score] pairs, sorted by score descending.
JSON:"""
        try:
            response = await self.llm.ainvoke(prompt)
            import json
            import re

            json_match = re.search(r"\[.*\]", response_text(response), re.DOTALL)
            if not json_match:
                raise ValueError("No JSON array found in response")
            scores = json.loads(json_match.group())
            scored = []
            for idx, score in scores:
                if 0 <= idx < len(sentences):
                    scored.append((sentences[idx], float(score)))
            scored.sort(key=lambda item: item[1], reverse=True)
            return scored
        except Exception as exc:
            logger.warning("Sentence scoring failed: %s", exc)
            return self._fallback_scoring(query, sentences)

    @staticmethod
    def _fallback_scoring(query: str, sentences: list[str]) -> list[tuple[str, float]]:
        query_words = set(query.lower().split())
        scored = []
        for sentence in sentences:
            sentence_words = set(sentence.lower().split())
            overlap = len(query_words & sentence_words)
            score = overlap / max(len(query_words), 1)
            scored.append((sentence, min(score, 1.0)))
        scored.sort(key=lambda item: item[1], reverse=True)
        return scored

    @staticmethod
    def _split_sentences(text: str) -> list[str]:
        import re

        pattern = r"(?<=[.!?។])\s+(?=[A-ZА-Я\u0400-\u04FF\u1000-\u109F\u0600-\u06FF])"
        return [
            s.strip()
            for s in re.split(pattern, text)
            if s.strip() and len(s.strip()) > 10
        ]

    @staticmethod
    def _apply_lost_in_middle_ordering(
        results: list[tuple[RetrievalResult, str]],
    ) -> list[tuple[RetrievalResult, str]]:
        sorted_results = sorted(results, key=lambda item: item[0].score, reverse=True)
        reordered = []
        left = 0
        right = len(sorted_results) - 1
        while left <= right:
            reordered.append(sorted_results[left])
            left += 1
            if left <= right:
                reordered.append(sorted_results[right])
                right -= 1
        return reordered

    @staticmethod
    def _build_compressed_text(
        results: list[tuple[RetrievalResult, str]],
    ) -> str:
        parts = []
        for result, compressed_content in results:
            citation_id = f"src-{result.chunk.id}"
            source = result.chunk.metadata.get("source", "unknown")
            version = result.chunk.metadata.get("version")
            chunk_type = result.chunk.chunk_type
            version_text = f", Version: {version}" if version else ""
            parts.append(
                f"[{citation_id}] (Source: {source}, Type: {chunk_type}{version_text})\n"
                f"{compressed_content}\n"
            )
        return "\n".join(parts)
