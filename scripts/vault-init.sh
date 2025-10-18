#!/bin/bash
# Script to initialize Vault and set up secrets

set -e

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    echo "kubectl is not installed. Please install kubectl first."
    exit 1
fi

# Check if jq is installed
if ! command -v jq &> /dev/null; then
    echo "jq is not installed. Please install jq first."
    exit 1
fi

# Get namespace from argument or use default
NAMESPACE=${1:-x7ai}

# Check if Vault is running
echo "Checking if Vault is running in namespace $NAMESPACE..."
if ! kubectl get pod -n $NAMESPACE -l app=vault -o jsonpath='{.items[0].metadata.name}' &> /dev/null; then
    echo "Vault is not running in namespace $NAMESPACE. Please deploy Vault first."
    exit 1
fi

VAULT_POD=$(kubectl get pod -n $NAMESPACE -l app=vault -o jsonpath='{.items[0].metadata.name}')
echo "Found Vault pod: $VAULT_POD"

# Port forward to Vault
echo "Setting up port forwarding to Vault..."
kubectl port-forward -n $NAMESPACE $VAULT_POD 8200:8200 &
PORT_FORWARD_PID=$!

# Wait for port forwarding to be established
sleep 5

# Set Vault address and token
export VAULT_ADDR="http://127.0.0.1:8200"
export VAULT_TOKEN=$(kubectl get secret -n $NAMESPACE vault-secrets -o jsonpath='{.data.root_token}' | base64 --decode)

echo "Vault address: $VAULT_ADDR"
echo "Using Vault token from Kubernetes secret"

# Check if Vault is initialized and unsealed
echo "Checking Vault status..."
VAULT_STATUS=$(curl -s $VAULT_ADDR/v1/sys/health)
INITIALIZED=$(echo $VAULT_STATUS | jq -r '.initialized')
SEALED=$(echo $VAULT_STATUS | jq -r '.sealed')

if [ "$INITIALIZED" != "true" ]; then
    echo "Vault is not initialized. Initializing Vault..."
    INIT_RESPONSE=$(curl -s -X PUT $VAULT_ADDR/v1/sys/init \
        -H "Content-Type: application/json" \
        -d '{"secret_shares": 1, "secret_threshold": 1}')
    
    ROOT_TOKEN=$(echo $INIT_RESPONSE | jq -r '.root_token')
    UNSEAL_KEY=$(echo $INIT_RESPONSE | jq -r '.keys[0]')
    
    echo "Vault initialized with root token: $ROOT_TOKEN"
    echo "Unseal key: $UNSEAL_KEY"
    
    # Save keys to a file
    echo "Saving keys to vault-keys.json..."
    echo $INIT_RESPONSE > vault-keys.json
    
    # Update Vault token
    export VAULT_TOKEN=$ROOT_TOKEN
    
    # Update the Kubernetes secret with the new root token
    kubectl create secret generic -n $NAMESPACE vault-secrets \
        --from-literal=root_token=$ROOT_TOKEN \
        --dry-run=client -o yaml | kubectl apply -f -
    
    echo "Kubernetes secret updated with new root token"
fi

if [ "$SEALED" == "true" ]; then
    echo "Vault is sealed. Unsealing Vault..."
    UNSEAL_KEY=$(cat vault-keys.json | jq -r '.keys[0]')
    curl -s -X PUT $VAULT_ADDR/v1/sys/unseal \
        -H "Content-Type: application/json" \
        -d "{\"key\": \"$UNSEAL_KEY\"}"
    echo "Vault unsealed"
fi

# Enable secrets engines
echo "Enabling secrets engines..."
curl -s -X POST -H "X-Vault-Token: $VAULT_TOKEN" \
    $VAULT_ADDR/v1/sys/mounts/kv \
    -d '{"type": "kv", "options": {"version": "2"}}'

# Create secrets
echo "Creating secrets..."

# Supabase secrets
echo "Creating Supabase secrets..."
curl -s -X POST -H "X-Vault-Token: $VAULT_TOKEN" \
    $VAULT_ADDR/v1/kv/data/supabase \
    -d "{\"data\": {\"url\": \"${SUPABASE_URL}\", \"anon_key\": \"${SUPABASE_ANON_KEY}\", \"service_role_key\": \"${SUPABASE_SERVICE_ROLE_KEY}\"}}"

# AI secrets
echo "Creating AI secrets..."
curl -s -X POST -H "X-Vault-Token: $VAULT_TOKEN" \
    $VAULT_ADDR/v1/kv/data/ai \
    -d "{\"data\": {\"openai_api_key\": \"${OPENAI_API_KEY}\", \"elevenlabs_api_key\": \"${ELEVENLABS_API_KEY}\"}}"

# Notification secrets
echo "Creating Notification secrets..."
curl -s -X POST -H "X-Vault-Token: $VAULT_TOKEN" \
    $VAULT_ADDR/v1/kv/data/notification \
    -d "{\"data\": {\"twilio_account_sid\": \"${TWILIO_ACCOUNT_SID}\", \"twilio_auth_token\": \"${TWILIO_AUTH_TOKEN}\", \"zapier_webhook_url\": \"${ZAPIER_WEBHOOK_URL}\"}}"

# Auth secrets
echo "Creating Auth secrets..."
curl -s -X POST -H "X-Vault-Token: $VAULT_TOKEN" \
    $VAULT_ADDR/v1/kv/data/auth \
    -d "{\"data\": {\"jwt_secret\": \"${JWT_SECRET}\"}}"

# Create policies
echo "Creating policies..."

# Create a policy for the auth service
cat <<EOF > auth-policy.hcl
path "kv/data/auth" {
  capabilities = ["read"]
}
path "kv/data/supabase" {
  capabilities = ["read"]
}
EOF

curl -s -X POST -H "X-Vault-Token: $VAULT_TOKEN" \
    $VAULT_ADDR/v1/sys/policies/acl/auth-service \
    -d "{\"policy\": \"$(cat auth-policy.hcl | sed 's/"/\\"/g' | sed ':a;N;$!ba;s/\n/\\n/g')\"}"

# Create a policy for the AI orchestration service
cat <<EOF > ai-policy.hcl
path "kv/data/ai" {
  capabilities = ["read"]
}
path "kv/data/supabase" {
  capabilities = ["read"]
}
EOF

curl -s -X POST -H "X-Vault-Token: $VAULT_TOKEN" \
    $VAULT_ADDR/v1/sys/policies/acl/ai-service \
    -d "{\"policy\": \"$(cat ai-policy.hcl | sed 's/"/\\"/g' | sed ':a;N;$!ba;s/\n/\\n/g')\"}"

# Create a policy for the notification service
cat <<EOF > notification-policy.hcl
path "kv/data/notification" {
  capabilities = ["read"]
}
EOF

curl -s -X POST -H "X-Vault-Token: $VAULT_TOKEN" \
    $VAULT_ADDR/v1/sys/policies/acl/notification-service \
    -d "{\"policy\": \"$(cat notification-policy.hcl | sed 's/"/\\"/g' | sed ':a;N;$!ba;s/\n/\\n/g')\"}"

# Enable Kubernetes authentication
echo "Enabling Kubernetes authentication..."
curl -s -X POST -H "X-Vault-Token: $VAULT_TOKEN" \
    $VAULT_ADDR/v1/sys/auth/kubernetes \
    -d '{"type": "kubernetes"}'

# Configure Kubernetes authentication
echo "Configuring Kubernetes authentication..."
KUBE_CA_CERT=$(kubectl config view --raw --minify --flatten --output='jsonpath={.clusters[].cluster.certificate-authority-data}' | base64 --decode)
KUBE_HOST=$(kubectl config view --raw --minify --flatten --output='jsonpath={.clusters[].cluster.server}')

curl -s -X POST -H "X-Vault-Token: $VAULT_TOKEN" \
    $VAULT_ADDR/v1/auth/kubernetes/config \
    -d "{\"kubernetes_host\": \"$KUBE_HOST\", \"kubernetes_ca_cert\": \"$KUBE_CA_CERT\", \"token_reviewer_jwt\": \"$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)\"}"

# Create Kubernetes authentication roles
echo "Creating Kubernetes authentication roles..."

# Auth service role
curl -s -X POST -H "X-Vault-Token: $VAULT_TOKEN" \
    $VAULT_ADDR/v1/auth/kubernetes/role/auth-service \
    -d "{\"bound_service_account_names\": [\"auth-service\"], \"bound_service_account_namespaces\": [\"$NAMESPACE\"], \"policies\": [\"auth-service\"], \"ttl\": \"1h\"}"

# AI orchestration service role
curl -s -X POST -H "X-Vault-Token: $VAULT_TOKEN" \
    $VAULT_ADDR/v1/auth/kubernetes/role/ai-service \
    -d "{\"bound_service_account_names\": [\"ai-orchestration-service\"], \"bound_service_account_namespaces\": [\"$NAMESPACE\"], \"policies\": [\"ai-service\"], \"ttl\": \"1h\"}"

# Notification service role
curl -s -X POST -H "X-Vault-Token: $VAULT_TOKEN" \
    $VAULT_ADDR/v1/auth/kubernetes/role/notification-service \
    -d "{\"bound_service_account_names\": [\"notification-integration-service\"], \"bound_service_account_namespaces\": [\"$NAMESPACE\"], \"policies\": [\"notification-service\"], \"ttl\": \"1h\"}"

echo "Vault initialization and setup completed successfully!"

# Clean up
echo "Cleaning up..."
kill $PORT_FORWARD_PID

echo "Done!"
