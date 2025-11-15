"""
Shared pytest fixtures and configuration for Jelly Rancher tests
"""

import sys
import pytest
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any
import json

# Add project root and all module directories to path
project_root = Path(__file__).parent.parent.parent
paths_to_add = [
    project_root,  # Root for top-level imports
    project_root / "scripts",  # scripts package
    project_root / "scripts" / "core",  # core modules (tmdb_backend, settings_backend, etc.)
    project_root / "scripts" / "media",  # media modules (media_org_backend, subtitle_backend, etc.)
    project_root / "scripts" / "utils",  # utility modules (analytics_backend, etc.)
    project_root / "scripts" / "_common",  # common utilities (tv_episode_cache, credential_manager, etc.)
]

for path in paths_to_add:
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)


@pytest.fixture
def temp_dir(tmp_path):
    """Provide a temporary directory for tests."""
    yield tmp_path
    # Cleanup is automatic with tmp_path


@pytest.fixture
def sample_movies_dir(temp_dir):
    """
    Create a sample Movies directory structure for testing
    
    Structure:
        Movies/
            Movie A (2020)/
                Movie A (2020).mkv
            Movie B (2019) H.265 1080p.mkv (directly in Movies, with codec tags)
            BadFolder/
                Movie C (2018).mp4
    """
    movies_dir = temp_dir / "Movies"
    movies_dir.mkdir()
    
    # Proper structure
    movie_a = movies_dir / "Movie A (2020)"
    movie_a.mkdir()
    (movie_a / "Movie A (2020).mkv").write_text("fake video content")
    
    # File directly in Movies with codec tags
    (movies_dir / "Movie B (2019) H.265 1080p.mkv").write_text("fake video content")
    
    # File in wrong folder
    bad_folder = movies_dir / "BadFolder"
    bad_folder.mkdir()
    (bad_folder / "Movie C (2018).mp4").write_text("fake video content")
    
    return movies_dir


@pytest.fixture
def sample_tv_shows_dir(temp_dir):
    """
    Create a sample TV Shows directory structure for testing
    
    Structure:
        TV Shows/
            Show A/
                Season 01/
                    Show A - S01E01 - Pilot.mkv
                    Show A - S01E02 - Second Episode.mkv
            Show B/
                Season 01/
                    S01E01 - Episode Title.mkv (missing show name)
    """
    tv_dir = temp_dir / "TV Shows"
    tv_dir.mkdir()
    
    # Show A - proper format
    show_a = tv_dir / "Show A"
    show_a.mkdir()
    season_1a = show_a / "Season 01"
    season_1a.mkdir()
    (season_1a / "Show A - S01E01 - Pilot.mkv").write_text("fake video")
    (season_1a / "Show A - S01E02 - Second Episode.mkv").write_text("fake video")
    
    # Show B - missing show name in filename
    show_b = tv_dir / "Show B"
    show_b.mkdir()
    season_1b = show_b / "Season 01"
    season_1b.mkdir()
    (season_1b / "S01E01 - Episode Title.mkv").write_text("fake video")
    
    return tv_dir


@pytest.fixture
def sample_tmdb_cache(temp_dir):
    """
    Create a sample TMDB cache file for testing
    """
    cache_data = {
        "show_name": "Test Show",
        "tmdb_id": 12345,
        "seasons": {
            "1": {
                "episodes": {
                    "1": {
                        "name": "Pilot Episode",
                        "season_number": 1,
                        "episode_number": 1
                    },
                    "2": {
                        "name": "Second Episode",
                        "season_number": 1,
                        "episode_number": 2
                    }
                }
            }
        }
    }
    
    cache_file = temp_dir / "test_cache.json"
    cache_file.write_text(json.dumps(cache_data, indent=2))
    
    return cache_file


@pytest.fixture
def mock_logger():
    """Provide a mock logger for tests."""
    class MockLogger:
        def __init__(self):
            self.messages = {
                'info': [],
                'warning': [],
                'error': [],
                'success': []
            }
        
        def info(self, msg):
            self.messages['info'].append(msg)
        
        def warning(self, msg):
            self.messages['warning'].append(msg)
        
        def error(self, msg):
            self.messages['error'].append(msg)
        
        def success(self, msg):
            self.messages['success'].append(msg)
        
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
            self.events.append({
                'type': event_type,
                'data': data
            })
        
        def clear(self):
            self.events = []
    
    return MockAuditLog()


@pytest.fixture(autouse=True)
def reset_sys_path():
    """Reset sys.path after each test to avoid pollution."""
    original_path = sys.path.copy()
    yield
    sys.path = original_path


# Skip markers for conditional tests
def pytest_configure(config):
    """Configure custom markers."""
    config.addinivalue_line(
        "markers", "requires_gui: mark test as requiring GUI/PyQt5"
    )
    config.addinivalue_line(
        "markers", "requires_tmdb_api: mark test as requiring TMDB API access"
    )


def pytest_collection_modifyitems(config, items):
    """Automatically skip certain tests based on environment."""
    skip_gui = pytest.mark.skip(reason="PyQt5 not available or headless environment")
    skip_network = pytest.mark.skip(reason="Network access not available")
    
    for item in items:
        # Skip GUI tests if running in CI or headless
        if "requires_gui" in item.keywords:
            try:
                import PyQt5
            except ImportError:
                item.add_marker(skip_gui)
        
        # Skip network tests if --no-network flag is set
        if "requires_network" in item.keywords:
            if config.getoption("--no-network", default=False):
                item.add_marker(skip_network)


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
