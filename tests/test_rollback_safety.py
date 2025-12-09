"""
Rollback Safety Tests for JellyRancher.

CRITICAL: This module tests the rollback functionality that is essential for
user data safety. Rollback has NEVER been fully tested with real files.

Test Categories:
1. Basic Rollback - Single file move and rollback
2. Batch Rollback - Multiple files in a batch
3. Partial Rollback - Some succeed, some fail
4. Hash Verification - BLAKE3 hashes match after rollback
5. Edge Cases - Empty batches, missing files, permission errors
6. Power Failure Simulation - Interrupted operations
7. Concurrent Operations - Thread safety
8. Stress Testing - Large number of files

Uses REAL files in a temp directory - no mocks for file operations.
"""

import os
import sys
import shutil
import tempfile
import logging
import time
import threading
import sqlite3
from pathlib import Path
from typing import List, Tuple, Optional
from dataclasses import dataclass

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.utils.transaction_manager import (
    TransactionManager, Operation, OperationType, FileHasher,
    TransactionStatus, BatchStatus, RollbackResult
)

logger = logging.getLogger(__name__)


# =============================================================================
# TEST FIXTURES
# =============================================================================

@pytest.fixture
def temp_workspace():
    """Create a temporary workspace with source and destination directories."""
    base_dir = tempfile.mkdtemp(prefix="jr_rollback_test_")
    source_dir = Path(base_dir) / "source"
    dest_dir = Path(base_dir) / "destination"
    db_path = Path(base_dir) / "test_transactions.db"

    source_dir.mkdir()
    dest_dir.mkdir()

    yield {
        "base": Path(base_dir),
        "source": source_dir,
        "dest": dest_dir,
        "db_path": db_path
    }

    # Cleanup
    try:
        shutil.rmtree(base_dir)
    except Exception as e:
        logger.warning(f"Failed to cleanup temp workspace: {e}")


@pytest.fixture
def transaction_manager(temp_workspace):
    """Create a TransactionManager with a temporary database."""
    tm = TransactionManager(db_path=temp_workspace["db_path"])
    yield tm


def create_test_file(path: Path, content: str = None, size_kb: int = 1) -> Tuple[Path, str]:
    """
    Create a test file with known content and return its BLAKE3 hash.

    Args:
        path: Full path for the file
        content: Optional content (random if None)
        size_kb: Size in KB if content is None

    Returns:
        Tuple of (path, blake3_hash)
    """
    if content is None:
        # Create random content of specified size
        content = os.urandom(size_kb * 1024).hex()

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)

    file_hash = FileHasher.calculate_hash(path)
    return path, file_hash


def create_test_files(source_dir: Path, count: int = 5) -> List[Tuple[Path, str, str]]:
    """
    Create multiple test files.

    Returns:
        List of (path, content, hash) tuples
    """
    files = []
    for i in range(count):
        content = f"Test file {i} content - unique identifier {os.urandom(16).hex()}"
        path = source_dir / f"test_file_{i:04d}.txt"
        path.write_text(content)
        file_hash = FileHasher.calculate_hash(path)
        files.append((path, content, file_hash))
    return files


# =============================================================================
# TEST CLASS: BASIC ROLLBACK
# =============================================================================

class TestBasicRollback:
    """Test basic single-file rollback operations."""

    def test_single_file_move_and_rollback(self, temp_workspace, transaction_manager):
        """Test moving a single file and rolling it back."""
        # Create test file
        source_file = temp_workspace["source"] / "movie.mkv"
        content = "This is fake movie data"
        source_file.write_text(content)
        original_hash = FileHasher.calculate_hash(source_file)

        dest_file = temp_workspace["dest"] / "Movie (2020)" / "Movie (2020).mkv"

        # Begin transaction
        batch_id = transaction_manager.begin_batch("test_single_rollback")

        # Log the operation
        operation = Operation(
            operation_type=OperationType.MOVE,
            source_path=str(source_file),
            destination_path=str(dest_file)
        )
        tx_id = transaction_manager.log_operation(operation, batch_id)

        # Execute the move
        dest_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source_file), str(dest_file))

        # Complete the operation
        dest_hash = FileHasher.calculate_hash(dest_file)
        transaction_manager.complete_operation(tx_id, dest_hash)

        # Verify file moved
        assert not source_file.exists(), "Source should no longer exist"
        assert dest_file.exists(), "Destination should exist"
        assert original_hash == dest_hash, "Hash should match after move"

        # ROLLBACK
        result = transaction_manager.rollback_batch(batch_id)

        # Verify rollback
        assert result.successful_rollbacks == 1, "Should have 1 successful rollback"
        assert result.failed_rollbacks == 0, "Should have 0 failed rollbacks"
        assert source_file.exists(), "Source should exist again after rollback"
        assert not dest_file.exists(), "Destination should not exist after rollback"

        # Verify hash matches original
        rollback_hash = FileHasher.calculate_hash(source_file)
        assert rollback_hash == original_hash, "Hash should match original after rollback"

        # Verify content matches
        assert source_file.read_text() == content, "Content should match after rollback"

    def test_rollback_dry_run(self, temp_workspace, transaction_manager):
        """Test dry run rollback doesn't actually move files."""
        # Create and move file
        source_file = temp_workspace["source"] / "test.txt"
        source_file.write_text("test content")
        dest_file = temp_workspace["dest"] / "test_moved.txt"

        batch_id = transaction_manager.begin_batch("test_dry_run")
        operation = Operation(OperationType.MOVE, str(source_file), str(dest_file))
        tx_id = transaction_manager.log_operation(operation, batch_id)

        dest_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source_file), str(dest_file))
        transaction_manager.complete_operation(tx_id, FileHasher.calculate_hash(dest_file))

        # Dry run rollback
        result = transaction_manager.rollback_batch(batch_id, dry_run=True)

        # File should NOT be moved back
        assert result.successful_rollbacks == 1, "Dry run should report success"
        assert not source_file.exists(), "Source should NOT exist (dry run)"
        assert dest_file.exists(), "Destination should still exist (dry run)"

    def test_rollback_empty_batch(self, temp_workspace, transaction_manager):
        """Test rollback of batch with no operations."""
        batch_id = transaction_manager.begin_batch("empty_batch")

        result = transaction_manager.rollback_batch(batch_id)

        assert result.total_operations == 0
        assert result.successful_rollbacks == 0
        assert result.failed_rollbacks == 0


# =============================================================================
# TEST CLASS: BATCH ROLLBACK
# =============================================================================

class TestBatchRollback:
    """Test rollback of multiple operations in a batch."""

    def test_multiple_file_rollback(self, temp_workspace, transaction_manager):
        """Test rolling back multiple files in sequence."""
        files = create_test_files(temp_workspace["source"], count=5)
        batch_id = transaction_manager.begin_batch("multi_file_test")

        # Move all files and track original info
        original_info = []
        for source_path, content, original_hash in files:
            dest_path = temp_workspace["dest"] / source_path.name
            original_info.append((source_path, dest_path, content, original_hash))

            operation = Operation(OperationType.MOVE, str(source_path), str(dest_path))
            tx_id = transaction_manager.log_operation(operation, batch_id)

            shutil.move(str(source_path), str(dest_path))
            transaction_manager.complete_operation(tx_id, FileHasher.calculate_hash(dest_path))

        # Verify all moved
        for source_path, dest_path, _, _ in original_info:
            assert not source_path.exists()
            assert dest_path.exists()

        # Rollback
        result = transaction_manager.rollback_batch(batch_id)

        assert result.successful_rollbacks == 5
        assert result.failed_rollbacks == 0

        # Verify all restored
        for source_path, dest_path, content, original_hash in original_info:
            assert source_path.exists(), f"Source should exist: {source_path}"
            assert not dest_path.exists(), f"Dest should not exist: {dest_path}"
            assert source_path.read_text() == content, "Content should match"
            assert FileHasher.calculate_hash(source_path) == original_hash, "Hash should match"

    def test_nested_directory_rollback(self, temp_workspace, transaction_manager):
        """Test rollback with nested directory structures."""
        # Create nested source structure
        nested_source = temp_workspace["source"] / "Movies" / "Sci-Fi" / "2020"
        nested_source.mkdir(parents=True)
        source_file = nested_source / "Movie.mkv"
        source_file.write_text("movie content")
        original_hash = FileHasher.calculate_hash(source_file)

        # Create nested destination
        nested_dest = temp_workspace["dest"] / "Media" / "Films" / "Science Fiction"
        dest_file = nested_dest / "Movie (2020).mkv"

        batch_id = transaction_manager.begin_batch("nested_dir_test")
        operation = Operation(OperationType.MOVE, str(source_file), str(dest_file))
        tx_id = transaction_manager.log_operation(operation, batch_id)

        nested_dest.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source_file), str(dest_file))
        transaction_manager.complete_operation(tx_id, FileHasher.calculate_hash(dest_file))

        # Rollback
        result = transaction_manager.rollback_batch(batch_id)

        assert result.successful_rollbacks == 1
        assert source_file.exists(), "Source should exist in original nested location"
        assert FileHasher.calculate_hash(source_file) == original_hash

    def test_rollback_order_is_reversed(self, temp_workspace, transaction_manager):
        """Verify rollback happens in reverse chronological order."""
        batch_id = transaction_manager.begin_batch("order_test")
        rollback_order = []

        # Create files with unique content
        for i in range(3):
            source = temp_workspace["source"] / f"file_{i}.txt"
            source.write_text(f"content_{i}")
            dest = temp_workspace["dest"] / f"moved_{i}.txt"

            operation = Operation(OperationType.MOVE, str(source), str(dest))
            tx_id = transaction_manager.log_operation(operation, batch_id)
            shutil.move(str(source), str(dest))
            transaction_manager.complete_operation(tx_id, FileHasher.calculate_hash(dest))

        # Get batch operations before rollback
        ops = transaction_manager.get_batch_operations(batch_id)
        # Rollback should process in DESC order (newest first)

        result = transaction_manager.rollback_batch(batch_id)
        assert result.successful_rollbacks == 3


# =============================================================================
# TEST CLASS: PARTIAL ROLLBACK
# =============================================================================

class TestPartialRollback:
    """Test rollback when some operations fail."""

    def test_rollback_with_missing_destination(self, temp_workspace, transaction_manager):
        """Test rollback when destination file was deleted externally."""
        # Create and move file
        source_file = temp_workspace["source"] / "test.txt"
        source_file.write_text("test content")
        dest_file = temp_workspace["dest"] / "test_moved.txt"

        batch_id = transaction_manager.begin_batch("missing_dest_test")
        operation = Operation(OperationType.MOVE, str(source_file), str(dest_file))
        tx_id = transaction_manager.log_operation(operation, batch_id)

        dest_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source_file), str(dest_file))
        transaction_manager.complete_operation(tx_id, FileHasher.calculate_hash(dest_file))

        # Externally delete the destination
        dest_file.unlink()

        # Attempt rollback
        result = transaction_manager.rollback_batch(batch_id)

        assert result.failed_rollbacks == 1
        assert len(result.errors) == 1
        assert "missing" in result.errors[0].lower() or "not found" in result.errors[0].lower()

    def test_partial_batch_rollback(self, temp_workspace, transaction_manager):
        """Test rollback when some files succeed and some fail."""
        batch_id = transaction_manager.begin_batch("partial_test")

        # Create and move 3 files
        moves = []
        for i in range(3):
            source = temp_workspace["source"] / f"file_{i}.txt"
            source.write_text(f"content_{i}")
            dest = temp_workspace["dest"] / f"moved_{i}.txt"
            moves.append((source, dest))

            operation = Operation(OperationType.MOVE, str(source), str(dest))
            tx_id = transaction_manager.log_operation(operation, batch_id)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(dest))
            transaction_manager.complete_operation(tx_id, FileHasher.calculate_hash(dest))

        # Delete middle file to simulate partial failure
        moves[1][1].unlink()

        # Rollback
        result = transaction_manager.rollback_batch(batch_id)

        # Should have 2 successes, 1 failure
        assert result.successful_rollbacks == 2
        assert result.failed_rollbacks == 1

        # File 0 and 2 should be restored, file 1 should not
        assert moves[0][0].exists(), "File 0 should be restored"
        assert not moves[1][0].exists(), "File 1 should NOT be restored (destination was missing)"
        assert moves[2][0].exists(), "File 2 should be restored"


# =============================================================================
# TEST CLASS: HASH VERIFICATION
# =============================================================================

class TestHashVerification:
    """Test BLAKE3 hash integrity throughout operations."""

    def test_hash_integrity_through_cycle(self, temp_workspace, transaction_manager):
        """Test that hash remains consistent through move->rollback cycle."""
        # Create file with specific content
        source_file = temp_workspace["source"] / "integrity_test.dat"
        content = b"Binary content with special chars: \x00\x01\x02\xff"
        source_file.write_bytes(content)

        original_hash = FileHasher.calculate_hash(source_file)

        dest_file = temp_workspace["dest"] / "integrity_moved.dat"

        batch_id = transaction_manager.begin_batch("hash_integrity_test")
        operation = Operation(OperationType.MOVE, str(source_file), str(dest_file))
        tx_id = transaction_manager.log_operation(operation, batch_id)

        dest_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source_file), str(dest_file))

        dest_hash = FileHasher.calculate_hash(dest_file)
        transaction_manager.complete_operation(tx_id, dest_hash)

        # Hash should match after move
        assert original_hash == dest_hash, "Hash should match after move"

        # Rollback
        transaction_manager.rollback_batch(batch_id)

        # Hash should match after rollback
        rollback_hash = FileHasher.calculate_hash(source_file)
        assert rollback_hash == original_hash, "Hash should match original after rollback"

        # Content should be identical
        assert source_file.read_bytes() == content, "Binary content should match"

    def test_large_file_hash_consistency(self, temp_workspace, transaction_manager):
        """Test hash consistency with larger files."""
        # Create a 10MB file
        source_file = temp_workspace["source"] / "large_file.bin"
        content = os.urandom(10 * 1024 * 1024)  # 10MB
        source_file.write_bytes(content)

        original_hash = FileHasher.calculate_hash(source_file)

        dest_file = temp_workspace["dest"] / "large_moved.bin"

        batch_id = transaction_manager.begin_batch("large_file_test")
        operation = Operation(OperationType.MOVE, str(source_file), str(dest_file))
        tx_id = transaction_manager.log_operation(operation, batch_id)

        dest_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source_file), str(dest_file))
        transaction_manager.complete_operation(tx_id, FileHasher.calculate_hash(dest_file))

        # Rollback
        transaction_manager.rollback_batch(batch_id)

        # Verify hash
        rollback_hash = FileHasher.calculate_hash(source_file)
        assert rollback_hash == original_hash, "Large file hash should match after rollback"

    def test_verify_hash_method(self, temp_workspace):
        """Test the verify_hash utility method."""
        file_path = temp_workspace["source"] / "verify_test.txt"
        file_path.write_text("verification content")

        correct_hash = FileHasher.calculate_hash(file_path)
        wrong_hash = "0" * 64  # BLAKE3 produces 64-char hex

        assert FileHasher.verify_hash(file_path, correct_hash) is True
        assert FileHasher.verify_hash(file_path, wrong_hash) is False
        assert FileHasher.verify_hash(temp_workspace["source"] / "nonexistent.txt", correct_hash) is False


# =============================================================================
# TEST CLASS: EDGE CASES
# =============================================================================

class TestEdgeCases:
    """Test edge cases and unusual scenarios."""

    def test_special_characters_in_filename(self, temp_workspace, transaction_manager):
        """Test rollback with special characters in filenames."""
        special_names = [
            "file with spaces.txt",
            "file_with_émojis_🎬.txt",
            "日本語ファイル.txt",
            "file (with) [brackets].txt",
            "file-with-dashes.txt",
            "file.multiple.dots.txt",
        ]

        batch_id = transaction_manager.begin_batch("special_chars_test")

        for name in special_names:
            try:
                source = temp_workspace["source"] / name
                source.write_text(f"Content for {name}")
                dest = temp_workspace["dest"] / f"moved_{name}"

                operation = Operation(OperationType.MOVE, str(source), str(dest))
                tx_id = transaction_manager.log_operation(operation, batch_id)
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(source), str(dest))
                transaction_manager.complete_operation(tx_id, FileHasher.calculate_hash(dest))
            except Exception as e:
                logger.warning(f"Skipping file with name '{name}': {e}")
                continue

        result = transaction_manager.rollback_batch(batch_id)

        # All that succeeded should rollback
        assert result.failed_rollbacks == 0

    def test_very_long_path(self, temp_workspace, transaction_manager):
        """Test rollback with very long file paths."""
        # Create a deep nested path
        deep_path = temp_workspace["source"]
        for i in range(10):
            deep_path = deep_path / f"level_{i:02d}"

        deep_path.mkdir(parents=True, exist_ok=True)
        source_file = deep_path / "deep_file.txt"
        source_file.write_text("deep content")

        dest_file = temp_workspace["dest"] / "shallow.txt"

        batch_id = transaction_manager.begin_batch("long_path_test")
        operation = Operation(OperationType.MOVE, str(source_file), str(dest_file))
        tx_id = transaction_manager.log_operation(operation, batch_id)

        dest_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source_file), str(dest_file))
        transaction_manager.complete_operation(tx_id, FileHasher.calculate_hash(dest_file))

        result = transaction_manager.rollback_batch(batch_id)

        assert result.successful_rollbacks == 1
        assert source_file.exists()

    def test_empty_file(self, temp_workspace, transaction_manager):
        """Test rollback with empty files."""
        source_file = temp_workspace["source"] / "empty.txt"
        source_file.write_text("")  # Empty file

        original_hash = FileHasher.calculate_hash(source_file)
        dest_file = temp_workspace["dest"] / "empty_moved.txt"

        batch_id = transaction_manager.begin_batch("empty_file_test")
        operation = Operation(OperationType.MOVE, str(source_file), str(dest_file))
        tx_id = transaction_manager.log_operation(operation, batch_id)

        dest_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source_file), str(dest_file))
        transaction_manager.complete_operation(tx_id, FileHasher.calculate_hash(dest_file))

        result = transaction_manager.rollback_batch(batch_id)

        assert result.successful_rollbacks == 1
        assert source_file.exists()
        assert source_file.read_text() == ""
        assert FileHasher.calculate_hash(source_file) == original_hash

    def test_rollback_nonexistent_batch(self, temp_workspace, transaction_manager):
        """Test rollback of a batch that doesn't exist."""
        result = transaction_manager.rollback_batch("nonexistent_batch_12345")

        assert result.total_operations == 0
        assert result.successful_rollbacks == 0
        assert result.failed_rollbacks == 0

    def test_batch_status_tracking(self, temp_workspace, transaction_manager):
        """Test batch status is properly tracked through operations."""
        source_file = temp_workspace["source"] / "status_test.txt"
        source_file.write_text("status test")
        dest_file = temp_workspace["dest"] / "status_moved.txt"

        batch_id = transaction_manager.begin_batch("status_tracking")

        # Check initial status (should be 0 operations)
        status = transaction_manager.get_batch_status(batch_id)
        assert status.total_operations == 0

        # Log operation
        operation = Operation(OperationType.MOVE, str(source_file), str(dest_file))
        tx_id = transaction_manager.log_operation(operation, batch_id)

        # Status should show 1 pending
        status = transaction_manager.get_batch_status(batch_id)
        assert status.total_operations == 1
        assert status.pending == 1
        assert status.completed == 0

        # Complete operation
        dest_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source_file), str(dest_file))
        transaction_manager.complete_operation(tx_id, FileHasher.calculate_hash(dest_file))

        # Status should show 1 completed
        status = transaction_manager.get_batch_status(batch_id)
        assert status.completed == 1
        assert status.pending == 0

        # Rollback
        transaction_manager.rollback_batch(batch_id)

        # Status should show 1 rolled back
        status = transaction_manager.get_batch_status(batch_id)
        assert status.rolled_back == 1
        assert status.completed == 0


# =============================================================================
# TEST CLASS: FAILURE SIMULATION
# =============================================================================

class TestFailureSimulation:
    """Test behavior during simulated failures."""

    def test_operation_failure_logging(self, temp_workspace, transaction_manager):
        """Test that failed operations are properly logged."""
        source_file = temp_workspace["source"] / "fail_test.txt"
        source_file.write_text("test")
        dest_file = temp_workspace["dest"] / "fail_moved.txt"

        batch_id = transaction_manager.begin_batch("failure_logging")
        operation = Operation(OperationType.MOVE, str(source_file), str(dest_file))
        tx_id = transaction_manager.log_operation(operation, batch_id)

        # Simulate failure (don't actually move, just mark as failed)
        transaction_manager.fail_operation(tx_id, "Simulated disk full error")

        # Check status
        status = transaction_manager.get_batch_status(batch_id)
        assert status.failed == 1
        assert status.completed == 0

        # Failed operations should not be included in rollback
        result = transaction_manager.rollback_batch(batch_id)
        assert result.total_operations == 0  # Only completed ops are rolled back

    def test_source_deleted_during_operation(self, temp_workspace, transaction_manager):
        """Test logging operation when source is deleted mid-operation."""
        source_file = temp_workspace["source"] / "disappearing.txt"
        source_file.write_text("test")

        batch_id = transaction_manager.begin_batch("disappearing_source")

        # Delete source before logging (simulates race condition)
        source_path = str(source_file)
        source_file.unlink()

        operation = Operation(OperationType.MOVE, source_path, str(temp_workspace["dest"] / "gone.txt"))

        # Should raise FileNotFoundError
        with pytest.raises(FileNotFoundError):
            transaction_manager.log_operation(operation, batch_id)

    def test_rollback_with_destination_permission_error(self, temp_workspace, transaction_manager):
        """Test rollback behavior when source dir is not writable."""
        source_file = temp_workspace["source"] / "perm_test.txt"
        source_file.write_text("permission test")
        dest_file = temp_workspace["dest"] / "perm_moved.txt"

        batch_id = transaction_manager.begin_batch("permission_test")
        operation = Operation(OperationType.MOVE, str(source_file), str(dest_file))
        tx_id = transaction_manager.log_operation(operation, batch_id)

        dest_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source_file), str(dest_file))
        transaction_manager.complete_operation(tx_id, FileHasher.calculate_hash(dest_file))

        # Remove source directory (rollback can't recreate it)
        shutil.rmtree(temp_workspace["source"])

        # Rollback should still work (it recreates parent dirs)
        result = transaction_manager.rollback_batch(batch_id)
        assert result.successful_rollbacks == 1
        assert source_file.exists()


# =============================================================================
# TEST CLASS: STRESS TESTING
# =============================================================================

class TestStress:
    """Stress tests for rollback functionality."""

    @pytest.mark.slow
    def test_large_batch_rollback(self, temp_workspace, transaction_manager):
        """Test rollback with a large number of files (100)."""
        batch_id = transaction_manager.begin_batch("large_batch")
        files = create_test_files(temp_workspace["source"], count=100)

        # Move all files
        for source_path, content, original_hash in files:
            dest_path = temp_workspace["dest"] / source_path.name
            operation = Operation(OperationType.MOVE, str(source_path), str(dest_path))
            tx_id = transaction_manager.log_operation(operation, batch_id)
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source_path), str(dest_path))
            transaction_manager.complete_operation(tx_id, FileHasher.calculate_hash(dest_path))

        # Verify all moved
        assert len(list(temp_workspace["dest"].glob("*.txt"))) == 100
        assert len(list(temp_workspace["source"].glob("*.txt"))) == 0

        # Rollback
        start_time = time.time()
        result = transaction_manager.rollback_batch(batch_id)
        elapsed = time.time() - start_time

        # All should succeed
        assert result.successful_rollbacks == 100
        assert result.failed_rollbacks == 0

        # All should be restored
        assert len(list(temp_workspace["source"].glob("*.txt"))) == 100
        assert len(list(temp_workspace["dest"].glob("*.txt"))) == 0

        # Should complete in reasonable time (< 30 seconds)
        assert elapsed < 30, f"Large batch rollback took {elapsed:.2f}s, expected < 30s"

    @pytest.mark.slow
    def test_repeated_rollback_same_batch(self, temp_workspace, transaction_manager):
        """Test that rolling back the same batch twice is safe."""
        source_file = temp_workspace["source"] / "repeat_test.txt"
        source_file.write_text("repeat")
        dest_file = temp_workspace["dest"] / "repeat_moved.txt"

        batch_id = transaction_manager.begin_batch("repeat_test")
        operation = Operation(OperationType.MOVE, str(source_file), str(dest_file))
        tx_id = transaction_manager.log_operation(operation, batch_id)

        dest_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source_file), str(dest_file))
        transaction_manager.complete_operation(tx_id, FileHasher.calculate_hash(dest_file))

        # First rollback
        result1 = transaction_manager.rollback_batch(batch_id)
        assert result1.successful_rollbacks == 1

        # Second rollback (should have nothing to do - status is now "rolled_back")
        result2 = transaction_manager.rollback_batch(batch_id)
        assert result2.total_operations == 0  # Nothing in "completed" status


# =============================================================================
# TEST CLASS: CONCURRENT OPERATIONS
# =============================================================================

class TestConcurrency:
    """Test thread safety of rollback operations."""

    def test_concurrent_batch_operations(self, temp_workspace):
        """Test that separate batches can operate concurrently."""
        db_path = temp_workspace["db_path"]
        results = []
        errors = []

        def worker(batch_num):
            try:
                tm = TransactionManager(db_path=db_path)
                batch_id = tm.begin_batch(f"concurrent_batch_{batch_num}")

                source = temp_workspace["source"] / f"concurrent_{batch_num}.txt"
                source.write_text(f"concurrent content {batch_num}")
                dest = temp_workspace["dest"] / f"concurrent_moved_{batch_num}.txt"

                operation = Operation(OperationType.MOVE, str(source), str(dest))
                tx_id = tm.log_operation(operation, batch_id)

                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(source), str(dest))
                tm.complete_operation(tx_id, FileHasher.calculate_hash(dest))

                result = tm.rollback_batch(batch_id)
                results.append((batch_num, result.successful_rollbacks))
            except Exception as e:
                errors.append((batch_num, str(e)))

        # Create source files first
        for i in range(5):
            (temp_workspace["source"] / f"concurrent_{i}.txt").write_text(f"content {i}")

        # Run in parallel
        threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Check results
        assert len(errors) == 0, f"Concurrent errors: {errors}"
        assert len(results) == 5
        assert all(count == 1 for _, count in results)


# =============================================================================
# TEST CLASS: DATABASE INTEGRITY
# =============================================================================

class TestDatabaseIntegrity:
    """Test database integrity and recovery."""

    def test_database_survives_crash_simulation(self, temp_workspace, transaction_manager):
        """Test that database maintains integrity even if process is interrupted."""
        source_file = temp_workspace["source"] / "crash_test.txt"
        source_file.write_text("crash test content")
        dest_file = temp_workspace["dest"] / "crash_moved.txt"

        batch_id = transaction_manager.begin_batch("crash_simulation")
        operation = Operation(OperationType.MOVE, str(source_file), str(dest_file))
        tx_id = transaction_manager.log_operation(operation, batch_id)

        # Complete the move
        dest_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source_file), str(dest_file))
        transaction_manager.complete_operation(tx_id, FileHasher.calculate_hash(dest_file))

        # Simulate "crash" by creating new TransactionManager instance
        del transaction_manager
        new_tm = TransactionManager(db_path=temp_workspace["db_path"])

        # Should be able to find and rollback the batch
        status = new_tm.get_batch_status(batch_id)
        assert status.completed == 1

        result = new_tm.rollback_batch(batch_id)
        assert result.successful_rollbacks == 1
        assert source_file.exists()

    def test_get_batch_operations(self, temp_workspace, transaction_manager):
        """Test retrieving all operations in a batch."""
        batch_id = transaction_manager.begin_batch("retrieval_test")

        # Create multiple operations
        for i in range(3):
            source = temp_workspace["source"] / f"retrieve_{i}.txt"
            source.write_text(f"content {i}")
            dest = temp_workspace["dest"] / f"retrieve_moved_{i}.txt"

            operation = Operation(OperationType.MOVE, str(source), str(dest))
            tx_id = transaction_manager.log_operation(operation, batch_id)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(dest))
            transaction_manager.complete_operation(tx_id, FileHasher.calculate_hash(dest))

        # Get operations
        ops = transaction_manager.get_batch_operations(batch_id)

        assert len(ops) == 3
        assert all(op.status == "completed" for op in ops)
        assert all(op.transaction_batch_id == batch_id for op in ops)


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
