# Enterprise Dashboard API Documentation

## Overview

The X-sevenAI Enterprise Dashboard provides Square-like functionality for food & hospitality businesses with comprehensive menu management, inventory tracking, operations management, and real-time analytics.

**Version:** 2.0.0  
**Base URL:** `http://analytics-dashboard-service:8060`  
**Authentication:** JWT Bearer Token

---

## Table of Contents

1. [Menu Management](#menu-management)
2. [Inventory Management](#inventory-management)
3. [Operations Management](#operations-management)
4. [Analytics & Reporting](#analytics--reporting)
5. [Real-time WebSocket](#real-time-websocket)
6. [Data Models](#data-models)

---

## Menu Management

### Categories

#### Create Menu Category
```http
POST /api/v1/menu/categories
Content-Type: application/json

{
  "business_id": "uuid",
  "name": "Appetizers",
  "description": "Starter dishes",
  "parent_id": null,
  "display_order": 1,
  "icon_url": "https://...",
  "is_active": true
}
```

#### List Menu Categories
```http
GET /api/v1/menu/categories?business_id={uuid}&is_active=true
```

#### Update Menu Category
```http
PUT /api/v1/menu/categories/{category_id}
Content-Type: application/json

{
  "name": "Updated Name",
  "display_order": 2
}
```

### Menu Items

#### Create Menu Item
```http
POST /api/v1/menu/items
Content-Type: application/json

{
  "business_id": "uuid",
  "category_id": "uuid",
  "name": "Margherita Pizza",
  "description": "Classic tomato and mozzarella",
  "price": 12.99,
  "cost": 4.50,
  "image_url": "https://...",
  "sku": "PIZZA-001",
  "is_available": true,
  "prep_time": 15,
  "calories": 800,
  "allergens": ["dairy", "gluten"],
  "tags": ["vegetarian", "popular"],
  "variants": [
    {
      "name": "Small",
      "price_adjustment": -2.00
    },
    {
      "name": "Large",
      "price_adjustment": 3.00
    }
  ],
  "modifiers": ["modifier-uuid-1", "modifier-uuid-2"]
}
```

#### List Menu Items
```http
GET /api/v1/menu/items?business_id={uuid}&category_id={uuid}&is_available=true&limit=50&offset=0
```

#### Get Menu Item with Details
```http
GET /api/v1/menu/items/{item_id}?include_modifiers=true
```

**Response:**
```json
{
  "id": "uuid",
  "business_id": "uuid",
  "name": "Margherita Pizza",
  "price": 12.99,
  "cost": 4.50,
  "profit_margin": 65.36,
  "category": {
    "id": "uuid",
    "name": "Pizzas"
  },
  "modifier_details": [
    {
      "id": "uuid",
      "name": "Extra Toppings",
      "type": "multiple",
      "options": [...]
    }
  ]
}
```

#### Bulk Update Menu Items
```http
POST /api/v1/menu/items/bulk-update
Content-Type: application/json

{
  "item_ids": ["uuid1", "uuid2", "uuid3"],
  "updates": {
    "is_available": false
  }
}
```

### Item Modifiers

#### Create Modifier
```http
POST /api/v1/menu/modifiers
Content-Type: application/json

{
  "business_id": "uuid",
  "name": "Extra Toppings",
  "type": "multiple",
  "required": false,
  "min_selections": 0,
  "max_selections": 5,
  "options": [
    {
      "name": "Extra Cheese",
      "price": 1.50,
      "is_default": false
    },
    {
      "name": "Mushrooms",
      "price": 1.00,
      "is_default": false
    }
  ]
}
```

---

## Inventory Management

### Inventory Items

#### Create Inventory Item
```http
POST /api/v1/inventory/items
Content-Type: application/json

{
  "business_id": "uuid",
  "name": "Mozzarella Cheese",
  "sku": "CHEESE-001",
  "unit": "kg",
  "current_stock": 50.0,
  "min_stock": 10.0,
  "max_stock": 100.0,
  "unit_cost": 8.50,
  "supplier_id": "uuid",
  "location_id": "uuid",
  "category": "Dairy",
  "is_tracked": true
}
```

#### List Inventory Items
```http
GET /api/v1/inventory/items?business_id={uuid}&low_stock_only=true
```

**Response includes metrics:**
```json
{
  "id": "uuid",
  "name": "Mozzarella Cheese",
  "current_stock": 8.0,
  "min_stock": 10.0,
  "stock_percentage": 8.0,
  "stock_value": 68.00,
  "needs_reorder": true,
  "days_of_stock": 2
}
```

### Stock Management

#### Adjust Stock
```http
POST /api/v1/inventory/adjustments
Content-Type: application/json

{
  "inventory_item_id": "uuid",
  "new_quantity": 45.0,
  "reason": "Physical count adjustment",
  "notes": "Found 5kg extra in storage"
}
```

#### Stock Count
```http
POST /api/v1/inventory/count
Content-Type: application/json

{
  "business_id": "uuid",
  "location_id": "uuid",
  "counts": [
    {
      "item_id": "uuid",
      "counted_quantity": 45.0
    }
  ]
}
```

### Stock Alerts

#### Create Alert
```http
POST /api/v1/inventory/alerts
Content-Type: application/json

{
  "business_id": "uuid",
  "inventory_item_id": "uuid",
  "alert_type": "low_stock",
  "threshold": 10.0,
  "is_active": true
}
```

#### Get Active Alerts
```http
GET /api/v1/inventory/alerts/active?business_id={uuid}
```

### Purchase Orders

#### Create Purchase Order
```http
POST /api/v1/inventory/purchase-orders
Content-Type: application/json

{
  "business_id": "uuid",
  "supplier_id": "uuid",
  "order_date": "2025-10-04T12:00:00Z",
  "expected_delivery_date": "2025-10-06T12:00:00Z",
  "items": [
    {
      "inventory_item_id": "uuid",
      "quantity": 50.0,
      "unit_cost": 8.50,
      "total": 425.00
    }
  ],
  "notes": "Urgent order"
}
```

#### Receive Purchase Order
```http
POST /api/v1/inventory/purchase-orders/{po_id}/receive
Content-Type: application/json

{
  "received_items": [
    {
      "item_id": "uuid",
      "quantity_received": 50.0
    }
  ]
}
```

---

## Operations Management

### Tables

#### Create Table
```http
POST /api/v1/operations/tables
Content-Type: application/json

{
  "business_id": "uuid",
  "table_number": "T-01",
  "capacity": 4,
  "location_id": "uuid",
  "floor_plan_id": "uuid",
  "position": {
    "x": 100.0,
    "y": 150.0,
    "rotation": 0
  },
  "shape": "circle",
  "status": "available"
}
```

#### List Tables
```http
GET /api/v1/operations/tables?business_id={uuid}&status=available
```

#### Assign Table
```http
POST /api/v1/operations/tables/assign
Content-Type: application/json

{
  "table_id": "uuid",
  "order_id": "uuid",
  "party_size": 4,
  "estimated_duration": 90
}
```

#### Release Table
```http
POST /api/v1/operations/tables/{table_id}/release
```

### Kitchen Display System (KDS)

#### Create KDS Order
```http
POST /api/v1/operations/kds/orders
Content-Type: application/json

{
  "business_id": "uuid",
  "order_id": "uuid",
  "station": "grill",
  "items": [
    {
      "menu_item_id": "uuid",
      "name": "Burger",
      "quantity": 2,
      "modifiers": ["No onions"],
      "special_instructions": "Well done"
    }
  ],
  "priority": 5,
  "target_time": "2025-10-04T13:30:00Z"
}
```

#### Update KDS Order Status
```http
PUT /api/v1/operations/kds/orders/{order_id}
Content-Type: application/json

{
  "status": "preparing",
  "prep_start_time": "2025-10-04T13:15:00Z"
}
```

#### Get Active KDS Orders
```http
GET /api/v1/operations/kds/orders?business_id={uuid}&station=grill&active_only=true
```

### Staff Management

#### Create Staff Member
```http
POST /api/v1/operations/staff
Content-Type: application/json

{
  "business_id": "uuid",
  "employee_id": "EMP-001",
  "first_name": "John",
  "last_name": "Doe",
  "email": "john@example.com",
  "phone": "+1234567890",
  "position": "Server",
  "department": "Front of House",
  "hourly_rate": 15.00,
  "hire_date": "2025-01-01",
  "status": "active"
}
```

#### Clock In
```http
POST /api/v1/operations/time-clock/clock-in
Content-Type: application/json

{
  "business_id": "uuid",
  "staff_id": "uuid",
  "clock_in": "2025-10-04T09:00:00Z",
  "location_id": "uuid"
}
```

#### Clock Out
```http
PUT /api/v1/operations/time-clock/{clock_id}/clock-out
Content-Type: application/json

{
  "clock_out_time": "2025-10-04T17:00:00Z"
}
```

#### Get Clocked-In Staff
```http
GET /api/v1/operations/time-clock/active?business_id={uuid}
```

### Operations Dashboard

#### Get Real-time Operations Dashboard
```http
GET /api/v1/operations/dashboard/{business_id}?location_id={uuid}
```

**Response:**
```json
{
  "business_id": "uuid",
  "timestamp": "2025-10-04T15:50:00Z",
  "tables": {
    "total": 20,
    "available": 8,
    "occupied": 10,
    "reserved": 2
  },
  "kitchen": {
    "pending": 5,
    "preparing": 8,
    "ready": 2
  },
  "staff": {
    "clocked_in": 12,
    "on_break": 2
  },
  "orders": {
    "active": 15,
    "completed_today": 87
  },
  "revenue_today": 3450.50,
  "avg_table_turnover": 65,
  "avg_prep_time": 12
}
```

---

## Analytics & Reporting

### Real-time Analytics

#### Get Real-time Dashboard
```http
GET /api/v1/analytics/realtime/{business_id}?location_id={uuid}
```

#### Get Comprehensive Dashboard
```http
GET /api/v1/analytics/dashboard/{business_id}?period=7d
```

### Sales Analytics

#### Sales Summary
```http
GET /api/v1/analytics/sales/summary?business_id={uuid}&start_date=2025-10-01&end_date=2025-10-04&group_by=day
```

#### Sales by Category
```http
GET /api/v1/analytics/sales/by-category?business_id={uuid}&start_date=2025-10-01&end_date=2025-10-04
```

### Menu Analytics

#### Top Menu Items
```http
GET /api/v1/analytics/menu/top-items?business_id={uuid}&start_date=2025-10-01&end_date=2025-10-04&metric=revenue&limit=10
```

#### Profit Analysis
```http
GET /api/v1/analytics/menu/profit-analysis?business_id={uuid}&start_date=2025-10-01&end_date=2025-10-04
```

### Customer Analytics

#### Customer Insights
```http
GET /api/v1/analytics/customers/insights?business_id={uuid}&start_date=2025-10-01&end_date=2025-10-04
```

### Operational Analytics

#### Table Turnover Analysis
```http
GET /api/v1/analytics/operations/table-turnover?business_id={uuid}&start_date=2025-10-01&end_date=2025-10-04
```

#### Kitchen Performance
```http
GET /api/v1/analytics/operations/kitchen-performance?business_id={uuid}&start_date=2025-10-01&end_date=2025-10-04
```

### Financial Analytics

#### Financial Summary
```http
GET /api/v1/analytics/financial/summary?business_id={uuid}&start_date=2025-10-01&end_date=2025-10-04
```

#### Labor Costs
```http
GET /api/v1/analytics/financial/labor-costs?business_id={uuid}&start_date=2025-10-01&end_date=2025-10-04
```

### Reports

#### Generate Report
```http
POST /api/v1/analytics/reports/generate?business_id={uuid}&report_type=weekly&format=pdf
```

---

## Real-time WebSocket

### Dashboard WebSocket

Connect to real-time dashboard updates:

```javascript
const ws = new WebSocket('ws://localhost:8060/api/v1/ws/dashboard/{business_id}');

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  
  switch(message.event) {
    case 'order_update':
      // Handle order update
      break;
    case 'table_update':
      // Handle table status change
      break;
    case 'revenue_update':
      // Handle revenue update
      break;
  }
};

// Send ping to keep connection alive
setInterval(() => {
  ws.send(JSON.stringify({ type: 'ping' }));
}, 30000);
```

### KDS WebSocket

Connect to Kitchen Display System:

```javascript
const ws = new WebSocket('ws://localhost:8060/api/v1/ws/kds/{business_id}?station=grill');

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  
  if (message.event === 'kds_update') {
    // Update kitchen display
  }
};
```

---

## Data Models

### Menu Item
```typescript
interface MenuItem {
  id: string;
  business_id: string;
  category_id?: string;
  name: string;
  description?: string;
  price: number;
  cost?: number;
  image_url?: string;
  sku?: string;
  is_available: boolean;
  prep_time?: number;
  calories?: number;
  allergens: string[];
  tags: string[];
  variants: Variant[];
  modifiers: string[];
  created_at: string;
  updated_at: string;
}
```

### Inventory Item
```typescript
interface InventoryItem {
  id: string;
  business_id: string;
  name: string;
  sku?: string;
  unit: string;
  current_stock: number;
  min_stock: number;
  max_stock?: number;
  unit_cost?: number;
  supplier_id?: string;
  location_id?: string;
  category?: string;
  is_tracked: boolean;
  created_at: string;
  updated_at: string;
}
```

### Table
```typescript
interface Table {
  id: string;
  business_id: string;
  table_number: string;
  capacity: number;
  location_id?: string;
  floor_plan_id?: string;
  position?: {
    x: number;
    y: number;
    rotation: number;
  };
  shape?: 'circle' | 'square' | 'rectangle' | 'oval';
  status: 'available' | 'occupied' | 'reserved' | 'cleaning';
  current_order_id?: string;
  created_at: string;
  updated_at: string;
}
```

---

## Error Responses

All endpoints return standard error responses:

```json
{
  "detail": "Error message",
  "status_code": 400
}
```

**Common Status Codes:**
- `200` - Success
- `201` - Created
- `204` - No Content
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `422` - Validation Error
- `500` - Internal Server Error
- `501` - Not Implemented

---

## Rate Limiting

- **Default**: 100 requests per minute per API key
- **Burst**: 200 requests per minute
- **WebSocket**: 1 connection per business per client

---

## Authentication

All API requests require JWT authentication:

```http
Authorization: Bearer <jwt_token>
```

Obtain tokens from the auth service:
```http
POST /api/v1/auth/login
```

---

## Pagination

List endpoints support pagination:

```http
GET /api/v1/menu/items?limit=50&offset=0
```

**Parameters:**
- `limit`: Items per page (default: 50, max: 100)
- `offset`: Number of items to skip (default: 0)

---

## Filtering

Most list endpoints support filtering:

```http
GET /api/v1/menu/items?category_id={uuid}&is_available=true&search=pizza
```

---

## Sorting

Use `order_by` parameter for sorting:

```http
GET /api/v1/menu/items?order_by=price&order=desc
```

---

## Best Practices

1. **Use WebSockets** for real-time updates instead of polling
2. **Implement caching** for frequently accessed data
3. **Batch operations** using bulk endpoints
4. **Handle errors** gracefully with retry logic
5. **Monitor rate limits** and implement backoff
6. **Use pagination** for large datasets
7. **Validate data** on client side before sending
8. **Keep connections alive** with periodic pings

---

## Support

For API support and questions:
- **Documentation**: `/docs` (Swagger UI)
- **OpenAPI Spec**: `/openapi.json`
- **Health Check**: `/health`

---

**Last Updated:** October 4, 2025  
**API Version:** 2.0.0
