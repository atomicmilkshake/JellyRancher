"""
Transaction Manager - SQLite-based file operation tracking with rollback capability.

This module provides ACID-compliant transaction logging for file operations,
enabling safe execution and rollback of media library reorganization.

Architecture:
    - TransactionManager: Main orchestration class with context manager support
    - FileHasher: MD5 calculation and verification utility
    - Models: Type-safe data classes for operations and results

Usage:
    from scripts.utils.transaction_manager import TransactionManager, Operation

    with TransactionManager() as tm:
        batch_id = tm.begin_batch("movie_reorganization")

        op = Operation(
            operation_type='move',
            source_path='/old/Movie.mkv',
            destination_path='/new/Movie (2020).mkv'
        )

        tx_id = tm.log_operation(op)

        # Perform file operation
        shutil.move(op.source_path, op.destination_path)

        # Verify and complete
        tm.complete_operation(tx_id, FileHasher.calculate_md5(op.destination_path))

    # Rollback if needed
    tm.rollback_batch(batch_id)

Best Practices:
    - Uses context manager for automatic resource cleanup
    - ACID compliance via SQLite transactions
    - Type hints throughout for IDE support
    - Comprehensive error handling with specific exceptions
    - Logging for audit trail
    - Single Responsibility Principle (separation of concerns)
"""

import hashlib
import json
import logging
import shutil
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from enum import Enum


# ============================================================================
# ENUMS
# ============================================================================

class OperationType(Enum):
    """Types of file operations that can be logged."""
    MOVE = "move"
    RENAME = "rename"
    NFO_CREATE = "nfo_create"
    COPY = "copy"
    DELETE = "delete"


class TransactionStatus(Enum):
    """Status of a transaction operation."""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class Operation:
    """
    Represents a file operation to be logged.

    Attributes:
        operation_type: Type of operation (move, rename, etc.)
        source_path: Original file path
        destination_path: Target file path (None for delete operations)
        metadata: Optional metadata (e.g., NFO content, original permissions)
    """
    operation_type: OperationType
    source_path: str
    destination_path: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, handling enum serialization."""
        return {
            'operation_type': self.operation_type.value,
            'source_path': self.source_path,
            'destination_path': self.destination_path,
            'metadata': json.dumps(self.metadata) if self.metadata else None
        }


@dataclass
class TransactionRecord:
    """
    Complete record of a logged transaction.

    Attributes:
        id: Database primary key
        transaction_batch_id: Batch identifier for grouping operations
        timestamp: When operation was logged
        operation_type: Type of operation
        source_path: Original file path
        destination_path: Target file path
        source_md5: MD5 hash of source file before operation
        destination_md5: MD5 hash of destination file after operation
        status: Current status of transaction
        error_message: Error details if failed
        metadata: Additional operation-specific data
    """
    id: int
    transaction_batch_id: str
    timestamp: str
    operation_type: str
    source_path: str
    destination_path: Optional[str]
    source_md5: str
    destination_md5: Optional[str]
    status: str
    error_message: Optional[str]
    metadata: Optional[str]


@dataclass
class BatchStatus:
    """
    Status summary for a transaction batch.

    Attributes:
        batch_id: Batch identifier
        total_operations: Total number of operations in batch
        pending: Number of pending operations
        completed: Number of completed operations
        failed: Number of failed operations
        rolled_back: Number of rolled back operations
    """
    batch_id: str
    total_operations: int
    pending: int
    completed: int
    failed: int
    rolled_back: int


@dataclass
class RollbackResult:
    """
    Result of a rollback operation.

    Attributes:
        batch_id: Batch identifier that was rolled back
        total_operations: Total operations in batch
        successful_rollbacks: Number of successfully rolled back operations
        failed_rollbacks: Number of failed rollback attempts
        errors: List of error messages encountered
    """
    batch_id: str
    total_operations: int
    successful_rollbacks: int
    failed_rollbacks: int
    errors: List[str]


# ============================================================================
# FILE HASHER UTILITY
# ============================================================================

class FileHasher:
    """
    Utility class for MD5 hash calculation and verification.

    Note: MD5 is used for file integrity verification, not cryptographic security.
    It's faster than SHA-256 for large video files and sufficient for detecting
    file corruption or modification.
    """

    @staticmethod
    def calculate_md5(file_path: str | Path, chunk_size: int = 8192) -> str:
        """
        Calculate MD5 hash of a file.

        Args:
            file_path: Path to file
            chunk_size: Size of chunks to read (8KB default for memory efficiency)

        Returns:
            Hexadecimal MD5 hash string

        Raises:
            FileNotFoundError: If file doesn't exist
            PermissionError: If file can't be read
            RuntimeError: If MD5 calculation fails
        """
        try:
            file_path = Path(file_path)

            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            if not file_path.is_file():
                raise ValueError(f"Not a file: {file_path}")

            hasher = hashlib.md5()

            with open(file_path, 'rb') as f:
                while chunk := f.read(chunk_size):
                    hasher.update(chunk)

            return hasher.hexdigest()
        except FileNotFoundError:
            raise
        except PermissionError:
            raise
        except ValueError:
            raise
        except OSError as e:
            raise PermissionError(f"Cannot read file {file_path}: {e}")
        except Exception as e:
            raise RuntimeError(f"MD5 calculation failed for {file_path}: {e}")

    @staticmethod
    def verify_md5(file_path: str | Path, expected_md5: str) -> bool:
        """
        Verify file matches expected MD5 hash.

        Args:
            file_path: Path to file
            expected_md5: Expected MD5 hash

        Returns:
            True if hash matches, False otherwise
        """
        try:
            actual_md5 = FileHasher.calculate_md5(file_path)
            matches = actual_md5 == expected_md5
            if not matches:
                # Log hash mismatch for debugging
                logging.getLogger(__name__).warning(
                    f"MD5 mismatch for {file_path}: expected {expected_md5}, got {actual_md5}"
                )
            return matches
        except (FileNotFoundError, PermissionError, ValueError, RuntimeError):
            return False


# ============================================================================
# TRANSACTION MANAGER
# ============================================================================

class TransactionManager:
    """
    SQLite-based transaction manager for file operations.

    Provides ACID-compliant logging of file operations with rollback capability.
    Uses context manager protocol for automatic resource management.

    Attributes:
        db_path: Path to SQLite database file
        logger: Logger instance for audit trail

    Example:
        with TransactionManager() as tm:
            batch_id = tm.begin_batch("reorganization")
            op = Operation(OperationType.MOVE, "/old/file.mkv", "/new/file.mkv")
            tx_id = tm.log_operation(op)
            # ... perform operation ...
            tm.complete_operation(tx_id, dest_md5)
    """

    DEFAULT_DB_PATH = Path("data/transactions.db")

    def __init__(self,
                 db_path: Optional[str | Path] = None,
                 logger: Optional[logging.Logger] = None):
        """
        Initialize TransactionManager.

        Args:
            db_path: Path to SQLite database (default: data/transactions.db)
            logger: Logger instance (creates default if None)
        """
        try:
            self.db_path = Path(db_path) if db_path else self.DEFAULT_DB_PATH
            self.logger = logger or self._setup_default_logger()
            self.connection: Optional[sqlite3.Connection] = None

            # Ensure database directory exists
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

            # Initialize database schema
            self._initialize_database()

            self.logger.info(f"TransactionManager initialized with database: {self.db_path}")
        except Exception as e:
            if hasattr(self, 'logger') and self.logger:
                self.logger.error(f"Failed to initialize TransactionManager: {e}", exc_info=True)
            else:
                print(f"Failed to initialize TransactionManager: {e}")
            raise RuntimeError(f"TransactionManager initialization failed: {e}")

    def _setup_default_logger(self) -> logging.Logger:
        """Create default logger if none provided."""
        logger = logging.getLogger('TransactionManager')
        logger.setLevel(logging.INFO)

        # Console handler
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger

    def _initialize_database(self) -> None:
        """Create database schema if it doesn't exist."""
        try:
            conn = sqlite3.connect(self.db_path)
            try:
                cursor = conn.cursor()

                # Create transactions table per architecture spec
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS transactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        transaction_batch_id TEXT NOT NULL,
                        timestamp DATETIME NOT NULL,
                        operation_type TEXT NOT NULL,
                        source_path TEXT NOT NULL,
                        destination_path TEXT,
                        source_md5 TEXT NOT NULL,
                        destination_md5 TEXT,
                        status TEXT NOT NULL,
                        error_message TEXT,
                        metadata TEXT
                    )
                """)

                # Create index for batch queries
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_batch_id
                    ON transactions(transaction_batch_id)
                """)

                # Create index for status queries
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_status
                    ON transactions(status)
                """)

                conn.commit()
                self.logger.info("Database schema initialized")
            except sqlite3.Error as e:
                self.logger.error(f"Database initialization failed: {e}", exc_info=True)
                raise RuntimeError(f"Failed to initialize database schema: {e}")
            finally:
                conn.close()
        except Exception as e:
            self.logger.error(f"Unexpected error during database initialization: {e}", exc_info=True)
            raise RuntimeError(f"Database initialization failed: {e}")

    def __enter__(self) -> 'TransactionManager':
        """Context manager entry - establish database connection."""
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row
            return self
        except sqlite3.Error as e:
            self.logger.error(f"Failed to establish database connection: {e}", exc_info=True)
            raise RuntimeError(f"Database connection failed: {e}")

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - close database connection."""
        try:
            if self.connection:
                self.connection.close()
                self.connection = None
        except Exception as e:
            self.logger.error(f"Error closing database connection: {e}", exc_info=True)

    @contextmanager
    def _get_connection(self):
        """
        Internal context manager for database connections.
        Uses existing connection if in context manager, otherwise creates temporary one.
        """
        if self.connection:
            try:
                yield self.connection
            except Exception as e:
                self.logger.error(f"Database operation error: {e}", exc_info=True)
                raise
        else:
            conn = None
            try:
                conn = sqlite3.connect(self.db_path)
                conn.row_factory = sqlite3.Row
                yield conn
            except sqlite3.Error as e:
                self.logger.error(f"Database connection error: {e}", exc_info=True)
                raise RuntimeError(f"Database operation failed: {e}")
            except Exception as e:
                self.logger.error(f"Unexpected database error: {e}", exc_info=True)
                raise RuntimeError(f"Database operation failed: {e}")
            finally:
                if conn:
                    try:
                        conn.close()
                    except Exception as e:
                        self.logger.error(f"Error closing temporary database connection: {e}")

    def begin_batch(self, batch_id: Optional[str] = None) -> str:
        """
        Begin a new transaction batch.

        Args:
            batch_id: Optional batch identifier (auto-generated if None)

        Returns:
            Batch identifier string
        """
        try:
            if not batch_id:
                batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            self.logger.info(f"Beginning transaction batch: {batch_id}")
            return batch_id
        except Exception as e:
            self.logger.error(f"Failed to begin batch: {e}", exc_info=True)
            raise RuntimeError("Failed to begin transaction batch") from e

    def log_operation(self,
                      operation: Operation,
                      batch_id: str) -> int:
        """
        Log a file operation before execution.

        This calculates the source MD5 and creates a pending transaction record.
        Call complete_operation() or fail_operation() after executing the operation.

        Args:
            operation: Operation to log
            batch_id: Batch identifier

        Returns:
            Transaction ID (database primary key)

        Raises:
            FileNotFoundError: If source file doesn't exist
            PermissionError: If source file can't be read
            RuntimeError: If logging fails
        """
        try:
            # Calculate source MD5
            source_md5 = FileHasher.calculate_md5(operation.source_path)

            with self._get_connection() as conn:
                cursor = conn.cursor()

                op_dict = operation.to_dict()

                cursor.execute("""
                    INSERT INTO transactions (
                        transaction_batch_id,
                        timestamp,
                        operation_type,
                        source_path,
                        destination_path,
                        source_md5,
                        destination_md5,
                        status,
                        error_message,
                        metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    batch_id,
                    datetime.now().isoformat(),
                    op_dict['operation_type'],
                    op_dict['source_path'],
                    op_dict['destination_path'],
                    source_md5,
                    None,  # destination_md5 filled in complete_operation
                    TransactionStatus.PENDING.value,
                    None,
                    op_dict['metadata']
                ))

                conn.commit()
                transaction_id = cursor.lastrowid

            self.logger.info(f"Logged operation {transaction_id}: {operation.operation_type.value} "
                            f"{operation.source_path} -> {operation.destination_path}")

            return transaction_id
        except (FileNotFoundError, PermissionError, ValueError):
            # Re-raise file-related errors
            raise
        except sqlite3.Error as e:
            self.logger.error(f"Database error logging operation: {e}", exc_info=True)
            raise RuntimeError(f"Failed to log operation: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error logging operation: {e}", exc_info=True)
            raise RuntimeError(f"Operation logging failed: {e}")

    def complete_operation(self,
                          transaction_id: int,
                          destination_md5: str) -> None:
        """
        Mark operation as completed with destination MD5 verification.

        Args:
            transaction_id: Transaction ID from log_operation()
            destination_md5: MD5 hash of destination file after operation
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    UPDATE transactions
                    SET status = ?,
                        destination_md5 = ?
                    WHERE id = ?
                """, (
                    TransactionStatus.COMPLETED.value,
                    destination_md5,
                    transaction_id
                ))

                conn.commit()

            self.logger.info(f"Completed operation {transaction_id}")
        except sqlite3.Error as e:
            self.logger.error(f"Failed to complete operation {transaction_id}: {e}", exc_info=True)
            raise RuntimeError(f"Database error completing operation {transaction_id}") from e
        except Exception as e:
            self.logger.error(f"Unexpected error completing operation {transaction_id}: {e}", exc_info=True)
            raise RuntimeError(f"Unexpected error completing operation {transaction_id}") from e

    def fail_operation(self,
                      transaction_id: int,
                      error_message: str) -> None:
        """
        Mark operation as failed with error details.

        Args:
            transaction_id: Transaction ID from log_operation()
            error_message: Error description
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    UPDATE transactions
                    SET status = ?,
                        error_message = ?
                    WHERE id = ?
                """, (
                    TransactionStatus.FAILED.value,
                    error_message,
                    transaction_id
                ))

                conn.commit()

            self.logger.error(f"Failed operation {transaction_id}: {error_message}")
        except sqlite3.Error as e:
            self.logger.error(f"Failed to mark operation {transaction_id} as failed: {e}", exc_info=True)
            raise RuntimeError(f"Database error marking operation {transaction_id} as failed") from e
        except Exception as e:
            self.logger.error(f"Unexpected error marking operation {transaction_id} as failed: {e}", exc_info=True)
            raise RuntimeError(f"Unexpected error marking operation {transaction_id} as failed") from e

    def get_batch_status(self, batch_id: str) -> BatchStatus:
        """
        Get status summary for a transaction batch.

        Args:
            batch_id: Batch identifier

        Returns:
            BatchStatus with operation counts
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Get counts by status
                cursor.execute("""
                    SELECT status, COUNT(*) as count
                    FROM transactions
                    WHERE transaction_batch_id = ?
                    GROUP BY status
                """, (batch_id,))

                status_counts = {row['status']: row['count'] for row in cursor.fetchall()}

                total = sum(status_counts.values())

                return BatchStatus(
                    batch_id=batch_id,
                    total_operations=total,
                    pending=status_counts.get(TransactionStatus.PENDING.value, 0),
                    completed=status_counts.get(TransactionStatus.COMPLETED.value, 0),
                    failed=status_counts.get(TransactionStatus.FAILED.value, 0),
                    rolled_back=status_counts.get(TransactionStatus.ROLLED_BACK.value, 0)
                )
        except sqlite3.Error as e:
            self.logger.error(f"Failed to get batch status for {batch_id}: {e}", exc_info=True)
            # Return safe default
            return BatchStatus(
                batch_id=batch_id,
                total_operations=0,
                pending=0,
                completed=0,
                failed=0,
                rolled_back=0
            )
        except Exception as e:
            self.logger.error(f"Unexpected error getting batch status for {batch_id}: {e}", exc_info=True)
            # Return safe default
            return BatchStatus(
                batch_id=batch_id,
                total_operations=0,
                pending=0,
                completed=0,
                failed=0,
                rolled_back=0
            )

    def rollback_batch(self,
                       batch_id: str,
                       dry_run: bool = False) -> RollbackResult:
        """
        Rollback all completed operations in a batch (reverse chronological order).

        Per knowledge-pack spec: Don't recalculate MD5 on rollback, just reverse
        the file operation.

        Args:
            batch_id: Batch identifier to rollback
            dry_run: If True, only simulate rollback without executing

        Returns:
            RollbackResult with success/failure counts
        """
        try:
            self.logger.info(f"{'[DRY RUN] ' if dry_run else ''}Rolling back batch: {batch_id}")

            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Get all completed operations in reverse chronological order
                cursor.execute("""
                    SELECT * FROM transactions
                    WHERE transaction_batch_id = ?
                    AND status = ?
                    ORDER BY id DESC
                """, (batch_id, TransactionStatus.COMPLETED.value))

                operations = [TransactionRecord(**dict(row)) for row in cursor.fetchall()]

            successful_rollbacks = 0
            failed_rollbacks = 0
            errors = []

            for op in operations:
                try:
                    if dry_run:
                        self.logger.info(f"[DRY RUN] Would rollback: {op.destination_path} -> {op.source_path}")
                        successful_rollbacks += 1
                    else:
                        # Reverse the operation (move destination back to source)
                        dest_path = Path(op.destination_path)
                        source_path = Path(op.source_path)

                        if not dest_path.exists():
                            raise FileNotFoundError(f"Destination file missing: {dest_path}")

                        # Ensure source directory exists
                        source_path.parent.mkdir(parents=True, exist_ok=True)

                        # Perform reverse operation
                        shutil.move(str(dest_path), str(source_path))

                        # Update transaction status
                        with self._get_connection() as conn:
                            cursor = conn.cursor()
                            cursor.execute("""
                                UPDATE transactions
                                SET status = ?
                                WHERE id = ?
                            """, (TransactionStatus.ROLLED_BACK.value, op.id))
                            conn.commit()

                        successful_rollbacks += 1
                        self.logger.info(f"Rolled back operation {op.id}: {op.destination_path} -> {op.source_path}")

                except Exception as e:
                    error_msg = f"Failed to rollback operation {op.id}: {str(e)}"
                    errors.append(error_msg)
                    failed_rollbacks += 1
                    self.logger.error(error_msg)

            result = RollbackResult(
                batch_id=batch_id,
                total_operations=len(operations),
                successful_rollbacks=successful_rollbacks,
                failed_rollbacks=failed_rollbacks,
                errors=errors
            )

            self.logger.info(f"Rollback complete: {successful_rollbacks}/{len(operations)} successful")

            return result
        except sqlite3.Error as e:
            self.logger.error(f"Database error during rollback of batch {batch_id}: {e}", exc_info=True)
            raise RuntimeError(f"Database error during rollback of batch {batch_id}") from e
        except Exception as e:
            self.logger.error(f"Unexpected error during rollback of batch {batch_id}: {e}", exc_info=True)
            raise RuntimeError(f"Unexpected error during rollback of batch {batch_id}") from e

    def get_batch_operations(self, batch_id: str) -> List[TransactionRecord]:
        """
        Get all operations for a batch.

        Args:
            batch_id: Batch identifier

        Returns:
            List of TransactionRecord objects
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT * FROM transactions
                    WHERE transaction_batch_id = ?
                    ORDER BY id ASC
                """, (batch_id,))

                return [TransactionRecord(**dict(row)) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            self.logger.error(f"Failed to get batch operations for {batch_id}: {e}", exc_info=True)
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error getting batch operations for {batch_id}: {e}", exc_info=True)
            return []


# ============================================================================
# STANDALONE CLI (for testing/debugging)
# ============================================================================

if __name__ == "__main__":
    import sys
    import argparse

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    parser = argparse.ArgumentParser(description="Transaction Manager CLI")
    parser.add_argument("command", choices=["status", "rollback", "list"],
                       help="Command to execute")
    parser.add_argument("--batch-id", help="Batch ID for status/rollback commands")
    parser.add_argument("--dry-run", action="store_true", help="Dry run mode for rollback")

    args = parser.parse_args()

    tm = TransactionManager()

    if args.command == "status":
        if not args.batch_id:
            print("Error: --batch-id required for status command")
            sys.exit(1)

        status = tm.get_batch_status(args.batch_id)
        print(f"\nBatch Status: {status.batch_id}")
        print(f"  Total: {status.total_operations}")
        print(f"  Completed: {status.completed}")
        print(f"  Pending: {status.pending}")
        print(f"  Failed: {status.failed}")
        print(f"  Rolled Back: {status.rolled_back}")

    elif args.command == "rollback":
        if not args.batch_id:
            print("Error: --batch-id required for rollback command")
            sys.exit(1)

        result = tm.rollback_batch(args.batch_id, dry_run=args.dry_run)
        print(f"\nRollback Result: {result.batch_id}")
        print(f"  Total: {result.total_operations}")
        print(f"  Successful: {result.successful_rollbacks}")
        print(f"  Failed: {result.failed_rollbacks}")
        if result.errors:
            print("\nErrors:")
            for error in result.errors:
                print(f"  - {error}")

    elif args.command == "list":
        # List all batches
        with tm._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT transaction_batch_id
                FROM transactions
                ORDER BY transaction_batch_id DESC
            """)
            batches = [row[0] for row in cursor.fetchall()]

        print("\nAvailable Batches:")
        for batch in batches:
            status = tm.get_batch_status(batch)
            print(f"  {batch}: {status.total_operations} operations "
                  f"({status.completed} completed, {status.failed} failed, "
                  f"{status.rolled_back} rolled back)")
