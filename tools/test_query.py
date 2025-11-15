#!/usr/bin/env python3
from scripts.core.chroma_memory_backend import get_memory_backend

backend = get_memory_backend()
query = "recent work"
print(f"Querying '{query}'...")

try:
    data = backend.query_memory(query, limit=5, include_metadata=True)
    print(f"Returned {len(data)} results")
    for i, m in enumerate(data):
        print(f"Result {i+1}:")
        print(f"  Content: {m.get('content', 'N/A')[:100]}...")
        print(f"  Category: {m.get('metadata', {}).get('category', 'N/A')}")
        print(f"  Tags: {m.get('tags', [])}")
        print(f"  Distance: {m.get('distance', 'N/A')}")
    print("Query successful!")
except Exception as e:
    print(f"Query failed: {e}")
    import traceback
    traceback.print_exc()
