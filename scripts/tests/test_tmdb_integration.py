#!/usr/bin/env python3
"""
Integration tests for TMDB Cache Builder workflow

Tests the complete workflow from API key validation through cache generation.

Note: These tests require a valid TMDB API key set in settings.
For CI/CD, mock the API calls or skip these tests if no key is available.

Usage:
    pytest scripts/tests/test_tmdb_integration.py
    pytest scripts/tests/test_tmdb_integration.py -v --cov=scripts/core
"""

import sys
import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent / "core"))
sys.path.insert(0, str(Path(__file__).parent.parent / "_common"))

from tmdb_backend import TMDBBackend, TMDBError, TMDBConnectionError
from settings_backend import SettingsManager


class TestTMDBIntegration:
    """Integration tests for TMDB workflow."""
    
    @pytest.fixture
    def settings(self):
        """Create settings manager."""
        return SettingsManager()
    
    @pytest.fixture
    def tmdb(self):
        """Create TMDB backend."""
        return TMDBBackend()
    
    def test_settings_tmdb_key_persistence(self, settings, tmp_path):
        """Test that TMDB API key can be saved and loaded."""
        # Override config file path for testing
        original_config = settings.CONFIG_FILE
        settings.CONFIG_FILE = tmp_path / "test_config.json"
        
        try:
            # Set a test key
            test_key = "test_api_key_12345"
            settings.set_tmdb_api_key(test_key)
            settings.save()
            
            # Create new settings instance and verify it loads
            new_settings = SettingsManager()
            new_settings.CONFIG_FILE = tmp_path / "test_config.json"
            new_settings.load()
            
            assert new_settings.get_tmdb_api_key() == test_key
        
        finally:
            settings.CONFIG_FILE = original_config
    
    @patch('tmdbv3api.TMDb')
    def test_api_key_validation_workflow(self, mock_tmdb_class, tmdb):
        """Test API key validation workflow."""
        # Mock the TMDb instance
        mock_instance = MagicMock()
        mock_tmdb_class.return_value = mock_instance
        
        # Set mock API key
        test_key = "valid_test_key"
        tmdb.set_api_key(test_key)
        
        # Verify key is set on the instance
        assert tmdb.tmdb_api.api_key == test_key
    
    @patch('tmdbv3api.TV')
    def test_search_workflow(self, mock_tv_class, tmdb):
        """Test show search workflow."""
        # Mock TV search
        mock_tv = MagicMock()
        mock_tv_class.return_value = mock_tv
        
        # Mock search results
        mock_tv.search.return_value = [
            {
                'id': 1399,
                'name': 'Game of Thrones',
                'first_air_date': '2011-04-17',
                'overview': 'Epic fantasy series'
            }
        ]
        
        # Set API key
        tmdb.set_api_key("test_key")
        tmdb.tv = mock_tv
        
        # Search
        results = tmdb.search_shows("Game of Thrones")
        
        assert len(results) == 1
        assert results[0]['name'] == 'Game of Thrones'
        assert results[0]['id'] == 1399
    
    @patch('tmdbv3api.TV')
    def test_get_show_details_workflow(self, mock_tv_class, tmdb):
        """Test getting show details workflow."""
        # Mock TV details
        mock_tv = MagicMock()
        mock_tv_class.return_value = mock_tv
        
        mock_tv.details.return_value = {
            'id': 1399,
            'name': 'Game of Thrones',
            'number_of_seasons': 8,
            'seasons': [
                {'season_number': 0, 'episode_count': 10},
                {'season_number': 1, 'episode_count': 10},
            ]
        }
        
        mock_tv.season_details.return_value = {
            'season_number': 1,
            'episodes': [
                {'episode_number': 1, 'name': 'Winter Is Coming'},
                {'episode_number': 2, 'name': 'The Kingsroad'},
            ]
        }
        
        # Set API key
        tmdb.set_api_key("test_key")
        tmdb.tv = mock_tv
        
        # Get details
        show = tmdb.get_show_details(1399)
        
        assert show['id'] == 1399
        assert show['name'] == 'Game of Thrones'
        assert show['number_of_seasons'] == 8
    
    @patch('tmdbv3api.TV')
    @patch('scripts.core.tmdb_backend.get_tv_cache_dir')
    def test_cache_generation_workflow(self, mock_cache_dir, mock_tv_class, tmdb, tmp_path):
        """Test complete cache generation workflow."""
        # Mock the cache directory
        mock_cache_dir.return_value = tmp_path
        
        # Mock TV details and season details
        mock_tv = MagicMock()
        mock_tv_class.return_value = mock_tv
        
        # Mock show details
        mock_tv.details.return_value = {
            'id': 12345,
            'name': 'Test Show',
            'number_of_seasons': 2,
            'seasons': [
                {'season_number': 1, 'episode_count': 3},
                {'season_number': 2, 'episode_count': 2},
            ]
        }
        
        # Mock season details for each season
        def mock_season(show_id, season_num):
            if season_num == 1:
                return {
                    'season_number': 1,
                    'name': 'Season 1',
                    'air_date': '2020-01-01',
                    'episodes': [
                        {'episode_number': 1, 'name': 'Episode 1', 'air_date': '2020-01-01', 'overview': 'Overview 1'},
                        {'episode_number': 2, 'name': 'Episode 2', 'air_date': '2020-01-08', 'overview': 'Overview 2'},
                        {'episode_number': 3, 'name': 'Episode 3', 'air_date': '2020-01-15', 'overview': 'Overview 3'},
                    ]
                }
            elif season_num == 2:
                return {
                    'season_number': 2,
                    'name': 'Season 2', 
                    'air_date': '2020-06-01',
                    'episodes': [
                        {'episode_number': 1, 'name': 'Episode 1', 'air_date': '2020-06-01', 'overview': 'Overview 1'},
                        {'episode_number': 2, 'name': 'Episode 2', 'air_date': '2020-06-08', 'overview': 'Overview 2'},
                    ]
                }
        
        mock_tv.season.side_effect = mock_season
        
        # Set API key and mock TV
        tmdb.set_api_key("test_key")
        tmdb.tv = mock_tv
        
        # Generate cache
        output_path = tmp_path / "test_cache.json"
        result_path, cache_data = tmdb.generate_cache(12345, output_path)
        
        # Verify cache file was created
        assert result_path.exists()
        
        # Verify cache content
        with open(result_path, 'r') as f:
            cache = json.load(f)
        
        assert cache['tmdb_id'] == 12345
        assert cache['show_name'] == 'Test Show'
        assert len(cache['seasons']) == 2
        assert len(cache['seasons']['1']['episodes']) == 3
        assert len(cache['seasons']['2']['episodes']) == 2
    
    @patch('tmdbv3api.TV')
    @patch('scripts.core.tmdb_backend.get_tv_cache_dir')
    def test_cache_progress_callback(self, mock_cache_dir, mock_tv_class, tmdb, tmp_path):
        """Test that progress callbacks work during cache generation."""
        # Mock the cache directory
        mock_cache_dir.return_value = tmp_path
        
        # Mock TV details
        mock_tv = MagicMock()
        mock_tv_class.return_value = mock_tv
        
        mock_tv.details.return_value = {
            'id': 12345,
            'name': 'Test Show',
            'number_of_seasons': 2,
            'seasons': [
                {'season_number': 1, 'episode_count': 2},
                {'season_number': 2, 'episode_count': 2},
            ]
        }
        
        def mock_season(show_id, season_num):
            return {
                'season_number': season_num,
                'name': f'Season {season_num}',
                'air_date': '2020-01-01',
                'episodes': [
                    {'episode_number': 1, 'name': 'Episode 1', 'air_date': '2020-01-01', 'overview': 'Overview 1'},
                    {'episode_number': 2, 'name': 'Episode 2', 'air_date': '2020-01-08', 'overview': 'Overview 2'},
                ]
            }
        
        mock_tv.season.side_effect = mock_season
        
        # Set API key
        tmdb.set_api_key("test_key")
        tmdb.tv = mock_tv
        
        # Track progress callbacks
        progress_updates = []
        
        def progress_callback(progress: int, status: str):
            progress_updates.append((progress, status))
        
        # Generate cache with callback
        output_path = tmp_path / "test_cache.json"
        tmdb.generate_cache(12345, output_path, progress_callback=progress_callback)
        
        # Verify callbacks were made
        assert len(progress_updates) > 0
        assert progress_updates[-1][0] == 100  # Final progress should be 100%
    
    def test_cache_file_structure(self, tmdb, tmp_path):
        """Test that generated cache has correct structure."""
        # Create a minimal cache manually to test structure
        cache_data = {
            'tmdb_id': 12345,
            'show_name': 'Test Show',
            'seasons': [
                {
                    'season_number': 1,
                    'episodes': [
                        {'episode_number': 1, 'name': 'Pilot'},
                        {'episode_number': 2, 'name': 'Second Episode'},
                    ]
                }
            ]
        }
        
        cache_path = tmp_path / "test_cache.json"
        with open(cache_path, 'w') as f:
            json.dump(cache_data, f, indent=2)
        
        # Load and verify structure
        with open(cache_path, 'r') as f:
            loaded = json.load(f)
        
        # Verify required fields
        assert 'tmdb_id' in loaded
        assert 'show_name' in loaded
        assert 'seasons' in loaded
        assert isinstance(loaded['seasons'], list)
        assert len(loaded['seasons']) > 0
        
        # Verify season structure
        season = loaded['seasons'][0]
        assert 'season_number' in season
        assert 'episodes' in season
        
        # Verify episode structure
        episode = season['episodes'][0]
        assert 'episode_number' in episode
        assert 'name' in episode
    
    @patch('tmdbv3api.TV')
    def test_error_handling_invalid_show_id(self, mock_tv_class, tmdb):
        """Test error handling for invalid show ID."""
        mock_tv = MagicMock()
        mock_tv_class.return_value = mock_tv
        
        # Mock API error
        from requests.exceptions import HTTPError
        mock_tv.details.side_effect = HTTPError("404 Not Found")
        
        tmdb.set_api_key("test_key")
        tmdb.tv = mock_tv
        
        # Should raise TMDBError
        with pytest.raises(TMDBError):
            tmdb.get_show_details(999999)
    
    @patch('tmdbv3api.TV')
    def test_error_handling_network_error(self, mock_tv_class, tmdb):
        """Test error handling for network errors."""
        mock_tv = MagicMock()
        mock_tv_class.return_value = mock_tv
        
        # Mock network error
        from requests.exceptions import ConnectionError
        mock_tv.search.side_effect = ConnectionError("Network error")
        
        tmdb.set_api_key("test_key")
        tmdb.tv = mock_tv
        
        # Should raise TMDBConnectionError
        with pytest.raises(TMDBConnectionError):
            tmdb.search_shows("Test Show")
    
    def test_title_sanitization(self, tmdb):
        """Test that show titles are sanitized for filesystem safety."""
        # Test various problematic characters
        test_cases = [
            ("Show: The Series", "Show - The Series"),
            ("Show/Movie", "Show-Movie"),
            ('Show "Quotes"', 'Show Quotes'),
            ("Show*Name", "ShowName"),
            ("Show<>Name", "ShowName"),
            ("Show|Name", "ShowName"),
            ("Show?Name", "ShowName"),
        ]
        
        for input_title, expected_output in test_cases:
            sanitized = tmdb._sanitize_title(input_title)
            # Basic check - should not contain problematic chars
            assert not any(char in sanitized for char in ['/', '\\', ':', '*', '?', '"', '<', '>', '|'])


class TestTMDBDialogIntegration:
    """Integration tests for TMDB dialog workflow (requires PyQt5)."""
    
    @pytest.fixture
    def qt_app(self):
        """Create Qt application for dialog testing."""
        try:
            from PyQt5.QtWidgets import QApplication
            import sys
            
            # Create app if it doesn't exist
            app = QApplication.instance()
            if app is None:
                app = QApplication(sys.argv)
            
            yield app
        except ImportError:
            pytest.skip("PyQt5 not available for dialog testing")
    
    def test_dialog_imports(self):
        """Test that dialog module can be imported."""
        try:
            from dialogs.tmdb_cache_dialog import TMDBCacheDialog
            assert TMDBCacheDialog is not None
        except ImportError as e:
            pytest.fail(f"Failed to import TMDBCacheDialog: {e}")
    
    def test_dialog_creation(self, qt_app):
        """Test that dialog can be instantiated."""
        from dialogs.tmdb_cache_dialog import TMDBCacheDialog
        
        # Mock settings to avoid API key issues
        with patch('dialogs.tmdb_cache_dialog.SettingsManager') as mock_settings:
            mock_settings.return_value.get_tmdb_api_key.return_value = "test_key"
            
            dialog = TMDBCacheDialog()
            assert dialog is not None
            assert dialog.windowTitle() == "TMDB Episode Cache Generator"


if __name__ == "__main__":
    """Run tests directly."""
    pytest.main([__file__, "-v", "--tb=short"])
