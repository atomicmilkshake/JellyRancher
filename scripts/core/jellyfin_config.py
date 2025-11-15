#!/usr/bin/env python3
"""
Jellyfin Configuration Manager

Stores Jellyfin server URL and API key securely.
Provides convenient access to configuration settings.

Configuration is stored in data/jellyfin_config.json with format:
{
    "server_url": "http://localhost:8096",
    "api_key": "your_api_key_here",
    "enabled": true,
    "auto_refresh": false
}

Environment variables take precedence over file configuration:
- JELLYFIN_SERVER_URL
- JELLYFIN_API_KEY
"""

import os
import json
import logging
from pathlib import Path
from typing import Optional


class JellyfinConfigManager:
    """Manage Jellyfin configuration."""

    def __init__(self, config_path: str = "data/jellyfin_config.json", logger: Optional[logging.Logger] = None):
        """
        Initialize configuration manager.

        Args:
            config_path: Path to configuration file
            logger: Logger instance
        """
        self.config_path = Path(config_path)
        self.logger = logger or logging.getLogger(__name__)

        # Ensure config directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        self.config = self._load_config()

    def _load_config(self) -> dict:
        """Load configuration from file."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    self.logger.debug(f"Loaded Jellyfin config from {self.config_path}")
                    return config
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse Jellyfin config: {e}")
                return {}
            except Exception as e:
                self.logger.error(f"Failed to load Jellyfin config: {e}")
                return {}
        else:
            self.logger.debug("No Jellyfin config file found, using defaults")
            return {}

    def save_config(self):
        """Save configuration to file."""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            self.logger.info(f"Saved Jellyfin config to {self.config_path}")
        except Exception as e:
            self.logger.error(f"Failed to save Jellyfin config: {e}")

    def set_server_url(self, url: str):
        """
        Set Jellyfin server URL.

        Args:
            url: Server URL (e.g., "http://localhost:8096")
        """
        self.config['server_url'] = url.rstrip('/')
        self.save_config()
        self.logger.info(f"Set Jellyfin server URL: {url}")

    def set_api_key(self, api_key: str):
        """
        Set Jellyfin API key.

        Args:
            api_key: API key from Jellyfin Dashboard > Advanced > API Keys

        Note:
            API key is stored in plain text. For enhanced security,
            consider using system keyring or encryption in future.
        """
        self.config['api_key'] = api_key
        self.save_config()
        self.logger.info("Set Jellyfin API key")

    def set_enabled(self, enabled: bool):
        """
        Enable or disable Jellyfin integration.

        Args:
            enabled: True to enable, False to disable
        """
        self.config['enabled'] = enabled
        self.save_config()
        self.logger.info(f"Jellyfin integration {'enabled' if enabled else 'disabled'}")

    def set_auto_refresh(self, auto_refresh: bool):
        """
        Enable or disable automatic library refresh after file operations.

        Args:
            auto_refresh: True to auto-refresh, False to manual
        """
        self.config['auto_refresh'] = auto_refresh
        self.save_config()
        self.logger.info(f"Jellyfin auto-refresh {'enabled' if auto_refresh else 'disabled'}")

    def get_server_url(self) -> Optional[str]:
        """
        Get Jellyfin server URL.

        Returns:
            Server URL or None if not configured

        Note:
            Environment variable JELLYFIN_SERVER_URL takes precedence
        """
        return os.getenv('JELLYFIN_SERVER_URL') or self.config.get('server_url')

    def get_api_key(self) -> Optional[str]:
        """
        Get Jellyfin API key.

        Returns:
            API key or None if not configured

        Note:
            Environment variable JELLYFIN_API_KEY takes precedence
        """
        return os.getenv('JELLYFIN_API_KEY') or self.config.get('api_key')

    def is_enabled(self) -> bool:
        """
        Check if Jellyfin integration is enabled.

        Returns:
            True if enabled, False otherwise (default: True)
        """
        return self.config.get('enabled', True)

    def is_auto_refresh_enabled(self) -> bool:
        """
        Check if automatic library refresh is enabled.

        Returns:
            True if enabled, False otherwise (default: False)
        """
        return self.config.get('auto_refresh', False)

    def is_configured(self) -> bool:
        """
        Check if Jellyfin is fully configured.

        Returns:
            True if server URL and API key are set
        """
        return bool(self.get_server_url() and self.get_api_key())

    def clear_config(self):
        """Clear all configuration settings."""
        self.config = {}
        self.save_config()
        self.logger.info("Cleared Jellyfin configuration")

    def get_config_summary(self) -> dict:
        """
        Get configuration summary (safe for display).

        Returns:
            Dict with configuration summary (API key masked)
        """
        server_url = self.get_server_url()
        api_key = self.get_api_key()

        return {
            'server_url': server_url or 'Not configured',
            'api_key_set': bool(api_key),
            'api_key_masked': f"{api_key[:8]}..." if api_key and len(api_key) > 8 else 'Not set',
            'enabled': self.is_enabled(),
            'auto_refresh': self.is_auto_refresh_enabled(),
            'source': 'environment' if (os.getenv('JELLYFIN_SERVER_URL') or os.getenv('JELLYFIN_API_KEY')) else 'config file'
        }


if __name__ == "__main__":
    # Example usage and testing
    logging.basicConfig(level=logging.INFO)

    config_manager = JellyfinConfigManager()

    # Display current configuration
    summary = config_manager.get_config_summary()
    print("Jellyfin Configuration Summary:")
    print(f"  Server URL: {summary['server_url']}")
    print(f"  API Key: {summary['api_key_masked']}")
    print(f"  Enabled: {summary['enabled']}")
    print(f"  Auto-refresh: {summary['auto_refresh']}")
    print(f"  Source: {summary['source']}")

    if not config_manager.is_configured():
        print("\nJellyfin not fully configured.")
        print("To configure:")
        print("  1. Set environment variables:")
        print("     export JELLYFIN_SERVER_URL=http://localhost:8096")
        print("     export JELLYFIN_API_KEY=your_api_key")
        print("  2. Or use GUI settings dialog in JellyRancher")
