#!/usr/bin/env python3
"""
Media File Scanner - Wrapper for media scanning backend

Provides the MediaFileScanner class expected by the GUI.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime

# Add scripts to path
current_dir = Path(__file__).parent
scripts_dir = current_dir / "scripts"
sys.path.insert(0, str(scripts_dir))
sys.path.insert(0, str(scripts_dir / "media"))

from media_scanner import MediaFileScanner as BackendMediaFileScanner


class MediaFileScanner:
    """Media file scanner wrapper class for GUI integration."""

    def __init__(self, folder_path: str):
        """Initialize media file scanner.

        Args:
            folder_path: Path to scan
        """
        self.folder_path = folder_path
        self.backend = BackendMediaFileScanner(source_dir=folder_path)
        self.last_result = None

    def scan_files(self) -> List[Dict[str, Any]]:
        """
        Scan all files in the folder and categorize them.

        Returns:
            List of file dictionaries with metadata
        """
        try:
            # Call the backend scan method
            files = self.backend.scan_files()

            # Add additional metadata
            result = {
                "files": files,
                "total_files": len(files),
                "timestamp": datetime.now().isoformat(),
                "scanner_version": "1.0",
                "success": True
            }

            # Count categories
            categories = {}
            for file_info in files:
                category = file_info.get('category', 'unknown')
                categories[category] = categories.get(category, 0) + 1

            result["categories"] = categories
            self.last_result = result
            return files  # Return just the files list as expected by GUI

        except Exception as e:
            error_result = {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "timestamp": datetime.now().isoformat(),
                "files": [],
                "total_files": 0
            }
            self.last_result = error_result
            return []  # Return empty list on error