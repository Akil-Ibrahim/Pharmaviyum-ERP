"""Async pgvector retriever and indexer."""
from typing import List, Dict, Optional
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sqlalchemy import select
from core.db import async_session_factory, PharmacyDocument
from config import settings
import structlog

logger = structlog.get_logger()
embeddings = HuggingFaceEmbeddings(model_name=settings.EMBEDDING_MODEL)

class AsyncPGVectorRetriever:
    async def retrieve(self, query: str, k: int = 5) -> List[Dict]:
        """Semantic search with cosine similarity."""
        query_vec = embeddings.embed_query(query)
        async with async_session_factory() as session:
            stmt = select(PharmacyDocument).order_by(PharmacyDocument.embedding.cosine_distance(query_vec)).limit(k)
            result = await session.execute(stmt)
            docs = result.scalars().all()
        return [{"content": d.content, "metadata": d.metadata_ or {}} for d in docs]

    async def upsert_chunks(self, texts: List[str], metadatas: Optional[List[Dict]] = None):
        """Chunk, embed, and batch-insert into pgvector."""
        splitter = RecursiveCharacterTextSplitter(chunk_size=settings.CHUNK_SIZE, chunk_overlap=settings.CHUNK_OVERLAP)
        chunks = splitter.create_documents(texts, metadatas=metadatas or [{}]*len(texts))
        embeddings_list = embeddings.embed_documents([c.page_content for c in chunks])
        async with async_session_factory() as session:
            for content, emb, meta in zip([c.page_content for c in chunks], embeddings_list, metadatas or [{}]*len(chunks)):
                session.add(PharmacyDocument(content=content, metadata_=meta, embedding=emb))
            await session.commit()
        logger.info("Indexed chunks", count=len(chunks))

retriever = AsyncPGVectorRetriever()
