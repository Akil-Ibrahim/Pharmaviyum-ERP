#!/bin/bash
# ============================================================================
# Database Migration Helper Script
# Usage: ./scripts/migrate.sh [upgrade|downgrade|current|history]
# ============================================================================

set -e

COMMAND=${1:-upgrade}
REVISION=${2:-head}

echo "🗄️  Running Alembic migration: $COMMAND $REVISION"
echo ""

case $COMMAND in
    upgrade)
        echo "⬆️  Upgrading to $REVISION..."
        alembic upgrade $REVISION
        ;;
    downgrade)
        echo "⬇️  Downgrading to $REVISION..."
        alembic downgrade $REVISION
        ;;
    current)
        echo "📍 Current revision:"
        alembic current
        ;;
    history)
        echo "📜 Migration history:"
        alembic history
        ;;
    heads)
        echo "🎯 Current heads:"
        alembic heads
        ;;
    revision)
        echo "✨ Creating new migration..."
        alembic revision --autogenerate -m "$REVISION"
        ;;
    *)
        echo "❓ Usage: $0 [upgrade|downgrade|current|history|heads|revision] [revision]"
        exit 1
        ;;
esac

echo ""
echo "✅ Migration completed successfully!"
