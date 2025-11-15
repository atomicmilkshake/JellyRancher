"""
Movie Name Backend - Analyze movie filenames for issues

Identifies:
1. Truncated movie titles (suspiciously short or incomplete)
2. Codec tags in filenames (H.265, x264, etc.)
3. Movies not in proper folder structure
4. Missing year in filename
5. Invalid characters or formatting issues
"""

import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from difflib import SequenceMatcher

# Add paths for imports
current_dir = Path(__file__).parent
scripts_dir = current_dir.parent
sys.path.insert(0, str(scripts_dir))
sys.path.insert(0, str(scripts_dir / "_common"))

from _common.logger import ProjectLogger


class MovieNameAnalyzer:
    """Analyzer for movie filename issues"""
    
    # Supported video extensions
    VIDEO_EXTENSIONS = ['.mkv', '.mp4', '.avi', '.m4v', '.ts']
    
    # Codec patterns to detect
    CODEC_PATTERNS = [
        r'H\.?265', r'H\.?264', r'HEVC', r'x264', r'x265', r'AVC',
        r'10bit', r'8bit', r'HDR', r'DV', r'WEB-?DL', r'BluRay',
        r'1080p', r'720p', r'2160p', r'4K', r'AAC', r'DTS', r'DD5\.?1'
    ]
    
    def __init__(self):
        """Initialize the analyzer"""
        self.logger = ProjectLogger('movie_name_analyzer')
    
    def analyze_movies_folder(self, movies_path: str,
                              progress_callback=None) -> Dict[str, any]:
        """
        Analyze all movies in a folder
        
        Args:
            movies_path: Path to Movies folder
            progress_callback: Optional callback(current, total, message)
        
        Returns:
            Dictionary with analysis results
        """
        movies_dir = Path(movies_path)
        
        if not movies_dir.exists():
            raise ValueError(
                f"Movies folder not found: {movies_path}. "
                "Please check that the folder exists and you have permission to access it."
            )
        
        # Collect all movie files
        movie_files = []
        for ext in self.VIDEO_EXTENSIONS:
            movie_files.extend(movies_dir.rglob(f'*{ext}'))
        
        if not movie_files:
            return {
                'folder': str(movies_dir),
                'total_files': 0,
                'movies': [],
                'summary': {
                    'truncated_titles': 0,
                    'codec_in_name': 0,
                    'not_in_folder': 0,
                    'missing_year': 0,
                    'multiple_issues': 0,
                    'no_issues': 0
                }
            }
        
        # Analyze each movie
        movies = []
        total = len(movie_files)
        
        for i, movie_file in enumerate(sorted(movie_files), 1):
            if progress_callback:
                progress_callback(i, total, f"Analyzing {movie_file.name}...")
            
            movie_info = self.analyze_movie_file(movie_file, movies_dir)
            movies.append(movie_info)
        
        # Generate summary
        summary = {
            'truncated_titles': 0,
            'codec_in_name': 0,
            'not_in_folder': 0,
            'missing_year': 0,
            'multiple_issues': 0,
            'no_issues': 0
        }
        
        for movie in movies:
            issue_count = len(movie['issues'])
            if issue_count == 0:
                summary['no_issues'] += 1
            elif issue_count > 1:
                summary['multiple_issues'] += 1
            
            for issue in movie['issues']:
                issue_type = issue['type']
                if issue_type in summary:
                    summary[issue_type] += 1
        
        return {
            'folder': str(movies_dir),
            'total_files': total,
            'movies': movies,
            'summary': summary
        }
    
    def analyze_movie_file(self, movie_file: Path, base_dir: Path) -> Dict[str, any]:
        """
        Analyze a single movie file
        
        Args:
            movie_file: Path to movie file
            base_dir: Base directory for relative paths
        
        Returns:
            Dictionary with movie info and issues
        """
        try:
            relative_path = movie_file.relative_to(base_dir)
        except ValueError:
            relative_path = movie_file
        
        filename = movie_file.stem
        parent_folder = movie_file.parent.name
        
        # Detect issues
        issues = []
        
        # Check 1: Codec tags in filename
        codec_issue = self.check_codec_tags(filename)
        if codec_issue:
            issues.append(codec_issue)
        
        # Check 2: Truncated titles
        truncated_issue = self.check_truncated_title(filename)
        if truncated_issue:
            issues.append(truncated_issue)
        
        # Check 3: Not in proper folder structure
        folder_issue = self.check_folder_structure(parent_folder, filename)
        if folder_issue:
            issues.append(folder_issue)
        
        # Check 4: Missing year
        year_issue = self.check_missing_year(filename)
        if year_issue:
            issues.append(year_issue)
        
        # Extract title and year if present
        title, year = self.extract_title_and_year(filename)
        
        # Clean filename (remove codec tags)
        cleaned_filename = self.clean_filename(filename)
        
        return {
            'file_path': str(relative_path),
            'filename': filename,
            'parent_folder': parent_folder,
            'title': title,
            'year': year,
            'cleaned_filename': cleaned_filename,
            'issues': issues,
            'needs_fix': len(issues) > 0,
            'extension': movie_file.suffix
        }
    
    def check_codec_tags(self, filename: str) -> Optional[Dict[str, str]]:
        """Check if filename contains codec tags"""
        for pattern in self.CODEC_PATTERNS:
            match = re.search(pattern, filename, re.IGNORECASE)
            if match:
                return {
                    'type': 'codec_in_name',
                    'severity': 'medium',
                    'description': f'Contains codec/quality tag: {match.group()}',
                    'pattern': pattern,
                    'matched_text': match.group()
                }
        return None
    
    def check_truncated_title(self, filename: str) -> Optional[Dict[str, str]]:
        """Check if title appears truncated"""
        # Look for suspiciously short words before year
        # Pattern: word of 1-2 chars followed by year in parentheses
        truncated_pattern = r'\b\w{1,2}\s+\(\d{4}\)'
        match = re.search(truncated_pattern, filename)
        
        if match:
            return {
                'type': 'truncated_titles',
                'severity': 'high',
                'description': 'Title appears truncated (very short word before year)',
                'matched_text': match.group()
            }
        
        # Also check for words ending abruptly (no year)
        # Look for single/double letter words in the middle of the title
        short_words = re.findall(r'\b\w{1,2}\b', filename)
        # Filter out common short words (articles, etc.)
        common_short = {'a', 'an', 'at', 'by', 'in', 'is', 'it', 'of', 'on', 
                       'or', 'to', 'up', 'vs', 'ii', 'iii', 'iv'}
        suspicious_short = [w for w in short_words if w.lower() not in common_short]
        
        if suspicious_short and len(suspicious_short) >= 2:
            return {
                'type': 'truncated_titles',
                'severity': 'medium',
                'description': f'Multiple suspiciously short words: {", ".join(suspicious_short)}',
                'matched_text': ', '.join(suspicious_short)
            }
        
        return None
    
    def check_folder_structure(self, parent_folder: str, 
                              filename: str) -> Optional[Dict[str, str]]:
        """Check if movie is in proper folder structure"""
        # Movies should be in their own folder, not directly in Movies/
        if parent_folder.lower() in ['movies', '#media', 'media']:
            return {
                'type': 'not_in_folder',
                'severity': 'low',
                'description': 'Movie not in dedicated folder (directly in Movies directory)',
                'current_folder': parent_folder
            }
        
        # Check if folder name matches movie name (loosely)
        title_from_file, _ = self.extract_title_and_year(filename)
        similarity = SequenceMatcher(None, 
                                    parent_folder.lower(), 
                                    title_from_file.lower()).ratio()
        
        if similarity < 0.5:
            return {
                'type': 'not_in_folder',
                'severity': 'medium',
                'description': 'Folder name doesn\'t match movie title',
                'current_folder': parent_folder,
                'expected_similarity': 'high',
                'actual_similarity': f'{similarity:.2f}'
            }
        
        return None
    
    def check_missing_year(self, filename: str) -> Optional[Dict[str, str]]:
        """Check if filename is missing year"""
        # Look for year in (YYYY) format
        if not re.search(r'\(\d{4}\)', filename):
            return {
                'type': 'missing_year',
                'severity': 'high',
                'description': 'Missing year in filename (expected format: Title (YYYY))'
            }
        return None
    
    def extract_title_and_year(self, filename: str) -> Tuple[str, Optional[str]]:
        """
        Extract movie title and year from filename
        
        Returns:
            Tuple of (title, year) or (title, None)
        """
        # Try to extract year first
        year_match = re.search(r'\((\d{4})\)', filename)
        year = year_match.group(1) if year_match else None
        
        # Get title (everything before year or codec tags)
        if year_match:
            title = filename[:year_match.start()].strip()
        else:
            # Try to find where codec tags start
            title = filename
            for pattern in self.CODEC_PATTERNS:
                match = re.search(pattern, title, re.IGNORECASE)
                if match:
                    title = title[:match.start()].strip()
                    break
        
        return title, year
    
    def clean_filename(self, filename: str) -> str:
        """
        Remove codec tags and clean up filename
        
        Args:
            filename: Original filename (without extension)
        
        Returns:
            Cleaned filename
        """
        cleaned = filename
        
        # Remove codec patterns
        for pattern in self.CODEC_PATTERNS:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        # Remove common separators and tags
        cleaned = re.sub(r'\[.*?\]', '', cleaned)  # Remove [tags]
        cleaned = re.sub(r'\{.*?\}', '', cleaned)  # Remove {tags}
        
        # Clean up spaces
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        # Remove trailing dashes/underscores
        cleaned = re.sub(r'[-_]+$', '', cleaned).strip()
        
        return cleaned
    
    def suggest_fix(self, movie_info: Dict[str, any]) -> Dict[str, any]:
        """
        Suggest a fix for movie naming issues
        
        Args:
            movie_info: Movie information from analyze_movie_file
        
        Returns:
            Dictionary with fix suggestions
        """
        suggestions = []
        
        for issue in movie_info['issues']:
            issue_type = issue['type']
            
            if issue_type == 'codec_in_name':
                # Suggest cleaned filename
                cleaned = movie_info['cleaned_filename']
                if movie_info['year']:
                    suggested = f"{cleaned} ({movie_info['year']})"
                else:
                    suggested = cleaned
                
                suggestions.append({
                    'issue_type': issue_type,
                    'action': 'remove_codec_tags',
                    'current_filename': movie_info['filename'],
                    'suggested_filename': suggested,
                    'auto_fixable': True
                })
            
            elif issue_type == 'truncated_titles':
                suggestions.append({
                    'issue_type': issue_type,
                    'action': 'manual_review',
                    'current_filename': movie_info['filename'],
                    'suggested_filename': None,
                    'auto_fixable': False,
                    'note': 'Requires manual title lookup and correction'
                })
            
            elif issue_type == 'not_in_folder':
                # Suggest proper folder structure
                title = movie_info['title']
                year = movie_info['year']
                if year:
                    folder_name = f"{title} ({year})"
                else:
                    folder_name = title
                
                suggestions.append({
                    'issue_type': issue_type,
                    'action': 'create_folder',
                    'current_folder': movie_info['parent_folder'],
                    'suggested_folder': folder_name,
                    'auto_fixable': True
                })
            
            elif issue_type == 'missing_year':
                suggestions.append({
                    'issue_type': issue_type,
                    'action': 'add_year',
                    'current_filename': movie_info['filename'],
                    'suggested_filename': None,
                    'auto_fixable': False,
                    'note': 'Requires year lookup (TMDB/IMDB)'
                })
        
        return {
            'movie': movie_info['filename'],
            'suggestions': suggestions,
            'can_auto_fix': any(s['auto_fixable'] for s in suggestions),
            'requires_manual': any(not s['auto_fixable'] for s in suggestions)
        }
