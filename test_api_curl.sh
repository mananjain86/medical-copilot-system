#!/bin/bash

# API Testing Script
# Tests the Medical Copilot API endpoints

echo "=========================================="
echo "Medical Copilot API Test"
echo "=========================================="
echo ""

# Configuration
API_URL="${1:-http://localhost:8000}"
echo "Testing API at: $API_URL"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Health Check
echo "Test 1: Health Check"
echo "-------------------"
echo "GET $API_URL/health"
echo ""

response=$(curl -s -w "\n%{http_code}" "$API_URL/health")
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$http_code" = "200" ]; then
    echo -e "${GREEN}✅ PASS${NC} - Status: $http_code"
    echo "Response: $body"
else
    echo -e "${RED}❌ FAIL${NC} - Status: $http_code"
    echo "Response: $body"
fi
echo ""
echo ""

# Test 2: Patient Search
echo "Test 2: Patient Search"
echo "----------------------"
echo "POST $API_URL/api/v1/search"
echo 'Body: {"user_id": 1, "query": "female patients over 60"}'
echo ""

response=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "query": "female patients over 60"}')

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$http_code" = "200" ]; then
    echo -e "${GREEN}✅ PASS${NC} - Status: $http_code"
    echo "Response (first 500 chars):"
    echo "$body" | head -c 500
    echo "..."
else
    echo -e "${RED}❌ FAIL${NC} - Status: $http_code"
    echo "Response: $body"
fi
echo ""
echo ""

# Test 3: Search History
echo "Test 3: Search History"
echo "---------------------"
echo "GET $API_URL/api/v1/history/1"
echo ""

response=$(curl -s -w "\n%{http_code}" "$API_URL/api/v1/history/1")
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$http_code" = "200" ]; then
    echo -e "${GREEN}✅ PASS${NC} - Status: $http_code"
    echo "Response (first 300 chars):"
    echo "$body" | head -c 300
    echo "..."
else
    echo -e "${RED}❌ FAIL${NC} - Status: $http_code"
    echo "Response: $body"
fi
echo ""
echo ""

# Test 4: Cohorts List
echo "Test 4: Cohorts List"
echo "-------------------"
echo "GET $API_URL/api/v1/cohorts"
echo ""

response=$(curl -s -w "\n%{http_code}" "$API_URL/api/v1/cohorts")
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$http_code" = "200" ]; then
    echo -e "${GREEN}✅ PASS${NC} - Status: $http_code"
    echo "Response (first 300 chars):"
    echo "$body" | head -c 300
    echo "..."
else
    echo -e "${RED}❌ FAIL${NC} - Status: $http_code"
    echo "Response: $body"
fi
echo ""
echo ""

# Test 5: Different Search Queries
echo "Test 5: Various Search Queries"
echo "------------------------------"

queries=(
    "diabetic patients"
    "male patients with hypertension"
    "patients in cardiology"
)

for query in "${queries[@]}"; do
    echo "Query: \"$query\""
    
    response=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/api/v1/search" \
      -H "Content-Type: application/json" \
      -d "{\"user_id\": 1, \"query\": \"$query\"}")
    
    http_code=$(echo "$response" | tail -n1)
    
    if [ "$http_code" = "200" ]; then
        echo -e "  ${GREEN}✅ PASS${NC}"
    else
        echo -e "  ${RED}❌ FAIL${NC} - Status: $http_code"
    fi
done

echo ""
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo ""
echo "To test against deployed API:"
echo "  ./test_api_curl.sh https://your-app.onrender.com"
echo ""
echo "To test locally:"
echo "  1. Start API: uvicorn api.main:app --host 0.0.0.0 --port 8000"
echo "  2. Run tests: ./test_api_curl.sh"
echo ""
