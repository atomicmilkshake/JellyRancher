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


@dataclass
class JellyfinConfig:
    """Jellyfin server configuration."""
    server_url: str  # e.g., "http://localhost:8096"
    api_key: str
    user_id: Optional[str] = None  # Auto-detected if None


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
            requests.exceptions.HTTPError: If API request fails
        """
        if self.user_id:
            return self.user_id

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
        # Normalize path for Windows/Linux compatibility
        search_path = str(file_path.resolve()).replace('\\', '/')

        # Query items with path field
        try:
            items = self.get_all_items(fields=['Path', 'ProviderIds'])
        except Exception as e:
            self.logger.error(f"Failed to query Jellyfin items: {e}")
            return None

        for item in items:
            item_path = item.get('Path', '').replace('\\', '/')
            if item_path == search_path:
                self.logger.debug(f"Found Jellyfin match: {item.get('Name')} (ID: {item.get('Id')})")
                return item

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
        params = {}
        if fields:
            params['Fields'] = ','.join(fields)

        try:
            response = self.session.get(
                f"{self.server_url}/Items/{item_id}",
                params=params,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                self.logger.warning(f"Item not found: {item_id}")
            else:
                self.logger.error(f"Failed to get item {item_id}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error getting item {item_id}: {e}")
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
        item = self.get_item_by_id(item_id, fields=['ProviderIds'])

        if item:
            return item.get('ProviderIds', {})
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
        params = {
            'ReplaceAllMetadata': 'true' if replace_metadata else 'false',
            'ReplaceAllImages': 'false'
        }

        try:
            response = self.session.post(
                f"{self.server_url}/Items/{item_id}/Refresh",
                params=params,
                timeout=10
            )
            response.raise_for_status()

            self.logger.info(f"Triggered refresh for item {item_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to refresh item {item_id}: {e}")
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
        except Exception as e:
            self.logger.error(f"Failed to refresh library: {e}")
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
        user_id = self.get_user_id()

        try:
            response = self.session.get(
                f"{self.server_url}/Users/{user_id}/Views",
                timeout=10
            )
            response.raise_for_status()

            data = response.json()
            libraries = data.get('Items', [])

            self.logger.info(f"Retrieved {len(libraries)} libraries")
            return libraries
        except Exception as e:
            self.logger.error(f"Failed to get libraries: {e}")
            return []

    def get_media_streams(self, item_id: str) -> List[Dict]:
        """
        Get media streams (video, audio, subtitle) for an item.

        Args:
            item_id: Jellyfin item ID

        Returns:
            List of media stream dictionaries
        """
        item = self.get_item_by_id(item_id, fields=['MediaStreams'])

        if item and 'MediaSources' in item:
            for source in item['MediaSources']:
                if 'MediaStreams' in source:
                    return source['MediaStreams']

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
        streams = self.get_media_streams(item_id)

        for stream in streams:
            if stream.get('Type') == 'Subtitle' and stream.get('Language', '').lower() == language.lower():
                return True

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
        except Exception as e:
            self.logger.error(f"Failed to create collection '{name}': {e}")
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
        except Exception as e:
            self.logger.error(f"Failed to add items to collection {collection_id}: {e}")
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
        except Exception as e:
            self.logger.error(f"Failed to get collections: {e}")
            return []

    def update_provider_ids(self, item_id: str, provider_ids: Dict[str, str]) -> bool:
        """Update provider IDs for an item (TMDb, TVDb, IMDb)."""
        try:
            item = self.get_item_by_id(item_id)
            if not item:
                return False

            current_providers = item.get('ProviderIds', {})
            current_providers.update(provider_ids)

            response = self.session.post(
                f"{self.server_url}/Items/{item_id}",
                json={'Id': item_id, 'ProviderIds': current_providers},
                timeout=10
            )
            response.raise_for_status()
            self.logger.info(f"Updated provider IDs for item {item_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to update provider IDs for {item_id}: {e}")
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
                    self.logger.info(f"Triggered refresh for path: {library_path}")
                    return True

            self.logger.warning(f"No library found for path: {library_path}")
            return self.refresh_library()
        except Exception as e:
            self.logger.error(f"Failed to refresh path {library_path}: {e}")
            return False


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
