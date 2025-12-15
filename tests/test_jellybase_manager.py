"""
Tests for JellyBaseManager and related classes.

Phase 59: JellyBase Code Quality Refinement - Phase 1 Test Infrastructure

Coverage Target: 85%+ line coverage
Test Count: 15 tests
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
import threading
import time

from scripts.core.jellybase_manager import (
    JellyBaseManager,
    JellyBaseState,
    Operation
)
from scripts.core.jellyfin_client import JellyfinClient


class TestJellyBaseManagerInit:
    """Tests for JellyBaseManager initialization."""

    @pytest.mark.unit
    def test_initialization_creates_default_state(self):
        """JellyBaseManager should initialize with default state."""
        manager = JellyBaseManager()
        
        assert isinstance(manager.state, JellyBaseState)
        assert manager.state.current_library is None
        assert manager.state.current_view == 'dashboard'
        assert len(manager.operation_queue) == 0
        assert len(manager.operation_history) == 0
        assert manager.cache == {}
        assert manager.cache_timestamp is None

    @pytest.mark.unit
    def test_initialization_creates_cache_lock(self):
        """JellyBaseManager should create thread-safe cache lock."""
        manager = JellyBaseManager()
        
        # RLock is a factory function, check that it's a lock instance
        assert hasattr(manager._cache_lock, 'acquire')
        assert hasattr(manager._cache_lock, 'release')


class TestLoadLibraryData:
    """Tests for load_library_data() with caching."""

    @pytest.mark.unit
    def test_load_library_data_fresh_load(self):
        """load_library_data() should load fresh data when cache is empty."""
        manager = JellyBaseManager()
        mock_client = MagicMock(spec=JellyfinClient)
        
        mock_items = [{'Id': 'item-1', 'Name': 'Movie 1'}]
        mock_stats = {'total_items': 1}
        mock_libraries = [{'Id': 'lib-1', 'Name': 'Movies'}]
        
        mock_client.get_all_items.return_value = mock_items
        mock_client.get_item_statistics.return_value = mock_stats
        mock_client.get_libraries.return_value = mock_libraries
        
        result = manager.load_library_data(mock_client)
        
        assert result['items'] == mock_items
        assert result['statistics'] == mock_stats
        assert result['libraries'] == mock_libraries
        assert 'timestamp' in result
        assert manager.cache == result
        assert manager.state.last_refresh is not None

    @pytest.mark.unit
    def test_load_library_data_uses_cache_when_valid(self):
        """load_library_data() should return cached data when cache is valid (<5 min)."""
        manager = JellyBaseManager()
        mock_client = MagicMock(spec=JellyfinClient)
        
        # Set up cache
        cached_data = {
            'items': [{'Id': 'cached-item'}],
            'statistics': {'total': 1},
            'libraries': [],
            'timestamp': datetime.now()
        }
        manager.cache = cached_data
        manager.cache_timestamp = datetime.now()  # Fresh cache
        
        result = manager.load_library_data(mock_client)
        
        # Should return cached data without calling API
        assert result == cached_data
        mock_client.get_all_items.assert_not_called()

    @pytest.mark.unit
    def test_load_library_data_refreshes_stale_cache(self):
        """load_library_data() should refresh cache when >5 minutes old."""
        manager = JellyBaseManager()
        mock_client = MagicMock(spec=JellyfinClient)
        
        # Set up stale cache (>5 minutes old)
        old_data = {'items': [], 'statistics': {}, 'libraries': []}
        manager.cache = old_data
        manager.cache_timestamp = datetime.now() - timedelta(minutes=6)
        
        # New data
        new_items = [{'Id': 'new-item'}]
        mock_client.get_all_items.return_value = new_items
        mock_client.get_item_statistics.return_value = {}
        mock_client.get_libraries.return_value = []
        
        result = manager.load_library_data(mock_client)
        
        # Should load fresh data
        assert result['items'] == new_items
        assert manager.cache['items'] == new_items

    @pytest.mark.unit
    def test_load_library_data_returns_stale_cache_on_error(self):
        """load_library_data() should return stale cache if API fails."""
        manager = JellyBaseManager()
        mock_client = MagicMock(spec=JellyfinClient)
        
        # Set up stale cache
        stale_data = {'items': [{'Id': 'stale-item'}], 'statistics': {}, 'libraries': []}
        manager.cache = stale_data
        manager.cache_timestamp = datetime.now() - timedelta(minutes=10)
        
        # API fails
        mock_client.get_all_items.side_effect = Exception("API Error")
        
        result = manager.load_library_data(mock_client)
        
        # Should return stale cache
        assert result == stale_data

    @pytest.mark.unit
    def test_load_library_data_raises_when_no_cache_on_error(self):
        """load_library_data() should raise if API fails and no cache exists."""
        manager = JellyBaseManager()
        mock_client = MagicMock(spec=JellyfinClient)
        
        # No cache, API fails
        mock_client.get_all_items.side_effect = Exception("API Error")
        
        with pytest.raises(Exception, match="API Error"):
            manager.load_library_data(mock_client)


class TestApplyFilters:
    """Tests for apply_filters()."""

    @pytest.mark.unit
    def test_apply_filters_by_item_type(self):
        """apply_filters() should filter by item type."""
        manager = JellyBaseManager()
        items = [
            {'Id': '1', 'Type': 'Movie'},
            {'Id': '2', 'Type': 'Episode'},
            {'Id': '3', 'Type': 'Movie'}
        ]
        
        filtered = manager.apply_filters(items, {'item_types': ['Movie']})
        
        assert len(filtered) == 2
        assert all(item['Type'] == 'Movie' for item in filtered)

    @pytest.mark.unit
    def test_apply_filters_by_genre(self):
        """apply_filters() should filter by genre (case-insensitive)."""
        manager = JellyBaseManager()
        items = [
            {'Id': '1', 'Genres': ['Action', 'Thriller']},
            {'Id': '2', 'Genres': ['Comedy']},
            {'Id': '3', 'Genres': ['ACTION', 'Drama']}
        ]
        
        filtered = manager.apply_filters(items, {'genres': ['Action']})
        
        assert len(filtered) == 2
        assert '1' in [item['Id'] for item in filtered]
        assert '3' in [item['Id'] for item in filtered]

    @pytest.mark.unit
    def test_apply_filters_by_year(self):
        """apply_filters() should filter by production year."""
        manager = JellyBaseManager()
        items = [
            {'Id': '1', 'ProductionYear': 2020},
            {'Id': '2', 'ProductionYear': 2019},
            {'Id': '3', 'ProductionYear': 2020}
        ]
        
        filtered = manager.apply_filters(items, {'years': [2020]})
        
        assert len(filtered) == 2
        assert all(item['ProductionYear'] == 2020 for item in filtered)

    @pytest.mark.unit
    def test_apply_filters_by_search(self):
        """apply_filters() should filter by search query (name, year, genre)."""
        manager = JellyBaseManager()
        items = [
            {'Id': '1', 'Name': 'The Matrix', 'ProductionYear': 1999, 'Genres': ['Sci-Fi']},
            {'Id': '2', 'Name': 'Inception', 'ProductionYear': 2010, 'Genres': ['Action']},
            {'Id': '3', 'Name': 'Matrix Reloaded', 'ProductionYear': 2003, 'Genres': ['Sci-Fi']}
        ]
        
        filtered = manager.apply_filters(items, {'search': 'matrix'})
        
        assert len(filtered) == 2
        assert '1' in [item['Id'] for item in filtered]
        assert '3' in [item['Id'] for item in filtered]

    @pytest.mark.unit
    def test_apply_filters_combines_multiple_filters(self):
        """apply_filters() should combine multiple filter criteria."""
        manager = JellyBaseManager()
        items = [
            {'Id': '1', 'Type': 'Movie', 'Genres': ['Action'], 'ProductionYear': 2020},
            {'Id': '2', 'Type': 'Movie', 'Genres': ['Comedy'], 'ProductionYear': 2020},
            {'Id': '3', 'Type': 'Episode', 'Genres': ['Action'], 'ProductionYear': 2020}
        ]
        
        filtered = manager.apply_filters(items, {
            'item_types': ['Movie'],
            'genres': ['Action']
        })
        
        assert len(filtered) == 1
        assert filtered[0]['Id'] == '1'


class TestOperationQueue:
    """Tests for operation queue management."""

    @pytest.mark.unit
    def test_queue_operation_creates_operation(self):
        """queue_operation() should create and queue an operation."""
        manager = JellyBaseManager()
        
        operation_id = manager.queue_operation('validate', {'item_ids': ['1', '2']})
        
        assert operation_id.startswith('validate_')
        assert len(manager.operation_queue) == 1
        op = manager.operation_queue[0]
        assert op.operation_type == 'validate'
        assert op.status == 'pending'
        assert op.parameters == {'item_ids': ['1', '2']}

    @pytest.mark.unit
    def test_get_operation_status_returns_queue_operation(self):
        """get_operation_status() should return status for queued operation."""
        manager = JellyBaseManager()
        
        operation_id = manager.queue_operation('validate', {'item_ids': ['1']})
        status = manager.get_operation_status(operation_id)
        
        assert status is not None
        assert status['operation_id'] == operation_id
        assert status['operation_type'] == 'validate'
        assert status['status'] == 'pending'

    @pytest.mark.unit
    def test_get_operation_status_returns_none_for_missing(self):
        """get_operation_status() should return None for non-existent operation."""
        manager = JellyBaseManager()
        
        status = manager.get_operation_status('nonexistent-id')
        
        assert status is None


class TestCacheManagement:
    """Tests for cache management."""

    @pytest.mark.unit
    def test_invalidate_cache_clears_cache(self):
        """invalidate_cache() should clear cache and timestamp."""
        manager = JellyBaseManager()
        
        # Set up cache
        manager.cache = {'items': []}
        manager.cache_timestamp = datetime.now()
        
        manager.invalidate_cache()
        
        assert manager.cache == {}
        assert manager.cache_timestamp is None


class TestStateManagement:
    """Tests for state management."""

    @pytest.mark.unit
    def test_update_state_updates_valid_fields(self):
        """update_state() should update state fields."""
        manager = JellyBaseManager()
        
        manager.update_state(current_library='lib-1', current_view='items')
        
        assert manager.state.current_library == 'lib-1'
        assert manager.state.current_view == 'items'
