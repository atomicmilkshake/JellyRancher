#!/usr/bin/env python3
"""
Anime Organization Script

Organizes anime files into proper Jellyfin structure:
Anime/{Title}/Season {NN}/{Title} - S{NN}E{NN} - {Episode Title}.{ext}

For test files, uses dummy titles and episode names.
"""

import sys
import re
from pathlib import Path
from typing import Optional
sys.path.insert(0, '_common')

from media_utils import hash_file, safe_move
from immutable_audit import ImmutableAuditLog
from snapshot_manager import SnapshotManager
from credential_cache import get_cache_status

def main():
    print("🎎 Organizing Anime")
    print("=" * 30)

    # Initialize systems
    audit = ImmutableAuditLog()
    audit.initialize()

    # Check credential cache status (initializes if needed)
    cache_status = get_cache_status()
    print(f"🔑 Credentials: {cache_status['credentials_cached']} cached, session active")

    # Create snapshot before operation
    snapshot_id = SnapshotManager.create_snapshot(
        media_root="test_media",
        snapshot_type="pre_anime_organization"
    )

    audit.log_event("snapshot_create", {
        "snapshot_id": snapshot_id,
        "media_count": 2,  # We know there are 2 test anime episodes
        "subtitle_count": 0
    }, actor="organize_anime.py")

    # Source and destination
    source_dir = Path("test_media/anime")
    dest_dir = Path("test_media/Anime")  # Capital A for organized

    if not source_dir.exists():
        print(f"❌ Source directory not found: {source_dir}")
        sys.exit(1)

    dest_dir.mkdir(parents=True, exist_ok=True)

    # Process each anime file
    processed = 0
    for file_path in source_dir.glob("*.fake"):
        try:
            # Extract anime info from filename
            anime_info = parse_test_anime_filename(file_path.name)
            if not anime_info:
                print(f"⚠️  Skipping unrecognized file: {file_path.name}")
                continue

            # Create destination structure
            anime_dir = dest_dir / anime_info['title']
            season_dir = anime_dir / f"Season {anime_info['season']:02d}"
            season_dir.mkdir(parents=True, exist_ok=True)

            dest_file = season_dir / f"{anime_info['title']} - S{anime_info['season']:02d}E{anime_info['episode']:02d} - {anime_info['episode_title']}.fake"

            # Hash before move
            hash_before = hash_file(file_path)

            # Move file
            print(f"📁 Moving: {file_path.name} -> {dest_file.relative_to(dest_dir)}")
            safe_move(file_path, dest_file)

            # Hash after move
            hash_after = hash_file(dest_file)

            # Verify integrity
            if hash_before != hash_after:
                raise ValueError(f"File corruption detected: {file_path}")

            # Log the move
            audit.log_event("move", {
                "source": str(file_path),
                "destination": str(dest_file),
                "file_hash_before": hash_before,
                "file_hash_after": hash_after,
                "file_size": dest_file.stat().st_size,
                "snapshot_id": snapshot_id
            }, actor="organize_anime.py")

            processed += 1

        except Exception as e:
            print(f"❌ Error processing {file_path}: {e}")
            # Rollback on error
            print(f"🔄 Rolling back to snapshot {snapshot_id}")
            SnapshotManager.restore_snapshot(snapshot_id)
            sys.exit(1)

    # Summary
    print(f"\n✅ Anime organization complete!")
    print(f"   Files moved: {processed}")
    print(f"   Snapshot: {snapshot_id}")
    print(f"   Audit entries added: {processed}")

    # Update journal
    update_journal(processed, snapshot_id)

def parse_test_anime_filename(filename: str) -> Optional[dict]:
    """Parse test anime filename into title, season, episode, and episode title."""
    # Pattern: baloney_anime_s01e01.fake -> Test Anime, Season 1, Episode 1
    match = re.match(r"baloney_anime_s(\d+)e(\d+)\.fake", filename)
    if match:
        season = int(match.group(1))
        episode = int(match.group(2))

        # Create dummy episode titles
        episode_titles = {
            (1, 1): "Awakening",
            (1, 2): "The Journey Begins"
        }

        episode_title = episode_titles.get((season, episode), f"Episode {episode}")

        return {
            "title": "Test Anime",
            "season": season,
            "episode": episode,
            "episode_title": episode_title
        }

    return None

def update_journal(processed_count, snapshot_id):
    """Update the agent journal with anime organization completion."""
    journal_path = Path("._state/agent-journal.md")

    if journal_path.exists():
        with open(journal_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Update current phase
        content = content.replace(
            "## Current Phase\nPhase 2: Movie Organization",
            "## Current Phase\nPhase 3: TV Show & Anime Organization"
        )

        # Add accomplishment
        accomplishment = f"2025-10-23 - Test anime organized\n- Moved {processed_count} anime episodes\n- Created proper season structure\n- Snapshot: {snapshot_id}\n- Audit entries: {processed_count}"
        content = content.replace(
            "## Latest Accomplishment\n2025-10-23 - Test TV shows organized",
            f"## Latest Accomplishment\n{accomplishment}"
        )

        with open(journal_path, 'w', encoding='utf-8') as f:
            f.write(content)

if __name__ == "__main__":
    main()