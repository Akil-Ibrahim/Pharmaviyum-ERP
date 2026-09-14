"""
Multi-language Embedding Strategy for SEA/MENA markets.

Best practice 2026:
- Language-specific model selection (vi/ar/th/id/en)
- Fallback to multilingual-e5-large for mixed content
- Language detection before embedding
- Per-language quality monitoring
"""
from __future__ import annotations
from typing import Any
from langdetect import detect, LangDetectException
from src.pharmaviyum.core.logging import logger


# Optimal embedding models per language (Ollama-compatible)
LANGUAGE_MODEL_MAP: dict[str, dict[str, Any]] = {
    "vi": {
        "model": "multilingual-e5-large",
        "dimensions": 1024,
        "notes": "Vietnamese requires multilingual model (Latin + diacritics)",
        "quality_threshold": 0.85,
    },
    "ar": {
        "model": "multilingual-e5-large",
        "dimensions": 1024,
        "notes": "Arabic script requires RTL-aware multilingual model",
        "quality_threshold": 0.85,
    },
    "th": {
        "model": "multilingual-e5-large",
        "dimensions": 1024,
        "notes": "Thai script (no spaces) needs specialized tokenizer",
        "quality_threshold": 0.80,
    },
    "id": {
        "model": "multilingual-e5-large",
        "dimensions": 1024,
        "notes": "Indonesian/Malay (Latin script, shared with English)",
        "quality_threshold": 0.85,
    },
    "en": {
        "model": "mxbai-embed-large",
        "dimensions": 1024,
        "notes": "English-optimized model (faster, higher quality)",
        "quality_threshold": 0.90,
    },
    "mixed": {
        "model": "multilingual-e5-large",
        "dimensions": 1024,
        "notes": "Fallback for mixed-language content",
        "quality_threshold": 0.80,
    },
}


class MultiLanguageEmbeddingRouter:
    """
    Routes texts to optimal embedding model based on detected language.
    
    Benefits:
    - Higher retrieval accuracy per language
    - Cost optimization (English model is faster)
    - Better handling of SEA/MENA scripts (Arabic, Thai, Vietnamese)
    """
    
    def __init__(self, embeddings_factory):
        """
        Args:
            embeddings_factory: Factory function (language, redis_client) -> EmbeddingsProvider
        """
        self.factory = embeddings_factory
        self._cache: dict[str, Any] = {}
    
    def detect_language(self, text: str) -> str:
        """Detect language of text sample."""
        try:
            if len(text) < 20:
                return "en"
            
            lang = detect(text[:500])
            
            # Map langdetect codes to our codes
            lang_map = {
                "vi": "vi", "ar": "ar", "th": "th",
                "id": "id", "ms": "id",  # Malay → Indonesian
                "en": "en",
            }
            return lang_map.get(lang, "mixed")
        except LangDetectException:
            return "mixed"
    
    def detect_language_batch(self, texts: list[str]) -> list[str]:
        """Detect languages for a batch of texts."""
        return [self.detect_language(t) for t in texts]
    
    def get_model_for_language(self, language: str) -> dict[str, Any]:
        """Get optimal model configuration for a language."""
        return LANGUAGE_MODEL_MAP.get(language, LANGUAGE_MODEL_MAP["mixed"])
    
    def get_embeddings_provider(self, language: str, redis_client=None):
        """Get or create embeddings provider for a language."""
        if language not in self._cache:
            config = self.get_model_for_language(language)
            self._cache[language] = self.factory(
                model=config["model"],
                dimensions=config["dimensions"],
                redis_client=redis_client,
            )
            logger.info(
                f"Initialized embeddings for {language}: {config['model']}",
                extra={"dimensions": config["dimensions"]}
            )
        return self._cache[language]
    
    async def embed_with_language_detection(
        self,
        texts: list[str],
        redis_client=None,
    ) -> tuple[list[list[float]], list[str]]:
        """
        Embed texts with automatic language detection and model routing.
        
        Returns:
            (embeddings, detected_languages)
        """
        languages = self.detect_language_batch(texts)
        
        # Group texts by language
        by_language: dict[str, list[tuple[int, str]]] = {}
        for i, (text, lang) in enumerate(zip(texts, languages)):
            by_language.setdefault(lang, []).append((i, text))
        
        # Embed each group with its optimal model
        embeddings: list[list[float] | None] = [None] * len(texts)
        
        for lang, indexed_texts in by_language.items():
            provider = self.get_embeddings_provider(lang, redis_client)
            texts_for_lang = [t for _, t in indexed_texts]
            
            lang_embeddings = await provider.embed_batch(texts_for_lang)
            
            for (idx, _), emb in zip(indexed_texts, lang_embeddings):
                embeddings[idx] = emb
        
        # All should be filled now
        return [e for e in embeddings if e is not None], languages
    
    def get_quality_threshold(self, language: str) -> float:
        """Get minimum acceptable quality threshold for a language."""
        config = self.get_model_for_language(language)
        return config.get("quality_threshold", 0.80)
