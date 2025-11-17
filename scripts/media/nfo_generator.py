#!/usr/bin/env python3
"""
NFO Generator - Create Jellyfin NFO metadata files

Generates .nfo files for media items, particularly useful for:
- Multi-part episodes (episodes split across multiple files)
- Custom metadata that Jellyfin can't auto-detect
- Integration with Jellyfin's metadata system

Supports:
- Movie NFO files
- TV Episode NFO files
- Multi-part episode handling
"""

import logging
from pathlib import Path
from typing import Dict, Optional
from xml.etree import ElementTree as ET
from datetime import datetime


class NFOGenerator:
    """Generate NFO metadata files for Jellyfin."""

    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize NFO generator."""
        self.logger = logger or logging.getLogger(__name__)

    def generate_movie_nfo(
        self,
        title: str,
        year: int,
        tmdb_id: Optional[str] = None,
        imdb_id: Optional[str] = None,
        overview: Optional[str] = None,
        runtime: Optional[int] = None,
        poster_path: Optional[str] = None
    ) -> str:
        """
        Generate NFO content for a movie.

        Args:
            title: Movie title
            year: Release year
            tmdb_id: The Movie Database ID
            imdb_id: IMDb ID
            overview: Plot summary
            runtime: Duration in minutes
            poster_path: Path to poster image

        Returns:
            XML string for NFO file
        """
        root = ET.Element('movie')

        # Basic info
        ET.SubElement(root, 'title').text = title
        ET.SubElement(root, 'year').text = str(year)
        ET.SubElement(root, 'plot').text = overview or ''
        ET.SubElement(root, 'runtime').text = str(runtime or 0)

        # IDs
        if tmdb_id:
            ET.SubElement(root, 'tmdbid').text = str(tmdb_id)
        if imdb_id:
            ET.SubElement(root, 'imdbid').text = imdb_id

        # Poster
        if poster_path:
            ET.SubElement(root, 'poster').text = str(poster_path)

        # Format and return
        xml_str = ET.tostring(root, encoding='unicode')
        return self._format_xml(xml_str)

    def generate_episode_nfo(
        self,
        show_title: str,
        season: int,
        episode: int,
        episode_title: Optional[str] = None,
        tvdb_id: Optional[str] = None,
        tmdb_id: Optional[str] = None,
        air_date: Optional[str] = None,
        overview: Optional[str] = None,
        runtime: Optional[int] = None,
        is_multi_part: bool = False,
        part_number: int = 1
    ) -> str:
        """
        Generate NFO content for a TV episode.

        Args:
            show_title: Name of the TV show
            season: Season number
            episode: Episode number
            episode_title: Episode title
            tvdb_id: TVDB ID
            tmdb_id: TMDB ID
            air_date: Air date (YYYY-MM-DD)
            overview: Episode plot summary
            runtime: Duration in minutes
            is_multi_part: Whether this is a multi-part episode
            part_number: Part number if multi-part (1, 2, etc.)

        Returns:
            XML string for NFO file
        """
        root = ET.Element('episodedetails')

        # Basic info
        title_text = episode_title or (f"Part {part_number}" if is_multi_part else f"Episode {episode}")
        ET.SubElement(root, 'title').text = title_text
        ET.SubElement(root, 'showtitle').text = show_title
        ET.SubElement(root, 'season').text = str(season)
        ET.SubElement(root, 'episode').text = str(episode)
        ET.SubElement(root, 'plot').text = overview or ''
        ET.SubElement(root, 'runtime').text = str(runtime or 45)

        # IDs
        if tvdb_id:
            ET.SubElement(root, 'tvdbid').text = str(tvdb_id)
        if tmdb_id:
            ET.SubElement(root, 'tmdbid').text = str(tmdb_id)

        # Air date
        if air_date:
            ET.SubElement(root, 'aired').text = air_date

        # Multi-part indicator
        if is_multi_part:
            ET.SubElement(root, 'part').text = str(part_number)
            ET.SubElement(root, 'multipart').text = "true"

        # Format and return
        xml_str = ET.tostring(root, encoding='unicode')
        return self._format_xml(xml_str)

    def save_nfo(self, nfo_content: str, output_path: Path) -> bool:
        """
        Save NFO content to file.

        Args:
            nfo_content: XML content string
            output_path: Path to save .nfo file

        Returns:
            True if successful, False otherwise
        """
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(nfo_content)
            self.logger.info(f"Saved NFO file: {output_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save NFO file {output_path}: {e}")
            return False

    @staticmethod
    def _format_xml(xml_str: str) -> str:
        """Pretty-format XML string."""
        try:
            root = ET.fromstring(xml_str)
            return ET.tostring(root, encoding='unicode')
        except Exception:
            # If formatting fails, return original
            return xml_str

    def infer_nfo_path(self, media_file_path: Path, suffix: str = 'nfo') -> Path:
        """
        Infer NFO file path from media file path.

        Examples:
            movie.mkv -> movie.nfo
            episode.mp4 -> episode.nfo

        Args:
            media_file_path: Path to media file
            suffix: File suffix (default: 'nfo')

        Returns:
            Path to NFO file
        """
        return media_file_path.with_suffix(f'.{suffix}')

    def detect_multi_part(self, title: str) -> Dict:
        """
        Detect if a filename suggests multi-part episodes.

        Looks for patterns like:
        - "Show Name S01E01-E02.mkv" -> two parts
        - "Show Name 1x01-02.mkv" -> two parts

        Args:
            title: Filename or title to analyze

        Returns:
            Dict with keys: is_multi_part, part_count, individual_episodes
        """
        result = {
            'is_multi_part': False,
            'part_count': 1,
            'individual_episodes': []
        }

        # Check for episode range patterns
        import re

        # Pattern: S##E##-E##
        pattern1 = r'S(\d+)E(\d+)-E(\d+)'
        match = re.search(pattern1, title, re.IGNORECASE)
        if match:
            season = int(match.group(1))
            start_ep = int(match.group(2))
            end_ep = int(match.group(3))
            result['is_multi_part'] = True
            result['part_count'] = end_ep - start_ep + 1
            result['individual_episodes'] = [
                {'season': season, 'episode': ep}
                for ep in range(start_ep, end_ep + 1)
            ]
            return result

        # Pattern: #x##-##
        pattern2 = r'(\d+)x(\d+)-(\d+)'
        match = re.search(pattern2, title)
        if match:
            season = int(match.group(1))
            start_ep = int(match.group(2))
            end_ep = int(match.group(3))
            result['is_multi_part'] = True
            result['part_count'] = end_ep - start_ep + 1
            result['individual_episodes'] = [
                {'season': season, 'episode': ep}
                for ep in range(start_ep, end_ep + 1)
            ]
            return result

        return result
