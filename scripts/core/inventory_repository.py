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

        Raises:
            ValueError: If db_path is invalid
            RuntimeError: If database initialization fails
        """
        try:
            # Validate and convert path
            if not db_path or not isinstance(db_path, str):
                raise ValueError(f"Invalid db_path: {db_path}")
            
            self.db_path = Path(db_path)
            
            # Create parent directory with error handling
            try:
                self.db_path.parent.mkdir(parents=True, exist_ok=True)
            except (PermissionError, OSError) as e:
                raise RuntimeError(f"Cannot create database directory {self.db_path.parent}: {e}")

            logger.info(f"InventoryRepository initialized: {self.db_path}")
            
            # Initialize database schema
            try:
                self._initialize_database()
            except Exception as e:
                raise RuntimeError(f"Database initialization failed: {e}")
                
        except (ValueError, RuntimeError) as e:
            logger.error(f"Failed to initialize InventoryRepository: {e}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Unexpected error initializing InventoryRepository: {e}", exc_info=True)
            raise RuntimeError(f"Failed to initialize InventoryRepository: {e}")

    @contextmanager
    def _get_connection(self):
        """
        Context manager for database connections.

        Ensures proper connection handling and automatic commit/rollback.

        Yields:
            sqlite3.Connection: Database connection with row factory

        Raises:
            sqlite3.Error: If database connection or operations fail
            RuntimeError: If connection cannot be established
        """
        conn = None
        try:
            # Attempt to connect to database
            try:
                conn = sqlite3.connect(str(self.db_path))
                conn.row_factory = sqlite3.Row  # Access columns by name
            except sqlite3.Error as e:
                raise RuntimeError(f"Cannot connect to database {self.db_path}: {e}")
            
            # Yield connection for use
            yield conn
            
            # Commit if no exceptions occurred
            try:
                conn.commit()
            except sqlite3.Error as e:
                logger.error(f"Failed to commit transaction: {e}", exc_info=True)
                raise
                
        except sqlite3.Error as e:
            # Rollback on database errors
            if conn:
                try:
                    conn.rollback()
                except sqlite3.Error as rollback_error:
                    logger.error(f"Rollback failed: {rollback_error}", exc_info=True)
            logger.error(f"Database error: {e}", exc_info=True)
            raise
        except Exception as e:
            # Rollback on unexpected errors
            if conn:
                try:
                    conn.rollback()
                except sqlite3.Error as rollback_error:
                    logger.error(f"Rollback failed: {rollback_error}", exc_info=True)
            logger.error(f"Unexpected database error: {e}", exc_info=True)
            raise RuntimeError(f"Database operation failed: {e}")
        finally:
            # Always close connection
            if conn:
                try:
                    conn.close()
                except sqlite3.Error as e:
                    logger.warning(f"Error closing database connection: {e}")

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
                    jellyfin_id TEXT,
                    jellyfin_provider_ids TEXT,
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

        Raises:
            TypeError: If root_folder is invalid
            sqlite3.Error: If database operation fails
            RuntimeError: If session creation fails
        """
        try:
            # Input validation
            if not root_folder:
                raise TypeError("root_folder cannot be None or empty")
            
            # Convert to Path if string
            if isinstance(root_folder, str):
                root_folder = Path(root_folder)
            elif not isinstance(root_folder, Path):
                raise TypeError(f"root_folder must be Path or str, got {type(root_folder)}")

            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                try:
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
                    
                    if not session_id:
                        raise RuntimeError("Failed to create scan session: no ID returned")
                    
                    logger.info(f"Created scan session {session_id} for {root_folder}")
                    return session_id
                    
                except sqlite3.IntegrityError as e:
                    logger.error(f"Database integrity error creating scan session: {e}", exc_info=True)
                    raise RuntimeError(f"Failed to create scan session: {e}")
                except sqlite3.Error as e:
                    logger.error(f"Database error creating scan session: {e}", exc_info=True)
                    raise
                    
        except (TypeError, ValueError) as e:
            logger.error(f"Invalid input to create_scan_session: {e}", exc_info=True)
            raise
        except (sqlite3.Error, RuntimeError) as e:
            logger.error(f"Failed to create scan session: {e}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating scan session: {e}", exc_info=True)
            raise RuntimeError(f"Failed to create scan session: {e}")

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
            update_existing: Ignored (kept for API compatibility)

        Raises:
            TypeError: If inputs are invalid
            ValueError: If session_id is invalid or file_records is empty
            sqlite3.Error: If database operation fails
            RuntimeError: If insert operation fails
        """
        try:
            # Input validation
            if not isinstance(session_id, int) or session_id <= 0:
                raise ValueError(f"Invalid session_id: {session_id}")
            
            if not isinstance(file_records, list):
                raise TypeError(f"file_records must be a list, got {type(file_records)}")
            
            if not file_records:
                logger.warning("add_file_records called with empty list")
                return

            import json
            
            # Prepare data with error isolation per record
            records = []
            errors = 0
            
            for record in file_records:
                try:
                    if not isinstance(record, FileRecord):
                        logger.warning(f"Skipping invalid record type: {type(record)}")
                        errors += 1
                        continue
                    
                    records.append((
                        session_id,
                        str(record.absolute_path),
                        record.size_bytes,
                        record.extension,
                        str(record.parent_folder),
                        record.scan_timestamp.isoformat(),
                        record.md5_hash,
                        record.jellyfin_id,
                        json.dumps(record.jellyfin_provider_ids) if record.jellyfin_provider_ids else None
                    ))
                except (AttributeError, TypeError) as e:
                    logger.warning(f"Error preparing file record: {e}")
                    errors += 1
                    continue

            if not records:
                raise RuntimeError("No valid records to insert")

            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                try:
                    # Batch insert (includes Jellyfin fields from Phase 20)
                    cursor.executemany('''
                        INSERT OR REPLACE INTO files
                        (scan_session_id, absolute_path, size_bytes, extension,
                         parent_folder, scan_timestamp, md5_hash, jellyfin_id, jellyfin_provider_ids)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', records)
                    
                    inserted = cursor.rowcount
                    logger.info(f"Inserted {len(records)} file records for session {session_id} ({errors} errors)")
                    
                    if inserted == 0:
                        logger.warning("No rows were inserted")
                        
                except sqlite3.IntegrityError as e:
                    logger.error(f"Database integrity error inserting records: {e}", exc_info=True)
                    raise RuntimeError(f"Failed to insert file records: {e}")
                except sqlite3.Error as e:
                    logger.error(f"Database error inserting records: {e}", exc_info=True)
                    raise
                    
        except (TypeError, ValueError) as e:
            logger.error(f"Invalid input to add_file_records: {e}", exc_info=True)
            raise
        except (sqlite3.Error, RuntimeError) as e:
            logger.error(f"Failed to add file records: {e}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Unexpected error adding file records: {e}", exc_info=True)
            raise RuntimeError(f"Failed to add file records: {e}")

    def get_all_files(
        self,
        session_id: Optional[int] = None
    ) -> List[FileRecord]:
        """
        Get all files from inventory.

        Args:
            session_id: Optional session ID filter

        Returns:
            List of FileRecord objects (empty list if no files found)

        Raises:
            ValueError: If session_id is invalid
            sqlite3.Error: If database query fails
            RuntimeError: If record reconstruction fails
        """
        try:
            import json
            
            # Input validation
            if session_id is not None and (not isinstance(session_id, int) or session_id <= 0):
                raise ValueError(f"Invalid session_id: {session_id}")

            with self._get_connection() as conn:
                cursor = conn.cursor()

                try:
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
                    
                except sqlite3.Error as e:
                    logger.error(f"Database error querying files: {e}", exc_info=True)
                    raise

            # Reconstruct FileRecord objects with error isolation
            file_records = []
            errors = 0
            
            for row in rows:
                try:
                    # Parse JSON provider IDs
                    provider_ids = None
                    if row['jellyfin_provider_ids']:
                        try:
                            provider_ids = json.loads(row['jellyfin_provider_ids'])
                        except json.JSONDecodeError as e:
                            logger.warning(f"Failed to parse provider IDs: {e}")
                    
                    record = FileRecord(
                        absolute_path=Path(row['absolute_path']),
                        size_bytes=row['size_bytes'],
                        extension=row['extension'],
                        parent_folder=Path(row['parent_folder']),
                        scan_timestamp=datetime.fromisoformat(row['scan_timestamp']),
                        md5_hash=row['md5_hash'],
                        jellyfin_id=row['jellyfin_id'],
                        jellyfin_provider_ids=provider_ids
                    )
                    file_records.append(record)
                    
                except (ValueError, TypeError, KeyError) as e:
                    logger.warning(f"Error reconstructing file record: {e}")
                    errors += 1
                    continue

            if errors > 0:
                logger.warning(f"Reconstructed {len(file_records)} records with {errors} errors")

            return file_records
            
        except ValueError as e:
            logger.error(f"Invalid input to get_all_files: {e}", exc_info=True)
            raise
        except sqlite3.Error as e:
            logger.error(f"Failed to get all files: {e}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting all files: {e}", exc_info=True)
            raise RuntimeError(f"Failed to get all files: {e}")

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
