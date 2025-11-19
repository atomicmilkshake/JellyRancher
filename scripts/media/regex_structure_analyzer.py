#!/usr/bin/env python3
"""
Regex Structure Analyzer - Deterministic Media Analysis

Fast, offline, regex-based analysis of media files as an alternative to LLM analysis.
Provides instant, free, deterministic reorganization proposals using pattern matching.

Based on Grok 4.1's regex parsing approach, adapted to match LLMStructureAnalyzer interface.

Advantages:
- Lightning fast (processes 1000s of files in milliseconds)
- No API costs (completely free)
- Deterministic (same input = same output)
- Offline capable (no internet required)
- Handles standard naming conventions excellently

Use Cases:
- Well-organized libraries with standard naming
- Quick previews without LLM costs
- Offline environments
- Batch processing large libraries
"""

import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from collections import defaultdict
from os.path import commonpath

from scripts.core.file_scanner import FileRecord

logger = logging.getLogger(__name__)

# File type classifications
VIDEO_EXTS = {'.mkv', '.mp4', '.avi', '.m4v', '.mov', '.wmv', '.flv', '.webm', '.mpg', '.mpeg', '.ts', '.m2ts'}
SUBTITLE_EXTS = {'.srt', '.sub', '.ass', '.vtt', '.idx', '.ssa', '.sbv'}


class RegexStructureAnalyzer:
    """
    Analyzes media folder structures using regex pattern matching.
    
    Provides deterministic, fast analysis without requiring LLM API calls.
    Returns results in same format as LLMStructureAnalyzer for compatibility.
    """
    
    def __init__(self, logger_instance: Optional[logging.Logger] = None):
        """
        Initialize the regex analyzer.
        
        Args:
            logger_instance: Logger instance (optional)
        
        Raises:
            RuntimeError: If initialization fails
        """
        try:
            self.logger = logger_instance or self._setup_logger()
            self.logger.info("RegexStructureAnalyzer initialized")
        except Exception as e:
            if logger_instance:
                logger_instance.error(f"Failed to initialize RegexStructureAnalyzer: {e}", exc_info=True)
            raise RuntimeError(f"Failed to initialize RegexStructureAnalyzer: {e}")
    
    def _setup_logger(self) -> logging.Logger:
        """Set up basic logger if none provided."""
        logger_inst = logging.getLogger(__name__)
        logger_inst.setLevel(logging.INFO)
        
        if not logger_inst.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger_inst.addHandler(handler)
        
        return logger_inst
    
    def analyze_structure(
        self,
        file_records: List[FileRecord],
        base_output_path: Optional[Path] = None
    ) -> Dict:
        """
        Analyze file records and generate reorganization plan.
        
        Args:
            file_records: List of FileRecord objects from scan
            base_output_path: Optional base path for reorganization (default: common_root/reorganized)
        
        Returns:
            Dictionary containing:
            - detected_media: List of detected movies and TV shows
            - reorganization_plan: Proposed Jellyfin-compliant structure
            - multi_part_episodes: Episodes requiring NFO files
            - reasoning: Analysis explanation
        
        Raises:
            TypeError: If file_records is not a list
            ValueError: If file_records is empty
            RuntimeError: If analysis fails
        """
        try:
            # Input validation
            if not isinstance(file_records, list):
                raise TypeError(f"file_records must be a list, got {type(file_records)}")
            
            if not file_records:
                raise ValueError("file_records cannot be empty")
            
            self.logger.info(f"Starting regex analysis of {len(file_records)} files...")
            
            # Parse all files
            parsed_files = []
            parse_errors = 0
            
            for record in file_records:
                try:
                    parsed_info, confidence = self._parse_media_file(record)
                    parsed_files.append({
                        'record': record,
                        'parsed': parsed_info,
                        'confidence': confidence
                    })
                except Exception as e:
                    self.logger.warning(f"Failed to parse {record.absolute_path}: {e}")
                    parse_errors += 1
                    continue
            
            if parse_errors > 0:
                self.logger.warning(f"Parsed {len(parsed_files)} files with {parse_errors} errors")
            
            # Determine common root for reorganization
            try:
                if base_output_path:
                    new_root = base_output_path
                else:
                    file_paths = [str(pf['record'].absolute_path) for pf in parsed_files]
                    common_root = commonpath(file_paths) if len(file_paths) > 1 else str(Path(file_paths[0]).parent)
                    new_root = Path(common_root) / 'reorganized'
            except Exception as e:
                self.logger.warning(f"Failed to determine common root: {e}")
                new_root = Path("reorganized")
            
            # Group by media (detect unique movies/TV shows)
            detected_media = self._detect_media_items(parsed_files)
            
            # Generate reorganization plan
            reorganization_plan = self._generate_reorganization_plan(parsed_files, new_root)
            
            # Detect multi-part episodes
            multi_part_episodes = self._detect_multi_part_episodes(parsed_files)
            
            # Generate reasoning
            reasoning = self._generate_reasoning(parsed_files, detected_media, parse_errors)
            
            result = {
                'detected_media': detected_media,
                'reorganization_plan': reorganization_plan,
                'multi_part_episodes': multi_part_episodes,
                'reasoning': reasoning,
                'metadata': {
                    'analyzer': 'regex',
                    'timestamp': datetime.now().isoformat(),
                    'total_files_analyzed': len(parsed_files),
                    'parse_errors': parse_errors
                }
            }
            
            self.logger.info(f"Regex analysis complete: {len(detected_media)} media items detected")
            return result
            
        except (TypeError, ValueError) as e:
            self.logger.error(f"Invalid input to analyze_structure: {e}", exc_info=True)
            raise
        except Exception as e:
            self.logger.error(f"Failed to analyze structure: {e}", exc_info=True)
            raise RuntimeError(f"Failed to analyze structure: {e}")
    
    def _parse_media_file(self, record: FileRecord) -> Tuple[Dict, float]:
        """
        Parse a media filename using regex patterns.
        
        Based on Grok 4.1's parse_media_name() with enhancements.
        
        Args:
            record: FileRecord to parse
        
        Returns:
            Tuple of (parsed_info_dict, confidence_score_0_to_1)
        """
        try:
            result = {}
            filename = record.absolute_path.stem
            ext = record.extension.lower()
            confidence = 1.0  # Start with high confidence
            
            # Skip non-media files
            if ext not in VIDEO_EXTS and ext not in SUBTITLE_EXTS:
                return {'type': 'other', 'title': filename}, 0.1
            
            # Language for subtitles (e.g., .en.srt, .en.forced.srt)
            lang_re = re.compile(r'\.([a-zA-Z]{2,3})(?:\.(forced|sdh))?$', re.I)
            lang_match = lang_re.search(filename)
            if lang_match:
                result['language'] = lang_match.group(1).lower()
                if lang_match.group(2):
                    result['subtitle_type'] = lang_match.group(2).lower()
                filename = filename[:lang_match.start()]
            
            # Remove garbage like [ettv] or (extra)
            garbage_re = re.compile(r'\[.*?\]|\(.*?\)', re.I)
            filename = garbage_re.sub('', filename)
            
            # Season and episode (CRITICAL - extract early)
            ep_re = re.compile(
                r'(?i)(?:s|season[ . -]?)(\d{1,3})(?:[ . -]?(?:e|episode[ . -]?|x))(\d{1,3})'
                r'(?:(?:[ . -]?(?:-|[to]|and|&|e|x)?[ . -]?)?(\d{1,3}))?'
            )
            ep_match = ep_re.search(filename)
            if ep_match:
                result['season'] = int(ep_match.group(1))
                result['episode'] = int(ep_match.group(2))
                if ep_match.group(3) and int(ep_match.group(3)) > result['episode']:
                    result['episode2'] = int(ep_match.group(3))  # Multi-part episode
                filename = filename.replace(ep_match.group(0), '')
                confidence = 0.95  # High confidence with explicit S01E01
            
            # Resolution (1080p, 720p, 2160p, 4K)
            res_re = re.search(r'(?i)(\d{3,4}[pi]|4k)', filename)
            if res_re:
                result['resolution'] = res_re.group(1).upper()
                filename = filename.replace(res_re.group(0), '')
            
            # Quality (BluRay, WEB-DL, HDTV, etc.)
            quality_re = re.search(
                r'(?i)(blu ?ray|br ?rip|bd ?rip|web ?-?dl|web ?rip|hdtv|dvd ?rip|hd ?rip|cam|ts|tc|dvd ?scr)',
                filename
            )
            if quality_re:
                result['quality'] = quality_re.group(1).upper().replace(' ', '')
                filename = filename.replace(quality_re.group(0), '')
            
            # Codec (x264, x265, HEVC, H.264)
            codec_re = re.search(r'(?i)(x[ . -]?264|x[ . -]?265|h[ . -]?264|h[ . -]?265|hevc)', filename)
            if codec_re:
                result['codec'] = codec_re.group(1).upper().replace(' ', '').replace('.', '').replace('-', '')
                filename = filename.replace(codec_re.group(0), '')
            
            # Audio (AAC, DTS, AC3, etc.)
            audio_re = re.search(r'(?i)(aac|dts[ . -]?hd|dts|ac3|ddp ?5\.1|truehd|5\.1|7\.1)', filename)
            if audio_re:
                result['audio'] = audio_re.group(1).upper().replace(' ', '')
                filename = filename.replace(audio_re.group(0), '')
            
            # Release Group (usually at end)
            group_re = re.search(r'[ . -]([a-z0-9]+?)(?:\[.*\])?$', filename, re.I)
            if group_re:
                result['group'] = group_re.group(1).upper()
                filename = filename.replace(group_re.group(0), '')
            
            # Year (1970-2029)
            year_re = re.search(r'(?<!\d)(19[78-9]\d|20[0-2]\d)(?!\d)', filename)
            if year_re:
                result['year'] = int(year_re.group(1))
                filename = filename.replace(year_re.group(0), '')
                if 'season' not in result:
                    confidence = min(confidence, 0.85)  # Year alone = good but not perfect
            
            # Clean title (what's left after removing all markers)
            title = re.sub(r'[ . _-]+', ' ', filename).strip()
            result['title'] = title
            
            # Determine type
            if 'season' in result:
                result['type'] = 'tv_show'
            elif 'year' in result and ext in VIDEO_EXTS:
                result['type'] = 'movie'
            else:
                result['type'] = 'other'
                confidence = 0.3  # Low confidence for unclear files
            
            # Adjust confidence based on completeness
            if not title:
                confidence = 0.2  # Very low if no title extracted
            elif result['type'] == 'other':
                confidence = 0.3  # Low if type unclear
            
            return result, confidence
            
        except Exception as e:
            self.logger.warning(f"Error parsing file {record.absolute_path}: {e}")
            return {'type': 'other', 'title': record.absolute_path.stem}, 0.1
    
    def _detect_media_items(self, parsed_files: List[Dict]) -> List[Dict]:
        """
        Group parsed files into unique media items (movies/TV shows).
        
        Args:
            parsed_files: List of parsed file info dicts
        
        Returns:
            List of detected media items with metadata
        """
        try:
            media_items = {}  # title -> media_info
            
            for pf in parsed_files:
                parsed = pf['parsed']
                media_type = parsed.get('type', 'other')
                
                if media_type == 'other':
                    continue
                
                title = parsed.get('title', '').strip()
                if not title:
                    continue
                
                # Normalize title for grouping
                title_key = title.lower().replace(' ', '')
                
                if title_key not in media_items:
                    media_items[title_key] = {
                        'title': title,  # Use original capitalization from first occurrence
                        'type': media_type,
                        'year_estimate': parsed.get('year'),
                        'current_location': str(pf['record'].parent_folder),
                        'confidence': 'high' if pf['confidence'] >= 0.8 else 'medium' if pf['confidence'] >= 0.6 else 'low',
                        'seasons_detected': set() if media_type == 'tv_show' else None,
                        'file_count': 0,
                        'notes': []
                    }
                
                # Increment file count
                media_items[title_key]['file_count'] += 1
                
                # Track seasons for TV shows
                if media_type == 'tv_show' and 'season' in parsed:
                    media_items[title_key]['seasons_detected'].add(parsed['season'])
                
                # Track quality markers
                if 'resolution' in parsed:
                    if 'quality_markers' not in media_items[title_key]:
                        media_items[title_key]['quality_markers'] = set()
                    media_items[title_key]['quality_markers'].add(parsed['resolution'])
            
            # Convert to list format
            detected = []
            for title_key, info in media_items.items():
                item = {
                    'title': info['title'],
                    'type': info['type'],
                    'year_estimate': info['year_estimate'],
                    'current_location': info['current_location'],
                    'confidence': info['confidence'],
                    'notes': f"Regex-detected from {info['file_count']} files"
                }
                
                if info['type'] == 'tv_show' and info['seasons_detected']:
                    item['seasons_detected'] = len(info['seasons_detected'])
                    item['notes'] += f" ({item['seasons_detected']} seasons)"
                
                detected.append(item)
            
            return detected
            
        except Exception as e:
            self.logger.error(f"Failed to detect media items: {e}", exc_info=True)
            return []
    
    def _generate_reorganization_plan(
        self,
        parsed_files: List[Dict],
        new_root: Path
    ) -> Dict:
        """
        Generate Jellyfin-compliant reorganization plan.
        
        Args:
            parsed_files: List of parsed file info dicts
            new_root: Base path for reorganization
        
        Returns:
            Reorganization plan dictionary
        """
        try:
            folder_changes = []
            jellyfin_issues = []
            
            for pf in parsed_files:
                record = pf['record']
                parsed = pf['parsed']
                confidence = pf['confidence']
                
                current_path = str(record.absolute_path)
                
                # Generate new path based on type
                if parsed['type'] == 'tv_show' and 'season' in parsed and 'episode' in parsed:
                    new_path = self._generate_tv_path(parsed, record.extension, new_root)
                    action = 'move'
                    reason = f"TV Show: {parsed['title']} S{parsed['season']:02d}E{parsed['episode']:02d}"
                    
                elif parsed['type'] == 'movie' and 'year' in parsed:
                    new_path = self._generate_movie_path(parsed, record.extension, new_root)
                    action = 'move'
                    reason = f"Movie: {parsed['title']} ({parsed['year']})"
                    
                else:
                    # Unsorted/unclear
                    new_path = str(new_root / 'unsorted' / record.absolute_path.name)
                    action = 'review'
                    reason = "Unclear media type - manual review needed"
                    jellyfin_issues.append(f"Could not classify: {record.absolute_path.name}")
                
                if confidence < 0.6:
                    action = 'review'
                    reason += " (low confidence - verify before executing)"
                
                folder_changes.append({
                    'current_path': current_path,
                    'proposed_path': new_path,
                    'action': action,
                    'reason': reason,
                    'confidence': confidence
                })
            
            return {
                'summary': f"Regex-based reorganization plan for {len(folder_changes)} files using Jellyfin naming conventions",
                'folder_changes': folder_changes,
                'jellyfin_compliance_issues': jellyfin_issues,
                'new_root': str(new_root)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to generate reorganization plan: {e}", exc_info=True)
            return {
                'summary': f'Failed to generate plan: {e}',
                'folder_changes': [],
                'jellyfin_compliance_issues': [str(e)]
            }
    
    def _generate_tv_path(self, parsed: Dict, ext: str, new_root: Path) -> str:
        """Generate Jellyfin-compliant TV show path."""
        title = parsed['title']
        season = parsed['season']
        episode = parsed['episode']
        
        # Handle multi-part episodes
        if 'episode2' in parsed:
            episode_str = f"s{season:02d}e{episode:02d}-e{parsed['episode2']:02d}"
        else:
            episode_str = f"s{season:02d}e{episode:02d}"
        
        # Add language for subtitles
        lang_str = f".{parsed['language']}" if 'language' in parsed else ''
        
        # Jellyfin format: Show Name/Season XX/Show Name - sXXeYY.ext
        season_str = f"Season {season:02d}"
        filename = f"{title} - {episode_str}{lang_str}{ext}"
        
        return str(new_root / 'TV' / title / season_str / filename)
    
    def _generate_movie_path(self, parsed: Dict, ext: str, new_root: Path) -> str:
        """Generate Jellyfin-compliant movie path."""
        title = parsed['title']
        year = parsed.get('year', '')
        
        # Add language for subtitles
        lang_str = f".{parsed['language']}" if 'language' in parsed else ''
        
        # Jellyfin format: Movie Title (Year)/Movie Title (Year).ext
        if year:
            folder_name = f"{title} ({year})"
            filename = f"{title} ({year}){lang_str}{ext}"
        else:
            folder_name = title
            filename = f"{title}{lang_str}{ext}"
        
        return str(new_root / 'Movies' / folder_name / filename)
    
    def _detect_multi_part_episodes(self, parsed_files: List[Dict]) -> List[Dict]:
        """
        Detect multi-part episodes that need NFO files.
        
        Args:
            parsed_files: List of parsed file info dicts
        
        Returns:
            List of multi-part episode information
        """
        try:
            multi_part = []
            
            for pf in parsed_files:
                parsed = pf['parsed']
                
                # Check if this is a multi-part episode
                if parsed.get('type') == 'tv_show' and 'episode2' in parsed:
                    multi_part.append({
                        'show_title': parsed['title'],
                        'season_number': parsed['season'],
                        'episode_numbers': [parsed['episode'], parsed['episode2']],
                        'combined_episode_title': f"Episode {parsed['episode']}-{parsed['episode2']}",
                        'reason': 'Multi-part episode detected via regex (e.g., s01e01-e02 pattern)',
                        'confidence': 'high' if pf['confidence'] >= 0.8 else 'medium'
                    })
            
            return multi_part
            
        except Exception as e:
            self.logger.error(f"Failed to detect multi-part episodes: {e}", exc_info=True)
            return []
    
    def _generate_reasoning(
        self,
        parsed_files: List[Dict],
        detected_media: List[Dict],
        parse_errors: int
    ) -> str:
        """Generate explanation of analysis process."""
        try:
            total_files = len(parsed_files)
            tv_count = sum(1 for m in detected_media if m['type'] == 'tv_show')
            movie_count = sum(1 for m in detected_media if m['type'] == 'movie')
            
            reasoning = f"""REGEX-BASED ANALYSIS RESULTS:

Total files analyzed: {total_files}
Parse errors: {parse_errors}

DETECTION SUMMARY:
- TV Shows: {tv_count} unique shows detected
- Movies: {movie_count} unique movies detected
- Total media items: {len(detected_media)}

METHODOLOGY:
This analysis used deterministic regex pattern matching to extract:
1. Media titles (cleaned from filenames)
2. Season/Episode numbers (S01E01 format)
3. Years (for movies and show detection)
4. Quality markers (resolution, codec, audio)
5. Multi-part episodes (S01E01-E02 format)
6. Subtitle languages (.en.srt, .en.forced.srt)

CONFIDENCE SCORING:
- HIGH (≥80%): Explicit S01E01 pattern or year in filename
- MEDIUM (60-79%): Title extracted but missing some markers
- LOW (<60%): Ambiguous or incomplete information

JELLYFIN COMPLIANCE:
All proposed paths follow Jellyfin naming conventions:
- Movies: "Title (Year)/Title (Year).ext"
- TV: "Show/Season XX/Show - sXXeYY.ext"
- Multi-part: Flagged for NFO file generation

ADVANTAGES:
✓ Instant results (no API calls)
✓ No cost (completely free)
✓ Deterministic (same input = same output)
✓ Offline capable

LIMITATIONS:
✗ No canonical metadata verification (years/episode titles may be incorrect)
✗ No context understanding (can't disambiguate similar titles)
✗ No Jellyfin cross-reference (doesn't check existing library)

RECOMMENDATION:
Use "Enrich Metadata" button to verify titles/years against TMDB/TVDB after regex analysis.
Or use Hybrid Mode for automatic canonical verification.
"""
            return reasoning
            
        except Exception as e:
            self.logger.error(f"Failed to generate reasoning: {e}", exc_info=True)
            return f"Analysis complete with {len(detected_media)} items detected. Reasoning generation failed: {e}"


def main():
    """CLI entry point for testing."""
    import sys
    from scripts.core.file_scanner import FileScanner
    
    if len(sys.argv) < 2:
        print("Usage: python regex_structure_analyzer.py <folder_path>")
        return
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Scan folder
    folder = Path(sys.argv[1])
    print(f"\n{'='*80}")
    print(f"REGEX STRUCTURE ANALYZER TEST")
    print(f"{'='*80}\n")
    print(f"Scanning: {folder}")
    
    scanner = FileScanner()
    file_records = scanner.scan_folder(folder)
    print(f"Found {len(file_records)} files\n")
    
    # Analyze
    analyzer = RegexStructureAnalyzer()
    result = analyzer.analyze_structure(file_records)
    
    # Display results
    print(f"{'='*80}")
    print("DETECTED MEDIA:")
    print(f"{'='*80}")
    for media in result['detected_media']:
        print(f"  {media['type'].upper()}: {media['title']}")
        if 'year_estimate' in media and media['year_estimate']:
            print(f"    Year: {media['year_estimate']}")
        if 'seasons_detected' in media:
            print(f"    Seasons: {media['seasons_detected']}")
        print(f"    Confidence: {media['confidence']}")
        print()
    
    print(f"{'='*80}")
    print(f"MULTI-PART EPISODES: {len(result['multi_part_episodes'])}")
    print(f"{'='*80}")
    for ep in result['multi_part_episodes']:
        print(f"  {ep['show_title']} S{ep['season_number']:02d}E{ep['episode_numbers']}")
        print(f"    Reason: {ep['reason']}\n")
    
    print(f"{'='*80}")
    print("REASONING:")
    print(f"{'='*80}")
    print(result['reasoning'])


if __name__ == "__main__":
    main()
