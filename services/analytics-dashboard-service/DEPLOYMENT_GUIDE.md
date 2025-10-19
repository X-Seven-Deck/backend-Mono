# 🚀 Analytics Dashboard Service - Deployment Guide

## Quick Start

### 1. Install Dependencies

```bash
cd services/analytics-dashboard-service
pip install -r requirements.txt
```

### 2. Configure Environment

Update `.env` file:

```env
# Supabase
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
SUPABASE_ANON_KEY=your_anon_key

# Redis
REDIS_URL=redis://localhost:6379

# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# AI Orchestration Service
AI_ORCHESTRATION_URL=http://ai-orchestration-service:8050

# Service Config
ANALYTICS_PORT=8060
LOG_LEVEL=INFO
```

### 3. Run the Service

```bash
# Development mode with auto-reload
uvicorn app.main:app --host 0.0.0.0 --port 8060 --reload

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8060 --workers 4
```

### 4. Access API Documentation

Open your browser to:
- Swagger UI: `http://localhost:8060/docs`
- ReDoc: `http://localhost:8060/redoc`

## Docker Deployment

```bash
# Build image
docker build -t analytics-dashboard-service:latest .

# Run container
docker run -d \
  --name analytics-dashboard \
  -p 8060:8060 \
  --env-file .env \
  analytics-dashboard-service:latest
```

## Kubernetes Deployment

```bash
# Apply deployment
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

# Check status
kubectl get pods -l app=analytics-dashboard-service
```

## Health Checks

```bash
# Liveness probe
curl http://localhost:8060/health/live

# Readiness probe
curl http://localhost:8060/health/ready

# Full health check
curl http://localhost:8060/health
```

## Testing AI Features

### 1. Test AI Insight Engine

```bash
curl -X POST "http://localhost:8060/api/v1/ai/insight-engine/detect-anomalies/YOUR_BUSINESS_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "metric_type": "revenue",
    "time_series_data": [
      {"date": "2025-01-01", "value": 1000},
      {"date": "2025-01-02", "value": 1050},
      {"date": "2025-01-03", "value": 900},
      {"date": "2025-01-04", "value": 1100},
      {"date": "2025-01-05", "value": 3500},
      {"date": "2025-01-06", "value": 1000},
      {"date": "2025-01-07", "value": 1200}
    ]
  }'
```

### 2. Test Revenue Forecasting

```bash
curl -X POST "http://localhost:8060/api/v1/ai/predictive/forecast-revenue/YOUR_BUSINESS_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "business_category": "food",
    "historical_revenue": [
      {"date": "2025-01-01", "value": 1000},
      {"date": "2025-01-02", "value": 1100},
      {"date": "2025-01-03", "value": 1200}
    ],
    "forecast_period": 7
  }'
```

### 3. Test AI Copilot

```bash
curl -X POST "http://localhost:8060/api/v1/ai/copilot/chat/YOUR_BUSINESS_ID?user_id=YOUR_USER_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What was my total revenue last week?"
  }'
```

## Monitoring

### Prometheus Metrics

Access metrics at: `http://localhost:8060/metrics`

Key metrics:
- `x7bd_food_qr_requests_total` - Total requests
- `x7bd_food_qr_pdf_uploads_total` - PDF uploads
- Request duration histograms

### Logs

Logs are output to stdout in JSON format. Configure log aggregation:

```bash
# View logs
docker logs -f analytics-dashboard

# Kubernetes logs
kubectl logs -f deployment/analytics-dashboard-service
```

## Integration with Other Services

### 1. AI Orchestration Service

Ensure AI Orchestration Service is running:
```bash
curl http://ai-orchestration-service:8050/health
```

### 2. Auth Service

Test authentication:
```bash
curl -X POST "http://auth-service:8070/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123"
  }'
```

## Troubleshooting

### Issue: AI features returning fallback responses

**Solution:** Verify AI Orchestration Service is accessible

```bash
# Check connectivity
curl http://ai-orchestration-service:8050/health

# Check environment variable
echo $AI_ORCHESTRATION_URL
```

### Issue: Database connection errors

**Solution:** Verify Supabase credentials

```bash
# Test Supabase connection
curl "$SUPABASE_URL/rest/v1/" \
  -H "apikey: $SUPABASE_ANON_KEY"
```

### Issue: Import errors

**Solution:** Reinstall dependencies

```bash
pip install -r requirements.txt --force-reinstall
```

## Performance Tuning

### 1. Increase Workers

For production, use multiple workers:

```bash
uvicorn app.main:app --workers 4 --host 0.0.0.0 --port 8060
```

### 2. Enable Redis Caching

Configure Redis for conversation history and forecast caching:

```python
# In .env
REDIS_URL=redis://redis:6379/0
```

### 3. Database Connection Pooling

Configure Supabase connection pool:

```python
# Supabase automatically handles connection pooling
# Adjust max_connections if needed
```

## Security Checklist

- ✅ All endpoints require authentication (except health checks)
- ✅ Environment variables stored securely (never commit .env)
- ✅ HTTPS enabled in production
- ✅ Rate limiting configured
- ✅ CORS properly configured
- ✅ SQL injection protection (ORM queries)
- ✅ Input validation with Pydantic models

## Backup & Recovery

### Database Backups

Supabase handles automatic backups. To create manual backup:

```bash
# Export data
pg_dump $DATABASE_URL > backup.sql
```

### Configuration Backups

```bash
# Backup environment
cp .env .env.backup

# Version control
git commit -am "Update configuration"
```

## Scaling

### Horizontal Scaling

```bash
# Scale Kubernetes deployment
kubectl scale deployment analytics-dashboard-service --replicas=5

# Docker Swarm
docker service scale analytics-dashboard=5
```

### Vertical Scaling

Update resource limits in deployment:

```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "500m"
  limits:
    memory: "2Gi"
    cpu: "2000m"
```

## Support

For issues or questions:
1. Check logs first
2. Review this deployment guide
3. Contact X-sevenAI engineering team

---

**Version:** 3.0.0  
**Last Updated:** October 18, 2025  
**Status:** Production Ready ✅
