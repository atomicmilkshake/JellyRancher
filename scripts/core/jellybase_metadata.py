#!/usr/bin/env python3
"""
JellyBase Metadata Enhancement - Bulk metadata operations

Provides bulk metadata management:
- Bulk metadata refresh
- Provider ID correction
- Tag management
- Custom metadata fields
"""

import logging
from typing import List, Dict
from scripts.core.jellyfin_client import JellyfinClient

logger = logging.getLogger(__name__)


def bulk_metadata_refresh(client: JellyfinClient, item_ids: List[str]) -> Dict:
    """
    Bulk metadata refresh for multiple items.
    
    Args:
        client: JellyfinClient instance
        item_ids: List of item IDs to refresh
        
    Returns:
        Dictionary with success_count and failed_ids
    """
    try:
        logger.info(f"Bulk refreshing metadata for {len(item_ids)} items...")
        
        success_count = 0
        failed_ids = []
        
        for item_id in item_ids:
            try:
                if client.refresh_item(item_id, replace_metadata=False):
                    success_count += 1
                else:
                    failed_ids.append(item_id)
            except Exception as e:
                failed_ids.append(item_id)
                logger.error(f"Error refreshing item {item_id}: {e}", exc_info=True)
        
        result = {
            'success_count': success_count,
            'failed_ids': failed_ids,
            'total': len(item_ids)
        }
        
        logger.info(f"Bulk refresh complete: {success_count}/{len(item_ids)} successful")
        return result
    except Exception as e:
        logger.error(f"Error in bulk_metadata_refresh: {e}", exc_info=True)
        return {
            'success_count': 0,
            'failed_ids': item_ids,
            'total': len(item_ids)
        }


def fix_missing_provider_ids(client: JellyfinClient, item_ids: List[str]) -> Dict:
    """
    Attempt to fix missing ProviderIds by refreshing metadata.
    
    ⚠️ IMPORTANT LIMITATION: This function triggers Jellyfin's built-in metadata
    refresh, which MAY populate ProviderIds IF Jellyfin's metadata providers
    are configured correctly. It does NOT directly query TMDB/TVDB APIs.
    
    Success depends on Jellyfin server configuration. For guaranteed ProviderID
    population, integrate with TMDB/TVDB APIs directly.
    
    Args:
        client: JellyfinClient instance
        item_ids: List of item IDs to fix
        
    Returns:
        Dictionary with:
        - fixed_count: Number of items refreshed (NOT necessarily fixed)
        - failed_ids: List of IDs that failed to refresh
        - total: Total items attempted
    """
    try:
        logger.info(f"Fixing missing ProviderIds for {len(item_ids)} items...")
        
        # For now, just refresh metadata which may pick up ProviderIds
        # In the future, this would query TMDb/TVDB APIs directly
        result = bulk_metadata_refresh(client, item_ids)
        
        # Rename keys for clarity
        result['fixed_count'] = result.pop('success_count')
        
        logger.info(f"Provider ID fix complete: {result['fixed_count']}/{len(item_ids)} successful")
        return result
    except Exception as e:
        logger.error(f"Error in fix_missing_provider_ids: {e}", exc_info=True)
        return {
            'fixed_count': 0,
            'failed_ids': item_ids,
            'total': len(item_ids)
        }


def bulk_tag_management(client: JellyfinClient, item_ids: List[str], 
                       tags: List[str], operation: str) -> Dict:
    """
    Bulk tag management (add/remove tags).
    
    Args:
        client: JellyfinClient instance
        item_ids: List of item IDs
        tags: List of tags to add/remove
        operation: 'add', 'remove', or 'replace'
        
    Returns:
        Dictionary with updated_count and failed_ids
    """
    try:
        logger.info(f"Bulk tag {operation} for {len(item_ids)} items: {tags}")
        
        updated_count = 0
        failed_ids = []
        
        for item_id in item_ids:
            try:
                # Get current item
                item = client.get_item_by_id(item_id)
                if not item:
                    failed_ids.append(item_id)
                    continue
                
                current_tags = item.get('Tags', [])
                
                # Apply operation
                if operation == 'add':
                    new_tags = list(set(current_tags + tags))
                elif operation == 'remove':
                    new_tags = [t for t in current_tags if t not in tags]
                elif operation == 'replace':
                    new_tags = tags
                else:
                    logger.warning(f"Unknown tag operation: {operation}")
                    failed_ids.append(item_id)
                    continue
                
                # Update item
                if client.update_item_metadata(item_id, {'Tags': new_tags}):
                    updated_count += 1
                else:
                    failed_ids.append(item_id)
            except Exception as e:
                failed_ids.append(item_id)
                logger.error(f"Error managing tags for item {item_id}: {e}", exc_info=True)
        
        result = {
            'updated_count': updated_count,
            'failed_ids': failed_ids,
            'total': len(item_ids)
        }
        
        logger.info(f"Tag management complete: {updated_count}/{len(item_ids)} successful")
        return result
    except Exception as e:
        logger.error(f"Error in bulk_tag_management: {e}", exc_info=True)
        return {
            'updated_count': 0,
            'failed_ids': item_ids,
            'total': len(item_ids)
        }


def update_custom_metadata_fields(client: JellyfinClient, item_ids: List[str], 
                                  fields: Dict) -> Dict:
    """
    Update custom metadata fields for multiple items.
    
    Args:
        client: JellyfinClient instance
        item_ids: List of item IDs
        fields: Dictionary of field names to values
        
    Returns:
        Dictionary with updated_count and failed_ids
    """
    try:
        logger.info(f"Updating custom metadata fields for {len(item_ids)} items: {list(fields.keys())}")
        
        updated_count = 0
        failed_ids = []
        
        for item_id in item_ids:
            try:
                if client.update_item_metadata(item_id, fields):
                    updated_count += 1
                else:
                    failed_ids.append(item_id)
            except Exception as e:
                failed_ids.append(item_id)
                logger.error(f"Error updating metadata for item {item_id}: {e}", exc_info=True)
        
        result = {
            'updated_count': updated_count,
            'failed_ids': failed_ids,
            'total': len(item_ids)
        }
        
        logger.info(f"Custom metadata update complete: {updated_count}/{len(item_ids)} successful")
        return result
    except Exception as e:
        logger.error(f"Error in update_custom_metadata_fields: {e}", exc_info=True)
        return {
            'updated_count': 0,
            'failed_ids': item_ids,
            'total': len(item_ids)
        }

