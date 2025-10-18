#!/bin/bash
# Script to build Docker images for X-sevenAI services

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Default values
SERVICE="all"
TAG="latest"
REGISTRY="your-registry"
PUSH=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --service)
      SERVICE="$2"
      shift 2
      ;;
    --tag)
      TAG="$2"
      shift 2
      ;;
    --registry)
      REGISTRY="$2"
      shift 2
      ;;
    --push)
      PUSH=true
      shift
      ;;
    --help)
      echo "Usage: $0 [--service all|api-gateway|auth|...] [--tag latest] [--registry your-registry] [--push]"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 [--service all|api-gateway|auth|...] [--tag latest] [--registry your-registry] [--push]"
      exit 1
      ;;
  esac
done

echo -e "${GREEN}Building Docker images for X-sevenAI...${NC}"
echo -e "${GREEN}Service: $SERVICE${NC}"
echo -e "${GREEN}Tag: $TAG${NC}"
echo -e "${GREEN}Registry: $REGISTRY${NC}"
echo -e "${GREEN}Push: $PUSH${NC}"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

# Function to build and optionally push a service
build_service() {
    local service=$1
    local service_path="services/$service"
    local dockerfile_path="$service_path/docker/Dockerfile"
    local image_name="$REGISTRY/x7ai/$service:$TAG"
    
    if [ ! -f "$dockerfile_path" ]; then
        echo -e "${RED}Dockerfile not found for $service at $dockerfile_path${NC}"
        return 1
    fi
    
    echo -e "${GREEN}Building $service...${NC}"
    docker build -t "$image_name" -f "$dockerfile_path" .
    
    if [ "$PUSH" == "true" ]; then
        echo -e "${GREEN}Pushing $service...${NC}"
        docker push "$image_name"
    fi
}

# Build services
if [ "$SERVICE" == "all" ]; then
    echo -e "${GREEN}Building all services...${NC}"
    
    # API Gateway
    build_service "api-gateway"
    
    # Auth Service
    build_service "auth-service"
    
    # Business Logic Service
    build_service "business-logic-service"
    
    # AI Orchestration Service
    build_service "ai-orchestration-service"
    
    # Chat & Communication Service
    build_service "chat-communication-service"
    
    # Analytics Dashboard Service
    build_service "analytics-dashboard-service"
    
    # Notification & Integration Service
    build_service "notification-integration-service"
    
    # Monitoring & Logging Service
    build_service "monitoring-logging-service"
    
    # Global Chat Service
    build_service "global-chat-service"
else
    echo -e "${GREEN}Building $SERVICE service...${NC}"
    build_service "$SERVICE"
fi

echo -e "${GREEN}Build complete!${NC}"
if [ "$PUSH" == "true" ]; then
    echo -e "${GREEN}Images pushed to registry.${NC}"
fi
