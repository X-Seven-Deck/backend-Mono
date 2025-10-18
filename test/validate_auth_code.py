#!/usr/bin/env python3
"""
Code structure validation for X-sevenAI Auth Service.
Tests imports and validates code structure without running the service.
"""

import sys
import os

# Set up proper Python path for imports
AUTH_SERVICE_PATH = '/Users/naveen/Desktop/x7AI/services/auth-service'
SHARED_LIBS_PATH = '/Users/naveen/Desktop/x7AI/shared/libs'

# Add paths to sys.path if not already there
if AUTH_SERVICE_PATH not in sys.path:
    sys.path.insert(0, AUTH_SERVICE_PATH)
if SHARED_LIBS_PATH not in sys.path:
    sys.path.insert(0, SHARED_LIBS_PATH)

class TestResult:
    """Test result tracker."""

    def __init__(self):
        self.passed = 0
        self.failed = 0

    def add_result(self, test_name: str, passed: bool, error: str = None):
        """Add a test result."""
        if passed:
            self.passed += 1
            print(f"✅ {test_name}")
        else:
            self.failed += 1
            print(f"❌ {test_name}: {error}")

    def summary(self):
        """Print test summary."""
        print(f"\n{'='*50}")
        print(f"CODE VALIDATION SUMMARY")
        print(f"{'='*50}")
        print(f"Total Tests: {self.passed + self.failed}")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        print(f"Success Rate: {(self.passed / (self.passed + self.failed) * 100):.1f}%")
        print(f"{'='*50}")

def test_imports():
    """Test all imports work correctly."""
    results = TestResult()

    # Ensure paths are set up for each import test
    if AUTH_SERVICE_PATH not in sys.path:
        sys.path.insert(0, AUTH_SERVICE_PATH)
    if SHARED_LIBS_PATH not in sys.path:
        sys.path.insert(0, SHARED_LIBS_PATH)

    try:
        # Test main app import - need to add app subdirectory to path
        app_path = os.path.join(AUTH_SERVICE_PATH, 'app')
        if app_path not in sys.path:
            sys.path.insert(0, app_path)

        from app.main import app
        results.add_result("Main App Import", True)
    except Exception as e:
        results.add_result("Main App Import", False, str(e))

    try:
        # Test route imports
        from routes.auth import router as auth_router
        results.add_result("Auth Routes Import", True)
    except Exception as e:
        results.add_result("Auth Routes Import", False, str(e))

    try:
        from routes.users import router as users_router
        results.add_result("Users Routes Import", True)
    except Exception as e:
        results.add_result("Users Routes Import", False, str(e))

    try:
        from routes.business import router as business_router
        results.add_result("Business Routes Import", True)
    except Exception as e:
        results.add_result("Business Routes Import", False, str(e))

    try:
        # Test service imports
        from services.auth_service import AuthService
        results.add_result("Auth Service Import", True)
    except Exception as e:
        results.add_result("Auth Service Import", False, str(e))

    try:
        # Test model imports
        from models.user import UserCreate, UserLogin, UserResponse
        results.add_result("User Models Import", True)
    except Exception as e:
        results.add_result("User Models Import", False, str(e))

    try:
        from models.token import Token, TokenData
        results.add_result("Token Models Import", True)
    except Exception as e:
        results.add_result("Token Models Import", False, str(e))

    try:
        # Test config imports
        from config.settings import settings
        results.add_result("Settings Import", True)
    except Exception as e:
        results.add_result("Settings Import", False, str(e))

    try:
        # Test supabase client import (already in path)
        from supabase_client import SupabaseManager
        results.add_result("Supabase Client Import", True)
    except Exception as e:
        results.add_result("Supabase Client Import", False, str(e))

    return results

def test_code_structure():
    """Test code structure and dependencies."""
    results = TestResult()

    # Check if all required files exist
    required_files = [
        '/Users/naveen/Desktop/x7AI/services/auth-service/app/main.py',
        '/Users/naveen/Desktop/x7AI/services/auth-service/app/routes/auth.py',
        '/Users/naveen/Desktop/x7AI/services/auth-service/app/services/auth_service.py',
        '/Users/naveen/Desktop/x7AI/services/auth-service/app/models/user.py',
        '/Users/naveen/Desktop/x7AI/services/auth-service/app/models/token.py',
        '/Users/naveen/Desktop/x7AI/services/auth-service/app/config/settings.py',
        '/Users/naveen/Desktop/x7AI/shared/libs/supabase_client.py',
        '/Users/naveen/Desktop/x7AI/.env'
    ]

    for file_path in required_files:
        if os.path.exists(file_path):
            results.add_result(f"File exists: {os.path.basename(file_path)}", True)
        else:
            results.add_result(f"File exists: {os.path.basename(file_path)}", False, f"File not found: {file_path}")

    # Check Python path setup
    try:
        import sys
        auth_service_path = '/Users/naveen/Desktop/x7AI/services/auth-service'
        shared_libs_path = '/Users/naveen/Desktop/x7AI/shared/libs'

        if auth_service_path in sys.path:
            results.add_result("Auth Service in Python Path", True)
        else:
            results.add_result("Auth Service in Python Path", False, "Auth service path not in sys.path")

        if shared_libs_path in sys.path:
            results.add_result("Shared Libs in Python Path", True)
        else:
            results.add_result("Shared Libs in Python Path", False, "Shared libs path not in sys.path")
    except Exception as e:
        results.add_result("Python Path Check", False, str(e))

    return results

def test_environment_configuration():
    """Test environment configuration."""
    results = TestResult()

    try:
        import os
        from dotenv import load_dotenv

        # Load environment variables
        load_dotenv('/Users/naveen/Desktop/x7AI/.env')

        required_env_vars = [
            'SUPABASE_URL',
            'SUPABASE_ANON_KEY',
            'SUPABASE_SERVICE_ROLE_KEY',
            'JWT_SECRET'
        ]

        for var in required_env_vars:
            value = os.getenv(var)
            if value and value.strip():
                results.add_result(f"Environment Variable: {var}", True)
            else:
                results.add_result(f"Environment Variable: {var}", False, f"Variable not set or empty")

    except Exception as e:
        results.add_result("Environment Configuration", False, str(e))

    return results

def main():
    """Main validation function."""
    print("🔍 X-sevenAI Auth Service - Code Structure Validation")
    print("=" * 60)

    # Run all validation tests
    import_results = test_imports()
    structure_results = test_code_structure()
    env_results = test_environment_configuration()

    # Combine results
    total_passed = import_results.passed + structure_results.passed + env_results.passed
    total_failed = import_results.failed + structure_results.failed + env_results.failed

    print(f"OVERALL VALIDATION SUMMARY")
    print(f"{'='*50}")
    print(f"Total Tests: {total_passed + total_failed}")
    print(f"Passed: {total_passed}")
    print(f"Failed: {total_failed}")
    print(f"Success Rate: {(total_passed / (total_passed + total_failed) * 100):.1f}%")
    print(f"{'='*50}")

    if total_failed == 0:
        print("🎉 All validations passed! Code structure is correct.")
        print("✅ Ready to run the auth service.")
        print(f"⚠️  {total_failed} validation(s) failed.")
        print("❌ Please fix the issues before running the service.")

if __name__ == "__main__":
    main()
