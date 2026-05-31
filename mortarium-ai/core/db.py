from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from pgvector.sqlalchemy import Vector
import redis.asyncio as aioredis
from config import settings
import structlog

logger = structlog.get_logger()
engine = create_async_engine(settings.DATABASE_URL, pool_size=8, max_overflow=2, echo=False)
async_session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
redis_client = aioredis.Redis.from_url(settings.REDIS_URL, decode_responses=True, max_connections=10)
Base = declarative_base()

async def init_db_extensions():
    async with engine.begin() as conn:
        await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
    logger.info("Database extensions initialized")

class PharmacyDocument(Base):
    __tablename__ = "pharmacy_documents"
    id = Base.Column("id", Base.Integer, primary_key=True)
    content = Base.Column("content", Base.Text, nullable=False)
    metadata_ = Base.Column("metadata", Base.JSON, default={})
    embedding = Base.Column("embedding", Vector(384))

async def get_db_session():
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
