#!/usr/bin/env python3
"""
Validate Jellyfin Library Files

Checks that all Jellyfin library entries point to real, valid video files on the filesystem.
Validates:
- File exists on filesystem
- Path points to a file (not directory)
- File has valid video extension
- File is readable

READ-ONLY OPERATION: This script does not modify or delete any files.
It only reads Jellyfin metadata and checks filesystem status.

Usage:
    python validate_jellyfin_files.py
    python validate_jellyfin_files.py --media-types Movie Episode
    python validate_jellyfin_files.py --json --missing-only
    python validate_jellyfin_files.py --verbose
"""

import sys
import json
import argparse
import logging
import time
from pathlib import Path
from typing import List, Dict, Set, Optional
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent))

from scripts.core.jellyfin_client import JellyfinClient
from scripts.core.jellyfin_config import JellyfinConfigManager
from scripts.core.file_scanner import FileScanner
from scripts.core.jellyfin_validator import JellyfinValidator

# Setup logging
logger = logging.getLogger(__name__)

# Valid video extensions from FileScanner
VIDEO_EXTENSIONS = FileScanner.DEFAULT_VIDEO_EXTENSIONS


class ValidationResult:
    """Result of validating a single Jellyfin item."""
    
    def __init__(self, item: Dict):
        self.item = item
        self.jellyfin_id = item.get('Id', 'N/A')
        self.title = item.get('Name', 'N/A')
        self.jellyfin_path = item.get('Path', '')
        self.valid = False
        self.issues = []
        self.file_size = None
        self.actual_path = None
    
    def add_issue(self, issue: str):
        """Add a validation issue."""
        self.issues.append(issue)
        self.valid = False
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON output."""
        return {
            'jellyfin_id': self.jellyfin_id,
            'title': self.title,
            'jellyfin_path': self.jellyfin_path,
            'valid': self.valid,
            'issues': self.issues,
            'file_size': self.file_size,
            'actual_path': self.actual_path
        }


def validate_file(item: Dict) -> ValidationResult:
    """
    Validate a single Jellyfin item.
    
    Checks:
    1. File exists on filesystem
    2. Path points to a file (not directory)
    3. File has valid video extension
    4. File is readable
    
    Returns:
        ValidationResult with validation status and issues
    """
    result = ValidationResult(item)
    
    jellyfin_path = item.get('Path', '')
    if not jellyfin_path:
        result.add_issue('No path in Jellyfin metadata')
        logger.debug(f"Item {result.jellyfin_id} ({result.title}): No path in metadata")
        return result
    
    # Check if path exists
    try:
        path = Path(jellyfin_path)
        if not path.exists():
            result.add_issue('File does not exist on filesystem')
            logger.warning(f"Item {result.jellyfin_id} ({result.title}): File not found: {jellyfin_path}")
            return result
        
        # Get resolved path (actual filesystem path)
        resolved = path.resolve()
        result.actual_path = str(resolved)
        
        # Check if it's a file (not directory)
        if resolved.is_dir():
            result.add_issue('Path is a directory, not a file')
            logger.warning(f"Item {result.jellyfin_id} ({result.title}): Path is directory: {jellyfin_path}")
            return result
        
        if not resolved.is_file():
            result.add_issue('Path exists but is not a file or directory')
            logger.warning(f"Item {result.jellyfin_id} ({result.title}): Path is not a file: {jellyfin_path}")
            return result
        
        # Check file extension
        extension = resolved.suffix.lower()
        if extension not in VIDEO_EXTENSIONS:
            valid_exts = ", ".join(sorted(VIDEO_EXTENSIONS))
            result.add_issue(f'Invalid video extension: {extension} (valid: {valid_exts})')
            logger.warning(f"Item {result.jellyfin_id} ({result.title}): Invalid extension {extension}")
            return result
        
        # Check if file is readable
        try:
            stat = resolved.stat()
            result.file_size = stat.st_size
            # Try to open file to verify readability
            with open(resolved, 'rb') as f:
                f.read(1)  # Read first byte
            logger.debug(f"Item {result.jellyfin_id} ({result.title}): Valid file")
        except PermissionError as e:
            result.add_issue('File exists but is not readable (permission denied)')
            logger.error(f"Item {result.jellyfin_id} ({result.title}): Permission denied: {jellyfin_path}", exc_info=True)
            return result
        except Exception as e:
            result.add_issue(f'File exists but cannot be read: {str(e)}')
            logger.error(f"Item {result.jellyfin_id} ({result.title}): Cannot read file: {jellyfin_path}", exc_info=True)
            return result
        
        # All checks passed
        result.valid = True
        return result
        
    except Exception as e:
        result.add_issue(f'Error validating file: {str(e)}')
        logger.error(f"Item {result.jellyfin_id} ({result.title}): Validation error: {jellyfin_path}", exc_info=True)
        return result


def validate_library(
    client: JellyfinClient,
    media_types: Optional[List[str]] = None
) -> List[ValidationResult]:
    """
    Validate all items in Jellyfin library.
    
    Args:
        client: JellyfinClient instance
        media_types: List of media types to check (e.g., ['Movie', 'Episode'])
                    If None, checks all media types
    
    Returns:
        List of ValidationResult objects
    """
    logger.info("Fetching items from Jellyfin library...")
    if media_types:
        logger.info(f"Filtering by media types: {', '.join(media_types)}")
    else:
        logger.info("Checking all media types")
    
    # Get all items with error handling
    try:
        items = client.get_all_items(
            item_types=media_types,
            fields=['Name', 'Path', 'MediaSources', 'Id', 'ProviderIds', 'Type']
        )
        logger.info(f"Found {len(items)} items to validate")
    except Exception as e:
        logger.error(f"Failed to fetch items from Jellyfin: {e}", exc_info=True)
        raise RuntimeError(f"Cannot fetch items from Jellyfin: {e}") from e
    
    if len(items) == 0:
        logger.warning("No items found in Jellyfin library")
        return []
    
    logger.info("Validating files...")
    
    results = []
    start_time = time.time()
    last_update_time = start_time
    
    for i, item in enumerate(items, 1):
        # Update progress every 10 items or every 1 second
        current_time = time.time()
        should_update = (i % 10 == 0) or (current_time - last_update_time >= 1.0)
        
        if should_update:
            elapsed = current_time - start_time
            rate = i / elapsed if elapsed > 0 else 0
            remaining = (len(items) - i) / rate if rate > 0 else 0
            percent = (i / len(items)) * 100
            
            # Format time
            elapsed_str = f"{elapsed:.1f}s"
            remaining_str = f"{remaining:.1f}s" if remaining > 0 else "calculating..."
            
            sys.stdout.write(f"\r  Progress: {i}/{len(items)} ({percent:.1f}%) - Elapsed: {elapsed_str} - Remaining: {remaining_str}")
            sys.stdout.flush()
            last_update_time = current_time
        
        result = validate_file(item)
        results.append(result)
    
    # Final progress update
    elapsed = time.time() - start_time
    sys.stdout.write(f"\r  Progress: {len(items)}/{len(items)} (100.0%) - Completed in {elapsed:.1f}s\n")
    sys.stdout.flush()
    
    logger.info(f"Validation complete: {len(results)} items processed in {elapsed:.1f}s")
    
    return results


def format_report(results: List[ValidationResult], missing_only: bool = False, invalid_only: bool = False) -> str:
    """Format validation results as a human-readable report."""
    lines = []
    
    # Summary
    total = len(results)
    valid = sum(1 for r in results if r.valid)
    invalid = total - valid
    
    # Filter results based on flags
    display_results = results
    if missing_only:
        display_results = [r for r in results if 'does not exist' in ' '.join(r.issues)]
    elif invalid_only:
        display_results = [r for r in results if not r.valid]
    
    lines.append("=" * 70)
    lines.append("JELLYFIN FILE VALIDATION REPORT")
    lines.append("=" * 70)
    lines.append(f"Total items checked: {total}")
    lines.append(f"Valid files: {valid}")
    lines.append(f"Invalid files: {invalid}")
    lines.append("=" * 70)
    lines.append("")
    
    if not display_results:
        lines.append("[SUCCESS] No issues found!")
        return "\n".join(lines)
    
    # Group issues by type
    issue_groups = defaultdict(list)
    for result in display_results:
        if result.issues:
            # Use first issue as category
            category = result.issues[0]
            issue_groups[category].append(result)
    
    # Report by issue category
    for category, items in sorted(issue_groups.items()):
        lines.append(f"{'=' * 70}")
        lines.append(f"ISSUE: {category}")
        lines.append(f"{'=' * 70}")
        lines.append(f"Found {len(items)} item(s) with this issue:\n")
        
        for result in items:
            lines.append(f"  Title: {result.title}")
            lines.append(f"  Jellyfin ID: {result.jellyfin_id}")
            lines.append(f"  Jellyfin Path: {result.jellyfin_path}")
            if result.actual_path and result.actual_path != result.jellyfin_path:
                lines.append(f"  Actual Path: {result.actual_path}")
            if result.file_size:
                size_gb = result.file_size / (1024**3)
                lines.append(f"  File Size: {size_gb:.2f} GB")
            if len(result.issues) > 1:
                lines.append(f"  Additional Issues:")
                for issue in result.issues[1:]:
                    lines.append(f"    - {issue}")
            lines.append("")
    
    lines.append("=" * 70)
    lines.append("SUMMARY")
    lines.append("=" * 70)
    lines.append(f"Total: {total} items")
    lines.append(f"Valid: {valid} items")
    lines.append(f"Invalid: {invalid} items")
    lines.append("=" * 70)
    
    return "\n".join(lines)


def print_startup_banner(media_types: Optional[List[str]] = None):
    """Print startup banner with script information."""
    print("=" * 70)
    print("JELLYFIN FILE VALIDATION SCRIPT")
    print("=" * 70)
    print()
    print("Purpose: Validate that all Jellyfin library entries point to")
    print("         real, valid video files on the filesystem.")
    print()
    print("READ-ONLY OPERATION: This script does NOT modify or delete")
    print("                     any files. It only reads Jellyfin metadata")
    print("                     and checks filesystem status.")
    print()
    print("Validation Checks:")
    print("  - File exists on filesystem")
    print("  - Path points to a file (not directory)")
    print("  - File has valid video extension")
    print("  - File is readable")
    print()
    if media_types:
        print(f"Media Types: {', '.join(media_types)}")
    else:
        print("Media Types: All types")
    print()
    print("=" * 70)
    print()


def main():
    parser = argparse.ArgumentParser(
        description='Validate Jellyfin library files exist and are valid video files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python validate_jellyfin_files.py
  python validate_jellyfin_files.py --media-types Movie Episode
  python validate_jellyfin_files.py --json --missing-only
  python validate_jellyfin_files.py --invalid-only
  python validate_jellyfin_files.py --verbose
        """
    )
    parser.add_argument(
        '--media-types',
        nargs='+',
        help='Media types to check (e.g., Movie Episode Series). Default: all types'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output JSON instead of formatted text'
    )
    parser.add_argument(
        '--missing-only',
        action='store_true',
        help='Only show files that are missing'
    )
    parser.add_argument(
        '--invalid-only',
        action='store_true',
        help='Only show invalid files (wrong type, unreadable, etc.)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable DEBUG level logging for detailed output'
    )
    
    args = parser.parse_args()
    
    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(levelname)s: %(message)s',
        handlers=[logging.StreamHandler(sys.stderr)]
    )
    
    # Print startup banner
    if not args.json:
        print_startup_banner(media_types=args.media_types)
    
    # Initialize Jellyfin client
    logger.info("Initializing Jellyfin client...")
    try:
        config = JellyfinConfigManager()
        client = JellyfinClient(
            server_url=config.get_server_url(),
            api_key=config.get_api_key()
        )
    except Exception as e:
        logger.error(f"Failed to initialize Jellyfin client: {e}", exc_info=True)
        print("ERROR: Failed to initialize Jellyfin client. Check your configuration.")
        sys.exit(1)
    
    # Test connection
    logger.info("Testing Jellyfin connection...")
    if not args.json:
        print("Connecting to Jellyfin server...")
    
    try:
        if not client.test_connection():
            logger.error("Jellyfin connection test failed")
            print("ERROR: Connection failed! Check your Jellyfin server URL and API key.")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Jellyfin connection error: {e}", exc_info=True)
        print(f"ERROR: Connection error: {e}")
        sys.exit(1)
    
    if not args.json:
        print("Connected successfully")
        print()
    logger.info("Jellyfin connection successful")
    
    # Validate library using enhanced validator
    try:
        validator = JellyfinValidator(client)
        validation_results = validator.validate_library(
            media_types=args.media_types,
            check_metadata=True,
            check_quality=True,
            check_subtitles=True
        )
        
        # Convert ValidationResult objects to ValidationResult format expected by reporting
        results = []
        for vr in validation_results:
            result = ValidationResult(vr.item)
            result.jellyfin_id = vr.jellyfin_id
            result.title = vr.title
            result.jellyfin_path = vr.jellyfin_path
            result.valid = vr.valid
            result.file_size = vr.file_size
            result.actual_path = vr.actual_path
            # Convert issues to strings for compatibility
            for issue in vr.issues:
                result.add_issue(issue.message)
            results.append(result)
    except RuntimeError as e:
        logger.error(f"Validation failed: {e}", exc_info=True)
        print(f"ERROR: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during validation: {e}", exc_info=True)
        print(f"ERROR: Unexpected error: {e}")
        sys.exit(1)
    
    # Output results
    if args.json:
        # JSON output
        output = {
            'total': len(results),
            'valid': sum(1 for r in results if r.valid),
            'invalid': sum(1 for r in results if not r.valid),
            'results': [r.to_dict() for r in results]
        }
        print(json.dumps(output, indent=2, default=str))
    else:
        # Formatted output
        report = format_report(results, missing_only=args.missing_only, invalid_only=args.invalid_only)
        print()
        print(report)
    
    # Exit code: 0 if all valid, 1 if issues found
    invalid_count = sum(1 for r in results if not r.valid)
    if invalid_count > 0:
        logger.warning(f"Validation complete with {invalid_count} invalid file(s)")
    else:
        logger.info("Validation complete: All files are valid")
    
    sys.exit(0 if invalid_count == 0 else 1)


if __name__ == "__main__":
    main()
