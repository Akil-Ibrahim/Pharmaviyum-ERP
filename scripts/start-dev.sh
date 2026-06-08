#!/bin/bash
# Quick start script for Pharmaviyum-CRM frontend and backend

set -e

echo "🚀 Starting Pharmaviyum-CRM..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is required but not installed.${NC}"
    exit 1
fi

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js is required but not installed.${NC}"
    exit 1
fi

# Check if venv exists, create if not
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}📦 Creating Python virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate venv
source venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"

# Install Python dependencies if needed
if [ ! -f "venv/lib/python*/site-packages/fastapi" ]; then
    echo -e "${YELLOW}📦 Installing Python dependencies...${NC}"
    pip install -q -r requirements.txt
    echo -e "${GREEN}✓ Python dependencies installed${NC}"
fi

# Check frontend dependencies
if [ ! -d "frontend/shadcn-admin/node_modules" ]; then
    echo -e "${YELLOW}📦 Installing frontend dependencies...${NC}"
    cd frontend/shadcn-admin
    npm install
    cd ../..
    echo -e "${GREEN}✓ Frontend dependencies installed${NC}"
fi

echo -e "${GREEN}✅ Setup complete!${NC}"
echo ""
echo -e "${YELLOW}🎯 Starting services...${NC}"
echo ""
echo -e "Backend will start on: ${GREEN}http://localhost:8000${NC}"
echo -e "Frontend will start on: ${GREEN}http://localhost:3000${NC}"
echo ""

# Start backend
echo -e "${YELLOW}Starting Backend (FastAPI)...${NC}"
python -m uvicorn src.pharmaviyum.main:app --reload --port 8000 &
BACKEND_PID=$!
echo -e "${GREEN}✓ Backend started (PID: $BACKEND_PID)${NC}"

# Give backend time to start
sleep 3

# Start frontend
echo -e "${YELLOW}Starting Frontend (Next.js)...${NC}"
cd frontend/shadcn-admin
npm run dev &
FRONTEND_PID=$!
echo -e "${GREEN}✓ Frontend started (PID: $FRONTEND_PID)${NC}"
cd ../..

echo ""
echo -e "${GREEN}🎉 All services started!${NC}"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Wait for interruption
wait $BACKEND_PID $FRONTEND_PID
