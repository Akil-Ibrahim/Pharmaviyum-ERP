"""
Contextual Compression for RAG Pipeline.

Best practice 2026:
- Extract only relevant sentences from retrieved chunks (save tokens)
- Lost-in-the-Middle mitigation: reorder documents so most relevant are first/last
- LLM-based relevance scoring per sentence
- Configurable compression ratio
"""
from __future__ import annotations
from typing import Any
from dataclasses import dataclass
from .schemas import RetrievalResult
from src.pharmaviyum.core.logging import logger


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
    """
    Compresses retrieved context before sending to LLM.
    
    Pipeline:
    1. Split each chunk into sentences
    2. Score each sentence for relevance to query
    3. Keep only top-N sentences per chunk
    4. Reorder chunks using Lost-in-the-Middle strategy
    5. Return compressed context
    """
    
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
        """
        Compress retrieved context for LLM consumption.
        
        Args:
            query: Original user query
            retrieved: List of retrieved chunks
            context: Optional context (language, etc.)
        
        Returns:
            CompressedContext with optimized text for LLM
        """
        if not retrieved:
            return CompressedContext(
                compressed_text="",
                original_chunks=0,
                compressed_chunks=0,
                sentences_kept=0,
                sentences_removed=0,
                tokens_saved_estimate=0,
                reordering_applied=False,
            )
        
        context = context or {}
        language = context.get("language", "en")
        
        # Step 1: Compress each chunk
        compressed_results = []
        total_sentences_kept = 0
        total_sentences_removed = 0
        original_tokens = 0
        compressed_tokens = 0
        
        for result in retrieved:
            original_tokens += len(result.chunk.content) // 4
            
            # Split into sentences
            sentences = self._split_sentences(result.chunk.content)
            
            if len(sentences) <= self.max_sentences:
                # Already small enough, keep as-is
                compressed_results.append((result, result.chunk.content))
                total_sentences_kept += len(sentences)
                compressed_tokens += len(result.chunk.content) // 4
                continue
            
            # Score sentences for relevance
            scored_sentences = await self._score_sentences(query, sentences, language)
            
            # Filter by threshold and take top-N
            filtered = [
                (s, score) for s, score in scored_sentences 
                if score >= self.threshold
            ][:self.max_sentences]
            
            if not filtered:
                # If nothing passes threshold, keep top 2 by score
                filtered = scored_sentences[:2]
            
            # Reconstruct compressed chunk
            compressed_content = " ".join([s for s, _ in filtered])
            compressed_results.append((result, compressed_content))
            
            total_sentences_kept += len(filtered)
            total_sentences_removed += len(sentences) - len(filtered)
            compressed_tokens += len(compressed_content) // 4
        
        # Step 2: Lost-in-the-Middle mitigation
        if self.enable_lim and len(compressed_results) > 2:
            compressed_results = self._apply_lost_in_middle_ordering(compressed_results)
            reordering_applied = True
        else:
            reordering_applied = False
        
        # Step 3: Build final compressed text
        compressed_text = self._build_compressed_text(compressed_results)
        
        tokens_saved = original_tokens - compressed_tokens
        
        logger.info(
            f"Context compression: {len(retrieved)} chunks → {len(compressed_results)} chunks, "
            f"saved ~{tokens_saved} tokens",
            extra={
                "sentences_kept": total_sentences_kept,
                "sentences_removed": total_sentences_removed,
                "tokens_saved": tokens_saved,
                "reordering_applied": reordering_applied,
            }
        )
        
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
        self,
        query: str,
        sentences: list[str],
        language: str,
    ) -> list[tuple[str, float]]:
        """
        Score each sentence for relevance to query using LLM.
        
        Returns:
            List of (sentence, score) tuples, sorted by score descending
        """
        # For efficiency, batch sentences and use structured output
        sentences_text = "\n".join([f"[{i}] {s}" for i, s in enumerate(sentences)])
        
        lang_instruction = {
            "vi": "Trả lời bằng tiếng Việt.",
            "ar": "أجب باللغة العربية.",
            "th": "ตอบเป็นภาษาไทย.",
            "id": "Jawab dalam bahasa Indonesia.",
            "en": "Answer in English.",
        }.get(language, "Answer in English.")
        
        prompt = f"""You are a relevance scoring assistant.
{lang_instruction}

Rate each sentence's relevance to the query on a scale from 0.0 to 1.0.
- 1.0 = directly answers the query
- 0.7 = contains relevant information
- 0.3 = tangentially related
- 0.0 = irrelevant

Query: {query}

Sentences:
{sentences_text}

Return a JSON array of [sentence_index, score] pairs, sorted by score descending.
Example: [[2, 0.95], [0, 0.7], [1, 0.3]]

JSON:"""
        
        try:
            response = await self.llm.ainvoke(prompt)
            import json
            import re
            
            # Extract JSON from response
            json_match = re.search(r'\[.*\]', response.content, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON array found in response")
            
            scores = json.loads(json_match.group())
            
            # Build scored sentences list
            scored = []
            for idx, score in scores:
                if 0 <= idx < len(sentences):
                    scored.append((sentences[idx], float(score)))
            
            # Sort by score descending
            scored.sort(key=lambda x: x[1], reverse=True)
            return scored
            
        except Exception as e:
            logger.warning(f"Sentence scoring failed: {e}, using fallback")
            # Fallback: simple keyword overlap scoring
            return self._fallback_scoring(query, sentences)
    
    def _fallback_scoring(
        self,
        query: str,
        sentences: list[str],
    ) -> list[tuple[str, float]]:
        """Fallback scoring using keyword overlap."""
        query_words = set(query.lower().split())
        scored = []
        
        for sentence in sentences:
            sentence_words = set(sentence.lower().split())
            overlap = len(query_words & sentence_words)
            score = overlap / max(len(query_words), 1)
            scored.append((sentence, min(score, 1.0)))
        
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored
    
    def _split_sentences(self, text: str) -> list[str]:
        """Split text into sentences (multi-language aware)."""
        import re
        # Handle multiple sentence endings including Arabic/Thai
        pattern = r'(?<=[.!?។])\s+(?=[A-ZА-Я\u0400-\u04FF\u1000-\u109F\u0600-\u06FF])'
        sentences = re.split(pattern, text)
        return [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]
    
    def _apply_lost_in_middle_ordering(
        self,
        results: list[tuple[RetrievalResult, str]],
    ) -> list[tuple[RetrievalResult, str]]:
        """
        Lost-in-the-Middle mitigation.
        
        Research shows LLMs pay most attention to:
        - First items in context
        - Last items in context
        - Least attention to middle items
        
        Strategy: Place most relevant at start and end, less relevant in middle.
        """
        if len(results) <= 2:
            return results
        
        # Sort by retrieval score (highest first)
        sorted_results = sorted(
            results,
            key=lambda x: x[0].score,
            reverse=True,
        )
        
        # Interleave: best → worst → second-best → second-worst → ...
        reordered = []
        left = 0
        right = len(sorted_results) - 1
        
        while left <= right:
            reordered.append(sorted_results[left])
            left += 1
            if left <= right:
                reordered.append(sorted_results[right])
                right -= 1
        
        logger.debug(f"Applied Lost-in-the-Middle reordering to {len(results)} chunks")
        return reordered
    
    def _build_compressed_text(
        self,
        results: list[tuple[RetrievalResult, str]],
    ) -> str:
        """Build final compressed text with source citations."""
        parts = []
        
        for i, (result, compressed_content) in enumerate(results, 1):
            source = result.chunk.metadata.get("source", "unknown")
            chunk_type = result.chunk.chunk_type
            
            parts.append(
                f"[{i}] (Source: {source}, Type: {chunk_type})\n"
                f"{compressed_content}\n"
            )
        
        return "\n".join(parts)
