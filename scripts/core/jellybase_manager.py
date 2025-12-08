#!/usr/bin/env python3
"""
JellyBase Manager - Central state and operation management

Provides centralized management for all JellyBase operations:
- State management (current library, filters, selections)
- Operation queue (batch operations with progress)
- History/audit log
- Cache management
"""

import logging
import threading
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from collections import deque

logger = logging.getLogger(__name__)


@dataclass
class Operation:
    """Represents a JellyBase operation."""
    operation_id: str
    operation_type: str  # 'validate', 'add_items', 'remove_items', 'create_collection', etc.
    status: str  # 'pending', 'running', 'completed', 'failed'
    parameters: Dict
    result: Optional[Dict] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


@dataclass
class JellyBaseState:
    """Current state of JellyBase."""
    current_library: Optional[str] = None
    active_filters: Dict = field(default_factory=dict)
    selected_items: Set[str] = field(default_factory=set)
    current_view: str = 'dashboard'  # 'dashboard', 'items', 'collections', 'validation', 'tools'
    last_refresh: Optional[datetime] = None


class JellyBaseManager:
    """
    Central manager for all JellyBase operations.
    
    Manages state, operation queue, history, and caching.
    """
    
    def __init__(self):
        """Initialize JellyBase manager."""
        self.state = JellyBaseState()
        self.operation_queue = deque()
        self.operation_history = deque(maxlen=100)  # Keep last 100 operations
        self.cache = {}  # Cache for library data
        self.cache_timestamp = None
        self._cache_lock = threading.RLock()  # Thread-safe cache access
        logger.info("JellyBaseManager initialized")
    
    def load_library_data(self, jellyfin_client) -> Dict:
        """
        Load library data (with thread-safe caching).
        
        Args:
            jellyfin_client: JellyfinClient instance
            
        Returns:
            Dictionary with library data
        """
        # Check cache (thread-safe)
        with self._cache_lock:
            if self.cache and self.cache_timestamp:
                # Cache valid for 5 minutes
                from datetime import timedelta
                if datetime.now() - self.cache_timestamp < timedelta(minutes=5):
                    logger.debug("Using cached library data")
                    return self.cache.copy()  # Return copy to prevent external modification
        
        try:
            # Load fresh data
            items = jellyfin_client.get_all_items()
            stats = jellyfin_client.get_item_statistics()
            libraries = jellyfin_client.get_libraries()
            
            data = {
                'items': items,
                'statistics': stats,
                'libraries': libraries,
                'timestamp': datetime.now()
            }
            
            # Update cache (thread-safe)
            with self._cache_lock:
                self.cache = data
                self.cache_timestamp = datetime.now()
            
            self.state.last_refresh = datetime.now()
            
            logger.info(f"Loaded library data: {len(items)} items")
            return data
        except Exception as e:
            logger.error(f"Error loading library data: {e}", exc_info=True)
            # Return cached data if available, even if stale (thread-safe)
            with self._cache_lock:
                if self.cache:
                    logger.warning("Using stale cache due to error")
                    return self.cache.copy()  # Return copy to prevent external modification
            raise
    
    def apply_filters(self, items: List[Dict], filters: Dict) -> List[Dict]:
        """
        Apply filters to items list.
        
        Args:
            items: List of item dictionaries
            filters: Dictionary with filter criteria:
                    - item_types: List of types
                    - genres: List of genres
                    - years: List of years
                    - libraries: List of library IDs
                    - search: Search query string
                    
        Returns:
            Filtered list of items
        """
        filtered = items
        
        # Filter by type
        if 'item_types' in filters and filters['item_types']:
            filtered = [item for item in filtered 
                       if item.get('Type') in filters['item_types']]
        
        # Filter by genre
        if 'genres' in filters and filters['genres']:
            filtered = [item for item in filtered
                       if any(g.lower() in [x.lower() for x in item.get('Genres', [])] 
                             for g in filters['genres'])]
        
        # Filter by year
        if 'years' in filters and filters['years']:
            filtered = [item for item in filtered
                       if item.get('ProductionYear') in filters['years']]
        
        # Filter by library
        if 'libraries' in filters and filters['libraries']:
            filtered = [item for item in filtered
                       if item.get('ParentId') in filters['libraries']]
        
        # Search filter
        if 'search' in filters and filters['search']:
            search_term = filters['search'].lower()
            filtered = [item for item in filtered
                       if search_term in item.get('Name', '').lower() or
                       search_term in str(item.get('ProductionYear', '')) or
                       any(search_term in g.lower() for g in item.get('Genres', []))]
        
        return filtered
    
    def queue_operation(self, operation_type: str, parameters: Dict) -> str:
        """
        Queue an operation for execution.
        
        Args:
            operation_type: Type of operation
            parameters: Operation parameters
            
        Returns:
            Operation ID
        """
        operation_id = f"{operation_type}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        operation = Operation(
            operation_id=operation_id,
            operation_type=operation_type,
            status='pending',
            parameters=parameters
        )
        
        self.operation_queue.append(operation)
        logger.info(f"Queued operation: {operation_type} (ID: {operation_id})")
        return operation_id
    
    def get_operation_status(self, operation_id: str) -> Optional[Dict]:
        """
        Get status of an operation.
        
        Args:
            operation_id: Operation ID
            
        Returns:
            Dictionary with operation status, or None if not found
        """
        # Check queue
        for op in self.operation_queue:
            if op.operation_id == operation_id:
                return {
                    'operation_id': op.operation_id,
                    'operation_type': op.operation_type,
                    'status': op.status,
                    'parameters': op.parameters,
                    'result': op.result,
                    'error': op.error,
                    'started_at': op.started_at.isoformat() if op.started_at else None,
                    'completed_at': op.completed_at.isoformat() if op.completed_at else None
                }
        
        # Check history
        for op in self.operation_history:
            if op.operation_id == operation_id:
                return {
                    'operation_id': op.operation_id,
                    'operation_type': op.operation_type,
                    'status': op.status,
                    'parameters': op.parameters,
                    'result': op.result,
                    'error': op.error,
                    'started_at': op.started_at.isoformat() if op.started_at else None,
                    'completed_at': op.completed_at.isoformat() if op.completed_at else None
                }
        
        return None
    
    def get_history(self, limit: int = 20) -> List[Dict]:
        """
        Get operation history.
        
        Args:
            limit: Maximum number of operations to return
            
        Returns:
            List of operation dictionaries
        """
        history = list(self.operation_history)[-limit:]
        return [{
            'operation_id': op.operation_id,
            'operation_type': op.operation_type,
            'status': op.status,
            'started_at': op.started_at.isoformat() if op.started_at else None,
            'completed_at': op.completed_at.isoformat() if op.completed_at else None,
            'error': op.error
        } for op in history]
    
    def invalidate_cache(self):
        """Invalidate cached library data (thread-safe)."""
        with self._cache_lock:
            self.cache = {}
            self.cache_timestamp = None
        logger.info("Cache invalidated")
    
    def update_state(self, **kwargs):
        """Update manager state."""
        for key, value in kwargs.items():
            if hasattr(self.state, key):
                setattr(self.state, key, value)
                logger.debug(f"State updated: {key} = {value}")

