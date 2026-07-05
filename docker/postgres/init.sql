-- ============================================================================
-- PostgreSQL Initialization Script
-- Best practice 2026: Enable required extensions
-- ============================================================================

-- Enable pgvector for AI embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable full-text search
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Create indexes for performance (will be expanded by Alembic migrations)
-- These are just examples, actual indexes created by migrations

-- Log initialization
DO $$
BEGIN
    RAISE NOTICE 'Pharmaviyum database initialized successfully';
END $$;
