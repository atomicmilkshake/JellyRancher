"""
Tests for TMDB Backend

Unit tests for the TMDB API integration backend.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import json

# Mock tmdbv3api before importing tmdb_backend
import sys
sys.modules['tmdbv3api'] = MagicMock()

from scripts.core.tmdb_backend import (
    TMDBBackend,
    TMDBError,
    TMDBConnectionError,
    TMDBNotFoundError,
    build_cache_from_tmdb
)


class TestTMDBBackend:
    """Test suite for TMDBBackend class"""
    
    def test_init_without_api_key(self):
        """Test initialization without API key"""
        backend = TMDBBackend()
        assert backend._api_key is None
    
    def test_init_with_api_key(self):
        """Test initialization with API key"""
        backend = TMDBBackend("test_api_key")
        assert backend._api_key == "test_api_key"
    
    def test_set_api_key(self):
        """Test setting API key"""
        backend = TMDBBackend()
        backend.set_api_key("new_api_key")
        assert backend._api_key == "new_api_key"
    
    @patch('scripts.core.tmdb_backend.TMDBBackend.tv')
    def test_validate_api_key_success(self, mock_tv):
        """Test API key validation success"""
        backend = TMDBBackend("valid_key")
        mock_tv.search.return_value = [{"name": "Test Show"}]
        
        is_valid, message = backend.validate_api_key()
        assert is_valid is True
        assert "valid" in message.lower()
    
    def test_validate_api_key_no_key(self):
        """Test API key validation with no key set"""
        backend = TMDBBackend()
        is_valid, message = backend.validate_api_key()
        assert is_valid is False
        assert "no api key" in message.lower()
    
    @patch('scripts.core.tmdb_backend.TMDBBackend.tv')
    def test_search_shows_no_api_key(self, mock_tv):
        """Test search without API key raises error"""
        backend = TMDBBackend()
        with pytest.raises(TMDBError, match="No TMDB API key configured"):
            backend.search_shows("Breaking Bad")
    
    @patch('scripts.core.tmdb_backend.TMDBBackend.tv')
    def test_search_shows_success(self, mock_tv):
        """Test successful show search"""
        backend = TMDBBackend("test_key")
        
        # Mock search results
        mock_show = Mock()
        mock_show.id = 1396
        mock_show.name = "Breaking Bad"
        mock_show.first_air_date = "2008-01-20"
        mock_show.overview = "A chemistry teacher turns to crime"
        mock_show.poster_path = "/poster.jpg"
        mock_show.number_of_seasons = 5
        mock_show.number_of_episodes = 62
        
        mock_tv.search.return_value = [mock_show]
        
        results = backend.search_shows("Breaking Bad")
        
        assert len(results) == 1
        assert results[0]['name'] == "Breaking Bad"
        assert results[0]['id'] == 1396
        assert results[0]['number_of_seasons'] == 5
    
    @patch('scripts.core.tmdb_backend.TMDBBackend.tv')
    def test_search_shows_with_year_filter(self, mock_tv):
        """Test show search with year filtering"""
        backend = TMDBBackend("test_key")
        
        # Mock two shows with different years
        show1 = Mock()
        show1.id = 1
        show1.name = "Show 2008"
        show1.first_air_date = "2008-01-01"
        
        show2 = Mock()
        show2.id = 2
        show2.name = "Show 2010"
        show2.first_air_date = "2010-01-01"
        
        mock_tv.search.return_value = [show1, show2]
        
        results = backend.search_shows("Show", year=2008)
        
        # Should filter to only 2008 show
        assert len(results) == 1
        assert results[0]['name'] == "Show 2008"
    
    @patch('scripts.core.tmdb_backend.TMDBBackend.tv')
    def test_search_shows_not_found(self, mock_tv):
        """Test search with no results raises error"""
        backend = TMDBBackend("test_key")
        mock_tv.search.return_value = []
        
        with pytest.raises(TMDBNotFoundError):
            backend.search_shows("NonexistentShow123456")
    
    @patch('scripts.core.tmdb_backend.TMDBBackend.tv')
    def test_get_show_details_success(self, mock_tv):
        """Test getting show details"""
        backend = TMDBBackend("test_key")
        
        mock_show = Mock()
        mock_show.id = 1396
        mock_show.name = "Breaking Bad"
        mock_show.first_air_date = "2008-01-20"
        mock_show.overview = "Overview"
        mock_show.number_of_seasons = 5
        mock_show.number_of_episodes = 62
        mock_show.status = "Ended"
        mock_show.genres = [{"name": "Drama"}]
        
        mock_tv.details.return_value = mock_show
        
        details = backend.get_show_details(1396)
        
        assert details['id'] == 1396
        assert details['name'] == "Breaking Bad"
        assert details['status'] == "Ended"
    
    @patch('scripts.core.tmdb_backend.TMDBBackend.tv')
    def test_get_show_details_not_found(self, mock_tv):
        """Test getting details for non-existent show"""
        backend = TMDBBackend("test_key")
        mock_tv.details.return_value = None
        
        with pytest.raises(TMDBNotFoundError):
            backend.get_show_details(99999)
    
    def test_sanitize_title_removes_illegal_chars(self):
        """Test title sanitization removes illegal characters"""
        test_cases = [
            ("Episode: The Title", "Episode - The Title"),
            ("Question?", "Question"),
            ("File/Path\\Test", "File or Path or Test"),
            ("Test*Test", "TestxTest"),
            ('Quote"Test', "Quote'Test"),
            ("<Less> Greater>", "(less than)Less(greater than) Greater(greater than)"),
        ]
        
        for input_title, expected in test_cases:
            result = TMDBBackend._sanitize_title(input_title)
            assert result == expected
    
    def test_sanitize_title_removes_extra_spaces(self):
        """Test title sanitization removes extra spaces"""
        title = "Too    Many     Spaces"
        result = TMDBBackend._sanitize_title(title)
        assert "  " not in result
        assert result == "Too Many Spaces"
    
    @patch('scripts.core.tmdb_backend.TMDBBackend.tv')
    @patch('builtins.open', new_callable=MagicMock)
    @patch('scripts.core.tmdb_backend.get_tv_cache_dir')
    def test_generate_cache_success(self, mock_cache_dir, mock_open, mock_tv):
        """Test cache generation success"""
        backend = TMDBBackend("test_key")
        
        # Mock show
        mock_show = Mock()
        mock_show.id = 1396
        mock_show.name = "Breaking Bad"
        mock_show.first_air_date = "2008-01-20"
        mock_show.overview = "Overview"
        mock_show.number_of_seasons = 2
        
        # Mock season
        mock_episode = Mock()
        mock_episode.episode_number = 1
        mock_episode.name = "Pilot"
        mock_episode.air_date = "2008-01-20"
        mock_episode.overview = "First episode"
        
        mock_season = Mock()
        mock_season.name = "Season 1"
        mock_season.air_date = "2008-01-20"
        mock_season.episodes = [mock_episode]
        
        mock_tv.details.return_value = mock_show
        mock_tv.season.return_value = mock_season
        
        # Mock file operations
        mock_cache_dir.return_value = Path("/tmp/cache")
        
        cache_path, cache_data = backend.generate_cache(1396)
        
        assert cache_data['show_name'] == "Breaking Bad"
        assert cache_data['tmdb_id'] == 1396
        assert '1' in cache_data['seasons']
        assert '1' in cache_data['seasons']['1']['episodes']
    
    @patch('scripts.core.tmdb_backend.TMDBBackend')
    def test_build_cache_from_tmdb_legacy(self, mock_backend_class):
        """Test legacy build_cache_from_tmdb function"""
        # Mock backend instance
        mock_backend = Mock()
        mock_backend.search_shows.return_value = [{'id': 1396, 'name': 'Breaking Bad'}]
        mock_backend.generate_cache.return_value = (Path("/cache/file.json"), {'show_name': 'Breaking Bad'})
        
        mock_backend_class.return_value = mock_backend
        
        result = build_cache_from_tmdb(
            api_key="test_key",
            show_name="Breaking Bad",
            year=2008
        )
        
        assert result['show_name'] == 'Breaking Bad'
        mock_backend.search_shows.assert_called_once()
        mock_backend.generate_cache.assert_called_once()


class TestTMDBBackendProgressCallbacks:
    """Test progress callback functionality"""
    
    @patch('scripts.core.tmdb_backend.TMDBBackend.tv')
    def test_search_with_progress_callback(self, mock_tv):
        """Test that progress callbacks are invoked during search"""
        backend = TMDBBackend("test_key")
        
        mock_show = Mock()
        mock_show.id = 1
        mock_show.name = "Test"
        mock_show.first_air_date = "2020-01-01"
        
        mock_tv.search.return_value = [mock_show]
        
        callback_messages = []
        def progress_callback(msg):
            callback_messages.append(msg)
        
        backend.search_shows("Test", progress_callback=progress_callback)
        
        assert len(callback_messages) > 0
        assert any("Searching" in msg for msg in callback_messages)
    
    @patch('scripts.core.tmdb_backend.TMDBBackend.tv')
    @patch('builtins.open', new_callable=MagicMock)
    @patch('scripts.core.tmdb_backend.get_tv_cache_dir')
    def test_generate_cache_with_progress_callback(self, mock_cache_dir, mock_open, mock_tv):
        """Test that progress callbacks are invoked during cache generation"""
        backend = TMDBBackend("test_key")
        
        mock_show = Mock()
        mock_show.id = 1
        mock_show.name = "Test"
        mock_show.first_air_date = "2020-01-01"
        mock_show.overview = "Test"
        mock_show.number_of_seasons = 1
        
        mock_episode = Mock()
        mock_episode.episode_number = 1
        mock_episode.name = "Pilot"
        mock_episode.air_date = None
        mock_episode.overview = ""
        
        mock_season = Mock()
        mock_season.episodes = [mock_episode]
        mock_season.name = "Season 1"
        mock_season.air_date = None
        
        mock_tv.details.return_value = mock_show
        mock_tv.season.return_value = mock_season
        mock_cache_dir.return_value = Path("/tmp")
        
        progress_updates = []
        def progress_callback(progress, status):
            progress_updates.append((progress, status))
        
        backend.generate_cache(1, progress_callback=progress_callback)
        
        assert len(progress_updates) > 0
        # Should have progress from 0 to 100
        assert any(p[0] == 0 for p in progress_updates)
        assert any(p[0] == 100 for p in progress_updates)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
