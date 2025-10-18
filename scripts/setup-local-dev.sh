#!/bin/bash
# Script to set up local development environment for X-sevenAI

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Setting up X-sevenAI local development environment...${NC}"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Docker Compose is not installed. Please install Docker Compose first.${NC}"
    exit 1
fi

# Check if .env file exists, if not create it from .env.example
if [ ! -f .env ]; then
    echo -e "${YELLOW}.env file not found. Creating from .env.example...${NC}"
    if [ -f .env.example ]; then
        cp .env.example .env
        echo -e "${GREEN}.env file created. Please update it with your credentials.${NC}"
    else
        echo -e "${RED}.env.example file not found. Please create a .env file manually.${NC}"
        exit 1
    fi
fi

# Create necessary directories
echo -e "${GREEN}Creating necessary directories...${NC}"
mkdir -p data/supabase data/redis data/elasticsearch data/grafana

# Pull Docker images
echo -e "${GREEN}Pulling Docker images...${NC}"
docker-compose pull

# Build Docker images
echo -e "${GREEN}Building Docker images...${NC}"
docker-compose build

# Start the services
echo -e "${GREEN}Starting services...${NC}"
docker-compose up -d

# Wait for services to be ready
echo -e "${GREEN}Waiting for services to be ready...${NC}"
sleep 10

# Check if services are running
echo -e "${GREEN}Checking if services are running...${NC}"
docker-compose ps

echo -e "${GREEN}Local development environment setup complete!${NC}"
echo -e "${GREEN}You can access the services at:${NC}"
echo -e "${GREEN}- API Gateway: http://localhost:8000${NC}"
echo -e "${GREEN}- Auth Service: http://localhost:8010${NC}"
echo -e "${GREEN}- Monitoring Dashboard: http://localhost:3000${NC}"
echo -e "${GREEN}- Supabase Studio: http://localhost:54322${NC}"

echo -e "${YELLOW}Note: It may take a few minutes for all services to be fully initialized.${NC}"
echo -e "${YELLOW}Check the logs with 'docker-compose logs -f' to monitor the progress.${NC}"
