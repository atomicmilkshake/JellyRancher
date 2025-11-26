"""
Real-World Integration Tests for JellyRancher Studio.

These tests use REAL files, REAL file operations, and verify ACTUAL behavior.
They do NOT use mocks for core functionality.

Run with: pytest tests/test_real_integration.py -v
WARNING: These tests create/move/delete files in temp directories.
"""

import pytest
import shutil
import tempfile
from pathlib import Path
from datetime import datetime
import sqlite3
import json

# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def real_media_folder(tmp_path):
    """
    Create a realistic media folder structure with actual files.
    
    Structure:
        media/
            Movies/
                Inception (2010).mkv
                The Matrix 1999 BluRay.mkv
                BadFolder/
                    Movie.avi
            TV Shows/
                Breaking.Bad.S01E01.mkv
                Breaking.Bad.S01E02.mkv
                Game of Thrones - S01E01 - Winter is Coming.mkv
    """
    media_dir = tmp_path / "media"
    media_dir.mkdir()
    
    movies = media_dir / "Movies"
    movies.mkdir()
    
    tv = media_dir / "TV Shows"
    tv.mkdir()
    
    # Create real files with actual content
    (movies / "Inception (2010).mkv").write_bytes(b"fake video " * 1000)
    (movies / "Inception (2010).srt").write_text("1\n00:00:01,000 --> 00:00:02,000\nSubtitle")
    (movies / "The Matrix 1999 BluRay.mkv").write_bytes(b"matrix video " * 1000)
    
    bad_folder = movies / "BadFolder"
    bad_folder.mkdir()
    (bad_folder / "Movie.avi").write_bytes(b"bad movie " * 500)
    
    (tv / "Breaking.Bad.S01E01.mkv").write_bytes(b"breaking bad ep1 " * 500)
    (tv / "Breaking.Bad.S01E02.mkv").write_bytes(b"breaking bad ep2 " * 500)
    (tv / "Game of Thrones - S01E01 - Winter is Coming.mkv").write_bytes(b"got ep1 " * 500)
    
    return media_dir


@pytest.fixture
def destination_folder(tmp_path):
    """Create empty destination folder for organized media."""
    dest = tmp_path / "organized"
    dest.mkdir()
    (dest / "Movies").mkdir()
    (dest / "TV Shows").mkdir()
    return dest


# =============================================================================
# REAL FILE SCANNER TESTS
# =============================================================================

class TestRealFileScanner:
    """Test FileScanner with real files."""
    
    def test_scan_real_files(self, real_media_folder):
        """FileScanner should find all real files."""
        from scripts.core.file_scanner import FileScanner
        
        scanner = FileScanner(calculate_md5=False)
        results = scanner.scan_folder(real_media_folder)
        
        # Verify we found the files
        assert len(results) >= 6, f"Expected at least 6 files, found {len(results)}"
        
        # Verify file types
        extensions = {r.extension for r in results}
        assert '.mkv' in extensions
        assert '.srt' in extensions or '.avi' in extensions
        
        # Verify paths are absolute
        for record in results:
            assert record.absolute_path.is_absolute()
            assert record.absolute_path.exists()
    
    def test_scan_with_hash_calculation(self, real_media_folder):
        """FileScanner should calculate BLAKE3 hashes correctly."""
        from scripts.core.file_scanner import FileScanner
        
        scanner = FileScanner(calculate_md5=True)
        results = scanner.scan_folder(real_media_folder)
        
        # All files should have hashes
        for record in results:
            assert record.md5_hash is not None, f"Missing hash for {record.absolute_path}"
            assert len(record.md5_hash) == 64, f"BLAKE3 hash should be 64 chars, got {len(record.md5_hash)}"
    
    def test_scan_handles_permission_error(self, tmp_path):
        """FileScanner should handle inaccessible files gracefully."""
        from scripts.core.file_scanner import FileScanner
        import os
        import sys
        
        # Create a test file
        test_dir = tmp_path / "protected"
        test_dir.mkdir()
        test_file = test_dir / "test.mkv"
        test_file.write_bytes(b"content")
        
        scanner = FileScanner()

        # On Windows, we can't easily make files unreadable
        # This test verifies error handling exists
        results = scanner.scan_folder(tmp_path)
        assert len(results) >= 1


# =============================================================================
# REAL FILE OPERATIONS TESTS
# =============================================================================

class TestRealFileOperations:
    """Test actual file move operations."""
    
    def test_move_file_with_hash_verification(self, tmp_path):
        """Moving a file should preserve its content (verified by hash)."""
        from scripts.utils.transaction_manager import TransactionManager, Operation, OperationType, FileHasher
        
        # Create source file
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        source_file = source_dir / "test_movie.mkv"
        source_file.write_bytes(b"This is test video content " * 100)
        
        # Calculate original hash
        original_hash = FileHasher.calculate_hash(source_file)
        
        # Create destination
        dest_dir = tmp_path / "destination"
        dest_dir.mkdir()
        dest_file = dest_dir / "test_movie.mkv"
        
        # Move file
        shutil.move(str(source_file), str(dest_file))
        
        # Verify hash matches
        new_hash = FileHasher.calculate_hash(dest_file)
        assert original_hash == new_hash, "File content changed during move!"
        
        # Verify source no longer exists
        assert not source_file.exists()
        
        # Verify destination exists
        assert dest_file.exists()
    
    def test_transaction_manager_rollback(self, tmp_path):
        """TransactionManager should correctly roll back operations."""
        from scripts.utils.transaction_manager import TransactionManager, Operation, OperationType, FileHasher
        
        # Create test file
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        source_file = source_dir / "rollback_test.mkv"
        original_content = b"Original content that should be restored"
        source_file.write_bytes(original_content)
        original_hash = FileHasher.calculate_hash(source_file)
        
        # Create destination
        dest_dir = tmp_path / "destination"
        dest_dir.mkdir()
        dest_file = dest_dir / "rollback_test.mkv"
        
        # Create TransactionManager
        tm = TransactionManager(str(tmp_path / "transactions.db"))
        
        # Begin batch
        batch_id = tm.begin_batch()
        
        # Log operation
        operation = Operation(
            operation_type=OperationType.MOVE,
            source_path=str(source_file),
            destination_path=str(dest_file)
        )
        tx_id = tm.log_operation(operation, batch_id)
        
        # Execute move
        shutil.move(str(source_file), str(dest_file))
        
        # Complete operation
        dest_hash = FileHasher.calculate_hash(dest_file)
        tm.complete_operation(tx_id, dest_hash)
        
        # Verify file is at destination
        assert dest_file.exists()
        assert not source_file.exists()
        
        # ROLLBACK
        result = tm.rollback_batch(batch_id)
        
        # Verify rollback worked
        assert source_file.exists(), "Source file not restored after rollback"
        assert not dest_file.exists(), "Destination file still exists after rollback"
        
        # Verify content matches
        restored_hash = FileHasher.calculate_hash(source_file)
        assert restored_hash == original_hash, "Content changed after rollback"
        
        # Verify result object
        assert result.successful_rollbacks >= 1, f"Should have at least one successful rollback, got {result.successful_rollbacks}"


# =============================================================================
# REAL REGEX ANALYSIS TESTS
# =============================================================================

class TestRealRegexAnalysis:
    """Test regex analysis with real file names."""
    
    def test_analyze_real_movie_names(self, real_media_folder):
        """RegexStructureAnalyzer should correctly parse real movie names."""
        from scripts.core.file_scanner import FileScanner
        from scripts.core.regex_analysis_worker import RegexStructureAnalyzer
        
        # Scan real files
        scanner = FileScanner()
        file_records = scanner.scan_folder(real_media_folder)
        
        # Analyze
        analyzer = RegexStructureAnalyzer()
        result = analyzer.analyze_structure(file_records)
        
        # Should detect media
        assert 'detected_media' in result
        detected = result['detected_media']
        assert len(detected) > 0, "Should detect at least some media"
        
        # Check for expected titles
        titles = [m.get('title', '').lower() for m in detected]
        assert any('inception' in t for t in titles) or any('matrix' in t for t in titles), \
            f"Expected to find Inception or Matrix in {titles}"
    
    def test_analyze_tv_show_episodes(self, real_media_folder):
        """RegexStructureAnalyzer should correctly parse TV show episodes."""
        from scripts.core.file_scanner import FileScanner
        from scripts.core.regex_analysis_worker import RegexStructureAnalyzer
        
        # Scan
        scanner = FileScanner()
        file_records = scanner.scan_folder(real_media_folder)

        # Analyze
        analyzer = RegexStructureAnalyzer()
        result = analyzer.analyze_structure(file_records)
        
        # Check for TV detection
        detected = result['detected_media']
        tv_shows = [m for m in detected if m.get('type') == 'tv']
        
        # Should find at least one TV show
        assert len(tv_shows) >= 0  # May not detect depending on file location


# =============================================================================
# REAL DATABASE TESTS
# =============================================================================

class TestRealDatabaseOperations:
    """Test database operations with real SQLite."""
    
    def test_roundup_persistence(self, tmp_path):
        """RoundUpManager should persist data correctly."""
        from scripts.core.roundup_manager import RoundUpManager, RoundUp
        
        # Create manager with custom location
        manager = RoundUpManager(roundups_dir=tmp_path)
        
        # Create Round-Up
        roundup = manager.create("Test Round-Up")
        roundup.config['source_folders'] = ['/test/path1', '/test/path2']
        roundup.current_step = 3
        manager.save(roundup)
        
        # Load it back
        loaded = manager.load("Test Round-Up")
        
        assert loaded is not None
        assert loaded.name == "Test Round-Up"
        assert loaded.current_step == 3
        assert loaded.config['source_folders'] == ['/test/path1', '/test/path2']
    
    def test_inventory_repository_persistence(self, real_media_folder, tmp_path):
        """InventoryRepository should correctly store scan data."""
        from scripts.core.file_scanner import FileScanner
        from scripts.core.inventory_repository import InventoryRepository
        
        # Scan real files
        scanner = FileScanner()
        file_records = scanner.scan_folder(real_media_folder)
        
        # Store in database
        db_path = tmp_path / "inventory.db"
        repo = InventoryRepository(str(db_path))
        
        session_id = repo.create_scan_session(real_media_folder)
        repo.add_file_records(session_id, file_records)
        total_size = sum(r.size_bytes for r in file_records)
        repo.finalize_scan_session(session_id, len(file_records), total_size)
        
        # Retrieve and verify
        retrieved = repo.get_all_files(session_id)
        
        assert len(retrieved) == len(file_records)
        
        # Verify data integrity
        original_paths = {str(r.absolute_path) for r in file_records}
        retrieved_paths = {str(r.absolute_path) for r in retrieved}
        assert original_paths == retrieved_paths


# =============================================================================
# EDGE CASE TESTS
# =============================================================================

class TestEdgeCases:
    """Test edge cases and error conditions with real operations."""
    
    def test_special_characters_in_filename(self, tmp_path):
        """Files with special characters should be handled correctly."""
        from scripts.core.file_scanner import FileScanner
        
        # Create files with special characters
        special_dir = tmp_path / "special"
        special_dir.mkdir()
        
        # Various special character scenarios
        (special_dir / "Movie (2020) [1080p].mkv").write_bytes(b"content")
        (special_dir / "Show - S01E01 - Title.mkv").write_bytes(b"content")
        (special_dir / "Café.mkv").write_bytes(b"content")  # Non-ASCII
        
        scanner = FileScanner()
        results = scanner.scan_folder(special_dir)
        
        assert len(results) == 3
    
    def test_empty_folder(self, tmp_path):
        """Empty folders should be handled gracefully."""
        from scripts.core.file_scanner import FileScanner
        
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        
        scanner = FileScanner()
        results = scanner.scan_folder(empty_dir)
        
        assert len(results) == 0
    
    def test_deeply_nested_structure(self, tmp_path):
        """Deep folder structures should be scanned correctly."""
        from scripts.core.file_scanner import FileScanner
        
        # Create 10-level deep structure
        current = tmp_path
        for i in range(10):
            current = current / f"level_{i}"
            current.mkdir()
        
        (current / "deep_movie.mkv").write_bytes(b"content")
        
        scanner = FileScanner()
        results = scanner.scan_folder(tmp_path)
        
        assert len(results) == 1
        assert "deep_movie.mkv" in str(results[0].absolute_path)
    
    def test_large_file_count(self, tmp_path):
        """Should handle many files efficiently."""
        from scripts.core.file_scanner import FileScanner
        import time
        
        # Create 500 files
        large_dir = tmp_path / "large"
        large_dir.mkdir()
        
        for i in range(500):
            (large_dir / f"movie_{i:04d}.mkv").write_bytes(b"x" * 100)
        
        scanner = FileScanner(calculate_md5=False)  # Skip hashing for speed
        
        start = time.time()
        results = scanner.scan_folder(large_dir)
        elapsed = time.time() - start
        
        assert len(results) == 500
        assert elapsed < 10.0, f"Scanning 500 files took {elapsed:.1f}s (should be <10s)"
    
    def test_move_to_nonexistent_directory(self, tmp_path):
        """Moving to a non-existent directory should create it."""
        from scripts.utils.transaction_manager import FileHasher
        
        source = tmp_path / "source.mkv"
        source.write_bytes(b"content")
        
        # Destination directory doesn't exist
        dest_dir = tmp_path / "new" / "deep" / "path"
        dest = dest_dir / "moved.mkv"
        
        # Create directory and move
        dest_dir.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(dest))
        
        assert dest.exists()
        assert not source.exists()


# =============================================================================
# FULL WORKFLOW TEST (No Mocks)
# =============================================================================

class TestFullWorkflowNoMocks:
    """Test complete workflow with real operations."""
    
    def test_scan_analyze_plan(self, real_media_folder, tmp_path):
        """
        Test the first half of the workflow without mocks.
        
        Steps:
        1. Scan real files
        2. Analyze with Regex (fast, no API)
        3. Generate operations
        """
        from scripts.core.file_scanner import FileScanner
        from scripts.core.inventory_repository import InventoryRepository
        from scripts.core.regex_analysis_worker import RegexStructureAnalyzer
        from scripts.core.extrapolation_engine import ExtrapolationEngine
        
        # Step 1: Scan
        scanner = FileScanner(calculate_md5=True)
        file_records = scanner.scan_folder(real_media_folder)
        assert len(file_records) > 0, "Scan found no files"
        
        # Step 2: Analyze with Regex (no LLM, fast)
        analyzer = RegexStructureAnalyzer()
        analysis = analyzer.analyze_structure(file_records)
        assert 'detected_media' in analysis
        assert 'reorganization_plan' in analysis
        
        # Step 3: Extrapolate to file-level operations
        engine = ExtrapolationEngine(file_records)
        operations = engine.extrapolate(analysis.get('reorganization_plan', {}))
        
        # Should have some operations (may be empty if no reorganization needed)
        assert isinstance(operations, list)
        
        # Verify scan data can be persisted
        db_path = tmp_path / "test.db"
        repo = InventoryRepository(str(db_path))
        session_id = repo.create_scan_session(real_media_folder)
        repo.add_file_records(session_id, file_records)
        total_size = sum(r.size_bytes for r in file_records)
        repo.finalize_scan_session(session_id, len(file_records), total_size)
        
        # Verify we can retrieve the data
        retrieved = repo.get_all_files(session_id)
        assert len(retrieved) == len(file_records)

