-- Initialize PostgreSQL with pgvector extension
-- Runs automatically on first container start

-- Enable pgvector extension for semantic search
CREATE EXTENSION IF NOT EXISTS vector;

-- Create table for pharmacy documents
CREATE TABLE IF NOT EXISTS pharmacy_documents (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    embedding vector(384)
);

-- Create index for efficient cosine similarity search
CREATE INDEX IF NOT EXISTS idx_pharmacy_documents_embedding 
ON pharmacy_documents 
USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE mortarium_db TO postgres;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
