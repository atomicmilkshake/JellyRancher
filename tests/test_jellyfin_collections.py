"""
Tests for Jellyfin Collection Management Tools.

Phase 59: JellyBase Code Quality Refinement - Phase 1 Test Infrastructure

Coverage Target: 85%+ line coverage
Test Count: 15 tests

Tests collection creation functions and documents stub function behavior.
"""
import pytest
from unittest.mock import MagicMock, patch
import logging

from scripts.core.jellyfin_collections import (
    create_collection_by_genre,
    create_collection_by_year,
    create_collection_by_series,
    merge_collections,
    split_collection
)
from scripts.core.jellyfin_client import JellyfinClient, JellyfinAPIError


class TestCreateCollectionByGenre:
    """Tests for create_collection_by_genre()."""

    @pytest.mark.unit
    def test_create_collection_success(self):
        """create_collection_by_genre() should create collection when items found."""
        mock_client = MagicMock(spec=JellyfinClient)
        
        # Mock items with matching genre
        mock_items = [
            {'Id': 'item-1', 'Name': 'Action Movie 1', 'Genres': ['Action', 'Thriller']},
            {'Id': 'item-2', 'Name': 'Action Movie 2', 'Genres': ['Action', 'Drama']},
            {'Id': 'item-3', 'Name': 'Comedy Movie', 'Genres': ['Comedy']}
        ]
        mock_client.get_all_items.return_value = mock_items
        mock_client.create_collection.return_value = 'collection-123'
        
        result = create_collection_by_genre(mock_client, 'Action')
        
        assert result == 'collection-123'
        mock_client.get_all_items.assert_called_once()
        mock_client.create_collection.assert_called_once_with(
            name='Action Collection',
            item_ids=['item-1', 'item-2']
        )

    @pytest.mark.unit
    def test_create_collection_case_insensitive(self):
        """create_collection_by_genre() should match genres case-insensitively."""
        mock_client = MagicMock(spec=JellyfinClient)
        
        mock_items = [
            {'Id': 'item-1', 'Name': 'Movie', 'Genres': ['ACTION', 'Thriller']},
            {'Id': 'item-2', 'Name': 'Movie 2', 'Genres': ['action', 'Drama']}
        ]
        mock_client.get_all_items.return_value = mock_items
        mock_client.create_collection.return_value = 'collection-456'
        
        result = create_collection_by_genre(mock_client, 'action')
        
        assert result == 'collection-456'
        # Should match both 'ACTION' and 'action'
        assert len(mock_client.create_collection.call_args[1]['item_ids']) == 2

    @pytest.mark.unit
    def test_create_collection_no_items_found(self):
        """create_collection_by_genre() should raise ValueError when no items match genre."""
        mock_client = MagicMock(spec=JellyfinClient)
        
        mock_items = [
            {'Id': 'item-1', 'Name': 'Comedy Movie', 'Genres': ['Comedy']},
            {'Id': 'item-2', 'Name': 'Drama Movie', 'Genres': ['Drama']}
        ]
        mock_client.get_all_items.return_value = mock_items
        
        with pytest.raises(ValueError, match="No items found for genre"):
            create_collection_by_genre(mock_client, 'Action')
        
        mock_client.get_all_items.assert_called_once()
        mock_client.create_collection.assert_not_called()

    @pytest.mark.unit
    def test_create_collection_empty_items_list(self):
        """create_collection_by_genre() should raise ValueError when library is empty."""
        mock_client = MagicMock(spec=JellyfinClient)
        mock_client.get_all_items.return_value = []
        
        with pytest.raises(ValueError, match="No items found for genre"):
            create_collection_by_genre(mock_client, 'Action')
        
        mock_client.create_collection.assert_not_called()

    @pytest.mark.unit
    def test_create_collection_api_failure(self):
        """create_collection_by_genre() should raise JellyfinAPIError when API call fails."""
        mock_client = MagicMock(spec=JellyfinClient)
        
        mock_items = [
            {'Id': 'item-1', 'Name': 'Action Movie', 'Genres': ['Action']}
        ]
        mock_client.get_all_items.return_value = mock_items
        mock_client.create_collection.return_value = None  # API failure
        
        with pytest.raises(JellyfinAPIError, match="Failed to create collection for genre"):
            create_collection_by_genre(mock_client, 'Action')
        
        mock_client.create_collection.assert_called_once()

    @pytest.mark.unit
    def test_create_collection_exception_handling(self):
        """create_collection_by_genre() should raise JellyfinAPIError on exception."""
        mock_client = MagicMock(spec=JellyfinClient)
        mock_client.get_all_items.side_effect = Exception("Network error")
        
        with pytest.raises(JellyfinAPIError, match="Failed to create collection by genre"):
            create_collection_by_genre(mock_client, 'Action')


class TestCreateCollectionByYear:
    """Tests for create_collection_by_year()."""

    @pytest.mark.unit
    def test_create_collection_success(self):
        """create_collection_by_year() should create collection when items found."""
        mock_client = MagicMock(spec=JellyfinClient)
        
        mock_items = [
            {'Id': 'item-1', 'Name': 'Movie 2020', 'ProductionYear': 2020},
            {'Id': 'item-2', 'Name': 'Movie 2021', 'ProductionYear': 2021},
            {'Id': 'item-3', 'Name': 'Movie 2020', 'ProductionYear': 2020}
        ]
        mock_client.get_all_items.return_value = mock_items
        mock_client.create_collection.return_value = 'collection-789'
        
        result = create_collection_by_year(mock_client, 2020)
        
        assert result == 'collection-789'
        mock_client.create_collection.assert_called_once_with(
            name='2020 Collection',
            item_ids=['item-1', 'item-3']
        )

    @pytest.mark.unit
    def test_create_collection_no_items_found(self):
        """create_collection_by_year() should raise ValueError when no items match year."""
        mock_client = MagicMock(spec=JellyfinClient)
        
        mock_items = [
            {'Id': 'item-1', 'Name': 'Movie 2020', 'ProductionYear': 2020},
            {'Id': 'item-2', 'Name': 'Movie 2021', 'ProductionYear': 2021}
        ]
        mock_client.get_all_items.return_value = mock_items
        
        with pytest.raises(ValueError, match="No items found for year"):
            create_collection_by_year(mock_client, 2019)
        
        mock_client.create_collection.assert_not_called()

    @pytest.mark.unit
    def test_create_collection_exception_handling(self):
        """create_collection_by_year() should raise JellyfinAPIError on exception."""
        mock_client = MagicMock(spec=JellyfinClient)
        mock_client.get_all_items.side_effect = Exception("API error")
        
        with pytest.raises(JellyfinAPIError, match="Failed to create collection by year"):
            create_collection_by_year(mock_client, 2020)


class TestCreateCollectionBySeries:
    """Tests for create_collection_by_series()."""

    @pytest.mark.unit
    def test_create_collection_success_by_series_name(self):
        """create_collection_by_series() should match by SeriesName field."""
        mock_client = MagicMock(spec=JellyfinClient)
        
        mock_episodes = [
            {'Id': 'ep-1', 'Name': 'Episode 1', 'SeriesName': 'Breaking Bad'},
            {'Id': 'ep-2', 'Name': 'Episode 2', 'SeriesName': 'Breaking Bad'},
            {'Id': 'ep-3', 'Name': 'Episode 1', 'SeriesName': 'Game of Thrones'}
        ]
        mock_client.get_all_items.return_value = mock_episodes
        mock_client.create_collection.return_value = 'collection-series-1'
        
        result = create_collection_by_series(mock_client, 'Breaking Bad')
        
        assert result == 'collection-series-1'
        mock_client.get_all_items.assert_called_once_with(item_types=['Episode'])
        mock_client.create_collection.assert_called_once_with(
            name='Breaking Bad Collection',
            item_ids=['ep-1', 'ep-2']
        )

    @pytest.mark.unit
    def test_create_collection_fuzzy_matching(self):
        """create_collection_by_series() should use fuzzy matching on Name field."""
        mock_client = MagicMock(spec=JellyfinClient)
        
        mock_episodes = [
            {'Id': 'ep-1', 'Name': 'Breaking Bad S01E01', 'SeriesName': ''},
            {'Id': 'ep-2', 'Name': 'Breaking Bad S01E02', 'SeriesName': ''}
        ]
        mock_client.get_all_items.return_value = mock_episodes
        mock_client.create_collection.return_value = 'collection-series-2'
        
        result = create_collection_by_series(mock_client, 'Breaking Bad')
        
        assert result == 'collection-series-2'
        assert len(mock_client.create_collection.call_args[1]['item_ids']) == 2

    @pytest.mark.unit
    def test_create_collection_no_episodes_found(self):
        """create_collection_by_series() should raise ValueError when no episodes match."""
        mock_client = MagicMock(spec=JellyfinClient)
        
        mock_episodes = [
            {'Id': 'ep-1', 'Name': 'Episode 1', 'SeriesName': 'Other Show'}
        ]
        mock_client.get_all_items.return_value = mock_episodes
        
        with pytest.raises(ValueError, match="No episodes found for series"):
            create_collection_by_series(mock_client, 'Breaking Bad')
        
        mock_client.create_collection.assert_not_called()

    @pytest.mark.unit
    def test_create_collection_exception_handling(self):
        """create_collection_by_series() should raise JellyfinAPIError on exception."""
        mock_client = MagicMock(spec=JellyfinClient)
        mock_client.get_all_items.side_effect = Exception("Connection error")
        
        with pytest.raises(JellyfinAPIError, match="Failed to create collection by series"):
            create_collection_by_series(mock_client, 'Test Series')


class TestMergeCollections:
    """Tests for merge_collections() - STUB FUNCTION."""

    @pytest.mark.unit
    def test_merge_collections_raises_not_implemented(self):
        """
        merge_collections() is a stub function that raises NotImplementedError.
        
        This documents the current behavior. The function requires collection
        children API integration which is not yet implemented.
        """
        mock_client = MagicMock(spec=JellyfinClient)
        
        with pytest.raises(NotImplementedError, match="Collection merging requires"):
            merge_collections(mock_client, ['coll-1', 'coll-2'])

    @pytest.mark.unit
    def test_merge_collections_stub_with_custom_name(self):
        """merge_collections() stub raises NotImplementedError even with custom name."""
        mock_client = MagicMock(spec=JellyfinClient)
        
        with pytest.raises(NotImplementedError, match="Collection merging requires"):
            merge_collections(mock_client, ['coll-1'], new_name='Custom Name')


class TestSplitCollection:
    """Tests for split_collection() - STUB FUNCTION."""

    @pytest.mark.unit
    def test_split_collection_raises_not_implemented(self):
        """
        split_collection() is a stub function that raises NotImplementedError.
        
        This documents the current behavior. The function requires collection
        children API integration which is not yet implemented.
        """
        mock_client = MagicMock(spec=JellyfinClient)
        
        criteria = {'field': 'genre', 'values': ['Action', 'Comedy']}
        with pytest.raises(NotImplementedError, match="Collection splitting requires"):
            split_collection(mock_client, 'collection-123', criteria)

    @pytest.mark.unit
    def test_split_collection_stub_with_custom_criteria(self):
        """split_collection() stub raises NotImplementedError with any criteria."""
        mock_client = MagicMock(spec=JellyfinClient)
        mock_client.get_item_by_id.return_value = None
        
        criteria = {'field': 'year', 'values': [2020, 2021]}
        with pytest.raises(NotImplementedError, match="Collection splitting requires"):
            split_collection(mock_client, 'missing-collection', criteria)


