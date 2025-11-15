"""
Quick test to verify DeepMemory query functionality.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "_common"))

from deepmemory_integration import DeepMemoryIntegrator

def test_query():
    """Test querying the ingested project knowledge."""
    print("\n" + "="*60)
    print("TESTING DEEPMEMORY QUERY")
    print("="*60 + "\n")
    
    # Initialize with project knowledge user_id
    memory = DeepMemoryIntegrator(user_id="jellyfin_project_knowledge")
    
    if not memory.initialize():
        print("❌ Failed to connect to OpenMemory")
        return False
    
    print("✅ Connected to OpenMemory\n")
    
    # Test queries
    queries = [
        "audit trail system",
        "immutable audit",
        "credential encryption",
        "deepmemory integration",
        "organize movies"
    ]
    
    for query in queries:
        print(f"🔍 Query: '{query}'")
        results = memory.query_memory(query, k=3)
        print(f"   Found {len(results)} results")
        
        if results:
            for i, result in enumerate(results[:2], 1):
                # Try different possible keys for source info
                content_preview = result.get("content", "")[:60]
                score = result.get("score", 0)
                sector = result.get("primary_sector", "unknown")
                print(f"   {i}. [{sector}] Score: {score:.3f}")
                print(f"      {content_preview}...")
        print()
    
    return True

if __name__ == "__main__":
    success = test_query()
    if success:
        print("✅ Memory query test completed")
    else:
        print("❌ Memory query test failed")
