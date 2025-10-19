"""
Pytest configuration and fixtures for notification service tests
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.models.database import Base
from app.config import settings


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def client():
    """Test client fixture"""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="session")
def test_db():
    """Test database fixture"""
    # Use in-memory SQLite for tests
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    yield TestingSessionLocal
    
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_sms_request():
    """Sample SMS request data"""
    return {
        "to": "+1234567890",
        "message": "Test SMS message",
        "priority": "high"
    }


@pytest.fixture
def sample_email_request():
    """Sample email request data"""
    return {
        "to_email": "test@example.com",
        "subject": "Test Email",
        "html_content": "<h1>Test</h1>",
        "priority": "normal"
    }


@pytest.fixture
def sample_push_request():
    """Sample push notification request"""
    return {
        "token": "test_fcm_token",
        "title": "Test Notification",
        "body": "Test message",
        "data": {"key": "value"}
    }
