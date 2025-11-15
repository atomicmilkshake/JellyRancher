#!/usr/bin/env python3
"""
Application Configuration Manager

Stores general application settings like destination base paths,
reorganization strategies, and user preferences.

Configuration is stored in data/app_config.json with format:
{
    "destination_movies_base": "V:/Movies",
    "destination_tv_base": "V:/TV Shows",
    "reorganization_strategy": "user_choice",
    "auto_approve_high_confidence": true,
    "show_subtitles_in_table": true,
    "duplicate_keep_strategy": "jellyfin_first"
}
"""

import json
import logging
from pathlib import Path
from typing import Optional, Literal


ReorganizationStrategy = Literal["llm", "canonical", "hybrid", "user_choice"]
DuplicateKeepStrategy = Literal["jellyfin_first", "largest_file", "manual"]


class AppConfigManager:
    """Manage application configuration settings."""

    DEFAULT_CONFIG = {
        "destination_movies_base": "",  # User must configure
        "destination_tv_base": "",  # User must configure
        "reorganization_strategy": "user_choice",
        "auto_approve_high_confidence": True,
        "show_subtitles_in_table": True,
        "duplicate_keep_strategy": "jellyfin_first",
        "subtitle_auto_approve": True,
        "md5_verify_operations": True,
    }

    def __init__(self, config_path: str = "data/app_config.json", logger: Optional[logging.Logger] = None):
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
                    loaded_config = json.load(f)
                    # Merge with defaults to handle new config keys
                    config = {**self.DEFAULT_CONFIG, **loaded_config}
                    self.logger.debug(f"Loaded app config from {self.config_path}")
                    return config
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse app config: {e}")
                return self.DEFAULT_CONFIG.copy()
            except Exception as e:
                self.logger.error(f"Failed to load app config: {e}")
                return self.DEFAULT_CONFIG.copy()
        else:
            self.logger.debug("No app config file found, using defaults")
            return self.DEFAULT_CONFIG.copy()

    def save_config(self):
        """Save configuration to file."""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            self.logger.info(f"Saved app config to {self.config_path}")
        except Exception as e:
            self.logger.error(f"Failed to save app config: {e}")

    # --- Destination Base Paths ---

    def set_movies_base(self, path: str):
        """Set destination base path for movies."""
        self.config['destination_movies_base'] = str(Path(path))
        self.save_config()
        self.logger.info(f"Set movies base path: {path}")

    def set_tv_base(self, path: str):
        """Set destination base path for TV shows."""
        self.config['destination_tv_base'] = str(Path(path))
        self.save_config()
        self.logger.info(f"Set TV base path: {path}")

    def get_movies_base(self) -> Optional[Path]:
        """Get destination base path for movies."""
        path_str = self.config.get('destination_movies_base', '')
        return Path(path_str) if path_str else None

    def get_tv_base(self) -> Optional[Path]:
        """Get destination base path for TV shows."""
        path_str = self.config.get('destination_tv_base', '')
        return Path(path_str) if path_str else None

    # --- Reorganization Strategy ---

    def set_reorganization_strategy(self, strategy: ReorganizationStrategy):
        """
        Set reorganization strategy.

        Args:
            strategy: One of "llm", "canonical", "hybrid", "user_choice"
        """
        valid_strategies = ["llm", "canonical", "hybrid", "user_choice"]
        if strategy not in valid_strategies:
            raise ValueError(f"Invalid strategy. Must be one of: {valid_strategies}")

        self.config['reorganization_strategy'] = strategy
        self.save_config()
        self.logger.info(f"Set reorganization strategy: {strategy}")

    def get_reorganization_strategy(self) -> ReorganizationStrategy:
        """Get reorganization strategy."""
        return self.config.get('reorganization_strategy', 'user_choice')

    # --- Duplicate Handling ---

    def set_duplicate_strategy(self, strategy: DuplicateKeepStrategy):
        """
        Set duplicate keep strategy.

        Args:
            strategy: One of "jellyfin_first", "largest_file", "manual"
        """
        valid_strategies = ["jellyfin_first", "largest_file", "manual"]
        if strategy not in valid_strategies:
            raise ValueError(f"Invalid strategy. Must be one of: {valid_strategies}")

        self.config['duplicate_keep_strategy'] = strategy
        self.save_config()
        self.logger.info(f"Set duplicate strategy: {strategy}")

    def get_duplicate_strategy(self) -> DuplicateKeepStrategy:
        """Get duplicate keep strategy."""
        return self.config.get('duplicate_keep_strategy', 'jellyfin_first')

    # --- Auto-Approval Settings ---

    def set_auto_approve_high_confidence(self, enabled: bool):
        """Enable/disable auto-approval of high confidence operations."""
        self.config['auto_approve_high_confidence'] = enabled
        self.save_config()
        self.logger.info(f"Auto-approve high confidence: {enabled}")

    def is_auto_approve_high_confidence(self) -> bool:
        """Check if auto-approval of high confidence operations is enabled."""
        return self.config.get('auto_approve_high_confidence', True)

    def set_subtitle_auto_approve(self, enabled: bool):
        """Enable/disable auto-approval of subtitle operations."""
        self.config['subtitle_auto_approve'] = enabled
        self.save_config()
        self.logger.info(f"Subtitle auto-approve: {enabled}")

    def is_subtitle_auto_approve(self) -> bool:
        """Check if auto-approval of subtitle operations is enabled."""
        return self.config.get('subtitle_auto_approve', True)

    # --- UI Settings ---

    def set_show_subtitles_in_table(self, enabled: bool):
        """Enable/disable showing subtitle files in action table."""
        self.config['show_subtitles_in_table'] = enabled
        self.save_config()
        self.logger.info(f"Show subtitles in table: {enabled}")

    def is_show_subtitles_in_table(self) -> bool:
        """Check if subtitle files should be shown in action table."""
        return self.config.get('show_subtitles_in_table', True)

    # --- Verification Settings ---

    def set_md5_verify_operations(self, enabled: bool):
        """Enable/disable MD5 verification for file operations."""
        self.config['md5_verify_operations'] = enabled
        self.save_config()
        self.logger.info(f"MD5 verification: {enabled}")

    def is_md5_verify_operations(self) -> bool:
        """Check if MD5 verification is enabled."""
        return self.config.get('md5_verify_operations', True)

    # --- Validation ---

    def is_configured(self) -> bool:
        """
        Check if application is fully configured.

        Returns:
            True if both destination base paths are set
        """
        movies_base = self.get_movies_base()
        tv_base = self.get_tv_base()
        return bool(movies_base and tv_base)

    def get_config_summary(self) -> dict:
        """
        Get configuration summary for display.

        Returns:
            Dict with configuration summary
        """
        movies_base = self.get_movies_base()
        tv_base = self.get_tv_base()

        return {
            'movies_base': str(movies_base) if movies_base else 'Not configured',
            'tv_base': str(tv_base) if tv_base else 'Not configured',
            'reorganization_strategy': self.get_reorganization_strategy(),
            'duplicate_strategy': self.get_duplicate_strategy(),
            'auto_approve_high_confidence': self.is_auto_approve_high_confidence(),
            'subtitle_auto_approve': self.is_subtitle_auto_approve(),
            'show_subtitles_in_table': self.is_show_subtitles_in_table(),
            'md5_verify': self.is_md5_verify_operations(),
        }


if __name__ == "__main__":
    # Example usage and testing
    logging.basicConfig(level=logging.INFO)

    config_manager = AppConfigManager()

    # Display current configuration
    summary = config_manager.get_config_summary()
    print("Application Configuration Summary:")
    print(f"  Movies Base: {summary['movies_base']}")
    print(f"  TV Base: {summary['tv_base']}")
    print(f"  Reorganization Strategy: {summary['reorganization_strategy']}")
    print(f"  Duplicate Strategy: {summary['duplicate_strategy']}")
    print(f"  Auto-approve High Confidence: {summary['auto_approve_high_confidence']}")
    print(f"  Subtitle Auto-approve: {summary['subtitle_auto_approve']}")
    print(f"  Show Subtitles in Table: {summary['show_subtitles_in_table']}")
    print(f"  MD5 Verification: {summary['md5_verify']}")

    if not config_manager.is_configured():
        print("\nApplication not fully configured.")
        print("Please set destination base paths for Movies and TV Shows.")
