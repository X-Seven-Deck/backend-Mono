# Xseven POS Microservice

Enterprise-grade Point of Sale microservice for small to medium-sized businesses in the hospitality industry.

## Features

- **Order Management**: Create, track, and manage orders from initiation to completion
- **Payment Processing**: Record payment methods (cash/card) without transaction processing
- **Receipt Generation**: Digital receipts with tax calculations and full order details
- **Tax Engine**: Location-based tax calculation with multiple tax types (VAT, GST, sales tax)
- **Mobile-Optimized APIs**: Lightweight endpoints for mobile app integration
- **Real-time Updates**: WebSocket support for live order status updates

## Architecture

- **Framework**: FastAPI 0.115.5
- **Database**: PostgreSQL via Supabase
- **Authentication**: JWT-based security
- **Monitoring**: Prometheus metrics
- **API Versioning**: `/api/v1/pos/`

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL (via Supabase)
- Redis (optional, for caching)

### Installation

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Run the service**:
   ```bash
   python -m app.main
   ```

   Or with uvicorn:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8070 --reload
   ```

## API Endpoints

### Orders
- `POST /api/v1/pos/orders/` - Create new order
- `GET /api/v1/pos/orders/{order_id}` - Get order details
- `GET /api/v1/pos/orders/` - List orders
- `GET /api/v1/pos/orders/active/summary` - Get active orders (mobile-optimized)
- `PUT /api/v1/pos/orders/{order_id}` - Update order
- `PUT /api/v1/pos/orders/{order_id}/status` - Update order status
- `DELETE /api/v1/pos/orders/{order_id}` - Cancel order

### Payments
- `POST /api/v1/pos/payments/` - Record payment
- `GET /api/v1/pos/payments/{payment_id}` - Get payment details
- `GET /api/v1/pos/payments/order/{order_id}` - Get payment for order

### Receipts
- `POST /api/v1/pos/receipts/` - Generate receipt
- `GET /api/v1/pos/receipts/{receipt_id}` - Get receipt data
- `GET /api/v1/pos/receipts/{receipt_id}/html` - Get receipt as HTML
- `GET /api/v1/pos/receipts/order/{order_id}` - Get receipt for order

### Tax
- `POST /api/v1/pos/tax/rules` - Create tax rule
- `GET /api/v1/pos/tax/rules` - Get tax rules
- `POST /api/v1/pos/tax/calculate` - Calculate tax

## Configuration

Key environment variables:

```env
# Service
POS_SERVICE_PORT=8070
ENVIRONMENT=development

# Database
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_KEY=your_service_key

# Authentication
JWT_SECRET=your_jwt_secret

# Tax
DEFAULT_TAX_RATE=0.10
TAX_CALCULATION_MODE=location_based
```

## Database Schema

The service uses existing Supabase tables:
- `orders` - Order records
- `order_items` - Order line items
- `payments` - Payment records
- `receipts` - Generated receipts
- `tax_rules` - Tax configuration
- `menu_items` - Menu items (read-only)
- `tables` - Table management (read-only)

## Development

### Run tests
```bash
pytest
```

### API Documentation
- Swagger UI: http://localhost:8070/api/v1/pos/docs
- ReDoc: http://localhost:8070/api/v1/pos/redoc

### Health Check
```bash
curl http://localhost:8070/health
```

## Integration

### With Dashboard Service
The POS service integrates with the Analytics Dashboard Service for:
- Menu item data
- Table management
- Staff information
- Business settings

### With Mobile App
Mobile-optimized endpoints provide:
- Lightweight JSON responses
- Pagination for large datasets
- Real-time order updates
- Offline order queuing support

## Security

- JWT token authentication required for all endpoints
- Role-based access control (staff, admin, manager)
- Business-level data isolation
- Input validation with Pydantic models

## Monitoring

Prometheus metrics available at `/metrics`:
- `pos_requests_total` - Total request count
- `pos_request_duration_seconds` - Request duration histogram

## License

Proprietary - Xseven AI

## Support

For issues or questions, contact the development team.


uvicorn app.main:app --reload --port 8070