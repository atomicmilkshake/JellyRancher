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
from scripts.core.jellyfin_validator import JellyfinValidator, ValidationResult

# Setup logging
logger = logging.getLogger(__name__)


def validate_library(
    client: JellyfinClient,
    media_types: Optional[List[str]] = None
) -> List[ValidationResult]:
    """
    Validate all items in Jellyfin library using JellyfinValidator.
    
    Args:
        client: JellyfinClient instance
        media_types: List of media types to check (e.g., ['Movie', 'Episode'])
                    If None, checks all media types
    
    Returns:
        List of ValidationResult objects
    """
    # Use JellyfinValidator for validation
    validator = JellyfinValidator(client)
    return validator.validate_library(media_types=media_types)


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
        display_results = [r for r in results if any('does not exist' in (issue.message if hasattr(issue, 'message') else str(issue)) for issue in r.issues)]
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
            # Use first issue message as category
            first_issue = result.issues[0]
            category = first_issue.message if hasattr(first_issue, 'message') else str(first_issue)
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
                    issue_str = issue.message if hasattr(issue, 'message') else str(issue)
                    lines.append(f"    - {issue_str}")
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
        results = validate_library(client, media_types=args.media_types)
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
