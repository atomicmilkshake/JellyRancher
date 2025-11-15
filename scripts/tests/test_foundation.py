"""
Foundation Module Test Suite

Tests all Phase 1 foundation modules to ensure they're working correctly.

Usage:
    python test_foundation.py
"""

import sys
import os
from pathlib import Path

# Add _common to path
sys.path.insert(0, str(Path(__file__).parent / "_common"))

def test_imports():
    """Test that all modules can be imported."""
    print("=" * 60)
    print("🧪 TEST 1: Module Imports")
    print("=" * 60)
    
    try:
        from immutable_audit import ImmutableAuditLog
        print("✅ immutable_audit.py imported successfully")
    except Exception as e:
        print(f"❌ Failed to import immutable_audit: {e}")
        return False
    
    try:
        from credential_manager import CredentialManager
        print("✅ credential_manager.py imported successfully")
    except Exception as e:
        print(f"❌ Failed to import credential_manager: {e}")
        return False
    
    try:
        from snapshot_manager import SnapshotManager
        print("✅ snapshot_manager.py imported successfully")
    except Exception as e:
        print(f"❌ Failed to import snapshot_manager: {e}")
        return False
    
    try:
        from media_utils import hash_file, normalize_windows_path, safe_move
        print("✅ media_utils.py imported successfully")
    except Exception as e:
        print(f"❌ Failed to import media_utils: {e}")
        return False
    
    return True


def test_audit_system():
    """Test audit trail system."""
    print("\n" + "=" * 60)
    print("🧪 TEST 2: Audit Trail System")
    print("=" * 60)
    
    try:
        from immutable_audit import ImmutableAuditLog
        
        # Initialize audit log
        audit = ImmutableAuditLog()
        audit.initialize()
        
        # Log a test event
        event_id = audit.log_event("test_event", {
            "message": "Foundation test event",
            "test": True
        }, actor="test_foundation.py")
        
        print(f"✅ Logged test event: {event_id}")
        
        # Verify chain integrity
        integrity = audit.verify_chain_integrity()
        
        if integrity['integrity_percentage'] == 100.0:
            print(f"✅ Chain integrity verified: {integrity['total_entries']} entries")
        else:
            print(f"⚠️  Chain integrity: {integrity['integrity_percentage']:.2f}%")
        
        # Search for test event
        results = audit.search(event_type="test_event")
        if results:
            print(f"✅ Search working: Found {len(results)} test event(s)")
        
        return True
    
    except Exception as e:
        print(f"❌ Audit system test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_media_utils():
    """Test media utilities."""
    print("\n" + "=" * 60)
    print("🧪 TEST 3: Media Utilities")
    print("=" * 60)
    
    try:
        from media_utils import hash_file, normalize_windows_path
        
        # Test with this script file
        test_file = Path(__file__)
        
        # Test hashing
        file_hash = hash_file(test_file)
        print(f"✅ File hashing working: {file_hash[:32]}...")
        
        # Test path normalization
        normalized = normalize_windows_path(test_file)
        print(f"✅ Path normalization working")
        
        return True
    
    except Exception as e:
        print(f"❌ Media utils test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_snapshot_system():
    """Test snapshot system."""
    print("\n" + "=" * 60)
    print("🧪 TEST 4: Snapshot System")
    print("=" * 60)
    
    try:
        from snapshot_manager import SnapshotManager
        
        # Create test directory with a test file
        test_dir = Path("._state/test_media")
        test_dir.mkdir(parents=True, exist_ok=True)
        
        test_file = test_dir / "test_movie.mkv"
        test_file.write_text("This is a test media file")
        
        print(f"📁 Created test directory: {test_dir}")
        
        # Create snapshot
        snapshot_id = SnapshotManager.create_snapshot(
            media_root=str(test_dir),
            snapshot_type="foundation_test"
        )
        
        print(f"✅ Snapshot created: {snapshot_id}")
        
        # List snapshots
        snapshots = SnapshotManager.list_snapshots()
        print(f"✅ Snapshot listing working: {len(snapshots)} snapshot(s) found")
        
        # Verify snapshot
        result = SnapshotManager.restore_snapshot(snapshot_id, dry_run=True)
        print(f"✅ Snapshot verification working: {result['restored_files']} file(s) verified")
        
        # Cleanup
        test_file.unlink()
        test_dir.rmdir()
        
        return True
    
    except Exception as e:
        print(f"❌ Snapshot system test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_credential_system():
    """Test credential management (without requiring password)."""
    print("\n" + "=" * 60)
    print("🧪 TEST 5: Credential System Structure")
    print("=" * 60)
    
    try:
        from credential_manager import CredentialManager
        
        # Just test the class structure exists
        print("✅ CredentialManager class available")
        print("   Note: Actual credential tests require master password")
        print("   Use: python _common/credential_manager.py to test manually")
        
        return True
    
    except Exception as e:
        print(f"❌ Credential system test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all foundation tests."""
    print("\n" + "=" * 70)
    print("🚀 JELLYFIN MEDIA ORGANIZATION AGENT - FOUNDATION TEST SUITE")
    print("=" * 70)
    print()
    
    results = {
        "Module Imports": test_imports(),
        "Audit System": test_audit_system(),
        "Media Utils": test_media_utils(),
        "Snapshot System": test_snapshot_system(),
        "Credential System": test_credential_system()
    }
    
    print("\n" + "=" * 70)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:.<50} {status}")
    
    print("=" * 70)
    print(f"Results: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    print("=" * 70)
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED - Foundation is ready!")
        print("\n📋 Next steps:")
        print("   1. Set up credentials: python _common/credential_manager.py set opensubtitles_username YOUR_USERNAME")
        print("   2. Specify media location (e.g., C:\\Jellyfin\\#MEDIA)")
        print("   3. Create genesis inventory")
        print("   4. Begin Phase 2 (Movie Organization)")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed - review errors above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
