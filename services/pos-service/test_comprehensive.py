"""
Comprehensive POS Service Test Suite
Tests all API endpoints with real data scenarios and enterprise-grade validation
"""

import os
import sys
import json
import pytest
import asyncio
from typing import Dict, List, Any
from decimal import Decimal
from datetime import datetime, timedelta
from uuid import uuid4, UUID
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from httpx import AsyncClient

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from main import app
from core.config import settings
from app.models import OrderStatus, PaymentMethod
from services.database import DatabaseService, get_database_service
from services.tax_engine import TaxEngine, get_tax_engine

# Test configuration
TEST_ENVIRONMENT = {
    "ENVIRONMENT": "testing",
    "SUPABASE_URL": "https://mock.supabase.co",
    "SUPABASE_KEY": "test_key",
    "SUPABASE_SERVICE_KEY": "test_service_key",
    "JWT_SECRET": "test_jwt_secret_key_for_testing_only_not_for_production_32_chars",
    "REDIS_HOST": "localhost",
    "POS_SERVICE_PORT": "8070"
}

# Mock data for testing
MOCK_BUSINESS = {
    "id": str(uuid4()),
    "name": "Test Restaurant",
    "type": "restaurant",
    "address": "123 Test St",
    "phone": "+1234567890"
}

MOCK_USER = {
    "user_id": str(uuid4()),
    "email": "test@example.com",
    "role": "staff",
    "business_id": MOCK_BUSINESS["id"]
}

MOCK_MENU_ITEMS = [
    {
        "id": str(uuid4()),
        "business_id": MOCK_BUSINESS["id"],
        "name": "Grilled Chicken Sandwich",
        "description": "Juicy grilled chicken with lettuce and tomato",
        "price": 12.99,
        "category": "mains",
        "is_available": True
    },
    {
        "id": str(uuid4()),
        "business_id": MOCK_BUSINESS["id"],
        "name": "Caesar Salad",
        "description": "Fresh romaine lettuce with Caesar dressing",
        "price": 8.99,
        "category": "salads",
        "is_available": True
    },
    {
        "id": str(uuid4()),
        "business_id": MOCK_BUSINESS["id"],
        "name": "Chocolate Cake",
        "description": "Rich chocolate cake with vanilla frosting",
        "price": 6.99,
        "category": "desserts",
        "is_available": True
    }
]

MOCK_TABLES = [
    {
        "id": str(uuid4()),
        "business_id": MOCK_BUSINESS["id"],
        "table_number": "T1",
        "capacity": 4,
        "status": "available"
    },
    {
        "id": str(uuid4()),
        "business_id": MOCK_BUSINESS["id"],
        "table_number": "T2",
        "capacity": 2,
        "status": "available"
    }
]

class MockDatabaseService(DatabaseService):
    """Mock database service for testing"""

    def __init__(self):
        self.orders = {}
        self.payments = {}
        self.receipts = {}
        self.tax_rules = {}
        self.menu_items = {item["id"]: item for item in MOCK_MENU_ITEMS}
        self.tables = {table["id"]: table for table in MOCK_TABLES}

    async def create_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock create order"""
        order_id = str(uuid4())
        order = {
            "id": order_id,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            **order_data
        }
        self.orders[order_id] = order
        return order

    async def get_order(self, order_id: UUID) -> Dict[str, Any]:
        """Mock get order"""
        return self.orders.get(str(order_id))

    async def get_order_with_items(self, order_id: UUID) -> Dict[str, Any]:
        """Mock get order with items"""
        order = self.orders.get(str(order_id))
        if not order:
            return None

        # Add mock order items
        order["items"] = [
            {
                "id": str(uuid4()),
                "order_id": str(order_id),
                "menu_item_id": MOCK_MENU_ITEMS[0]["id"],
                "name": MOCK_MENU_ITEMS[0]["name"],
                "quantity": 2,
                "unit_price": 12.99,
                "status": "pending"
            }
        ]
        return order

    async def get_orders(self, business_id: str, **kwargs) -> List[Dict[str, Any]]:
        """Mock get orders"""
        return [order for order in self.orders.values() if order.get("business_id") == business_id]

    async def get_active_orders(self, business_id: str) -> List[Dict[str, Any]]:
        """Mock get active orders"""
        return [order for order in self.orders.values()
                if order.get("business_id") == business_id and order.get("status") != "completed"]

    async def update_order(self, order_id: UUID, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Mock update order"""
        if str(order_id) not in self.orders:
            return None

        self.orders[str(order_id)].update({
            "updated_at": datetime.utcnow().isoformat(),
            **updates
        })
        return self.orders[str(order_id)]

    async def update_order_status(self, order_id: UUID, status: str) -> Dict[str, Any]:
        """Mock update order status"""
        if str(order_id) not in self.orders:
            return None

        self.orders[str(order_id)]["status"] = status
        self.orders[str(order_id)]["updated_at"] = datetime.utcnow().isoformat()
        return self.orders[str(order_id)]

    async def create_order_items(self, items: List[Dict[str, Any]]):
        """Mock create order items"""
        pass  # Items are handled in get_order_with_items

    async def update_table_status(self, table_id: UUID, status: str, order_id: UUID = None):
        """Mock update table status"""
        if str(table_id) in self.tables:
            self.tables[str(table_id)]["status"] = status
            if order_id:
                self.tables[str(table_id)]["order_id"] = str(order_id)

    async def get_menu_item(self, menu_item_id: UUID) -> Dict[str, Any]:
        """Mock get menu item"""
        return self.menu_items.get(str(menu_item_id))

    async def calculate_order_totals(self, order_id: UUID) -> Dict[str, Any]:
        """Mock calculate order totals"""
        return {"item_count": 1, "total_amount": 25.98}

    async def create_payment(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock create payment"""
        payment_id = str(uuid4())
        payment = {
            "id": payment_id,
            "created_at": datetime.utcnow().isoformat(),
            **payment_data
        }
        self.payments[payment_id] = payment
        return payment

    async def get_payment(self, payment_id: UUID) -> Dict[str, Any]:
        """Mock get payment"""
        return self.payments.get(str(payment_id))

    async def get_payment_by_order(self, order_id: UUID) -> Dict[str, Any]:
        """Mock get payment by order"""
        for payment in self.payments.values():
            if payment.get("order_id") == str(order_id):
                return payment
        return None

    async def create_tax_rule(self, rule_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock create tax rule"""
        rule_id = str(uuid4())
        rule = {
            "id": rule_id,
            "created_at": datetime.utcnow().isoformat(),
            **rule_data
        }
        self.tax_rules[rule_id] = rule
        return rule

    async def get_tax_rules(self, business_id: str, location_id: str = None, is_active: bool = True) -> List[Dict[str, Any]]:
        """Mock get tax rules"""
        return [rule for rule in self.tax_rules.values()
                if rule.get("business_id") == business_id and rule.get("is_active", True)]

    async def create_receipt(self, receipt_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock create receipt"""
        receipt_id = str(uuid4())
        receipt = {
            "id": receipt_id,
            "created_at": datetime.utcnow().isoformat(),
            **receipt_data
        }
        self.receipts[receipt_id] = receipt
        return receipt

    async def get_receipt(self, receipt_id: UUID) -> Dict[str, Any]:
        """Mock get receipt"""
        return self.receipts.get(str(receipt_id))

    async def get_receipt_by_order(self, order_id: UUID) -> Dict[str, Any]:
        """Mock get receipt by order"""
        for receipt in self.receipts.values():
            if receipt.get("order_id") == str(order_id):
                return receipt
        return None


class MockTaxEngine(TaxEngine):
    """Mock tax engine for testing"""

    async def calculate_tax(self, business_id: str, subtotal: Decimal, location_id: str = None) -> Dict[str, Any]:
        """Mock tax calculation"""
        tax_rate = Decimal("0.10")  # 10% tax
        tax_amount = subtotal * tax_rate
        total_with_tax = subtotal + tax_amount

        return {
            "tax_rate": float(tax_rate),
            "tax_amount": float(tax_amount),
            "total_with_tax": float(total_with_tax),
            "tax_breakdown": [
                {
                    "name": "Sales Tax",
                    "rate": 0.10,
                    "amount": float(tax_amount)
                }
            ]
        }


# Test fixtures
@pytest.fixture
def client():
    """Test client fixture"""
    return TestClient(app)


@pytest.fixture
def mock_db():
    """Mock database service fixture"""
    return MockDatabaseService()


@pytest.fixture
def mock_tax_engine():
    """Mock tax engine fixture"""
    return MockTaxEngine()


@pytest.fixture
def auth_headers():
    """Mock authentication headers"""
    return {"Authorization": f"Bearer mock_token_{MOCK_USER['user_id']}"}


# Helper functions for testing
def create_test_order_data():
    """Create test order data"""
    return {
        "business_id": MOCK_BUSINESS["id"],
        "table_id": MOCK_TABLES[0]["id"],
        "customer_count": 2,
        "notes": "Test order notes",
        "items": [
            {
                "menu_item_id": MOCK_MENU_ITEMS[0]["id"],
                "quantity": 2,
                "unit_price": 12.99,
                "special_instructions": "No onions"
            },
            {
                "menu_item_id": MOCK_MENU_ITEMS[1]["id"],
                "quantity": 1,
                "unit_price": 8.99,
                "special_instructions": "Extra dressing"
            }
        ]
    }


def create_test_payment_data(order_id: str):
    """Create test payment data"""
    return {
        "order_id": order_id,
        "payment_method": PaymentMethod.CREDIT_CARD.value,
        "amount": 35.97,
        "tip_amount": 5.00,
        "transaction_id": "txn_test_123",
        "notes": "Test payment"
    }


# Override dependencies for testing
app.dependency_overrides[get_database_service] = lambda: MockDatabaseService()
app.dependency_overrides[get_tax_engine] = lambda: MockTaxEngine()


class TestPOSService:
    """Main test class for POS service"""

    def setup_method(self):
        """Setup for each test"""
        # Set test environment variables
        for key, value in TEST_ENVIRONMENT.items():
            os.environ[key] = value
