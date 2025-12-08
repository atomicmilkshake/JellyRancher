#!/usr/bin/env python3
"""
Jellyfin Library Validator - Enhanced Validation Module

Provides comprehensive validation of Jellyfin library entries including:
- File existence and validity
- Metadata completeness
- Quality analysis
- Subtitle coverage
- Duplicate content detection
- Orphan detection (files on disk not in Jellyfin)
"""

import logging
from pathlib import Path
from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass
from collections import defaultdict

from scripts.core.jellyfin_client import JellyfinClient
from scripts.core.file_scanner import FileScanner
from scripts.utils.transaction_manager import FileHasher

logger = logging.getLogger(__name__)

# Valid video extensions
VIDEO_EXTENSIONS = FileScanner.DEFAULT_VIDEO_EXTENSIONS


@dataclass
class ValidationIssue:
    """Represents a validation issue found for an item."""
    severity: str  # 'critical', 'warning', 'info'
    category: str  # 'file', 'metadata', 'quality', 'subtitle', 'duplicate'
    message: str
    item_id: str
    item_title: str


@dataclass
class ValidationResult:
    """Result of validating a single Jellyfin item."""
    item: Dict
    jellyfin_id: str
    title: str
    jellyfin_path: str
    valid: bool
    issues: List[ValidationIssue]
    file_size: Optional[int] = None
    actual_path: Optional[str] = None
    resolution: Optional[str] = None
    codec: Optional[str] = None
    has_subtitles: bool = False
    subtitle_languages: List[str] = None
    
    def __post_init__(self):
        if self.subtitle_languages is None:
            self.subtitle_languages = []
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON output."""
        return {
            'jellyfin_id': self.jellyfin_id,
            'title': self.title,
            'jellyfin_path': self.jellyfin_path,
            'valid': self.valid,
            'issues': [{'severity': issue.severity, 'category': issue.category, 'message': issue.message} 
                       for issue in self.issues],
            'file_size': self.file_size,
            'actual_path': self.actual_path,
            'resolution': self.resolution,
            'codec': self.codec,
            'has_subtitles': self.has_subtitles,
            'subtitle_languages': self.subtitle_languages
        }


class JellyfinValidator:
    """
    Enhanced validator for Jellyfin library entries.
    
    Provides comprehensive validation including file checks, metadata,
    quality analysis, subtitle coverage, and duplicate detection.
    """
    
    def __init__(self, jellyfin_client: JellyfinClient):
        """
        Initialize validator.
        
        Args:
            jellyfin_client: JellyfinClient instance for API access
        """
        self.client = jellyfin_client
        self.hasher = FileHasher()
        logger.info("JellyfinValidator initialized")
    
    def validate_item(self, item: Dict, check_metadata: bool = True, 
                     check_quality: bool = True, check_subtitles: bool = True) -> ValidationResult:
        """
        Validate a single Jellyfin item.
        
        Args:
            item: Jellyfin item dictionary
            check_metadata: Whether to validate metadata
            check_quality: Whether to analyze quality
            check_subtitles: Whether to check subtitle coverage
            
        Returns:
            ValidationResult with validation status and issues
        """
        result = ValidationResult(
            item=item,
            jellyfin_id=item.get('Id', 'N/A'),
            title=item.get('Name', 'N/A'),
            jellyfin_path=item.get('Path', ''),
            valid=True,
            issues=[]
        )
        
        # File validation (always performed)
        self._validate_file(result)
        
        # Metadata validation
        if check_metadata:
            self._validate_metadata(result)
        
        # Quality analysis
        if check_quality and result.valid:
            self._analyze_quality(result)
        
        # Subtitle coverage
        if check_subtitles:
            self._check_subtitles(result)
        
        # Update valid status based on issues
        if any(issue.severity == 'critical' for issue in result.issues):
            result.valid = False
        
        return result
    
    def _validate_file(self, result: ValidationResult):
        """Validate file existence and basic properties."""
        jellyfin_path = result.jellyfin_path
        if not jellyfin_path:
            result.issues.append(ValidationIssue(
                severity='critical',
                category='file',
                message='No path in Jellyfin metadata',
                item_id=result.jellyfin_id,
                item_title=result.title
            ))
            result.valid = False
            return
        
        try:
            path = Path(jellyfin_path)
            if not path.exists():
                result.issues.append(ValidationIssue(
                    severity='critical',
                    category='file',
                    message='File does not exist on filesystem',
                    item_id=result.jellyfin_id,
                    item_title=result.title
                ))
                result.valid = False
                return
            
            resolved = path.resolve()
            result.actual_path = str(resolved)
            
            if resolved.is_dir():
                result.issues.append(ValidationIssue(
                    severity='critical',
                    category='file',
                    message='Path is a directory, not a file',
                    item_id=result.jellyfin_id,
                    item_title=result.title
                ))
                result.valid = False
                return
            
            if not resolved.is_file():
                result.issues.append(ValidationIssue(
                    severity='critical',
                    category='file',
                    message='Path exists but is not a file',
                    item_id=result.jellyfin_id,
                    item_title=result.title
                ))
                result.valid = False
                return
            
            # Check extension
            extension = resolved.suffix.lower()
            if extension not in VIDEO_EXTENSIONS:
                valid_exts = ", ".join(sorted(VIDEO_EXTENSIONS))
                result.issues.append(ValidationIssue(
                    severity='warning',
                    category='file',
                    message=f'Invalid video extension: {extension} (valid: {valid_exts})',
                    item_id=result.jellyfin_id,
                    item_title=result.title
                ))
            
            # Check readability
            try:
                stat = resolved.stat()
                result.file_size = stat.st_size
                with open(resolved, 'rb') as f:
                    f.read(1)  # Try reading first byte
            except PermissionError:
                result.issues.append(ValidationIssue(
                    severity='critical',
                    category='file',
                    message='File exists but is not readable (permission denied)',
                    item_id=result.jellyfin_id,
                    item_title=result.title
                ))
                result.valid = False
            except (OSError, IOError) as e:
                result.issues.append(ValidationIssue(
                    severity='critical',
                    category='file',
                    message=f'File exists but cannot be read: {str(e)}',
                    item_id=result.jellyfin_id,
                    item_title=result.title
                ))
                result.valid = False
                
        except (OSError, ValueError) as e:
            result.issues.append(ValidationIssue(
                severity='critical',
                category='file',
                message=f'Error validating file: {str(e)}',
                item_id=result.jellyfin_id,
                item_title=result.title
            ))
            result.valid = False
    
    def _validate_metadata(self, result: ValidationResult):
        """Validate metadata completeness."""
        item = result.item
        
        # Check ProviderIds
        provider_ids = item.get('ProviderIds', {})
        if not provider_ids:
            result.issues.append(ValidationIssue(
                severity='warning',
                category='metadata',
                message='Missing ProviderIds (TMDb, TVDb, IMDb)',
                item_id=result.jellyfin_id,
                item_title=result.title
            ))
        else:
            # Check for common providers
            has_tmdb = 'Tmdb' in provider_ids
            has_tvdb = 'Tvdb' in provider_ids
            has_imdb = 'Imdb' in provider_ids
            
            if not (has_tmdb or has_tvdb or has_imdb):
                result.issues.append(ValidationIssue(
                    severity='warning',
                    category='metadata',
                    message='Missing common ProviderIds (TMDb, TVDb, or IMDb)',
                    item_id=result.jellyfin_id,
                    item_title=result.title
                ))
        
        # Check for production year
        if not item.get('ProductionYear'):
            result.issues.append(ValidationIssue(
                severity='info',
                category='metadata',
                message='Missing production year',
                item_id=result.jellyfin_id,
                item_title=result.title
            ))
        
        # Check for genres
        genres = item.get('Genres', [])
        if not genres:
            result.issues.append(ValidationIssue(
                severity='info',
                category='metadata',
                message='Missing genre information',
                item_id=result.jellyfin_id,
                item_title=result.title
            ))
        
        # Check for overview/description
        if not item.get('Overview'):
            result.issues.append(ValidationIssue(
                severity='info',
                category='metadata',
                message='Missing description/overview',
                item_id=result.jellyfin_id,
                item_title=result.title
            ))
    
    def _analyze_quality(self, result: ValidationResult):
        """Analyze video quality (resolution, codec, bitrate)."""
        item = result.item
        media_sources = item.get('MediaSources', [])
        
        if not media_sources:
            result.issues.append(ValidationIssue(
                severity='warning',
                category='quality',
                message='No media source information available',
                item_id=result.jellyfin_id,
                item_title=result.title
            ))
            return
        
        # Get first media source (usually the main one)
        source = media_sources[0]
        media_streams = source.get('MediaStreams', [])
        
        # Find video stream
        video_stream = None
        for stream in media_streams:
            if stream.get('Type') == 'Video':
                video_stream = stream
                break
        
        if video_stream:
            # Extract resolution
            width = video_stream.get('Width', 0)
            height = video_stream.get('Height', 0)
            if width and height:
                if height >= 2160:
                    result.resolution = '4K'
                elif height >= 1080:
                    result.resolution = '1080p'
                elif height >= 720:
                    result.resolution = '720p'
                elif height >= 480:
                    result.resolution = '480p'
                else:
                    result.resolution = 'SD'
                    result.issues.append(ValidationIssue(
                        severity='info',
                        category='quality',
                        message=f'Low resolution: {width}x{height}',
                        item_id=result.jellyfin_id,
                        item_title=result.title
                    ))
            
            # Extract codec
            codec = video_stream.get('Codec', '')
            if codec:
                result.codec = codec
                # Warn about old codecs
                if codec.lower() in ['mpeg2video', 'mpeg4']:
                    result.issues.append(ValidationIssue(
                        severity='info',
                        category='quality',
                        message=f'Legacy codec: {codec}',
                        item_id=result.jellyfin_id,
                        item_title=result.title
                    ))
        else:
            result.issues.append(ValidationIssue(
                severity='warning',
                category='quality',
                message='No video stream found in media source',
                item_id=result.jellyfin_id,
                item_title=result.title
            ))
    
    def _check_subtitles(self, result: ValidationResult):
        """Check subtitle coverage."""
        item = result.item
        media_sources = item.get('MediaSources', [])
        
        if not media_sources:
            return
        
        # Get subtitle streams from all sources
        subtitle_languages = set()
        for source in media_sources:
            media_streams = source.get('MediaStreams', [])
            for stream in media_streams:
                if stream.get('Type') == 'Subtitle':
                    lang = stream.get('Language', 'unknown')
                    if lang and lang != 'unknown':
                        subtitle_languages.add(lang)
        
        result.subtitle_languages = sorted(list(subtitle_languages))
        result.has_subtitles = len(subtitle_languages) > 0
        
        if not result.has_subtitles:
            result.issues.append(ValidationIssue(
                severity='info',
                category='subtitle',
                message='No subtitle tracks found',
                item_id=result.jellyfin_id,
                item_title=result.title
            ))
    
    def validate_library(self, media_types: Optional[List[str]] = None,
                        check_metadata: bool = True, check_quality: bool = True,
                        check_subtitles: bool = True) -> List[ValidationResult]:
        """
        Validate all items in Jellyfin library.
        
        Args:
            media_types: Filter by types (e.g., ['Movie', 'Episode'])
            check_metadata: Whether to validate metadata
            check_quality: Whether to analyze quality
            check_subtitles: Whether to check subtitle coverage
            
        Returns:
            List of ValidationResult objects
        """
        logger.info("Fetching items from Jellyfin library...")
        if media_types:
            logger.info(f"Filtering by media types: {', '.join(media_types)}")
        
        try:
            items = self.client.get_all_items(
                item_types=media_types,
                fields=['Name', 'Path', 'MediaSources', 'Id', 'ProviderIds', 
                       'Type', 'ProductionYear', 'Genres', 'Overview']
            )
            logger.info(f"Found {len(items)} items to validate")
        except RuntimeError:
            # JellyfinClient.get_all_items() raises RuntimeError for API failures
            # Re-raise to maintain error context
            raise
        except Exception as e:
            # Catch any unexpected exceptions and wrap in RuntimeError
            logger.error(f"Unexpected error fetching items from Jellyfin: {e}", exc_info=True)
            raise RuntimeError(f"Cannot fetch items from Jellyfin: {e}") from e
        
        if len(items) == 0:
            logger.warning("No items found in Jellyfin library")
            return []
        
        logger.info("Validating files...")
        results = []
        
        for i, item in enumerate(items, 1):
            if i % 100 == 0:
                logger.info(f"Validated {i}/{len(items)} items...")
            
            result = self.validate_item(
                item,
                check_metadata=check_metadata,
                check_quality=check_quality,
                check_subtitles=check_subtitles
            )
            results.append(result)
        
        logger.info(f"Validation complete: {len(results)} items processed")
        return results
    
    def detect_content_duplicates(self, items: List[Dict], 
                                  hash_cache: Optional[Dict[str, str]] = None) -> List[Tuple[str, List[str]]]:
        """
        Detect duplicate content using hash-based comparison.
        
        Args:
            items: List of Jellyfin items
            hash_cache: Optional cache of file paths to hashes
            
        Returns:
            List of (hash, [item_ids]) tuples for duplicate groups
        """
        if hash_cache is None:
            hash_cache = {}
        
        logger.info("Detecting content duplicates using hash comparison...")
        
        # Group items by hash
        hash_to_items = defaultdict(list)
        
        for item in items:
            path = item.get('Path', '')
            if not path:
                continue
            
            try:
                file_path = Path(path)
                if not file_path.exists() or not file_path.is_file():
                    continue
                
                # Get hash from cache or calculate
                if path in hash_cache:
                    file_hash = hash_cache[path]
                else:
                    file_hash = self.hasher.calculate_hash(file_path)
                    hash_cache[path] = file_hash
                
                hash_to_items[file_hash].append(item.get('Id'))
                
            except (OSError, IOError) as e:
                logger.warning(f"Error hashing file {path}: {e}")
                continue
        
        # Find duplicates (groups with more than one item)
        duplicates = [(hash_val, item_ids) for hash_val, item_ids in hash_to_items.items() 
                     if len(item_ids) > 1]
        
        logger.info(f"Found {len(duplicates)} duplicate content groups")
        return duplicates
    
    def detect_orphans(self, jellyfin_items: List[Dict], 
                      filesystem_paths: Set[Path]) -> List[Path]:
        """
        Detect orphaned files (on disk but not in Jellyfin).
        
        Args:
            jellyfin_items: List of Jellyfin items
            filesystem_paths: Set of filesystem paths to check
            
        Returns:
            List of orphaned file paths
        """
        logger.info("Detecting orphaned files...")
        
        # Create set of Jellyfin paths (normalized)
        jellyfin_paths = set()
        for item in jellyfin_items:
            path = item.get('Path', '')
            if path:
                try:
                    normalized = str(Path(path).resolve())
                    jellyfin_paths.add(normalized)
                except OSError:
                    # Skip paths that cannot be resolved (e.g., network drives, invalid paths)
                    pass
        
        # Find filesystem paths not in Jellyfin
        orphans = []
        for fs_path in filesystem_paths:
            try:
                normalized = str(fs_path.resolve())
                if normalized not in jellyfin_paths:
                    orphans.append(fs_path)
            except OSError:
                # Skip paths that cannot be resolved (e.g., network drives, invalid paths)
                pass
        
        logger.info(f"Found {len(orphans)} orphaned files")
        return orphans

