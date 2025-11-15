#!/usr/bin/env python3
"""
TMDB Cache Generator Dialog

Provides UI for searching TMDB and generating episode title caches.

Features:
- Show search with optional year and TMDB ID
- Results preview with metadata
- Cache generation with progress tracking
- Error handling and validation

Usage:
    from dialogs.tmdb_cache_dialog import TMDBCacheDialog
    
    dialog = TMDBCacheDialog(parent)
    if dialog.exec():
        # Cache was generated successfully
        pass
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any, List

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QListWidget, QListWidgetItem, QTextEdit,
    QProgressBar, QMessageBox, QGroupBox, QSpinBox,
    QFormLayout, QWidget, QSplitter
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "_common"))

from settings_backend import SettingsManager
from tmdb_backend import TMDBBackend, TMDBError
from logger import ProjectLogger


class TMDBSearchWorker(QThread):
    """Worker thread for TMDB search operations."""
    
    # Signals
    search_complete = pyqtSignal(list)  # List of search results
    search_error = pyqtSignal(str)  # Error message
    
    def __init__(self, tmdb: TMDBBackend, query: str, year: Optional[int] = None):
        super().__init__()
        self.tmdb = tmdb
        self.query = query
        self.year = year
    
    def run(self):
        """Execute the search."""
        try:
            results = self.tmdb.search_shows(self.query, year=self.year)
            self.search_complete.emit(results)
        except Exception as e:
            self.search_error.emit(str(e))


class TMDBCacheWorker(QThread):
    """Worker thread for cache generation."""
    
    # Signals
    progress_update = pyqtSignal(int, str)  # Progress percent, status message
    cache_complete = pyqtSignal(str)  # Cache file path
    cache_error = pyqtSignal(str)  # Error message
    
    def __init__(self, tmdb: TMDBBackend, tmdb_id: int, output_path: Path):
        super().__init__()
        self.tmdb = tmdb
        self.tmdb_id = tmdb_id
        self.output_path = output_path
    
    def run(self):
        """Execute cache generation."""
        try:
            def progress_callback(progress: int, status: str):
                self.progress_update.emit(progress, status)
            
            cache_path = self.tmdb.generate_cache(
                self.tmdb_id,
                self.output_path,
                progress_callback=progress_callback
            )
            self.cache_complete.emit(str(cache_path))
        except Exception as e:
            self.cache_error.emit(str(e))


class TMDBCacheDialog(QDialog):
    """Dialog for searching TMDB and generating episode caches."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = ProjectLogger("tmdb_cache_dialog")
        self.settings = SettingsManager()
        self.tmdb = TMDBBackend()
        
        # State
        self.search_results: List[Dict[str, Any]] = []
        self.selected_show: Optional[Dict[str, Any]] = None
        self.search_worker: Optional[TMDBSearchWorker] = None
        self.cache_worker: Optional[TMDBCacheWorker] = None
        
        self.init_ui()
        self.load_api_key()
    
    def init_ui(self):
        """Initialize the dialog UI."""
        self.setWindowTitle("TMDB Episode Cache Generator")
        self.setModal(True)
        self.resize(900, 700)
        
        layout = QVBoxLayout(self)
        
        # Search section
        search_group = self.create_search_section()
        layout.addWidget(search_group)
        
        # Splitter for results and preview
        splitter = QSplitter(Qt.Horizontal)
        
        # Results section
        results_widget = self.create_results_section()
        splitter.addWidget(results_widget)
        
        # Preview section
        preview_widget = self.create_preview_section()
        splitter.addWidget(preview_widget)
        
        splitter.setSizes([400, 500])
        layout.addWidget(splitter, stretch=1)
        
        # Progress section
        progress_group = self.create_progress_section()
        layout.addWidget(progress_group)
        
        # Buttons
        button_layout = self.create_button_section()
        layout.addLayout(button_layout)
    
    def create_search_section(self) -> QGroupBox:
        """Create the search input section."""
        group = QGroupBox("Search TMDB")
        layout = QFormLayout()
        
        # Show name
        self.show_name_input = QLineEdit()
        self.show_name_input.setPlaceholderText("Enter show name...")
        self.show_name_input.setToolTip("Execute TMDB search")
        self.show_name_input.returnPressed.connect(self.search_tmdb)
        layout.addRow("Show Name:", self.show_name_input)
        
        # Year (optional)
        self.year_input = QSpinBox()
        self.year_input.setRange(1900, 2100)
        self.year_input.setValue(0)
        self.year_input.setSpecialValueText("Any")
        layout.addRow("Year (optional):", self.year_input)
        
        # TMDB ID (optional, for direct lookup)
        self.tmdb_id_input = QLineEdit()
        self.tmdb_id_input.setPlaceholderText("Direct TMDB ID lookup...")
        layout.addRow("TMDB ID (optional):", self.tmdb_id_input)
        
        # Search button
        self.search_button = QPushButton("🔍 Search")
        self.search_button.setToolTip("Execute TMDB search")
        self.search_button.clicked.connect(self.search_tmdb)
        self.search_button.setFixedHeight(40)
        font = QFont()
        font.setPointSize(12)
        self.search_button.setFont(font)
        layout.addRow("", self.search_button)
        
        group.setLayout(layout)
        return group
    
    def create_results_section(self) -> QWidget:
        """Create the search results section."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        label = QLabel("Search Results:")
        label.setStyleSheet("font-weight: bold;")
        layout.addWidget(label)
        
        self.results_list = QListWidget()
        self.results_list.setToolTip("Handle result selection")
        self.results_list.itemClicked.connect(self.on_result_selected)
        layout.addWidget(self.results_list)
        
        return widget
    
    def create_preview_section(self) -> QWidget:
        """Create the show preview section."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        label = QLabel("Show Details:")
        label.setStyleSheet("font-weight: bold;")
        layout.addWidget(label)
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        layout.addWidget(self.preview_text)
        
        return widget
    
    def create_progress_section(self) -> QGroupBox:
        """Create the progress tracking section."""
        group = QGroupBox("Progress")
        layout = QVBoxLayout()
        
        self.progress_label = QLabel("Ready to search or generate cache")
        layout.addWidget(self.progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        group.setLayout(layout)
        return group
    
    def create_button_section(self) -> QHBoxLayout:
        """Create the dialog buttons."""
        layout = QHBoxLayout()
        
        layout.addStretch()
        
        self.generate_button = QPushButton("📥 Generate Cache")
        self.generate_button.setToolTip("Generate episode cache for selected show")
        self.generate_button.clicked.connect(self.generate_cache)
        self.generate_button.setEnabled(False)
        self.generate_button.setFixedHeight(40)
        font = QFont()
        font.setPointSize(11)
        self.generate_button.setFont(font)
        layout.addWidget(self.generate_button)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        self.cancel_button.setFixedHeight(40)
        layout.addWidget(self.cancel_button)
        
        return layout
    
    def load_api_key(self):
        """Load and validate TMDB API key."""
        api_key = self.settings.get_tmdb_api_key()
        
        if not api_key:
            QMessageBox.warning(
                self,
                "TMDB API Key Required",
                "No TMDB API key found. Please go to Settings → TMDB Configuration "
                "and enter your API key. You can get a free API key from "
                "https://www.themoviedb.org/settings/api"
            )
            self.search_button.setEnabled(False)
            return
        
        try:
            self.tmdb.set_api_key(api_key)
            if not self.tmdb.validate_api_key():
                QMessageBox.warning(
                    self,
                    "Invalid TMDB API Key",
                    "The TMDB API key is invalid or expired. Please check your API key "
                    "in Settings → TMDB Configuration. Make sure you're using a v3 API key "
                    "from https://www.themoviedb.org/settings/api"
                )
                self.search_button.setEnabled(False)
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Error validating API key: {str(e)}"
            )
            self.search_button.setEnabled(False)
    
    def search_tmdb(self):
        """Execute TMDB search."""
        # Get search parameters
        query = self.show_name_input.text().strip()
        tmdb_id = self.tmdb_id_input.text().strip()
        
        # If TMDB ID provided, do direct lookup
        if tmdb_id:
            try:
                show_id = int(tmdb_id)
                self.direct_lookup(show_id)
                return
            except ValueError:
                QMessageBox.warning(
                    self,
                    "Invalid ID",
                    "TMDB ID must be a number."
                )
                return
        
        # Otherwise need show name
        if not query:
            QMessageBox.warning(
                self,
                "No Query",
                "Please enter a show name to search."
            )
            return
        
        # Get optional year
        year = self.year_input.value() if self.year_input.value() > 0 else None
        
        # Disable UI during search
        self.search_button.setEnabled(False)
        self.generate_button.setEnabled(False)
        self.progress_label.setText(f"Searching for '{query}'...")
        self.progress_bar.setValue(0)
        
        # Create and start worker
        self.search_worker = TMDBSearchWorker(self.tmdb, query, year)
        self.search_worker.search_complete.connect(self.on_search_complete)
        self.search_worker.search_error.connect(self.on_search_error)
        self.search_worker.start()
    
    def direct_lookup(self, tmdb_id: int):
        """Look up show directly by TMDB ID."""
        self.search_button.setEnabled(False)
        self.generate_button.setEnabled(False)
        self.progress_label.setText(f"Looking up TMDB ID {tmdb_id}...")
        
        try:
            show = self.tmdb.get_show_details(tmdb_id)
            self.search_results = [show]
            self.populate_results()
            self.progress_label.setText(f"Found: {show.get('name', 'Unknown')}")
        except Exception as e:
            self.on_search_error(str(e))
        finally:
            self.search_button.setEnabled(True)
    
    def on_search_complete(self, results: List[Dict[str, Any]]):
        """Handle search completion."""
        self.search_results = results
        self.populate_results()
        
        count = len(results)
        self.progress_label.setText(f"Found {count} result{'s' if count != 1 else ''}")
        self.search_button.setEnabled(True)
        
        if count == 0:
            QMessageBox.information(
                self,
                "No Results",
                "No shows found. Try a different search term."
            )
    
    def on_search_error(self, error: str):
        """Handle search error."""
        self.progress_label.setText("Search failed")
        self.search_button.setEnabled(True)
        
        QMessageBox.critical(
            self,
            "Search Error",
            f"Error searching TMDB:\n{error}"
        )
        self.logger.error(f"TMDB search error: {error}")
    
    def populate_results(self):
        """Populate the results list."""
        self.results_list.clear()
        
        for show in self.search_results:
            name = show.get('name', 'Unknown')
            year = show.get('first_air_date', '')[:4] if show.get('first_air_date') else '????'
            tmdb_id = show.get('id', 0)
            
            item_text = f"{name} ({year}) - ID: {tmdb_id}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, show)
            self.results_list.addItem(item)
    
    def on_result_selected(self, item: QListWidgetItem):
        """Handle result selection."""
        self.selected_show = item.data(Qt.UserRole)
        self.display_preview()
        self.generate_button.setEnabled(True)
    
    def display_preview(self):
        """Display preview of selected show."""
        if not self.selected_show:
            return
        
        name = self.selected_show.get('name', 'Unknown')
        tmdb_id = self.selected_show.get('id', 0)
        first_air = self.selected_show.get('first_air_date', 'Unknown')
        overview = self.selected_show.get('overview', 'No description available')
        
        preview_html = f"""
        <h2>{name}</h2>
        <p><b>TMDB ID:</b> {tmdb_id}</p>
        <p><b>First Aired:</b> {first_air}</p>
        <h3>Overview</h3>
        <p>{overview}</p>
        """
        
        self.preview_text.setHtml(preview_html)
    
    def generate_cache(self):
        """Generate episode cache for selected show."""
        if not self.selected_show:
            return
        
        tmdb_id = self.selected_show.get('id')
        if not tmdb_id:
            QMessageBox.warning(
                self,
                "No ID",
                "Selected show has no TMDB ID."
            )
            return
        
        # Ask for output location
        from PyQt6.QtWidgets import QFileDialog
        media_root = self.settings.get("media_root", "")
        
        output_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Episode Cache",
            f"{media_root}/episode_cache_{tmdb_id}.json",
            "JSON Files (*.json)"
        )
        
        if not output_path:
            return  # User cancelled
        
        # Disable UI during generation
        self.search_button.setEnabled(False)
        self.generate_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_label.setText("Generating cache...")
        
        # Create and start worker
        self.cache_worker = TMDBCacheWorker(self.tmdb, tmdb_id, Path(output_path))
        self.cache_worker.progress_update.connect(self.on_cache_progress)
        self.cache_worker.cache_complete.connect(self.on_cache_complete)
        self.cache_worker.cache_error.connect(self.on_cache_error)
        self.cache_worker.start()
    
    def on_cache_progress(self, progress: int, status: str):
        """Handle cache generation progress."""
        self.progress_bar.setValue(progress)
        self.progress_label.setText(status)
    
    def on_cache_complete(self, cache_path: str):
        """Handle cache generation completion."""
        self.progress_bar.setValue(100)
        self.progress_label.setText(f"Cache generated: {cache_path}")
        
        QMessageBox.information(
            self,
            "Success",
            f"Episode cache generated successfully!\n\n{cache_path}"
        )
        
        self.logger.info(f"Cache generated: {cache_path}")
        self.accept()  # Close dialog with success
    
    def on_cache_error(self, error: str):
        """Handle cache generation error."""
        self.progress_label.setText("Cache generation failed")
        self.search_button.setEnabled(True)
        self.generate_button.setEnabled(True)
        
        QMessageBox.critical(
            self,
            "Generation Error",
            f"Error generating cache:\n{error}"
        )
        self.logger.error(f"Cache generation error: {error}")
    
    def closeEvent(self, event):
        """Handle dialog close."""
        # Cancel any running workers
        if self.search_worker and self.search_worker.isRunning():
            self.search_worker.terminate()
            self.search_worker.wait()
        
        if self.cache_worker and self.cache_worker.isRunning():
            self.cache_worker.terminate()
            self.cache_worker.wait()
        
        event.accept()


if __name__ == "__main__":
    """Test the dialog."""
    from PyQt6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    dialog = TMDBCacheDialog()
    dialog.show()
    sys.exit(app.exec())
