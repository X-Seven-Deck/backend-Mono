import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
AUTH_URL = "http://localhost:9999"
ANON_KEY = os.getenv("ANON_KEY", "your-anon-key")
SITE_URL = os.getenv("SITE_URL", "http://localhost:3000")

def test_auth_flow():
    # Test user credentials
    test_email = "test@example.com"
    test_password = "Test@1234"
    
    # Headers for the requests
    headers = {
        "apikey": ANON_KEY,
        "Authorization": f"Bearer {ANON_KEY}",
        "Content-Type": "application/json"
    }
    
    # 1. Test signup
    print("Testing signup...")
    signup_data = {
        "email": test_email,
        "password": test_password,
        "data": {"full_name": "Test User"}
    }
    
    try:
        response = requests.post(
            f"{AUTH_URL}/auth/v1/signup",
            headers=headers,
            json=signup_data
        )
        response.raise_for_status()
        print("✅ Signup successful!")
        print(json.dumps(response.json(), indent=2))
        
        # Get the session token
        session_token = response.json().get("session", {}).get("access_token")
        
        if not session_token:
            print("❌ No session token received")
            return
        
        # 2. Test getting user info
        print("\nTesting get user info...")
        user_headers = {
            "Authorization": f"Bearer {session_token}",
            "apikey": ANON_KEY
        }
        
        response = requests.get(
            f"{AUTH_URL}/auth/v1/user",
            headers=user_headers
        )
        response.raise_for_status()
        print("✅ Get user info successful!")
        print(json.dumps(response.json(), indent=2))
        
        # 3. Test sign out
        print("\nTesting sign out...")
        response = requests.post(
            f"{AUTH_URL}/auth/v1/logout",
            headers={
                "Authorization": f"Bearer {session_token}",
                "apikey": ANON_KEY
            }
        )
        print("✅ Sign out successful!")
        
        # 4. Test sign in
        print("\nTesting sign in...")
        signin_data = {
            "email": test_email,
            "password": test_password
        }
        
        response = requests.post(
            f"{AUTH_URL}/auth/v1/token?grant_type=password",
            headers=headers,
            json=signin_data
        )
        response.raise_for_status()
        print("✅ Sign in successful!")
        print(json.dumps(response.json(), indent=2))
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response status: {e.response.status_code}")
            print(f"Response body: {e.response.text}")

if __name__ == "__main__":
    print("Starting Supabase Auth test...")
    test_auth_flow()
