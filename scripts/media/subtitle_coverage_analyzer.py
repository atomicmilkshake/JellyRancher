#!/usr/bin/env python3
"""
Subtitle Coverage Analyzer - Step 8

Evaluates subtitle coverage across media library by:
- Detecting embedded subtitles using ffprobe
- Finding external subtitle files (.srt, .sub, .vtt, .ass, .ssa)
- Generating comprehensive report of missing subtitles
- Organizing results by movies vs TV shows

Features:
- FFprobe integration for embedded subtitle detection
- Language detection (embedded and external)
- Coverage statistics and percentages
- Missing subtitle list generation
- Export to JSON/CSV for review
"""

import json
import subprocess
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
from collections import defaultdict


logger = logging.getLogger(__name__)


# Video and subtitle extensions
VIDEO_EXTENSIONS = {'.mkv', '.mp4', '.avi', '.m4v', '.mov', '.wmv', '.flv', '.webm', '.mpg', '.mpeg', '.ts', '.m2ts', '.vob'}
SUBTITLE_EXTENSIONS = {'.srt', '.sub', '.vtt', '.ass', '.ssa', '.idx'}


@dataclass
class SubtitleInfo:
    """Information about a subtitle track."""
    type: str  # 'embedded' or 'external'
    language: str
    codec: Optional[str] = None  # For embedded
    forced: bool = False
    default: bool = False
    file_path: Optional[str] = None  # For external
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class MediaFileInfo:
    """Information about a media file and its subtitles."""
    file_path: str
    media_type: str  # 'movie' or 'tv_show'
    size_bytes: int
    has_subtitles: bool
    embedded_subtitles: List[SubtitleInfo]
    external_subtitles: List[SubtitleInfo]
    
    # For TV shows
    show_name: Optional[str] = None
    season: Optional[int] = None
    episode: Optional[int] = None
    
    # For movies
    title: Optional[str] = None
    year: Optional[int] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        data = asdict(self)
        data['embedded_subtitles'] = [s.to_dict() for s in self.embedded_subtitles]
        data['external_subtitles'] = [s.to_dict() for s in self.external_subtitles]
        return data


class SubtitleCoverageAnalyzer:
    """
    Analyzes subtitle coverage across media library.
    """
    
    def __init__(self, output_dir: str = "data/subtitle_coverage"):
        """
        Initialize analyzer.
        
        Args:
            output_dir: Directory to save coverage reports
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.ffprobe_available = self._check_ffprobe_available()
        if not self.ffprobe_available:
            logger.warning("ffprobe not available - embedded subtitle detection disabled")
        
        self.media_files: List[MediaFileInfo] = []
        self.missing_subtitles: List[MediaFileInfo] = []
        
        logger.info(f"Initialized SubtitleCoverageAnalyzer (ffprobe: {self.ffprobe_available})")
    
    def _check_ffprobe_available(self) -> bool:
        """Check if ffprobe is available in system PATH."""
        try:
            result = subprocess.run(
                ['ffprobe', '-version'],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def _get_embedded_subtitles(self, video_path: Path) -> List[SubtitleInfo]:
        """
        Extract embedded subtitle information using ffprobe.
        
        Args:
            video_path: Path to video file
        
        Returns:
            List of SubtitleInfo objects for embedded subtitles
        """
        if not self.ffprobe_available:
            return []
        
        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_streams',
                '-select_streams', 's',
                str(video_path)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return []
            
            data = json.loads(result.stdout)
            subtitles = []
            
            for stream in data.get('streams', []):
                if stream.get('codec_type') == 'subtitle':
                    language = stream.get('tags', {}).get('language', 'und')
                    codec = stream.get('codec_name', 'unknown')
                    forced = stream.get('disposition', {}).get('forced', 0) == 1
                    default = stream.get('disposition', {}).get('default', 0) == 1
                    
                    subtitle = SubtitleInfo(
                        type='embedded',
                        language=language,
                        codec=codec,
                        forced=forced,
                        default=default
                    )
                    subtitles.append(subtitle)
            
            return subtitles
        
        except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception) as e:
            logger.warning(f"Error scanning embedded subtitles for {video_path.name}: {e}")
            return []
    
    def _get_external_subtitles(self, video_path: Path) -> List[SubtitleInfo]:
        """
        Find external subtitle files matching the video.
        
        Args:
            video_path: Path to video file
        
        Returns:
            List of SubtitleInfo objects for external subtitles
        """
        video_stem = video_path.stem
        video_dir = video_path.parent
        
        subtitles = []
        
        # Look for subtitle files with same base name
        for sub_ext in SUBTITLE_EXTENSIONS:
            # Exact match (Video.srt)
            exact_match = video_dir / f"{video_stem}{sub_ext}"
            if exact_match.exists():
                subtitle = SubtitleInfo(
                    type='external',
                    language='unknown',  # Would need to parse filename
                    file_path=str(exact_match)
                )
                subtitles.append(subtitle)
            
            # Language variants (Video.en.srt, Video.eng.srt, etc.)
            for sub_file in video_dir.glob(f"{video_stem}.*{sub_ext}"):
                if sub_file != exact_match:
                    # Try to extract language from filename
                    parts = sub_file.stem.split('.')
                    language = 'unknown'
                    if len(parts) > 1:
                        # Last part before extension might be language
                        lang_part = parts[-1].lower()
                        if lang_part in ['en', 'eng', 'english']:
                            language = 'eng'
                        elif lang_part in ['es', 'spa', 'spanish']:
                            language = 'spa'
                        elif lang_part in ['fr', 'fre', 'french']:
                            language = 'fra'
                        elif lang_part in ['de', 'ger', 'german']:
                            language = 'deu'
                        elif lang_part in ['pt', 'por', 'portuguese']:
                            language = 'por'
                        elif 'forced' not in lang_part and 'sdh' not in lang_part:
                            language = lang_part
                    
                    subtitle = SubtitleInfo(
                        type='external',
                        language=language,
                        file_path=str(sub_file)
                    )
                    subtitles.append(subtitle)
        
        return subtitles
    
    def _detect_media_type(self, file_path: Path) -> Tuple[str, Dict]:
        """
        Detect if file is a movie or TV show and extract metadata.
        
        Args:
            file_path: Path to media file
        
        Returns:
            Tuple of (media_type, metadata_dict)
        """
        # Simple heuristic based on path and filename
        path_str = str(file_path).lower()
        
        # Check for season/episode patterns
        import re
        
        # Match patterns like S01E01, s01e01, 1x01, etc.
        season_episode_patterns = [
            r's(\d+)e(\d+)',  # S01E01
            r'season\s*(\d+).*episode\s*(\d+)',  # Season 1 Episode 1
            r'(\d+)x(\d+)',  # 1x01
        ]
        
        for pattern in season_episode_patterns:
            match = re.search(pattern, path_str)
            if match:
                season = int(match.group(1))
                episode = int(match.group(2))
                
                # Extract show name (usually parent folder or part of filename)
                if 'season' in path_str or file_path.parent.name.lower().startswith('season'):
                    # Show name is likely grandparent folder
                    show_name = file_path.parent.parent.name
                else:
                    # Show name is likely parent folder
                    show_name = file_path.parent.name
                
                return ('tv_show', {
                    'show_name': show_name,
                    'season': season,
                    'episode': episode
                })
        
        # If no episode pattern found, assume it's a movie
        # Try to extract title and year
        title = file_path.stem
        year = None
        
        # Look for year pattern (1900-2099)
        year_match = re.search(r'\(?(19\d{2}|20\d{2})\)?', title)
        if year_match:
            year = int(year_match.group(1))
            title = title[:year_match.start()].strip()
        
        return ('movie', {
            'title': title,
            'year': year
        })
    
    def analyze_folder(
        self,
        folder_path: str,
        recursive: bool = True,
        language_filter: Optional[str] = None
    ) -> Dict:
        """
        Analyze subtitle coverage in a folder.
        
        Args:
            folder_path: Path to folder to analyze
            recursive: Whether to scan subdirectories
            language_filter: Optional language code to filter (e.g., 'eng')
        
        Returns:
            Dict with analysis results
        """
        logger.info(f"Analyzing subtitle coverage in: {folder_path}")
        
        folder = Path(folder_path)
        if not folder.exists():
            raise ValueError(f"Folder not found: {folder_path}")
        
        self.media_files = []
        self.missing_subtitles = []
        
        # Find all video files
        video_files = []
        if recursive:
            for ext in VIDEO_EXTENSIONS:
                video_files.extend(folder.rglob(f"*{ext}"))
        else:
            for ext in VIDEO_EXTENSIONS:
                video_files.extend(folder.glob(f"*{ext}"))
        
        logger.info(f"Found {len(video_files)} video files")
        
        # Analyze each video file
        for i, video_path in enumerate(video_files):
            if (i + 1) % 50 == 0:
                logger.info(f"Progress: {i + 1}/{len(video_files)} files analyzed")
            
            try:
                # Get subtitle information
                embedded_subs = self._get_embedded_subtitles(video_path)
                external_subs = self._get_external_subtitles(video_path)
                
                # Filter by language if specified
                if language_filter:
                    embedded_subs = [s for s in embedded_subs if language_filter.lower() in s.language.lower()]
                    external_subs = [s for s in external_subs if language_filter.lower() in s.language.lower()]
                
                has_subtitles = bool(embedded_subs or external_subs)
                
                # Detect media type
                media_type, metadata = self._detect_media_type(video_path)
                
                # Create MediaFileInfo
                file_info = MediaFileInfo(
                    file_path=str(video_path),
                    media_type=media_type,
                    size_bytes=video_path.stat().st_size,
                    has_subtitles=has_subtitles,
                    embedded_subtitles=embedded_subs,
                    external_subtitles=external_subs,
                    **metadata
                )
                
                self.media_files.append(file_info)
                
                if not has_subtitles:
                    self.missing_subtitles.append(file_info)
            
            except Exception as e:
                logger.error(f"Error analyzing {video_path}: {e}")
        
        logger.info(f"Analysis complete: {len(self.media_files)} files, {len(self.missing_subtitles)} missing subtitles")
        
        return self.get_statistics()
    
    def get_statistics(self) -> Dict:
        """Get coverage statistics."""
        total = len(self.media_files)
        with_subs = sum(1 for f in self.media_files if f.has_subtitles)
        without_subs = total - with_subs
        
        movies = [f for f in self.media_files if f.media_type == 'movie']
        tv_shows = [f for f in self.media_files if f.media_type == 'tv_show']
        
        movies_with_subs = sum(1 for f in movies if f.has_subtitles)
        tv_shows_with_subs = sum(1 for f in tv_shows if f.has_subtitles)
        
        embedded_count = sum(1 for f in self.media_files if f.embedded_subtitles)
        external_count = sum(1 for f in self.media_files if f.external_subtitles)
        
        return {
            'total_files': total,
            'with_subtitles': with_subs,
            'without_subtitles': without_subs,
            'coverage_percent': (with_subs / total * 100) if total > 0 else 0,
            'movies': {
                'total': len(movies),
                'with_subtitles': movies_with_subs,
                'without_subtitles': len(movies) - movies_with_subs,
                'coverage_percent': (movies_with_subs / len(movies) * 100) if movies else 0
            },
            'tv_shows': {
                'total': len(tv_shows),
                'with_subtitles': tv_shows_with_subs,
                'without_subtitles': len(tv_shows) - tv_shows_with_subs,
                'coverage_percent': (tv_shows_with_subs / len(tv_shows) * 100) if tv_shows else 0
            },
            'subtitle_types': {
                'embedded_only': embedded_count - external_count,
                'external_only': external_count - embedded_count,
                'both': min(embedded_count, external_count)
            }
        }
    
    def get_missing_subtitles_list(self) -> List[Dict]:
        """Get list of files missing subtitles."""
        return [f.to_dict() for f in self.missing_subtitles]
    
    def save_report(self, filename: Optional[str] = None) -> str:
        """
        Save coverage report to JSON file.
        
        Args:
            filename: Optional filename (default: timestamp-based)
        
        Returns:
            Path to saved file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"subtitle_coverage_{timestamp}.json"
        
        output_path = self.output_dir / filename
        
        report_data = {
            'generated': datetime.now().isoformat(),
            'ffprobe_available': self.ffprobe_available,
            'statistics': self.get_statistics(),
            'all_files': [f.to_dict() for f in self.media_files],
            'missing_subtitles': self.get_missing_subtitles_list()
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved coverage report to: {output_path}")
        return str(output_path)
    
    def export_missing_to_csv(self, filename: Optional[str] = None) -> str:
        """
        Export missing subtitles list to CSV.
        
        Args:
            filename: Optional filename (default: timestamp-based)
        
        Returns:
            Path to saved CSV file
        """
        import csv
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"missing_subtitles_{timestamp}.csv"
        
        output_path = self.output_dir / filename
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'File Path', 'Media Type', 'Title/Show', 'Season', 'Episode', 'Size MB'
            ])
            
            for file_info in self.missing_subtitles:
                size_mb = file_info.size_bytes / (1024 * 1024)
                
                if file_info.media_type == 'movie':
                    title = f"{file_info.title} ({file_info.year})" if file_info.year else file_info.title
                    season = ''
                    episode = ''
                else:
                    title = file_info.show_name or 'Unknown'
                    season = file_info.season or ''
                    episode = file_info.episode or ''
                
                writer.writerow([
                    file_info.file_path,
                    file_info.media_type,
                    title,
                    season,
                    episode,
                    f"{size_mb:.2f}"
                ])
        
        logger.info(f"Exported missing subtitles to CSV: {output_path}")
        return str(output_path)
    
    def generate_download_queue(self) -> List[Dict]:
        """
        Generate download queue for files missing subtitles.
        
        Returns:
            List of dicts with file info ready for subtitle downloader
        """
        queue = []
        
        for file_info in self.missing_subtitles:
            item = {
                'file_path': file_info.file_path,
                'media_type': file_info.media_type
            }
            
            if file_info.media_type == 'movie':
                item['title'] = file_info.title
                item['year'] = file_info.year
            else:
                item['show_name'] = file_info.show_name
                item['season'] = file_info.season
                item['episode'] = file_info.episode
            
            queue.append(item)
        
        return queue


def main():
    """CLI interface for testing."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze subtitle coverage')
    parser.add_argument('folder', help='Folder to analyze')
    parser.add_argument('--language', help='Filter by language code (e.g., eng)')
    parser.add_argument('--no-recursive', action='store_true', help='Don\'t scan subdirectories')
    parser.add_argument('--output', default='data/subtitle_coverage', help='Output directory')
    parser.add_argument('--export-csv', action='store_true', help='Export missing list to CSV')
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create analyzer
    analyzer = SubtitleCoverageAnalyzer(output_dir=args.output)
    
    # Analyze folder
    stats = analyzer.analyze_folder(
        folder_path=args.folder,
        recursive=not args.no_recursive,
        language_filter=args.language
    )
    
    # Display statistics
    print("\n" + "=" * 60)
    print("SUBTITLE COVERAGE ANALYSIS")
    print("=" * 60)
    print(f"Total files: {stats['total_files']}")
    print(f"With subtitles: {stats['with_subtitles']} ({stats['coverage_percent']:.1f}%)")
    print(f"Without subtitles: {stats['without_subtitles']}")
    print()
    print(f"Movies: {stats['movies']['total']} files")
    print(f"  With subs: {stats['movies']['with_subtitles']} ({stats['movies']['coverage_percent']:.1f}%)")
    print(f"  Without subs: {stats['movies']['without_subtitles']}")
    print()
    print(f"TV Shows: {stats['tv_shows']['total']} files")
    print(f"  With subs: {stats['tv_shows']['with_subtitles']} ({stats['tv_shows']['coverage_percent']:.1f}%)")
    print(f"  Without subs: {stats['tv_shows']['without_subtitles']}")
    print()
    print("Subtitle Types:")
    print(f"  Embedded only: {stats['subtitle_types']['embedded_only']}")
    print(f"  External only: {stats['subtitle_types']['external_only']}")
    print(f"  Both: {stats['subtitle_types']['both']}")
    
    # Save report
    report_path = analyzer.save_report()
    print(f"\nReport saved: {report_path}")
    
    # Export CSV if requested
    if args.export_csv:
        csv_path = analyzer.export_missing_to_csv()
        print(f"Missing subtitles CSV: {csv_path}")
    
    # Show sample of missing files
    missing = analyzer.get_missing_subtitles_list()
    if missing:
        print(f"\nSample of files missing subtitles ({min(10, len(missing))} of {len(missing)}):")
        for item in missing[:10]:
            path = Path(item['file_path'])
            print(f"  - {path.name}")


if __name__ == '__main__':
    main()
