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
        try:
            self.logger = logger or logging.getLogger(__name__)
            if not self.logger:
                raise ValueError("Logger cannot be None")
            
            self.logger.debug("NFOGenerator initialized successfully")
            
        except ValueError as e:
            if logger:
                logger.error(f"Failed to initialize NFOGenerator: {e}")
            else:
                print(f"Failed to initialize NFOGenerator: {e}")
            raise
        except Exception as e:
            if self.logger:
                self.logger.error(f"Unexpected error initializing NFOGenerator: {e}", exc_info=True)
            else:
                print(f"Unexpected error initializing NFOGenerator: {e}")
            raise

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
        try:
            if not title or not title.strip():
                raise ValueError("Movie title cannot be empty")
            if not isinstance(year, int) or year < 1900 or year > 2100:
                raise ValueError(f"Invalid year: {year}")
            
            root = ET.Element('movie')

            # Basic info
            ET.SubElement(root, 'title').text = title.strip()
            ET.SubElement(root, 'year').text = str(year)
            ET.SubElement(root, 'plot').text = overview or ''
            ET.SubElement(root, 'runtime').text = str(runtime or 0)

            # IDs
            if tmdb_id:
                if not isinstance(tmdb_id, str) or not tmdb_id.strip():
                    self.logger.warning(f"Invalid TMDB ID: {tmdb_id}")
                else:
                    ET.SubElement(root, 'tmdbid').text = str(tmdb_id).strip()
            if imdb_id:
                if not isinstance(imdb_id, str) or not imdb_id.strip():
                    self.logger.warning(f"Invalid IMDb ID: {imdb_id}")
                else:
                    ET.SubElement(root, 'imdbid').text = imdb_id.strip()

            # Poster
            if poster_path:
                try:
                    poster_path_obj = Path(poster_path)
                    if poster_path_obj.exists():
                        ET.SubElement(root, 'poster').text = str(poster_path_obj)
                    else:
                        self.logger.warning(f"Poster path does not exist: {poster_path}")
                except Exception as e:
                    self.logger.warning(f"Error processing poster path {poster_path}: {e}")

            # Format and return
            try:
                xml_str = ET.tostring(root, encoding='unicode')
                formatted_xml = self._format_xml(xml_str)
                self.logger.debug(f"Generated NFO for movie: {title}")
                return formatted_xml
            except Exception as e:
                self.logger.error(f"Failed to format XML for movie '{title}': {e}", exc_info=True)
                raise
                
        except ValueError as e:
            self.logger.error(f"Invalid parameters for movie NFO generation: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error generating movie NFO for '{title}': {e}", exc_info=True)
            raise

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
        try:
            if not show_title or not show_title.strip():
                raise ValueError("Show title cannot be empty")
            if not isinstance(season, int) or season < 0:
                raise ValueError(f"Invalid season number: {season}")
            if not isinstance(episode, int) or episode < 0:
                raise ValueError(f"Invalid episode number: {episode}")
            if is_multi_part and (not isinstance(part_number, int) or part_number < 1):
                raise ValueError(f"Invalid part number: {part_number}")
            
            root = ET.Element('episodedetails')

            # Basic info
            title_text = episode_title or (f"Part {part_number}" if is_multi_part else f"Episode {episode}")
            ET.SubElement(root, 'title').text = title_text
            ET.SubElement(root, 'showtitle').text = show_title.strip()
            ET.SubElement(root, 'season').text = str(season)
            ET.SubElement(root, 'episode').text = str(episode)
            ET.SubElement(root, 'plot').text = overview or ''
            ET.SubElement(root, 'runtime').text = str(runtime or 45)

            # IDs
            if tvdb_id:
                if not isinstance(tvdb_id, str) or not tvdb_id.strip():
                    self.logger.warning(f"Invalid TVDB ID: {tvdb_id}")
                else:
                    ET.SubElement(root, 'tvdbid').text = str(tvdb_id).strip()
            if tmdb_id:
                if not isinstance(tmdb_id, str) or not tmdb_id.strip():
                    self.logger.warning(f"Invalid TMDB ID: {tmdb_id}")
                else:
                    ET.SubElement(root, 'tmdbid').text = str(tmdb_id).strip()

            # Air date
            if air_date:
                try:
                    # Validate date format
                    datetime.fromisoformat(air_date)
                    ET.SubElement(root, 'aired').text = air_date
                except ValueError as e:
                    self.logger.warning(f"Invalid air date format '{air_date}': {e}")

            # Multi-part indicator
            if is_multi_part:
                ET.SubElement(root, 'part').text = str(part_number)
                ET.SubElement(root, 'multipart').text = "true"

            # Format and return
            try:
                xml_str = ET.tostring(root, encoding='unicode')
                formatted_xml = self._format_xml(xml_str)
                self.logger.debug(f"Generated NFO for episode: {show_title} S{season:02d}E{episode:02d}")
                return formatted_xml
            except Exception as e:
                self.logger.error(f"Failed to format XML for episode '{show_title} S{season}E{episode}': {e}", exc_info=True)
                raise
                
        except ValueError as e:
            self.logger.error(f"Invalid parameters for episode NFO generation: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error generating episode NFO for '{show_title} S{season}E{episode}': {e}", exc_info=True)
            raise

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
            if not nfo_content or not nfo_content.strip():
                self.logger.error("NFO content cannot be empty")
                return False
            if not output_path:
                self.logger.error("Output path cannot be None")
                return False
            
            try:
                output_path.parent.mkdir(parents=True, exist_ok=True)
            except PermissionError as e:
                self.logger.error(f"Cannot create directory {output_path.parent}: {e}")
                return False
            except OSError as e:
                self.logger.error(f"Failed to create directory {output_path.parent}: {e}")
                return False
            
            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(nfo_content)
                self.logger.info(f"Saved NFO file: {output_path}")
                return True
            except PermissionError as e:
                self.logger.error(f"Permission denied writing to {output_path}: {e}")
                return False
            except OSError as e:
                self.logger.error(f"OS error writing to {output_path}: {e}")
                return False
            except UnicodeEncodeError as e:
                self.logger.error(f"Encoding error writing NFO to {output_path}: {e}")
                return False
                
        except Exception as e:
            self.logger.error(f"Unexpected error saving NFO file {output_path}: {e}", exc_info=True)
            return False

    @staticmethod
    def _format_xml(xml_str: str) -> str:
        """Pretty-format XML string."""
        try:
            if not xml_str or not xml_str.strip():
                return xml_str
            
            root = ET.fromstring(xml_str)
            return ET.tostring(root, encoding='unicode')
        except ET.ParseError as e:
            # If XML parsing fails, return original
            logging.getLogger(__name__).warning(f"XML parsing failed, returning unformatted: {e}")
            return xml_str
        except Exception as e:
            # If formatting fails, return original
            logging.getLogger(__name__).warning(f"XML formatting failed, returning unformatted: {e}")
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
        try:
            if not media_file_path:
                raise ValueError("Media file path cannot be None")
            if not suffix or not suffix.strip():
                suffix = 'nfo'
            
            nfo_path = media_file_path.with_suffix(f'.{suffix.strip()}')
            self.logger.debug(f"Inferred NFO path: {media_file_path} -> {nfo_path}")
            return nfo_path
            
        except ValueError as e:
            self.logger.error(f"Invalid parameters for NFO path inference: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error inferring NFO path for {media_file_path}: {e}", exc_info=True)
            raise

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
        try:
            if not title or not title.strip():
                self.logger.warning("Empty title provided for multi-part detection")
                return {
                    'is_multi_part': False,
                    'part_count': 1,
                    'individual_episodes': []
                }
            
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
                try:
                    season = int(match.group(1))
                    start_ep = int(match.group(2))
                    end_ep = int(match.group(3))
                    
                    if season < 0 or start_ep < 0 or end_ep < start_ep:
                        self.logger.warning(f"Invalid episode range in title '{title}': S{season}E{start_ep}-E{end_ep}")
                        return result
                    
                    result['is_multi_part'] = True
                    result['part_count'] = end_ep - start_ep + 1
                    result['individual_episodes'] = [
                        {'season': season, 'episode': ep}
                        for ep in range(start_ep, end_ep + 1)
                    ]
                    self.logger.debug(f"Detected multi-part episode in '{title}': {result['part_count']} parts")
                    return result
                    
                except (ValueError, IndexError) as e:
                    self.logger.warning(f"Error parsing episode range in title '{title}': {e}")
                    return result

            # Pattern: #x##-##
            pattern2 = r'(\d+)x(\d+)-(\d+)'
            match = re.search(pattern2, title)
            if match:
                try:
                    season = int(match.group(1))
                    start_ep = int(match.group(2))
                    end_ep = int(match.group(3))
                    
                    if season < 0 or start_ep < 0 or end_ep < start_ep:
                        self.logger.warning(f"Invalid episode range in title '{title}': {season}x{start_ep}-{end_ep}")
                        return result
                    
                    result['is_multi_part'] = True
                    result['part_count'] = end_ep - start_ep + 1
                    result['individual_episodes'] = [
                        {'season': season, 'episode': ep}
                        for ep in range(start_ep, end_ep + 1)
                    ]
                    self.logger.debug(f"Detected multi-part episode in '{title}': {result['part_count']} parts")
                    return result
                    
                except (ValueError, IndexError) as e:
                    self.logger.warning(f"Error parsing episode range in title '{title}': {e}")
                    return result

            return result
            
        except Exception as e:
            self.logger.error(f"Unexpected error detecting multi-part in title '{title}': {e}", exc_info=True)
            return {
                'is_multi_part': False,
                'part_count': 1,
                'individual_episodes': []
            }
