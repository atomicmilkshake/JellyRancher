#!/usr/bin/env python3
"""
Jellyfin Collection Management Tools

Provides functions for automated collection creation and management:
- Group by genre, year, series
- Merge and split collections
- Collection operations
"""

import logging
from typing import List, Dict, Optional
from scripts.core.jellyfin_client import JellyfinClient

logger = logging.getLogger(__name__)


def create_collection_by_genre(client: JellyfinClient, genre: str) -> Optional[str]:
    """
    Auto-group items by genre.
    
    Args:
        client: JellyfinClient instance
        genre: Genre name to group by
        
    Returns:
        Collection ID if successful, None otherwise
    """
    try:
        logger.info(f"Creating collection for genre: {genre}")
        
        # Get all items
        items = client.get_all_items()
        
        # Filter items by genre
        matching_items = []
        for item in items:
            item_genres = [g.lower() for g in item.get('Genres', [])]
            if genre.lower() in item_genres:
                matching_items.append(item.get('Id'))
        
        if not matching_items:
            logger.warning(f"No items found for genre: {genre}")
            return None
        
        # Create collection
        collection_id = client.create_collection(
            name=f"{genre} Collection",
            item_ids=matching_items
        )
        
        if collection_id:
            logger.info(f"Created collection '{genre} Collection' with {len(matching_items)} items")
        
        return collection_id
    except Exception as e:
        logger.error(f"Error creating collection by genre {genre}: {e}", exc_info=True)
        return None


def create_collection_by_year(client: JellyfinClient, year: int) -> Optional[str]:
    """
    Group by release year.
    
    Args:
        client: JellyfinClient instance
        year: Release year to group by
        
    Returns:
        Collection ID if successful, None otherwise
    """
    try:
        logger.info(f"Creating collection for year: {year}")
        
        # Get all items
        items = client.get_all_items()
        
        # Filter items by year
        matching_items = []
        for item in items:
            item_year = item.get('ProductionYear')
            if item_year == year:
                matching_items.append(item.get('Id'))
        
        if not matching_items:
            logger.warning(f"No items found for year: {year}")
            return None
        
        # Create collection
        collection_id = client.create_collection(
            name=f"{year} Collection",
            item_ids=matching_items
        )
        
        if collection_id:
            logger.info(f"Created collection '{year} Collection' with {len(matching_items)} items")
        
        return collection_id
    except Exception as e:
        logger.error(f"Error creating collection by year {year}: {e}", exc_info=True)
        return None


def create_collection_by_series(client: JellyfinClient, series_name: str) -> Optional[str]:
    """
    Group TV series episodes.
    
    Args:
        client: JellyfinClient instance
        series_name: Series name to group
        
    Returns:
        Collection ID if successful, None otherwise
    """
    try:
        logger.info(f"Creating collection for series: {series_name}")
        
        # Get all episodes
        items = client.get_all_items(item_types=['Episode'])
        
        # Filter episodes by series name (fuzzy matching)
        matching_items = []
        series_name_lower = series_name.lower()
        
        for item in items:
            # Check series name in various fields
            item_series = item.get('SeriesName', '').lower()
            item_name = item.get('Name', '').lower()
            
            if series_name_lower in item_series or series_name_lower in item_name:
                matching_items.append(item.get('Id'))
        
        if not matching_items:
            logger.warning(f"No episodes found for series: {series_name}")
            return None
        
        # Create collection
        collection_id = client.create_collection(
            name=f"{series_name} Collection",
            item_ids=matching_items
        )
        
        if collection_id:
            logger.info(f"Created collection '{series_name} Collection' with {len(matching_items)} items")
        
        return collection_id
    except Exception as e:
        logger.error(f"Error creating collection by series {series_name}: {e}", exc_info=True)
        return None


def merge_collections(client: JellyfinClient, collection_ids: List[str], 
                     new_name: Optional[str] = None) -> bool:
    """
    Merge multiple collections into one.
    
    STATUS: NOT IMPLEMENTED (stub function)
    TODO: Implement in future phase when collection children API is integrated.
    Requires GET /Collections/{id}/Items endpoint support to retrieve items from collections.
    
    Args:
        client: JellyfinClient instance
        collection_ids: List of collection IDs to merge
        new_name: Optional name for merged collection (default: "Merged Collection")
        
    Returns:
        True if merge successful, False otherwise
        
    Raises:
        NotImplementedError: Function is stub pending API integration
    """
    logger.warning("merge_collections: Not implemented (stub function)")
    raise NotImplementedError(
        "Collection merging requires collection children API integration. "
        "Track implementation: [Future GitHub Issue]"
    )


def split_collection(client: JellyfinClient, collection_id: str, 
                    criteria: Dict) -> bool:
    """
    Split collection by criteria.
    
    STATUS: NOT IMPLEMENTED (stub function)
    TODO: Implement in future phase when collection children API is integrated.
    Requires GET /Collections/{id}/Items endpoint support to retrieve items from collections.
    
    Args:
        client: JellyfinClient instance
        collection_id: Collection ID to split
        criteria: Dictionary with split criteria:
                 - 'field': Field to split by ('genre', 'year', 'type')
                 - 'values': List of values to create separate collections for
                 
    Returns:
        True if split successful, False otherwise
        
    Raises:
        NotImplementedError: Function is stub pending API integration
    """
    logger.warning("split_collection: Not implemented (stub function)")
    raise NotImplementedError(
        "Collection splitting requires collection children API integration. "
        "Track implementation: [Future GitHub Issue]"
    )

