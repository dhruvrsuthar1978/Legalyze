# test_upload.py

import requests
import os

# First, login to get token
BASE_URL = os.environ.get("TEST_BASE_URL", "http://localhost:8000/api")

print("🔑 Logging in...")
login_response = requests.post(f"{BASE_URL}/auth/login", json={
    "email": "test@example.com",
    "password": "TestPass123!"
})

if login_response.status_code != 200:
    print("❌ Login failed. Run test_api.py first to create user.")
    exit(1)

token = login_response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

print("✅ Logged in\n")

# Create a sample text file (if no PDF available)
print("📄 Creating sample document...")
sample_content = """
EMPLOYMENT AGREEMENT

This Employment Agreement ("Agreement") is entered into as of January 1, 2024.

CONFIDENTIALITY
The Employee shall not disclose any confidential information to third parties during and after employment.

PAYMENT
The Company shall pay the Employee a salary of $100,000 per year.

TERMINATION
Either party may terminate this agreement with 30 days written notice.
"""

with open("sample_contract.txt", "w") as f:
    f.write(sample_content)

# Note: For real testing, use a PDF file
# For now, this will test the upload endpoint even if it fails validation

print("📤 Uploading document...")
files = {"file": ("sample_contract.pdf", open("sample_contract.txt", "rb"), "application/pdf")}
data = {"title": "Test Employment Contract", "tags": "employment,test"}

response = requests.post(
    f"{BASE_URL}/contracts/upload",
    headers=headers,
    files=files,
    data=data
)

print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")

if response.status_code in [200, 201]:
    print("\n✅ Upload successful!")
elif response.status_code == 415:
    print("\n⚠️  File type not supported (expected - we used .txt)")
    print("💡 For real upload, use a PDF file")
else:
    print(f"\n❌ Upload failed: {response.text}")

# Cleanup
os.remove("sample_contract.txt")