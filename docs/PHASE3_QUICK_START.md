# Phase 3 Quick Start Guide

## Overview

This guide helps you quickly set up and run the Phase 3 backend components.

## Prerequisites

- Python 3.11+
- Redis
- Kafka (optional, for event-driven notifications)
- PostgreSQL (Supabase)

## Installation

### 1. Install Dependencies

```bash
# AI Orchestration Service
cd services/ai-orchestration-service
pip install -r requirements.txt

# Notification Service
cd services/notification-integration-service
pip install -r requirements.txt

# Shared Libraries
cd shared/libs
pip install -r requirements.txt
```

### 2. Environment Configuration

Create `.env` files for each service:

**AI Orchestration Service** (`.env`):
```env
# Service Config
SERVICE_HOST=0.0.0.0
SERVICE_PORT=8001
ENVIRONMENT=development
LOG_LEVEL=INFO

# LLM Providers
OPENAI_API_KEY=your_openai_key
GROQ_API_KEY=your_groq_key
ANTHROPIC_API_KEY=your_anthropic_key

# Redis
REDIS_URL=redis://localhost:6379

# Observability
OTLP_ENDPOINT=http://localhost:4317
SENTRY_DSN=your_sentry_dsn

# Security
JWT_SECRET=your_jwt_secret
```

**Notification Service** (`.env`):
```env
# Service Config
SERVICE_HOST=0.0.0.0
SERVICE_PORT=8006
ENVIRONMENT=development
LOG_LEVEL=INFO

# Twilio
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890
TWILIO_WHATSAPP_NUMBER=+1234567890

# SendGrid
SENDGRID_API_KEY=your_sendgrid_key
SENDGRID_FROM_EMAIL=noreply@x7ai.com

# Zapier
ZAPIER_WEBHOOK_URL=your_webhook_url

# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# Redis
REDIS_URL=redis://localhost:6379
```

## Running Services

### 1. Start AI Orchestration Service

```bash
cd services/ai-orchestration-service
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

Access at: http://localhost:8001/docs

### 2. Start Notification Service

```bash
cd services/notification-integration-service
uvicorn app.main:app --host 0.0.0.0 --port 8006 --reload
```

Access at: http://localhost:8006/docs

## Testing Phase 3 Features

### 1. Crew AI Multi-Agent Workflows

**Customer Support Workflow**:
```bash
curl -X POST http://localhost:8001/api/v1/crew/customer-support \
  -H "Content-Type: application/json" \
  -d '{
    "customer_query": "I need to change my reservation time",
    "business_id": "biz_123",
    "business_name": "The Italian Place",
    "business_type": "restaurant"
  }'
```

**Business Onboarding Workflow**:
```bash
curl -X POST http://localhost:8001/api/v1/crew/business-onboarding \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Bella Salon",
    "business_type": "salon",
    "category": "beauty",
    "location": "New York, NY"
  }'
```

### 2. Notification Service

**Send SMS**:
```bash
curl -X POST http://localhost:8006/api/v1/notifications/sms \
  -H "Content-Type: application/json" \
  -d '{
    "to": "+1234567890",
    "message": "Your order is ready for pickup!"
  }'
```

**Send Email**:
```bash
curl -X POST http://localhost:8006/api/v1/notifications/email \
  -H "Content-Type: application/json" \
  -d '{
    "to_email": "customer@example.com",
    "subject": "Order Confirmation",
    "html_content": "<h1>Thank you for your order!</h1>"
  }'
```

**Send WhatsApp**:
```bash
curl -X POST http://localhost:8006/api/v1/notifications/whatsapp \
  -H "Content-Type: application/json" \
  -d '{
    "to": "+1234567890",
    "message": "Your reservation is confirmed for 7 PM tonight!"
  }'
```

### 3. OpenTelemetry Tracing

Enable tracing in your service:

```python
from shared.libs.telemetry import TelemetryManager

# Initialize
telemetry = TelemetryManager(
    service_name="my-service",
    otlp_endpoint="http://localhost:4317"
)
telemetry.initialize()
telemetry.instrument_fastapi(app)
```

View traces in Jaeger: http://localhost:16686

### 4. Sentry Error Tracking

Enable Sentry:

```python
from shared.libs.sentry_integration import SentryManager

sentry = SentryManager(
    dsn="your-sentry-dsn",
    environment="development",
    service_name="my-service"
)
sentry.initialize()
```

### 5. Chaos Engineering

Enable chaos mode for testing:

```python
from shared.libs.chaos_engineering import chaos_config, chaos_latency

# Enable chaos
chaos_config.enabled = True
chaos_config.failure_rate = 0.1

# Use decorators
@chaos_latency(min_ms=100, max_ms=1000)
async def my_function():
    # This will have random latency injected
    pass
```

### 6. Security & RBAC

Add security middleware:

```python
from shared.libs.security_middleware import SecurityMiddleware, RateLimiter, RBACManager

# Setup
rate_limiter = RateLimiter(redis_client, default_limit=100)
rbac_manager = RBACManager()

# Add middleware
app.add_middleware(
    SecurityMiddleware,
    rate_limiter=rate_limiter,
    rbac_manager=rbac_manager,
    jwt_secret="your-secret"
)

# Protect endpoints
from shared.libs.security_middleware import require_permission

@app.post("/orders")
@require_permission("orders:create")
async def create_order(request: Request):
    # Only users with orders:create permission
    pass
```

## Monitoring & Observability

### Prometheus Metrics

Access metrics:
- AI Orchestration: http://localhost:8001/metrics
- Notification Service: http://localhost:8006/metrics

### Health Checks

- AI Orchestration: http://localhost:8001/api/v1/health
- Notification Service: http://localhost:8006/api/v1/health

### API Documentation

- AI Orchestration: http://localhost:8001/docs
- Notification Service: http://localhost:8006/docs

## Common Issues & Solutions

### Issue: Redis Connection Failed
**Solution**: Ensure Redis is running
```bash
redis-server
```

### Issue: Kafka Not Available
**Solution**: Start Kafka or disable Kafka consumer
```bash
# Start Kafka
docker run -d -p 9092:9092 apache/kafka
```

### Issue: OpenTelemetry Export Failed
**Solution**: Start Jaeger
```bash
docker run -d -p 16686:16686 -p 4317:4317 jaegertracing/all-in-one:latest
```

### Issue: Rate Limit Errors
**Solution**: Increase rate limits in configuration
```python
rate_limiter = RateLimiter(
    redis_client,
    default_limit=1000,  # Increase limit
    window_seconds=60
)
```

## Development Tips

### 1. Hot Reload
Both services support hot reload in development mode:
```bash
uvicorn app.main:app --reload
```

### 2. Debug Logging
Enable debug logging:
```env
LOG_LEVEL=DEBUG
```

### 3. Testing Crew AI Locally
Use smaller models for faster testing:
```python
# In crew_orchestrator.py
self.llm = ChatOpenAI(
    model="gpt-3.5-turbo",  # Faster for testing
    temperature=0.7
)
```

### 4. Mock External Services
For testing without external dependencies:
```python
# Mock Twilio
TWILIO_ACCOUNT_SID=test_sid
TWILIO_AUTH_TOKEN=test_token
```

## Next Steps

1. **Configure Production Settings**: Update `.env` files with production credentials
2. **Setup Monitoring**: Configure Prometheus, Grafana, Jaeger
3. **Security Hardening**: Enable HTTPS, configure proper JWT secrets
4. **Load Testing**: Run performance tests with Locust
5. **Deploy to Kubernetes**: Use provided K8s manifests

## Support

For issues or questions:
- Check logs: `tail -f logs/service.log`
- Review API docs: http://localhost:PORT/docs
- Check health: http://localhost:PORT/api/v1/health

---

**Happy Coding! 🚀**
