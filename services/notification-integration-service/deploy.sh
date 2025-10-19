#!/bin/bash

# Notification Integration Service Deployment Script

set -e

echo "========================================="
echo "Notification Integration Service Deploy"
echo "========================================="

# Configuration
SERVICE_NAME="notification-integration-service"
DOCKER_REGISTRY="${DOCKER_REGISTRY:-x7ai}"
VERSION="${VERSION:-latest}"
ENVIRONMENT="${ENVIRONMENT:-production}"

echo "Environment: $ENVIRONMENT"
echo "Version: $VERSION"

# Build Docker image
echo ""
echo "Building Docker image..."
docker build -t ${DOCKER_REGISTRY}/${SERVICE_NAME}:${VERSION} \
  -f docker/Dockerfile .

# Tag as latest
docker tag ${DOCKER_REGISTRY}/${SERVICE_NAME}:${VERSION} \
  ${DOCKER_REGISTRY}/${SERVICE_NAME}:latest

# Push to registry (if configured)
if [ -n "$DOCKER_REGISTRY" ]; then
  echo ""
  echo "Pushing to Docker registry..."
  docker push ${DOCKER_REGISTRY}/${SERVICE_NAME}:${VERSION}
  docker push ${DOCKER_REGISTRY}/${SERVICE_NAME}:latest
fi

# Deploy to Kubernetes (if configured)
if [ "$DEPLOY_K8S" = "true" ]; then
  echo ""
  echo "Deploying to Kubernetes..."
  
  # Apply configurations
  kubectl apply -f k8s/deployment.yaml
  kubectl apply -f k8s/service.yaml
  
  # Wait for rollout
  kubectl rollout status deployment/${SERVICE_NAME} -n ${K8S_NAMESPACE:-default}
  
  echo ""
  echo "Deployment complete!"
  kubectl get pods -l app=${SERVICE_NAME} -n ${K8S_NAMESPACE:-default}
fi

# Run database migrations
if [ "$RUN_MIGRATIONS" = "true" ]; then
  echo ""
  echo "Running database migrations..."
  
  # Run migrations in container or pod
  if [ "$DEPLOY_K8S" = "true" ]; then
    POD=$(kubectl get pod -l app=${SERVICE_NAME} -o jsonpath="{.items[0].metadata.name}" -n ${K8S_NAMESPACE:-default})
    kubectl exec -it $POD -n ${K8S_NAMESPACE:-default} -- alembic upgrade head
  else
    docker run --rm --env-file .env \
      ${DOCKER_REGISTRY}/${SERVICE_NAME}:${VERSION} \
      alembic upgrade head
  fi
fi

echo ""
echo "========================================="
echo "Deployment completed successfully!"
echo "========================================="
