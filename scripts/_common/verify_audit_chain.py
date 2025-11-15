"""
Audit Chain Integrity Verification Utility

Standalone script to verify the integrity of the audit trail.
Walks through all audit log files and verifies cryptographic hash chain.

Usage:
    python verify_audit_chain.py
    
    # Or with custom log directory
    python verify_audit_chain.py --log-dir ./custom-audit-logs
"""

import sys
from pathlib import Path

# Add _common to path
sys.path.insert(0, str(Path(__file__).parent))

from _common.immutable_audit import ImmutableAuditLog


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Verify audit trail integrity"
    )
    parser.add_argument(
        '--log-dir',
        type=str,
        default='./audit-logs',
        help='Directory containing audit logs (default: ./audit-logs)'
    )
    
    args = parser.parse_args()
    
    print("🔍 Verifying Audit Chain Integrity...\n")
    
    # Initialize audit system
    audit = ImmutableAuditLog(log_directory=args.log_dir)
    
    # Check if logs exist
    log_files = list(Path(args.log_dir).glob("audit-*.jsonl"))
    if not log_files:
        print(f"❌ No audit logs found in {args.log_dir}")
        print(f"   Run a script to create genesis inventory first.")
        sys.exit(1)
    
    print(f"📁 Found {len(log_files)} audit log file(s)")
    for log_file in sorted(log_files):
        print(f"   - {log_file.name}")
    print()
    
    # Verify integrity
    integrity = audit.verify_chain_integrity()
    
    print("=" * 60)
    print("📊 AUDIT CHAIN INTEGRITY REPORT")
    print("=" * 60)
    print(f"Total entries:     {integrity['total_entries']}")
    print(f"Valid entries:     {integrity['valid_entries']}")
    print(f"Invalid entries:   {len(integrity['invalid_entries'])}")
    print(f"Integrity:         {integrity['integrity_percentage']:.2f}%")
    print("=" * 60)
    
    if integrity['is_compromised']:
        print("\n⚠️  CHAIN COMPROMISED - Integrity check failed!")
        print(f"\n❌ Invalid entry IDs:")
        for entry_id in integrity['invalid_entries']:
            print(f"   - {entry_id}")
        print("\n⚠️  WARNING: Audit trail has been tampered with or corrupted!")
        print("   Actions:")
        print("   1. Do NOT proceed with operations")
        print("   2. Restore from backup if available")
        print("   3. Investigate compromised entries")
        sys.exit(1)
    else:
        print("\n✅ CHAIN VERIFIED - All entries are cryptographically valid!")
        print(f"   Audit trail is intact and trustworthy.")
        
        # Show statistics
        stats = audit.get_statistics()
        print(f"\n📊 Statistics:")
        print(f"   Log files: {stats['log_files_count']}")
        print(f"   Total size: {stats['total_log_size_mb']:.2f} MB")
        print(f"   Oldest entry: {stats['oldest_entry_timestamp']}")
        print(f"   Newest entry: {stats['newest_entry_timestamp']}")


if __name__ == "__main__":
    main()