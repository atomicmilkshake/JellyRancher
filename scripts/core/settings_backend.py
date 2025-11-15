#!/usr/bin/env python3
"""
Settings Backend - Configuration persistence and management

Handles configuration file management, credential storage, and preferences.

Features:
- JSON-based configuration storage
- Credential management integration
- Path validation
- Default settings
- Settings versioning

Usage (from UI):
    from settings_backend import SettingsManager
    
    settings = SettingsManager()
    media_root = settings.get("media_root")
    settings.set("media_root", "/path/to/media")
    settings.save()
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

# Add common modules to path
sys.path.insert(0, str(Path(__file__).parent / "_common"))

from immutable_audit import ImmutableAuditLog
from logger import ProjectLogger
from credential_manager import CredentialManager


class SettingsManager:
    """Manages application settings and configuration."""

    CONFIG_FILE = Path(__file__).parent / "config" / "settings.json"
    CONFIG_VERSION = "1.0"
    
    DEFAULT_SETTINGS = {
        "media_root": "C:/Jellyfin/#MEDIA",
        "movies_folder": "Movies",
        "tv_shows_folder": "TV Shows",
        "anime_folder": "Anime",
        "enable_dry_run": True,
        "auto_snapshot": True,
        "subtitle_languages": ["English"],
        "subtitle_providers": ["opensubtitles"],
        "batch_size": 10,
        "batch_delay": 0.5,
        "audit_log_rotation_mb": 10,
        "theme": "light",
        "window_geometry": None,
        "window_state": None,
        "last_session_date": None,
        "tmdb_api_key": ""  # TMDB API key for episode cache generation
    }

    def __init__(self):
        self.audit = ImmutableAuditLog()
        self.audit.initialize()
        self.logger = ProjectLogger("settings_manager")
        self.creds = CredentialManager()
        self.settings = self.DEFAULT_SETTINGS.copy()
        self.load()

    def load(self) -> bool:
        """
        Load settings from configuration file.
        
        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            if self.CONFIG_FILE.exists():
                with open(self.CONFIG_FILE, 'r') as f:
                    loaded = json.load(f)
                
                # Validate version
                if loaded.get("version") != self.CONFIG_VERSION:
                    self.logger.warning(f"Settings version mismatch: {loaded.get('version')} vs {self.CONFIG_VERSION}")
                
                # Merge with defaults (loaded settings override defaults)
                self.settings = {**self.DEFAULT_SETTINGS, **loaded.get("settings", {})}
                
                self.logger.info(f"Settings loaded from {self.CONFIG_FILE}")
                return True
            else:
                self.logger.info("No existing settings file found, using defaults")
                return False

        except Exception as e:
            self.logger.error(f"Failed to load settings: {str(e)}")
            return False

    def save(self) -> bool:
        """
        Save current settings to configuration file.
        
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Create config directory if needed
            self.CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)

            config = {
                "version": self.CONFIG_VERSION,
                "last_updated": datetime.now().isoformat(),
                "settings": self.settings
            }

            with open(self.CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=2)

            # Log the save operation
            self.audit.log_event("settings_save", {
                "config_file": str(self.CONFIG_FILE),
                "settings_count": len(self.settings)
            }, actor="settings_backend.py")

            self.logger.info(f"Settings saved to {self.CONFIG_FILE}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to save settings: {str(e)}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a setting value.
        
        Args:
            key: Setting key
            default: Default value if key not found
        
        Returns:
            Setting value or default
        """
        return self.settings.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """
        Set a setting value.
        
        Args:
            key: Setting key
            value: New value
        """
        old_value = self.settings.get(key)
        self.settings[key] = value
        
        if old_value != value:
            self.logger.info(f"Setting changed: {key} = {value}")

    def get_all(self) -> Dict[str, Any]:
        """Get all settings."""
        return self.settings.copy()

    def reset_to_defaults(self) -> None:
        """Reset all settings to defaults."""
        self.settings = self.DEFAULT_SETTINGS.copy()
        
        self.audit.log_event("settings_reset", {
            "reason": "user_requested"
        }, actor="settings_backend.py")

        self.logger.info("Settings reset to defaults")

    def validate_paths(self) -> Dict[str, bool]:
        """
        Validate all configured paths exist.
        
        Returns:
            Dict with path validation results
        """
        results = {}
        
        media_root = Path(self.get("media_root", ""))
        results["media_root"] = media_root.exists()

        return results

    def get_credentials(self, service: str) -> Optional[Dict[str, str]]:
        """
        Get credentials for a service.
        
        Args:
            service: Service name (e.g., "opensubtitles")
        
        Returns:
            Dict with username/password or None
        """
        try:
            username_key = f"{service}_username"
            password_key = f"{service}_password"
            
            username = self.creds.get_credential(username_key)
            password = self.creds.get_credential(password_key)
            
            if username and password:
                return {"username": username, "password": password}
            return None

        except Exception as e:
            self.logger.error(f"Failed to get credentials for {service}: {str(e)}")
            return None

    def set_credentials(self, service: str, username: str, password: str) -> bool:
        """
        Set credentials for a service.
        
        Args:
            service: Service name
            username: Username
            password: Password
        
        Returns:
            True if set successfully
        """
        try:
            self.creds.set_credential(f"{service}_username", username)
            self.creds.set_credential(f"{service}_password", password)
            
            self.audit.log_event("credentials_set", {
                "service": service
            }, actor="settings_backend.py")

            self.logger.info(f"Credentials set for {service}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to set credentials for {service}: {str(e)}")
            return False

    def get_available_services(self) -> List[str]:
        """Get list of available services."""
        return [
            "opensubtitles",
            "subscene",
            "podnapisi",
            "addic7ed",
            "yify",
            "subtitle_seeker"
        ]
    
    def get_tmdb_api_key(self) -> Optional[str]:
        """
        Get TMDB API key from settings.
        
        Returns:
            TMDB API key or None if not set
        """
        api_key = self.get("tmdb_api_key", "")
        return api_key if api_key else None
    
    def set_tmdb_api_key(self, api_key: str) -> bool:
        """
        Set TMDB API key in settings.
        
        Args:
            api_key: TMDB API key
        
        Returns:
            True if set successfully
        """
        try:
            self.set("tmdb_api_key", api_key)
            self.save()
            
            self.audit.log_event("tmdb_api_key_set", {
                "key_length": len(api_key) if api_key else 0
            }, actor="settings_backend.py")
            
            self.logger.info("TMDB API key updated")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to set TMDB API key: {str(e)}")
            return False
    
    def validate_tmdb_api_key(self) -> bool:
        """
        Check if TMDB API key is configured.
        
        Returns:
            True if API key is set and non-empty
        """
        api_key = self.get_tmdb_api_key()
        return api_key is not None and len(api_key) > 0

    def export_settings(self, filepath: str) -> bool:
        """
        Export settings to a file (without credentials).
        
        Args:
            filepath: Path to export to
        
        Returns:
            True if exported successfully
        """
        try:
            filepath = Path(filepath)
            filepath.parent.mkdir(parents=True, exist_ok=True)

            export_data = {
                "version": self.CONFIG_VERSION,
                "exported": datetime.now().isoformat(),
                "settings": self.settings
            }

            with open(filepath, 'w') as f:
                json.dump(export_data, f, indent=2)

            return True

        except Exception as e:
            self.logger.error(f"Failed to export settings: {str(e)}")
            return False

    def import_settings(self, filepath: str) -> bool:
        """
        Import settings from a file.
        
        Args:
            filepath: Path to import from
        
        Returns:
            True if imported successfully
        """
        try:
            filepath = Path(filepath)
            if not filepath.exists():
                self.logger.error(f"Import file not found: {filepath}")
                return False

            with open(filepath, 'r') as f:
                import_data = json.load(f)

            if import_data.get("version") != self.CONFIG_VERSION:
                self.logger.warning(f"Version mismatch: {import_data.get('version')} vs {self.CONFIG_VERSION}")

            # Merge imported settings
            self.settings.update(import_data.get("settings", {}))
            
            self.audit.log_event("settings_import", {
                "source_file": str(filepath)
            }, actor="settings_backend.py")

            return True

        except Exception as e:
            self.logger.error(f"Failed to import settings: {str(e)}")
            return False


# Test the backend
if __name__ == "__main__":
    settings = SettingsManager()
    
    print("Current Settings:")
    print(f"  Media Root: {settings.get('media_root')}")
    print(f"  Theme: {settings.get('theme')}")
    print(f"  Dry Run: {settings.get('enable_dry_run')}\n")
    
    print("All Settings:")
    for key, value in settings.get_all().items():
        print(f"  {key}: {value}")
    
    print("\nAvailable Services:")
    for service in settings.get_available_services():
        print(f"  • {service}")
