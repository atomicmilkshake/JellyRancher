#!/usr/bin/env python3
"""
Round-Up Manager - Persistence layer for JellyRancher Round-Ups.

A Round-Up is a saved session representing one media library organization project.
Users can work on multiple Round-Ups, save progress at any workflow step, close
the application, and resume exactly where they left off.

Storage Structure (Hybrid: SQLite + JSON):
    ~/JellyRancher/roundups/
    ├── My_TV_Library.roundup/
    │   ├── metadata.json      ← Name, timestamps, current step, source folders
    │   ├── config.json        ← User preferences for this Round-Up
    │   └── data.db            ← SQLite for all step data
    └── backups/
        └── My_TV_Library_2025-11-21_120000/  ← Pre-Step-6 backup

Usage:
    from scripts.core.roundup_manager import RoundUpManager, RoundUp

    manager = RoundUpManager()

    # Create new Round-Up
    roundup = manager.create("My TV Library")

    # Save after step completion
    manager.save(roundup)

    # Load existing Round-Up
    roundup = manager.load("My_TV_Library")

    # List all Round-Ups
    roundups = manager.list_all()
"""

import sqlite3
import logging
import json
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
from contextlib import contextmanager
from enum import Enum

logger = logging.getLogger(__name__)


class StepStatus(Enum):
    """Status of a workflow step."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


@dataclass
class RoundUp:
    """
    Represents a JellyRancher Round-Up session.

    A Round-Up encapsulates all workflow state for one media organization project:
    - Current step (1-8) the user is on
    - Completion status of each step
    - All step data (scans, analyses, plans, execution logs, etc.)

    Attributes:
        name: User-provided name for this Round-Up
        path: Path to the .roundup directory
        created_at: ISO timestamp of creation
        last_modified: ISO timestamp of last modification
        current_step: Current step number (1-8)
        step_status: Dict mapping step number to status
        source_folders: List of folder paths being organized
        config: User preferences specific to this Round-Up
    """
    name: str
    path: Path
    created_at: str = ""
    last_modified: str = ""
    current_step: int = 1
    step_status: Dict[int, str] = field(default_factory=lambda: {
        1: "not_started", 2: "not_started", 3: "not_started", 4: "not_started",
        5: "not_started", 6: "not_started", 7: "not_started", 8: "not_started"
    })
    source_folders: List[str] = field(default_factory=list)
    config: Dict[str, Any] = field(default_factory=dict)
    version: str = "1.0"

    # Runtime state (not persisted in metadata.json)
    _unsaved_changes: bool = field(default=False, repr=False)

    @property
    def has_unsaved_changes(self) -> bool:
        """Check if there are unsaved changes."""
        return self._unsaved_changes

    def mark_modified(self):
        """Mark the Round-Up as having unsaved changes."""
        self._unsaved_changes = True
        self.last_modified = datetime.now().isoformat()

    def mark_saved(self):
        """Mark the Round-Up as saved."""
        self._unsaved_changes = False

    def get_step_name(self, step: int) -> str:
        """Get human-readable name for a step number."""
        step_names = {
            1: "Scan Folders",
            2: "Structure Summary",
            3: "Analysis",
            4: "Canonical Database",
            5: "Review Table",
            6: "Execute Operations",
            7: "Subtitle Audit",
            8: "Subtitle Downloads"
        }
        return step_names.get(step, f"Step {step}")

    def is_step_completed(self, step: int) -> bool:
        """Check if a step is completed."""
        return self.step_status.get(step) == StepStatus.COMPLETED.value

    def complete_step(self, step: int):
        """Mark a step as completed and advance current_step."""
        self.step_status[step] = StepStatus.COMPLETED.value
        if step == self.current_step and step < 8:
            self.current_step = step + 1
        self.mark_modified()

    def to_metadata_dict(self) -> Dict[str, Any]:
        """Convert to metadata.json dictionary."""
        return {
            "name": self.name,
            "created_at": self.created_at,
            "last_modified": self.last_modified,
            "current_step": self.current_step,
            "step_status": {str(k): v for k, v in self.step_status.items()},
            "source_folders": self.source_folders,
            "version": self.version
        }

    @classmethod
    def from_metadata_dict(cls, data: Dict[str, Any], path: Path) -> 'RoundUp':
        """Create RoundUp from metadata.json dictionary."""
        step_status = {int(k): v for k, v in data.get("step_status", {}).items()}
        # Fill in any missing steps with not_started
        for i in range(1, 9):
            if i not in step_status:
                step_status[i] = "not_started"

        return cls(
            name=data.get("name", path.stem),
            path=path,
            created_at=data.get("created_at", ""),
            last_modified=data.get("last_modified", ""),
            current_step=data.get("current_step", 1),
            step_status=step_status,
            source_folders=data.get("source_folders", []),
            version=data.get("version", "1.0")
        )


class RoundUpManager:
    """
    Manages Round-Up lifecycle and persistence.

    Responsibilities:
    - Create, load, save, delete Round-Ups
    - Manage the .roundup directory structure
    - Handle database operations for step data
    - Create backups before destructive operations
    - Handle corruption gracefully

    Storage Location: ~/JellyRancher/roundups/
    """

    # Default storage location
    DEFAULT_ROUNDUPS_DIR = Path.home() / "JellyRancher" / "roundups"

    def __init__(self, roundups_dir: Optional[Path] = None):
        """
        Initialize RoundUpManager.

        Args:
            roundups_dir: Custom directory for Round-Ups (default: ~/JellyRancher/roundups/)
        """
        self.roundups_dir = roundups_dir or self.DEFAULT_ROUNDUPS_DIR
        self.roundups_dir.mkdir(parents=True, exist_ok=True)

        # Create backups directory
        self.backups_dir = self.roundups_dir / "backups"
        self.backups_dir.mkdir(exist_ok=True)

        logger.info(f"RoundUpManager initialized: {self.roundups_dir}")

    # ========================================================================
    # CRUD Operations
    # ========================================================================

    def create(self, name: str, source_folders: Optional[List[str]] = None) -> RoundUp:
        """
        Create a new Round-Up.

        Args:
            name: User-provided name (will be sanitized for filesystem)
            source_folders: Optional list of source folder paths

        Returns:
            Created RoundUp instance

        Raises:
            ValueError: If name is empty or Round-Up already exists
        """
        if not name or not name.strip():
            raise ValueError("Round-Up name cannot be empty")

        # Sanitize name for filesystem
        safe_name = self._sanitize_name(name)
        roundup_path = self.roundups_dir / f"{safe_name}.roundup"

        if roundup_path.exists():
            raise ValueError(f"Round-Up '{name}' already exists")

        # Create directory structure
        roundup_path.mkdir(parents=True)

        now = datetime.now().isoformat()

        # Create RoundUp instance
        roundup = RoundUp(
            name=name,
            path=roundup_path,
            created_at=now,
            last_modified=now,
            current_step=1,
            source_folders=source_folders or []
        )

        # Save metadata.json
        self._save_metadata(roundup)

        # Save default config.json
        self._save_config(roundup)

        # Initialize database
        self._init_database(roundup)

        logger.info(f"Created Round-Up: {name} at {roundup_path}")
        return roundup

    def load(self, name_or_path: str) -> Optional[RoundUp]:
        """
        Load an existing Round-Up by name or path.

        Args:
            name_or_path: Round-Up name or full path to .roundup directory

        Returns:
            RoundUp instance or None if not found/corrupted
        """
        # Determine path
        if Path(name_or_path).suffix == ".roundup":
            roundup_path = Path(name_or_path)
        else:
            safe_name = self._sanitize_name(name_or_path)
            roundup_path = self.roundups_dir / f"{safe_name}.roundup"

        if not roundup_path.exists():
            logger.warning(f"Round-Up not found: {roundup_path}")
            return None

        # Load metadata.json
        metadata_file = roundup_path / "metadata.json"
        if not metadata_file.exists():
            logger.error(f"Corrupted Round-Up (no metadata.json): {roundup_path}")
            return None

        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)

            roundup = RoundUp.from_metadata_dict(metadata, roundup_path)

            # Load config.json
            config_file = roundup_path / "config.json"
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    roundup.config = json.load(f)

            # Validate database exists
            db_file = roundup_path / "data.db"
            if not db_file.exists():
                logger.warning(f"Round-Up missing database, will be recreated: {roundup_path}")
                self._init_database(roundup)

            # Validate source folders still exist
            missing_folders = [f for f in roundup.source_folders if not Path(f).exists()]
            if missing_folders:
                logger.warning(f"Round-Up has {len(missing_folders)} missing source folders")
                # Don't fail, just warn - user will be prompted to remap

            # Update last_modified timestamp
            roundup.last_modified = datetime.now().isoformat()
            self._save_metadata(roundup)

            logger.info(f"Loaded Round-Up: {roundup.name}")
            return roundup

        except json.JSONDecodeError as e:
            logger.error(f"Corrupted metadata.json in {roundup_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to load Round-Up {roundup_path}: {e}", exc_info=True)
            return None

    def save(self, roundup: RoundUp) -> bool:
        """
        Save Round-Up metadata and config.

        Note: Step data is saved to the database via specific methods.
        This method saves metadata.json and config.json.

        Args:
            roundup: RoundUp instance to save

        Returns:
            True if successful
        """
        try:
            roundup.last_modified = datetime.now().isoformat()
            self._save_metadata(roundup)
            self._save_config(roundup)
            roundup.mark_saved()

            logger.info(f"Saved Round-Up: {roundup.name}")
            return True
        except Exception as e:
            logger.error(f"Failed to save Round-Up {roundup.name}: {e}", exc_info=True)
            return False

    def delete(self, roundup: RoundUp, confirm: bool = False) -> bool:
        """
        Delete a Round-Up and all its data.

        Args:
            roundup: RoundUp instance to delete
            confirm: Must be True to actually delete (safety check)

        Returns:
            True if deleted successfully
        """
        if not confirm:
            logger.warning("Delete called without confirmation - refusing to delete")
            return False

        try:
            if roundup.path.exists():
                shutil.rmtree(roundup.path)
                logger.info(f"Deleted Round-Up: {roundup.name}")
                return True
            else:
                logger.warning(f"Round-Up directory not found: {roundup.path}")
                return False
        except Exception as e:
            logger.error(f"Failed to delete Round-Up {roundup.name}: {e}", exc_info=True)
            return False

    def list_all(self) -> List[RoundUp]:
        """
        List all Round-Ups, sorted by last_modified (most recent first).

        Returns:
            List of RoundUp instances (metadata only, not full data)
        """
        roundups = []

        for item in self.roundups_dir.iterdir():
            if item.is_dir() and item.suffix == ".roundup":
                metadata_file = item / "metadata.json"
                if metadata_file.exists():
                    try:
                        with open(metadata_file, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                        roundup = RoundUp.from_metadata_dict(metadata, item)
                        roundups.append(roundup)
                    except Exception as e:
                        logger.warning(f"Skipping corrupted Round-Up {item}: {e}")

        # Sort by last_modified (most recent first)
        roundups.sort(key=lambda r: r.last_modified or "", reverse=True)

        logger.info(f"Listed {len(roundups)} Round-Ups")
        return roundups

    def get_recent(self, limit: int = 5) -> List[RoundUp]:
        """
        Get recently modified Round-Ups.

        Args:
            limit: Maximum number to return

        Returns:
            List of RoundUp instances
        """
        all_roundups = self.list_all()
        return all_roundups[:limit]

    # ========================================================================
    # Database Operations
    # ========================================================================

    @contextmanager
    def get_connection(self, roundup: RoundUp):
        """
        Context manager for database connections.

        Args:
            roundup: RoundUp instance

        Yields:
            SQLite connection with row_factory set to sqlite3.Row
        """
        db_path = roundup.path / "data.db"
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error in {roundup.name}: {e}", exc_info=True)
            raise
        finally:
            conn.close()

    def _init_database(self, roundup: RoundUp):
        """Initialize the database schema for a Round-Up."""
        db_path = roundup.path / "data.db"

        with sqlite3.connect(str(db_path)) as conn:
            cursor = conn.cursor()

            # Step 1: Scan Files
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scan_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    path TEXT NOT NULL,
                    relative_path TEXT,
                    filename TEXT NOT NULL,
                    extension TEXT,
                    size_bytes INTEGER,
                    md5_hash TEXT,
                    created_at TEXT,
                    modified_at TEXT,
                    metadata_json TEXT,
                    UNIQUE(path)
                )
            ''')

            # Step 2: Structure Summary
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS structure_summary (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    folder_path TEXT,
                    file_count INTEGER,
                    total_size INTEGER,
                    file_types_json TEXT,
                    summary_json TEXT,
                    created_at TEXT
                )
            ''')

            # Step 3: Analysis Results (LLM/Regex/Hybrid)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS analysis_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    analysis_mode TEXT,
                    model_used TEXT,
                    prompt_sent TEXT,
                    response_json TEXT,
                    detected_media_json TEXT,
                    reorganization_plan_json TEXT,
                    created_at TEXT
                )
            ''')

            # Step 4: Canonical Metadata
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS canonical_metadata (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    media_type TEXT,
                    title TEXT,
                    year INTEGER,
                    tmdb_id TEXT,
                    tvdb_id TEXT,
                    imdb_id TEXT,
                    metadata_json TEXT,
                    fetched_at TEXT
                )
            ''')

            # Step 5: Review Actions
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS review_actions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_id INTEGER REFERENCES scan_files(id),
                    original_path TEXT,
                    proposed_path TEXT,
                    action TEXT,
                    status TEXT DEFAULT 'pending',
                    confidence REAL,
                    user_edited INTEGER DEFAULT 0,
                    notes TEXT
                )
            ''')

            # Step 6: Execution Log
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS execution_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action_id INTEGER REFERENCES review_actions(id),
                    operation TEXT,
                    source_path TEXT,
                    dest_path TEXT,
                    source_md5 TEXT,
                    dest_md5 TEXT,
                    status TEXT,
                    error_message TEXT,
                    executed_at TEXT
                )
            ''')

            # Step 7: Subtitle Audit
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS subtitle_audit (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_file_id INTEGER REFERENCES scan_files(id),
                    video_path TEXT,
                    subtitle_found INTEGER,
                    subtitle_path TEXT,
                    subtitle_language TEXT,
                    coverage_status TEXT
                )
            ''')

            # Step 8: Subtitle Downloads
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS subtitle_downloads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_file_id INTEGER REFERENCES scan_files(id),
                    provider TEXT,
                    language TEXT,
                    download_url TEXT,
                    saved_path TEXT,
                    status TEXT,
                    downloaded_at TEXT
                )
            ''')

            conn.commit()
            logger.info(f"Initialized database for Round-Up: {roundup.name}")

    # ========================================================================
    # Step-Specific Data Operations
    # ========================================================================

    def save_scan_files(self, roundup: RoundUp, files: List[Dict[str, Any]]) -> int:
        """
        Save scanned files to Step 1 table.

        Args:
            roundup: RoundUp instance
            files: List of file dictionaries with path, filename, size_bytes, md5_hash, etc.

        Returns:
            Number of files saved
        """
        with self.get_connection(roundup) as conn:
            cursor = conn.cursor()

            # Clear existing scan data
            cursor.execute('DELETE FROM scan_files')

            count = 0
            for file_data in files:
                try:
                    cursor.execute('''
                        INSERT INTO scan_files
                        (path, relative_path, filename, extension, size_bytes, md5_hash,
                         created_at, modified_at, metadata_json)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        str(file_data.get('path', '')),
                        file_data.get('relative_path', ''),
                        file_data.get('filename', ''),
                        file_data.get('extension', ''),
                        file_data.get('size_bytes', 0),
                        file_data.get('md5_hash', ''),
                        file_data.get('created_at', ''),
                        file_data.get('modified_at', ''),
                        json.dumps(file_data.get('metadata', {}))
                    ))
                    count += 1
                except Exception as e:
                    logger.warning(f"Failed to save file {file_data.get('path')}: {e}")

            conn.commit()

        # Update step status
        roundup.complete_step(1)
        self.save(roundup)

        logger.info(f"Saved {count} scan files for Round-Up: {roundup.name}")
        return count

    def get_scan_files(self, roundup: RoundUp) -> List[Dict[str, Any]]:
        """
        Get all scanned files from Step 1.

        Args:
            roundup: RoundUp instance

        Returns:
            List of file dictionaries
        """
        with self.get_connection(roundup) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM scan_files ORDER BY path')

            files = []
            for row in cursor.fetchall():
                file_data = {
                    'id': row['id'],
                    'path': row['path'],
                    'relative_path': row['relative_path'],
                    'filename': row['filename'],
                    'extension': row['extension'],
                    'size_bytes': row['size_bytes'],
                    'md5_hash': row['md5_hash'],
                    'created_at': row['created_at'],
                    'modified_at': row['modified_at'],
                }
                if row['metadata_json']:
                    try:
                        file_data['metadata'] = json.loads(row['metadata_json'])
                    except json.JSONDecodeError:
                        file_data['metadata'] = {}
                files.append(file_data)

            return files

    def save_structure_cache(self, roundup: RoundUp, folder_structure: Dict[str, Any],
                             duplicate_groups: Dict[str, List[Any]], scan_file_count: int) -> bool:
        """
        Cache computed structure summary and duplicate groups for fast reload.

        Args:
            roundup: RoundUp instance
            folder_structure: Dict of folder path -> {file_count, total_size, file_types}
            duplicate_groups: Dict of MD5 hash -> list of duplicate file records
            scan_file_count: Number of scan files (for cache invalidation)

        Returns:
            True if cache saved successfully
        """
        try:
            with self.get_connection(roundup) as conn:
                cursor = conn.cursor()

                # Clear existing cache
                cursor.execute('DELETE FROM structure_summary')

                # Store as single cache entry with all data
                # Convert Path keys to strings for JSON serialization
                folder_structure_serializable = {
                    str(k): v for k, v in folder_structure.items()
                }

                # Convert duplicate groups (FileRecord objects to dicts)
                duplicate_groups_serializable = {}
                for md5, records in duplicate_groups.items():
                    duplicate_groups_serializable[md5] = [
                        {
                            'path': str(getattr(r, 'absolute_path', r.get('path', ''))),
                            'filename': getattr(r, 'filename', r.get('filename', '')),
                            'size_bytes': getattr(r, 'size_bytes', r.get('size_bytes', 0)),
                        }
                        for r in records
                    ]

                cache_data = {
                    'folder_structure': folder_structure_serializable,
                    'duplicate_groups': duplicate_groups_serializable,
                    'scan_file_count': scan_file_count,
                    'total_folders': len(folder_structure),
                    'total_duplicates': len(duplicate_groups),
                }

                cursor.execute('''
                    INSERT INTO structure_summary
                    (folder_path, file_count, total_size, summary_json, created_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    '__CACHE__',  # Special marker for cache entry
                    scan_file_count,
                    sum(v.get('total_size', 0) for v in folder_structure.values()),
                    json.dumps(cache_data),
                    datetime.now().isoformat()
                ))

                conn.commit()
                logger.info(f"Cached structure summary: {len(folder_structure)} folders, {len(duplicate_groups)} duplicate groups")
                return True

        except Exception as e:
            logger.error(f"Failed to save structure cache: {e}", exc_info=True)
            return False

    def get_structure_cache(self, roundup: RoundUp) -> Optional[Dict[str, Any]]:
        """
        Get cached structure summary if valid.

        Args:
            roundup: RoundUp instance

        Returns:
            Cache data dict with folder_structure and duplicate_groups, or None if cache invalid
        """
        try:
            with self.get_connection(roundup) as conn:
                cursor = conn.cursor()

                # Check current scan file count
                cursor.execute('SELECT COUNT(*) FROM scan_files')
                current_count = cursor.fetchone()[0]

                if current_count == 0:
                    return None

                # Get cached data
                cursor.execute('''
                    SELECT summary_json, file_count FROM structure_summary
                    WHERE folder_path = '__CACHE__'
                    ORDER BY created_at DESC LIMIT 1
                ''')
                row = cursor.fetchone()

                if not row:
                    logger.debug("No structure cache found")
                    return None

                cached_count = row['file_count']
                if cached_count != current_count:
                    logger.info(f"Structure cache invalidated: scan count changed ({cached_count} -> {current_count})")
                    return None

                cache_data = json.loads(row['summary_json'])
                logger.info(f"Using cached structure summary ({cache_data.get('total_folders', 0)} folders)")
                return cache_data

        except Exception as e:
            logger.warning(f"Failed to load structure cache: {e}")
            return None

    def save_analysis_result(self, roundup: RoundUp, analysis_mode: str,
                            model_used: str, response: Dict[str, Any]) -> int:
        """
        Save analysis result to Step 3 table.

        Args:
            roundup: RoundUp instance
            analysis_mode: 'llm', 'regex', or 'hybrid'
            model_used: Model name (e.g., 'Grok-4.1-Fast-Reasoning')
            response: Analysis response dictionary

        Returns:
            Analysis ID
        """
        with self.get_connection(roundup) as conn:
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO analysis_results
                (analysis_mode, model_used, response_json, detected_media_json,
                 reorganization_plan_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                analysis_mode,
                model_used,
                json.dumps(response),
                json.dumps(response.get('detected_media', {})),
                json.dumps(response.get('reorganization_plan', {})),
                datetime.now().isoformat()
            ))

            analysis_id = cursor.lastrowid
            conn.commit()

        # Update step status
        roundup.complete_step(3)
        self.save(roundup)

        logger.info(f"Saved analysis result #{analysis_id} for Round-Up: {roundup.name}")
        return analysis_id

    def get_latest_analysis(self, roundup: RoundUp) -> Optional[Dict[str, Any]]:
        """
        Get the most recent analysis result.

        Args:
            roundup: RoundUp instance

        Returns:
            Analysis dictionary or None
        """
        with self.get_connection(roundup) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM analysis_results
                ORDER BY created_at DESC LIMIT 1
            ''')

            row = cursor.fetchone()
            if not row:
                return None

            result = {
                'id': row['id'],
                'analysis_mode': row['analysis_mode'],
                'model_used': row['model_used'],
                'created_at': row['created_at']
            }

            if row['response_json']:
                try:
                    result['response'] = json.loads(row['response_json'])
                except json.JSONDecodeError:
                    result['response'] = {}

            return result

    def save_review_actions(self, roundup: RoundUp, actions: List[Dict[str, Any]]) -> int:
        """
        Save review actions to Step 5 table.

        Args:
            roundup: RoundUp instance
            actions: List of action dictionaries

        Returns:
            Number of actions saved
        """
        with self.get_connection(roundup) as conn:
            cursor = conn.cursor()

            # Clear existing review actions
            cursor.execute('DELETE FROM review_actions')

            count = 0
            for action in actions:
                try:
                    cursor.execute('''
                        INSERT INTO review_actions
                        (file_id, original_path, proposed_path, action, status,
                         confidence, user_edited, notes)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        action.get('file_id'),
                        action.get('original_path', ''),
                        action.get('proposed_path', ''),
                        action.get('action', ''),
                        action.get('status', 'pending'),
                        action.get('confidence', 0.0),
                        1 if action.get('user_edited') else 0,
                        action.get('notes', '')
                    ))
                    count += 1
                except Exception as e:
                    logger.warning(f"Failed to save action: {e}")

            conn.commit()

        logger.info(f"Saved {count} review actions for Round-Up: {roundup.name}")
        return count

    def get_review_actions(self, roundup: RoundUp) -> List[Dict[str, Any]]:
        """
        Get all review actions from Step 5.

        Args:
            roundup: RoundUp instance

        Returns:
            List of action dictionaries
        """
        with self.get_connection(roundup) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM review_actions ORDER BY id')

            actions = []
            for row in cursor.fetchall():
                actions.append({
                    'id': row['id'],
                    'file_id': row['file_id'],
                    'original_path': row['original_path'],
                    'proposed_path': row['proposed_path'],
                    'action': row['action'],
                    'status': row['status'],
                    'confidence': row['confidence'],
                    'user_edited': bool(row['user_edited']),
                    'notes': row['notes']
                })

            return actions

    def save_execution_log(self, roundup: RoundUp, log_entry: Dict[str, Any]) -> int:
        """
        Save execution log entry to Step 6 table.

        Args:
            roundup: RoundUp instance
            log_entry: Log entry dictionary

        Returns:
            Log entry ID
        """
        with self.get_connection(roundup) as conn:
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO execution_log
                (action_id, operation, source_path, dest_path, source_md5,
                 dest_md5, status, error_message, executed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                log_entry.get('action_id'),
                log_entry.get('operation', ''),
                log_entry.get('source_path', ''),
                log_entry.get('dest_path', ''),
                log_entry.get('source_md5', ''),
                log_entry.get('dest_md5', ''),
                log_entry.get('status', ''),
                log_entry.get('error_message', ''),
                datetime.now().isoformat()
            ))

            log_id = cursor.lastrowid
            conn.commit()

        logger.debug(f"Saved execution log #{log_id} for Round-Up: {roundup.name}")
        return log_id

    def get_execution_log(self, roundup: RoundUp) -> List[Dict[str, Any]]:
        """
        Get all execution log entries from Step 6.

        Args:
            roundup: RoundUp instance

        Returns:
            List of log entry dictionaries
        """
        with self.get_connection(roundup) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM execution_log ORDER BY executed_at')

            logs = []
            for row in cursor.fetchall():
                logs.append({
                    'id': row['id'],
                    'action_id': row['action_id'],
                    'operation': row['operation'],
                    'source_path': row['source_path'],
                    'dest_path': row['dest_path'],
                    'source_md5': row['source_md5'],
                    'dest_md5': row['dest_md5'],
                    'status': row['status'],
                    'error_message': row['error_message'],
                    'executed_at': row['executed_at']
                })

            return logs

    # ========================================================================
    # Backup Operations
    # ========================================================================

    def create_backup(self, roundup: RoundUp, reason: str = "manual") -> Optional[Path]:
        """
        Create a backup of a Round-Up.

        Args:
            roundup: RoundUp instance to backup
            reason: Reason for backup (e.g., "pre_execution", "manual")

        Returns:
            Path to backup directory or None if failed
        """
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
            backup_name = f"{self._sanitize_name(roundup.name)}_{timestamp}_{reason}"
            backup_path = self.backups_dir / backup_name

            # Copy entire .roundup directory
            shutil.copytree(roundup.path, backup_path)

            logger.info(f"Created backup: {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"Failed to create backup for {roundup.name}: {e}", exc_info=True)
            return None

    def restore_from_backup(self, backup_path: Path) -> Optional[RoundUp]:
        """
        Restore a Round-Up from a backup.

        Args:
            backup_path: Path to backup directory

        Returns:
            Restored RoundUp instance or None if failed
        """
        try:
            # Load metadata from backup
            metadata_file = backup_path / "metadata.json"
            if not metadata_file.exists():
                logger.error(f"Invalid backup (no metadata.json): {backup_path}")
                return None

            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)

            # Determine target path
            safe_name = self._sanitize_name(metadata.get("name", "Restored"))
            target_path = self.roundups_dir / f"{safe_name}.roundup"

            # Check if already exists
            if target_path.exists():
                # Add timestamp to make unique
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_name = f"{safe_name}_{timestamp}"
                target_path = self.roundups_dir / f"{safe_name}.roundup"

            # Copy backup to roundups directory
            shutil.copytree(backup_path, target_path)

            # Update metadata with new path
            metadata["name"] = safe_name.replace("_", " ")
            with open(target_path / "metadata.json", 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)

            # Load and return
            return self.load(str(target_path))

        except Exception as e:
            logger.error(f"Failed to restore from backup {backup_path}: {e}", exc_info=True)
            return None

    def list_backups(self, roundup: Optional[RoundUp] = None) -> List[Dict[str, Any]]:
        """
        List all backups, optionally filtered by Round-Up.

        Args:
            roundup: Optional RoundUp to filter by

        Returns:
            List of backup info dictionaries
        """
        backups = []

        for item in self.backups_dir.iterdir():
            if item.is_dir():
                metadata_file = item / "metadata.json"
                if metadata_file.exists():
                    try:
                        with open(metadata_file, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)

                        # Parse backup name for timestamp and reason
                        parts = item.name.rsplit("_", 2)
                        reason = parts[-1] if len(parts) > 1 else "unknown"

                        backup_info = {
                            "path": item,
                            "name": metadata.get("name", "Unknown"),
                            "created_at": metadata.get("last_modified", ""),
                            "reason": reason
                        }

                        # Filter by roundup if specified
                        if roundup is None or metadata.get("name") == roundup.name:
                            backups.append(backup_info)

                    except Exception as e:
                        logger.warning(f"Skipping corrupted backup {item}: {e}")

        # Sort by creation time (most recent first)
        backups.sort(key=lambda b: b.get("created_at", ""), reverse=True)
        return backups

    # ========================================================================
    # Validation & Recovery
    # ========================================================================

    def validate_roundup(self, roundup: RoundUp) -> Dict[str, Any]:
        """
        Validate a Round-Up's integrity.

        Args:
            roundup: RoundUp instance to validate

        Returns:
            Validation result with 'valid' bool and 'issues' list
        """
        issues = []

        # Check directory exists
        if not roundup.path.exists():
            issues.append("Round-Up directory does not exist")
            return {"valid": False, "issues": issues}

        # Check metadata.json
        if not (roundup.path / "metadata.json").exists():
            issues.append("Missing metadata.json")

        # Check database
        db_path = roundup.path / "data.db"
        if not db_path.exists():
            issues.append("Missing data.db")
        else:
            # Try to connect and verify tables
            try:
                with sqlite3.connect(str(db_path)) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = {row[0] for row in cursor.fetchall()}

                    required_tables = {
                        'scan_files', 'structure_summary', 'analysis_results',
                        'canonical_metadata', 'review_actions', 'execution_log',
                        'subtitle_audit', 'subtitle_downloads'
                    }

                    missing = required_tables - tables
                    if missing:
                        issues.append(f"Missing database tables: {missing}")
            except Exception as e:
                issues.append(f"Database error: {e}")

        # Check source folders
        missing_folders = [f for f in roundup.source_folders if not Path(f).exists()]
        if missing_folders:
            issues.append(f"Missing source folders: {missing_folders}")

        return {
            "valid": len(issues) == 0,
            "issues": issues
        }

    def attempt_recovery(self, roundup_path: Path) -> Optional[RoundUp]:
        """
        Attempt to recover a corrupted Round-Up.

        Args:
            roundup_path: Path to corrupted .roundup directory

        Returns:
            Recovered RoundUp instance or None if unrecoverable
        """
        try:
            # Check what files exist
            metadata_exists = (roundup_path / "metadata.json").exists()
            db_exists = (roundup_path / "data.db").exists()

            if not metadata_exists and not db_exists:
                logger.error(f"Unrecoverable: No metadata.json or data.db in {roundup_path}")
                return None

            # Try to reconstruct metadata if missing
            if not metadata_exists:
                logger.info(f"Reconstructing metadata.json for {roundup_path}")
                metadata = {
                    "name": roundup_path.stem.replace(".roundup", ""),
                    "created_at": datetime.now().isoformat(),
                    "last_modified": datetime.now().isoformat(),
                    "current_step": 1,
                    "step_status": {str(i): "not_started" for i in range(1, 9)},
                    "source_folders": [],
                    "version": "1.0"
                }

                with open(roundup_path / "metadata.json", 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, indent=2)

            # Reinitialize database if missing
            if not db_exists:
                logger.info(f"Reinitializing database for {roundup_path}")
                # Create a temporary RoundUp to init the database
                temp_roundup = RoundUp(
                    name=roundup_path.stem,
                    path=roundup_path
                )
                self._init_database(temp_roundup)

            # Now try to load normally
            return self.load(str(roundup_path))

        except Exception as e:
            logger.error(f"Recovery failed for {roundup_path}: {e}", exc_info=True)
            return None

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def _sanitize_name(self, name: str) -> str:
        """Sanitize a name for use as a filesystem path."""
        # Replace spaces with underscores
        safe = name.replace(" ", "_")
        # Remove characters that are problematic on Windows/Unix
        safe = "".join(c for c in safe if c.isalnum() or c in "_-")
        return safe or "Unnamed"

    def _save_metadata(self, roundup: RoundUp):
        """Save metadata.json for a Round-Up."""
        metadata_file = roundup.path / "metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(roundup.to_metadata_dict(), f, indent=2, ensure_ascii=False)

    def _save_config(self, roundup: RoundUp):
        """Save config.json for a Round-Up."""
        config_file = roundup.path / "config.json"

        # Default config if empty
        config = roundup.config or {
            "analysis_mode": "hybrid",
            "llm_model": "Grok-4.1-Fast-Reasoning",
            "auto_approve_subtitles": True,
            "duplicate_strategy": "keep_largest",
            "jellyfin_refresh_enabled": False
        }

        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

    # ========================================================================
    # Structure Cache Methods (for scan results performance)
    # ========================================================================

    def get_structure_cache(self, roundup: RoundUp) -> Optional[Dict[str, Any]]:
        """
        Get cached folder structure and duplicate groups for a Round-Up.
        
        Returns None if no cache exists or cache is invalid.
        The cache is invalidated when scan_file_count changes.
        
        Args:
            roundup: The RoundUp to get cache for
            
        Returns:
            Dict with 'folder_structure', 'duplicate_groups', 'scan_file_count'
            or None if no valid cache
        """
        try:
            db_path = roundup.path / "data.db"
            if not db_path.exists():
                return None
                
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # Check if cache table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='structure_cache'
            """)
            if not cursor.fetchone():
                conn.close()
                return None
            
            # Get cached data
            cursor.execute("""
                SELECT folder_structure, duplicate_groups, scan_file_count, cached_at
                FROM structure_cache
                WHERE id = 1
            """)
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                return None
            
            folder_structure_json, duplicate_groups_json, scan_file_count, cached_at = row
            
            # Parse JSON, converting string keys back to Path objects for folder_structure
            folder_structure_raw = json.loads(folder_structure_json)
            folder_structure = {Path(k): v for k, v in folder_structure_raw.items()}
            
            duplicate_groups = json.loads(duplicate_groups_json)
            
            logger.info(f"Retrieved structure cache: {len(folder_structure)} folders, "
                       f"{len(duplicate_groups)} duplicate groups (cached at {cached_at})")
            
            return {
                'folder_structure': folder_structure,
                'duplicate_groups': duplicate_groups,
                'scan_file_count': scan_file_count,
                'cached_at': cached_at
            }
            
        except Exception as e:
            logger.warning(f"Failed to get structure cache: {e}")
            return None

    def save_structure_cache(
        self, 
        roundup: RoundUp, 
        folder_structure: Dict[Path, Dict[str, Any]], 
        duplicate_groups: Dict[str, list],
        scan_file_count: int
    ):
        """
        Save folder structure and duplicate groups to cache.
        
        The cache includes scan_file_count so we can detect when
        the scan data has changed and invalidate the cache.
        
        Args:
            roundup: The RoundUp to save cache for
            folder_structure: Dict mapping folder paths to stats
            duplicate_groups: Dict mapping MD5 hashes to file lists
            scan_file_count: Number of files in the scan (for invalidation)
        """
        try:
            db_path = roundup.path / "data.db"
            if not db_path.exists():
                logger.warning("Cannot save cache - database doesn't exist")
                return
                
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # Create cache table if needed
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS structure_cache (
                    id INTEGER PRIMARY KEY DEFAULT 1,
                    folder_structure TEXT NOT NULL,
                    duplicate_groups TEXT NOT NULL,
                    scan_file_count INTEGER NOT NULL,
                    cached_at TEXT NOT NULL
                )
            """)
            
            # Convert Path keys to strings for JSON serialization
            folder_structure_serializable = {str(k): v for k, v in folder_structure.items()}
            
            # For duplicate_groups, we can't serialize FileRecord objects directly
            # So we serialize just the essential info (paths)
            duplicate_groups_serializable = {}
            for md5, records in duplicate_groups.items():
                duplicate_groups_serializable[md5] = [
                    str(getattr(r, 'absolute_path', r)) for r in records
                ]
            
            # Upsert cache
            now = datetime.now().isoformat()
            cursor.execute("""
                INSERT OR REPLACE INTO structure_cache 
                (id, folder_structure, duplicate_groups, scan_file_count, cached_at)
                VALUES (1, ?, ?, ?, ?)
            """, (
                json.dumps(folder_structure_serializable),
                json.dumps(duplicate_groups_serializable),
                scan_file_count,
                now
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Saved structure cache: {len(folder_structure)} folders, "
                       f"{len(duplicate_groups)} duplicate groups, {scan_file_count} files")
            
        except Exception as e:
            logger.warning(f"Failed to save structure cache: {e}")

    def invalidate_structure_cache(self, roundup: RoundUp):
        """
        Invalidate the structure cache for a Round-Up.
        
        Call this when scan data changes (e.g., after a new scan).
        
        Args:
            roundup: The RoundUp to invalidate cache for
        """
        try:
            db_path = roundup.path / "data.db"
            if not db_path.exists():
                return
                
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM structure_cache WHERE id = 1")
            conn.commit()
            conn.close()
            
            logger.info(f"Invalidated structure cache for {roundup.name}")
            
        except Exception as e:
            logger.warning(f"Failed to invalidate structure cache: {e}")


def main():
    """CLI entry point for testing RoundUpManager."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("=" * 70)
    print("JellyRancher Round-Up Manager Test")
    print("=" * 70)

    manager = RoundUpManager()

    # List existing Round-Ups
    print("\n1. Listing existing Round-Ups...")
    roundups = manager.list_all()
    for r in roundups:
        print(f"   - {r.name} (Step {r.current_step}/8, Last modified: {r.last_modified[:19] if r.last_modified else 'Unknown'})")

    # Create a test Round-Up
    print("\n2. Creating test Round-Up...")
    try:
        test_roundup = manager.create("Test Round-Up", source_folders=["C:/Test/Media"])
        print(f"   Created: {test_roundup.name} at {test_roundup.path}")

        # Validate it
        print("\n3. Validating Round-Up...")
        validation = manager.validate_roundup(test_roundup)
        print(f"   Valid: {validation['valid']}")
        if validation['issues']:
            for issue in validation['issues']:
                print(f"   Issue: {issue}")

        # Clean up
        print("\n4. Deleting test Round-Up...")
        manager.delete(test_roundup, confirm=True)
        print("   Deleted successfully")

    except ValueError as e:
        print(f"   Error: {e}")

    print("\n" + "=" * 70)
    print("[SUCCESS] RoundUpManager test completed!")
    print(f"Round-Ups directory: {manager.roundups_dir}")
    print("=" * 70)


if __name__ == "__main__":
    main()
