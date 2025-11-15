#!/usr/bin/env python3
"""
Fix Movie Naming Issues

Fixes identified movie naming problems:
1. Removes codec tags from filenames (H.265, H.264, etc.)
2. Prompts for manual correction of truncated titles
3. Ensures proper Jellyfin naming format

Works with the output from analyze_movie_names.py
"""

import sys
import json
import re
from pathlib import Path
from typing import Dict, List

sys.path.insert(0, str(Path(__file__).parent / '_common'))

from immutable_audit import ImmutableAuditLog
from snapshot_manager import SnapshotManager
from logger import ProjectLogger
from media_utils import hash_file


def remove_codec_tags(filename: str) -> str:
    """Remove codec tags from filename."""
    cleaned = filename
    
    # Remove codec patterns
    codec_patterns = [
        r'\s*H\.?265\s*',
        r'\s*H\.?264\s*',
        r'\s*HEVC\s*',
        r'\s*x264\s*',
        r'\s*x265\s*',
        r'\s*AVC\s*'
    ]
    
    for pattern in codec_patterns:
        cleaned = re.sub(pattern, ' ', cleaned, flags=re.IGNORECASE)
    
    # Clean up multiple spaces
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    return cleaned


def fix_codec_tags(issues: List[Dict], media_root: Path, audit: ImmutableAuditLog, 
                   logger: ProjectLogger, dry_run: bool = False) -> int:
    """Fix files with codec tags in their names."""
    
    if not issues:
        return 0
    
    logger.info(f"🟡 Fixing {len(issues)} files with codec tags...")
    logger.info("")
    
    fixed_count = 0
    
    for item in issues:
        old_path = media_root / item['path']
        
        if not old_path.exists():
            logger.warning(f"  ⚠️  File not found: {old_path}")
            continue
        
        # Get cleaned filename
        old_filename = old_path.stem
        cleaned_filename = remove_codec_tags(old_filename)
        
        # If no change, skip
        if old_filename == cleaned_filename:
            logger.info(f"  ℹ️  No change needed: {old_filename}")
            continue
        
        # Create new path
        new_path = old_path.parent / f"{cleaned_filename}{old_path.suffix}"
        
        logger.info(f"  📝 {old_path.name}")
        logger.info(f"     → {new_path.name}")
        
        if dry_run:
            logger.dryrun(f"     [DRY RUN] Would rename file")
        else:
            try:
                # Hash before rename
                hash_before = hash_file(old_path)
                
                # Rename file
                old_path.rename(new_path)
                
                # Hash after rename
                hash_after = hash_file(new_path)
                
                # Verify integrity
                if hash_before != hash_after:
                    logger.error(f"     ❌ Hash mismatch after rename!")
                    # Restore original name
                    new_path.rename(old_path)
                    continue
                
                # Also rename parent folder if it has codec tags
                parent_folder = new_path.parent
                parent_name = parent_folder.name
                cleaned_parent = remove_codec_tags(parent_name)
                
                if parent_name != cleaned_parent:
                    new_parent = parent_folder.parent / cleaned_parent
                    logger.info(f"     📁 Renaming folder: {parent_name}")
                    logger.info(f"        → {cleaned_parent}")
                    
                    parent_folder.rename(new_parent)
                    new_path = new_parent / new_path.name
                
                # Log to audit
                audit.log_event('rename_remove_codec', {
                    'old_path': str(old_path),
                    'new_path': str(new_path),
                    'old_filename': old_filename,
                    'new_filename': cleaned_filename,
                    'hash': hash_after,
                    'file_size': new_path.stat().st_size
                })
                
                logger.success(f"     ✅ Renamed successfully")
                fixed_count += 1
                
            except Exception as e:
                logger.error(f"     ❌ Error: {e}")
        
        logger.info("")
    
    return fixed_count


def prompt_truncated_title_fixes(issues: List[Dict], media_root: Path, 
                                 audit: ImmutableAuditLog, logger: ProjectLogger,
                                 dry_run: bool = False) -> int:
    """Interactively fix truncated movie titles."""
    
    if not issues:
        return 0
    
    logger.info(f"🔴 Found {len(issues)} files with potentially truncated titles")
    logger.info("    These require manual review and correction:")
    logger.info("")
    
    fixed_count = 0
    
    for i, item in enumerate(issues, 1):
        old_path = media_root / item['path']
        
        if not old_path.exists():
            logger.warning(f"  ⚠️  File not found: {old_path}")
            continue
        
        logger.info(f"[{i}/{len(issues)}] Current: {item['filename']}")
        logger.info(f"         Path: {item['path']}")
        logger.info("")
        
        if dry_run:
            logger.dryrun("         [DRY RUN] Skipping interactive prompt")
            logger.info("")
            continue
        
        # Prompt for correct title
        print("    Enter the correct full title (or press Enter to skip):")
        print("    Format: Title (Year)")
        print("    Example: Doc Martin and the Legend of the Cloutie Well (2003)")
        print("    > ", end="")
        
        user_input = input().strip()
        
        if not user_input:
            logger.info("         ⏭️  Skipped")
            logger.info("")
            continue
        
        # Parse the input
        match = re.match(r'^(.+?)\s*\((\d{4})\)$', user_input)
        if not match:
            logger.warning("         ⚠️  Invalid format. Skipping.")
            logger.info("")
            continue
        
        new_title = match.group(1).strip()
        new_year = match.group(2)
        
        # Create new filename
        new_filename = f"{new_title} ({new_year})"
        
        # Determine the correct parent directory
        # If file is already in a folder, use that folder's parent (Movies dir)
        # If file is loose in Movies dir, use Movies dir
        if old_path.parent.name == "Movies":
            # File is loose in Movies directory
            movies_dir = old_path.parent
        else:
            # File is in a subfolder, go up to Movies directory
            movies_dir = old_path.parent.parent
        
        # Create new folder in Movies directory
        new_parent = movies_dir / new_filename
        new_parent.mkdir(exist_ok=True)
        final_path = new_parent / f"{new_filename}{old_path.suffix}"
        
        try:
            # Hash before rename
            hash_before = hash_file(old_path)
            
            # Move to new location
            old_path.rename(final_path)
            
            # Hash after rename
            hash_after = hash_file(final_path)
            
            # Verify integrity
            if hash_before != hash_after:
                logger.error(f"         ❌ Hash mismatch after rename!")
                final_path.rename(old_path)
                continue
            
            # Remove old parent folder if empty
            if not any(old_path.parent.iterdir()):
                old_path.parent.rmdir()
            
            # Log to audit
            audit.log_event('rename_fix_truncated', {
                'old_path': str(old_path),
                'new_path': str(final_path),
                'old_filename': item['filename'],
                'new_filename': new_filename,
                'hash': hash_after,
                'file_size': final_path.stat().st_size
            })
            
            logger.success(f"         ✅ Renamed to: {new_filename}")
            fixed_count += 1
            
        except Exception as e:
            logger.error(f"         ❌ Error: {e}")
        
        logger.info("")
    
    return fixed_count


def main():
    """Main execution function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Fix movie naming issues identified by analyze_movie_names.py'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be changed without actually changing files'
    )
    parser.add_argument(
        '--media-root',
        default='M:\\#MEDIA',
        help='Root directory of media files'
    )
    parser.add_argument(
        '--issues-file',
        default='reports/movie_naming_issues.json',
        help='Path to issues JSON file from analyze_movie_names.py'
    )
    parser.add_argument(
        '--skip-truncated',
        action='store_true',
        help='Skip fixing truncated titles (only fix codec tags)'
    )
    
    args = parser.parse_args()
    
    # Initialize logger
    logger = ProjectLogger('fix_movie_names')
    
    logger.info("=" * 70)
    logger.info("MOVIE NAMING FIXES")
    logger.info("=" * 70)
    logger.info("")
    
    if args.dry_run:
        logger.dryrun("🔍 DRY RUN MODE - No files will be modified")
        logger.info("")
    
    # Load issues file
    issues_file = Path(__file__).parent / args.issues_file
    
    if not issues_file.exists():
        logger.error(f"❌ Issues file not found: {issues_file}")
        logger.info("")
        logger.info("💡 Run analyze_movie_names.py first to generate the issues file")
        return 1
    
    with open(issues_file, 'r', encoding='utf-8') as f:
        issues = json.load(f)
    
    media_root = Path(args.media_root)
    if not media_root.exists():
        logger.error(f"❌ Media root not found: {media_root}")
        return 1
    
    # Initialize audit log
    audit = ImmutableAuditLog()
    audit.initialize()
    
    # Create snapshot before making changes
    if not args.dry_run:
        logger.info("📸 Creating snapshot before making changes...")
        snapshot_id = SnapshotManager.create_snapshot(
            media_root=str(media_root),
            snapshot_type="pre_movie_name_fixes"
        )
        logger.success(f"✅ Snapshot created: {snapshot_id}")
        logger.info("")
    
    # Fix codec tags
    codec_fixed = fix_codec_tags(
        issues.get('codec_in_name', []),
        media_root,
        audit,
        logger,
        args.dry_run
    )
    
    # Fix truncated titles (interactive)
    truncated_fixed = 0
    if not args.skip_truncated and issues.get('truncated_titles'):
        truncated_fixed = prompt_truncated_title_fixes(
            issues.get('truncated_titles', []),
            media_root,
            audit,
            logger,
            args.dry_run
        )
    
    # Summary
    logger.info("=" * 70)
    logger.info("SUMMARY")
    logger.info("=" * 70)
    logger.info(f"✅ Codec tags removed: {codec_fixed}")
    logger.info(f"✅ Truncated titles fixed: {truncated_fixed}")
    
    if args.dry_run:
        logger.dryrun("🔍 DRY RUN - No files were modified")
    
    logger.info("")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
