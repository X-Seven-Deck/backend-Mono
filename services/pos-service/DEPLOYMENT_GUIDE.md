# POS Service Deployment Guide

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Local Development](#local-development)
3. [Docker Deployment](#docker-deployment)
4. [Kubernetes Deployment](#kubernetes-deployment)
5. [Environment Configuration](#environment-configuration)
6. [Database Setup](#database-setup)
7. [Monitoring & Logging](#monitoring--logging)
8. [Health Checks](#health-checks)
9. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Tools
- **Python 3.11+**
- **Docker 20.10+**
- **Kubernetes 1.24+** (for production)
- **kubectl** CLI tool
- **PostgreSQL** (via Supabase)
- **Redis** (optional, for caching)

### Required Services
- **Supabase** account and project
- **JWT Secret** for authentication
- **Dashboard Service** running (for integration)

---

## Local Development

### 1. Clone Repository
```bash
cd /Users/naveen/Desktop/x7AI/services/pos-service
```

### 2. Create Virtual Environment
```bash
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment
```bash
cp .env.example .env
# Edit .env with your configuration
```

Required environment variables:
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your_service_key
JWT_SECRET=your_secure_secret_key_minimum_32_characters
```

### 5. Run Database Migrations
```bash
# Apply database migrations
psql -h your-supabase-host -U postgres -d your-database -f database_migrations/001_pos_tables.sql
```

### 6. Start Service
```bash
# Development mode with auto-reload
uvicorn app.main:app --reload --port 8070

# Or using the script
python -m app.main
```

### 7. Verify Service
```bash
# Health check
curl http://localhost:8070/health

# API documentation
open http://localhost:8070/docs
```

---

## Docker Deployment

### 1. Build Docker Image
```bash
docker build -t x7ai/pos-service:latest -f docker/Dockerfile .
```

### 2. Run Container
```bash
docker run -d \
  --name pos-service \
  -p 8070:8070 \
  -e SUPABASE_URL="https://your-project.supabase.co" \
  -e SUPABASE_SERVICE_KEY="your_service_key" \
  -e JWT_SECRET="your_secret_key" \
  x7ai/pos-service:latest
```

### 3. Using Docker Compose
```bash
docker-compose up -d
```

`docker-compose.yml` example:
```yaml
version: '3.8'

services:
  pos-service:
    build:
      context: .
      dockerfile: docker/Dockerfile
    ports:
      - "8070:8070"
    environment:
      - ENVIRONMENT=production
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_SERVICE_KEY=${SUPABASE_SERVICE_KEY}
      - JWT_SECRET=${JWT_SECRET}
      - REDIS_HOST=redis
    depends_on:
      - redis
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    restart: unless-stopped
```

---

## Kubernetes Deployment

### 1. Create Namespace
```bash
kubectl create namespace x7ai
```

### 2. Create Secrets
```bash
# Supabase credentials
kubectl create secret generic supabase-credentials \
  --from-literal=url="https://your-project.supabase.co" \
  --from-literal=anon-key="your_anon_key" \
  --from-literal=service-key="your_service_key" \
  -n x7ai

# JWT secret
kubectl create secret generic jwt-secret \
  --from-literal=secret="your_jwt_secret_key" \
  -n x7ai
```

### 3. Deploy Service
```bash
kubectl apply -f k8s/deployment.yaml -n x7ai
```

### 4. Verify Deployment
```bash
# Check pods
kubectl get pods -n x7ai -l app=pos-service

# Check service
kubectl get svc pos-service -n x7ai

# View logs
kubectl logs -f deployment/pos-service -n x7ai
```

### 5. Access Service
```bash
# Port forward for local access
kubectl port-forward svc/pos-service 8070:8070 -n x7ai

# Or create Ingress for external access
```

---

## Environment Configuration

### Required Variables
```env
# Application
ENVIRONMENT=production          # development, staging, production
LOG_LEVEL=INFO                 # DEBUG, INFO, WARNING, ERROR
POS_SERVICE_HOST=0.0.0.0
POS_SERVICE_PORT=8070

# Supabase
SUPABASE_URL=<required>
SUPABASE_KEY=<required>
SUPABASE_SERVICE_KEY=<required>

# Authentication
JWT_SECRET=<required>           # Minimum 32 characters
JWT_ALGORITHM=HS256
JWT_EXPIRY=86400               # 24 hours

# Redis (optional)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=1

# Inter-Service
DASHBOARD_SERVICE_URL=http://analytics-dashboard-service:8060
API_GATEWAY_URL=http://api-gateway:8000

# CORS
CORS_ORIGINS=*                 # Comma-separated list or *
CORS_ALLOW_CREDENTIALS=true

# Tax
DEFAULT_TAX_RATE=0.10         # 10%
TAX_CALCULATION_MODE=location_based

# Receipt
RECEIPT_PREFIX=RCP
BUSINESS_NAME=Your Business
BUSINESS_ADDRESS=123 Main St
BUSINESS_PHONE=+1234567890

# Monitoring
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=9091

# Feature Flags
ENABLE_OFFLINE_MODE=true
ENABLE_PUSH_NOTIFICATIONS=true
ENABLE_RECEIPT_EMAIL=true
```

### Environment-Specific Configs

**Development:**
```env
ENVIRONMENT=development
LOG_LEVEL=DEBUG
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
```

**Staging:**
```env
ENVIRONMENT=staging
LOG_LEVEL=INFO
CORS_ORIGINS=https://staging.x7ai.com
```

**Production:**
```env
ENVIRONMENT=production
LOG_LEVEL=WARNING
CORS_ORIGINS=https://app.x7ai.com
```

---

## Database Setup

### 1. Connect to Supabase
```bash
psql "postgresql://postgres:[password]@db.[project-ref].supabase.co:5432/postgres"
```

### 2. Run Migrations
```sql
-- Run migration files in order
\i database_migrations/001_pos_tables.sql
```

### 3. Verify Tables
```sql
-- List POS tables
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN ('orders', 'order_items', 'payments', 'receipts', 'tax_rules', 'customers');

-- Check indexes
SELECT indexname, tablename
FROM pg_indexes
WHERE tablename IN ('orders', 'payments', 'customers');
```

### 4. Create Test Data (Development Only)
```sql
-- Insert test business
INSERT INTO public.businesses (id, name, category_id)
VALUES (gen_random_uuid(), 'Test Restaurant', 1);

-- Insert test tax rule
INSERT INTO public.tax_rules (business_id, name, rate, type)
VALUES ('your-business-id', 'Sales Tax', 0.0875, 'sales_tax');
```

---

## Monitoring & Logging

### Prometheus Metrics

Metrics endpoint: `http://localhost:8070/metrics`

**Available Metrics:**
- `pos_requests_total`: Total request count by method, endpoint, status
- `pos_request_duration_seconds`: Request duration histogram by method, endpoint

### Grafana Dashboard

Import the provided Grafana dashboard:
```bash
# Dashboard JSON in monitoring/grafana/dashboards/pos-service.json
```

**Key Metrics to Monitor:**
- Request rate (requests/second)
- Response time (p50, p95, p99)
- Error rate
- Order creation rate
- Payment processing rate
- Active WebSocket connections

### Logging

**Log Levels:**
- **DEBUG**: Detailed diagnostic information
- **INFO**: General informational messages
- **WARNING**: Warning messages for potentially problematic situations
- **ERROR**: Error events that might still allow the application to continue

**Log Format (JSON):**
```json
{
  "timestamp": "2024-10-18T12:34:56Z",
  "level": "INFO",
  "service": "pos-service",
  "message": "Order created successfully",
  "order_id": "uuid",
  "business_id": "uuid"
}
```

### Centralized Logging

Forward logs to centralized logging system:

**Using Fluentd:**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: fluentd-config
data:
  fluent.conf: |
    <source>
      @type tail
      path /var/log/containers/pos-service*.log
      pos_file /var/log/fluentd-containers.log.pos
      tag kubernetes.*
      format json
    </source>
```

---

## Health Checks

### Health Endpoint
```bash
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "pos-service",
  "version": "1.0.0",
  "timestamp": "2024-10-18T12:34:56Z"
}
```

### Kubernetes Probes

**Liveness Probe:**
- Checks if service is alive
- Restarts pod if failing
- Path: `/health`
- Initial delay: 30s
- Period: 10s

**Readiness Probe:**
- Checks if service is ready to accept traffic
- Removes pod from load balancer if failing
- Path: `/health`
- Initial delay: 10s
- Period: 5s

---

## Troubleshooting

### Common Issues

#### 1. Service Won't Start

**Error:** `Failed to connect to database`

**Solution:**
```bash
# Verify Supabase credentials
echo $SUPABASE_URL
echo $SUPABASE_SERVICE_KEY

# Test connection
curl "$SUPABASE_URL/rest/v1/" \
  -H "apikey: $SUPABASE_SERVICE_KEY"
```

#### 2. Authentication Failing

**Error:** `Invalid authentication credentials`

**Solution:**
```bash
# Verify JWT secret is set
echo $JWT_SECRET

# Test token generation
python -c "from jose import jwt; print(jwt.encode({'sub': 'test'}, 'your-secret', algorithm='HS256'))"
```

#### 3. WebSocket Connection Failed

**Error:** `WebSocket closed with code 1008`

**Solution:**
```bash
# Ensure token is passed as query parameter
wscat -c "ws://localhost:8070/api/v1/pos/ws/orders?token=YOUR_JWT_TOKEN"

# Check CORS settings
curl -I -X OPTIONS http://localhost:8070/api/v1/pos/orders
```

#### 4. High Memory Usage

**Symptoms:** Memory usage > 500MB

**Solution:**
```bash
# Check for memory leaks
kubectl top pod -n x7ai -l app=pos-service

# Restart pods
kubectl rollout restart deployment/pos-service -n x7ai

# Adjust resource limits
kubectl set resources deployment/pos-service -n x7ai \
  --limits=memory=1Gi \
  --requests=memory=512Mi
```

### Debug Mode

Enable debug logging:
```env
LOG_LEVEL=DEBUG
```

View detailed logs:
```bash
# Local
tail -f logs/pos-service.log

# Docker
docker logs -f pos-service

# Kubernetes
kubectl logs -f deployment/pos-service -n x7ai --tail=100
```

### Performance Issues

**Check database query performance:**
```sql
-- Enable query logging
ALTER DATABASE postgres SET log_statement = 'all';
ALTER DATABASE postgres SET log_duration = on;

-- View slow queries
SELECT query, mean_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
```

**Profile API endpoints:**
```bash
# Use Apache Bench for load testing
ab -n 1000 -c 10 -H "Authorization: Bearer $TOKEN" \
  http://localhost:8070/api/v1/pos/orders/
```

---

## Scaling

### Horizontal Scaling

**Kubernetes HPA:**
```bash
# Scale based on CPU
kubectl autoscale deployment pos-service \
  --cpu-percent=70 \
  --min=3 \
  --max=10 \
  -n x7ai

# Check autoscaler status
kubectl get hpa -n x7ai
```

### Load Balancing

**NGINX Ingress:**
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: pos-service-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  rules:
  - host: api.x7ai.com
    http:
      paths:
      - path: /pos
        pathType: Prefix
        backend:
          service:
            name: pos-service
            port:
              number: 8070
```

---

## Backup & Recovery

### Database Backups

**Automated Supabase Backups:**
- Supabase provides automated daily backups
- Point-in-time recovery available
- Retention: 30 days (Pro plan)

**Manual Backup:**
```bash
# Backup specific tables
pg_dump -h your-supabase-host -U postgres \
  -t orders -t order_items -t payments -t receipts \
  -t customers -t tax_rules \
  > pos-backup-$(date +%Y%m%d).sql
```

**Restore:**
```bash
psql -h your-supabase-host -U postgres -d postgres \
  < pos-backup-20241018.sql
```

---

## Security Checklist

- [ ] JWT secret is strong (>32 characters)
- [ ] HTTPS enabled in production
- [ ] CORS configured correctly
- [ ] Rate limiting enabled
- [ ] Secrets stored securely (Kubernetes Secrets, not env files)
- [ ] Row-level security enabled in Supabase
- [ ] Regular security updates applied
- [ ] Audit logging enabled
- [ ] Network policies configured
- [ ] Firewall rules in place

---

## Maintenance

### Regular Tasks

**Daily:**
- Monitor error rates
- Check service health
- Review logs for anomalies

**Weekly:**
- Review performance metrics
- Check disk usage
- Verify backups

**Monthly:**
- Update dependencies
- Review security patches
- Test disaster recovery
- Optimize database queries

### Update Procedure

1. **Backup database**
2. **Test in staging**
3. **Deploy to production** (rolling update)
4. **Monitor for issues**
5. **Rollback if needed**

```bash
# Deploy new version
kubectl set image deployment/pos-service \
  pos-service=x7ai/pos-service:v1.1.0 \
  -n x7ai

# Monitor rollout
kubectl rollout status deployment/pos-service -n x7ai

# Rollback if issues
kubectl rollout undo deployment/pos-service -n x7ai
```

---

## Support

**Documentation:**
- API Documentation: `/docs`
- Architecture: `README.md`
- Implementation: `POS_SERVICE_IMPLEMENTATION_COMPLETE.md`

**Contact:**
- Email: support@x7ai.com
- Slack: #pos-service

**Emergency:**
- On-call: [PagerDuty/Opsgenie]
- Escalation: engineering@x7ai.com
