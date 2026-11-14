#!/bin/bash
# Generate TypeScript API client from FastAPI OpenAPI spec
set -e
echo "Generating API client..."
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "Backend not running. Start with: docker compose up -d"
    exit 1
fi
cd frontend/shadcn-admin
npx openapi-typescript-codegen \
    --input http://localhost:8000/openapi.json \
    --output ./src/client \
    --client axios \
    --name PharmaviyumClient
echo "Client generated in frontend/shadcn-admin/src/client/"
