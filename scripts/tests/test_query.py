import requests

# Test query
resp = requests.post('http://localhost:3737/memory/query', 
                     json={'query': 'Python', 'user_id': 'jellyfin_agent'})
print(f'Status: {resp.status_code}')
result = resp.json()
print(f'Results: {len(result.get("memories", []))} memories')
if result.get("memories"):
    print(f'First result: {result["memories"][0].get("content", "")[:100]}')
