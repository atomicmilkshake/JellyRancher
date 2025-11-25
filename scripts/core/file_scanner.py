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
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
        exclude_paths: Optional[Set[Path]] = None,
        calculate_md5: bool = False,
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
            exclude_paths: Set of paths to exclude from scanning
            calculate_md5: Whether to calculate MD5 hashes during scan (slower but useful for duplicates)

        Raises:
            TypeError: If arguments are of incorrect type
            ValueError: If extensions set is empty
        """
        try:
            # Input validation
            if extensions is not None and not isinstance(extensions, set):
                raise TypeError(f"extensions must be a set, got {type(extensions)}")
            
            if exclude_paths is not None and not isinstance(exclude_paths, set):
                raise TypeError(f"exclude_paths must be a set, got {type(exclude_paths)}")
            
            # Initialize extensions
            self.extensions = extensions or self.DEFAULT_VIDEO_EXTENSIONS.copy()

            if include_subtitles:
                self.extensions.update(self.DEFAULT_SUBTITLE_EXTENSIONS)
            if include_metadata:
                self.extensions.update(self.DEFAULT_METADATA_EXTENSIONS)
            
            if not self.extensions:
                raise ValueError("Extensions set cannot be empty")

            self.progress_callback = progress_callback
            self.statistics = ScanStatistics()
            
            # Normalize exclusion paths (used to skip subfolders/files)
            try:
                self.exclude_paths: Set[Path] = {p.resolve() for p in exclude_paths} if exclude_paths else set()
            except (OSError, RuntimeError) as e:
                logger.warning(f"Failed to resolve some exclusion paths: {e}")
                self.exclude_paths = set()

            self.calculate_md5 = calculate_md5

            logger.info(f"FileScanner initialized with {len(self.extensions)} extensions (MD5: {calculate_md5})")
            
        except (TypeError, ValueError) as e:
            logger.error(f"Failed to initialize FileScanner: {e}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Unexpected error initializing FileScanner: {e}", exc_info=True)
            raise RuntimeError(f"Failed to initialize FileScanner: {e}")

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
            NotADirectoryError: If path is not a directory
            PermissionError: If folder_path is not accessible
            RuntimeError: If scan fails catastrophically
        """
        try:
            start_time = datetime.now()
            
            # Input validation and path conversion
            try:
                folder_path = Path(folder_path)
            except (TypeError, ValueError) as e:
                raise ValueError(f"Invalid folder path: {e}")

            # Path validation
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
            except (FileNotFoundError, NotADirectoryError, PermissionError):
                # Re-raise expected exceptions
                raise
            except Exception as e:
                error_msg = f"Scan operation failed: {e}"
                logger.error(error_msg, exc_info=True)
                self.statistics.errors.append(error_msg)
                raise RuntimeError(error_msg)

            # Calculate duration
            end_time = datetime.now()
            self.statistics.scan_duration_seconds = (end_time - start_time).total_seconds()

            logger.info(
                f"Scan complete: {self.statistics.total_files} files "
                f"({self._format_size(self.statistics.total_size_bytes)}) "
                f"in {self.statistics.scan_duration_seconds:.1f}s"
            )

            return file_records
            
        except (FileNotFoundError, NotADirectoryError, PermissionError, ValueError) as e:
            logger.error(f"Scan failed with validation error: {e}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Unexpected error during scan: {e}", exc_info=True)
            raise RuntimeError(f"Failed to scan folder: {e}")

    def _scan_recursive(self, folder_path: Path) -> List[FileRecord]:
        """
        Recursively scan folder and all subdirectories.
        
        OPTIMIZED: Single-pass traversal with immediate feedback.
        No more double-scanning or per-extension iteration.
        """
        file_records = []
        processed = 0

        logger.debug(f"Starting optimized single-pass recursive scan of {folder_path}")

        try:
            # SINGLE PASS: Walk the tree once, filter as we go
            for item_path in folder_path.rglob('*'):
                try:
                    # Skip directories
                    if not item_path.is_file():
                        continue
                    
                    # Filter by extension
                    if item_path.suffix.lower() not in self.extensions:
                        continue
                    
                    # Skip excluded paths
                    if self._is_excluded(item_path):
                        continue
                    
                    # Process the file
                    record = self._process_file(item_path)
                    if record:
                        file_records.append(record)
                        processed += 1
                        
                        # Progress callback - immediate feedback, no total needed
                        if self.progress_callback and processed % 10 == 0:
                            self.progress_callback(
                                f"Scanning: {item_path.name}",
                                processed,
                                0  # No total available in single-pass, show count only
                            )
                
                except (PermissionError, OSError) as e:
                    # Skip inaccessible files/folders
                    logger.debug(f"Skipping inaccessible path {item_path}: {e}")
                    continue
                    
        except Exception as e:
            error_msg = f"Error during recursive scan: {e}"
            logger.error(error_msg, exc_info=True)
            self.statistics.errors.append(error_msg)

        logger.info(f"Single-pass scan complete: found {processed} files")
        return file_records

    def _scan_single_folder(self, folder_path: Path) -> List[FileRecord]:
        """
        Scan only the specified folder (non-recursive).
        
        OPTIMIZED: Single-pass with extension filtering.
        """
        file_records = []
        processed = 0

        try:
            for item_path in folder_path.iterdir():
                try:
                    # Skip directories
                    if not item_path.is_file():
                        continue
                    
                    # Filter by extension
                    if item_path.suffix.lower() not in self.extensions:
                        continue
                    
                    # Skip excluded paths
                    if self._is_excluded(item_path):
                        continue
                    
                    # Process the file
                    record = self._process_file(item_path)
                    if record:
                        file_records.append(record)
                        processed += 1
                        
                        # Progress callback
                        if self.progress_callback and processed % 10 == 0:
                            self.progress_callback(
                                f"Scanning: {item_path.name}",
                                processed,
                                0
                            )
                
                except (PermissionError, OSError) as e:
                    logger.debug(f"Skipping inaccessible file {item_path}: {e}")
                    continue
                    
        except Exception as e:
            error_msg = f"Error scanning folder {folder_path}: {e}"
            logger.warning(error_msg)
            self.statistics.errors.append(error_msg)

        return file_records

    def _is_excluded(self, file_path: Path) -> bool:
        """
        Check whether a file or its parent folder is under any excluded path.

        Args:
            file_path: File path to check

        Returns:
            True if the file should be excluded from scanning.
        """
        if not self.exclude_paths:
            return False

        try:
            file_path_resolved = file_path.resolve()
        except Exception:
            file_path_resolved = file_path

        for excluded in self.exclude_paths:
            try:
                # Python 3.9+: Path.is_relative_to
                if file_path_resolved.is_relative_to(excluded):
                    return True
            except Exception:
                # Fallback for unexpected path issues
                if str(file_path_resolved).startswith(str(excluded)):
                    return True

        return False

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

            # Calculate BLAKE3 hash ONLY if enabled (major performance impact)
            # Note: Field still named md5_hash for backward compatibility, but uses BLAKE3 algorithm
            md5_hash: Optional[str] = None
            if self.calculate_md5:
                try:
                    md5_hash = FileHasher.calculate_hash(file_path)
                except (FileNotFoundError, PermissionError, OSError) as e:
                    # If we can't hash the file, log the issue but still keep the record
                    error_msg = f"Cannot calculate hash for {file_path}: {e}"
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

        Raises:
            TypeError: If file_records is not a list
            RuntimeError: If structure generation fails
        """
        try:
            # Input validation
            if not isinstance(file_records, list):
                raise TypeError(f"file_records must be a list, got {type(file_records)}")

            structure = defaultdict(lambda: {
                'total_size': 0,
                'file_count': 0,
                'file_types': defaultdict(int),
                'file_type_sizes': defaultdict(int)
            })

            # Process each record with error isolation
            processed = 0
            errors = 0
            
            for record in file_records:
                try:
                    if not isinstance(record, FileRecord):
                        logger.warning(f"Skipping invalid record type: {type(record)}")
                        errors += 1
                        continue
                    
                    folder = record.parent_folder
                    ext = record.extension

                    structure[folder]['total_size'] += record.size_bytes
                    structure[folder]['file_count'] += 1
                    structure[folder]['file_types'][ext] += 1
                    structure[folder]['file_type_sizes'][ext] += record.size_bytes
                    processed += 1
                    
                except (AttributeError, TypeError) as e:
                    logger.warning(f"Error processing file record: {e}")
                    errors += 1
                    continue

            # Update folders scanned count
            self.statistics.folders_scanned = len(structure)

            if errors > 0:
                logger.warning(f"Processed {processed} records with {errors} errors")

            return dict(structure)
            
        except TypeError as e:
            logger.error(f"Invalid input to get_folder_structure: {e}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Failed to generate folder structure: {e}", exc_info=True)
            raise RuntimeError(f"Failed to generate folder structure: {e}")

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

        Raises:
            TypeError: If structure is not a dictionary
            RuntimeError: If formatting fails
        """
        try:
            # Input validation
            if not isinstance(structure, dict):
                raise TypeError(f"structure must be a dict, got {type(structure)}")

            lines = []
            lines.append("FOLDER STRUCTURE ANALYSIS")
            lines.append("=" * 80)
            lines.append(f"Total folders: {len(structure)}")
            lines.append(f"Total files: {self.statistics.total_files}")
            lines.append(f"Total size: {self._format_size(self.statistics.total_size_bytes)}")
            lines.append("")

            # Process folders with error isolation
            for folder, data in sorted(structure.items()):
                try:
                    lines.append(f"\n{folder}")
                    lines.append(f"  Files: {data.get('file_count', 0)}")
                    lines.append(f"  Size: {self._format_size(data.get('total_size', 0))}")
                    lines.append(f"  File types:")

                    # Sort by count descending
                    file_types = data.get('file_types', {})
                    file_type_sizes = data.get('file_type_sizes', {})
                    
                    sorted_types = sorted(
                        file_types.items(),
                        key=lambda x: x[1],
                        reverse=True
                    )

                    for ext, count in sorted_types:
                        try:
                            size = file_type_sizes.get(ext, 0)
                            lines.append(f"    {ext}: {count} files ({self._format_size(size)})")
                        except Exception as e:
                            logger.warning(f"Error formatting file type {ext}: {e}")
                            continue
                            
                except (KeyError, TypeError, AttributeError) as e:
                    logger.warning(f"Error formatting folder {folder}: {e}")
                    continue

            return "\n".join(lines)
            
        except TypeError as e:
            logger.error(f"Invalid input to format_folder_structure: {e}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Failed to format folder structure: {e}", exc_info=True)
            raise RuntimeError(f"Failed to format folder structure: {e}")


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
