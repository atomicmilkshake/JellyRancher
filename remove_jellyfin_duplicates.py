#!/usr/bin/env python3
"""
Find Duplicate Jellyfin Entries

Identifies duplicate entries (Movies, Episodes, etc.) caused by case-sensitive path differences.
Generates a summary report with recommendations on which entries to keep and which to remove.

READ-ONLY OPERATION: This script does not modify or delete any files.
It only analyzes Jellyfin metadata and generates recommendations.
"""

import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Tuple
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent))

from scripts.core.jellyfin_client import JellyfinClient
from scripts.core.jellyfin_config import JellyfinConfigManager


def normalize_path(path: str) -> str:
    """Normalize path for comparison (case-insensitive, normalized separators)."""
    return str(Path(path)).lower().replace('\\', '/')


def resolve_path(path_str: str) -> Path:
    """Resolve path and get actual filesystem path."""
    try:
        path = Path(path_str)
        if path.exists():
            return path.resolve()
        return path
    except Exception:
        return Path(path_str)


def find_duplicate_groups(items: List[Dict]) -> List[Tuple[str, List[Dict]]]:
    """
    Find groups of duplicate items (same normalized path).
    
    Returns:
        List of (normalized_path, [duplicate_items]) tuples
    """
    by_normalized_path = defaultdict(list)
    
    for item in items:
        path = item.get('Path', '')
        if path:
            normalized = normalize_path(path)
            by_normalized_path[normalized].append(item)
    
    # Return only groups with duplicates
    duplicates = [(norm_path, items_list) for norm_path, items_list in by_normalized_path.items() 
                  if len(items_list) > 1]
    
    return duplicates


def choose_keep_entry(items: List[Dict]) -> Tuple[Dict, List[Dict]]:
    """
    Choose which entry to keep and which to delete.
    
    Strategy: Compare Jellyfin path to resolved filesystem path.
    Keep the entry where they match exactly (correct case).
    Delete entries where they don't match (wrong case).
    
    Returns:
        (entry_to_keep, [entries_to_delete])
    """
    if len(items) == 1:
        return items[0], []
    
    # For each item, compare Jellyfin path to resolved filesystem path
    for item in items:
        jellyfin_path = item.get('Path', '')
        if not jellyfin_path:
            continue
        
        resolved = resolve_path(jellyfin_path)
        if resolved.exists():
            resolved_path_str = str(resolved)
            # If Jellyfin path matches resolved path exactly, keep this one
            if jellyfin_path == resolved_path_str:
                to_delete = [other for other in items if other != item]
                return item, to_delete
    
    # Fallback: if no exact match found, prefer entry with more metadata
    best = max(items, key=lambda x: len(x.get('ProviderIds', {})))
    to_delete = [item for item in items if item != best]
    return best, to_delete


def format_recommendations_report(
    duplicate_groups: List[Tuple[str, List[Dict]]],
    to_keep: List[Dict],
    to_delete: List[Dict]
) -> str:
    """Format a comprehensive recommendations report."""
    lines = []
    
    lines.append("=" * 70)
    lines.append("DUPLICATE ENTRIES ANALYSIS & RECOMMENDATIONS")
    lines.append("=" * 70)
    lines.append("")
    lines.append("SUMMARY:")
    lines.append(f"  Total duplicate groups found: {len(duplicate_groups)}")
    lines.append(f"  Entries to KEEP: {len(to_keep)}")
    lines.append(f"  Entries to DELETE: {len(to_delete)}")
    lines.append("")
    lines.append("=" * 70)
    lines.append("")
    
    if not duplicate_groups:
        lines.append("[SUCCESS] No duplicates found in your Jellyfin library!")
        return "\n".join(lines)
    
    lines.append("RECOMMENDATIONS:")
    lines.append("")
    lines.append("The following duplicate entries were found. For each group,")
    lines.append("one entry matches the actual filesystem path and should be KEPT.")
    lines.append("The others should be DELETED from Jellyfin (files will not be affected).")
    lines.append("")
    lines.append("=" * 70)
    lines.append("")
    
    # Group by media type for better organization
    by_type = defaultdict(list)
    for norm_path, items_list in duplicate_groups:
        item_type = items_list[0].get('Type', 'Unknown')
        by_type[item_type].append((norm_path, items_list))
    
    for item_type, groups in sorted(by_type.items()):
        lines.append(f"{'=' * 70}")
        lines.append(f"{item_type.upper()} DUPLICATES")
        lines.append(f"{'=' * 70}")
        lines.append(f"Found {len(groups)} duplicate group(s) for {item_type}s")
        lines.append("")
        
        for norm_path, items_list in groups:
            # Find which one to keep and which to delete
            keep_item = None
            delete_items = []
            for item in items_list:
                jellyfin_path = item.get('Path', '')
                resolved = resolve_path(jellyfin_path)
                if resolved.exists():
                    resolved_path_str = str(resolved)
                    if jellyfin_path == resolved_path_str:
                        keep_item = item
                        break
            
            if not keep_item:
                # Fallback: use first item
                keep_item = items_list[0]
            
            delete_items = [item for item in items_list if item != keep_item]
            
            lines.append(f"Duplicate Path: {norm_path}")
            lines.append(f"  Found {len(items_list)} entries pointing to the same file")
            lines.append("")
            lines.append("  RECOMMENDATION: KEEP")
            lines.append(f"    Title: {keep_item.get('Name', 'N/A')}")
            lines.append(f"    Path: {keep_item.get('Path', 'N/A')}")
            lines.append(f"    Jellyfin ID: {keep_item.get('Id', 'N/A')}")
            lines.append(f"    Reason: Path matches actual filesystem path")
            lines.append("")
            lines.append(f"  RECOMMENDATION: DELETE ({len(delete_items)} entries)")
            for item in delete_items:
                lines.append(f"    - {item.get('Name', 'N/A')}")
                lines.append(f"      Path: {item.get('Path', 'N/A')}")
                lines.append(f"      Jellyfin ID: {item.get('Id', 'N/A')}")
                lines.append(f"      Reason: Path case doesn't match filesystem")
            lines.append("")
    
    lines.append("=" * 70)
    lines.append("NEXT STEPS")
    lines.append("=" * 70)
    lines.append("")
    lines.append("To remove these duplicates, you can:")
    lines.append("")
    lines.append("1. Use the Jellyfin web interface:")
    lines.append("   - Navigate to each item listed above")
    lines.append("   - Delete the duplicate entries manually")
    lines.append("")
    lines.append("2. Use Jellyfin API (if you have a script):")
    lines.append("   - Delete items using their Jellyfin IDs listed above")
    lines.append("   - Example: DELETE /Items/{jellyfin_id}")
    lines.append("")
    lines.append("3. Export this report to JSON for programmatic deletion:")
    lines.append("   python remove_jellyfin_duplicates.py --json > duplicates.json")
    lines.append("")
    lines.append("IMPORTANT: Only the Jellyfin library entries will be removed.")
    lines.append("The actual video files on your filesystem will NOT be affected.")
    lines.append("")
    lines.append("=" * 70)
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description='Find duplicate Jellyfin entries and generate recommendations',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python remove_jellyfin_duplicates.py                              # Analyze all types
  python remove_jellyfin_duplicates.py --media-types Movie          # Movies only
  python remove_jellyfin_duplicates.py --media-types Episode        # TV Episodes only
  python remove_jellyfin_duplicates.py --media-types Movie Episode  # Both Movies and Episodes
  python remove_jellyfin_duplicates.py --json                       # JSON output
        """
    )
    parser.add_argument(
        '--media-types',
        nargs='+',
        default=['Movie', 'Episode'],
        help='Media types to check (e.g., Movie Episode). Default: Movie Episode (both)'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output JSON instead of formatted report'
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
    
    # Build description of what we're checking
    media_types_str = ', '.join(args.media_types)
    print(f"Fetching {media_types_str} from Jellyfin library...")
    
    # Get all items of specified types
    items = client.get_all_items(
        item_types=args.media_types,
        fields=['Name', 'Path', 'MediaSources', 'Id', 'ProviderIds', 'ProductionYear']
    )
    
    print(f"Found {len(items)} {media_types_str.lower()} in library")
    print("Analyzing for duplicates...\n")
    
    # Find duplicate groups
    duplicate_groups = find_duplicate_groups(items)
    
    if not duplicate_groups:
        print("[SUCCESS] No duplicates found!")
        sys.exit(0)
    
    print(f"[WARNING] Found {len(duplicate_groups)} duplicate path(s)\n")
    
    # Process each duplicate group to determine keep/delete
    to_delete = []
    to_keep = []
    
    for norm_path, items_list in duplicate_groups:
        keep_item, delete_items = choose_keep_entry(items_list)
        to_keep.append(keep_item)
        to_delete.extend(delete_items)
    
    # Generate recommendations report
    if args.json:
        # JSON output for programmatic use
        output = {
            'summary': {
                'total_duplicate_groups': len(duplicate_groups),
                'entries_to_keep': len(to_keep),
                'entries_to_delete': len(to_delete)
            },
            'duplicates': []
        }
        
        for norm_path, items_list in duplicate_groups:
            # Determine which to keep
            keep_item = None
            for item in items_list:
                jellyfin_path = item.get('Path', '')
                resolved = resolve_path(jellyfin_path)
                if resolved.exists():
                    resolved_path_str = str(resolved)
                    if jellyfin_path == resolved_path_str:
                        keep_item = item
                        break
            
            if not keep_item:
                keep_item = items_list[0]
            
            delete_items = [item for item in items_list if item != keep_item]
            
            output['duplicates'].append({
                'normalized_path': norm_path,
                'keep': {
                    'jellyfin_id': keep_item.get('Id'),
                    'title': keep_item.get('Name'),
                    'path': keep_item.get('Path'),
                    'type': keep_item.get('Type', 'Unknown')
                },
                'delete': [
                    {
                        'jellyfin_id': item.get('Id'),
                        'title': item.get('Name'),
                        'path': item.get('Path'),
                        'type': item.get('Type', 'Unknown')
                    }
                    for item in delete_items
                ]
            })
        
        print(json.dumps(output, indent=2, default=str))
    else:
        # Formatted recommendations report
        report = format_recommendations_report(duplicate_groups, to_keep, to_delete)
        print(report)


if __name__ == "__main__":
    main()

