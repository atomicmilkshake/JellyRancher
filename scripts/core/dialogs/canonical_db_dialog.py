#!/usr/bin/env python3
"""
Canonical Database Builder Dialog

Provides UI for building canonical metadata databases from detected media files.

Features:
- File selection for LLM analysis JSON files
- Progress tracking during metadata lookup
- Results preview with success/failure counts
- Error handling and validation

Usage:
    from dialogs.canonical_db_dialog import CanonicalDBDialog

    dialog = CanonicalDBDialog(parent)
    if dialog.exec():
        # Database was built successfully
        pass
"""

import sys
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QListWidget, QListWidgetItem, QTextEdit,
    QProgressBar, QMessageBox, QGroupBox, QFormLayout,
    QWidget, QFileDialog
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "_common"))
sys.path.insert(0, str(Path(__file__).parent.parent / "media"))

from media_metadata_lookup import MediaMetadataLookup
from logger import ProjectLogger


class CanonicalDBWorker(QThread):
    """Worker thread for canonical database building."""

    # Signals
    progress_update = pyqtSignal(int, str)  # Progress percent, status message
    db_complete = pyqtSignal(dict)  # Database results
    db_error = pyqtSignal(str)  # Error message

    def __init__(self, analysis_file: Path, output_file: Optional[Path] = None):
        super().__init__()
        self.analysis_file = analysis_file
        self.output_file = output_file

    def run(self):
        """Execute canonical database building."""
        try:
            def progress_callback(current: int, total: int, item_name: str):
                progress = int((current / total) * 100) if total > 0 else 0
                status = f"Processing {current}/{total}: {item_name}"
                self.progress_update.emit(progress, status)

            # Load analysis file
            self.progress_update.emit(5, "Loading analysis file...")
            with open(self.analysis_file, 'r', encoding='utf-8') as f:
                analysis_data = json.load(f)

            detected_media = analysis_data.get('detected_media', [])
            if not detected_media:
                self.db_error.emit("No detected media found in analysis file")
                return

            # Initialize metadata lookup
            self.progress_update.emit(10, "Initializing metadata lookup service...")
            lookup = MediaMetadataLookup()

            # Build canonical database
            self.progress_update.emit(15, f"Building canonical database for {len(detected_media)} items...")

            # Override progress callback for more detailed updates
            original_build = lookup.build_canonical_database

            def build_with_progress(detected_media, output_path=None):
                total_items = len(detected_media)
                canonical_db = {
                    'timestamp': datetime.now().isoformat(),
                    'total_items': total_items,
                    'movies': [],
                    'tv_shows': [],
                    'lookup_failures': []
                }

                for i, item in enumerate(detected_media):
                    title = item.get('title', 'Unknown')
                    progress = 15 + int((i / total_items) * 70)
                    self.progress_update.emit(progress, f"Processing {i+1}/{total_items}: {title}")

                    media_type = item.get('type')
                    year_estimate = item.get('year_estimate')

                    if media_type == 'movie':
                        metadata = lookup.lookup_movie(title, year_estimate)
                        if metadata:
                            metadata['original_detection'] = item
                            canonical_db['movies'].append(metadata)
                        else:
                            canonical_db['lookup_failures'].append(item)
                    elif media_type == 'tv_show':
                        metadata = lookup.lookup_tv_show(title, year_estimate)
                        if metadata:
                            metadata['original_detection'] = item
                            canonical_db['tv_shows'].append(metadata)
                        else:
                            canonical_db['lookup_failures'].append(item)

                # Save if output path provided
                if output_path:
                    self.progress_update.emit(90, "Saving database...")
                    lookup.save_database(canonical_db, str(output_path))

                self.progress_update.emit(100, "Database build complete")
                return canonical_db

            # Build the database
            canonical_db = build_with_progress(detected_media, self.output_file)

            self.db_complete.emit(canonical_db)

        except Exception as e:
            self.db_error.emit(str(e))


class CanonicalDBDialog(QDialog):
    """Dialog for building canonical metadata databases."""

    def __init__(self, parent=None):
        super().__init__(parent)
        # Non-modal dialog (Phase 48-E-4: Modal banishment)
        self.setModal(False)
        self.logger = ProjectLogger("canonical_db_dialog")

        # State
        self.analysis_file: Optional[Path] = None
        self.canonical_db: Optional[Dict[str, Any]] = None
        self.worker: Optional[CanonicalDBWorker] = None

        self.init_ui()
    
    def _set_status(self, message: str, level: str = 'info'):
        """Show status message in parent window's status bar if available."""
        if self.parent() and hasattr(self.parent(), 'status_label'):
            if level == 'error':
                self.parent().status_label.setText(f"❌ {message}")
                self.parent().status_label.setStyleSheet("color: red;")
            elif level == 'warning':
                self.parent().status_label.setText(f"⚠ {message}")
                self.parent().status_label.setStyleSheet("color: orange;")
            else:
                self.parent().status_label.setText(f"ℹ {message}")
                self.parent().status_label.setStyleSheet("color: green;")
        if hasattr(self, 'logger'):
            self.logger.info(f"[{level.upper()}] {message}")

    def init_ui(self):
        """Initialize the dialog UI."""
        self.setWindowTitle("Canonical Database Builder")
        self.setModal(True)
        self.resize(800, 600)

        layout = QVBoxLayout(self)

        # File selection section
        file_group = self.create_file_section()
        layout.addWidget(file_group)

        # Progress section
        progress_group = self.create_progress_section()
        layout.addWidget(progress_group)

        # Results section
        results_group = self.create_results_section()
        layout.addWidget(results_group, stretch=1)

        # Buttons
        button_layout = self.create_button_section()
        layout.addLayout(button_layout)

    def create_file_section(self) -> QGroupBox:
        """Create the file selection section."""
        group = QGroupBox("Input File")
        layout = QFormLayout()

        # File path display
        self.file_path_label = QLabel("No file selected")
        self.file_path_label.setStyleSheet("font-weight: bold; color: #666;")
        layout.addRow("Analysis File:", self.file_path_label)

        # File selection button
        self.select_file_button = QPushButton("📁 Select Analysis File")
        self.select_file_button.setToolTip("Select JSON file with detected media from LLM analysis")
        self.select_file_button.clicked.connect(self.select_analysis_file)
        self.select_file_button.setFixedHeight(35)
        layout.addRow("", self.select_file_button)

        # File info
        self.file_info_label = QLabel(
            "Select a JSON file containing 'detected_media' array from LLM analysis.\n"
            "This will build a canonical database with accurate metadata from TMDB/OMDb."
        )
        self.file_info_label.setWordWrap(True)
        self.file_info_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addRow("", self.file_info_label)

        group.setLayout(layout)
        return group

    def create_progress_section(self) -> QGroupBox:
        """Create the progress tracking section."""
        group = QGroupBox("Progress")
        layout = QVBoxLayout()

        self.progress_label = QLabel("Select an analysis file to begin")
        layout.addWidget(self.progress_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        group.setLayout(layout)
        return group

    def create_results_section(self) -> QGroupBox:
        """Create the results display section."""
        group = QGroupBox("Results")
        layout = QVBoxLayout()

        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setPlaceholderText("Database build results will appear here...")
        layout.addWidget(self.results_text)

        group.setLayout(layout)
        return group

    def create_button_section(self) -> QHBoxLayout:
        """Create the dialog buttons."""
        layout = QHBoxLayout()

        layout.addStretch()

        self.build_button = QPushButton("🏗️ Build Database")
        self.build_button.setToolTip("Build canonical metadata database")
        self.build_button.clicked.connect(self.build_database)
        self.build_button.setEnabled(False)
        self.build_button.setFixedHeight(40)
        font = QFont()
        font.setPointSize(11)
        self.build_button.setFont(font)
        layout.addWidget(self.build_button)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        self.cancel_button.setFixedHeight(40)
        layout.addWidget(self.cancel_button)

        return layout

    def select_analysis_file(self):
        """Select analysis file containing detected media."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Analysis File",
            "",
            "JSON Files (*.json);;All Files (*)"
        )

        if file_path:
            self.analysis_file = Path(file_path)
            self.file_path_label.setText(str(self.analysis_file))

            # Try to load and validate the file
            try:
                with open(self.analysis_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                detected_media = data.get('detected_media', [])
                if detected_media:
                    self.file_info_label.setText(
                        f"✓ Found {len(detected_media)} detected media items\n"
                        "Ready to build canonical database."
                    )
                    self.build_button.setEnabled(True)
                    self.progress_label.setText(f"Ready to process {len(detected_media)} items")
                else:
                    self.file_info_label.setText(
                        "⚠ No 'detected_media' array found in file.\n"
                        "Please select a valid LLM analysis file."
                    )
                    self.build_button.setEnabled(False)

            except Exception as e:
                self.file_info_label.setText(f"❌ Error reading file: {str(e)}")
                self.build_button.setEnabled(False)
                self.logger.error(f"Error reading analysis file: {e}")

    def build_database(self):
        """Build the canonical database."""
        if not self.analysis_file:
            return

        # Ask for output location
        output_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Canonical Database",
            f"canonical_metadata_{self.analysis_file.stem}.json",
            "JSON Files (*.json)"
        )

        if not output_path:
            return  # User cancelled

        output_file = Path(output_path)

        # Disable UI during build
        self.select_file_button.setEnabled(False)
        self.build_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.results_text.clear()

        # Create and start worker
        self.worker = CanonicalDBWorker(self.analysis_file, output_file)
        self.worker.progress_update.connect(self.on_build_progress)
        self.worker.db_complete.connect(self.on_build_complete)
        self.worker.db_error.connect(self.on_build_error)
        self.worker.start()

    def on_build_progress(self, progress: int, status: str):
        """Handle build progress."""
        self.progress_bar.setValue(progress)
        self.progress_label.setText(status)

    def on_build_complete(self, canonical_db: Dict[str, Any]):
        """Handle database build completion."""
        self.canonical_db = canonical_db
        self.progress_bar.setValue(100)

        # Display results
        movies = len(canonical_db.get('movies', []))
        tv_shows = len(canonical_db.get('tv_shows', []))
        failures = len(canonical_db.get('lookup_failures', []))
        total = movies + tv_shows + failures

        results_html = f"""
        <h2>✅ Database Build Complete</h2>
        <p><b>Total Items Processed:</b> {total}</p>
        <p><b>✅ Movies:</b> {movies}</p>
        <p><b>✅ TV Shows:</b> {tv_shows}</p>
        <p><b>❌ Lookup Failures:</b> {failures}</p>
        <p><b>Success Rate:</b> {((movies + tv_shows) / total * 100):.1f}%</p>
        """

        if canonical_db.get('lookup_failures'):
            results_html += "<h3>Failed Lookups:</h3><ul>"
            for failure in canonical_db['lookup_failures'][:10]:  # Show first 10
                title = failure.get('title', 'Unknown')
                media_type = failure.get('type', 'unknown')
                results_html += f"<li>{title} ({media_type})</li>"
            if len(canonical_db['lookup_failures']) > 10:
                results_html += f"<li>... and {len(canonical_db['lookup_failures']) - 10} more</li>"
            results_html += "</ul>"

        self.results_text.setHtml(results_html)

        success_msg = f"Canonical database built successfully! Movies: {movies}, TV Shows: {tv_shows}, Failures: {failures}, Success Rate: {((movies + tv_shows) / total * 100):.1f}%"
        self._set_status(success_msg, level='info')

        self.logger.info(f"Canonical database built: {movies} movies, {tv_shows} TV shows, {failures} failures")
        self.accept()  # Close dialog with success

    def on_build_error(self, error: str):
        """Handle build error."""
        self.progress_label.setText("Database build failed")
        self.select_file_button.setEnabled(True)
        self.build_button.setEnabled(True)

        self.results_text.setHtml(f"<h2>❌ Build Failed</h2><p>Error: {error}</p>")

        self._set_status(f"Build Error: {error}", level='error')
        self.logger.error(f"Error building canonical database: {error}")
        self.logger.error(f"Canonical database build error: {error}")

    def closeEvent(self, event):
        """Handle dialog close."""
        # Cancel any running workers
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()

        event.accept()


if __name__ == "__main__":
    """Test the dialog."""
    from PyQt6.QtWidgets import QApplication
    import sys
    import json
    from datetime import datetime

    app = QApplication(sys.argv)
    dialog = CanonicalDBDialog()
    dialog.show()
    sys.exit(app.exec())
