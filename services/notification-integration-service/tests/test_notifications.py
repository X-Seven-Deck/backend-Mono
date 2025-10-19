"""
Unit tests for notification endpoints
"""

import pytest
from unittest.mock import patch, AsyncMock


class TestSMSNotifications:
    """Test SMS notification endpoints"""
    
    @patch('app.services.twilio_service.twilio_service.send_sms')
    async def test_send_sms_success(self, mock_send_sms, client, sample_sms_request):
        """Test successful SMS sending"""
        mock_send_sms.return_value = {
            "status": "success",
            "message_sid": "SM123456",
            "timestamp": "2025-01-01T00:00:00"
        }
        
        response = client.post("/api/v1/notifications/sms", json=sample_sms_request)
        
        assert response.status_code == 200
        assert response.json()["status"] == "success"
    
    def test_send_sms_invalid_phone(self, client):
        """Test SMS with invalid phone number"""
        response = client.post("/api/v1/notifications/sms", json={
            "to": "invalid",
            "message": "Test"
        })
        
        assert response.status_code == 422  # Validation error


class TestEmailNotifications:
    """Test email notification endpoints"""
    
    @patch('app.services.sendgrid_service.sendgrid_service.send_email')
    async def test_send_email_success(self, mock_send_email, client, sample_email_request):
        """Test successful email sending"""
        mock_send_email.return_value = {
            "status": "success",
            "message_id": "MSG123",
            "timestamp": "2025-01-01T00:00:00"
        }
        
        response = client.post("/api/v1/notifications/email", json=sample_email_request)
        
        assert response.status_code == 200
        assert response.json()["status"] == "success"


class TestPushNotifications:
    """Test push notification endpoints"""
    
    @patch('app.services.push_notification_service.push_notification_service.send_notification')
    async def test_send_push_success(self, mock_send_push, client, sample_push_request):
        """Test successful push notification"""
        mock_send_push.return_value = {
            "status": "success",
            "message_id": "PUSH123",
            "timestamp": "2025-01-01T00:00:00"
        }
        
        response = client.post("/api/v1/push/send", json=sample_push_request)
        
        assert response.status_code == 200
        assert response.json()["status"] == "success"


class TestHealthCheck:
    """Test health check endpoint"""
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
