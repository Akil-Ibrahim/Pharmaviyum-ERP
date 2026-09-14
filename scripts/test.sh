#!/bin/bash
# ============================================================================
# Run Test Suite
# Usage: ./scripts/test.sh [unit|integration|all|coverage]
# ============================================================================

set -e

COMMAND=${1:-unit}

echo "🧪 Running tests: $COMMAND"
echo ""

case $COMMAND in
    unit)
        echo "📦 Running unit tests..."
        pytest tests/ -m unit -v
        ;;
    integration)
        echo "🔗 Running integration tests..."
        pytest tests/ -m integration -v
        ;;
    all)
        echo " Running all tests..."
        pytest tests/ -v
        ;;
    coverage)
        echo "📊 Running tests with coverage..."
        pytest tests/ --cov=src.pharmaviyum --cov-report=html --cov-report=term -v
        echo ""
        echo "📄 Coverage report: htmlcov/index.html"
        ;;
    *)
        echo "❓ Usage: $0 [unit|integration|all|coverage]"
        exit 1
        ;;
esac

echo ""
echo "✅ Tests completed!"
