#!/usr/bin/env python3
"""
Jellyfin Batch Operations

Provides batch operations for managing Jellyfin library:
- Batch add items
- Batch remove items
- Batch update metadata
- Batch collection operations
"""

import logging
from typing import List, Dict, Optional, Callable
from scripts.core.jellyfin_client import JellyfinClient

logger = logging.getLogger(__name__)


def batch_add_items(client: JellyfinClient, paths: List[str], 
                   progress_callback: Optional[Callable[[int, int, str], None]] = None) -> Dict:
    """
    Batch add items (multiple paths).
    
    Args:
        client: JellyfinClient instance
        paths: List of filesystem paths to scan
        progress_callback: Optional callback(current, total, message)
        
    Returns:
        Dictionary with:
        - success_count: Number of successful scans
        - failed_paths: List of paths that failed
    """
    try:
        logger.info(f"Batch adding items from {len(paths)} paths...")
        
        success_count = 0
        failed_paths = []
        
        for i, path in enumerate(paths, 1):
            if progress_callback:
                progress_callback(i, len(paths), f"Scanning: {path}")
            
            try:
                if client.add_item_by_path(path):
                    success_count += 1
                    logger.info(f"Successfully triggered scan for: {path}")
                else:
                    failed_paths.append(path)
                    logger.warning(f"Failed to trigger scan for: {path}")
            except Exception as e:
                failed_paths.append(path)
                logger.error(f"Error scanning path {path}: {e}", exc_info=True)
        
        result = {
            'success_count': success_count,
            'failed_paths': failed_paths,
            'total': len(paths)
        }
        
        logger.info(f"Batch add complete: {success_count}/{len(paths)} successful")
        return result
    except Exception as e:
        logger.error(f"Error in batch_add_items: {e}", exc_info=True)
        return {
            'success_count': 0,
            'failed_paths': paths,
            'total': len(paths)
        }


def batch_remove_items(client: JellyfinClient, item_ids: List[str], 
                      dry_run: bool = True) -> Dict:
    """
    Batch remove items (with confirmation).
    
    Args:
        client: JellyfinClient instance
        item_ids: List of item IDs to remove
        dry_run: If True, only preview (no actual deletion)
        
    Returns:
        Dictionary with:
        - items_to_delete: List of items that would be deleted
        - confirmation_required: True if dry_run
    """
    try:
        logger.info(f"Batch remove: {len(item_ids)} items (dry_run={dry_run})")
        
        items_to_delete = []
        
        for item_id in item_ids:
            item = client.get_item_by_id(item_id)
            if item:
                items_to_delete.append({
                    'id': item_id,
                    'title': item.get('Name', 'Unknown'),
                    'path': item.get('Path', 'N/A')
                })
        
        result = {
            'items_to_delete': items_to_delete,
            'confirmation_required': dry_run,
            'total': len(item_ids)
        }
        
        if not dry_run:
            # Actually delete items
            deleted_count = 0
            failed_count = 0
            
            for item_id in item_ids:
                try:
                    if client.delete_item(item_id):
                        deleted_count += 1
                    else:
                        failed_count += 1
                except Exception as e:
                    failed_count += 1
                    logger.error(f"Error deleting item {item_id}: {e}", exc_info=True)
            
            result['deleted_count'] = deleted_count
            result['failed_count'] = failed_count
            logger.info(f"Batch remove complete: {deleted_count} deleted, {failed_count} failed")
        else:
            logger.info(f"Batch remove preview: {len(items_to_delete)} items would be deleted")
        
        return result
    except Exception as e:
        logger.error(f"Error in batch_remove_items: {e}", exc_info=True)
        return {
            'items_to_delete': [],
            'confirmation_required': True,
            'total': len(item_ids)
        }


def batch_update_metadata(client: JellyfinClient, item_ids: List[str], 
                         metadata_updates: Dict) -> Dict:
    """
    Batch update metadata (bulk ProviderId updates).
    
    Args:
        client: JellyfinClient instance
        item_ids: List of item IDs to update
        metadata_updates: Dictionary of metadata fields to update
                         Can be same for all items, or per-item if structure allows
                         
    Returns:
        Dictionary with:
        - success_count: Number of successful updates
        - failed_ids: List of item IDs that failed
    """
    try:
        logger.info(f"Batch updating metadata for {len(item_ids)} items...")
        
        success_count = 0
        failed_ids = []
        
        for item_id in item_ids:
            try:
                if client.update_item_metadata(item_id, metadata_updates):
                    success_count += 1
                else:
                    failed_ids.append(item_id)
            except Exception as e:
                failed_ids.append(item_id)
                logger.error(f"Error updating metadata for item {item_id}: {e}", exc_info=True)
        
        result = {
            'success_count': success_count,
            'failed_ids': failed_ids,
            'total': len(item_ids)
        }
        
        logger.info(f"Batch update complete: {success_count}/{len(item_ids)} successful")
        return result
    except Exception as e:
        logger.error(f"Error in batch_update_metadata: {e}", exc_info=True)
        return {
            'success_count': 0,
            'failed_ids': item_ids,
            'total': len(item_ids)
        }


def batch_collection_operations(client: JellyfinClient, operations: List[Dict]) -> Dict:
    """
    Batch collection operations.
    
    Args:
        client: JellyfinClient instance
        operations: List of operation dictionaries, each with:
                   - 'operation': 'create', 'add_items', 'remove_items', 'delete'
                   - 'collection_id': Collection ID (for add/remove/delete)
                   - 'name': Collection name (for create)
                   - 'item_ids': List of item IDs (for add_items)
                   - Other operation-specific fields
                   
    Returns:
        Dictionary with:
        - results: List of operation results
        - success_count: Number of successful operations
        - failed_count: Number of failed operations
    """
    try:
        logger.info(f"Batch collection operations: {len(operations)} operations...")
        
        results = []
        success_count = 0
        failed_count = 0
        
        for op in operations:
            op_type = op.get('operation')
            result = {'operation': op_type, 'success': False, 'error': None}
            
            try:
                if op_type == 'create':
                    collection_id = client.create_collection(
                        name=op.get('name', 'New Collection'),
                        item_ids=op.get('item_ids', [])
                    )
                    if collection_id:
                        result['success'] = True
                        result['collection_id'] = collection_id
                        success_count += 1
                    else:
                        result['error'] = 'Failed to create collection'
                        failed_count += 1
                
                elif op_type == 'add_items':
                    collection_id = op.get('collection_id')
                    item_ids = op.get('item_ids', [])
                    if client.add_to_collection(collection_id, item_ids):
                        result['success'] = True
                        success_count += 1
                    else:
                        result['error'] = 'Failed to add items to collection'
                        failed_count += 1
                
                elif op_type == 'remove_items':
                    collection_id = op.get('collection_id')
                    item_ids = op.get('item_ids', [])
                    if client.remove_from_collection(collection_id, item_ids):
                        result['success'] = True
                        success_count += 1
                    else:
                        result['error'] = 'Failed to remove items from collection'
                        failed_count += 1
                
                elif op_type == 'delete':
                    collection_id = op.get('collection_id')
                    if client.delete_item(collection_id):
                        result['success'] = True
                        success_count += 1
                    else:
                        result['error'] = 'Failed to delete collection'
                        failed_count += 1
                
                else:
                    result['error'] = f'Unknown operation type: {op_type}'
                    failed_count += 1
                
            except Exception as e:
                result['error'] = str(e)
                failed_count += 1
                logger.error(f"Error in collection operation {op_type}: {e}", exc_info=True)
            
            results.append(result)
        
        return {
            'results': results,
            'success_count': success_count,
            'failed_count': failed_count,
            'total': len(operations)
        }
    except Exception as e:
        logger.error(f"Error in batch_collection_operations: {e}", exc_info=True)
        return {
            'results': [],
            'success_count': 0,
            'failed_count': len(operations),
            'total': len(operations)
        }

