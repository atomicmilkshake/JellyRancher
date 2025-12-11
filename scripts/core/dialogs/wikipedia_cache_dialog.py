#!/usr/bin/env python3
"""
Wikipedia Episode Cache Generator Dialog

Provides UI for searching Wikipedia and generating episode title caches.

Features:
- Show search with intelligent Wikipedia lookup
- Results preview with episode count and seasons
- Cache generation with progress tracking
- Error handling and validation

Usage:
    from dialogs.wikipedia_cache_dialog import WikipediaCacheDialog

    dialog = WikipediaCacheDialog(parent)
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
    QProgressBar, QMessageBox, QGroupBox, QFormLayout,
    QWidget, QSplitter
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "_common"))

from tv_episode_cache import TVEpisodeCache
from logger import ProjectLogger


class WikipediaSearchWorker(QThread):
    """Worker thread for Wikipedia search operations."""

    # Signals
    search_complete = pyqtSignal(dict)  # Episode data
    search_error = pyqtSignal(str)  # Error message

    def __init__(self, cache: TVEpisodeCache, query: str):
        super().__init__()
        self.cache = cache
        self.query = query

    def run(self):
        """Execute the search."""
        try:
            result = self.cache.fetch_wikipedia_episodes(self.query)
            self.search_complete.emit(result or {})
        except Exception as e:
            self.search_error.emit(str(e))


class WikipediaCacheWorker(QThread):
    """Worker thread for cache generation."""

    # Signals
    progress_update = pyqtSignal(int, str)  # Progress percent, status message
    cache_complete = pyqtSignal(str)  # Cache file path
    cache_error = pyqtSignal(str)  # Error message

    def __init__(self, cache: TVEpisodeCache, show_title: str, output_path: Path):
        super().__init__()
        self.cache = cache
        self.show_title = show_title
        self.output_path = output_path

    def run(self):
        """Execute cache generation."""
        try:
            def progress_callback(progress: int, status: str):
                self.progress_update.emit(progress, status)

            # Fetch episode data
            progress_callback(10, "Searching Wikipedia...")
            episode_data = self.cache.fetch_wikipedia_episodes(self.show_title)

            if not episode_data:
                self.cache_error.emit("No episode data found on Wikipedia")
                return

            # Save to cache
            progress_callback(50, "Saving episode cache...")
            self.cache.save_episode_data(self.show_title, episode_data)

            # Get cache path for confirmation
            show_id = self.cache.get_show_id(self.show_title)
            cache_path = self.cache.get_cache_path(show_id)

            progress_callback(100, f"Cache saved: {cache_path}")
            self.cache_complete.emit(str(cache_path))

        except Exception as e:
            self.cache_error.emit(str(e))


class WikipediaCacheDialog(QDialog):
    """Dialog for searching Wikipedia and generating episode caches."""

    def __init__(self, parent=None):
        super().__init__(parent)
        # Non-modal dialog (Phase 48-E-4: Modal banishment)
        self.setModal(False)
        self.logger = ProjectLogger("wikipedia_cache_dialog")
        self.cache = TVEpisodeCache()

        # State
        self.episode_data: Optional[Dict[str, Any]] = None
        self.search_worker: Optional[WikipediaSearchWorker] = None
        self.cache_worker: Optional[WikipediaCacheWorker] = None

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
        self.setWindowTitle("Wikipedia Episode Cache Generator")
        self.setModal(False)  # Non-modal (Phase 48-E-4: Modal banishment)
        self.resize(900, 560)

        layout = QVBoxLayout(self)

        # Search section
        search_group = self.create_search_section()
        layout.addWidget(search_group)

        # Splitter for results and preview
        splitter = QSplitter(Qt.Orientation.Horizontal)

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
        group = QGroupBox("Search Wikipedia")
        layout = QFormLayout()

        # Show name
        self.show_name_input = QLineEdit()
        self.show_name_input.setPlaceholderText("Enter TV show name...")
        self.show_name_input.setToolTip("Search Wikipedia for TV show episodes")
        self.show_name_input.returnPressed.connect(self.search_wikipedia)
        layout.addRow("TV Show Name:", self.show_name_input)

        # Search button
        self.search_button = QPushButton("🔍 Search Wikipedia")
        self.search_button.setToolTip("Search Wikipedia for episode data")
        self.search_button.clicked.connect(self.search_wikipedia)
        self.search_button.setFixedHeight(32)
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
        self.results_list.setToolTip("Select a show to preview episode data")
        self.results_list.itemClicked.connect(self.on_result_selected)
        layout.addWidget(self.results_list)

        return widget

    def create_preview_section(self) -> QWidget:
        """Create the episode data preview section."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        label = QLabel("Episode Data Preview:")
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

        self.progress_label = QLabel("Ready to search Wikipedia")
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
        self.generate_button.setToolTip(
            "Generate episode cache from Wikipedia data.\n\n"
            "This button is disabled until you:\n"
            "1. Search Wikipedia for a TV show\n"
            "2. Select a result from the search results list\n\n"
            "Once enabled, clicking will save episode data to the cache."
        )
        self.generate_button.clicked.connect(self.generate_cache)
        self.generate_button.setEnabled(False)
        self.generate_button.setFixedHeight(32)
        font = QFont()
        font.setPointSize(11)
        self.generate_button.setFont(font)
        layout.addWidget(self.generate_button)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        self.cancel_button.setFixedHeight(32)
        layout.addWidget(self.cancel_button)

        return layout

    def search_wikipedia(self):
        """Execute Wikipedia search."""
        query = self.show_name_input.text().strip()

        if not query:
            self._set_status("No Query: Please enter a TV show name to search.", level='warning')
            return

        # Disable UI during search
        self.search_button.setEnabled(False)
        self.generate_button.setEnabled(False)
        self.progress_label.setText(f"Searching Wikipedia for '{query}'...")
        self.progress_bar.setValue(0)

        # Clear previous results
        self.results_list.clear()
        self.preview_text.clear()
        self.episode_data = None

        # Create and start worker
        self.search_worker = WikipediaSearchWorker(self.cache, query)
        self.search_worker.search_complete.connect(self.on_search_complete)
        self.search_worker.search_error.connect(self.on_search_error)
        self.search_worker.start()

    def on_search_complete(self, episode_data: Dict[str, Any]):
        """Handle search completion."""
        self.episode_data = episode_data
        self.populate_results()

        if episode_data:
            show_name = episode_data.get('show_name', 'Unknown')
            seasons = len(episode_data.get('seasons', {}))
            total_episodes = sum(len(season.get('episodes', {})) for season in episode_data.get('seasons', {}).values())

            self.progress_label.setText(f"Found: {show_name} - {seasons} seasons, {total_episodes} episodes")
        else:
            self.progress_label.setText("No episode data found")

        self.search_button.setEnabled(True)

    def on_search_error(self, error: str):
        """Handle search error."""
        self.progress_label.setText("Search failed")
        self.search_button.setEnabled(True)

        self._set_status(f"Search Error: Error searching Wikipedia: {error}", level='error')
        self.logger.error(f"Error searching Wikipedia: {error}", exc_info=True)
        self.logger.error(f"Wikipedia search error: {error}")

    def populate_results(self):
        """Populate the results list."""
        self.results_list.clear()

        if not self.episode_data:
            item = QListWidgetItem("No episode data found")
            item.setData(Qt.UserRole, None)
            self.results_list.addItem(item)
            return

        show_name = self.episode_data.get('show_name', 'Unknown Show')
        seasons = len(self.episode_data.get('seasons', {}))
        total_episodes = sum(len(season.get('episodes', {})) for season in self.episode_data.get('seasons', {}).values())

        item_text = f"{show_name} - {seasons} seasons, {total_episodes} episodes"
        item = QListWidgetItem(item_text)
        item.setData(Qt.UserRole, self.episode_data)
        self.results_list.addItem(item)

    def on_result_selected(self, item: QListWidgetItem):
        """Handle result selection."""
        data = item.data(Qt.UserRole)
        if data:
            self.episode_data = data
            self.display_preview()
            self.generate_button.setEnabled(True)
        else:
            self.generate_button.setEnabled(False)

    def display_preview(self):
        """Display preview of episode data."""
        if not self.episode_data:
            return

        show_name = self.episode_data.get('show_name', 'Unknown')
        seasons = self.episode_data.get('seasons', {})

        preview_html = f"""
        <h2>{show_name}</h2>
        <p><b>Source:</b> Wikipedia</p>
        <p><b>Seasons:</b> {len(seasons)}</p>
        <h3>Season Breakdown</h3>
        <ul>
        """

        for season_num, season_data in sorted(seasons.items()):
            episode_count = len(season_data.get('episodes', {}))
            season_name = season_data.get('name', f'Season {season_num}')
            preview_html += f"<li>{season_name}: {episode_count} episodes</li>"

        preview_html += "</ul>"

        # Show first few episodes of first season
        if seasons:
            first_season_num = min(seasons.keys())
            first_season = seasons[first_season_num]
            episodes = first_season.get('episodes', {})

            if episodes:
                preview_html += "<h3>Sample Episodes (Season 1)</h3><ul>"
                for ep_num in sorted(episodes.keys())[:5]:  # First 5 episodes
                    ep_data = episodes[ep_num]
                    title = ep_data.get('original_title', ep_data.get('canonical_title', f'Episode {ep_num}'))
                    preview_html += f"<li>#{ep_num}: {title}</li>"
                if len(episodes) > 5:
                    preview_html += f"<li>... and {len(episodes) - 5} more episodes</li>"
                preview_html += "</ul>"

        self.preview_text.setHtml(preview_html)

    def generate_cache(self):
        """Generate episode cache from Wikipedia data."""
        if not self.episode_data:
            return

        show_name = self.episode_data.get('show_name', 'Unknown')

        # Ask for output location (optional - will use default cache location)
        from PyQt6.QtWidgets import QFileDialog, QMessageBox

        # Auto-use default location (no confirmation needed - user clicked the button)
        # Status message will show what's happening
        if True:  # Always use default
            # Use default cache location
            show_id = self.cache.get_show_id(show_name)
            output_path = self.cache.get_cache_path(show_id)
        else:
            # Ask for custom location
            output_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Episode Cache",
                f"episode_cache_{show_name.replace(' ', '_')}.json",
                "JSON Files (*.json)"
            )

            if not output_path:
                return  # User cancelled

            output_path = Path(output_path)

        # Disable UI during generation
        self.search_button.setEnabled(False)
        self.generate_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_label.setText("Generating cache...")

        # Create and start worker
        self.cache_worker = WikipediaCacheWorker(self.cache, show_name, output_path)
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

        self._set_status(f"Success: Wikipedia episode cache generated successfully! {cache_path}", level='info')

        self.logger.info(f"Wikipedia cache generated: {cache_path}")
        self.accept()  # Close dialog with success

    def on_cache_error(self, error: str):
        """Handle cache generation error."""
        self.progress_label.setText("Cache generation failed")
        self.search_button.setEnabled(True)
        self.generate_button.setEnabled(True)

        self._set_status(f"Generation Error: Error generating cache: {error}", level='error')
        self.logger.error(f"Error generating cache: {error}", exc_info=True)
        self.logger.error(f"Wikipedia cache generation error: {error}")

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
    dialog = WikipediaCacheDialog()
    dialog.show()
    sys.exit(app.exec())
