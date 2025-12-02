#!/usr/bin/env python3
"""
Jellyfin Cleanup View - Utility tab for cleaning up existing Jellyfin library

Validates EXISTING Jellyfin library entries against filesystem:
- Missing files (entry points to nothing)
- Invalid paths (directories, wrong extensions)
- Duplicate entries (case-sensitive path issues)

NOT part of Round-Up workflow - standalone maintenance tool.
"""

import logging
import time
from pathlib import Path
from typing import List, Dict, Optional
from collections import defaultdict

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QProgressBar, QGroupBox,
    QHeaderView, QCheckBox, QComboBox
)
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCore import Qt, pyqtSignal, QThread

from scripts.core.jellyfin_client import JellyfinClient
from scripts.core.jellyfin_config import JellyfinConfigManager
from scripts.core.file_scanner import FileScanner

logger = logging.getLogger(__name__)

# Valid video extensions
VIDEO_EXTENSIONS = FileScanner.DEFAULT_VIDEO_EXTENSIONS


class ValidationWorker(QThread):
    """Background worker for validating Jellyfin library entries."""

    progress = pyqtSignal(str, int, int)  # message, current, total
    finished = pyqtSignal(list)  # list of result dicts
    error = pyqtSignal(str)  # error message

    def __init__(self, jellyfin_client: JellyfinClient, media_types: List[str]):
        super().__init__()
        self.jellyfin_client = jellyfin_client
        self.media_types = media_types

    def run(self):
        """Validate all Jellyfin items and detect duplicates."""
        try:
            # Fetch all items from Jellyfin
            self.progress.emit("Fetching items from Jellyfin...", 0, 1)
            items = self.jellyfin_client.get_all_items(
                item_types=self.media_types,
                fields=['Name', 'Path', 'ProviderIds', 'Type']
            )

            if not items:
                self.finished.emit([])
                return

            total = len(items)
            logger.info(f"Validating {total} Jellyfin items...")

            results = []
            last_update = time.time()

            # Validate each item
            for i, item in enumerate(items):
                result = self._validate_item(item)
                results.append(result)

                # Emit progress every 10 items or 1 second
                if (i + 1) % 10 == 0 or time.time() - last_update > 1.0:
                    self.progress.emit(
                        f"Validating items: {i + 1}/{total}",
                        i + 1,
                        total
                    )
                    last_update = time.time()

            # Detect duplicates
            self.progress.emit("Detecting duplicates...", total, total)
            self._detect_duplicates(results)

            logger.info(f"Validation complete: {len(results)} items processed")
            self.finished.emit(results)

        except Exception as e:
            logger.error(f"Validation worker error: {e}", exc_info=True)
            self.error.emit(f"Validation failed: {str(e)}")

    def _validate_item(self, item: Dict) -> Dict:
        """Validate a single Jellyfin item."""
        jellyfin_id = item.get('Id', 'N/A')
        title = item.get('Name', 'N/A')
        jellyfin_path = item.get('Path', '')
        item_type = item.get('Type', 'Unknown')

        result = {
            'jellyfin_id': jellyfin_id,
            'title': title,
            'path': jellyfin_path,
            'type': item_type,
            'status': 'VALID',
            'issue': '',
            'file_size': None,
        }

        # Check if path exists
        if not jellyfin_path:
            result['status'] = 'INVALID'
            result['issue'] = 'No path in metadata'
            return result

        try:
            path = Path(jellyfin_path)

            # Check existence
            if not path.exists():
                result['status'] = 'MISSING'
                result['issue'] = 'File does not exist'
                return result

            # Check if file vs directory
            if path.is_dir():
                result['status'] = 'INVALID'
                result['issue'] = 'Path is a directory, not a file'
                return result

            if not path.is_file():
                result['status'] = 'INVALID'
                result['issue'] = 'Path is not a file'
                return result

            # Check extension
            extension = path.suffix.lower()
            if extension not in VIDEO_EXTENSIONS:
                result['status'] = 'INVALID'
                result['issue'] = f'Invalid extension: {extension}'
                return result

            # Check readability
            try:
                stat = path.stat()
                result['file_size'] = stat.st_size
                with open(path, 'rb') as f:
                    f.read(1)  # Try reading first byte
            except PermissionError:
                result['status'] = 'INVALID'
                result['issue'] = 'File not readable (permission denied)'
                return result
            except Exception as e:
                result['status'] = 'INVALID'
                result['issue'] = f'Cannot read file: {str(e)}'
                return result

            # All checks passed
            result['status'] = 'VALID'
            result['issue'] = ''

        except Exception as e:
            result['status'] = 'INVALID'
            result['issue'] = f'Error: {str(e)}'

        return result

    def _detect_duplicates(self, results: List[Dict]):
        """Detect duplicate entries (case-sensitive path issues)."""
        # Group by normalized path
        by_normalized_path = defaultdict(list)

        for result in results:
            # Check ALL items, not just VALID ones.
            # Even MISSING items can be duplicates (e.g. wrong case on Linux)
            if result.get('path'):
                path = result['path']
                normalized = str(Path(path)).lower().replace('\\', '/')
                by_normalized_path[normalized].append(result)

        # Mark duplicates
        for normalized_path, items in by_normalized_path.items():
            if len(items) > 1:
                # Find which one matches filesystem case
                keep_item = None
                for item in items:
                    path = Path(item['path'])
                    if path.exists():
                        resolved = str(path.resolve())
                        if item['path'] == resolved:
                            keep_item = item
                            break

                # Mark all as duplicates, note which to keep
                for item in items:
                    item['status'] = 'DUPLICATE'
                    if item == keep_item:
                        item['issue'] = 'Duplicate (KEEP - correct case)'
                    else:
                        item['issue'] = 'Duplicate (DELETE - wrong case)'


class JellyfinCleanupView(QWidget):
    """
    Jellyfin Cleanup View - Utility tab for library maintenance.

    Validates Jellyfin library entries, detects duplicates, allows deletion.
    Standalone operation - no Round-Up required.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.jellyfin_client = None
        self.validation_worker = None
        self.all_results = []
        self.filtered_results = []

        self._init_ui()
        self._test_jellyfin_connection()

        logger.info("JellyfinCleanupView initialized")

    def _init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # Title
        title = QLabel("🧹 Jellyfin Cleanup")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        layout.addWidget(title)

        # Connection section
        conn_group = QGroupBox("Connection")
        conn_layout = QVBoxLayout()

        self.conn_status_label = QLabel("● Status: Not connected")
        self.conn_status_label.setFont(QFont("Segoe UI", 10))
        conn_layout.addWidget(self.conn_status_label)

        btn_layout = QHBoxLayout()
        btn_test = QPushButton("Test Connection")
        btn_test.clicked.connect(self._test_jellyfin_connection)
        btn_config = QPushButton("Configure Jellyfin")
        btn_config.clicked.connect(self._open_jellyfin_settings)
        btn_layout.addWidget(btn_test)
        btn_layout.addWidget(btn_config)
        btn_layout.addStretch()
        conn_layout.addLayout(btn_layout)

        conn_group.setLayout(conn_layout)
        layout.addWidget(conn_group)

        # Options section
        options_group = QGroupBox("Validation Options")
        options_layout = QHBoxLayout()

        self.chk_movies = QCheckBox("Movies")
        self.chk_movies.setChecked(True)
        self.chk_episodes = QCheckBox("Episodes")
        self.chk_episodes.setChecked(True)

        options_layout.addWidget(QLabel("Media Types:"))
        options_layout.addWidget(self.chk_movies)
        options_layout.addWidget(self.chk_episodes)
        options_layout.addStretch()

        options_group.setLayout(options_layout)
        layout.addWidget(options_group)

        # Action buttons
        action_layout = QHBoxLayout()

        self.btn_scan = QPushButton("▶ Scan Jellyfin Library")
        self.btn_scan.setMinimumHeight(40)
        self.btn_scan.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                font-size: 14px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.btn_scan.clicked.connect(self._start_scan)

        self.btn_export = QPushButton("Export CSV")
        self.btn_export.setEnabled(False)
        self.btn_export.clicked.connect(self._export_csv)

        action_layout.addWidget(self.btn_scan)
        action_layout.addWidget(self.btn_export)
        action_layout.addStretch()

        layout.addLayout(action_layout)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Results table
        results_group = QGroupBox("Results")
        results_layout = QVBoxLayout()

        # Filter
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter:"))
        self.filter_combo = QComboBox()
        self.filter_combo.addItems([
            "All Items",
            "Issues Only (Missing/Invalid/Duplicate)",
            "Valid Only",
            "Missing Only",
            "Duplicates Only"
        ])
        self.filter_combo.currentTextChanged.connect(self._apply_filter)
        filter_layout.addWidget(self.filter_combo)
        filter_layout.addStretch()
        results_layout.addLayout(filter_layout)

        # Table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(7)
        self.results_table.setHorizontalHeaderLabels([
            "☑", "Status", "Title", "Path", "Jellyfin ID", "Size", "Issue"
        ])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.results_table.horizontalHeader().setStretchLastSection(True)
        self.results_table.setColumnWidth(0, 30)  # Checkbox
        self.results_table.setColumnWidth(1, 100)  # Status
        self.results_table.setColumnWidth(2, 200)  # Title
        self.results_table.setColumnWidth(3, 300)  # Path
        self.results_table.setColumnWidth(4, 120)  # ID
        self.results_table.setColumnWidth(5, 80)   # Size
        self.results_table.setSortingEnabled(True)
        self.results_table.setMinimumHeight(300)
        results_layout.addWidget(self.results_table)

        # Summary
        self.summary_label = QLabel("No results yet")
        results_layout.addWidget(self.summary_label)

        results_group.setLayout(results_layout)
        layout.addWidget(results_group, 1)  # Stretch factor

        # Delete section
        delete_group = QGroupBox("Actions")
        delete_layout = QVBoxLayout()

        delete_btn_layout = QHBoxLayout()

        btn_select_issues = QPushButton("Select All Issues")
        btn_select_issues.clicked.connect(self._select_all_issues)
        btn_deselect = QPushButton("Deselect All")
        btn_deselect.clicked.connect(self._deselect_all)

        delete_btn_layout.addWidget(btn_select_issues)
        delete_btn_layout.addWidget(btn_deselect)
        delete_btn_layout.addStretch()
        delete_layout.addLayout(delete_btn_layout)

        delete_action_layout = QHBoxLayout()

        self.btn_delete = QPushButton("Delete Selected from Jellyfin")
        self.btn_delete.setMinimumHeight(35)
        self.btn_delete.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.btn_delete.setEnabled(False)
        self.btn_delete.clicked.connect(self._delete_selected)

        self.chk_dry_run = QCheckBox("Dry Run (preview only, no changes)")
        self.chk_dry_run.setChecked(True)
        self.chk_dry_run.setStyleSheet("font-weight: bold;")

        delete_action_layout.addWidget(self.btn_delete)
        delete_action_layout.addWidget(self.chk_dry_run)
        delete_action_layout.addStretch()
        delete_layout.addLayout(delete_action_layout)

        warning_label = QLabel("⚠ Note: Physical files will NOT be deleted, only Jellyfin database entries")
        warning_label.setStyleSheet("color: #e67e22; font-weight: bold;")
        delete_layout.addWidget(warning_label)

        delete_group.setLayout(delete_layout)
        layout.addWidget(delete_group)

        self.setLayout(layout)

    def _set_status(self, message: str):
        """Set status message in main window's status bar."""
        try:
            main_window = self.window()
            if main_window and hasattr(main_window, 'status_label'):
                main_window.status_label.setText(message)
        except Exception:
            logger.warning(f"Could not set status: {message}")

    def _test_jellyfin_connection(self):
        """Test connection to Jellyfin server."""
        try:
            config_mgr = JellyfinConfigManager()
            if not config_mgr.is_enabled():
                self.conn_status_label.setText("● Status: Not configured")
                self.conn_status_label.setStyleSheet("color: #e67e22;")
                self._set_status("⚠ Jellyfin not configured. Click 'Configure Jellyfin' to set up.")
                self.btn_scan.setEnabled(False)
                return

            server_url = config_mgr.get_server_url()
            api_key = config_mgr.get_api_key()

            if not server_url or not api_key:
                self.conn_status_label.setText("● Status: Missing URL or API key")
                self.conn_status_label.setStyleSheet("color: #e74c3c;")
                self._set_status("✗ Jellyfin: Missing server URL or API key")
                self.btn_scan.setEnabled(False)
                return

            self.jellyfin_client = JellyfinClient(server_url=server_url, api_key=api_key)

            if self.jellyfin_client.test_connection():
                self.conn_status_label.setText(f"● Status: Connected to {server_url}")
                self.conn_status_label.setStyleSheet("color: #27ae60;")
                self._set_status(f"✓ Connected to Jellyfin: {server_url}")
                self.btn_scan.setEnabled(True)
                logger.info(f"Connected to Jellyfin: {server_url}")
            else:
                self.conn_status_label.setText("● Status: Connection failed")
                self.conn_status_label.setStyleSheet("color: #e74c3c;")
                self._set_status("✗ Jellyfin connection test failed")
                self.btn_scan.setEnabled(False)
                self.jellyfin_client = None
                logger.warning("Jellyfin connection test failed")

        except Exception as e:
            logger.error(f"Connection test error: {e}", exc_info=True)
            self.conn_status_label.setText("● Status: Error")
            self.conn_status_label.setStyleSheet("color: #e74c3c;")
            self._set_status(f"✗ Jellyfin connection error: {e}")
            self.btn_scan.setEnabled(False)
            self.jellyfin_client = None

    def _open_jellyfin_settings(self):
        """Open Jellyfin settings dialog."""
        try:
            from scripts.core.dialogs.jellyfin_settings_dialog import JellyfinSettingsDialog
            dialog = JellyfinSettingsDialog(self)
            dialog.show()
        except Exception as e:
            logger.error(f"Failed to open settings dialog: {e}", exc_info=True)
            self._set_status(f"✗ Failed to open settings: {e}")

    def _start_scan(self):
        """Start scanning Jellyfin library."""
        if not self.jellyfin_client:
            self._set_status("✗ Not connected to Jellyfin")
            return

        if self.validation_worker and self.validation_worker.isRunning():
            self._set_status("⚠ Scan already running")
            return

        # Get selected media types
        media_types = []
        if self.chk_movies.isChecked():
            media_types.append("Movie")
        if self.chk_episodes.isChecked():
            media_types.append("Episode")

        if not media_types:
            self._set_status("⚠ Please select at least one media type")
            return

        # Start validation worker
        self.validation_worker = ValidationWorker(self.jellyfin_client, media_types)
        self.validation_worker.progress.connect(self._on_scan_progress)
        self.validation_worker.finished.connect(self._on_scan_finished)
        self.validation_worker.error.connect(self._on_scan_error)

        self.btn_scan.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self._set_status("Scanning Jellyfin library...")

        self.validation_worker.start()
        logger.info(f"Started validation scan for: {media_types}")

    def _on_scan_progress(self, message: str, current: int, total: int):
        """Handle scan progress updates."""
        if total > 0:
            percent = int((current / total) * 100)
            self.progress_bar.setValue(percent)
        self._set_status(message)

    def _on_scan_finished(self, results: List[Dict]):
        """Handle scan completion."""
        self.all_results = results
        self.filtered_results = results

        self.progress_bar.setVisible(False)
        self.btn_scan.setEnabled(True)
        self.btn_export.setEnabled(True)
        self.btn_delete.setEnabled(True)

        self._populate_table()
        self._update_summary()

        self._set_status(f"✓ Scan complete: {len(results)} items validated")
        logger.info(f"Scan complete: {len(results)} items")

    def _on_scan_error(self, error_msg: str):
        """Handle scan error."""
        self.progress_bar.setVisible(False)
        self.btn_scan.setEnabled(True)
        self._set_status(f"✗ {error_msg}")
        logger.error(f"Scan error: {error_msg}")

    def _apply_filter(self):
        """Apply filter to results."""
        filter_text = self.filter_combo.currentText()

        if filter_text == "All Items":
            self.filtered_results = self.all_results
        elif filter_text == "Issues Only (Missing/Invalid/Duplicate)":
            self.filtered_results = [r for r in self.all_results if r['status'] != 'VALID']
        elif filter_text == "Valid Only":
            self.filtered_results = [r for r in self.all_results if r['status'] == 'VALID']
        elif filter_text == "Missing Only":
            self.filtered_results = [r for r in self.all_results if r['status'] == 'MISSING']
        elif filter_text == "Duplicates Only":
            self.filtered_results = [r for r in self.all_results if r['status'] == 'DUPLICATE']

        self._populate_table()
        self._update_summary()

    def _populate_table(self):
        """Populate the results table."""
        self.results_table.setSortingEnabled(False)
        self.results_table.setRowCount(len(self.filtered_results))

        for row, result in enumerate(self.filtered_results):
            try:
                # Checkbox
                checkbox = QCheckBox()
                self.results_table.setCellWidget(row, 0, checkbox)

                # Status
                status_item = QTableWidgetItem(result['status'])
                if result['status'] == 'VALID':
                    status_item.setBackground(QColor(39, 174, 96, 50))  # Green
                elif result['status'] == 'MISSING':
                    status_item.setBackground(QColor(231, 76, 60, 50))  # Red
                elif result['status'] == 'DUPLICATE':
                    status_item.setBackground(QColor(243, 156, 18, 50))  # Orange
                else:  # INVALID
                    status_item.setBackground(QColor(255, 235, 59, 50))  # Yellow
                self.results_table.setItem(row, 1, status_item)

                # Title
                title_item = QTableWidgetItem(result['title'])
                self.results_table.setItem(row, 2, title_item)

                # Path
                path_item = QTableWidgetItem(result['path'])
                self.results_table.setItem(row, 3, path_item)

                # Jellyfin ID
                id_item = QTableWidgetItem(result['jellyfin_id'])
                self.results_table.setItem(row, 4, id_item)

                # Size
                size_str = self._format_size(result['file_size']) if result['file_size'] else '-'
                size_item = QTableWidgetItem(size_str)
                self.results_table.setItem(row, 5, size_item)

                # Issue
                issue_item = QTableWidgetItem(result['issue'])
                self.results_table.setItem(row, 6, issue_item)

            except Exception as e:
                logger.error(f"Failed to populate row {row}: {e}", exc_info=True)

        self.results_table.setSortingEnabled(True)

    def _update_summary(self):
        """Update summary statistics."""
        total = len(self.all_results)
        valid = sum(1 for r in self.all_results if r['status'] == 'VALID')
        missing = sum(1 for r in self.all_results if r['status'] == 'MISSING')
        invalid = sum(1 for r in self.all_results if r['status'] == 'INVALID')
        duplicates = sum(1 for r in self.all_results if r['status'] == 'DUPLICATE')
        issues = total - valid

        filtered_count = len(self.filtered_results)

        summary = (
            f"Total: {total} | Valid: {valid} | Issues: {issues} "
            f"(Missing: {missing}, Invalid: {invalid}, Duplicates: {duplicates}) | "
            f"Showing: {filtered_count}"
        )
        self.summary_label.setText(summary)

    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"

    def _select_all_issues(self):
        """Select all rows with issues."""
        for row in range(self.results_table.rowCount()):
            checkbox = self.results_table.cellWidget(row, 0)
            if checkbox:
                status_item = self.results_table.item(row, 1)
                if status_item and status_item.text() != 'VALID':
                    checkbox.setChecked(True)

    def _deselect_all(self):
        """Deselect all rows."""
        for row in range(self.results_table.rowCount()):
            checkbox = self.results_table.cellWidget(row, 0)
            if checkbox:
                checkbox.setChecked(False)

    def _delete_selected(self):
        """Delete selected items from Jellyfin."""
        if not self.jellyfin_client:
            self._set_status("✗ Not connected to Jellyfin")
            return

        # Get selected items
        selected_ids = []
        selected_titles = []

        for row in range(self.results_table.rowCount()):
            checkbox = self.results_table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                id_item = self.results_table.item(row, 4)
                title_item = self.results_table.item(row, 2)
                if id_item:
                    selected_ids.append(id_item.text())
                    selected_titles.append(title_item.text() if title_item else "Unknown")

        if not selected_ids:
            self._set_status("⚠ No items selected")
            return

        # Dry run mode
        if self.chk_dry_run.isChecked():
            self._set_status(f"⚠ DRY RUN: Would delete {len(selected_ids)} items (no changes made)")
            logger.info(f"Dry run: would delete {len(selected_ids)} items")
            logger.info(f"Items: {selected_titles}")
            return

        # Real deletion
        self._set_status(f"Deleting {len(selected_ids)} items from Jellyfin...")
        self.btn_delete.setEnabled(False)

        deleted = 0
        failed = 0

        for item_id, title in zip(selected_ids, selected_titles):
            try:
                if self.jellyfin_client.delete_item(item_id):
                    deleted += 1
                    logger.info(f"Deleted: {title} (ID: {item_id})")
                else:
                    failed += 1
                    logger.warning(f"Failed to delete: {title} (ID: {item_id})")
            except Exception as e:
                failed += 1
                logger.error(f"Error deleting {title}: {e}", exc_info=True)

        self.btn_delete.setEnabled(True)
        self._set_status(f"✓ Deleted {deleted} items, {failed} failed")

        # Re-scan to update table
        if deleted > 0:
            self._start_scan()

    def _export_csv(self):
        """Export results to CSV."""
        try:
            from PyQt6.QtWidgets import QFileDialog
            import csv

            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Export Results",
                f"jellyfin_cleanup_{time.strftime('%Y%m%d_%H%M%S')}.csv",
                "CSV Files (*.csv)"
            )

            if not filename:
                return

            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Status', 'Title', 'Path', 'Jellyfin ID', 'Size', 'Issue'])

                for result in self.filtered_results:
                    size_str = self._format_size(result['file_size']) if result['file_size'] else ''
                    writer.writerow([
                        result['status'],
                        result['title'],
                        result['path'],
                        result['jellyfin_id'],
                        size_str,
                        result['issue']
                    ])

            self._set_status(f"✓ Exported {len(self.filtered_results)} items to {filename}")
            logger.info(f"Exported to: {filename}")

        except Exception as e:
            logger.error(f"Export failed: {e}", exc_info=True)
            self._set_status(f"✗ Export failed: {e}")
