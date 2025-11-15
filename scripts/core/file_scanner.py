#!/usr/bin/env python3
"""
File Scanner - Point 1 of 9-Point Workflow

Recursive directory scanning and master file inventory generation.
Scans folders for media files and creates comprehensive file list with metadata.

Architecture Reference: Section 4.1 (File Scanner)
Knowledge Pack: Point 1 (Folder Scanning & Inventory)
"""

import logging
from pathlib import Path
from typing import List, Set, Dict, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict

from scripts.utils.transaction_manager import FileHasher


logger = logging.getLogger(__name__)


@dataclass
class FileRecord:
    """
    Represents a single file in the master inventory.

    Architecture Reference: Section 6 (Data Models)
    """
    absolute_path: Path
    size_bytes: int
    extension: str
    parent_folder: Path
    scan_timestamp: datetime
    md5_hash: Optional[str] = None  # Calculated on-demand for performance

    # Jellyfin integration fields (Phase 20)
    jellyfin_id: Optional[str] = None
    jellyfin_item_type: Optional[str] = None
    jellyfin_library_id: Optional[str] = None
    jellyfin_provider_ids: Optional[Dict[str, str]] = field(default_factory=dict)
    jellyfin_matched: bool = False

    def __post_init__(self):
        """Ensure Path objects are converted properly."""
        if isinstance(self.absolute_path, str):
            self.absolute_path = Path(self.absolute_path)
        if isinstance(self.parent_folder, str):
            self.parent_folder = Path(self.parent_folder)


@dataclass
class ScanStatistics:
    """Statistics from a folder scan operation."""
    total_files: int = 0
    total_size_bytes: int = 0
    file_types: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    folders_scanned: int = 0
    scan_duration_seconds: float = 0.0
    errors: List[str] = field(default_factory=list)

    def add_file(self, file_path: Path, size: int):
        """Add a file to the statistics."""
        self.total_files += 1
        self.total_size_bytes += size
        self.file_types[file_path.suffix.lower()] += 1


class FileScanner:
    """
    Recursive directory scanner that generates master file inventory.

    Implementation per Architecture Reference Section 4.1:
    - Uses pathlib.Path.rglob() for recursive scanning
    - Generates master file list with absolute paths
    - Calculates folder sizes and file type statistics

    Features:
    - Configurable file extensions filter
    - Progress callback for GUI integration
    - Error handling with detailed logging
    - Statistics tracking
    - Optional MD5 calculation (deferred for performance)
    """

    # Default media file extensions per Jellyfin documentation
    DEFAULT_VIDEO_EXTENSIONS = {
        '.mkv', '.mp4', '.avi', '.mov', '.m4v', '.ts', '.wmv', '.flv',
        '.webm', '.mpg', '.mpeg', '.m2ts', '.vob', '.ogv', '.3gp'
    }

    DEFAULT_SUBTITLE_EXTENSIONS = {
        '.srt', '.sub', '.sbv', '.ass', '.ssa', '.vtt', '.idx'
    }

    DEFAULT_METADATA_EXTENSIONS = {
        '.nfo', '.xml', '.jpg', '.jpeg', '.png', '.tbn'
    }

    def __init__(
        self,
        extensions: Optional[Set[str]] = None,
        include_subtitles: bool = True,
        include_metadata: bool = True,
        progress_callback: Optional[Callable[[str, int, int], None]] = None
    ):
        """
        Initialize the file scanner.

        Args:
            extensions: Set of file extensions to scan (e.g., {'.mkv', '.mp4'})
                       If None, uses DEFAULT_VIDEO_EXTENSIONS
            include_subtitles: Whether to include subtitle files in scan
            include_metadata: Whether to include metadata files (NFO, images)
            progress_callback: Optional callback function(message, current, total)
                             for progress reporting
        """
        self.extensions = extensions or self.DEFAULT_VIDEO_EXTENSIONS.copy()

        if include_subtitles:
            self.extensions.update(self.DEFAULT_SUBTITLE_EXTENSIONS)
        if include_metadata:
            self.extensions.update(self.DEFAULT_METADATA_EXTENSIONS)

        self.progress_callback = progress_callback
        self.statistics = ScanStatistics()

        logger.info(f"FileScanner initialized with {len(self.extensions)} extensions")

    def scan_folder(
        self,
        folder_path: Path | str,
        recursive: bool = True
    ) -> List[FileRecord]:
        """
        Scan a folder and generate file inventory.

        This is the main entry point for Point 1 of the workflow.

        Args:
            folder_path: Root folder to scan
            recursive: Whether to scan subdirectories recursively

        Returns:
            List of FileRecord objects representing all found files

        Raises:
            FileNotFoundError: If folder_path doesn't exist
            PermissionError: If folder_path is not accessible
        """
        start_time = datetime.now()
        folder_path = Path(folder_path)

        if not folder_path.exists():
            raise FileNotFoundError(f"Folder does not exist: {folder_path}")

        if not folder_path.is_dir():
            raise NotADirectoryError(f"Path is not a directory: {folder_path}")

        logger.info(f"Starting {'recursive' if recursive else 'non-recursive'} scan: {folder_path}")

        # Reset statistics
        self.statistics = ScanStatistics()

        # Collect all files
        file_records = []

        try:
            if recursive:
                file_records = self._scan_recursive(folder_path)
            else:
                file_records = self._scan_single_folder(folder_path)
        except Exception as e:
            logger.error(f"Error during scan: {e}", exc_info=True)
            self.statistics.errors.append(str(e))
            raise

        # Calculate duration
        end_time = datetime.now()
        self.statistics.scan_duration_seconds = (end_time - start_time).total_seconds()

        logger.info(
            f"Scan complete: {self.statistics.total_files} files "
            f"({self._format_size(self.statistics.total_size_bytes)}) "
            f"in {self.statistics.scan_duration_seconds:.1f}s"
        )

        return file_records

    def _scan_recursive(self, folder_path: Path) -> List[FileRecord]:
        """Recursively scan folder and all subdirectories."""
        file_records = []

        # First pass: count total files for progress reporting
        total_files = sum(1 for ext in self.extensions for _ in folder_path.rglob(f'*{ext}'))
        processed = 0

        logger.debug(f"Found approximately {total_files} files to scan")

        # Second pass: process files
        for ext in self.extensions:
            try:
                for file_path in folder_path.rglob(f'*{ext}'):
                    record = self._process_file(file_path)
                    if record:
                        file_records.append(record)

                    processed += 1

                    # Progress callback
                    if self.progress_callback and processed % 10 == 0:
                        self.progress_callback(
                            f"Scanning: {file_path.name}",
                            processed,
                            total_files
                        )
            except Exception as e:
                error_msg = f"Error scanning for extension {ext}: {e}"
                logger.warning(error_msg)
                self.statistics.errors.append(error_msg)

        return file_records

    def _scan_single_folder(self, folder_path: Path) -> List[FileRecord]:
        """Scan only the specified folder (non-recursive)."""
        file_records = []

        try:
            all_files = [f for f in folder_path.iterdir() if f.is_file()]
            total_files = len(all_files)

            for idx, file_path in enumerate(all_files):
                if file_path.suffix.lower() in self.extensions:
                    record = self._process_file(file_path)
                    if record:
                        file_records.append(record)

                # Progress callback
                if self.progress_callback and idx % 10 == 0:
                    self.progress_callback(
                        f"Scanning: {file_path.name}",
                        idx,
                        total_files
                    )
        except Exception as e:
            error_msg = f"Error scanning folder {folder_path}: {e}"
            logger.warning(error_msg)
            self.statistics.errors.append(error_msg)

        return file_records

    def _process_file(self, file_path: Path) -> Optional[FileRecord]:
        """
        Process a single file and create FileRecord.

        Args:
            file_path: Path to the file

        Returns:
            FileRecord if successful, None if file couldn't be processed
        """
        try:
            # Get file statistics
            stat = file_path.stat()

            # Calculate MD5 hash for integrity / duplicate detection
            md5_hash: Optional[str] = None
            try:
                md5_hash = FileHasher.calculate_md5(file_path)
            except (FileNotFoundError, PermissionError, OSError) as e:
                # If we can't hash the file, log the issue but still keep the record
                error_msg = f"Cannot calculate MD5 for {file_path}: {e}"
                logger.debug(error_msg)
                self.statistics.errors.append(error_msg)

            # Create record
            record = FileRecord(
                absolute_path=file_path.resolve(),
                size_bytes=stat.st_size,
                extension=file_path.suffix.lower(),
                parent_folder=file_path.parent.resolve(),
                scan_timestamp=datetime.now(),
                md5_hash=md5_hash
            )

            # Update statistics
            self.statistics.add_file(file_path, stat.st_size)

            return record

        except (PermissionError, OSError, FileNotFoundError) as e:
            error_msg = f"Cannot access file {file_path}: {e}"
            logger.debug(error_msg)
            self.statistics.errors.append(error_msg)
            return None

    def get_folder_structure(
        self,
        file_records: List[FileRecord]
    ) -> Dict[Path, Dict[str, any]]:
        """
        Generate hierarchical folder structure from file records.

        This implements Point 2 of the workflow: Hierarchical Overview.

        Returns dictionary mapping folder paths to:
        - total_size: Total size in bytes
        - file_count: Number of files
        - file_types: Dict of extension -> count
        - file_type_sizes: Dict of extension -> total size

        Args:
            file_records: List of FileRecord objects from scan

        Returns:
            Dictionary with folder structure and statistics
        """
        structure = defaultdict(lambda: {
            'total_size': 0,
            'file_count': 0,
            'file_types': defaultdict(int),
            'file_type_sizes': defaultdict(int)
        })

        for record in file_records:
            folder = record.parent_folder
            ext = record.extension

            structure[folder]['total_size'] += record.size_bytes
            structure[folder]['file_count'] += 1
            structure[folder]['file_types'][ext] += 1
            structure[folder]['file_type_sizes'][ext] += record.size_bytes

        # Update folders scanned count
        self.statistics.folders_scanned = len(structure)

        return dict(structure)

    def get_statistics(self) -> ScanStatistics:
        """Get scan statistics."""
        return self.statistics

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """Format bytes as human-readable size."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"

    def format_folder_structure(
        self,
        structure: Dict[Path, Dict[str, any]]
    ) -> str:
        """
        Format folder structure as human-readable text.

        Useful for LLM analysis (Point 3 of workflow).

        Args:
            structure: Output from get_folder_structure()

        Returns:
            Formatted string representation
        """
        lines = []
        lines.append("FOLDER STRUCTURE ANALYSIS")
        lines.append("=" * 80)
        lines.append(f"Total folders: {len(structure)}")
        lines.append(f"Total files: {self.statistics.total_files}")
        lines.append(f"Total size: {self._format_size(self.statistics.total_size_bytes)}")
        lines.append("")

        for folder, data in sorted(structure.items()):
            lines.append(f"\n{folder}")
            lines.append(f"  Files: {data['file_count']}")
            lines.append(f"  Size: {self._format_size(data['total_size'])}")
            lines.append(f"  File types:")

            # Sort by count descending
            sorted_types = sorted(
                data['file_types'].items(),
                key=lambda x: x[1],
                reverse=True
            )

            for ext, count in sorted_types:
                size = data['file_type_sizes'][ext]
                lines.append(f"    {ext}: {count} files ({self._format_size(size)})")

        return "\n".join(lines)


def main():
    """CLI entry point for testing."""
    import argparse

    parser = argparse.ArgumentParser(description="Scan folders for media files")
    parser.add_argument("folder", help="Folder to scan")
    parser.add_argument("--no-recursive", action="store_true", help="Disable recursive scan")
    parser.add_argument("--video-only", action="store_true", help="Scan video files only")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Create scanner
    scanner = FileScanner(
        extensions=FileScanner.DEFAULT_VIDEO_EXTENSIONS if args.video_only else None,
        include_subtitles=not args.video_only,
        include_metadata=not args.video_only,
        progress_callback=lambda msg, cur, tot: print(f"[{cur}/{tot}] {msg}")
    )

    # Scan
    try:
        file_records = scanner.scan_folder(
            args.folder,
            recursive=not args.no_recursive
        )

        # Generate structure
        structure = scanner.get_folder_structure(file_records)

        # Print formatted output
        print("\n" + scanner.format_folder_structure(structure))

        # Print statistics
        stats = scanner.get_statistics()
        print(f"\nScan completed in {stats.scan_duration_seconds:.1f}s")

        if stats.errors:
            print(f"\nErrors encountered: {len(stats.errors)}")
            for error in stats.errors[:10]:  # Show first 10
                print(f"  - {error}")

    except Exception as e:
        logger.error(f"Scan failed: {e}", exc_info=True)
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
