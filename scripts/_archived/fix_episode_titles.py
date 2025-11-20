#!/usr/bin/env python3
r"""
Episode Title Fixer Script

Applies episode title cleaning recommendations from analysis.
Creates snapshots and logs all changes for rollback safety.

Usage:
    python fix_episode_titles.py [media_root] [show_name] [--dry-run]

Examples:
    python fix_episode_titles.py "M:\#MEDIA" "Star Trek - Voyager (1995)" --dry-run
    python fix_episode_titles.py "M:\#MEDIA" "Looney Tunes (1930)"
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
sys.path.insert(0, '_common')

from media_utils import clean_episode_title, compare_episode_titles
from tv_episode_cache import TVEpisodeCache
from immutable_audit import ImmutableAuditLog
from snapshot_manager import SnapshotManager

def load_analysis_results() -> Dict[str, Any]:
    """Load the analysis results from the JSON file."""
    results_file = Path('reports/episode_title_analysis.json')
    if not results_file.exists():
        print(f"❌ Analysis results not found: {results_file}")
        print("Run analyze_episode_titles.py first.")
        return {}

    with open(results_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def find_show_issues(analysis_data: Dict[str, Any], target_show: str) -> List[Dict[str, Any]]:
    """Find issues for a specific show."""
    for show_name, show_data in analysis_data.get('shows', {}).items():
        if show_name.lower() == target_show.lower():
            return show_data.get('issues', [])
    return []

def apply_title_fix(media_root: Path, issue: Dict[str, Any], dry_run: bool = False) -> bool:
    """Apply a single title fix."""
    rel_path = issue['file']
    # The rel_path is relative to TV Shows directory, so construct full path
    full_path = media_root / "TV Shows" / rel_path
    
    if not full_path.exists():
        print(f"⚠️  File not found: {full_path}")
        return False    # Determine new title
    if issue['type'] in ['title_mismatch', 'technical_tags']:
        new_title = issue.get('cleaned_title', issue.get('canonical_title', issue['current_title']))
    else:
        print(f"⚠️  Skipping unsupported issue type: {issue['type']}")
        return False

    # Parse current filename to reconstruct with new title
    current_name = full_path.name
    name_parts = current_name.rsplit('.', 1)
    base_name = name_parts[0]
    extension = name_parts[1] if len(name_parts) > 1 else ''

    # Different patterns for different filename formats
    import re

    # Pattern 1: "S01E01 - Episode Title"
    pattern1 = r'^(S\d+E\d+(?:-E\d+)?)\s*-\s*(.+)$'
    match1 = re.match(pattern1, base_name, re.IGNORECASE)

    if match1:
        episode_part = match1.group(1)
        new_name = f"{episode_part} - {new_title}.{extension}"
    else:
        # Pattern 2: "Show Title S01E01 Title"
        pattern2 = r'^(.+?)\s+(S\d+E\d+(?:-E\d+)?)\s+(.+)$'
        match2 = re.match(pattern2, base_name, re.IGNORECASE)

        if match2:
            show_part = match2.group(1)
            episode_part = match2.group(2)
            new_name = f"{show_part} {episode_part} {new_title}.{extension}"
        else:
            print(f"⚠️  Could not parse filename pattern: {current_name}")
            return False

    if new_name == current_name:
        print(f"ℹ️  No change needed: {rel_path}")
        return True

    new_path = full_path.parent / new_name

    if dry_run:
        print(f"🔄 Would rename: {rel_path}")
        print(f"   To: {new_path.relative_to(media_root)}")
        return True

    # Perform the rename
    try:
        full_path.rename(new_path)
        print(f"✅ Renamed: {rel_path}")
        print(f"   To: {new_path.relative_to(media_root)}")
        return True
    except Exception as e:
        print(f"❌ Failed to rename {rel_path}: {e}")
        return False

def fix_show_titles(media_root: Path, show_name: str, dry_run: bool = False) -> bool:
    """Fix all title issues for a specific show."""
    print(f"🎬 Fixing episode titles for: {show_name}")
    print(f"📁 Media root: {media_root}")
    print(f"🏃 Dry run: {dry_run}")
    print("=" * 50)

    # Load analysis results
    analysis_data = load_analysis_results()
    if not analysis_data:
        return False

    # Find issues for this show
    issues = find_show_issues(analysis_data, show_name)
    if not issues:
        print(f"ℹ️  No issues found for show: {show_name}")
        return True

    print(f"📊 Found {len(issues)} issues to fix")

    # Initialize audit and snapshot
    audit = ImmutableAuditLog()
    audit.initialize()

    snapshot_id = None
    if not dry_run:
        # Create snapshot before changes
        snapshot_id = SnapshotManager.create_snapshot(
            media_root=str(media_root / "TV Shows" / show_name),
            snapshot_type="pre_title_fix"
        )
        print(f"📸 Created snapshot: {snapshot_id}")

        # Log the operation start
        audit.log_event("title_fix_start", {
            "show_name": show_name,
            "issues_count": len(issues),
            "snapshot_id": snapshot_id,
            "dry_run": dry_run
        }, actor="fix_episode_titles.py")

    # Apply fixes
    success_count = 0
    for i, issue in enumerate(issues, 1):
        print(f"\n[{i}/{len(issues)}] ", end="")
        if apply_title_fix(media_root, issue, dry_run):
            success_count += 1

            if not dry_run:
                # Log each successful fix
                audit.log_event("title_fix_applied", {
                    "show_name": show_name,
                    "file": issue['file'],
                    "old_title": issue.get('current_title', 'N/A'),
                    "new_title": issue.get('cleaned_title', issue.get('canonical_title', 'N/A')),
                    "snapshot_id": snapshot_id
                }, actor="fix_episode_titles.py")

    # Summary
    print(f"\n{'='*50}")
    if dry_run:
        print(f"🏃 Dry run complete: {success_count}/{len(issues)} would be fixed")
    else:
        print(f"✅ Fixed {success_count}/{len(issues)} episode titles")

        # Log completion
        audit.log_event("title_fix_complete", {
            "show_name": show_name,
            "fixed_count": success_count,
            "total_issues": len(issues),
            "snapshot_id": snapshot_id
        }, actor="fix_episode_titles.py")

    return success_count > 0

def main():
    parser = argparse.ArgumentParser(description="Fix episode titles based on analysis results")
    parser.add_argument("media_root", help="Path to media root directory")
    parser.add_argument("show_name", help="Name of the show to fix (must match analysis results)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be changed without making changes")

    args = parser.parse_args()

    media_root = Path(args.media_root)
    if not media_root.exists():
        print(f"❌ Media root not found: {media_root}")
        sys.exit(1)

    success = fix_show_titles(media_root, args.show_name, args.dry_run)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()