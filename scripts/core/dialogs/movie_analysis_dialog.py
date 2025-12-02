"""
Movie Analysis Dialog - UI for analyzing and fixing movie naming issues

Provides:
1. Movie folder analysis
2. Issue detection and display
3. Fix suggestions and preview
4. Export results
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QFileDialog, QTextEdit,
    QProgressBar, QMessageBox, QHeaderView, QCheckBox, QGroupBox,
    QAbstractItemView
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor, QFont

# Add paths
current_dir = Path(__file__).parent
scripts_dir = current_dir.parent.parent
sys.path.insert(0, str(scripts_dir))
sys.path.insert(0, str(scripts_dir / "_common"))

from movie_name_backend import MovieNameAnalyzer
from movie_name_fixer import MovieNameFixer
from _common.logger import ProjectLogger


class AnalysisWorker(QThread):
    """Worker thread for movie analysis"""
    
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    progress = pyqtSignal(int, int, str)  # current, total, message
    
    def __init__(self, movies_path: str):
        super().__init__()
        self.movies_path = movies_path
        self.analyzer = MovieNameAnalyzer()
    
    def run(self):
        """Run analysis in background thread"""
        try:
            def progress_callback(current, total, message):
                self.progress.emit(current, total, message)
            
            results = self.analyzer.analyze_movies_folder(
                self.movies_path,
                progress_callback=progress_callback
            )
            
            self.finished.emit(results)
            
        except Exception as e:
            self.error.emit(str(e))


class MovieAnalysisDialog(QDialog):
    """Dialog for analyzing movie naming issues"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # Non-modal dialog (Phase 48-E-4: Modal banishment)
        self.setModal(False)
        self.setWindowTitle("Movie Name Analysis")
        self.setModal(False)  # Non-modal (Phase 48-E-4: Modal banishment)
        self.resize(1000, 700)
        
        self.analyzer = MovieNameAnalyzer()
        self.logger = ProjectLogger('movie_analysis_dialog')
        self.worker = None
        self.analysis_results = None
        
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
        """Initialize the user interface"""
        layout = QVBoxLayout()
        
        # Input section
        input_group = self.create_input_section()
        layout.addWidget(input_group)
        
        # Progress section
        progress_group = self.create_progress_section()
        layout.addWidget(progress_group)
        
        # Filter section
        filter_layout = QHBoxLayout()
        self.show_all_checkbox = QCheckBox("Show all movies (including those without issues)")
        self.show_all_checkbox.stateChanged.connect(self.filter_results)
        filter_layout.addWidget(self.show_all_checkbox)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # Results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(7)
        self.results_table.setHorizontalHeaderLabels([
            "File", "Title", "Year", "Folder", "Issues", "Severity", "Auto-Fixable"
        ])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.results_table.horizontalHeader().setStretchLastSection(False)
        self.results_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.results_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.results_table.itemSelectionChanged.connect(self.on_selection_changed)
        self.results_table.setSortingEnabled(True)
        layout.addWidget(self.results_table, stretch=3)
        
        # Details section
        details_label = QLabel("Movie Details:")
        layout.addWidget(details_label)
        
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setMaximumHeight(150)
        layout.addWidget(self.details_text, stretch=1)
        
        # Button section
        button_layout = self.create_button_section()
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def create_input_section(self) -> QGroupBox:
        """Create input section for folder selection"""
        group = QGroupBox("Analysis Settings")
        layout = QVBoxLayout()
        
        # Movies folder
        folder_layout = QHBoxLayout()
        folder_layout.addWidget(QLabel("Movies Folder:"))
        self.folder_input = QLabel("(not selected)")
        self.folder_input.setStyleSheet("padding: 5px; background: #f0f0f0; border: 1px solid #ccc;")
        folder_layout.addWidget(self.folder_input, stretch=1)
        
        self.browse_button = QPushButton("Browse...")
        self.browse_button.clicked.connect(self.browse_folder)
        folder_layout.addWidget(self.browse_button)
        
        layout.addLayout(folder_layout)
        
        # Analyze button
        self.analyze_button = QPushButton("🔍 Analyze Movies")
        self.analyze_button.clicked.connect(self.start_analysis)
        self.analyze_button.setEnabled(False)
        self.analyze_button.setFixedHeight(40)
        font = QFont()
        font.setPointSize(12)
        self.analyze_button.setFont(font)
        layout.addWidget(self.analyze_button)
        
        group.setLayout(layout)
        return group
    
    def create_progress_section(self) -> QGroupBox:
        """Create the progress tracking section."""
        group = QGroupBox("Progress")
        layout = QVBoxLayout()
        
        self.progress_label = QLabel("Ready to analyze movies")
        layout.addWidget(self.progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        group.setLayout(layout)
        return group
    
    def create_button_section(self) -> QHBoxLayout:
        """Create button section"""
        layout = QHBoxLayout()
        
        self.export_button = QPushButton("📄 Export Results")
        self.export_button.clicked.connect(self.export_results)
        self.export_button.setEnabled(False)
        self.export_button.setFixedHeight(40)
        layout.addWidget(self.export_button)
        
        layout.addStretch()
        
        # Fix buttons
        self.fix_button = QPushButton("🔧 Fix Issues (Dry Run)")
        self.fix_button.clicked.connect(lambda: self.fix_issues(dry_run=True))
        self.fix_button.setEnabled(False)
        self.fix_button.setFixedHeight(40)
        layout.addWidget(self.fix_button)
        
        self.fix_apply_button = QPushButton("✅ Apply Fixes")
        self.fix_apply_button.clicked.connect(lambda: self.fix_issues(dry_run=False))
        self.fix_apply_button.setEnabled(False)
        self.fix_apply_button.setFixedHeight(40)
        layout.addWidget(self.fix_apply_button)
        
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.close)
        self.close_button.setFixedHeight(40)
        layout.addWidget(self.close_button)
        
        return layout
    
    def browse_folder(self):
        """Browse for movies folder"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Movies Folder",
            "",
            QFileDialog.ShowDirsOnly
        )
        
        if folder:
            self.folder_input.setText(folder)
            self.analyze_button.setEnabled(True)
    
    def start_analysis(self):
        """Start movie analysis"""
        movies_path = self.folder_input.text()
        
        if not movies_path or movies_path == "(not selected)":
            self._set_status("No Movies Folder Selected: Please click 'Browse...' to select your movies folder before starting analysis.", level='warning')
            return
        
        # Clear previous results
        self.results_table.setRowCount(0)
        self.details_text.clear()
        self.analysis_results = None
        
        # Disable controls
        self.analyze_button.setEnabled(False)
        self.browse_button.setEnabled(False)
        self.export_button.setEnabled(False)
        
        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_label.setText("Starting analysis...")
        
        # Start worker thread
        self.worker = AnalysisWorker(movies_path)
        self.worker.finished.connect(self.on_analysis_complete)
        self.worker.error.connect(self.on_analysis_error)
        self.worker.progress.connect(self.on_analysis_progress)
        self.worker.start()
    
    def on_analysis_progress(self, current: int, total: int, message: str):
        """Update progress bar"""
        if total > 0:
            percent = int((current / total) * 100)
            self.progress_bar.setValue(percent)
        self.progress_label.setText(message)
    
    def on_analysis_complete(self, results: Dict[str, Any]):
        """Handle analysis completion"""
        self.analysis_results = results
        
        # Hide progress
        self.progress_bar.setVisible(False)
        
        # Update status
        total = results['total_files']
        summary = results['summary']
        issues_count = total - summary['no_issues']
        
        self.progress_label.setText(
            f"Analysis complete: {total} movies analyzed, {issues_count} with issues"
        )
        
        # Populate table
        self.populate_results_table()
        
        # Re-enable controls
        self.analyze_button.setEnabled(True)
        self.browse_button.setEnabled(True)
        self.export_button.setEnabled(True)
        
        # Enable fix buttons if there are issues
        if issues_count > 0:
            self.fix_button.setEnabled(True)
            self.fix_apply_button.setEnabled(True)
        
        self.logger.info(f"Analysis complete: {issues_count}/{total} movies have issues")
    
    def on_analysis_error(self, error: str):
        """Handle analysis error"""
        self.progress_bar.setVisible(False)
        self.progress_label.setText("Analysis failed")
        
        self._set_status(f"Movie Analysis Failed: {error}. Please check that the selected folder exists and is accessible, you have read permission, and the folder contains movie files with supported extensions.", level='error')
        self.logger.error(f"Failed to analyze movie names: {error}", exc_info=True)
        
        # Re-enable controls
        self.analyze_button.setEnabled(True)
        self.browse_button.setEnabled(True)
        
        self.logger.error(f"Analysis error: {error}")
    
    def populate_results_table(self):
        """Populate results table with analysis data"""
        if not self.analysis_results:
            return
        
        movies = self.analysis_results['movies']
        
        # Filter based on checkbox
        if not self.show_all_checkbox.isChecked():
            movies = [m for m in movies if m['needs_fix']]
        
        self.results_table.setSortingEnabled(False)
        self.results_table.setRowCount(len(movies))
        
        for row, movie in enumerate(movies):
            # File
            self.results_table.setItem(row, 0, QTableWidgetItem(movie['filename']))
            
            # Title
            self.results_table.setItem(row, 1, QTableWidgetItem(movie['title'] or '(unknown)'))
            
            # Year
            self.results_table.setItem(row, 2, QTableWidgetItem(movie['year'] or '(missing)'))
            
            # Folder
            self.results_table.setItem(row, 3, QTableWidgetItem(movie['parent_folder']))
            
            # Issues
            issue_count = len(movie['issues'])
            issues_item = QTableWidgetItem(str(issue_count))
            issues_item.setData(Qt.UserRole, movie)  # Store movie data
            self.results_table.setItem(row, 4, issues_item)
            
            # Severity (highest severity among issues)
            severities = [i['severity'] for i in movie['issues']]
            severity = 'none'
            if 'high' in severities:
                severity = 'high'
            elif 'medium' in severities:
                severity = 'medium'
            elif 'low' in severities:
                severity = 'low'
            
            severity_item = QTableWidgetItem(severity)
            
            # Color code by severity
            if severity == 'high':
                severity_item.setBackground(QColor('#ff9999'))  # Red
            elif severity == 'medium':
                severity_item.setBackground(QColor('#ffcc99'))  # Orange
            elif severity == 'low':
                severity_item.setBackground(QColor('#ffff99'))  # Yellow
            else:
                severity_item.setBackground(QColor('#99ff99'))  # Green
            
            self.results_table.setItem(row, 5, severity_item)
            
            # Auto-fixable
            fix_suggestions = self.analyzer.suggest_fix(movie)
            can_auto_fix = fix_suggestions.get('can_auto_fix', False)
            auto_fix_item = QTableWidgetItem('Yes' if can_auto_fix else 'No')
            self.results_table.setItem(row, 6, auto_fix_item)
        
        self.results_table.setSortingEnabled(True)
        self.results_table.resizeColumnsToContents()
    
    def filter_results(self):
        """Filter results based on checkbox state"""
        if self.analysis_results:
            self.populate_results_table()
    
    def on_selection_changed(self):
        """Handle table row selection"""
        selected_items = self.results_table.selectedItems()
        
        if not selected_items:
            self.details_text.clear()
            return
        
        row = selected_items[0].row()
        issues_item = self.results_table.item(row, 4)
        movie = issues_item.data(Qt.UserRole)
        
        if not movie:
            return
        
        # Generate detailed HTML display
        html = f"<h3>{movie['filename']}</h3>"
        html += f"<p><b>Path:</b> {movie['file_path']}</p>"
        html += f"<p><b>Title:</b> {movie['title'] or '(unknown)'}</p>"
        html += f"<p><b>Year:</b> {movie['year'] or '(missing)'}</p>"
        html += f"<p><b>Folder:</b> {movie['parent_folder']}</p>"
        
        if movie['cleaned_filename'] != movie['filename']:
            html += f"<p><b>Cleaned:</b> {movie['cleaned_filename']}</p>"
        
        if movie['issues']:
            html += "<h4>Issues Found:</h4><ul>"
            for issue in movie['issues']:
                html += f"<li><b>{issue['type']}</b> ({issue['severity']}): "
                html += f"{issue['description']}</li>"
            html += "</ul>"
            
            # Show fix suggestions
            fix_suggestions = self.analyzer.suggest_fix(movie)
            if fix_suggestions['suggestions']:
                html += "<h4>Suggested Fixes:</h4><ul>"
                for suggestion in fix_suggestions['suggestions']:
                    action = suggestion['action']
                    auto = '✓ Auto' if suggestion['auto_fixable'] else '✗ Manual'
                    html += f"<li>[{auto}] <b>{action}</b>: "
                    
                    if 'suggested_filename' in suggestion and suggestion['suggested_filename']:
                        html += f"{suggestion['suggested_filename']}"
                    elif 'suggested_folder' in suggestion and suggestion['suggested_folder']:
                        html += f"Move to folder: {suggestion['suggested_folder']}"
                    elif 'note' in suggestion:
                        html += suggestion['note']
                    
                    html += "</li>"
                html += "</ul>"
        else:
            html += "<p><b>✓ No issues found</b></p>"
        
        self.details_text.setHtml(html)
    
    def export_results(self):
        """Export analysis results to JSON"""
        if not self.analysis_results:
            return
        
        try:
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Export Results",
                "movie_analysis_results.json",
                "JSON Files (*.json)"
            )
            
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(self.analysis_results, f, indent=2, ensure_ascii=False)
                
                self._set_status(f"Export Successful: Results exported to {filename}", level='info')
                
                self.logger.info(f"Results exported to {filename}")
        
        except Exception as e:
            self._set_status(f"Export Error: Error exporting results: {e}", level='error')
            self.logger.error(f"Error exporting results: {e}", exc_info=True)
            self.logger.error(f"Export error: {e}")
    
    def fix_issues(self, dry_run: bool = True):
        """Fix movie naming issues."""
        if not self.analysis_results:
            return
        
        # Get movies with issues
        movies_to_fix = [
            m for m in self.analysis_results['movies']
            if m['needs_fix']
        ]
        
        if not movies_to_fix:
            self._set_status("No Issues: No movies need fixing.", level='info')
            return
        
        # Determine fix types needed
        fix_types = set()
        for movie in movies_to_fix:
            for issue in movie['issues']:
                if issue['type'] == 'codec_in_name':
                    fix_types.add('codec')
                elif issue['type'] == 'not_in_folder':
                    fix_types.add('folder')
        
        # Confirm with user
        mode_text = "DRY RUN (Preview)" if dry_run else "APPLY CHANGES"
        message = f"{mode_text}\n\n"
        message += f"This will process {len(movies_to_fix)} movie(s).\n\n"
        message += f"Fix types to apply:\n"
        if 'codec' in fix_types:
            message += "  • Remove codec tags from filenames\n"
        if 'folder' in fix_types:
            message += "  • Create proper folder structure\n"
        message += "\n"
        
        if dry_run:
            message += "No actual changes will be made - this is a preview only.\n"
            message += "Review the results and use 'Apply Fixes' when ready."
        else:
            message += "⚠️ WARNING: This will rename/move files on disk!\n\n"
            message += "Make sure you have a backup before proceeding.\n"
            message += "Changes are logged and can be traced in audit logs."
        
        # Auto-proceed with fix (no confirmation needed - user clicked the button)
        # Status message will show what's happening
        
        # Disable UI during operation
        self.fix_button.setEnabled(False)
        self.fix_apply_button.setEnabled(False)
        self.analyze_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        
        # Create fixer and apply
        try:
            fixer = MovieNameFixer()
            base_dir = Path(self.analysis_results['folder'])
            
            def progress_callback(current, total, message):
                percent = int((current / total) * 100)
                self.progress_bar.setValue(percent)
                self.progress_label.setText(message)
            
            # Apply fixes
            results = fixer.apply_fixes(
                movies_to_fix,
                base_dir,
                list(fix_types),
                dry_run=dry_run,
                progress_callback=progress_callback
            )
            
            # Show results
            self.show_fix_results(results, dry_run)
            
            # If we actually fixed files, re-run analysis to update UI
            if not dry_run and results['successful'] > 0:
                self._set_status(f"Fixes Applied: Successfully fixed {results['successful']} movie(s). Re-running analysis to refresh results...", level='info')
                self.start_analysis()
        
        except Exception as e:
            self._set_status(f"Fix Error: Error during fix operation: {e}", level='error')
            self.logger.error(f"Error during fix operation: {e}", exc_info=True)
            self.logger.error(f"Fix operation error: {e}")
        
        finally:
            # Re-enable UI
            self.progress_bar.setVisible(False)
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
        message += f"Skipped: {results['skipped']}\n"
        message += f"Failed: {results['failed']}\n\n"
        
        # Show first few operations
        operations = results['operations'][:10]
        for op in operations:
            if op.get('skipped'):
                message += f"⊘ {op['movie']}\n"
                message += f"  Skipped: {op.get('reason', 'N/A')}\n\n"
            elif op['success']:
                message += f"✓ {op.get('old_filename', op['movie'])}\n"
                if 'new_filename' in op:
                    message += f"  → {op['new_filename']}\n"
                elif 'action' in op:
                    message += f"  Action: {op['action']}\n"
                message += "\n"
            else:
                message += f"✗ {op['movie']}\n"
                message += f"  Error: {op.get('error', 'Unknown error')}\n\n"
        
        if len(results['operations']) > 10:
            message += f"... and {len(results['operations']) - 10} more\n"
        
        # Show in dialog
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Fix Results")
        msg_box.setText(message)
        msg_box.setIcon(QMessageBox.Information if results['failed'] == 0 else QMessageBox.Warning)
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.setDetailedText(json.dumps(results, indent=2))
        msg_box.setModal(False)  # Non-modal (Phase 48-E-4)
        msg_box.show()
    
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
    dialog = MovieAnalysisDialog()
    dialog.show()
    sys.exit(app.exec())
