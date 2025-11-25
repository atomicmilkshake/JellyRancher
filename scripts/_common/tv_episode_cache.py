#!/usr/bin/env python3
"""
TV Episode Cache Manager

Manages canonical TV episode data from Wikipedia.
Provides episode title verification, numbering validation, and caching.

Cache Structure:
._state/tv_episode_cache/{show_id}.json
{
    "show_title": "Breaking Bad",
    "show_id": "breaking_bad",
    "source": "wikipedia",
    "last_updated": "2024-01-15T10:30:00Z",
    "seasons": {
        "1": {
            "episodes": {
                "1": {
                    "title": "Pilot",
                    "air_date": "2008-01-20",
                    "canonical_title": "Pilot",
                    "alternate_titles": ["Pilot (Part 1)"],
                    "special_type": null
                },
                "2": {
                    "title": "Cat's in the Bag...",
                    "air_date": "2008-01-27",
                    "canonical_title": "Cat's in the Bag...",
                    "alternate_titles": [],
                    "special_type": null
                }
            }
        }
    },
    "specials": {
        "1": {
            "title": "Behind the Scenes",
            "air_date": "2009-03-15",
            "canonical_title": "Behind the Scenes",
            "alternate_titles": [],
            "special_type": "behind_the_scenes"
        }
    }
}
"""

import json
import hashlib
import logging
from pathlib import Path
from typing import Dict, Optional, List, Any
from datetime import datetime, timedelta
import requests
from urllib.parse import quote
import re
from bs4 import BeautifulSoup
import time

logger = logging.getLogger(__name__)

class TVEpisodeCache:
    """Manages canonical TV episode data caching and retrieval."""

    def __init__(self, cache_dir: Path = None):
        if cache_dir is None:
            cache_dir = Path("._state/tv_episode_cache")
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # HTML cache for development (temporary)
        self.html_cache_dir = Path("._state/html_cache")
        self.html_cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cached_html(self, url: str) -> Optional[str]:
        """Get cached HTML content for a URL."""
        import hashlib
        url_hash = hashlib.md5(url.encode()).hexdigest()
        cache_file = self.html_cache_dir / f"{url_hash}.html"

        if cache_file.exists():
            try:
                return cache_file.read_text(encoding='utf-8')
            except:
                return None
        return None

    def _set_cached_html(self, url: str, html: str):
        """Cache HTML content for a URL."""
        import hashlib
        url_hash = hashlib.md5(url.encode()).hexdigest()
        cache_file = self.html_cache_dir / f"{url_hash}.html"

        try:
            cache_file.write_text(html, encoding='utf-8')
        except:
            pass  # Ignore cache write failures

    def get_show_id(self, show_title: str) -> str:
        """Generate a consistent show ID from title."""
        # Normalize title for ID generation
        normalized = show_title.lower()
        normalized = ''.join(c for c in normalized if c.isalnum() or c in ' -_')
        normalized = normalized.replace(' ', '_').replace('-', '_')
        # Remove duplicate underscores
        while '__' in normalized:
            normalized = normalized.replace('__', '_')
        return normalized.strip('_')

    def get_cache_path(self, show_id: str) -> Path:
        """Get the cache file path for a show."""
        return self.cache_dir / f"{show_id}.json"

    def is_cache_valid(self, show_id: str, max_age_days: int = 90) -> bool:
        """Check if cached data is still valid (not too old)."""
        cache_path = self.get_cache_path(show_id)
        if not cache_path.exists():
            return False

        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            last_updated = datetime.fromisoformat(data.get('last_updated', '2000-01-01T00:00:00'))
            age = datetime.now() - last_updated
            return age.days < max_age_days
        except (json.JSONDecodeError, KeyError, ValueError):
            return False

    def get_cached_episode_data(self, show_title: str) -> Optional[Dict[str, Any]]:
        """Get cached episode data for a show."""
        show_id = self.get_show_id(show_title)
        cache_path = self.get_cache_path(show_id)

        if not cache_path.exists():
            return None

        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return None

    def save_episode_data(self, show_title: str, episode_data: Dict[str, Any]) -> None:
        """Save episode data to cache."""
        show_id = self.get_show_id(show_title)
        cache_path = self.get_cache_path(show_id)

        # Add metadata
        episode_data['show_id'] = show_id
        episode_data['last_updated'] = datetime.now().isoformat()

        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(episode_data, f, indent=2, ensure_ascii=False)

    def get_looney_tunes_data(self) -> Optional[Dict[str, Any]]:
        """Load Looney Tunes data from the full filmography JSON file."""
        filmography_path = self.cache_dir / "looney_tunes_full_filmography.json"

        if not filmography_path.exists():
            print(f"❌ Looney Tunes filmography file not found: {filmography_path}")
            return None

        try:
            with open(filmography_path, 'r', encoding='utf-8') as f:
                filmography_data = json.load(f)

            # Convert the flat filmography to TVEpisodeCache format
            episode_data = {
                'show_title': 'Looney Tunes (1930)',
                'source': filmography_data.get('source', 'Looney Tunes Cartoon Checklist'),
                'seasons': {}
            }

            # Group episodes by year (each year becomes a season)
            year_groups = {}
            for entry in filmography_data.get('entries', []):
                year = entry.get('year', 'Unknown')
                if year not in year_groups:
                    year_groups[year] = []
                year_groups[year].append(entry)

            # Sort years chronologically
            sorted_years = sorted(year_groups.keys(), key=lambda x: int(x) if x.isdigit() else 9999)

            # Create seasons
            for season_num, year in enumerate(sorted_years, 1):
                episodes = year_groups[year]
                season_data = {
                    'season_number': season_num,
                    'episodes': {}
                }

                # Sort episodes within year by global_index
                episodes.sort(key=lambda x: x.get('global_index', 9999))

                for ep_num, entry in enumerate(episodes, 1):
                    season_data['episodes'][str(ep_num)] = {
                        'episode_number': ep_num,
                        'canonical_title': entry.get('title', f'Unknown Title {ep_num}'),
                        'alternate_titles': [],
                        'air_date': f"{entry.get('year', '1930')}-01-01",  # Use year as approximate air date
                        'year': entry.get('year'),
                        'global_index': entry.get('global_index')
                    }

                episode_data['seasons'][str(season_num)] = season_data

            return episode_data

        except (json.JSONDecodeError, KeyError, FileNotFoundError) as e:
            print(f"❌ Error loading Looney Tunes filmography: {e}")
            return None

    def _cached_get(self, url: str, headers: dict = None, timeout: int = 10) -> requests.Response:
        """Get URL with caching for development."""
        # Check cache first
        cached_content = self._get_cached_html(url)
        if cached_content is not None:
            print(f"📋 Using cached content for: {url}")
            # Create a mock response object
            class MockResponse:
                def __init__(self, content, is_json=False):
                    self._text = content
                    self.status_code = 200
                    self._is_json = is_json
                    if is_json:
                        self.content = content.encode('utf-8')
                    else:
                        self.content = content.encode('utf-8')

                def raise_for_status(self):
                    pass

                def json(self):
                    import json
                    return json.loads(self._text)

                @property
                def text(self):
                    return self._text

            # Detect if this is JSON content (Wikipedia API calls)
            is_json = 'api.php' in url or cached_content.strip().startswith('{')
            return MockResponse(cached_content, is_json)

        # Not cached, make real request
        print(f"🌐 Fetching: {url}")
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()

        # Cache the response (JSON for APIs, text for HTML)
        if 'api.php' in url:
            # For JSON APIs, cache the JSON string
            self._set_cached_html(url, response.text)
        else:
            # For HTML pages, cache the HTML
            self._set_cached_html(url, response.text)

        return response

    def fetch_wikipedia_episodes(self, show_title: str) -> Optional[Dict[str, Any]]:
        """Fetch episode data from Wikipedia with intelligent search variations."""
        # Add delay to avoid hammering Wikipedia (11 seconds between requests)
        print("⏳ Respecting Wikipedia - waiting 11 seconds before fetch...")
        time.sleep(11)

        try:
            # Set a proper User-Agent to avoid 403 errors
            headers = {
                'User-Agent': 'Jellyfin-Organizer/1.0 (https://github.com/your-repo; contact@example.com)'
            }

            # Generate multiple search variations
            search_variations = self._generate_search_variations(show_title)
            print(f"🔍 Generated {len(search_variations)} search variations for '{show_title}':")
            for i, var in enumerate(search_variations[:5], 1):  # Show first 5
                print(f"   {i}. '{var}'")
            if len(search_variations) > 5:
                print(f"   ... and {len(search_variations) - 5} more")

            # Try each variation
            for variation in search_variations:
                print(f"\n🔍 Trying variation: '{variation}'")

                # Try different search suffixes
                suffixes = [' episodes', ' (TV series)', '']
                for suffix in suffixes:
                    search_term = variation + suffix
                    search_url = f"https://en.wikipedia.org/w/api.php?action=opensearch&search={quote(search_term)}&limit=5&format=json"
                    print(f"   📡 Searching: {search_url}")

                    try:
                        response = self._cached_get(search_url, headers=headers, timeout=10)
                        response.raise_for_status()
                        search_results = response.json()

                        if search_results and len(search_results) >= 4 and search_results[3]:
                            # Check each result
                            for i, result_url in enumerate(search_results[3]):
                                result_title = search_results[1][i] if i < len(search_results[1]) else "Unknown"
                                print(f"   📋 Result {i+1}: '{result_title}' -> {result_url}")

                                # Check if this looks like an episode page
                                if self._is_episode_page_url(result_url, variation):
                                    print(f"   ✅ Found potential episode page: {result_url}")
                                    page_url = result_url
                                    break
                                # Also accept main pages that closely match the show name
                                elif self._is_main_page_url(result_url, variation):
                                    print(f"   ✅ Found main page for show: {result_url}")
                                    page_url = result_url
                                    break
                            else:
                                continue
                            break  # Found a good result
                        else:
                            print(f"   📋 No results for '{search_term}'")

                    except Exception as e:
                        print(f"   ❌ Search failed for '{search_term}': {e}")
                        continue

                if 'page_url' in locals():
                    break  # We found a page URL

            if 'page_url' not in locals():
                print(f"❌ No suitable Wikipedia page found for '{show_title}' after trying all variations")
                return None

            print(f"📖 Found Wikipedia page: {page_url}")

            # Check if this is an episode list page
            if 'episodes' not in page_url.lower():
                # Try to find the episode list page by searching for links
                response = self._cached_get(page_url, headers=headers, timeout=10)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'lxml')

                # Look for episode list links with multiple patterns
                episode_link = None

                # Try multiple patterns for episode list links
                patterns = [
                    r'List of .* episodes',
                    r'.* episodes',
                    r'Episodes',
                    r'Episode list'
                ]

                for pattern in patterns:
                    candidate_links = soup.find_all('a', string=re.compile(pattern, re.IGNORECASE))
                    for link in candidate_links:
                        href = link.get('href', '')
                        # Only accept Wikipedia internal links
                        if href.startswith('/wiki/') and 'episodes' in href.lower():
                            episode_link = link
                            break
                    if episode_link:
                        break

                # Also check link titles and hrefs
                if not episode_link:
                    all_links = soup.find_all('a', href=re.compile(r'/wiki/.*episodes?', re.IGNORECASE))
                    for link in all_links:
                        link_text = link.get_text().strip()
                        href = link.get('href')
                        # Only accept Wikipedia links, not external sites
                        if href and href.startswith('/wiki/') and any(keyword in link_text.lower() for keyword in ['episode', 'list']):
                            episode_link = link
                            break

                if episode_link:
                    href = episode_link.get('href')
                    if href.startswith('http'):
                        episode_url = href
                    else:
                        episode_url = 'https://en.wikipedia.org' + href
                    
                    # Validate that the episode list page is relevant to the show
                    link_text = episode_link.get_text().strip()
                    show_words = set(show_title.lower().split())
                    link_words = set(link_text.lower().split())
                    
                    # Check if the link is specifically about this show
                    # For shows like Looney Tunes, avoid generic cartoon lists
                    relevant_keywords = ['episode', 'season', 'series']
                    has_relevant_keyword = any(keyword in link_text.lower() for keyword in relevant_keywords)
                    
                    # For anthology shows or collections, be more restrictive
                    if 'looney' in show_title.lower() or 'toon' in show_title.lower():
                        # For Looney Tunes, only accept links that mention the show specifically
                        show_specific = any(word in link_text.lower() for word in ['looney', 'tunes', 'toon'])
                        if not show_specific:
                            print(f"⚠️  Skipping irrelevant episode list link for anthology show: {link_text}")
                            episode_link = None
                    
                    if episode_link:
                        print(f"📖 Found episode list page: {episode_url}")
                        page_url = episode_url
                        response = requests.get(page_url, headers=headers, timeout=10)
                        response.raise_for_status()
                        soup = BeautifulSoup(response.content, 'lxml')
                    else:
                        print(f"⚠️  No relevant episode list link found, using main page")
                else:
                    print(f"⚠️  No episode list link found, using main page")
                    # For shows like Stranger Things, try searching for season-specific pages
                    season_links = soup.find_all('a', href=re.compile(r'/wiki/.*season.*\d+', re.IGNORECASE))
                    if season_links:
                        # Try the first season page
                        season_url = 'https://en.wikipedia.org' + season_links[0].get('href')
                        print(f"📖 Trying season page: {season_url}")
                        try:
                            response = self._cached_get(season_url, headers=headers, timeout=10)
                            response.raise_for_status()
                            soup = BeautifulSoup(response.content, 'lxml')
                            page_url = season_url
                        except:
                            print(f"⚠️  Season page failed, using main page")

            # Fetch the page content (if not already fetched)
            if 'soup' not in locals():
                response = self._cached_get(page_url, headers=headers, timeout=10)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'lxml')

            # Try to find episode tables (this is a simplified approach)
            episode_data = self._parse_wikipedia_episodes(soup, show_title)

            if episode_data:
                episode_data['wikipedia_url'] = page_url
                return episode_data

            print(f"❌ Could not parse episode data from Wikipedia page")
            return None

        except Exception as e:
            print(f"❌ Error fetching Wikipedia data for '{show_title}': {e}")
            return None

    def _parse_wikipedia_episodes(self, soup: BeautifulSoup, show_title: str) -> Optional[Dict[str, Any]]:
        """Parse episode data from Wikipedia page HTML with multiple strategies."""
        episode_data = {
            'show_title': show_title,
            'seasons': {},
            'specials': {}
        }

        # Strategy 1: Enhanced standard table parsing
        episodes_found = self._parse_standard_tables_enhanced(soup, episode_data)
        if episodes_found > 0:
            total_episodes = sum(len(season['episodes']) for season in episode_data['seasons'].values())
            print(f"✅ Parsed {total_episodes} episodes across {len(episode_data['seasons'])} seasons")
            return episode_data

        # Strategy 2: Infobox episode lists
        episodes_found = self._parse_infobox_episodes(soup, episode_data)
        if episodes_found > 0:
            total_episodes = sum(len(season['episodes']) for season in episode_data['seasons'].values())
            print(f"✅ Parsed {total_episodes} episodes from infobox")
            return episode_data

        # Strategy 3: Alternative table formats
        episodes_found = self._parse_alternative_tables(soup, episode_data)
        if episodes_found > 0:
            total_episodes = sum(len(season['episodes']) for season in episode_data['seasons'].values())
            print(f"✅ Parsed {total_episodes} episodes from alternative format")
            return episode_data

        # Strategy 4: List-based parsing (fallback)
        episodes_found = self._parse_list_episodes(soup, episode_data)
        if episodes_found > 0:
            total_episodes = sum(len(season['episodes']) for season in episode_data['seasons'].values())
            print(f"✅ Parsed {total_episodes} episodes from list format")
            return episode_data

        # Strategy 5: Season summary table parsing (for shows like Batman)
        episodes_found = self._parse_season_summary_table(soup, episode_data)
        if episodes_found > 0:
            total_episodes = sum(len(season['episodes']) for season in episode_data['seasons'].values())
            print(f"✅ Parsed {total_episodes} episodes from season summary")
            return episode_data

        return None

    def _parse_standard_tables_enhanced(self, soup: BeautifulSoup, episode_data: Dict[str, Any]) -> int:
        """Enhanced standard table parsing with flexible column detection."""
        episodes_found = 0

        # Find all tables that look like episode tables
        tables = soup.find_all('table', {'class': re.compile(r'wikitable.*')})
        print(f"📊 Found {len(tables)} wikitable tables on the page")

        for i, table in enumerate(tables):
            # Check if this is an episode table by looking at headers
            headers = table.find_all('th')
            if not headers:
                continue

            header_texts = [h.get_text().strip().lower() for h in headers]
            print(f"📋 Table {i+1} headers: {header_texts[:6]}...")  # Show first 6 headers

            # Enhanced episode table detection
            has_episode_info = any(
                'episode' in h or 'no.' in h or 'no. in' in h or 
                'season' in h or 'series' in h or '#' in h
                for h in header_texts
            )
            has_title = any('title' in h for h in header_texts)

            if not (has_episode_info and has_title):
                continue

            print(f"📊 Found episode table with headers: {header_texts[:5]}...")

            # Try to determine the season for this table
            season_num = self._get_table_season_enhanced(table, soup)
            if season_num is None:
                print(f"⚠️  Could not determine season for table {i+1}")
                continue

            print(f"📅 Table {i+1} is for Season {season_num}")

            # Parse the table rows with enhanced logic
            table_episodes = self._parse_table_rows_enhanced(table, header_texts, season_num, episode_data)
            episodes_found += table_episodes

        return episodes_found

    def _get_table_season_enhanced(self, table, soup) -> Optional[int]:
        """Enhanced season detection with multiple strategies."""
        # Strategy 1: Table ID
        table_id = table.get('id', '')
        if table_id:
            season_match = re.search(r'season[_-]?(\d+)', table_id, re.IGNORECASE)
            if season_match:
                return int(season_match.group(1))

        # Strategy 2: Caption
        caption = table.find('caption')
        if caption:
            caption_text = caption.get_text().strip()
            season_match = re.search(r'(?:season|series)\s+(\d+)', caption_text, re.IGNORECASE)
            if season_match:
                return int(season_match.group(1))

        # Strategy 3: Preceding headers (expanded search)
        for level in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            prev_header = table.find_previous(level)
            if prev_header:
                header_text = prev_header.get_text().strip()
                season_match = re.search(r'(?:season|series)\s+(\d+)', header_text, re.IGNORECASE)
                if season_match:
                    return int(season_match.group(1))

        # Strategy 4: Span with season class
        season_span = table.find_previous('span', {'class': re.compile(r'season|series', re.IGNORECASE)})
        if season_span:
            span_text = season_span.get_text().strip()
            season_match = re.search(r'(\d+)', span_text)
            if season_match:
                return int(season_match.group(1))

        # Strategy 5: Look for season info in nearby text
        prev_siblings = []
        current = table.previous_sibling
        for _ in range(10):  # Check up to 10 previous siblings
            if current:
                if hasattr(current, 'get_text'):
                    text = current.get_text().strip()
                    if text:
                        prev_siblings.append(text)
                current = current.previous_sibling
            else:
                break

        for text in prev_siblings:
            season_match = re.search(r'(?:season|series)\s+(\d+)', text, re.IGNORECASE)
            if season_match:
                return int(season_match.group(1))

        return None

    def _parse_table_rows_enhanced(self, table, header_texts: List[str], season_num: int, episode_data: Dict[str, Any]) -> int:
        """Parse table rows with enhanced flexibility."""
        episodes_found = 0

        # Create column mapping
        col_map = self._create_column_mapping(header_texts)

        # Parse data rows
        rows = table.find_all('tr')[1:]  # Skip header row

        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) < 2:
                continue

            # Extract episode information
            episode_info = self._extract_episode_from_cells(cells, col_map, season_num)
            if episode_info:
                # Add to episode data structure
                season_key = str(episode_info['season'])
                episode_key = str(episode_info['episode'])

                if season_key not in episode_data['seasons']:
                    episode_data['seasons'][season_key] = {
                        'season_number': episode_info['season'],
                        'episodes': {}
                    }

                episode_data['seasons'][season_key]['episodes'][episode_key] = {
                    'episode_number': episode_info['episode'],
                    'canonical_title': episode_info['title'],
                    'alternate_titles': [],
                    'air_date': episode_info.get('air_date')
                }

                episodes_found += 1

        return episodes_found

    def _create_column_mapping(self, headers: List[str]) -> Dict[str, int]:
        """Create flexible column mapping for different table formats."""
        col_map = {}

        # Common column name variations
        season_patterns = [
            r'^\s*season', r'^\s*series'
        ]
        episode_in_season_patterns = [
            r'^\s*no\.\s*in\s*season', r'^\s*no\.\s*in\s*series',
            r'^\s*no\.\s*inseason', r'^\s*no\.inseas', r'^\s*ep\s*no',
            r'^\s*episode\s*no'
        ]
        episode_patterns = [
            r'^\s*no\.\s*overall', r'^\s*overall', r'^\s*#',
            r'^\s*ep\.\s*no', r'^\s*episode\s*number'
        ]
        title_patterns = [
            r'^\s*title', r'^\s*episode\s*title', r'^\s*episode\s*name'
        ]
        air_date_patterns = [
            r'^\s*original\s*air\s*date', r'^\s*air\s*date',
            r'^\s*first\s*aired', r'^\s*original\s*release'
        ]

        for i, header in enumerate(headers):
            header_lower = header.lower()

            if any(re.search(pattern, header_lower) for pattern in season_patterns):
                col_map['season'] = i
            elif any(re.search(pattern, header_lower) for pattern in episode_in_season_patterns):
                col_map['episode_in_season'] = i
            elif any(re.search(pattern, header_lower) for pattern in episode_patterns):
                col_map['episode_overall'] = i
            elif any(re.search(pattern, header_lower) for pattern in title_patterns):
                col_map['title'] = i
            elif any(re.search(pattern, header_lower) for pattern in air_date_patterns):
                col_map['air_date'] = i

        return col_map

    def _extract_episode_from_cells(self, cells, col_map: Dict[str, int], default_season: int) -> Optional[Dict[str, Any]]:
        """Extract episode data from table cells with flexible parsing."""
        try:
            # Get title (required)
            if 'title' not in col_map:
                # Try positional guessing for title
                title_candidates = []
                for i, cell in enumerate(cells):
                    text = cell.get_text().strip()
                    # Title is usually substantial text, not just numbers
                    if len(text) > 3 and not text.replace('.', '').replace('-', '').isdigit():
                        title_candidates.append((i, text))

                if title_candidates:
                    # Choose the most substantial title candidate
                    title_candidates.sort(key=lambda x: len(x[1]), reverse=True)
                    title_idx, title = title_candidates[0]
                else:
                    return None
            else:
                title_idx = col_map['title']
                title = cells[title_idx].get_text().strip() if title_idx < len(cells) else ""

            # Clean title
            title = self._clean_episode_title(title)
            if not title or title.lower() in ['tba', 'to be announced', 'n/a']:
                return None

            # Get episode number - prefer season-relative over overall
            episode_num = None
            season_num = default_season

            # Try episode-in-season first (preferred for Jellyfin)
            if 'episode_in_season' in col_map and col_map['episode_in_season'] < len(cells):
                episode_text = cells[col_map['episode_in_season']].get_text().strip()
                episode_num = self._extract_number(episode_text)

            # Fall back to overall episode number if no season-relative available
            if episode_num is None and 'episode_overall' in col_map and col_map['episode_overall'] < len(cells):
                episode_text = cells[col_map['episode_overall']].get_text().strip()
                episode_num = self._extract_number(episode_text)

            # If no episode number found, try to infer from position or content
            if episode_num is None:
                # Look for S01E01 patterns in any cell
                for cell in cells:
                    cell_text = cell.get_text().strip()
                    match = re.search(r'S(\d+)E(\d+)', cell_text, re.IGNORECASE)
                    if match:
                        season_num = int(match.group(1))
                        episode_num = int(match.group(2))
                        break

                # If still no episode number, use row position as fallback
                if episode_num is None:
                    episode_num = 1  # Will be corrected by sorting

            # Get air date if available
            air_date = None
            if 'air_date' in col_map and col_map['air_date'] < len(cells):
                date_cell = cells[col_map['air_date']]
                air_date = self._extract_air_date(date_cell)

            return {
                'season': season_num,
                'episode': episode_num,
                'title': title,
                'air_date': air_date
            }

        except (IndexError, AttributeError, ValueError):
            return None

    def _clean_episode_title(self, title: str) -> str:
        """Clean and normalize episode title."""
        if not title:
            return ""

        # Remove quotes
        title = re.sub(r'["""]', '', title)

        # Remove footnotes like [1], [2], etc.
        title = re.sub(r'\[.*?\]', '', title)

        # Remove extra whitespace
        title = ' '.join(title.split())

        return title.strip()

    def _extract_number(self, text: str) -> Optional[int]:
        """Extract the first number from text."""
        if not text:
            return None

        match = re.search(r'\d+', text)
        return int(match.group()) if match else None

    def _extract_air_date(self, cell) -> Optional[str]:
        """Extract air date from cell."""
        if not cell:
            return None

        text = cell.get_text().strip()

        # Look for date patterns
        # Common formats: "January 1, 2020", "2020-01-01", "1 Jan 2020"
        date_patterns = [
            r'(\w+)\s+(\d{1,2}),\s+(\d{4})',  # January 1, 2020
            r'(\d{4})-(\d{2})-(\d{2})',        # 2020-01-01
            r'(\d{1,2})\s+(\w+)\s+(\d{4})',    # 1 Jan 2020
        ]

        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                return text  # Return the original text for now

        return None

    def _parse_infobox_episodes(self, soup: BeautifulSoup, episode_data: Dict[str, Any]) -> int:
        """Parse episode data from infobox episode lists."""
        # Implementation for infobox parsing
        # This would handle shows that list episodes in infoboxes rather than tables
        return 0

    def _parse_alternative_tables(self, soup: BeautifulSoup, episode_data: Dict[str, Any]) -> int:
        """Parse non-standard table formats like The Simpsons individual episode tables."""
        episodes_found = 0

        # Strategy for The Simpsons: individual episode tables
        # Each table contains a single episode, not a season
        tables = soup.find_all('table', {'class': re.compile(r'wikitable.*')})

        for table in tables:
            headers = table.find_all('th')
            if not headers:
                continue

            header_texts = [h.get_text().strip().lower() for h in headers]

            # Check if this looks like a Simpsons-style episode table
            has_title = any('title' in h for h in header_texts)
            has_directed = any('directed' in h for h in header_texts)
            has_written = any('written' in h for h in header_texts)
            has_air_date = any('air date' in h or 'original' in h for h in header_texts)

            # For The Simpsons unusual format, check if we have multiple episode titles in headers
            episode_titles_in_headers = [h for h in header_texts if h and len(h) > 5 and not any(keyword in h.lower() for keyword in ['title', 'directed', 'written', 'original', 'air', 'release', 'date'])]

            if has_title and has_directed and has_written and has_air_date and episode_titles_in_headers:
                # This is the Simpsons format with episode titles as column headers
                table_episodes = self._parse_simpsons_multi_episode_table(table, header_texts, episode_data)
                episodes_found += table_episodes

        return episodes_found

    def _parse_individual_episode_table(self, table, header_texts: List[str]) -> Optional[Dict[str, Any]]:
        """Parse a table containing information about a single episode (Simpsons format)."""
        try:
            # For The Simpsons, the table headers themselves are episode titles!
            # The format is: Title | Directed by | Written by | Original release date | Episode1 | Episode2 | ...

            # Find the main title column (usually the first one)
            title_idx = 0  # Assume first column is the main title

            # Get the data row
            rows = table.find_all('tr')[1:]
            if not rows:
                return None

            row = rows[0]
            cells = row.find_all(['td', 'th'])

            if title_idx >= len(cells):
                return None

            # Extract the main episode title
            title_cell = cells[title_idx]
            title = title_cell.get_text().strip()
            title = self._clean_episode_title(title)

            if not title or title.lower() in ['tba', 'to be announced']:
                return None

            # For episode number, we need to use the table position on the page
            # This is a fallback - ideally we'd parse from context
            episode_num = 1  # Will need better logic

            # Get air date - look for date column
            air_date = None
            for i, header in enumerate(header_texts):
                if ('air date' in header.lower() or 'original' in header.lower() or 'release' in header.lower()) and i < len(cells):
                    date_cell = cells[i]
                    air_date = self._extract_air_date(date_cell)
                    break

            # For season, default to 1 for now
            season_num = 1

            return {
                'season': season_num,
                'episode': episode_num,
                'title': title,
                'air_date': air_date
            }

        except (IndexError, AttributeError):
            return None

    def _parse_simpsons_multi_episode_table(self, table, header_texts: List[str], episode_data: Dict[str, Any]) -> int:
        """Parse Simpsons tables where episode titles are column headers."""
        episodes_found = 0

        try:
            # Find indices of metadata columns vs episode title columns
            metadata_indices = []
            episode_title_indices = []

            for i, header in enumerate(header_texts):
                header_lower = header.lower()
                if any(keyword in header_lower for keyword in ['title', 'directed', 'written', 'original', 'air', 'release', 'date']):
                    metadata_indices.append(i)
                else:
                    # Assume this is an episode title
                    episode_title_indices.append(i)

            if not episode_title_indices:
                return 0

            # Get data rows
            rows = table.find_all('tr')[1:]  # Skip header row

            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) < max(metadata_indices + episode_title_indices) + 1:
                    continue

                # Extract metadata for this row
                directed_by = ""
                written_by = ""
                air_date = ""

                for i in metadata_indices:
                    if i < len(cells):
                        cell_text = cells[i].get_text().strip()
                        header = header_texts[i].lower()
                        if 'directed' in header:
                            directed_by = cell_text
                        elif 'written' in header:
                            written_by = cell_text
                        elif 'air' in header or 'original' in header or 'release' in header:
                            air_date = cell_text

                # Now extract each episode from the title columns
                for ep_idx in episode_title_indices:
                    if ep_idx < len(cells):
                        episode_title = cells[ep_idx].get_text().strip()
                        episode_title = self._clean_episode_title(episode_title)

                        if episode_title and episode_title.lower() not in ['tba', 'to be announced']:
                            # For episode/season numbers, we'll use defaults since Simpsons format doesn't include them
                            season_num = 1  # Would need better logic
                            episode_num = episodes_found + 1  # Sequential numbering

                            season_key = str(season_num)
                            if season_key not in episode_data['seasons']:
                                episode_data['seasons'][season_key] = {
                                    'season_number': season_num,
                                    'episodes': {}
                                }

                            episode_key = str(episode_num)
                            episode_data['seasons'][season_key]['episodes'][episode_key] = {
                                'episode_number': episode_num,
                                'canonical_title': episode_title,
                                'alternate_titles': [],
                                'air_date': air_date if air_date else None
                            }

                            episodes_found += 1

        except Exception:
            pass

        return episodes_found

    def _get_simpsons_season(self, table, soup) -> Optional[int]:
        """Determine season for Simpsons-style tables."""
        # Look for season information in nearby headers or table content
        for level in ['h1', 'h2', 'h3', 'h4']:
            prev_header = table.find_previous(level)
            if prev_header:
                header_text = prev_header.get_text().strip()
                # Look for patterns like "Season 1", "The Simpsons (season 1)", etc.
                season_match = re.search(r'(?:season|series)\s+(\d+)', header_text, re.IGNORECASE)
                if season_match:
                    return int(season_match.group(1))

        # Check table caption
        caption = table.find('caption')
        if caption:
            caption_text = caption.get_text().strip()
            season_match = re.search(r'(?:season|series)\s+(\d+)', caption_text, re.IGNORECASE)
            if season_match:
                return int(season_match.group(1))

        return None

    def _parse_simpsons_table(self, table, header_texts: List[str], season_num: int, episode_data: Dict[str, Any]) -> int:
        """Parse a Simpsons-style episode table."""
        episodes_found = 0

        # Create column mapping for Simpsons format
        col_map = {}
        for i, header in enumerate(header_texts):
            header_lower = header.lower()
            if 'no.' in header_lower or 'no. in' in header_lower:
                col_map['episode'] = i
            elif 'title' in header_lower:
                col_map['title'] = i
            elif 'air date' in header_lower or 'original' in header_lower:
                col_map['air_date'] = i

        # Parse rows
        rows = table.find_all('tr')[1:]  # Skip header

        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) < 2:
                continue

            cell_texts = [cell.get_text().strip() for cell in cells]

            # Extract episode info
            episode_info = self._extract_simpsons_episode(cells, col_map, season_num)
            if episode_info:
                # Add to episode data
                season_key = str(episode_info['season'])
                episode_key = str(episode_info['episode'])

                if season_key not in episode_data['seasons']:
                    episode_data['seasons'][season_key] = {
                        'season_number': episode_info['season'],
                        'episodes': {}
                    }

                episode_data['seasons'][season_key]['episodes'][episode_key] = {
                    'episode_number': episode_info['episode'],
                    'canonical_title': episode_info['title'],
                    'alternate_titles': [],
                    'air_date': episode_info.get('air_date')
                }

                episodes_found += 1

        return episodes_found

    def _extract_simpsons_episode(self, cells, col_map: Dict[str, int], default_season: int) -> Optional[Dict[str, Any]]:
        """Extract episode info from Simpsons table cells."""
        try:
            # Get title
            if 'title' not in col_map:
                return None

            title_cell = cells[col_map['title']]
            title = title_cell.get_text().strip()
            title = self._clean_episode_title(title)

            if not title or title.lower() in ['tba', 'to be announced']:
                return None

            # Get episode number
            episode_num = None
            if 'episode' in col_map:
                episode_text = cells[col_map['episode']].get_text().strip()
                episode_num = self._extract_number(episode_text)

            # If no episode number, try to infer from row position
            if episode_num is None:
                episode_num = 1  # Will be corrected by sorting

            # Get air date
            air_date = None
            if 'air_date' in col_map and col_map['air_date'] < len(cells):
                date_cell = cells[col_map['air_date']]
                air_date = self._extract_air_date(date_cell)

            return {
                'season': default_season,
                'episode': episode_num,
                'title': title,
                'air_date': air_date
            }

        except (IndexError, AttributeError):
            return None

    def _parse_list_episodes(self, soup: BeautifulSoup, episode_data: Dict[str, Any]) -> int:
        """Parse episode data from list formats (fallback)."""
        # Implementation for list-based parsing
        return 0

    def _parse_season_summary_table(self, soup: BeautifulSoup, episode_data: Dict[str, Any]) -> int:
        """Parse season summary tables for shows that don't have detailed episode tables."""
        episodes_found = 0

        # Look for tables with season and episodes columns
        tables = soup.find_all('table', {'class': re.compile(r'wikitable.*')})

        for table in tables:
            headers = table.find_all('th')
            if not headers:
                continue

            header_texts = [h.get_text().strip().lower() for h in headers]

            # Check if this looks like a season summary table
            has_season = any('season' in h for h in header_texts)
            has_episodes = any('episodes' in h or 'episode' in h for h in header_texts)

            if not (has_season and has_episodes):
                continue

            print(f"📊 Found season summary table with headers: {header_texts[:4]}...")

            # Find column indices
            season_col = None
            episodes_col = None

            for i, header in enumerate(header_texts):
                if 'season' in header:
                    season_col = i
                elif 'episodes' in header or ('episode' in header and 'no' not in header):
                    episodes_col = i

            if season_col is None or episodes_col is None:
                continue

            # Parse the table rows
            rows = table.find_all('tr')[1:]  # Skip header row

            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) <= max(season_col, episodes_col):
                    continue

                season_text = cells[season_col].get_text().strip()
                episodes_text = cells[episodes_col].get_text().strip()

                # Extract season number
                season_match = re.search(r'(\d+)', season_text)
                if not season_match:
                    continue
                season_num = int(season_match.group(1))

                # Extract episode count
                episodes_match = re.search(r'(\d+)', episodes_text)
                if not episodes_match:
                    continue
                episode_count = int(episodes_match.group(1))

                print(f"📅 Season {season_num}: {episode_count} episodes")

                # Create placeholder episodes for this season
                season_key = str(season_num)
                episode_data['seasons'][season_key] = {
                    'season_number': season_num,
                    'episodes': {}
                }

                # Create placeholder episodes
                for ep_num in range(1, episode_count + 1):
                    episode_key = str(ep_num)
                    episode_data['seasons'][season_key]['episodes'][episode_key] = {
                        'episode_number': ep_num,
                        'canonical_title': f"Episode {ep_num}",
                        'alternate_titles': [],
                        'air_date': None
                    }
                    episodes_found += 1

        return episodes_found

    def _get_table_season(self, table, soup) -> Optional[int]:
        """Determine which season a table belongs to."""
        # Look for season headers before the table
        # Common patterns: "Season 1", "Series 1", etc.

        # Check the table's id or caption
        table_id = table.get('id', '')
        if table_id:
            season_match = re.search(r'season[_-]?(\d+)', table_id, re.IGNORECASE)
            if season_match:
                return int(season_match.group(1))

        # Check for caption
        caption = table.find('caption')
        if caption:
            caption_text = caption.get_text().strip()
            season_match = re.search(r'(?:season|series)\s+(\d+)', caption_text, re.IGNORECASE)
            if season_match:
                return int(season_match.group(1))

        # Look for preceding headers
        prev_element = table.find_previous(['h1', 'h2', 'h3', 'h4', 'h5'])
        if prev_element:
            header_text = prev_element.get_text().strip()
            season_match = re.search(r'(?:season|series)\s+(\d+)', header_text, re.IGNORECASE)
            if season_match:
                return int(season_match.group(1))

        # Look for span with season class
        season_span = table.find_previous('span', {'class': re.compile(r'season|series', re.IGNORECASE)})
        if season_span:
            span_text = season_span.get_text().strip()
            season_match = re.search(r'(\d+)', span_text)
            if season_match:
                return int(season_match.group(1))

        return None

    def _parse_episode_row(self, cell_texts: List[str], headers: List[str], season_num: int) -> Optional[Dict[str, Any]]:
        """Parse a single episode row from the table."""
        if len(cell_texts) < 3:
            return None

        # Common Wikipedia episode table formats:
        # Format 1: No. overall | No. in season | Title | ...
        # Format 2: No. in season | Title | ... (no overall)
        # Format 3: Season | Episode | Title | ...

        # Find column indices
        overall_idx = None
        season_ep_idx = None
        title_idx = None

        for i, header in enumerate(headers):
            header_lower = header.lower()
            if 'no. overall' in header_lower or 'overall' in header_lower:
                overall_idx = i
            elif 'no. in season' in header_lower or 'no. inseason' in header_lower or 'in season' in header_lower or 'episode' in header_lower:
                season_ep_idx = i
            elif 'title' in header_lower:
                title_idx = i

        # If we can't find the basic columns, try positional guessing
        if title_idx is None:
            # Assume title is in position 2 or 3
            for i in [2, 3]:
                if i < len(cell_texts) and len(cell_texts[i]) > 0:
                    title_idx = i
                    break

        if title_idx is None or title_idx >= len(cell_texts):
            return None

        title = cell_texts[title_idx]

        # Clean up title (remove quotes, extra whitespace, and escaped characters)
        title = title.strip('"').strip("'").strip()
        # Remove escaped quotes
        title = title.replace('\\"', '"').replace("\\'", "'")
        # Clean up any remaining escape sequences
        title = title.replace('\\', '')

        # Skip if title looks like a header or is empty
        if not title or title.lower() in ['title', 'episode title', ''] or len(title) < 2:
            return None

        # Extract episode number from "No. in season" column
        episode_num = None
        if season_ep_idx is not None and season_ep_idx < len(cell_texts):
            season_ep_text = cell_texts[season_ep_idx]
            # Handle formats like "1", "01", "1–2" (multi-part), etc.
            match = re.match(r'^(\d+)', season_ep_text)
            if match:
                episode_num = int(match.group(1))

        # If we couldn't find episode number, skip this row
        if episode_num is None:
            return None

        return {
            'season': season_num,
            'episode': episode_num,
            'title': title
        }

    def get_episode_data(self, show_title: str, force_refresh: bool = False) -> Optional[Dict[str, Any]]:
        """Get episode data for a show, fetching if needed."""
        show_id = self.get_show_id(show_title)

        # Special handling for Looney Tunes - use full filmography instead of Wikipedia
        if 'looney' in show_title.lower() and 'tunes' in show_title.lower():
            print(f"🎬 Loading Looney Tunes data from full filmography...")
            episode_data = self.get_looney_tunes_data()
            if episode_data:
                # Save to cache for consistency
                self.save_episode_data(show_title, episode_data)
                print(f"✅ Successfully loaded Looney Tunes episode data ({len(episode_data.get('seasons', {}))} seasons)")
                return episode_data
            else:
                print(f"❌ Failed to load Looney Tunes filmography data")
                return None

        # Check cache first (unless force refresh)
        if not force_refresh and self.is_cache_valid(show_id):
            cached_data = self.get_cached_episode_data(show_title)
            if cached_data:
                print(f"✅ Using cached episode data for '{show_title}'")
                return cached_data

        # Try to fetch from Wikipedia
        print(f"🔍 Fetching episode data for '{show_title}' from Wikipedia...")
        episode_data = self.fetch_wikipedia_episodes(show_title)
        if episode_data:
            episode_data['source'] = 'wikipedia'
            self.save_episode_data(show_title, episode_data)
            print(f"✅ Successfully cached episode data from Wikipedia")
            return episode_data

        print(f"❌ No episode data found for '{show_title}' from Wikipedia")
        return None

    def _generate_search_variations(self, show_title: str) -> List[str]:
        """Generate multiple search variations for a show title."""
        variations = [show_title]  # Original

        # Remove year in parentheses
        import re
        title_no_year = re.sub(r'\s*\(\d{4}\)$', '', show_title)
        if title_no_year != show_title:
            variations.append(title_no_year)

        # Add colon variations for common patterns
        # "Batman The Animated Series" -> "Batman: The Animated Series"
        if ' The ' in title_no_year:
            parts = title_no_year.split(' The ', 1)
            if len(parts) == 2:
                colon_version = f"{parts[0]}: The {parts[1]}"
                variations.append(colon_version)

        # "Breaking Bad" -> "Breaking Bad (TV series)" etc.
        # Keep existing Star Trek logic
        if 'star trek' in title_no_year.lower():
            if 'next generation' in title_no_year.lower():
                variations.extend([
                    'Star Trek: The Next Generation',
                    'Star Trek TNG',
                    'TNG'
                ])
            elif 'voyager' in title_no_year.lower():
                variations.extend([
                    'Star Trek: Voyager',
                    'Star Trek Voyager'
                ])
            elif 'deep space nine' in title_no_year.lower():
                variations.extend([
                    'Star Trek: Deep Space Nine',
                    'Star Trek DS9',
                    'DS9'
                ])

        # Remove extra spaces and clean up
        variations = [v.strip() for v in variations if v.strip()]
        variations = list(set(variations))  # Remove duplicates

        return variations

    def _is_episode_page_url(self, url: str, show_name: str) -> bool:
        """Check if a URL looks like an episode list page for a specific show."""
        url_lower = url.lower()
        show_lower = show_name.lower()

        # Check for episode-related keywords
        episode_keywords = ['episode', 'episodes', 'list_of']
        has_episode_keyword = any(keyword in url_lower for keyword in episode_keywords)

        # Must have episode keyword
        if not has_episode_keyword:
            return False

        # Check for show-specific words (be more specific)
        show_words = []
        if 'star trek' in show_lower:
            # For Star Trek shows, require the specific series name
            if 'voyager' in show_lower:
                show_words = ['voyager']
            elif 'next generation' in show_lower or 'tng' in show_lower:
                show_words = ['next_generation', 'the_next_generation', 'tng']
            elif 'deep space nine' in show_lower or 'ds9' in show_lower:
                show_words = ['deep_space_nine', 'ds9']
            else:
                show_words = ['star_trek']
        else:
            # For other shows, use the show name words
            show_words = show_lower.replace(':', '').replace('(', '').replace(')', '').replace(' the ', ' ').split()

        # Require at least one significant show word to be in the URL
        significant_words = [word for word in show_words if len(word) > 2]
        show_in_url = any(word in url_lower for word in significant_words)

        # Additional check: avoid generic Star Trek pages
        if 'star_trek_episodes' in url_lower and 'voyager' not in url_lower and 'next_generation' not in url_lower and 'deep_space' not in url_lower:
            return False  # This is the generic Star Trek episodes page

        return show_in_url

    def _is_main_page_url(self, url: str, show_name: str) -> bool:
        """Check if a URL looks like a main show page (not episodes page)."""
        url_lower = url.lower()
        show_lower = show_name.lower()

        # Avoid video games, movies, etc.
        exclude_keywords = ['video_game', 'film', 'movie', 'soundtrack', 'comic']
        if any(keyword in url_lower for keyword in exclude_keywords):
            return False

        # Should be a Wikipedia page
        if not '/wiki/' in url:
            return False

        # Should contain show-related words
        show_words = show_lower.replace('(', '').replace(')', '').replace(':', '').split()
        show_words = [word for word in show_words if len(word) > 2]  # Skip short words

        # Check if URL contains key show words
        url_words = url_lower.replace('/wiki/', '').replace('_', ' ').split()
        matching_words = sum(1 for word in show_words if any(word in url_word for url_word in url_words))

        # Require at least 50% of significant words to match
        return matching_words >= len(show_words) * 0.5

    def verify_episode_title(self, show_title: str, season: int, episode: int,
                           parsed_title: str) -> Dict[str, Any]:
        """Verify a parsed episode title against canonical data."""
        episode_data = self.get_episode_data(show_title)

        if not episode_data:
            return {
                'verified': False,
                'canonical_title': None,
                'confidence': 0,
                'reason': 'no_canonical_data'
            }

        # Navigate to the specific episode
        season_key = str(season)
        episode_key = str(episode)

        try:
            episode_info = episode_data['seasons'][season_key]['episodes'][episode_key]
            canonical_title = episode_info['canonical_title']

            # Check if parsed title matches canonical or alternate titles
            if parsed_title == canonical_title:
                confidence = 100
            elif parsed_title in episode_info.get('alternate_titles', []):
                confidence = 90
            else:
                # Check for fuzzy matches (case insensitive, punctuation differences)
                parsed_lower = parsed_title.lower().replace('...', '').replace(' & ', ' and ')
                canonical_lower = canonical_title.lower().replace('...', '').replace(' & ', ' and ')

                if parsed_lower == canonical_lower:
                    confidence = 95
                elif parsed_lower in canonical_lower or canonical_lower in parsed_lower:
                    confidence = 70
                else:
                    confidence = 0

            return {
                'verified': confidence >= 70,
                'canonical_title': canonical_title,
                'confidence': confidence,
                'reason': 'title_match' if confidence >= 70 else 'title_mismatch'
            }

        except KeyError:
            return {
                'verified': False,
                'canonical_title': None,
                'confidence': 0,
                'reason': 'episode_not_found'
            }

    def get_corrected_episode_title(self, show_title: str, season: int, episode: int,
                                  parsed_title: str) -> str:
        """Get the corrected episode title, preferring canonical data."""
        verification = self.verify_episode_title(show_title, season, episode, parsed_title)

        if verification['verified'] and verification['canonical_title']:
            return verification['canonical_title']
        else:
            # Fall back to parsed title if canonical data unavailable or doesn't match
            return parsed_title