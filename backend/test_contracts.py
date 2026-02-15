import requests
import json

token = open("test_token.txt").read().strip()
headers = {"Authorization": f"Bearer {token}"}

print("=" * 60)
print("Testing Contract Endpoints")
print("=" * 60)

# Test 1: Get contracts
print("\n1. GET /api/contracts")
r = requests.get("http://localhost:8000/api/contracts", headers=headers)
print(f"Status: {r.status_code}")
if r.status_code == 200:
    print(f"Response: {json.dumps(r.json(), indent=2)}")
else:
    print(f"Error: {r.text}")

# Test 2: Get stats
print("\n2. GET /api/contracts/stats")
r = requests.get("http://localhost:8000/api/contracts/stats", headers=headers)
print(f"Status: {r.status_code}")
if r.status_code == 200:
    print(f"Response: {json.dumps(r.json(), indent=2)}")
else:
    print(f"Error: {r.text}")

print("\n" + "=" * 60)
print("Tests Complete")
print("=" * 60)
