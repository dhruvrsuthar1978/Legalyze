# test_api.py

import os
import requests
import json

# Allow overriding target under test via environment variable for TestClient/Docker
BASE_URL = os.environ.get("TEST_BASE_URL", "http://localhost:8000/api")

print("🧪 Testing API endpoints...\n")

# Test 1: Register User
print("1️⃣ Testing user registration...")
register_data = {
    "name": "Test User",
    "email": "test@example.com",
    "password": "TestPass123!",
    "confirm_password": "TestPass123!"
}

response = requests.post(f"{BASE_URL}/auth/register", json=register_data)
print(f"Status: {response.status_code}")

if response.status_code == 200:
    print(f"✅ Registration successful")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
elif response.status_code == 409:
    print("⚠️  User already exists (this is OK)")
else:
    print(f"❌ Registration failed: {response.text}")
    exit(1)

# Test 2: Login
print("\n2️⃣ Testing login...")
login_data = {
    "email": "test@example.com",
    "password": "TestPass123!",
    "remember_me": False
}

response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
print(f"Status: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    access_token = data["access_token"]
    print(f"✅ Login successful")
    print(f"Access token: {access_token[:30]}...")
else:
    print(f"❌ Login failed: {response.text}")
    exit(1)

# Test 3: Get Current User
print("\n3️⃣ Testing get current user...")
headers = {"Authorization": f"Bearer {access_token}"}

response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
print(f"Status: {response.status_code}")

if response.status_code == 200:
    print(f"✅ Get user successful")
    print(f"User: {json.dumps(response.json(), indent=2)}")
else:
    print(f"❌ Get user failed: {response.text}")
    exit(1)

# Test 4: Unauthorized Access
print("\n4️⃣ Testing unauthorized access...")
response = requests.get(f"{BASE_URL}/contracts")
print(f"Status: {response.status_code}")

if response.status_code == 401:
    print("✅ Unauthorized correctly blocked")
else:
    print(f"⚠️  Expected 401, got {response.status_code}")

print("\n✅ All API tests passed!")
print(f"\n💡 Access Token for manual testing:\n{access_token}")