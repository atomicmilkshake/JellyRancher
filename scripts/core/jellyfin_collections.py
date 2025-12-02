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
    
    Args:
        client: JellyfinClient instance
        collection_ids: List of collection IDs to merge
        new_name: Optional name for merged collection (default: "Merged Collection")
        
    Returns:
        True if merge successful, False otherwise
    """
    try:
        logger.info(f"Merging {len(collection_ids)} collections...")
        
        # Get all items from source collections
        all_item_ids = set()
        collection_names = []
        
        for coll_id in collection_ids:
            collection = client.get_item_by_id(coll_id)
            if not collection:
                logger.warning(f"Collection {coll_id} not found, skipping")
                continue
            
            collection_names.append(collection.get('Name', 'Unknown'))
            
            # Get items in collection (via children)
            # Note: This requires getting collection children
            # For now, we'll need to track items when creating collections
            # This is a limitation - we'd need to store item lists
            
            logger.warning("Merge collections: Need to implement collection item retrieval")
            return False
        
        # Create merged collection
        if not new_name:
            new_name = "Merged Collection"
        
        merged_id = client.create_collection(name=new_name, item_ids=list(all_item_ids))
        
        if merged_id:
            # Delete source collections
            for coll_id in collection_ids:
                client.delete_item(coll_id)
            
            logger.info(f"Merged collections into '{new_name}'")
            return True
        
        return False
    except Exception as e:
        logger.error(f"Error merging collections: {e}", exc_info=True)
        return False


def split_collection(client: JellyfinClient, collection_id: str, 
                    criteria: Dict) -> bool:
    """
    Split collection by criteria.
    
    Args:
        client: JellyfinClient instance
        collection_id: Collection ID to split
        criteria: Dictionary with split criteria:
                 - 'field': Field to split by ('genre', 'year', 'type')
                 - 'values': List of values to create separate collections for
                 
    Returns:
        True if split successful, False otherwise
    """
    try:
        logger.info(f"Splitting collection {collection_id} by criteria: {criteria}")
        
        # Get collection
        collection = client.get_item_by_id(collection_id)
        if not collection:
            logger.error(f"Collection {collection_id} not found")
            return False
        
        # Get items in collection (would need collection children API)
        logger.warning("Split collection: Need to implement collection item retrieval")
        return False
    except Exception as e:
        logger.error(f"Error splitting collection: {e}", exc_info=True)
        return False

