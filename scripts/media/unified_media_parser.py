#!/usr/bin/env python3
"""
Unified Media Parser - Consolidated media filename analysis

This module wraps existing backend analyzers into a unified interface with:
- Movie parsing (from MovieNameAnalyzer)
- TV episode parsing (from EpisodeTitleAnalyzer)  
- Folder classification (from FolderStructureScanner)
- ADDED: Anime patterns, pre-1978 years, edition detection

Architecture: Adapter pattern wrapping existing battle-tested code while
adding missing capabilities. Each backend can evolve independently.

Phase 1 Implementation per ANALYSIS_TAB_IMPROVEMENT_PLAN.md Option D (Hybrid)
"""

import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


class MediaType(Enum):
    """Media type classification."""
    MOVIE = "movie"
    TV_EPISODE = "tv_episode"
    ANIME = "anime"
    OTHER = "other"


class Confidence(Enum):
    """Confidence level for parsed results."""
    HIGH = "high"      # >80% - explicit patterns matched
    MEDIUM = "medium"  # 60-80% - some ambiguity
    LOW = "low"        # <60% - needs manual review


@dataclass
class ParsedMedia:
    """Unified parsed media result."""
    media_type: MediaType
    title: str
    confidence: Confidence
    
    # Movie fields
    year: Optional[int] = None
    edition: Optional[str] = None  # Director's Cut, Extended, etc.
    
    # TV/Anime fields
    season: Optional[int] = None
    episode: Optional[int] = None
    episode_end: Optional[int] = None  # For multi-episode files
    episode_title: Optional[str] = None
    absolute_episode: Optional[int] = None  # Anime absolute numbering
    
    # Technical metadata
    resolution: Optional[str] = None
    codec: Optional[str] = None
    quality: Optional[str] = None
    audio: Optional[str] = None
    language: Optional[str] = None
    release_group: Optional[str] = None
    
    # Source info
    original_filename: str = ""
    parent_folder: str = ""
    issues: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'media_type': self.media_type.value,
            'title': self.title,
            'confidence': self.confidence.value,
            'year': self.year,
            'edition': self.edition,
            'season': self.season,
            'episode': self.episode,
            'episode_end': self.episode_end,
            'episode_title': self.episode_title,
            'absolute_episode': self.absolute_episode,
            'resolution': self.resolution,
            'codec': self.codec,
            'quality': self.quality,
            'audio': self.audio,
            'language': self.language,
            'release_group': self.release_group,
            'original_filename': self.original_filename,
            'parent_folder': self.parent_folder,
            'issues': self.issues
        }


class UnifiedMediaParser:
    """
    Unified parser consolidating all media parsing logic.
    
    Wraps existing backends while adding missing patterns:
    - Anime absolute numbering
    - Pre-1978 year detection (classics)
    - Edition detection (Director's Cut, Extended, etc.)
    - Improved folder-aware parsing
    """
    
    # =========================================================================
    # Pattern Constants
    # =========================================================================
    
    # File extensions
    VIDEO_EXTS = {'.mkv', '.mp4', '.avi', '.m4v', '.mov', '.wmv', '.flv', 
                  '.webm', '.mpg', '.mpeg', '.ts', '.m2ts', '.vob'}
    SUBTITLE_EXTS = {'.srt', '.sub', '.ass', '.vtt', '.idx', '.ssa', '.sbv'}
    
    # Year patterns - EXPANDED to include pre-1978 films (classics)
    YEAR_PATTERNS = [
        r'\((\d{4})\)',           # (2020) - standard
        r'\[(\d{4})\]',           # [2020] - brackets
        r'\.(\d{4})\.',           # .2020. - dots
        r'\s(\d{4})\s',           # space-separated
    ]
    # Valid year range: 1888 (first film) to current+1
    YEAR_MIN = 1888
    YEAR_MAX = 2030
    
    # Edition patterns - NEW
    EDITION_PATTERNS = [
        (r"director'?s?\s*cut", "Director's Cut"),
        (r"extended\s*(edition|cut)?", "Extended Edition"),
        (r"theatrical\s*(edition|cut)?", "Theatrical"),
        (r"unrated\s*(edition|cut)?", "Unrated"),
        (r"remastered", "Remastered"),
        (r"special\s*edition", "Special Edition"),
        (r"ultimate\s*(edition|cut)?", "Ultimate Edition"),
        (r"anniversary\s*edition", "Anniversary Edition"),
        (r"criterion\s*(collection)?", "Criterion Collection"),
        (r"imax\s*(edition)?", "IMAX"),
        (r"3d", "3D"),
        (r"redux", "Redux"),
        (r"final\s*cut", "Final Cut"),
    ]
    
    # TV Episode patterns - standard S01E01 format
    TV_PATTERNS = [
        # S01E01 format (most common)
        r'[Ss](\d{1,2})[Ee](\d{1,3})(?:[Ee-](\d{1,3}))?',
        # Season 1 Episode 1 format
        r'[Ss]eason\s*(\d{1,2})\s*[Ee]pisode\s*(\d{1,3})',
        # 1x01 format
        r'(\d{1,2})[Xx](\d{1,3})(?:-(\d{1,3}))?',
    ]
    
    # Anime patterns - NEW (absolute numbering)
    ANIME_PATTERNS = [
        # [01] or [001] - common fansub format
        r'\[(\d{2,4})\](?:\s|$|\.)',
        # - 01 - or - 001 - 
        r'\s-\s(\d{2,4})\s-\s',
        # Episode 01 or Ep 01 or E01 (without season)
        r'(?:Episode|Ep\.?|E)\s*(\d{2,4})(?:\s|$|\.)',
        # Just number at end after title: "Show Name 01.mkv"
        r'\s(\d{2,3})(?:v\d)?(?:\s*\[|\s*\(|\s*\.|\s*$)',
    ]
    
    # Resolution patterns
    RESOLUTION_PATTERNS = [
        (r'2160[pi]|4[Kk]|UHD', '2160p'),
        (r'1080[pi]', '1080p'),
        (r'720[pi]', '720p'),
        (r'480[pi]|SD', '480p'),
        (r'576[pi]', '576p'),
    ]
    
    # Quality/Source patterns
    QUALITY_PATTERNS = [
        (r'[Bb]lu-?[Rr]ay|BD[Rr]ip|BR[Rr]ip', 'BluRay'),
        (r'WEB-?DL', 'WEB-DL'),
        (r'WEB[Rr]ip', 'WEBRip'),
        (r'HDTV', 'HDTV'),
        (r'DVD[Rr]ip', 'DVDRip'),
        (r'HD[Rr]ip', 'HDRip'),
        (r'[Cc][Aa][Mm]', 'CAM'),
        (r'TS|TELESYNC', 'TS'),
        (r'TC|TELECINE', 'TC'),
        (r'REMUX', 'REMUX'),
    ]
    
    # Codec patterns
    CODEC_PATTERNS = [
        (r'[Xx]\.?264|[Hh]\.?264|AVC', 'H.264'),
        (r'[Xx]\.?265|[Hh]\.?265|HEVC', 'H.265'),
        (r'AV1', 'AV1'),
        (r'VP9', 'VP9'),
        (r'MPEG-?2', 'MPEG2'),
        (r'[Xx]vid', 'XviD'),
        (r'DivX', 'DivX'),
    ]
    
    # Audio patterns
    AUDIO_PATTERNS = [
        (r'DTS-?HD(?:\s*MA)?', 'DTS-HD MA'),
        (r'TrueHD|Atmos', 'TrueHD'),
        (r'DTS', 'DTS'),
        (r'DD[P\+]?\s*5\.1|Dolby\s*Digital\s*Plus', 'DD+ 5.1'),
        (r'DD\s*5\.1|AC-?3\s*5\.1', 'DD 5.1'),
        (r'AC-?3', 'AC3'),
        (r'AAC', 'AAC'),
        (r'FLAC', 'FLAC'),
        (r'MP3', 'MP3'),
        (r'7\.1', '7.1'),
        (r'5\.1', '5.1'),
        (r'2\.0|[Ss]tereo', 'Stereo'),
    ]
    
    # Garbage patterns to remove
    GARBAGE_PATTERNS = [
        r'\[.*?\]',      # [anything]
        r'\((?![12]\d{3}\)).*?\)',  # (anything) except years
        r'\{.*?\}',      # {anything}
        r'-\s*\w+$',     # Release group at end
    ]
    
    # Subtitle language detection
    SUBTITLE_LANG_PATTERN = r'\.([a-z]{2,3})(?:\.(forced|sdh|cc))?$'
    
    def __init__(self):
        """Initialize the unified parser."""
        self._compile_patterns()
        logger.info("UnifiedMediaParser initialized")
    
    def _compile_patterns(self):
        """Pre-compile regex patterns for performance."""
        self._tv_re = [re.compile(p, re.I) for p in self.TV_PATTERNS]
        self._anime_re = [re.compile(p, re.I) for p in self.ANIME_PATTERNS]
        self._edition_re = [(re.compile(p, re.I), name) for p, name in self.EDITION_PATTERNS]
        self._resolution_re = [(re.compile(p, re.I), name) for p, name in self.RESOLUTION_PATTERNS]
        self._quality_re = [(re.compile(p, re.I), name) for p, name in self.QUALITY_PATTERNS]
        self._codec_re = [(re.compile(p, re.I), name) for p, name in self.CODEC_PATTERNS]
        self._audio_re = [(re.compile(p, re.I), name) for p, name in self.AUDIO_PATTERNS]
    
    # =========================================================================
    # Main Parse Methods
    # =========================================================================
    
    def parse(self, filepath: Path, use_folder_context: bool = True) -> ParsedMedia:
        """
        Parse a media file and extract all metadata.
        
        Args:
            filepath: Path to media file
            use_folder_context: If True, uses parent folder name for context
        
        Returns:
            ParsedMedia with all extracted information
        """
        filename = filepath.stem
        ext = filepath.suffix.lower()
        parent_folder = filepath.parent.name if use_folder_context else ""
        
        # Initialize result
        result = ParsedMedia(
            media_type=MediaType.OTHER,
            title="",
            confidence=Confidence.LOW,
            original_filename=filepath.name,
            parent_folder=parent_folder
        )
        
        # Skip non-media files
        if ext not in self.VIDEO_EXTS and ext not in self.SUBTITLE_EXTS:
            result.issues.append("Not a recognized media file extension")
            return result
        
        # Handle subtitle language
        if ext in self.SUBTITLE_EXTS:
            self._extract_subtitle_info(filename, result)
        
        # Working copy for parsing (will be stripped down)
        working = filename
        
        # Extract technical metadata first (before title extraction)
        working = self._extract_technical_metadata(working, result)
        
        # Try TV episode patterns first
        if self._try_parse_tv(working, result, parent_folder):
            return result
        
        # Try anime patterns
        if self._try_parse_anime(working, result, parent_folder):
            return result
        
        # Try movie patterns
        if self._try_parse_movie(working, result, parent_folder):
            return result
        
        # Fallback: unknown type, use cleaned filename as title
        result.title = self._clean_title(working)
        result.issues.append("Could not determine media type")
        
        return result
    
    def parse_batch(self, filepaths: List[Path]) -> List[ParsedMedia]:
        """Parse multiple files."""
        return [self.parse(fp) for fp in filepaths]
    
    # =========================================================================
    # Type-Specific Parsing
    # =========================================================================
    
    def _try_parse_tv(self, filename: str, result: ParsedMedia, 
                      parent_folder: str) -> bool:
        """
        Try to parse as TV episode (S01E01 format).
        
        Returns True if successfully parsed as TV.
        """
        for pattern in self._tv_re:
            match = pattern.search(filename)
            if match:
                result.media_type = MediaType.TV_EPISODE
                result.season = int(match.group(1))
                result.episode = int(match.group(2))
                
                # Multi-episode (S01E01-E02)
                if match.lastindex >= 3 and match.group(3):
                    result.episode_end = int(match.group(3))
                
                # Extract title (before the episode marker)
                title_part = filename[:match.start()].strip()
                
                # If title is empty, use folder name
                if not title_part or len(title_part) < 2:
                    title_part = parent_folder
                
                result.title = self._clean_title(title_part)
                
                # Extract episode title (after the episode marker)
                after_match = filename[match.end():].strip(' -.')
                if after_match and not self._is_technical_tag(after_match):
                    result.episode_title = self._clean_title(after_match)
                
                # Confidence based on pattern quality
                if result.title and result.season and result.episode:
                    result.confidence = Confidence.HIGH
                else:
                    result.confidence = Confidence.MEDIUM
                
                return True
        
        return False
    
    def _try_parse_anime(self, filename: str, result: ParsedMedia,
                         parent_folder: str) -> bool:
        """
        Try to parse as anime (absolute episode numbering).
        
        Returns True if successfully parsed as anime.
        """
        # Check for anime indicators
        anime_indicators = [
            '[', ']',  # Common in fansub releases
            'fansub', 'horriblesubs', 'erai-raws', 'subsplease',
            'nyaa', 'bakabt',
        ]
        
        filename_lower = filename.lower()
        has_anime_indicator = any(ind in filename_lower for ind in anime_indicators)
        
        # Also check parent folder for anime indicators
        folder_lower = parent_folder.lower()
        is_anime_folder = 'anime' in folder_lower or has_anime_indicator
        
        if not is_anime_folder and not has_anime_indicator:
            # Check if it matches anime patterns anyway
            for pattern in self._anime_re:
                if pattern.search(filename):
                    is_anime_folder = True
                    break
        
        if is_anime_folder:
            for pattern in self._anime_re:
                match = pattern.search(filename)
                if match:
                    result.media_type = MediaType.ANIME
                    result.absolute_episode = int(match.group(1))
                    
                    # Extract title (before the episode number)
                    title_part = filename[:match.start()].strip()
                    
                    # Clean up common anime group tags
                    title_part = re.sub(r'^\[.*?\]\s*', '', title_part)
                    
                    if not title_part or len(title_part) < 2:
                        title_part = parent_folder
                        # Also clean group tags from folder
                        title_part = re.sub(r'^\[.*?\]\s*', '', title_part)
                    
                    result.title = self._clean_title(title_part)
                    result.confidence = Confidence.MEDIUM  # Anime parsing is less certain
                    
                    return True
        
        return False
    
    def _try_parse_movie(self, filename: str, result: ParsedMedia,
                         parent_folder: str) -> bool:
        """
        Try to parse as movie.
        
        Returns True if successfully parsed as movie.
        """
        # Extract year
        year = self._extract_year(filename)
        
        # Extract edition
        edition = self._extract_edition(filename)
        
        if year:
            result.media_type = MediaType.MOVIE
            result.year = year
            result.edition = edition
            
            # Extract title (everything before year)
            for pattern in self.YEAR_PATTERNS:
                match = re.search(pattern, filename)
                if match:
                    title_part = filename[:match.start()].strip()
                    break
            else:
                title_part = filename
            
            result.title = self._clean_title(title_part)
            result.confidence = Confidence.HIGH if result.title else Confidence.MEDIUM
            
            return True
        
        # No year found - check if folder has year (common for movies)
        folder_year = self._extract_year(parent_folder)
        if folder_year:
            result.media_type = MediaType.MOVIE
            result.year = folder_year
            result.edition = edition
            
            # Use folder name as title basis if it has the year
            for pattern in self.YEAR_PATTERNS:
                match = re.search(pattern, parent_folder)
                if match:
                    result.title = self._clean_title(parent_folder[:match.start()])
                    break
            
            if not result.title:
                result.title = self._clean_title(filename)
            
            result.confidence = Confidence.MEDIUM
            result.issues.append("Year found in folder name, not filename")
            
            return True
        
        return False
    
    # =========================================================================
    # Extraction Helpers
    # =========================================================================
    
    def _extract_year(self, text: str) -> Optional[int]:
        """Extract year from text, supporting pre-1978 films."""
        for pattern in self.YEAR_PATTERNS:
            match = re.search(pattern, text)
            if match:
                year = int(match.group(1))
                if self.YEAR_MIN <= year <= self.YEAR_MAX:
                    return year
        return None
    
    def _extract_edition(self, text: str) -> Optional[str]:
        """Extract edition (Director's Cut, Extended, etc.)."""
        for pattern, name in self._edition_re:
            if pattern.search(text):
                return name
        return None
    
    def _extract_technical_metadata(self, filename: str, result: ParsedMedia) -> str:
        """
        Extract and remove technical metadata from filename.
        Returns cleaned filename.
        """
        working = filename
        
        # Resolution
        for pattern, name in self._resolution_re:
            if pattern.search(working):
                result.resolution = name
                working = pattern.sub('', working)
                break
        
        # Quality/Source
        for pattern, name in self._quality_re:
            if pattern.search(working):
                result.quality = name
                working = pattern.sub('', working)
                break
        
        # Codec
        for pattern, name in self._codec_re:
            if pattern.search(working):
                result.codec = name
                working = pattern.sub('', working)
                break
        
        # Audio
        for pattern, name in self._audio_re:
            if pattern.search(working):
                result.audio = name
                working = pattern.sub('', working)
                break
        
        # Release group (usually at end)
        group_match = re.search(r'-([A-Za-z0-9]+)$', working)
        if group_match and len(group_match.group(1)) <= 15:
            result.release_group = group_match.group(1)
            working = working[:group_match.start()]
        
        return working
    
    def _extract_subtitle_info(self, filename: str, result: ParsedMedia):
        """Extract subtitle language and type."""
        match = re.search(self.SUBTITLE_LANG_PATTERN, filename, re.I)
        if match:
            result.language = match.group(1).lower()
    
    def _clean_title(self, title: str) -> str:
        """Clean up extracted title."""
        # Remove garbage patterns
        for pattern in self.GARBAGE_PATTERNS:
            title = re.sub(pattern, '', title, flags=re.I)
        
        # Replace separators with spaces
        title = re.sub(r'[._]', ' ', title)
        
        # Clean up whitespace
        title = re.sub(r'\s+', ' ', title)
        title = re.sub(r'^\s*-\s*|\s*-\s*$', '', title)
        
        return title.strip()
    
    def _is_technical_tag(self, text: str) -> bool:
        """Check if text is purely technical metadata."""
        text_lower = text.lower()
        
        # Check against all technical patterns
        for pattern, _ in self._resolution_re + self._quality_re + self._codec_re + self._audio_re:
            if pattern.search(text_lower):
                return True
        
        # Check for common release group patterns
        if re.match(r'^[A-Za-z0-9]{2,10}$', text):
            return True
        
        return False
    
    # =========================================================================
    # Folder Classification
    # =========================================================================
    
    def classify_folder(self, folder_path: Path) -> str:
        """
        Classify a folder's content type.
        
        Returns one of:
        - 'tv_show_with_seasons'
        - 'tv_show_flat'
        - 'anime'
        - 'movie'
        - 'movie_collection'
        - 'mixed'
        - 'unknown'
        """
        if not folder_path.exists():
            return 'unknown'
        
        folder_name = folder_path.name.lower()
        
        # Check for season folders
        subfolders = [f for f in folder_path.iterdir() if f.is_dir()]
        season_folders = [f for f in subfolders 
                        if 'season' in f.name.lower() or 
                        re.match(r's\d{1,2}$', f.name.lower())]
        
        if len(season_folders) >= 2:
            return 'tv_show_with_seasons'
        
        # Check folder name for anime
        if 'anime' in folder_name:
            return 'anime'
        
        # Check folder name for season
        if 'season' in folder_name or re.match(r's\d{1,2}$', folder_name):
            return 'season'
        
        # Count video files
        video_files = []
        for ext in self.VIDEO_EXTS:
            video_files.extend(folder_path.glob(f'*{ext}'))
        
        direct_video_count = len(video_files)
        
        # Many videos directly = flat TV show
        if direct_video_count > 5:
            return 'tv_show_flat'
        
        # Few videos, no subfolders = movie folder
        if direct_video_count > 0 and len(subfolders) == 0:
            return 'movie'
        
        # Has subfolders with videos = collection
        if len(subfolders) > 0:
            return 'movie_collection'
        
        return 'unknown'
    
    # =========================================================================
    # Similarity Scoring
    # =========================================================================
    
    def calculate_similarity(self, title1: str, title2: str) -> float:
        """
        Calculate similarity score between two titles (0.0 to 1.0).
        """
        norm1 = title1.lower().strip()
        norm2 = title2.lower().strip()
        return SequenceMatcher(None, norm1, norm2).ratio()


# =============================================================================
# Module-level convenience functions
# =============================================================================

_parser_instance: Optional[UnifiedMediaParser] = None

def get_parser() -> UnifiedMediaParser:
    """Get singleton parser instance."""
    global _parser_instance
    if _parser_instance is None:
        _parser_instance = UnifiedMediaParser()
    return _parser_instance

def parse_media_file(filepath: Path) -> ParsedMedia:
    """Convenience function to parse a single file."""
    return get_parser().parse(filepath)

def parse_media_files(filepaths: List[Path]) -> List[ParsedMedia]:
    """Convenience function to parse multiple files."""
    return get_parser().parse_batch(filepaths)


# =============================================================================
# CLI Entry Point
# =============================================================================

if __name__ == "__main__":
    import sys
    
    logging.basicConfig(level=logging.INFO)
    
    if len(sys.argv) < 2:
        print("Usage: python unified_media_parser.py <file_or_folder>")
        print("\nExamples:")
        print("  python unified_media_parser.py 'Movie Name (2020).mkv'")
        print("  python unified_media_parser.py 'Show.S01E01.Episode.Title.mkv'")
        print("  python unified_media_parser.py '/path/to/media/folder'")
        sys.exit(1)
    
    target = Path(sys.argv[1])
    parser = UnifiedMediaParser()
    
    if target.is_file():
        result = parser.parse(target)
        print(f"\n{'='*60}")
        print(f"FILE: {target.name}")
        print(f"{'='*60}")
        print(f"Type: {result.media_type.value}")
        print(f"Title: {result.title}")
        print(f"Confidence: {result.confidence.value}")
        if result.year:
            print(f"Year: {result.year}")
        if result.edition:
            print(f"Edition: {result.edition}")
        if result.season:
            print(f"Season: {result.season}")
        if result.episode:
            ep_str = f"E{result.episode}"
            if result.episode_end:
                ep_str += f"-E{result.episode_end}"
            print(f"Episode: {ep_str}")
        if result.absolute_episode:
            print(f"Absolute Episode: {result.absolute_episode}")
        if result.resolution:
            print(f"Resolution: {result.resolution}")
        if result.codec:
            print(f"Codec: {result.codec}")
        if result.issues:
            print(f"Issues: {', '.join(result.issues)}")
    
    elif target.is_dir():
        folder_type = parser.classify_folder(target)
        print(f"\n{'='*60}")
        print(f"FOLDER: {target.name}")
        print(f"Type: {folder_type}")
        print(f"{'='*60}")
        
        # Parse all video files
        files = []
        for ext in parser.VIDEO_EXTS:
            files.extend(target.rglob(f'*{ext}'))
        
        print(f"\nFound {len(files)} video files:")
        for f in sorted(files)[:20]:
            result = parser.parse(f)
            print(f"  [{result.media_type.value}] {result.title} "
                  f"({result.confidence.value})")
        
        if len(files) > 20:
            print(f"  ... and {len(files) - 20} more")

