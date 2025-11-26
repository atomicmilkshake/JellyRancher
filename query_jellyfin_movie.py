#!/usr/bin/env python3
"""
Query Jellyfin Library - Find movies and display detailed information

Usage:
    python query_jellyfin_movie.py "search term"
    python query_jellyfin_movie.py "barbie mermaid"
"""

import sys
import argparse
import json
from pathlib import Path
from typing import List, Dict, Optional

sys.path.insert(0, str(Path(__file__).parent))

from scripts.core.jellyfin_client import JellyfinClient
from scripts.core.jellyfin_config import JellyfinConfigManager


def format_movie_info(movie: Dict) -> str:
    """Format movie information for display."""
    lines = []
    lines.append(f"Title: {movie.get('Name', 'N/A')}")
    lines.append(f"Path: {movie.get('Path', 'N/A')}")
    lines.append(f"Jellyfin ID: {movie.get('Id', 'N/A')}")
    
    # Provider IDs
    provider_ids = movie.get('ProviderIds', {})
    if provider_ids:
        lines.append("Provider IDs:")
        for provider, pid in provider_ids.items():
            lines.append(f"  - {provider}: {pid}")
    
    # Media sources and streams
    media_sources = movie.get('MediaSources', [])
    if media_sources:
        for idx, source in enumerate(media_sources):
            lines.append(f"\nMedia Source {idx + 1}:")
            lines.append(f"  Container: {source.get('Container', 'N/A')}")
            lines.append(f"  Size: {source.get('Size', 0) / (1024**3):.2f} GB" if source.get('Size') else "  Size: N/A")
            
            if 'MediaStreams' in source:
                streams = source['MediaStreams']
                video_streams = [s for s in streams if s.get('Type') == 'Video']
                audio_streams = [s for s in streams if s.get('Type') == 'Audio']
                subtitle_streams = [s for s in streams if s.get('Type') == 'Subtitle']
                
                if video_streams:
                    lines.append(f"  Video Streams ({len(video_streams)}):")
                    for vs in video_streams:
                        codec = vs.get('Codec', 'N/A')
                        width = vs.get('Width', '?')
                        height = vs.get('Height', '?')
                        bitrate = vs.get('BitRate', 0)
                        bitrate_mbps = bitrate / 1_000_000 if bitrate else 0
                        lines.append(f"    - {codec} {width}x{height} @ {bitrate_mbps:.1f} Mbps")
                
                if audio_streams:
                    lines.append(f"  Audio Streams ({len(audio_streams)}):")
                    for as_stream in audio_streams:
                        codec = as_stream.get('Codec', 'N/A')
                        channels = as_stream.get('Channels', '?')
                        language = as_stream.get('Language', 'N/A')
                        bitrate = as_stream.get('BitRate', 0)
                        bitrate_kbps = bitrate / 1000 if bitrate else 0
                        lines.append(f"    - {codec} {channels}ch {language} @ {bitrate_kbps:.0f} kbps")
                
                if subtitle_streams:
                    lines.append(f"  Subtitle Streams ({len(subtitle_streams)}):")
                    for sub in subtitle_streams:
                        codec = sub.get('Codec', 'N/A')
                        language = sub.get('Language', 'N/A')
                        is_forced = sub.get('IsForced', False)
                        forced_str = " (forced)" if is_forced else ""
                        lines.append(f"    - {codec} {language}{forced_str}")
    
    return "\n".join(lines)


def search_movies(client: JellyfinClient, search_term: str) -> List[Dict]:
    """
    Search for movies in Jellyfin library.
    
    Args:
        client: JellyfinClient instance
        search_term: Search term (case-insensitive partial match)
    
    Returns:
        List of matching movie dictionaries
    """
    print(f"Searching Jellyfin library for: '{search_term}'...")
    
    items = client.get_all_items(
        item_types=['Movie'],
        fields=['Name', 'Path', 'MediaSources', 'Id', 'ProviderIds', 'ProductionYear']
    )
    
    search_lower = search_term.lower()
    matches = [
        item for item in items
        if search_lower in item.get('Name', '').lower()
    ]
    
    return matches


def main():
    parser = argparse.ArgumentParser(
        description='Query Jellyfin library for movies',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python query_jellyfin_movie.py "barbie mermaid"
  python query_jellyfin_movie.py "star wars"
  python query_jellyfin_movie.py "matrix" --json
        """
    )
    parser.add_argument(
        'search_term',
        help='Search term to find movies (case-insensitive)'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output full JSON instead of formatted text'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Show all matches (default: show first match only)'
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
    
    print("Connected successfully\n")
    
    # Search for movies
    matches = search_movies(client, args.search_term)
    
    if not matches:
        print(f"No movies found matching '{args.search_term}'")
        sys.exit(1)
    
    print(f"Found {len(matches)} matching movie(s)\n")
    
    # Display results
    if args.json:
        # Output full JSON
        if args.all:
            print(json.dumps(matches, indent=2, default=str))
        else:
            print(json.dumps(matches[0], indent=2, default=str))
    else:
        # Formatted output
        display_count = len(matches) if args.all else 1
        for i, movie in enumerate(matches[:display_count]):
            if len(matches) > 1:
                print(f"\n{'='*60}")
                print(f"Match {i + 1} of {len(matches)}")
                print(f"{'='*60}")
            print(format_movie_info(movie))
            print()
        
        if len(matches) > 1 and not args.all:
            print(f"(Showing first match only. Use --all to see all {len(matches)} matches)")


if __name__ == "__main__":
    main()

