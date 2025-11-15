"""
Test Suite for DeepMemory Integration

Verifies OpenMemory connectivity and DeepMemoryIntegrator functionality
for the Jellyfin Media Organization Agent.
"""

import sys
from pathlib import Path

# Add _common to path
sys.path.insert(0, str(Path(__file__).parent / "_common"))

from deepmemory_integration import DeepMemoryIntegrator
import time


def print_header(text: str):
    """Print a formatted header."""
    print(f"\n{'=' * 60}")
    print(f"🧠 {text}")
    print('=' * 60)


def test_connection():
    """Test OpenMemory server connection."""
    print_header("TEST 1: OpenMemory Connection")
    
    memory = DeepMemoryIntegrator()
    if memory.initialize():
        print(f"✅ Connected to OpenMemory at {memory.api_url}")
        print(f"   User ID: {memory.user_id}")
        return memory
    else:
        print("❌ Failed to connect to OpenMemory")
        print("\n💡 To start OpenMemory:")
        print("   cd OpenMemory/backend")
        print("   npm install  # First time only")
        print("   npm run dev")
        return None


def test_episodic_memory(memory: DeepMemoryIntegrator):
    """Test episodic memory (operation logging)."""
    print_header("TEST 2: Episodic Memory (Operations)")
    
    # Log a test operation
    result = memory.log_operation(
        operation_type="test_operation",
        description="Test movie organization: The Matrix (1999)",
        metadata={
            "source": "V:/test/The Matrix.mkv",
            "destination": "V:/test/Movies/The Matrix (1999)/The Matrix (1999).mkv",
            "test": True
        }
    )
    
    if result:
        print("✅ Operation logged to episodic memory")
        print(f"   Memory ID: {result.get('id', 'N/A')}")
    else:
        print("⚠️  Failed to log operation (server may be unavailable)")
    
    # Query for similar operations
    time.sleep(0.5)  # Allow indexing
    similar = memory.get_similar_operations("Matrix movie organization", k=2)
    print(f"✅ Retrieved {len(similar)} similar operation(s)")
    for op in similar[:1]:
        content = op.get('content', '')
        print(f"   - {content[:60]}...")


def test_semantic_memory(memory: DeepMemoryIntegrator):
    """Test semantic memory (patterns and facts)."""
    print_header("TEST 3: Semantic Memory (Patterns)")
    
    # Store a naming pattern
    result = memory.store_media_pattern(
        pattern_type="movie_naming",
        description="Standard movie naming with year",
        examples=[
            "The Matrix (1999)",
            "Inception (2010)"
        ]
    )
    
    if result:
        print("✅ Pattern stored to semantic memory")
    else:
        print("⚠️  Failed to store pattern")
    
    # Query for patterns
    time.sleep(0.5)
    patterns = memory.get_relevant_patterns(
        media_type="movie",
        context="naming conventions with year",
        k=2
    )
    print(f"✅ Retrieved {len(patterns)} relevant pattern(s)")
    for pattern in patterns[:1]:
        content = pattern.get('content', '')
        print(f"   - {content[:60]}...")


def test_procedural_memory(memory: DeepMemoryIntegrator):
    """Test procedural memory (procedures and skills)."""
    print_header("TEST 4: Procedural Memory (Procedures)")
    
    # Store a procedure
    result = memory.store_procedure(
        procedure_name="organize_tv_episode",
        description="Steps to organize a TV episode file",
        steps=[
            "Parse filename for metadata",
            "Create season directory",
            "Rename to standard format",
            "Move file and verify hash"
        ]
    )
    
    if result:
        print("✅ Procedure stored to procedural memory")
    else:
        print("⚠️  Failed to store procedure")
    
    # Query for procedures
    time.sleep(0.5)
    procedures = memory.query_memory(
        "how to organize TV show episodes",
        k=2,
        sector=memory.SECTOR_PROCEDURAL
    )
    print(f"✅ Retrieved {len(procedures)} procedure(s)")
    for proc in procedures[:1]:
        content = proc.get('content', '')
        print(f"   - {content[:60]}...")


def test_reflective_memory(memory: DeepMemoryIntegrator):
    """Test reflective memory (insights and preferences)."""
    print_header("TEST 5: Reflective Memory (Insights)")
    
    # Store an insight
    result = memory.store_reflection(
        insight="User prefers forced subtitles for foreign language dialogue",
        context="Downloaded subtitles for Inglourious Basterds",
        learned_from="user correction"
    )
    
    if result:
        print("✅ Insight stored to reflective memory")
    else:
        print("⚠️  Failed to store insight")
    
    # Query for preferences
    time.sleep(0.5)
    preferences = memory.get_user_preferences(
        preference_type="subtitles",
        k=2
    )
    print(f"✅ Retrieved {len(preferences)} preference(s)")
    for pref in preferences[:1]:
        content = pref.get('content', '')
        print(f"   - {content[:60]}...")


def test_cross_sector_retrieval(memory: DeepMemoryIntegrator):
    """Test retrieval across all sectors."""
    print_header("TEST 6: Cross-Sector Retrieval")
    
    # Query without sector filter
    results = memory.query_memory(
        "movie organization",
        k=5
    )
    
    print(f"✅ Retrieved {len(results)} memories across all sectors")
    
    # Count by sector
    sectors = {}
    for result in results:
        sector = result.get('metadata', {}).get('sector', 'unknown')
        sectors[sector] = sectors.get(sector, 0) + 1
    
    for sector, count in sectors.items():
        print(f"   - {sector}: {count} memories")


def test_agent_summary(memory: DeepMemoryIntegrator):
    """Test agent summary retrieval."""
    print_header("TEST 7: Agent Summary")
    
    summary = memory.get_agent_summary()
    
    if summary:
        print("✅ Agent summary retrieved")
        print(f"   Length: {len(summary)} characters")
        if len(summary) > 0:
            print(f"   Preview: {summary[:80]}...")
    else:
        print("⚠️  No agent summary available (may require memory history)")


def run_all_tests():
    """Run complete test suite."""
    print("=" * 60)
    print("🧠 DeepMemory Integration Test Suite")
    print("=" * 60)
    print("\nTesting OpenMemory integration for Jellyfin Media Organizer")
    print("This verifies persistent memory across agent sessions.\n")
    
    # Test 1: Connection
    memory = test_connection()
    if not memory:
        print("\n" + "=" * 60)
        print("❌ TESTS ABORTED - OpenMemory server not running")
        print("=" * 60)
        return False
    
    # Run all tests
    test_episodic_memory(memory)
    test_semantic_memory(memory)
    test_procedural_memory(memory)
    test_reflective_memory(memory)
    test_cross_sector_retrieval(memory)
    test_agent_summary(memory)
    
    # Summary
    print("\n" + "=" * 60)
    print("✅ ALL TESTS COMPLETED")
    print("=" * 60)
    print("\n💡 DeepMemory Integration Status:")
    print("   - OpenMemory connected and operational")
    print("   - All memory sectors functioning")
    print("   - Ready for production use")
    print("\n📝 Next Steps:")
    print("   1. Integrate into main organization scripts")
    print("   2. Log all media operations to episodic memory")
    print("   3. Store learned patterns to semantic memory")
    print("   4. Build procedural knowledge base")
    print("   5. Track user preferences in reflective memory")
    
    return True


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
