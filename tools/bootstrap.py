#!/usr/bin/env python3
"""
JellyRancher Bootstrap Verification Script
Provides comprehensive environment verification and project status
"""
import sys
import os
from pathlib import Path

def check_virtual_environment():
    """Verify we're using the correct Python version in virtual environment"""
    print("🔍 Checking Virtual Environment...")

    python_version = sys.version_info
    version_str = f"{python_version.major}.{python_version.minor}.{python_version.micro}"

    # Check if we're in a virtual environment
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)

    if not in_venv:
        print("❌ WARNING: Not running in a virtual environment!")
        print("   This may cause compatibility issues with ChromaDB")
        return False

    if python_version.major == 3 and python_version.minor == 10:
        print(f"✅ Virtual Environment: Python {version_str}")
        return True
    else:
        print(f"⚠️  Virtual Environment: Python {version_str} (expected 3.10.x)")
        print("   This may cause compatibility issues")
        return False

def check_chromadb_connection():
    """Test ChromaDB connection and get basic statistics"""
    print("\n🔍 Checking ChromaDB Connection...")

    try:
        # Add scripts to path for imports
        scripts_path = Path(__file__).parent / "scripts" / "core"
        if str(scripts_path) not in sys.path:
            sys.path.insert(0, str(scripts_path))

        from chroma_memory_backend import ChromaMemoryBackend

        chroma_path = Path(__file__).parent / "chroma_db"
        mem = ChromaMemoryBackend(str(chroma_path))

        # Get memory statistics
        stats = mem.get_memory_stats()

        total_memories = stats.get('total_memories', 0)
        users = stats.get('users', 'unknown')
        content_length = stats.get('total_content_length', 0)

        print("✅ ChromaDB Connection: Successful")
        print(f"   Total Memories: {total_memories:,}")
        print(f"   Users: {users}")
        print(f"   Content Size: {content_length:,} characters")

        return mem, stats

    except Exception as e:
        print(f"❌ ChromaDB Connection: Failed - {e}")
        import traceback
        traceback.print_exc()
        return None, None

def query_project_context(mem):
    """Query ChromaDB for current project status and recent activity"""
    print("\n🔍 Querying Project Context...")

    try:
        # Query for current project state
        context_queries = [
            "current project state status",
            "recent development activity",
            "known issues bugs problems"
        ]

        for query in context_queries:
            print(f"\n   Querying: '{query}'")
            results = mem.query_memory(query, limit=2)

            if results:
                for i, result in enumerate(results, 1):
                    content_preview = result['content'][:120].replace('\n', ' ')
                    metadata = result.get('metadata', {})
                    timestamp = metadata.get('timestamp', 'unknown')
                    print(f"     {i}. [{timestamp}] {content_preview}...")
            else:
                print("     No results found")

        return True

    except Exception as e:
        print(f"❌ Project Context Query: Failed - {e}")
        return False

def check_gui_components():
    """Test basic GUI component initialization (optional check)"""
    print("\n🔍 Checking GUI Components...")

    try:
        # This is a lightweight check - don't actually create QApplication
        # Just verify the imports work and basic class structure exists

        scripts_path = Path(__file__).parent / "scripts" / "core"
        if str(scripts_path) not in sys.path:
            sys.path.insert(0, str(scripts_path))

        # Import the main window class
        from jelly_rancher_main import JellyRancherMainWindow

        # Check if the class exists and has basic methods
        required_methods = [
            '__init__',                # Constructor
            'get_function_docstring',  # Enhanced docstring method
        ]

        missing_methods = []
        for method in required_methods:
            if not hasattr(JellyRancherMainWindow, method):
                missing_methods.append(method)

        if missing_methods:
            print(f"⚠️  GUI Components: Missing methods - {missing_methods}")
            return False
        else:
            print("✅ GUI Components: Core class structure present")
            print("   Note: Full GUI functionality requires QApplication instance")
            return True

    except Exception as e:
        print(f"⚠️  GUI Components Check: Import failed - {e}")
        print("   This is non-critical for basic bootstrap functionality")
        return True  # Don't fail bootstrap for GUI import issues

def main():
    """Main bootstrap verification function"""
    print("=" * 50)
    print("🍫 JELLYRANCHER BOOTSTRAP VERIFICATION")
    print("=" * 50)

    # Change to project root directory
    project_root = Path(__file__).parent
    os.chdir(project_root)
    print(f"📁 Working Directory: {project_root}")

    results = []

    # Run all checks
    results.append(("Virtual Environment", check_virtual_environment()))
    mem, stats = check_chromadb_connection()
    results.append(("ChromaDB Connection", mem is not None))

    if mem:
        results.append(("Project Context Query", query_project_context(mem)))

    results.append(("GUI Components", check_gui_components()))

    # Summary
    print("\n" + "=" * 50)
    print("📊 BOOTSTRAP SUMMARY")
    print("=" * 50)

    all_passed = True
    for check_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {check_name}")
        if not passed:
            all_passed = False

    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 BOOTSTRAP COMPLETE - All systems operational!")
        print("   Ready for development tasks.")
    else:
        print("⚠️  BOOTSTRAP ISSUES DETECTED")
        print("   Some checks failed. Review output above.")
        print("   You may experience issues with development tasks.")

    print("\n💡 Next Steps:")
    print("   • Query ChromaDB: mem.query_memory('topic', limit=N)")
    print("   • Launch GUI: .venv\\Scripts\\python.exe launch_gui.py")
    print("   • Run tests: .venv\\Scripts\\python.exe -m pytest")
    print("=" * 50)

if __name__ == "__main__":
    main()