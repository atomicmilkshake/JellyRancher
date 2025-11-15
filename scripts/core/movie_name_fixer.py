"""
Movie Name Fixer - Fix movie filename issues

Provides safe file/folder renaming operations:
1. Remove codec tags from filenames
2. Create proper folder structure
3. Handle truncated titles (manual input)
4. Ensure Jellyfin naming format
"""

import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Callable

# Add paths for imports
current_dir = Path(__file__).parent
scripts_dir = current_dir.parent
sys.path.insert(0, str(scripts_dir))
sys.path.insert(0, str(scripts_dir / "_common"))

from _common.logger import ProjectLogger
from _common.immutable_audit import ImmutableAuditLog


class MovieNameFixer:
    """Fixer for movie naming issues"""
    
    def __init__(self):
        """Initialize the fixer"""
        self.logger = ProjectLogger('movie_name_fixer')
        try:
            self.audit = ImmutableAuditLog()
        except:
            self.audit = None
            self.logger.warning("Audit log not available")
    
    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename for filesystem safety
        
        Args:
            filename: Original filename
        
        Returns:
            Safe filename
        """
        # Remove invalid characters (Windows + Unix)
        invalid_chars = r'<>:"/\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '')
        
        # Remove control characters
        filename = ''.join(char for char in filename if ord(char) >= 32)
        
        # Limit length (200 chars for display, 255 OS limit)
        if len(filename) > 200:
            filename = filename[:200].rstrip()
        
        return filename.strip()
    
    def remove_codec_tags(self, filename: str) -> str:
        """
        Remove codec and quality tags from filename
        
        Args:
            filename: Original filename (without extension)
        
        Returns:
            Cleaned filename
        """
        cleaned = filename
        
        # Codec patterns to remove
        patterns = [
            r'\s*H\.?265\s*', r'\s*H\.?264\s*', r'\s*HEVC\s*',
            r'\s*x264\s*', r'\s*x265\s*', r'\s*AVC\s*',
            r'\s*10bit\s*', r'\s*8bit\s*', r'\s*HDR\s*',
            r'\s*DV\s*', r'\s*WEB-?DL\s*', r'\s*BluRay\s*',
            r'\s*1080p\s*', r'\s*720p\s*', r'\s*2160p\s*',
            r'\s*4K\s*', r'\s*AAC\s*', r'\s*DTS\s*',
            r'\s*DD5\.?1\s*', r'\s*Atmos\s*'
        ]
        
        for pattern in patterns:
            cleaned = re.sub(pattern, ' ', cleaned, flags=re.IGNORECASE)
        
        # Remove common tags in brackets/braces
        cleaned = re.sub(r'\[.*?\]', '', cleaned)
        cleaned = re.sub(r'\{.*?\}', '', cleaned)
        
        # Clean up multiple spaces
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        # Remove trailing dashes/underscores
        cleaned = re.sub(r'[-_]+$', '', cleaned).strip()
        
        return cleaned
    
    def construct_new_filename(self, title: str, year: Optional[str], 
                              extension: str) -> str:
        """
        Construct Jellyfin-compliant filename
        
        Args:
            title: Movie title
            year: Release year (optional)
            extension: File extension (with dot)
        
        Returns:
            New filename
        """
        # Sanitize title
        clean_title = self.sanitize_filename(title)
        
        # Build filename
        if year:
            filename = f"{clean_title} ({year}){extension}"
        else:
            filename = f"{clean_title}{extension}"
        
        return filename
    
    def validate_rename_operation(self, old_path: Path, 
                                  new_path: Path) -> Tuple[bool, Optional[str]]:
        """
        Validate that rename operation is safe
        
        Args:
            old_path: Current file path
            new_path: Proposed new path
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check source exists
        if not old_path.exists():
            return False, f"Source file not found: {old_path}"
        
        # Check source is a file
        if not old_path.is_file():
            return False, f"Source is not a file: {old_path}"
        
        # Check target doesn't exist
        if new_path.exists():
            return False, f"Target already exists: {new_path.name}"
        
        # Check parent directory exists
        if not new_path.parent.exists():
            # Will need to create it
            pass
        
        # Check parent is writable
        try:
            if new_path.parent.exists():
                # Test write permission
                test_file = new_path.parent / '.test_write'
                test_file.touch()
                test_file.unlink()
        except (PermissionError, OSError) as e:
            return False, f"Directory not writable: {str(e)}"
        
        # Check filename length
        if len(new_path.name) > 255:
            return False, f"Filename too long: {len(new_path.name)} chars (max 255)"
        
        return True, None
    
    def fix_codec_tags(self, movie_info: Dict[str, any],
                      base_dir: Path,
                      dry_run: bool = True) -> Dict[str, any]:
        """
        Fix codec tags in movie filename
        
        Args:
            movie_info: Movie information dictionary
            base_dir: Base directory for relative paths
            dry_run: If True, don't actually rename
        
        Returns:
            Result dictionary
        """
        old_path = base_dir / movie_info['file_path']
        
        # Generate new filename
        title = movie_info['title']
        year = movie_info['year']
        extension = movie_info['extension']
        
        # Remove codec tags from title
        clean_title = self.remove_codec_tags(title)
        
        # If no change, skip
        if clean_title == title:
            return {
                'success': True,
                'skipped': True,
                'reason': 'No codec tags found',
                'old_path': str(old_path),
                'new_path': str(old_path)
            }
        
        new_filename = self.construct_new_filename(clean_title, year, extension)
        new_path = old_path.parent / new_filename
        
        # Validate
        valid, error = self.validate_rename_operation(old_path, new_path)
        if not valid:
            return {
                'success': False,
                'error': error,
                'old_path': str(old_path),
                'new_path': str(new_path)
            }
        
        if dry_run:
            return {
                'success': True,
                'dry_run': True,
                'old_path': str(old_path),
                'new_path': str(new_path),
                'old_filename': old_path.name,
                'new_filename': new_filename
            }
        
        # Perform rename
        try:
            old_path.rename(new_path)
            
            # Log to audit
            if self.audit:
                self.audit.log_event('movie_rename_codec', {
                    'old_path': str(old_path),
                    'new_path': str(new_path),
                    'old_filename': old_path.name,
                    'new_filename': new_filename
                })
            
            return {
                'success': True,
                'old_path': str(old_path),
                'new_path': str(new_path),
                'old_filename': old_path.name,
                'new_filename': new_filename
            }
        
        except Exception as e:
            self.logger.error(f"Rename error: {e}")
            return {
                'success': False,
                'error': str(e),
                'old_path': str(old_path),
                'new_path': str(new_path)
            }
    
    def create_proper_folder(self, movie_info: Dict[str, any],
                            base_dir: Path,
                            dry_run: bool = True) -> Dict[str, any]:
        """
        Move movie to proper folder structure
        
        Args:
            movie_info: Movie information dictionary
            base_dir: Base directory (Movies folder)
            dry_run: If True, don't actually move
        
        Returns:
            Result dictionary
        """
        old_path = base_dir / movie_info['file_path']
        
        # Generate proper folder name
        title = movie_info['title']
        year = movie_info['year']
        
        if year:
            folder_name = f"{title} ({year})"
        else:
            folder_name = title
        
        folder_name = self.sanitize_filename(folder_name)
        
        # Create target paths
        new_folder = base_dir / folder_name
        new_filename = self.construct_new_filename(title, year, movie_info['extension'])
        new_path = new_folder / new_filename
        
        # Validate
        valid, error = self.validate_rename_operation(old_path, new_path)
        if not valid:
            return {
                'success': False,
                'error': error,
                'old_path': str(old_path),
                'new_path': str(new_path)
            }
        
        if dry_run:
            return {
                'success': True,
                'dry_run': True,
                'old_path': str(old_path),
                'new_path': str(new_path),
                'folder_created': folder_name,
                'action': 'move_to_folder'
            }
        
        # Perform move
        try:
            # Create folder if needed
            new_folder.mkdir(exist_ok=True, parents=True)
            
            # Move file
            old_path.rename(new_path)
            
            # Try to remove old folder if empty
            try:
                if old_path.parent != base_dir and not any(old_path.parent.iterdir()):
                    old_path.parent.rmdir()
            except:
                pass  # Not critical if we can't remove
            
            # Log to audit
            if self.audit:
                self.audit.log_event('movie_move_folder', {
                    'old_path': str(old_path),
                    'new_path': str(new_path),
                    'folder_created': folder_name
                })
            
            return {
                'success': True,
                'old_path': str(old_path),
                'new_path': str(new_path),
                'folder_created': folder_name,
                'action': 'move_to_folder'
            }
        
        except Exception as e:
            self.logger.error(f"Move error: {e}")
            return {
                'success': False,
                'error': str(e),
                'old_path': str(old_path),
                'new_path': str(new_path)
            }
    
    def apply_fixes(self, movies: List[Dict[str, any]],
                   base_dir: Path,
                   fix_types: List[str],
                   dry_run: bool = True,
                   progress_callback: Optional[Callable] = None) -> Dict[str, any]:
        """
        Apply fixes to multiple movies
        
        Args:
            movies: List of movie information dictionaries
            base_dir: Base directory for operations
            fix_types: List of fix types to apply ('codec', 'folder', etc.)
            dry_run: If True, preview only
            progress_callback: Optional callback(current, total, message)
        
        Returns:
            Results dictionary with operation summary
        """
        results = {
            'total': len(movies),
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'operations': []
        }
        
        for i, movie in enumerate(movies, 1):
            if progress_callback:
                progress_callback(i, len(movies), 
                                f"Processing {movie['filename']}...")
            
            # Determine which fixes to apply
            movie_results = []
            
            # Fix codec tags
            if 'codec' in fix_types:
                has_codec = any(issue['type'] == 'codec_in_name' 
                              for issue in movie['issues'])
                if has_codec:
                    result = self.fix_codec_tags(movie, base_dir, dry_run)
                    movie_results.append(result)
            
            # Fix folder structure
            if 'folder' in fix_types:
                has_folder_issue = any(issue['type'] == 'not_in_folder' 
                                      for issue in movie['issues'])
                if has_folder_issue:
                    result = self.create_proper_folder(movie, base_dir, dry_run)
                    movie_results.append(result)
            
            # Track results
            for result in movie_results:
                if result.get('skipped'):
                    results['skipped'] += 1
                elif result['success']:
                    results['successful'] += 1
                else:
                    results['failed'] += 1
                
                results['operations'].append({
                    'movie': movie['filename'],
                    **result
                })
        
        return results
