#!/usr/bin/env python3
"""
TV Show Organization Script

Organizes TV show files into proper Jellyfin structure:
TV Shows/{Title}/Season {NN}/{Title} - S{NN}E{NN} - {Episode Title}.{ext}

For test files, uses dummy titles and episode names.
"""

import sys
import re
from pathlib import Path
from typing import Optional
sys.path.insert(0, '_common')

from media_utils import hash_file, safe_move, safe_move_incremental, safe_move_ultimate
from immutable_audit import ImmutableAuditLog
from snapshot_manager import SnapshotManager
from credential_cache import get_cache_status
from tv_episode_cache import TVEpisodeCache

def main(source_dir_path: Optional[str] = None, dry_run: bool = False):
    print("Organizing TV Shows")
    print("=" * 35)

    # Use provided directory or default to test
    if source_dir_path:
        source_dir = Path(source_dir_path).resolve()
        print(f"Using source directory: {source_dir}")
    else:
        source_dir = Path("test_media/tv_shows")
        print(f"Using default test directory: {source_dir}")

    # Initialize systems
    audit = ImmutableAuditLog()
    audit.initialize()

    # Check credential cache status (initializes if needed)
    cache_status = get_cache_status()
    print(f"Credentials: {cache_status['credentials_cached']} cached, session active")

    # Create snapshot before operation
    snapshot_id = SnapshotManager.create_snapshot(
        media_root=str(source_dir),
        snapshot_type="pre_tv_organization"
    )

    audit.log_event("snapshot_create", {
        "snapshot_id": snapshot_id,
        "source_dir": str(source_dir),
        "media_count": len(list(source_dir.glob("*.fake"))) if source_dir.exists() else 0,
        "subtitle_count": 0
    }, actor="organize_tv_shows.py")

    # Source and destination
    if source_dir_path:
        # For real directories, create TV Shows subfolder within the source directory
        dest_dir = source_dir / "TV Shows"
    else:
        # For test, use test_media/TV Shows
        dest_dir = Path("test_media/TV Shows")  # Capital for organized

    if not source_dir.exists():
        print(f"❌ Source directory not found: {source_dir}")
        sys.exit(1)

    dest_dir.mkdir(parents=True, exist_ok=True)

    # Find all TV show files
    # Check if this is test mode (has .fake files) or real media mode
    fake_files = list(source_dir.glob("*.fake"))
    media_files = []
    
    if fake_files:
        # Test mode: use .fake files
        media_files = fake_files
        print(f"🎯 Found {len(media_files)} test TV files to organize")
    else:
        # Real media mode: look for actual media files
        from snapshot_manager import SnapshotManager as SM
        for ext in SM.MEDIA_EXTENSIONS:
            found_files = list(source_dir.glob(f"**/*{ext}"))  # Recursive search
            media_files.extend(found_files)
        
        if media_files:
            print(f"🎯 Found {len(media_files)} media files to organize")
        else:
            print("⚠️  No media files found to organize")
            return

    # Process each TV show file
    processed = 0
    audited = 0
    errors = 0

    for file_path in media_files:
        try:
            if file_path.suffix == '.fake':
                # Test file processing
                show_info = parse_test_tv_filename(file_path.name)
                if not show_info:
                    print(f"⚠️  Skipping unrecognized file: {file_path.name}")
                    continue

                # Create destination structure
                show_dir = dest_dir / show_info['title']
                season_dir = show_dir / f"Season {show_info['season']:02d}"
                season_dir.mkdir(parents=True, exist_ok=True)

                dest_file = season_dir / f"{show_info['title']} - S{show_info['season']:02d}E{show_info['episode']:02d} - {show_info['episode_title']}.fake"
            else:
                # Real media file - check if already organized
                if is_already_organized_tv(file_path, dest_dir):
                    print(f"ℹ️  Already organized file: {file_path.name}")
                    audited += 1
                    continue
                
                # Parse real TV filename (pass Path so parser can use folder context)
                show_info = parse_tv_filename(file_path)
                if not show_info:
                    print(f"⚠️  Skipping unrecognized file: {file_path.name}")
                    continue

                # Handle special episode types
                is_special = show_info.get('special_episode', False)
                is_combined = show_info.get('combined_episode', False)

                # For special episodes, use "Specials" directory instead of season
                if is_special:
                    season_dir_name = "Specials"
                else:
                    season_dir_name = f"Season {show_info['season']:02d}"

                # Verify and correct episode title against canonical data
                # Skip verification for special episodes (season 0) as they may not have canonical data
                if not is_special:
                    episode_cache = TVEpisodeCache()
                    corrected_title = episode_cache.get_corrected_episode_title(
                        show_info['title'],
                        show_info['season'],
                        show_info['episode'],
                        show_info['episode_title']
                    )

                    # Update show_info with corrected title if different
                    if corrected_title != show_info['episode_title']:
                        print(f"🔍 Corrected episode title: '{show_info['episode_title']}' → '{corrected_title}'")
                        show_info['episode_title'] = corrected_title

                # Create destination structure
                show_dir = dest_dir / show_info['title']
                season_dir = show_dir / season_dir_name
                season_dir.mkdir(parents=True, exist_ok=True)

                # Handle filename generation for different episode types
                if is_combined and 'episode_range' in show_info:
                    # Combined episodes: Show - S01E01-E02 - Title
                    episode_part = f"S{show_info['season']:02d}E{show_info['episode_range']}"
                elif is_special:
                    # Special episodes: Show - Special 1 - Title
                    episode_part = f"Special {show_info['episode']}"
                else:
                    # Standard episodes: Show - S01E01 - Title
                    episode_part = f"S{show_info['season']:02d}E{show_info['episode']:02d}"

                dest_file = season_dir / f"{show_info['title']} - {episode_part} - {show_info['episode_title']}{file_path.suffix}"

            # Ultimate optimized move with all performance enhancements
            operation_id = f"tv_org_{processed}_{file_path.name}"
            print(f"📁 Moving: {file_path.name} -> {dest_file.relative_to(dest_dir)}")
            
            if dry_run:
                print(f"   [DRY RUN] Would move to: {dest_file}")
                hash_before = "dry_run"
                hash_after = "dry_run"
            else:
                move_result = safe_move_ultimate(file_path, dest_file, operation_id=operation_id)
                # Extract hash information for logging
                hash_before = move_result['hash_before']
                hash_after = move_result['hash_after']

            # Log the move
            if not dry_run:
                audit.log_event("move", {
                    "source": str(file_path),
                    "destination": str(dest_file),
                    "file_hash_before": hash_before,
                    "file_hash_after": hash_after,
                    "file_size": dest_file.stat().st_size,
                    "snapshot_id": snapshot_id,
                    "optimization": move_result.get('method', 'unknown'),
                    "cached": 'cached' in move_result.get('method', ''),
                    "deferred": move_result.get('deferred', False)
                }, actor="organize_tv_shows.py")
            else:
                print(f"   [DRY RUN] Would log move operation")

            processed += 1

        except Exception as e:
            print(f"❌ Error processing {file_path}: {e}")
            errors += 1
            # Rollback on error
            print(f"🔄 Rolling back to snapshot {snapshot_id}")
            SnapshotManager.restore_snapshot(snapshot_id)
            sys.exit(1)

    # Summary
    print(f"\n✅ TV show organization complete!")
    print(f"   Files moved: {processed}")
    print(f"   Files audited: {audited}")
    print(f"   Errors: {errors}")
    print(f"   Snapshot: {snapshot_id}")
    print(f"   Audit entries added: {processed}")

    # Update journal
    update_journal(processed, audited, snapshot_id)

def is_already_organized_tv(file_path: Path, dest_dir: Path) -> bool:
    """Check if a TV show file is already in the correct Jellyfin structure."""
    # Check if file is already in dest_dir structure
    try:
        relative_path = file_path.relative_to(dest_dir)
        parts = relative_path.parts
        
        # Should be: Show Name/Season NN/Show Name - SNNENN - Title.ext
        if len(parts) == 3:
            show_name, season_dir, filename = parts
            
            # Check season directory format
            if season_dir.startswith("Season "):
                # Check filename format
                if " - S" in filename and "E" in filename and " - " in filename:
                    return True
    except ValueError:
        # File is not under dest_dir
        pass
    
    return False

def correct_show_name(show_name: str) -> str:
    """Correct common spelling errors in TV show names."""
    corrections = {
        # Known typos from audit logs
        "Deepp": "Deep",
        "Readingg": "Reading",
        # Add more corrections as needed
    }
    
    # Apply corrections
    corrected = show_name
    for wrong, right in corrections.items():
        corrected = corrected.replace(wrong, right)
    
    return corrected

def clean_episode_title(episode_title: str) -> str:
    """Clean episode title by removing technical tags and formatting."""
    if not episode_title:
        return episode_title
    
    # Handle both dot-separated and space-separated input
    if '.' in episode_title:
        segments = episode_title.split('.')
    else:
        # For space-separated, we need to be smarter about splitting
        # Split by spaces but keep parenthetical groups together
        segments = re.split(r'\s+', episode_title)
    
    cleaned_segments = []
    
    # Common technical keywords that indicate the start of technical tags
    technical_keywords = {
        '2160p', '1080p', '720p', '480p', '360p',  # resolutions
        '10bit', '8bit',  # bit depth
        'x264', 'x265', 'h264', 'h265', 'HEVC', 'AVC', 'XviD', 'DivX',  # codecs
        'WEB-DL', 'WEB', 'BluRay', 'BD', 'DVD', 'HDTV', 'SDTV', 'PDTV',  # sources
        'DDP', 'DD', 'AC3', 'DTS', 'AAC', 'FLAC', 'MP3',  # audio
        'RARBG', 'Vyndros', 'DSNP', 'NOGRP', 'ABC', 'CBS', 'NBC', 'FOX',  # groups
        'REPACK', 'PROPER', 'INTERNAL', 'LIMITED', 'EXTENDED', 'UNRATED',  # tags
        'REMUX', 'REMASTERED', 'DIRECTORS', 'CUT', 'MULTi', 'DUAL',  # other
        'Silence'  # specific to this release
    }
    
    # Go through segments and stop when we hit technical tags
    for segment in segments:
        segment_clean = segment.strip('()')  # Remove parentheses for checking
        if segment_clean in technical_keywords:
            break
        # Also check if segment contains numbers followed by common patterns
        if re.match(r'^\d+(?:p|bit)$', segment_clean):
            break
        if re.match(r'^(?:DD|DDP|AC3|DTS)\d+', segment_clean):
            break
        if re.match(r'^[A-Z]{2,8}(?:\-[A-Z]{2,8})*$', segment_clean):
            break
            
        cleaned_segments.append(segment)
    
    # Join cleaned segments
    cleaned = ' '.join(cleaned_segments)
    
    # Remove incomplete parentheticals at the end
    cleaned = re.sub(r'\s*\([^)]*$', '', cleaned)
    
    # Final cleanup
    cleaned = re.sub(r'\s+', ' ', cleaned)
    cleaned = cleaned.strip()
    
    return cleaned

def parse_tv_filename(filename_or_path) -> Optional[dict]:
    """Parse real TV show filename or Path into title, season, episode, and episode title.

    Accepts either a filename string or a Path so we can infer the show name from
    parent folders when filenames are just numeric (e.g. "1. On Guard.mkv").
    """
    # Accept both Path objects and plain filenames
    if isinstance(filename_or_path, Path):
        file_path = filename_or_path
        name = file_path.stem
        parent_dir = file_path.parent
    else:
        name = Path(filename_or_path).stem
        file_path = None
        parent_dir = None

    # First try combined episodes pattern: SXXEXXEXX (no separator) or SXXEXX-EXX or SXXEXX EXX
    combined_match = re.search(r'S(\d{1,2})E(\d{1,2})(?:[-\s]?E(\d{1,2}))', name, re.IGNORECASE)
    if combined_match:
        season = int(combined_match.group(1))
        episode_start = int(combined_match.group(2))
        episode_end = int(combined_match.group(3))

        # Extract title (everything before SXXEXX)
        title_part = name[:combined_match.start()].strip()
        # Remove trailing ' -' if present
        if title_part.endswith(' -'):
            title_part = title_part[:-2].strip()

        # Extract episode title (everything after the combined episode pattern)
        episode_title_part = name[combined_match.end():].strip()
        if episode_title_part.startswith('-'):
            episode_title_part = episode_title_part[1:].strip()

        # Clean up title
        title = re.sub(r'[._]', ' ', title_part).strip()
        title = correct_show_name(title)  # Apply spelling corrections

        # Clean up episode title
        episode_title = clean_episode_title(episode_title_part)
        if not episode_title:
            episode_title = f"Episodes {episode_start}-{episode_end}"

        return {
            "title": title,
            "season": season,
            "episode": episode_start,
            "episode_title": episode_title,
            "combined_episode": True,
            "episode_range": f"{episode_start}-{episode_end}"
        }

        # For combined episodes, use the starting episode number
        return {
            "title": title,
            "season": season,
            "episode": episode_start,
            "episode_title": episode_title,
            "combined_episode": True,
            "episode_range": f"{episode_start}-{episode_end}"
        }

    # Try special episodes pattern: S00EXX or Special or Pilot
    special_match = re.search(r'S(0{1,2})E(\d{1,2})', name, re.IGNORECASE)
    if special_match:
        season = 0  # Special season
        episode = int(special_match.group(2))

        # Extract title (everything before S00EXX)
        title_part = name[:special_match.start()].strip()
        # Remove trailing ' -' if present
        if title_part.endswith(' -'):
            title_part = title_part[:-2].strip()

        # Extract episode title (everything after S00EXX)
        episode_title_part = name[special_match.end():].strip()
        if episode_title_part.startswith('-'):
            episode_title_part = episode_title_part[1:].strip()

        # Clean up title
        title = re.sub(r'[._]', ' ', title_part).strip()
        title = correct_show_name(title)  # Apply spelling corrections

        # Clean up episode title
        episode_title = re.sub(r'[._]', ' ', episode_title_part).strip()
        episode_title = clean_episode_title(episode_title)  # Remove technical tags
        if not episode_title:
            episode_title = f"Special {episode}"

        return {
            "title": title,
            "season": season,
            "episode": episode,
            "episode_title": episode_title,
            "special_episode": True
        }

    # Then try standard SXXEXX pattern
    season_match = re.search(r'S(\d{1,2})E(\d{1,2})', name, re.IGNORECASE)
    if season_match:
        season = int(season_match.group(1))
        episode = int(season_match.group(2))

        # Extract title (everything before SXXEXX)
        title_part = name[:season_match.start()].strip()
        # Remove trailing ' -' if present (common in filenames like "Title - S01E01 - Episode")
        if title_part.endswith(' -'):
            title_part = title_part[:-2].strip()

        # Extract episode title (everything after SXXEXX)
        episode_title_part = name[season_match.end():].strip()
        if episode_title_part.startswith('-'):
            episode_title_part = episode_title_part[1:].strip()

        # Clean up title
        title = re.sub(r'[._]', ' ', title_part).strip()
        title = correct_show_name(title)  # Apply spelling corrections

        # Clean up episode title
        episode_title = re.sub(r'[._]', ' ', episode_title_part).strip()
        episode_title = clean_episode_title(episode_title)  # Remove technical tags
        if not episode_title:
            episode_title = f"Episode {episode}"

        return {
            "title": title,
            "season": season,
            "episode": episode,
            "episode_title": episode_title
        }

    # Try alternative pattern: "X. Show Name - Episode Title" or "X Show Name - Episode Title"
    # Pattern: "<num> - Episode Title" or "<num>. Episode Title"
    alt_match = re.match(r'^(\d+)\s*\.?\s*(?:-\s*)?(.*)$', name)
    if alt_match:
        episode = int(alt_match.group(1))
        episode_title = alt_match.group(2).strip()

        title = 'Unknown Show'
        season = None

        # If we have a parent directory that looks like the show folder, infer title and possibly season
        if parent_dir is not None:
            # Look up to two levels for season markers or a series folder
            candidates = [parent_dir, parent_dir.parent] if parent_dir.parent is not None else [parent_dir]
            for cand in candidates:
                if cand is None:
                    continue
                cand_name = cand.name
                # Try to infer season from folder name like 'Season 2' or 'S02' or 'S2'
                m_season = re.search(r'Season\s*[_\-\s]?(\d{1,2})', cand_name, re.IGNORECASE) or re.search(r'\bS(\d{1,2})\b', cand_name, re.IGNORECASE)
                if m_season:
                    try:
                        season = int(m_season.group(1))
                    except Exception:
                        season = None

            # Use the highest-level folder that looks like a series folder for the title (prefer grandparent)
            series_folder = parent_dir.parent.name if parent_dir.parent and parent_dir.parent.name and not re.search(r'Season|S\d', parent_dir.parent.name, re.IGNORECASE) else parent_dir.name
            title_guess = re.sub(r'[._]', ' ', series_folder)
            title_guess = re.sub(r'\s+S\d+.*$', '', title_guess)  # strip season suffixes
            title = correct_show_name(title_guess).strip()
        else:
            # No parent context: attempt to split show and title if the filename contains a dash
            maybe = re.split(r'\s*-\s*', episode_title, maxsplit=1)
            if len(maybe) == 2 and re.search(r'[A-Za-z]', maybe[0]):
                title = re.sub(r'[._]', ' ', maybe[0]).strip()
                episode_title = maybe[1].strip()

        # Clean up episode title
        episode_title = re.sub(r'[._]', ' ', episode_title).strip()
        episode_title = clean_episode_title(episode_title)  # Remove technical tags

        # Default to season 1 unless we inferred something from folders
        if season is None:
            season = 1

        return {
            "title": title,
            "season": season,
            "episode": episode,
            "episode_title": episode_title
        }

    # Special case for Lost: Missing Pieces (mobisodes) — canonical 13 short webisodes
    # Source: Wikipedia "Lost: Missing Pieces" / List of Lost episodes (Specials)
    lost_mobisodes = {
        "the watch": {"season": 0, "episode": 1, "title": "The Watch"},
        "the adventures of hurley and frogurt": {"season": 0, "episode": 2, "title": "The Adventures of Hurley and Frogurt"},
        "king of the castle": {"season": 0, "episode": 3, "title": "King of the Castle"},
        "the deal": {"season": 0, "episode": 4, "title": "The Deal"},
        "operation: sleeper": {"season": 0, "episode": 5, "title": "Operation: Sleeper"},
        "room 23": {"season": 0, "episode": 6, "title": "Room 23"},
        "arzt & crafts": {"season": 0, "episode": 7, "title": "Arzt & Crafts"},
        "buried secrets": {"season": 0, "episode": 8, "title": "Buried Secrets"},
        "tropical depression": {"season": 0, "episode": 9, "title": "Tropical Depression"},
        "jack, meet ethan. ethan? jack.": {"season": 0, "episode": 10, "title": "Jack, Meet Ethan. Ethan? Jack."},
        "jin has a temper-tantrum on the golf course": {"season": 0, "episode": 11, "title": "Jin Has a Temper-Tantrum on the Golf Course"},
        "the envelope": {"season": 0, "episode": 12, "title": "The Envelope"},
        "so it begins": {"season": 0, "episode": 13, "title": "So It Begins"},
    }

    # Check if this is a Lost mobisode (compare cleaned, lowercased name)
    clean_name = clean_episode_title(name).lower()
    if clean_name in lost_mobisodes:
        mobisode_info = lost_mobisodes[clean_name]
        return {
            "title": "Lost (2004)",
            "season": mobisode_info["season"],
            "episode": mobisode_info["episode"],
            "episode_title": mobisode_info["title"],
            "special_episode": True
        }

    return None

def parse_test_tv_filename(filename: str) -> Optional[dict]:
    """Parse test TV show filename into title, season, episode, and episode title."""
    # Pattern: baloney_show_s01e01.fake -> Test Show, Season 1, Episode 1
    match = re.match(r"baloney_show_s(\d+)e(\d+)\.fake", filename)
    if match:
        season = int(match.group(1))
        episode = int(match.group(2))

        # Create dummy episode titles
        episode_titles = {
            (1, 1): "Pilot",
            (1, 2): "The Beginning"
        }

        episode_title = episode_titles.get((season, episode), f"Episode {episode}")

        return {
            "title": "Test Show",
            "season": season,
            "episode": episode,
            "episode_title": episode_title
        }

    return None

def update_journal(processed_count, audited_count, snapshot_id):
    """Update the agent journal with TV show organization completion."""
    journal_path = Path("._state/agent-journal.md")

    if journal_path.exists():
        with open(journal_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Add accomplishment
        accomplishment = f"2025-10-23 - TV shows organized\n- Moved {processed_count} TV episodes\n- Audited {audited_count} already organized files\n- Created proper season structure\n- Snapshot: {snapshot_id}\n- Audit entries: {processed_count}"
        content = content.replace(
            "## Latest Accomplishment\n2025-10-23 - Test movies organized",
            f"## Latest Accomplishment\n{accomplishment}"
        )

        with open(journal_path, 'w', encoding='utf-8') as f:
            f.write(content)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Organize TV shows into Jellyfin structure')
    parser.add_argument('source_path', nargs='?', help='Source directory path')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    
    args = parser.parse_args()
    main(args.source_path, dry_run=args.dry_run)