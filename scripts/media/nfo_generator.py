#!/usr/bin/env python3
"""
NFO Generator - Hooks from canonical metadata DB to NFO file creation.

This module provides a small, focused surface for generating NFO files
for multi-part episodes identified in the canonical metadata database.

It is intentionally conservative: it does not attempt to infer exact
video file paths. Instead, it creates NFOs in a caller-provided base
directory using show/season/episode metadata, and logs all file
creations through TransactionManager using ActionType.CREATE_NFO.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, List, Optional
from xml.etree.ElementTree import Element, SubElement, ElementTree

from scripts.core.action_plan import ActionType
from scripts.utils.transaction_manager import TransactionManager, Operation, OperationType


logger = logging.getLogger(__name__)


@dataclass
class NFOGenerationTask:
    """Represents a single NFO file to be generated."""
    show_title: str
    season_number: int
    episode_number: int
    episode_name: str
    output_path: Path


def _sanitize_name(name: str) -> str:
    """Sanitize a string for use in filesystem paths."""
    return "".join(c if c not in '\\/:*?"<>|' else "_" for c in name).strip()


def build_nfo_tasks_from_canonical(
    canonical_db: Dict[str, Any],
    base_output_dir: Path,
) -> List[NFOGenerationTask]:
    """
    Build NFO generation tasks from a canonical metadata database.

    Args:
        canonical_db: Canonical database as produced by MediaMetadataLookup.
        base_output_dir: Root directory under which to place generated NFO files.

    Returns:
        List of NFOGenerationTask objects.
    """
    tasks: List[NFOGenerationTask] = []
    multi_part = canonical_db.get("multi_part_episodes", [])

    for entry in multi_part:
        show_title = entry.get("show_title", "Unknown Show")
        season_number = int(entry.get("season_number", 0))
        episode_number = int(entry.get("episode_number", 0))
        episode_name = entry.get("episode_name", "Unknown Episode")

        show_dir = base_output_dir / _sanitize_name(show_title)
        season_dir = show_dir / f"Season {season_number:02d}"
        season_dir.mkdir(parents=True, exist_ok=True)

        nfo_filename = f"S{season_number:02d}E{episode_number:02d}.nfo"
        output_path = season_dir / nfo_filename

        tasks.append(
            NFOGenerationTask(
                show_title=show_title,
                season_number=season_number,
                episode_number=episode_number,
                episode_name=episode_name,
                output_path=output_path,
            )
        )

    logger.info("Prepared %d NFO tasks from canonical DB", len(tasks))
    return tasks


def _build_episode_nfo_xml(task: NFOGenerationTask) -> Element:
    """Build a minimal Kodi/Jellyfin-compatible episodedetails XML element."""
    root = Element("episodedetails")

    title_el = SubElement(root, "title")
    title_el.text = task.episode_name

    season_el = SubElement(root, "season")
    season_el.text = str(task.season_number)

    ep_el = SubElement(root, "episode")
    ep_el.text = str(task.episode_number)

    show_el = SubElement(root, "showtitle")
    show_el.text = task.show_title

    # Multi-part episodes are encoded as normal episodes; the multi-part
    # mapping itself lives in the canonical metadata DB.
    return root


def generate_nfo_files(
    tasks: List[NFOGenerationTask],
    dry_run: bool = False,
    transaction_db: Optional[Path] = None,
) -> None:
    """
    Generate NFO files for the provided tasks, logging all creations
    through TransactionManager using OperationType.NFO_CREATE.

    Args:
        tasks: List of NFOGenerationTask objects to realize on disk.
        dry_run: If True, only log what would be done.
        transaction_db: Optional path to a custom transactions DB.
    """
    if not tasks:
        logger.info("No NFO tasks provided; nothing to do.")
        return

    logger.info(
        "Generating %d NFO file(s)%s",
        len(tasks),
        " (dry run)" if dry_run else "",
    )

    tm = TransactionManager(db_path=transaction_db) if transaction_db else TransactionManager()

    with tm:
        batch_id = tm.begin_batch("nfo_generation")

        for task in tasks:
            nfo_path = task.output_path

            if dry_run:
                logger.info(
                    "[DRY RUN] Would create NFO for %s S%02dE%02d at %s",
                    task.show_title,
                    task.season_number,
                    task.episode_number,
                    nfo_path,
                )
                continue

            # Build XML content
            root = _build_episode_nfo_xml(task)
            tree = ElementTree(root)
            nfo_path.parent.mkdir(parents=True, exist_ok=True)
            tree.write(nfo_path, encoding="utf-8", xml_declaration=True)

            # Log NFO creation into transaction manager
            op = Operation(
                operation_type=OperationType.NFO_CREATE,
                source_path=str(nfo_path),
                destination_path=None,
                metadata={
                    "action_type": ActionType.CREATE_NFO.name,
                    "show_title": task.show_title,
                    "season_number": task.season_number,
                    "episode_number": task.episode_number,
                },
            )
            tx_id = tm.log_operation(op, batch_id=batch_id)

            # For a create operation, the MD5 before/after are the same file;
            # we simply calculate once after creation.
            from scripts.utils.transaction_manager import FileHasher

            dest_md5 = FileHasher.calculate_md5(nfo_path)
            tm.complete_operation(tx_id, dest_md5)

            logger.info("Created NFO file at %s", nfo_path)


__all__ = [
    "NFOGenerationTask",
    "build_nfo_tasks_from_canonical",
    "generate_nfo_files",
]

#!/usr/bin/env python3
"""
NFO File Generator for Jellyfin

Generates NFO (XML) files to provide Jellyfin with accurate metadata,
especially for multi-part episodes that need special handling.

NFO files help Jellyfin correctly identify:
- Multi-part episodes (e.g., 2-part pilots)
- Feature-length episodes
- Special episodes
- Correct episode numbering

Format follows Kodi/Jellyfin NFO specification:
https://kodi.wiki/view/NFO_files/TV_shows
"""

import xml.etree.ElementTree as ET
from xml.dom import minidom
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import logging


class NFOGenerator:
    """
    Generates NFO files for Jellyfin media server.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize NFO generator.
        
        Args:
            logger: Logger instance
        """
        self.logger = logger or self._setup_logger()
        self.logger.info("NFO Generator initialized")
    
    def _setup_logger(self) -> logging.Logger:
        """Set up basic logger if none provided."""
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def generate_multipart_episode_nfo(
        self,
        show_title: str,
        season_number: int,
        episode_numbers: List[int],
        episode_title: str,
        overview: Optional[str] = None,
        air_date: Optional[str] = None,
        tmdb_id: Optional[int] = None,
        imdb_id: Optional[str] = None,
        runtime: Optional[int] = None
    ) -> str:
        """
        Generate NFO content for a multi-part episode.
        
        For episodes like Star Trek TNG "Encounter at Farpoint" that aired
        as Episodes 1 & 2 but are stored as a single file, this generates
        an NFO that tells Jellyfin to treat it as Episode 1 with proper metadata.
        
        Args:
            show_title: TV show title
            season_number: Season number
            episode_numbers: List of episode numbers that comprise this multi-part episode
            episode_title: Episode title
            overview: Plot description
            air_date: Original air date (YYYY-MM-DD)
            tmdb_id: TMDB show ID
            imdb_id: IMDB show ID
            runtime: Runtime in minutes
            
        Returns:
            NFO XML content as string
        """
        # Use first episode number as the primary
        primary_episode = min(episode_numbers)
        
        # Create root element
        root = ET.Element("episodedetails")
        
        # Basic episode info
        ET.SubElement(root, "title").text = episode_title
        ET.SubElement(root, "showtitle").text = show_title
        ET.SubElement(root, "season").text = str(season_number)
        ET.SubElement(root, "episode").text = str(primary_episode)
        
        # Add display season/episode (for multi-part episodes)
        ET.SubElement(root, "displayseason").text = str(season_number)
        ET.SubElement(root, "displayepisode").text = str(primary_episode)
        
        # Plot/overview
        if overview:
            ET.SubElement(root, "plot").text = overview
        
        # Air date
        if air_date:
            ET.SubElement(root, "aired").text = air_date
            ET.SubElement(root, "premiered").text = air_date
        
        # Runtime
        if runtime:
            ET.SubElement(root, "runtime").text = str(runtime)
        
        # IDs for scrapers
        if tmdb_id:
            uniqueid_tmdb = ET.SubElement(root, "uniqueid", type="tmdb", default="true")
            uniqueid_tmdb.text = str(tmdb_id)
        
        if imdb_id:
            uniqueid_imdb = ET.SubElement(root, "uniqueid", type="imdb")
            uniqueid_imdb.text = imdb_id
        
        # Multi-part indicator
        if len(episode_numbers) > 1:
            multipart = ET.SubElement(root, "multipart")
            for ep_num in sorted(episode_numbers):
                ET.SubElement(multipart, "part").text = str(ep_num)
        
        # Convert to pretty-printed XML string
        xml_string = self._prettify_xml(root)
        
        self.logger.info(
            f"Generated NFO for {show_title} S{season_number:02d}E{primary_episode:02d} "
            f"({episode_title}) - Multi-part: {len(episode_numbers)} episodes"
        )
        
        return xml_string
    
    def generate_movie_nfo(
        self,
        title: str,
        year: Optional[int] = None,
        overview: Optional[str] = None,
        tmdb_id: Optional[int] = None,
        imdb_id: Optional[str] = None,
        runtime: Optional[int] = None,
        genres: Optional[List[str]] = None,
        poster_url: Optional[str] = None
    ) -> str:
        """
        Generate NFO content for a movie.
        
        Args:
            title: Movie title
            year: Release year
            overview: Plot description
            tmdb_id: TMDB movie ID
            imdb_id: IMDB movie ID
            runtime: Runtime in minutes
            genres: List of genre names
            poster_url: URL to poster image
            
        Returns:
            NFO XML content as string
        """
        # Create root element
        root = ET.Element("movie")
        
        # Basic movie info
        ET.SubElement(root, "title").text = title
        
        if year:
            ET.SubElement(root, "year").text = str(year)
        
        if overview:
            ET.SubElement(root, "plot").text = overview
        
        if runtime:
            ET.SubElement(root, "runtime").text = str(runtime)
        
        # IDs
        if tmdb_id:
            uniqueid_tmdb = ET.SubElement(root, "uniqueid", type="tmdb", default="true")
            uniqueid_tmdb.text = str(tmdb_id)
        
        if imdb_id:
            uniqueid_imdb = ET.SubElement(root, "uniqueid", type="imdb")
            uniqueid_imdb.text = imdb_id
        
        # Genres
        if genres:
            for genre in genres:
                ET.SubElement(root, "genre").text = genre
        
        # Poster
        if poster_url:
            thumb = ET.SubElement(root, "thumb", aspect="poster")
            thumb.text = poster_url
        
        # Convert to pretty-printed XML string
        xml_string = self._prettify_xml(root)
        
        self.logger.info(f"Generated NFO for movie: {title} ({year or 'unknown year'})")
        
        return xml_string
    
    def generate_tvshow_nfo(
        self,
        title: str,
        year: Optional[int] = None,
        overview: Optional[str] = None,
        tmdb_id: Optional[int] = None,
        imdb_id: Optional[str] = None,
        genres: Optional[List[str]] = None,
        poster_url: Optional[str] = None
    ) -> str:
        """
        Generate NFO content for a TV show (tvshow.nfo).
        
        Args:
            title: TV show title
            year: First air year
            overview: Show description
            tmdb_id: TMDB show ID
            imdb_id: IMDB show ID
            genres: List of genre names
            poster_url: URL to poster image
            
        Returns:
            NFO XML content as string
        """
        # Create root element
        root = ET.Element("tvshow")
        
        # Basic show info
        ET.SubElement(root, "title").text = title
        
        if year:
            ET.SubElement(root, "year").text = str(year)
            ET.SubElement(root, "premiered").text = f"{year}-01-01"  # Approximate
        
        if overview:
            ET.SubElement(root, "plot").text = overview
        
        # IDs
        if tmdb_id:
            uniqueid_tmdb = ET.SubElement(root, "uniqueid", type="tmdb", default="true")
            uniqueid_tmdb.text = str(tmdb_id)
        
        if imdb_id:
            uniqueid_imdb = ET.SubElement(root, "uniqueid", type="imdb")
            uniqueid_imdb.text = imdb_id
        
        # Genres
        if genres:
            for genre in genres:
                ET.SubElement(root, "genre").text = genre
        
        # Poster
        if poster_url:
            thumb = ET.SubElement(root, "thumb", aspect="poster")
            thumb.text = poster_url
        
        # Convert to pretty-printed XML string
        xml_string = self._prettify_xml(root)
        
        self.logger.info(f"Generated NFO for TV show: {title} ({year or 'unknown year'})")
        
        return xml_string
    
    def _prettify_xml(self, elem: ET.Element) -> str:
        """
        Return a pretty-printed XML string for the Element.
        
        Args:
            elem: XML Element to prettify
            
        Returns:
            Pretty-printed XML string
        """
        rough_string = ET.tostring(elem, encoding='unicode')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")
    
    def save_nfo(
        self, 
        nfo_content: str, 
        file_path: str,
        dry_run: bool = False
    ) -> bool:
        """
        Save NFO content to file.
        
        Args:
            nfo_content: NFO XML content
            file_path: Path where NFO should be saved
            dry_run: If True, don't actually write file
            
        Returns:
            True if successful, False otherwise
        """
        nfo_file = Path(file_path)
        
        if dry_run:
            self.logger.info(f"[DRY RUN] Would save NFO to: {nfo_file}")
            return True
        
        try:
            nfo_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(nfo_file, 'w', encoding='utf-8') as f:
                f.write(nfo_content)
            
            self.logger.info(f"✓ NFO saved: {nfo_file}")
            return True
        
        except Exception as e:
            self.logger.error(f"✗ Failed to save NFO to {nfo_file}: {e}")
            return False
    
    def generate_nfos_for_multipart_episodes(
        self,
        canonical_db: Dict,
        multipart_episodes: List[Dict],
        output_dir: str,
        dry_run: bool = False
    ) -> List[Dict]:
        """
        Generate NFO files for all detected multi-part episodes.
        
        Args:
            canonical_db: Canonical metadata database
            multipart_episodes: List of multi-part episodes from LLM analysis
            output_dir: Base directory for NFO files
            dry_run: If True, don't actually write files
            
        Returns:
            List of NFO generation results
        """
        results = []
        output_path = Path(output_dir)
        
        self.logger.info(f"Generating NFO files for {len(multipart_episodes)} multi-part episodes...")
        
        for mp_episode in multipart_episodes:
            show_title = mp_episode.get('show_title')
            season_number = mp_episode.get('season_number')
            episode_numbers = mp_episode.get('episode_numbers', [])
            combined_title = mp_episode.get('combined_episode_title')
            
            # Find metadata in canonical database
            show_metadata = self._find_show_metadata(canonical_db, show_title)
            
            if not show_metadata:
                self.logger.warning(f"No metadata found for show: {show_title}")
                results.append({
                    'show': show_title,
                    'season': season_number,
                    'episodes': episode_numbers,
                    'status': 'error',
                    'error': 'Show metadata not found'
                })
                continue
            
            # Get episode metadata
            episode_metadata = self._find_episode_metadata(
                show_metadata, season_number, min(episode_numbers)
            )
            
            # Generate NFO
            nfo_content = self.generate_multipart_episode_nfo(
                show_title=show_metadata.get('title', show_title),
                season_number=season_number,
                episode_numbers=episode_numbers,
                episode_title=combined_title or episode_metadata.get('name', 'Unknown'),
                overview=episode_metadata.get('overview'),
                air_date=episode_metadata.get('air_date'),
                tmdb_id=show_metadata.get('tmdb_id'),
                imdb_id=show_metadata.get('imdb_id'),
                runtime=episode_metadata.get('runtime')
            )
            
            # Determine NFO file path
            # Format: Show Name (Year)/Season XX/Show Name - sXXeYY.nfo
            safe_show_name = self._sanitize_filename(show_metadata.get('title', show_title))
            year = show_metadata.get('year')
            show_folder = f"{safe_show_name} ({year})" if year else safe_show_name
            
            primary_episode = min(episode_numbers)
            nfo_filename = f"{safe_show_name} - s{season_number:02d}e{primary_episode:02d}.nfo"
            nfo_path = output_path / show_folder / f"Season {season_number:02d}" / nfo_filename
            
            # Save NFO
            success = self.save_nfo(nfo_content, str(nfo_path), dry_run=dry_run)
            
            results.append({
                'show': show_title,
                'season': season_number,
                'episodes': episode_numbers,
                'nfo_path': str(nfo_path),
                'status': 'success' if success else 'error'
            })
        
        # Summary
        success_count = sum(1 for r in results if r['status'] == 'success')
        self.logger.info(f"NFO generation complete: {success_count}/{len(results)} successful")
        
        return results
    
    def _find_show_metadata(self, canonical_db: Dict, show_title: str) -> Optional[Dict]:
        """Find show metadata in canonical database by title."""
        for show in canonical_db.get('tv_shows', []):
            if show.get('title', '').lower() == show_title.lower():
                return show
            if show.get('original_title', '').lower() == show_title.lower():
                return show
        return None
    
    def _find_episode_metadata(
        self, 
        show_metadata: Dict, 
        season_number: int, 
        episode_number: int
    ) -> Dict:
        """Find specific episode metadata within show metadata."""
        for season in show_metadata.get('seasons', []):
            if season.get('season_number') == season_number:
                for episode in season.get('episodes', []):
                    if episode.get('episode_number') == episode_number:
                        return episode
        return {}
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename by removing invalid characters."""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '')
        return filename.strip()


def main():
    """Example usage of NFO Generator."""
    import json
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python nfo_generator.py <canonical_metadata.json> <llm_analysis.json>")
        print("\nExample:")
        print("  python nfo_generator.py data/canonical_metadata_20241108_120000.json data/llm_analysis_20241108_120000.json")
        return
    
    # Load canonical database
    canonical_file = Path(sys.argv[1])
    if not canonical_file.exists():
        print(f"Error: File not found: {canonical_file}")
        return
    
    print(f"Loading canonical database from: {canonical_file}")
    with open(canonical_file, 'r', encoding='utf-8') as f:
        canonical_db = json.load(f)
    
    # Load LLM analysis
    analysis_file = Path(sys.argv[2])
    if not analysis_file.exists():
        print(f"Error: File not found: {analysis_file}")
        return
    
    print(f"Loading LLM analysis from: {analysis_file}")
    with open(analysis_file, 'r', encoding='utf-8') as f:
        analysis_data = json.load(f)
    
    multipart_episodes = analysis_data.get('multi_part_episodes', [])
    
    if not multipart_episodes:
        print("No multi-part episodes detected in analysis")
        return
    
    # Initialize NFO generator
    nfo_gen = NFOGenerator()
    
    # Generate NFO files
    print("\n" + "="*80)
    print("GENERATING NFO FILES FOR MULTI-PART EPISODES")
    print("="*80 + "\n")
    
    results = nfo_gen.generate_nfos_for_multipart_episodes(
        canonical_db=canonical_db,
        multipart_episodes=multipart_episodes,
        output_dir="data/nfo_files",
        dry_run=False
    )
    
    print("\n" + "="*80)
    print("NFO GENERATION COMPLETE")
    print("="*80)
    print(f"✓ Successful: {sum(1 for r in results if r['status'] == 'success')}")
    print(f"✗ Failed: {sum(1 for r in results if r['status'] == 'error')}")
    print("="*80)


if __name__ == "__main__":
    main()
