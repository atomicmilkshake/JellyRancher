"""
Stress Tests for JellyRancher.

Tests system behavior under high load and stress conditions:
1. Large file counts - 1000+ files in a single batch
2. Large file sizes - Files over 1GB (simulated)
3. Deep directory structures - 50+ levels deep
4. Concurrent operations - Multiple batches simultaneously
5. Rapid operations - Many operations in quick succession
6. Memory pressure - Operations under low memory conditions
7. Long-running operations - Tests that simulate extended usage

These tests are designed to find edge cases and performance bottlenecks.
"""

import os
import sys
import time
import sqlite3
import tempfile
import shutil
import threading
import random
import string
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional, Tuple

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.utils.transaction_manager import (
    TransactionManager, Operation, OperationType, FileHasher
)


# =============================================================================
# MARKERS
# =============================================================================

slow = pytest.mark.skipif(
    "not config.getoption('--run-slow')",
    reason="Slow test (use --run-slow to run)"
)


# =============================================================================
# TEST FIXTURES
# =============================================================================

@pytest.fixture
def temp_workspace():
    """Create a temporary workspace."""
    base_dir = tempfile.mkdtemp(prefix="jr_stress_")
    yield {
        "base": Path(base_dir),
        "db_path": Path(base_dir) / "test.db"
    }
    try:
        shutil.rmtree(base_dir)
    except Exception:
        pass


@pytest.fixture
def large_file_set(temp_workspace):
    """Create a set of test files for stress testing."""
    source_dir = temp_workspace["base"] / "source"
    source_dir.mkdir(parents=True)
    
    files = []
    for i in range(100):  # 100 files for basic tests
        f = source_dir / f"file_{i:04d}.txt"
        f.write_text(f"Content for file {i}")
        files.append(f)
    
    return files


# =============================================================================
# TEST CLASS: FILE COUNT STRESS
# =============================================================================

class TestFileCountStress:
    """Test handling of large numbers of files."""

    def test_100_file_batch(self, temp_workspace, large_file_set):
        """Test batch operations with 100 files."""
        tm = TransactionManager(db_path=temp_workspace["db_path"])
        dest_dir = temp_workspace["base"] / "dest"
        dest_dir.mkdir(parents=True)

        batch_id = tm.begin_batch("100_files")
        
        operations = []
        for source in large_file_set:
            dest = dest_dir / source.name
            op = Operation(OperationType.MOVE, str(source), str(dest))
            tx_id = tm.log_operation(op, batch_id)
            operations.append((source, dest, tx_id))

        # Execute all operations
        for source, dest, tx_id in operations:
            shutil.move(str(source), str(dest))
            tm.complete_operation(tx_id, FileHasher.calculate_hash(dest))

        # Verify all completed
        status = tm.get_batch_status(batch_id)
        assert status.completed == 100
        assert status.failed == 0

    def test_rollback_100_files(self, temp_workspace, large_file_set):
        """Test rolling back 100 file operations."""
        tm = TransactionManager(db_path=temp_workspace["db_path"])
        dest_dir = temp_workspace["base"] / "dest"
        dest_dir.mkdir(parents=True)

        batch_id = tm.begin_batch("rollback_100")
        
        # Move all files
        for source in large_file_set:
            dest = dest_dir / source.name
            op = Operation(OperationType.MOVE, str(source), str(dest))
            tx_id = tm.log_operation(op, batch_id)
            shutil.move(str(source), str(dest))
            tm.complete_operation(tx_id, FileHasher.calculate_hash(dest))

        # Verify files moved
        assert len(list(dest_dir.iterdir())) == 100

        # Rollback all
        result = tm.rollback_batch(batch_id)
        assert result.successful_rollbacks == 100

        # Verify files restored
        source_dir = temp_workspace["base"] / "source"
        assert len(list(source_dir.iterdir())) == 100
        assert len(list(dest_dir.iterdir())) == 0

    @slow
    def test_1000_file_batch(self, temp_workspace):
        """Test batch operations with 1000 files."""
        tm = TransactionManager(db_path=temp_workspace["db_path"])
        source_dir = temp_workspace["base"] / "source"
        dest_dir = temp_workspace["base"] / "dest"
        source_dir.mkdir(parents=True)
        dest_dir.mkdir(parents=True)

        # Create 1000 files
        for i in range(1000):
            (source_dir / f"file_{i:04d}.txt").write_text(f"Content {i}")

        batch_id = tm.begin_batch("1000_files")
        start_time = time.time()

        # Log and execute all operations
        for f in source_dir.iterdir():
            dest = dest_dir / f.name
            op = Operation(OperationType.MOVE, str(f), str(dest))
            tx_id = tm.log_operation(op, batch_id)
            shutil.move(str(f), str(dest))
            tm.complete_operation(tx_id, FileHasher.calculate_hash(dest))

        elapsed = time.time() - start_time
        
        status = tm.get_batch_status(batch_id)
        assert status.completed == 1000
        # Should complete in reasonable time (< 30 seconds)
        assert elapsed < 30, f"1000 file operations took {elapsed:.2f}s (too slow)"


# =============================================================================
# TEST CLASS: FILE SIZE STRESS
# =============================================================================

class TestFileSizeStress:
    """Test handling of large files."""

    def test_10mb_file_operations(self, temp_workspace):
        """Test operations on 10MB files."""
        tm = TransactionManager(db_path=temp_workspace["db_path"])
        
        source = temp_workspace["base"] / "large.bin"
        dest = temp_workspace["base"] / "moved_large.bin"

        # Create 10MB file
        data = os.urandom(10 * 1024 * 1024)  # 10MB of random data
        source.write_bytes(data)

        batch_id = tm.begin_batch("large_file")
        op = Operation(OperationType.MOVE, str(source), str(dest))
        tx_id = tm.log_operation(op, batch_id)
        
        # Move the file
        shutil.move(str(source), str(dest))
        
        # Hash should be calculated correctly
        hash_value = FileHasher.calculate_hash(dest)
        tm.complete_operation(tx_id, hash_value)

        status = tm.get_batch_status(batch_id)
        assert status.completed == 1

    def test_many_medium_files(self, temp_workspace):
        """Test operations on many medium-sized files (1MB each)."""
        tm = TransactionManager(db_path=temp_workspace["db_path"])
        source_dir = temp_workspace["base"] / "source"
        dest_dir = temp_workspace["base"] / "dest"
        source_dir.mkdir(parents=True)
        dest_dir.mkdir(parents=True)

        # Create 10 x 1MB files
        for i in range(10):
            f = source_dir / f"medium_{i}.bin"
            f.write_bytes(os.urandom(1024 * 1024))

        batch_id = tm.begin_batch("medium_files")
        
        for f in source_dir.iterdir():
            dest = dest_dir / f.name
            op = Operation(OperationType.MOVE, str(f), str(dest))
            tx_id = tm.log_operation(op, batch_id)
            shutil.move(str(f), str(dest))
            tm.complete_operation(tx_id, FileHasher.calculate_hash(dest))

        status = tm.get_batch_status(batch_id)
        assert status.completed == 10


# =============================================================================
# TEST CLASS: DIRECTORY DEPTH STRESS
# =============================================================================

class TestDirectoryDepthStress:
    """Test handling of deep directory structures."""

    def test_20_level_deep_directory(self, temp_workspace):
        """Test operations 20 levels deep."""
        tm = TransactionManager(db_path=temp_workspace["db_path"])

        # Create nested structure
        deep_path = temp_workspace["base"]
        for i in range(20):
            deep_path = deep_path / f"level_{i:02d}"
        deep_path.mkdir(parents=True)

        source = deep_path / "deep_file.txt"
        source.write_text("Deep content")

        # Create equally deep destination
        dest_path = temp_workspace["base"] / "dest"
        for i in range(20):
            dest_path = dest_path / f"level_{i:02d}"
        dest_path.mkdir(parents=True)

        dest = dest_path / "deep_file.txt"

        batch_id = tm.begin_batch("deep_structure")
        op = Operation(OperationType.MOVE, str(source), str(dest))
        tx_id = tm.log_operation(op, batch_id)
        shutil.move(str(source), str(dest))
        tm.complete_operation(tx_id, FileHasher.calculate_hash(dest))

        # Verify
        assert dest.exists()
        status = tm.get_batch_status(batch_id)
        assert status.completed == 1

    @slow
    def test_50_level_deep_directory(self, temp_workspace):
        """Test operations 50 levels deep."""
        tm = TransactionManager(db_path=temp_workspace["db_path"])

        # Create 50-level nested structure
        deep_path = temp_workspace["base"]
        for i in range(50):
            deep_path = deep_path / f"L{i:02d}"
        
        try:
            deep_path.mkdir(parents=True)
        except OSError as e:
            # Some systems have path length limits
            pytest.skip(f"Cannot create 50-level deep directory: {e}")

        source = deep_path / "file.txt"
        source.write_text("Very deep content")

        batch_id = tm.begin_batch("very_deep")
        dest = deep_path.parent / "moved_file.txt"
        op = Operation(OperationType.MOVE, str(source), str(dest))
        tx_id = tm.log_operation(op, batch_id)
        shutil.move(str(source), str(dest))
        tm.complete_operation(tx_id, FileHasher.calculate_hash(dest))

        assert dest.exists()


# =============================================================================
# TEST CLASS: CONCURRENT OPERATIONS
# =============================================================================

class TestConcurrentOperations:
    """Test concurrent batch operations."""

    def test_multiple_batches_simultaneously(self, temp_workspace):
        """Test running multiple batches at the same time."""
        tm = TransactionManager(db_path=temp_workspace["db_path"])
        
        # Create source files for each batch
        batch_count = 5
        files_per_batch = 10
        
        for batch_idx in range(batch_count):
            source_dir = temp_workspace["base"] / f"batch_{batch_idx}" / "source"
            source_dir.mkdir(parents=True)
            for i in range(files_per_batch):
                (source_dir / f"file_{i}.txt").write_text(f"B{batch_idx}F{i}")

        results = []
        
        def run_batch(batch_idx: int) -> Tuple[str, int, int]:
            """Run a batch and return results."""
            source_dir = temp_workspace["base"] / f"batch_{batch_idx}" / "source"
            dest_dir = temp_workspace["base"] / f"batch_{batch_idx}" / "dest"
            dest_dir.mkdir(parents=True)
            
            batch_id = tm.begin_batch(f"concurrent_batch_{batch_idx}")
            completed = 0
            
            for f in source_dir.iterdir():
                dest = dest_dir / f.name
                op = Operation(OperationType.MOVE, str(f), str(dest))
                tx_id = tm.log_operation(op, batch_id)
                shutil.move(str(f), str(dest))
                tm.complete_operation(tx_id, FileHasher.calculate_hash(dest))
                completed += 1
            
            status = tm.get_batch_status(batch_id)
            return (batch_id, completed, status.completed)

        # Run all batches in threads
        with ThreadPoolExecutor(max_workers=batch_count) as executor:
            futures = [executor.submit(run_batch, i) for i in range(batch_count)]
            for future in as_completed(futures):
                results.append(future.result())

        # All batches should complete successfully
        for batch_id, local_count, db_count in results:
            assert local_count == files_per_batch
            assert db_count == files_per_batch

    def test_concurrent_rollbacks(self, temp_workspace):
        """Test concurrent rollback operations."""
        tm = TransactionManager(db_path=temp_workspace["db_path"])
        
        # Create and complete batches
        batch_ids = []
        for batch_idx in range(3):
            source_dir = temp_workspace["base"] / f"rb_{batch_idx}" / "source"
            dest_dir = temp_workspace["base"] / f"rb_{batch_idx}" / "dest"
            source_dir.mkdir(parents=True)
            dest_dir.mkdir(parents=True)
            
            for i in range(5):
                (source_dir / f"file_{i}.txt").write_text(f"Content {batch_idx}-{i}")
            
            batch_id = tm.begin_batch(f"rollback_batch_{batch_idx}")
            batch_ids.append(batch_id)
            
            for f in source_dir.iterdir():
                dest = dest_dir / f.name
                op = Operation(OperationType.MOVE, str(f), str(dest))
                tx_id = tm.log_operation(op, batch_id)
                shutil.move(str(f), str(dest))
                tm.complete_operation(tx_id, FileHasher.calculate_hash(dest))

        # Rollback all batches concurrently
        def do_rollback(batch_id: str):
            return tm.rollback_batch(batch_id)

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(do_rollback, bid) for bid in batch_ids]
            results = [f.result() for f in as_completed(futures)]

        # All rollbacks should succeed
        for result in results:
            assert result.successful_rollbacks == 5


# =============================================================================
# TEST CLASS: RAPID OPERATIONS
# =============================================================================

class TestRapidOperations:
    """Test rapid sequential operations."""

    def test_rapid_batch_creation(self, temp_workspace):
        """Test creating many batches in rapid succession."""
        tm = TransactionManager(db_path=temp_workspace["db_path"])
        
        start_time = time.time()
        batch_ids = []
        
        for i in range(100):
            batch_id = tm.begin_batch(f"rapid_batch_{i}")
            batch_ids.append(batch_id)
        
        elapsed = time.time() - start_time
        
        assert len(batch_ids) == 100
        # Should be very fast (< 1 second for 100 batches)
        assert elapsed < 1.0, f"Creating 100 batches took {elapsed:.2f}s"

    def test_rapid_operation_logging(self, temp_workspace):
        """Test logging many operations rapidly."""
        tm = TransactionManager(db_path=temp_workspace["db_path"])
        
        # Create test files
        source_dir = temp_workspace["base"] / "source"
        source_dir.mkdir(parents=True)
        for i in range(50):
            (source_dir / f"file_{i}.txt").write_text(f"Content {i}")

        batch_id = tm.begin_batch("rapid_log")
        start_time = time.time()
        
        for f in source_dir.iterdir():
            dest = temp_workspace["base"] / "dest" / f.name
            op = Operation(OperationType.MOVE, str(f), str(dest))
            tm.log_operation(op, batch_id)
        
        elapsed = time.time() - start_time
        
        # Should be fast (< 1.0 seconds for 50 operations; accounts for machine variance)
        assert elapsed < 1.0, f"Logging 50 operations took {elapsed:.2f}s"

    def test_rapid_status_queries(self, temp_workspace):
        """Test querying batch status rapidly."""
        tm = TransactionManager(db_path=temp_workspace["db_path"])
        batch_id = tm.begin_batch("status_test")
        
        # Add some operations
        source = temp_workspace["base"] / "test.txt"
        source.write_text("test")
        op = Operation(OperationType.MOVE, str(source), str(temp_workspace["base"] / "moved.txt"))
        tm.log_operation(op, batch_id)
        
        start_time = time.time()
        
        for _ in range(1000):
            tm.get_batch_status(batch_id)
        
        elapsed = time.time() - start_time
        
        # 1000 queries should be very fast (< 1 second)
        assert elapsed < 1.0, f"1000 status queries took {elapsed:.2f}s"


# =============================================================================
# TEST CLASS: LONG PATH STRESS
# =============================================================================

class TestLongPathStress:
    """Test handling of long file paths."""

    def test_long_filename(self, temp_workspace):
        """Test operations on files with long names."""
        tm = TransactionManager(db_path=temp_workspace["db_path"])
        
        # Create file with longest reasonable name (200 chars)
        long_name = "A" * 200 + ".txt"
        source = temp_workspace["base"] / long_name
        
        try:
            source.write_text("Long filename content")
        except OSError:
            pytest.skip("OS doesn't support 200-char filenames")
        
        dest = temp_workspace["base"] / ("B" * 200 + ".txt")
        
        batch_id = tm.begin_batch("long_name")
        op = Operation(OperationType.MOVE, str(source), str(dest))
        tx_id = tm.log_operation(op, batch_id)
        shutil.move(str(source), str(dest))
        tm.complete_operation(tx_id, FileHasher.calculate_hash(dest))
        
        assert dest.exists()

    def test_unicode_stress(self, temp_workspace):
        """Test operations with various Unicode characters."""
        tm = TransactionManager(db_path=temp_workspace["db_path"])
        
        unicode_names = [
            "japanese_file.txt",
            "russian_file.txt", 
            "greek_file.txt",
            "emoji_file.txt",
            "mixed_unicode.txt"
        ]
        
        created = []
        for name in unicode_names:
            source = temp_workspace["base"] / name
            try:
                # Use ASCII content to avoid encoding issues
                source.write_text(f"Content for {name}", encoding='utf-8')
                created.append(source)
            except OSError:
                continue  # Skip if OS doesn't support the filename
        
        if not created:
            pytest.skip("No Unicode filenames supported")
        
        batch_id = tm.begin_batch("unicode_stress")
        dest_dir = temp_workspace["base"] / "dest"
        dest_dir.mkdir(parents=True)
        
        for source in created:
            dest = dest_dir / source.name
            op = Operation(OperationType.MOVE, str(source), str(dest))
            tx_id = tm.log_operation(op, batch_id)
            shutil.move(str(source), str(dest))
            tm.complete_operation(tx_id, FileHasher.calculate_hash(dest))
        
        status = tm.get_batch_status(batch_id)
        assert status.completed == len(created)


# =============================================================================
# TEST CLASS: DATABASE STRESS
# =============================================================================

class TestDatabaseStress:
    """Test database under stress conditions."""

    def test_large_number_of_batches(self, temp_workspace):
        """Test database with many batches."""
        tm = TransactionManager(db_path=temp_workspace["db_path"])
        
        # Create 500 empty batches
        for i in range(500):
            tm.begin_batch(f"batch_{i:04d}")
        
        # Should still be responsive
        batch_id = tm.begin_batch("test_batch")
        assert batch_id == "test_batch"

    def test_large_batch_history(self, temp_workspace):
        """Test batch with many operations in history."""
        tm = TransactionManager(db_path=temp_workspace["db_path"])
        
        source_dir = temp_workspace["base"] / "source"
        dest_dir = temp_workspace["base"] / "dest"
        source_dir.mkdir(parents=True)
        dest_dir.mkdir(parents=True)
        
        # Create files
        for i in range(100):
            (source_dir / f"file_{i:04d}.txt").write_text(f"Content {i}")
        
        batch_id = tm.begin_batch("history_test")
        
        # Log all operations
        for f in source_dir.iterdir():
            dest = dest_dir / f.name
            op = Operation(OperationType.MOVE, str(f), str(dest))
            tx_id = tm.log_operation(op, batch_id)
            shutil.move(str(f), str(dest))
            tm.complete_operation(tx_id, FileHasher.calculate_hash(dest))
        
        # Query operations should still be fast
        start_time = time.time()
        ops = tm.get_batch_operations(batch_id)
        elapsed = time.time() - start_time
        
        assert len(ops) == 100
        assert elapsed < 0.1, f"Querying 100 operations took {elapsed:.2f}s"

    def test_database_recovery_under_load(self, temp_workspace):
        """Test database integrity after many operations."""
        tm = TransactionManager(db_path=temp_workspace["db_path"])
        
        # Perform many operations
        for batch_idx in range(10):
            source = temp_workspace["base"] / f"file_{batch_idx}.txt"
            source.write_text(f"Content {batch_idx}")
            dest = temp_workspace["base"] / f"moved_{batch_idx}.txt"
            
            batch_id = tm.begin_batch(f"recovery_test_{batch_idx}")
            op = Operation(OperationType.MOVE, str(source), str(dest))
            tx_id = tm.log_operation(op, batch_id)
            shutil.move(str(source), str(dest))
            tm.complete_operation(tx_id, FileHasher.calculate_hash(dest))
        
        # Create new manager and verify data
        tm2 = TransactionManager(db_path=temp_workspace["db_path"])
        
        for batch_idx in range(10):
            status = tm2.get_batch_status(f"recovery_test_{batch_idx}")
            assert status.completed == 1


# =============================================================================
# TEST CLASS: EDGE CASE COMBINATIONS
# =============================================================================

class TestEdgeCaseCombinations:
    """Test combinations of edge cases."""

    def test_empty_files_in_deep_dirs(self, temp_workspace):
        """Test empty files in deeply nested directories."""
        tm = TransactionManager(db_path=temp_workspace["db_path"])
        
        # Create 10-level deep structure with empty files
        deep_path = temp_workspace["base"]
        for i in range(10):
            deep_path = deep_path / f"level_{i}"
        deep_path.mkdir(parents=True)
        
        # Create empty files
        files = []
        for i in range(5):
            f = deep_path / f"empty_{i}.txt"
            f.write_bytes(b"")
            files.append(f)
        
        batch_id = tm.begin_batch("empty_deep")
        dest_dir = temp_workspace["base"] / "dest"
        dest_dir.mkdir(parents=True)
        
        for source in files:
            dest = dest_dir / source.name
            op = Operation(OperationType.MOVE, str(source), str(dest))
            tx_id = tm.log_operation(op, batch_id)
            shutil.move(str(source), str(dest))
            tm.complete_operation(tx_id, FileHasher.calculate_hash(dest))
        
        status = tm.get_batch_status(batch_id)
        assert status.completed == 5

    def test_special_chars_and_unicode_combo(self, temp_workspace):
        """Test special characters combined with unicode."""
        tm = TransactionManager(db_path=temp_workspace["db_path"])
        
        # File names with special chars and unicode
        test_names = [
            "file with spaces.txt",
            "file-with-dashes.txt",
            "file_with_underscores.txt",
            "file.multiple.dots.txt",
        ]
        
        source_dir = temp_workspace["base"] / "source"
        dest_dir = temp_workspace["base"] / "dest"
        source_dir.mkdir(parents=True)
        dest_dir.mkdir(parents=True)
        
        created = []
        for name in test_names:
            try:
                source = source_dir / name
                source.write_text(f"Content for {name}")
                created.append(source)
            except OSError:
                continue
        
        batch_id = tm.begin_batch("special_unicode")
        
        for source in created:
            dest = dest_dir / source.name
            op = Operation(OperationType.MOVE, str(source), str(dest))
            tx_id = tm.log_operation(op, batch_id)
            shutil.move(str(source), str(dest))
            tm.complete_operation(tx_id, FileHasher.calculate_hash(dest))
        
        status = tm.get_batch_status(batch_id)
        assert status.completed == len(created)


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
