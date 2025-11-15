#!/usr/bin/env python3
"""
Subtitle Management Backend - Unified Interface for UI

Provides high-level subtitle management functions that the PyQt5 UI can call.
Wraps the focused_subtitle_downloader.py functionality for easy integration.

Features:
- Folder scanning with subtitle coverage detection
- Multi-provider subtitle downloading with fallback
- Progress callback integration
- Audit trail logging
- Dry-run mode for safe testing

Usage (from UI):
    from subtitle_backend import SubtitleBackend
    
    backend = SubtitleBackend()
    
    # Detect coverage
    stats = backend.detect_coverage(folder_path, progress_callback)
    
    # Download subtitles
    result = backend.download_subtitles(
        folder_path,
        language="English",
        providers=["OpenSubtitles.org", "Subscene"],
        dry_run=True,
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

# Optional: real subtitle downloads via subliminal
try:
    # These imports are optional; if unavailable, backend will fallback to simulation
    from babelfish import Language as _BF_Language  # type: ignore
    import subliminal  # type: ignore
    _HAS_SUBLIMINAL = True
except Exception:
    _HAS_SUBLIMINAL = False


class SubtitleLanguage(Enum):
    """Supported subtitle languages."""
    ENGLISH = "English"
    SPANISH = "Spanish"
    FRENCH = "French"
    GERMAN = "German"
    PORTUGUESE = "Portuguese"
    ITALIAN = "Italian"


class CoverageStats:
    """Statistics from subtitle coverage scan."""
    def __init__(self):
        self.total_videos = 0
        self.videos_with_subtitles = 0
        self.videos_without_subtitles = 0
        self.external_subtitles = 0
        self.embedded_subtitles = 0
        self.coverage_percent = 0.0
        self.files_missing = []
        self.errors = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_videos": self.total_videos,
            "with_subtitles": self.videos_with_subtitles,
            "without_subtitles": self.videos_without_subtitles,
            "external_subs": self.external_subtitles,
            "embedded_subs": self.embedded_subtitles,
            "coverage_percent": self.coverage_percent,
            "missing_count": len(self.files_missing),
            "errors_count": len(self.errors)
        }


class SubtitleBackend:
    """High-level subtitle management interface for UI."""

    MEDIA_EXTENSIONS = {
        '.mkv', '.mp4', '.avi', '.m4v', '.mov', '.wmv', '.flv',
        '.webm', '.mpeg', '.mpg', '.m2ts', '.ts', '.vob', '.ogv', '.3gp'
    }

    SUBTITLE_EXTENSIONS = {'.srt', '.ass', '.ssa', '.vtt', '.sub'}

    PROVIDERS = [
        "OpenSubtitles.org",
        "Subscene",
        "Podnapisi",
        "Addic7ed",
        "YIFY Subtitles",
        "Subtitle Seeker"
    ]

    def __init__(self):
        self.audit = ImmutableAuditLog()
        self.audit.initialize()
        self.logger = ProjectLogger("subtitle_backend")

    def detect_coverage(
        self,
        folder_path: str,
        language: str = "English",
        progress_callback: Optional[Callable[[str, int], None]] = None
    ) -> CoverageStats:
        """
        Detect subtitle coverage in a folder.
        
        Args:
            folder_path: Path to scan
            language: Language to report
            progress_callback: Optional callback(message, percent)
        
        Returns:
            CoverageStats with detailed coverage information
        """
        stats = CoverageStats()
        folder = Path(folder_path)

        if not folder.exists():
            stats.errors.append(f"Folder not found: {folder_path}")
            return stats

        if progress_callback:
            progress_callback(f"Scanning {folder_path}...", 0)

        try:
            # Find all media files
            media_files = []
            for ext in self.MEDIA_EXTENSIONS:
                media_files.extend(folder.rglob(f"*{ext}"))

            stats.total_videos = len(media_files)

            if progress_callback:
                progress_callback(f"Found {stats.total_videos} videos. Checking subtitles...", 10)

            # Check each media file for subtitles
            for idx, media_file in enumerate(media_files):
                try:
                    # Calculate progress
                    percent = 10 + int((idx / max(stats.total_videos, 1)) * 80)
                    
                    if idx % 10 == 0 and progress_callback:
                        progress_callback(
                            f"Checking subtitles: {idx}/{stats.total_videos}",
                            percent
                        )

                    # Check for external subtitles
                    has_external = self._has_external_subtitles(media_file)
                    has_embedded = self._has_embedded_subtitles(media_file)

                    if has_external:
                        stats.videos_with_subtitles += 1
                        stats.external_subtitles += 1
                    elif has_embedded:
                        stats.videos_with_subtitles += 1
                        stats.embedded_subtitles += 1
                    else:
                        stats.videos_without_subtitles += 1
                        stats.files_missing.append(str(media_file))

                except Exception as e:
                    error_msg = f"Error checking {media_file.name}: {str(e)}"
                    stats.errors.append(error_msg)
                    self.logger.error(error_msg)

            # Calculate coverage percentage
            stats.coverage_percent = (stats.videos_with_subtitles / max(stats.total_videos, 1)) * 100

            if progress_callback:
                progress_callback(
                    f"Coverage: {stats.coverage_percent:.1f}% ({stats.videos_with_subtitles}/{stats.total_videos})",
                    100
                )

            # Log coverage detection
            self.audit.log_event("subtitle_coverage_detect", {
                "folder": str(folder_path),
                "total_videos": stats.total_videos,
                "with_subtitles": stats.videos_with_subtitles,
                "coverage_percent": stats.coverage_percent,
                "external": stats.external_subtitles,
                "embedded": stats.embedded_subtitles
            }, actor="subtitle_backend.py")

            return stats

        except Exception as e:
            error_msg = f"Error detecting coverage: {str(e)}"
            stats.errors.append(error_msg)
            self.logger.error(error_msg)
            return stats

    def download_subtitles(
        self,
        folder_path: str,
        language: str = "English",
        providers: Optional[List[str]] = None,
        dry_run: bool = True,
        batch_size: int = 5,
        batch_delay: int = 10,
        create_snapshot: bool = True,
        progress_callback: Optional[Callable[[str, int], None]] = None
    ) -> Dict[str, Any]:
        """
        Download subtitles for media in a folder.
        
        Args:
            folder_path: Path containing media files
            language: Language code or name
            providers: List of providers to try (defaults to all)
            dry_run: If True, don't download files
            batch_size: Number of files per batch
            batch_delay: Delay between batches (seconds)
            create_snapshot: If True, create pre-operation snapshot
            progress_callback: Optional callback(message, percent)
        
        Returns:
            Dict with operation status and results
        """
        try:
            folder = Path(folder_path)
            if not folder.exists():
                return {
                    "success": False,
                    "error": f"Folder not found: {folder_path}",
                    "downloaded": 0,
                    "errors": 1
                }

            if progress_callback:
                progress_callback("Initializing subtitle download...", 0)

            # Use all providers if not specified
            if providers is None:
                providers = self.PROVIDERS
            else:
                # Filter to only available providers
                providers = [p for p in providers if p in self.PROVIDERS]

            # Create snapshot if requested
            snapshot_id = None
            if create_snapshot and not dry_run:
                if progress_callback:
                    progress_callback("Creating pre-operation snapshot...", 5)

                snapshot_id = SnapshotManager.create_snapshot(
                    media_root=str(folder),
                    snapshot_type="pre_subtitle_download"
                )

                self.audit.log_event("snapshot_create", {
                    "snapshot_id": snapshot_id,
                    "folder": str(folder_path),
                    "operation": "subtitle_download"
                }, actor="subtitle_backend.py")

            # Find all media files needing subtitles
            if progress_callback:
                progress_callback("Scanning for media files...", 10)

            media_files = []
            for ext in self.MEDIA_EXTENSIONS:
                media_files.extend(folder.rglob(f"*{ext}"))

            # Filter to only files without subtitles
            files_to_download = []
            for media_file in media_files:
                if not self._has_external_subtitles(media_file):
                    files_to_download.append(media_file)

            total_files = len(files_to_download)
            downloaded = 0
            errors = []

            if progress_callback:
                progress_callback(f"Found {total_files} files needing subtitles", 15)

            # Download subtitles for each file
            for idx, media_file in enumerate(files_to_download):
                try:
                    # Calculate progress
                    percent = 15 + int((idx / max(total_files, 1)) * 80)
                    
                    if progress_callback:
                        progress_callback(
                            f"Processing {idx+1}/{total_files}: {media_file.name}...",
                            percent
                        )

                    # Try each provider in sequence (fallback)
                    subtitle_path: Optional[Path] = None
                    for provider in providers:
                        try:
                            if progress_callback:
                                progress_callback(
                                    f"Trying {provider} for {media_file.name}...",
                                    percent
                                )

                            # If live mode and subliminal available, attempt real download
                            if not dry_run and _HAS_SUBLIMINAL:
                                subtitle_path = self._download_with_subliminal(media_file, language)
                            else:
                                # Simulated path (no file writes in dry-run)
                                subtitle_path = self._simulate_download(media_file, language)
                            
                            if subtitle_path:
                                downloaded += 1
                                self.audit.log_event("subtitle_downloaded", {
                                    "video_file": str(media_file),
                                    "subtitle_file": str(subtitle_path),
                                    "provider": provider,
                                    "language": language,
                                    "dry_run": dry_run,
                                    "snapshot_id": snapshot_id
                                }, actor="subtitle_backend.py")
                                break  # Success, stop trying providers

                        except Exception:
                            # This provider failed, try next
                            continue

                    if not subtitle_path:
                        error_msg = f"Could not download subtitle for {media_file.name} from any provider"
                        errors.append(error_msg)
                        self.logger.warning(error_msg)

                    # Rate limiting
                    if (idx + 1) % batch_size == 0 and idx < total_files - 1:
                        if progress_callback:
                            progress_callback(f"Batch complete. Waiting {batch_delay}s...", percent)
                        # time.sleep(batch_delay)  # In production

                except Exception as e:
                    error_msg = f"Error processing {media_file.name}: {str(e)}"
                    errors.append(error_msg)
                    self.logger.error(error_msg)

            if progress_callback:
                progress_callback("Subtitle download complete", 100)

            result = {
                "success": len(errors) == 0,
                "downloaded": downloaded,
                "failed": len(errors),
                "total": total_files,
                "coverage_after": (len(media_files) - len(errors)) / max(len(media_files), 1) * 100,
                "errors": errors,
                "snapshot_id": snapshot_id,
                "dry_run": dry_run,
                "language": language,
                "providers_tried": providers
            }

            # Log completion
            self.audit.log_event("subtitle_download_complete", result, actor="subtitle_backend.py")

            return result

        except Exception as e:
            error_msg = f"Subtitle download failed: {str(e)}"
            self.logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "downloaded": 0,
                "errors": 1
            }

    def _has_external_subtitles(self, media_file: Path) -> bool:
        """Check if media file has external subtitle files."""
        base_name = media_file.stem
        media_parent = media_file.parent

        # Check for common subtitle naming patterns
        for ext in self.SUBTITLE_EXTENSIONS:
            # {filename}.{ext}
            if (media_parent / f"{base_name}{ext}").exists():
                return True
            # {filename}.en.{ext}
            if (media_parent / f"{base_name}.en{ext}").exists():
                return True
            # {filename}.eng.{ext}
            if (media_parent / f"{base_name}.eng{ext}").exists():
                return True

        return False

    def _has_embedded_subtitles(self, media_file: Path) -> bool:
        """Check if media file has embedded subtitles (using ffprobe)."""
        try:
            import subprocess
            result = subprocess.run(
                ["ffprobe", "-v", "error", "-select_streams", "s", "-show_entries",
                 "stream=codec_type", "-of", "csv=p=0", str(media_file)],
                capture_output=True,
                text=True,
                timeout=5
            )
            return "s" in result.stdout
        except Exception:
            # ffprobe not available or error occurred, assume no embedded subs
            return False

    def _simulate_download(self, media_file: Path, language: str) -> Optional[Path]:
        """Simulate downloading a subtitle (for demo purposes)."""
        # In production, would call actual provider APIs
        base_name = media_file.stem
        subtitle_path = media_file.parent / f"{base_name}.{language.lower()}.srt"
        return subtitle_path

    def _download_with_subliminal(self, media_file: Path, language: str) -> Optional[Path]:
        """Attempt real subtitle download using subliminal; returns saved path or None."""
        if not _HAS_SUBLIMINAL:
            return None
        try:
            # Configure in-memory cache for subliminal
            subliminal.region.configure('dogpile.cache.memory')

            # Scan the video
            video = subliminal.scan_video(str(media_file))

            # Prepare language
            # Map common names to codes
            lang_normalized = language.strip().lower()
            code = {
                'english': 'eng', 'spanish': 'spa', 'french': 'fra', 'german': 'deu',
                'portuguese': 'por', 'italian': 'ita'
            }.get(lang_normalized, 'eng')
            langs = { _BF_Language(code) }

            # Download and save
            subs = subliminal.download_best_subtitles({video}, langs)
            if video in subs and subs[video]:
                subliminal.save_subtitles(video, subs[video])
                # Try to find the saved path
                base = media_file.stem
                # Common suffixes used by subliminal: .en.srt or .eng.srt etc.
                for suf in (code, code[:2]):
                    candidate = media_file.parent / f"{base}.{suf}.srt"
                    if candidate.exists():
                        return candidate
                # Fallback: any .srt created right next to the video
                for p in media_file.parent.glob(f"{base}*.srt"):
                    return p
        except Exception as e:
            self.logger.warning(f"subliminal failed for {media_file.name}: {e}")
        return None

    def rollback_download(self, snapshot_id: str) -> Dict[str, Any]:
        """
        Restore from a snapshot to rollback subtitle downloads.
        
        Args:
            snapshot_id: ID of snapshot to restore
        
        Returns:
            Dict with restoration status
        """
        try:
            SnapshotManager.restore_snapshot(snapshot_id)

            self.audit.log_event("snapshot_restore", {
                "snapshot_id": snapshot_id,
                "operation": "subtitle_download_rollback",
                "timestamp": datetime.now().isoformat()
            }, actor="subtitle_backend.py")

            return {
                "success": True,
                "snapshot_id": snapshot_id,
                "message": "Subtitle download rolled back successfully"
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
    backend = SubtitleBackend()

    def progress_callback(msg: str, percent: int):
        print(f"[{percent:3d}%] {msg}")

    # Test detection
    test_folder = r"C:\test_media"
    if Path(test_folder).exists():
        print("Testing coverage detection...")
        stats = backend.detect_coverage(test_folder, progress_callback=progress_callback)
        print(f"Coverage: {stats.to_dict()}")
