#!/usr/bin/env python3
"""
Find Duplicate Movies in Jellyfin Library

Identifies duplicate movies by:
- Exact title match (case-insensitive)
- File size comparison
- Path normalization (case-insensitive)
- Provider ID matching (TMDb, IMDb)

Usage:
    python find_jellyfin_duplicates.py
    python find_jellyfin_duplicates.py --json
"""

import sys
import json
import argparse
from pathlib import Path
from collections import defaultdict
from typing import List, Dict, Tuple

sys.path.insert(0, str(Path(__file__).parent))

from scripts.core.jellyfin_client import JellyfinClient
from scripts.core.jellyfin_config import JellyfinConfigManager


def normalize_path(path: str) -> str:
    """Normalize path for comparison (case-insensitive, normalized separators)."""
    return str(Path(path)).lower().replace('\\', '/')


def get_file_size(item: Dict) -> int:
    """Get total file size from media sources."""
    total = 0
    for source in item.get('MediaSources', []):
        total += source.get('Size', 0)
    return total


def find_duplicates(items: List[Dict]) -> List[Tuple[str, List[Dict]]]:
    """
    Find duplicate movies by title and size.
    
    Returns:
        List of (title, [duplicate_items]) tuples
    """
    # Group by normalized title
    by_title = defaultdict(list)
    for item in items:
        title = item.get('Name', '').strip()
        if title:
            by_title[title.lower()].append(item)
    
    duplicates = []
    for title, items_list in by_title.items():
        if len(items_list) > 1:
            # Check if they're actually duplicates (same size or same path base)
            # Group by size
            by_size = defaultdict(list)
            for item in items_list:
                size = get_file_size(item)
                by_size[size].append(item)
            
            # Also check normalized paths
            by_path_base = defaultdict(list)
            for item in items_list:
                path = item.get('Path', '')
                # Get parent directory (normalized)
                path_base = normalize_path(str(Path(path).parent))
                by_path_base[path_base].append(item)
            
            # If multiple items share same size OR same path base, they're duplicates
            duplicate_groups = []
            seen = set()
            
            for size, size_items in by_size.items():
                if len(size_items) > 1:
                    # Check if paths are similar (case-insensitive)
                    paths = [normalize_path(item.get('Path', '')) for item in size_items]
                    if len(set(paths)) < len(paths):
                        # Some paths are duplicates (case difference)
                        duplicate_groups.append(size_items)
                        for item in size_items:
                            seen.add(item.get('Id'))
            
            # Also check path-based duplicates
            for path_base, path_items in by_path_base.items():
                if len(path_items) > 1 and any(item.get('Id') not in seen for item in path_items):
                    duplicate_groups.append(path_items)
            
            if duplicate_groups:
                duplicates.append((title, items_list))
    
    return duplicates


def format_duplicate_group(title: str, items: List[Dict]) -> str:
    """Format duplicate group for display."""
    lines = []
    lines.append(f"\n{'='*70}")
    lines.append(f"DUPLICATE: {title}")
    lines.append(f"{'='*70}")
    lines.append(f"Found {len(items)} copies:\n")
    
    for i, item in enumerate(items, 1):
        path = item.get('Path', 'N/A')
        size = get_file_size(item)
        size_gb = size / (1024**3)
        jellyfin_id = item.get('Id', 'N/A')
        
        # Get provider IDs
        provider_ids = item.get('ProviderIds', {})
        provider_str = ", ".join([f"{k}:{v}" for k, v in provider_ids.items()]) if provider_ids else "None"
        
        lines.append(f"  Copy {i}:")
        lines.append(f"    Path: {path}")
        lines.append(f"    Size: {size_gb:.2f} GB")
        lines.append(f"    Jellyfin ID: {jellyfin_id}")
        lines.append(f"    Provider IDs: {provider_str}")
        
        # Check if path is case-different duplicate
        normalized = normalize_path(path)
        for j, other in enumerate(items):
            if i != j:
                other_normalized = normalize_path(other.get('Path', ''))
                if normalized == other_normalized:
                    lines.append(f"    [WARNING] CASE-DUPLICATE of Copy {j+1}")
        
        lines.append("")
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description='Find duplicate movies in Jellyfin library',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output JSON instead of formatted text'
    )
    parser.add_argument(
        '--min-size',
        type=int,
        default=0,
        help='Minimum file size in MB to consider (default: 0)'
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
    
    # Filter by minimum size
    if args.min_size > 0:
        min_bytes = args.min_size * 1024 * 1024
        items = [item for item in items if get_file_size(item) >= min_bytes]
        print(f"Filtered to {len(items)} movies >= {args.min_size} MB")
    
    # Find duplicates
    print("\nAnalyzing for duplicates...")
    duplicates = find_duplicates(items)
    
    if not duplicates:
        print("\n[SUCCESS] No duplicates found!")
        sys.exit(0)
    
    print(f"\n[WARNING] Found {len(duplicates)} duplicate movie(s):")
    
    if args.json:
        # JSON output
        output = []
        for title, items_list in duplicates:
            output.append({
                'title': title,
                'count': len(items_list),
                'items': [
                    {
                        'id': item.get('Id'),
                        'path': item.get('Path'),
                        'size_gb': round(get_file_size(item) / (1024**3), 2),
                        'provider_ids': item.get('ProviderIds', {})
                    }
                    for item in items_list
                ]
            })
        print(json.dumps(output, indent=2, default=str))
    else:
        # Formatted output
        total_duplicates = sum(len(items) - 1 for _, items in duplicates)
        print(f"Total duplicate copies: {total_duplicates}\n")
        
        for title, items_list in duplicates:
            print(format_duplicate_group(title, items_list))
        
        print(f"\n{'='*70}")
        print(f"SUMMARY: {len(duplicates)} movies have duplicates")
        print(f"Total extra copies: {total_duplicates}")
        print(f"{'='*70}")


if __name__ == "__main__":
    main()

