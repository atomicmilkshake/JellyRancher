#!/usr/bin/env python3
"""
Verify Jellyfin Movie Files Exist on Filesystem

Checks if files reported by Jellyfin actually exist on disk.
Handles Windows case-insensitivity to detect if duplicate paths
point to the same physical file.

Usage:
    python verify_jellyfin_files_exist.py
    python verify_jellyfin_files_exist.py --check-duplicates
"""

import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Tuple, Optional

sys.path.insert(0, str(Path(__file__).parent))

from scripts.core.jellyfin_client import JellyfinClient
from scripts.core.jellyfin_config import JellyfinConfigManager


def normalize_path(path: str) -> str:
    """Normalize path for comparison (case-insensitive, normalized separators)."""
    return str(Path(path)).lower().replace('\\', '/')


def resolve_path(path_str: str) -> Optional[Path]:
    """Resolve path and check if it exists (case-insensitive on Windows)."""
    try:
        path = Path(path_str)
        # On Windows, Path.exists() is case-insensitive
        if path.exists():
            # Get the actual resolved path (what Windows sees)
            return path.resolve()
        return None
    except Exception:
        return None


def get_actual_path(path_str: str) -> Optional[Path]:
    """
    Get the actual filesystem path (case-corrected).
    On Windows, this resolves case-insensitive paths to their actual case.
    """
    try:
        path = Path(path_str)
        if path.exists():
            # Resolve to get actual case
            resolved = path.resolve()
            return resolved
        return None
    except Exception:
        return None


def verify_movie_file(item: Dict) -> Dict:
    """
    Verify a movie file exists and get filesystem info.
    
    Returns:
        Dict with verification results
    """
    jellyfin_path = item.get('Path', '')
    jellyfin_id = item.get('Id', 'N/A')
    title = item.get('Name', 'N/A')
    
    result = {
        'jellyfin_id': jellyfin_id,
        'title': title,
        'jellyfin_path': jellyfin_path,
        'exists': False,
        'actual_path': None,
        'is_file': False,
        'file_size': None,
        'error': None
    }
    
    if not jellyfin_path:
        result['error'] = 'No path in Jellyfin metadata'
        return result
    
    # Check if path exists
    fs_path = resolve_path(jellyfin_path)
    if fs_path is None:
        result['error'] = 'File does not exist on filesystem'
        return result
    
    result['exists'] = True
    result['actual_path'] = str(fs_path)
    
    # Check if it's a file (not a directory)
    if fs_path.is_file():
        result['is_file'] = True
        result['file_size'] = fs_path.stat().st_size
    elif fs_path.is_dir():
        result['error'] = 'Path is a directory, not a file'
        # Try to find video files in directory
        video_extensions = {'.mp4', '.mkv', '.avi', '.m4v', '.mov', '.wmv', '.flv', '.webm'}
        video_files = [f for f in fs_path.iterdir() if f.suffix.lower() in video_extensions]
        if video_files:
            result['found_video_files'] = [str(f) for f in video_files]
    
    return result


def check_duplicate_paths(items: List[Dict]) -> List[Tuple[str, List[Dict]]]:
    """Find items with duplicate paths (case-insensitive)."""
    by_normalized_path = {}
    duplicates = []
    
    for item in items:
        path = item.get('Path', '')
        if not path:
            continue
        
        normalized = normalize_path(path)
        if normalized in by_normalized_path:
            # Found duplicate path
            if normalized not in [d[0] for d in duplicates]:
                duplicates.append((normalized, [by_normalized_path[normalized], item]))
            else:
                # Add to existing duplicate group
                for dup in duplicates:
                    if dup[0] == normalized:
                        dup[1].append(item)
                        break
        else:
            by_normalized_path[normalized] = item
    
    return duplicates


def main():
    parser = argparse.ArgumentParser(
        description='Verify Jellyfin movie files exist on filesystem',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        '--check-duplicates',
        action='store_true',
        help='Also check for duplicate paths (case-insensitive)'
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
    
    args = parser.parse_args()
    
    # Initialize Jellyfin client
    config = JellyfinConfigManager()
    client = JellyfinClient(
        server_url=config.get_server_url(),
        api_key=config.get_api_key()
    )
    
    print("Testing Jellyfin connection...")
    if not client.test_connection():
        print("ERROR: Connection failed!")
        sys.exit(1)
    
    print("Connected successfully")
    print("Fetching all movies from Jellyfin library...")
    
    # Get all movies
    items = client.get_all_items(
        item_types=['Movie'],
        fields=['Name', 'Path', 'MediaSources', 'Id', 'ProviderIds', 'ProductionYear']
    )
    
    print(f"Found {len(items)} movies in library")
    print("Verifying files exist on filesystem...\n")
    
    # Verify each file
    results = []
    missing_count = 0
    exists_count = 0
    
    for item in items:
        result = verify_movie_file(item)
        results.append(result)
        
        if result['exists']:
            exists_count += 1
        else:
            missing_count += 1
    
    # Check for duplicate paths if requested
    duplicate_paths = []
    if args.check_duplicates:
        print("Checking for duplicate paths (case-insensitive)...")
        duplicate_paths = check_duplicate_paths(items)
    
    # Filter results
    display_results = results
    if args.missing_only:
        display_results = [r for r in results if not r['exists']]
    
    # Output
    if args.json:
        output = {
            'total_movies': len(items),
            'exists': exists_count,
            'missing': missing_count,
            'results': results
        }
        if duplicate_paths:
            output['duplicate_paths'] = [
                {
                    'normalized_path': norm_path,
                    'items': [
                        {
                            'id': item.get('Id'),
                            'title': item.get('Name'),
                            'path': item.get('Path')
                        }
                        for item in items_list
                    ]
                }
                for norm_path, items_list in duplicate_paths
            ]
        print(json.dumps(output, indent=2, default=str))
    else:
        # Formatted output
        print(f"{'='*70}")
        print(f"VERIFICATION RESULTS")
        print(f"{'='*70}")
        print(f"Total movies: {len(items)}")
        print(f"Files exist: {exists_count}")
        print(f"Files missing: {missing_count}")
        print(f"{'='*70}\n")
        
        if display_results:
            for result in display_results:
                status = "[EXISTS]" if result['exists'] else "[MISSING]"
                print(f"{status} {result['title']}")
                print(f"  Jellyfin Path: {result['jellyfin_path']}")
                
                if result['exists']:
                    print(f"  Actual Path: {result['actual_path']}")
                    if result['is_file']:
                        size_gb = result['file_size'] / (1024**3)
                        print(f"  Size: {size_gb:.2f} GB")
                    else:
                        print(f"  [WARNING] Path is directory, not file")
                        if 'found_video_files' in result:
                            print(f"  Found video files in directory:")
                            for vf in result['found_video_files']:
                                print(f"    - {vf}")
                else:
                    if result['error']:
                        print(f"  Error: {result['error']}")
                print()
        
        # Show duplicate paths
        if duplicate_paths:
            print(f"\n{'='*70}")
            print(f"DUPLICATE PATHS (Case-Insensitive)")
            print(f"{'='*70}")
            print(f"Found {len(duplicate_paths)} duplicate path(s):\n")
            
            for norm_path, items_list in duplicate_paths:
                print(f"Path (normalized): {norm_path}")
                print(f"  Found {len(items_list)} Jellyfin entries pointing to same path:\n")
                
                for i, item in enumerate(items_list, 1):
                    title = item.get('Name', 'N/A')
                    jellyfin_id = item.get('Id', 'N/A')
                    jellyfin_path = item.get('Path', 'N/A')
                    
                    # Verify this specific path
                    verify_result = verify_movie_file(item)
                    
                    print(f"  Entry {i}:")
                    print(f"    Title: {title}")
                    print(f"    Jellyfin ID: {jellyfin_id}")
                    print(f"    Jellyfin Path: {jellyfin_path}")
                    print(f"    Exists on disk: {verify_result['exists']}")
                    if verify_result['exists']:
                        print(f"    Actual Path: {verify_result['actual_path']}")
                        if verify_result['is_file']:
                            size_gb = verify_result['file_size'] / (1024**3)
                            print(f"    Size: {size_gb:.2f} GB")
                    
                    # Check if paths resolve to same file
                    if i > 1:
                        first_path = resolve_path(items_list[0].get('Path', ''))
                        current_path = resolve_path(jellyfin_path)
                        if first_path and current_path:
                            if first_path == current_path:
                                print(f"    [SAME FILE] Resolves to same filesystem path as Entry 1")
                            else:
                                print(f"    [DIFFERENT] Resolves to different path than Entry 1")
                    print()
        
        print(f"\n{'='*70}")
        print(f"SUMMARY")
        print(f"{'='*70}")
        print(f"Total: {len(items)} movies")
        print(f"Exist: {exists_count}")
        print(f"Missing: {missing_count}")
        if duplicate_paths:
            print(f"Duplicate paths: {len(duplicate_paths)}")
        print(f"{'='*70}")


if __name__ == "__main__":
    main()

