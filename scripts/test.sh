#!/bin/bash
# Run All Tests in Docker Isolation
set -e

echo "Running tests in isolated Docker environment..."

# Start test database
docker run -d --name pharmaviyum-test-db \
    -e POSTGRES_USER=postgres \
    -e POSTGRES_PASSWORD=postgres \
    -e POSTGRES_DB=pharmaviyum_test \
    pgvector/pgvector:pg16

sleep 5

# Run tests
docker run --rm \
    --network host \
    -e DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/pharmaviyum_test \
    -v $(pwd)/backend:/app \
    -w /app \
    python:3.12-slim \
    bash -c "pip install -r requirements.txt pytest && pytest tests/ -v"

# Cleanup
docker stop pharmaviyum-test-db
docker rm pharmaviyum-test-db

echo "Tests complete!"
