import requests
import time

BACKEND = "http://localhost:3737"

print("Waiting for backend...")
time.sleep(2)

# Test 1: Add memory and capture full response
print("\n=== TEST 1: Add Memory ===")
try:
    resp = requests.post(f"{BACKEND}/memory/add", json={
        "content": "Test memory about debugging SQLite storage issues in OpenMemory backend",
        "sector": "semantic",
        "user_id": "debug_user"
    }, timeout=10)
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.json()}")
except Exception as e:
    print(f"ERROR: {e}")

# Test 2: Query immediately
print("\n=== TEST 2: Query Immediately ===")
try:
    resp = requests.post(f"{BACKEND}/memory/query", json={
        "query": "SQLite storage",
        "user_id": "debug_user",
        "k": 5
    }, timeout=10)
    print(f"Status: {resp.status_code}")
    result = resp.json()
    print(f"Query: {result.get('query')}")
    print(f"Matches: {len(result.get('matches', []))}")
    if result.get('matches'):
        for i, match in enumerate(result['matches'][:3], 1):
            print(f"\nMatch {i}:")
            print(f"  ID: {match.get('id')}")
            print(f"  Score: {match.get('score')}")
            print(f"  Content: {match.get('content', '')[:100]}")
except Exception as e:
    print(f"ERROR: {e}")

# Test 3: Wait and query again
print("\n=== TEST 3: Query After Delay ===")
time.sleep(2)
try:
    resp = requests.post(f"{BACKEND}/memory/query", json={
        "query": "debugging",
        "user_id": "debug_user",
        "k": 10
    }, timeout=10)
    result = resp.json()
    print(f"Matches: {len(result.get('matches', []))}")
except Exception as e:
    print(f"ERROR: {e}")
