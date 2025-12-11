#!/usr/bin/env python3
"""
Bucket Manager - Manages media categorization buckets for the Sorting Canvas.

The Sorting Canvas allows users to drag-drop files/folders into category buckets
before LLM analysis. Each bucket gets a specialized LLM prompt optimized for
that media type (movies vs TV shows vs games, etc.).

Buckets:
- Movies: Film content, optimized for year detection
- TV Shows: Series with S01E01 patterns
- Games: Game-related content
- Music: Audio files
- Books: eBooks and audiobooks
- Unsorted: Catch-all for unrecognized content
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Dict, Set, Optional, Any
import json

logger = logging.getLogger(__name__)


class BucketType(Enum):
    """Category bucket types for media organization."""
    MOVIES = "movies"
    TV_SHOWS = "tv_shows"
    GAMES = "games"
    MUSIC = "music"
    BOOKS = "books"
    UNSORTED = "unsorted"
    
    @classmethod
    def from_string(cls, value: str) -> 'BucketType':
        """Convert string to BucketType."""
        mapping = {
            'movies': cls.MOVIES,
            'tv_shows': cls.TV_SHOWS,
            'tv shows': cls.TV_SHOWS,
            'games': cls.GAMES,
            'music': cls.MUSIC,
            'books': cls.BOOKS,
            'unsorted': cls.UNSORTED,
        }
        return mapping.get(value.lower(), cls.UNSORTED)


@dataclass
class BucketItem:
    """An item in a bucket (file or folder)."""
    path: Path
    name: str
    is_folder: bool
    size_bytes: int = 0
    file_count: int = 1
    original_bucket: Optional[BucketType] = None  # For undo tracking
    auto_assigned: bool = False  # True if auto-categorized, False if user-assigned
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'path': str(self.path),
            'name': self.name,
            'is_folder': self.is_folder,
            'size_bytes': self.size_bytes,
            'file_count': self.file_count,
            'original_bucket': self.original_bucket.value if self.original_bucket else None,
            'auto_assigned': self.auto_assigned
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BucketItem':
        """Deserialize from dictionary."""
        original_bucket = None
        if data.get('original_bucket'):
            original_bucket = BucketType.from_string(data['original_bucket'])
        return cls(
            path=Path(data['path']),
            name=data['name'],
            is_folder=data['is_folder'],
            size_bytes=data.get('size_bytes', 0),
            file_count=data.get('file_count', 1),
            original_bucket=original_bucket,
            auto_assigned=data.get('auto_assigned', False)
        )


@dataclass
class Bucket:
    """A category bucket containing items."""
    bucket_type: BucketType
    items: List[BucketItem] = field(default_factory=list)
    
    @property
    def name(self) -> str:
        """Human-readable bucket name."""
        names = {
            BucketType.MOVIES: "🎬 Movies",
            BucketType.TV_SHOWS: "📺 TV Shows",
            BucketType.GAMES: "🎮 Games",
            BucketType.MUSIC: "🎵 Music",
            BucketType.BOOKS: "📚 Books",
            BucketType.UNSORTED: "❓ Unsorted",
        }
        return names.get(self.bucket_type, "Unknown")
    
    @property
    def total_files(self) -> int:
        """Total file count in bucket."""
        return sum(item.file_count for item in self.items)
    
    @property
    def total_size_bytes(self) -> int:
        """Total size of items in bucket."""
        return sum(item.size_bytes for item in self.items)
    
    def add_item(self, item: BucketItem):
        """Add item to bucket."""
        self.items.append(item)
    
    def remove_item(self, path: Path) -> Optional[BucketItem]:
        """Remove and return item by path."""
        for i, item in enumerate(self.items):
            if item.path == path:
                return self.items.pop(i)
        return None
    
    def clear(self):
        """Remove all items from bucket."""
        self.items.clear()
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'bucket_type': self.bucket_type.value,
            'items': [item.to_dict() for item in self.items]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Bucket':
        """Deserialize from dictionary."""
        return cls(
            bucket_type=BucketType.from_string(data['bucket_type']),
            items=[BucketItem.from_dict(item) for item in data.get('items', [])]
        )


class BucketManager:
    """
    Manages the categorization buckets for the Sorting Canvas.
    
    Responsibilities:
    - Create and manage buckets
    - Track item assignments
    - Auto-categorize items based on heuristics
    - Persist bucket state to Round-Up database
    - Support undo/redo of assignments
    """
    
    # Patterns for auto-categorization
    TV_PATTERNS = [
        r'[sS]\d{1,2}[eE]\d{1,2}',  # S01E01
        r'[sS]eason\s*\d+',  # Season 1
        r'\d+x\d+',  # 1x01 format
        r'[eE]pisode\s*\d+',  # Episode 1
    ]
    
    MOVIE_PATTERNS = [
        r'\(\d{4}\)',  # (2020)
        r'\.\d{4}\.',  # .2020.
        r'720p|1080p|2160p|4[kK]|[bB]lu[rR]ay|[dD][vV][dD][rR]ip|[wW][eE][bB][rR]ip',
    ]
    
    GAME_PATTERNS = [
        r'[gG]ame',
        r'[iI][sS][oO]',
        r'[rR][oO][mM]',
    ]
    
    MUSIC_EXTENSIONS = {'.mp3', '.flac', '.wav', '.aac', '.ogg', '.m4a', '.wma'}
    BOOK_EXTENSIONS = {'.epub', '.mobi', '.pdf', '.azw3', '.djvu'}
    VIDEO_EXTENSIONS = {'.mkv', '.mp4', '.avi', '.mov', '.wmv', '.flv', '.m4v', '.ts', '.webm'}
    
    def __init__(self):
        """Initialize the BucketManager with empty buckets."""
        self.buckets: Dict[BucketType, Bucket] = {
            bt: Bucket(bt) for bt in BucketType
        }
        self._undo_stack: List[Dict[str, Any]] = []
        self._redo_stack: List[Dict[str, Any]] = []
        logger.info("BucketManager initialized with all bucket types")
    
    def get_bucket(self, bucket_type: BucketType) -> Bucket:
        """Get a bucket by type."""
        return self.buckets[bucket_type]
    
    def get_all_buckets(self) -> List[Bucket]:
        """Get all buckets."""
        return list(self.buckets.values())
    
    def get_non_empty_buckets(self) -> List[Bucket]:
        """Get buckets that have items."""
        return [b for b in self.buckets.values() if b.items]
    
    def find_item_bucket(self, path: Path) -> Optional[BucketType]:
        """Find which bucket contains an item by path."""
        for bucket_type, bucket in self.buckets.items():
            for item in bucket.items:
                if item.path == path:
                    return bucket_type
        return None
    
    def add_item(self, bucket_type: BucketType, item: BucketItem, record_undo: bool = True):
        """
        Add an item to a bucket.
        
        Args:
            bucket_type: Target bucket
            item: Item to add
            record_undo: Whether to record for undo (False during load)
        """
        # Check if item already exists in another bucket
        existing_bucket = self.find_item_bucket(item.path)
        if existing_bucket:
            if existing_bucket == bucket_type:
                logger.debug(f"Item already in {bucket_type.value}: {item.path}")
                return
            # Move from existing bucket
            self.move_item(item.path, existing_bucket, bucket_type, record_undo)
            return
        
        if record_undo:
            self._record_undo('add', item.path, None, bucket_type)
        
        self.buckets[bucket_type].add_item(item)
        logger.debug(f"Added {item.name} to {bucket_type.value}")
    
    def move_item(self, path: Path, from_bucket: BucketType, to_bucket: BucketType, 
                  record_undo: bool = True) -> bool:
        """
        Move an item between buckets.
        
        Args:
            path: Path of item to move
            from_bucket: Source bucket
            to_bucket: Destination bucket
            record_undo: Whether to record for undo
            
        Returns:
            True if move succeeded
        """
        if from_bucket == to_bucket:
            return True
        
        item = self.buckets[from_bucket].remove_item(path)
        if item:
            if record_undo:
                self._record_undo('move', path, from_bucket, to_bucket)
            
            item.original_bucket = from_bucket
            item.auto_assigned = False  # User moved it
            self.buckets[to_bucket].add_item(item)
            logger.debug(f"Moved {item.name} from {from_bucket.value} to {to_bucket.value}")
            return True
        return False
    
    def remove_item(self, path: Path, record_undo: bool = True) -> Optional[BucketItem]:
        """Remove an item from all buckets."""
        for bucket_type, bucket in self.buckets.items():
            item = bucket.remove_item(path)
            if item:
                if record_undo:
                    self._record_undo('remove', path, bucket_type, None)
                logger.debug(f"Removed {item.name} from {bucket_type.value}")
                return item
        return None
    
    def clear_all(self):
        """Clear all buckets."""
        for bucket in self.buckets.values():
            bucket.clear()
        self._undo_stack.clear()
        self._redo_stack.clear()
        logger.info("All buckets cleared")
    
    def _record_undo(self, action: str, path: Path, from_bucket: Optional[BucketType],
                     to_bucket: Optional[BucketType]):
        """Record an action for undo."""
        self._undo_stack.append({
            'action': action,
            'path': str(path),
            'from_bucket': from_bucket.value if from_bucket else None,
            'to_bucket': to_bucket.value if to_bucket else None
        })
        self._redo_stack.clear()  # Clear redo when new action is recorded
    
    def undo(self) -> bool:
        """Undo the last action."""
        if not self._undo_stack:
            return False
        
        action_data = self._undo_stack.pop()
        path = Path(action_data['path'])
        from_bucket = BucketType.from_string(action_data['from_bucket']) if action_data['from_bucket'] else None
        to_bucket = BucketType.from_string(action_data['to_bucket']) if action_data['to_bucket'] else None
        
        if action_data['action'] == 'move':
            # Reverse the move
            if to_bucket and from_bucket:
                self.move_item(path, to_bucket, from_bucket, record_undo=False)
        elif action_data['action'] == 'add':
            # Remove the added item
            if to_bucket:
                self.buckets[to_bucket].remove_item(path)
        elif action_data['action'] == 'remove':
            # We can't undo a remove without storing the item
            pass
        
        self._redo_stack.append(action_data)
        return True
    
    def redo(self) -> bool:
        """Redo the last undone action."""
        if not self._redo_stack:
            return False
        
        action_data = self._redo_stack.pop()
        path = Path(action_data['path'])
        from_bucket = BucketType.from_string(action_data['from_bucket']) if action_data['from_bucket'] else None
        to_bucket = BucketType.from_string(action_data['to_bucket']) if action_data['to_bucket'] else None
        
        if action_data['action'] == 'move':
            if from_bucket and to_bucket:
                self.move_item(path, from_bucket, to_bucket, record_undo=False)
        
        self._undo_stack.append(action_data)
        return True
    
    def auto_categorize_item(self, path: Path, name: str, is_folder: bool,
                            size_bytes: int = 0, file_count: int = 1,
                            file_extensions: Optional[Set[str]] = None) -> BucketType:
        """
        Auto-categorize an item based on name patterns and file extensions.
        
        Args:
            path: Item path
            name: Item name for pattern matching
            is_folder: Whether item is a folder
            size_bytes: Total size
            file_count: Number of files (for folders)
            file_extensions: Set of extensions found in item (for folders)
            
        Returns:
            Suggested BucketType
        """
        import re
        
        name_lower = name.lower()
        extensions = file_extensions or set()
        
        # Check for music based on extensions
        if extensions & self.MUSIC_EXTENSIONS:
            music_ratio = len(extensions & self.MUSIC_EXTENSIONS) / max(len(extensions), 1)
            if music_ratio > 0.5:
                return BucketType.MUSIC
        
        # Check for books based on extensions
        if extensions & self.BOOK_EXTENSIONS:
            book_ratio = len(extensions & self.BOOK_EXTENSIONS) / max(len(extensions), 1)
            if book_ratio > 0.5:
                return BucketType.BOOKS
        
        # Check TV show patterns
        for pattern in self.TV_PATTERNS:
            if re.search(pattern, name):
                return BucketType.TV_SHOWS
        
        # Check game patterns
        for pattern in self.GAME_PATTERNS:
            if re.search(pattern, name):
                return BucketType.GAMES
        
        # Check movie patterns (after TV to avoid false positives)
        for pattern in self.MOVIE_PATTERNS:
            if re.search(pattern, name):
                return BucketType.MOVIES
        
        # Default: if it has video files, assume movies
        if extensions & self.VIDEO_EXTENSIONS:
            return BucketType.MOVIES
        
        return BucketType.UNSORTED
    
    def auto_categorize_all(self, items: List[Dict[str, Any]]):
        """
        Auto-categorize a list of items and add them to buckets.
        
        Args:
            items: List of dicts with 'path', 'name', 'is_folder', etc.
        """
        for item_data in items:
            path = Path(item_data['path'])
            name = item_data.get('name', path.name)
            is_folder = item_data.get('is_folder', False)
            size_bytes = item_data.get('size_bytes', 0)
            file_count = item_data.get('file_count', 1)
            extensions = set(item_data.get('extensions', []))
            
            bucket_type = self.auto_categorize_item(
                path, name, is_folder, size_bytes, file_count, extensions
            )
            
            item = BucketItem(
                path=path,
                name=name,
                is_folder=is_folder,
                size_bytes=size_bytes,
                file_count=file_count,
                auto_assigned=True
            )
            
            self.add_item(bucket_type, item, record_undo=False)
        
        logger.info(f"Auto-categorized {len(items)} items into buckets")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about bucket contents."""
        stats = {
            'total_items': 0,
            'total_files': 0,
            'total_size_bytes': 0,
            'buckets': {}
        }
        
        for bucket_type, bucket in self.buckets.items():
            bucket_stats = {
                'item_count': len(bucket.items),
                'file_count': bucket.total_files,
                'size_bytes': bucket.total_size_bytes,
                'auto_assigned': sum(1 for item in bucket.items if item.auto_assigned),
                'user_assigned': sum(1 for item in bucket.items if not item.auto_assigned)
            }
            stats['buckets'][bucket_type.value] = bucket_stats
            stats['total_items'] += bucket_stats['item_count']
            stats['total_files'] += bucket_stats['file_count']
            stats['total_size_bytes'] += bucket_stats['size_bytes']
        
        return stats
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize all buckets to dictionary."""
        return {
            'buckets': {bt.value: bucket.to_dict() for bt, bucket in self.buckets.items()},
            'undo_stack': self._undo_stack[-50:],  # Keep last 50 undos
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BucketManager':
        """Deserialize from dictionary."""
        manager = cls()
        
        for bucket_type_str, bucket_data in data.get('buckets', {}).items():
            bucket_type = BucketType.from_string(bucket_type_str)
            manager.buckets[bucket_type] = Bucket.from_dict(bucket_data)
        
        manager._undo_stack = data.get('undo_stack', [])
        
        return manager
    
    def save_to_database(self, db_path: Path) -> bool:
        """Save bucket state to Round-Up database."""
        try:
            import sqlite3
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # Create table if not exists
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS bucket_assignments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    path TEXT UNIQUE NOT NULL,
                    bucket_type TEXT NOT NULL,
                    name TEXT,
                    is_folder INTEGER,
                    size_bytes INTEGER,
                    file_count INTEGER,
                    auto_assigned INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Clear existing assignments
            cursor.execute('DELETE FROM bucket_assignments')
            
            # Insert current assignments
            for bucket_type, bucket in self.buckets.items():
                for item in bucket.items:
                    cursor.execute('''
                        INSERT INTO bucket_assignments 
                        (path, bucket_type, name, is_folder, size_bytes, file_count, auto_assigned)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        str(item.path),
                        bucket_type.value,
                        item.name,
                        1 if item.is_folder else 0,
                        item.size_bytes,
                        item.file_count,
                        1 if item.auto_assigned else 0
                    ))
            
            conn.commit()
            conn.close()
            logger.info(f"Saved bucket assignments to {db_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save bucket assignments: {e}")
            return False
    
    def load_from_database(self, db_path: Path) -> bool:
        """Load bucket state from Round-Up database."""
        try:
            import sqlite3
            
            if not db_path.exists():
                return False
            
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Check if table exists
            cursor.execute('''
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='bucket_assignments'
            ''')
            if not cursor.fetchone():
                conn.close()
                return False
            
            # Clear current buckets
            self.clear_all()
            
            # Load assignments
            cursor.execute('SELECT * FROM bucket_assignments')
            for row in cursor.fetchall():
                bucket_type = BucketType.from_string(row['bucket_type'])
                item = BucketItem(
                    path=Path(row['path']),
                    name=row['name'],
                    is_folder=bool(row['is_folder']),
                    size_bytes=row['size_bytes'] or 0,
                    file_count=row['file_count'] or 1,
                    auto_assigned=bool(row['auto_assigned'])
                )
                self.add_item(bucket_type, item, record_undo=False)
            
            conn.close()
            logger.info(f"Loaded bucket assignments from {db_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load bucket assignments: {e}")
            return False

