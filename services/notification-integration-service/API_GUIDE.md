# API Usage Guide - Notification Integration Service

## 📘 Complete API Reference

### Authentication

All API requests should include the API key in the header:

```bash
X-API-Key: your_api_key_here
```

---

## 1. SMS Notifications

### Send Single SMS

```bash
curl -X POST http://localhost:8006/api/v1/notifications/sms \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key" \
  -d '{
    "to": "+1234567890",
    "message": "Your verification code is: 123456",
    "priority": "high"
  }'
```

**Response:**
```json
{
  "status": "success",
  "message_id": "SM1234567890abcdef",
  "timestamp": "2025-01-01T12:00:00Z",
  "details": {
    "to": "+1234567890",
    "status_code": "queued"
  }
}
```

### Send Bulk SMS

```bash
curl -X POST http://localhost:8006/api/v1/notifications/bulk/sms \
  -H "Content-Type: application/json" \
  -d '{
    "recipients": ["+1234567890", "+0987654321"],
    "message": "Bulk SMS message",
    "batch_size": 100
  }'
```

---

## 2. Email Notifications

### Send Standard Email

```bash
curl -X POST http://localhost:8006/api/v1/notifications/email \
  -H "Content-Type: application/json" \
  -d '{
    "to_email": "user@example.com",
    "subject": "Welcome to X7AI",
    "html_content": "<h1>Welcome!</h1><p>Thank you for joining.</p>",
    "plain_content": "Welcome! Thank you for joining."
  }'
```

### Send Template Email

```bash
curl -X POST http://localhost:8006/api/v1/notifications/email/template \
  -H "Content-Type: application/json" \
  -d '{
    "to_email": "user@example.com",
    "template_id": "welcome_email",
    "dynamic_data": {
      "user_name": "John Doe",
      "activation_link": "https://app.x7ai.com/activate/token123"
    }
  }'
```

---

## 3. WhatsApp Messages

### Send WhatsApp Text

```bash
curl -X POST http://localhost:8006/api/v1/notifications/whatsapp \
  -H "Content-Type: application/json" \
  -d '{
    "to": "+1234567890",
    "message": "Hello from X7AI!",
    "priority": "normal"
  }'
```

### Send WhatsApp with Media

```bash
curl -X POST http://localhost:8006/api/v1/notifications/whatsapp \
  -H "Content-Type: application/json" \
  -d '{
    "to": "+1234567890",
    "message": "Check out this image!",
    "media_url": "https://example.com/image.jpg"
  }'
```

---

## 4. Push Notifications

### Send to Single Device

```bash
curl -X POST http://localhost:8006/api/v1/push/send \
  -H "Content-Type: application/json" \
  -d '{
    "token": "device_fcm_token_here",
    "title": "New Message",
    "body": "You have a new message from John",
    "data": {
      "message_id": "msg123",
      "sender": "john"
    },
    "image_url": "https://example.com/notification.jpg"
  }'
```

### Send to Multiple Devices (Multicast)

```bash
curl -X POST http://localhost:8006/api/v1/push/multicast \
  -H "Content-Type: application/json" \
  -d '{
    "tokens": ["token1", "token2", "token3"],
    "title": "System Alert",
    "body": "Scheduled maintenance at 2 AM",
    "data": {
      "type": "maintenance",
      "scheduled_time": "2025-01-02T02:00:00Z"
    }
  }'
```

### Send to Topic

```bash
curl -X POST http://localhost:8006/api/v1/push/topic \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "news_updates",
    "title": "Breaking News",
    "body": "Important update for all subscribers",
    "data": {
      "article_id": "article123"
    }
  }'
```

### Subscribe to Topic

```bash
curl -X POST http://localhost:8006/api/v1/push/topic/subscribe \
  -H "Content-Type: application/json" \
  -d '{
    "tokens": ["device_token_1", "device_token_2"],
    "topic": "news_updates"
  }'
```

---

## 5. Scheduled Notifications

### Schedule SMS for Future

```bash
curl -X POST http://localhost:8006/api/v1/schedule/sms \
  -H "Content-Type: application/json" \
  -d '{
    "to": "+1234567890",
    "message": "Reminder: Your appointment is tomorrow",
    "schedule_time": "2025-01-02T09:00:00Z",
    "priority": 7
  }'
```

**Response:**
```json
{
  "status": "scheduled",
  "task_id": "celery-task-id-123",
  "scheduled_for": "2025-01-02T09:00:00Z"
}
```

### Schedule Email

```bash
curl -X POST http://localhost:8006/api/v1/schedule/email \
  -H "Content-Type: application/json" \
  -d '{
    "to_email": "user@example.com",
    "subject": "Scheduled Newsletter",
    "html_content": "<h1>Weekly Newsletter</h1>",
    "schedule_time": "2025-01-07T10:00:00Z",
    "priority": 5
  }'
```

### Create Recurring Notification

```bash
curl -X POST http://localhost:8006/api/v1/schedule/recurring \
  -H "Content-Type: application/json" \
  -d '{
    "notification_type": "email",
    "cron_schedule": "0 9 * * 1",
    "notification_data": {
      "to_email": "team@example.com",
      "subject": "Weekly Report",
      "html_content": "<h1>Weekly Report</h1>"
    }
  }'
```

**Cron Schedule Examples:**
- `0 9 * * *` - Every day at 9:00 AM
- `0 9 * * 1` - Every Monday at 9:00 AM
- `0 */6 * * *` - Every 6 hours
- `0 0 1 * *` - First day of every month at midnight

### Get Task Status

```bash
curl -X GET http://localhost:8006/api/v1/schedule/task-id-123/status
```

### Cancel Scheduled Task

```bash
curl -X DELETE http://localhost:8006/api/v1/schedule/task-id-123
```

---

## 6. Webhooks

### Trigger Custom Webhook

```bash
curl -X POST http://localhost:8006/api/v1/notifications/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "webhook_url": "https://your-webhook-endpoint.com/callback",
    "data": {
      "event": "order_created",
      "order_id": "order123",
      "customer": "john@example.com",
      "amount": 99.99
    },
    "retry_enabled": true
  }'
```

---

## 7. Monitoring & Health

### Health Check

```bash
curl http://localhost:8006/health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "notification-integration-service",
  "version": "1.0.0",
  "timestamp": "2025-01-01T12:00:00Z"
}
```

### Prometheus Metrics

```bash
curl http://localhost:8006/metrics
```

---

## 8. Error Handling

All endpoints return standard error responses:

### 400 - Bad Request

```json
{
  "error": "Invalid request parameters",
  "status_code": 400,
  "timestamp": "2025-01-01T12:00:00Z"
}
```

### 422 - Validation Error

```json
{
  "detail": [
    {
      "loc": ["body", "to"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### 500 - Internal Server Error

```json
{
  "error": "Internal server error",
  "message": "Error details here",
  "timestamp": "2025-01-01T12:00:00Z"
}
```

---

## 9. Python SDK Example

```python
import httpx
import asyncio
from datetime import datetime, timedelta

class NotificationClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key
        self.headers = {"X-API-Key": api_key}
    
    async def send_sms(self, to: str, message: str):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v1/notifications/sms",
                json={"to": to, "message": message},
                headers=self.headers
            )
            return response.json()
    
    async def send_email(self, to_email: str, subject: str, html_content: str):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v1/notifications/email",
                json={
                    "to_email": to_email,
                    "subject": subject,
                    "html_content": html_content
                },
                headers=self.headers
            )
            return response.json()
    
    async def schedule_notification(
        self,
        notification_type: str,
        schedule_time: datetime,
        **kwargs
    ):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v1/schedule/{notification_type}",
                json={
                    "schedule_time": schedule_time.isoformat(),
                    **kwargs
                },
                headers=self.headers
            )
            return response.json()

# Usage
async def main():
    client = NotificationClient(
        base_url="http://localhost:8006",
        api_key="your_api_key"
    )
    
    # Send SMS
    sms_result = await client.send_sms(
        to="+1234567890",
        message="Hello from Python SDK!"
    )
    print(f"SMS sent: {sms_result}")
    
    # Send Email
    email_result = await client.send_email(
        to_email="user@example.com",
        subject="Test Email",
        html_content="<h1>Hello!</h1>"
    )
    print(f"Email sent: {email_result}")
    
    # Schedule future SMS
    schedule_time = datetime.utcnow() + timedelta(hours=1)
    scheduled = await client.schedule_notification(
        notification_type="sms",
        schedule_time=schedule_time,
        to="+1234567890",
        message="Scheduled SMS"
    )
    print(f"Scheduled: {scheduled}")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 10. Rate Limits

| Channel | Rate Limit |
|---------|------------|
| SMS | 100/hour per business |
| Email | 1,000/hour per business |
| Push | 5,000/hour per business |
| WhatsApp | 100/hour per business |
| Webhook | 500/hour per business |

Rate limit headers in response:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1704110400
```

---

## Support

For issues or questions:
- Documentation: `/docs` endpoint
- Email: support@x7ai.com
- Status: https://status.x7ai.com
