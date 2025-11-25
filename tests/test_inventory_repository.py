"""
Tests for InventoryRepository.

Function Index Queries:
- search "inventory repository database sqlite file record save get" -> Found InventoryRepository
  __init__ at scripts/core/inventory_repository.py:40 (used for context)
- search "sqlite connection context" -> Found _get_connection pattern in roundup_manager.py
  (used as reference for context manager testing)

KNOWN ISSUE: The database schema in _initialize_database() does not include jellyfin_id and
jellyfin_provider_ids columns, but add_file_records() and get_all_files() try to use them.
This causes OperationalError when testing file record operations. The migration script
migrate_db_for_jellyfin.py adds these columns, but they should be in the base schema.

Coverage Target: 80%+ line coverage (Tier 1: Core Backend)
"""
import pytest
from pathlib import Path
from datetime import datetime
import sqlite3

from scripts.core.inventory_repository import InventoryRepository
from scripts.core.file_scanner import FileRecord


def make_file_record(path: Path, extension: str = ".mkv", size: int = 1000, md5: str = None) -> FileRecord:
    """Helper to create FileRecord instances."""
    return FileRecord(
        absolute_path=path,
        size_bytes=size,
        extension=extension,
        parent_folder=path.parent,
        scan_timestamp=datetime.now(),
        md5_hash=md5
    )


@pytest.fixture
def repo_with_jellyfin_schema(tmp_path):
    """Create InventoryRepository and add missing Jellyfin columns to schema."""
    repo = InventoryRepository(str(tmp_path / "inventory.db"))
    
    # Add missing Jellyfin columns (schema bug workaround)
    with repo._get_connection() as conn:
        cursor = conn.cursor()
        # Check if columns exist
        cursor.execute("PRAGMA table_info(files)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'jellyfin_id' not in columns:
            cursor.execute("ALTER TABLE files ADD COLUMN jellyfin_id TEXT")
        if 'jellyfin_provider_ids' not in columns:
            cursor.execute("ALTER TABLE files ADD COLUMN jellyfin_provider_ids TEXT")
    
    return repo


class TestInventoryRepositoryInit:
    """Tests for InventoryRepository initialization."""
    
    @pytest.mark.unit
    def test_init_creates_database(self, tmp_path):
        """Should create database file if it doesn't exist."""
        db_path = tmp_path / "inventory.db"
        repo = InventoryRepository(str(db_path))
        
        assert db_path.exists()
        assert repo.db_path == db_path
    
    @pytest.mark.unit
    def test_init_creates_parent_directory(self, tmp_path):
        """Should create parent directory if it doesn't exist."""
        db_path = tmp_path / "data" / "inventory.db"
        repo = InventoryRepository(str(db_path))
        
        assert db_path.parent.exists()
        assert db_path.exists()
    
    @pytest.mark.unit
    def test_init_raises_on_invalid_db_path(self):
        """Should raise ValueError for invalid db_path."""
        with pytest.raises(ValueError, match="Invalid db_path"):
            InventoryRepository("")
        
        with pytest.raises(ValueError, match="Invalid db_path"):
            InventoryRepository(None)
    
    @pytest.mark.unit
    def test_init_initializes_schema(self, tmp_path):
        """Should create tables and indexes on initialization."""
        db_path = tmp_path / "inventory.db"
        repo = InventoryRepository(str(db_path))
        
        with repo._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            assert 'files' in tables
            assert 'scan_sessions' in tables
            
            # Check indexes
            cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
            indexes = [row[0] for row in cursor.fetchall()]
            
            assert 'idx_files_parent_folder' in indexes
            assert 'idx_files_extension' in indexes
            assert 'idx_files_scan_session' in indexes


class TestInventoryRepositoryConnection:
    """Tests for _get_connection context manager."""
    
    @pytest.mark.unit
    def test_get_connection_context_manager(self, tmp_path):
        """Should provide connection as context manager."""
        repo = InventoryRepository(str(tmp_path / "inventory.db"))
        
        with repo._get_connection() as conn:
            assert isinstance(conn, sqlite3.Connection)
            assert conn.row_factory == sqlite3.Row
        
        # Connection should be closed outside context
        with pytest.raises(sqlite3.ProgrammingError):
            conn.execute("SELECT 1")
    
    @pytest.mark.unit
    def test_get_connection_auto_commits(self, tmp_path):
        """Should auto-commit on successful exit."""
        repo = InventoryRepository(str(tmp_path / "inventory.db"))
        
        with repo._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO scan_sessions (root_folder, scan_start) VALUES (?, ?)",
                          ("/test", datetime.now().isoformat()))
        
        # Verify data persisted (commit happened)
        with repo._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM scan_sessions")
            assert cursor.fetchone()['count'] == 1


class TestInventoryRepositoryScanSessions:
    """Tests for scan session management."""
    
    @pytest.mark.unit
    def test_create_scan_session(self, tmp_path):
        """Should create a new scan session."""
        repo = InventoryRepository(str(tmp_path / "inventory.db"))
        
        session_id = repo.create_scan_session(Path("/test/folder"), recursive=True, notes="Test scan")
        
        assert isinstance(session_id, int)
        assert session_id > 0
    
    @pytest.mark.unit
    def test_create_scan_session_with_string_path(self, tmp_path):
        """Should accept string path for root_folder."""
        repo = InventoryRepository(str(tmp_path / "inventory.db"))
        
        session_id = repo.create_scan_session("/test/folder")
        
        assert session_id > 0
    
    @pytest.mark.unit
    def test_create_scan_session_raises_on_invalid_input(self, tmp_path):
        """Should raise TypeError for invalid root_folder."""
        repo = InventoryRepository(str(tmp_path / "inventory.db"))
        
        with pytest.raises(TypeError):
            repo.create_scan_session(None)
    
    @pytest.mark.integration
    def test_finalize_scan_session(self, tmp_path):
        """Should update scan session with statistics."""
        repo = InventoryRepository(str(tmp_path / "inventory.db"))
        
        session_id = repo.create_scan_session(Path("/test"))
        repo.finalize_scan_session(session_id, total_files=10, total_size_bytes=1000, error_count=0)
        
        with repo._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT total_files, total_size_bytes, error_count, scan_end FROM scan_sessions WHERE id = ?",
                          (session_id,))
            row = cursor.fetchone()
            
            assert row['total_files'] == 10
            assert row['total_size_bytes'] == 1000
            assert row['error_count'] == 0
            assert row['scan_end'] is not None


class TestInventoryRepositoryFileRecords:
    """Tests for file record operations."""
    
    @pytest.mark.integration
    def test_add_file_records(self, repo_with_jellyfin_schema, tmp_path):
        """Should add file records to database."""
        repo = repo_with_jellyfin_schema
        session_id = repo.create_scan_session(Path("/test"))
        
        file1 = tmp_path / "movie1.mkv"
        file2 = tmp_path / "movie2.mkv"
        file1.write_bytes(b"content1")
        file2.write_bytes(b"content2")
        
        records = [
            make_file_record(file1, ".mkv", 100),
            make_file_record(file2, ".mkv", 200)
        ]
        
        repo.add_file_records(session_id, records)
        
        all_files = repo.get_all_files(session_id)
        assert len(all_files) == 2
        assert all(isinstance(f, FileRecord) for f in all_files)
    
    @pytest.mark.integration
    def test_add_file_records_empty_list(self, repo_with_jellyfin_schema):
        """Should handle empty file_records list gracefully."""
        repo = repo_with_jellyfin_schema
        session_id = repo.create_scan_session(Path("/test"))
        
        # Should not raise
        repo.add_file_records(session_id, [])
        
        all_files = repo.get_all_files(session_id)
        assert len(all_files) == 0
    
    @pytest.mark.integration
    def test_add_file_records_raises_on_invalid_session_id(self, tmp_path):
        """Should raise ValueError for invalid session_id."""
        repo = InventoryRepository(str(tmp_path / "inventory.db"))
        
        file1 = tmp_path / "test.mkv"
        file1.write_bytes(b"content")
        records = [make_file_record(file1)]
        
        with pytest.raises(ValueError, match="Invalid session_id"):
            repo.add_file_records(0, records)
        
        with pytest.raises(ValueError, match="Invalid session_id"):
            repo.add_file_records(-1, records)
    
    @pytest.mark.integration
    def test_add_file_records_raises_on_invalid_type(self, tmp_path):
        """Should raise TypeError for non-list file_records."""
        repo = InventoryRepository(str(tmp_path / "inventory.db"))
        session_id = repo.create_scan_session(Path("/test"))
        
        with pytest.raises(TypeError, match="must be a list"):
            repo.add_file_records(session_id, "not a list")
    
    @pytest.mark.integration
    def test_get_all_files_with_session_id(self, repo_with_jellyfin_schema, tmp_path):
        """Should return files filtered by session_id."""
        repo = repo_with_jellyfin_schema
        
        session1 = repo.create_scan_session(Path("/test1"))
        session2 = repo.create_scan_session(Path("/test2"))
        
        file1 = tmp_path / "file1.mkv"
        file2 = tmp_path / "file2.mkv"
        file1.write_bytes(b"content1")
        file2.write_bytes(b"content2")
        
        repo.add_file_records(session1, [make_file_record(file1)])
        repo.add_file_records(session2, [make_file_record(file2)])
        
        files1 = repo.get_all_files(session1)
        files2 = repo.get_all_files(session2)
        
        assert len(files1) == 1
        assert len(files2) == 1
        assert files1[0].absolute_path == file1
        assert files2[0].absolute_path == file2
    
    @pytest.mark.integration
    def test_get_all_files_without_session_id(self, repo_with_jellyfin_schema, tmp_path):
        """Should return all files when session_id is None."""
        repo = repo_with_jellyfin_schema
        
        session1 = repo.create_scan_session(Path("/test1"))
        session2 = repo.create_scan_session(Path("/test2"))
        
        file1 = tmp_path / "file1.mkv"
        file2 = tmp_path / "file2.mkv"
        file1.write_bytes(b"content1")
        file2.write_bytes(b"content2")
        
        repo.add_file_records(session1, [make_file_record(file1)])
        repo.add_file_records(session2, [make_file_record(file2)])
        
        all_files = repo.get_all_files()
        
        assert len(all_files) == 2


class TestInventoryRepositoryQueries:
    """Tests for query methods."""
    
    @pytest.mark.integration
    def test_get_files_by_folder(self, repo_with_jellyfin_schema, tmp_path):
        """Should return files from specific folder."""
        repo = repo_with_jellyfin_schema
        session_id = repo.create_scan_session(Path("/test"))
        
        folder1 = tmp_path / "movies"
        folder2 = tmp_path / "tv"
        folder1.mkdir()
        folder2.mkdir()
        
        file1 = folder1 / "movie1.mkv"
        file2 = folder1 / "movie2.mkv"
        file3 = folder2 / "episode1.mkv"
        
        file1.write_bytes(b"content1")
        file2.write_bytes(b"content2")
        file3.write_bytes(b"content3")
        
        repo.add_file_records(session_id, [
            make_file_record(file1),
            make_file_record(file2),
            make_file_record(file3)
        ])
        
        movies = repo.get_files_by_folder(folder1, recursive=False)
        assert len(movies) == 2
        
        all_movies = repo.get_files_by_folder(folder1, recursive=True)
        assert len(all_movies) == 2
    
    @pytest.mark.integration
    def test_get_files_by_extension(self, repo_with_jellyfin_schema, tmp_path):
        """Should return files with specific extensions."""
        repo = repo_with_jellyfin_schema
        session_id = repo.create_scan_session(Path("/test"))
        
        file1 = tmp_path / "movie.mkv"
        file2 = tmp_path / "subtitle.srt"
        file3 = tmp_path / "image.jpg"
        
        file1.write_bytes(b"content1")
        file2.write_text("subtitle")
        file3.write_bytes(b"image")
        
        repo.add_file_records(session_id, [
            make_file_record(file1, ".mkv"),
            make_file_record(file2, ".srt"),
            make_file_record(file3, ".jpg")
        ])
        
        videos = repo.get_files_by_extension([".mkv", ".mp4"])
        assert len(videos) == 1
        assert videos[0].extension == ".mkv"
    
    @pytest.mark.integration
    def test_get_folder_statistics(self, repo_with_jellyfin_schema, tmp_path):
        """Should return aggregated folder statistics."""
        repo = repo_with_jellyfin_schema
        session_id = repo.create_scan_session(Path("/test"))
        
        folder = tmp_path / "movies"
        folder.mkdir()
        
        file1 = folder / "movie1.mkv"
        file2 = folder / "movie2.mkv"
        file1.write_bytes(b"content1")
        file2.write_bytes(b"content2")
        
        repo.add_file_records(session_id, [
            make_file_record(file1, ".mkv", 100),
            make_file_record(file2, ".mkv", 200)
        ])
        
        stats = repo.get_folder_statistics()
        
        assert str(folder) in stats
        folder_stat = stats[str(folder)]
        assert folder_stat['file_count'] == 2
        assert folder_stat['total_size'] == 300
        assert '.mkv' in folder_stat['extensions']
        assert folder_stat['extensions']['.mkv'] == 2
    
    @pytest.mark.integration
    def test_get_scan_history(self, tmp_path):
        """Should return recent scan history."""
        repo = InventoryRepository(str(tmp_path / "inventory.db"))
        
        session1 = repo.create_scan_session(Path("/test1"), notes="First scan")
        session2 = repo.create_scan_session(Path("/test2"), notes="Second scan")
        
        history = repo.get_scan_history(limit=10)
        
        assert len(history) == 2
        # Path comparison should be platform-agnostic
        assert Path(history[0]['root_folder']) == Path("/test2")  # Most recent first
        assert Path(history[1]['root_folder']) == Path("/test1")
        assert history[0]['notes'] == "Second scan"
    
    @pytest.mark.integration
    def test_get_database_statistics(self, repo_with_jellyfin_schema, tmp_path):
        """Should return overall database statistics."""
        repo = repo_with_jellyfin_schema
        session_id = repo.create_scan_session(Path("/test"))
        
        file1 = tmp_path / "movie.mkv"
        file1.write_bytes(b"content")
        
        repo.add_file_records(session_id, [make_file_record(file1, ".mkv", 1000)])
        repo.finalize_scan_session(session_id, total_files=1, total_size_bytes=1000)
        
        stats = repo.get_database_statistics()
        
        assert stats['total_files'] == 1
        assert stats['total_size_bytes'] == 1000
        assert stats['total_scan_sessions'] == 1
        assert '.mkv' in stats['top_extensions']
        assert stats['top_extensions']['.mkv'] == 1


class TestInventoryRepositoryDataManagement:
    """Tests for data management operations."""
    
    @pytest.mark.integration
    def test_clear_all_data(self, repo_with_jellyfin_schema, tmp_path):
        """Should clear all files and scan sessions."""
        repo = repo_with_jellyfin_schema
        session_id = repo.create_scan_session(Path("/test"))
        
        file1 = tmp_path / "test.mkv"
        file1.write_bytes(b"content")
        
        repo.add_file_records(session_id, [make_file_record(file1)])
        
        # Verify data exists
        assert len(repo.get_all_files()) == 1
        assert len(repo.get_scan_history()) == 1
        
        # Clear data
        repo.clear_all_data()
        
        # Verify data cleared
        assert len(repo.get_all_files()) == 0
        assert len(repo.get_scan_history()) == 0


class TestInventoryRepositoryJellyfinFields:
    """Tests for Jellyfin-related fields in file records."""
    
    @pytest.mark.integration
    def test_add_file_records_with_jellyfin_fields(self, repo_with_jellyfin_schema, tmp_path):
        """Should store Jellyfin ID and provider IDs."""
        repo = repo_with_jellyfin_schema
        session_id = repo.create_scan_session(Path("/test"))
        
        file1 = tmp_path / "movie.mkv"
        file1.write_bytes(b"content")
        
        record = make_file_record(file1)
        record.jellyfin_id = "jellyfin-123"
        record.jellyfin_provider_ids = {"tmdb": "456", "imdb": "tt789"}
        
        repo.add_file_records(session_id, [record])
        
        files = repo.get_all_files(session_id)
        assert len(files) == 1
        assert files[0].jellyfin_id == "jellyfin-123"
        assert files[0].jellyfin_provider_ids == {"tmdb": "456", "imdb": "tt789"}

