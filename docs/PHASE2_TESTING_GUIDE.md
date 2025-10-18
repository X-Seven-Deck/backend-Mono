# 🧪 Phase 2 Testing Guide

## Quick Start Testing

### 1. Start Services

```bash
# Start all services
docker-compose up -d

# Check service health
docker-compose ps

# View logs
docker-compose logs -f business-logic-service
```

### 2. Verify Business Logic Service

```bash
# Health check
curl http://localhost:8020/health

# Check API docs
open http://localhost:8020/docs
```

---

## Template-Specific API Testing

### Food & Hospitality Template

```bash
# Create restaurant order
curl -X POST http://localhost:8020/api/v1/template/food-hospitality/orders \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: tenant_001" \
  -d '{
    "business_id": "biz_001",
    "items": [
      {"name": "Burger", "price": 12.99, "quantity": 2},
      {"name": "Fries", "price": 4.99, "quantity": 1}
    ],
    "table_number": "5"
  }'

# Optimize menu
curl -X POST http://localhost:8020/api/v1/template/food-hospitality/menu/optimize?business_id=biz_001 \
  -H "X-Tenant-ID: tenant_001"

# Get table status
curl http://localhost:8020/api/v1/template/food-hospitality/tables/status?business_id=biz_001 \
  -H "X-Tenant-ID: tenant_001"
```

### Service-Based Template

```bash
# Create appointment
curl -X POST http://localhost:8020/api/v1/template/service-based/appointments \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: tenant_002" \
  -d '{
    "business_id": "biz_002",
    "service_type": "haircut",
    "client_id": "client_123",
    "scheduled_time": "2025-10-08T10:00:00Z",
    "duration": 60
  }'

# Optimize schedule
curl http://localhost:8020/api/v1/template/service-based/schedule/optimize?business_id=biz_002&date=2025-10-08 \
  -H "X-Tenant-ID: tenant_002"

# Optimize routes
curl http://localhost:8020/api/v1/template/service-based/routes/optimize?business_id=biz_002&date=2025-10-08 \
  -H "X-Tenant-ID: tenant_002"
```

### Retail & E-commerce Template

```bash
# Create retail order
curl -X POST http://localhost:8020/api/v1/template/retail/orders \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: tenant_003" \
  -d '{
    "business_id": "biz_003",
    "customer_id": "cust_456",
    "items": [
      {"name": "T-Shirt", "price": 29.99, "quantity": 2}
    ],
    "shipping_cost": 5.99
  }'

# Dynamic pricing
curl -X POST http://localhost:8020/api/v1/template/retail/pricing/dynamic \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: tenant_003" \
  -d '{"product_id": "prod_123"}'

# Inventory forecast
curl http://localhost:8020/api/v1/template/retail/inventory/forecast?business_id=biz_003 \
  -H "X-Tenant-ID: tenant_003"
```

### Professional Services Template

```bash
# Create project
curl -X POST http://localhost:8020/api/v1/template/professional/projects \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: tenant_004" \
  -d '{
    "business_id": "biz_004",
    "client_id": "client_789",
    "project_name": "Website Redesign",
    "estimated_hours": 120,
    "hourly_rate": 150
  }'

# Get profitability
curl http://localhost:8020/api/v1/template/professional/projects/prj_123/profitability?business_id=biz_004 \
  -H "X-Tenant-ID: tenant_004"

# Resource allocation
curl http://localhost:8020/api/v1/template/professional/resources/allocation?business_id=biz_004 \
  -H "X-Tenant-ID: tenant_004"
```

---

## AI Features Testing

### 1. Customer Retention Predictor

```bash
curl http://localhost:8020/api/v1/ai-features/retention/predict/cust_123?business_id=biz_001 \
  -H "X-Tenant-ID: tenant_001"
```

### 2. Smart Menu Optimizer

```bash
curl -X POST http://localhost:8020/api/v1/ai-features/optimizer/menu \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: tenant_001" \
  -d '{
    "business_id": "biz_001",
    "menu_data": [
      {"id": "item_1", "name": "Burger", "price": 12.99},
      {"id": "item_2", "name": "Pizza", "price": 15.99}
    ]
  }'
```

### 3. Dynamic Pricing Engine

```bash
curl -X POST http://localhost:8020/api/v1/ai-features/pricing/calculate \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: tenant_003" \
  -d '{
    "product_id": "prod_123",
    "current_price": 29.99
  }'
```

### 4. AI Route Optimizer

```bash
curl -X POST http://localhost:8020/api/v1/ai-features/routes/optimize \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: tenant_002" \
  -d '{
    "business_id": "biz_002",
    "appointments": [
      {"id": "apt_1", "address": "123 Main St"},
      {"id": "apt_2", "address": "456 Oak Ave"}
    ]
  }'
```

### 5. Project Profitability Analyzer

```bash
curl http://localhost:8020/api/v1/ai-features/profitability/analyze/prj_123?business_id=biz_004 \
  -H "X-Tenant-ID: tenant_004"
```

### 6. What-If Simulator

```bash
curl -X POST http://localhost:8020/api/v1/ai-features/simulator/scenario \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: tenant_001" \
  -d '{
    "business_id": "biz_001",
    "scenario_type": "price_increase",
    "parameters": {
      "current_revenue": 100000,
      "price_change_percent": 10
    }
  }'
```

### 7. Competitor & Market Watchdog

```bash
curl http://localhost:8020/api/v1/ai-features/market/competitors/biz_001?industry=restaurant \
  -H "X-Tenant-ID: tenant_001"
```

---

## Integration Testing

### Test Template Selection → Business Logic Flow

```bash
# 1. Select template
curl -X POST http://localhost:8090/api/v1/template-selection/select \
  -H "Content-Type: application/json" \
  -d '{
    "business_id": "biz_test_001",
    "business_name": "Test Restaurant",
    "category": "restaurant",
    "subscription_tier": "premium"
  }'

# 2. Create tenant with template
curl -X POST http://localhost:8020/api/v1/tenants \
  -H "Content-Type: application/json" \
  -d '{
    "business_id": "biz_test_001",
    "business_name": "Test Restaurant",
    "tier": "premium",
    "template_type": "food_hospitality"
  }'

# 3. Use template-specific endpoint
curl -X POST http://localhost:8020/api/v1/template/food-hospitality/orders \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: biz_test_001" \
  -d '{
    "business_id": "biz_test_001",
    "items": [{"name": "Test Item", "price": 10.00, "quantity": 1}]
  }'
```

---

## Performance Testing

### Load Test Template APIs

```bash
# Install Apache Bench if needed
# brew install httpd (macOS)

# Test order creation endpoint
ab -n 1000 -c 10 -p order_payload.json -T application/json \
  http://localhost:8020/api/v1/template/food-hospitality/orders
```

### Monitor Metrics

```bash
# View Prometheus metrics
curl http://localhost:8020/metrics

# Access Grafana
open http://localhost:3000
# Login: admin/admin
```

---

## Troubleshooting

### Check Service Logs

```bash
# Business Logic Service
docker-compose logs -f business-logic-service

# All services
docker-compose logs -f
```

### Restart Services

```bash
# Restart specific service
docker-compose restart business-logic-service

# Rebuild and restart
docker-compose up -d --build business-logic-service
```

### Database Connection

```bash
# Check if services can connect to dependencies
docker-compose exec business-logic-service ping redis
docker-compose exec business-logic-service ping kafka
```

---

## Success Criteria

✅ All health endpoints return 200
✅ Template-specific APIs respond correctly
✅ AI features return predictions
✅ Tenant middleware works
✅ Metrics are collected
✅ No errors in logs

---

## Next Steps

1. ✅ Phase 1 Complete - Template Selection & Multi-Tenancy
2. ✅ Phase 2 Complete - Template Ecosystem & Data Architecture
3. 🔄 Phase 3 Pending - DevOps Excellence & Business Continuity
