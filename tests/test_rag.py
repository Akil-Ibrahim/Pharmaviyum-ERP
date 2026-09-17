"""
Tests for RAG pipeline components.

Tests cover:
- Document preprocessing
- Chunking strategies
- Embedding generation
- Vector store operations
- Query transformation
"""

from unittest.mock import AsyncMock

import pytest


@pytest.mark.unit
class TestDocumentPreprocessing:
    """Test document preprocessing pipeline."""

    def test_text_normalization(self):
        """Test text normalization removes extra whitespace."""
        from src.pharmaviyum.ai.mortarium_rag.preprocessing import TextNormalizer

        text = "This   has   extra   spaces\n\n\nand newlines"
        normalized = TextNormalizer.normalize(text)

        assert "   " not in normalized
        assert "\n\n\n" not in normalized
        assert normalized.strip() == normalized

    def test_pii_redaction_email(self):
        """Test PII redaction removes email addresses."""
        from src.pharmaviyum.ai.mortarium_rag.preprocessing import PIIRedactor

        text = "Contact us at test@example.com for more info"
        redacted, types = PIIRedactor.redact(text)

        assert "test@example.com" not in redacted
        assert "[REDACTED_EMAIL]" in redacted
        assert "email" in types

    def test_pii_redaction_phone(self):
        """Test PII redaction removes phone numbers."""
        from src.pharmaviyum.ai.mortarium_rag.preprocessing import PIIRedactor

        text = "Call +84-123-456-789 for assistance"
        redacted, types = PIIRedactor.redact(text)

        assert "+84-123-456-789" not in redacted
        assert "phone" in types

    def test_metadata_extraction_language(self):
        """Test metadata extraction detects language."""
        from src.pharmaviyum.ai.mortarium_rag.preprocessing import MetadataExtractor

        text = "Thuốc paracetamol được sử dụng để giảm đau và hạ sốt"
        metadata = MetadataExtractor.extract(text, {})

        assert metadata.get("language") == "vi"

    def test_content_hash_generation(self):
        """Test content hash is generated for deduplication."""
        from src.pharmaviyum.ai.mortarium_rag.preprocessing import DocumentPreprocessor
        from src.pharmaviyum.ai.mortarium_rag.schemas import Document

        preprocessor = DocumentPreprocessor(enable_pii_redaction=False)
        doc = Document(
            id="test-1",
            content="Test content for hashing",
            source="test.pdf",
            doc_type="drug_info",
            metadata={},
            country="VN",
            language="en",
        )

        processed = preprocessor.process(doc)
        assert "content_hash" in processed.metadata
        assert len(processed.metadata["content_hash"]) == 64


@pytest.mark.unit
class TestMedicalChunker:
    """Test medical-aware chunking."""

    def test_basic_chunking(self):
        """Test basic text chunking respects token limits."""
        from src.pharmaviyum.ai.mortarium_rag.chunking import MedicalChunker
        from src.pharmaviyum.ai.mortarium_rag.schemas import Document

        chunker = MedicalChunker(max_tokens=100, overlap=20)

        long_text = "This is a test sentence. " * 50
        doc = Document(
            id="test-1",
            content=long_text,
            source="test.pdf",
            doc_type="drug_info",
            metadata={},
            country="VN",
            language="en",
        )

        chunks = chunker.chunk(doc, strategy="basic")

        assert len(chunks) > 1
        assert all(len(chunk.content) > 0 for chunk in chunks)

    def test_medical_section_detection(self):
        """Test chunking detects medical sections."""
        from src.pharmaviyum.ai.mortarium_rag.chunking import MedicalChunker
        from src.pharmaviyum.ai.mortarium_rag.schemas import Document

        chunker = MedicalChunker(max_tokens=200, overlap=50)

        content = """
        INDICATIONS:
        Paracetamol is used for pain relief.
        
        DOSAGE:
        Adults: 500mg every 4-6 hours.
        
        CONTRAINDICATIONS:
        Do not use if allergic to paracetamol.
        """

        doc = Document(
            id="test-1",
            content=content,
            source="test.pdf",
            doc_type="drug_info",
            metadata={},
            country="VN",
            language="en",
        )

        chunks = chunker.chunk(doc, strategy="medical")
        assert len(chunks) > 0


@pytest.mark.unit
class TestEmbeddings:
    """Test embedding generation."""

    @pytest.mark.asyncio
    async def test_ollama_embeddings(self, mock_redis):
        """Test Ollama embedding generation."""
        from src.pharmaviyum.ai.mortarium_rag.embeddings import OllamaEmbeddings

        embeddings = OllamaEmbeddings(
            model="mxbai-embed-large",
            base_url="http://localhost:11434",
            dimensions=1024,
            redis_client=mock_redis,
        )

        embeddings.client = AsyncMock()
        embeddings.client.embed = AsyncMock(return_value=[[0.1] * 1024])

        result = await embeddings.embed("Test text")

        assert len(result) == 1024
        assert all(isinstance(x, float) for x in result)

    @pytest.mark.asyncio
    async def test_embedding_cache(self, mock_redis):
        """Test embedding cache prevents redundant API calls."""
        from src.pharmaviyum.ai.mortarium_rag.embeddings import CachedEmbeddings

        base_provider = AsyncMock()
        base_provider.embed = AsyncMock(return_value=[0.1] * 1024)
        base_provider.dimensions = 1024

        cached = CachedEmbeddings(
            base_provider=base_provider,
            redis_client=mock_redis,
            ttl_seconds=3600,
        )

        result1 = await cached.embed("Test text")
        assert len(result1) == 1024

        import json

        mock_redis.get.return_value = json.dumps([0.1] * 1024)

        result2 = await cached.embed("Test text")
        assert len(result2) == 1024
        assert base_provider.embed.call_count == 1


@pytest.mark.unit
class TestQueryTransformer:
    """Test query transformation techniques."""

    @pytest.mark.asyncio
    async def test_hyde_transformation(self, mock_ollama_llm):
        """Test HyDE generates hypothetical document."""
        from src.pharmaviyum.ai.mortarium_rag.query_transformer import QueryTransformer

        transformer = QueryTransformer(llm=mock_ollama_llm)

        result = await transformer.transform_with_hyde(
            query="What is Paracetamol?", context={"language": "en"}
        )

        assert result.transformation_type == "hyde"
        assert len(result.transformed_query) > 0

    @pytest.mark.asyncio
    async def test_multi_query_generation(self, mock_ollama_llm):
        """Test multi-query generates variations."""
        from src.pharmaviyum.ai.mortarium_rag.query_transformer import QueryTransformer

        transformer = QueryTransformer(llm=mock_ollama_llm)

        variations = await transformer.generate_multi_query(
            query="Drug interactions between Warfarin and Aspirin",
            num_variations=3,
            context={"language": "en"},
        )

        assert len(variations) > 0
        assert all(
            v.original_query == "Drug interactions between Warfarin and Aspirin"
            for v in variations
        )
