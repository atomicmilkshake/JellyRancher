"""
Immutable Audit Trail System
Blockchain-inspired audit logging with cryptographic hash chaining.

Adapted from production Node.js audit system for Windows/Jellyfin use.

Features:
- SHA-256 hash chaining for tamper detection
- Automatic log rotation (10MB files)
- Chain integrity verification
- JSONL storage format
- Windows path handling

Usage:
    from _common.immutable_audit import ImmutableAuditLog

import logging
logger = logging.getLogger(__name__)
    
    audit = ImmutableAuditLog()
    audit.initialize()  # Verifies chain integrity
    
    # Log events
    audit.log_event("move", {
        "source": "C:\\path\\to\\source.mkv",
        "destination": "C:\\path\\to\\dest.mkv",
        "file_hash": "sha256:abc123..."
    }, actor="organize_movies.py")
    
    # Search logs
    results = audit.search(event_type="move", start_date="2024-01-01")
    
    # Verify integrity
    integrity = audit.verify_chain_integrity()
"""

import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import uuid


class ImmutableAuditLog:
    """
    Immutable audit trail with cryptographic hash chaining.
    
    Each entry is cryptographically linked to the previous entry via SHA-256 hash,
    creating a tamper-evident chain similar to blockchain technology.
    """
    
    def __init__(self, 
                 log_directory: str = "./audit-logs", 
                 max_log_size: int = 10 * 1024 * 1024,
                 log_prefix: str = "audit"):
        """
        Initialize audit log system.
        
        Args:
            log_directory: Directory for audit log files (default: ./audit-logs)
            max_log_size: Maximum size per log file in bytes (default: 10MB)
            log_prefix: Prefix for log filenames (default: "audit")
        """
        self.log_directory = Path(log_directory).resolve()
        self.max_log_size = max_log_size
        self.log_prefix = log_prefix
        self.current_log_file: Optional[Path] = None
        self.last_hash: str = "0" * 64  # Genesis hash (64 zeros)
        self.initialized = False
    
    def initialize(self) -> None:
        """
        Initialize audit system and verify chain integrity.
        
        Creates log directory if needed, loads current log file,
        and verifies integrity of existing chain.
        
        Raises:
            Exception: If chain integrity is severely compromised
        """
        # Create log directory
        self.log_directory.mkdir(parents=True, exist_ok=True)
        
        # Load or create log file
        self._load_current_log_file()
        
        # Verify chain integrity
        integrity = self.verify_chain_integrity()
        
        if integrity['is_compromised']:
            logger.warning(f"[WARN] Audit chain compromised!")
            logger.info(f"   Valid entries: {integrity['valid_entries']}/{integrity['total_entries']}")
            logger.info(f"   Integrity: {integrity['integrity_percentage']:.2f}%")
            logger.info(f"   Invalid entries: {integrity['invalid_entries']}")
            # Don't raise exception here - let startup protocol handle it
        else:
            logger.info(f"[OK] Audit chain verified: {integrity['total_entries']} entries (100% integrity)")
        
        self.initialized = True
        
        # Log system initialization
        self.log_event("system_init", {
            "message": "Audit system initialized",
            "integrity_percentage": integrity['integrity_percentage'],
            "total_entries": integrity['total_entries']
        }, actor="SYSTEM")
    
    def _load_current_log_file(self) -> None:
        """Load most recent log file or create new one."""
        log_files = sorted(self.log_directory.glob(f"{self.log_prefix}-*.jsonl"))
        
        if log_files:
            self.current_log_file = log_files[-1]
            
            # Load last hash from most recent entry
            try:
                with open(self.current_log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    if lines:
                        last_entry = json.loads(lines[-1].strip())
                        self.last_hash = last_entry['hash']
                        logger.info(f"[LOAD] Loaded audit log: {self.current_log_file.name}")
            except Exception as e:
                logger.warning(f"[WARN] Could not load last hash from {self.current_log_file.name}: {e}")
                self.last_hash = "0" * 64
        else:
            self._create_new_log_file()
    
    def _create_new_log_file(self) -> None:
        """Create a new log file with timestamp."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.log_prefix}-{timestamp}.jsonl"
        self.current_log_file = self.log_directory / filename
        logger.info(f"[NEW] Created new audit log: {filename}")
    
    def _calculate_hash(self, entry: Dict[str, Any]) -> str:
        """
        Calculate SHA-256 hash for an audit entry.
        
        Args:
            entry: Audit entry dictionary (must include previous_hash, timestamp, type, details, actor)
        
        Returns:
            SHA-256 hash as hex string
        """
        hash_data = {
            'previous_hash': entry['previous_hash'],
            'timestamp': entry['timestamp'],
            'type': entry['type'],
            'details': entry['details'],
            'actor': entry['actor']
        }
        data_str = json.dumps(hash_data, sort_keys=True)
        return hashlib.sha256(data_str.encode('utf-8')).hexdigest()
    
    def log_event(self, 
                  event_type: str, 
                  details: Dict[str, Any], 
                  actor: str = "SYSTEM") -> str:
        """
        Log an audit event with cryptographic chaining.
        
        Args:
            event_type: Type of event (e.g., "move", "rename", "genesis_inventory")
            details: Event details dictionary (paths, hashes, changes, etc.)
            actor: Who/what performed the action (script name or "SYSTEM")
        
        Returns:
            UUID of the logged transaction
        
        Example:
            audit.log_event("move", {
                "source": "C:\\Movies\\old.mkv",
                "destination": "C:\\Movies\\Movie (2023)\\Movie (2023).mkv",
                "file_hash_before": "sha256:abc123...",
                "file_hash_after": "sha256:abc123...",
                "file_size": 1234567890
            }, actor="organize_movies.py")
        """
        if not self.initialized:
            self.initialize()
        
        entry = {
            'id': str(uuid.uuid4()),
            'timestamp': datetime.now().isoformat(),
            'type': event_type,
            'details': details,
            'actor': actor,
            'previous_hash': self.last_hash,
            'hash': None  # Calculate next
        }
        
        # Calculate hash for this entry
        entry['hash'] = self._calculate_hash(entry)
        
        # Check rotation before writing
        self._check_rotation()
        
        # Append to log file
        with open(self.current_log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry) + '\n')
        
        # Update last hash for next entry
        self.last_hash = entry['hash']
        
        return entry['id']
    
    def _check_rotation(self) -> None:
        """Rotate log file if size exceeds threshold."""
        if self.current_log_file and self.current_log_file.exists():
            if self.current_log_file.stat().st_size > self.max_log_size:
                logger.info(f"🔄 Rotating log file (size: {self.current_log_file.stat().st_size / 1024 / 1024:.2f} MB)")
                self._create_new_log_file()
    
    def verify_chain_integrity(self) -> Dict[str, Any]:
        """
        Verify cryptographic integrity of entire audit chain.
        
        Walks through all log files chronologically and verifies that each
        entry's hash matches the calculated hash from its contents.
        
        Returns:
            Dictionary with:
                - total_entries: Total number of entries
                - valid_entries: Number of valid entries
                - invalid_entries: List of invalid entry IDs
                - integrity_percentage: Percentage of valid entries
                - is_compromised: True if any entries are invalid
        """
        log_files = sorted(self.log_directory.glob(f"{self.log_prefix}-*.jsonl"))
        
        total_entries = 0
        valid_entries = 0
        invalid_entries = []
        
        for log_file in log_files:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if not line.strip():
                        continue
                    
                    total_entries += 1
                    entry = json.loads(line.strip())
                    
                    # Recalculate hash and verify
                    expected_hash = self._calculate_hash(entry)
                    
                    if expected_hash == entry['hash']:
                        valid_entries += 1
                    else:
                        invalid_entries.append(entry['id'])
                        logger.warning(f"[WARN] Hash mismatch in entry {entry['id']} (file: {log_file.name})")
        
        integrity_pct = (valid_entries / total_entries * 100) if total_entries > 0 else 100.0
        
        return {
            'total_entries': total_entries,
            'valid_entries': valid_entries,
            'invalid_entries': invalid_entries,
            'integrity_percentage': integrity_pct,
            'is_compromised': integrity_pct < 100.0
        }
    
    def search(self, 
               event_type: Optional[str] = None, 
               actor: Optional[str] = None,
               start_date: Optional[str] = None,
               end_date: Optional[str] = None,
               details_filter: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Search audit logs with filters.
        
        Args:
            event_type: Filter by event type (e.g., "move")
            actor: Filter by actor (e.g., "organize_movies.py")
            start_date: Filter by start date (ISO format)
            end_date: Filter by end date (ISO format)
            details_filter: Filter by details fields (e.g., {"source": "C:\\Movies\\..."})
        
        Returns:
            List of matching audit entries (most recent first)
        """
        results = []
        log_files = sorted(self.log_directory.glob(f"{self.log_prefix}-*.jsonl"), 
                          reverse=True)  # Most recent first
        
        for log_file in log_files:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if not line.strip():
                        continue
                    
                    entry = json.loads(line.strip())
                    
                    # Apply filters
                    if event_type and entry['type'] != event_type:
                        continue
                    if actor and entry['actor'] != actor:
                        continue
                    if start_date and entry['timestamp'] < start_date:
                        continue
                    if end_date and entry['timestamp'] > end_date:
                        continue
                    
                    # Custom details filtering
                    if details_filter:
                        match = True
                        for key, value in details_filter.items():
                            if key not in entry['details'] or entry['details'][key] != value:
                                match = False
                                break
                        if not match:
                            continue
                    
                    results.append(entry)
        
        return results
    
    def get_genesis_inventory(self) -> Optional[Dict[str, Any]]:
        """
        Retrieve the genesis inventory transaction.
        
        Returns:
            Genesis transaction entry, or None if not found
        """
        results = self.search(event_type="genesis_inventory")
        return results[0] if results else None
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get audit system statistics.
        
        Returns:
            Dictionary with:
                - total_entries: Total audit entries
                - integrity_percentage: Chain integrity percentage
                - is_compromised: True if chain is compromised
                - log_files_count: Number of log files
                - oldest_entry_timestamp: Timestamp of oldest entry
                - newest_entry_timestamp: Timestamp of newest entry
                - total_log_size_mb: Total size of all log files in MB
        """
        log_files = sorted(self.log_directory.glob(f"{self.log_prefix}-*.jsonl"))
        
        total_size = sum(f.stat().st_size for f in log_files)
        all_logs = self.search()  # Get all logs
        integrity = self.verify_chain_integrity()
        
        return {
            'total_entries': len(all_logs),
            'integrity_percentage': integrity['integrity_percentage'],
            'is_compromised': integrity['is_compromised'],
            'log_files_count': len(log_files),
            'oldest_entry_timestamp': all_logs[-1]['timestamp'] if all_logs else None,
            'newest_entry_timestamp': all_logs[0]['timestamp'] if all_logs else None,
            'total_log_size_mb': total_size / 1024 / 1024
        }


# Standalone CLI usage
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        logger.info("Usage: python immutable_audit.py <command>")
        logger.info("Commands:")
        logger.info("  init           - Initialize audit system")
        logger.info("  verify         - Verify chain integrity")
        logger.info("  stats          - Show statistics")
        logger.info("  search [type]  - Search audit logs")
        sys.exit(1)
    
    command = sys.argv[1]
    audit = ImmutableAuditLog()
    
    if command == "init":
        audit.initialize()
        logger.info("✅ Audit system initialized")
    
    elif command == "verify":
        audit.initialize()
        integrity = audit.verify_chain_integrity()
        logger.info(f"\n[REPORT] Chain Integrity Report:")
        logger.info(f"   Total entries: {integrity['total_entries']}")
        logger.info(f"   Valid entries: {integrity['valid_entries']}")
        logger.info(f"   Integrity: {integrity['integrity_percentage']:.2f}%")
        if integrity['is_compromised']:
            logger.info(f"   [WARN] COMPROMISED - Invalid entries: {integrity['invalid_entries']}")
        else:
            logger.info(f"   [OK] VERIFIED - Chain is intact")
    
    elif command == "stats":
        audit.initialize()
        stats = audit.get_statistics()
        logger.info(f"\n📊 Audit Statistics:")
        logger.info(f"   Total entries: {stats['total_entries']}")
        logger.info(f"   Log files: {stats['log_files_count']}")
        logger.info(f"   Total size: {stats['total_log_size_mb']:.2f} MB")
        logger.info(f"   Oldest entry: {stats['oldest_entry_timestamp']}")
        logger.info(f"   Newest entry: {stats['newest_entry_timestamp']}")
        logger.info(f"   Integrity: {stats['integrity_percentage']:.2f}%")
    
    elif command == "search":
        audit.initialize()
        event_type = sys.argv[2] if len(sys.argv) > 2 else None
        results = audit.search(event_type=event_type)
        logger.info(f"\n🔍 Search Results: {len(results)} entries")
        for entry in results[:10]:  # Show first 10
            logger.info(f"   [{entry['timestamp']}] {entry['type']} by {entry['actor']}")
        if len(results) > 10:
            logger.info(f"   ... and {len(results) - 10} more")
    
    else:
        logger.error(f"❌ Unknown command: {command}")
        sys.exit(1)