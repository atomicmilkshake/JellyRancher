#!/usr/bin/env python3
"""
Jellyfin API Client - Integration with Jellyfin Media Server

Provides programmatic access to Jellyfin server for:
- Authentication with API key
- Query Jellyfin items by path
- Get library structure
- Get ProviderIds (TMDb, TVDb, IMDb)
- Trigger library refresh
- Verify subtitle streams

Architecture Reference: Layer 3 (External Services)
Integration Points: Points 1-4 (scanning, metadata, cross-reference)
"""

import os
import logging
import requests
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class JellyfinConfig:
    """Jellyfin server configuration."""
    server_url: str  # e.g., "http://localhost:8096"
    api_key: str
    user_id: Optional[str] = None  # Auto-detected if None


class JellyfinAPIError(Exception):
    """
    Raised when Jellyfin API operations fail.
    
    Commandment #5: Fail Loudly - Use specific exceptions instead of returning None/False.
    """
    pass


class JellyfinClient:
    """
    Client for Jellyfin API interactions.

    Provides methods to query Jellyfin server for media items, cross-reference
    with local filesystem, retrieve metadata (ProviderIds), and trigger refreshes.

    Usage:
        client = JellyfinClient(
            server_url="http://localhost:8096",
            api_key="your_api_key"
        )

        if client.test_connection():
            items = client.get_all_items(item_types=["Movie", "Episode"])
            for item in items:
                print(f"{item['Name']}: {item['Path']}")
    """

    def __init__(
        self,
        server_url: str = None,
        api_key: str = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize Jellyfin client.

        Args:
            server_url: Jellyfin server URL (or env JELLYFIN_SERVER_URL)
                       Example: "http://localhost:8096" or "https://jellyfin.example.com"
            api_key: Jellyfin API key (or env JELLYFIN_API_KEY)
                    Generate in Dashboard > Advanced > API Keys
            logger: Logger instance for debugging
        """
        self.server_url = (server_url or os.getenv('JELLYFIN_SERVER_URL', '')).rstrip('/')
        self.api_key = api_key or os.getenv('JELLYFIN_API_KEY', '')
        self.logger = logger or logging.getLogger(__name__)

        self.user_id = None
        self.session = requests.Session()

        # Set authentication header
        if self.api_key:
            self.session.headers.update({
                'X-Emby-Token': self.api_key,
                'Accept': 'application/json'
            })

            self.logger.info(f"Jellyfin client initialized: {self.server_url}")
        else:
            self.logger.warning("No Jellyfin API key configured")

    def is_configured(self) -> bool:
        """
        Check if Jellyfin client is configured.

        Returns:
            True if server URL and API key are set
        """
        return bool(self.server_url and self.api_key)

    def test_connection(self) -> bool:
        """
        Test connection to Jellyfin server.

        Returns:
            True if connection successful, False otherwise
        """
        if not self.is_configured():
            self.logger.error("Jellyfin not configured (missing server URL or API key)")
            return False

        try:
            response = self.session.get(f"{self.server_url}/System/Info", timeout=10)
            response.raise_for_status()

            info = response.json()
            self.logger.info(
                f"Connected to Jellyfin {info.get('Version')} "
                f"({info.get('ServerName')})"
            )
            return True

        except requests.exceptions.Timeout:
            self.logger.error("Jellyfin connection timeout (server not responding)")
            return False
        except requests.exceptions.ConnectionError as e:
            self.logger.error(f"Jellyfin connection failed: {e}")
            return False
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                self.logger.error("Jellyfin authentication failed (invalid API key)")
            else:
                self.logger.error(f"Jellyfin HTTP error: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Jellyfin connection error: {e}")
            return False

    def get_user_id(self) -> str:
        """
        Get current user ID (cached after first call).

        Returns:
            User ID string

        Raises:
            ValueError: If no users found in Jellyfin
            RuntimeError: If API request fails
        """
        if self.user_id:
            return self.user_id

        try:
            # Get users and return first admin or first user
            response = self.session.get(f"{self.server_url}/Users", timeout=10)
            response.raise_for_status()

            users = response.json()

            # Prefer admin user
            for user in users:
                if user.get('Policy', {}).get('IsAdministrator'):
                    self.user_id = user['Id']
                    self.logger.info(f"Using admin user: {user['Name']} (ID: {self.user_id})")
                    return self.user_id

            # Fallback to first user
            if users:
                self.user_id = users[0]['Id']
                self.logger.info(f"Using first user: {users[0]['Name']} (ID: {self.user_id})")
                return self.user_id

            raise ValueError("No users found in Jellyfin")
        except requests.exceptions.Timeout:
            self.logger.error("Timeout getting Jellyfin user ID")
            raise RuntimeError("Jellyfin timeout")
        except requests.exceptions.ConnectionError as e:
            self.logger.error(f"Connection error getting Jellyfin user ID: {e}")
            raise RuntimeError(f"Jellyfin connection failed: {e}")
        except requests.exceptions.HTTPError as e:
            self.logger.error(f"HTTP error getting Jellyfin user ID: {e}")
            raise RuntimeError(f"Jellyfin API error: {e}")
        except ValueError:
            # Re-raise our custom error
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error getting Jellyfin user ID: {e}", exc_info=True)
            raise RuntimeError(f"Failed to get Jellyfin user ID: {e}")

    def get_all_items(
        self,
        item_types: List[str] = None,
        fields: List[str] = None,
        limit: int = None
    ) -> List[Dict]:
        """
        Get all media items from Jellyfin.

        Args:
            item_types: Filter by types (e.g., ["Movie", "Episode", "Series"])
            fields: Additional fields to include (e.g., ["Path", "ProviderIds", "MediaSources"])
            limit: Maximum number of items to return (default: all)

        Returns:
            List of Jellyfin item dictionaries

        Example:
            items = client.get_all_items(
                item_types=["Movie", "Episode"],
                fields=["Path", "ProviderIds"]
            )
        """
        try:
            user_id = self.get_user_id()

            params = {
                'Recursive': 'true',
                'Fields': ','.join(fields or ['Path', 'ProviderIds', 'MediaSources'])
            }

            if item_types:
                params['IncludeItemTypes'] = ','.join(item_types)

            if limit:
                params['Limit'] = limit

            response = self.session.get(
                f"{self.server_url}/Users/{user_id}/Items",
                params=params,
                timeout=30
            )
            response.raise_for_status()

            data = response.json()
            items = data.get('Items', [])

            self.logger.info(f"Retrieved {len(items)} items from Jellyfin")
            return items
        except RuntimeError:
            # Re-raise errors from get_user_id
            raise
        except requests.exceptions.Timeout:
            self.logger.error("Timeout retrieving items from Jellyfin")
            raise RuntimeError("Jellyfin timeout")
        except requests.exceptions.ConnectionError as e:
            self.logger.error(f"Connection error retrieving items from Jellyfin: {e}")
            raise RuntimeError(f"Jellyfin connection failed: {e}")
        except requests.exceptions.HTTPError as e:
            self.logger.error(f"HTTP error retrieving items from Jellyfin: {e}")
            raise RuntimeError(f"Jellyfin API error: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error retrieving items from Jellyfin: {e}", exc_info=True)
            raise RuntimeError(f"Failed to retrieve items from Jellyfin: {e}")

    def find_item_by_path(self, file_path: Path) -> Optional[Dict]:
        """
        Find Jellyfin item by file path.

        Args:
            file_path: Absolute file path to search for

        Returns:
            Jellyfin item dict or None if not found

        Note:
            This method normalizes paths for cross-platform compatibility
            (Windows backslashes vs Linux forward slashes)
        """
        try:
            # Normalize path for Windows/Linux compatibility
            search_path = str(file_path.resolve()).replace('\\', '/')

            # Query items with path field
            items = self.get_all_items(fields=['Path', 'ProviderIds'])

            for item in items:
                item_path = item.get('Path', '').replace('\\', '/')
                if item_path == search_path:
                    self.logger.debug(f"Found Jellyfin match: {item.get('Name')} (ID: {item.get('Id')})")
                    return item

            self.logger.debug(f"No Jellyfin item found for path: {search_path}")
            return None
        except RuntimeError:
            # Re-raise errors from get_all_items
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error finding item by path {file_path}: {e}", exc_info=True)
            return None

    def get_item_by_id(self, item_id: str, fields: List[str] = None) -> Optional[Dict]:
        """
        Get Jellyfin item by ID.

        Args:
            item_id: Jellyfin item ID
            fields: Additional fields to include

        Returns:
            Jellyfin item dict or None if not found
        """
        try:
            params = {}
            if fields:
                params['Fields'] = ','.join(fields)

            response = self.session.get(
                f"{self.server_url}/Items/{item_id}",
                params=params,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            self.logger.error(f"Timeout getting item {item_id} from Jellyfin")
            return None
        except requests.exceptions.ConnectionError as e:
            self.logger.error(f"Connection error getting item {item_id}: {e}")
            return None
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                self.logger.warning(f"Item not found: {item_id}")
            else:
                self.logger.error(f"HTTP error getting item {item_id}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error getting item {item_id}: {e}", exc_info=True)
            return None

    def get_provider_ids(self, item_id: str) -> Dict[str, str]:
        """
        Get provider IDs (TMDb, TVDb, IMDb) for an item.

        Args:
            item_id: Jellyfin item ID

        Returns:
            Dict mapping provider names to IDs
            Example: {"Tmdb": "123456", "Tvdb": "789", "Imdb": "tt9876543"}
        """
        try:
            item = self.get_item_by_id(item_id, fields=['ProviderIds'])

            if item:
                provider_ids = item.get('ProviderIds', {})
                self.logger.debug(f"Retrieved provider IDs for item {item_id}: {list(provider_ids.keys())}")
                return provider_ids
            else:
                self.logger.warning(f"Could not retrieve provider IDs for item {item_id}")
                return {}
        except Exception as e:
            self.logger.error(f"Unexpected error getting provider IDs for item {item_id}: {e}", exc_info=True)
            return {}

    def refresh_item(self, item_id: str, replace_metadata: bool = False) -> bool:
        """
        Trigger metadata refresh for an item.

        Args:
            item_id: Jellyfin item ID
            replace_metadata: Whether to replace existing metadata (default: False)

        Returns:
            True if refresh triggered successfully
        """
        try:
            params = {
                'ReplaceAllMetadata': 'true' if replace_metadata else 'false',
                'ReplaceAllImages': 'false'
            }

            response = self.session.post(
                f"{self.server_url}/Items/{item_id}/Refresh",
                params=params,
                timeout=10
            )
            response.raise_for_status()

            self.logger.info(f"Triggered refresh for item {item_id}")
            return True
        except requests.exceptions.Timeout:
            self.logger.error(f"Timeout refreshing item {item_id}")
            return False
        except requests.exceptions.ConnectionError as e:
            self.logger.error(f"Connection error refreshing item {item_id}: {e}")
            return False
        except requests.exceptions.HTTPError as e:
            self.logger.error(f"HTTP error refreshing item {item_id}: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error refreshing item {item_id}: {e}", exc_info=True)
            return False

    def refresh_library(self) -> bool:
        """
        Trigger full library refresh.

        Returns:
            True if refresh triggered successfully
        """
        try:
            response = self.session.post(
                f"{self.server_url}/Library/Refresh",
                timeout=10
            )
            response.raise_for_status()

            self.logger.info("Triggered full library refresh")
            return True
        except requests.exceptions.Timeout:
            self.logger.error("Timeout refreshing Jellyfin library")
            return False
        except requests.exceptions.ConnectionError as e:
            self.logger.error(f"Connection error refreshing library: {e}")
            return False
        except requests.exceptions.HTTPError as e:
            self.logger.error(f"HTTP error refreshing library: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error refreshing library: {e}", exc_info=True)
            return False

    def get_libraries(self) -> List[Dict]:
        """
        Get all media libraries.

        Returns:
            List of library dictionaries

        Example:
            libraries = client.get_libraries()
            for lib in libraries:
                print(f"{lib['Name']} - {lib['CollectionType']}")
        """
        try:
            user_id = self.get_user_id()

            response = self.session.get(
                f"{self.server_url}/Users/{user_id}/Views",
                timeout=10
            )
            response.raise_for_status()

            data = response.json()
            libraries = data.get('Items', [])

            self.logger.info(f"Retrieved {len(libraries)} libraries")
            return libraries
        except RuntimeError:
            # Re-raise errors from get_user_id
            raise
        except requests.exceptions.Timeout:
            self.logger.error("Timeout retrieving libraries from Jellyfin")
            return []
        except requests.exceptions.ConnectionError as e:
            self.logger.error(f"Connection error retrieving libraries: {e}")
            return []
        except requests.exceptions.HTTPError as e:
            self.logger.error(f"HTTP error retrieving libraries: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error retrieving libraries: {e}", exc_info=True)
            return []

    def get_media_streams(self, item_id: str) -> List[Dict]:
        """
        Get media streams (video, audio, subtitle) for an item.

        Args:
            item_id: Jellyfin item ID

        Returns:
            List of media stream dictionaries
        """
        try:
            item = self.get_item_by_id(item_id, fields=['MediaStreams'])

            if item and 'MediaSources' in item:
                for source in item['MediaSources']:
                    if 'MediaStreams' in source:
                        streams = source['MediaStreams']
                        self.logger.debug(f"Retrieved {len(streams)} media streams for item {item_id}")
                        return streams

            self.logger.debug(f"No media streams found for item {item_id}")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error getting media streams for item {item_id}: {e}", exc_info=True)
            return []

    def has_subtitle_stream(self, item_id: str, language: str = 'eng') -> bool:
        """
        Check if item has subtitle stream in specified language.

        Args:
            item_id: Jellyfin item ID
            language: ISO 639-2 language code (default: 'eng' for English)

        Returns:
            True if subtitle stream found
        """
        try:
            streams = self.get_media_streams(item_id)

            for stream in streams:
                if stream.get('Type') == 'Subtitle' and stream.get('Language', '').lower() == language.lower():
                    self.logger.debug(f"Found {language} subtitle stream for item {item_id}")
                    return True

            self.logger.debug(f"No {language} subtitle stream found for item {item_id}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error checking subtitle stream for item {item_id}: {e}", exc_info=True)
            return False

    def create_collection(self, name: str, item_ids: List[str] = None) -> Optional[str]:
        """Create a new collection in Jellyfin."""
        try:
            params = {'Name': name, 'IsLocked': 'false'}
            if item_ids:
                params['Ids'] = ','.join(item_ids)

            response = self.session.post(f"{self.server_url}/Collections", params=params, timeout=10)
            response.raise_for_status()

            collection_id = response.json().get('Id')
            self.logger.info(f"Created collection '{name}' (ID: {collection_id})")
            return collection_id
        except requests.exceptions.Timeout:
            self.logger.error(f"Timeout creating collection '{name}'")
            return None
        except requests.exceptions.ConnectionError as e:
            self.logger.error(f"Connection error creating collection '{name}': {e}")
            return None
        except requests.exceptions.HTTPError as e:
            self.logger.error(f"HTTP error creating collection '{name}': {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error creating collection '{name}': {e}", exc_info=True)
            return None

    def add_to_collection(self, collection_id: str, item_ids: List[str]) -> bool:
        """Add items to an existing collection."""
        try:
            response = self.session.post(
                f"{self.server_url}/Collections/{collection_id}/Items",
                params={'Ids': ','.join(item_ids)},
                timeout=10
            )
            response.raise_for_status()
            self.logger.info(f"Added {len(item_ids)} items to collection {collection_id}")
            return True
        except requests.exceptions.Timeout:
            self.logger.error(f"Timeout adding items to collection {collection_id}")
            return False
        except requests.exceptions.ConnectionError as e:
            self.logger.error(f"Connection error adding items to collection {collection_id}: {e}")
            return False
        except requests.exceptions.HTTPError as e:
            self.logger.error(f"HTTP error adding items to collection {collection_id}: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error adding items to collection {collection_id}: {e}", exc_info=True)
            return False

    def get_collections(self) -> List[Dict]:
        """Get all collections in Jellyfin."""
        try:
            user_id = self.get_user_id()
            response = self.session.get(
                f"{self.server_url}/Users/{user_id}/Items",
                params={'Recursive': 'true', 'IncludeItemTypes': 'BoxSet', 'Fields': 'ChildCount'},
                timeout=30
            )
            response.raise_for_status()
            collections = response.json().get('Items', [])
            self.logger.info(f"Retrieved {len(collections)} collections")
            return collections
        except RuntimeError:
            # Re-raise errors from get_user_id
            raise
        except requests.exceptions.Timeout:
            self.logger.error("Timeout retrieving collections from Jellyfin")
            return []
        except requests.exceptions.ConnectionError as e:
            self.logger.error(f"Connection error retrieving collections: {e}")
            return []
        except requests.exceptions.HTTPError as e:
            self.logger.error(f"HTTP error retrieving collections: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error retrieving collections: {e}", exc_info=True)
            return []

    def update_provider_ids(self, item_id: str, provider_ids: Dict[str, str]) -> bool:
        """Update provider IDs for an item (TMDb, TVDb, IMDb)."""
        try:
            item = self.get_item_by_id(item_id)
            if not item:
                self.logger.warning(f"Item {item_id} not found for provider ID update")
                return False

            current_providers = item.get('ProviderIds', {})
            current_providers.update(provider_ids)

            response = self.session.post(
                f"{self.server_url}/Items/{item_id}",
                json={'Id': item_id, 'ProviderIds': current_providers},
                timeout=10
            )
            response.raise_for_status()
            self.logger.info(f"Updated provider IDs for item {item_id}: {list(provider_ids.keys())}")
            return True
        except requests.exceptions.Timeout:
            self.logger.error(f"Timeout updating provider IDs for item {item_id}")
            return False
        except requests.exceptions.ConnectionError as e:
            self.logger.error(f"Connection error updating provider IDs for item {item_id}: {e}")
            return False
        except requests.exceptions.HTTPError as e:
            self.logger.error(f"HTTP error updating provider IDs for item {item_id}: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error updating provider IDs for item {item_id}: {e}", exc_info=True)
            return False

    def refresh_library_by_path(self, library_path: str) -> bool:
        """Trigger targeted library refresh for a specific path."""
        try:
            libraries = self.get_libraries()
            for lib in libraries:
                if library_path.startswith(lib.get('Path', '')):
                    response = self.session.post(
                        f"{self.server_url}/Library/Media/Updated",
                        json={'Path': library_path},
                        timeout=10
                    )
                    response.raise_for_status()
                    self.logger.info(f"Triggered targeted refresh for path: {library_path}")
                    return True

            self.logger.warning(f"No library found for path: {library_path}, falling back to full refresh")
            return self.refresh_library()
        except requests.exceptions.Timeout:
            self.logger.error(f"Timeout refreshing library by path {library_path}")
            return False
        except requests.exceptions.ConnectionError as e:
            self.logger.error(f"Connection error refreshing library by path {library_path}: {e}")
            return False
        except requests.exceptions.HTTPError as e:
            self.logger.error(f"HTTP error refreshing library by path {library_path}: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error refreshing library by path {library_path}: {e}", exc_info=True)
            return False

    def delete_item(self, item_id: str) -> bool:
        """
        Delete an item from Jellyfin library.
        
        Args:
            item_id: Jellyfin item ID to delete
            
        Returns:
            True if deletion successful, False otherwise
            
        Note:
            This removes the item from Jellyfin's library but does NOT delete
            the physical file from disk. The file remains on the filesystem.
        """
        try:
            response = self.session.delete(
                f"{self.server_url}/Items/{item_id}",
                timeout=10
            )
            response.raise_for_status()
            
            self.logger.info(f"Deleted item {item_id} from Jellyfin library")
            return True
        except requests.exceptions.Timeout:
            self.logger.error(f"Timeout deleting item {item_id}")
            return False
        except requests.exceptions.ConnectionError as e:
            self.logger.error(f"Connection error deleting item {item_id}: {e}")
            return False
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                self.logger.warning(f"Item {item_id} not found (may already be deleted)")
                return True  # Consider already deleted as success
            self.logger.error(f"HTTP error deleting item {item_id}: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error deleting item {item_id}: {e}", exc_info=True)
            return False

    def add_item_by_path(self, path: str) -> bool:
        """
        Trigger scan of new path to add items to Jellyfin library.
        
        Args:
            path: Filesystem path to scan for new items
            
        Returns:
            True if scan triggered successfully, False otherwise
        """
        try:
            # Use refresh_library_by_path which triggers a scan
            result = self.refresh_library_by_path(path)
            if result:
                self.logger.info(f"Triggered library scan for path: {path}")
            return result
        except Exception as e:
            self.logger.error(f"Error triggering scan for path {path}: {e}", exc_info=True)
            return False

    def remove_from_collection(self, collection_id: str, item_ids: List[str]) -> bool:
        """
        Remove items from an existing collection.
        
        Args:
            collection_id: Jellyfin collection ID
            item_ids: List of item IDs to remove from collection
            
        Returns:
            True if removal successful, False otherwise
        """
        try:
            # Jellyfin API: DELETE /Collections/{id}/Items with item IDs
            response = self.session.delete(
                f"{self.server_url}/Collections/{collection_id}/Items",
                params={'Ids': ','.join(item_ids)},
                timeout=10
            )
            response.raise_for_status()
            self.logger.info(f"Removed {len(item_ids)} items from collection {collection_id}")
            return True
        except requests.exceptions.Timeout:
            self.logger.error(f"Timeout removing items from collection {collection_id}")
            return False
        except requests.exceptions.ConnectionError as e:
            self.logger.error(f"Connection error removing items from collection {collection_id}: {e}")
            return False
        except requests.exceptions.HTTPError as e:
            self.logger.error(f"HTTP error removing items from collection {collection_id}: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error removing items from collection {collection_id}: {e}", exc_info=True)
            return False

    def update_item_metadata(self, item_id: str, metadata: Dict) -> bool:
        """
        Update item metadata (title, year, description, tags, etc.).
        
        Args:
            item_id: Jellyfin item ID
            metadata: Dictionary of metadata fields to update
                     (e.g., {'Name': 'New Title', 'ProductionYear': 2024})
            
        Returns:
            True if update successful, False otherwise
        """
        try:
            # Get current item data
            item = self.get_item_by_id(item_id)
            if not item:
                self.logger.warning(f"Item {item_id} not found for metadata update")
                return False
            
            # Merge metadata updates
            updated_item = item.copy()
            updated_item.update(metadata)
            updated_item['Id'] = item_id  # Ensure ID is preserved
            
            # Update via POST
            response = self.session.post(
                f"{self.server_url}/Items/{item_id}",
                json=updated_item,
                timeout=10
            )
            response.raise_for_status()
            self.logger.info(f"Updated metadata for item {item_id}: {list(metadata.keys())}")
            return True
        except requests.exceptions.Timeout:
            self.logger.error(f"Timeout updating metadata for item {item_id}")
            return False
        except requests.exceptions.ConnectionError as e:
            self.logger.error(f"Connection error updating metadata for item {item_id}: {e}")
            return False
        except requests.exceptions.HTTPError as e:
            self.logger.error(f"HTTP error updating metadata for item {item_id}: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error updating metadata for item {item_id}: {e}", exc_info=True)
            return False

    def get_item_statistics(self) -> Dict:
        """
        Get library statistics (counts, sizes, etc.).
        
        Returns:
            Dictionary with statistics:
            - total_items: Total number of items
            - by_type: Count by item type (Movie, Episode, etc.)
            - by_library: Count by library
            - total_size: Total size in bytes (if available)
        """
        try:
            items = self.get_all_items()
            
            stats = {
                'total_items': len(items),
                'by_type': defaultdict(int),
                'by_library': defaultdict(int),
                'total_size': 0
            }
            
            libraries = self.get_libraries()
            library_map = {lib['Id']: lib['Name'] for lib in libraries}
            
            for item in items:
                # Count by type
                item_type = item.get('Type', 'Unknown')
                stats['by_type'][item_type] += 1
                
                # Count by library (if available)
                library_id = item.get('ParentId')
                if library_id and library_id in library_map:
                    stats['by_library'][library_map[library_id]] += 1
                
                # Sum sizes (if available)
                media_sources = item.get('MediaSources', [])
                for source in media_sources:
                    size = source.get('Size')
                    if size:
                        stats['total_size'] += size
            
            # Convert defaultdicts to regular dicts
            stats['by_type'] = dict(stats['by_type'])
            stats['by_library'] = dict(stats['by_library'])
            
            self.logger.info(f"Retrieved statistics: {stats['total_items']} items")
            return stats
        except Exception as e:
            self.logger.error(f"Error getting statistics: {e}", exc_info=True)
            return {
                'total_items': 0,
                'by_type': {},
                'by_library': {},
                'total_size': 0
            }

    def search_items(self, query: str, filters: Optional[Dict] = None) -> List[Dict]:
        """
        Advanced search with filters.
        
        Args:
            query: Search query string
            filters: Optional filters dictionary:
                    - item_types: List of types (e.g., ['Movie', 'Episode'])
                    - genres: List of genres
                    - years: List of years
                    - libraries: List of library IDs
                    
        Returns:
            List of matching Jellyfin items
        """
        try:
            user_id = self.get_user_id()
            
            params = {
                'SearchTerm': query,
                'Recursive': 'true',
                'Fields': 'Path,ProviderIds,MediaSources'
            }
            
            if filters:
                if 'item_types' in filters:
                    params['IncludeItemTypes'] = ','.join(filters['item_types'])
            
            response = self.session.get(
                f"{self.server_url}/Users/{user_id}/Items",
                params=params,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            items = data.get('Items', [])
            
            # Apply additional filters
            if filters:
                filtered_items = []
                for item in items:
                    # Filter by genre
                    if 'genres' in filters:
                        item_genres = [g.lower() for g in item.get('Genres', [])]
                        filter_genres = [g.lower() for g in filters['genres']]
                        if not any(g in item_genres for g in filter_genres):
                            continue
                    
                    # Filter by year
                    if 'years' in filters:
                        year = item.get('ProductionYear')
                        if year and year not in filters['years']:
                            continue
                    
                    # Filter by library
                    if 'libraries' in filters:
                        parent_id = item.get('ParentId')
                        if parent_id and parent_id not in filters['libraries']:
                            continue
                    
                    filtered_items.append(item)
                items = filtered_items
            
            self.logger.info(f"Search found {len(items)} items for query: {query}")
            return items
        except RuntimeError:
            # Re-raise errors from get_user_id
            raise
        except requests.exceptions.Timeout:
            self.logger.error(f"Timeout searching items with query: {query}")
            return []
        except requests.exceptions.ConnectionError as e:
            self.logger.error(f"Connection error searching items: {e}")
            return []
        except requests.exceptions.HTTPError as e:
            self.logger.error(f"HTTP error searching items: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error searching items: {e}", exc_info=True)
            return []


if __name__ == "__main__":
    # Example usage and testing
    logging.basicConfig(level=logging.INFO)

    # Initialize client (will use environment variables if available)
    client = JellyfinClient()

    if not client.is_configured():
        print("Jellyfin not configured.")
        print("Set environment variables:")
        print("  JELLYFIN_SERVER_URL=http://localhost:8096")
        print("  JELLYFIN_API_KEY=your_api_key")
        exit(1)

    # Test connection
    print("Testing Jellyfin connection...")
    if client.test_connection():
        print("✓ Connected successfully")

        # Get libraries
        libraries = client.get_libraries()
        print(f"\nLibraries ({len(libraries)}):")
        for lib in libraries:
            print(f"  - {lib['Name']} ({lib.get('CollectionType', 'mixed')})")

        # Get sample items
        items = client.get_all_items(item_types=["Movie", "Episode"], limit=5)
        print(f"\nSample Items ({len(items)}):")
        for item in items:
            provider_ids = item.get('ProviderIds', {})
            tmdb_id = provider_ids.get('Tmdb', 'N/A')
            print(f"  - {item['Name']} (TMDb: {tmdb_id})")
    else:
        print("✗ Connection failed")
        exit(1)
