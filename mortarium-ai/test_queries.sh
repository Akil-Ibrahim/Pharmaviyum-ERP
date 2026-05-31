#!/bin/bash
# Mortarium AI - Quick Validation Tool
# Usage: ./test_queries.sh
# Tests basic connectivity and LangGraph endpoint response.

set -e

BASE_URL="http://localhost:8000"
API_ENDPOINT="${BASE_URL}/api/ask"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}🔍 Checking API Health...${NC}"
if curl -sf "${BASE_URL}/health" > /dev/null; then
    echo -e "${GREEN}✅ API is healthy${NC}"
else
    echo -e "${RED}❌ API is down. Run 'docker compose up -d'${NC}"
    exit 1
fi

# Function to test a query
query() {
    local text=$1
    echo -e "\n${YELLOW}💊 Query:${NC} $text"
    
    # Send request with pretty formatting
    response=$(curl -s -X POST "$API_ENDPOINT" \
        -H "Content-Type: application/json" \
        -d "{\"question\": \"$text\", \"user_id\": \"cli_test\"}")
        
    # Check for error keys in JSON
    if echo "$response" | grep -q "detail"; then
        echo -e "${RED}❌ Error: $response${NC}"
    else
        echo -e "${GREEN}✅ Response received${NC}"
        echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
    fi
}

# Run scenarios
query "Dosage of Amoxicillin for adults"
query "Contraindications for Aspirin"
query "Is Nurofen in stock?"

echo -e "\n${GREEN}✅ Validation complete.${NC}"
