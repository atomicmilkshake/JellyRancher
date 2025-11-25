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

import logging
logger = logging.getLogger(__name__)

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
    
    logger.info("🔍 Verifying Audit Chain Integrity...\n")
    
    # Initialize audit system
    audit = ImmutableAuditLog(log_directory=args.log_dir)
    
    # Check if logs exist
    log_files = list(Path(args.log_dir).glob("audit-*.jsonl"))
    if not log_files:
        logger.error(f"❌ No audit logs found in {args.log_dir}")
        logger.info(f"   Run a script to create genesis inventory first.")
        sys.exit(1)
    
    logger.info(f"📁 Found {len(log_files)} audit log file(s)")
    for log_file in sorted(log_files):
        logger.info(f"   - {log_file.name}")
    logger.info()
    
    # Verify integrity
    integrity = audit.verify_chain_integrity()
    
    logger.info("=" * 60)
    logger.info("📊 AUDIT CHAIN INTEGRITY REPORT")
    logger.info("=" * 60)
    logger.info(f"Total entries:     {integrity['total_entries']}")
    logger.info(f"Valid entries:     {integrity['valid_entries']}")
    logger.info(f"Invalid entries:   {len(integrity['invalid_entries'])}")
    logger.info(f"Integrity:         {integrity['integrity_percentage']:.2f}%")
    logger.info("=" * 60)
    
    if integrity['is_compromised']:
        logger.info("\n⚠️  CHAIN COMPROMISED - Integrity check failed!")
        logger.info(f"\n❌ Invalid entry IDs:")
        for entry_id in integrity['invalid_entries']:
            logger.info(f"   - {entry_id}")
        logger.info("\n⚠️  WARNING: Audit trail has been tampered with or corrupted!")
        logger.info("   Actions:")
        logger.info("   1. Do NOT proceed with operations")
        logger.info("   2. Restore from backup if available")
        logger.info("   3. Investigate compromised entries")
        sys.exit(1)
    else:
        logger.info("\n✅ CHAIN VERIFIED - All entries are cryptographically valid!")
        logger.info(f"   Audit trail is intact and trustworthy.")
        
        # Show statistics
        stats = audit.get_statistics()
        logger.info(f"\n📊 Statistics:")
        logger.info(f"   Log files: {stats['log_files_count']}")
        logger.info(f"   Total size: {stats['total_log_size_mb']:.2f} MB")
        logger.info(f"   Oldest entry: {stats['oldest_entry_timestamp']}")
        logger.info(f"   Newest entry: {stats['newest_entry_timestamp']}")


if __name__ == "__main__":
    main()