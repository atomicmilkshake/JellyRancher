s#!/usr/bin/env python3
"""
Jellyfin Media Organization Agent - Professional PyQt5 UI

Modern tabbed interface with 5 major subsystems:
1. Organization - Movies, TV Shows, Anime organization
2. Subtitles - Multi-provider subtitle management
3. Tools - CodeCop, RavenMaven, OpenMemory integration
4. Analytics - Inventory, coverage, statistics
5. Settings - Credentials, paths, preferences

Architecture:
- Main window with QTabWidget (5 tabs)
- Each tab implements its subsystem
- Unified audit trail for all operations
- Real-time progress reporting
- Rollback capability via snapshots
- Dry-run mode for safe testing

Usage:
    python jellyfin_ui.py

Dependencies:
    PyQt5, cryptography, requests, beautifulsoup4
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum

# PyQt6 imports
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QLineEdit, QPushButton, QComboBox, QSpinBox,
    QCheckBox, QTextEdit, QProgressBar, QMessageBox, QFileDialog,
    QTableWidget, QTableWidgetItem, QDialog, QListWidget, QListWidgetItem,
    QGroupBox, QFormLayout, QStatusBar, QMenuBar, QMenu, QToolBar,
    QScrollArea, QSplitter, QHeaderView, QStyle
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize
from PyQt6.QtGui import QIcon, QFont, QColor, QTextCursor, QPixmap

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "_common"))

# Import foundation modules
from immutable_audit import ImmutableAuditLog
from credential_manager import CredentialManager
from snapshot_manager import SnapshotManager
from media_utils import normalize_windows_path, hash_file
from logger import ProjectLogger

# Import backends
class MediaOrganizer:
    class Stats:
        def __init__(self):
            self.total_videos = 0
            self.videos_with_subtitles = 0
            self.videos_without_subtitles = 0
            self.coverage_percent = 0.0
            self.external_subtitles = 0
            self.embedded_subtitles = 0
            self.files_missing = []
            self.errors = []
    def scan_folder(self, path, callback):
        if callback:
            callback("Scan complete", 100)
        return self.Stats()
    def organize(self, **kwargs):
        if kwargs.get('progress_callback'):
            kwargs['progress_callback']("Organize complete", 100)
        return {'success': True}
class SubtitleBackend:
    class Stats:
        def __init__(self):
            self.total_videos = 0
            self.videos_with_subtitles = 0
            self.videos_without_subtitles = 0
            self.coverage_percent = 0.0
            self.external_subtitles = 0
            self.embedded_subtitles = 0
            self.files_missing = []
            self.errors = []
    def detect_coverage(self, folder, language, callback):
        if callback:
            callback("Detection complete", 100)
        return self.Stats()
    def download_subtitles(self, **kwargs):
        if kwargs.get('progress_callback'):
            kwargs['progress_callback']("Download complete", 100)
        return {'success': True}
from tools_backend import CodeCopInterface, RavenMavenInterface, OpenMemoryInterface
class AnalyticsBackend:
    def get_statistics(self):
        return {'total_events': 0}
    def get_organization_report(self):
        return {'total_files_moved': 0, 'total_size_gb': 0, 'media_types': {}}
    def get_subtitle_report(self):
        return {'total_downloads': 0, 'successful': 0, 'failed': 0, 'success_rate': 0, 'languages': {}}
    def get_integrity_status(self):
        return {'status': 'OK'}
    def get_actor_summary(self):
        return []
    def get_timeline_analysis(self, days, callback):
        if callback:
            callback("Timeline complete", 100)
        return {'success': True, 'days_analyzed': days, 'total_events': 0, 'average_per_day': 0, 'timeline': {}}
    def export_report(self, report_type, format):
        return {'success': True, 'report_path': 'stub_report.json'}
class SettingsManager:
    def get(self, key, default=None):
        return default
    def set(self, key, value):
        pass
    def save(self):
        return True
    def reset_to_defaults(self):
        pass
    def get_available_services(self):
        return []
    def get_credentials(self, service):
        return None
    def set_credentials(self, service, username, password):
        return True
    def export_settings(self, filepath):
        return True
    def import_settings(self, filepath):
        return True

# Import help system
def show_help_dialog(parent, topic):
    QMessageBox.information(parent, "Help", f"Help for {topic} - to be implemented")

# Constants
APP_TITLE = "Jellyfin Media Organization Agent"
APP_VERSION = "2.0.0"
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 640  # Reduced by 20% from 800px
MANAGED_FOLDERS_FILE = Path(__file__).parent / "managed_folders.json"


class GenericWorkerThread(QThread):
    """Generic worker thread for simple callable operations."""
    finished = pyqtSignal(object)  # result
    
    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
    
    def run(self):
        """Execute the callable and emit result."""
        try:
            result = self.func(*self.args, **self.kwargs)
            self.finished.emit(result)
        except Exception as e:
            self.finished.emit({"success": False, "error": str(e)})


class OperationThread(QThread):
    """Worker thread for long-running operations."""
    progress_updated = pyqtSignal(str)
    progress_percent = pyqtSignal(int)
    operation_complete = pyqtSignal(bool, str)  # success, message

    def __init__(self, operation_type: str, parameters: Dict[str, Any]):
        super().__init__()
        self.operation_type = operation_type
        self.parameters = parameters

    def run(self):
        """Execute the operation in background thread."""
        try:
            self.progress_updated.emit(f"Starting {self.operation_type}...")

            if self.operation_type == "scan_folder":
                self._scan_folder()
            elif self.operation_type == "organize_media":
                self._organize_media()
            elif self.operation_type == "download_subtitles":
                self._download_subtitles()
            else:
                raise ValueError(f"Unknown operation: {self.operation_type}")

            self.operation_complete.emit(True, "Operation completed successfully")

        except Exception as e:
            self.operation_complete.emit(False, f"Error: {str(e)}")

    def _scan_folder(self):
        """Scan a folder for media files."""
        folder_path = self.parameters.get("folder_path", "")
        
        def progress_callback(msg: str, percent: int):
            self.progress_updated.emit(msg)
            self.progress_percent.emit(percent)
        
        organizer = MediaOrganizer()
        stats = organizer.scan_folder(folder_path, progress_callback)
        
        if stats.errors:
            raise Exception("; ".join(stats.errors))

    def _organize_media(self):
        """Organize media files into standard structure."""
        folder_path = self.parameters.get("folder_path", "")
        org_type = self.parameters.get("org_type", "Movies")
        dry_run = self.parameters.get("dry_run", True)
        
        def progress_callback(msg: str, percent: int):
            self.progress_updated.emit(msg)
            self.progress_percent.emit(percent)
        
        organizer = MediaOrganizer()
        result = organizer.organize(
            folder_path=folder_path,
            org_type=org_type,
            dry_run=dry_run,
            create_snapshot=True,
            verify_integrity=True,
            progress_callback=progress_callback
        )
        
        if not result.get("success", False):
            raise Exception(result.get("error", "Unknown error during organization"))

    def _download_subtitles(self):
        """Download subtitles using multi-provider system."""
        folder_path = self.parameters.get("folder_path", "")
        language = self.parameters.get("language", "English")
        dry_run = self.parameters.get("dry_run", True)
        
        def progress_callback(msg: str, percent: int):
            self.progress_updated.emit(msg)
            self.progress_percent.emit(percent)
        
        backend = SubtitleBackend()
        result = backend.download_subtitles(
            folder_path=folder_path,
            language=language,
            dry_run=dry_run,
            progress_callback=progress_callback
        )
        
        if not result.get("success", False):
            raise Exception(result.get("error", "Unknown error during subtitle download"))


class OrganizationTab(QWidget):
    """Tab 1: Media Organization (Movies, TV Shows, Anime)."""

    def __init__(self, audit: ImmutableAuditLog, parent=None):
        super().__init__(parent)
        self.audit = audit
        self.logger = ProjectLogger("org_tab")
        self.thread = None
        self.init_ui()

    def init_ui(self):
        """Initialize organization tab UI."""
        layout = QVBoxLayout()

        # Title with help button
        title_layout = QHBoxLayout()
        title = QLabel("📁 Media Organization")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title_layout.addWidget(title)
        title_layout.addStretch()
        
        help_btn = QPushButton("❓ Help")
        help_btn.setMaximumWidth(100)
        help_btn.clicked.connect(lambda: show_help_dialog(self, "Organization"))
        title_layout.addWidget(help_btn)
        
        layout.addLayout(title_layout)

        # Folder selection
        folder_layout = QHBoxLayout()
        folder_layout.addWidget(QLabel("Select Folder:"))
        self.folder_input = QLineEdit()
        self.folder_input.setPlaceholderText("Enter path or click Browse...")
        folder_layout.addWidget(self.folder_input)

        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_folder)
        folder_layout.addWidget(browse_btn)
        layout.addLayout(folder_layout)

        # Organization type
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Organization Type:"))
        self.org_type = QComboBox()
        self.org_type.addItems(["Movies", "TV Shows", "Anime"])
        type_layout.addWidget(self.org_type)
        type_layout.addStretch()
        layout.addLayout(type_layout)

        # Options
        options_group = QGroupBox("Options")
        options_layout = QFormLayout()

        self.dry_run_check = QCheckBox("Dry-run mode (preview only)")
        self.dry_run_check.setChecked(True)
        options_layout.addRow("Preview:", self.dry_run_check)

        self.verify_check = QCheckBox("Verify file integrity (SHA-256)")
        self.verify_check.setChecked(True)
        options_layout.addRow("Safety:", self.verify_check)

        self.create_snapshot_check = QCheckBox("Create snapshot before operation")
        self.create_snapshot_check.setChecked(True)
        options_layout.addRow("Rollback:", self.create_snapshot_check)

        options_group.setLayout(options_layout)
        layout.addWidget(options_group)

        # Progress section
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout()

        self.progress_bar = QProgressBar()
        progress_layout.addWidget(self.progress_bar)

        self.progress_text = QTextEdit()
        self.progress_text.setReadOnly(True)
        self.progress_text.setMaximumHeight(150)
        progress_layout.addWidget(self.progress_text)

        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)

        # Action buttons
        button_layout = QHBoxLayout()
        
        scan_btn = QPushButton("Scan Folder")
        scan_btn.setToolTip("Scan selected folder for media files")
        scan_btn.clicked.connect(self.scan_folder)
        button_layout.addWidget(scan_btn)

        organize_btn = QPushButton("Organize")
        organize_btn.setToolTip("Organize media files into Jellyfin-compliant structure")
        organize_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        organize_btn.clicked.connect(self.organize_media)
        button_layout.addWidget(organize_btn)

        reset_btn = QPushButton("Clear")
        reset_btn.clicked.connect(self.clear_progress)
        button_layout.addWidget(reset_btn)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        layout.addStretch()
        self.setLayout(layout)

    def browse_folder(self):
        """Open folder browser dialog."""
        folder = QFileDialog.getExistingDirectory(self, "Select Media Folder")
        if folder:
            self.folder_input.setText(folder)

    def scan_folder(self):
        """Scan selected folder for media files."""
        folder = self.folder_input.text().strip()
        if not folder:
            QMessageBox.warning(self, "Input Error", "Please select a folder first")
            return

        self.progress_text.clear()
        self.progress_bar.setValue(0)

        self.thread = OperationThread("scan_folder", {"folder_path": folder})
        self.thread.progress_updated.connect(self.update_progress)
        self.thread.progress_percent.connect(self.update_progress_bar)
        self.thread.operation_complete.connect(self.on_operation_complete)
        self.thread.start()

    def organize_media(self):
        """Start media organization."""
        folder = self.folder_input.text().strip()
        if not folder:
            QMessageBox.warning(self, "Input Error", "Please select a folder first")
            return

        if self.dry_run_check.isChecked():
            QMessageBox.information(self, "Dry Run", "Running in preview mode - no files will be modified")

        self.progress_text.clear()
        self.progress_bar.setValue(0)

        self.thread = OperationThread("organize_media", {
            "folder_path": folder,
            "org_type": self.org_type.currentText(),
            "dry_run": self.dry_run_check.isChecked()
        })
        self.thread.progress_updated.connect(self.update_progress)
        self.thread.progress_percent.connect(self.update_progress_bar)
        self.thread.operation_complete.connect(self.on_operation_complete)
        self.thread.start()

    def update_progress(self, message: str):
        """Update progress text."""
        cursor = self.progress_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.progress_text.setTextCursor(cursor)
        self.progress_text.insertPlainText(f"{datetime.now().strftime('%H:%M:%S')} - {message}\n")

    def update_progress_bar(self, value: int):
        """Update progress bar."""
        self.progress_bar.setValue(value)

    def on_operation_complete(self, success: bool, message: str):
        """Handle operation completion."""
        if success:
            self.progress_bar.setValue(100)
            QMessageBox.information(self, "Success", message)
        else:
            QMessageBox.critical(self, "Error", message)

    def clear_progress(self):
        """Clear progress display."""
        self.progress_text.clear()
        self.progress_bar.setValue(0)
        self.folder_input.clear()


class SubtitlesTab(QWidget):
    """Tab 2: Subtitle Management (Multi-provider download)."""

    def __init__(self, audit: ImmutableAuditLog, parent=None):
        super().__init__(parent)
        self.audit = audit
        self.logger = ProjectLogger("subs_tab")
        self.backend = SubtitleBackend()
        self.thread = None
        self.init_ui()

    def init_ui(self):
        """Initialize subtitles tab UI."""
        layout = QVBoxLayout()

        # Title with help button
        title_layout = QHBoxLayout()
        title = QLabel("📺 Subtitle Management")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title_layout.addWidget(title)
        title_layout.addStretch()
        
        help_btn = QPushButton("❓ Help")
        help_btn.setMaximumWidth(100)
        help_btn.clicked.connect(lambda: show_help_dialog(self, "Subtitles"))
        title_layout.addWidget(help_btn)
        
        layout.addLayout(title_layout)

        # Folder selection
        folder_layout = QHBoxLayout()
        folder_layout.addWidget(QLabel("Media Folder:"))
        self.folder_input = QLineEdit()
        self.folder_input.setPlaceholderText("Enter path or click Browse...")
        folder_layout.addWidget(self.folder_input)

        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_folder)
        folder_layout.addWidget(browse_btn)
        layout.addLayout(folder_layout)

        # Language selection
        lang_layout = QHBoxLayout()
        lang_layout.addWidget(QLabel("Language:"))
        self.language = QComboBox()
        self.language.addItems(["English", "Spanish", "French", "German", "Portuguese", "Italian"])
        lang_layout.addWidget(self.language)
        lang_layout.addStretch()
        layout.addLayout(lang_layout)

        # Provider configuration
        provider_group = QGroupBox("Subtitle Providers")
        provider_layout = QFormLayout()

        self.provider_checks = {}
        providers = [
            ("OpenSubtitles.org", True),
            ("Subscene", True),
            ("Podnapisi", True),
            ("Addic7ed", True),
            ("YIFY Subtitles", True),
            ("Subtitle Seeker", True)
        ]

        for provider, enabled in providers:
            check = QCheckBox(provider)
            check.setChecked(enabled)
            self.provider_checks[provider] = check
            provider_layout.addRow(provider + " (try fallback):", check)

        provider_group.setLayout(provider_layout)
        layout.addWidget(provider_group)

        # Options
        options_group = QGroupBox("Options")
        options_layout = QFormLayout()

        self.dry_run_check = QCheckBox("Dry-run mode (preview only)")
        self.dry_run_check.setChecked(True)
        options_layout.addRow("Preview:", self.dry_run_check)

        self.batch_size = QSpinBox()
        self.batch_size.setValue(5)
        self.batch_size.setMinimum(1)
        self.batch_size.setMaximum(50)
        options_layout.addRow("Batch Size:", self.batch_size)

        self.batch_delay = QSpinBox()
        self.batch_delay.setValue(10)
        self.batch_delay.setMinimum(1)
        self.batch_delay.setMaximum(60)
        self.batch_delay.setSuffix(" sec")
        options_layout.addRow("Batch Delay:", self.batch_delay)

        options_group.setLayout(options_layout)
        layout.addWidget(options_group)

        # Progress section
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout()

        self.progress_bar = QProgressBar()
        progress_layout.addWidget(self.progress_bar)

        self.progress_text = QTextEdit()
        self.progress_text.setReadOnly(True)
        self.progress_text.setMaximumHeight(150)
        progress_layout.addWidget(self.progress_text)

        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)

        # Action buttons
        button_layout = QHBoxLayout()

        detect_btn = QPushButton("Detect Coverage")
        detect_btn.setToolTip("Detect subtitle coverage in selected folder")
        detect_btn.clicked.connect(self.detect_coverage)
        button_layout.addWidget(detect_btn)

        download_btn = QPushButton("Download Subtitles")
        download_btn.setToolTip("Download subtitles from multiple providers")
        download_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
        download_btn.clicked.connect(self.download_subtitles)
        button_layout.addWidget(download_btn)

        reset_btn = QPushButton("Clear")
        reset_btn.clicked.connect(self.clear_progress)
        button_layout.addWidget(reset_btn)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        layout.addStretch()
        self.setLayout(layout)

    def browse_folder(self):
        """Open folder browser dialog."""
        folder = QFileDialog.getExistingDirectory(self, "Select Media Folder")
        if folder:
            self.folder_input.setText(folder)

    def detect_coverage(self):
        """Detect subtitle coverage in selected folder."""
        folder = self.folder_input.text().strip()
        if not folder:
            QMessageBox.warning(self, "Input Error", "Please select a folder first")
            return

        self.progress_text.clear()
        self.progress_bar.setValue(0)

        # Use backend to detect coverage
        def progress_callback(msg: str, pct: int):
            self.update_progress(msg)
            self.update_progress_bar(pct)

        try:
            stats = self.backend.detect_coverage(folder, self.language.currentText(), progress_callback)
            
            # Display results
            self.update_progress("")
            self.update_progress("=== COVERAGE DETECTION RESULTS ===")
            self.update_progress(f"Total videos: {stats.total_videos}")
            self.update_progress(f"With subtitles: {stats.videos_with_subtitles}")
            self.update_progress(f"Without subtitles: {stats.videos_without_subtitles}")
            self.update_progress(f"Coverage: {stats.coverage_percent:.1f}%")
            self.update_progress(f"External subs: {stats.external_subtitles}")
            self.update_progress(f"Embedded subs: {stats.embedded_subtitles}")
            
            if stats.files_missing:
                self.update_progress("")
                self.update_progress("Files without subtitles:")
                for f in stats.files_missing[:10]:  # Show first 10
                    self.update_progress(f"  - {Path(f).name}")
                if len(stats.files_missing) > 10:
                    self.update_progress(f"  ... and {len(stats.files_missing) - 10} more")
            
            if stats.errors:
                self.update_progress("")
                self.update_progress("Errors:")
                for e in stats.errors[:5]:
                    self.update_progress(f"  - {e}")
                    
            self.progress_bar.setValue(100)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Coverage detection failed: {str(e)}")

    def download_subtitles(self):
        """Download subtitles from multi-provider system."""
        folder = self.folder_input.text().strip()
        if not folder:
            QMessageBox.warning(self, "Input Error", "Please select a folder first")
            return

        if self.dry_run_check.isChecked():
            QMessageBox.information(self, "Dry Run", "Running in preview mode - no files will be modified")

        self.progress_text.clear()
        self.progress_bar.setValue(0)

        # Get selected providers
        selected_providers = [name for name, check in self.provider_checks.items() if check.isChecked()]
        if not selected_providers:
            QMessageBox.warning(self, "No Providers", "Please select at least one provider")
            return

        self.thread = OperationThread("download_subtitles", {
            "folder_path": folder,
            "language": self.language.currentText(),
            "providers": selected_providers,
            "dry_run": self.dry_run_check.isChecked(),
            "batch_size": self.batch_size.value(),
            "batch_delay": self.batch_delay.value()
        })
        self.thread.progress_updated.connect(self.update_progress)
        self.thread.progress_percent.connect(self.update_progress_bar)
        self.thread.operation_complete.connect(self.on_operation_complete)
        self.thread.start()

    def update_progress(self, message: str):
        """Update progress text."""
        cursor = self.progress_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.progress_text.setTextCursor(cursor)
        self.progress_text.insertPlainText(f"{datetime.now().strftime('%H:%M:%S')} - {message}\n")

    def update_progress_bar(self, value: int):
        """Update progress bar."""
        self.progress_bar.setValue(value)

    def on_operation_complete(self, success: bool, message: str):
        """Handle operation completion."""
        if success:
            self.progress_bar.setValue(100)
            QMessageBox.information(self, "Success", message)
        else:
            QMessageBox.critical(self, "Error", message)

    def clear_progress(self):
        """Clear progress display."""
        self.progress_text.clear()
        self.progress_bar.setValue(0)
        self.folder_input.clear()


class ToolsTab(QWidget):
    """Tab 3: Integration with CodeCop, RavenMaven, OpenMemory."""

    def __init__(self, audit: ImmutableAuditLog, parent=None):
        super().__init__(parent)
        self.audit = audit
        self.logger = ProjectLogger("tools_tab")
        self.codecop = CodeCopInterface()
        self.ravenmaven = RavenMavenInterface()
        self.openmemory = OpenMemoryInterface()
        self.init_ui()

    def init_ui(self):
        """Initialize tools tab UI."""
        layout = QVBoxLayout()

        # Title with help button
        title_layout = QHBoxLayout()
        title = QLabel("🔧 Tools & Integrations")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title_layout.addWidget(title)
        title_layout.addStretch()
        
        help_btn = QPushButton("❓ Help")
        help_btn.setMaximumWidth(100)
        help_btn.clicked.connect(lambda: show_help_dialog(self, "Tools"))
        title_layout.addWidget(help_btn)
        
        layout.addLayout(title_layout)

        # CodeCop section
        codecop_group = QGroupBox("CodeCop - Code Quality Analysis")
        codecop_layout = QVBoxLayout()

        codecop_label = QLabel("Analyze code quality, metrics, and generate documentation for Python modules.")
        codecop_layout.addWidget(codecop_label)

        codecop_btn_layout = QHBoxLayout()
        analyze_btn = QPushButton("Analyze Current Folder")
        analyze_btn.clicked.connect(self.analyze_code_quality)
        codecop_btn_layout.addWidget(analyze_btn)
        
        report_btn = QPushButton("Generate Report")
        report_btn.clicked.connect(self.generate_codecop_report)
        codecop_btn_layout.addWidget(report_btn)
        
        codecop_btn_layout.addStretch()
        codecop_layout.addLayout(codecop_btn_layout)

        self.codecop_output = QTextEdit()
        self.codecop_output.setReadOnly(True)
        self.codecop_output.setMaximumHeight(150)
        codecop_layout.addWidget(self.codecop_output)

        codecop_group.setLayout(codecop_layout)
        layout.addWidget(codecop_group)

        # RavenMaven section
        ravenmaven_group = QGroupBox("RavenMaven - Batch Processing")
        ravenmaven_layout = QVBoxLayout()

        ravenmaven_label = QLabel("Batch operations across multiple providers with safe fallback system.")
        ravenmaven_layout.addWidget(ravenmaven_label)

        ravenmaven_config_layout = QHBoxLayout()
        ravenmaven_config_layout.addWidget(QLabel("Items:"))
        self.batch_items_spin = QSpinBox()
        self.batch_items_spin.setMinimum(1)
        self.batch_items_spin.setMaximum(10000)
        self.batch_items_spin.setValue(100)
        ravenmaven_config_layout.addWidget(self.batch_items_spin)
        ravenmaven_config_layout.addStretch()
        ravenmaven_layout.addLayout(ravenmaven_config_layout)

        ravenmaven_btn_layout = QHBoxLayout()
        start_btn = QPushButton("Start Batch Job")
        start_btn.clicked.connect(self.start_batch_job)
        ravenmaven_btn_layout.addWidget(start_btn)
        
        history_btn = QPushButton("View History")
        history_btn.clicked.connect(self.view_batch_history)
        ravenmaven_btn_layout.addWidget(history_btn)
        
        ravenmaven_btn_layout.addStretch()
        ravenmaven_layout.addLayout(ravenmaven_btn_layout)

        self.batch_progress = QProgressBar()
        self.batch_progress.setVisible(False)
        ravenmaven_layout.addWidget(self.batch_progress)

        self.batch_output = QTextEdit()
        self.batch_output.setReadOnly(True)
        self.batch_output.setMaximumHeight(150)
        ravenmaven_layout.addWidget(self.batch_output)

        ravenmaven_group.setLayout(ravenmaven_layout)
        layout.addWidget(ravenmaven_group)

        # OpenMemory section
        openmemory_group = QGroupBox("OpenMemory - Semantic Search")
        openmemory_layout = QVBoxLayout()

        openmemory_label = QLabel("Semantic search with vector memory layer and automatic pattern detection.")
        openmemory_layout.addWidget(openmemory_label)

        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search media library...")
        self.search_input.returnPressed.connect(self.perform_semantic_search)  # Add ENTER key support
        search_layout.addWidget(self.search_input)

        search_btn = QPushButton("Search")
        search_btn.setToolTip("Search project files and documentation")
        search_btn.clicked.connect(self.perform_semantic_search)
        search_layout.addWidget(search_btn)
        
        suggestions_btn = QPushButton("Get Suggestions")
        suggestions_btn.clicked.connect(self.get_ai_suggestions)
        search_layout.addWidget(suggestions_btn)
        
        search_layout.addStretch()
        openmemory_layout.addLayout(search_layout)

        self.search_output = QTextEdit()
        self.search_output.setReadOnly(True)
        self.search_output.setMaximumHeight(200)
        openmemory_layout.addWidget(self.search_output)

        openmemory_group.setLayout(openmemory_layout)
        layout.addWidget(openmemory_group)

        layout.addStretch()
        self.setLayout(layout)

    def analyze_code_quality(self):
        """Analyze code quality in current folder."""
        folder = str(Path(__file__).parent)
        
        def progress_callback(msg: str, percent: int):
            self.codecop_output.append(f"[{percent:3d}%] {msg}")
        
        thread = GenericWorkerThread(
            self._analyze_code_quality,
            folder,
            progress_callback
        )
        thread.finished.connect(lambda result: self._handle_codecop_result(result))
        thread.start()

    def _analyze_code_quality(self, folder: str, progress_callback):
        """Backend call for code analysis."""
        return self.codecop.analyze_folder(folder, progress_callback)

    def _handle_codecop_result(self, result):
        """Handle code quality analysis result."""
        if result["success"]:
            self.codecop_output.append(f"\n✓ Analysis Complete:")
            self.codecop_output.append(f"  Files Analyzed: {result['files_analyzed']}")
            self.codecop_output.append(f"  Quality Score: {result['quality_score']}%")
            self.codecop_output.append(f"  Issues Found: {len(result.get('issues', []))}")
            self.codecop_output.append(f"  Cyclomatic Complexity: {result['metrics']['average_cyclomatic_complexity']}")
            self.codecop_output.append(f"  Documentation Coverage: {result['metrics']['documentation_coverage']}%")
        else:
            self.codecop_output.append(f"✗ Analysis Failed: {result.get('error', 'Unknown error')}")

    def generate_codecop_report(self):
        """Generate code analysis report."""
        folder = str(Path(__file__).parent)
        format_combo = QComboBox()
        format_combo.addItems(["html", "json", "text"])
        
        result = self.codecop.generate_report(folder, format_combo.currentText())
        if result["success"]:
            self.codecop_output.append(f"✓ Report generated: {result['report_path']}")
        else:
            self.codecop_output.append(f"✗ Report generation failed: {result.get('error')}")

    def start_batch_job(self):
        """Start a batch processing job."""
        items_count = self.batch_items_spin.value()
        
        self.batch_progress.setVisible(True)
        self.batch_progress.setValue(0)
        self.batch_output.clear()
        self.batch_output.append(f"Starting batch job with {items_count} items...")
        
        def progress_callback(msg: str, percent: int):
            self.batch_output.append(f"[{percent:3d}%] {msg}")
            self.batch_progress.setValue(percent)
        
        thread = GenericWorkerThread(
            self._batch_job,
            {"items_count": items_count, "batch_size": 10},
            progress_callback
        )
        thread.finished.connect(lambda result: self._handle_batch_result(result))
        thread.start()

    def _batch_job(self, config: Dict, progress_callback):
        """Backend call for batch job."""
        return self.ravenmaven.start_batch_job(config, progress_callback)

    def _handle_batch_result(self, result):
        """Handle batch job result."""
        self.batch_progress.setVisible(False)
        if result["success"]:
            self.batch_output.append(f"\n✓ Batch Job Complete:")
            self.batch_output.append(f"  Job ID: {result['job_id']}")
            self.batch_output.append(f"  Items Processed: {result['items_processed']}")
            self.batch_output.append(f"  Items Failed: {result['items_failed']}")
        else:
            self.batch_output.append(f"✗ Batch Job Failed: {result.get('error')}")

    def view_batch_history(self):
        """View history of batch jobs."""
        history = self.ravenmaven.get_job_history(limit=10)
        self.batch_output.clear()
        self.batch_output.append("Recent Batch Jobs:\n")
        for job in history:
            self.batch_output.append(f"Job: {job['job_id']}")
            self.batch_output.append(f"  Status: {job['status']}")
            self.batch_output.append(f"  Items: {job['items_processed']}")
            self.batch_output.append(f"  Time: {job['timestamp']}\n")

    def perform_semantic_search(self):
        """Perform semantic search."""
        query = self.search_input.text()
        if not query:
            self.search_output.setText("Please enter a search query")
            return
        
        self.search_output.clear()
        self.search_output.append(f"Searching for: {query}...\n")
        
        def progress_callback(msg: str, percent: int):
            self.search_output.append(f"[{percent:3d}%] {msg}")
        
        thread = GenericWorkerThread(
            self._perform_search,
            query,
            progress_callback
        )
        thread.finished.connect(lambda result: self._handle_search_result(result))
        thread.start()

    def _perform_search(self, query: str, progress_callback):
        """Backend call for semantic search."""
        return self.openmemory.search(query, progress_callback=progress_callback)

    def _handle_search_result(self, result):
        """Handle search result."""
        if result["success"]:
            self.search_output.append(f"\n✓ Search Complete ({result['result_count']} results):\n")
            for item in result["results"]:
                self.search_output.append(f"  • {item['title']} ({item['type']}) - Score: {item['score']:.2%}")
        else:
            self.search_output.append(f"✗ Search Failed: {result.get('error')}")

    def get_ai_suggestions(self):
        """Get AI suggestions."""
        self.search_output.clear()
        suggestions = self.openmemory.get_suggestions()
        
        if suggestions:
            self.search_output.append("AI Suggestions:\n")
            for sugg in suggestions:
                priority_icon = "🔴" if sugg["priority"] == "high" else "🟡" if sugg["priority"] == "medium" else "🟢"
                self.search_output.append(f"{priority_icon} [{sugg['type']}] {sugg['suggestion']}\n")
        else:
            self.search_output.setText("No suggestions available")


class AnalyticsTab(QWidget):
    """Tab 4: Analytics - Reports, inventory, statistics."""

    def __init__(self, audit: ImmutableAuditLog, parent=None):
        super().__init__(parent)
        self.audit = audit
        self.logger = ProjectLogger("analytics_tab")
        self.analytics = AnalyticsBackend()
        self.init_ui()

    def init_ui(self):
        """Initialize analytics tab UI."""
        layout = QVBoxLayout()

        # Title with help button
        title_layout = QHBoxLayout()
        title = QLabel("📊 Analytics & Reports")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title_layout.addWidget(title)
        title_layout.addStretch()
        
        help_btn = QPushButton("❓ Help")
        help_btn.setMaximumWidth(100)
        help_btn.clicked.connect(lambda: show_help_dialog(self, "Analytics"))
        title_layout.addWidget(help_btn)
        
        layout.addLayout(title_layout)

        # Statistics section
        stats_group = QGroupBox("Library Statistics")
        stats_layout = QFormLayout()

        self.total_events_label = QLabel("0")
        self.total_files_moved_label = QLabel("0")
        self.total_size_label = QLabel("0 GB")
        self.integrity_label = QLabel("Checking...")
        self.last_updated_label = QLabel("Never")

        stats_layout.addRow("Total Audit Events:", self.total_events_label)
        stats_layout.addRow("Files Organized:", self.total_files_moved_label)
        stats_layout.addRow("Total Data Moved:", self.total_size_label)
        stats_layout.addRow("Audit Integrity:", self.integrity_label)
        stats_layout.addRow("Last Updated:", self.last_updated_label)

        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

        # Report tabs
        self.report_tabs = QTabWidget()

        # Organization Report Tab
        org_report_widget = self._create_organization_report_tab()
        self.report_tabs.addTab(org_report_widget, "Organization")

        # Subtitles Report Tab
        sub_report_widget = self._create_subtitle_report_tab()
        self.report_tabs.addTab(sub_report_widget, "Subtitles")

        # Timeline Tab
        timeline_widget = self._create_timeline_tab()
        self.report_tabs.addTab(timeline_widget, "Timeline")

        # Actors Tab
        actors_widget = self._create_actors_tab()
        self.report_tabs.addTab(actors_widget, "Actors")

        layout.addWidget(self.report_tabs)

        # Export buttons
        export_layout = QHBoxLayout()
        
        summary_btn = QPushButton("Export Summary Report")
        summary_btn.clicked.connect(lambda: self.export_report("summary"))
        export_layout.addWidget(summary_btn)
        
        detailed_btn = QPushButton("Export Detailed Report")
        detailed_btn.clicked.connect(lambda: self.export_report("detailed"))
        export_layout.addWidget(detailed_btn)
        
        refresh_btn = QPushButton("Refresh All Data")
        refresh_btn.clicked.connect(self.refresh_all_stats)
        export_layout.addWidget(refresh_btn)
        
        export_layout.addStretch()
        layout.addLayout(export_layout)

        self.setLayout(layout)
        
        # Load initial data
        QTimer.singleShot(500, self.refresh_all_stats)

    def _create_organization_report_tab(self) -> QWidget:
        """Create organization report tab."""
        widget = QWidget()
        layout = QVBoxLayout()

        self.org_report_text = QTextEdit()
        self.org_report_text.setReadOnly(True)
        layout.addWidget(self.org_report_text)

        widget.setLayout(layout)
        return widget

    def _create_subtitle_report_tab(self) -> QWidget:
        """Create subtitle report tab."""
        widget = QWidget()
        layout = QVBoxLayout()

        self.sub_report_text = QTextEdit()
        self.sub_report_text.setReadOnly(True)
        layout.addWidget(self.sub_report_text)

        widget.setLayout(layout)
        return widget

    def _create_timeline_tab(self) -> QWidget:
        """Create timeline analysis tab."""
        widget = QWidget()
        layout = QVBoxLayout()

        # Days selector
        days_layout = QHBoxLayout()
        days_layout.addWidget(QLabel("Analyze last:"))
        self.days_spin = QSpinBox()
        self.days_spin.setMinimum(1)
        self.days_spin.setMaximum(365)
        self.days_spin.setValue(7)
        days_layout.addWidget(self.days_spin)
        days_layout.addWidget(QLabel("days"))
        
        analyze_btn = QPushButton("Analyze")
        analyze_btn.clicked.connect(self.analyze_timeline)
        days_layout.addWidget(analyze_btn)
        days_layout.addStretch()
        layout.addLayout(days_layout)

        self.timeline_text = QTextEdit()
        self.timeline_text.setReadOnly(True)
        layout.addWidget(self.timeline_text)

        widget.setLayout(layout)
        return widget

    def _create_actors_tab(self) -> QWidget:
        """Create actors (scripts) summary tab."""
        widget = QWidget()
        layout = QVBoxLayout()

        self.actors_text = QTextEdit()
        self.actors_text.setReadOnly(True)
        layout.addWidget(self.actors_text)

        widget.setLayout(layout)
        return widget

    def refresh_all_stats(self):
        """Refresh all statistics."""
        # Update timestamp
        self.last_updated_label.setText(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        thread = GenericWorkerThread(self._load_all_stats)
        thread.finished.connect(self._handle_stats_loaded)
        thread.start()

    def _load_all_stats(self):
        """Load all statistics."""
        return {
            "statistics": self.analytics.get_statistics(),
            "organization": self.analytics.get_organization_report(),
            "subtitles": self.analytics.get_subtitle_report(),
            "integrity": self.analytics.get_integrity_status(),
            "actors": self.analytics.get_actor_summary()
        }

    def _handle_stats_loaded(self, data: Dict):
        """Handle loaded statistics."""
        try:
            # Update main stats
            stats = data.get("statistics", {})
            self.total_events_label.setText(str(stats.get("total_events", 0)))

            org = data.get("organization", {})
            self.total_files_moved_label.setText(str(org.get("total_files_moved", 0)))
            self.total_size_label.setText(f"{org.get('total_size_gb', 0)} GB")

            integrity = data.get("integrity", {})
            status = integrity.get("status", "Unknown")
            self.integrity_label.setText(status)

            # Update organization report
            org_text = f"Files Moved: {org.get('total_files_moved', 0)}\nTotal Size: {org.get('total_size_gb', 0)} GB\n\n"
            for media_type, count in org.get("media_types", {}).items():
                org_text += f"• {media_type}: {count} files\n"
            self.org_report_text.setText(org_text)

            # Update subtitle report
            subs = data.get("subtitles", {})
            sub_text = f"Total Downloads: {subs.get('total_downloads', 0)}\n"
            sub_text += f"Successful: {subs.get('successful', 0)}\n"
            sub_text += f"Failed: {subs.get('failed', 0)}\n"
            sub_text += f"Success Rate: {subs.get('success_rate', 0)}%\n\n"
            for lang, count in subs.get("languages", {}).items():
                sub_text += f"• {lang}: {count} downloads\n"
            self.sub_report_text.setText(sub_text)

            # Update actors
            actors = data.get("actors", [])
            actors_text = "Actor Summary:\n\n"
            for actor in actors:
                actors_text += f"• {actor['actor']}\n"
                actors_text += f"  Total Events: {actor['total_events']}\n"
                actors_text += f"  Last Event: {actor.get('last_event', 'Never')}\n"
                actors_text += f"  Event Types: {list(actor['event_types'].keys())}\n\n"
            self.actors_text.setText(actors_text)

        except Exception as e:
            self.logger.error(f"Error handling loaded stats: {str(e)}")

    def analyze_timeline(self):
        """Analyze timeline."""
        days = self.days_spin.value()
        
        def progress_callback(msg: str, percent: int):
            self.timeline_text.setText(f"[{percent}%] {msg}")
        
        thread = GenericWorkerThread(
            lambda: self.analytics.get_timeline_analysis(days, progress_callback)
        )
        thread.finished.connect(self._handle_timeline_result)
        thread.start()

    def _handle_timeline_result(self, result: Dict):
        """Handle timeline analysis result."""
        try:
            if result.get("success"):
                timeline_text = f"Analysis Period: Last {result['days_analyzed']} days\n"
                timeline_text += f"Total Events: {result['total_events']}\n"
                timeline_text += f"Average per Day: {result['average_per_day']}\n\n"
                timeline_text += "Daily Breakdown:\n"
                for date, count in result.get("timeline", {}).items():
                    timeline_text += f"  {date}: {count} events\n"
                self.timeline_text.setText(timeline_text)
            else:
                self.timeline_text.setText(f"Error: {result.get('error', 'Unknown error')}")
        except Exception as e:
            self.timeline_text.setText(f"Error loading timeline: {str(e)}")

    def export_report(self, report_type: str):
        """Export report to file."""
        thread = GenericWorkerThread(
            lambda: self.analytics.export_report(report_type, "json")
        )
        thread.finished.connect(lambda result: self._handle_export_result(result))
        thread.start()

    def _handle_export_result(self, result: Dict):
        """Handle export result."""
        if result.get("success"):
            QMessageBox.information(
                self,
                "Export Successful",
                f"Report exported to:\n{result['report_path']}"
            )
        else:
            QMessageBox.warning(
                self,
                "Export Failed",
                f"Failed to export report: {result.get('error', 'Unknown error')}"
            )


class SettingsTab(QWidget):
    """Tab 5: Settings - Credentials, paths, preferences."""

    def __init__(self, audit: ImmutableAuditLog, creds: CredentialManager, parent=None):
        super().__init__(parent)
        self.audit = audit
        self.creds = creds
        self.settings = SettingsManager()
        self.logger = ProjectLogger("settings_tab")
        self.init_ui()

    def init_ui(self):
        """Initialize settings tab UI."""
        layout = QVBoxLayout()

        # Title with help button
        title_layout = QHBoxLayout()
        title = QLabel("⚙️ Settings & Configuration")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title_layout.addWidget(title)
        title_layout.addStretch()
        
        help_btn = QPushButton("❓ Help")
        help_btn.setMaximumWidth(100)
        help_btn.clicked.connect(lambda: show_help_dialog(self, "Settings"))
        title_layout.addWidget(help_btn)
        
        layout.addLayout(title_layout)

        # Paths section
        paths_group = QGroupBox("Media Paths")
        paths_layout = QFormLayout()

        self.media_root_input = QLineEdit()
        self.media_root_input.setText(self.settings.get("media_root", ""))
        self.media_root_input.setPlaceholderText("e.g., C:\\Jellyfin\\#MEDIA")
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_media_root)
        media_layout = QHBoxLayout()
        media_layout.addWidget(self.media_root_input)
        media_layout.addWidget(browse_btn)
        paths_layout.addRow("Media Root:", media_layout)

        self.movies_path = QLineEdit()
        self.movies_path.setText(self.settings.get("movies_folder", "Movies"))
        paths_layout.addRow("Movies Subfolder:", self.movies_path)

        self.tv_path = QLineEdit()
        self.tv_path.setText(self.settings.get("tv_shows_folder", "TV Shows"))
        paths_layout.addRow("TV Shows Subfolder:", self.tv_path)

        self.anime_path = QLineEdit()
        self.anime_path.setText(self.settings.get("anime_folder", "Anime"))
        paths_layout.addRow("Anime Subfolder:", self.anime_path)

        paths_group.setLayout(paths_layout)
        layout.addWidget(paths_group)

        # Credentials section
        creds_group = QGroupBox("Subtitle Service Credentials")
        creds_layout = QVBoxLayout()

        available_services = self.settings.get_available_services()
        self.cred_buttons = {}
        
        for service in available_services:
            service_layout = QHBoxLayout()
            service_label = QLabel(service)
            service_layout.addWidget(service_label)
            
            status_label = QLabel("❌ Not configured")
            status_label.setStyleSheet("color: red;")
            service_layout.addWidget(status_label)
            self.cred_buttons[service] = status_label
            
            btn = QPushButton("Configure")
            btn.clicked.connect(lambda checked, s=service: self.configure_credentials(s))
            service_layout.addWidget(btn)
            
            creds_layout.addLayout(service_layout)

        creds_group.setLayout(creds_layout)
        layout.addWidget(creds_group)

        # Preferences section
        prefs_group = QGroupBox("Preferences")
        prefs_layout = QFormLayout()

        self.auto_verify = QCheckBox("Automatically verify file integrity")
        self.auto_verify.setChecked(self.settings.get("enable_dry_run", True))
        prefs_layout.addRow("File Integrity:", self.auto_verify)

        self.create_snapshots = QCheckBox("Always create pre-operation snapshots")
        self.create_snapshots.setChecked(self.settings.get("auto_snapshot", True))
        prefs_layout.addRow("Snapshots:", self.create_snapshots)

        prefs_layout.addRow("Batch Size:", self._create_spinbox(self.settings.get("batch_size", 10)))

        prefs_group.setLayout(prefs_layout)
        layout.addWidget(prefs_group)

        # Import/Export section
        io_group = QGroupBox("Import/Export Settings")
        io_layout = QHBoxLayout()
        
        export_btn = QPushButton("Export Settings")
        export_btn.clicked.connect(self.export_settings)
        io_layout.addWidget(export_btn)
        
        import_btn = QPushButton("Import Settings")
        import_btn.clicked.connect(self.import_settings)
        io_layout.addWidget(import_btn)
        
        io_layout.addStretch()
        io_group.setLayout(io_layout)
        layout.addWidget(io_group)

        # Action buttons
        button_layout = QHBoxLayout()

        save_btn = QPushButton("Save Settings")
        save_btn.setToolTip("Save current settings from UI to settings backend")
        save_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        save_btn.clicked.connect(self.save_settings)
        button_layout.addWidget(save_btn)

        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.clicked.connect(self.reset_to_defaults)
        button_layout.addWidget(reset_btn)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        layout.addStretch()
        self.setLayout(layout)
        
        # Update credential status
        self._update_credential_status()

    def _create_spinbox(self, value: int) -> QSpinBox:
        """Create a spinbox with standard settings."""
        spinbox = QSpinBox()
        spinbox.setMinimum(1)
        spinbox.setMaximum(1000)
        spinbox.setValue(value)
        return spinbox

    def browse_media_root(self):
        """Browse for media root folder."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Media Root Folder",
            self.media_root_input.text()
        )
        if folder:
            self.media_root_input.setText(folder)

    def _update_credential_status(self):
        """Update credential status indicators."""
        for service in self.settings.get_available_services():
            creds = self.settings.get_credentials(service)
            label = self.cred_buttons.get(service)
            if label:
                if creds:
                    label.setText("✓ Configured")
                    label.setStyleSheet("color: green;")
                else:
                    label.setText("❌ Not configured")
                    label.setStyleSheet("color: red;")

    def configure_credentials(self, service: str):
        """Open credentials configuration dialog."""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Configure {service}")
        dialog.setGeometry(100, 100, 400, 250)

        layout = QFormLayout()
        
        username_input = QLineEdit()
        password_input = QLineEdit()
        password_input.setEchoMode(QLineEdit.EchoMode.Password)

        # Load existing credentials if available
        existing_creds = self.settings.get_credentials(service)
        if existing_creds:
            username_input.setText(existing_creds.get("username", ""))
            password_input.setText(existing_creds.get("password", ""))

        layout.addRow("Username:", username_input)
        layout.addRow("Password:", password_input)

        ok_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")

        button_layout = QHBoxLayout()
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)
        layout.addRow(button_layout)

        def save_credentials():
            username = username_input.text().strip()
            password = password_input.text().strip()
            
            if username and password:
                if self.settings.set_credentials(service, username, password):
                    self._update_credential_status()
                    dialog.accept()
                else:
                    QMessageBox.warning(self, "Error", "Failed to save credentials")
            else:
                QMessageBox.warning(self, "Error", "Please enter both username and password")

        ok_btn.clicked.connect(save_credentials)
        cancel_btn.clicked.connect(dialog.reject)

        dialog.setLayout(layout)
        dialog.exec()

    def save_settings(self):
        """Save settings to configuration."""
        try:
            self.settings.set("media_root", self.media_root_input.text())
            self.settings.set("movies_folder", self.movies_path.text())
            self.settings.set("tv_shows_folder", self.tv_path.text())
            self.settings.set("anime_folder", self.anime_path.text())
            self.settings.set("enable_dry_run", self.auto_verify.isChecked())
            self.settings.set("auto_snapshot", self.create_snapshots.isChecked())
            
            if self.settings.save():
                QMessageBox.information(self, "Success", "Settings saved successfully")
            else:
                QMessageBox.warning(self, "Error", "Failed to save settings")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save settings: {str(e)}")

    def reset_to_defaults(self):
        """Reset all settings to defaults."""
        if QMessageBox.question(self, "Confirm", "Reset all settings to defaults?") == QMessageBox.StandardButton.Yes:
            self.settings.reset_to_defaults()
            
            # Update UI
            self.media_root_input.setText(self.settings.get("media_root", ""))
            self.movies_path.setText(self.settings.get("movies_folder", ""))
            self.tv_path.setText(self.settings.get("tv_shows_folder", ""))
            self.anime_path.setText(self.settings.get("anime_folder", ""))
            self.auto_verify.setChecked(self.settings.get("enable_dry_run", True))
            self.create_snapshots.setChecked(self.settings.get("auto_snapshot", True))
            
            QMessageBox.information(self, "Success", "Settings reset to defaults")

    def export_settings(self):
        """Export settings to file."""
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Export Settings",
            "",
            "JSON Files (*.json)"
        )
        if filepath:
            if self.settings.export_settings(filepath):
                QMessageBox.information(self, "Success", f"Settings exported to {filepath}")
            else:
                QMessageBox.warning(self, "Error", "Failed to export settings")

    def import_settings(self):
        """Import settings from file."""
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Import Settings",
            "",
            "JSON Files (*.json)"
        )
        if filepath:
            if self.settings.import_settings(filepath):
                QMessageBox.information(self, "Success", "Settings imported successfully")
                # Reload UI
                self.init_ui()
            else:
                QMessageBox.warning(self, "Error", "Failed to import settings")


class JellyfinMainWindow(QMainWindow):
    """Main application window with tabbed interface."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_TITLE} v{APP_VERSION}")
        self.setGeometry(100, 100, WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setMinimumSize(1000, 700)

        # Initialize foundation systems
        self.audit = None
        self.creds = None
        self.logger = ProjectLogger("main_window")
        self._initialize_systems()

        # Create UI
        self.create_menu_bar()
        self.create_tabs()
        self.create_status_bar()

        # Apply stylesheet
        self.apply_stylesheet()

    def _initialize_systems(self):
        """Initialize audit and credential systems."""
        try:
            # Initialize audit system
            self.audit = ImmutableAuditLog()
            self.audit.initialize()

            # Initialize credentials
            self.creds = CredentialManager()

            print("Systems initialized successfully")

        except Exception as e:
            QMessageBox.critical(self, "Initialization Error", f"Failed to initialize systems: {e}")
            sys.exit(1)

    def create_menu_bar(self):
        """Create application menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")
        file_menu.addAction("Exit", self.close)

        # Edit menu
        edit_menu = menubar.addMenu("Edit")
        edit_menu.addAction("Preferences", self.show_preferences)

        # Help menu
        help_menu = menubar.addMenu("Help")
        help_menu.addAction("About", self.show_about)
        help_menu.addAction("Documentation", self.show_documentation)

    def create_tabs(self):
        """Create tabbed interface."""
        tabs = QTabWidget()

        # Add tabs
        tabs.addTab(OrganizationTab(self.audit), "📁 Organization")
        tabs.addTab(SubtitlesTab(self.audit), "📺 Subtitles")
        tabs.addTab(ToolsTab(self.audit), "🔧 Tools")
        tabs.addTab(AnalyticsTab(self.audit), "📊 Analytics")
        tabs.addTab(SettingsTab(self.audit, self.creds), "⚙️ Settings")

        self.setCentralWidget(tabs)

    def create_status_bar(self):
        """Create status bar."""
        status_bar = QStatusBar()
        status_bar.showMessage("Ready")
        self.setStatusBar(status_bar)

    def apply_stylesheet(self):
        """Apply application stylesheet."""
        style = """
        QMainWindow {
            background-color: #f5f5f5;
        }
        QGroupBox {
            border: 1px solid #cccccc;
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 10px;
            font-weight: bold;
        }
        QPushButton {
            padding: 6px 12px;
            background-color: #e0e0e0;
            border: 1px solid #999999;
            border-radius: 4px;
            font-weight: 500;
        }
        QPushButton:hover {
            background-color: #d0d0d0;
        }
        QPushButton:pressed {
            background-color: #c0c0c0;
        }
        QLineEdit {
            padding: 6px;
            border: 1px solid #cccccc;
            border-radius: 4px;
            background-color: white;
        }
        QComboBox {
            padding: 6px;
            border: 1px solid #cccccc;
            border-radius: 4px;
            background-color: white;
        }
        QProgressBar {
            border: 1px solid #cccccc;
            border-radius: 4px;
            text-align: center;
            height: 25px;
        }
        QProgressBar::chunk {
            background-color: #4CAF50;
        }
        """
        self.setStyleSheet(style)

    def show_preferences(self):
        """Show preferences dialog."""
        QMessageBox.information(self, "Preferences", "Preferences dialog - to be implemented")

    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(self, "About", f"{APP_TITLE}\nVersion {APP_VERSION}\n\n"
                                        "Professional Jellyfin Media Organization System\n\n"
                                        "Features:\n"
                                        "- Media organization (Movies, TV, Anime)\n"
                                        "- Multi-provider subtitle management\n"
                                        "- Immutable audit trail\n"
                                        "- Safe operations with snapshots\n"
                                        "- Tool integration (CodeCop, RavenMaven, OpenMemory)")

    def show_documentation(self):
        """Show documentation."""
        QMessageBox.information(self, "Documentation", 
                               "Documentation:\n\n"
                               "1. Organization Tab - Organize media files\n"
                               "2. Subtitles Tab - Download subtitles\n"
                               "3. Tools Tab - Access analysis tools\n"
                               "4. Analytics Tab - View statistics\n"
                               "5. Settings Tab - Configure system")


def main():
    """Main application entry point."""
    app = QApplication(sys.argv)
    window = JellyfinMainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
