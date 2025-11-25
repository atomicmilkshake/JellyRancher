"""
Shared pytest fixtures and configuration for JellyRancher tests.

Function Index Queries:
- search "sample test fixture mock" -> Found existing fixtures in scripts/tests/conftest.py
- search "roundup create initialize" -> RoundUpManager API understood

This conftest.py consolidates all test fixtures for the project.
"""

import sys
import pytest
import tempfile
import shutil
import sqlite3
import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

# Add project root and all module directories to path
project_root = Path(__file__).parent.parent
paths_to_add = [
    project_root,
    project_root / "scripts",
    project_root / "scripts" / "core",
    project_root / "scripts" / "media",
    project_root / "scripts" / "utils",
    project_root / "scripts" / "_common",
]

for path in paths_to_add:
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)


# =============================================================================
# BASIC FIXTURES
# =============================================================================

@pytest.fixture
def temp_dir(tmp_path):
    """Provide a temporary directory for tests."""
    yield tmp_path
    # Cleanup is automatic with tmp_path


# =============================================================================
# MEDIA STRUCTURE FIXTURES
# =============================================================================

@pytest.fixture
def sample_movies_dir(tmp_path):
    """
    Create a sample Movies directory structure for testing.
    
    Structure:
        Movies/
            Movie A (2020)/
                Movie A (2020).mkv
                Movie A (2020).en.srt
            Movie B (2019) H.265 1080p.mkv (loose file with codec tags)
            BadFolder/
                Movie C (2018).mp4
    """
    movies_dir = tmp_path / "Movies"
    movies_dir.mkdir()
    
    # Proper structure with subtitle
    movie_a = movies_dir / "Movie A (2020)"
    movie_a.mkdir()
    (movie_a / "Movie A (2020).mkv").write_bytes(b"fake video content " * 100)
    (movie_a / "Movie A (2020).en.srt").write_text("1\n00:00:01,000 --> 00:00:02,000\nSubtitle")
    
    # File directly in Movies with codec tags
    (movies_dir / "Movie B (2019) H.265 1080p.mkv").write_bytes(b"fake video content " * 50)
    
    # File in wrong folder
    bad_folder = movies_dir / "BadFolder"
    bad_folder.mkdir()
    (bad_folder / "Movie C (2018).mp4").write_bytes(b"fake video content " * 30)
    
    return movies_dir


@pytest.fixture
def sample_tv_shows_dir(tmp_path):
    """
    Create a sample TV Shows directory structure for testing.
    
    Structure:
        TV Shows/
            Show A/
                Season 01/
                    Show A - S01E01 - Pilot.mkv
                    Show A - S01E01 - Pilot.en.srt
                    Show A - S01E02 - Second Episode.mkv
            Show B/
                Season 01/
                    S01E01 - Episode Title.mkv (missing show name)
    """
    tv_dir = tmp_path / "TV Shows"
    tv_dir.mkdir()
    
    # Show A - proper format
    show_a = tv_dir / "Show A"
    show_a.mkdir()
    season_1a = show_a / "Season 01"
    season_1a.mkdir()
    (season_1a / "Show A - S01E01 - Pilot.mkv").write_bytes(b"fake video " * 100)
    (season_1a / "Show A - S01E01 - Pilot.en.srt").write_text("1\n00:00:01,000 --> 00:00:02,000\nPilot")
    (season_1a / "Show A - S01E02 - Second Episode.mkv").write_bytes(b"fake video " * 100)
    
    # Show B - missing show name in filename
    show_b = tv_dir / "Show B"
    show_b.mkdir()
    season_1b = show_b / "Season 01"
    season_1b.mkdir()
    (season_1b / "S01E01 - Episode Title.mkv").write_bytes(b"fake video " * 50)
    
    return tv_dir


@pytest.fixture
def sample_mixed_media_dir(tmp_path):
    """
    Create a mixed media directory for comprehensive testing.
    
    Includes movies, TV shows, and edge cases.
    """
    media_dir = tmp_path / "Media"
    media_dir.mkdir()
    
    # Movies
    movies = media_dir / "Movies"
    movies.mkdir()
    (movies / "The Matrix (1999).mkv").write_bytes(b"x" * 1000)
    (movies / "Inception.2010.1080p.BluRay.mkv").write_bytes(b"x" * 2000)
    
    # TV Shows
    tv = media_dir / "TV"
    tv.mkdir()
    breaking_bad = tv / "Breaking Bad"
    breaking_bad.mkdir()
    s1 = breaking_bad / "Season 1"
    s1.mkdir()
    (s1 / "Breaking.Bad.S01E01.Pilot.mkv").write_bytes(b"x" * 500)
    (s1 / "Breaking.Bad.S01E02.Cats.in.the.Bag.mkv").write_bytes(b"x" * 500)
    
    # Edge cases
    misc = media_dir / "Unsorted"
    misc.mkdir()
    (misc / "random_video.avi").write_bytes(b"x" * 100)
    (misc / "Movie (2020) [1080p].mkv").write_bytes(b"x" * 100)
    
    return media_dir


# =============================================================================
# ROUND-UP FIXTURES
# =============================================================================

@pytest.fixture
def roundup_base_dir(tmp_path):
    """
    Provide a temporary base directory for Round-Up storage.
    
    Simulates ~/JellyRancher/roundups/ structure.
    """
    base = tmp_path / "JellyRancher" / "roundups"
    base.mkdir(parents=True)
    return base


@pytest.fixture
def sample_roundup_dir(roundup_base_dir):
    """
    Create a sample Round-Up directory structure.
    
    Structure:
        Test_Project.roundup/
            metadata.json
            config.json
            data.db (with schema initialized)
    """
    roundup_dir = roundup_base_dir / "Test_Project.roundup"
    roundup_dir.mkdir()
    
    # Create metadata.json
    metadata = {
        "name": "Test Project",
        "created_at": datetime.now().isoformat(),
        "last_modified": datetime.now().isoformat(),
        "current_step": 1,
        "step_status": {
            "1": "not_started", "2": "not_started", "3": "not_started", "4": "not_started",
            "5": "not_started", "6": "not_started", "7": "not_started", "8": "not_started"
        },
        "source_folders": [],
        "version": "1.0"
    }
    (roundup_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))
    
    # Create config.json
    config = {
        "analysis_mode": "hybrid",
        "llm_model": "grok-4-fast",
        "auto_approve_subtitles": True
    }
    (roundup_dir / "config.json").write_text(json.dumps(config, indent=2))
    
    # Create data.db with schema
    db_path = roundup_dir / "data.db"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Create tables matching RoundUpManager schema
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS scan_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT NOT NULL,
            filename TEXT NOT NULL,
            extension TEXT,
            size_bytes INTEGER,
            md5_hash TEXT,
            relative_path TEXT,
            created_at TEXT,
            metadata_json TEXT
        );
        
        CREATE TABLE IF NOT EXISTS structure_summary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            folder_path TEXT NOT NULL,
            file_count INTEGER,
            total_size INTEGER,
            file_types_json TEXT
        );
        
        CREATE TABLE IF NOT EXISTS analysis_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            analysis_mode TEXT,
            model_used TEXT,
            response_json TEXT,
            detected_media_json TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS structure_cache (
            id INTEGER PRIMARY KEY DEFAULT 1,
            folder_structure TEXT NOT NULL,
            duplicate_groups TEXT NOT NULL,
            scan_file_count INTEGER NOT NULL,
            cached_at TEXT NOT NULL
        );
    """)
    
    conn.commit()
    conn.close()
    
    return roundup_dir


@pytest.fixture
def roundup_manager(roundup_base_dir):
    """
    Create a RoundUpManager instance with temp storage.
    
    Returns a manager that stores Round-Ups in a temp directory.
    """
    from scripts.core.roundup_manager import RoundUpManager
    
    # Create manager with custom base path
    manager = RoundUpManager(base_path=roundup_base_dir)
    return manager


# =============================================================================
# DATABASE FIXTURES
# =============================================================================

@pytest.fixture
def in_memory_db():
    """Provide an in-memory SQLite database."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


@pytest.fixture
def sample_tmdb_cache(tmp_path):
    """Create a sample TMDB cache file for testing."""
    cache_data = {
        "show_name": "Test Show",
        "tmdb_id": 12345,
        "seasons": {
            "1": {
                "episodes": {
                    "1": {"name": "Pilot Episode", "season_number": 1, "episode_number": 1},
                    "2": {"name": "Second Episode", "season_number": 1, "episode_number": 2}
                }
            }
        }
    }
    
    cache_file = tmp_path / "test_cache.json"
    cache_file.write_text(json.dumps(cache_data, indent=2))
    return cache_file


# =============================================================================
# MOCK FIXTURES
# =============================================================================

@pytest.fixture
def mock_logger():
    """Provide a mock logger for tests."""
    class MockLogger:
        def __init__(self):
            self.messages = {'info': [], 'warning': [], 'error': [], 'debug': [], 'success': []}
        
        def info(self, msg): self.messages['info'].append(msg)
        def warning(self, msg): self.messages['warning'].append(msg)
        def error(self, msg): self.messages['error'].append(msg)
        def debug(self, msg): self.messages['debug'].append(msg)
        def success(self, msg): self.messages['success'].append(msg)
        def clear(self):
            for key in self.messages:
                self.messages[key] = []
    
    return MockLogger()


@pytest.fixture
def mock_audit_log():
    """Provide a mock audit log for tests."""
    class MockAuditLog:
        def __init__(self):
            self.events = []
        
        def log_event(self, event_type, data):
            self.events.append({'type': event_type, 'data': data})
        
        def clear(self):
            self.events = []
    
    return MockAuditLog()


# =============================================================================
# FILE RECORD FIXTURES
# =============================================================================

@pytest.fixture
def sample_file_records(sample_mixed_media_dir):
    """
    Create sample FileRecord objects from mixed media directory.
    
    Returns a list of FileRecord-like dicts (for testing without FileScanner dependency).
    """
    records = []
    for file_path in sample_mixed_media_dir.rglob("*"):
        if file_path.is_file():
            records.append({
                "absolute_path": file_path,
                "filename": file_path.name,
                "extension": file_path.suffix.lower(),
                "size_bytes": file_path.stat().st_size,
                "parent_folder": file_path.parent,
                "md5_hash": None,  # Not calculated by default
            })
    return records


# =============================================================================
# PYTEST CONFIGURATION
# =============================================================================

@pytest.fixture(autouse=True)
def reset_sys_path():
    """Reset sys.path after each test to avoid pollution."""
    original_path = sys.path.copy()
    yield
    sys.path = original_path


def pytest_configure(config):
    """Configure custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests (fast, no external I/O)")
    config.addinivalue_line("markers", "integration: Integration tests (filesystem, database)")
    config.addinivalue_line("markers", "slow: Slow tests (skipped by default)")
    config.addinivalue_line("markers", "requires_gui: Tests requiring PyQt6 GUI")
    config.addinivalue_line("markers", "requires_network: Tests requiring network access")


def pytest_collection_modifyitems(config, items):
    """Automatically skip certain tests based on environment."""
    skip_gui = pytest.mark.skip(reason="PyQt6 not available or headless environment")
    skip_network = pytest.mark.skip(reason="Network access not available")
    skip_slow = pytest.mark.skip(reason="Slow test (use --run-slow to run)")
    
    for item in items:
        # Skip GUI tests if PyQt6 not available
        if "requires_gui" in item.keywords:
            try:
                import PyQt6
            except ImportError:
                item.add_marker(skip_gui)
        
        # Skip network tests if --no-network flag is set
        if "requires_network" in item.keywords:
            if config.getoption("--no-network", default=False):
                item.add_marker(skip_network)
        
        # Skip slow tests unless --run-slow is set
        if "slow" in item.keywords:
            if not config.getoption("--run-slow", default=False):
                item.add_marker(skip_slow)


def pytest_addoption(parser):
    """Add custom command-line options."""
    parser.addoption(
        "--no-network",
        action="store_true",
        default=False,
        help="Skip tests that require network access"
    )
    parser.addoption(
        "--run-slow",
        action="store_true",
        default=False,
        help="Run slow tests (skipped by default)"
    )

