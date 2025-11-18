#!/usr/bin/env python3
"""
Inventory Repository - SQLite Storage for Master File Inventory

Stores and manages the master file inventory in SQLite database.
Implements Point 1 data persistence and Point 2 hierarchy queries.

Architecture Reference: Section 4.1 (File Scanner), Layer 4 (Data Access Layer)
Knowledge Pack: Point 1 (Master List Foundation)
"""

import sqlite3
import logging
from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime
from contextlib import contextmanager

from scripts.core.file_scanner import FileRecord


logger = logging.getLogger(__name__)


class InventoryRepository:
    """
    SQLite repository for master file inventory.

    Responsibilities:
    - Store scanned file records in SQLite database
    - Query files by folder, extension, date range
    - Track scan history
    - Support hierarchical folder queries for Point 2

    Database Schema:
    - files: Master file inventory
    - scan_sessions: Track individual scan operations
    """

    def __init__(self, db_path: str = "data/inventory.db"):
        """
        Initialize inventory repository.

        Args:
            db_path: Path to SQLite database file (created if doesn't exist)
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"InventoryRepository initialized: {self.db_path}")
        self._initialize_database()

    @contextmanager
    def _get_connection(self):
        """
        Context manager for database connections.

        Ensures proper connection handling and automatic commit/rollback.
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row  # Access columns by name
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}", exc_info=True)
            raise
        finally:
            conn.close()

    def _initialize_database(self):
        """Create database schema if it doesn't exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Files table - master inventory
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scan_session_id INTEGER NOT NULL,
                    absolute_path TEXT NOT NULL UNIQUE,
                    size_bytes INTEGER NOT NULL,
                    extension TEXT NOT NULL,
                    parent_folder TEXT NOT NULL,
                    scan_timestamp DATETIME NOT NULL,
                    md5_hash TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (scan_session_id) REFERENCES scan_sessions(id)
                )
            ''')

            # Index for common queries
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_files_parent_folder
                ON files(parent_folder)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_files_extension
                ON files(extension)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_files_scan_session
                ON files(scan_session_id)
            ''')

            # Scan sessions table - track individual scans
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scan_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    root_folder TEXT NOT NULL,
                    scan_start DATETIME NOT NULL,
                    scan_end DATETIME,
                    total_files INTEGER DEFAULT 0,
                    total_size_bytes INTEGER DEFAULT 0,
                    recursive BOOLEAN DEFAULT 1,
                    error_count INTEGER DEFAULT 0,
                    notes TEXT
                )
            ''')

            logger.debug("Database schema initialized")

    def create_scan_session(
        self,
        root_folder: Path,
        recursive: bool = True,
        notes: Optional[str] = None
    ) -> int:
        """
        Create a new scan session.

        Args:
            root_folder: Root folder that was scanned
            recursive: Whether scan was recursive
            notes: Optional notes about the scan

        Returns:
            Scan session ID
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO scan_sessions
                (root_folder, scan_start, recursive, notes)
                VALUES (?, ?, ?, ?)
            ''', (
                str(root_folder),
                datetime.now().isoformat(),
                recursive,
                notes
            ))

            session_id = cursor.lastrowid
            logger.info(f"Created scan session {session_id} for {root_folder}")
            return session_id

    def finalize_scan_session(
        self,
        session_id: int,
        total_files: int,
        total_size_bytes: int,
        error_count: int = 0
    ):
        """
        Finalize a scan session with statistics.

        Args:
            session_id: Scan session ID
            total_files: Total files scanned
            total_size_bytes: Total size in bytes
            error_count: Number of errors encountered
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE scan_sessions
                SET scan_end = ?,
                    total_files = ?,
                    total_size_bytes = ?,
                    error_count = ?
                WHERE id = ?
            ''', (
                datetime.now().isoformat(),
                total_files,
                total_size_bytes,
                error_count,
                session_id
            ))

            logger.info(
                f"Finalized scan session {session_id}: "
                f"{total_files} files, {total_size_bytes} bytes"
            )

    def add_file_records(
        self,
        session_id: int,
        file_records: List[FileRecord],
        update_existing: bool = False
    ):
        """
        Add file records to inventory.

        Uses INSERT OR REPLACE to handle duplicates.

        Args:
            session_id: Scan session ID
            file_records: List of FileRecord objects to insert
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Prepare data for batch insert. The update_existing flag is accepted
            # for API parity with older callers but SQLite's INSERT OR REPLACE
            # already updates existing rows, so no special handling is needed.
            import json
            records = [
                (
                    session_id,
                    str(record.absolute_path),
                    record.size_bytes,
                    record.extension,
                    str(record.parent_folder),
                    record.scan_timestamp.isoformat(),
                    record.md5_hash,
                    record.jellyfin_id,
                    json.dumps(record.jellyfin_provider_ids) if record.jellyfin_provider_ids else None
                )
                for record in file_records
            ]

            # Batch insert (includes Jellyfin fields from Phase 20)
            cursor.executemany('''
                INSERT OR REPLACE INTO files
                (scan_session_id, absolute_path, size_bytes, extension,
                 parent_folder, scan_timestamp, md5_hash, jellyfin_id, jellyfin_provider_ids)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', records)

            logger.info(f"Inserted {len(records)} file records for session {session_id}")

    def get_all_files(
        self,
        session_id: Optional[int] = None
    ) -> List[FileRecord]:
        """
        Get all files from inventory.

        Args:
            session_id: Optional session ID filter

        Returns:
            List of FileRecord objects
        """
        import json

        with self._get_connection() as conn:
            cursor = conn.cursor()

            if session_id:
                cursor.execute('''
                    SELECT absolute_path, size_bytes, extension, parent_folder,
                           scan_timestamp, md5_hash, jellyfin_id, jellyfin_provider_ids
                    FROM files
                    WHERE scan_session_id = ?
                    ORDER BY absolute_path
                ''', (session_id,))
            else:
                cursor.execute('''
                    SELECT absolute_path, size_bytes, extension, parent_folder,
                           scan_timestamp, md5_hash, jellyfin_id, jellyfin_provider_ids
                    FROM files
                    ORDER BY absolute_path
                ''')

            rows = cursor.fetchall()

            return [
                FileRecord(
                    absolute_path=Path(row['absolute_path']),
                    size_bytes=row['size_bytes'],
                    extension=row['extension'],
                    parent_folder=Path(row['parent_folder']),
                    scan_timestamp=datetime.fromisoformat(row['scan_timestamp']),
                    md5_hash=row['md5_hash'],
                    jellyfin_id=row['jellyfin_id'],
                    jellyfin_provider_ids=json.loads(row['jellyfin_provider_ids']) if row['jellyfin_provider_ids'] else None
                )
                for row in rows
            ]

    def get_files_by_folder(
        self,
        folder_path: Path,
        recursive: bool = True
    ) -> List[FileRecord]:
        """
        Get files from a specific folder.

        Args:
            folder_path: Folder path to query
            recursive: If True, include subdirectories

        Returns:
            List of FileRecord objects
        """
        import json

        with self._get_connection() as conn:
            cursor = conn.cursor()

            if recursive:
                # Use LIKE for recursive search
                cursor.execute('''
                    SELECT absolute_path, size_bytes, extension, parent_folder,
                           scan_timestamp, md5_hash, jellyfin_id, jellyfin_provider_ids
                    FROM files
                    WHERE parent_folder LIKE ?
                    ORDER BY absolute_path
                ''', (f"{folder_path}%",))
            else:
                # Exact match for non-recursive
                cursor.execute('''
                    SELECT absolute_path, size_bytes, extension, parent_folder,
                           scan_timestamp, md5_hash, jellyfin_id, jellyfin_provider_ids
                    FROM files
                    WHERE parent_folder = ?
                    ORDER BY absolute_path
                ''', (str(folder_path),))

            rows = cursor.fetchall()

            return [
                FileRecord(
                    absolute_path=Path(row['absolute_path']),
                    size_bytes=row['size_bytes'],
                    extension=row['extension'],
                    parent_folder=Path(row['parent_folder']),
                    scan_timestamp=datetime.fromisoformat(row['scan_timestamp']),
                    md5_hash=row['md5_hash'],
                    jellyfin_id=row['jellyfin_id'],
                    jellyfin_provider_ids=json.loads(row['jellyfin_provider_ids']) if row['jellyfin_provider_ids'] else None
                )
                for row in rows
            ]

    def get_files_by_extension(
        self,
        extensions: List[str]
    ) -> List[FileRecord]:
        """
        Get files with specific extensions.

        Args:
            extensions: List of extensions (e.g., ['.mkv', '.mp4'])

        Returns:
            List of FileRecord objects
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            placeholders = ','.join('?' * len(extensions))
            cursor.execute(f'''
                SELECT absolute_path, size_bytes, extension, parent_folder,
                       scan_timestamp, md5_hash
                FROM files
                WHERE extension IN ({placeholders})
                ORDER BY absolute_path
            ''', extensions)

            rows = cursor.fetchall()

            return [
                FileRecord(
                    absolute_path=Path(row['absolute_path']),
                    size_bytes=row['size_bytes'],
                    extension=row['extension'],
                    parent_folder=Path(row['parent_folder']),
                    scan_timestamp=datetime.fromisoformat(row['scan_timestamp']),
                    md5_hash=row['md5_hash']
                )
                for row in rows
            ]

    def get_folder_statistics(self) -> Dict[str, any]:
        """
        Get aggregated folder statistics for hierarchical overview (Point 2).

        Returns:
            Dictionary mapping folder paths to statistics:
            - file_count: Number of files
            - total_size: Total size in bytes
            - extensions: Dict of extension -> count
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Get folder-level aggregates
            cursor.execute('''
                SELECT
                    parent_folder,
                    COUNT(*) as file_count,
                    SUM(size_bytes) as total_size,
                    extension,
                    COUNT(extension) as ext_count
                FROM files
                GROUP BY parent_folder, extension
                ORDER BY parent_folder
            ''')

            rows = cursor.fetchall()

            # Build hierarchical structure
            from collections import defaultdict
            statistics = defaultdict(lambda: {
                'file_count': 0,
                'total_size': 0,
                'extensions': {}
            })

            for row in rows:
                folder = row['parent_folder']
                ext = row['extension']

                # First time seeing this folder
                if not statistics[folder]['extensions']:
                    statistics[folder]['file_count'] = row['file_count']
                    statistics[folder]['total_size'] = row['total_size']

                statistics[folder]['extensions'][ext] = row['ext_count']

            return dict(statistics)

    def get_scan_history(self, limit: int = 10) -> List[Dict]:
        """
        Get recent scan history.

        Args:
            limit: Maximum number of sessions to return

        Returns:
            List of scan session dictionaries
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('''
                SELECT
                    id,
                    root_folder,
                    scan_start,
                    scan_end,
                    total_files,
                    total_size_bytes,
                    recursive,
                    error_count,
                    notes
                FROM scan_sessions
                ORDER BY scan_start DESC
                LIMIT ?
            ''', (limit,))

            rows = cursor.fetchall()

            return [
                {
                    'id': row['id'],
                    'root_folder': row['root_folder'],
                    'scan_start': row['scan_start'],
                    'scan_end': row['scan_end'],
                    'total_files': row['total_files'],
                    'total_size_bytes': row['total_size_bytes'],
                    'recursive': bool(row['recursive']),
                    'error_count': row['error_count'],
                    'notes': row['notes']
                }
                for row in rows
            ]

    def clear_all_data(self):
        """
        Clear all data from inventory (dangerous operation).

        Use with caution - only for testing or full reset.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM files')
            cursor.execute('DELETE FROM scan_sessions')
            logger.warning("Cleared all inventory data")

    def get_database_statistics(self) -> Dict[str, any]:
        """
        Get overall database statistics.

        Returns:
            Dictionary with database metrics
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Total files
            cursor.execute('SELECT COUNT(*) as count FROM files')
            total_files = cursor.fetchone()['count']

            # Total size
            cursor.execute('SELECT SUM(size_bytes) as total FROM files')
            total_size = cursor.fetchone()['total'] or 0

            # Total scan sessions
            cursor.execute('SELECT COUNT(*) as count FROM scan_sessions')
            total_sessions = cursor.fetchone()['count']

            # File type breakdown
            cursor.execute('''
                SELECT extension, COUNT(*) as count
                FROM files
                GROUP BY extension
                ORDER BY count DESC
                LIMIT 10
            ''')
            top_extensions = {
                row['extension']: row['count']
                for row in cursor.fetchall()
            }

            return {
                'total_files': total_files,
                'total_size_bytes': total_size,
                'total_scan_sessions': total_sessions,
                'top_extensions': top_extensions,
                'database_path': str(self.db_path),
                'database_size_bytes': self.db_path.stat().st_size if self.db_path.exists() else 0
            }


def main():
    """CLI entry point for testing."""
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Inventory Repository CLI")
    parser.add_argument("--db", default="data/inventory.db", help="Database path")
    parser.add_argument("--stats", action="store_true", help="Show database statistics")
    parser.add_argument("--history", action="store_true", help="Show scan history")
    parser.add_argument("--clear", action="store_true", help="Clear all data (DANGEROUS)")

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Create repository
    repo = InventoryRepository(args.db)

    if args.clear:
        response = input("⚠️ This will delete ALL inventory data. Type 'yes' to confirm: ")
        if response.lower() == 'yes':
            repo.clear_all_data()
            print("All data cleared.")
        else:
            print("Cancelled.")
        return 0

    if args.stats:
        stats = repo.get_database_statistics()
        print("\nDatabase Statistics:")
        print(json.dumps(stats, indent=2))

    if args.history:
        history = repo.get_scan_history(limit=20)
        print("\nScan History:")
        print(json.dumps(history, indent=2, default=str))

    if not (args.stats or args.history or args.clear):
        parser.print_help()

    return 0


if __name__ == "__main__":
    exit(main())
