#!/usr/bin/env python3
"""
Media Organizer - Wrapper for media organization backend

Provides the MediaOrganizer class expected by the GUI.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime

# Add scripts to path
current_dir = Path(__file__).parent.parent
scripts_dir = current_dir / "scripts"
sys.path.insert(0, str(scripts_dir))
sys.path.insert(0, str(scripts_dir / "_common"))
sys.path.insert(0, str(scripts_dir / "core"))
sys.path.insert(0, str(scripts_dir / "media"))

try:
    from media_org_backend import MediaOrganizer as BackendMediaOrganizer
except ImportError:
    # Try alternative import path
    try:
        from scripts.media.media_org_backend import MediaOrganizer as BackendMediaOrganizer
    except ImportError:
        print("Warning: Could not import MediaOrganizer backend")
        BackendMediaOrganizer = None


class MediaOrganizer:
    """Media organizer wrapper class for GUI integration."""

    def __init__(self):
        """Initialize media organizer."""
        self.backend = BackendMediaOrganizer()
        self.last_result = None

    def organize(
        self,
        folder_path: str,
        org_type: str = "All",
        dry_run: bool = True,
        create_snapshot: bool = False,
        verify_integrity: bool = False,
        progress_callback: Optional[Callable[[str, int], None]] = None
    ) -> Dict[str, Any]:
        """
        Organize media files in folder.

        Args:
            folder_path: Path to organize
            org_type: "Movies", "TV Shows", "Anime", or "All"
            dry_run: If True, preview only
            create_snapshot: Create snapshot before changes
            verify_integrity: Verify file integrity after moves
            progress_callback: Optional progress callback

        Returns:
            Dict with results
        """
        try:
            # Call the backend organize method
            result = self.backend.organize(
                folder_path=folder_path,
                org_type=org_type,
                dry_run=dry_run,
                create_snapshot=create_snapshot,
                verify_integrity=verify_integrity,
                progress_callback=progress_callback
            )

            # Add additional metadata
            result.update({
                "timestamp": datetime.now().isoformat(),
                "organizer_version": "1.0",
                "success": True
            })

            self.last_result = result
            return result

        except Exception as e:
            error_result = {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "timestamp": datetime.now().isoformat(),
                "files_moved": 0,
                "errors": [str(e)]
            }
            self.last_result = error_result
            return error_result
