#!/bin/bash
# Integration test script

echo "🧪 Testing Pharmaviyum-CRM Frontend-Backend Integration..."
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check backend
echo "🔍 Checking Backend..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Backend is running${NC}"
    BACKEND_OK=1
else
    echo -e "${RED}✗ Backend is not responding${NC}"
    echo "   Start backend: python -m uvicorn src.pharmaviyum.main:app --reload --port 8000"
    BACKEND_OK=0
fi

# Check frontend
echo "🔍 Checking Frontend..."
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Frontend is running${NC}"
    FRONTEND_OK=1
else
    echo -e "${RED}✗ Frontend is not responding${NC}"
    echo "   Start frontend: cd frontend/shadcn-admin && npm run dev"
    FRONTEND_OK=0
fi

# Check database
echo "🔍 Checking Database..."
if command -v psql &> /dev/null; then
    if psql -h localhost -U app_user -d pharmaviyum -c "SELECT 1" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Database is accessible${NC}"
        DB_OK=1
    else
        echo -e "${RED}✗ Database is not accessible${NC}"
        echo "   Make sure PostgreSQL is running on localhost:5432"
        DB_OK=0
    fi
else
    echo -e "${YELLOW}⚠ psql not installed, skipping database check${NC}"
    DB_OK=1
fi

echo ""

# Test API connectivity
if [ $BACKEND_OK -eq 1 ]; then
    echo "🔗 Testing API Connectivity..."
    
    # Test health endpoint
    RESPONSE=$(curl -s http://localhost:8000/health)
    if echo "$RESPONSE" | grep -q "healthy"; then
        echo -e "${GREEN}✓ Health check passed${NC}"
        echo "   Response: $RESPONSE"
    else
        echo -e "${RED}✗ Health check failed${NC}"
        echo "   Response: $RESPONSE"
    fi
    
    # Test CORS
    CORS_TEST=$(curl -s -i -X OPTIONS http://localhost:8000/api/v1/users \
        -H "Origin: http://localhost:3000" \
        -H "Access-Control-Request-Method: GET" 2>&1)
    
    if echo "$CORS_TEST" | grep -q "Access-Control-Allow-Origin"; then
        echo -e "${GREEN}✓ CORS is enabled${NC}"
    else
        echo -e "${RED}✗ CORS might not be configured${NC}"
    fi
fi

echo ""

# Summary
if [ $BACKEND_OK -eq 1 ] && [ $FRONTEND_OK -eq 1 ] && [ $DB_OK -eq 1 ]; then
    echo -e "${GREEN}✅ All systems operational!${NC}"
    echo ""
    echo "Access your app at: http://localhost:3000"
    exit 0
else
    echo -e "${YELLOW}⚠️  Some services are not running${NC}"
    echo ""
    echo "To start all services:"
    echo "  bash scripts/start-dev.sh"
    echo ""
    echo "Or in Docker:"
    echo "  docker compose up --build"
    exit 1
fi
