#!/bin/bash
# Script to run tests for X-sevenAI

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Default values
SERVICE="all"
COVERAGE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --service)
      SERVICE="$2"
      shift 2
      ;;
    --coverage)
      COVERAGE=true
      shift
      ;;
    --help)
      echo "Usage: $0 [--service all|auth|business|...] [--coverage]"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 [--service all|auth|business|...] [--coverage]"
      exit 1
      ;;
  esac
done

echo -e "${GREEN}Running tests for X-sevenAI...${NC}"
echo -e "${GREEN}Service: $SERVICE${NC}"
echo -e "${GREEN}Coverage: $COVERAGE${NC}"

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${YELLOW}pytest is not installed. Installing...${NC}"
    pip install pytest pytest-cov
fi

# Set up environment variables for testing
export TESTING=true
export SUPABASE_URL="http://localhost:54321"
export SUPABASE_ANON_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0"
export SUPABASE_SERVICE_ROLE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU"
export JWT_SECRET="super-secret-jwt-token-for-testing"
export REDIS_HOST="localhost"
export REDIS_PORT="6379"

# Run tests based on service
if [ "$SERVICE" == "all" ]; then
    echo -e "${GREEN}Running tests for all services...${NC}"
    
    if [ "$COVERAGE" == "true" ]; then
        pytest services/ shared/ --cov=services --cov=shared --cov-report=term --cov-report=html
    else
        pytest services/ shared/
    fi
else
    echo -e "${GREEN}Running tests for $SERVICE service...${NC}"
    
    if [ "$COVERAGE" == "true" ]; then
        pytest services/$SERVICE-service/ --cov=services/$SERVICE-service --cov-report=term --cov-report=html
    else
        pytest services/$SERVICE-service/
    fi
fi

# Check if tests passed
if [ $? -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    
    if [ "$COVERAGE" == "true" ]; then
        echo -e "${GREEN}Coverage report generated in htmlcov/ directory.${NC}"
        echo -e "${GREEN}Open htmlcov/index.html in your browser to view the report.${NC}"
    fi
    
    exit 0
else
    echo -e "${RED}Tests failed!${NC}"
    exit 1
fi
