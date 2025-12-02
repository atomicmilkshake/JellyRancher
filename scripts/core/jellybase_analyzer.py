#!/usr/bin/env python3
"""
JellyBase Library Analyzer - Comprehensive library analysis

Provides analysis functions:
- Content-based duplicate detection
- Quality analysis
- Coverage analysis
- Library health scoring
"""

import logging
from typing import List, Dict, Tuple
from collections import defaultdict
from scripts.core.jellyfin_client import JellyfinClient
from scripts.core.jellyfin_validator import JellyfinValidator
from scripts.utils.transaction_manager import FileHasher

logger = logging.getLogger(__name__)


def detect_content_duplicates(client: JellyfinClient, items: List[Dict]) -> List[Tuple[str, List[str]]]:
    """
    Detect duplicate content using hash-based comparison.
    
    Args:
        client: JellyfinClient instance
        items: List of Jellyfin items
        
    Returns:
        List of (hash, [item_ids]) tuples for duplicate groups
    """
    try:
        logger.info("Detecting content duplicates using hash comparison...")
        
        hasher = FileHasher()
        hash_to_items = defaultdict(list)
        
        for item in items:
            path = item.get('Path', '')
            if not path:
                continue
            
            try:
                from pathlib import Path as PathLib
                file_path = PathLib(path)
                if not file_path.exists() or not file_path.is_file():
                    continue
                
                # Calculate hash
                file_hash = hasher.calculate_hash(file_path)
                hash_to_items[file_hash].append(item.get('Id'))
                
            except Exception as e:
                logger.warning(f"Error hashing file {path}: {e}")
                continue
        
        # Find duplicates (groups with more than one item)
        duplicates = [(hash_val, item_ids) for hash_val, item_ids in hash_to_items.items() 
                     if len(item_ids) > 1]
        
        logger.info(f"Found {len(duplicates)} duplicate content groups")
        return duplicates
    except Exception as e:
        logger.error(f"Error detecting content duplicates: {e}", exc_info=True)
        return []


def analyze_quality_distribution(client: JellyfinClient, items: List[Dict]) -> Dict:
    """
    Analyze quality distribution (resolution, codec, bitrate).
    
    Args:
        client: JellyfinClient instance
        items: List of Jellyfin items
        
    Returns:
        Dictionary with quality statistics
    """
    try:
        logger.info("Analyzing quality distribution...")
        
        resolution_dist = defaultdict(int)
        codec_dist = defaultdict(int)
        total_items = 0
        
        for item in items:
            media_sources = item.get('MediaSources', [])
            if not media_sources:
                continue
            
            for source in media_sources:
                media_streams = source.get('MediaStreams', [])
                for stream in media_streams:
                    if stream.get('Type') == 'Video':
                        total_items += 1
                        
                        # Resolution
                        width = stream.get('Width', 0)
                        height = stream.get('Height', 0)
                        if width and height:
                            if height >= 2160:
                                resolution_dist['4K'] += 1
                            elif height >= 1080:
                                resolution_dist['1080p'] += 1
                            elif height >= 720:
                                resolution_dist['720p'] += 1
                            elif height >= 480:
                                resolution_dist['480p'] += 1
                            else:
                                resolution_dist['SD'] += 1
                        
                        # Codec
                        codec = stream.get('Codec', '')
                        if codec:
                            codec_dist[codec] += 1
                        break
        
        result = {
            'total_items': total_items,
            'resolution_distribution': dict(resolution_dist),
            'codec_distribution': dict(codec_dist)
        }
        
        logger.info(f"Quality analysis complete: {total_items} items analyzed")
        return result
    except Exception as e:
        logger.error(f"Error analyzing quality distribution: {e}", exc_info=True)
        return {
            'total_items': 0,
            'resolution_distribution': {},
            'codec_distribution': {}
        }


def analyze_coverage(client: JellyfinClient, items: List[Dict]) -> Dict:
    """
    Analyze coverage (missing metadata, subtitles, artwork).
    
    Args:
        client: JellyfinClient instance
        items: List of Jellyfin items
        
    Returns:
        Dictionary with coverage statistics
    """
    try:
        logger.info("Analyzing coverage...")
        
        total_items = len(items)
        missing_provider_ids = 0
        missing_overview = 0
        missing_subtitles = 0
        missing_year = 0
        missing_genres = 0
        
        for item in items:
            # Check ProviderIds
            provider_ids = item.get('ProviderIds', {})
            if not provider_ids:
                missing_provider_ids += 1
            
            # Check overview
            if not item.get('Overview'):
                missing_overview += 1
            
            # Check year
            if not item.get('ProductionYear'):
                missing_year += 1
            
            # Check genres
            if not item.get('Genres'):
                missing_genres += 1
            
            # Check subtitles
            media_sources = item.get('MediaSources', [])
            has_subtitles = False
            for source in media_sources:
                media_streams = source.get('MediaStreams', [])
                for stream in media_streams:
                    if stream.get('Type') == 'Subtitle':
                        has_subtitles = True
                        break
                if has_subtitles:
                    break
            if not has_subtitles:
                missing_subtitles += 1
        
        result = {
            'total_items': total_items,
            'metadata_coverage': {
                'provider_ids': {
                    'missing': missing_provider_ids,
                    'coverage_percent': ((total_items - missing_provider_ids) / total_items * 100) if total_items > 0 else 0
                },
                'overview': {
                    'missing': missing_overview,
                    'coverage_percent': ((total_items - missing_overview) / total_items * 100) if total_items > 0 else 0
                },
                'year': {
                    'missing': missing_year,
                    'coverage_percent': ((total_items - missing_year) / total_items * 100) if total_items > 0 else 0
                },
                'genres': {
                    'missing': missing_genres,
                    'coverage_percent': ((total_items - missing_genres) / total_items * 100) if total_items > 0 else 0
                }
            },
            'subtitle_coverage': {
                'missing': missing_subtitles,
                'coverage_percent': ((total_items - missing_subtitles) / total_items * 100) if total_items > 0 else 0
            }
        }
        
        logger.info(f"Coverage analysis complete: {total_items} items analyzed")
        return result
    except Exception as e:
        logger.error(f"Error analyzing coverage: {e}", exc_info=True)
        return {
            'total_items': 0,
            'metadata_coverage': {},
            'subtitle_coverage': {}
        }


def calculate_health_score(validator: JellyfinValidator, items: List[Dict]) -> int:
    """
    Calculate library health score (0-100).
    
    Factors:
    - File validity (40%)
    - Metadata completeness (30%)
    - Subtitle coverage (20%)
    - Duplicate count (10%)
    
    Args:
        validator: JellyfinValidator instance
        items: List of Jellyfin items
        
    Returns:
        Health score (0-100)
    """
    try:
        logger.info("Calculating library health score...")
        
        if not items:
            return 0
        
        # Validate items
        validation_results = []
        for item in items[:100]:  # Sample first 100 for performance
            result = validator.validate_item(item, check_metadata=True, check_quality=False, check_subtitles=True)
            validation_results.append(result)
        
        total = len(validation_results)
        if total == 0:
            return 0
        
        # File validity (40%)
        valid_files = sum(1 for r in validation_results if r.valid)
        file_score = (valid_files / total) * 40
        
        # Metadata completeness (30%)
        items_with_metadata = sum(1 for r in validation_results 
                                 if r.item.get('ProviderIds') and 
                                 r.item.get('Overview') and 
                                 r.item.get('ProductionYear'))
        metadata_score = (items_with_metadata / total) * 30
        
        # Subtitle coverage (20%)
        items_with_subtitles = sum(1 for r in validation_results if r.has_subtitles)
        subtitle_score = (items_with_subtitles / total) * 20
        
        # Duplicate count (10%) - penalize duplicates
        # For now, assume no duplicates (would need duplicate detection)
        duplicate_score = 10
        
        total_score = file_score + metadata_score + subtitle_score + duplicate_score
        health_score = int(min(100, max(0, total_score)))
        
        logger.info(f"Library health score: {health_score}/100")
        return health_score
    except Exception as e:
        logger.error(f"Error calculating health score: {e}", exc_info=True)
        return 0

