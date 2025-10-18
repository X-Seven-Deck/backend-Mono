#!/bin/bash
# Script to deploy X-sevenAI to Kubernetes

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT="dev"
DOCKER_REGISTRY="your-registry"
IMAGE_TAG="latest"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --env)
      ENVIRONMENT="$2"
      shift 2
      ;;
    --registry)
      DOCKER_REGISTRY="$2"
      shift 2
      ;;
    --tag)
      IMAGE_TAG="$2"
      shift 2
      ;;
    --help)
      echo "Usage: $0 [--env dev|staging|prod] [--registry your-registry] [--tag latest]"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 [--env dev|staging|prod] [--registry your-registry] [--tag latest]"
      exit 1
      ;;
  esac
done

# Set namespace based on environment
case $ENVIRONMENT in
  dev)
    K8S_NAMESPACE="x7ai-dev"
    ;;
  staging)
    K8S_NAMESPACE="x7ai-staging"
    ;;
  prod)
    K8S_NAMESPACE="x7ai-prod"
    ;;
  *)
    echo -e "${RED}Invalid environment: $ENVIRONMENT. Must be one of: dev, staging, prod${NC}"
    exit 1
    ;;
esac

echo -e "${GREEN}Deploying X-sevenAI to Kubernetes...${NC}"
echo -e "${GREEN}Environment: $ENVIRONMENT${NC}"
echo -e "${GREEN}Namespace: $K8S_NAMESPACE${NC}"
echo -e "${GREEN}Docker Registry: $DOCKER_REGISTRY${NC}"
echo -e "${GREEN}Image Tag: $IMAGE_TAG${NC}"

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}kubectl is not installed. Please install kubectl first.${NC}"
    exit 1
fi

# Check if kubectl is configured
if ! kubectl cluster-info &> /dev/null; then
    echo -e "${RED}kubectl is not configured or cannot connect to the cluster.${NC}"
    exit 1
fi

# Export variables for substitution in YAML files
export K8S_NAMESPACE
export DOCKER_REGISTRY
export IMAGE_TAG
export ENVIRONMENT

# Create namespace if it doesn't exist
echo -e "${GREEN}Creating namespace if it doesn't exist...${NC}"
kubectl get namespace $K8S_NAMESPACE &> /dev/null || kubectl create namespace $K8S_NAMESPACE

# Apply namespace configuration
echo -e "${GREEN}Applying namespace configuration...${NC}"
envsubst < infra/kubernetes/namespace.yaml | kubectl apply -f -

# Apply secrets
echo -e "${GREEN}Applying secrets...${NC}"
# Note: In a real deployment, you would use a more secure way to handle secrets
# such as using Vault or Kubernetes Secrets Store CSI Driver
if [ -f infra/kubernetes/secrets.yaml ]; then
    # This is just a placeholder - in reality, you would need to handle base64 encoding of secrets
    envsubst < infra/kubernetes/secrets.yaml | kubectl apply -f -
else
    echo -e "${YELLOW}Secrets file not found. Skipping...${NC}"
fi

# Apply Vault configuration
echo -e "${GREEN}Applying Vault configuration...${NC}"
if [ -d infra/kubernetes/vault ]; then
    for file in infra/kubernetes/vault/*.yaml; do
        envsubst < $file | kubectl apply -f -
    done
else
    echo -e "${YELLOW}Vault configuration not found. Skipping...${NC}"
fi

# Apply monitoring configuration
echo -e "${GREEN}Applying monitoring configuration...${NC}"
if [ -d infra/kubernetes/monitoring ]; then
    for file in infra/kubernetes/monitoring/*.yaml; do
        envsubst < $file | kubectl apply -f -
    done
else
    echo -e "${YELLOW}Monitoring configuration not found. Skipping...${NC}"
fi

# Deploy services
echo -e "${GREEN}Deploying services...${NC}"

# API Gateway
echo -e "${GREEN}Deploying API Gateway...${NC}"
for file in services/api-gateway/k8s/*.yaml; do
    envsubst < $file | kubectl apply -f -
done

# Auth Service
echo -e "${GREEN}Deploying Auth Service...${NC}"
for file in services/auth-service/k8s/*.yaml; do
    envsubst < $file | kubectl apply -f -
done

# Business Logic Service
echo -e "${GREEN}Deploying Business Logic Service...${NC}"
for file in services/business-logic-service/k8s/*.yaml; do
    envsubst < $file | kubectl apply -f -
done

# AI Orchestration Service
echo -e "${GREEN}Deploying AI Orchestration Service...${NC}"
for file in services/ai-orchestration-service/k8s/*.yaml; do
    envsubst < $file | kubectl apply -f -
done

# Chat & Communication Service
echo -e "${GREEN}Deploying Chat & Communication Service...${NC}"
for file in services/chat-communication-service/k8s/*.yaml; do
    envsubst < $file | kubectl apply -f -
done

# Analytics Dashboard Service
echo -e "${GREEN}Deploying Analytics Dashboard Service...${NC}"
for file in services/analytics-dashboard-service/k8s/*.yaml; do
    envsubst < $file | kubectl apply -f -
done

# Notification & Integration Service
echo -e "${GREEN}Deploying Notification & Integration Service...${NC}"
for file in services/notification-integration-service/k8s/*.yaml; do
    envsubst < $file | kubectl apply -f -
done

# Monitoring & Logging Service
echo -e "${GREEN}Deploying Monitoring & Logging Service...${NC}"
for file in services/monitoring-logging-service/k8s/*.yaml; do
    envsubst < $file | kubectl apply -f -
done

# Global Chat Service
echo -e "${GREEN}Deploying Global Chat Service...${NC}"
for file in services/global-chat-service/k8s/*.yaml; do
    envsubst < $file | kubectl apply -f -
done

# Verify deployments
echo -e "${GREEN}Verifying deployments...${NC}"
kubectl get deployments -n $K8S_NAMESPACE

echo -e "${GREEN}Deployment complete!${NC}"
echo -e "${GREEN}You can check the status of the pods with:${NC}"
echo -e "${YELLOW}kubectl get pods -n $K8S_NAMESPACE${NC}"

# Get the API Gateway service URL
if [ "$ENVIRONMENT" != "dev" ]; then
    echo -e "${GREEN}Waiting for API Gateway service to get an external IP...${NC}"
    kubectl wait --for=condition=available --timeout=300s deployment/api-gateway -n $K8S_NAMESPACE
    
    API_GATEWAY_URL=$(kubectl get service api-gateway -n $K8S_NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
    if [ -z "$API_GATEWAY_URL" ]; then
        API_GATEWAY_URL=$(kubectl get service api-gateway -n $K8S_NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
    fi
    
    if [ -n "$API_GATEWAY_URL" ]; then
        echo -e "${GREEN}API Gateway is available at: http://$API_GATEWAY_URL${NC}"
    else
        echo -e "${YELLOW}Could not determine API Gateway URL. Please check the service manually.${NC}"
    fi
fi
