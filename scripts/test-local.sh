#!/bin/bash
# Run tests locally with coverage report
set -e

cd backend
pip install pytest pytest-asyncio pytest-cov

pytest tests/ \
    --cov=app \
    --cov-report=html \
    --cov-report=term-missing \
    -v

echo "Coverage report: htmlcov/index.html"
