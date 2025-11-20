#!/usr/bin/env python3
r"""
Final Episode Title Fixes Script

Handles the remaining 4 unparsed files that require manual resolution:
1. Move Doc Martin TV movies to Movies folder
2. Fix That '70s Show Season 6 Episode 22 filename
3. Clean parentheses from Season 7 Episode 3 title

Usage:
    python fix_remaining_issues.py [media_root]

Example:
    python fix_remaining_issues.py "M:\#MEDIA"
"""

import sys
import shutil
from pathlib import Path
sys.path.insert(0, '_common')

from media_utils import safe_move, hash_file
from immutable_audit import ImmutableAuditLog
from snapshot_manager import SnapshotManager

def move_doc_martin_movies(media_root: Path, audit: ImmutableAuditLog):
    """Move Doc Martin TV movies from TV show Movies folder to root Movies folder."""

    # Source paths
    doc_martin_tv_path = media_root / "TV Shows" / "Doc Martin (2004)" / "Movies"
    movies_root = media_root / "Movies"

    if not doc_martin_tv_path.exists():
        print(f"⚠️  Doc Martin Movies folder not found: {doc_martin_tv_path}")
        return

    movies_root.mkdir(exist_ok=True)

    # Files to move
    files_to_move = [
        "Doc Martin And The Legend Of The Cloutie Ru 2003.mkv",
        "Doc Martin The Movies 2001.mkv"
    ]

    for filename in files_to_move:
        source_file = doc_martin_tv_path / filename
        if source_file.exists():
            # Create destination with proper naming
            dest_file = movies_root / filename

            print(f"📁 Moving: {source_file} -> {dest_file}")

            # Hash before move
            hash_before = hash_file(source_file)

            # Move file
            safe_move(source_file, dest_file)

            # Hash after move
            hash_after = hash_file(dest_file)

            # Verify integrity
            if hash_before != hash_after:
                raise ValueError(f"Hash mismatch after move: {filename}")

            # Log the move
            audit.log_event("move", {
                "source": str(source_file),
                "destination": str(dest_file),
                "file_hash_before": hash_before,
                "file_hash_after": hash_after,
                "reason": "Moving TV movies from TV show folder to Movies folder"
            }, actor="fix_remaining_issues.py")

            print(f"✅ Moved: {filename}")
        else:
            print(f"⚠️  File not found: {source_file}")

    # Remove empty Movies folder
    try:
        doc_martin_tv_path.rmdir()
        print(f"🗂️  Removed empty Movies folder: {doc_martin_tv_path}")
    except OSError:
        print(f"⚠️  Could not remove Movies folder (not empty): {doc_martin_tv_path}")

def fix_that_70s_show_s06e22(media_root: Path, audit: ImmutableAuditLog):
    """Fix That '70s Show Season 6 Episode 22 filename."""

    show_path = media_root / "TV Shows" / "That '70s Show (1998)" / "Season 06"
    source_file = show_path / "22.mp4"
    dest_file = show_path / "That '70s Show - S06E22 - Sparks.mp4"

    if not source_file.exists():
        print(f"⚠️  Source file not found: {source_file}")
        return

    print(f"📝 Renaming: {source_file.name} -> {dest_file.name}")

    # Hash before rename
    hash_before = hash_file(source_file)

    # Rename file
    safe_move(source_file, dest_file)

    # Hash after rename
    hash_after = hash_file(dest_file)

    # Verify integrity
    if hash_before != hash_after:
        raise ValueError(f"Hash mismatch after rename: {source_file.name}")

    # Log the rename
    audit.log_event("rename", {
        "source": str(source_file),
        "destination": str(dest_file),
        "file_hash_before": hash_before,
        "file_hash_after": hash_after,
        "reason": "Fixing Season 6 Episode 22 filename to match canonical title 'Sparks'"
    }, actor="fix_remaining_issues.py")

    print(f"✅ Renamed: {source_file.name} -> {dest_file.name}")

def fix_that_70s_show_s07e03(media_root: Path, audit: ImmutableAuditLog):
    """Clean parentheses from That '70s Show Season 7 Episode 3 title."""

    show_path = media_root / "TV Shows" / "That '70s Show (1998)" / "Season 07"
    source_file = show_path / "That '70s Show S07E03 (I Can't Get No) Satisfaction.mp4"
    dest_file = show_path / "That '70s Show - S07E03 - I Can't Get No) Satisfaction.mp4"

    if not source_file.exists():
        print(f"⚠️  Source file not found: {source_file}")
        return

    print(f"🧹 Cleaning title: {source_file.name}")
    print(f"   -> {dest_file.name}")

    # Hash before rename
    hash_before = hash_file(source_file)

    # Rename file
    safe_move(source_file, dest_file)

    # Hash after rename
    hash_after = hash_file(dest_file)

    # Verify integrity
    if hash_before != hash_after:
        raise ValueError(f"Hash mismatch after rename: {source_file.name}")

    # Log the rename
    audit.log_event("rename", {
        "source": str(source_file),
        "destination": str(dest_file),
        "file_hash_before": hash_before,
        "file_hash_after": hash_after,
        "reason": "Removing parentheses from episode title to match canonical format"
    }, actor="fix_remaining_issues.py")

    print(f"✅ Cleaned: {source_file.name} -> {dest_file.name}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python fix_remaining_issues.py <media_root>")
        print('Example: python fix_remaining_issues.py "M:\\#MEDIA"')
        sys.exit(1)

    media_root_str = sys.argv[1]
    media_root = Path(media_root_str)

    if not media_root.exists():
        print(f"❌ Media root not found: {media_root}")
        sys.exit(1)

    print("🔧 Final Episode Title Fixes")
    print("=" * 40)
    print(f"📁 Media root: {media_root}")

    # Initialize audit
    audit = ImmutableAuditLog()
    audit.initialize()

    try:
        # Create snapshot before changes
        snapshot_id = SnapshotManager.create_snapshot(
            media_root=str(media_root),
            snapshot_type="pre_final_fixes"
        )

        audit.log_event("snapshot_create", {
            "snapshot_id": snapshot_id,
            "reason": "Pre-operation snapshot for final episode title fixes"
        }, actor="fix_remaining_issues.py")

        print(f"📸 Created snapshot: {snapshot_id}")

        # Fix issues
        print("\n1️⃣ Moving Doc Martin TV movies to Movies folder...")
        move_doc_martin_movies(media_root, audit)

        print("\n2️⃣ Fixing That '70s Show Season 6 Episode 22 filename...")
        fix_that_70s_show_s06e22(media_root, audit)

        print("\n3️⃣ Cleaning parentheses from Season 7 Episode 3 title...")
        fix_that_70s_show_s07e03(media_root, audit)

        print("\n✅ All fixes completed successfully!")
        print("\n🔍 Run analysis again to verify:")
        print(f"   python analyze_episode_titles.py \"{media_root}\"")

    except Exception as e:
        print(f"❌ Error during fixes: {e}")
        print("🔄 Consider restoring from snapshot if needed:")
        print(f"   python rollback_to_snapshot.py \"{snapshot_id}\"")
        raise

if __name__ == "__main__":
    main()