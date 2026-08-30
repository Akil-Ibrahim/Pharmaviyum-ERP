#!/bin/bash
# Run All Tests in Docker Isolation
set -e

echo "Running tests in isolated Docker environment..."

docker run -d --name pharmaviyum-test-db \
    -e POSTGRES_USER=postgres \
    -e POSTGRES_PASSWORD=postgres \
    -e POSTGRES_DB=pharmaviyum_test \
    pgvector/pgvector:pg16

sleep 5

docker run --rm \
    --network host \
    -e DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/pharmaviyum_test \
    -v $(pwd):/app \
    -w /app \
    python:3.12-slim \
    bash -c "pip install -r requirements.txt pytest && pytest tests/ -v"

docker stop pharmaviyum-test-db
docker rm pharmaviyum-test-db

echo "Tests complete!"
