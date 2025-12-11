#!/usr/bin/env python3
"""
Per-Bucket Prompts - Category-specific LLM prompts for media analysis.

Each bucket type (Movies, TV Shows, Games, etc.) gets a specialized prompt
that is optimized for that media category. This improves LLM analysis accuracy
by providing domain-specific context and patterns.

The key insight: A TV show prompt knows about S01E01 patterns and multi-episode
files, while a movie prompt focuses on year detection and release format parsing.
"""

import logging
from typing import Dict, List, Any, Optional
from enum import Enum

from scripts.core.bucket_manager import BucketType, BucketItem

logger = logging.getLogger(__name__)


# Jellyfin naming conventions per category
JELLYFIN_NAMING = {
    BucketType.MOVIES: """
Movies: /Movies/{Movie Name} ({Year})/{Movie Name} ({Year}).{ext}
Examples:
- /Movies/Inception (2010)/Inception (2010).mkv
- /Movies/The Matrix (1999)/The Matrix (1999).mp4
- Collections: /Movies/The Godfather Collection/The Godfather (1972)/The Godfather (1972).mkv
""",
    BucketType.TV_SHOWS: """
TV Shows: /TV Shows/{Series Name} ({Year})/Season {NN}/{Series Name} - S{NN}E{EE} - {Episode Title}.{ext}
Examples:
- /TV Shows/Breaking Bad (2008)/Season 01/Breaking Bad - S01E01 - Pilot.mkv
- Multi-episode files: Breaking Bad - S01E01-E02 - Pilot.mkv
- Specials: /TV Shows/Breaking Bad (2008)/Season 00/Breaking Bad - S00E01 - Special.mkv
""",
    BucketType.GAMES: """
Games: Organize by platform and title
Examples:
- /Games/PC/{Game Name}/
- /Games/PlayStation/{Game Name}/
- /Games/Nintendo/{Game Name}/
""",
    BucketType.MUSIC: """
Music: /Music/{Artist}/{Album}/{Track Number} - {Track Title}.{ext}
Examples:
- /Music/Pink Floyd/The Dark Side of the Moon/01 - Speak to Me.flac
- /Music/Various Artists/Compilation Name/01 - Artist - Track.mp3
""",
    BucketType.BOOKS: """
Books: /Books/{Author}/{Title}/{Title}.{ext}
Examples:
- /Books/Frank Herbert/Dune/Dune.epub
- /Books/J.R.R. Tolkien/The Lord of the Rings/The Fellowship of the Ring.epub
""",
}


class PromptBuilder:
    """Builds category-specific prompts for LLM analysis."""
    
    @staticmethod
    def get_base_prompt() -> str:
        """Get the base system prompt for all categories."""
        return """You are a media library organizer. Your task is to analyze file/folder names
and propose a reorganization plan that follows Jellyfin naming conventions.

CRITICAL RULES:
1. Preserve the original file extension
2. Extract year information when available
3. Flag ambiguous cases for manual review
4. Use confidence levels: HIGH, MEDIUM, LOW, MANUAL
5. Output ONLY valid JSON

Confidence Guidelines:
- HIGH: Clear pattern match, unambiguous title and year
- MEDIUM: Good match but minor uncertainty (e.g., year from folder not filename)
- LOW: Partial match, may need manual verification
- MANUAL: Cannot determine, requires human decision
"""
    
    @staticmethod
    def get_movie_prompt(folder_summary: str) -> str:
        """
        Generate a movie-specific analysis prompt.
        
        Movies focus on:
        - Year detection from various patterns
        - Resolution/quality tags
        - Release group detection
        - Collection grouping
        """
        return f"""{PromptBuilder.get_base_prompt()}

CATEGORY: MOVIES

{JELLYFIN_NAMING[BucketType.MOVIES]}

MOVIE-SPECIFIC PATTERNS TO DETECT:
- Years: (2020), .2020., [2020]
- Quality: 720p, 1080p, 2160p, 4K, BluRay, WEB-DL, HDRip, DVDRip
- Release groups: YIFY, RARBG, SPARKS, FGT, etc.
- Collections: "Trilogy", "Collection", numbered series

FOLDER STRUCTURE TO ANALYZE:
{folder_summary}

Respond with JSON:
{{
  "detected_media": [
    {{
      "current_location": "original/path/Movie.Name.2020.1080p.BluRay.mkv",
      "detected_title": "Movie Name",
      "detected_year": 2020,
      "proposed_path": "/Movies/Movie Name (2020)/Movie Name (2020).mkv",
      "confidence": "HIGH",
      "notes": "Clear year and quality tags"
    }}
  ],
  "ambiguous_items": [
    {{
      "current_location": "some/path",
      "issue": "Cannot determine year",
      "suggestions": ["Possible title 1 (Year)", "Possible title 2 (Year)"]
    }}
  ],
  "statistics": {{
    "total_analyzed": 10,
    "high_confidence": 7,
    "medium_confidence": 2,
    "manual_review": 1
  }}
}}
"""
    
    @staticmethod
    def get_tv_show_prompt(folder_summary: str) -> str:
        """
        Generate a TV show-specific analysis prompt.
        
        TV shows focus on:
        - Season/Episode detection (S01E01, 1x01, etc.)
        - Multi-episode files (S01E01-E02)
        - Specials and extras
        - Series year (premiere year)
        """
        return f"""{PromptBuilder.get_base_prompt()}

CATEGORY: TV SHOWS

{JELLYFIN_NAMING[BucketType.TV_SHOWS]}

TV SHOW-SPECIFIC PATTERNS TO DETECT:
- Episode formats: S01E01, s01e01, 1x01, Season 1 Episode 1
- Multi-episode: S01E01-E02, S01E01-02, S01E01E02
- Specials: S00E01 or placed in Season 00
- Date-based shows: 2020.01.15 or 2020-01-15 format
- Series premiere year: (2008) usually from folder name

FOLDER STRUCTURE TO ANALYZE:
{folder_summary}

Respond with JSON:
{{
  "detected_media": [
    {{
      "current_location": "original/path",
      "detected_title": "Show Name",
      "detected_year": 2020,
      "season": 1,
      "episode": 1,
      "episode_title": "Pilot",
      "is_multi_episode": false,
      "proposed_path": "/TV Shows/Show Name (2020)/Season 01/Show Name - S01E01 - Pilot.mkv",
      "confidence": "HIGH",
      "notes": "Clear S01E01 pattern"
    }}
  ],
  "ambiguous_items": [...],
  "statistics": {{...}}
}}
"""
    
    @staticmethod
    def get_game_prompt(folder_summary: str) -> str:
        """Generate a game-specific analysis prompt."""
        return f"""{PromptBuilder.get_base_prompt()}

CATEGORY: GAMES

{JELLYFIN_NAMING[BucketType.GAMES]}

GAME-SPECIFIC PATTERNS TO DETECT:
- Platform indicators: PC, PS4, PS5, Xbox, Switch, Nintendo
- File types: ISO, ROM, PKG, XCI, NSP
- Versions: v1.0, Update, DLC, GOTY Edition
- Regions: USA, EUR, JPN, NTSC, PAL

FOLDER STRUCTURE TO ANALYZE:
{folder_summary}

Respond with JSON:
{{
  "detected_media": [
    {{
      "current_location": "original/path",
      "detected_title": "Game Name",
      "platform": "PC",
      "version": "1.0",
      "proposed_path": "/Games/PC/Game Name/",
      "confidence": "HIGH",
      "notes": "Clear PC game"
    }}
  ],
  "ambiguous_items": [...],
  "statistics": {{...}}
}}
"""
    
    @staticmethod
    def get_music_prompt(folder_summary: str) -> str:
        """Generate a music-specific analysis prompt."""
        return f"""{PromptBuilder.get_base_prompt()}

CATEGORY: MUSIC

{JELLYFIN_NAMING[BucketType.MUSIC]}

MUSIC-SPECIFIC PATTERNS TO DETECT:
- Artist - Album - Track format
- Track numbers: 01, 01., (1)
- Disc numbers: CD1, Disc 1
- Quality: FLAC, 320kbps, Lossless
- Various Artists / Compilations

FOLDER STRUCTURE TO ANALYZE:
{folder_summary}

Respond with JSON:
{{
  "detected_media": [
    {{
      "current_location": "original/path",
      "detected_artist": "Artist Name",
      "detected_album": "Album Name",
      "detected_track": 1,
      "detected_title": "Track Title",
      "proposed_path": "/Music/Artist Name/Album Name/01 - Track Title.flac",
      "confidence": "HIGH"
    }}
  ],
  "ambiguous_items": [...],
  "statistics": {{...}}
}}
"""
    
    @staticmethod
    def get_book_prompt(folder_summary: str) -> str:
        """Generate a book-specific analysis prompt."""
        return f"""{PromptBuilder.get_base_prompt()}

CATEGORY: BOOKS

{JELLYFIN_NAMING[BucketType.BOOKS]}

BOOK-SPECIFIC PATTERNS TO DETECT:
- Author - Title format
- Series: "(Book 1)", "#1", "Vol. 1"
- ISBN numbers
- Formats: epub, mobi, pdf, audiobook

FOLDER STRUCTURE TO ANALYZE:
{folder_summary}

Respond with JSON:
{{
  "detected_media": [
    {{
      "current_location": "original/path",
      "detected_author": "Author Name",
      "detected_title": "Book Title",
      "series_name": null,
      "series_number": null,
      "proposed_path": "/Books/Author Name/Book Title/Book Title.epub",
      "confidence": "HIGH"
    }}
  ],
  "ambiguous_items": [...],
  "statistics": {{...}}
}}
"""
    
    @staticmethod
    def get_unsorted_prompt(folder_summary: str) -> str:
        """Generate a prompt for unsorted/mixed content."""
        return f"""{PromptBuilder.get_base_prompt()}

CATEGORY: MIXED/UNSORTED CONTENT

This bucket contains items that couldn't be automatically categorized.
Try to identify each item's category and propose appropriate organization.

{JELLYFIN_NAMING[BucketType.MOVIES]}
{JELLYFIN_NAMING[BucketType.TV_SHOWS]}

FOLDER STRUCTURE TO ANALYZE:
{folder_summary}

Respond with JSON:
{{
  "detected_media": [
    {{
      "current_location": "original/path",
      "detected_type": "movie" | "tv_show" | "game" | "music" | "book" | "unknown",
      "detected_title": "Title",
      "proposed_path": "appropriate/path",
      "confidence": "MEDIUM",
      "notes": "Guessed type based on..."
    }}
  ],
  "ambiguous_items": [...],
  "statistics": {{...}}
}}
"""
    
    @classmethod
    def get_prompt_for_bucket(cls, bucket_type: BucketType, folder_summary: str) -> str:
        """Get the appropriate prompt for a bucket type."""
        prompt_map = {
            BucketType.MOVIES: cls.get_movie_prompt,
            BucketType.TV_SHOWS: cls.get_tv_show_prompt,
            BucketType.GAMES: cls.get_game_prompt,
            BucketType.MUSIC: cls.get_music_prompt,
            BucketType.BOOKS: cls.get_book_prompt,
            BucketType.UNSORTED: cls.get_unsorted_prompt,
        }
        
        prompt_func = prompt_map.get(bucket_type, cls.get_unsorted_prompt)
        return prompt_func(folder_summary)


def build_folder_summary_for_bucket(items: List[BucketItem], max_items: int = 100) -> str:
    """
    Build a folder summary string for items in a bucket.
    
    Args:
        items: List of BucketItems in the bucket
        max_items: Maximum items to include (to fit token limits)
        
    Returns:
        Formatted string for LLM consumption
    """
    lines = []
    
    # Sort by path for readability
    sorted_items = sorted(items, key=lambda x: str(x.path))[:max_items]
    
    for item in sorted_items:
        prefix = "📁" if item.is_folder else "📄"
        size_mb = item.size_bytes / (1024 * 1024)
        size_str = f"{size_mb:.1f}MB" if size_mb < 1024 else f"{size_mb/1024:.2f}GB"
        
        if item.is_folder:
            lines.append(f"{prefix} {item.name}/ ({item.file_count} files, {size_str})")
        else:
            lines.append(f"{prefix} {item.name} ({size_str})")
    
    if len(items) > max_items:
        lines.append(f"\n... and {len(items) - max_items} more items")
    
    return "\n".join(lines)


class PerBucketAnalyzer:
    """
    Analyzes bucket contents using per-bucket specialized prompts.
    
    This class orchestrates the LLM analysis for each bucket, sending
    category-specific prompts and collecting results.
    """
    
    def __init__(self, llm_client=None, model: str = "Grok-4.1-Fast-Reasoning"):
        """
        Initialize the analyzer.
        
        Args:
            llm_client: Optional LLM client (will use default if not provided)
            model: LLM model to use
        """
        self.llm_client = llm_client
        self.model = model
        self.results: Dict[BucketType, Dict[str, Any]] = {}
        
    def analyze_bucket(self, bucket_type: BucketType, items: List[BucketItem],
                       api_key: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze a single bucket's contents.
        
        Args:
            bucket_type: Type of bucket being analyzed
            items: Items in the bucket
            api_key: Optional API key for LLM
            
        Returns:
            Analysis results dict
        """
        if not items:
            return {
                'bucket_type': bucket_type.value,
                'status': 'empty',
                'detected_media': [],
                'statistics': {'total_analyzed': 0}
            }
        
        # Build folder summary
        folder_summary = build_folder_summary_for_bucket(items)
        
        # Get category-specific prompt
        prompt = PromptBuilder.get_prompt_for_bucket(bucket_type, folder_summary)
        
        logger.info(f"Analyzing {bucket_type.value} bucket with {len(items)} items")
        
        # If no LLM client configured, return a placeholder
        if self.llm_client is None:
            return {
                'bucket_type': bucket_type.value,
                'status': 'needs_llm',
                'prompt': prompt,
                'item_count': len(items),
                'detected_media': [],
                'statistics': {'total_analyzed': 0}
            }
        
        # TODO: Call LLM with prompt and parse response
        # For now, return the prepared prompt
        return {
            'bucket_type': bucket_type.value,
            'status': 'prompt_ready',
            'prompt': prompt,
            'item_count': len(items)
        }
    
    def analyze_all_buckets(self, bucket_manager, api_key: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze all non-empty buckets.
        
        Args:
            bucket_manager: BucketManager with categorized items
            api_key: Optional API key for LLM
            
        Returns:
            Combined results from all buckets
        """
        from scripts.core.bucket_manager import BucketManager
        
        all_results = {
            'buckets': {},
            'total_items': 0,
            'status': 'complete'
        }
        
        for bucket in bucket_manager.get_non_empty_buckets():
            result = self.analyze_bucket(bucket.bucket_type, bucket.items, api_key)
            all_results['buckets'][bucket.bucket_type.value] = result
            all_results['total_items'] += len(bucket.items)
        
        return all_results

