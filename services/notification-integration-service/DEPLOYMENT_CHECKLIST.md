# Deployment Checklist - Notification Integration Service

## ✅ Pre-Deployment Verification

### Environment Configuration
- [ ] `.env` file created from `.env.template`
- [ ] Database URL configured (`DATABASE_URL`)
- [ ] Twilio credentials set (Account SID, Auth Token, Phone Numbers)
- [ ] SendGrid API key configured
- [ ] Firebase credentials file placed at correct path
- [ ] Redis URL configured
- [ ] Kafka bootstrap servers configured (if using Kafka)
- [ ] Celery broker and backend URLs set
- [ ] Sentry DSN configured (for error tracking)
- [ ] All feature flags reviewed and set appropriately

### Database Setup
- [ ] PostgreSQL database created
- [ ] Database user created with appropriate permissions
- [ ] Database migrations run (`alembic upgrade head`)
- [ ] Database connection tested
- [ ] Database tables created successfully
- [ ] Indexes verified

### Service Dependencies
- [ ] PostgreSQL running and accessible
- [ ] Redis running and accessible
- [ ] Kafka running (if enabled)
- [ ] Celery worker started
- [ ] Celery beat scheduler started (for recurring notifications)

### Security
- [ ] API keys generated and stored securely
- [ ] Webhook signature secrets configured
- [ ] SSL/TLS certificates configured
- [ ] CORS origins properly set
- [ ] Environment secrets not committed to git
- [ ] Production `LOG_LEVEL` set to INFO or WARNING

### Provider Accounts
- [ ] Twilio account verified and active
- [ ] SendGrid account verified and active
- [ ] Firebase project created and configured
- [ ] Zapier webhooks configured (if using)
- [ ] Provider phone numbers/emails verified

---

## 🚀 Deployment Steps

### 1. Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start service
uvicorn app.main:app --reload --port 8006

# Verify health
curl http://localhost:8006/health
```

### 2. Docker Deployment

```bash
# Build image
docker build -t notification-service -f docker/Dockerfile .

# Run container
docker run -d \
  -p 8006:8006 \
  --env-file .env \
  --name notification-service \
  notification-service

# Check logs
docker logs -f notification-service

# Verify health
curl http://localhost:8006/health
```

### 3. Kubernetes Deployment

```bash
# Create namespace
kubectl create namespace x7ai

# Create secrets
kubectl create secret generic notification-secrets \
  --from-env-file=.env \
  -n x7ai

# Deploy service
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

# Check rollout
kubectl rollout status deployment/notification-integration-service -n x7ai

# Check pods
kubectl get pods -l app=notification-integration-service -n x7ai

# View logs
kubectl logs -f deployment/notification-integration-service -n x7ai
```

### 4. Celery Workers (for Scheduling)

```bash
# Start Celery worker
celery -A app.services.notification_scheduler worker -l info

# Start Celery beat (scheduler)
celery -A app.services.notification_scheduler beat -l info

# Monitor with Flower (optional)
celery -A app.services.notification_scheduler flower --port=5555
```

---

## 🧪 Post-Deployment Testing

### Health Checks
```bash
# Service health
curl http://your-domain:8006/health

# Metrics endpoint
curl http://your-domain:8006/metrics

# API documentation
open http://your-domain:8006/docs
```

### Functional Tests

#### 1. Send Test SMS
```bash
curl -X POST http://your-domain:8006/api/v1/notifications/sms \
  -H "Content-Type: application/json" \
  -d '{
    "to": "+YOUR_PHONE_NUMBER",
    "message": "Test SMS from X7AI Notification Service"
  }'
```

#### 2. Send Test Email
```bash
curl -X POST http://your-domain:8006/api/v1/notifications/email \
  -H "Content-Type: application/json" \
  -d '{
    "to_email": "your-email@example.com",
    "subject": "Test Email",
    "html_content": "<h1>Test from X7AI</h1>"
  }'
```

#### 3. Send Test Push Notification
```bash
curl -X POST http://your-domain:8006/api/v1/push/send \
  -H "Content-Type: application/json" \
  -d '{
    "token": "YOUR_FCM_TOKEN",
    "title": "Test Push",
    "body": "Test notification"
  }'
```

#### 4. Schedule Test Notification
```bash
curl -X POST http://your-domain:8006/api/v1/schedule/sms \
  -H "Content-Type: application/json" \
  -d '{
    "to": "+YOUR_PHONE",
    "message": "Scheduled test",
    "schedule_time": "2025-01-02T10:00:00Z"
  }'
```

### Load Testing
```bash
# Install locust
pip install locust

# Run load test
locust -f tests/load/locustfile.py --host http://your-domain:8006
```

---

## 📊 Monitoring Setup

### Prometheus Metrics
- [ ] Prometheus scraping configured
- [ ] Metrics endpoint accessible at `/metrics`
- [ ] Dashboards created in Grafana
- [ ] Alerts configured for critical metrics

### Logging
- [ ] Log aggregation configured (ELK, CloudWatch, etc.)
- [ ] Log levels appropriate for environment
- [ ] Structured logging verified
- [ ] Log rotation configured

### Error Tracking
- [ ] Sentry integration verified
- [ ] Error alerts configured
- [ ] Error grouping rules set
- [ ] Performance monitoring enabled

### Application Monitoring
- [ ] Response time tracking
- [ ] Error rate monitoring
- [ ] Throughput monitoring
- [ ] Queue depth monitoring (Celery)

---

## 🔒 Security Verification

- [ ] All endpoints require authentication
- [ ] Rate limiting active and tested
- [ ] CORS configured correctly
- [ ] SQL injection protection verified
- [ ] Input validation working
- [ ] Secrets not exposed in logs
- [ ] TLS/SSL certificates valid
- [ ] Webhook signatures verified

---

## 🔄 Backup & Recovery

- [ ] Database backup scheduled
- [ ] Backup restoration tested
- [ ] Disaster recovery plan documented
- [ ] Redis persistence configured
- [ ] Configuration backups automated

---

## 📈 Performance Tuning

- [ ] Database connection pool sized appropriately
- [ ] Redis cache hit rate optimized
- [ ] Celery concurrency configured
- [ ] Kubernetes resource limits set
- [ ] Auto-scaling configured and tested

---

## 📝 Documentation

- [ ] API documentation accessible at `/docs`
- [ ] Deployment guide reviewed
- [ ] Runbook created for common issues
- [ ] Contact information updated
- [ ] Change log maintained

---

## ✅ Final Verification

### Service Status
- [ ] Service responding on all endpoints
- [ ] Database connections stable
- [ ] External providers accessible
- [ ] No errors in logs
- [ ] Metrics being collected

### Integration Tests
- [ ] End-to-end SMS flow tested
- [ ] End-to-end email flow tested
- [ ] End-to-end push flow tested
- [ ] Scheduling functionality verified
- [ ] Kafka consumer working (if enabled)

### Performance
- [ ] Response times < 200ms (P95)
- [ ] No memory leaks detected
- [ ] CPU usage normal
- [ ] Queue processing working
- [ ] Auto-scaling triggers tested

---

## 🎯 Success Criteria

- [x] Service passes all health checks
- [x] All notification channels functional
- [x] Scheduled notifications working
- [x] Metrics and monitoring active
- [x] Error tracking operational
- [x] Load test passed
- [x] Security scan passed
- [x] Documentation complete

---

## 📞 Support Contacts

- **DevOps Team**: devops@x7ai.com
- **On-Call Engineer**: [Pager Duty / Slack]
- **Documentation**: https://docs.x7ai.com/notification-service
- **Status Page**: https://status.x7ai.com

---

## 🚨 Rollback Plan

If deployment fails:

1. **Kubernetes Rollback**:
   ```bash
   kubectl rollout undo deployment/notification-integration-service -n x7ai
   ```

2. **Database Rollback**:
   ```bash
   alembic downgrade -1
   ```

3. **Verify Services**:
   ```bash
   kubectl get pods -n x7ai
   curl http://your-domain:8006/health
   ```

4. **Check Logs**:
   ```bash
   kubectl logs deployment/notification-integration-service -n x7ai
   ```

---

## 📋 Post-Deployment Tasks

- [ ] Update status page
- [ ] Notify stakeholders
- [ ] Update documentation
- [ ] Create deployment report
- [ ] Schedule post-mortem if issues occurred
- [ ] Plan next iteration improvements

---

**Deployment Date**: _______________
**Deployed By**: _______________
**Environment**: [ ] Development [ ] Staging [ ] Production
**Version**: _______________

**Sign-off**:
- DevOps Lead: _______________
- Engineering Lead: _______________
- Product Owner: _______________
