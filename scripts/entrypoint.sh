#!/bin/bash
# =============================================================================
# PharmaViyum CRM - Backend Entrypoint Script
# =============================================================================
# This script runs before the main application starts.
# It performs necessary setup tasks like database migrations.
#
# Tasks performed:
#   1. Wait for PostgreSQL to be ready
#   2. Run Alembic database migrations
#   3. Start the FastAPI application with Uvicorn
#
# Usage:
#   This script is called automatically by Docker ENTRYPOINT.
#   No manual execution needed.
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}🚀 PharmaViyum CRM - Backend Starting...${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

# =============================================================================
# Step 1: Wait for PostgreSQL to be ready
# =============================================================================
echo -e "${YELLOW} Waiting for PostgreSQL to be ready...${NC}"

# Database connection parameters (from environment variables)
DB_HOST="${POSTGRES_HOST:-postgres}"
DB_PORT="${POSTGRES_PORT:-5432}"
DB_NAME="${POSTGRES_DB:-pharmaviyum}"
DB_USER="${POSTGRES_USER:-postgres}"

# Maximum wait time in seconds
MAX_WAIT=60
WAIT_INTERVAL=2
ELAPSED=0

# Check if pg_isready is available (PostgreSQL client tool)
if command -v pg_isready &> /dev/null; then    # Wait for PostgreSQL to accept connections
    until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" > /dev/null 2>&1; do
        echo -e "${YELLOW}  PostgreSQL not ready yet. Waiting... (${ELAPSED}s/${MAX_WAIT}s)${NC}"
        sleep $WAIT_INTERVAL
        ELAPSED=$((ELAPSED + WAIT_INTERVAL))
        
        if [ $ELAPSED -ge $MAX_WAIT ]; then
            echo -e "${RED}❌ PostgreSQL did not become ready within ${MAX_WAIT} seconds${NC}"
            echo -e "${RED}   Check if the database container is running and healthy${NC}"
            exit 1
        fi
    done
    echo -e "${GREEN}✅ PostgreSQL is ready at ${DB_HOST}:${DB_PORT}${NC}"
else
    echo -e "${YELLOW}⚠️  pg_isready not available, skipping PostgreSQL health check${NC}"
    # Fallback: simple sleep
    sleep 5
fi

echo ""

# =============================================================================
# Step 2: Run Alembic Database Migrations
# =============================================================================
echo -e "${YELLOW}🔄 Running database migrations...${NC}"

# Check if alembic is installed
if command -v alembic &> /dev/null; then
    # Run migrations
    if alembic upgrade head; then
        echo -e "${GREEN}✅ Database migrations completed successfully${NC}"
    else
        echo -e "${RED}❌ Database migrations failed${NC}"
        echo -e "${YELLOW}️  Continuing startup anyway (non-fatal error)${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Alembic not found, skipping migrations${NC}"
    echo -e "${YELLOW}   Install alembic: pip install alembic${NC}"
fi

echo ""

# =============================================================================
# Step 3: Start the FastAPI Application
# =============================================================================
echo -e "${GREEN} Starting FastAPI application...${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

# Determine run mode based on environmentENVIRONMENT="${ENVIRONMENT:-development}"

if [ "$ENVIRONMENT" = "production" ]; then
    # Production mode: use uvicorn with multiple workers
    echo -e "${GREEN}📦 Mode: PRODUCTION${NC}"
    echo -e "${GREEN}   Workers: ${UVICORN_WORKERS:-4}${NC}"
    echo -e "${GREEN}   Host: 0.0.0.0${NC}"
    echo -e "${GREEN}   Port: ${UVICORN_PORT:-8000}${NC}"
    echo ""
    
    exec uvicorn src.pharmaviyum.main:app \
        --host 0.0.0.0 \
        --port "${UVICORN_PORT:-8000}" \
        --workers "${UVICORN_WORKERS:-4}" \
        --log-level "${LOG_LEVEL:-info}" \
        --proxy-headers \
        --forwarded-allow-ips="*"
else
    # Development mode: use uvicorn with hot reload
    echo -e "${GREEN}️  Mode: DEVELOPMENT${NC}"
    echo -e "${GREEN}   Hot reload: enabled${NC}"
    echo -e "${GREEN}   Host: 0.0.0.0${NC}"
    echo -e "${GREEN}   Port: ${UVICORN_PORT:-8000}${NC}"
    echo ""
    
    exec uvicorn src.pharmaviyum.main:app \
        --host 0.0.0.0 \
        --port "${UVICORN_PORT:-8000}" \
        --reload \
        --log-level "${LOG_LEVEL:-debug}"
fi
