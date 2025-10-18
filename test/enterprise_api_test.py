#!/usr/bin/env python3
"""
Enterprise-Grade API Testing Suite for X-sevenAI Platform
Tests all endpoints across auth-service and analytics-dashboard-service with real data.

This script performs comprehensive testing including:
- User registration and authentication
- Business creation and management
- Analytics dashboard endpoints (retail, service-based, professional)
- Menu, inventory, operations management
- Real-time analytics and reporting

Author: X-sevenAI Testing Team
Date: 2025-10-08
"""

import asyncio
import json
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from uuid import UUID, uuid4
import requests
from colorama import init, Fore, Style
import time

# Initialize colorama for colored output
init(autoreset=True)

# Configuration
AUTH_SERVICE_URL = "http://localhost:8010"
ANALYTICS_SERVICE_URL = "http://localhost:8060"

# Test Data Storage
test_data = {
    "user": {},
    "business": {},
    "tokens": {},
    "products": [],
    "services": [],
    "menu_items": [],
    "customers": [],
    "staff": [],
    "orders": []
}

# Test Results
test_results = {
    "total": 0,
    "passed": 0,
    "failed": 0,
    "errors": []
}


class TestLogger:
    """Enhanced logger for test output"""
    
    @staticmethod
    def header(message: str):
        print(f"\n{Fore.CYAN}{'='*80}")
        print(f"{Fore.CYAN}{message.center(80)}")
        print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")
    
    @staticmethod
    def section(message: str):
        print(f"\n{Fore.YELLOW}{'─'*80}")
        print(f"{Fore.YELLOW}► {message}")
        print(f"{Fore.YELLOW}{'─'*80}{Style.RESET_ALL}")
    
    @staticmethod
    def success(message: str):
        print(f"{Fore.GREEN}✓ {message}{Style.RESET_ALL}")
    
    @staticmethod
    def error(message: str):
        print(f"{Fore.RED}✗ {message}{Style.RESET_ALL}")
    
    @staticmethod
    def info(message: str):
        print(f"{Fore.BLUE}ℹ {message}{Style.RESET_ALL}")
    
    @staticmethod
    def warning(message: str):
        print(f"{Fore.YELLOW}⚠ {message}{Style.RESET_ALL}")
    
    @staticmethod
    def data(label: str, value: Any):
        print(f"{Fore.MAGENTA}  {label}: {Fore.WHITE}{value}{Style.RESET_ALL}")


def test_endpoint(name: str, method: str, url: str, **kwargs) -> Optional[Dict]:
    """
    Test an API endpoint and track results
    
    Args:
        name: Test name
        method: HTTP method (GET, POST, PUT, DELETE)
        url: Full URL to test
        **kwargs: Additional arguments for requests
    
    Returns:
        Response JSON or None if failed
    """
    test_results["total"] += 1
    
    try:
        TestLogger.info(f"Testing: {name}")
        TestLogger.data("Method", method)
        TestLogger.data("URL", url)
        
        if "json" in kwargs:
            TestLogger.data("Payload", json.dumps(kwargs["json"], indent=2)[:200] + "...")
        
        start_time = time.time()
        response = requests.request(method, url, timeout=30, **kwargs)
        elapsed_time = time.time() - start_time
        
        TestLogger.data("Status Code", response.status_code)
        TestLogger.data("Response Time", f"{elapsed_time:.2f}s")
        
        if response.status_code in [200, 201, 204]:
            test_results["passed"] += 1
            TestLogger.success(f"PASSED: {name}")
            
            if response.status_code != 204:
                try:
                    return response.json()
                except:
                    return {"status": "success"}
            return {"status": "success"}
        else:
            test_results["failed"] += 1
            error_msg = f"FAILED: {name} - Status {response.status_code}"
            try:
                error_detail = response.json()
                error_msg += f" - {error_detail}"
            except:
                error_msg += f" - {response.text[:200]}"
            
            TestLogger.error(error_msg)
            test_results["errors"].append(error_msg)
            return None
            
    except Exception as e:
        test_results["failed"] += 1
        error_msg = f"EXCEPTION: {name} - {str(e)}"
        TestLogger.error(error_msg)
        test_results["errors"].append(error_msg)
        return None


def generate_test_user_data() -> Dict:
    """Generate realistic test user data"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return {
        "email": f"test.user.{timestamp}@x7ai.com",
        "password": "SecureP@ssw0rd123!",
        "confirm_password": "SecureP@ssw0rd123!",
        "full_name": "John Enterprise Tester",
        "phone_number": "+15550100"
    }


def test_auth_service():
    """Test all auth service endpoints"""
    TestLogger.header("AUTHENTICATION SERVICE TESTS")
    
    # Generate test user
    user_data = generate_test_user_data()
    test_data["user"] = user_data
    
    # Test 1: Register new user
    TestLogger.section("1. User Registration")
    response = test_endpoint(
        "Register New User",
        "POST",
        f"{AUTH_SERVICE_URL}/api/v1/auth/register",
        json={
            "email": user_data["email"],
            "password": user_data["password"],
            "confirm_password": user_data["confirm_password"],
            "full_name": user_data["full_name"],
            "phone_number": user_data["phone_number"]
        }
    )
    
    if response:
        test_data["user"]["id"] = response.get("user", {}).get("id")
        test_data["tokens"]["access_token"] = response.get("session", {}).get("access_token")
        test_data["tokens"]["refresh_token"] = response.get("session", {}).get("refresh_token")
        TestLogger.data("User ID", test_data["user"]["id"])
        TestLogger.data("Access Token", test_data["tokens"]["access_token"][:50] + "...")
    
    # Test 2: Login
    TestLogger.section("2. User Login")
    response = test_endpoint(
        "User Login",
        "POST",
        f"{AUTH_SERVICE_URL}/api/v1/auth/login",
        json={
            "email": user_data["email"],
            "password": user_data["password"]
        }
    )
    
    if response:
        test_data["tokens"]["access_token"] = response.get("session", {}).get("access_token")
        test_data["tokens"]["refresh_token"] = response.get("session", {}).get("refresh_token")
    
    # Test 3: Get Current User
    TestLogger.section("3. Get Current User Profile")
    headers = {"Authorization": f"Bearer {test_data['tokens']['access_token']}"}
    response = test_endpoint(
        "Get Current User",
        "GET",
        f"{AUTH_SERVICE_URL}/api/v1/auth/me",
        headers=headers
    )
    
    # Test 4: Refresh Token
    TestLogger.section("4. Refresh Access Token")
    response = test_endpoint(
        "Refresh Token",
        "POST",
        f"{AUTH_SERVICE_URL}/api/v1/auth/refresh",
        json={"refresh_token": test_data["tokens"]["refresh_token"]}
    )
    
    if response:
        test_data["tokens"]["access_token"] = response.get("access_token", test_data["tokens"]["access_token"])


def test_business_service():
    """Test business management endpoints"""
    TestLogger.header("BUSINESS MANAGEMENT TESTS")
    
    headers = {"Authorization": f"Bearer {test_data['tokens']['access_token']}"}
    
    # Test 1: Create Business
    TestLogger.section("1. Create New Business")
    business_data = {
        "name": "Enterprise Test Retail Store",
        "business_type": "retail",
        "email": "business@x7ai.com",
        "phone": "+1-555-0200",
        "address": "123 Enterprise Ave, Tech City, TC 12345",
        "description": "A comprehensive retail store for enterprise testing",
        "settings": {
            "currency": "USD",
            "timezone": "America/New_York",
            "tax_rate": 0.08
        }
    }
    
    response = test_endpoint(
        "Create Business",
        "POST",
        f"{AUTH_SERVICE_URL}/api/v1/business",
        headers=headers,
        json=business_data
    )
    
    if response:
        test_data["business"]["id"] = response.get("id")
        test_data["business"]["name"] = response.get("name")
        TestLogger.data("Business ID", test_data["business"]["id"])
        TestLogger.data("Business Name", test_data["business"]["name"])
    
    # Test 2: List Businesses
    TestLogger.section("2. List User Businesses")
    response = test_endpoint(
        "List Businesses",
        "GET",
        f"{AUTH_SERVICE_URL}/api/v1/business",
        headers=headers
    )
    
    # Test 3: Get Business Details
    if test_data["business"].get("id"):
        TestLogger.section("3. Get Business Details")
        response = test_endpoint(
            "Get Business",
            "GET",
            f"{AUTH_SERVICE_URL}/api/v1/business/{test_data['business']['id']}",
            headers=headers
        )
    
    # Test 4: Update Business
    if test_data["business"].get("id"):
        TestLogger.section("4. Update Business")
        response = test_endpoint(
            "Update Business",
            "PUT",
            f"{AUTH_SERVICE_URL}/api/v1/business/{test_data['business']['id']}",
            headers=headers,
            json={
                "description": "Updated: Enterprise-grade retail testing facility",
                "settings": {
                    "currency": "USD",
                    "timezone": "America/New_York",
                    "tax_rate": 0.085
                }
            }
        )


def test_retail_endpoints():
    """Test retail-specific endpoints"""
    TestLogger.header("RETAIL TEMPLATE TESTS")
    
    headers = {"Authorization": f"Bearer {test_data['tokens']['access_token']}"}
    business_id = test_data["business"].get("id")
    
    if not business_id:
        TestLogger.error("No business ID available, skipping retail tests")
        return
    
    # Test 1: Create Products
    TestLogger.section("1. Create Retail Products")
    products = [
        {
            "business_id": business_id,
            "name": "Premium Wireless Headphones",
            "description": "High-quality noise-canceling headphones",
            "sku": "WH-001",
            "barcode": "1234567890123",
            "category": "Electronics",
            "brand": "TechPro",
            "price": 299.99,
            "cost": 150.00,
            "compare_at_price": 349.99,
            "tax_rate": 0.08,
            "weight": 0.5,
            "weight_unit": "kg",
            "is_available": True,
            "track_inventory": True,
            "inventory_quantity": 50,
            "low_stock_threshold": 10,
            "tags": ["electronics", "audio", "premium"]
        },
        {
            "business_id": business_id,
            "name": "Organic Coffee Beans",
            "description": "Premium organic coffee from Colombia",
            "sku": "CF-001",
            "barcode": "1234567890124",
            "category": "Food & Beverage",
            "brand": "CoffeePro",
            "price": 24.99,
            "cost": 12.00,
            "weight": 1.0,
            "weight_unit": "kg",
            "is_available": True,
            "track_inventory": True,
            "inventory_quantity": 100,
            "low_stock_threshold": 20,
            "tags": ["organic", "coffee", "beverage"]
        }
    ]
    
    for product in products:
        response = test_endpoint(
            f"Create Product: {product['name']}",
            "POST",
            f"{ANALYTICS_SERVICE_URL}/api/v1/retail/products",
            headers=headers,
            json=product
        )
        if response:
            test_data["products"].append(response)
    
    # Test 2: List Products
    TestLogger.section("2. List All Products")
    response = test_endpoint(
        "List Products",
        "GET",
        f"{ANALYTICS_SERVICE_URL}/api/v1/retail/products?business_id={business_id}",
        headers=headers
    )
    
    # Test 3: Get Product Details
    if test_data["products"]:
        TestLogger.section("3. Get Product Details")
        product_id = test_data["products"][0]["id"]
        response = test_endpoint(
            "Get Product",
            "GET",
            f"{ANALYTICS_SERVICE_URL}/api/v1/retail/products/{product_id}",
            headers=headers
        )
    
    # Test 4: Update Product
    if test_data["products"]:
        TestLogger.section("4. Update Product")
        product_id = test_data["products"][0]["id"]
        response = test_endpoint(
            "Update Product",
            "PUT",
            f"{ANALYTICS_SERVICE_URL}/api/v1/retail/products/{product_id}",
            headers=headers,
            json={
                "price": 279.99,
                "inventory_quantity": 45
            }
        )
    
    # Test 5: Adjust Inventory
    if test_data["products"]:
        TestLogger.section("5. Adjust Product Inventory")
        product_id = test_data["products"][0]["id"]
        response = test_endpoint(
            "Adjust Inventory",
            "POST",
            f"{ANALYTICS_SERVICE_URL}/api/v1/retail/products/{product_id}/adjust-inventory?adjustment=-5",
            headers=headers
        )
    
    # Test 6: Create Product Categories
    TestLogger.section("6. Create Product Categories")
    categories = [
        {
            "business_id": business_id,
            "name": "Electronics",
            "description": "Electronic devices and accessories",
            "display_order": 1,
            "is_active": True
        },
        {
            "business_id": business_id,
            "name": "Food & Beverage",
            "description": "Food and beverage products",
            "display_order": 2,
            "is_active": True
        }
    ]
    
    for category in categories:
        response = test_endpoint(
            f"Create Category: {category['name']}",
            "POST",
            f"{ANALYTICS_SERVICE_URL}/api/v1/retail/categories",
            headers=headers,
            json=category
        )
    
    # Test 7: List Categories
    TestLogger.section("7. List Product Categories")
    response = test_endpoint(
        "List Categories",
        "GET",
        f"{ANALYTICS_SERVICE_URL}/api/v1/retail/categories?business_id={business_id}",
        headers=headers
    )
    
    # Test 8: Create Supplier
    TestLogger.section("8. Create Supplier")
    supplier_data = {
        "business_id": business_id,
        "name": "TechSupply Co.",
        "contact_name": "Jane Smith",
        "email": "jane@techsupply.com",
        "phone": "+1-555-0300",
        "address": "456 Supplier St, Supply City, SC 54321",
        "payment_terms": "Net 30",
        "is_active": True
    }
    
    response = test_endpoint(
        "Create Supplier",
        "POST",
        f"{ANALYTICS_SERVICE_URL}/api/v1/retail/suppliers",
        headers=headers,
        json=supplier_data
    )
    
    supplier_id = None
    if response:
        supplier_id = response.get("id")
    
    # Test 9: List Suppliers
    TestLogger.section("9. List Suppliers")
    response = test_endpoint(
        "List Suppliers",
        "GET",
        f"{ANALYTICS_SERVICE_URL}/api/v1/retail/suppliers?business_id={business_id}",
        headers=headers
    )
    
    # Test 10: Create Purchase Order
    if supplier_id and test_data["products"]:
        TestLogger.section("10. Create Purchase Order")
        po_data = {
            "business_id": business_id,
            "supplier_id": supplier_id,
            "order_date": datetime.now().isoformat(),
            "expected_delivery": (datetime.now() + timedelta(days=7)).isoformat(),
            "status": "pending",
            "items": [
                {
                    "product_id": test_data["products"][0]["id"],
                    "quantity": 20,
                    "unit_price": 150.00
                }
            ],
            "total_amount": 3000.00
        }
        
        response = test_endpoint(
            "Create Purchase Order",
            "POST",
            f"{ANALYTICS_SERVICE_URL}/api/v1/retail/purchase-orders",
            headers=headers,
            json=po_data
        )
    
    # Test 11: List Purchase Orders
    TestLogger.section("11. List Purchase Orders")
    response = test_endpoint(
        "List Purchase Orders",
        "GET",
        f"{ANALYTICS_SERVICE_URL}/api/v1/retail/purchase-orders?business_id={business_id}",
        headers=headers
    )
    
    # Test 12: Create Stock Alert
    if test_data["products"]:
        TestLogger.section("12. Create Stock Alert")
        alert_data = {
            "business_id": business_id,
            "product_id": test_data["products"][0]["id"],
            "alert_type": "low_stock",
            "threshold": 10,
            "is_active": True
        }
        
        response = test_endpoint(
            "Create Stock Alert",
            "POST",
            f"{ANALYTICS_SERVICE_URL}/api/v1/retail/stock-alerts",
            headers=headers,
            json=alert_data
        )
    
    # Test 13: List Stock Alerts
    TestLogger.section("13. List Stock Alerts")
    response = test_endpoint(
        "List Stock Alerts",
        "GET",
        f"{ANALYTICS_SERVICE_URL}/api/v1/retail/stock-alerts?business_id={business_id}",
        headers=headers
    )
    
    # Test 14: Get Active Stock Alerts
    TestLogger.section("14. Get Active Stock Alerts")
    response = test_endpoint(
        "Get Active Alerts",
        "GET",
        f"{ANALYTICS_SERVICE_URL}/api/v1/retail/stock-alerts/active?business_id={business_id}",
        headers=headers
    )
    
    # Test 15: Create Promotion
    TestLogger.section("15. Create Promotion")
    promotion_data = {
        "business_id": business_id,
        "name": "Black Friday Sale",
        "description": "20% off all electronics",
        "promotion_type": "percentage",
        "discount_type": "percentage",
        "discount_value": 20,
        "start_date": datetime.now().isoformat(),
        "end_date": (datetime.now() + timedelta(days=7)).isoformat(),
        "applicable_categories": ["Electronics"],
        "is_active": True
    }
    
    response = test_endpoint(
        "Create Promotion",
        "POST",
        f"{ANALYTICS_SERVICE_URL}/api/v1/retail/promotions",
        headers=headers,
        json=promotion_data
    )
    
    # Test 16: List Promotions
    TestLogger.section("16. List Promotions")
    response = test_endpoint(
        "List Promotions",
        "GET",
        f"{ANALYTICS_SERVICE_URL}/api/v1/retail/promotions?business_id={business_id}",
        headers=headers
    )


def test_service_based_endpoints():
    """Test service-based business endpoints"""
    TestLogger.header("SERVICE-BASED TEMPLATE TESTS")
    
    headers = {"Authorization": f"Bearer {test_data['tokens']['access_token']}"}
    business_id = test_data["business"].get("id")
    
    if not business_id:
        TestLogger.error("No business ID available, skipping service-based tests")
        return
    
    # Test 1: Create Services
    TestLogger.section("1. Create Services")
    services = [
        {
            "business_id": business_id,
            "name": "Premium Haircut",
            "description": "Professional haircut with styling",
            "category": "Hair Services",
            "price": 45.00,
            "duration": 45,
            "is_available": True,
            "requires_booking": True,
            "staff_required": 1
        },
        {
            "business_id": business_id,
            "name": "Deep Tissue Massage",
            "description": "60-minute therapeutic massage",
            "category": "Spa Services",
            "price": 120.00,
            "duration": 60,
            "is_available": True,
            "requires_booking": True,
            "staff_required": 1
        }
    ]
    
    for service in services:
        response = test_endpoint(
            f"Create Service: {service['name']}",
            "POST",
            f"{ANALYTICS_SERVICE_URL}/api/v1/service-based/services",
            headers=headers,
            json=service
        )
        if response:
            test_data["services"].append(response)
    
    # Test 2: List Services
    TestLogger.section("2. List All Services")
    response = test_endpoint(
        "List Services",
        "GET",
        f"{ANALYTICS_SERVICE_URL}/api/v1/service-based/services?business_id={business_id}",
        headers=headers
    )
    
    # Test 3: Create Service Categories
    TestLogger.section("3. Create Service Categories")
    categories = [
        {
            "business_id": business_id,
            "name": "Hair Services",
            "description": "All hair-related services",
            "display_order": 1
        },
        {
            "business_id": business_id,
            "name": "Spa Services",
            "description": "Relaxation and wellness services",
            "display_order": 2
        }
    ]
    
    for category in categories:
        response = test_endpoint(
            f"Create Service Category: {category['name']}",
            "POST",
            f"{ANALYTICS_SERVICE_URL}/api/v1/service-based/service-categories",
            headers=headers,
            json=category
        )
    
    # Test 4: Create Appointment
    if test_data["services"]:
        TestLogger.section("4. Create Appointment")
        appointment_data = {
            "business_id": business_id,
            "service_id": test_data["services"][0]["id"],
            "customer_name": "Alice Johnson",
            "customer_email": "alice@example.com",
            "customer_phone": "+1-555-0400",
            "appointment_date": (datetime.now() + timedelta(days=2)).isoformat(),
            "start_time": "14:00:00",
            "end_time": "14:45:00",
            "status": "confirmed",
            "notes": "First-time customer"
        }
        
        response = test_endpoint(
            "Create Appointment",
            "POST",
            f"{ANALYTICS_SERVICE_URL}/api/v1/service-based/appointments",
            headers=headers,
            json=appointment_data
        )
    
    # Test 5: List Appointments
    TestLogger.section("5. List Appointments")
    response = test_endpoint(
        "List Appointments",
        "GET",
        f"{ANALYTICS_SERVICE_URL}/api/v1/service-based/appointments?business_id={business_id}",
        headers=headers
    )


def test_menu_endpoints():
    """Test menu management endpoints (food & hospitality)"""
    TestLogger.header("MENU MANAGEMENT TESTS")
    
    headers = {"Authorization": f"Bearer {test_data['tokens']['access_token']}"}
    business_id = test_data["business"].get("id")
    
    if not business_id:
        TestLogger.error("No business ID available, skipping menu tests")
        return
    
    # Test 1: Create Menu Categories
    TestLogger.section("1. Create Menu Categories")
    categories = [
        {
            "business_id": business_id,
            "name": "Appetizers",
            "description": "Start your meal right",
            "display_order": 1,
            "is_active": True
        },
        {
            "business_id": business_id,
            "name": "Main Courses",
            "description": "Hearty main dishes",
            "display_order": 2,
            "is_active": True
        }
    ]
    
    category_ids = []
    for category in categories:
        response = test_endpoint(
            f"Create Menu Category: {category['name']}",
            "POST",
            f"{ANALYTICS_SERVICE_URL}/api/v1/menu/categories",
            headers=headers,
            json=category
        )
        if response:
            category_ids.append(response.get("id"))
    
    # Test 2: Create Menu Items
    if category_ids:
        TestLogger.section("2. Create Menu Items")
        items = [
            {
                "business_id": business_id,
                "category_id": category_ids[0],
                "name": "Caesar Salad",
                "description": "Fresh romaine with parmesan and croutons",
                "price": 12.99,
                "cost": 4.50,
                "is_available": True,
                "prep_time": 10,
                "calories": 350
            },
            {
                "business_id": business_id,
                "category_id": category_ids[1],
                "name": "Grilled Salmon",
                "description": "Atlantic salmon with seasonal vegetables",
                "price": 28.99,
                "cost": 12.00,
                "is_available": True,
                "prep_time": 25,
                "calories": 520
            }
        ]
        
        for item in items:
            response = test_endpoint(
                f"Create Menu Item: {item['name']}",
                "POST",
                f"{ANALYTICS_SERVICE_URL}/api/v1/menu/items",
                headers=headers,
                json=item
            )
            if response:
                test_data["menu_items"].append(response)
    
    # Test 3: List Menu Items
    TestLogger.section("3. List Menu Items")
    response = test_endpoint(
        "List Menu Items",
        "GET",
        f"{ANALYTICS_SERVICE_URL}/api/v1/menu/items?business_id={business_id}",
        headers=headers
    )


def test_analytics_endpoints():
    """Test analytics and reporting endpoints"""
    TestLogger.header("ANALYTICS & REPORTING TESTS")
    
    headers = {"Authorization": f"Bearer {test_data['tokens']['access_token']}"}
    business_id = test_data["business"].get("id")
    
    if not business_id:
        TestLogger.error("No business ID available, skipping analytics tests")
        return
    
    # Test 1: Dashboard Analytics
    TestLogger.section("1. Get Dashboard Analytics")
    response = test_endpoint(
        "Dashboard Analytics",
        "GET",
        f"{ANALYTICS_SERVICE_URL}/api/v1/analytics/dashboard/{business_id}?period=7d",
        headers=headers
    )
    
    # Test 2: Top Categories
    TestLogger.section("2. Get Top Categories")
    response = test_endpoint(
        "Top Categories",
        "GET",
        f"{ANALYTICS_SERVICE_URL}/api/v1/analytics/top-categories/{business_id}?limit=5",
        headers=headers
    )
    
    # Test 3: Customer Insights
    TestLogger.section("3. Get Customer Insights")
    response = test_endpoint(
        "Customer Insights",
        "GET",
        f"{ANALYTICS_SERVICE_URL}/api/v1/analytics/customer-insights/{business_id}",
        headers=headers
    )
    
    # Test 4: Real-time Metrics
    TestLogger.section("4. Get Real-time Metrics")
    response = test_endpoint(
        "Real-time Metrics",
        "GET",
        f"{ANALYTICS_SERVICE_URL}/api/v1/analytics/real-time/{business_id}",
        headers=headers
    )
    
    # Test 5: Retail Product Performance
    TestLogger.section("5. Get Product Performance Analytics")
    response = test_endpoint(
        "Product Performance",
        "GET",
        f"{ANALYTICS_SERVICE_URL}/api/v1/retail/analytics/product-performance?business_id={business_id}",
        headers=headers
    )
    
    # Test 6: Inventory Turnover
    TestLogger.section("6. Get Inventory Turnover")
    response = test_endpoint(
        "Inventory Turnover",
        "GET",
        f"{ANALYTICS_SERVICE_URL}/api/v1/retail/analytics/inventory-turnover?business_id={business_id}&period_days=30",
        headers=headers
    )
    
    # Test 7: Category Performance
    TestLogger.section("7. Get Category Performance")
    response = test_endpoint(
        "Category Performance",
        "GET",
        f"{ANALYTICS_SERVICE_URL}/api/v1/retail/analytics/category-performance?business_id={business_id}",
        headers=headers
    )
    
    # Test 8: Profit Margins
    TestLogger.section("8. Get Profit Margins")
    response = test_endpoint(
        "Profit Margins",
        "GET",
        f"{ANALYTICS_SERVICE_URL}/api/v1/retail/analytics/profit-margins?business_id={business_id}",
        headers=headers
    )


def test_health_endpoints():
    """Test health check endpoints"""
    TestLogger.header("HEALTH CHECK TESTS")
    
    # Test Auth Service Health
    TestLogger.section("1. Auth Service Health")
    test_endpoint(
        "Auth Service Health",
        "GET",
        f"{AUTH_SERVICE_URL}/health"
    )
    
    # Test Analytics Service Health
    TestLogger.section("2. Analytics Service Health")
    test_endpoint(
        "Analytics Service Health",
        "GET",
        f"{ANALYTICS_SERVICE_URL}/health"
    )
    
    # Test Analytics Service Liveness
    TestLogger.section("3. Analytics Service Liveness")
    test_endpoint(
        "Analytics Service Liveness",
        "GET",
        f"{ANALYTICS_SERVICE_URL}/health/live"
    )
    
    # Test Analytics Service Readiness
    TestLogger.section("4. Analytics Service Readiness")
    test_endpoint(
        "Analytics Service Readiness",
        "GET",
        f"{ANALYTICS_SERVICE_URL}/health/ready"
    )


def generate_test_report():
    """Generate comprehensive test report"""
    TestLogger.header("TEST EXECUTION REPORT")
    
    print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Test Summary{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")
    
    TestLogger.data("Total Tests", test_results["total"])
    TestLogger.data("Passed", f"{Fore.GREEN}{test_results['passed']}{Style.RESET_ALL}")
    TestLogger.data("Failed", f"{Fore.RED}{test_results['failed']}{Style.RESET_ALL}")
    
    success_rate = (test_results["passed"] / test_results["total"] * 100) if test_results["total"] > 0 else 0
    TestLogger.data("Success Rate", f"{success_rate:.2f}%")
    
    if test_results["errors"]:
        print(f"\n{Fore.RED}{'='*80}")
        print(f"{Fore.RED}Failed Tests Details{Style.RESET_ALL}")
        print(f"{Fore.RED}{'='*80}{Style.RESET_ALL}\n")
        for i, error in enumerate(test_results["errors"], 1):
            print(f"{Fore.RED}{i}. {error}{Style.RESET_ALL}")
    
    # Test Credentials
    print(f"\n{Fore.CYAN}{'='*80}")
    print(f"{Fore.CYAN}Test Account Credentials{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")
    
    TestLogger.data("Email", test_data["user"].get("email", "N/A"))
    TestLogger.data("Password", test_data["user"].get("password", "N/A"))
    TestLogger.data("Full Name", test_data["user"].get("full_name", "N/A"))
    TestLogger.data("User ID", test_data["user"].get("id", "N/A"))
    TestLogger.data("Business ID", test_data["business"].get("id", "N/A"))
    TestLogger.data("Business Name", test_data["business"].get("name", "N/A"))
    
    # Save report to file
    report_file = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report_data = {
        "timestamp": datetime.now().isoformat(),
        "results": test_results,
        "credentials": {
            "email": test_data["user"].get("email"),
            "password": test_data["user"].get("password"),
            "full_name": test_data["user"].get("full_name"),
            "user_id": test_data["user"].get("id"),
            "business_id": test_data["business"].get("id"),
            "business_name": test_data["business"].get("name")
        },
        "test_data": {
            "products_created": len(test_data["products"]),
            "services_created": len(test_data["services"]),
            "menu_items_created": len(test_data["menu_items"])
        }
    }
    
    with open(report_file, 'w') as f:
        json.dump(report_data, f, indent=2)
    
    TestLogger.info(f"Detailed report saved to: {report_file}")
    
    print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")


def main():
    """Main test execution"""
    TestLogger.header("X-SEVENAI ENTERPRISE API TEST SUITE")
    TestLogger.info(f"Test Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    TestLogger.info(f"Auth Service: {AUTH_SERVICE_URL}")
    TestLogger.info(f"Analytics Service: {ANALYTICS_SERVICE_URL}")
    
    try:
        # Execute test suites
        test_health_endpoints()
        test_auth_service()
        test_business_service()
        test_retail_endpoints()
        test_service_based_endpoints()
        test_menu_endpoints()
        test_analytics_endpoints()
        
        # Generate report
        generate_test_report()
        
        TestLogger.info(f"Test Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Exit with appropriate code
        sys.exit(0 if test_results["failed"] == 0 else 1)
        
    except KeyboardInterrupt:
        TestLogger.warning("\nTest execution interrupted by user")
        generate_test_report()
        sys.exit(1)
    except Exception as e:
        TestLogger.error(f"Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        generate_test_report()
        sys.exit(1)


if __name__ == "__main__":
    main()
