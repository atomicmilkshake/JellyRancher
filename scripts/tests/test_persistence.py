import requests
import time

BACKEND = "http://localhost:3737"

# Wait for backend
print("Waiting for backend...")
time.sleep(6)

# Add a memory
print("\n1. Adding test memory...")
resp = requests.post(f"{BACKEND}/memory/add", json={
    "content": "This is a unique test memory about Python parsing functions",
    "sector": "semantic",
    "user_id": "test_user"
})
print(f"Status: {resp.status_code}")
result = resp.json()
print(f"Response: {result}")
memory_id = result.get('id')

# Query for it
print(f"\n2. Querying for memory ID: {memory_id}...")
resp2 = requests.post(f"{BACKEND}/memory/query", json={
    "query": "Python parsing",
    "user_id": "test_user"
})
print(f"Status: {resp2.status_code}")
results = resp2.json()
print(f"Found {len(results.get('memories', []))} memories")
if results.get('memories'):
    print(f"First result: {results['memories'][0]}")
