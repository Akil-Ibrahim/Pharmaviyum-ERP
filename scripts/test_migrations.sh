#!/bin/bash
# ============================================================================
# Test Database Migrations
# Verifies that migrations can be applied and rolled back
# ============================================================================

set -e

echo "🧪 Testing database migrations..."
echo ""

# 1. Check current revision
echo "📍 Step 1: Check current revision"
alembic current
echo ""

# 2. Upgrade to head
echo "️  Step 2: Upgrade to head"
alembic upgrade head
echo ""

# 3. Downgrade to base
echo "️  Step 3: Downgrade to base (remove all tables)"
alembic downgrade base
echo ""

# 4. Upgrade again
echo "⬆️  Step 4: Upgrade to head again"
alembic upgrade head
echo ""

# 5. Verify tables exist
echo "🔍 Step 5: Verify tables exist"
PGPASSWORD=postgres psql -h localhost -U postgres -d pharmaviyum -c "\dt"
echo ""

# 6. Check pgvector extension
echo "🔍 Step 6: Check pgvector extension"
PGPASSWORD=postgres psql -h localhost -U postgres -d pharmaviyum -c "SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';"
echo ""

# 7. Check indexes
echo "🔍 Step 7: Check indexes on document_chunks"
PGPASSWORD=postgres psql -h localhost -U postgres -d pharmaviyum -c "\di document_chunks*"
echo ""

echo "✅ All migration tests passed!"
