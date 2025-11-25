#!/usr/bin/env python3
"""
Subtitles View - Workflow Steps 8-9

Full implementation of subtitle coverage evaluation and download functionality.
Integrates with SubtitleCoverageAnalyzer and SubtitleBackend for real operations.

Step 8: Subtitle Coverage Evaluation
- Scans media files for embedded subtitles (via ffprobe)
- Detects external subtitle files (.srt, .ass, .ssa, .vtt)
- Reports coverage statistics and missing files

Step 9: Subtitle Acquisition
- Downloads subtitles from OpenSubtitles via subliminal
- Batch processing with rate limiting
- Dry-run mode for safe previewing
- Progress tracking and audit logging
"""

import logging
from pathlib import Path
from typing import Optional, List
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QGroupBox,
    QMessageBox,
    QProgressBar,
    QComboBox,
    QCheckBox,
    QSpinBox,
    QFormLayout,
    QFileDialog,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QSplitter,
)
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from scripts.core.project_manager import ProjectManager, Project
from scripts.core.roundup_manager import RoundUpManager
from scripts.media.subtitle_coverage_analyzer import SubtitleCoverageAnalyzer
from scripts.media.subtitle_downloader import SubtitleDownloader, SUBLIMINAL_AVAILABLE

logger = logging.getLogger(__name__)


class CoverageWorker(QThread):
    """Background worker for subtitle coverage analysis."""
    
    progress = pyqtSignal(str, int)  # message, percent
    finished = pyqtSignal(dict)  # statistics
    error = pyqtSignal(str)
    
    def __init__(self, folder_path: str, language: str = "eng"):
        super().__init__()
        self.folder_path = folder_path
        self.language = language
    
    def run(self):
        try:
            analyzer = SubtitleCoverageAnalyzer()
            
            def progress_callback(msg: str, pct: int):
                self.progress.emit(msg, pct)
            
            # Analyze folder
            self.progress.emit("Starting coverage analysis...", 0)
            stats = analyzer.analyze_folder(
                folder_path=self.folder_path,
                recursive=True,
                language_filter=self.language if self.language != "all" else None
            )
            
            # Add missing files list to stats
            stats['missing_files'] = analyzer.get_missing_subtitles_list()
            stats['ffprobe_available'] = analyzer.ffprobe_available
            
            self.finished.emit(stats)
            
        except Exception as e:
            logger.error(f"Coverage analysis failed: {e}", exc_info=True)
            self.error.emit(str(e))


class DownloadWorker(QThread):
    """Background worker for subtitle downloads."""
    
    progress = pyqtSignal(str, int)  # message, percent
    finished = pyqtSignal(dict)  # statistics
    error = pyqtSignal(str)
    
    def __init__(
        self,
        file_list: List[str],
        language: str = "English",
        dry_run: bool = True,
        batch_size: int = 5,
        batch_delay: int = 10
    ):
        super().__init__()
        self.file_list = file_list
        self.language = language
        self.dry_run = dry_run
        self.batch_size = batch_size
        self.batch_delay = batch_delay
    
    def run(self):
        try:
            downloader = SubtitleDownloader(
                batch_size=self.batch_size,
                batch_delay=self.batch_delay
            )
            
            def progress_callback(msg: str, pct: int):
                self.progress.emit(msg, pct)
            
            downloader.set_progress_callback(progress_callback)
            
            stats = downloader.download_subtitles(
                file_list=self.file_list,
                language=self.language,
                dry_run=self.dry_run
            )
            
            self.finished.emit(stats)
            
        except Exception as e:
            logger.error(f"Subtitle download failed: {e}", exc_info=True)
            self.error.emit(str(e))


class SubtitlesView(QWidget):
    """Full implementation of subtitle coverage and download workflow."""

    def __init__(self, project: Project, project_manager: ProjectManager, parent=None):
        """
        Initialize the SubtitlesView widget.
        
        Args:
            project: The current project/Round-Up containing media files
            project_manager: Manager for project operations
            parent: Parent widget
        """
        super().__init__(parent)
        try:
            self.project = project
            self.project_manager = project_manager
            
            # State
            self.coverage_stats = None
            self.missing_files: List[str] = []
            self.coverage_worker: Optional[CoverageWorker] = None
            self.download_worker: Optional[DownloadWorker] = None
            
            self._init_ui()
            self._load_from_roundup()
            
            logger.info("SubtitlesView initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize SubtitlesView: {e}", exc_info=True)
            QMessageBox.critical(self, "Initialization Error", f"Failed to initialize:\n\n{str(e)}")
            raise

    def _init_ui(self):
        """Build the full UI with coverage and download sections."""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Title
        title = QLabel("Subtitle Coverage & Downloads")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        main_layout.addWidget(title)
        
        # Subliminal status
        if not SUBLIMINAL_AVAILABLE:
            warning = QLabel("⚠️ subliminal library not installed. Downloads will be simulated.")
            warning.setStyleSheet("color: orange; font-weight: bold;")
            main_layout.addWidget(warning)

        # Splitter for coverage and download sections
        splitter = QSplitter(Qt.Orientation.Vertical)

        # === COVERAGE SECTION (Step 8) ===
        coverage_widget = QWidget()
        coverage_layout = QVBoxLayout(coverage_widget)
        coverage_layout.setContentsMargins(0, 0, 0, 0)
        
        coverage_group = QGroupBox("Step 8: Subtitle Coverage Evaluation")
        coverage_inner = QVBoxLayout()

        # Folder selection
        folder_layout = QHBoxLayout()
        folder_layout.addWidget(QLabel("Folder:"))
        self.folder_input = QLineEdit()
        self.folder_input.setPlaceholderText("Select folder or use Round-Up source folders...")
        folder_layout.addWidget(self.folder_input)
        
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_folder)
        folder_layout.addWidget(browse_btn)
        coverage_inner.addLayout(folder_layout)

        # Language filter
        lang_layout = QHBoxLayout()
        lang_layout.addWidget(QLabel("Language Filter:"))
        self.lang_filter = QComboBox()
        self.lang_filter.addItems(["eng (English)", "spa (Spanish)", "fra (French)", 
                                    "deu (German)", "por (Portuguese)", "all (Any)"])
        lang_layout.addWidget(self.lang_filter)
        lang_layout.addStretch()
        
        self.btn_check = QPushButton("🔍 Check Coverage")
        self.btn_check.clicked.connect(self._check_coverage)
        lang_layout.addWidget(self.btn_check)
        coverage_inner.addLayout(lang_layout)

        # Coverage results
        self.coverage_stats_label = QLabel("No coverage data yet. Click 'Check Coverage' to analyze.")
        self.coverage_stats_label.setStyleSheet("color: #888;")
        coverage_inner.addWidget(self.coverage_stats_label)

        # Missing files list
        coverage_inner.addWidget(QLabel("Files Missing Subtitles:"))
        self.missing_list = QListWidget()
        self.missing_list.setMaximumHeight(150)
        coverage_inner.addWidget(self.missing_list)

        coverage_group.setLayout(coverage_inner)
        coverage_layout.addWidget(coverage_group)
        splitter.addWidget(coverage_widget)

        # === DOWNLOAD SECTION (Step 9) ===
        download_widget = QWidget()
        download_layout = QVBoxLayout(download_widget)
        download_layout.setContentsMargins(0, 0, 0, 0)
        
        download_group = QGroupBox("Step 9: Subtitle Acquisition")
        download_inner = QVBoxLayout()

        # Options row
        options_layout = QFormLayout()
        
        self.download_lang = QComboBox()
        self.download_lang.addItems(["English", "Spanish", "French", "German", "Portuguese", "Italian"])
        options_layout.addRow("Download Language:", self.download_lang)
        
        self.dry_run_check = QCheckBox("Dry-run mode (preview only)")
        self.dry_run_check.setChecked(True)
        options_layout.addRow("Mode:", self.dry_run_check)
        
        batch_layout = QHBoxLayout()
        self.batch_size = QSpinBox()
        self.batch_size.setValue(5)
        self.batch_size.setRange(1, 50)
        batch_layout.addWidget(QLabel("Batch Size:"))
        batch_layout.addWidget(self.batch_size)
        
        self.batch_delay = QSpinBox()
        self.batch_delay.setValue(10)
        self.batch_delay.setRange(1, 60)
        self.batch_delay.setSuffix(" sec")
        batch_layout.addWidget(QLabel("Delay:"))
        batch_layout.addWidget(self.batch_delay)
        batch_layout.addStretch()
        options_layout.addRow("Rate Limiting:", batch_layout)
        
        download_inner.addLayout(options_layout)

        # Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        download_inner.addWidget(self.progress_bar)

        self.download_log = QTextEdit()
        self.download_log.setReadOnly(True)
        self.download_log.setPlaceholderText("Download progress and results will appear here...")
        self.download_log.setMaximumHeight(150)
        download_inner.addWidget(self.download_log)

        # Action buttons
        button_layout = QHBoxLayout()
        
        self.btn_download = QPushButton("📥 Download Missing Subtitles")
        self.btn_download.setEnabled(False)  # Enable after coverage check
        self.btn_download.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
        self.btn_download.clicked.connect(self._download_subtitles)
        button_layout.addWidget(self.btn_download)
        
        btn_clear = QPushButton("Clear Log")
        btn_clear.clicked.connect(self._clear_log)
        button_layout.addWidget(btn_clear)
        
        button_layout.addStretch()
        download_inner.addLayout(button_layout)

        download_group.setLayout(download_inner)
        download_layout.addWidget(download_group)
        splitter.addWidget(download_widget)

        main_layout.addWidget(splitter)

    def _load_from_roundup(self):
        """Load source folders from Round-Up if available."""
        try:
            if hasattr(self.project, 'roundup') and self.project.roundup:
                roundup = self.project.roundup
                # Get source folders from Round-Up config
                source_folders = roundup.config.get('source_folders', [])
                if source_folders:
                    # Use first source folder as default
                    self.folder_input.setText(str(source_folders[0]))
                    logger.info(f"Loaded source folder from Round-Up: {source_folders[0]}")
        except Exception as e:
            logger.warning(f"Could not load from Round-Up: {e}")

    def _browse_folder(self):
        """Open folder browser dialog."""
        folder = QFileDialog.getExistingDirectory(self, "Select Media Folder")
        if folder:
            self.folder_input.setText(folder)

    def _check_coverage(self):
        """Run subtitle coverage analysis."""
        folder = self.folder_input.text().strip()
        if not folder:
            QMessageBox.warning(self, "No Folder", "Please select a folder first.")
            return
        
        if not Path(folder).exists():
            QMessageBox.warning(self, "Invalid Folder", f"Folder not found:\n{folder}")
            return
        
        # Get language filter
        lang_text = self.lang_filter.currentText()
        lang_code = lang_text.split(" ")[0] if lang_text != "all (Any)" else "all"
        
        # Disable UI during analysis
        self.btn_check.setEnabled(False)
        self.btn_check.setText("Analyzing...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.missing_list.clear()
        
        # Start worker
        self.coverage_worker = CoverageWorker(folder, lang_code)
        self.coverage_worker.progress.connect(self._on_coverage_progress)
        self.coverage_worker.finished.connect(self._on_coverage_complete)
        self.coverage_worker.error.connect(self._on_coverage_error)
        self.coverage_worker.start()

    def _on_coverage_progress(self, message: str, percent: int):
        """Handle coverage progress update."""
        self.progress_bar.setValue(percent)
        self.coverage_stats_label.setText(message)

    def _on_coverage_complete(self, stats: dict):
        """Handle coverage analysis completion."""
        self.btn_check.setEnabled(True)
        self.btn_check.setText("🔍 Check Coverage")
        self.progress_bar.setVisible(False)
        
        self.coverage_stats = stats
        
        # Update stats label
        total = stats.get('total_files', 0)
        with_subs = stats.get('with_subtitles', 0)
        without_subs = stats.get('without_subtitles', 0)
        coverage_pct = stats.get('coverage_percent', 0)
        
        ffprobe_status = "✓ ffprobe available" if stats.get('ffprobe_available') else "⚠️ ffprobe not found (embedded detection disabled)"
        
        if coverage_pct >= 90:
            color = "green"
        elif coverage_pct >= 70:
            color = "orange"
        else:
            color = "red"
        
        self.coverage_stats_label.setText(
            f"<b style='color:{color}'>{coverage_pct:.1f}% coverage</b> — "
            f"{with_subs}/{total} files have subtitles, {without_subs} missing — "
            f"{ffprobe_status}"
        )
        
        # Populate missing files list
        self.missing_files = []
        missing = stats.get('missing_files', [])
        for item in missing:
            file_path = item.get('file_path', str(item)) if isinstance(item, dict) else str(item)
            self.missing_files.append(file_path)
            
            # Add to list widget with truncated display
            display_name = Path(file_path).name
            list_item = QListWidgetItem(display_name)
            list_item.setToolTip(file_path)
            self.missing_list.addItem(list_item)
        
        # Enable download button if there are missing files
        self.btn_download.setEnabled(len(self.missing_files) > 0)
        
        if len(self.missing_files) > 0:
            self._log(f"Found {len(self.missing_files)} files missing subtitles")
        else:
            self._log("All files have subtitles! ✓")
        
        logger.info(f"Coverage analysis complete: {coverage_pct:.1f}% ({with_subs}/{total})")

    def _on_coverage_error(self, error: str):
        """Handle coverage analysis error."""
        self.btn_check.setEnabled(True)
        self.btn_check.setText("🔍 Check Coverage")
        self.progress_bar.setVisible(False)
        
        self.coverage_stats_label.setText(f"<span style='color:red'>Error: {error}</span>")
        QMessageBox.critical(self, "Coverage Error", f"Coverage analysis failed:\n\n{error}")

    def _download_subtitles(self):
        """Download subtitles for missing files."""
        if not self.missing_files:
            QMessageBox.warning(self, "No Files", "No files need subtitles. Run coverage check first.")
            return
        
        # Confirmation
        dry_run = self.dry_run_check.isChecked()
        mode_text = "PREVIEW mode (no files modified)" if dry_run else "LIVE mode (files will be downloaded)"
        
        reply = QMessageBox.question(
            self, "Download Subtitles",
            f"Download subtitles for {len(self.missing_files)} files?\n\n"
            f"Language: {self.download_lang.currentText()}\n"
            f"Mode: {mode_text}\n"
            f"Batch: {self.batch_size.value()} files, {self.batch_delay.value()}s delay",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Disable UI during download
        self.btn_download.setEnabled(False)
        self.btn_download.setText("Downloading...")
        self.btn_check.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        self._log(f"\n{'='*50}")
        self._log(f"Starting subtitle download...")
        self._log(f"Files: {len(self.missing_files)}")
        self._log(f"Language: {self.download_lang.currentText()}")
        self._log(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
        self._log(f"{'='*50}\n")
        
        # Start worker
        self.download_worker = DownloadWorker(
            file_list=self.missing_files,
            language=self.download_lang.currentText(),
            dry_run=dry_run,
            batch_size=self.batch_size.value(),
            batch_delay=self.batch_delay.value()
        )
        self.download_worker.progress.connect(self._on_download_progress)
        self.download_worker.finished.connect(self._on_download_complete)
        self.download_worker.error.connect(self._on_download_error)
        self.download_worker.start()

    def _on_download_progress(self, message: str, percent: int):
        """Handle download progress update."""
        self.progress_bar.setValue(percent)
        self._log(message)

    def _on_download_complete(self, stats: dict):
        """Handle download completion."""
        self.btn_download.setEnabled(True)
        self.btn_download.setText("📥 Download Missing Subtitles")
        self.btn_check.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        success = stats.get('success', 0)
        failed = stats.get('failed', 0)
        skipped = stats.get('skipped', 0)
        total = stats.get('total', 0)
        success_rate = stats.get('success_rate', 0)
        
        self._log(f"\n{'='*50}")
        self._log(f"DOWNLOAD COMPLETE")
        self._log(f"{'='*50}")
        self._log(f"Total: {total}")
        self._log(f"Success: {success} ({success_rate:.1f}%)")
        self._log(f"Failed: {failed}")
        self._log(f"Skipped: {skipped}")
        
        if failed > 0:
            self._log(f"\nFailed downloads:")
            for result in stats.get('results', []):
                if result.get('status') == 'failed':
                    file_name = Path(result.get('file_path', '')).name
                    error = result.get('error', 'Unknown error')
                    self._log(f"  - {file_name}: {error}")
        
        # Show summary dialog
        QMessageBox.information(
            self, "Download Complete",
            f"Subtitle download finished!\n\n"
            f"Success: {success}/{total} ({success_rate:.1f}%)\n"
            f"Failed: {failed}\n"
            f"Skipped: {skipped}\n\n"
            f"{'Files were not modified (dry-run mode)' if self.dry_run_check.isChecked() else 'Subtitles saved alongside video files'}"
        )
        
        logger.info(f"Subtitle download complete: {success}/{total} successful")

    def _on_download_error(self, error: str):
        """Handle download error."""
        self.btn_download.setEnabled(True)
        self.btn_download.setText("📥 Download Missing Subtitles")
        self.btn_check.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        self._log(f"\n❌ ERROR: {error}")
        QMessageBox.critical(self, "Download Error", f"Subtitle download failed:\n\n{error}")

    def _log(self, message: str):
        """Append message to download log."""
        self.download_log.append(message)
        # Scroll to bottom
        scrollbar = self.download_log.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _clear_log(self):
        """Clear the download log."""
        self.download_log.clear()
