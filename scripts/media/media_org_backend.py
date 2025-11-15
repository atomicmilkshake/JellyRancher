#!/usr/bin/env python3
"""
Media Organization Backend - Unified interface for UI

Provides high-level organization functions that the PyQt5 UI can call.
Handles movies, TV shows, and anime with unified interface.

Features:
- Folder scanning with progress callback
- Organization with dry-run mode
- Audit trail integration
- Snapshot creation
- Error handling and rollback

Usage (from UI):
    from media_org_backend import MediaOrganizer
    
    organizer = MediaOrganizer()
    
    # Scan folder
    stats = organizer.scan_folder(folder_path, progress_callback)
    
    # Organize media
    result = organizer.organize(
        folder_path,
        org_type="Movies",
        dry_run=True,
        create_snapshot=True,
        progress_callback=callback
    )
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime
from enum import Enum

# Add common modules to path
sys.path.insert(0, str(Path(__file__).parent / "_common"))

from immutable_audit import ImmutableAuditLog
from snapshot_manager import SnapshotManager
from media_utils import normalize_windows_path, hash_file
from logger import ProjectLogger

# Import NFO backend for multi-part episode handling
try:
    from nfo_backend import NFOBackend
    _HAS_NFO_BACKEND = True
except ImportError:
    _HAS_NFO_BACKEND = False


class OrganizationType(Enum):
    """Media organization types."""
    MOVIES = "Movies"
    TV_SHOWS = "TV Shows"
    ANIME = "Anime"


class MediaScanStats:
    """Statistics from media scan."""
    def __init__(self):
        self.total_files = 0
        self.video_files = 0
        self.subtitle_files = 0
        self.other_files = 0
        self.total_size_bytes = 0
        self.folders_found = 0
        self.duplicates = []
        self.errors = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_files": self.total_files,
            "video_files": self.video_files,
            "subtitle_files": self.subtitle_files,
            "other_files": self.other_files,
            "total_size_mb": self.total_size_bytes / (1024 * 1024),
            "folders_found": self.folders_found,
            "duplicates_count": len(self.duplicates),
            "errors_count": len(self.errors)
        }


class MediaOrganizer:
    """High-level media organization interface for UI."""

    MEDIA_EXTENSIONS = {
        '.mkv', '.mp4', '.avi', '.m4v', '.mov', '.wmv', '.flv',
        '.webm', '.mpeg', '.mpg', '.m2ts', '.ts', '.vob', '.ogv', '.3gp'
    }

    SUBTITLE_EXTENSIONS = {'.srt', '.ass', '.ssa', '.vtt', '.sub'}

    def __init__(self):
        self.audit = ImmutableAuditLog()
        self.audit.initialize()
        self.logger = ProjectLogger("media_org_backend")

    def scan_folder(
        self,
        folder_path: str,
        progress_callback: Optional[Callable[[str, int], None]] = None
    ) -> MediaScanStats:
        """
        Scan folder for media files.
        
        Args:
            folder_path: Path to scan
            progress_callback: Optional callback(message, percent) for progress updates
        
        Returns:
            MediaScanStats with scan results
        """
        stats = MediaScanStats()
        folder = Path(folder_path)

        if not folder.exists():
            stats.errors.append(f"Folder not found: {folder_path}")
            return stats

        if progress_callback:
            progress_callback(f"Scanning {folder_path}...", 0)

        try:
            all_files = list(folder.rglob("*"))
            total = len(all_files)

            for idx, file_path in enumerate(all_files):
                # Update progress every 10 files
                if idx % 10 == 0 and progress_callback:
                    percent = int((idx / max(total, 1)) * 100)
                    progress_callback(
                        f"Scanned {idx}/{total} items ({stats.video_files} videos, "
                        f"{stats.subtitle_files} subtitles)",
                        percent
                    )

                if file_path.is_file():
                    stats.total_files += 1
                    stats.total_size_bytes += file_path.stat().st_size

                    ext = file_path.suffix.lower()
                    if ext in self.MEDIA_EXTENSIONS:
                        stats.video_files += 1
                    elif ext in self.SUBTITLE_EXTENSIONS:
                        stats.subtitle_files += 1
                    else:
                        stats.other_files += 1

                elif file_path.is_dir():
                    stats.folders_found += 1

            if progress_callback:
                progress_callback("Scan complete", 100)

            # Log scan result
            self.audit.log_event("media_scan", {
                "folder": str(folder_path),
                "total_files": stats.total_files,
                "video_files": stats.video_files,
                "subtitle_files": stats.subtitle_files,
                "folders": stats.folders_found,
                "total_size_mb": stats.total_size_bytes / (1024 * 1024)
            }, actor="media_org_backend.py")

            return stats

        except Exception as e:
            error_msg = f"Error scanning folder: {str(e)}"
            stats.errors.append(error_msg)
            self.logger.error(error_msg)
            return stats

    def organize(
        self,
        folder_path: str,
        org_type: str = "Movies",
        dry_run: bool = True,
        create_snapshot: bool = True,
        verify_integrity: bool = True,
        progress_callback: Optional[Callable[[str, int], None]] = None
    ) -> Dict[str, Any]:
        """
        Organize media in folder.
        
        Args:
            folder_path: Path to organize
            org_type: "Movies", "TV Shows", or "Anime"
            dry_run: If True, don't move files
            create_snapshot: If True, create pre-operation snapshot
            verify_integrity: If True, verify file hashes
            progress_callback: Optional callback(message, percent) for updates
        
        Returns:
            Dict with result status and details
        """
        try:
            folder = Path(folder_path)
            if not folder.exists():
                return {
                    "success": False,
                    "error": f"Folder not found: {folder_path}",
                    "files_moved": 0,
                    "errors": 1
                }

            if progress_callback:
                progress_callback(f"Initializing {org_type} organization...", 0)

            # Create snapshot if requested
            snapshot_id = None
            if create_snapshot:
                if progress_callback:
                    progress_callback("Creating pre-operation snapshot...", 5)

                snapshot_id = SnapshotManager.create_snapshot(
                    media_root=str(folder),
                    snapshot_type=f"pre_organization_{org_type.lower().replace(' ', '_')}"
                )

                self.audit.log_event("snapshot_create", {
                    "snapshot_id": snapshot_id,
                    "folder": str(folder_path),
                    "org_type": org_type
                }, actor="media_org_backend.py")

            # Scan for media files
            if progress_callback:
                progress_callback("Scanning for media files...", 10)

            media_files = []
            for ext in self.MEDIA_EXTENSIONS:
                media_files.extend(folder.rglob(f"*{ext}"))

            total_files = len(media_files)
            if progress_callback:
                progress_callback(f"Found {total_files} media files", 20)

            # Process files
            files_moved = 0
            errors = []

            for idx, media_file in enumerate(media_files):
                try:
                    if progress_callback:
                        percent = 20 + int((idx / max(total_files, 1)) * 70)
                        progress_callback(
                            f"Processing {media_file.name}...",
                            percent
                        )

                    # Determine destination based on org_type
                    dest_path = self._get_destination_path(media_file, org_type)

                    if not dry_run:
                        # Hash verification before move
                        if verify_integrity:
                            hash_before = hash_file(media_file)

                        # Move file
                        dest_path.parent.mkdir(parents=True, exist_ok=True)
                        media_file.rename(dest_path)

                        # Hash verification after move
                        if verify_integrity:
                            hash_after = hash_file(dest_path)
                            if hash_before != hash_after:
                                raise ValueError(f"Hash mismatch after move: {media_file.name}")

                        # Log the move
                        self.audit.log_event("move", {
                            "source": str(media_file),
                            "destination": str(dest_path),
                            "file_hash": hash_before if verify_integrity else None,
                            "org_type": org_type,
                            "snapshot_id": snapshot_id
                        }, actor="media_org_backend.py")

                    files_moved += 1

                except Exception as e:
                    error_msg = f"Error processing {media_file.name}: {str(e)}"
                    errors.append(error_msg)
                    self.logger.error(error_msg)

            # Generate NFO files for multi-part episodes if NFO backend is available
            nfo_created = 0
            if _HAS_NFO_BACKEND and not dry_run:
                if progress_callback:
                    progress_callback("Checking for multi-part episodes...", 90)

                nfo_backend = NFOBackend()
                nfo_result = nfo_backend.scan_and_generate_nfos(str(folder))

                if nfo_result["success"]:
                    nfo_created = nfo_result.get("nfo_created", 0)
                    if progress_callback:
                        progress_callback(f"Generated {nfo_created} NFO files for multi-part episodes", 95)
                else:
                    errors.append(f"NFO generation failed: {nfo_result.get('error', 'Unknown error')}")

            if progress_callback:
                progress_callback("Organization complete", 100)

            result = {
                "success": len(errors) == 0,
                "files_moved": files_moved,
                "nfo_created": nfo_created,
                "errors": len(errors),
                "error_details": errors,
                "snapshot_id": snapshot_id,
                "dry_run": dry_run,
                "org_type": org_type
            }

            # Log completion
            self.audit.log_event("organization_complete", result, actor="media_org_backend.py")

            return result

        except Exception as e:
            error_msg = f"Organization failed: {str(e)}"
            self.logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "files_moved": 0,
                "errors": 1
            }

    def _get_destination_path(self, media_file: Path, org_type: str) -> Path:
        """
        Determine destination path based on organization type.
        
        Movies: Movies/{Title} ({Year})/{Title} ({Year}).{ext}
        TV Shows: TV Shows/{Title}/Season {NN}/{Title} - S{NN}E{NN}.{ext}
        Anime: Same as TV Shows
        """
        # Extract base name and extension
        name_parts = media_file.stem.split(" - ")
        base_name = name_parts[0] if name_parts else media_file.stem
        ext = media_file.suffix

        # Use media root (parent of parent typically)
        media_root = media_file.parent

        if org_type == "Movies":
            # Movies/{Title} ({Year})/{Title} ({Year}).{ext}
            movie_folder = media_root / "Movies" / base_name
            return movie_folder / f"{base_name}{ext}"

        elif org_type == "TV Shows":
            # TV Shows/{Title}/Season {NN}/{Title} - S{NN}E{NN}.{ext}
            # This would need episode parsing
            show_name = base_name
            season_num = 1
            episode_num = 1
            
            show_folder = media_root / "TV Shows" / show_name / f"Season {season_num:02d}"
            return show_folder / f"{show_name} - S{season_num:02d}E{episode_num:02d}{ext}"

        elif org_type == "Anime":
            # Same as TV Shows
            show_name = base_name
            season_num = 1
            episode_num = 1
            
            show_folder = media_root / "Anime" / show_name / f"Season {season_num:02d}"
            return show_folder / f"{show_name} - S{season_num:02d}E{episode_num:02d}{ext}"

        else:
            # Default: keep in parent folder
            return media_file

    def rollback_snapshot(self, snapshot_id: str) -> Dict[str, Any]:
        """
        Restore from a snapshot.
        
        Args:
            snapshot_id: ID of snapshot to restore
        
        Returns:
            Dict with restoration status
        """
        try:
            SnapshotManager.restore_snapshot(snapshot_id)

            self.audit.log_event("snapshot_restore", {
                "snapshot_id": snapshot_id,
                "timestamp": datetime.now().isoformat()
            }, actor="media_org_backend.py")

            return {
                "success": True,
                "snapshot_id": snapshot_id,
                "message": "Snapshot restored successfully"
            }

        except Exception as e:
            error_msg = f"Rollback failed: {str(e)}"
            self.logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg
            }


# Test the backend
if __name__ == "__main__":
    organizer = MediaOrganizer()

    def progress_callback(msg: str, percent: int):
        print(f"[{percent:3d}%] {msg}")

    # Test scan
    test_folder = r"C:\test_media"
    if Path(test_folder).exists():
        print("Testing scan...")
        stats = organizer.scan_folder(test_folder, progress_callback)
        print(f"Stats: {stats.to_dict()}")
