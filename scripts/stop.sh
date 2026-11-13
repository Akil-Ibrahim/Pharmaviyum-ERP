#!/bin/bash
# ============================================================================
# Stop Pharmaviyum AI Stack
# ============================================================================

echo "🛑 Stopping Pharmaviyum AI Stack..."
docker-compose down

echo ""
echo "✅ All services stopped."
echo ""
echo "💡 To remove volumes (delete all data):"
echo "  docker-compose down -v"
