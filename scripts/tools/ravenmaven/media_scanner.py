#!/usr/bin/env python3
"""
RavenMaven File Scanner - Generate accurate reorganization plans
based on actual files present in the source directory.
"""

import os
import json
import pathlib
from typing import Dict, List, Tuple
import re

class MediaFileScanner:
    def __init__(self, source_dir: str, base_dir: str = "V:\\#MEDIA"):
        self.source_dir = pathlib.Path(source_dir)
        self.base_dir = pathlib.Path(base_dir)
        self.movies_dir = self.base_dir / "Movies"
        self.tv_shows_dir = self.base_dir / "TV Shows"

    def scan_files(self) -> List[Dict]:
        """Scan all files in source directory and categorize them."""
        files = []
        for root, dirs, filenames in os.walk(self.source_dir):
            for filename in filenames:
                filepath = pathlib.Path(root) / filename
                relative_path = filepath.relative_to(self.source_dir)

                file_info = {
                    'full_path': str(filepath),
                    'relative_path': str(relative_path),
                    'filename': filename,
                    'extension': filepath.suffix.lower(),
                    'size': filepath.stat().st_size
                }

                # Categorize the file
                category = self.categorize_file(file_info)
                file_info['category'] = category

                files.append(file_info)

        return files

    def categorize_file(self, file_info: Dict) -> str:
        """Categorize a file as movie, tv_show, subtitle, or other."""
        filename = file_info['filename'].lower()
        extension = file_info['extension']

        # Skip non-media files
        if extension not in ['.mp4', '.mkv', '.avi', '.srt', '.sub', '.txt', '.nfo']:
            return 'other'

        # Check for TV show patterns
        tv_patterns = [
            r's\d{1,2}e\d{1,2}',  # S01E01
            r'season\s*\d+',      # Season 1
            r'episode\s*\d+',     # Episode 1
            r'\b\d{1,2}x\d{1,2}\b'  # 1x01
        ]

        if any(re.search(pattern, filename, re.IGNORECASE) for pattern in tv_patterns):
            if extension in ['.srt', '.sub']:
                return 'tv_subtitle'
            else:
                return 'tv_episode'

        # Check for movie patterns (no season/episode indicators)
        if extension in ['.mp4', '.mkv', '.avi']:
            return 'movie'

        if extension in ['.srt', '.sub']:
            return 'movie_subtitle'

        return 'other'

    def generate_reorganization_plan(self, files: List[Dict]) -> List[Dict]:
        """Generate reorganization operations based on categorized files."""
        operations = []

        for file_info in files:
            if file_info['category'] == 'other':
                continue

            operation = self.create_operation(file_info)
            if operation:
                operations.append(operation)

        return operations

    def create_operation(self, file_info: Dict) -> Dict:
        """Create a single reorganization operation."""
        source_path = file_info['full_path']
        filename = file_info['filename']

        if file_info['category'] in ['movie', 'movie_subtitle']:
            # Extract movie title from filename
            title = self.extract_movie_title(filename)
            if not title:
                return None

            # Create destination path
            dest_dir = self.movies_dir / title
            dest_path = dest_dir / filename

        elif file_info['category'] in ['tv_episode', 'tv_subtitle']:
            # Extract TV show info
            show_info = self.extract_tv_show_info(filename)
            if not show_info:
                return None

            show_title, season, episode = show_info

            # Create destination path
            show_dir = self.tv_shows_dir / show_title
            season_dir = show_dir / f"Season {season:02d}"
            dest_path = season_dir / filename

        else:
            return None

        return {
            'source': source_path,
            'destination': str(dest_path),
            'operation': 'move'
        }

    def extract_movie_title(self, filename: str) -> str:
        """Extract movie title from filename."""
        # Remove extension
        name = pathlib.Path(filename).stem

        # Remove common patterns
        patterns_to_remove = [
            r'\(\d{4}\)',  # (1994)
            r'\[.*?\]',    # [1080p]
            r'\..*?$',     # file extensions in middle
            r'1080p|720p|480p|2160p',
            r'bluray|blu-ray|dvd|web-dl|webrip|hdtv',
            r'x264|x265|h264|h265',
            r'aac|ac3|dts|truehd|atmos',
            r'-rarbg|-ettv|-eztv|-dimension',
            r'\d+\.\d+gb|\d+gb|\d+mb'
        ]

        for pattern in patterns_to_remove:
            name = re.sub(pattern, '', name, flags=re.IGNORECASE)

        # Clean up extra spaces and punctuation
        name = re.sub(r'[._-]+', ' ', name)
        name = re.sub(r'\s+', ' ', name).strip()

        return name.title() if name else None

    def extract_tv_show_info(self, filename: str) -> Tuple[str, int, int]:
        """Extract TV show title, season, and episode from filename."""
        name = pathlib.Path(filename).stem.lower()

        # Look for season/episode patterns
        patterns = [
            r'(.+?)[.\s]+s(\d{1,2})e(\d{1,2})',  # Show.S01E01
            r'(.+?)[.\s]+(\d{1,2})x(\d{1,2})',   # Show.1x01
            r'(.+?)[.\s]+season\s*(\d{1,2}).*?episode\s*(\d{1,2})'  # Show Season 1 Episode 1
        ]

        for pattern in patterns:
            match = re.search(pattern, name, re.IGNORECASE)
            if match:
                show_title = match.group(1).strip()
                season = int(match.group(2))
                episode = int(match.group(3))

                # Clean show title
                show_title = self.clean_show_title(show_title)
                return (show_title, season, episode)

        return None

    def clean_show_title(self, title: str) -> str:
        """Clean TV show title."""
        # Remove common patterns
        patterns_to_remove = [
            r'\(\d{4}.*?\)',  # (2011)
            r'\[.*?\]',       # [1080p]
            r'complete|season|series',
            r'720p|1080p|480p',
            r'hdtv|web-dl|bluray',
            r'x264|x265'
        ]

        for pattern in patterns_to_remove:
            title = re.sub(pattern, '', title, flags=re.IGNORECASE)

        # Clean up
        title = re.sub(r'[._-]+', ' ', title)
        title = re.sub(r'\s+', ' ', title).strip()

        return title.title()

def main():
    scanner = MediaFileScanner(r"E:\MOVIES")

    print("🔍 Scanning media files...")
    files = scanner.scan_files()

    print(f"📊 Found {len(files)} total files")

    # Count by category
    categories = {}
    for file_info in files:
        cat = file_info['category']
        categories[cat] = categories.get(cat, 0) + 1

    print("📈 File categories:")
    for cat, count in categories.items():
        print(f"  {cat}: {count}")

    print("\n🎯 Generating reorganization plan...")
    operations = scanner.generate_reorganization_plan(files)

    print(f"✅ Generated {len(operations)} reorganization operations")

    # Save to JSON file
    output_file = pathlib.Path("V:\\RavenMaven\\actual_file_plan.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump([{
            'success': True,
            'response': '\n'.join([f"OLD: {op['source']}\nNEW: {op['destination']}" for op in operations])
        }], f, indent=2, ensure_ascii=False)

    print(f"💾 Plan saved to: {output_file}")

    # Show sample operations
    print("\n📋 Sample operations:")
    for i, op in enumerate(operations[:5]):
        print(f"  {i+1}. {pathlib.Path(op['source']).name} -> {pathlib.Path(op['destination']).name}")

if __name__ == "__main__":
    main()