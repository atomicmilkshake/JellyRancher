"""
Tests for JellyBase Manager - Central state and operation management.

Phase 59: JellyBase Code Quality Refinement - Phase 1 Test Infrastructure

Coverage Target: 85%+ line coverage
Test Count: 15 tests

Tests state management, caching, filtering, and operation queue.
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

from scripts.core.jellybase_manager import (
    JellyBaseManager,
    JellyBaseState,
    Operation
)
from scripts.core.jellyfin_client import JellyfinClient


class TestJellyBaseManagerInit:
    """Tests for JellyBaseManager initialization."""

    @pytest.mark.unit
    def test_manager_initialization(self):
        """JellyBaseManager should initialize with empty state and queues."""
        manager = JellyBaseManager()
        
        assert manager.state is not None
        assert isinstance(manager.state, JellyBaseState)
        assert len(manager.operation_queue) == 0
        assert len(manager.operation_history) == 0
        assert manager.cache == {}
        assert manager.cache_timestamp is None


class TestLoadLibraryData:
    """Tests for load_library_data() with caching."""

    @pytest.mark.unit
    def test_load_fresh_data(self):
        """load_library_data() should load fresh data when cache is empty."""
        manager = JellyBaseManager()
        mock_client = MagicMock(spec=JellyfinClient)
        
        mock_items = [
            {'Id': 'item-1', 'Name': 'Movie 1', 'Type': 'Movie'},
            {'Id': 'item-2', 'Name': 'Movie 2', 'Type': 'Movie'}
        ]
        mock_client.get_all_items.return_value = mock_items
        mock_client.get_item_statistics.return_value = {'total': 2}
        mock_client.get_libraries.return_value = [{'Id': 'lib-1', 'Name': 'Movies'}]
        
        result = manager.load_library_data(mock_client)
        
        assert 'items' in result
        assert 'statistics' in result
        assert 'libraries' in result
        assert 'timestamp' in result
        assert len(result['items']) == 2
        assert manager.cache == result
        assert manager.cache_timestamp is not None

    @pytest.mark.unit
    def test_load_uses_cache_when_valid(self):
        """load_library_data() should return cached data if less than 5 minutes old."""
        manager = JellyBaseManager()
        mock_client = MagicMock(spec=JellyfinClient)
        
        # Set up cache
        cached_data = {
            'items': [{'Id': 'cached-1', 'Name': 'Cached Movie'}],
            'statistics': {'total': 1},
            'libraries': [],
            'timestamp': datetime.now()
        }
        manager.cache = cached_data
        manager.cache_timestamp = datetime.now() - timedelta(minutes=2)  # 2 minutes ago
        
        result = manager.load_library_data(mock_client)
        
        assert result == cached_data
        mock_client.get_all_items.assert_not_called()

    @pytest.mark.unit
    def test_load_refreshes_stale_cache(self):
        """load_library_data() should refresh cache if older than 5 minutes."""
        manager = JellyBaseManager()
        mock_client = MagicMock(spec=JellyfinClient)
        
        # Set up stale cache
        manager.cache = {'items': [], 'statistics': {}, 'libraries': []}
        manager.cache_timestamp = datetime.now() - timedelta(minutes=6)  # 6 minutes ago
        
        mock_items = [{'Id': 'new-1', 'Name': 'New Movie'}]
        mock_client.get_all_items.return_value = mock_items
        mock_client.get_item_statistics.return_value = {'total': 1}
        mock_client.get_libraries.return_value = []
        
        result = manager.load_library_data(mock_client)
        
        assert len(result['items']) == 1
        assert result['items'][0]['Id'] == 'new-1'
        mock_client.get_all_items.assert_called_once()

    @pytest.mark.unit
    def test_load_returns_stale_cache_on_error(self):
        """load_library_data() should return stale cache if API call fails."""
        manager = JellyBaseManager()
        mock_client = MagicMock(spec=JellyfinClient)
        
        # Set up stale cache
        stale_data = {
            'items': [{'Id': 'stale-1', 'Name': 'Stale Movie'}],
            'statistics': {'total': 1},
            'libraries': [],
            'timestamp': datetime.now() - timedelta(minutes=10)
        }
        manager.cache = stale_data
        manager.cache_timestamp = datetime.now() - timedelta(minutes=10)
        
        mock_client.get_all_items.side_effect = Exception("API error")
        
        result = manager.load_library_data(mock_client)
        
        assert result == stale_data

    @pytest.mark.unit
    def test_load_raises_on_error_with_no_cache(self):
        """load_library_data() should raise exception if API fails and no cache exists."""
        manager = JellyBaseManager()
        mock_client = MagicMock(spec=JellyfinClient)
        mock_client.get_all_items.side_effect = Exception("API error")
        
        with pytest.raises(Exception):
            manager.load_library_data(mock_client)


class TestApplyFilters:
    """Tests for apply_filters()."""

    @pytest.mark.unit
    def test_filter_by_item_type(self):
        """apply_filters() should filter items by type."""
        manager = JellyBaseManager()
        
        items = [
            {'Id': '1', 'Name': 'Movie 1', 'Type': 'Movie'},
            {'Id': '2', 'Name': 'Episode 1', 'Type': 'Episode'},
            {'Id': '3', 'Name': 'Movie 2', 'Type': 'Movie'}
        ]
        
        filters = {'item_types': ['Movie']}
        result = manager.apply_filters(items, filters)
        
        assert len(result) == 2
        assert all(item['Type'] == 'Movie' for item in result)

    @pytest.mark.unit
    def test_filter_by_genre(self):
        """apply_filters() should filter items by genre (case-insensitive)."""
        manager = JellyBaseManager()
        
        items = [
            {'Id': '1', 'Name': 'Action Movie', 'Genres': ['Action', 'Thriller']},
            {'Id': '2', 'Name': 'Comedy Movie', 'Genres': ['Comedy']},
            {'Id': '3', 'Name': 'Action Drama', 'Genres': ['ACTION', 'Drama']}
        ]
        
        filters = {'genres': ['Action']}
        result = manager.apply_filters(items, filters)
        
        assert len(result) == 2
        assert all('Action' in [g.lower() for g in item.get('Genres', [])] 
                  or 'action' in [g.lower() for g in item.get('Genres', [])]
                  for item in result)

    @pytest.mark.unit
    def test_filter_by_year(self):
        """apply_filters() should filter items by production year."""
        manager = JellyBaseManager()
        
        items = [
            {'Id': '1', 'Name': 'Movie 2020', 'ProductionYear': 2020},
            {'Id': '2', 'Name': 'Movie 2021', 'ProductionYear': 2021},
            {'Id': '3', 'Name': 'Movie 2020', 'ProductionYear': 2020}
        ]
        
        filters = {'years': [2020]}
        result = manager.apply_filters(items, filters)
        
        assert len(result) == 2
        assert all(item['ProductionYear'] == 2020 for item in result)

    @pytest.mark.unit
    def test_filter_by_search(self):
        """apply_filters() should filter items by search query."""
        manager = JellyBaseManager()
        
        items = [
            {'Id': '1', 'Name': 'Breaking Bad', 'ProductionYear': 2008},
            {'Id': '2', 'Name': 'Game of Thrones', 'ProductionYear': 2011},
            {'Id': '3', 'Name': 'Breaking Bad Movie', 'Genres': ['Action']}
        ]
        
        filters = {'search': 'breaking'}
        result = manager.apply_filters(items, filters)
        
        assert len(result) == 2
        assert all('breaking' in item['Name'].lower() for item in result)

    @pytest.mark.unit
    def test_filter_multiple_criteria(self):
        """apply_filters() should apply multiple filters together."""
        manager = JellyBaseManager()
        
        items = [
            {'Id': '1', 'Name': 'Action Movie 2020', 'Type': 'Movie', 
             'ProductionYear': 2020, 'Genres': ['Action']},
            {'Id': '2', 'Name': 'Comedy Movie 2020', 'Type': 'Movie',
             'ProductionYear': 2020, 'Genres': ['Comedy']},
            {'Id': '3', 'Name': 'Action Movie 2021', 'Type': 'Movie',
             'ProductionYear': 2021, 'Genres': ['Action']}
        ]
        
        filters = {'item_types': ['Movie'], 'years': [2020], 'genres': ['Action']}
        result = manager.apply_filters(items, filters)
        
        assert len(result) == 1
        assert result[0]['Id'] == '1'


class TestOperationQueue:
    """Tests for operation queue management."""

    @pytest.mark.unit
    def test_queue_operation(self):
        """queue_operation() should add operation to queue."""
        manager = JellyBaseManager()
        
        operation_id = manager.queue_operation('validate', {'item_ids': ['1', '2']})
        
        assert operation_id is not None
        assert len(manager.operation_queue) == 1
        op = manager.operation_queue[0]
        assert op.operation_type == 'validate'
        assert op.status == 'pending'
        assert op.parameters == {'item_ids': ['1', '2']}

    @pytest.mark.unit
    def test_get_operation_status_from_queue(self):
        """get_operation_status() should return status from queue."""
        manager = JellyBaseManager()
        
        operation_id = manager.queue_operation('create_collection', {'name': 'Test'})
        status = manager.get_operation_status(operation_id)
        
        assert status is not None
        assert status['operation_type'] == 'create_collection'
        assert status['status'] == 'pending'
        assert status['parameters'] == {'name': 'Test'}

    @pytest.mark.unit
    def test_get_operation_status_not_found(self):
        """get_operation_status() should return None for non-existent operation."""
        manager = JellyBaseManager()
        
        status = manager.get_operation_status('non-existent-id')
        
        assert status is None


class TestCacheManagement:
    """Tests for cache management."""

    @pytest.mark.unit
    def test_invalidate_cache(self):
        """invalidate_cache() should clear cache and timestamp."""
        manager = JellyBaseManager()
        
        # Set up cache
        manager.cache = {'items': [{'Id': '1'}]}
        manager.cache_timestamp = datetime.now()
        
        manager.invalidate_cache()
        
        assert manager.cache == {}
        assert manager.cache_timestamp is None


class TestStateManagement:
    """Tests for state management."""

    @pytest.mark.unit
    def test_update_state(self):
        """update_state() should update state attributes."""
        manager = JellyBaseManager()
        
        manager.update_state(
            current_library='library-123',
            current_view='items',
            selected_items={'item-1', 'item-2'}
        )
        
        assert manager.state.current_library == 'library-123'
        assert manager.state.current_view == 'items'
        assert manager.state.selected_items == {'item-1', 'item-2'}


