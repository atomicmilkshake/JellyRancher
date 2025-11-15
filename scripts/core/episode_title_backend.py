#!/usr/bin/env python3
"""
Episode Title Backend - Episode title analysis and management

Analyzes episode titles in organized TV shows against canonical data from TMDB caches.
Identifies titles that need cleaning or correction.

Features:
- Parse Jellyfin-formatted episode filenames
- Compare against TMDB cache data
- Identify technical tags and quality markers
- Score match quality
- Generate fix recommendations

Usage:
    from episode_title_backend import EpisodeTitleAnalyzer
    
    analyzer = EpisodeTitleAnalyzer()
    results = analyzer.analyze_show_folder(show_path, cache_path)
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from difflib import SequenceMatcher

from _common.logger import ProjectLogger


class EpisodeTitleAnalyzer:
    """Analyzes TV episode titles for issues and corrections."""
    
    # Common technical tags to remove
    TECHNICAL_TAGS = [
        r'\[(?:480|720|1080|2160)p\]',  # Resolution
        r'\[(?:x264|x265|H\.264|H\.265|HEVC|AVC)\]',  # Codecs
        r'\[(?:AAC|AC3|DTS|TrueHD|FLAC)\]',  # Audio codecs
        r'\[(?:WEB-DL|WEBRip|BluRay|HDTV|DVDRip)\]',  # Source
        r'\[(?:10bit|8bit)\]',  # Bit depth
        r'\[(?:DD\+?5\.1|DD5\.1|5\.1)\]',  # Audio channels
        r'\[(?:REPACK|PROPER|REAL)\]',  # Release info
        r'\[(?:Multi|Dual)(?:-Audio)?\]',  # Audio tracks
    ]
    
    # Quality markers that don't belong in titles
    QUALITY_MARKERS = [
        r'\[[\w\.-]+\]$',  # Release group at end
        r'\([\w\.-]+\)$',  # Release group in parens at end
    ]
    
    def __init__(self):
        self.logger = ProjectLogger("episode_title_analyzer")
    
    def extract_episode_info(self, filename: str, show_title: str) -> Optional[Dict[str, Any]]:
        """
        Extract episode information from a Jellyfin-formatted filename.
        
        Handles multiple Jellyfin naming patterns:
        - "S01E01 - Episode Title.ext"
        - "Show Title S01E01.ext" 
        - "Show Title - S01E01 - Episode Title.ext"
        
        Args:
            filename: Episode filename
            show_title: Show title for validation
        
        Returns:
            Dict with show_title, season, episode, episode_title or None if parse failed
        """
        # Remove extension
        name_without_ext = filename.rsplit('.', 1)[0]
        
        # Pattern 1: "S01E01 - Episode Title" (most common Jellyfin format)
        pattern1 = r'^S(\d+)E(\d+(?:-E\d+)?)\s*-\s*(.+)$'
        match1 = re.match(pattern1, name_without_ext, re.IGNORECASE)
        
        if match1:
            season = int(match1.group(1))
            episode = match1.group(2)
            title = match1.group(3).strip()
            return {
                'show_title': show_title,
                'season': season,
                'episode': episode,
                'episode_title': title,
                'pattern': 'jellyfin_standard'
            }
        
        # Pattern 2: "Show Title S01E01 [optional title]" (some shows)
        pattern2 = r'^(.+?)\s+S(\d+)E(\d+(?:-E\d+)?)(?:\s+(.+))?$'
        match2 = re.match(pattern2, name_without_ext, re.IGNORECASE)
        
        if match2:
            parsed_show = match2.group(1).strip()
            season = int(match2.group(2))
            episode = match2.group(3)
            title_part = match2.group(4).strip() if match2.group(4) else ""
            
            # Check if show title matches (basic check)
            show_base = show_title.lower().split(' (')[0]  # Remove year
            if show_base not in parsed_show.lower():
                return None
                
            # Use title part if available, otherwise generic
            episode_title = title_part if title_part else f"Episode {episode}"
                
            return {
                'show_title': parsed_show,
                'season': season,
                'episode': episode,
                'episode_title': episode_title,
                'pattern': 'show_title_prefix'
            }
        
        # Pattern 3: "Show Title - S01E01 - Episode Title" (full format)
        pattern3 = r'^(.+?)\s*-\s*S(\d+)E(\d+(?:-E\d+)?)\s*-\s*(.+)$'
        match3 = re.match(pattern3, name_without_ext, re.IGNORECASE)
        
        if match3:
            parsed_show = match3.group(1).strip()
            season = int(match3.group(2))
            episode = match3.group(3)
            title = match3.group(4).strip()
            
            # Check if show title matches (basic check)
            show_base = show_title.lower().split(' (')[0]  # Remove year
            if show_base not in parsed_show.lower():
                return None
                
            return {
                'show_title': parsed_show,
                'season': season,
                'episode': episode,
                'episode_title': title,
                'pattern': 'full_format'
            }
        
        return None
    
    def clean_episode_title(self, title: str) -> str:
        """
        Remove technical tags and quality markers from episode title.
        
        Args:
            title: Original episode title
        
        Returns:
            Cleaned title
        """
        cleaned = title
        
        # Remove technical tags
        for pattern in self.TECHNICAL_TAGS:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        # Remove quality markers
        for pattern in self.QUALITY_MARKERS:
            cleaned = re.sub(pattern, '', cleaned)
        
        # Clean up extra whitespace and hyphens
        cleaned = re.sub(r'\s+', ' ', cleaned)
        cleaned = re.sub(r'\s*-\s*$', '', cleaned)
        cleaned = cleaned.strip()
        
        return cleaned
    
    def calculate_similarity(self, title1: str, title2: str) -> float:
        """
        Calculate similarity score between two titles (0.0 to 1.0).
        
        Args:
            title1: First title
            title2: Second title
        
        Returns:
            Similarity score (1.0 = identical, 0.0 = completely different)
        """
        # Normalize for comparison
        norm1 = title1.lower().strip()
        norm2 = title2.lower().strip()
        
        # Use SequenceMatcher for fuzzy matching
        return SequenceMatcher(None, norm1, norm2).ratio()
    
    def compare_with_canonical(
        self,
        current_title: str,
        canonical_title: str
    ) -> Dict[str, Any]:
        """
        Compare current title with canonical title and generate recommendation.
        
        Args:
            current_title: Current episode title from filename
            canonical_title: Canonical title from TMDB
        
        Returns:
            Dict with comparison results and recommendation
        """
        # Clean current title
        cleaned_title = self.clean_episode_title(current_title)
        
        # Calculate similarities
        current_similarity = self.calculate_similarity(current_title, canonical_title)
        cleaned_similarity = self.calculate_similarity(cleaned_title, canonical_title)
        
        # Determine recommendation
        if current_title == canonical_title:
            recommendation = 'perfect'
            confidence = 'high'
            needs_rename = False
        elif cleaned_title == canonical_title:
            recommendation = 'use_cleaned'
            confidence = 'high'
            needs_rename = True
        elif cleaned_similarity > 0.9:
            recommendation = 'use_canonical'
            confidence = 'high'
            needs_rename = True
        elif cleaned_similarity > 0.7:
            recommendation = 'use_canonical'
            confidence = 'medium'
            needs_rename = True
        elif cleaned_similarity > 0.5:
            recommendation = 'review_manual'
            confidence = 'low'
            needs_rename = True
        else:
            recommendation = 'review_manual'
            confidence = 'very_low'
            needs_rename = True
        
        return {
            'current_title': current_title,
            'cleaned_title': cleaned_title,
            'canonical_title': canonical_title,
            'current_similarity': round(current_similarity, 3),
            'cleaned_similarity': round(cleaned_similarity, 3),
            'recommendation': recommendation,
            'confidence': confidence,
            'needs_rename': needs_rename
        }
    
    def load_tmdb_cache(self, cache_path: Path) -> Optional[Dict[str, Any]]:
        """
        Load TMDB cache file.
        
        Args:
            cache_path: Path to TMDB cache JSON file
        
        Returns:
            Cache data dict or None if load failed
        """
        try:
            if not cache_path.exists():
                self.logger.warning(f"Cache file not found: {cache_path}")
                return None
            
            with open(cache_path, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            self.logger.info(f"Loaded TMDB cache: {cache_data.get('show_name', 'Unknown')}")
            return cache_data
        
        except Exception as e:
            self.logger.error(f"Failed to load TMDB cache: {e}")
            return None
    
    def analyze_show_folder(
        self,
        show_path: Path,
        cache_path: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        Analyze all episodes in a show folder.
        
        Args:
            show_path: Path to show folder
            cache_path: Optional path to TMDB cache file
        
        Returns:
            Analysis results dict
        """
        show_title = show_path.name
        self.logger.info(f"Analyzing show: {show_title}")
        
        results = {
            'show_title': show_title,
            'show_path': str(show_path),
            'cache_path': str(cache_path) if cache_path else None,
            'canonical_available': False,
            'total_episodes': 0,
            'issues_found': 0,
            'episodes': []
        }
        
        # Load TMDB cache if provided
        cache_data = None
        if cache_path:
            cache_data = self.load_tmdb_cache(cache_path)
            if cache_data:
                results['canonical_available'] = True
                results['tmdb_id'] = cache_data.get('tmdb_id')
        
        # Find all video files
        video_extensions = ['*.mkv', '*.mp4', '*.avi', '*.m4v']
        episode_files = []
        for ext in video_extensions:
            episode_files.extend(show_path.rglob(ext))
        
        results['total_episodes'] = len(episode_files)
        self.logger.info(f"Found {len(episode_files)} episodes")
        
        # Analyze each episode
        for episode_file in sorted(episode_files):
            # Get relative path
            try:
                rel_path = episode_file.relative_to(show_path.parent)
            except:
                rel_path = episode_file
            
            episode_result = {
                'file_name': episode_file.name,
                'file_path': str(rel_path),
                'full_path': str(episode_file)
            }
            
            # Extract episode info
            episode_info = self.extract_episode_info(episode_file.name, show_title)
            if not episode_info:
                episode_result['issue_type'] = 'parse_error'
                episode_result['message'] = 'Could not parse episode information'
                results['issues_found'] += 1
                results['episodes'].append(episode_result)
                continue
            
            episode_result.update(episode_info)
            
            # Get canonical title from cache
            canonical_title = None
            if cache_data and 'seasons' in cache_data:
                season_key = str(episode_info['season'])
                if season_key in cache_data['seasons']:
                    season_data = cache_data['seasons'][season_key]
                    
                    # Handle episode ranges like "1-2"
                    episode_str = str(episode_info['episode'])
                    if '-' in episode_str:
                        # For combined episodes, use first episode
                        first_ep = episode_str.split('-')[0]
                        if 'episodes' in season_data and first_ep in season_data['episodes']:
                            canonical_title = season_data['episodes'][first_ep].get('name')
                    elif 'episodes' in season_data and episode_str in season_data['episodes']:
                        canonical_title = season_data['episodes'][episode_str].get('name')
            
            # Compare with canonical if available
            if canonical_title:
                comparison = self.compare_with_canonical(
                    episode_info['episode_title'],
                    canonical_title
                )
                episode_result.update(comparison)
                
                if comparison['needs_rename']:
                    episode_result['issue_type'] = 'title_mismatch'
                    results['issues_found'] += 1
            else:
                # No canonical data - just check if cleaning would help
                cleaned = self.clean_episode_title(episode_info['episode_title'])
                if cleaned != episode_info['episode_title']:
                    episode_result['issue_type'] = 'technical_tags'
                    episode_result['cleaned_title'] = cleaned
                    episode_result['recommendation'] = 'use_cleaned'
                    episode_result['confidence'] = 'medium'
                    episode_result['needs_rename'] = True
                    results['issues_found'] += 1
                else:
                    episode_result['issue_type'] = None
                    episode_result['needs_rename'] = False
            
            results['episodes'].append(episode_result)
        
        self.logger.info(f"Analysis complete: {results['issues_found']} issues found")
        return results
    
    def analyze_multiple_shows(
        self,
        show_paths: List[Path],
        cache_dir: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        Analyze multiple shows.
        
        Args:
            show_paths: List of show folder paths
            cache_dir: Optional directory containing TMDB cache files
        
        Returns:
            Combined analysis results
        """
        combined_results = {
            'total_shows': len(show_paths),
            'total_episodes': 0,
            'total_issues': 0,
            'shows': {}
        }
        
        for show_path in show_paths:
            show_title = show_path.name
            
            # Try to find matching cache file
            cache_path = None
            if cache_dir and cache_dir.exists():
                # Try common naming patterns
                possible_names = [
                    f"{show_title.lower().replace(' ', '_')}.json",
                    f"{show_title}.json",
                    f"cache_{show_title.lower().replace(' ', '_')}.json"
                ]
                
                for name in possible_names:
                    potential_cache = cache_dir / name
                    if potential_cache.exists():
                        cache_path = potential_cache
                        break
            
            # Analyze this show
            show_results = self.analyze_show_folder(show_path, cache_path)
            
            combined_results['total_episodes'] += show_results['total_episodes']
            combined_results['total_issues'] += show_results['issues_found']
            combined_results['shows'][show_title] = show_results
        
        return combined_results


if __name__ == "__main__":
    """Quick test of analyzer."""
    analyzer = EpisodeTitleAnalyzer()
    
    # Test title cleaning
    test_title = "The Pilot [1080p] [x264] [AAC] [WEB-DL]"
    cleaned = analyzer.clean_episode_title(test_title)
    print(f"Original: {test_title}")
    print(f"Cleaned: {cleaned}")
    
    # Test similarity
    similarity = analyzer.calculate_similarity("The Pilot", "Pilot")
    print(f"Similarity: {similarity:.3f}")
