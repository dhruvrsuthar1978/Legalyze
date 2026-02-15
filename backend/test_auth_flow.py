import requests
import json

BASE_URL = "http://localhost:8000/api"

print("=" * 60)
print("TESTING AUTHENTICATION FLOW")
print("=" * 60)

# Test 1: Register New User
print("\nTest 1: User Registration")
register_payload = {
    "name": "Test User",
    "email": "test@legalyze.com",
    "password": "SecurePass123!",
    "confirm_password": "SecurePass123!"
}

response = requests.post(f"{BASE_URL}/auth/register", json=register_payload)
print(f"Status Code: {response.status_code}")

if response.status_code == 200:
    print("PASS: Registration successful")
    user_data = response.json()
    print(f"User: {json.dumps(user_data, indent=2)}")
elif response.status_code == 409:
    print("User already exists (OK)")
else:
    print(f"FAIL: {response.text}")
    exit(1)

# Test 2: Login
print("\nTest 2: User Login")
login_payload = {
    "email": "test@legalyze.com",
    "password": "SecurePass123!",
    "remember_me": False
}

response = requests.post(f"{BASE_URL}/auth/login", json=login_payload)
print(f"Status Code: {response.status_code}")

if response.status_code == 200:
    print("PASS: Login successful")
    token_data = response.json()
    access_token = token_data.get("access_token")
    print(f"Access Token: {access_token[:50]}...")
    
    with open("test_token.txt", "w") as f:
        f.write(access_token)
    print("Token saved to test_token.txt")
else:
    print(f"FAIL: {response.text}")
    exit(1)

# Test 3: Get Current User
print("\nTest 3: Get Current User")
headers = {"Authorization": f"Bearer {access_token}"}
response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
print(f"Status Code: {response.status_code}")

if response.status_code == 200:
    print("PASS: Profile retrieved")
else:
    print(f"FAIL: {response.text}")

print("\n" + "=" * 60)
print("TESTS COMPLETE")
print("=" * 60)