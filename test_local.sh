#!/bin/bash

# Local Testing Script
# Run this to test both frontend and backend locally before deploying

echo "=================================="
echo "LOCAL TESTING SCRIPT"
echo "=================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if virtual environment is activated
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo -e "${YELLOW}⚠️  Virtual environment not activated${NC}"
    echo "Run: source .venv/bin/activate"
    echo ""
fi

# Check if dependencies are installed
echo "📦 Checking dependencies..."
python -c "import streamlit" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Dependencies not installed${NC}"
    echo "Run: pip install -r requirements.txt"
    exit 1
fi
echo -e "${GREEN}✅ Dependencies installed${NC}"
echo ""

# Run verification script
echo "🔍 Running deployment verification..."
python verify_deployment.py
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Verification failed${NC}"
    echo "Fix the issues above before proceeding"
    exit 1
fi
echo ""

# Ask user what to test
echo "What would you like to test?"
echo "1) Frontend only (Streamlit)"
echo "2) Backend only (FastAPI)"
echo "3) Both (in separate terminals)"
echo ""
read -p "Enter choice (1-3): " choice

case $choice in
    1)
        echo ""
        echo -e "${GREEN}🚀 Starting Streamlit frontend...${NC}"
        echo "URL: http://localhost:8501"
        echo "Press Ctrl+C to stop"
        echo ""
        streamlit run app.py --server.port 8501
        ;;
    2)
        echo ""
        echo -e "${GREEN}🚀 Starting FastAPI backend...${NC}"
        echo "URL: http://localhost:8000"
        echo "Docs: http://localhost:8000/docs"
        echo "Press Ctrl+C to stop"
        echo ""
        uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
        ;;
    3)
        echo ""
        echo -e "${YELLOW}⚠️  This requires two terminal windows${NC}"
        echo ""
        echo "Terminal 1 - Run backend:"
        echo "  uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload"
        echo ""
        echo "Terminal 2 - Run frontend:"
        echo "  streamlit run app.py --server.port 8501"
        echo ""
        echo "URLs:"
        echo "  Frontend: http://localhost:8501"
        echo "  Backend:  http://localhost:8000"
        echo "  API Docs: http://localhost:8000/docs"
        ;;
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac
