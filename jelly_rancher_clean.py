#!/usr/bin/env python3
"""
JellyRancher - Clean 9-Point Workflow Implementation

A fresh, simple PyQt6 GUI that follows WORKFLOW_SPEC.md exactly.
No legacy cruft, no bloat - just the 9-point workflow.

Usage:
    python jelly_rancher_clean.py
"""

import sys
import logging
from pathlib import Path
from typing import List
from collections import defaultdict
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTextEdit, QListWidget, QTreeWidget,
    QTreeWidgetItem, QTableWidget, QTableWidgetItem, QProgressBar,
    QFileDialog, QMessageBox, QSplitter, QGroupBox, QCheckBox,
    QHeaderView, QAbstractItemView, QTabWidget, QInputDialog, QLineEdit
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor, QFont

# Import our new components
from scripts.core.file_scanner import FileScanner, FileRecord, ScanStatistics
from scripts.core.inventory_repository import InventoryRepository
from scripts.media.llm_structure_analyzer import LLMStructureAnalyzer
from scripts.media.media_metadata_lookup import MediaMetadataLookup
from scripts.core.action_plan import ProposedOperation, ActionType, Confidence
from scripts.core.action_plan_generator import ActionPlanGenerator

# Jellyfin integration (Phase 20)
from scripts.core.jellyfin_config import JellyfinConfigManager
from scripts.core.jellyfin_client import JellyfinClient
from scripts.core.dialogs.jellyfin_settings_dialog import JellyfinSettingsDialog

# Application configuration (Phase 27)
from scripts.core.app_config import AppConfigManager


# Setup logging
# Ensure logs directory exists
Path('data/logs').mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/logs/jellyrancher.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ScanWorker(QThread):
    """
    Background worker thread for folder scanning.

    Prevents GUI freezing during large scans.
    """
    progress = pyqtSignal(str, int, int)  # message, current, total
    finished = pyqtSignal(list, dict, object)  # file_records, statistics, session_id
    error = pyqtSignal(str)  # error message

    def __init__(self, folder_path: Path, recursive: bool = True):
        super().__init__()
        self.folder_path = folder_path
        self.recursive = recursive
        self.repository = InventoryRepository()

    def run(self):
        """Execute scan in background thread."""
        try:
            # Create scan session
            session_id = self.repository.create_scan_session(
                root_folder=self.folder_path,
                recursive=self.recursive,
                notes="GUI scan"
            )

            # Create scanner with progress callback
            scanner = FileScanner(
                progress_callback=self._progress_callback
            )

            # Perform scan
            file_records = scanner.scan_folder(
                self.folder_path,
                recursive=self.recursive
            )

            # Get statistics
            stats = scanner.get_statistics()

            # Save to database
            self.repository.add_file_records(session_id, file_records)
            self.repository.finalize_scan_session(
                session_id,
                stats.total_files,
                stats.total_size_bytes,
                len(stats.errors)
            )

            # Get folder structure
            folder_structure = scanner.get_folder_structure(file_records)

            # Emit success
            self.finished.emit(file_records, folder_structure, session_id)

        except Exception as e:
            logger.error(f"Scan failed: {e}", exc_info=True)
            self.error.emit(str(e))

    def _progress_callback(self, message: str, current: int, total: int):
        """Forward progress to GUI."""
        self.progress.emit(message, current, total)


class MultiScanWorker(QThread):
    """
    Worker thread for scanning multiple folders sequentially.

    Aggregates results from all folders into a combined master inventory.
    """

    # Signals
    progress = pyqtSignal(str, int, int)  # message, current, total
    finished = pyqtSignal(list, dict, list)  # file_records, folder_structure, session_ids
    error = pyqtSignal(str)

    def __init__(self, folder_paths: List[Path], recursive: bool = True, jellyfin_client: JellyfinClient = None):
        """
        Initialize multi-folder scanner.

        Args:
            folder_paths: List of Path objects to scan
            recursive: Whether to scan recursively
            jellyfin_client: Optional JellyfinClient for cross-referencing
        """
        super().__init__()
        self.folder_paths = folder_paths
        self.recursive = recursive
        self.repository = InventoryRepository()
        self.jellyfin_client = jellyfin_client

    def run(self):
        """Execute multi-folder scan and Jellyfin cross-reference."""
        try:
            combined_file_records = []
            combined_folder_structure = {}
            session_ids = []
            total_folders = len(self.folder_paths)

            # --- Filesystem Scan ---
            for folder_idx, folder_path in enumerate(self.folder_paths, 1):
                self.progress.emit(
                    f"Scanning folder {folder_idx}/{total_folders}: {folder_path.name}",
                    folder_idx - 1,
                    total_folders
                )
                try:
                    session_id = self.repository.create_scan_session(
                        root_folder=folder_path,
                        recursive=self.recursive,
                        notes=f"Multi-folder scan ({folder_idx}/{total_folders})"
                    )
                    session_ids.append(session_id)
                    scanner = FileScanner(
                        progress_callback=lambda msg, cur, tot: self._progress_callback(
                            msg, cur, tot, folder_idx, total_folders
                        )
                    )
                    file_records = scanner.scan_folder(folder_path, recursive=self.recursive)
                    stats = scanner.get_statistics()
                    
                    # Save to database (initial records without Jellyfin data)
                    self.repository.add_file_records(session_id, file_records)
                    self.repository.finalize_scan_session(
                        session_id,
                        stats.total_files,
                        stats.total_size_bytes,
                        len(stats.errors)
                    )
                    
                    folder_structure = scanner.get_folder_structure(file_records)
                    combined_file_records.extend(file_records)
                    combined_folder_structure.update(folder_structure)
                    logger.info(f"Completed scan {folder_idx}/{total_folders}: {stats.total_files} files from {folder_path}")

                except Exception as folder_error:
                    logger.error(f"Error scanning folder {folder_path}: {folder_error}", exc_info=True)
                    self.progress.emit(f"⚠️ Error scanning {folder_path.name}: {str(folder_error)}", folder_idx, total_folders)

            self.progress.emit(f"Completed filesystem scan: {len(combined_file_records)} total files found.", total_folders, total_folders)

            # --- Jellyfin Cross-Reference ---
            jellyfin_matches = 0
            if self.jellyfin_client and self.jellyfin_client.is_configured():
                self.progress.emit("Querying Jellyfin library...", 0, 1)
                try:
                    jellyfin_items = self.jellyfin_client.get_all_items(
                        item_types=["Movie", "Episode"],
                        fields=["Path", "ProviderIds", "LibraryId"]
                    )
                    
                    # Create a path lookup map for efficient matching
                    path_map = {
                        str(Path(item['Path']).resolve()): item
                        for item in jellyfin_items if 'Path' in item
                    }
                    self.progress.emit(f"Found {len(jellyfin_items)} items in Jellyfin. Cross-referencing...", 1, 1)

                    # Enrich file records with Jellyfin data
                    for record in combined_file_records:
                        record_path_str = str(record.absolute_path.resolve())
                        if record_path_str in path_map:
                            jellyfin_item = path_map[record_path_str]
                            record.jellyfin_id = jellyfin_item.get('Id')
                            record.jellyfin_item_type = jellyfin_item.get('Type')
                            record.jellyfin_library_id = jellyfin_item.get('LibraryId')
                            record.jellyfin_provider_ids = jellyfin_item.get('ProviderIds', {})
                            record.jellyfin_matched = True
                            jellyfin_matches += 1
                    
                    self.progress.emit(f"Jellyfin cross-reference complete. Matched {jellyfin_matches} files.", 1, 1)
                    
                    # Update database with enriched data
                    # This is inefficient but simple. A better approach would be a bulk update.
                    self.progress.emit("Updating inventory database with Jellyfin data...", 0, 1)
                    for session_id in session_ids:
                        self.repository.add_file_records(session_id, combined_file_records, update_existing=True)
                    self.progress.emit("Database updated.", 1, 1)

                except Exception as e:
                    logger.error(f"Jellyfin cross-reference failed: {e}", exc_info=True)
                    self.error.emit(f"Jellyfin error: {e}")
                    # Continue without Jellyfin data
            
            # Emit combined results
            self.finished.emit(combined_file_records, combined_folder_structure, session_ids)

        except Exception as e:
            logger.error(f"Multi-scan failed: {e}", exc_info=True)
            self.error.emit(str(e))

    def _progress_callback(
        self,
        message: str,
        current: int,
        total: int,
        folder_idx: int,
        total_folders: int
    ):
        """
        Forward file-level progress to GUI with folder context.

        Args:
            message: Progress message from FileScanner
            current: Current file number
            total: Total files in current folder
            folder_idx: Current folder index (1-based)
            total_folders: Total number of folders
        """
        # Enhance message with folder context
        enhanced_message = f"[Folder {folder_idx}/{total_folders}] {message}"
        self.progress.emit(enhanced_message, current, total)


class LLMAnalysisWorker(QThread):
    """
    Worker thread for LLM folder structure analysis.

    Prevents GUI freezing during LLM API calls which can take 30+ seconds.
    """

    # Signals
    progress = pyqtSignal(str)  # status message
    finished = pyqtSignal(dict)  # analysis_result
    error = pyqtSignal(str)  # error message

    def __init__(self, folder_structure: dict, scanned_files: list, api_key: str = None, model: str = "Claude-Sonnet-4.5"):
        """
        Initialize LLM analysis worker.

        Args:
            folder_structure: Folder structure dict from FileScanner
            scanned_files: List of FileRecord objects (including Jellyfin data)
            api_key: Poe API key (optional, falls back to env var)
            model: LLM model to use
        """
        super().__init__()
        self.folder_structure = folder_structure
        self.scanned_files = scanned_files
        self.api_key = api_key
        self.model = model

    def run(self):
        """Execute LLM analysis in background thread."""
        try:
            self.progress.emit("Initializing LLM analyzer...")

            # Initialize analyzer
            analyzer = LLMStructureAnalyzer(
                model=self.model,
                api_key=self.api_key,
                logger=logger
            )

            self.progress.emit(f"Preparing folder structure data for {self.model}...")

            # Convert folder_structure to format expected by analyzer
            # LLMStructureAnalyzer expects a richer structure summary
            # We need to adapt our simple folder_structure dict
            structure_summary = self._build_structure_summary()

            self.progress.emit(f"Sending analysis request to {self.model} (this may take 30-60 seconds)...")

            # Perform analysis
            analysis_result = analyzer.analyze_structure(structure_summary)

            self.progress.emit("LLM analysis complete!")

            # Emit success
            self.finished.emit(analysis_result)

        except Exception as e:
            logger.error(f"LLM analysis failed: {e}", exc_info=True)
            self.error.emit(str(e))

    def _build_structure_summary(self) -> dict:
        """
        Convert FileScanner folder_structure to LLMStructureAnalyzer format,
        including Jellyfin ProviderIds.

        Returns:
            Structure summary dict compatible with LLMStructureAnalyzer
        """
        # Create a map for quick lookup of FileRecord by absolute path
        file_record_map = {str(f.absolute_path): f for f in self.scanned_files}

        folders = []
        for folder_path, data in self.folder_structure.items():
            folder_info = {
                'path': str(folder_path),
                'file_count': data['file_count'],
                'total_size_bytes': data['total_size'],
                'file_types': dict(data['file_types']),
                'file_type_sizes': dict(data['file_type_sizes']),
                'jellyfin_provider_ids': []  # Collect provider IDs for files in this folder
            }

            # Iterate through files in this folder to collect Jellyfin ProviderIds
            for file_path_str in file_record_map:
                file_record = file_record_map[file_path_str]
                if (
                    file_record.parent_folder == folder_path
                    and getattr(file_record, "jellyfin_matched", False)
                    and getattr(file_record, "jellyfin_provider_ids", None)
                ):
                    folder_info['jellyfin_provider_ids'].append(file_record.jellyfin_provider_ids)
            
            # Remove duplicates from provider IDs
            unique_provider_ids = []
            seen_ids = set()
            for p_ids in folder_info['jellyfin_provider_ids']:
                # Convert dict to frozenset of (key, value) tuples for hashing
                frozen_p_ids = frozenset(p_ids.items())
                if frozen_p_ids not in seen_ids:
                    unique_provider_ids.append(p_ids)
                    seen_ids.add(frozen_p_ids)
            folder_info['jellyfin_provider_ids'] = unique_provider_ids

            folders.append(folder_info)

        # Sort folders by path for consistency
        folders.sort(key=lambda x: x['path'])

        # Build MD5 duplicate groups for LLM context
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
            duplicate_groups.append({
                'md5': md5_value,
                'count': len(paths),
                'example_paths': paths[:5],
            })

        # Sort duplicate groups by size (largest first) for readability
        duplicate_groups.sort(key=lambda g: g['count'], reverse=True)

        return {
            'scan_metadata': {
                'total_folders': len(folders),
                'total_files': sum(f['file_count'] for f in folders),
                'total_size_bytes': sum(f['total_size_bytes'] for f in folders)
            },
            'folders': folders,
            'duplicate_groups': duplicate_groups,
        }


class MetadataLookupWorker(QThread):
    """
    Worker thread for metadata lookup from TMDB/OMDb APIs.
    
    Takes LLM-detected media and queries external APIs to build canonical database
    with correct years, titles, episode information, etc.
    """
    
    # Signals
    progress = pyqtSignal(str, int, int)  # message, current, total
    finished = pyqtSignal(dict)  # canonical_database
    error = pyqtSignal(str)  # error message
    
    def __init__(self, detected_media: list, scanned_files: list, tmdb_api_key: str = None, omdb_api_key: str = None):
        """
        Initialize metadata lookup worker.
        
        Args:
            detected_media: List of detected media from LLM analysis
            scanned_files: List of FileRecord objects (including Jellyfin data)
            tmdb_api_key: TMDB API key (optional, falls back to env var)
            omdb_api_key: OMDb API key (optional, falls back to env var)
        """
        super().__init__()
        self.detected_media = detected_media
        self.scanned_files = scanned_files
        self.tmdb_api_key = tmdb_api_key
        self.omdb_api_key = omdb_api_key
    
    def run(self):
        """Execute metadata lookup in background thread."""
        try:
            from datetime import datetime
            
            self.progress.emit("Initializing metadata lookup service...", 0, len(self.detected_media))
            
            # Create a map from detected media title/year to FileRecord for Jellyfin ProviderIds
            # This is a simplified mapping and might need refinement for complex cases
            detected_media_to_filerecord = {}
            for file_record in self.scanned_files:
                # Assuming a simple match for now based on title and year estimate
                # In a real scenario, this might involve more sophisticated matching
                # or the detected_media items would carry a reference to their FileRecord.
                # For this implementation, we'll try to match based on common attributes.
                # This part needs to be carefully considered based on how detected_media is structured.
                # For now, we'll skip direct mapping and iterate through scanned_files for each detected_media.
                pass # We will iterate through scanned_files inside the loop for each detected_media item.

            # Initialize lookup service
            lookup = MediaMetadataLookup(
                tmdb_api_key=self.tmdb_api_key,
                omdb_api_key=self.omdb_api_key,
                cache_dir='data/metadata_cache',
                logger=logger
            )
            
            self.progress.emit(f"Building canonical database for {len(self.detected_media)} items...", 0, len(self.detected_media))
            
            canonical_db = {
                'timestamp': datetime.now().isoformat(),
                'total_items': len(self.detected_media),
                'movies': [],
                'tv_shows': [],
                'lookup_failures': [],
                'multi_part_episodes': []
            }
            
            for idx, item in enumerate(self.detected_media):
                title = item.get('title')
                media_type = item.get('type')
                year_estimate = item.get('year_estimate')
                
                self.progress.emit(
                    f"Querying {media_type}: {title} ({year_estimate or 'unknown year'})...",
                    idx + 1,
                    len(self.detected_media)
                )
                
                # Find associated FileRecord to get Jellyfin ProviderIds
                jellyfin_provider_ids = {}
                for file_record in self.scanned_files:
                    # This is a very basic heuristic. A more robust solution would involve
                    # the LLM analysis output including a reference to the original file_record.
                    # For now, we assume a direct match on title and year for simplicity.
                    if file_record.jellyfin_matched and file_record.jellyfin_provider_ids:
                        # This logic needs to be refined. How do we link a detected_media item
                        # (which is a conceptual movie/show) back to a specific file_record?
                        # For now, we'll just pass the provider IDs if we find any for *any* file
                        # that might be related. This is a placeholder for more precise linking.
                        # A better approach would be for the LLM to return the file_record.absolute_path
                        # or a unique ID for the detected media.
                        # For now, we'll just take the first matching provider_ids we find.
                        # This is a known limitation for this iteration.
                        jellyfin_provider_ids = file_record.jellyfin_provider_ids
                        break # Found some provider IDs, use them.

                if media_type == 'movie':
                    metadata = lookup.lookup_movie(title, year_estimate, jellyfin_provider_ids=jellyfin_provider_ids)
                    if metadata:
                        metadata['original_detection'] = item
                        canonical_db['movies'].append(metadata)
                    else:
                        canonical_db['lookup_failures'].append(item)
                
                elif media_type == 'tv_show':
                    metadata = lookup.lookup_tv_show(title, year_estimate, jellyfin_provider_ids=jellyfin_provider_ids)
                    if metadata:
                        metadata['original_detection'] = item
                        canonical_db['tv_shows'].append(metadata)
                        
                        # Check for multi-part episodes in seasons
                        for season in metadata.get('seasons', []):
                            for episode in season.get('episodes', []):
                                if episode.get('is_multi_part'):
                                    canonical_db['multi_part_episodes'].append({
                                        'show_title': title,
                                        'season_number': season['season_number'],
                                        'episode_number': episode['episode_number'],
                                        'episode_name': episode['name'],
                                        'needs_nfo': True
                                    })
                    else:
                        canonical_db['lookup_failures'].append(item)
            
            self.progress.emit("Metadata lookup complete!", len(self.detected_media), len(self.detected_media))
            
            # Emit success
            self.finished.emit(canonical_db)
            
        except Exception as e:
            logger.error(f"Metadata lookup failed: {e}", exc_info=True)
            self.error.emit(str(e))


class ActionPlanWorker(QThread):
    """
    Worker thread for generating the action plan.

    Prevents GUI freezing during the potentially complex process of
    correlating all data sources and generating the proposed operations.
    """

    finished = pyqtSignal(list)  # list of ProposedOperation objects
    error = pyqtSignal(str)

    def __init__(self, scanned_files: list, llm_analysis: dict, canonical_database: dict, app_config=None):
        super().__init__()
        self.scanned_files = scanned_files
        self.llm_analysis = llm_analysis
        self.canonical_database = canonical_database
        self.app_config = app_config

    def run(self):
        """Execute action plan generation in background thread."""
        try:
            generator = ActionPlanGenerator(
                scanned_files=self.scanned_files,
                llm_analysis=self.llm_analysis,
                canonical_database=self.canonical_database,
                app_config=self.app_config
            )
            action_plan = generator.generate_plan()
            self.finished.emit(action_plan)
        except Exception as e:
            logger.error(f"Action plan generation failed: {e}", exc_info=True)
            self.error.emit(str(e))


class JellyRancherClean(QMainWindow):
    """Clean implementation of the 9-point Jellyfin workflow."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("JellyRancher - Jellyfin Media Organizer")
        self.setGeometry(100, 100, 1024, 600)

        # Data storage
        self.scanned_files = []
        self.folder_structure = {}
        self.action_plan = []
        self.current_session_id = None

        # Multiple folder selection
        self.selected_folders = []  # List of Path objects
        self.combined_session_ids = []  # Track all scan sessions

        # LLM analysis results
        self.llm_analysis = None
        self.detected_media = []
        self.reorganization_plan = {}
        
        # Metadata lookup results (Point 4)
        self.canonical_database = None
        self.multi_part_episodes = []

        # MD5 duplicate detection (Point 2 enhancement)
        self.duplicate_groups = {}  # md5_hash -> list[FileRecord]

        # Initialize repository
        self.repository = InventoryRepository()

        # Jellyfin integration (Phase 20)
        self.jellyfin_config = JellyfinConfigManager()
        self.jellyfin_client = None

        # Application configuration (Phase 27)
        self.app_config = AppConfigManager()

        # Worker threads
        self.scan_worker = None
        self.llm_worker = None
        self.metadata_worker = None
        self.action_plan_worker = None

        self.init_ui()

    def init_ui(self):
        """Initialize the user interface."""
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Title and Settings button
        title_layout = QHBoxLayout()

        title = QLabel("JellyRancher - 9-Point Jellyfin Workflow")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_layout.addWidget(title)

        # Jellyfin Settings button (Phase 20)
        settings_btn = QPushButton("Jellyfin Settings")
        settings_btn.clicked.connect(self.open_jellyfin_settings)
        settings_btn.setMaximumWidth(150)
        title_layout.addWidget(settings_btn)

        layout.addLayout(title_layout)
        
        # Create tab widget
        self.tabs = QTabWidget()
        
        # Tab 1-2: Scanning & Overview
        self.tab_scan = self.create_scan_tab()
        self.tabs.addTab(self.tab_scan, "1-2. Scan & Overview")
        
        # Tab 3-4: LLM & Metadata
        self.tab_metadata = self.create_metadata_tab()
        self.tabs.addTab(self.tab_metadata, "3-4. LLM & Metadata")
        
        # Tab 5: Action Review
        self.tab_review = self.create_review_tab()
        self.tabs.addTab(self.tab_review, "5. Review Actions")
        
        # Tab 6-7: Snapshot & Execute
        self.tab_execute = self.create_execute_tab()
        self.tabs.addTab(self.tab_execute, "6-7. Snapshot & Execute")
        
        # Tab 8-9: Subtitles
        self.tab_subtitles = self.create_subtitles_tab()
        self.tabs.addTab(self.tab_subtitles, "8-9. Subtitles")
        
        layout.addWidget(self.tabs)
        
        # Status bar
        self.statusBar().showMessage("Ready. Start by scanning folders in Tab 1.")

    def create_scan_tab(self):
        """Create tab for Steps 1-2: Scanning and Overview."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Step 1: Scan
        scan_group = QGroupBox("Step 1: Folder Scanning")
        scan_layout = QVBoxLayout()

        # Folder selection list
        scan_layout.addWidget(QLabel("Selected Folders to Scan:"))
        self.selected_folders_list = QListWidget()
        self.selected_folders_list.setMaximumHeight(120)
        scan_layout.addWidget(self.selected_folders_list)

        # Folder management buttons
        folder_button_layout = QHBoxLayout()

        btn_add_folder = QPushButton("➕ Add Folder")
        btn_add_folder.clicked.connect(self.add_folder_to_list)
        folder_button_layout.addWidget(btn_add_folder)

        btn_remove_folder = QPushButton("➖ Remove Selected")
        btn_remove_folder.clicked.connect(self.remove_selected_folder)
        folder_button_layout.addWidget(btn_remove_folder)

        btn_clear_folders = QPushButton("Clear All")
        btn_clear_folders.clicked.connect(self.clear_folder_list)
        folder_button_layout.addWidget(btn_clear_folders)

        folder_button_layout.addStretch()
        scan_layout.addLayout(folder_button_layout)

        # Start scan button
        btn_scan = QPushButton("Start Scan")
        btn_scan.clicked.connect(self.step_1_scan_folders)
        btn_scan.setStyleSheet("font-weight: bold; padding: 8px;")
        scan_layout.addWidget(btn_scan)

        # Progress bar for scanning
        self.scan_progress = QProgressBar()
        self.scan_progress.setVisible(False)
        scan_layout.addWidget(self.scan_progress)

        self.scan_status = QLabel("No folders selected. Click 'Add Folder' to begin.")
        scan_layout.addWidget(self.scan_status)

        self.scan_file_list = QListWidget()
        scan_layout.addWidget(QLabel("Scanned Files (showing first 500):"))
        scan_layout.addWidget(self.scan_file_list)
        
        scan_group.setLayout(scan_layout)
        layout.addWidget(scan_group)
        
        # Step 2: Overview
        overview_group = QGroupBox("Step 2: Hierarchical Overview")
        overview_layout = QVBoxLayout()
        
        btn_overview = QPushButton("Generate Overview")
        btn_overview.clicked.connect(self.step_2_overview)
        overview_layout.addWidget(btn_overview)
        
        self.overview_tree = QTreeWidget()
        self.overview_tree.setHeaderLabels(["Folder", "Files", "Size (MB)", "Jellyfin Matches", "Details"])
        self.overview_tree.setColumnWidth(0, 450)
        self.overview_tree.setColumnWidth(3, 120)
        overview_layout.addWidget(self.overview_tree)

        # MD5 duplicate summary
        self.duplicate_summary_label = QLabel("MD5 duplicate groups: not computed yet.")
        overview_layout.addWidget(self.duplicate_summary_label)

        self.duplicate_tree = QTreeWidget()
        self.duplicate_tree.setHeaderLabels(["MD5 Hash", "File Count", "Example Paths"])
        self.duplicate_tree.setColumnWidth(0, 260)
        self.duplicate_tree.setColumnWidth(1, 80)
        overview_layout.addWidget(self.duplicate_tree)
        
        overview_group.setLayout(overview_layout)
        layout.addWidget(overview_group)
        
        return widget

    def create_metadata_tab(self):
        """Create tab for Steps 3-4: LLM and Metadata."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Step 3: LLM
        llm_group = QGroupBox("Step 3: LLM Reorganization Proposal")
        llm_layout = QVBoxLayout()
        
        llm_layout.addWidget(QLabel("Submit folder structure to Claude API for Jellyfin-compliant reorganization:"))
        btn_llm = QPushButton("Get LLM Proposal")
        btn_llm.clicked.connect(self.step_3_llm_proposal)
        llm_layout.addWidget(btn_llm)
        
        self.llm_output = QTextEdit()
        self.llm_output.setReadOnly(True)
        self.llm_output.setPlaceholderText("LLM proposal will appear here...")
        llm_layout.addWidget(self.llm_output)
        
        llm_group.setLayout(llm_layout)
        layout.addWidget(llm_group)
        
        # Step 4: Metadata
        metadata_group = QGroupBox("Step 4: Build Metadata Database")
        metadata_layout = QVBoxLayout()
        
        metadata_layout.addWidget(QLabel("Query TMDB/TVDB for canonical metadata:"))
        btn_metadata = QPushButton("Build Metadata DB")
        btn_metadata.clicked.connect(self.step_4_metadata)
        metadata_layout.addWidget(btn_metadata)
        
        self.metadata_progress = QProgressBar()
        metadata_layout.addWidget(self.metadata_progress)
        
        self.metadata_output = QTextEdit()
        self.metadata_output.setReadOnly(True)
        self.metadata_output.setPlaceholderText("Metadata results will appear here...")
        metadata_layout.addWidget(self.metadata_output)
        
        metadata_group.setLayout(metadata_layout)
        layout.addWidget(metadata_group)
        
        return widget

    def create_review_tab(self):
        """Create tab for Step 5: Action Review."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        layout.addWidget(QLabel("Step 5: Review and Edit Action Plan"))
        
        # Color legend
        legend = QLabel(
            "🟢 Green = High confidence (auto-safe) | "
            "🟡 Yellow = Review recommended | "
            "🔴 Red = Manual decision required"
        )
        legend.setWordWrap(True)
        layout.addWidget(legend)
        
        # Action table
        self.action_table = QTableWidget()
        self.action_table.setColumnCount(7)
        self.action_table.setHorizontalHeaderLabels([
            "Source File", "Proposed Destination", "Action", "Confidence", 
            "Jellyfin Status", "Notes", "Approve"
        ])
        self.action_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.action_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.action_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        self.action_table.setColumnWidth(2, 100) # Action
        self.action_table.setColumnWidth(3, 100) # Confidence
        self.action_table.setColumnWidth(4, 120) # Jellyfin Status
        self.action_table.setColumnWidth(6, 80)  # Approve
        layout.addWidget(self.action_table)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_load = QPushButton("Load Action Plan")
        btn_load.clicked.connect(self.step_5_review)
        btn_export = QPushButton("Export to CSV")
        btn_dry_run = QPushButton("Dry Run Preview")
        btn_layout.addWidget(btn_load)
        btn_layout.addWidget(btn_export)
        btn_layout.addWidget(btn_dry_run)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        return widget

    def create_execute_tab(self):
        """Create tab for Steps 6-7: Snapshot and Execute."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Step 6: Snapshot
        snapshot_group = QGroupBox("Step 6: Create Transaction Snapshot")
        snapshot_layout = QVBoxLayout()
        
        snapshot_layout.addWidget(QLabel("Create SQLite transaction log for complete rollback capability:"))
        btn_snapshot = QPushButton("Create Snapshot")
        btn_snapshot.clicked.connect(self.step_6_snapshot)
        snapshot_layout.addWidget(btn_snapshot)
        
        self.snapshot_info = QTextEdit()
        self.snapshot_info.setReadOnly(True)
        self.snapshot_info.setMaximumHeight(100)
        snapshot_layout.addWidget(self.snapshot_info)
        
        snapshot_group.setLayout(snapshot_layout)
        layout.addWidget(snapshot_group)
        
        # Step 7: Execute
        execute_group = QGroupBox("Step 7: Execute Reorganization")
        execute_layout = QVBoxLayout()
        
        execute_layout.addWidget(QLabel("⚠️ This will perform actual file operations!"))
        btn_execute = QPushButton("Execute File Operations")
        btn_execute.clicked.connect(self.step_7_execute)
        btn_execute.setStyleSheet("background-color: #ff6b6b; color: white; font-weight: bold;")
        execute_layout.addWidget(btn_execute)
        
        self.execute_progress = QProgressBar()
        execute_layout.addWidget(self.execute_progress)
        
        self.execute_log = QTextEdit()
        self.execute_log.setReadOnly(True)
        self.execute_log.setPlaceholderText("Execution log will appear here...")
        execute_layout.addWidget(self.execute_log)
        
        execute_group.setLayout(execute_layout)
        layout.addWidget(execute_group)
        
        return widget

    def create_subtitles_tab(self):
        """Create tab for Steps 8-9: Subtitle handling."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Step 8: Check
        check_group = QGroupBox("Step 8: Subtitle Coverage Evaluation")
        check_layout = QVBoxLayout()
        
        check_layout.addWidget(QLabel("Scan for embedded and external English subtitles:"))
        btn_check = QPushButton("Check Subtitle Coverage")
        btn_check.clicked.connect(self.step_8_subtitle_check)
        check_layout.addWidget(btn_check)
        
        self.subtitle_check_list = QListWidget()
        check_layout.addWidget(QLabel("Files Missing English Subtitles:"))
        check_layout.addWidget(self.subtitle_check_list)
        
        check_group.setLayout(check_layout)
        layout.addWidget(check_group)
        
        # Step 9: Download
        download_group = QGroupBox("Step 9: Subtitle Acquisition")
        download_layout = QVBoxLayout()
        
        download_layout.addWidget(QLabel("Download subtitles from OpenSubtitles, Podnapisi, etc.:"))
        btn_download = QPushButton("Download Missing Subtitles")
        btn_download.clicked.connect(self.step_9_subtitle_download)
        download_layout.addWidget(btn_download)
        
        self.subtitle_download_progress = QProgressBar()
        download_layout.addWidget(self.subtitle_download_progress)
        
        self.subtitle_download_log = QTextEdit()
        self.subtitle_download_log.setReadOnly(True)
        self.subtitle_download_log.setPlaceholderText("Download log will appear here...")
        download_layout.addWidget(self.subtitle_download_log)
        
        download_group.setLayout(download_layout)
        layout.addWidget(download_group)
        
        return widget

    def log_status(self, message):
        """Log a status message to the status bar."""
        self.statusBar().showMessage(message)
        print(message)  # Also print to console

    # =========================================================================
    # WORKFLOW STEP 1: FOLDER SCANNING - MULTI-FOLDER SUPPORT
    # =========================================================================

    def add_folder_to_list(self):
        """Add a folder to the scan list."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Folder to Add",
            "",
            QFileDialog.Option.ShowDirsOnly
        )

        if not folder:
            return

        folder_path = Path(folder)

        # Check for duplicates
        if folder_path in self.selected_folders:
            QMessageBox.warning(
                self,
                "Duplicate Folder",
                f"This folder is already in the list:\n{folder_path}"
            )
            return

        # Add to list
        self.selected_folders.append(folder_path)
        self.update_folder_list_display()
        self.log_status(f"Added folder: {folder_path}")

    def remove_selected_folder(self):
        """Remove the selected folder from the list."""
        current_row = self.selected_folders_list.currentRow()

        if current_row < 0:
            QMessageBox.information(
                self,
                "No Selection",
                "Please select a folder to remove from the list."
            )
            return

        # Remove from list
        removed_folder = self.selected_folders.pop(current_row)
        self.update_folder_list_display()
        self.log_status(f"Removed folder: {removed_folder}")

    def clear_folder_list(self):
        """Clear all selected folders."""
        if not self.selected_folders:
            return

        reply = QMessageBox.question(
            self,
            "Clear All Folders",
            f"Remove all {len(self.selected_folders)} folders from the list?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.selected_folders.clear()
            self.update_folder_list_display()
            self.log_status("Cleared all folders")

    def update_folder_list_display(self):
        """Refresh the folder list widget display."""
        self.selected_folders_list.clear()

        for folder in self.selected_folders:
            self.selected_folders_list.addItem(str(folder))

        # Update status
        count = len(self.selected_folders)
        if count == 0:
            self.scan_status.setText("No folders selected. Click 'Add Folder' to begin.")
        elif count == 1:
            self.scan_status.setText(f"Ready to scan 1 folder")
        else:
            self.scan_status.setText(f"Ready to scan {count} folders")

    def step_1_scan_folders(self):
        """Step 1: Scan multiple folders and generate master file inventory."""
        # Don't start new scan if one is running
        if self.scan_worker and self.scan_worker.isRunning():
            QMessageBox.warning(
                self,
                "Scan In Progress",
                "A scan is already running. Please wait for it to complete."
            )
            return

        # Check if folders are selected
        if not self.selected_folders:
            QMessageBox.warning(
                self,
                "No Folders Selected",
                "Please add at least one folder to scan using the 'Add Folder' button."
            )
            return

        self.log_status(f"Starting scan of {len(self.selected_folders)} folder(s)...")

        # Show progress bar
        self.scan_progress.setVisible(True)
        self.scan_progress.setValue(0)

        if len(self.selected_folders) == 1:
            self.scan_status.setText(f"Scanning: {self.selected_folders[0].name}")
        else:
            self.scan_status.setText(f"Scanning {len(self.selected_folders)} folders...")

        # Create and start multi-scan worker thread
        self.scan_worker = MultiScanWorker(
            self.selected_folders.copy(),
            recursive=True,
            jellyfin_client=self.jellyfin_client
        )
        self.scan_worker.progress.connect(self._on_scan_progress)
        self.scan_worker.finished.connect(self._on_multiscan_finished)
        self.scan_worker.error.connect(self._on_scan_error)
        self.scan_worker.start()

    def _on_scan_progress(self, message: str, current: int, total: int):
        """Handle scan progress updates."""
        if total > 0:
            progress = int((current / total) * 100)
            self.scan_progress.setValue(progress)
            self.scan_status.setText(f"{message} ({current}/{total})")
        else:
            self.scan_status.setText(message)

    def _on_scan_finished(self, file_records: list, folder_structure: dict, session_id: int):
        """Handle scan completion."""
        self.scanned_files = file_records
        self.folder_structure = folder_structure
        self.current_session_id = session_id

        # Hide progress
        self.scan_progress.setVisible(False)

        # Update file list
        self.scan_file_list.clear()

        # Show first 500 files
        display_count = min(500, len(file_records))
        for record in file_records[:display_count]:
            # Get relative path for display
            try:
                rel_path = record.absolute_path.relative_to(record.absolute_path.parents[2])
            except (ValueError, IndexError):
                rel_path = record.absolute_path.name

            self.scan_file_list.addItem(f"{rel_path} ({self._format_size(record.size_bytes)})")

        if len(file_records) > 500:
            self.scan_file_list.addItem(f"... and {len(file_records) - 500} more files")

        # Update status
        total_size = sum(r.size_bytes for r in file_records)
        self.scan_status.setText(
            f"✓ Scan complete: {len(file_records)} files "
            f"({self._format_size(total_size)}) in {len(folder_structure)} folders"
        )

        self.log_status(f"Scan complete: {len(file_records)} files found")

        # Automatically trigger Step 2
        self.step_2_overview()

    def _on_multiscan_finished(
        self,
        file_records: list,
        folder_structure: dict,
        session_ids: list
    ):
        """
        Handle multi-folder scan completion and display Jellyfin stats.
        """
        self.scanned_files = file_records
        self.folder_structure = folder_structure
        self.combined_session_ids = session_ids

        # Hide progress
        self.scan_progress.setVisible(False)

        # Update file list
        self.scan_file_list.clear()
        display_count = min(500, len(file_records))
        for record in file_records[:display_count]:
            try:
                rel_path = record.absolute_path.relative_to(record.absolute_path.parents[2])
            except (ValueError, IndexError):
                rel_path = record.absolute_path.name
            
            # Add Jellyfin status indicator
            jellyfin_status = "✓" if record.jellyfin_matched else " "
            self.scan_file_list.addItem(f"[{jellyfin_status}] {rel_path} ({self._format_size(record.size_bytes)})")

        if len(file_records) > 500:
            self.scan_file_list.addItem(f"... and {len(file_records) - 500} more files")

        # --- Display Statistics ---
        total_size = sum(r.size_bytes for r in file_records)
        folder_count = len(self.selected_folders)
        jellyfin_matches = sum(1 for r in file_records if r.jellyfin_matched)
        
        status_text = (
            f"✓ Scan complete: {len(file_records)} files ({self._format_size(total_size)}) "
            f"from {folder_count} folders."
        )
        
        if self.jellyfin_client and self.jellyfin_client.is_configured():
            status_text += f" | Jellyfin matches: {jellyfin_matches}"

        self.scan_status.setText(status_text)
        self.log_status(status_text.replace(" | ", ", "))

        # Automatically trigger Step 2
        self.step_2_overview()

    def _on_scan_error(self, error_message: str):
        """Handle scan errors."""
        self.scan_progress.setVisible(False)
        self.scan_status.setText(f"❌ Scan failed: {error_message}")

        QMessageBox.critical(
            self,
            "Scan Error",
            f"An error occurred during scanning:\n\n{error_message}"
        )

        self.log_status(f"Scan failed: {error_message}")

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """Format bytes as human-readable size."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"

    # =========================================================================
    # WORKFLOW STEP 2: HIERARCHICAL OVERVIEW
    # =========================================================================
    
    def step_2_overview(self):
        """Step 2: Display hierarchical folder structure with Jellyfin stats."""
        self.log_status("Step 2: Generating hierarchical overview...")

        if not self.folder_structure:
            QMessageBox.warning(self, "Error", "No folder structure available. Run Step 1 first.")
            return

        self.overview_tree.clear()

        # Create a map of parent folders to their scanned files for efficient lookup
        folder_to_files_map = defaultdict(list)
        for file_record in self.scanned_files:
            folder_to_files_map[file_record.parent_folder].append(file_record)

        for folder_path, data in sorted(self.folder_structure.items()):
            size_mb = data['total_size'] / (1024 * 1024)
            
            # Get Jellyfin match count for this folder
            files_in_folder = folder_to_files_map.get(folder_path, [])
            jellyfin_matches = sum(1 for f in files_in_folder if getattr(f, "jellyfin_matched", False))
            jellyfin_match_str = (
                f"{jellyfin_matches}"
                if self.jellyfin_client and self.jellyfin_client.is_configured()
                else "N/A"
            )

            sorted_types = sorted(data['file_types'].items(), key=lambda x: x[1], reverse=True)
            details = ", ".join([f"{ext}: {count}" for ext, count in sorted_types[:4]])

            item = QTreeWidgetItem([
                str(folder_path),
                str(data['file_count']),
                f"{size_mb:.1f}",
                jellyfin_match_str,
                details
            ])
            
            # Color coding for Jellyfin status
            if jellyfin_matches > 0:
                if jellyfin_matches == data['file_count']:
                    item.setBackground(3, QColor(200, 255, 200)) # All matched - green
                else:
                    item.setBackground(3, QColor(255, 255, 200)) # Partially matched - yellow
            
            self.overview_tree.addTopLevelItem(item)

        # ------------------------------------------------------------------
        # MD5 duplicate grouping (Point 2 enhancement)
        # ------------------------------------------------------------------
        self.duplicate_tree.clear()
        self.duplicate_groups = {}

        md5_map = defaultdict(list)
        for record in self.scanned_files:
            md5_value = getattr(record, "md5_hash", None)
            if md5_value:
                md5_map[md5_value].append(record)

        for md5_value, records in md5_map.items():
            if len(records) < 2:
                continue  # not a duplicate group
            self.duplicate_groups[md5_value] = records

        if not self.duplicate_groups:
            self.duplicate_summary_label.setText("MD5 duplicate groups: none detected.")
        else:
            total_files = sum(len(v) for v in self.duplicate_groups.values())
            self.duplicate_summary_label.setText(
                f"MD5 duplicate groups: {len(self.duplicate_groups)} groups, {total_files} files."
            )

            for md5_value, records in sorted(self.duplicate_groups.items(), key=lambda x: len(x[1]), reverse=True):
                example_paths = []
                for rec in records[:3]:
                    try:
                        example_paths.append(str(rec.absolute_path))
                    except Exception:
                        example_paths.append("<unknown path>")

                item = QTreeWidgetItem([
                    md5_value,
                    str(len(records)),
                    "; ".join(example_paths)
                ])
                self.duplicate_tree.addTopLevelItem(item)

        self.log_status(
            f"Overview complete: {len(self.folder_structure)} folders analyzed; "
            f"{len(self.duplicate_groups)} MD5 duplicate groups detected."
        )

    # =========================================================================
    # WORKFLOW STEP 3: LLM PROPOSAL
    # =========================================================================
    
    def step_3_llm_proposal(self):
        """Step 3: Get LLM reorganization proposal."""
        # Don't start if already running
        if self.llm_worker and self.llm_worker.isRunning():
            QMessageBox.warning(
                self,
                "Analysis In Progress",
                "LLM analysis is already running. Please wait for it to complete."
            )
            return

        # Check if we have folder structure from step 2
        if not self.folder_structure:
            QMessageBox.warning(
                self,
                "No Folder Structure",
                "Please complete Steps 1-2 (scan folders) before running LLM analysis."
            )
            return

        self.log_status("Starting LLM analysis...")

        # Clear previous output
        self.llm_output.clear()
        self.llm_output.append("Initializing LLM analysis...\n")

        # Check for API key (from environment or prompt user)
        import os
        api_key = os.getenv('OPENAI_API_KEY')

        if not api_key:
            # Prompt for API key
            api_key, ok = QInputDialog.getText(
                self,
                "Poe API Key Required",
                "Enter your Poe.com API key:\n\n"
                "(Set OPENAI_API_KEY environment variable to avoid this prompt)\n"
                "Get your key from: https://poe.com/api_key",
                echo=QLineEdit.EchoMode.Password
            )

            if not ok or not api_key:
                self.log_status("LLM analysis cancelled - no API key provided")
                return

        # Start LLM analysis worker
        self.llm_worker = LLMAnalysisWorker(
            folder_structure=self.folder_structure,
            scanned_files=self.scanned_files,
            api_key=api_key,
            model="Claude-Sonnet-4.5"
        )

        # Connect signals
        self.llm_worker.progress.connect(self._on_llm_progress)
        self.llm_worker.finished.connect(self._on_llm_finished)
        self.llm_worker.error.connect(self._on_llm_error)

        # Start
        self.llm_worker.start()

        self.log_status("LLM analysis in progress...")

    def _on_llm_progress(self, message: str):
        """Handle LLM analysis progress updates."""
        self.llm_output.append(f"• {message}")
        self.log_status(message)

    def _on_llm_finished(self, analysis_result: dict):
        """Handle LLM analysis completion."""
        self.llm_analysis = analysis_result
        self.detected_media = analysis_result.get('detected_media', [])
        self.reorganization_plan = analysis_result.get('reorganization_plan', {})

        # Display results in GUI
        self.llm_output.clear()
        self.llm_output.append("=" * 80)
        self.llm_output.append("LLM ANALYSIS COMPLETE")
        self.llm_output.append("=" * 80 + "\n")

        # Show detected media
        self.llm_output.append(f"DETECTED MEDIA ({len(self.detected_media)} items):")
        self.llm_output.append("-" * 80)
        for media in self.detected_media[:10]:  # Show first 10
            media_type = media.get('type', 'unknown').upper()
            title = media.get('title', 'Unknown')
            year = media.get('year_estimate', '?')
            confidence = media.get('confidence', 'unknown')
            self.llm_output.append(f"  [{media_type}] {title} ({year}) - Confidence: {confidence}")
            if media.get('notes'):
                self.llm_output.append(f"           Notes: {media['notes']}")

        if len(self.detected_media) > 10:
            self.llm_output.append(f"  ... and {len(self.detected_media) - 10} more")

        self.llm_output.append("")

        # Show reorganization summary
        plan_summary = self.reorganization_plan.get('summary', 'No summary provided')
        self.llm_output.append("REORGANIZATION PLAN:")
        self.llm_output.append("-" * 80)
        self.llm_output.append(plan_summary)
        self.llm_output.append("")

        # Show folder changes (first 10)
        folder_changes = self.reorganization_plan.get('folder_changes', [])
        if folder_changes:
            self.llm_output.append(f"PROPOSED CHANGES ({len(folder_changes)} folders):")
            self.llm_output.append("-" * 80)
            for change in folder_changes[:10]:
                self.llm_output.append(f"  {change.get('action', 'unknown').upper()}: {change.get('current_path', 'unknown')}")
                self.llm_output.append(f"    → {change.get('proposed_path', 'unknown')}")
                self.llm_output.append(f"    Reason: {change.get('reason', 'No reason provided')}")
                self.llm_output.append("")

            if len(folder_changes) > 10:
                self.llm_output.append(f"  ... and {len(folder_changes) - 10} more changes")

        # Show multi-part episodes
        multi_part = analysis_result.get('multi_part_episodes', [])
        if multi_part:
            self.llm_output.append("")
            self.llm_output.append(f"MULTI-PART EPISODES ({len(multi_part)}):")
            self.llm_output.append("-" * 80)
            for episode in multi_part:
                show = episode.get('show_title', 'Unknown')
                season = episode.get('season_number', '?')
                episodes = episode.get('episode_numbers', [])
                title = episode.get('combined_episode_title', 'Unknown')
                self.llm_output.append(f"  {show} - S{season:02d}E{episodes} - {title}")
                self.llm_output.append(f"    Reason: {episode.get('reason', 'No reason provided')}")

        # Show reasoning
        self.llm_output.append("")
        self.llm_output.append("LLM REASONING:")
        self.llm_output.append("-" * 80)
        reasoning = analysis_result.get('reasoning', 'No reasoning provided')
        self.llm_output.append(reasoning)

        self.llm_output.append("")
        self.llm_output.append("=" * 80)

        # Save to file
        import json
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = Path(f"data/llm_analysis_{timestamp}.json")
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_result, f, indent=2, ensure_ascii=False)

        self.llm_output.append(f"\nAnalysis saved to: {output_file}")

        self.log_status(f"LLM analysis complete: {len(self.detected_media)} media items detected")

    def _on_llm_error(self, error_message: str):
        """Handle LLM analysis errors."""
        self.llm_output.append(f"\nERROR: {error_message}")

        QMessageBox.critical(
            self,
            "LLM Analysis Error",
            f"An error occurred during LLM analysis:\n\n{error_message}\n\n"
            f"Check that your Poe API key is valid and you have internet connectivity."
        )

        self.log_status(f"LLM analysis failed: {error_message}")

    # =========================================================================
    # WORKFLOW STEP 4: METADATA DATABASE
    # =========================================================================
    
    def step_4_metadata(self):
        """Step 4: Build canonical metadata database."""
        # Check prerequisites
        if not self.detected_media:
            QMessageBox.warning(
                self,
                "No Detected Media",
                "Please complete Step 3 (LLM Proposal) first.\n\n"
                "The LLM must detect movies and TV shows before we can query metadata."
            )
            return
        
        # Check for TMDB API key
        import os
        tmdb_key = os.getenv('TMDB_API_KEY')
        omdb_key = os.getenv('OMDB_API_KEY')
        
        if not tmdb_key and not omdb_key:
            # Prompt user for API key
            key, ok = QInputDialog.getText(
                self,
                "TMDB API Key Required",
                "No TMDB_API_KEY or OMDB_API_KEY environment variable found.\n\n"
                "Enter your TMDB API key (get free key at https://www.themoviedb.org/settings/api):",
                QLineEdit.EchoMode.Normal
            )
            
            if not ok or not key:
                return
            
            tmdb_key = key
        
        self.log_status(f"Step 4: Building canonical metadata database for {len(self.detected_media)} items...")
        
        # Clear previous output
        self.metadata_output.clear()
        self.metadata_output.append("🔍 Metadata Lookup Started\n")
        self.metadata_output.append(f"Detected media: {len(self.detected_media)} items\n")
        self.metadata_output.append("Querying TMDB/OMDb APIs...\n")
        self.metadata_output.append("(This may take 1-2 minutes with rate limiting)\n")
        self.metadata_progress.setValue(0)
        
        # Prevent starting another lookup while one is running
        if self.metadata_worker and self.metadata_worker.isRunning():
            QMessageBox.warning(
                self,
                "Lookup In Progress",
                "Metadata lookup is already running. Please wait for it to complete."
            )
            return
        
        # Create and start metadata lookup worker
        self.metadata_worker = MetadataLookupWorker(
            detected_media=self.detected_media,
            scanned_files=self.scanned_files,
            tmdb_api_key=tmdb_key,
            omdb_api_key=omdb_key
        )
        
        # Connect signals
        self.metadata_worker.progress.connect(self._on_metadata_progress)
        self.metadata_worker.finished.connect(self._on_metadata_finished)
        self.metadata_worker.error.connect(self._on_metadata_error)
        
        # Start background processing
        self.metadata_worker.start()
    
    def _on_metadata_progress(self, message: str, current: int, total: int):
        """Handle metadata lookup progress updates."""
        self.metadata_output.append(f"[{current}/{total}] {message}")
        
        # Update progress bar
        if total > 0:
            progress_pct = int((current / total) * 100)
            self.metadata_progress.setValue(progress_pct)
        
        # Auto-scroll to bottom
        cursor = self.metadata_output.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.metadata_output.setTextCursor(cursor)
    
    def _on_metadata_finished(self, canonical_db: dict):
        """Handle successful metadata lookup completion."""
        from datetime import datetime
        
        # Store results
        self.canonical_database = canonical_db
        self.multi_part_episodes = canonical_db.get('multi_part_episodes', [])
        
        # Update progress bar
        self.metadata_progress.setValue(100)
        
        # Display results summary
        self.metadata_output.append("\n" + "="*60)
        self.metadata_output.append("✅ METADATA LOOKUP COMPLETE")
        self.metadata_output.append("="*60 + "\n")
        
        self.metadata_output.append(f"📽️  Movies: {len(canonical_db['movies'])}")
        for movie in canonical_db['movies']:
            title = movie.get('title', 'Unknown')
            year = movie.get('year', '????')
            tmdb_id = movie.get('tmdb_id', 'N/A')
            self.metadata_output.append(f"   • {title} ({year}) [TMDB: {tmdb_id}]")
        
        self.metadata_output.append(f"\n📺 TV Shows: {len(canonical_db['tv_shows'])}")
        for show in canonical_db['tv_shows']:
            title = show.get('title', 'Unknown')
            year = show.get('year', '????')
            tmdb_id = show.get('tmdb_id', 'N/A')
            num_seasons = show.get('number_of_seasons', 0)
            num_episodes = show.get('number_of_episodes', 0)
            self.metadata_output.append(
                f"   • {title} ({year}) - {num_seasons} seasons, "
                f"{num_episodes} episodes [TMDB: {tmdb_id}]"
            )
        
        if canonical_db['multi_part_episodes']:
            self.metadata_output.append(f"\n⚠️  Multi-Part Episodes: {len(canonical_db['multi_part_episodes'])}")
            self.metadata_output.append("   (These will require NFO files for proper Jellyfin recognition)")
            for mp_ep in canonical_db['multi_part_episodes'][:5]:  # Show first 5
                self.metadata_output.append(
                    f"   • {mp_ep['show_title']} - S{mp_ep['season_number']:02d}E{mp_ep['episode_number']:02d} - {mp_ep['episode_name']}"
                )
            if len(canonical_db['multi_part_episodes']) > 5:
                self.metadata_output.append(f"   ... and {len(canonical_db['multi_part_episodes']) - 5} more")
        
        if canonical_db['lookup_failures']:
            self.metadata_output.append(f"\n❌ Lookup Failures: {len(canonical_db['lookup_failures'])}")
            for failure in canonical_db['lookup_failures']:
                self.metadata_output.append(f"   • {failure.get('title', 'Unknown')} ({failure.get('type', '?')})")
        
        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = Path(f"data/canonical_metadata_{timestamp}.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        import json
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(canonical_db, f, indent=2, ensure_ascii=False)
        
        self.metadata_output.append(f"\n💾 Canonical database saved to: {output_path}")
        self.metadata_output.append("\n✅ Ready for Step 5: Review Actions")
        
        self.log_status(f"Metadata database complete: {len(canonical_db['movies'])} movies, {len(canonical_db['tv_shows'])} TV shows")
    
    def _on_metadata_error(self, error_message: str):
        """Handle metadata lookup errors."""
        self.metadata_output.append("\n" + "="*60)
        self.metadata_output.append("❌ METADATA LOOKUP FAILED")
        self.metadata_output.append("="*60)
        self.metadata_output.append(f"\nError: {error_message}")
        self.metadata_output.append("\nPlease check:")
        self.metadata_output.append("1. TMDB API key is correct")
        self.metadata_output.append("2. Internet connection is active")
        self.metadata_output.append("3. API services are not down")
        
        self.metadata_progress.setValue(0)
        self.log_status(f"Metadata lookup failed: {error_message}")
        
        QMessageBox.critical(
            self,
            "Metadata Lookup Failed",
            f"An error occurred during metadata lookup:\n\n{error_message}\n\n"
            "Check the output window for details."
        )

    # =========================================================================
    # WORKFLOW STEP 5: REVIEW ACTIONS
    # =========================================================================
    
    def step_5_review(self):
        """Step 5: Generate and display the action plan for review."""
        self.log_status("Step 5: Generating action plan...")

        # --- Prerequisite Checks ---
        if not self.scanned_files:
            QMessageBox.warning(self, "Missing Data", "Please complete Step 1 (Scan) first.")
            return
        if not self.llm_analysis:
            QMessageBox.warning(self, "Missing Data", "Please complete Step 3 (LLM Proposal) first.")
            return
        if not self.canonical_database:
            QMessageBox.warning(self, "Missing Data", "Please complete Step 4 (Build Metadata DB) first.")
            return
            
        # --- Worker Execution ---
        if self.action_plan_worker and self.action_plan_worker.isRunning():
            QMessageBox.warning(self, "In Progress", "Action plan generation is already in progress.")
            return

        self.log_status("Generating action plan in background...")
        self.tabs.setCurrentIndex(2) # Switch to review tab
        self.action_table.setRowCount(0) # Clear table

        self.action_plan_worker = ActionPlanWorker(
            scanned_files=self.scanned_files,
            llm_analysis=self.llm_analysis,
            canonical_database=self.canonical_database,
            app_config=self.app_config
        )
        self.action_plan_worker.finished.connect(self._on_action_plan_finished)
        self.action_plan_worker.error.connect(self._on_action_plan_error)
        self.action_plan_worker.start()

    def _on_action_plan_finished(self, action_plan: List[ProposedOperation]):
        """Handle successful action plan generation."""
        self.log_status(f"Action plan generated with {len(action_plan)} operations.")
        self.action_plan = action_plan
        self.action_table.setRowCount(len(action_plan))

        confidence_colors = {
            Confidence.HIGH: QColor(200, 255, 200),    # Green
            Confidence.MEDIUM: QColor(255, 255, 200), # Yellow
            Confidence.LOW: QColor(255, 200, 200),      # Red
            Confidence.MANUAL: QColor(255, 220, 180),   # Orange
            Confidence.NONE: QColor(240, 240, 240),     # Grey
        }

        for row, op in enumerate(action_plan):
            color = confidence_colors.get(op.confidence, QColor(255, 255, 255))

            # --- Create Items ---
            source_item = QTableWidgetItem(str(op.source_path.name))
            source_item.setToolTip(str(op.source_path))
            
            dest_text = str(op.destination_path) if op.destination_path else "N/A"
            dest_item = QTableWidgetItem(dest_text)
            
            action_item = QTableWidgetItem(op.action_type.name)
            confidence_item = QTableWidgetItem(op.confidence.name)
            jellyfin_item = QTableWidgetItem(op.jellyfin_status)
            notes_item = QTableWidgetItem(op.notes)

            # --- Apply Color and Set Items ---
            for col, item in enumerate([source_item, dest_item, action_item, confidence_item, jellyfin_item, notes_item]):
                item.setBackground(color)
                # Make items non-editable for now, except for notes
                if col != 5:
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.action_table.setItem(row, col, item)

            # --- Add 'Approve' Checkbox ---
            checkbox_widget = QWidget()
            checkbox_layout = QHBoxLayout(checkbox_widget)
            checkbox = QCheckBox()
            checkbox_layout.addWidget(checkbox)
            checkbox_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            checkbox_layout.setContentsMargins(0, 0, 0, 0)
            
            # Set initial state based on confidence
            if op.confidence == Confidence.HIGH:
                checkbox.setChecked(True)
            
            self.action_table.setCellWidget(row, 6, checkbox_widget)

        self.action_table.resizeRowsToContents()
        self.log_status("Action plan loaded. Review and approve changes.")

    def _on_action_plan_error(self, error_message: str):
        """Handle action plan generation errors."""
        self.log_status(f"Action plan generation failed: {error_message}")
        QMessageBox.critical(
            self,
            "Action Plan Error",
            f"An error occurred while generating the action plan:\n\n{error_message}"
        )

    # =========================================================================
    # WORKFLOW STEP 6: SNAPSHOT & TRANSACTION LOG
    # =========================================================================
    
    def step_6_snapshot(self):
        """Step 6: Create transaction log for rollback."""
        self.log_status("Step 6: Creating transaction snapshot...")
        
        # Switch to execute tab
        self.tabs.setCurrentIndex(3)
        
        self.snapshot_info.setPlainText(
            "📸 Transaction Snapshot Created\n\n"
            "SQLite database: transaction_log.db\n"
            "Table: transactions\n\n"
            "Columns:\n"
            "- transaction_id (PRIMARY KEY)\n"
            "- timestamp\n"
            "- source_path\n"
            "- destination_path\n"
            "- md5_before\n"
            "- md5_after\n"
            "- operation_type (move/copy/delete)\n"
            "- status (pending/completed/failed)\n\n"
            "Enables complete rollback capability.\n\n"
            "TODO: Implement SQLite transaction logging"
        )
        
        self.log_status("Transaction snapshot created (placeholder).")

    # =========================================================================
    # WORKFLOW STEP 7: EXECUTE
    # =========================================================================
    
    def step_7_execute(self):
        """Step 7: Execute file operations."""
        self.log_status("Step 7: Executing file operations...")
        
        reply = QMessageBox.question(
            self,
            "Execute Operations?",
            "⚠️ This will perform file moves/renames.\n\n"
            "Transaction log will enable rollback if needed.\n\n"
            "Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.No:
            self.log_status("Execution cancelled.")
            return
        
        # Switch to execute tab
        self.tabs.setCurrentIndex(3)
        
        self.execute_log.setPlainText(
            "🔄 Executing File Operations (Placeholder)\n\n"
            "For each approved action:\n"
            "1. Calculate MD5 hash of source file\n"
            "2. Create destination directory\n"
            "3. Move file to destination\n"
            "4. Verify MD5 hash matches\n"
            "5. Log transaction in SQLite\n"
            "6. Update progress bar\n\n"
            "Example:\n"
            "✓ Moved: Breaking Bad S01E01.mkv → TV/Breaking Bad (2008)/Season 01/...\n"
            "✓ Verified: MD5 match confirmed\n\n"
            "TODO: Implement file operations with shutil.move() and MD5 verification"
        )
        
        self.execute_progress.setValue(0)
        self.log_status("File operations completed (placeholder).")

    # =========================================================================
    # WORKFLOW STEP 8: SUBTITLE COVERAGE
    # =========================================================================
    
    def step_8_subtitle_check(self):
        """Step 8: Check for missing English subtitles."""
        self.log_status("Step 8: Checking subtitle coverage...")
        
        # Switch to subtitles tab
        self.tabs.setCurrentIndex(4)
        
        self.subtitle_check_list.clear()
        self.subtitle_check_list.addItems([
            "Movie1.mkv - No English subtitles found",
            "TVShow.S01E05.mkv - No English subtitles found",
            "Movie2.mkv - Has embedded English subtitles ✓",
            "TVShow.S01E06.mkv - Has external .srt file ✓",
        ])
        
        self.log_status("Subtitle coverage check complete (placeholder).")

    # =========================================================================
    # WORKFLOW STEP 9: SUBTITLE DOWNLOAD
    # =========================================================================
    
    def step_9_subtitle_download(self):
        """Step 9: Download missing subtitles."""
        self.log_status("Step 9: Downloading subtitles...")
        
        # Switch to subtitles tab
        self.tabs.setCurrentIndex(4)
        
        self.subtitle_download_log.setPlainText(
            "📥 Downloading Subtitles (Placeholder)\n\n"
            "Using subliminal library to download from:\n"
            "- OpenSubtitles\n"
            "- Podnapisi\n"
            "- TVsubtitles\n"
            "- Addic7ed\n\n"
            "Process:\n"
            "1. Hash-based matching (most accurate)\n"
            "2. Fallback to filename fuzzy matching\n"
            "3. Download both regular and forced subtitles\n"
            "4. Save alongside video files\n\n"
            "Example:\n"
            "✓ Movie1.mkv → Downloaded from OpenSubtitles\n"
            "✓ TVShow.S01E05.mkv → Downloaded from Podnapisi\n\n"
            "TODO: Integrate subliminal library"
        )
        
        self.subtitle_download_progress.setValue(0)
        self.log_status("Subtitle download complete (placeholder).")
        self.log_status("✅ All 9 workflow steps complete!")

    def open_jellyfin_settings(self):
        """Open Jellyfin settings dialog (Phase 20)."""
        dialog = JellyfinSettingsDialog(self)
        if dialog.exec():
            # Settings were saved
            config = dialog.get_config()

            # Reload config manager
            self.jellyfin_config = JellyfinConfigManager()

            # Initialize Jellyfin client if enabled
            if config['enabled'] and config['server_url'] and config['api_key']:
                self.jellyfin_client = JellyfinClient(
                    server_url=config['server_url'],
                    api_key=config['api_key']
                )
                self.log_status(f"Jellyfin integration enabled: {config['server_url']}")
            else:
                self.jellyfin_client = None
                self.log_status("Jellyfin integration disabled")


def main():
    """Main application entry point."""
    app = QApplication(sys.argv)
    
    # Set application-wide font
    app.setFont(QFont("Arial", 9))
    
    window = JellyRancherClean()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
