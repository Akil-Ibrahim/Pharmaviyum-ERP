#!/bin/bash
# Script to collect all Docker logs

echo "Collecting logs..."
docker-compose logs --no-color > all_logs.txt 2>&1
docker-compose logs --no-color backend > backend_logs.txt 2>&1
docker-compose logs --no-color frontend > frontend_logs.txt 2>&1

echo "✅ Logs collected:"
ls -lh *logs.txt
