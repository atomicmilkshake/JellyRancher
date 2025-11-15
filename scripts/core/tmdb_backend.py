"""
TMDB Backend - The Movie Database API Integration

Provides TV show metadata fetching and episode cache generation
from TMDB API for the JellyRancher application.

This backend wraps the tmdbv3api library and provides GUI-friendly
interfaces with progress callbacks and error handling.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Callable, Tuple
from datetime import datetime

try:
    from tmdbv3api import TMDb, TV
    TMDB_AVAILABLE = True
except ImportError:
    TMDB_AVAILABLE = False

from _common.config_loader import get_tv_cache_dir
from _common.logger import ProjectLogger

# Set up logging
logger = ProjectLogger('tmdb_backend')


class TMDBError(Exception):
    """Base exception for TMDB-related errors"""
    pass


class TMDBConnectionError(TMDBError):
    """Raised when TMDB API connection fails"""
    pass


class TMDBNotFoundError(TMDBError):
    """Raised when show is not found on TMDB"""
    pass


class TMDBBackend:
    """Backend for TMDB API operations"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize TMDB backend

        Args:
            api_key: TMDB API key (optional, can be set later)
        """
        if not TMDB_AVAILABLE:
            raise ImportError(
                "tmdbv3api library not found. "
                "Install it with: pip install tmdbv3api"
            )

        self.tmdb = TMDb()
        self._tv = None
        self._api_key = api_key

        # Rate limiting: Respect TMDB's ~40 req/sec upper limit
        # Use conservative 1 req/sec (1000ms) to be courteous
        self.min_request_interval = 1.0  # seconds between requests
        self.last_request_time = 0

        if api_key:
            self.set_api_key(api_key)
    
    @property
    def tv(self):
        """Lazy initialization of TV API"""
        if self._tv is None:
            self._tv = TV()
        return self._tv
    
    @tv.setter
    def tv(self, value):
        """Allow tests to mock the TV API"""
        self._tv = value
    
    @property
    def tmdb_api(self):
        """Alias for tmdb (backward compatibility with tests)"""
        return self.tmdb
    
    def _rate_limit(self):
        """
        Enforce courteous rate limiting between TMDB API requests.
        
        TMDB guidelines: ~40 req/sec upper limit, respect 429 responses.
        We use conservative 1 req/sec to be courteous and avoid issues.
        """
        import time
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            sleep_time = self.min_request_interval - elapsed
            logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s")
            time.sleep(sleep_time)
        self.last_request_time = time.time()
    
    def _handle_api_error(self, error: Exception, operation: str) -> None:
        """
        Handle API errors with special handling for rate limits.
        
        Args:
            error: The exception that occurred
            operation: Description of the operation being performed
            
        Raises:
            TMDBConnectionError: For connection issues
            TMDBError: For other API errors
        """
        error_msg = str(error).lower()
        
        # Check for rate limiting (429 Too Many Requests)
        if "429" in error_msg or "too many requests" in error_msg or "rate limit" in error_msg:
            logger.warning(f"TMDB rate limit hit during {operation}. Backing off...")
            # Increase rate limiting temporarily
            self.min_request_interval = min(self.min_request_interval * 2, 10.0)  # Max 10 seconds
            raise TMDBConnectionError(
                f"TMDB rate limit exceeded. Please wait and try again. "
                f"Current rate limit: 1 request every {self.min_request_interval}s"
            )
        
        # Other API errors
        raise TMDBConnectionError(f"TMDB API error during {operation}: {str(error)}")
    
    def set_api_key(self, api_key: str) -> None:
        """
        Set the TMDB API key
        
        Args:
            api_key: TMDB API key
        """
        self._api_key = api_key
        self.tmdb.api_key = api_key
        logger.info("TMDB API key configured")
    
    def validate_api_key(self) -> Tuple[bool, str]:
        """
        Validate the current API key
        
        Returns:
            Tuple of (is_valid, message)
        """
        if not self._api_key:
            return False, "No API key set"
        
        try:
            # Try a simple search to validate
            results = self.tv.search("test")
            return True, "API key is valid"
        except Exception as e:
            logger.error(f"API key validation failed: {e}")
            return False, f"Invalid API key: {str(e)}"
    
    def search_shows(
        self,
        query: str,
        year: Optional[int] = None,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> List[Dict]:
        """
        Search for TV shows on TMDB
        
        Args:
            query: Show name to search for
            year: Optional year to filter results
            progress_callback: Optional callback for progress updates
            
        Returns:
            List of show dictionaries with keys:
                - id: TMDB ID
                - name: Show name
                - first_air_date: First air date
                - overview: Show description
                - poster_path: Poster image path
                
        Raises:
            TMDBConnectionError: If API connection fails
            TMDBNotFoundError: If no shows found
        """
        if not self._api_key:
            raise TMDBError(
                "No TMDB API key configured. "
                "Please go to Settings and configure your TMDB API key. "
                "You can get a free API key from https://www.themoviedb.org/settings/api"
            )
        
        if progress_callback:
            progress_callback(f"Searching TMDB for '{query}'...")
        
        logger.info(f"Searching for show: {query} (year: {year or 'any'})")
        
        # Rate limiting for courteous API usage
        self._rate_limit()
        
        try:
            results = self.tv.search(query)
        except Exception as e:
            self._handle_api_error(e, f"search for '{query}'")
        
        if not results:
            raise TMDBNotFoundError(
                f"No TV shows found for '{query}'. "
                "Try a different search term, check spelling, or try searching by TMDB ID directly."
            )
        
        # Filter by year if provided
        if year:
            filtered = []
            for s in results:
                # Handle both dict and object responses
                if isinstance(s, dict):
                    first_air = s.get('first_air_date', '')
                else:
                    first_air = getattr(s, 'first_air_date', '')
                
                if first_air and str(year) in first_air:
                    filtered.append(s)
            
            if filtered:
                results = filtered
        
        # Convert to dictionaries (handle both dict and object responses)
        shows = []
        for show in results:
            # Handle both dict and object responses from tmdbv3api
            if isinstance(show, dict):
                shows.append({
                    'id': show.get('id'),
                    'name': show.get('name'),
                    'first_air_date': show.get('first_air_date', 'Unknown'),
                    'overview': show.get('overview', ''),
                    'poster_path': show.get('poster_path', None),
                    'number_of_seasons': show.get('number_of_seasons', 0),
                    'number_of_episodes': show.get('number_of_episodes', 0)
                })
            else:
                # Object with attributes
                shows.append({
                    'id': show.id,
                    'name': show.name,
                    'first_air_date': getattr(show, 'first_air_date', 'Unknown'),
                    'overview': getattr(show, 'overview', ''),
                    'poster_path': getattr(show, 'poster_path', None),
                    'number_of_seasons': getattr(show, 'number_of_seasons', 0),
                    'number_of_episodes': getattr(show, 'number_of_episodes', 0)
                })
        
        if progress_callback:
            progress_callback(f"Found {len(shows)} results")
        
        logger.info(f"Found {len(shows)} shows")
        return shows
    
    def get_show_details(
        self,
        tmdb_id: int,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Dict:
        """
        Get detailed information about a TV show
        
        Args:
            tmdb_id: TMDB show ID
            progress_callback: Optional callback for progress updates
            
        Returns:
            Show details dictionary
            
        Raises:
            TMDBConnectionError: If API connection fails
            TMDBNotFoundError: If show not found
        """
        if not self._api_key:
            raise TMDBError(
                "No TMDB API key configured. "
                "Please go to Settings and configure your TMDB API key. "
                "You can get a free API key from https://www.themoviedb.org/settings/api"
            )
        
        if progress_callback:
            progress_callback(f"Fetching show details (ID: {tmdb_id})...")
        
        logger.info(f"Fetching show details for TMDB ID: {tmdb_id}")
        
        # Rate limiting for courteous API usage
        self._rate_limit()
        
        try:
            show = self.tv.details(tmdb_id)
        except Exception as e:
            self._handle_api_error(e, f"fetch show details (ID: {tmdb_id})")
        
        if not show:
            raise TMDBNotFoundError(f"Show not found (ID: {tmdb_id})")
        
        # Handle both dict and object responses from tmdbv3api
        if isinstance(show, dict):
            details = {
                'id': show.get('id'),
                'name': show.get('name'),
                'first_air_date': show.get('first_air_date', 'Unknown'),
                'overview': show.get('overview', ''),
                'poster_path': show.get('poster_path', None),
                'number_of_seasons': show.get('number_of_seasons', 0),
                'number_of_episodes': show.get('number_of_episodes', 0),
                'status': show.get('status', 'Unknown'),
                'genres': show.get('genres', [])
            }
        else:
            # Object with attributes
            details = {
                'id': show.id,
                'name': show.name,
                'first_air_date': getattr(show, 'first_air_date', 'Unknown'),
                'overview': getattr(show, 'overview', ''),
                'poster_path': getattr(show, 'poster_path', None),
                'number_of_seasons': getattr(show, 'number_of_seasons', 0),
                'number_of_episodes': getattr(show, 'number_of_episodes', 0),
                'status': getattr(show, 'status', 'Unknown'),
                'genres': getattr(show, 'genres', [])
            }
        
        if progress_callback:
            progress_callback(f"Loaded: {details['name']}")
        
        return details
    
    def generate_cache(
        self,
        tmdb_id: int,
        show_name: Optional[str] = None,
        output_path: Optional[Path] = None,
        progress_callback: Optional[Callable[[int, str], None]] = None
    ) -> Tuple[Path, Dict]:
        """
        Generate episode cache file from TMDB data
        
        Args:
            tmdb_id: TMDB show ID
            show_name: Optional show name (fetched if not provided)
            output_path: Optional custom output path
            progress_callback: Optional callback(progress_percent, status_message)
            
        Returns:
            Tuple of (cache_file_path, cache_data)
            
        Raises:
            TMDBConnectionError: If API connection fails
            TMDBError: If cache generation fails
        """
        if not self._api_key:
            raise TMDBError(
                "No TMDB API key configured. "
                "Please go to Settings and configure your TMDB API key. "
                "You can get a free API key from https://www.themoviedb.org/settings/api"
            )
        
        logger.info(f"Generating cache for TMDB ID: {tmdb_id}")
        
        # Get show details
        if progress_callback:
            progress_callback(0, "Fetching show information...")
        
        # Rate limiting for courteous API usage
        self._rate_limit()
        
        try:
            show = self.tv.details(tmdb_id)
        except Exception as e:
            self._handle_api_error(e, f"fetch show details for cache (ID: {tmdb_id})")
        
        # Handle both dict and object responses
        show_name_value = show.get('name') if isinstance(show, dict) else show.name
        show_id_value = show.get('id') if isinstance(show, dict) else show.id
        show_first_air = show.get('first_air_date', '') if isinstance(show, dict) else getattr(show, 'first_air_date', '')
        show_overview = show.get('overview', '') if isinstance(show, dict) else getattr(show, 'overview', '')
        total_seasons = show.get('number_of_seasons', 0) if isinstance(show, dict) else getattr(show, 'number_of_seasons', 0)
        
        show_name = show_name or show_name_value
        
        # Build cache structure
        cache = {
            'show_name': show_name_value,
            'tmdb_id': show_id_value,
            'first_air_date': show_first_air,
            'overview': show_overview,
            'generated_date': datetime.now().isoformat(),
            'seasons': {}
        }
        
        if progress_callback:
            progress_callback(5, f"Found {show_name_value} with {total_seasons} seasons")
        
        # Fetch all seasons and episodes
        for season_num in range(1, total_seasons + 1):
            try:
                if progress_callback:
                    progress = 5 + int((season_num / total_seasons) * 90)
                    progress_callback(progress, f"Fetching season {season_num}/{total_seasons}...")
                
                # Rate limiting for courteous API usage
                self._rate_limit()
                
                try:
                    season = self.tv.season(show_id_value, season_num)
                except Exception as e:
                    logger.warning(f"Failed to fetch season {season_num}: {e}")
                    continue
                
                # Handle both dict and object responses
                episodes = season.get('episodes') if isinstance(season, dict) else getattr(season, 'episodes', None)
                
                if not episodes:
                    logger.warning(f"Season {season_num}: No episodes found")
                    continue
                
                season_name = season.get('name', f"Season {season_num}") if isinstance(season, dict) else getattr(season, 'name', f"Season {season_num}")
                season_air_date = season.get('air_date') if isinstance(season, dict) else getattr(season, 'air_date', None)
                
                cache['seasons'][str(season_num)] = {
                    'season_number': season_num,
                    'name': season_name,
                    'air_date': season_air_date,
                    'episodes': {}
                }
                
                for episode in episodes:
                    # Handle both dict and object responses
                    if isinstance(episode, dict):
                        episode_num = episode.get('episode_number')
                        title = episode.get('name', f"Episode {episode_num}")
                        ep_air_date = episode.get('air_date')
                        ep_overview = episode.get('overview', '')
                    else:
                        episode_num = episode.episode_number
                        title = getattr(episode, 'name', f"Episode {episode_num}")
                        ep_air_date = getattr(episode, 'air_date', None)
                        ep_overview = getattr(episode, 'overview', '')
                    
                    # Sanitize title for filesystem compatibility
                    canonical_title = self._sanitize_title(title)
                    
                    cache['seasons'][str(season_num)]['episodes'][str(episode_num)] = {
                        'episode_number': episode_num,
                        'canonical_title': canonical_title,
                        'original_title': title,
                        'air_date': ep_air_date,
                        'overview': ep_overview
                    }
                
                logger.info(f"Season {season_num}: {len(episodes)} episodes")
                
            except Exception as e:
                logger.error(f"Failed to fetch season {season_num}: {e}")
                if progress_callback:
                    progress = 5 + int((season_num / total_seasons) * 90)
                    progress_callback(progress, f"Warning: Failed to fetch season {season_num}")
                continue
        
        # Determine output path
        if output_path is None:
            cache_dir = get_tv_cache_dir()
            cache_dir.mkdir(parents=True, exist_ok=True)
            
            # Create filename
            show_name_normalized = show_name_value.lower()
            show_name_normalized = show_name_normalized.replace(' ', '_').replace(':', '').replace('&', 'and')
            show_name_normalized = show_name_normalized.replace('(', '').replace(')', '').replace("'", '')
            
            # Extract year from first_air_date
            year = None
            if show_first_air:
                year = show_first_air[:4]
            
            if year:
                filename = f"{show_name_normalized}_{year}.json"
            else:
                filename = f"{show_name_normalized}.json"
            
            output_path = cache_dir / filename
        
        # Save cache file
        if progress_callback:
            progress_callback(95, "Saving cache file...")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(cache, f, indent=2, ensure_ascii=False)
        
        total_episodes = sum(len(s['episodes']) for s in cache['seasons'].values())
        
        if progress_callback:
            progress_callback(100, f"Complete! {len(cache['seasons'])} seasons, {total_episodes} episodes")
        
        logger.info(f"Cache saved to: {output_path}")
        logger.info(f"Total seasons: {len(cache['seasons'])}, episodes: {total_episodes}")
        
        return output_path, cache
    
    @staticmethod
    def _sanitize_title(title: str) -> str:
        """
        Sanitize episode title to remove illegal filesystem characters
        
        Args:
            title: Original title
            
        Returns:
            Sanitized title safe for filenames
        """
        illegal_chars = {
            '<': '(less than)',
            '>': '(greater than)',
            ':': ' -',
            '"': "'",
            '/': ' or ',
            '\\': ' or ',
            '|': '-',
            '?': '',
            '*': 'x',
        }
        
        sanitized = title
        for illegal, replacement in illegal_chars.items():
            sanitized = sanitized.replace(illegal, replacement)
        
        # Clean up multiple spaces
        while '  ' in sanitized:
            sanitized = sanitized.replace('  ', ' ')
        
        return sanitized.strip()


# Convenience function for scripts
def build_cache_from_tmdb(
    api_key: str,
    show_name: str,
    year: Optional[int] = None,
    tmdb_id: Optional[int] = None,
    output_path: Optional[Path] = None
) -> Dict:
    """
    Build episode cache from TMDB data (legacy interface)
    
    Args:
        api_key: TMDB API key
        show_name: Name of the TV show
        year: Optional year to help identify the show
        tmdb_id: Optional TMDB ID if known
        output_path: Optional custom output path
        
    Returns:
        Cache data dictionary
    """
    backend = TMDBBackend(api_key)
    
    # Search for show if no ID provided
    if tmdb_id is None:
        shows = backend.search_shows(show_name, year)
        if not shows:
            raise TMDBNotFoundError(f"Show not found: {show_name}")
        tmdb_id = shows[0]['id']
    
    # Generate cache
    _, cache = backend.generate_cache(tmdb_id, show_name, output_path)
    return cache
