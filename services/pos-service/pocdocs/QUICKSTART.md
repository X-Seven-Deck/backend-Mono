# POS Service Quick Start Guide

## Prerequisites
- Python 3.11+
- Supabase account with project set up
- JWT secret key
- (Optional) Redis for caching

## Step 1: Environment Setup

1. **Navigate to POS service directory**:
   ```bash
   cd services/pos-service
   ```

2. **Create virtual environment** (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Step 2: Configuration

1. **Copy environment template**:
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` file** with your credentials:
   ```env
   # Required
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_SERVICE_KEY=your-service-role-key
   JWT_SECRET=your-secret-key-min-32-chars
   
   # Optional (defaults provided)
   POS_SERVICE_PORT=8070
   DEFAULT_TAX_RATE=0.10
   ```

## Step 3: Verify Database Tables

Ensure these tables exist in your Supabase database:
- ✅ `orders`
- ✅ `order_items`
- ✅ `payments`
- ✅ `menu_items`
- ✅ `tables`
- ✅ `staff_members`

**Note**: The service will use existing tables. If `receipts` or `tax_rules` tables don't exist, you may need to create them.

## Step 4: Run the Service

### Development Mode
```bash
python -m app.main
```

Or with uvicorn:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8070 --reload
```

### Production Mode (Docker)
```bash
docker-compose up -d
```

## Step 5: Verify Installation

1. **Check health endpoint**:
   ```bash
   curl http://localhost:8070/health
   ```
   
   Expected response:
   ```json
   {
     "status": "healthy",
     "service": "pos-service",
     "version": "1.0.0",
     "timestamp": "2025-10-06T..."
   }
   ```

2. **Access API documentation**:
   - Swagger UI: http://localhost:8070/api/v1/pos/docs
   - ReDoc: http://localhost:8070/api/v1/pos/redoc

## Step 6: Test Basic Flow

### 1. Get JWT Token
First, authenticate with your auth service to get a JWT token.

### 2. Create an Order
```bash
curl -X POST http://localhost:8070/api/v1/pos/orders/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "business_id": "your-business-uuid",
    "customer_count": 2,
    "items": [
      {
        "menu_item_id": "menu-item-uuid",
        "quantity": 2,
        "unit_price": 15.99,
        "modifiers": []
      }
    ]
  }'
```

### 3. Record Payment
```bash
curl -X POST http://localhost:8070/api/v1/pos/payments/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "order-uuid-from-step-2",
    "payment_method": "cash",
    "amount": 35.18
  }'
```

### 4. Generate Receipt
```bash
curl -X POST http://localhost:8070/api/v1/pos/receipts/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "order-uuid-from-step-2",
    "business_id": "your-business-uuid"
  }'
```

## Common Issues & Solutions

### Issue: "SUPABASE_URL and SUPABASE_SERVICE_KEY must be set"
**Solution**: Ensure `.env` file exists and contains valid Supabase credentials.

### Issue: "Invalid authentication credentials"
**Solution**: Verify JWT token is valid and not expired. Check JWT_SECRET matches auth service.

### Issue: "Order not found" or "Menu item not found"
**Solution**: Ensure UUIDs are correct and data exists in Supabase tables.

### Issue: Port 8070 already in use
**Solution**: Change `POS_SERVICE_PORT` in `.env` or stop conflicting service.

## Integration with Other Services

### With Analytics Dashboard
The POS service reads from shared Supabase tables:
- Menu items
- Tables
- Staff members
- Business settings

### With Mobile App
Mobile apps should:
1. Authenticate with auth service to get JWT token
2. Use token to call POS endpoints
3. Handle responses and display to users

## Monitoring

### Prometheus Metrics
Available at: http://localhost:8070/metrics

Key metrics:
- `pos_requests_total` - Total request count
- `pos_request_duration_seconds` - Request duration

### Logs
Service logs to stdout. In production, configure log aggregation.

## Next Steps

1. ✅ Configure tax rules for your business
2. ✅ Test order flow end-to-end
3. ✅ Integrate with mobile app
4. ✅ Set up monitoring and alerts
5. ✅ Configure backup and disaster recovery

## Support

For issues or questions:
- Check logs: `docker-compose logs pos-service`
- Review API docs: http://localhost:8070/api/v1/pos/docs
- Check implementation summary: `IMPLEMENTATION_SUMMARY.md`

---

**Service Status**: ✅ Ready for Production
**Port**: 8070
**API Version**: v1
