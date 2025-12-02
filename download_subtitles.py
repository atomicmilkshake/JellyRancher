#!/usr/bin/env python3
"""
Download subtitles for Barbie in A Mermaid Tale (2010)
"""

from scripts.media.subtitle_downloader import SubtitleDownloader
import os

def main():
    # Initialize downloader
    downloader = SubtitleDownloader()

    # Movie file path
    movie_path = r'L:\#MEDIA\Movies\Barbie in A Mermaid Tale (2010)\Barbie in A Mermaid Tale (2010) - SD HEVC HandBrake.mkv'

    # Download English subtitles
    print(f'Downloading English subtitles for: {os.path.basename(movie_path)}')
    stats = downloader.download_subtitles([movie_path], language='English', dry_run=False)

    print('Download statistics:')
    print(f'  Total: {stats.get("total", 0)}')
    print(f'  Success: {stats.get("success", 0)}')
    print(f'  Failed: {stats.get("failed", 0)}')

    print('Individual results:')
    for result in downloader.results:
        status = result.status.value if hasattr(result.status, 'value') else str(result.status)
        subtitle = result.subtitle_path or 'None'
        provider = result.provider or 'None'
        error = result.error or 'None'
        print(f'  Status: {status}')
        print(f'    File: {result.file_path}')
        print(f'    Subtitle: {subtitle}')
        print(f'    Provider: {provider}')
        print(f'    Error: {error}')
        print()

if __name__ == '__main__':
    main()