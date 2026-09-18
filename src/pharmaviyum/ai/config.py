"""AI layer configuration — Pydantic settings."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class OllamaSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="OLLAMA_")
    base_url: str = "http://localhost:11434"
    fast_model: str = "qwen2.5:1.5b"
    main_model: str = "qwen2.5:7b"
    complex_model: str = "qwen2.5:72b"
    embedding_model: str = "mxbai-embed-large"
    reranker_model: str = "bge-reranker-v2-m3"
    timeout_seconds: float = 60.0
    temperature: float = 0.1


class GroqSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="GROQ_")
    api_key: SecretStr | None = None
    model: str = "llama-3.1-70b-versatile"
    fast_model: str = "llama-3.1-8b-instant"
    timeout_seconds: float = 30.0
    temperature: float = 0.1


class OpenAISettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="OPENAI_")
    api_key: SecretStr | None = None
    model: str = "gpt-4o-mini"
    complex_model: str = "gpt-4o"
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1024
    timeout_seconds: float = 30.0
    temperature: float = 0.1


class AnthropicSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ANTHROPIC_")
    api_key: SecretStr | None = None
    model: str = "claude-3-5-sonnet-20241022"
    timeout_seconds: float = 30.0
    temperature: float = 0.1


class RedisSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="REDIS_")
    url: str = "redis://localhost:6379/0"
    cache_ttl_seconds: int = 86400 * 30
    embedding_cache_ttl: int = 86400 * 30
    prompt_cache_ttl: int = 86400 * 7
    memory_ttl: int = 86400 * 7


class PgVectorSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="PGVECTOR_")
    database_url: SecretStr = SecretStr(
        "postgresql+asyncpg://postgres:postgres@localhost:5432/pharmaviyum"
    )
    table_name: str = "document_chunks"
    hnsw_m: int = 16
    hnsw_ef_construction: int = 200
    hnsw_ef_search: int = 100
    vector_dimensions: int = 1024

    @field_validator("database_url")
    @classmethod
    def normalize_database_url(cls, value: SecretStr) -> SecretStr:
        url = value.get_secret_value()
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return SecretStr(url)


class LangSmithSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="LANGSMITH_")
    enabled: bool = False
    api_key: SecretStr | None = None
    project: str = "pharmaviyum-pharmacist-agent"
    endpoint: str | None = None


class OTelSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="OTEL_")
    enabled: bool = True
    exporter_endpoint: str = "http://otel-collector:4317"
    service_name: str = "pharmaviyum-ai"


class RAGSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="RAG_")
    max_chunk_tokens: int = 512
    chunk_overlap: int = 50
    top_k: int = 10
    rerank_top_n: int = 5
    rrf_k: int = 60
    similarity_threshold: float = 0.70
    enable_hyde: bool = True
    enable_multi_query: bool = True
    enable_contextual_compression: bool = True
    default_languages: list[str] = ["vi", "en", "ar", "th", "id"]


class AgentSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AGENT_")
    max_iterations: int = 5
    max_history_messages: int = 10
    summarization_threshold: int = 20
    enable_checkpointer: bool = True
    enable_hitl: bool = True
    safety_score_threshold: float = 0.9
    streaming_timeout_seconds: float = 60.0


class HalalSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="HALAL_")
    default_country: str = "SA"
    default_fiqh: Literal[
        "Hanafi", "Shafii", "Maliki", "Hanbali", "Ja'fari", "Zaydi"
    ] = "Hanbali"
    enable_istihalah_check: bool = True
    enable_darurah_exception: bool = True
    strict_mode: bool = True


class MCPSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MCP_")
    server_name: str = "pharmaviyum-mcp"
    server_version: str = "1.0.0"
    tool_timeout_seconds: float = 30.0
    max_retries: int = 3
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: float = 60.0
    enable_rbac: bool = True
    enable_analytics: bool = True


class AISettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    ollama: OllamaSettings = Field(default_factory=OllamaSettings)
    groq: GroqSettings = Field(default_factory=GroqSettings)
    openai: OpenAISettings = Field(default_factory=OpenAISettings)
    anthropic: AnthropicSettings = Field(default_factory=AnthropicSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    pgvector: PgVectorSettings = Field(default_factory=PgVectorSettings)
    langsmith: LangSmithSettings = Field(default_factory=LangSmithSettings)
    otel: OTelSettings = Field(default_factory=OTelSettings)
    rag: RAGSettings = Field(default_factory=RAGSettings)
    agent: AgentSettings = Field(default_factory=AgentSettings)
    halal: HalalSettings = Field(default_factory=HalalSettings)
    mcp: MCPSettings = Field(default_factory=MCPSettings)

    environment: Literal["development", "staging", "production"] = "development"
    log_level: str = "INFO"
    enable_telemetry: bool = True
    use_cloud_llm: bool = False
    cors_origins: list[str] = Field(default_factory=list)

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        allowed = {"development", "staging", "production"}
        if v not in allowed:
            raise ValueError(f"environment must be one of {allowed}")
        return v


settings = AISettings()
