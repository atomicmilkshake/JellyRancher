#!/usr/bin/env python3
"""
Empty Directory Cleanup Script
Removes all empty subdirectories from a specified base path.

This script is used by final_cleanup.ps1 to clean up empty folders
after media reorganization.

Usage:
    python cleanup_empty_dirs.py --path "E:/MOVIES"
    python cleanup_empty_dirs.py --path "M:/#MEDIA/Movies"
"""

import os
import sys
from pathlib import Path
import argparse


def cleanup_empty_dirs(base_path: Path, verbose: bool = True) -> int:
    """
    Removes all empty subdirectories from a base path.

    Args:
        base_path: The base directory to clean
        verbose: If True, print progress messages

    Returns:
        Number of directories removed
    """
    if not base_path.exists():
        print(f"ERROR: Path does not exist: {base_path}")
        return 0

    if not base_path.is_dir():
        print(f"ERROR: Path is not a directory: {base_path}")
        return 0

    removed = 0

    if verbose:
        print(f"Cleaning empty directories in: {base_path}")
        print("-" * 70)

    # Sort by depth (deepest first) to ensure we remove leaf directories first
    all_dirs = [d for d in base_path.rglob('*') if d.is_dir()]
    all_dirs_sorted = sorted(all_dirs, key=lambda x: len(x.parts), reverse=True)

    for dirpath in all_dirs_sorted:
        try:
            # Check if directory is empty
            if not any(dirpath.iterdir()):
                dirpath.rmdir()
                removed += 1
                if verbose:
                    print(f"Removed empty directory: {dirpath}")
        except PermissionError:
            if verbose:
                print(f"WARNING: Permission denied: {dirpath}")
        except Exception as e:
            if verbose:
                print(f"WARNING: Could not remove {dirpath}: {e}")

    if verbose:
        print("-" * 70)
        print(f"Cleanup complete: {removed} empty directories removed")

    return removed


def main():
    parser = argparse.ArgumentParser(
        description="Remove empty directories from a specified path.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cleanup_empty_dirs.py --path "E:/MOVIES"
  python cleanup_empty_dirs.py --path "M:/#MEDIA/Movies" --quiet
        """
    )

    parser.add_argument(
        "--path",
        required=True,
        help="The base path to clean (removes empty subdirectories)"
    )

    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress progress output"
    )

    args = parser.parse_args()

    base_path = Path(args.path)
    verbose = not args.quiet

    try:
        removed_count = cleanup_empty_dirs(base_path, verbose=verbose)
        sys.exit(0)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
