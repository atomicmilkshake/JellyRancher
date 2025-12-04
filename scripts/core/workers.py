#!/usr/bin/env python3
"""
Shared worker threads for JellyRancher workflows.

Provides reusable QThread implementations for:
- Multi-folder scanning with Jellyfin enrichment
- LLM folder structure analysis
- Metadata lookup via TMDB/OMDb
- Action plan generation

These workers were originally embedded in `jelly_rancher_clean.py`.
Extracting them into this module ensures JellyRancher Studio uses
proper background threading for consistent workflow behavior.
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

from PyQt6.QtCore import QThread, pyqtSignal

from scripts.core.file_scanner import FileScanner, FileRecord
from scripts.core.inventory_repository import InventoryRepository
from scripts.media.llm_structure_analyzer import LLMStructureAnalyzer
from scripts.media.media_metadata_lookup import MediaMetadataLookup
from scripts.core.action_plan import ProposedOperation
from scripts.core.action_plan_generator import ActionPlanGenerator
from scripts.core.app_config import AppConfigManager
from scripts._common.error_handling import log_function_entry_exit

logger = logging.getLogger(__name__)


class MultiScanWorker(QThread):
    """
    Worker thread for scanning multiple folders sequentially.

    Aggregates results from all folders into a combined master inventory
    and enriches file records with Jellyfin data when configured.
    """

    # Signals
    progress = pyqtSignal(str, int, int)  # message, current, total
    finished = pyqtSignal(list, dict, list)  # file_records, folder_structure, session_ids
    error = pyqtSignal(str)

    def __init__(
        self,
        folder_paths: List[Path],
        recursive: bool = True,
        jellyfin_client=None,
        excluded_subfolders: Optional[List[Path]] = None,
    ):
        """
        Initialize multi-folder scanner.

        Args:
            folder_paths: List of Path objects to scan
            recursive: Whether to scan recursively
            jellyfin_client: Optional JellyfinClient for cross-referencing
            excluded_subfolders: Paths to skip during scan
        """
        super().__init__()
        self.folder_paths = folder_paths
        self.recursive = recursive
        self.repository = InventoryRepository()
        self.jellyfin_client = jellyfin_client
        self.excluded_subfolders = [p.resolve() for p in (excluded_subfolders or [])]

    @log_function_entry_exit()
    def run(self):
        """Execute multi-folder scan and Jellyfin cross-reference."""
        try:
            overall_start_time = datetime.now()

            combined_file_records: List[FileRecord] = []
            combined_folder_structure: Dict[Path, Dict[str, Any]] = {}
            session_ids: List[int] = []
            total_folders = len(self.folder_paths)

            for folder_idx, folder_path in enumerate(self.folder_paths, 1):
                self.progress.emit(
                    f"Scanning folder {folder_idx}/{total_folders}: {folder_path.name}",
                    folder_idx - 1,
                    total_folders,
                )
                try:
                    session_id = self.repository.create_scan_session(
                        root_folder=folder_path,
                        recursive=self.recursive,
                        notes=f"Multi-folder scan ({folder_idx}/{total_folders})",
                    )
                    session_ids.append(session_id)

                    app_config = AppConfigManager()
                    calculate_md5 = app_config.is_md5_calculate_during_scan()

                    scanner = FileScanner(
                        progress_callback=lambda msg, cur, tot: self._progress_callback(
                            msg, cur, tot, folder_idx, total_folders
                        ),
                        exclude_paths=set(self.excluded_subfolders),
                        calculate_md5=calculate_md5,
                    )
                    file_records = scanner.scan_folder(folder_path, recursive=self.recursive)
                    stats = scanner.get_statistics()

                    self.repository.add_file_records(session_id, file_records)
                    self.repository.finalize_scan_session(
                        session_id,
                        stats.total_files,
                        stats.total_size_bytes,
                        len(stats.errors),
                    )

                    folder_structure = scanner.get_folder_structure(file_records)
                    combined_file_records.extend(file_records)
                    combined_folder_structure.update(folder_structure)
                    logger.info(
                        "Completed scan %d/%d: %d files from %s",
                        folder_idx,
                        total_folders,
                        stats.total_files,
                        folder_path,
                    )

                except Exception as folder_error:  # pragma: no cover - safety net
                    logger.error(
                        "Error scanning folder %s: %s",
                        folder_path,
                        folder_error,
                        exc_info=True,
                    )
                    self.progress.emit(
                        f"⚠️ Error scanning {folder_path.name}: {str(folder_error)}",
                        folder_idx,
                        total_folders,
                    )

            self.progress.emit(
                f"Completed filesystem scan: {len(combined_file_records)} total files found.",
                total_folders,
                total_folders,
            )

            # Optional Jellyfin cross-reference
            jellyfin_matches = 0
            if self.jellyfin_client and self.jellyfin_client.is_configured():  # pragma: no cover
                self.progress.emit("Querying Jellyfin library...", 0, 1)
                try:
                    jellyfin_items = self.jellyfin_client.get_all_items(
                        item_types=["Movie", "Episode"],
                        fields=["Path", "ProviderIds", "LibraryId"],
                    )

                    path_map = {
                        str(Path(item["Path"]).resolve()): item
                        for item in jellyfin_items
                        if "Path" in item
                    }
                    self.progress.emit(
                        f"Found {len(jellyfin_items)} items in Jellyfin. Cross-referencing...", 1, 1
                    )

                    for record in combined_file_records:
                        record_path_str = str(record.absolute_path.resolve())
                        if record_path_str in path_map:
                            jellyfin_item = path_map[record_path_str]
                            record.jellyfin_id = jellyfin_item.get("Id")
                            record.jellyfin_item_type = jellyfin_item.get("Type")
                            record.jellyfin_library_id = jellyfin_item.get("LibraryId")
                            record.jellyfin_provider_ids = jellyfin_item.get("ProviderIds", {})
                            record.jellyfin_matched = True
                            jellyfin_matches += 1

                    self.progress.emit(
                        f"Jellyfin cross-reference complete. Matched {jellyfin_matches} files.",
                        1,
                        1,
                    )

                    self.progress.emit("Updating inventory database with Jellyfin data...", 0, 1)
                    for session_id in session_ids:
                        self.repository.add_file_records(
                            session_id, combined_file_records, update_existing=True
                        )
                    self.progress.emit("Database updated.", 1, 1)

                except Exception as e:  # pragma: no cover - network errors
                    logger.error("Jellyfin cross-reference failed: %s", e, exc_info=True)
                    self.error.emit(f"Jellyfin error: {e}")

            self.finished.emit(combined_file_records, combined_folder_structure, session_ids)

            overall_duration = (datetime.now() - overall_start_time).total_seconds()
            if overall_duration > 0 and combined_file_records:
                total_files = len(combined_file_records)
                total_bytes = sum(r.size_bytes for r in combined_file_records)
                total_mb = total_bytes / (1024 * 1024)
                files_per_sec = total_files / overall_duration
                mb_per_sec = total_mb / overall_duration

                logger.info(
                    "Multi-scan performance: %.1fs total, %d files (%.1f MB), "
                    "%.1f files/s, %.1f MB/s",
                    overall_duration,
                    total_files,
                    total_mb,
                    files_per_sec,
                    mb_per_sec,
                )

        except Exception as e:  # pragma: no cover - fail-safe
            logger.error("Multi-scan failed: %s", e, exc_info=True)
            self.error.emit(str(e))

    def _progress_callback(
        self,
        message: str,
        current: int,
        total: int,
        folder_idx: int,
        total_folders: int,
    ):
        """
        Forward file-level progress to GUI with folder context.
        """
        enhanced_message = f"[Folder {folder_idx}/{total_folders}] {message}"
        self.progress.emit(enhanced_message, current, total)


class LLMAnalysisWorker(QThread):
    """
    Worker thread for LLM folder structure analysis.

    Prevents GUI freezing during LLM API calls which can take 30+ seconds.
    """

    progress = pyqtSignal(str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(
        self,
        folder_structure: dict,
        scanned_files: List[FileRecord],
        api_key: Optional[str] = None,
        model: str = "Grok-4.1-Fast-Reasoning",
    ):
        super().__init__()
        self.folder_structure = folder_structure
        self.scanned_files = scanned_files
        self.api_key = api_key
        self.model = model

    @log_function_entry_exit()
    def run(self):
        """Execute LLM analysis in background thread."""
        try:
            self.progress.emit("Initializing LLM analyzer...")

            analyzer = LLMStructureAnalyzer(
                model=self.model,
                api_key=self.api_key,
                logger=logger,
            )

            self.progress.emit(f"Preparing folder structure data for {self.model}...")
            structure_summary = self._build_structure_summary()

            self.progress.emit(
                f"Sending analysis request to {self.model} (this may take 30-60 seconds)..."
            )

            analysis_result = analyzer.analyze_structure(structure_summary)

            self.progress.emit("LLM analysis complete!")
            self.finished.emit(analysis_result)

        except Exception as e:  # pragma: no cover - network/API errors
            logger.error("LLM analysis failed: %s", e, exc_info=True)
            self.error.emit(str(e))

    def _build_structure_summary(self) -> dict:
        """
        Convert FileScanner folder_structure to LLMStructureAnalyzer format.
        Includes Jellyfin ProviderIds and MD5 duplicate groups.
        """
        file_record_map = {str(f.absolute_path): f for f in self.scanned_files}

        folders = []
        # Filter out metadata keys (project_name, scan_id, total_files) - only process folder dicts
        metadata_keys = {'project_name', 'scan_id', 'total_files'}
        for folder_path, data in self.folder_structure.items():
            if folder_path in metadata_keys or not isinstance(data, dict):
                continue
            folder_info = {
                "path": str(folder_path),
                "file_count": data["file_count"],
                "total_size_bytes": data["total_size"],
                "file_types": dict(data["file_types"]),
                "file_type_sizes": dict(data["file_type_sizes"]),
                "jellyfin_provider_ids": [],
            }

            for file_record in file_record_map.values():
                if (
                    file_record.parent_folder == folder_path
                    and getattr(file_record, "jellyfin_matched", False)
                    and getattr(file_record, "jellyfin_provider_ids", None)
                ):
                    folder_info["jellyfin_provider_ids"].append(file_record.jellyfin_provider_ids)

            unique_provider_ids = []
            seen_ids = set()
            for p_ids in folder_info["jellyfin_provider_ids"]:
                frozen_p_ids = frozenset(p_ids.items())
                if frozen_p_ids not in seen_ids:
                    unique_provider_ids.append(p_ids)
                    seen_ids.add(frozen_p_ids)
            folder_info["jellyfin_provider_ids"] = unique_provider_ids

            folders.append(folder_info)

        folders.sort(key=lambda x: x["path"])

        from collections import defaultdict as _dd

        md5_map = _dd(list)
        for record in self.scanned_files:
            md5_value = getattr(record, "md5_hash", None)
            if md5_value:
                md5_map[md5_value].append(str(record.absolute_path))

        duplicate_groups = []
        for md5_value, paths in md5_map.items():
            if len(paths) < 2:
                continue
            duplicate_groups.append(
                {
                    "md5": md5_value,
                    "count": len(paths),
                    "example_paths": paths[:5],
                }
            )

        duplicate_groups.sort(key=lambda g: g["count"], reverse=True)

        return {
            "scan_metadata": {
                "total_folders": len(folders),
                "total_files": sum(f["file_count"] for f in folders),
                "total_size_bytes": sum(f["total_size_bytes"] for f in folders),
            },
            "folders": folders,
            "duplicate_groups": duplicate_groups,
        }


class MetadataLookupWorker(QThread):
    """
    Worker thread for metadata lookup from TMDB/OMDb APIs.
    """

    progress = pyqtSignal(str, int, int)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(
        self,
        detected_media: List[dict],
        scanned_files: List[FileRecord],
        tmdb_api_key: Optional[str] = None,
        omdb_api_key: Optional[str] = None,
    ):
        super().__init__()
        self.detected_media = detected_media
        self.scanned_files = scanned_files
        self.tmdb_api_key = tmdb_api_key
        self.omdb_api_key = omdb_api_key

    @log_function_entry_exit()
    def run(self):
        """Execute metadata lookup in background thread."""
        try:
            self.progress.emit("Initializing metadata lookup service...", 0, len(self.detected_media))

            lookup = MediaMetadataLookup(
                tmdb_api_key=self.tmdb_api_key,
                omdb_api_key=self.omdb_api_key,
                cache_dir="data/metadata_cache",
                logger=logger,
            )

            self.progress.emit(
                f"Building canonical database for {len(self.detected_media)} items...",
                0,
                len(self.detected_media),
            )

            canonical_db = lookup.build_canonical_database(
                detected_media=self.detected_media,
                scanned_files=self.scanned_files,
                progress_callback=lambda msg, cur, total: self.progress.emit(msg, cur, total),
            )

            self.progress.emit("Metadata lookup complete!", len(self.detected_media), len(self.detected_media))
            self.finished.emit(canonical_db)

        except Exception as e:  # pragma: no cover - network/API errors
            logger.error("Metadata lookup failed: %s", e, exc_info=True)
            self.error.emit(str(e))


class ActionPlanWorker(QThread):
    """
    Worker thread for generating the action plan.

    Prevents GUI freezing during the potentially complex process of
    correlating all data sources and generating the proposed operations.
    """

    finished = pyqtSignal(list)  # list of ProposedOperation objects
    error = pyqtSignal(str)

    def __init__(
        self,
        scanned_files: List[FileRecord],
        llm_analysis: dict,
        canonical_database: dict,
        app_config: Optional[AppConfigManager] = None,
    ):
        super().__init__()
        self.scanned_files = scanned_files
        self.llm_analysis = llm_analysis
        self.canonical_database = canonical_database
        self.app_config = app_config

    @log_function_entry_exit()
    def run(self):
        """Execute action plan generation in background thread."""
        try:
            generator = ActionPlanGenerator(
                scanned_files=self.scanned_files,
                llm_analysis=self.llm_analysis,
                canonical_database=self.canonical_database,
                app_config=self.app_config,
            )
            action_plan = generator.generate_plan()
            self.finished.emit(action_plan)
        except Exception as e:  # pragma: no cover - logic errors
            logger.error("Action plan generation failed: %s", e, exc_info=True)
            self.error.emit(str(e))


class ScanResultsLoadWorker(QThread):
    """
    Worker thread for loading scan results from database.

    Prevents GUI freezing when loading large scan sessions (5000+ files)
    by performing database I/O and computation in background.

    Loads from Round-Up's scan_files table.
    """

    progress = pyqtSignal(str, int, int)  # message, current, total
    finished = pyqtSignal(list, dict, dict)  # files, folder_structure, duplicate_groups
    error = pyqtSignal(str)

    def __init__(
        self,
        scan_session_id: int,
        inventory_repo: InventoryRepository,
        roundup_db_path: Optional[Path] = None,
        roundup_manager: Optional[Any] = None,
        roundup: Optional[Any] = None,
    ):
        """
        Initialize scan results loader.

        Args:
            scan_session_id: Unused, kept for backwards compatibility
            inventory_repo: Unused, kept for backwards compatibility
            roundup_db_path: Path to Round-Up's data.db
            roundup_manager: RoundUpManager instance for caching (optional)
            roundup: RoundUp instance for caching (optional)
        """
        super().__init__()
        self.scan_session_id = scan_session_id
        self.inventory_repo = inventory_repo
        self.roundup_db_path = roundup_db_path
        self.roundup_manager = roundup_manager
        self.roundup = roundup

    @log_function_entry_exit()
    def run(self):
        """Load scan results and compute statistics in background thread."""
        import sqlite3
        import json
        from collections import defaultdict

        try:
            # Check for cached structure data first (fast path)
            cached_data = None
            if self.roundup_manager and self.roundup:
                self.progress.emit("Checking cache...", 0, 4)
                try:
                    cached_data = self.roundup_manager.get_structure_cache(self.roundup)
                except Exception as e:
                    logger.warning("Failed to check structure cache: %s", e)

            # Load from Round-Up database (no legacy fallback)
            scanned_files = None
            
            print(f"WORKER DEBUG: roundup_db_path = {self.roundup_db_path}")
            print(f"WORKER DEBUG: path exists = {self.roundup_db_path.exists() if self.roundup_db_path else 'N/A'}")

            if self.roundup_db_path and self.roundup_db_path.exists():
                print(f"WORKER DEBUG: Loading from Round-Up database...")
                scanned_files = self._load_from_roundup(sqlite3, json)
                print(f"WORKER DEBUG: Loaded {len(scanned_files)} files")
            else:
                print(f"WORKER DEBUG: No database found!")
                raise ValueError(f"No Round-Up database found at {self.roundup_db_path}. Please run a scan first.")

            # If we have valid cached data, use it instead of recomputing
            if cached_data and cached_data.get('scan_file_count') == len(scanned_files):
                self.progress.emit("Using cached statistics...", 3, 4)
                folder_structure = cached_data.get('folder_structure', {})
                duplicate_groups = cached_data.get('duplicate_groups', {})
                logger.info("Using cached structure: %d folders, %d duplicate groups",
                           len(folder_structure), len(duplicate_groups))
                self.progress.emit("Load complete! (cached)", 4, 4)
                self.finished.emit(scanned_files, folder_structure, duplicate_groups)
                return

            self.progress.emit("Computing folder structure...", 2, 4)

            # Step 3: Compute folder structure
            folder_structure = {}
            folder_stats = defaultdict(
                lambda: {"file_count": 0, "total_size": 0, "file_types": defaultdict(int)}
            )

            for record in scanned_files:
                try:
                    parent = record.absolute_path.parent
                    stats = folder_stats[parent]
                    stats["file_count"] += 1
                    stats["total_size"] += record.size_bytes
                    stats["file_types"][record.extension] += 1
                except Exception as e:
                    logger.warning("Error processing record for folder structure: %s", e)
                    continue

            # Convert defaultdict to regular dict for signal emission
            folder_structure = {
                k: {
                    "file_count": v["file_count"],
                    "total_size": v["total_size"],
                    "file_types": dict(v["file_types"]),
                }
                for k, v in folder_stats.items()
            }

            self.progress.emit("Detecting duplicates...", 3, 4)

            # Step 4: Compute duplicate groups
            md5_map = defaultdict(list)
            for record in scanned_files:
                md5_value = getattr(record, "md5_hash", None)
                if md5_value:
                    md5_map[md5_value].append(record)

            duplicate_groups = {
                md5: records for md5, records in md5_map.items() if len(records) >= 2
            }

            # Save to cache for next time (if Round-Up mode)
            if self.roundup_manager and self.roundup:
                try:
                    self.roundup_manager.save_structure_cache(
                        self.roundup, folder_structure, duplicate_groups, len(scanned_files)
                    )
                except Exception as e:
                    logger.warning("Failed to save structure cache: %s", e)

            self.progress.emit("Load complete!", 4, 4)

            self.finished.emit(scanned_files, folder_structure, duplicate_groups)
            logger.info(
                "Loaded %d files for session %d (%d folders, %d duplicate groups)",
                len(scanned_files),
                self.scan_session_id,
                len(folder_structure),
                len(duplicate_groups),
            )

        except sqlite3.Error as e:
            logger.error("Database error loading scan results: %s", e, exc_info=True)
            self.error.emit(f"Database error: {e}")
        except json.JSONDecodeError as e:
            logger.error("Invalid scan options JSON: %s", e, exc_info=True)
            self.error.emit(f"Invalid session data: {e}")
        except ValueError as e:
            logger.error("Scan session validation error: %s", e, exc_info=True)
            self.error.emit(str(e))
        except Exception as e:
            logger.error("Failed to load scan results: %s", e, exc_info=True)
            self.error.emit(str(e))

    def _load_from_roundup(self, sqlite3, json) -> List[FileRecord]:
        """Load scan results from Round-Up's scan_files table."""
        self.progress.emit("Loading from Round-Up database...", 0, 4)

        conn = sqlite3.connect(str(self.roundup_db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM scan_files')
        total_count = cursor.fetchone()[0]
        print(f"WORKER DEBUG: scan_files count = {total_count}")

        if total_count == 0:
            conn.close()
            raise ValueError("No scan data found in Round-Up database")

        self.progress.emit(f"Loading {total_count} files from Round-Up...", 1, 4)

        cursor.execute('''
            SELECT id, path, relative_path, filename, extension, size_bytes,
                   md5_hash, created_at, modified_at, metadata_json
            FROM scan_files
            ORDER BY path
        ''')

        scanned_files: List[FileRecord] = []
        for row in cursor.fetchall():
            try:
                # Parse metadata JSON if present
                metadata = {}
                if row['metadata_json']:
                    try:
                        metadata = json.loads(row['metadata_json'])
                    except json.JSONDecodeError:
                        pass

                # Create FileRecord from Round-Up data
                # FileRecord requires: absolute_path, size_bytes, extension, parent_folder, scan_timestamp
                abs_path = Path(row['path'])
                record = FileRecord(
                    absolute_path=abs_path,
                    size_bytes=row['size_bytes'] or 0,
                    extension=row['extension'] or '',
                    parent_folder=abs_path.parent,
                    scan_timestamp=datetime.fromisoformat(row['created_at']) if row['created_at'] else datetime.now(),
                    md5_hash=row['md5_hash'] or None,
                )
                scanned_files.append(record)
            except Exception as e:
                logger.warning("Error converting Round-Up row to FileRecord: %s", e)
                continue

        conn.close()
        logger.info("Loaded %d files from Round-Up database", len(scanned_files))
        return scanned_files


