"""
Unit tests for TransactionManager.

Tests cover:
- Database initialization
- Operation logging
- MD5 calculation and verification
- Transaction completion and failure
- Batch status tracking
- Rollback functionality
- Context manager behavior
- Error handling
"""

import hashlib
import os
import shutil
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.utils.transaction_manager import (
    TransactionManager,
    FileHasher,
    Operation,
    OperationType,
    TransactionStatus,
    BatchStatus,
    RollbackResult
)


class TestFileHasher(unittest.TestCase):
    """Test cases for FileHasher utility class."""

    def setUp(self):
        """Create temporary directory and test files."""
        self.test_dir = tempfile.mkdtemp()
        self.test_file = Path(self.test_dir) / "test.txt"
        self.test_content = b"Hello, World! This is test content."
        self.test_file.write_bytes(self.test_content)

        # Calculate expected MD5
        self.expected_md5 = hashlib.md5(self.test_content).hexdigest()

    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.test_dir)

    def test_calculate_md5(self):
        """Test MD5 calculation returns correct hash."""
        md5 = FileHasher.calculate_md5(self.test_file)
        self.assertEqual(md5, self.expected_md5)

    def test_calculate_md5_nonexistent_file(self):
        """Test MD5 calculation raises FileNotFoundError for missing file."""
        with self.assertRaises(FileNotFoundError):
            FileHasher.calculate_md5(Path(self.test_dir) / "nonexistent.txt")

    def test_calculate_md5_directory(self):
        """Test MD5 calculation raises ValueError for directory."""
        with self.assertRaises(ValueError):
            FileHasher.calculate_md5(self.test_dir)

    def test_verify_md5_success(self):
        """Test MD5 verification succeeds with correct hash."""
        result = FileHasher.verify_md5(self.test_file, self.expected_md5)
        self.assertTrue(result)

    def test_verify_md5_failure(self):
        """Test MD5 verification fails with incorrect hash."""
        result = FileHasher.verify_md5(self.test_file, "wrong_hash")
        self.assertFalse(result)

    def test_verify_md5_missing_file(self):
        """Test MD5 verification returns False for missing file."""
        result = FileHasher.verify_md5(Path(self.test_dir) / "missing.txt", "any_hash")
        self.assertFalse(result)


class TestTransactionManager(unittest.TestCase):
    """Test cases for TransactionManager class."""

    def setUp(self):
        """Create temporary directory and database."""
        self.test_dir = tempfile.mkdtemp()
        self.db_path = Path(self.test_dir) / "test_transactions.db"
        self.tm = TransactionManager(db_path=self.db_path)

        # Create test files
        self.source_file = Path(self.test_dir) / "source.txt"
        self.dest_file = Path(self.test_dir) / "dest.txt"
        self.source_file.write_text("Test content")

    def tearDown(self):
        """Clean up temporary directory."""
        # Explicitly close any open connections to avoid Windows file locking
        if hasattr(self, 'tm') and self.tm:
            if self.tm.connection:
                self.tm.connection.close()
                self.tm.connection = None

            # Force garbage collection to release file handles
            del self.tm

        # Small delay to ensure Windows releases file locks
        import time
        time.sleep(0.1)

        # Clean up temp directory
        try:
            shutil.rmtree(self.test_dir)
        except PermissionError:
            # On Windows, sometimes need to retry
            time.sleep(0.2)
            shutil.rmtree(self.test_dir)

    def test_database_initialization(self):
        """Test database schema is created correctly."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Check transactions table exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='transactions'
        """)
        result = cursor.fetchone()
        self.assertIsNotNone(result)

        # Check indexes exist
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='index' AND name='idx_batch_id'
        """)
        result = cursor.fetchone()
        self.assertIsNotNone(result)

        conn.close()

    def test_begin_batch_auto_generate_id(self):
        """Test batch creation with auto-generated ID."""
        batch_id = self.tm.begin_batch()
        self.assertTrue(batch_id.startswith("batch_"))

    def test_begin_batch_custom_id(self):
        """Test batch creation with custom ID."""
        batch_id = self.tm.begin_batch("custom_batch")
        self.assertEqual(batch_id, "custom_batch")

    def test_log_operation(self):
        """Test operation logging creates database record."""
        batch_id = self.tm.begin_batch("test_batch")

        op = Operation(
            operation_type=OperationType.MOVE,
            source_path=str(self.source_file),
            destination_path=str(self.dest_file)
        )

        tx_id = self.tm.log_operation(op, batch_id)
        self.assertIsInstance(tx_id, int)
        self.assertGreater(tx_id, 0)

        # Verify record in database
        with self.tm._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM transactions WHERE id = ?", (tx_id,))
            row = cursor.fetchone()

        self.assertIsNotNone(row)
        self.assertEqual(row['transaction_batch_id'], batch_id)
        self.assertEqual(row['operation_type'], OperationType.MOVE.value)
        self.assertEqual(row['source_path'], str(self.source_file))
        self.assertEqual(row['status'], TransactionStatus.PENDING.value)
        self.assertIsNotNone(row['source_md5'])

    def test_log_operation_missing_source(self):
        """Test operation logging fails for missing source file."""
        batch_id = self.tm.begin_batch("test_batch")

        op = Operation(
            operation_type=OperationType.MOVE,
            source_path=str(Path(self.test_dir) / "missing.txt"),
            destination_path=str(self.dest_file)
        )

        with self.assertRaises(FileNotFoundError):
            self.tm.log_operation(op, batch_id)

    def test_complete_operation(self):
        """Test marking operation as completed."""
        batch_id = self.tm.begin_batch("test_batch")

        op = Operation(
            operation_type=OperationType.MOVE,
            source_path=str(self.source_file),
            destination_path=str(self.dest_file)
        )

        tx_id = self.tm.log_operation(op, batch_id)

        # Perform operation
        shutil.move(str(self.source_file), str(self.dest_file))

        # Complete transaction
        dest_md5 = FileHasher.calculate_md5(self.dest_file)
        self.tm.complete_operation(tx_id, dest_md5)

        # Verify status updated
        with self.tm._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT status, destination_md5 FROM transactions WHERE id = ?", (tx_id,))
            row = cursor.fetchone()

        self.assertEqual(row['status'], TransactionStatus.COMPLETED.value)
        self.assertEqual(row['destination_md5'], dest_md5)

    def test_fail_operation(self):
        """Test marking operation as failed."""
        batch_id = self.tm.begin_batch("test_batch")

        op = Operation(
            operation_type=OperationType.MOVE,
            source_path=str(self.source_file),
            destination_path=str(self.dest_file)
        )

        tx_id = self.tm.log_operation(op, batch_id)

        # Fail operation
        error_msg = "Test error message"
        self.tm.fail_operation(tx_id, error_msg)

        # Verify status updated
        with self.tm._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT status, error_message FROM transactions WHERE id = ?", (tx_id,))
            row = cursor.fetchone()

        self.assertEqual(row['status'], TransactionStatus.FAILED.value)
        self.assertEqual(row['error_message'], error_msg)

    def test_get_batch_status(self):
        """Test batch status retrieval."""
        batch_id = self.tm.begin_batch("test_batch")

        # Create multiple operations with different statuses
        ops = []
        for i in range(5):
            file_path = Path(self.test_dir) / f"file_{i}.txt"
            file_path.write_text(f"Content {i}")

            op = Operation(
                operation_type=OperationType.MOVE,
                source_path=str(file_path),
                destination_path=str(Path(self.test_dir) / f"dest_{i}.txt")
            )
            ops.append(op)

        tx_ids = [self.tm.log_operation(op, batch_id) for op in ops]

        # Complete some, fail others
        self.tm.complete_operation(tx_ids[0], "hash1")
        self.tm.complete_operation(tx_ids[1], "hash2")
        self.tm.fail_operation(tx_ids[2], "error")

        # Get status
        status = self.tm.get_batch_status(batch_id)

        self.assertEqual(status.batch_id, batch_id)
        self.assertEqual(status.total_operations, 5)
        self.assertEqual(status.completed, 2)
        self.assertEqual(status.failed, 1)
        self.assertEqual(status.pending, 2)
        self.assertEqual(status.rolled_back, 0)

    def test_rollback_batch(self):
        """Test batch rollback functionality."""
        batch_id = self.tm.begin_batch("test_batch")

        # Create test files and log operations
        source1 = Path(self.test_dir) / "source1.txt"
        dest1 = Path(self.test_dir) / "dest1.txt"
        source1.write_text("Content 1")

        source2 = Path(self.test_dir) / "source2.txt"
        dest2 = Path(self.test_dir) / "dest2.txt"
        source2.write_text("Content 2")

        op1 = Operation(OperationType.MOVE, str(source1), str(dest1))
        op2 = Operation(OperationType.MOVE, str(source2), str(dest2))

        tx_id1 = self.tm.log_operation(op1, batch_id)
        tx_id2 = self.tm.log_operation(op2, batch_id)

        # Perform operations
        shutil.move(str(source1), str(dest1))
        shutil.move(str(source2), str(dest2))

        # Complete operations
        self.tm.complete_operation(tx_id1, FileHasher.calculate_md5(dest1))
        self.tm.complete_operation(tx_id2, FileHasher.calculate_md5(dest2))

        # Verify files moved
        self.assertFalse(source1.exists())
        self.assertFalse(source2.exists())
        self.assertTrue(dest1.exists())
        self.assertTrue(dest2.exists())

        # Rollback
        result = self.tm.rollback_batch(batch_id, dry_run=False)

        # Verify rollback result
        self.assertEqual(result.batch_id, batch_id)
        self.assertEqual(result.total_operations, 2)
        self.assertEqual(result.successful_rollbacks, 2)
        self.assertEqual(result.failed_rollbacks, 0)
        self.assertEqual(len(result.errors), 0)

        # Verify files restored
        self.assertTrue(source1.exists())
        self.assertTrue(source2.exists())
        self.assertFalse(dest1.exists())
        self.assertFalse(dest2.exists())

        # Verify database status
        status = self.tm.get_batch_status(batch_id)
        self.assertEqual(status.rolled_back, 2)

    def test_rollback_batch_dry_run(self):
        """Test dry run mode doesn't actually rollback."""
        batch_id = self.tm.begin_batch("test_batch")

        source = Path(self.test_dir) / "source.txt"
        dest = Path(self.test_dir) / "dest.txt"
        source.write_text("Content")

        op = Operation(OperationType.MOVE, str(source), str(dest))
        tx_id = self.tm.log_operation(op, batch_id)

        shutil.move(str(source), str(dest))
        self.tm.complete_operation(tx_id, FileHasher.calculate_md5(dest))

        # Dry run rollback
        result = self.tm.rollback_batch(batch_id, dry_run=True)

        # Verify files NOT restored
        self.assertFalse(source.exists())
        self.assertTrue(dest.exists())

        # Verify status NOT updated
        status = self.tm.get_batch_status(batch_id)
        self.assertEqual(status.completed, 1)
        self.assertEqual(status.rolled_back, 0)

    def test_context_manager(self):
        """Test context manager opens and closes connection."""
        self.assertIsNone(self.tm.connection)

        with self.tm as tm:
            self.assertIsNotNone(tm.connection)

        self.assertIsNone(self.tm.connection)

    def test_get_batch_operations(self):
        """Test retrieving all operations for a batch."""
        batch_id = self.tm.begin_batch("test_batch")

        # Create operations
        for i in range(3):
            file_path = Path(self.test_dir) / f"file_{i}.txt"
            file_path.write_text(f"Content {i}")

            op = Operation(
                operation_type=OperationType.MOVE,
                source_path=str(file_path),
                destination_path=str(Path(self.test_dir) / f"dest_{i}.txt")
            )
            self.tm.log_operation(op, batch_id)

        # Get operations
        operations = self.tm.get_batch_operations(batch_id)

        self.assertEqual(len(operations), 3)
        for i, op in enumerate(operations):
            self.assertEqual(op.transaction_batch_id, batch_id)
            self.assertTrue(op.source_path.endswith(f"file_{i}.txt"))


class TestOperationDataclass(unittest.TestCase):
    """Test cases for Operation dataclass."""

    def test_to_dict(self):
        """Test Operation.to_dict() method."""
        op = Operation(
            operation_type=OperationType.MOVE,
            source_path="/source/file.mkv",
            destination_path="/dest/file.mkv",
            metadata={"key": "value"}
        )

        op_dict = op.to_dict()

        self.assertEqual(op_dict['operation_type'], "move")
        self.assertEqual(op_dict['source_path'], "/source/file.mkv")
        self.assertEqual(op_dict['destination_path'], "/dest/file.mkv")
        self.assertIn("key", op_dict['metadata'])


if __name__ == "__main__":
    unittest.main()
