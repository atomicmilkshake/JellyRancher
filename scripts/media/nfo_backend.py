#!/usr/bin/env python3
"""
NFO Generation Backend - Creates Jellyfin-compatible NFO files for multi-part episodes

Provides high-level NFO file generation that the PyQt5 UI can call.
Handles multi-part episodes (E01-E02, S01E01-E02) with proper Jellyfin metadata.

Features:
- Multi-part episode detection from filenames
- TMDB metadata integration for episode details
- Automatic NFO file creation alongside video files
- Audit trail integration
- Error handling and rollback

Usage (from UI):
    from nfo_backend import NFOBackend

    backend = NFOBackend()

    # Generate NFO for multi-part episode
    result = backend.generate_nfo_for_multipart(
        video_path="path/to/Star.Trek.TNG.S01E01-E02.mkv",
        progress_callback=callback
    )
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any, Tuple
from datetime import datetime
from enum import Enum
import re
import json

# Add common modules to path
sys.path.insert(0, str(Path(__file__).parent / "_common"))

from immutable_audit import ImmutableAuditLog
from logger import ProjectLogger

# Optional TMDB integration
try:
    from tmdbv3api import TMDb, TV
    _HAS_TMDB = True
except ImportError:
    _HAS_TMDB = False


class MultipartPattern(Enum):
    """Common multi-part episode filename patterns."""
    S01E01_E02 = r"S(\d{1,2})E(\d{1,2})-E(\d{1,2})"  # S01E01-E02
    S01E01_02 = r"S(\d{1,2})E(\d{1,2})-(\d{1,2})"    # S01E01-02
    E01_E02 = r"E(\d{1,2})-E(\d{1,2})"                # E01-E02 (no season)
    E01_02 = r"E(\d{1,2})-(\d{1,2})"                  # E01-02 (no season)


class NFOBackend:
    """High-level NFO file generation interface for UI."""

    def __init__(self, tmdb_api_key: Optional[str] = None):
        self.audit = ImmutableAuditLog()
        self.audit.initialize()
        self.logger = ProjectLogger("nfo_backend")

        # TMDB setup
        self.tmdb = None
        self.tv = None
        if _HAS_TMDB and tmdb_api_key:
            self.tmdb = TMDb()
            self.tmdb.api_key = tmdb_api_key
            self.tv = TV()

    def generate_nfo_for_multipart(
        self,
        video_path: str,
        show_title: Optional[str] = None,
        season: Optional[int] = None,
        progress_callback: Optional[Callable[[str, int], None]] = None
    ) -> Dict[str, Any]:
        """
        Generate NFO file for a multi-part episode.

        Args:
            video_path: Path to the multi-part video file
            show_title: Override show title (auto-detected if None)
            season: Override season number (auto-detected if None)
            progress_callback: Optional callback(message, percent)

        Returns:
            Dict with generation status and details
        """
        try:
            video_file = Path(video_path)
            if not video_file.exists():
                return {
                    "success": False,
                    "error": f"Video file not found: {video_path}",
                    "nfo_created": False
                }

            if progress_callback:
                progress_callback("Analyzing multi-part episode...", 10)

            # Detect multi-part pattern
            pattern_info = self._detect_multipart_pattern(str(video_file.name))
            if not pattern_info:
                return {
                    "success": False,
                    "error": f"No multi-part pattern detected in filename: {video_file.name}",
                    "nfo_created": False
                }

            if progress_callback:
                progress_callback(f"Detected {pattern_info['episode_count']} part episode", 30)

            # Extract show information
            show_info = self._extract_show_info(str(video_file.name), show_title, season)
            if not show_info:
                return {
                    "success": False,
                    "error": "Could not extract show information from filename",
                    "nfo_created": False
                }

            if progress_callback:
                progress_callback(f"Show: {show_info['title']} Season {show_info['season']}", 50)

            # Get episode metadata from TMDB if available
            episode_data = []
            if self.tv and show_info.get('tmdb_id'):
                episode_data = self._get_episode_metadata_tmdb(
                    show_info['tmdb_id'],
                    show_info['season'],
                    pattern_info['episodes']
                )
            else:
                # Fallback to basic metadata
                episode_data = self._create_basic_episode_data(
                    show_info['season'],
                    pattern_info['episodes']
                )

            if progress_callback:
                progress_callback("Generating NFO content...", 70)

            # Generate NFO content
            nfo_content = self._generate_nfo_content(show_info, episode_data)

            # Create NFO file
            nfo_path = video_file.with_suffix('.nfo')
            nfo_path.write_text(nfo_content, encoding='utf-8')

            if progress_callback:
                progress_callback("NFO file created successfully", 100)

            result = {
                "success": True,
                "nfo_path": str(nfo_path),
                "nfo_created": True,
                "show_title": show_info['title'],
                "season": show_info['season'],
                "episodes": pattern_info['episodes'],
                "episode_count": pattern_info['episode_count']
            }

            # Log NFO creation
            self.audit.log_event("nfo_generated", {
                "video_path": str(video_path),
                "nfo_path": str(nfo_path),
                "show_title": show_info['title'],
                "season": show_info['season'],
                "episodes": pattern_info['episodes']
            }, actor="nfo_backend.py")

            return result

        except Exception as e:
            error_msg = f"NFO generation failed: {str(e)}"
            self.logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "nfo_created": False
            }

    def scan_and_generate_nfos(
        self,
        folder_path: str,
        progress_callback: Optional[Callable[[str, int], None]] = None
    ) -> Dict[str, Any]:
        """
        Scan folder for multi-part episodes and generate NFO files.

        Args:
            folder_path: Path to scan for multi-part episodes
            progress_callback: Optional callback(message, percent)

        Returns:
            Dict with scan and generation results
        """
        try:
            folder = Path(folder_path)
            if not folder.exists():
                return {
                    "success": False,
                    "error": f"Folder not found: {folder_path}",
                    "scanned_files": 0,
                    "nfo_created": 0
                }

            if progress_callback:
                progress_callback("Scanning for multi-part episodes...", 10)

            # Find video files
            video_extensions = {'.mkv', '.mp4', '.avi', '.m4v', '.mov', '.wmv', '.flv'}
            video_files = []
            for ext in video_extensions:
                video_files.extend(folder.rglob(f"*{ext}"))

            if progress_callback:
                progress_callback(f"Found {len(video_files)} video files", 20)

            # Filter to multi-part episodes
            multipart_files = []
            for video_file in video_files:
                if self._detect_multipart_pattern(str(video_file.name)):
                    multipart_files.append(video_file)

            if progress_callback:
                progress_callback(f"Found {len(multipart_files)} multi-part episodes", 30)

            # Generate NFOs
            created_nfos = 0
            errors = []

            for i, video_file in enumerate(multipart_files):
                if progress_callback:
                    percent = 30 + int((i / max(len(multipart_files), 1)) * 70)
                    progress_callback(f"Processing {video_file.name}...", percent)

                result = self.generate_nfo_for_multipart(str(video_file))
                if result["success"]:
                    created_nfos += 1
                else:
                    errors.append(f"{video_file.name}: {result.get('error', 'Unknown error')}")

            if progress_callback:
                progress_callback("Scan and generation complete", 100)

            result = {
                "success": True,
                "scanned_files": len(video_files),
                "multipart_found": len(multipart_files),
                "nfo_created": created_nfos,
                "errors": errors
            }

            # Log scan results
            self.audit.log_event("nfo_scan_complete", result, actor="nfo_backend.py")

            return result

        except Exception as e:
            error_msg = f"Scan and generate failed: {str(e)}"
            self.logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "scanned_files": 0,
                "nfo_created": 0
            }

    def _detect_multipart_pattern(self, filename: str) -> Optional[Dict[str, Any]]:
        """Detect multi-part episode pattern in filename."""
        for pattern in MultipartPattern:
            match = re.search(pattern.value, filename, re.IGNORECASE)
            if match:
                groups = match.groups()
                if len(groups) >= 3:  # Season, start_episode, end_episode
                    season = int(groups[0]) if len(groups) > 2 else 1
                    start_ep = int(groups[-2])
                    end_ep = int(groups[-1])
                    episodes = list(range(start_ep, end_ep + 1))

                    return {
                        "pattern": pattern.name,
                        "season": season,
                        "episodes": episodes,
                        "episode_count": len(episodes),
                        "start_episode": start_ep,
                        "end_episode": end_ep
                    }
                elif len(groups) == 2:  # Just start and end episode
                    start_ep = int(groups[0])
                    end_ep = int(groups[1])
                    episodes = list(range(start_ep, end_ep + 1))

                    return {
                        "pattern": pattern.name,
                        "season": 1,  # Default season
                        "episodes": episodes,
                        "episode_count": len(episodes),
                        "start_episode": start_ep,
                        "end_episode": end_ep
                    }

        return None

    def _extract_show_info(
        self,
        filename: str,
        override_title: Optional[str] = None,
        override_season: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """Extract show information from filename."""
        if override_title:
            show_title = override_title
        else:
            # Extract show title from filename
            # Remove extension first
            name = Path(filename).stem

            # Find the season/episode pattern and extract everything before it
            # Look for patterns like S01E01-E02, S01E01-02, etc.
            season_ep_pattern = re.search(r'(S\d+E\d+-\w+)', name, re.IGNORECASE)
            if season_ep_pattern:
                # Extract show name as everything before the season/episode pattern
                show_part = name[:season_ep_pattern.start()].strip()
            else:
                # Fallback: look for E01-E02 pattern without season
                ep_pattern = re.search(r'(E\d+-\w+)', name, re.IGNORECASE)
                if ep_pattern:
                    show_part = name[:ep_pattern.start()].strip()
                else:
                    # No pattern found, use whole name
                    show_part = name

            # Clean up the show name
            # Replace dots, underscores, dashes with spaces
            show_title = re.sub(r'[._-]+', ' ', show_part)

            # Remove year patterns (4 digits that look like years)
            show_title = re.sub(r'\b(19|20)\d{2}\b', '', show_title)

            # Clean up extra whitespace
            show_title = ' '.join(show_title.split())

            if not show_title:
                return None

        season = override_season
        if season is None:
            # Try to extract season from filename
            season_match = re.search(r'S(\d{1,2})', filename, re.IGNORECASE)
            season = int(season_match.group(1)) if season_match else 1

        return {
            "title": show_title,
            "season": season,
            "tmdb_id": None  # Would need TMDB search to populate
        }

    def _get_episode_metadata_tmdb(
        self,
        tmdb_id: int,
        season: int,
        episodes: List[int]
    ) -> List[Dict[str, Any]]:
        """Get episode metadata from TMDB."""
        episode_data = []

        try:
            season_details = self.tv.season_details(tmdb_id, season)

            for ep_num in episodes:
                episode_info = None
                for ep in season_details.episodes:
                    if ep.episode_number == ep_num:
                        episode_info = ep
                        break

                if episode_info:
                    episode_data.append({
                        "episode_number": ep_num,
                        "title": episode_info.name,
                        "plot": episode_info.overview or "",
                        "aired": episode_info.air_date or "",
                        "tmdb_id": episode_info.id
                    })
                else:
                    # Fallback for missing episode
                    episode_data.append({
                        "episode_number": ep_num,
                        "title": f"Episode {ep_num}",
                        "plot": "",
                        "aired": "",
                        "tmdb_id": None
                    })

        except Exception as e:
            self.logger.error(f"TMDB metadata fetch failed: {str(e)}")
            # Fallback to basic data
            episode_data = self._create_basic_episode_data(season, episodes)

        return episode_data

    def _create_basic_episode_data(self, season: int, episodes: List[int]) -> List[Dict[str, Any]]:
        """Create basic episode data when TMDB is unavailable."""
        return [
            {
                "episode_number": ep_num,
                "title": f"Episode {ep_num}",
                "plot": "",
                "aired": "",
                "tmdb_id": None
            }
            for ep_num in episodes
        ]

    def _generate_nfo_content(self, show_info: Dict[str, Any], episode_data: List[Dict[str, Any]]) -> str:
        """Generate NFO XML content for multi-part episode."""
        # Create XML structure for each episode
        episode_xmls = []

        for ep_data in episode_data:
            episode_xml = f'''<episodedetails>
    <title>{ep_data["title"]}</title>
    <showtitle>{show_info["title"]}</showtitle>
    <season>{show_info["season"]}</season>
    <episode>{ep_data["episode_number"]}</episode>'''

            if ep_data.get("plot"):
                episode_xml += f'''
    <plot>{ep_data["plot"]}</plot>'''

            if ep_data.get("aired"):
                episode_xml += f'''
    <aired>{ep_data["aired"]}</aired>'''

            if ep_data.get("tmdb_id"):
                episode_xml += f'''
    <uniqueid type="tmdb" default="true">{ep_data["tmdb_id"]}</uniqueid>'''

            episode_xml += '''
</episodedetails>'''

            episode_xmls.append(episode_xml)

        # Combine all episodes into single NFO
        nfo_content = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
{chr(10).join(episode_xmls)}
'''

        return nfo_content