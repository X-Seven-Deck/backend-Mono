# POS Service API Documentation

## Version: 1.0.0
## Base URL: `http://localhost:8070` or `https://api.x7ai.com/pos`

---

## Table of Contents
1. [Authentication](#authentication)
2. [Orders API](#orders-api)
3. [Payments API](#payments-api)
4. [Receipts API](#receipts-api)
5. [Tax API](#tax-api)
6. [WebSocket API](#websocket-api)
7. [Offline API](#offline-api)
8. [Analytics API](#analytics-api)
9. [Customers API](#customers-api)
10. [Error Handling](#error-handling)

---

## Authentication

All API endpoints (except health check) require JWT authentication.

### Headers
```
Authorization: Bearer <JWT_TOKEN>
```

### JWT Claims
- `sub`: User ID
- `business_id`: Business ID
- `role`: User role (staff, admin, owner, manager)
- `email`: User email

---

## Orders API

### Create Order
**POST** `/api/v1/pos/orders/`

Creates a new order with items.

**Request Body:**
```json
{
  "business_id": "uuid",
  "table_id": "uuid",
  "customer_id": "uuid",
  "customer_count": 2,
  "items": [
    {
      "menu_item_id": "uuid",
      "quantity": 2,
      "unit_price": 12.99,
      "modifiers": [
        {"name": "Extra Cheese", "price": 1.50}
      ],
      "special_instructions": "No onions"
    }
  ],
  "notes": "Birthday celebration",
  "staff_id": "uuid"
}
```

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "business_id": "uuid",
  "order_number": "ORD-20241018123456",
  "table_id": "uuid",
  "status": "new",
  "subtotal": 25.98,
  "tax_amount": 2.60,
  "total_amount": 28.58,
  "items": [...],
  "created_at": "2024-10-18T12:34:56Z"
}
```

### Get Order
**GET** `/api/v1/pos/orders/{order_id}`

Retrieves order with full details including items.

**Response:** `200 OK`

### List Orders
**GET** `/api/v1/pos/orders/`

Lists orders with filtering and pagination.

**Query Parameters:**
- `status`: Filter by status (new, confirmed, preparing, ready, served, completed, cancelled)
- `table_id`: Filter by table
- `limit`: Number of results (1-100, default: 50)
- `offset`: Pagination offset (default: 0)

### Get Active Orders
**GET** `/api/v1/pos/orders/active/summary`

Returns mobile-optimized summary of active orders.

**Response:** `200 OK`
```json
[
  {
    "id": "uuid",
    "order_number": "ORD-123",
    "status": "preparing",
    "table_number": "T1",
    "total_amount": 28.58,
    "item_count": 2,
    "created_at": "2024-10-18T12:34:56Z"
  }
]
```

### Update Order
**PUT** `/api/v1/pos/orders/{order_id}`

Updates order details.

### Update Order Status
**PUT** `/api/v1/pos/orders/{order_id}/status`

Updates order status.

**Query Parameters:**
- `status`: new, confirmed, preparing, ready, served, completed, cancelled

### Cancel Order
**DELETE** `/api/v1/pos/orders/{order_id}`

Cancels order and frees table.

**Response:** `204 No Content`

---

## Payments API

### Create Payment
**POST** `/api/v1/pos/payments/`

Records payment for an order.

**Request Body:**
```json
{
  "order_id": "uuid",
  "payment_method": "cash",
  "amount": 28.58,
  "tip_amount": 5.00,
  "transaction_id": "TXN-123",
  "notes": "Change given: $1.42"
}
```

**Response:** `201 Created`

### Get Payment
**GET** `/api/v1/pos/payments/{payment_id}`

Retrieves payment details.

### Get Payment by Order
**GET** `/api/v1/pos/payments/order/{order_id}`

Retrieves payment for specific order.

---

## Receipts API

### Generate Receipt
**POST** `/api/v1/pos/receipts/`

Generates receipt for an order.

**Request Body:**
```json
{
  "order_id": "uuid",
  "business_id": "uuid",
  "generated_by": "uuid"
}
```

**Response:** `201 Created`

### Get Receipt
**GET** `/api/v1/pos/receipts/{receipt_id}`

Retrieves receipt data in JSON format.

### Get Receipt HTML
**GET** `/api/v1/pos/receipts/{receipt_id}/html`

Returns receipt as formatted HTML for display or printing.

### Get Receipt PDF
**GET** `/api/v1/pos/receipts/{receipt_id}/pdf`

Downloads receipt as PDF file.

### Get Receipt by Order
**GET** `/api/v1/pos/receipts/order/{order_id}`

Retrieves receipt for specific order.

---

## Tax API

### Create Tax Rule
**POST** `/api/v1/pos/tax/rules`

Creates tax rule for business/location.

**Request Body:**
```json
{
  "business_id": "uuid",
  "location_id": "uuid",
  "name": "State Sales Tax",
  "rate": 0.0875,
  "type": "sales_tax",
  "is_active": true
}
```

### Get Tax Rules
**GET** `/api/v1/pos/tax/rules`

Lists active tax rules.

**Query Parameters:**
- `location_id`: Filter by location
- `is_active`: Filter by active status (default: true)

### Calculate Tax
**POST** `/api/v1/pos/tax/calculate`

Calculates tax for given amount.

**Request Body:**
```json
{
  "business_id": "uuid",
  "location_id": "uuid",
  "subtotal": 100.00,
  "items": []
}
```

**Response:** `200 OK`
```json
{
  "subtotal": 100.00,
  "tax_rate": 0.0875,
  "tax_amount": 8.75,
  "total_with_tax": 108.75,
  "tax_breakdown": {
    "State Sales Tax": 8.75
  }
}
```

---

## WebSocket API

### Orders WebSocket
**WS** `/api/v1/pos/ws/orders?token=<JWT_TOKEN>`

Real-time order updates.

**Client → Server Messages:**
```json
{"type": "ping"}
```

**Server → Client Messages:**
```json
{
  "type": "order_created",
  "data": {
    "order_id": "uuid",
    "status": "new",
    "total_amount": 28.58
  },
  "timestamp": "2024-10-18T12:34:56Z"
}
```

**Event Types:**
- `order_created`: New order created
- `order_updated`: Order details updated
- `order_status_changed`: Order status changed
- `order_cancelled`: Order cancelled
- `order_completed`: Order completed with payment

### Tables WebSocket
**WS** `/api/v1/pos/ws/tables?token=<JWT_TOKEN>`

Real-time table status updates.

**Event Types:**
- `table_occupied`: Table marked as occupied
- `table_available`: Table marked as available
- `table_reserved`: Table reserved
- `table_cleaning`: Table being cleaned

---

## Offline API

### Queue Offline Order
**POST** `/api/v1/pos/offline/orders/queue`

Queues order created while offline.

**Request Body:**
```json
{
  "client_id": "client-generated-uuid",
  "order": { /* OrderCreate object */ },
  "created_at_client": "2024-10-18T12:34:56Z",
  "device_info": {
    "device_id": "DEVICE-123",
    "app_version": "1.0.0"
  }
}
```

**Response:** `200 OK`
```json
{
  "status": "success",
  "client_id": "client-generated-uuid",
  "server_id": "server-uuid",
  "message": "Order synchronized successfully"
}
```

### Batch Sync Orders
**POST** `/api/v1/pos/offline/orders/batch-sync`

Synchronizes multiple offline orders.

**Request Body:**
```json
{
  "orders": [/* Array of OfflineOrder */]
}
```

**Response:** `200 OK`
```json
{
  "results": [
    {
      "client_id": "...",
      "server_id": "...",
      "status": "success",
      "error": null
    }
  ],
  "total_count": 10,
  "success_count": 9,
  "failed_count": 1,
  "duplicate_count": 0
}
```

### Check Order Status
**GET** `/api/v1/pos/offline/orders/status/{client_id}`

Checks if offline order has been synchronized.

---

## Analytics API

### Sales Analytics
**GET** `/api/v1/pos/analytics/sales`

Gets sales analytics for time period.

**Query Parameters:**
- `start_date`: Start date (YYYY-MM-DD)
- `end_date`: End date (YYYY-MM-DD)
- `period`: day, week, month

**Response:** `200 OK`
```json
{
  "period": "day",
  "start_date": "2024-10-18T00:00:00Z",
  "end_date": "2024-10-18T23:59:59Z",
  "total_revenue": 1250.00,
  "total_orders": 45,
  "average_order_value": 27.78,
  "total_tax": 125.00,
  "total_tips": 200.00,
  "payment_breakdown": {
    "cash": 500.00,
    "card": 750.00
  },
  "hourly_breakdown": [
    {"hour": 12, "orders": 8, "revenue": 220.00}
  ]
}
```

### Top Items
**GET** `/api/v1/pos/analytics/items/top`

Gets top-selling items.

**Query Parameters:**
- `start_date`: Start date
- `end_date`: End date
- `limit`: Number of items (1-100, default: 10)

**Response:** `200 OK`
```json
[
  {
    "item_id": "uuid",
    "item_name": "Grilled Chicken Sandwich",
    "quantity_sold": 45,
    "revenue": 584.55,
    "percentage_of_total": 15.2,
    "rank": 1
  }
]
```

### Staff Performance
**GET** `/api/v1/pos/analytics/staff`

Gets staff performance metrics.

**Response:** `200 OK`
```json
[
  {
    "staff_id": "uuid",
    "staff_name": "John Doe",
    "orders_processed": 25,
    "total_revenue": 750.00,
    "average_order_value": 30.00,
    "tips_earned": 120.00
  }
]
```

### Table Analytics
**GET** `/api/v1/pos/analytics/tables`

Gets table turnover analytics.

**Response:** `200 OK`
```json
[
  {
    "table_id": "uuid",
    "table_number": "T1",
    "total_orders": 12,
    "total_revenue": 450.00,
    "average_occupancy_time": 45.5,
    "turnover_rate": 1.5
  }
]
```

---

## Customers API

### Create Customer
**POST** `/api/v1/pos/customers/`

Creates customer profile.

**Request Body:**
```json
{
  "email": "customer@example.com",
  "phone": "+1234567890",
  "first_name": "Jane",
  "last_name": "Doe",
  "notes": "Prefers window seating"
}
```

### Get Customer
**GET** `/api/v1/pos/customers/{customer_id}`

Retrieves customer profile.

### List Customers
**GET** `/api/v1/pos/customers/`

Lists customers with search.

**Query Parameters:**
- `search`: Search by name, email, or phone
- `limit`: Results per page
- `offset`: Pagination offset

### Update Customer
**PUT** `/api/v1/pos/customers/{customer_id}`

Updates customer profile.

### Delete Customer
**DELETE** `/api/v1/pos/customers/{customer_id}`

Deletes customer (only if no orders).

### Get Customer Orders
**GET** `/api/v1/pos/customers/{customer_id}/orders`

Gets customer order history.

### Add Loyalty Points
**POST** `/api/v1/pos/customers/{customer_id}/loyalty/add-points?points=10`

Adds loyalty points to customer.

### Redeem Loyalty Points
**POST** `/api/v1/pos/customers/{customer_id}/loyalty/redeem-points?points=50`

Redeems loyalty points.

---

## Error Handling

### Error Response Format
```json
{
  "detail": "Error message describing what went wrong"
}
```

### HTTP Status Codes

- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `204 No Content`: Request successful, no content to return
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required or failed
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `409 Conflict`: Resource conflict (e.g., duplicate)
- `500 Internal Server Error`: Server error

### Common Errors

**Authentication Error:**
```json
{
  "detail": "Invalid authentication credentials"
}
```

**Validation Error:**
```json
{
  "detail": "Validation error: quantity must be greater than 0"
}
```

**Not Found:**
```json
{
  "detail": "Order not found"
}
```

---

## Rate Limiting

- **Default**: 100 requests per minute per user
- **WebSocket**: 1000 messages per minute per connection

Headers included in response:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1634567890
```

---

## Pagination

List endpoints support pagination:

**Request:**
```
GET /api/v1/pos/orders/?limit=20&offset=40
```

**Response Headers:**
```
X-Total-Count: 150
X-Page-Size: 20
X-Page-Number: 3
```

---

## Interactive Documentation

- **Swagger UI**: http://localhost:8070/docs
- **ReDoc**: http://localhost:8070/redoc
- **OpenAPI Schema**: http://localhost:8070/openapi.json

---

## Support

For API support, contact: support@x7ai.com
