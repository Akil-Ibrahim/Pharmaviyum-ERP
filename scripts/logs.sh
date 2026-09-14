#!/bin/bash
# ============================================================================
# View Logs for Pharmaviyum AI Stack
# Usage: ./scripts/logs.sh [service]
# ============================================================================

SERVICE=${1:-api}

echo "📋 Showing logs for: $SERVICE"
echo "Press Ctrl+C to exit"
echo ""

docker-compose logs -f $SERVICE
