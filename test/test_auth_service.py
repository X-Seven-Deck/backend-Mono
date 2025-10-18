#!/usr/bin/env python3
"""
Comprehensive test script for X-sevenAI Auth Service endpoints.
Tests all authentication and authorization endpoints in production-grade manner.
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, Any
import uuid

import httpx
import jwt
from pydantic import BaseModel, EmailStr

# Set up proper Python path for imports
AUTH_SERVICE_PATH = '/Users/naveen/Desktop/x7AI/services/auth-service'
SHARED_LIBS_PATH = '/Users/naveen/Desktop/x7AI/shared/libs'

# Add paths to sys.path if not already there
if AUTH_SERVICE_PATH not in sys.path:
    sys.path.insert(0, AUTH_SERVICE_PATH)
if SHARED_LIBS_PATH not in sys.path:
    sys.path.insert(0, SHARED_LIBS_PATH)

# Test configuration
AUTH_SERVICE_URL = "http://localhost:8010"
API_BASE = f"{AUTH_SERVICE_URL}/api/v1/auth"

class TestUser(BaseModel):
    """Test user data model."""
    email: EmailStr
    password: str = "TestPass123!"
    full_name: str = "Test User"
    phone_number: str = "+1234567890"
    role: str = "customer"

class TestResult:
    """Test result tracker."""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests = []

    def add_result(self, test_name: str, passed: bool, error: str = None, response_data: Any = None):
        """Add a test result."""
        self.tests.append({
            "test": test_name,
            "passed": passed,
            "error": error,
            "response": response_data,
            "timestamp": datetime.now().isoformat()
        })

        if passed:
            self.passed += 1
            print(f"✅ {test_name}")
        else:
            self.failed += 1
            print(f"❌ {test_name}: {error}")

    def summary(self):
        """Print test summary."""
        print(f"\n{'='*50}")
        print(f"TEST SUMMARY")
        print(f"{'='*50}")
        print(f"Total Tests: {self.passed + self.failed}")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        print(f"Success Rate: {(self.passed / (self.passed + self.failed) * 100):.1f}%")
        print(f"{'='*50}")

class AuthTester:
    """Authentication service tester."""

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.test_user = TestUser(
            email=f"test_{uuid.uuid4()}@example.com",
            full_name="Test User",
            phone_number="+1234567890"
        )
        self.token = None
        self.results = TestResult()

    async def cleanup(self):
        """Cleanup test resources."""
        await self.client.aclose()

    async def test_health_check(self):
        """Test health check endpoint."""
        try:
            response = await self.client.get(f"{AUTH_SERVICE_URL}/health")
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    self.results.add_result("Health Check", True, response_data=data)
                else:
                    self.results.add_result("Health Check", False, f"Expected 'healthy', got '{data.get('status')}'")
            else:
                self.results.add_result("Health Check", False, f"Status code {response.status_code}")
        except Exception as e:
            self.results.add_result("Health Check", False, str(e))

    async def test_user_registration(self):
        """Test user registration endpoint."""
        try:
            user_data = {
                "email": self.test_user.email,
                "password": self.test_user.password,
                "confirm_password": self.test_user.password,
                "full_name": self.test_user.full_name,
                "phone_number": self.test_user.phone_number,
                "avatar_url": None,
                "role": self.test_user.role
            }

            response = await self.client.post(f"{API_BASE}/register", json=user_data)

            if response.status_code == 201:
                data = response.json()
                if "id" in data and "email" in data:
                    self.results.add_result("User Registration", True, response_data=data)
                else:
                    self.results.add_result("User Registration", False, "Response missing id or email")
            elif response.status_code == 400 and "already registered" in response.text.lower():
                # User might already exist from previous test run
                self.results.add_result("User Registration", True, "User already exists (acceptable)")
            else:
                self.results.add_result("User Registration", False, f"Status code {response.status_code}: {response.text}")
        except Exception as e:
            self.results.add_result("User Registration", False, str(e))

    async def test_user_login(self):
        """Test user login endpoint."""
        try:
            login_data = {
                "email": self.test_user.email,
                "password": self.test_user.password
            }

            response = await self.client.post(f"{API_BASE}/login", json=login_data)

            if response.status_code == 200:
                data = response.json()
                if "access_token" in data and "token_type" in data:
                    self.token = data["access_token"]
                    self.results.add_result("User Login", True, response_data=data)
                else:
                    self.results.add_result("User Login", False, "Response missing access_token or token_type")
            else:
                self.results.add_result("User Login", False, f"Status code {response.status_code}: {response.text}")
        except Exception as e:
            self.results.add_result("User Login", False, str(e))

    async def test_oauth2_token_endpoint(self):
        """Test OAuth2 token endpoint."""
        try:
            login_data = {
                "username": self.test_user.email,
                "password": self.test_user.password
            }

            response = await self.client.post(f"{API_BASE}/token", data=login_data)

            if response.status_code == 200:
                data = response.json()
                if "access_token" in data and "token_type" in data:
                    oauth_token = data["access_token"]
                    # Verify tokens are different (OAuth2 should generate new token)
                    if oauth_token != self.token:
                        self.results.add_result("OAuth2 Token Endpoint", True, response_data=data)
                    else:
                        self.results.add_result("OAuth2 Token Endpoint", False, "OAuth2 token same as regular login token")
                else:
                    self.results.add_result("OAuth2 Token Endpoint", False, "Response missing access_token or token_type")
            else:
                self.results.add_result("OAuth2 Token Endpoint", False, f"Status code {response.status_code}: {response.text}")
        except Exception as e:
            self.results.add_result("OAuth2 Token Endpoint", False, str(e))

    async def test_get_current_user(self):
        """Test get current user endpoint."""
        if not self.token:
            self.results.add_result("Get Current User", False, "No token available from login")
            return

        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = await self.client.get(f"{API_BASE}/me", headers=headers)

            if response.status_code == 200:
                data = response.json()
                if "id" in data and "email" in data:
                    if data["email"] == self.test_user.email:
                        self.results.add_result("Get Current User", True, response_data=data)
                    else:
                        self.results.add_result("Get Current User", False, f"Email mismatch: expected {self.test_user.email}, got {data['email']}")
                else:
                    self.results.add_result("Get Current User", False, "Response missing id or email")
            else:
                self.results.add_result("Get Current User", False, f"Status code {response.status_code}: {response.text}")
        except Exception as e:
            self.results.add_result("Get Current User", False, str(e))

    async def test_invalid_credentials(self):
        """Test login with invalid credentials."""
        try:
            login_data = {
                "email": self.test_user.email,
                "password": "WrongPassword123!"
            }

            response = await self.client.post(f"{API_BASE}/login", json=login_data)

            if response.status_code == 401:
                data = response.json()
                if "detail" in data:
                    self.results.add_result("Invalid Credentials Test", True, response_data=data)
                else:
                    self.results.add_result("Invalid Credentials Test", False, "Response missing detail")
            else:
                self.results.add_result("Invalid Credentials Test", False, f"Expected 401, got {response.status_code}")
        except Exception as e:
            self.results.add_result("Invalid Credentials Test", False, str(e))

    async def test_invalid_token(self):
        """Test get current user with invalid token."""
        try:
            headers = {"Authorization": "Bearer invalid_token_12345"}
            response = await self.client.get(f"{API_BASE}/me", headers=headers)

            if response.status_code == 401:
                data = response.json()
                if "detail" in data:
                    self.results.add_result("Invalid Token Test", True, response_data=data)
                else:
                    self.results.add_result("Invalid Token Test", False, "Response missing detail")
            else:
                self.results.add_result("Invalid Token Test", False, f"Expected 401, got {response.status_code}")
        except Exception as e:
            self.results.add_result("Invalid Token Test", False, str(e))

    async def test_jwt_token_validation(self):
        """Test JWT token structure and validation."""
        if not self.token:
            self.results.add_result("JWT Token Validation", False, "No token available")
            return

        try:
            # Decode token without verification to check structure
            import base64

            # Split the JWT and decode payload
            parts = self.token.split('.')
            if len(parts) != 3:
                self.results.add_result("JWT Token Validation", False, "Invalid JWT structure")
                return

            # Decode payload (middle part)
            payload_b64 = parts[1]
            # Add padding if needed
            payload_b64 += '=' * (4 - len(payload_b64) % 4)
            payload_bytes = base64.urlsafe_b64decode(payload_b64)
            payload = json.loads(payload_bytes)

            # Check required fields
            required_fields = ["sub", "email", "role", "exp", "iat", "iss", "aud"]
            missing_fields = [field for field in required_fields if field not in payload]

            if missing_fields:
                self.results.add_result("JWT Token Validation", False, f"Missing fields: {missing_fields}")
            else:
                # Check expiration
                import time
                current_time = int(time.time())
                if payload["exp"] > current_time:
                    self.results.add_result("JWT Token Validation", True, response_data=payload)
                else:
                    self.results.add_result("JWT Token Validation", False, "Token already expired")
        except Exception as e:
            self.results.add_result("JWT Token Validation", False, str(e))

    async def run_all_tests(self):
        """Run all tests."""
        print("🧪 Starting Auth Service Tests")
        print("=" * 50)

        # Run tests in order
        await self.test_health_check()
        await self.test_user_registration()
        await self.test_user_login()
        await self.test_oauth2_token_endpoint()
        await self.test_get_current_user()
        await self.test_invalid_credentials()
        await self.test_invalid_token()
        await self.test_jwt_token_validation()

        self.results.summary()

        return self.results

async def main():
    """Main test function."""
    print("🚀 X-sevenAI Auth Service - Comprehensive Test Suite")
    print("=" * 60)

    # Check if service is running
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{AUTH_SERVICE_URL}/health", timeout=5.0)
            if response.status_code != 200:
                print(f"❌ Auth service not responding at {AUTH_SERVICE_URL}")
                print("Please start the auth service first:")
                print("cd services/auth-service && python -m app.main")
                return
    except Exception as e:
        print(f"❌ Cannot connect to auth service at {AUTH_SERVICE_URL}")
        print(f"Error: {e}")
        print("Please start the auth service first.")
        return

    # Run tests
    tester = AuthTester()
    try:
        results = await tester.run_all_tests()
        if results.failed == 0:
            print("🎉 All tests passed! Auth service is working correctly.")
        else:
            print(f"⚠️  {results.failed} test(s) failed. Please check the errors above.")
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
