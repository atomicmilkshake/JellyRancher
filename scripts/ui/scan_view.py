#!/usr/bin/env python3
"""
Scan View - Folder selection and file scanning interface

Implements Point 1 from plan.md: Master File Inventory
Allows users to select folders, configure scan options, and view results.
"""

import logging
from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime
from collections import defaultdict

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QProgressBar, QFileDialog,
    QMessageBox, QGroupBox, QCheckBox, QHeaderView, QDialog,
    QScrollArea, QLineEdit
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

from scripts.core.file_scanner import FileScanner, FileRecord, ScanStatistics
from scripts.core.project_manager import ProjectManager, Project
from scripts.core.app_config import AppConfigManager
from scripts.core.inventory_repository import InventoryRepository
from scripts.core.jellyfin_client import JellyfinClient
from scripts.core.jellyfin_config import JellyfinConfigManager
from scripts.core.workers import MultiScanWorker
import sqlite3
import json

logger = logging.getLogger(__name__)


class FolderContentSelectionDialog(QDialog):
    """
    Dialog for selecting which subfolders and files to include in scan.
    
    Shows all immediate contents of a selected folder with checkboxes,
    allowing user to exclude specific items before adding to scan list.
    """
    
    def __init__(self, folder_path: Path, parent=None):
        try:
            super().__init__(parent)
            self.folder_path = folder_path
            self.checkboxes = {}  # path -> QCheckBox
            
            self.setWindowTitle(f"Select contents to include in scan")
            self.setMinimumSize(600, 400)
            
            # Apply comprehensive dialog styling with white background for list
            dialog_stylesheet = """
                /* Dialog container */
                FolderContentSelectionDialog {
                    background-color: #ecf0f1;
                }
                
                /* Labels */
                QLabel {
                    color: #2c3e50;
                    background-color: transparent;
                }
                
                /* Scroll area - WHITE background for item list */
                QScrollArea {
                    background-color: white;
                    border: 1px solid #bdc3c7;
                }
                
                QScrollArea QWidget {
                    background-color: white;
                }
                
                /* Checkboxes in the scroll area */
                /* Removed custom QCheckBox styling to ensure native OS rendering */
                
                /* Buttons */
                QPushButton {
                    background-color: #1f6fb2;
                    color: white;
                    border: 1px solid #155a9a;
                    padding: 6px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                
                QPushButton:hover {
                    background-color: #155a9a;
                }
                
                QPushButton:pressed {
                    background-color: #0f3d5a;
                }
                
                /* Scrollbar styling */
                QScrollBar:vertical {
                    background-color: white;
                    width: 12px;
                }
                
                QScrollBar::handle:vertical {
                    background-color: #bdc3c7;
                    border-radius: 6px;
                }
                
                QScrollBar::handle:vertical:hover {
                    background-color: #95a5a6;
                }
            """
            self.setStyleSheet(dialog_stylesheet)
            
            self.init_ui()
        except Exception as e:
            logger.error(f"Failed to initialize folder content selection dialog for {folder_path}: {e}", exc_info=True)
            QMessageBox.critical(parent, "Initialization Error", f"Failed to open folder selection dialog: {str(e)}")
            raise
    
    def init_ui(self):
        """Initialize the dialog UI."""
        try:
            layout = QVBoxLayout(self)
            
            # Header
            header = QLabel(f"<b>Folder:</b> {self.folder_path}")
            header.setWordWrap(True)
            layout.addWidget(header)
            
            instruction = QLabel(
                "Uncheck any subfolders or files you want to exclude from the scan:"
            )
            layout.addWidget(instruction)
            
            # Scroll area for checkboxes
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll_widget = QWidget()
            scroll_layout = QVBoxLayout(scroll_widget)
            
            try:
                # Get all immediate contents (subfolders and files)
                contents = sorted(
                    self.folder_path.iterdir(), 
                    key=lambda p: (not p.is_dir(), p.name.lower())
                )
                
                if not contents:
                    no_content_label = QLabel("(Empty folder)")
                    scroll_layout.addWidget(no_content_label)
                else:
                    for item_path in contents:
                        checkbox = QCheckBox()
                        checkbox.setChecked(True)  # Default: include everything
                        
                        # Format label with icon indicator
                        if item_path.is_dir():
                            label_text = f"📁 {item_path.name}/"
                        else:
                            try:
                                size_mb = item_path.stat().st_size / (1024 * 1024)
                                label_text = f"📄 {item_path.name} ({size_mb:.1f} MB)"
                            except OSError as e:
                                logger.warning(f"Could not get file size for {item_path}: {e}")
                                label_text = f"📄 {item_path.name} (size unknown)"
                        
                        checkbox.setText(label_text)
                        scroll_layout.addWidget(checkbox)
                        self.checkboxes[item_path] = checkbox
                    
            except (OSError, PermissionError) as e:
                logger.error(f"Failed to read folder contents for {self.folder_path}: {e}", exc_info=True)
                error_label = QLabel(f"Error reading folder contents: {e}")
                scroll_layout.addWidget(error_label)
            except Exception as e:
                logger.error(f"Unexpected error reading folder contents for {self.folder_path}: {e}", exc_info=True)
                error_label = QLabel(f"Unexpected error reading folder contents: {e}")
                scroll_layout.addWidget(error_label)
            
            scroll_layout.addStretch()
            scroll.setWidget(scroll_widget)
            layout.addWidget(scroll)
            
            # Bulk selection buttons
            button_row = QHBoxLayout()
            
            btn_select_all = QPushButton("Select All")
            btn_select_all.clicked.connect(self._select_all)
            button_row.addWidget(btn_select_all)
            
            btn_select_none = QPushButton("Select None")
            btn_select_none.clicked.connect(self._select_none)
            button_row.addWidget(btn_select_none)
            
            button_row.addStretch()
            layout.addLayout(button_row)
            
            # Dialog buttons
            dialog_buttons = QHBoxLayout()
            
            btn_ok = QPushButton("OK")
            btn_ok.clicked.connect(self.accept)
            btn_ok.setDefault(True)
            dialog_buttons.addWidget(btn_ok)
            
            btn_cancel = QPushButton("Cancel")
            btn_cancel.clicked.connect(self.reject)
            dialog_buttons.addWidget(btn_cancel)
            
            layout.addLayout(dialog_buttons)
        except Exception as e:
            logger.error(f"Failed to initialize UI for folder content selection dialog: {e}", exc_info=True)
            QMessageBox.critical(self, "UI Error", f"Failed to initialize dialog interface: {str(e)}")
            raise
    
    def _select_all(self):
        """Check all checkboxes."""
        try:
            for checkbox in self.checkboxes.values():
                checkbox.setChecked(True)
        except Exception as e:
            logger.error(f"Failed to select all checkboxes: {e}", exc_info=True)
    
    def _select_none(self):
        """Uncheck all checkboxes."""
        try:
            for checkbox in self.checkboxes.values():
                checkbox.setChecked(False)
        except Exception as e:
            logger.error(f"Failed to select none checkboxes: {e}", exc_info=True)
    
    def get_excluded_paths(self) -> List[Path]:
        """
        Get list of paths that were unchecked (excluded).
        
        Returns:
            List of Path objects that should be excluded from scan
        """
        try:
            excluded = []
            for path, checkbox in self.checkboxes.items():
                if not checkbox.isChecked():
                    excluded.append(path)
            return excluded
        except Exception as e:
            logger.error(f"Failed to get excluded paths: {e}", exc_info=True)
            return []


class ScanView(QWidget):
    """
    Scan View - Folder selection and file scanning interface.
    
    Features:
    - Add/remove folders with content selection
    - Configure scan options (MD5, deep scan)
    - View scan results in sortable table
    - Search and filter results
    - Export results
    """
    
    # Signals
    scan_completed = pyqtSignal(int)  # scan_session_id
    results_ready = pyqtSignal(int)  # scan_session_id for results view
    
    def __init__(self, project: Project, project_manager: ProjectManager, parent=None):
        try:
            super().__init__(parent)
            
            self.project = project
            self.project_manager = project_manager
            self.app_config = AppConfigManager()
            self.inventory_repo = InventoryRepository()
            self.jellyfin_client = self._create_jellyfin_client()
            
            self.selected_folders: List[Path] = []
            self.excluded_paths: List[Path] = []
            self.scan_statistics: Optional[ScanStatistics] = None
            self.current_scan_session_id: Optional[int] = None
            self.inventory_session_ids: List[int] = []
            self.scan_start_time: Optional[datetime] = None
            
            self._init_ui()
            self.setAcceptDrops(True)  # Enable drag-and-drop
            logger.info(f"ScanView initialized for project: {project.name}")
        except Exception as e:
            logger.error(f"Failed to initialize ScanView for project {project.name}: {e}", exc_info=True)
            QMessageBox.critical(parent, "Initialization Error", f"Failed to initialize scan view: {str(e)}")
            raise
    
    def _create_jellyfin_client(self) -> Optional[JellyfinClient]:
        """Create a Jellyfin client if configuration is available."""
        try:
            config_mgr = JellyfinConfigManager()
            config = config_mgr.load_config()
            if (
                config
                and config.get("enabled")
                and config.get("server_url")
                and config.get("api_key")
            ):
                client = JellyfinClient(
                    server_url=config["server_url"],
                    api_key=config["api_key"],
                )
                if client.test_connection():
                    logger.info("Jellyfin client initialized for ScanView")
                    return client
                logger.warning("Jellyfin connection test failed; disabling integration")
        except Exception as exc:
            logger.warning("Unable to initialize Jellyfin client: %s", exc)
        return None
    
    def _init_ui(self):
        """Initialize the UI."""
        try:
            layout = QVBoxLayout()
            layout.setSpacing(10)
            layout.setContentsMargins(10, 10, 10, 10)
            
            # Title
            title = QLabel("Scan Folders")
            title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
            title.setStyleSheet("color: #2c3e50; padding: 10px;")
            layout.addWidget(title)
            
            # Folder selection section
            folder_group = self._create_folder_selection_section()
            layout.addWidget(folder_group)
            
            # Scan options section
            options_group = self._create_scan_options_section()
            layout.addWidget(options_group)
            
            # Progress section
            progress_group = self._create_progress_section()
            layout.addWidget(progress_group)
            
            self.setLayout(layout)
        except Exception as e:
            logger.error(f"Failed to initialize ScanView UI: {e}", exc_info=True)
            QMessageBox.critical(self, "UI Error", f"Failed to initialize scan interface: {str(e)}")
            raise
    
    def _create_folder_selection_section(self) -> QGroupBox:
        """Create the folder selection section."""
        try:
            group = QGroupBox("Selected Folders")
            layout = QVBoxLayout()
            
            # Folder table
            self.folder_table = QTableWidget()
            self.folder_table.setMinimumHeight(150)  # Ensure at least a few rows are visible
            self.folder_table.setColumnCount(3)
            self.folder_table.setHorizontalHeaderLabels(["Folder Path", "Included Items", "Excluded Items"])
            self.folder_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
            self.folder_table.setColumnWidth(0, 400)
            self.folder_table.setColumnWidth(1, 100)
            self.folder_table.setColumnWidth(2, 100)
            self.folder_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
            layout.addWidget(self.folder_table)
            
            # Buttons
            button_layout = QHBoxLayout()
            
            self.btn_add_folder = QPushButton("+ Add Folder")
            self.btn_add_folder.clicked.connect(self._add_folder)
            button_layout.addWidget(self.btn_add_folder)
            
            self.btn_remove_folder = QPushButton("- Remove Selected")
            self.btn_remove_folder.clicked.connect(self._remove_folder)
            button_layout.addWidget(self.btn_remove_folder)

            self.btn_clear_folders = QPushButton("Clear All")
            self.btn_clear_folders.clicked.connect(self._clear_folders)
            button_layout.addWidget(self.btn_clear_folders)
            
            button_layout.addStretch()
            layout.addLayout(button_layout)
            
            group.setLayout(layout)
            return group
        except Exception as e:
            logger.error(f"Failed to create folder selection section: {e}", exc_info=True)
            raise RuntimeError(f"Failed to create folder selection UI: {e}") from e
    
    def _create_scan_options_section(self) -> QGroupBox:
        """Create the scan options section."""
        try:
            group = QGroupBox("Scan Options")
            layout = QVBoxLayout()
            
            self.chk_md5 = QCheckBox("Calculate MD5 hashes (slower, enables duplicate detection)")
            self.chk_md5.setChecked(self.app_config.is_md5_calculate_during_scan())
            layout.addWidget(self.chk_md5)
            
            self.chk_metadata = QCheckBox("Extract metadata from filenames")
            self.chk_metadata.setChecked(True)
            layout.addWidget(self.chk_metadata)
            
            # Estimated time label
            self.lbl_estimate = QLabel("Estimated time: ~30 seconds for 1,000 files")
            self.lbl_estimate.setStyleSheet("color: #566573; font-style: italic;")
            layout.addWidget(self.lbl_estimate)
            
            group.setLayout(layout)
            return group
        except Exception as e:
            logger.error(f"Failed to create scan options section: {e}", exc_info=True)
            raise RuntimeError(f"Failed to create scan options UI: {e}") from e
    
    def _create_progress_section(self) -> QGroupBox:
        """Create the progress section."""
        try:
            group = QGroupBox("Scan Progress")
            layout = QVBoxLayout()
            
            self.progress_bar = QProgressBar()
            self.progress_bar.setMinimum(0)
            self.progress_bar.setMaximum(100)
            self.progress_bar.setValue(0)
            layout.addWidget(self.progress_bar)
            
            self.lbl_status = QLabel("Ready to scan")
            layout.addWidget(self.lbl_status)
            
            # Scan button
            self.btn_scan = QPushButton("▶ Start Scan")
            self.btn_scan.clicked.connect(self._start_scan)
            self.btn_scan.setMinimumHeight(40)
            self.btn_scan.setStyleSheet("""
                QPushButton {
                    background-color: #1f6fb2;
                    color: white;
                    font-size: 14px;
                    font-weight: bold;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #1b63a0;
                }
                QPushButton:disabled {
                    background-color: #bdc3c7;
                    color: #3b4650;
                }
            """)
            layout.addWidget(self.btn_scan)
            
            group.setLayout(layout)
            return group
        except Exception as e:
            logger.error(f"Failed to create progress section: {e}", exc_info=True)
            raise RuntimeError(f"Failed to create progress UI: {e}") from e

    def _update_overview(self):
        """Generate hierarchical overview and duplicate summary."""
        try:
            if not self.folder_structure:
                QMessageBox.information(
                    self,
                    "No Data",
                    "No folder structure available. Run a scan before generating the overview.",
                )
                return

            folder_to_files = defaultdict(list)
            for record in self.scanned_files:
                folder_to_files[record.parent_folder].append(record)

            self.overview_tree.clear()
            for folder_path, data in sorted(self.folder_structure.items()):
                path_str = str(folder_path)
                size_mb = data["total_size"] / (1024 * 1024)
                files_in_folder = folder_to_files.get(folder_path, [])
                jellyfin_matches = sum(
                    1 for f in files_in_folder if getattr(f, "jellyfin_matched", False)
                )
                jellyfin_match_str = (
                    str(jellyfin_matches) if self.jellyfin_client else "N/A"
                )

                sorted_types = sorted(data["file_types"].items(), key=lambda x: x[1], reverse=True)
                details = ", ".join([f"{ext}: {count}" for ext, count in sorted_types[:4]])

                item = QTreeWidgetItem(
                    [
                        path_str,
                        str(data["file_count"]),
                        f"{size_mb:.1f}",
                        jellyfin_match_str,
                        details,
                    ]
                )

                if self.jellyfin_client:
                    if jellyfin_matches == data["file_count"]:
                        item.setBackground(3, QColor(200, 255, 200))
                    elif jellyfin_matches > 0:
                        item.setBackground(3, QColor(255, 255, 200))

                self.overview_tree.addTopLevelItem(item)

            # Duplicate detection
            self.duplicate_tree.clear()
            self.duplicate_groups = {}
            md5_map = defaultdict(list)
            for record in self.scanned_files:
                md5_value = getattr(record, "md5_hash", None)
                if md5_value:
                    md5_map[md5_value].append(record)

            for md5_value, records in md5_map.items():
                if len(records) < 2:
                    continue
                self.duplicate_groups[md5_value] = records

            if not self.duplicate_groups:
                self.duplicate_summary_label.setText("MD5 duplicate groups: none detected.")
            else:
                total_files = sum(len(v) for v in self.duplicate_groups.values())
                self.duplicate_summary_label.setText(
                    f"MD5 duplicate groups: {len(self.duplicate_groups)} groups, {total_files} files."
                )
        except Exception as e:
            logger.error(f"Failed to update overview: {e}", exc_info=True)
            QMessageBox.critical(self, "Overview Error", f"Failed to generate overview: {str(e)}")

            for md5_value, records in sorted(
                self.duplicate_groups.items(), key=lambda x: len(x[1]), reverse=True
            ):
                example_paths = [str(rec.absolute_path) for rec in records[:3]]
                item = QTreeWidgetItem(
                    [
                        md5_value,
                        str(len(records)),
                        "; ".join(example_paths),
                    ]
                )
                self.duplicate_tree.addTopLevelItem(item)
    
    def _add_folder(self):
        """Add a folder to scan list."""
        try:
            folder = QFileDialog.getExistingDirectory(
                self,
                "Select Folder to Scan",
                str(Path.home())
            )
            
            if not folder:
                return
            
            folder_path = Path(folder)
            
            # Show content selection dialog
            dialog = FolderContentSelectionDialog(folder_path, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                excluded = dialog.get_excluded_paths()
                
                # Add to selected folders
                self.selected_folders.append(folder_path)
                self.excluded_paths.extend(excluded)
                self._append_folder_row(folder_path, excluded)
                logger.info(f"Added folder: {folder_path} ({len(excluded)} items excluded)")
        except Exception as e:
            logger.error(f"Failed to add folder: {e}", exc_info=True)
            QMessageBox.critical(self, "Add Folder Error", f"Failed to add folder: {str(e)}")
    
    def _remove_folder(self):
        """Remove selected folder from scan list."""
        try:
            current_row = self.folder_table.currentRow()
            if current_row >= 0:
                folder_path = Path(self.folder_table.item(current_row, 0).text())
                self.selected_folders.remove(folder_path)
                self.excluded_paths = [
                    p for p in self.excluded_paths if not (p.parent == folder_path or p == folder_path)
                ]
                self.folder_table.removeRow(current_row)
                logger.info(f"Removed folder: {folder_path}")
        except Exception as e:
            logger.error(f"Failed to remove folder: {e}", exc_info=True)
            QMessageBox.critical(self, "Remove Folder Error", f"Failed to remove folder: {str(e)}")

    def _clear_folders(self):
        """Clear all selected folders and exclusions."""
        try:
            if not self.selected_folders:
                return

            reply = QMessageBox.question(
                self,
                "Clear All Folders",
                f"Remove all {len(self.selected_folders)} folder(s) from the list?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )

            if reply != QMessageBox.StandardButton.Yes:
                return

            self.selected_folders.clear()
            self.excluded_paths.clear()
            self.folder_table.setRowCount(0)
            logger.info("Cleared all selected folders")
        except Exception as e:
            logger.error(f"Failed to clear folders: {e}", exc_info=True)
            QMessageBox.critical(self, "Clear Folders Error", f"Failed to clear folders: {str(e)}")
    
    def _append_folder_row(self, folder_path: Path, excluded: List[Path]):
        """Append folder information to the table."""
        try:
            row = self.folder_table.rowCount()
            self.folder_table.insertRow(row)

            self.folder_table.setItem(row, 0, QTableWidgetItem(str(folder_path)))

            try:
                total_items = len(list(folder_path.iterdir()))
                excluded_count = len(excluded)
                included_count = total_items - excluded_count
            except (OSError, PermissionError) as e:
                logger.warning(f"Could not count items in {folder_path}: {e}")
                included_count = "?"
                excluded_count = "?"

            self.folder_table.setItem(row, 1, QTableWidgetItem(str(included_count)))
            self.folder_table.setItem(row, 2, QTableWidgetItem(str(excluded_count)))
        except Exception as e:
            logger.error(f"Failed to append folder row for {folder_path}: {e}", exc_info=True)
            QMessageBox.critical(self, "Table Error", f"Failed to add folder to table: {str(e)}")
    
    def _start_scan(self):
        """Start the scan process."""
        try:
            if not self.selected_folders:
                QMessageBox.warning(self, "No Folders", "Please add at least one folder to scan.")
                return
            
            self.scan_start_time = datetime.now()

            # Disable UI during scan
            self.btn_scan.setEnabled(False)
            self.btn_add_folder.setEnabled(False)
            self.btn_remove_folder.setEnabled(False)
            
            # Clear previous results
            self.scanned_files = []
            
            # Create and start multi-scan worker
            self.scan_worker = MultiScanWorker(
                self.selected_folders.copy(),
                recursive=True,
                jellyfin_client=self.jellyfin_client,
                excluded_subfolders=self.excluded_paths.copy()
            )
            
            self.scan_worker.progress.connect(self._on_scan_progress)
            self.scan_worker.finished.connect(self._on_multiscan_finished)
            self.scan_worker.error.connect(self._on_scan_error)
            
            self.scan_worker.start()
            
            logger.info(f"Started scan of {len(self.selected_folders)} folders")
        except Exception as e:
            logger.error(f"Failed to start scan: {e}", exc_info=True)
            QMessageBox.critical(self, "Scan Error", f"Failed to start scan: {str(e)}")
            # Re-enable UI on error
            self.btn_scan.setEnabled(True)
            self.btn_add_folder.setEnabled(True)
            self.btn_remove_folder.setEnabled(True)
    
    def _on_scan_progress(self, message: str, current: int, total: int):
        """Handle scan progress updates from MultiScanWorker."""
        try:
            elapsed = 0.0
            if self.scan_start_time:
                elapsed = (datetime.now() - self.scan_start_time).total_seconds()

            if total > 0:
                self.progress_bar.setMaximum(total)
                self.progress_bar.setValue(current)
                percent = (current / total) * 100
                avg_time = (elapsed / current) if current > 0 else 0
                self.lbl_status.setText(
                    f"{message} ({current}/{total}) - {percent:.1f}% | "
                    f"Elapsed: {elapsed:.1f}s | Avg: {avg_time:.2f}s/file"
                )
            else:
                self.progress_bar.setMaximum(0)
                if current > 0:
                    self.lbl_status.setText(f"{message} ({current} files) | {elapsed:.1f}s elapsed")
                else:
                    self.lbl_status.setText(f"{message} | {elapsed:.1f}s elapsed")
        except Exception as e:
            logger.error(f"Failed to update scan progress: {e}", exc_info=True)
    
    def _on_multiscan_finished(
        self,
        file_records: List[FileRecord],
        folder_structure: dict,
        session_ids: List[int],
    ):
        """Handle completion of the MultiScanWorker."""
        try:
            self.inventory_session_ids = session_ids

            stats = ScanStatistics()
            stats.total_files = len(file_records)
            stats.total_size_bytes = sum(r.size_bytes for r in file_records)
            if self.scan_start_time:
                stats.scan_duration_seconds = (datetime.now() - self.scan_start_time).total_seconds()
            self.scan_statistics = stats

            # Re-enable UI
            self.btn_scan.setEnabled(True)
            self.btn_add_folder.setEnabled(True)
            self.btn_remove_folder.setEnabled(True)
            self.progress_bar.setMaximum(100)
            self.progress_bar.setValue(100)
            self.progress_bar.setVisible(False)

            # Update status
            total_size_gb = stats.total_size_bytes / (1024 ** 3) if stats.total_size_bytes else 0
            folder_count = len(self.selected_folders)
            jellyfin_matches = sum(1 for r in file_records if getattr(r, "jellyfin_matched", False))
            elapsed_str = (
                f"{stats.scan_duration_seconds:.1f}s"
                if stats.scan_duration_seconds
                else "n/a"
            )
            self.lbl_status.setText("Scan complete.")

            # Persist session metadata
            self._save_scan_to_database(file_records, stats, session_ids)

            # Emit signals
            self.scan_completed.emit(self.current_scan_session_id)
            self.results_ready.emit(self.current_scan_session_id)

            logger.info(
                "Scan completed: %d files, %.2f GB, %d Jellyfin matches",
                stats.total_files,
                total_size_gb,
                jellyfin_matches,
            )

            QMessageBox.information(
                self,
                "Scan Complete",
                f"Successfully scanned {stats.total_files} files!\n\n"
                f"Total size: {total_size_gb:.2f} GB\n"
                f"Jellyfin matches: {jellyfin_matches}\n"
                f"Elapsed: {elapsed_str}",
            )
        except Exception as e:
            logger.error(f"Failed to handle scan completion: {e}", exc_info=True)
            QMessageBox.critical(self, "Scan Completion Error", f"Scan completed but failed to process results: {str(e)}")
            # Still re-enable UI
            self.btn_scan.setEnabled(True)
            self.btn_add_folder.setEnabled(True)
            self.btn_remove_folder.setEnabled(True)
    
    def _on_scan_error(self, error_msg: str):
        """Handle scan errors."""
        try:
            self.btn_scan.setEnabled(True)
            self.btn_add_folder.setEnabled(True)
            self.btn_remove_folder.setEnabled(True)
            self.progress_bar.setVisible(False)
            self.scan_worker = None
            
            self.lbl_status.setText(f"Scan failed: {error_msg}")
            
            QMessageBox.critical(self, "Scan Error", f"Scan failed:\n\n{error_msg}")
            logger.error(f"Scan error: {error_msg}")
        except Exception as e:
            logger.error(f"Failed to handle scan error: {e}", exc_info=True)
    
    def _save_scan_to_database(
        self,
        files: List[FileRecord],
        stats: Optional[ScanStatistics] = None,
        session_ids: Optional[List[int]] = None,
    ):
        """Save scan session to database."""
        try:
            import sqlite3
            conn = sqlite3.connect("data/media_library.db")
            cursor = conn.cursor()
            
            # Create scan session
            scan_options = {
                'md5_enabled': self.chk_md5.isChecked(),
                'metadata_extraction': self.chk_metadata.isChecked(),
                'folders': [str(f) for f in self.selected_folders],
                'excluded_paths': [str(p) for p in self.excluded_paths]
            }
            if session_ids:
                scan_options['inventory_session_ids'] = session_ids
            
            total_size = stats.total_size_bytes if stats else sum(r.size_bytes for r in files)
            total_files = stats.total_files if stats else len(files)
            
            cursor.execute('''
                INSERT INTO project_scan_sessions 
                (project_id, scan_start, scan_end, total_files, total_size_bytes, scan_options_json)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                self.project.id,
                datetime.now().isoformat(),
                datetime.now().isoformat(),
                total_files,
                total_size,
                json.dumps(scan_options)
            ))
            
            self.current_scan_session_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            logger.info(f"Saved scan session to database: ID={self.current_scan_session_id}")
            
            # Emit signal for Studio to update Project Explorer
            self.scan_completed.emit(self.current_scan_session_id)
            
        except Exception as e:
            logger.error(f"Failed to save scan to database: {e}", exc_info=True)

    def dragEnterEvent(self, event):
        """Handle drag enter event - allow folders to be dropped."""
        try:
            if event.mimeData().hasUrls():
                event.acceptProposedAction()
            else:
                event.ignore()
        except Exception as e:
            logger.error(f"Failed to handle drag enter event: {e}", exc_info=True)
            event.ignore()

    def dropEvent(self, event):
        """Handle drop event - add dropped folders to scan list."""
        try:
            if event.mimeData().hasUrls():
                event.acceptProposedAction()

                # Extract folder paths from dropped URLs
                dropped_paths = []
                for url in event.mimeData().urls():
                    path = Path(url.toLocalFile())
                    if path.is_dir():
                        dropped_paths.append(path)

                for folder_path in dropped_paths:
                    if folder_path in self.selected_folders:
                        continue
                    dialog = FolderContentSelectionDialog(folder_path, self)
                    if dialog.exec() == QDialog.DialogCode.Accepted:
                        excluded = dialog.get_excluded_paths()
                        self.selected_folders.append(folder_path)
                        self.excluded_paths.extend(excluded)
                        self._append_folder_row(folder_path, excluded)
                        logger.info(f"Added folder via drag-and-drop: {folder_path}")
            else:
                event.ignore()
        except Exception as e:
            logger.error(f"Failed to handle drop event: {e}", exc_info=True)
            QMessageBox.critical(self, "Drop Error", f"Failed to add dropped folders: {str(e)}")
            event.ignore()
