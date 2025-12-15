"""
Tests for Jellyfin collection management functions.

Phase 59: JellyBase Code Quality Refinement - Phase 1 Test Infrastructure

Coverage Target: 85%+ line coverage
Test Count: 15 tests
"""
import pytest
from unittest.mock import MagicMock, patch
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
        """create_collection_by_genre() should create collection with matching items."""
        mock_client = MagicMock(spec=JellyfinClient)
        
        # Mock items with genre
        mock_items = [
            {'Id': 'item-1', 'Genres': ['Action', 'Thriller']},
            {'Id': 'item-2', 'Genres': ['Action']},
            {'Id': 'item-3', 'Genres': ['Comedy']}
        ]
        mock_client.get_all_items.return_value = mock_items
        mock_client.create_collection.return_value = 'collection-id-123'
        
        result = create_collection_by_genre(mock_client, 'Action')
        
        assert result == 'collection-id-123'
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
            {'Id': 'item-1', 'Genres': ['ACTION', 'Thriller']},
            {'Id': 'item-2', 'Genres': ['action']}
        ]
        mock_client.get_all_items.return_value = mock_items
        mock_client.create_collection.return_value = 'collection-id-456'
        
        result = create_collection_by_genre(mock_client, 'action')
        
        assert result == 'collection-id-456'
        mock_client.create_collection.assert_called_once_with(
            name='action Collection',
            item_ids=['item-1', 'item-2']
        )

    @pytest.mark.unit
    def test_create_collection_no_matching_items(self):
        """create_collection_by_genre() should raise ValueError when no items match."""
        mock_client = MagicMock(spec=JellyfinClient)
        mock_items = [
            {'Id': 'item-1', 'Genres': ['Comedy']},
            {'Id': 'item-2', 'Genres': ['Drama']}
        ]
        mock_client.get_all_items.return_value = mock_items
        
        with pytest.raises(ValueError, match="No items found for genre: Action"):
            create_collection_by_genre(mock_client, 'Action')

    @pytest.mark.unit
    def test_create_collection_api_failure(self):
        """create_collection_by_genre() should raise JellyfinAPIError on API failure."""
        mock_client = MagicMock(spec=JellyfinClient)
        mock_items = [{'Id': 'item-1', 'Genres': ['Action']}]
        mock_client.get_all_items.return_value = mock_items
        mock_client.create_collection.return_value = None
        
        with pytest.raises(JellyfinAPIError, match="Failed to create collection for genre"):
            create_collection_by_genre(mock_client, 'Action')

    @pytest.mark.unit
    def test_create_collection_empty_genres_list(self):
        """create_collection_by_genre() should handle items with empty Genres list."""
        mock_client = MagicMock(spec=JellyfinClient)
        mock_items = [
            {'Id': 'item-1', 'Genres': []},
            {'Id': 'item-2'}  # Missing Genres key
        ]
        mock_client.get_all_items.return_value = mock_items
        
        with pytest.raises(ValueError, match="No items found for genre"):
            create_collection_by_genre(mock_client, 'Action')


class TestCreateCollectionByYear:
    """Tests for create_collection_by_year()."""

    @pytest.mark.unit
    def test_create_collection_by_year_success(self):
        """create_collection_by_year() should create collection with matching year."""
        mock_client = MagicMock(spec=JellyfinClient)
        mock_items = [
            {'Id': 'item-1', 'ProductionYear': 2020},
            {'Id': 'item-2', 'ProductionYear': 2020},
            {'Id': 'item-3', 'ProductionYear': 2019}
        ]
        mock_client.get_all_items.return_value = mock_items
        mock_client.create_collection.return_value = 'collection-year-2020'
        
        result = create_collection_by_year(mock_client, 2020)
        
        assert result == 'collection-year-2020'
        mock_client.create_collection.assert_called_once_with(
            name='2020 Collection',
            item_ids=['item-1', 'item-2']
        )

    @pytest.mark.unit
    def test_create_collection_by_year_no_matches(self):
        """create_collection_by_year() should raise ValueError when no items match year."""
        mock_client = MagicMock(spec=JellyfinClient)
        mock_items = [
            {'Id': 'item-1', 'ProductionYear': 2019},
            {'Id': 'item-2', 'ProductionYear': 2021}
        ]
        mock_client.get_all_items.return_value = mock_items
        
        with pytest.raises(ValueError, match="No items found for year: 2020"):
            create_collection_by_year(mock_client, 2020)

    @pytest.mark.unit
    def test_create_collection_by_year_missing_year_field(self):
        """create_collection_by_year() should handle items without ProductionYear."""
        mock_client = MagicMock(spec=JellyfinClient)
        mock_items = [
            {'Id': 'item-1'},  # Missing ProductionYear
            {'Id': 'item-2', 'ProductionYear': None}
        ]
        mock_client.get_all_items.return_value = mock_items
        
        with pytest.raises(ValueError, match="No items found for year"):
            create_collection_by_year(mock_client, 2020)

    @pytest.mark.unit
    def test_create_collection_by_year_api_failure(self):
        """create_collection_by_year() should raise JellyfinAPIError on API failure."""
        mock_client = MagicMock(spec=JellyfinClient)
        mock_items = [{'Id': 'item-1', 'ProductionYear': 2020}]
        mock_client.get_all_items.return_value = mock_items
        mock_client.create_collection.return_value = None
        
        with pytest.raises(JellyfinAPIError, match="Failed to create collection for year"):
            create_collection_by_year(mock_client, 2020)


class TestCreateCollectionBySeries:
    """Tests for create_collection_by_series()."""

    @pytest.mark.unit
    def test_create_collection_by_series_success(self):
        """create_collection_by_series() should create collection with matching episodes."""
        mock_client = MagicMock(spec=JellyfinClient)
        mock_episodes = [
            {'Id': 'ep-1', 'SeriesName': 'Breaking Bad', 'Name': 'Pilot'},
            {'Id': 'ep-2', 'SeriesName': 'Breaking Bad', 'Name': 'Cat\'s in the Bag'},
            {'Id': 'ep-3', 'SeriesName': 'The Office', 'Name': 'Pilot'}
        ]
        mock_client.get_all_items.return_value = mock_episodes
        mock_client.create_collection.return_value = 'collection-series-bb'
        
        result = create_collection_by_series(mock_client, 'Breaking Bad')
        
        assert result == 'collection-series-bb'
        mock_client.get_all_items.assert_called_once_with(item_types=['Episode'])
        mock_client.create_collection.assert_called_once_with(
            name='Breaking Bad Collection',
            item_ids=['ep-1', 'ep-2']
        )

    @pytest.mark.unit
    def test_create_collection_by_series_fuzzy_match_in_name(self):
        """create_collection_by_series() should match series name in Name field."""
        mock_client = MagicMock(spec=JellyfinClient)
        mock_episodes = [
            {'Id': 'ep-1', 'Name': 'Breaking Bad S01E01'},
            {'Id': 'ep-2', 'Name': 'Breaking Bad S01E02'}
        ]
        mock_client.get_all_items.return_value = mock_episodes
        mock_client.create_collection.return_value = 'collection-bb'
        
        result = create_collection_by_series(mock_client, 'Breaking Bad')
        
        assert result == 'collection-bb'
        mock_client.create_collection.assert_called_once_with(
            name='Breaking Bad Collection',
            item_ids=['ep-1', 'ep-2']
        )

    @pytest.mark.unit
    def test_create_collection_by_series_case_insensitive(self):
        """create_collection_by_series() should match case-insensitively."""
        mock_client = MagicMock(spec=JellyfinClient)
        mock_episodes = [
            {'Id': 'ep-1', 'SeriesName': 'BREAKING BAD', 'Name': 'Pilot'}
        ]
        mock_client.get_all_items.return_value = mock_episodes
        mock_client.create_collection.return_value = 'collection-bb'
        
        result = create_collection_by_series(mock_client, 'breaking bad')
        
        assert result == 'collection-bb'

    @pytest.mark.unit
    def test_create_collection_by_series_no_matches(self):
        """create_collection_by_series() should raise ValueError when no episodes match."""
        mock_client = MagicMock(spec=JellyfinClient)
        mock_episodes = [
            {'Id': 'ep-1', 'SeriesName': 'The Office', 'Name': 'Pilot'}
        ]
        mock_client.get_all_items.return_value = mock_episodes
        
        with pytest.raises(ValueError, match="No episodes found for series: Breaking Bad"):
            create_collection_by_series(mock_client, 'Breaking Bad')


class TestStubFunctions:
    """Tests for stub functions (merge_collections, split_collection)."""

    @pytest.mark.unit
    def test_merge_collections_raises_not_implemented(self):
        """merge_collections() should raise NotImplementedError (stub function)."""
        mock_client = MagicMock(spec=JellyfinClient)
        
        with pytest.raises(NotImplementedError, match="Collection merging requires"):
            merge_collections(mock_client, ['coll-1', 'coll-2'])

    @pytest.mark.unit
    def test_merge_collections_with_custom_name(self):
        """merge_collections() should raise NotImplementedError even with custom name."""
        mock_client = MagicMock(spec=JellyfinClient)
        
        with pytest.raises(NotImplementedError):
            merge_collections(mock_client, ['coll-1'], new_name='Merged Collection')

    @pytest.mark.unit
    def test_split_collection_raises_not_implemented(self):
        """split_collection() should raise NotImplementedError (stub function)."""
        mock_client = MagicMock(spec=JellyfinClient)
        criteria = {'field': 'genre', 'values': ['Action', 'Comedy']}
        
        with pytest.raises(NotImplementedError, match="Collection splitting requires"):
            split_collection(mock_client, 'collection-id', criteria)
