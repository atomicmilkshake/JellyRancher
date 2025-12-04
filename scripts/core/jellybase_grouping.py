#!/usr/bin/env python3
"""
JellyBase Smart Grouping - Automated collection creation

Provides smart grouping functions for creating collections:
- Group by genre (with fuzzy matching)
- Group by series (TV show detection)
- Group by franchise (Marvel, Star Wars, etc.)
- Group by director/actor
- Custom grouping rules
"""

import logging
from typing import List, Dict, Optional
from difflib import SequenceMatcher
from scripts.core.jellyfin_client import JellyfinClient

logger = logging.getLogger(__name__)


# Known franchises for grouping
FRANCHISES = {
    'marvel': ['marvel', 'mcu', 'iron man', 'captain america', 'thor', 'avengers', 'spider-man', 'guardians of the galaxy'],
    'star wars': ['star wars', 'starwars', 'episode', 'the force awakens', 'the last jedi', 'the rise of skywalker'],
    'dc': ['dc', 'batman', 'superman', 'wonder woman', 'justice league', 'aquaman'],
    'fast & furious': ['fast and furious', 'fast & furious', 'furious'],
    'james bond': ['james bond', '007', 'bond'],
    'harry potter': ['harry potter', 'hogwarts'],
    'lord of the rings': ['lord of the rings', 'hobbit', 'middle-earth'],
    'pirates of the caribbean': ['pirates of the caribbean', 'jack sparrow'],
    'transformers': ['transformers', 'autobots', 'decepticons'],
    'mission impossible': ['mission impossible', 'mission: impossible', 'tom cruise'],
    'jurassic': ['jurassic park', 'jurassic world', 'jurassic'],
    'x-men': ['x-men', 'xmen', 'wolverine', 'professor x'],
    'terminator': ['terminator'],
    'alien': ['alien', 'aliens', 'predator'],
    'matrix': ['matrix'],
    'john wick': ['john wick'],
    'hunger games': ['hunger games'],
    'twilight': ['twilight'],
    'toy story': ['toy story'],
    'shrek': ['shrek'],
    'despicable me': ['despicable me', 'minions']
}


def fuzzy_match(str1: str, str2: str, threshold: float = 0.8) -> bool:
    """
    Check if two strings are similar (fuzzy matching).
    
    Args:
        str1: First string
        str2: Second string
        threshold: Similarity threshold (0.0 to 1.0)
        
    Returns:
        True if strings are similar enough
    """
    similarity = SequenceMatcher(None, str1.lower(), str2.lower()).ratio()
    return similarity >= threshold


def group_by_genre(client: JellyfinClient, genre: str, fuzzy: bool = True) -> List[Dict]:
    """
    Group items by genre with optional fuzzy matching.
    
    Args:
        client: JellyfinClient instance
        genre: Genre name to group by
        fuzzy: Whether to use fuzzy matching for genre variations
        
    Returns:
        List of collection definitions (name, item_ids)
        
    Raises:
        TypeError: If client is not JellyfinClient or types are invalid
        ValueError: If genre is empty or whitespace-only
    """
    # Commandment #2: Paranoid Input Validation
    if not isinstance(client, JellyfinClient):
        raise TypeError(f"client must be JellyfinClient, got {type(client)}")
    
    if not isinstance(genre, str):
        raise TypeError(f"genre must be str, got {type(genre)}")
    
    if not genre or not genre.strip():
        raise ValueError("genre must be non-empty string")
    
    if not isinstance(fuzzy, bool):
        raise TypeError(f"fuzzy must be bool, got {type(fuzzy)}")
    
    try:
        logger.info(f"Grouping by genre: {genre} (fuzzy={fuzzy})")
        
        items = client.get_all_items()
        
        matching_items = []
        genre_lower = genre.lower()
        
        for item in items:
            item_genres = item.get('Genres', [])
            if not item_genres:
                continue
            
            if fuzzy:
                # Fuzzy match against any genre
                for item_genre in item_genres:
                    if fuzzy_match(genre_lower, item_genre.lower()):
                        matching_items.append(item.get('Id'))
                        break
            else:
                # Exact match
                if genre_lower in [g.lower() for g in item_genres]:
                    matching_items.append(item.get('Id'))
        
        if not matching_items:
            logger.warning(f"No items found for genre: {genre}")
            return []
        
        return [{
            'name': f"{genre} Collection",
            'item_ids': matching_items
        }]
    except Exception as e:
        logger.error(f"Error grouping by genre {genre}: {e}", exc_info=True)
        return []


def group_by_series(client: JellyfinClient) -> List[Dict]:
    """
    Group TV series episodes.
    
    Args:
        client: JellyfinClient instance
        
    Returns:
        List of collection definitions (name, item_ids) for each series
        
    Raises:
        TypeError: If client is not JellyfinClient
    """
    # Commandment #2: Paranoid Input Validation
    if not isinstance(client, JellyfinClient):
        raise TypeError(f"client must be JellyfinClient, got {type(client)}")
    
    try:
        logger.info("Grouping TV series...")
        
        items = client.get_all_items(item_types=['Episode'])
        
        # Group by SeriesName
        series_groups = {}
        for item in items:
            series_name = item.get('SeriesName', '')
            if not series_name:
                continue
            
            if series_name not in series_groups:
                series_groups[series_name] = []
            series_groups[series_name].append(item.get('Id'))
        
        # Convert to collection definitions
        collections = []
        for series_name, item_ids in series_groups.items():
            if len(item_ids) > 1:  # Only create collections for series with multiple episodes
                collections.append({
                    'name': f"{series_name} Collection",
                    'item_ids': item_ids
                })
        
        logger.info(f"Found {len(collections)} series to group")
        return collections
    except Exception as e:
        logger.error(f"Error grouping by series: {e}", exc_info=True)
        return []


def group_by_franchise(client: JellyfinClient) -> List[Dict]:
    """
    Group items by franchise (Marvel, Star Wars, etc.).
    
    Args:
        client: JellyfinClient instance
        
    Returns:
        List of collection definitions (name, item_ids) for each franchise
        
    Raises:
        TypeError: If client is not JellyfinClient
    """
    # Commandment #2: Paranoid Input Validation
    if not isinstance(client, JellyfinClient):
        raise TypeError(f"client must be JellyfinClient, got {type(client)}")
    
    try:
        logger.info("Grouping by franchise...")
        
        items = client.get_all_items()
        
        franchise_groups = {franchise: [] for franchise in FRANCHISES.keys()}
        
        for item in items:
            title = item.get('Name', '').lower()
            genres = [g.lower() for g in item.get('Genres', [])]
            tags = [t.lower() for t in item.get('Tags', [])]
            
            # Check against all franchises
            for franchise, keywords in FRANCHISES.items():
                # Check title
                if any(keyword in title for keyword in keywords):
                    franchise_groups[franchise].append(item.get('Id'))
                    break
                # Check genres
                if any(keyword in ' '.join(genres) for keyword in keywords):
                    franchise_groups[franchise].append(item.get('Id'))
                    break
                # Check tags
                if any(keyword in ' '.join(tags) for keyword in keywords):
                    franchise_groups[franchise].append(item.get('Id'))
                    break
        
        # Convert to collection definitions
        collections = []
        for franchise, item_ids in franchise_groups.items():
            if item_ids:
                franchise_name = franchise.replace('_', ' ').title()
                collections.append({
                    'name': f"{franchise_name} Collection",
                    'item_ids': item_ids
                })
        
        logger.info(f"Found {len(collections)} franchises to group")
        return collections
    except Exception as e:
        logger.error(f"Error grouping by franchise: {e}", exc_info=True)
        return []


def group_by_director(client: JellyfinClient) -> List[Dict]:
    """
    Group movies by director.
    
    Args:
        client: JellyfinClient instance
        
    Returns:
        List of collection definitions (name, item_ids) for each director
        
    Raises:
        TypeError: If client is not JellyfinClient
    """
    # Commandment #2: Paranoid Input Validation
    if not isinstance(client, JellyfinClient):
        raise TypeError(f"client must be JellyfinClient, got {type(client)}")
    
    try:
        logger.info("Grouping by director...")
        
        items = client.get_all_items(item_types=['Movie'])
        
        # Group by director (from People metadata)
        director_groups = {}
        for item in items:
            # Get director from People array
            people = item.get('People', [])
            directors = [p for p in people if p.get('Type') == 'Director']
            
            for director in directors:
                director_name = director.get('Name', '')
                if not director_name:
                    continue
                
                if director_name not in director_groups:
                    director_groups[director_name] = []
                director_groups[director_name].append(item.get('Id'))
                break  # Only use first director
        
        # Convert to collection definitions
        collections = []
        for director_name, item_ids in director_groups.items():
            if len(item_ids) > 1:  # Only create collections for directors with multiple movies
                collections.append({
                    'name': f"{director_name} Collection",
                    'item_ids': item_ids
                })
        
        logger.info(f"Found {len(collections)} directors to group")
        return collections
    except Exception as e:
        logger.error(f"Error grouping by director: {e}", exc_info=True)
        return []


def apply_custom_grouping_rules(client: JellyfinClient, rules: List[Dict]) -> List[Dict]:
    """
    Apply custom grouping rules.
    
    Args:
        client: JellyfinClient instance
        rules: List of rule dictionaries, each with:
               - 'name': Collection name
               - 'field': Field to filter on ('genre', 'year', 'type', etc.)
               - 'operator': Operator ('equals', 'contains', 'greater_than', etc.)
               - 'value': Value to match
               
    Returns:
        List of collection definitions (name, item_ids)
        
    Raises:
        TypeError: If client is not JellyfinClient or rules is not a list
        ValueError: If rules is empty or contains invalid rule dictionaries
    """
    # Commandment #2: Paranoid Input Validation
    if not isinstance(client, JellyfinClient):
        raise TypeError(f"client must be JellyfinClient, got {type(client)}")
    
    if not isinstance(rules, list):
        raise TypeError(f"rules must be list, got {type(rules)}")
    
    if not rules:
        raise ValueError("rules must be non-empty list")
    
    # Validate each rule has required fields
    required_fields = ['name', 'field', 'operator', 'value']
    for i, rule in enumerate(rules):
        if not isinstance(rule, dict):
            raise TypeError(f"rules[{i}] must be dict, got {type(rule)}")
        
        for field in required_fields:
            if field not in rule:
                raise ValueError(f"rules[{i}] missing required field: {field}")
    
    try:
        logger.info(f"Applying {len(rules)} custom grouping rules...")
        
        items = client.get_all_items()
        collections = []
        
        for rule in rules:
            rule_name = rule.get('name', 'Custom Collection')
            field = rule.get('field', '')
            operator = rule.get('operator', 'equals')
            value = rule.get('value', '')
            
            matching_items = []
            
            for item in items:
                item_value = None
                
                # Get field value
                if field == 'genre':
                    item_value = item.get('Genres', [])
                elif field == 'year':
                    item_value = item.get('ProductionYear')
                elif field == 'type':
                    item_value = item.get('Type')
                elif field == 'title':
                    item_value = item.get('Name', '')
                else:
                    item_value = item.get(field)
                
                # Apply operator
                if operator == 'equals':
                    if field == 'genre':
                        if value.lower() in [g.lower() for g in item_value]:
                            matching_items.append(item.get('Id'))
                    else:
                        if str(item_value).lower() == str(value).lower():
                            matching_items.append(item.get('Id'))
                elif operator == 'contains':
                    if field == 'genre':
                        if any(value.lower() in g.lower() for g in item_value):
                            matching_items.append(item.get('Id'))
                    else:
                        if value.lower() in str(item_value).lower():
                            matching_items.append(item.get('Id'))
                elif operator == 'greater_than':
                    if isinstance(item_value, (int, float)) and item_value > value:
                        matching_items.append(item.get('Id'))
                elif operator == 'less_than':
                    if isinstance(item_value, (int, float)) and item_value < value:
                        matching_items.append(item.get('Id'))
            
            if matching_items:
                collections.append({
                    'name': rule_name,
                    'item_ids': matching_items
                })
        
        logger.info(f"Created {len(collections)} collections from custom rules")
        return collections
    except Exception as e:
        logger.error(f"Error applying custom grouping rules: {e}", exc_info=True)
        return []

