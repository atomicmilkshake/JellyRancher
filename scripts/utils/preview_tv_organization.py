import os
import sys
import json
from pathlib import Path
sys.path.insert(0, '_common')

from tv_episode_cache import TVEpisodeCache

def clean_show_title_from_folder(folder_name: str) -> str:
    """Extract clean show title from season folder name."""
    import re
    
    # Patterns for season folders
    # Examples: "Lost (2004) Season 1 S01 + Extras..."
    #           "That.70s.Show.S01-S08.COMPLETE.SERIES..."
    #           "The Mandalorian (2019) Season 3 S03 + Extras..."
    
    # Try to match "Show Name (Year)" pattern
    year_match = re.search(r'^(.+?)\s*\((\d{4})\)', folder_name)
    if year_match:
        title = year_match.group(1).strip()
        year = year_match.group(2)
        # Clean title: replace dots/underscores with spaces
        title = re.sub(r'[._]', ' ', title)
        return f"{title} ({year})"
    
    # Fallback: extract before "Season" or "S01"
    season_match = re.search(r'^(.+?)\s*(?:Season|S\d+)', folder_name, re.IGNORECASE)
    if season_match:
        title = season_match.group(1).strip()
        # Clean title
        title = re.sub(r'[._]', ' ', title)
        return title
    
    # Last resort: use whole name cleaned
    title = re.sub(r'[._]', ' ', folder_name)
    return title

def parse_tv_filename(filename: str) -> dict:
    """Parse TV filename into components (simplified version)."""
    import re
    from pathlib import Path
    
    # Remove extension
    name = Path(filename).stem
    
    # Find SXXEXX pattern
    season_match = re.search(r'S(\d{1,2})E(\d{1,2})', name, re.IGNORECASE)
    if not season_match:
        return None
    
    season = int(season_match.group(1))
    episode = int(season_match.group(2))
    
    # Extract title (everything before SXXEXX)
    title_part = name[:season_match.start()].strip()
    # Remove trailing ' -' if present
    if title_part.endswith(' -'):
        title_part = title_part[:-2].strip()
    
    # Clean title
    title = re.sub(r'[._]', ' ', title_part).strip()
    
    # Extract episode title (everything after SXXEXX)
    episode_title_part = name[season_match.end():].strip()
    if episode_title_part.startswith('-'):
        episode_title_part = episode_title_part[1:].strip()
    
    # Clean episode title (simplified)
    episode_title = re.sub(r'[._]', ' ', episode_title_part).strip()
    # Remove technical tags (basic)
    technical_keywords = {'1080p', '720p', 'BluRay', 'x265', 'x264', 'AAC', 'Silence'}
    words = episode_title.split()
    cleaned_words = []
    for word in words:
        if word not in technical_keywords:
            cleaned_words.append(word)
        else:
            break
    episode_title = ' '.join(cleaned_words).strip()
    
    return {
        'show_name': title,
        'season': season,
        'episode': episode,
        'title': episode_title
    }

def preview_tv_organization(root_path: str):
    """
    Preview proposed TV show organization changes without actually moving files.
    
    Args:
        root_path: Root directory to scan (e.g., "W:\\#MEDIA")
    """
    root = Path(root_path)
    
    if not root.exists():
        print(f"❌ Directory does not exist: {root_path}")
        return
    
    print(f"📁 Previewing TV organization for: {root_path}")
    print("🔍 Scanning for media files and generating proposed changes...\n")
    
    # Initialize episode cache
    cache = TVEpisodeCache()
    
    changes = []
    total_files = 0
    
    for dirpath, dirnames, filenames in os.walk(root):
        for filename in filenames:
            # Skip non-media files
            if not any(filename.lower().endswith(ext) for ext in ['.mkv', '.mp4', '.avi']):
                continue
            
            filepath = Path(dirpath) / filename
            total_files += 1
            
            # Parse filename
            parsed = parse_tv_filename(filename)
            if not parsed:
                print(f"⚠️  Could not parse: {filename}")
                continue
            
            show_name = parsed['show_name']
            season = parsed['season']
            episode = parsed['episode']
            current_title = parsed['title']
            
            # Get canonical title if available
            try:
                canonical_title = cache.get_corrected_episode_title(show_name, season, episode, current_title)
                if canonical_title and canonical_title != current_title:
                    proposed_title = canonical_title
                    title_note = f" (corrected from '{current_title}')"
                else:
                    proposed_title = current_title
                    title_note = ""
            except:
                proposed_title = current_title
                title_note = " (cache unavailable)"
            
            # Generate proposed path
            show_folder = f"{show_name}"
            season_folder = f"Season {season:02d}"
            new_filename = f"{show_name} - S{season:02d}E{episode:02d} - {proposed_title}{Path(filename).suffix}"
            proposed_path = Path(root) / "TV Shows" / show_folder / season_folder / new_filename
            
            # Record change
            changes.append({
                'current_path': str(filepath.relative_to(root)),
                'proposed_path': str(proposed_path.relative_to(root)),
                'title_note': title_note,
                'parsed_info': parsed
            })
    
    # Display changes
    print(f"📋 PROPOSED CHANGES ({len(changes)} files out of {total_files} total media files):\n")
    
    for change in changes[:20]:  # Limit to first 20 for readability
        print(f"📁 Current: {change['current_path']}")
        print(f"➡️  Proposed: {change['proposed_path']}{change['title_note']}")
        print()
    
    if len(changes) > 20:
        print(f"... and {len(changes) - 20} more changes (showing first 20)")
    
    print(f"\n📊 Summary:")
    print(f"  - Total media files scanned: {total_files}")
    print(f"  - Files with proposed changes: {len(changes)}")
    print(f"  - Files unchanged: {total_files - len(changes)}")
    
    # Save full list to file for review
    output_file = Path(root) / "tv_organization_preview.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(changes, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Full preview saved to: {output_file}")
    print("\n🔍 Review the changes above. If any look wrong, let me know what to fix before proceeding.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python preview_tv_organization.py <root_path>")
        print("Example: python preview_tv_organization.py \"W:\\#MEDIA\"")
        sys.exit(1)
    
    root_path = sys.argv[1]
    preview_tv_organization(root_path)