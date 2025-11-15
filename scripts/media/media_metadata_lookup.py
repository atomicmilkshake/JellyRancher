#!/usr/bin/env python3
"""
Media Metadata Lookup - Step 4 of JellyRancher Workflow

Takes detected movies and TV shows from LLM analysis and queries external
metadata APIs to build a canonical database with:
- Correct movie years
- Correct TV show names and years
- Accurate season structures
- Episode titles and numbers
- Multi-part episode detection and handling

Supports: TMDB (The Movie Database), OMDb, and TVDB APIs
"""

import os
import json
import requests
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging
import time


class MediaMetadataLookup:
    """
    Looks up accurate metadata for movies and TV shows using external APIs.
    """
    
    def __init__(
        self,
        tmdb_api_key: Optional[str] = None,
        omdb_api_key: Optional[str] = None,
        cache_dir: Optional[str] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize metadata lookup service.
        
        Args:
            tmdb_api_key: TMDB API key (or env var TMDB_API_KEY)
            omdb_api_key: OMDb API key (or env var OMDB_API_KEY)
            cache_dir: Directory for caching API responses
            logger: Logger instance
        """
        self.tmdb_api_key = tmdb_api_key or os.getenv('TMDB_API_KEY')
        self.omdb_api_key = omdb_api_key or os.getenv('OMDB_API_KEY')
        self.logger = logger or self._setup_logger()
        
        # Set up cache directory
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            self.cache_dir = Path(os.getcwd()) / '.cache' / 'metadata'
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # API endpoints
        self.tmdb_base_url = "https://api.themoviedb.org/3"
        self.omdb_base_url = "http://www.omdbapi.com/"
        
        # Rate limiting: Be courteous to TMDB API
        # TMDB allows ~40 req/sec but recommends respecting their service
        # We use conservative 1 req/sec (1000ms) to be very courteous
        self.last_request_time = 0
        self.min_request_interval = 1.0  # 1 second between requests
        
        self.logger.info("Media Metadata Lookup initialized")
        if self.tmdb_api_key:
            self.logger.info("[OK] TMDB API key configured")
        else:
            self.logger.warning("[WARN] No TMDB API key - set TMDB_API_KEY environment variable")
        
        if self.omdb_api_key:
            self.logger.info("[OK] OMDb API key configured")
        else:
            self.logger.warning("[WARN] No OMDb API key - set OMDB_API_KEY environment variable")
    
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
    
    def _rate_limit(self):
        """Enforce rate limiting between API requests."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()
    
    def _get_cache_path(self, cache_key: str) -> Path:
        """Generate cache file path for a given key."""
        # Sanitize cache key for filename
        safe_key = "".join(c if c.isalnum() or c in '-_' else '_' for c in cache_key)
        return self.cache_dir / f"{safe_key}.json"
    
    def _read_cache(self, cache_key: str) -> Optional[Dict]:
        """Read cached data if available."""
        cache_path = self._get_cache_path(cache_key)
        if cache_path.exists():
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"Failed to read cache for {cache_key}: {e}")
        return None
    
    def _write_cache(self, cache_key: str, data: Dict):
        """Write data to cache."""
        cache_path = self._get_cache_path(cache_key)
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.warning(f"Failed to write cache for {cache_key}: {e}")
    
    def lookup_movie(
        self, 
        title: str, 
        year: Optional[int] = None,
        jellyfin_provider_ids: Optional[Dict[str, str]] = None,
        use_cache: bool = True
    ) -> Optional[Dict]:
        """
        Look up movie metadata.
        
        Args:
            title: Movie title
            year: Optional year to narrow search
            jellyfin_provider_ids: Optional dictionary of provider IDs from Jellyfin (e.g., {'Tmdb': '12345'})
            use_cache: Whether to use cached results
            
        Returns:
            Dictionary with movie metadata or None if not found
        """
        cache_key = f"movie_{title}_{year or 'noyear'}_{jellyfin_provider_ids.get('Tmdb', '') if jellyfin_provider_ids else ''}"
        
        # Check cache first
        if use_cache:
            cached = self._read_cache(cache_key)
            if cached:
                self.logger.debug(f"Cache hit for movie: {title}")
                return cached
        
        self.logger.info(f"Looking up movie: {title} ({year or 'unknown year'})")
        
        # Try TMDB first (more comprehensive)
        if self.tmdb_api_key:
            tmdb_id = jellyfin_provider_ids.get('Tmdb') if jellyfin_provider_ids else None
            if tmdb_id:
                self.logger.info(f"Using Jellyfin TMDB ID {tmdb_id} for direct lookup of movie: {title}")
                result = self._get_movie_details_tmdb(tmdb_id)
                if result:
                    self._write_cache(cache_key, result)
                    return result
            
            # If no TMDB ID from Jellyfin or direct lookup failed, perform search
            result = self._lookup_movie_tmdb(title, year)
            if result:
                self._write_cache(cache_key, result)
                return result
        
        # Fallback to OMDb
        if self.omdb_api_key:
            result = self._lookup_movie_omdb(title, year)
            if result:
                self._write_cache(cache_key, result)
                return result
        
        self.logger.warning(f"No metadata found for movie: {title}")
        return None
    
    def _lookup_movie_tmdb(self, title: str, year: Optional[int] = None) -> Optional[Dict]:
        """Look up movie using TMDB API."""
        try:
            self._rate_limit()
            
            # Search for movie
            params = {
                'api_key': self.tmdb_api_key,
                'query': title
            }
            if year:
                params['year'] = year
            
            response = requests.get(
                f"{self.tmdb_base_url}/search/movie",
                params=params,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get('results'):
                # Get first result (most relevant)
                movie = data['results'][0]
                
                return {
                    'title': movie.get('title'),
                    'original_title': movie.get('original_title'),
                    'year': int(movie.get('release_date', '')[:4]) if movie.get('release_date') else None,
                    'overview': movie.get('overview'),
                    'tmdb_id': movie.get('id'),
                    'poster_path': movie.get('poster_path'),
                    'source': 'tmdb'
                }
        
        except Exception as e:
            self.logger.error(f"TMDB movie lookup failed for '{title}': {e}")
        
        return None
    
    def _get_movie_details_tmdb(self, tmdb_id: str) -> Optional[Dict]:
        """Directly get movie details using TMDB ID."""
        try:
            self._rate_limit()
            response = requests.get(
                f"{self.tmdb_base_url}/movie/{tmdb_id}",
                params={'api_key': self.tmdb_api_key},
                timeout=10
            )
            response.raise_for_status()
            movie = response.json()
            
            return {
                'title': movie.get('title'),
                'original_title': movie.get('original_title'),
                'year': int(movie.get('release_date', '')[:4]) if movie.get('release_date') else None,
                'overview': movie.get('overview'),
                'tmdb_id': movie.get('id'),
                'poster_path': movie.get('poster_path'),
                'source': 'tmdb'
            }
        except Exception as e:
            self.logger.error(f"TMDB direct movie lookup failed for ID '{tmdb_id}': {e}")
        return None
    
    def _lookup_movie_omdb(self, title: str, year: Optional[int] = None) -> Optional[Dict]:
        """Look up movie using OMDb API."""
        try:
            self._rate_limit()
            
            params = {
                'apikey': self.omdb_api_key,
                't': title,
                'type': 'movie'
            }
            if year:
                params['y'] = year
            
            response = requests.get(self.omdb_base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('Response') == 'True':
                return {
                    'title': data.get('Title'),
                    'year': int(data.get('Year', '0').split('–')[0]) if data.get('Year') else None,
                    'overview': data.get('Plot'),
                    'imdb_id': data.get('imdbID'),
                    'poster_url': data.get('Poster'),
                    'source': 'omdb'
                }
        
        except Exception as e:
            self.logger.error(f"OMDb movie lookup failed for '{title}': {e}")
        
        return None
    
    def lookup_tv_show(
        self, 
        title: str, 
        year: Optional[int] = None,
        jellyfin_provider_ids: Optional[Dict[str, str]] = None,
        use_cache: bool = True
    ) -> Optional[Dict]:
        """
        Look up TV show metadata including all seasons and episodes.
        
        Args:
            title: TV show title
            year: Optional year to narrow search
            jellyfin_provider_ids: Optional dictionary of provider IDs from Jellyfin (e.g., {'Tmdb': '12345', 'Tvdb': '67890'})
            use_cache: Whether to use cached results
            
        Returns:
            Dictionary with TV show metadata including season/episode details
        """
        cache_key = f"tv_{title}_{year or 'noyear'}_{jellyfin_provider_ids.get('Tmdb', '') if jellyfin_provider_ids else ''}_{jellyfin_provider_ids.get('Tvdb', '') if jellyfin_provider_ids else ''}"
        
        # Check cache first
        if use_cache:
            cached = self._read_cache(cache_key)
            if cached:
                self.logger.debug(f"Cache hit for TV show: {title}")
                return cached
        
        self.logger.info(f"Looking up TV show: {title} ({year or 'unknown year'})")
        
        # Try TMDB (best for TV shows)
        if self.tmdb_api_key:
            tmdb_id = jellyfin_provider_ids.get('Tmdb') if jellyfin_provider_ids else None
            tvdb_id = jellyfin_provider_ids.get('Tvdb') if jellyfin_provider_ids else None

            if tmdb_id:
                self.logger.info(f"Using Jellyfin TMDB ID {tmdb_id} for direct lookup of TV show: {title}")
                result = self._get_tv_details_tmdb(tmdb_id)
                if result:
                    self._write_cache(cache_key, result)
                    return result
            elif tvdb_id:
                self.logger.info(f"Using Jellyfin TVDB ID {tvdb_id} for direct lookup of TV show: {title} (via TMDB external IDs)")
                # TMDB can find TV shows by TVDB ID via external_ids endpoint
                result = self._get_tv_details_tmdb_by_external_id(tvdb_id, 'tvdb_id')
                if result:
                    self._write_cache(cache_key, result)
                    return result
            
            # If no TMDB/TVDB ID from Jellyfin or direct lookup failed, perform search
            result = self._lookup_tv_tmdb(title, year)
            if result:
                self._write_cache(cache_key, result)
                return result
        
        # Fallback to OMDb (limited TV data)
        if self.omdb_api_key:
            result = self._lookup_tv_omdb(title, year)
            if result:
                self._write_cache(cache_key, result)
                return result
        
        self.logger.warning(f"No metadata found for TV show: {title}")
        return None
    
    def _lookup_tv_tmdb(self, title: str, year: Optional[int] = None) -> Optional[Dict]:
        """Look up TV show using TMDB API with full season/episode details."""
        try:
            self._rate_limit()
            
            # Search for TV show
            params = {
                'api_key': self.tmdb_api_key,
                'query': title
            }
            if year:
                params['first_air_date_year'] = year
            
            response = requests.get(
                f"{self.tmdb_base_url}/search/tv",
                params=params,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            if not data.get('results'):
                return None
            
            # Get first result
            show = data['results'][0]
            show_id = show.get('id')
            
            # Get detailed show info including seasons
            self._rate_limit()
            detail_response = requests.get(
                f"{self.tmdb_base_url}/tv/{show_id}",
                params={'api_key': self.tmdb_api_key},
                timeout=10
            )
            detail_response.raise_for_status()
            detail_data = detail_response.json()
            
            # Build seasons information
            seasons = []
            for season in detail_data.get('seasons', []):
                season_number = season.get('season_number')
                if season_number == 0:  # Skip specials for now
                    continue
                
                # Get episode details for this season
                season_info = self._get_season_episodes(show_id, season_number)
                if season_info:
                    seasons.append(season_info)
            
            return {
                'title': detail_data.get('name'),
                'original_title': detail_data.get('original_name'),
                'year': int(detail_data.get('first_air_date', '')[:4]) if detail_data.get('first_air_date') else None,
                'overview': detail_data.get('overview'),
                'tmdb_id': show_id,
                'poster_path': detail_data.get('poster_path'),
                'number_of_seasons': detail_data.get('number_of_seasons'),
                'number_of_episodes': detail_data.get('number_of_episodes'),
                'seasons': seasons,
                'source': 'tmdb'
            }
        
        except Exception as e:
            self.logger.error(f"TMDB TV lookup failed for '{title}': {e}")
        
        return None
    
    def _get_season_episodes(self, show_id: int, season_number: int) -> Optional[Dict]:
        """Get detailed episode information for a specific season."""
        try:
            self._rate_limit()
            
            response = requests.get(
                f"{self.tmdb_base_url}/tv/{show_id}/season/{season_number}",
                params={'api_key': self.tmdb_api_key},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            episodes = []
            for ep in data.get('episodes', []):
                episode_info = {
                    'episode_number': ep.get('episode_number'),
                    'name': ep.get('name'),
                    'overview': ep.get('overview'),
                    'air_date': ep.get('air_date'),
                    'runtime': ep.get('runtime'),
                }
                
                # Check if this might be part of a multi-part episode
                ep_name = ep.get('name', '').lower()
                if any(marker in ep_name for marker in ['part 1', 'part 2', 'part i', 'part ii', '(1)', '(2)']):
                    episode_info['is_multi_part'] = True
                
                episodes.append(episode_info)
            
            return {
                'season_number': season_number,
                'episode_count': len(episodes),
                'air_date': data.get('air_date'),
                'overview': data.get('overview'),
                'episodes': episodes
            }
        
        except Exception as e:
            self.logger.error(f"Failed to get episodes for season {season_number}: {e}")
        
        return None
    
    def _lookup_tv_omdb(self, title: str, year: Optional[int] = None) -> Optional[Dict]:
        """Look up TV show using OMDb API (limited data)."""
        try:
            self._rate_limit()
            
            params = {
                'apikey': self.omdb_api_key,
                't': title,
                'type': 'series'
            }
            if year:
                params['y'] = year
            
            response = requests.get(self.omdb_base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('Response') == 'True':
                # OMDb doesn't provide detailed episode info
                year_str = data.get('Year', '')
                year_match = year_str.split('–')[0] if '–' in year_str else year_str
                
                return {
                    'title': data.get('Title'),
                    'year': int(year_match) if year_match and year_match.isdigit() else None,
                    'overview': data.get('Plot'),
                    'imdb_id': data.get('imdbID'),
                    'poster_url': data.get('Poster'),
                    'total_seasons': int(data.get('totalSeasons', 0)),
                    'seasons': [],  # OMDb doesn't provide episode details
                    'source': 'omdb'
                }
        
        except Exception as e:
            self.logger.error(f"OMDb TV lookup failed for '{title}': {e}")
        
        return None

    def _get_tv_details_tmdb(self, tmdb_id: str) -> Optional[Dict]:
        """Directly get TV show details using TMDB ID."""
        try:
            self._rate_limit()
            detail_response = requests.get(
                f"{self.tmdb_base_url}/tv/{tmdb_id}",
                params={'api_key': self.tmdb_api_key},
                timeout=10
            )
            detail_response.raise_for_status()
            detail_data = detail_response.json()
            
            seasons = []
            for season in detail_data.get('seasons', []):
                season_number = season.get('season_number')
                if season_number == 0:  # Skip specials for now
                    continue
                
                season_info = self._get_season_episodes(tmdb_id, season_number)
                if season_info:
                    seasons.append(season_info)
            
            return {
                'title': detail_data.get('name'),
                'original_title': detail_data.get('original_name'),
                'year': int(detail_data.get('first_air_date', '')[:4]) if detail_data.get('first_air_date') else None,
                'overview': detail_data.get('overview'),
                'tmdb_id': tmdb_id,
                'poster_path': detail_data.get('poster_path'),
                'number_of_seasons': detail_data.get('number_of_seasons'),
                'number_of_episodes': detail_data.get('number_of_episodes'),
                'seasons': seasons,
                'source': 'tmdb'
            }
        except Exception as e:
            self.logger.error(f"TMDB direct TV lookup failed for ID '{tmdb_id}': {e}")
        return None

    def _get_tv_details_tmdb_by_external_id(self, external_id: str, external_source: str) -> Optional[Dict]:
        """
        Get TV show details from TMDB using an external ID (e.g., TVDB ID).
        First finds the TMDB ID, then fetches details.
        """
        try:
            self._rate_limit()
            find_response = requests.get(
                f"{self.tmdb_base_url}/find/{external_id}",
                params={'api_key': self.tmdb_api_key, 'external_source': external_source},
                timeout=10
            )
            find_response.raise_for_status()
            find_data = find_response.json()

            if find_data.get('tv_results'):
                tmdb_id = find_data['tv_results'][0].get('id')
                if tmdb_id:
                    return self._get_tv_details_tmdb(tmdb_id)
            
        except Exception as e:
            self.logger.error(f"TMDB external ID lookup failed for '{external_id}' ({external_source}): {e}")
        return None
    
    def build_canonical_database(
        self, 
        detected_media: List[Dict],
        output_path: Optional[str] = None
    ) -> Dict:
        """
        Build canonical database from LLM-detected media list.
        
        Args:
            detected_media: List of detected media from LLM analysis
            output_path: Optional path to save the database
            
        Returns:
            Canonical database with complete metadata
        """
        self.logger.info(f"Building canonical database for {len(detected_media)} items...")
        
        canonical_db = {
            'timestamp': datetime.now().isoformat(),
            'total_items': len(detected_media),
            'movies': [],
            'tv_shows': [],
            'lookup_failures': []
        }
        
        for item in detected_media:
            title = item.get('title')
            media_type = item.get('type')
            year_estimate = item.get('year_estimate')
            
            self.logger.info(f"Processing: {title} ({media_type})")
            
            if media_type == 'movie':
                metadata = self.lookup_movie(title, year_estimate)
                if metadata:
                    metadata['original_detection'] = item
                    canonical_db['movies'].append(metadata)
                else:
                    canonical_db['lookup_failures'].append(item)
            
            elif media_type == 'tv_show':
                metadata = self.lookup_tv_show(title, year_estimate)
                if metadata:
                    metadata['original_detection'] = item
                    canonical_db['tv_shows'].append(metadata)
                else:
                    canonical_db['lookup_failures'].append(item)
        
        # Summary
        self.logger.info(f"[OK] Movies: {len(canonical_db['movies'])}")
        self.logger.info(f"[OK] TV Shows: {len(canonical_db['tv_shows'])}")
        self.logger.info(f"[WARN] Lookup failures: {len(canonical_db['lookup_failures'])}")
        
        # Save if output path provided
        if output_path:
            self.save_database(canonical_db, output_path)
        
        return canonical_db
    
    def save_database(self, canonical_db: Dict, output_path: str):
        """Save canonical database to JSON file."""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(canonical_db, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Canonical database saved to: {output_file}")


def main():
    """Example usage of MediaMetadataLookup."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python media_metadata_lookup.py <llm_analysis.json>")
        print("\nExample:")
        print("  python media_metadata_lookup.py data/llm_analysis_20241108_120000.json")
        print("\nRequired environment variables:")
        print("  TMDB_API_KEY - Get free key from https://www.themoviedb.org/settings/api")
        print("  OMDB_API_KEY - Get free key from http://www.omdbapi.com/apikey.aspx")
        return
    
    # Load LLM analysis
    analysis_file = Path(sys.argv[1])
    if not analysis_file.exists():
        print(f"Error: File not found: {analysis_file}")
        return
    
    print(f"Loading LLM analysis from: {analysis_file}")
    with open(analysis_file, 'r', encoding='utf-8') as f:
        analysis_data = json.load(f)
    
    detected_media = analysis_data.get('detected_media', [])
    
    if not detected_media:
        print("No detected media found in analysis file")
        return
    
    # Initialize lookup service
    lookup = MediaMetadataLookup()
    
    # Build canonical database
    print("\n" + "="*80)
    print("BUILDING CANONICAL METADATA DATABASE")
    print("="*80 + "\n")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"data/canonical_metadata_{timestamp}.json"
    
    canonical_db = lookup.build_canonical_database(
        detected_media,
        output_path=output_path
    )
    
    print("\n" + "="*80)
    print("DATABASE BUILD COMPLETE")
    print("="*80)
    print(f"Movies: {len(canonical_db['movies'])}")
    print(f"TV Shows: {len(canonical_db['tv_shows'])}")
    print(f"Lookup failures: {len(canonical_db['lookup_failures'])}")
    print(f"\nSaved to: {output_path}")
    print("="*80)


if __name__ == "__main__":
    main()
