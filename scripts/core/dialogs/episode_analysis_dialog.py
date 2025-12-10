#!/usr/bin/env python3
"""
Episode Title Analysis Dialog

Provides UI for analyzing TV show episode titles and viewing recommendations.

Features:
- Show folder selection
- TMDB cache selection
- Progress tracking during analysis
- Results table with issues
- Fix recommendations with confidence levels
- Export results to JSON

Usage:
    from dialogs.episode_analysis_dialog import EpisodeAnalysisDialog
    
    dialog = EpisodeAnalysisDialog(parent)
    if dialog.exec():
        results = dialog.get_results()
"""

import sys
import json
from pathlib import Path
from typing import Optional, Dict, Any, List

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QMessageBox,
    QGroupBox, QFormLayout, QFileDialog, QProgressBar,
    QHeaderView, QAbstractItemView, QSplitter, QTextEdit,
    QCheckBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor

# Add paths
current_dir = Path(__file__).parent
scripts_dir = current_dir.parent.parent
sys.path.insert(0, str(scripts_dir))
sys.path.insert(0, str(scripts_dir / "_common"))

from episode_title_backend import EpisodeTitleAnalyzer
from episode_title_fixer import EpisodeTitleFixer
from _common.logger import ProjectLogger


class AnalysisWorker(QThread):
    """Worker thread for episode analysis."""
    
    # Signals
    progress_update = pyqtSignal(int, str)  # Progress percent, status message
    analysis_complete = pyqtSignal(dict)  # Analysis results
    analysis_error = pyqtSignal(str)  # Error message
    
    def __init__(self, show_path: Path, cache_path: Optional[Path] = None):
        super().__init__()
        self.show_path = show_path
        self.cache_path = cache_path
        self.analyzer = EpisodeTitleAnalyzer()
    
    def run(self):
        """Execute the analysis."""
        try:
            self.progress_update.emit(10, "Initializing analyzer...")
            
            self.progress_update.emit(30, f"Scanning {self.show_path.name}...")
            
            # Run analysis
            results = self.analyzer.analyze_show_folder(self.show_path, self.cache_path)
            
            self.progress_update.emit(100, "Analysis complete")
            self.analysis_complete.emit(results)
        
        except Exception as e:
            self.analysis_error.emit(str(e))


class EpisodeAnalysisDialog(QDialog):
    """Dialog for analyzing TV show episode titles."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # Non-modal dialog (Phase 48-E-4: Modal banishment)
        self.setModal(False)
        self.logger = ProjectLogger("episode_analysis_dialog")
        
        # State
        self.show_path: Optional[Path] = None
        self.cache_path: Optional[Path] = None
        self.analysis_results: Optional[Dict[str, Any]] = None
        self.worker: Optional[AnalysisWorker] = None
        
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
        self.setWindowTitle("Episode Title Analyzer")
        self.setModal(False)  # Non-modal (Phase 48-E-4: Modal banishment)
        self.resize(1200, 800)
        
        layout = QVBoxLayout(self)
        
        # Input section
        input_group = self.create_input_section()
        layout.addWidget(input_group)
        
        # Results section
        results_splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Table
        table_widget = self.create_table_section()
        results_splitter.addWidget(table_widget)
        
        # Details pane
        details_widget = self.create_details_section()
        results_splitter.addWidget(details_widget)
        
        results_splitter.setSizes([500, 200])
        layout.addWidget(results_splitter, stretch=1)
        
        # Progress section
        progress_group = self.create_progress_section()
        layout.addWidget(progress_group)
        
        # Buttons
        button_layout = self.create_button_section()
        layout.addLayout(button_layout)
    
    def create_input_section(self) -> QGroupBox:
        """Create the input section."""
        group = QGroupBox("Analysis Configuration")
        layout = QFormLayout()
        
        # Show folder
        show_layout = QHBoxLayout()
        self.show_path_input = QLineEdit()
        self.show_path_input.setPlaceholderText("Select TV show folder...")
        self.show_path_input.setReadOnly(True)
        show_layout.addWidget(self.show_path_input)
        
        browse_show_btn = QPushButton("Browse...")
        browse_show_btn.clicked.connect(self.browse_show_folder)
        show_layout.addWidget(browse_show_btn)
        
        layout.addRow("Show Folder:", show_layout)
        
        # TMDB Cache (optional)
        cache_layout = QHBoxLayout()
        self.cache_path_input = QLineEdit()
        self.cache_path_input.setPlaceholderText("Optional: Select TMDB cache file...")
        self.cache_path_input.setReadOnly(True)
        cache_layout.addWidget(self.cache_path_input)
        
        browse_cache_btn = QPushButton("Browse...")
        browse_cache_btn.clicked.connect(self.browse_cache_file)
        cache_layout.addWidget(browse_cache_btn)
        
        clear_cache_btn = QPushButton("Clear")
        clear_cache_btn.clicked.connect(lambda: self.set_cache_path(None))
        cache_layout.addWidget(clear_cache_btn)
        
        layout.addRow("TMDB Cache:", cache_layout)
        
        # Options
        self.show_all_checkbox = QCheckBox("Show all episodes (including those without issues)")
        layout.addRow("", self.show_all_checkbox)
        
        # Analyze button
        self.analyze_button = QPushButton("🔍 Analyze Episodes")
        self.analyze_button.clicked.connect(self.start_analysis)
        self.analyze_button.setEnabled(False)
        self.analyze_button.setFixedHeight(40)
        font = QFont()
        font.setPointSize(12)
        self.analyze_button.setFont(font)
        layout.addRow("", self.analyze_button)
        
        group.setLayout(layout)
        return group
    
    def create_table_section(self) -> QGroupBox:
        """Create the results table section."""
        group = QGroupBox("Analysis Results")
        layout = QVBoxLayout()
        
        # Summary label
        self.summary_label = QLabel("No analysis run yet")
        self.summary_label.setStyleSheet("font-weight: bold; padding: 5px;")
        layout.addWidget(self.summary_label)
        
        # Results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(7)
        self.results_table.setHorizontalHeaderLabels([
            "File", "Season", "Episode", "Current Title", 
            "Recommended Title", "Confidence", "Issue Type"
        ])
        
        # Configure table
        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        
        self.results_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.results_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setSortingEnabled(True)
        
        # Connect selection handler
        self.results_table.itemSelectionChanged.connect(self.on_row_selected)
        
        layout.addWidget(self.results_table)
        
        group.setLayout(layout)
        return group
    
    def create_details_section(self) -> QGroupBox:
        """Create the details pane."""
        group = QGroupBox("Episode Details")
        layout = QVBoxLayout()
        
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        layout.addWidget(self.details_text)
        
        group.setLayout(layout)
        return group
    
    def create_progress_section(self) -> QGroupBox:
        """Create the progress section."""
        group = QGroupBox("Progress")
        layout = QVBoxLayout()
        
        self.progress_label = QLabel("Ready to analyze")
        layout.addWidget(self.progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        group.setLayout(layout)
        return group
    
    def create_button_section(self) -> QHBoxLayout:
        """Create the button section."""
        layout = QHBoxLayout()
        
        self.export_button = QPushButton("💾 Export Results")
        self.export_button.clicked.connect(self.export_results)
        self.export_button.setEnabled(False)
        layout.addWidget(self.export_button)
        
        self.fix_button = QPushButton("🔧 Fix Issues (Dry Run)")
        self.fix_button.clicked.connect(lambda: self.fix_issues(dry_run=True))
        self.fix_button.setEnabled(False)
        self.fix_button.setStyleSheet("background-color: #FFA500; font-weight: bold;")
        layout.addWidget(self.fix_button)
        
        self.fix_apply_button = QPushButton("✅ Apply Fixes")
        self.fix_apply_button.clicked.connect(lambda: self.fix_issues(dry_run=False))
        self.fix_apply_button.setEnabled(False)
        self.fix_apply_button.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        layout.addWidget(self.fix_apply_button)
        
        layout.addStretch()
        
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.accept)
        self.close_button.setFixedHeight(40)
        layout.addWidget(self.close_button)
        
        return layout
    
    def browse_show_folder(self):
        """Browse for show folder."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select TV Show Folder",
            str(Path.home()),
            QFileDialog.ShowDirsOnly
        )
        
        if folder:
            self.set_show_path(Path(folder))
    
    def set_show_path(self, path: Path):
        """Set the show path."""
        self.show_path = path
        self.show_path_input.setText(str(path))
        self.analyze_button.setEnabled(True)
    
    def browse_cache_file(self):
        """Browse for TMDB cache file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select TMDB Cache File",
            str(Path.home()),
            "JSON Files (*.json)"
        )
        
        if file_path:
            self.set_cache_path(Path(file_path))
    
    def set_cache_path(self, path: Optional[Path]):
        """Set the cache path."""
        self.cache_path = path
        if path:
            self.cache_path_input.setText(str(path))
        else:
            self.cache_path_input.clear()
    
    def start_analysis(self):
        """Start episode analysis."""
        if not self.show_path:
            self._set_status("No Show Selected: Please select a TV show folder first.", level='warning')
            return
        
        # Disable UI during analysis
        self.analyze_button.setEnabled(False)
        self.export_button.setEnabled(False)
        self.results_table.setRowCount(0)
        self.progress_bar.setValue(0)
        self.progress_label.setText("Starting analysis...")
        
        # Create and start worker
        self.worker = AnalysisWorker(self.show_path, self.cache_path)
        self.worker.progress_update.connect(self.on_progress)
        self.worker.analysis_complete.connect(self.on_analysis_complete)
        self.worker.analysis_error.connect(self.on_analysis_error)
        self.worker.start()
    
    def on_progress(self, progress: int, message: str):
        """Handle progress updates."""
        self.progress_bar.setValue(progress)
        self.progress_label.setText(message)
    
    def on_analysis_complete(self, results: Dict[str, Any]):
        """Handle analysis completion."""
        self.analysis_results = results
        self.populate_results()
        
        self.analyze_button.setEnabled(True)
        self.export_button.setEnabled(True)
        
        # Update summary
        total = results['total_episodes']
        issues = results['issues_found']
        has_cache = " (with TMDB cache)" if results['canonical_available'] else " (no cache)"
        
        self.summary_label.setText(
            f"✓ Analyzed {total} episodes, found {issues} issue{'s' if issues != 1 else ''}{has_cache}"
        )
        
        if issues == 0:
            self._set_status("Analysis Complete: No issues found! All episode titles look good.", level='info')
    
    def on_analysis_error(self, error: str):
        """Handle analysis error."""
        self.progress_label.setText("Analysis failed")
        self.analyze_button.setEnabled(True)
        
        error_msg = f"Episode Analysis Failed: {error}. Please check that:"
        self._set_status(error_msg, level='error')
        self.logger.error(f"Failed to analyze episode titles: {error}", exc_info=True)
        # Legacy QMessageBox.critical call - replaced with status
        # QMessageBox.critical(
        #     self,
        #     "Episode Analysis Failed",
        #     f"Failed to analyze episode titles:\n\n{error}\n\n"
        #     "Please check that:\n"
        #     "• The selected folder contains TV episode files\n"
        #     "• You have read permission for the folder\n"
        #     "• TMDB cache file (if selected) is valid and accessible"
        # )
        self.logger.error(f"Analysis error: {error}")
    
    def populate_results(self):
        """Populate the results table."""
        if not self.analysis_results:
            return
        
        episodes = self.analysis_results['episodes']
        show_all = self.show_all_checkbox.isChecked()
        
        # Filter episodes if not showing all
        if not show_all:
            episodes = [ep for ep in episodes if ep.get('needs_rename', False)]
        
        self.results_table.setRowCount(len(episodes))
        
        for row, episode in enumerate(episodes):
            # File name
            file_item = QTableWidgetItem(episode['file_name'])
            self.results_table.setItem(row, 0, file_item)
            
            # Season
            season = episode.get('season', 'N/A')
            season_item = QTableWidgetItem(str(season))
            season_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.results_table.setItem(row, 1, season_item)
            
            # Episode
            ep_num = episode.get('episode', 'N/A')
            ep_item = QTableWidgetItem(str(ep_num))
            ep_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.results_table.setItem(row, 2, ep_item)
            
            # Current title
            current = episode.get('episode_title', 'N/A')
            current_item = QTableWidgetItem(current)
            self.results_table.setItem(row, 3, current_item)
            
            # Recommended title
            if 'canonical_title' in episode and episode['canonical_title']:
                recommended = episode['canonical_title']
            elif 'cleaned_title' in episode:
                recommended = episode['cleaned_title']
            else:
                recommended = "No changes"
            
            rec_item = QTableWidgetItem(recommended)
            self.results_table.setItem(row, 4, rec_item)
            
            # Confidence
            confidence = episode.get('confidence', 'N/A')
            conf_item = QTableWidgetItem(confidence)
            conf_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # Color code by confidence
            if confidence == 'high':
                conf_item.setBackground(QColor(200, 255, 200))
            elif confidence == 'medium':
                conf_item.setBackground(QColor(255, 255, 200))
            elif confidence in ['low', 'very_low']:
                conf_item.setBackground(QColor(255, 200, 200))
            
            self.results_table.setItem(row, 5, conf_item)
            
            # Issue type
            issue_type = episode.get('issue_type', 'none')
            issue_item = QTableWidgetItem(issue_type or 'none')
            issue_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.results_table.setItem(row, 6, issue_item)
        
        self.results_table.resizeColumnsToContents()
    
    def on_row_selected(self):
        """Handle row selection."""
        selected = self.results_table.selectedItems()
        if not selected or not self.analysis_results:
            return
        
        row = selected[0].row()
        episodes = self.analysis_results['episodes']
        
        # Filter if needed
        if not self.show_all_checkbox.isChecked():
            episodes = [ep for ep in episodes if ep.get('needs_rename', False)]
        
        if row >= len(episodes):
            return
        
        episode = episodes[row]
        
        # Display details
        details_html = f"""
        <h3>{episode['file_name']}</h3>
        <p><b>Full Path:</b> {episode.get('full_path', 'N/A')}</p>
        <p><b>Season:</b> {episode.get('season', 'N/A')} | <b>Episode:</b> {episode.get('episode', 'N/A')}</p>
        
        <h4>Current Title:</h4>
        <p>{episode.get('episode_title', 'N/A')}</p>
        
        {f"<h4>Cleaned Title:</h4><p>{episode.get('cleaned_title', 'N/A')}</p>" if 'cleaned_title' in episode else ''}
        
        {f"<h4>Canonical Title (TMDB):</h4><p>{episode.get('canonical_title', 'N/A')}</p>" if 'canonical_title' in episode else ''}
        
        <h4>Recommendation:</h4>
        <p><b>{episode.get('recommendation', 'N/A')}</b> (confidence: {episode.get('confidence', 'N/A')})</p>
        
        {f"<p><b>Similarity Score:</b> {episode.get('cleaned_similarity', 0):.1%}</p>" if 'cleaned_similarity' in episode else ''}
        
        <h4>Issue Type:</h4>
        <p>{episode.get('issue_type', 'none')}</p>
        """
        
        self.details_text.setHtml(details_html)
    
    def export_results(self):
        """Export analysis results to JSON."""
        if not self.analysis_results:
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Analysis Results",
            f"episode_analysis_{self.show_path.name}.json",
            "JSON Files (*.json)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.analysis_results, f, indent=2, ensure_ascii=False)
                
                self._set_status(f"Export Success: Results exported to {file_path}", level='info')
                self.logger.info(f"Exported results to {file_path}")
            
            except Exception as e:
                self._set_status(f"Export Error: Failed to export results: {e}", level='error')
                self.logger.error(f"Failed to export results: {e}", exc_info=True)
                self.logger.error(f"Export error: {e}")
    
    def fix_issues(self, dry_run: bool = True):
        """Fix episode title issues."""
        if not self.analysis_results:
            return
        
        # Get episodes with issues
        episodes_to_fix = [
            ep for ep in self.analysis_results['episodes']
            if ep.get('needs_rename', False)
        ]
        
        if not episodes_to_fix:
            self._set_status("No Issues: No episodes need fixing.", level='info')
            return
        
        # Confirm with user
        mode_text = "DRY RUN (Preview)" if dry_run else "APPLY CHANGES"
        message = f"{mode_text}\n\n"
        message += f"This will process {len(episodes_to_fix)} episode(s).\n\n"
        
        if dry_run:
            message += "No actual changes will be made - this is a preview only.\n"
            message += "Review the results and use 'Apply Fixes' when ready."
        else:
            message += "⚠️ WARNING: This will rename files on disk!\n\n"
            message += "Make sure you have a backup before proceeding.\n"
            message += "Changes are logged and can be traced in audit logs."
        
        # Auto-proceed with fix (no confirmation needed - user clicked the button)
        # Status message will show what's happening
        
        # Disable UI during operation
        self.fix_button.setEnabled(False)
        self.fix_apply_button.setEnabled(False)
        self.analyze_button.setEnabled(False)
        self.progress_bar.setValue(0)
        
        # Create fixer and apply
        try:
            fixer = EpisodeTitleFixer()
            
            # Create snapshot before applying fixes (not for dry run)
            snapshot_id = None
            if not dry_run:
                self.progress_label.setText("Creating backup snapshot...")
                snapshot_id = fixer.create_snapshot_backup(self.show_path, "pre_episode_title_fix")
                if snapshot_id:
                    self.logger.info(f"Created snapshot: {snapshot_id}")
                else:
                    self._set_status("Snapshot Warning: Failed to create backup snapshot. Changes will still be logged to audit trail, but file-level rollback may not be available.", level='warning')
            
            def progress_callback(current, total, message):
                percent = int((current / total) * 100)
                self.progress_bar.setValue(percent)
                self.progress_label.setText(message)
            
            # Apply fixes
            results = fixer.apply_fixes(
                episodes_to_fix,
                dry_run=dry_run,
                progress_callback=progress_callback
            )
            
            # Show results
            self.show_fix_results(results, dry_run)
            
            # If we actually fixed files, re-run analysis to update UI
            if not dry_run and results['successful'] > 0:
                snapshot_msg = f" Snapshot created: {snapshot_id}" if snapshot_id else " ⚠️ No snapshot created (check logs)"
                self._set_status(f"Fixes Applied: Successfully fixed {results['successful']} episode(s).{snapshot_msg} Re-running analysis to refresh results...", level='info')
                self.start_analysis()
        
        except Exception as e:
            self._set_status(f"Fix Error: Error during fix operation: {e}", level='error')
            self.logger.error(f"Error during fix operation: {e}", exc_info=True)
            self.logger.error(f"Fix operation error: {e}")
        
        finally:
            # Re-enable UI
            self.fix_button.setEnabled(True)
            self.fix_apply_button.setEnabled(True)
            self.analyze_button.setEnabled(True)
    
    def show_fix_results(self, results: Dict[str, Any], dry_run: bool):
        """Show fix operation results."""
        mode = "DRY RUN PREVIEW" if dry_run else "FIXES APPLIED"
        
        message = f"{'='*50}\n"
        message += f"{mode}\n"
        message += f"{'='*50}\n\n"
        message += f"Total: {results['total']}\n"
        message += f"Successful: {results['successful']}\n"
        message += f"Failed: {results['failed']}\n\n"
        
        # Show first few operations
        operations = results['operations'][:10]
        for op in operations:
            if op['success']:
                message += f"✓ {op['old_filename']}\n"
                message += f"  → {op['new_filename']}\n\n"
            else:
                message += f"✗ {op['episode']}\n"
                message += f"  Error: {op['error']}\n\n"
        
        if len(results['operations']) > 10:
            message += f"... and {len(results['operations']) - 10} more\n"
        
        # Non-modal status message (Phase 48-E-4)
        if results['failed'] == 0:
            self._set_status(f"Fix Results: {message}", level='info')
        else:
            self._set_status(f"Fix Results: {message} (Some failures - check logs)", level='warning')
        self.logger.info(f"Fix Results: {json.dumps(results, indent=2)}")
    
    def get_results(self) -> Optional[Dict[str, Any]]:
        """Get the analysis results."""
        return self.analysis_results
    
    def closeEvent(self, event):
        """Handle dialog close."""
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()
        
        event.accept()


if __name__ == "__main__":
    """Test the dialog."""
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    dialog = EpisodeAnalysisDialog()
    dialog.show()
    sys.exit(app.exec())
