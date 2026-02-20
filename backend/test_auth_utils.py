# test_auth_utils.py

from app.utils.jwt_utils import create_access_token, decode_token
from app.utils.hash_utils import hash_password, verify_password

print("🧪 Testing authentication utilities...\n")

# Test JWT
print("1️⃣ Testing JWT...")
payload = {"sub": "test_user_123", "email": "test@example.com"}
token = create_access_token(payload)
print(f"✅ Token created: {token[:30]}...")

decoded = decode_token(token)
if decoded and decoded["sub"] == "test_user_123":
    print(f"✅ Token decoded successfully: {decoded}")
else:
    print("❌ Token decode failed")
    exit(1)

# Test Password Hashing
print("\n2️⃣ Testing password hashing...")
password = "TestPassword123!"
hashed = hash_password(password)
print(f"✅ Password hashed: {hashed[:30]}...")

if verify_password(password, hashed):
    print("✅ Password verification successful")
else:
    print("❌ Password verification failed")
    exit(1)

if not verify_password("WrongPassword", hashed):
    print("✅ Wrong password correctly rejected")
else:
    print("❌ Wrong password incorrectly accepted")
    exit(1)

print("\n✅ All authentication utility tests passed!")