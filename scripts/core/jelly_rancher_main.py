#!/usr/bin/env python3
"""
JellyRancher - Unified Media Organization Platform

Complete GUI application combining all media organization tools:
- Media Organization (Movies, TV Shows, Anime)
- Subtitle Management (Multi-provider downloads)
- Batch Processing (RavenMaven AI integration)
- Code Analysis (CodeCop quality metrics)
- Analytics & Reporting
- Settings & Configuration

Built on PyQt6 with modern interface and comprehensive feature set.
"""

import sys
import os
import json
import ast
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum

# Enable High DPI scaling for modern displays
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"

# PyQt6 imports
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QLineEdit, QPushButton, QComboBox, QSpinBox,
    QCheckBox, QTextEdit, QProgressBar, QMessageBox, QFileDialog,
    QTableWidget, QTableWidgetItem, QDialog, QListWidget, QListWidgetItem,
    QGroupBox, QFormLayout, QStatusBar, QMenuBar, QMenu, QToolBar,
    QScrollArea, QSplitter, QHeaderView, QTreeWidget, QTreeWidgetItem,
    QStyle, QFrame, QAbstractItemView
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize, QEvent, QUrl
from PyQt6.QtGui import QIcon, QFont, QColor, QTextCursor, QPixmap, QWheelEvent, QDesktopServices, QAction

# Add scripts to path
current_dir = Path(__file__).parent
jellyfin_dir = current_dir / "Jellyfin Organizer"
ravenmaven_dir = current_dir / "RavenMaven"
scripts_dir = current_dir.parent
sys.path.insert(0, str(scripts_dir))
sys.path.insert(0, str(scripts_dir / "_common"))
sys.path.insert(0, str(scripts_dir / "core"))
sys.path.insert(0, str(scripts_dir / "media"))
sys.path.insert(0, str(scripts_dir / "ai"))
sys.path.insert(0, str(scripts_dir / "utils"))
sys.path.insert(0, str(jellyfin_dir / "scripts"))
sys.path.insert(0, str(jellyfin_dir / "scripts" / "_common"))
sys.path.insert(0, str(jellyfin_dir / "tools" / "ravenmaven"))
sys.path.insert(0, str(jellyfin_dir / "tools" / "code_cop" / "tools" / "audit"))
sys.path.insert(0, str(ravenmaven_dir))

# Import foundation modules
from _common.immutable_audit import ImmutableAuditLog
from _common.credential_manager import CredentialManager
from _common.snapshot_manager import SnapshotManager
from _common.media_utils import normalize_windows_path, hash_file
from _common.logger import ProjectLogger

# Import backends
from media_org_backend import MediaOrganizer
from subtitle_backend import SubtitleBackend
from tools_backend import CodeCopInterface, RavenMavenInterface
from analytics_backend import AnalyticsBackend
from settings_backend import SettingsManager

# Import RavenMaven components
try:
    from ravenmaven_client import PoeClient
    from jellyfin_safe_executor import JellyfinSafeExecutor
    from batch_queue_processor import BatchQueueProcessor
except ImportError:
    PoeClient = None
    JellyfinSafeExecutor = None
    BatchQueueProcessor = None

# Import CodeCop components
try:
    from codecop_gui import CodeCopWizard
except ImportError:
    CodeCopWizard = None

# Import TMDB dialog
try:
    from dialogs.tmdb_cache_dialog import TMDBCacheDialog
except ImportError:
    TMDBCacheDialog = None

# Import Wikipedia dialog
try:
    from dialogs.wikipedia_cache_dialog import WikipediaCacheDialog
except ImportError:
    WikipediaCacheDialog = None

# Import Canonical DB dialog
try:
    from dialogs.canonical_db_dialog import CanonicalDBDialog
except ImportError:
    CanonicalDBDialog = None

# Import episode analysis dialog
try:
    from dialogs.episode_analysis_dialog import EpisodeAnalysisDialog
except ImportError:
    EpisodeAnalysisDialog = None

# Import movie analysis dialog
try:
    from dialogs.movie_analysis_dialog import MovieAnalysisDialog
except ImportError:
    MovieAnalysisDialog = None

# Import help system
from jelly_rancher_help import show_help_dialog

# Constants
APP_TITLE = "JellyRancher - Unified Media Organization Platform"
APP_VERSION = "2.0.0"
WINDOW_WIDTH = 1200  # Reduced from 1400 for more comfortable screen fit
WINDOW_HEIGHT = 700  # Reduced from 800 for more comfortable screen fit
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

    def __init__(self, operation_type: str, params: Dict):
        super().__init__()
        self.operation_type = operation_type
        self.params = params
        self.logger = ProjectLogger("operation_thread")

    def run(self):
        """Execute the operation."""
        try:
            if self.operation_type == "scan_folder":
                self._scan_folder()
            elif self.operation_type == "organize_media":
                self._organize_media()
            elif self.operation_type == "download_subtitles":
                self._download_subtitles()
            elif self.operation_type == "batch_process":
                self._batch_process()
            elif self.operation_type == "code_analysis":
                self._code_analysis()
            else:
                self.operation_complete.emit(False, f"Unknown operation: {self.operation_type}")
        except Exception as e:
            self.logger.error(f"Operation failed: {str(e)}")
            self.operation_complete.emit(False, str(e))

    def _scan_folder(self):
        """Scan media folder."""
        folder_path = self.params.get("folder_path")
        if not folder_path:
            self.operation_complete.emit(False, "No folder path provided")
            return

        # Import here to avoid circular imports
        from media_scanner import MediaFileScanner

        scanner = MediaFileScanner(folder_path)
        files = scanner.scan_files()

        self.progress_updated.emit(f"Found {len(files)} media files")
        self.progress_percent.emit(100)
        self.operation_complete.emit(True, f"Scan complete: {len(files)} files found")

    def _organize_media(self):
        """Organize media files."""
        # Implementation would go here
        self.progress_updated.emit("Organizing media files...")
        self.progress_percent.emit(50)
        self.progress_updated.emit("Creating folder structure...")
        self.progress_percent.emit(100)
        self.operation_complete.emit(True, "Media organization complete")

    def _download_subtitles(self):
        """Download subtitles."""
        # Implementation would go here
        self.progress_updated.emit("Downloading subtitles...")
        self.progress_percent.emit(100)
        self.operation_complete.emit(True, "Subtitle download complete")

    def _batch_process(self):
        """Batch processing with RavenMaven."""
        # Implementation would go here
        self.progress_updated.emit("Processing batch...")
        self.progress_percent.emit(100)
        self.operation_complete.emit(True, "Batch processing complete")

    def _code_analysis(self):
        """Code analysis with CodeCop."""
        # Implementation would go here
        self.progress_updated.emit("Analyzing code...")
        self.progress_percent.emit(100)
        self.operation_complete.emit(True, "Code analysis complete")


class JellyRancherMainWindow(QMainWindow):
    """Main JellyRancher application window."""

    def __init__(self):
        super().__init__()
        self.audit = ImmutableAuditLog()
        self.creds = CredentialManager()
        self.settings = SettingsManager()
        self.logger = ProjectLogger("jelly_rancher_main")

        # Zoom level for Ctrl+MouseWheel scaling - default 0.85x for more comfortable size
        self.zoom_level = 0.85
        self.min_zoom = 0.5
        self.max_zoom = 3.0

        # Load function index for dynamic docstring lookup
        self.function_index = self._load_function_index()

        self.init_ui()
        self.apply_stylesheet()

        # Install event filter for zoom functionality
        self.installEventFilter(self)
        
        # Show welcome wizard on first launch
        self.show_welcome_wizard_if_needed()

    def _load_function_index(self):
        """Load function index for docstring lookup."""
        try:
            import json
            from pathlib import Path
            index_path = Path(__file__).parent.parent.parent / 'function_index.json'
            with open(index_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('functions', {})
        except Exception as e:
            self.logger.warning(f'Could not load function index: {e}')
            return {}

    def get_function_docstring(self, function_name):
        """Get docstring for a function by name, prioritizing enhanced versions."""
        if not self.function_index:
            return 'No documentation available.'

        # First try to find an enhanced docstring by name (more flexible than line matching)
        for file_path, functions in self.function_index.items():
            if not isinstance(functions, list):
                continue
            for func in functions:
                if func.get('name') == function_name and func.get('docstring_enhanced'):
                    return func['docstring']

        # Fall back to any docstring for this function name
        for file_path, functions in self.function_index.items():
            if not isinstance(functions, list):
                continue
            for func in functions:
                if func.get('name') == function_name:
                    docstring = func.get('docstring', 'No documentation available.')
                    return docstring

        return f'Function "{function_name}" not found in index.'

    def format_hover_help(self, control_name: str, docstring: str) -> str:
        """Format hover help text with control title and description."""
        return f"**{control_name}**\n\n{docstring}"

    def get_control_display_name(self, control, control_help_dict):
        """Get a user-friendly display name for a control."""
        # Try to get the description from the control_help_dict
        for ctrl, description in control_help_dict.items():
            if ctrl is control:
                # Extract the control name from the description (everything before the first dash)
                if " - " in description:
                    return description.split(" - ")[0]
                
                # Fallback: try to get text from control
                if hasattr(control, 'text'):
                    text = str(control.text()).strip()
                    if text:
                        return f"{text} Button" if isinstance(control, QPushButton) else text
                
                # Last resort: use description as-is
                return description
        
        return "Control"

    def update_hover_help(self, tab_name: str, control_name: str, description: str):
        """Update hover help for a specific tab and control."""
        formatted_help = self.format_hover_help(control_name, description)
        
        # Update the appropriate help text widget
        if tab_name == "organization":
            self.org_help_text.setPlainText(formatted_help)
        elif tab_name == "subtitles":
            self.sub_help_text.setPlainText(formatted_help)
        elif tab_name == "batch":
            self.batch_help_text.setPlainText(formatted_help)
        elif tab_name == "code":
            self.code_help_text.setPlainText(formatted_help)
        elif tab_name == "analytics":
            self.analytics_help_text.setPlainText(formatted_help)
        elif tab_name == "memory":
            self.memory_help_text.setPlainText(formatted_help)
        elif tab_name == "settings":
            self.settings_help_text.setPlainText(formatted_help)

    def eventFilter(self, obj, event):
        """Handle Ctrl+MouseWheel for GUI scaling and hover events for contextual help."""
        # Handle zoom
        if event.type() == QEvent.Type.Wheel and event.modifiers() == Qt.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self.zoom_in()
            else:
                self.zoom_out()
            return True

        # Handle organization tab hover events
        if hasattr(self, 'org_control_help') and obj in self.org_control_help:
            if event.type() == QEvent.Type.Enter:
                control_name = self.get_control_display_name(obj, self.org_control_help)
                description = self.org_control_help[obj]
                self.update_hover_help("organization", control_name, description)
                return False
            # Remove Leave handler - help now persists until another control is hovered

        # Handle subtitles tab hover events
        if hasattr(self, 'sub_control_help') and obj in self.sub_control_help:
            if event.type() == QEvent.Type.Enter:
                control_name = self.get_control_display_name(obj, self.sub_control_help)
                description = self.sub_control_help[obj]
                self.update_hover_help("subtitles", control_name, description)
                return False
            # Remove Leave handler - help now persists until another control is hovered

        # Handle batch processing tab hover events
        if hasattr(self, 'batch_control_help') and obj in self.batch_control_help:
            if event.type() == QEvent.Type.Enter:
                control_name = self.get_control_display_name(obj, self.batch_control_help)
                func_name = self.batch_control_help[obj]
                self.update_hover_help("batch", control_name, func_name)
                return False
            # Remove Leave handler - help now persists until another control is hovered

        # Handle code analysis tab hover events
        if hasattr(self, 'code_control_help') and obj in self.code_control_help:
            if event.type() == QEvent.Type.Enter:
                control_name = self.get_control_display_name(obj, self.code_control_help)
                func_name = self.code_control_help[obj]
                self.update_hover_help("code", control_name, func_name)
                return False
            # Remove Leave handler - help now persists until another control is hovered

        # Handle analytics tab hover events
        if hasattr(self, 'analytics_control_help') and obj in self.analytics_control_help:
            if event.type() == QEvent.Type.Enter:
                control_name = self.get_control_display_name(obj, self.analytics_control_help)
                func_name = self.analytics_control_help[obj]
                self.update_hover_help("analytics", control_name, func_name)
                return False
            # Remove Leave handler - help now persists until another control is hovered

        # Handle memory tab hover events
        if hasattr(self, 'memory_control_help') and obj in self.memory_control_help:
            if event.type() == QEvent.Type.Enter:
                control_name = self.get_control_display_name(obj, self.memory_control_help)
                func_name = self.memory_control_help[obj]
                self.update_hover_help("memory", control_name, func_name)
                return False
            # Remove Leave handler - help now persists until another control is hovered

        # Handle settings tab hover events
        if hasattr(self, 'settings_control_help') and obj in self.settings_control_help:
            if event.type() == QEvent.Type.Enter:
                control_name = self.get_control_display_name(obj, self.settings_control_help)
                func_name = self.settings_control_help[obj]
                self.update_hover_help("settings", control_name, func_name)
                return False
            # Remove Leave handler - help now persists until another control is hovered

        # Handle tab hover events
        if obj is self.tab_widget:
            if event.type() == QEvent.Type.Enter or event.type() == QEvent.Type.MouseMove:
                # Get the tab index under the mouse
                # PyQt6: Use position().toPoint() for QEnterEvent, pos() for QMouseEvent
                pos = event.position().toPoint() if hasattr(event, 'position') else event.pos()
                tab_index = self.get_tab_under_mouse(pos)
                if tab_index >= 0 and tab_index in self.tab_help:
                    tab_title, tab_description = self.tab_help[tab_index]
                    # Show tab help in the current tab's help pane
                    current_tab = self.tab_widget.currentIndex()
                    if current_tab == 0:  # Organization tab
                        self.org_help_text.setPlainText(f"**{tab_title}**\n\n{tab_description}")
                    elif current_tab == 1:  # Subtitles tab
                        self.sub_help_text.setPlainText(f"**{tab_title}**\n\n{tab_description}")
                    elif current_tab == 2:  # Batch processing tab
                        self.batch_help_text.setPlainText(f"**{tab_title}**\n\n{tab_description}")
                    elif current_tab == 3:  # Code analysis tab
                        self.code_help_text.setPlainText(f"**{tab_title}**\n\n{tab_description}")
                    elif current_tab == 4:  # Analytics tab
                        self.analytics_help_text.setPlainText(f"**{tab_title}**\n\n{tab_description}")
                    # Memory tab removed (was index 5)
                    elif current_tab == 5:  # Settings tab (now index 5)
                        self.settings_help_text.setPlainText(f"**{tab_title}**\n\n{tab_description}")
                return False

        return super().eventFilter(obj, event)
    
    def zoom_in(self):
        """Increase GUI scale."""
        self.zoom_level = min(self.zoom_level + 0.1, self.max_zoom)
        self.apply_zoom()
    
    def zoom_out(self):
        """Decrease GUI scale."""
        self.zoom_level = max(self.zoom_level - 0.1, self.min_zoom)
        self.apply_zoom()
    
    def reset_zoom(self):
        """Reset GUI scale to default."""
        self.zoom_level = 1.0
        self.apply_zoom()
    
    def apply_zoom(self):
        """Apply current zoom level to the application."""
        # Don't change global font - just reapply stylesheet with scaled sizes
        # This keeps tab headers and UI chrome at reasonable sizes
        self.apply_stylesheet()
        
        # Update status bar
        self.status_bar.showMessage(f"Zoom: {int(self.zoom_level * 100)}%", 2000)

    def init_ui(self):
        """Initialize the main UI."""
        self.setWindowTitle(APP_TITLE)
        self.setGeometry(100, 100, WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setMinimumSize(1100, 500)  # Exact fit for compact layout

        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(2, 2, 2, 2)  # Minimal margins for max space
        layout.setSpacing(2)  # Minimal spacing

        # Create menu bar
        self.create_menu_bar()

        # Create toolbar - DISABLED: Redundant, buggy, adds no value
        # self.create_toolbar()

        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # Create tabs
        self.create_organization_tab()
        self.create_subtitles_tab()
        self.create_batch_processing_tab()
        self.create_code_analysis_tab()
        self.create_analytics_tab()
        # Memory tab removed - ChromaDB dependency removed
        self.create_settings_tab()
        
        # Set up tab hover help
        self.setup_tab_hover_help()
        
        # Load settings into UI
        self.load_settings_into_ui()

        # Create status bar
        self.create_status_bar()

    def setup_tab_hover_help(self):
        """Set up hover help for tab headers."""
        self.tab_help = {
            0: ("📁 Organization", """**Media Organization & Management**

This tab is the heart of JellyRancher's media organization capabilities. Use it to:

• **Media Type Selection**: Choose between Movies, TV Shows, Anime, or process all media types
• **Source Folder Setup**: Browse and select folders containing your media files to organize
• **Organization Options**: 
  - Dry-run mode for safe previewing of changes
  - File integrity verification during organization
• **Core Actions**:
  - Scan folders to analyze media structure and count files
  - Organize media files into proper folder hierarchies
  - Analyze episode titles to fix naming inconsistencies
  - Analyze movie names to correct title issues
• **Progress Tracking**: Real-time progress bars and detailed activity logs
• **Snapshot Management**: 
  - Create backup snapshots before major changes
  - View available snapshots with timestamps
  - Restore previous organization states
  - Delete old snapshots to free up space
• **Structure Summary**: Get detailed statistics about your media collection

Perfect for maintaining a well-organized, searchable media library with full backup/rollback capabilities."""),
            
            1: ("📺 Subtitles", """**Subtitle Management & Downloads**

Comprehensive subtitle handling for your media collection:

• **Media Folder Selection**: Choose folders containing video files to check for subtitle coverage
• **Language Configuration**: Select your preferred subtitle language for downloads
• **Provider Management**: Enable/disable multiple subtitle providers:
  - OpenSubtitles.org (largest subtitle database)
  - Subscene (high-quality user-contributed subtitles)  
  - Podnapisi (European language specialist)
• **Operation Modes**:
  - Detection mode: Analyze which files are missing subtitles
  - Live mode: Download and save subtitles immediately
• **Coverage Analysis**: Get detailed reports on subtitle availability across your collection
• **Batch Downloads**: Download missing subtitles for entire folders at once
• **Progress Monitoring**: Track download progress and view detailed operation logs

Ensures your media library has complete subtitle coverage in your preferred languages."""),
            
            2: ("🤖 Batch Processing", """**AI-Powered Batch Operations**

Leverage RavenMaven's AI capabilities for advanced media processing:

• **AI Integration**: Connect to RavenMaven AI for intelligent media analysis
• **Batch Queue Management**: Set up and monitor multiple processing jobs
• **Automated Processing**: Let AI handle complex media organization tasks
• **Queue Monitoring**: Track progress of long-running batch operations
• **Error Handling**: Intelligent retry logic for failed operations
• **Result Analysis**: Review AI-generated processing results and suggestions
• **Performance Metrics**: Monitor processing speed and success rates

Ideal for processing large media collections with minimal manual intervention."""),
            
            3: ("🔍 Code Analysis", """**Code Quality Analysis & Metrics**

Professional code analysis tools powered by CodeCop:

• **Code Quality Scanning**: Analyze Python code for quality issues and metrics
• **Comprehensive Reports**: Generate detailed analysis reports with scores
• **Issue Detection**: Identify code smells, complexity problems, and best practice violations
• **Metric Tracking**: Monitor cyclomatic complexity, maintainability index, and other metrics
• **Trend Analysis**: Track code quality improvements over time
• **Automated Fixes**: Apply suggested code improvements automatically
• **Custom Rules**: Configure analysis rules to match your coding standards
• **Batch Analysis**: Process entire codebases or specific directories

Maintain high code quality standards across your entire project."""),
            
            4: ("📊 Analytics", """**Media Library Analytics & Reporting**

Deep insights into your media collection and system performance:

• **Collection Statistics**: Comprehensive statistics about your media library
  - File counts by type, genre, and quality
  - Storage usage and growth trends
  - Duplicate detection and cleanup opportunities
• **Performance Metrics**: System performance analysis and optimization suggestions
• **Quality Analysis**: Media quality assessments and recommendations
• **Usage Patterns**: Understand how your collection is organized and accessed
• **Trend Reports**: Track changes in your library over time
• **Export Capabilities**: Generate reports for external analysis
• **Visualization**: Charts and graphs showing library composition
• **Health Checks**: Automated checks for common media library issues

Make data-driven decisions about your media collection management."""),
            
            5: ("🧠 Memory", """**Semantic Memory & Document Search**

Intelligent search through processed documents and media information:

• **Semantic Search**: Natural language queries across all processed content
• **Document Indexing**: Search through documentation, code comments, and media metadata
• **Context-Aware Results**: Get relevant results with surrounding context
• **Query History**: Review and reuse previous searches
• **Result Filtering**: Narrow results by content type, date, or relevance
• **Memory Backend**: Powered by ChromaDB for fast, accurate retrieval
• **Integration**: Works with all JellyRancher processing outputs
• **Advanced Queries**: Support for complex search patterns and filters

Find information quickly across your entire knowledge base using natural language."""),
            
            6: ("⚙️ Settings", """**Application Configuration & Preferences**

Complete control over JellyRancher's behavior and integration:

• **API Configuration**: Set up API keys for external services
  - TMDB (The Movie Database) for metadata
  - OpenSubtitles for subtitle downloads
  - Other service integrations
• **Path Management**: Configure default folders and search paths
• **UI Preferences**: Customize interface appearance and behavior
• **Performance Settings**: Adjust processing speed and resource usage
• **Backup Configuration**: Set up automatic backup schedules
• **Logging Options**: Control log verbosity and retention
• **Integration Settings**: Configure connections to external tools
• **Security Options**: Manage credentials and access controls
• **Update Preferences**: Control automatic update checking

Tailor JellyRancher to your specific workflow and environment."""),
        }
        
        # Install event filter on tab widget to catch tab hover events
        self.tab_widget.installEventFilter(self)

    def get_tab_under_mouse(self, pos):
        """Get the tab index under the mouse position."""
        # Get the tab bar
        tab_bar = self.tab_widget.tabBar()
        if tab_bar:
            # Convert position to tab bar coordinates
            tab_bar_pos = tab_bar.mapFrom(self.tab_widget, pos)
            return tab_bar.tabAt(tab_bar_pos)
        return -1

    def create_menu_bar(self):
        """Create application menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu('File')
        
        # Quick Start Guide
        guide_action = file_menu.addAction('🎯 Quick Start Guide...', self.show_quick_start_guide)
        guide_action.setShortcut('F1')
        guide_action.setStatusTip('Show quick start guide (F1)')
        
        file_menu.addSeparator()
        exit_action = file_menu.addAction('Exit', self.close)
        exit_action.setShortcut('Ctrl+Q')

        # Tools menu
        tools_menu = menubar.addMenu('Tools')
        
        # New v2.0.0 features with keyboard shortcuts
        tmdb_action = tools_menu.addAction('📺 Generate TMDB Cache', self.open_tmdb_cache_dialog)
        tmdb_action.setShortcut('Ctrl+T')
        tmdb_action.setStatusTip('Generate TMDB episode cache for TV shows (Ctrl+T)')
        
        wikipedia_action = tools_menu.addAction('🌐 Generate Wikipedia Cache', self.open_wikipedia_cache_dialog)
        wikipedia_action.setShortcut('Ctrl+W')
        wikipedia_action.setStatusTip('Generate episode cache from Wikipedia (Ctrl+W)')
        
        canonical_action = tools_menu.addAction('📊 Build Canonical Database', self.open_canonical_db_dialog)
        canonical_action.setShortcut('Ctrl+D')
        canonical_action.setStatusTip('Build canonical metadata database from analysis file (Ctrl+D)')
        
        episode_action = tools_menu.addAction('🔍 Analyze Episode Titles', self.open_episode_analyzer)
        episode_action.setShortcut('Ctrl+E')
        episode_action.setStatusTip('Analyze and fix TV episode title issues (Ctrl+E)')
        
        movie_action = tools_menu.addAction('🎬 Analyze Movie Names', self.open_movie_analyzer)
        movie_action.setShortcut('Ctrl+M')
        movie_action.setStatusTip('Analyze and fix movie naming issues (Ctrl+M)')
        
        tools_menu.addSeparator()
        
        # Memory Query removed - ChromaDB dependency removed
        
        audit_action = tools_menu.addAction('Audit Log Viewer', self.open_audit_viewer)
        audit_action.setShortcut('Ctrl+L')
        audit_action.setStatusTip('View audit logs and operation history (Ctrl+L)')

        # View menu
        view_menu = menubar.addMenu('View')
        
        zoom_in_action = view_menu.addAction('🔍 Zoom In', self.zoom_in)
        zoom_in_action.setShortcut('Ctrl++')
        zoom_in_action.setStatusTip('Increase UI scale (Ctrl++ or Ctrl+MouseWheel Up)')
        
        zoom_out_action = view_menu.addAction('🔍 Zoom Out', self.zoom_out)
        zoom_out_action.setShortcut('Ctrl+-')
        zoom_out_action.setStatusTip('Decrease UI scale (Ctrl+- or Ctrl+MouseWheel Down)')
        
        reset_zoom_action = view_menu.addAction('↺ Reset Zoom', self.reset_zoom)
        reset_zoom_action.setShortcut('Ctrl+0')
        reset_zoom_action.setStatusTip('Reset UI scale to default (Ctrl+0)')

        # Help menu
        help_menu = menubar.addMenu('Help')
        help_action = help_menu.addAction('Documentation', self.show_documentation)
        help_action.setShortcut('F1')
        help_action.setStatusTip('Open help documentation (F1)')
        
        about_action = help_menu.addAction('About JellyRancher', self.show_about)
        about_action.setShortcut('Ctrl+F1')
        about_action.setStatusTip('Show application information (Ctrl+F1)')

    def create_toolbar(self):
        """Create application toolbar with quick actions."""
        toolbar = self.addToolBar('Quick Actions')
        toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        toolbar.setIconSize(QSize(16, 16))
        toolbar.setMaximumHeight(32)

        # Quick Start Guide
        guide_action = toolbar.addAction('🎯 Quick Start')
        guide_action.triggered.connect(self.show_quick_start_guide)
        guide_action.setStatusTip('Show quick start guide (F1)')
        
        toolbar.addSeparator()

        # Quick actions for common tasks
        scan_action = toolbar.addAction('🔍 Scan Folder')
        scan_action.triggered.connect(self.quick_scan)
        scan_action.setShortcut('Ctrl+S')
        scan_action.setStatusTip('Quick scan for media files (Ctrl+S)')

        organize_action = toolbar.addAction('📁 Organize Media')
        organize_action.triggered.connect(self.quick_organize)
        organize_action.setShortcut('Ctrl+O')
        organize_action.setStatusTip('Quick organize media files (Ctrl+O)')
        
        subtitles_action = toolbar.addAction('💬 Get Subtitles')
        subtitles_action.triggered.connect(self.quick_subtitles)
        subtitles_action.setStatusTip('Quickly download subtitles for a folder')
        
        toolbar.addSeparator()
        
        # Tool to switch to specific tabs
        workflow_action = toolbar.addAction('🚀 Full Workflow')
        workflow_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(0))
        workflow_action.setStatusTip('Switch to full workflow tab')

        toolbar.addSeparator()

        # Memory action removed - ChromaDB dependency removed

    def create_organization_tab(self):
        """Create media organization tab with numbered steps and sub-tabs."""
        tab = QWidget()
        self.tab_widget.addTab(tab, "📁 Organization")

        # Main horizontal layout - split into left panel (controls) and right panel (help)
        main_layout = QHBoxLayout()

        # Left panel - main controls with sub-tabs
        left_panel = QWidget()
        layout = QVBoxLayout()

        # Title and Help
        title_layout = QHBoxLayout()
        title = QLabel("Media Organization Workflow")
        title.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        title_layout.addWidget(title)
        title_layout.addStretch()
        self.org_help_btn = QPushButton("❓ Help")
        self.org_help_btn.clicked.connect(lambda: show_help_dialog(self, "Organization"))
        title_layout.addWidget(self.org_help_btn)
        layout.addLayout(title_layout)

        # Sub-tabs for organized workflow
        self.org_sub_tabs = QTabWidget()
        
        # STEP 1: Setup
        step1_tab = self.create_step1_setup_tab()
        self.org_sub_tabs.addTab(step1_tab, "Step 1: Setup")
        
        # STEP 2: Scan
        step2_tab = self.create_step2_scan_tab()
        self.org_sub_tabs.addTab(step2_tab, "Step 2: Scan")
        
        # STEP 3: Analyze (LLM)
        step3_tab = self.create_step3_analyze_tab()
        self.org_sub_tabs.addTab(step3_tab, "Step 3: Analyze")
        
        # STEP 4: Organize
        step4_tab = self.create_step4_organize_tab()
        self.org_sub_tabs.addTab(step4_tab, "Step 4: Organize")
        
        # STEP 5: Snapshots
        step5_tab = self.create_step5_snapshots_tab()
        self.org_sub_tabs.addTab(step5_tab, "Step 5: Snapshots")
        
        layout.addWidget(self.org_sub_tabs)
        
        left_panel.setLayout(layout)

        # Right panel - split vertically: top = help, bottom = progress
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        right_layout.setSpacing(10)

        # Top: Control Help
        help_group = QGroupBox("💡 Control Help")
        help_layout = QVBoxLayout()
        self.org_help_text = QTextEdit()
        self.org_help_text.setReadOnly(True)
        self.org_help_text.setPlainText("**Welcome to Media Organization**\n\nHover over any control to see detailed help, or hover over tab headers to learn about each section of the application.\n\nThis tab helps you organize your media library by:\n• Scanning folders for media files\n• Organizing movies and TV shows\n• Analyzing and fixing naming issues\n• Managing snapshots for backup/rollback")
        help_layout.addWidget(self.org_help_text)
        help_group.setLayout(help_layout)
        right_layout.addWidget(help_group, 1)  # Takes 50% of vertical space

        # Bottom: Progress & Activity Log
        progress_group = QGroupBox("📊 Progress & Activity Log")
        progress_layout = QVBoxLayout()
        progress_layout.setSpacing(5)
        self.org_progress = QProgressBar()
        progress_layout.addWidget(self.org_progress)
        self.org_log = QTextEdit()
        self.org_log.setPlaceholderText("Activity log will appear here...")
        progress_layout.addWidget(self.org_log)
        progress_group.setLayout(progress_layout)
        right_layout.addWidget(progress_group, 1)  # Takes 50% of vertical space

        right_panel.setLayout(right_layout)
        right_panel.setMaximumWidth(350)
        right_panel.setMinimumWidth(300)

        # Add panels to main layout
        main_layout.addWidget(left_panel, 3)  # 3/4 of width
        main_layout.addWidget(right_panel, 1)  # 1/4 of width

        tab.setLayout(main_layout)

        # Set up hover event handlers
        self.setup_organization_hover_handlers()

    def setup_organization_hover_handlers(self):
        """Set up hover event handlers for organization tab controls."""
        self.org_control_help = {
            # Media type selection
            self.media_type_combo: "Media Type Selector - Choose between Movies, TV Shows, Anime, or All media types to organize",
            
            # Folder selection
            self.org_folder_input: "Source Folder Input - Enter or browse to select the folder containing media files to organize",
            self.org_browse_btn: "Browse Folder Button - Open file dialog to select source media folder",
            
            # Organization options
            self.org_dry_run: "Dry Run Mode - Preview organization changes without actually moving files",
            self.org_verify: "File Verification - Check file integrity during organization process",
            
            # Main action buttons
            self.org_scan_btn: "Scan Folder Button - Analyze media folder structure and count files without organizing",
            self.org_organize_btn: "Organize Media Button - Execute the actual organization of media files",
            self.org_help_btn: "Help Button - Open detailed help documentation for this tab",
            
            # Analysis tools
            self.org_analyze_btn: "Analyze Episodes Button - Open episode title analyzer to fix TV show naming issues",
            self.org_movie_analyze_btn: "Analyze Movies Button - Open movie name analyzer to fix movie naming issues",
            
            # Progress and feedback
            self.org_progress: "Progress Bar - Shows current operation progress percentage",
            self.org_log: "Activity Log - Displays detailed log messages from operations",
            self.org_summary: "Folder Structure Summary - Shows statistics about media files found during scan",
            
            # Snapshot management
            self.snapshot_list: "Snapshots List - Shows available backup snapshots of your media organization",
            self.org_refresh_snapshots_btn: "Refresh Snapshots Button - Reload the list of available snapshots",
            self.org_rollback_btn: "Restore Snapshot Button - Roll back media organization to a previous snapshot",
            self.org_delete_snapshot_btn: "Delete Snapshot Button - Permanently remove a snapshot (cannot be undone)",
        }
        for control in self.org_control_help.keys():
            control.installEventFilter(self)

    def create_step1_setup_tab(self):
        """STEP 1: Initial setup - media type, folder selection, and options."""
        # Create content widget
        content = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Step header
        header = QLabel("STEP 1: Configure Your Source")
        header.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        header.setStyleSheet("color: #2196F3; padding: 5px;")
        layout.addWidget(header)
        
        info = QLabel("Select the media type and folder you want to organize")
        info.setStyleSheet("color: #666; padding: 2px 5px;")
        layout.addWidget(info)
        
        # Media type selection
        type_group = QGroupBox("📂 Media Type")
        type_layout = QVBoxLayout()
        type_layout.setSpacing(5)
        type_layout.addWidget(QLabel("What type of media are you organizing?"))
        self.media_type_combo = QComboBox()
        self.media_type_combo.addItems(["Movies", "TV Shows", "Anime", "All"])
        type_layout.addWidget(self.media_type_combo)
        type_group.setLayout(type_layout)
        layout.addWidget(type_group)
        
        # Folder selection
        folder_group = QGroupBox("📁 Source Folder")
        folder_layout = QVBoxLayout()
        folder_layout.setSpacing(5)
        folder_layout.addWidget(QLabel("Where are your media files located?"))
        folder_select = QHBoxLayout()
        self.org_folder_input = QLineEdit()
        self.org_folder_input.setPlaceholderText("Click Browse to select your media folder...")
        folder_select.addWidget(self.org_folder_input)
        self.org_browse_btn = QPushButton("📂 Browse...")
        self.org_browse_btn.clicked.connect(self.browse_org_folder)
        self.org_browse_btn.setStyleSheet("font-weight: bold;")
        folder_select.addWidget(self.org_browse_btn)
        folder_layout.addLayout(folder_select)
        folder_group.setLayout(folder_layout)
        layout.addWidget(folder_group)
        
        # Options
        options_group = QGroupBox("⚙️ Safety Options")
        options_layout = QVBoxLayout()
        options_layout.setSpacing(5)
        self.org_dry_run = QCheckBox("✓ Dry-run mode (preview changes without moving files)")
        self.org_dry_run.setChecked(True)
        self.org_dry_run.setToolTip("Recommended: See what will happen before actually moving files")
        options_layout.addWidget(self.org_dry_run)
        self.org_verify = QCheckBox("✓ Verify file integrity after operations")
        self.org_verify.setChecked(True)
        self.org_verify.setToolTip("Ensures files aren't corrupted during organization")
        options_layout.addWidget(self.org_verify)
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        # Next step hint
        next_hint = QLabel("➡️ After configuring, go to Step 2: Scan to analyze your media")
        next_hint.setStyleSheet("color: #4CAF50; font-weight: bold; padding: 8px; background: #E8F5E9; border-radius: 5px;")
        layout.addWidget(next_hint)
        
        layout.addStretch()
        content.setLayout(layout)
        
        # Wrap in scroll area to prevent overlapping
        scroll = QScrollArea()
        scroll.setWidget(content)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        # Create container tab
        tab = QWidget()
        tab_layout = QVBoxLayout()
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.addWidget(scroll)
        tab.setLayout(tab_layout)
        
        return tab

    def create_step2_scan_tab(self):
        """STEP 2: Scan folder to analyze media structure."""
        # Create content widget
        content = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Step header
        header = QLabel("STEP 2: Scan Your Media")
        header.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        header.setStyleSheet("color: #2196F3; padding: 5px;")
        layout.addWidget(header)
        
        info = QLabel("Analyze your media folder to see what's inside before organizing")
        info.setStyleSheet("color: #666; padding: 2px 5px;")
        layout.addWidget(info)
        
        # Scan action
        scan_group = QGroupBox("🔍 Scan Operation")
        scan_layout = QVBoxLayout()
        scan_layout.setSpacing(5)
        scan_layout.addWidget(QLabel("Click the button below to scan your media folder:"))
        self.org_scan_btn = QPushButton("🔍 SCAN FOLDER NOW")
        self.org_scan_btn.clicked.connect(self.scan_organization_folder)
        self.org_scan_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold; padding: 8px;")
        scan_layout.addWidget(self.org_scan_btn)
        scan_layout.addWidget(QLabel("\nThis will:"))
        scan_layout.addWidget(QLabel("• Count all media files"))
        scan_layout.addWidget(QLabel("• Identify TV shows and episodes"))
        scan_layout.addWidget(QLabel("• List all movies"))
        scan_layout.addWidget(QLabel("• Show folder structure"))
        scan_group.setLayout(scan_layout)
        layout.addWidget(scan_group)
        
        # Folder Structure Summary
        summary_group = QGroupBox("📊 Scan Results")
        summary_layout = QVBoxLayout()
        summary_layout.setSpacing(5)
        self.org_summary = QTextEdit()
        self.org_summary.setReadOnly(True)
        self.org_summary.setMinimumHeight(200)  # Reduced from 300
        self.org_summary.setPlaceholderText("Scan results will appear here...\n\nYou'll see:\n• TV Shows with episode counts per season\n• Movies organized by title\n• Total file counts and statistics\n• Folder structure summary")
        self.org_summary.setStyleSheet("QTextEdit { font-family: 'Courier New', monospace; font-size: 9pt; }")
        summary_layout.addWidget(self.org_summary)
        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)
        
        # Next step hint
        next_hint = QLabel("➡️ After scanning, go to Step 3: Analyze if you need to fix naming issues")
        next_hint.setStyleSheet("color: #4CAF50; font-weight: bold; padding: 8px; background: #E8F5E9; border-radius: 5px;")
        layout.addWidget(next_hint)
        
        content.setLayout(layout)
        
        # Wrap in scroll area to prevent overlapping
        scroll = QScrollArea()
        scroll.setWidget(content)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        # Create container tab
        tab = QWidget()
        tab_layout = QVBoxLayout()
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.addWidget(scroll)
        tab.setLayout(tab_layout)
        
        return tab

    def create_step3_analyze_tab(self):
        """STEP 3: Analyze and fix naming issues with LLM."""
        # Create content widget
        content = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Step header
        header = QLabel("STEP 3: Analyze & Fix Names (Optional)")
        header.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        header.setStyleSheet("color: #FF9800; padding: 5px;")
        layout.addWidget(header)
        
        info = QLabel("Use AI to identify and fix naming problems in your media files")
        info.setStyleSheet("color: #666; padding: 2px 5px;")
        layout.addWidget(info)
        
        # Why use this step
        why_group = QGroupBox("❓ When to Use This Step")
        why_layout = QVBoxLayout()
        why_layout.setSpacing(3)
        why_layout.addWidget(QLabel("Use LLM analysis if:"))
        why_layout.addWidget(QLabel("✓ Episode titles are incorrect or generic"))
        why_layout.addWidget(QLabel("✓ Movie names don't match the actual film"))
        why_layout.addWidget(QLabel("✓ Files have confusing or corrupted names"))
        why_layout.addWidget(QLabel("✓ You want AI suggestions for better names"))
        why_layout.addWidget(QLabel("\n✗ Skip this step if your files are already named correctly"))
        why_group.setLayout(why_layout)
        layout.addWidget(why_group)
        
        # TV Shows analysis
        tv_group = QGroupBox("📺 TV Show Episode Analysis")
        tv_layout = QVBoxLayout()
        tv_layout.setSpacing(5)
        tv_layout.addWidget(QLabel("Analyze and fix TV show episode titles:"))
        self.org_analyze_btn = QPushButton("🔍 Analyze Episode Titles")
        self.org_analyze_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold; padding: 8px;")
        self.org_analyze_btn.clicked.connect(self.open_episode_analyzer)
        tv_layout.addWidget(self.org_analyze_btn)
        tv_layout.addWidget(QLabel("Opens a window to review and correct episode names using AI"))
        tv_group.setLayout(tv_layout)
        layout.addWidget(tv_group)
        
        # Movies analysis
        movie_group = QGroupBox("🎬 Movie Name Analysis")
        movie_layout = QVBoxLayout()
        movie_layout.setSpacing(5)
        movie_layout.addWidget(QLabel("Analyze and fix movie file names:"))
        self.org_movie_analyze_btn = QPushButton("🎬 Analyze Movie Names")
        self.org_movie_analyze_btn.setStyleSheet("background-color: #FF9800; color: white; font-weight: bold; padding: 8px;")
        self.org_movie_analyze_btn.clicked.connect(self.open_movie_analyzer)
        movie_layout.addWidget(self.org_movie_analyze_btn)
        movie_layout.addWidget(QLabel("Opens a window to review and correct movie names using AI"))
        movie_group.setLayout(movie_layout)
        layout.addWidget(movie_group)
        
        # Next step hint
        next_hint = QLabel("➡️ After fixing names (or skipping), go to Step 4: Organize to move files")
        next_hint.setStyleSheet("color: #4CAF50; font-weight: bold; padding: 8px; background: #E8F5E9; border-radius: 5px;")
        layout.addWidget(next_hint)
        
        layout.addStretch()
        content.setLayout(layout)
        
        # Wrap in scroll area to prevent overlapping
        scroll = QScrollArea()
        scroll.setWidget(content)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        # Create container tab
        tab = QWidget()
        tab_layout = QVBoxLayout()
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.addWidget(scroll)
        tab.setLayout(tab_layout)
        
        return tab

    def create_step4_organize_tab(self):
        """STEP 4: Execute the actual organization."""
        # Create content widget
        content = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Step header
        header = QLabel("STEP 4: Organize Your Media")
        header.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        header.setStyleSheet("color: #4CAF50; padding: 5px;")
        layout.addWidget(header)
        
        info = QLabel("Execute the organization to move files into proper folder structures")
        info.setStyleSheet("color: #666; padding: 2px 5px;")
        layout.addWidget(info)
        
        # Safety reminder
        safety_group = QGroupBox("⚠️ Before You Organize")
        safety_layout = QVBoxLayout()
        safety_layout.setSpacing(5)
        safety_layout.addWidget(QLabel("Important reminders:"))
        safety_layout.addWidget(QLabel("✓ Make sure you've scanned first (Step 2)"))
        safety_layout.addWidget(QLabel("✓ Dry-run mode is enabled by default for safety"))
        safety_layout.addWidget(QLabel("✓ Review the scan results before proceeding"))
        safety_layout.addWidget(QLabel("✓ Snapshots will be created automatically (see Step 5)"))
        safety_group.setLayout(safety_layout)
        layout.addWidget(safety_group)
        
        # Organize action
        organize_group = QGroupBox("📁 Execute Organization")
        organize_layout = QVBoxLayout()
        organize_layout.setSpacing(5)
        organize_layout.addWidget(QLabel("Ready to organize? Click the button below:"))
        self.org_organize_btn = QPushButton("📁 ORGANIZE MEDIA NOW")
        self.org_organize_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 8px;")
        self.org_organize_btn.clicked.connect(self.organize_media)
        organize_layout.addWidget(self.org_organize_btn)
        organize_layout.addWidget(QLabel("\nThis will:"))
        organize_layout.addWidget(QLabel("• Create proper folder structures"))
        organize_layout.addWidget(QLabel("• Move files to correct locations"))
        organize_layout.addWidget(QLabel("• Verify file integrity (if enabled)"))
        organize_layout.addWidget(QLabel("• Create a snapshot automatically"))
        organize_group.setLayout(organize_layout)
        layout.addWidget(organize_group)
        
        # Dry-run vs Live
        mode_group = QGroupBox("🔄 Operation Mode")
        mode_layout = QVBoxLayout()
        mode_layout.setSpacing(5)
        mode_layout.addWidget(QLabel("Current mode: Check Step 1 settings"))
        mode_layout.addWidget(QLabel(""))
        mode_layout.addWidget(QLabel("• DRY-RUN MODE: Preview only, no files moved (SAFE)"))
        mode_layout.addWidget(QLabel("• LIVE MODE: Actually moves files (use after testing)"))
        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)
        
        # Next step hint
        next_hint = QLabel("➡️ After organizing, use Step 5: Snapshots to manage backups")
        next_hint.setStyleSheet("color: #4CAF50; font-weight: bold; padding: 8px; background: #E8F5E9; border-radius: 5px;")
        layout.addWidget(next_hint)
        
        layout.addStretch()
        content.setLayout(layout)
        
        # Wrap in scroll area to prevent overlapping
        scroll = QScrollArea()
        scroll.setWidget(content)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        # Create container tab
        tab = QWidget()
        tab_layout = QVBoxLayout()
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.addWidget(scroll)
        tab.setLayout(tab_layout)
        
        return tab

    def create_step5_snapshots_tab(self):
        """STEP 5: Manage snapshots for backup and rollback."""
        # Create content widget
        content = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Step header
        header = QLabel("STEP 5: Snapshot Management")
        header.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        header.setStyleSheet("color: #9C27B0; padding: 5px;")
        layout.addWidget(header)
        
        info = QLabel("Create, restore, and manage backups of your media organization")
        info.setStyleSheet("color: #666; padding: 2px 5px;")
        layout.addWidget(info)
        
        # What are snapshots
        what_group = QGroupBox("💾 What Are Snapshots?")
        what_layout = QVBoxLayout()
        what_layout.setSpacing(3)
        what_layout.addWidget(QLabel("Snapshots are backup copies of your media folder structure:"))
        what_layout.addWidget(QLabel(""))
        what_layout.addWidget(QLabel("✓ Created automatically before major operations"))
        what_layout.addWidget(QLabel("✓ Allow you to undo organization changes"))
        what_layout.addWidget(QLabel("✓ Stored securely with timestamps"))
        what_layout.addWidget(QLabel("✓ Up to 10 snapshots kept automatically"))
        what_group.setLayout(what_layout)
        layout.addWidget(what_group)
        
        # Snapshot list and management
        manage_group = QGroupBox("📋 Your Snapshots")
        manage_layout = QVBoxLayout()
        manage_layout.setSpacing(5)
        
        # Refresh button
        refresh_layout = QHBoxLayout()
        refresh_layout.addWidget(QLabel("Available snapshots:"))
        refresh_layout.addStretch()
        self.org_refresh_snapshots_btn = QPushButton("🔄 Refresh List")
        self.org_refresh_snapshots_btn.clicked.connect(self.refresh_snapshots)
        refresh_layout.addWidget(self.org_refresh_snapshots_btn)
        manage_layout.addLayout(refresh_layout)
        
        # Snapshot list
        self.snapshot_list = QListWidget()
        self.snapshot_list.setMinimumHeight(150)  # Reduced from 200
        self.snapshot_list.setToolTip("Select a snapshot to restore or delete")
        manage_layout.addWidget(self.snapshot_list)
        
        # Action buttons
        actions_layout = QHBoxLayout()
        self.org_rollback_btn = QPushButton("↩️ Restore Selected Snapshot")
        self.org_rollback_btn.clicked.connect(self.restore_snapshot)
        self.org_rollback_btn.setStyleSheet("background-color: #FF9800; color: white; font-weight: bold; padding: 8px;")
        actions_layout.addWidget(self.org_rollback_btn)
        
        self.org_delete_snapshot_btn = QPushButton("🗑️ Delete Selected Snapshot")
        self.org_delete_snapshot_btn.clicked.connect(self.delete_snapshot)
        self.org_delete_snapshot_btn.setStyleSheet("background-color: #F44336; color: white; padding: 8px;")
        actions_layout.addWidget(self.org_delete_snapshot_btn)
        
        manage_layout.addLayout(actions_layout)
        
        # Warning
        warning = QLabel("⚠️ Restoring a snapshot will revert your media organization to that point in time")
        warning.setStyleSheet("color: #F44336; font-weight: bold; padding: 8px; background: #FFEBEE; border-radius: 5px;")
        manage_layout.addWidget(warning)
        
        manage_group.setLayout(manage_layout)
        layout.addWidget(manage_group)
        
        layout.addStretch()
        content.setLayout(layout)
        
        # Wrap in scroll area to prevent overlapping
        scroll = QScrollArea()
        scroll.setWidget(content)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        # Create container tab
        tab = QWidget()
        tab_layout = QVBoxLayout()
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.addWidget(scroll)
        tab.setLayout(tab_layout)
        
        return tab

    def create_subtitles_tab(self):
        """Create subtitle management tab."""
        tab = QWidget()
        self.tab_widget.addTab(tab, "📺 Subtitles")

        # Main horizontal layout - split into left panel (controls) and right panel (help)
        main_layout = QHBoxLayout()

        # Left panel - main controls
        left_panel = QWidget()
        layout = QVBoxLayout()

        # Title
        title_layout = QHBoxLayout()
        title = QLabel("Subtitle Management")
        title.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        title_layout.addWidget(title)
        title_layout.addStretch()
        help_btn = QPushButton("❓ Help")
        help_btn.clicked.connect(lambda: show_help_dialog(self, "Subtitles"))
        title_layout.addWidget(help_btn)
        layout.addLayout(title_layout)

        # Folder selection
        folder_group = QGroupBox("Media Folder")
        folder_layout = QHBoxLayout()
        self.sub_folder_input = QLineEdit()
        self.sub_folder_input.setPlaceholderText("Select folder with videos...")
        folder_layout.addWidget(self.sub_folder_input)
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_sub_folder)
        folder_layout.addWidget(browse_btn)
        folder_group.setLayout(folder_layout)
        layout.addWidget(folder_group)

        # Language and providers
        config_group = QGroupBox("Configuration")
        config_layout = QHBoxLayout()

        # Language
        lang_layout = QVBoxLayout()
        lang_layout.addWidget(QLabel("Language:"))
        self.sub_language = QComboBox()
        self.sub_language.addItems(["English", "Spanish", "French", "German"])
        lang_layout.addWidget(self.sub_language)
        config_layout.addLayout(lang_layout)

        # Providers
        providers_layout = QVBoxLayout()
        providers_layout.addWidget(QLabel("Providers:"))
        self.provider_checks = {}
        providers = ["OpenSubtitles.org", "Subscene", "Podnapisi"]
        for provider in providers:
            check = QCheckBox(provider)
            check.setChecked(True)
            self.provider_checks[provider] = check
            providers_layout.addWidget(check)
        config_layout.addLayout(providers_layout)

        # Live mode toggle
        live_layout = QVBoxLayout()
        live_layout.addWidget(QLabel("Mode:"))
        self.sub_live_mode = QCheckBox("Live mode (write files)")
        self.sub_live_mode.setChecked(False)
        live_layout.addWidget(self.sub_live_mode)
        config_layout.addLayout(live_layout)

        config_layout.addStretch()
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)

        # Progress
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout()
        self.sub_progress = QProgressBar()
        progress_layout.addWidget(self.sub_progress)
        self.sub_log = QTextEdit()
        self.sub_log.setMaximumHeight(200)
        progress_layout.addWidget(self.sub_log)
        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)

        # Actions
        actions_layout = QHBoxLayout()
        detect_btn = QPushButton("🔍 Detect Coverage")
        detect_btn.clicked.connect(self.detect_subtitle_coverage)
        actions_layout.addWidget(detect_btn)

        download_btn = QPushButton("📥 Download Subtitles")
        download_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
        download_btn.clicked.connect(self.download_subtitles)
        actions_layout.addWidget(download_btn)

        actions_layout.addStretch()
        layout.addLayout(actions_layout)

        layout.addStretch()
        left_panel.setLayout(layout)

        # Right panel - contextual help pane
        right_panel = QWidget()
        right_layout = QVBoxLayout()

        help_title = QLabel("Control Help")
        help_title.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        right_layout.addWidget(help_title)

        self.sub_help_text = QTextEdit()
        self.sub_help_text.setReadOnly(True)
        self.sub_help_text.setPlainText("**Welcome to Subtitle Management**\n\nHover over any control to see detailed help.\n\nThis tab helps you manage subtitles by:\n• Detecting which media files are missing subtitles\n• Downloading subtitles from multiple providers\n• Managing subtitle file organization")
        self.sub_help_text.setMaximumWidth(350)
        self.sub_help_text.setMinimumWidth(300)
        right_layout.addWidget(self.sub_help_text)

        right_panel.setLayout(right_layout)

        # Add panels to main layout
        main_layout.addWidget(left_panel, 3)  # 3/4 of width
        main_layout.addWidget(right_panel, 1)  # 1/4 of width

        tab.setLayout(main_layout)

        # Set up hover event handlers
        self.setup_subtitles_hover_handlers()

    def setup_subtitles_hover_handlers(self):
        """Set up hover event handlers for subtitles tab controls."""
        self.sub_control_help = {
            self.sub_folder_input: "Media Folder Input - Select the folder containing video files to check for subtitle coverage",
            self.sub_language: "Language Selector - Choose the language for subtitle downloads",
            self.sub_live_mode: "Live Mode Toggle - When enabled, downloaded subtitles are saved to disk immediately",
            self.sub_progress: "Progress Bar - Shows subtitle detection or download progress",
            self.sub_log: "Activity Log - Displays detailed messages from subtitle operations",
        }
        # Add provider checkboxes
        for provider_name, checkbox in self.provider_checks.items():
            self.sub_control_help[checkbox] = f"{provider_name} Provider - Enable/disable subtitle downloads from {provider_name}"
        
        for control in self.sub_control_help.keys():
            control.installEventFilter(self)

    def setup_batch_processing_hover_handlers(self):
        """Set up hover event handlers for batch processing tab controls."""
        # TODO: Map controls to function names
        self.batch_control_help = {}
        for control in self.batch_control_help.keys():
            control.installEventFilter(self)

    def create_batch_processing_tab(self):
        """Create RavenMaven batch processing tab."""
        tab = QWidget()
        self.tab_widget.addTab(tab, "⚙️ Batch Processing")

        # Main horizontal layout - split into left panel (controls) and right panel (help)
        main_layout = QHBoxLayout()

        # Left panel - main controls
        left_panel = QWidget()
        layout = QVBoxLayout()

        # Title
        title_layout = QHBoxLayout()
        title = QLabel("AI-Powered Batch Processing")
        title.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        title_layout.addWidget(title)
        title_layout.addStretch()
        help_btn = QPushButton("❓ Help")
        help_btn.clicked.connect(lambda: show_help_dialog(self, "Batch"))
        title_layout.addWidget(help_btn)
        layout.addLayout(title_layout)

        # Source folder
        source_group = QGroupBox("Source Directory")
        source_layout = QHBoxLayout()
        self.batch_source_input = QLineEdit()
        self.batch_source_input.setPlaceholderText("Select folder to process...")
        source_layout.addWidget(self.batch_source_input)
        self.batch_browse_btn = QPushButton("Browse...")
        self.batch_browse_btn.clicked.connect(self.browse_batch_source)
        source_layout.addWidget(self.batch_browse_btn)
        source_group.setLayout(source_layout)
        layout.addWidget(source_group)

        # AI Configuration
        ai_group = QGroupBox("AI Configuration")
        ai_layout = QHBoxLayout()
        self.batch_model_label = QLabel("Model:")
        ai_layout.addWidget(self.batch_model_label)
        self.batch_model_combo = QComboBox()
        self.batch_model_combo.addItems(["GPT-4", "Claude-3", "Gemini Pro"])
        ai_layout.addWidget(self.batch_model_combo)
        self.batch_prompt_label = QLabel("Prompt:")
        ai_layout.addWidget(self.batch_prompt_label)
        self.batch_prompt_input = QLineEdit()
        self.batch_prompt_input.setPlaceholderText("Custom prompt or template...")
        ai_layout.addWidget(self.batch_prompt_input)
        ai_group.setLayout(ai_layout)
        layout.addWidget(ai_group)

        # Processing options
        options_group = QGroupBox("Processing Options")
        options_layout = QHBoxLayout()
        self.batch_dry_run = QCheckBox("Dry-run mode")
        self.batch_dry_run.setChecked(True)
        options_layout.addWidget(self.batch_dry_run)
        self.batch_chunk_label = QLabel("Chunk size:")
        options_layout.addWidget(self.batch_chunk_label)
        self.batch_chunk_size = QSpinBox()
        self.batch_chunk_size.setValue(50)
        self.batch_chunk_size.setMinimum(10)
        self.batch_chunk_size.setMaximum(500)
        options_layout.addWidget(self.batch_chunk_size)
        options_layout.addStretch()
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)

        # Progress and preview
        progress_group = QGroupBox("Progress & Preview")
        progress_layout = QVBoxLayout()
        self.batch_progress = QProgressBar()
        progress_layout.addWidget(self.batch_progress)
        self.batch_log = QTextEdit()
        self.batch_log.setMaximumHeight(150)
        progress_layout.addWidget(self.batch_log)

        # Editable Action Table (ENHANCED!)
        action_table_group = QGroupBox("📋 Editable Action Plan")
        action_table_layout = QVBoxLayout()

        # Toolbar for table operations
        toolbar_layout = QHBoxLayout()

        bulk_select_label = QLabel("Bulk Select:")
        toolbar_layout.addWidget(bulk_select_label)

        select_all_btn = QPushButton("✓ All")
        select_all_btn.clicked.connect(lambda: self.batch_bulk_select(True))
        toolbar_layout.addWidget(select_all_btn)

        select_none_btn = QPushButton("✗ None")
        select_none_btn.clicked.connect(lambda: self.batch_bulk_select(False))
        toolbar_layout.addWidget(select_none_btn)

        toolbar_layout.addWidget(QLabel(" | Filter:"))

        self.batch_filter_input = QLineEdit()
        self.batch_filter_input.setPlaceholderText("Filter by filename...")
        self.batch_filter_input.textChanged.connect(self.batch_filter_actions)
        toolbar_layout.addWidget(self.batch_filter_input)

        toolbar_layout.addWidget(QLabel(" | "))

        export_plan_btn = QPushButton("📤 Export Plan")
        export_plan_btn.clicked.connect(self.batch_export_plan)
        toolbar_layout.addWidget(export_plan_btn)

        import_plan_btn = QPushButton("📥 Import Plan")
        import_plan_btn.clicked.connect(self.batch_import_plan)
        toolbar_layout.addWidget(import_plan_btn)

        toolbar_layout.addStretch()
        action_table_layout.addLayout(toolbar_layout)

        # The editable table
        self.batch_action_table = QTableWidget()
        self.batch_action_table.setColumnCount(6)
        self.batch_action_table.setHorizontalHeaderLabels([
            "✓", "Filename", "Current Path", "Proposed Path", "Action", "Status"
        ])
        self.batch_action_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.batch_action_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)  # We'll use dropdowns
        self.batch_action_table.horizontalHeader().setStretchLastSection(False)
        self.batch_action_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Checkbox
        self.batch_action_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)  # Filename
        self.batch_action_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Current
        self.batch_action_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)  # Proposed
        self.batch_action_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Action
        self.batch_action_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Status
        action_table_layout.addWidget(self.batch_action_table)

        action_table_group.setLayout(action_table_layout)
        progress_layout.addWidget(action_table_group)

        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)

        # Actions
        actions_layout = QHBoxLayout()
        self.batch_analyze_btn = QPushButton("🧠 AI Analysis")
        self.batch_analyze_btn.clicked.connect(self.run_batch_analysis)
        actions_layout.addWidget(self.batch_analyze_btn)

        self.batch_execute_btn = QPushButton("⚡ Execute Batch")
        self.batch_execute_btn.setStyleSheet("background-color: #FF9800; color: white; font-weight: bold;")
        self.batch_execute_btn.clicked.connect(self.execute_batch)
        actions_layout.addWidget(self.batch_execute_btn)

        actions_layout.addStretch()
        layout.addLayout(actions_layout)

        layout.addStretch()
        left_panel.setLayout(layout)

        # Right panel - contextual help pane
        right_panel = QWidget()
        right_layout = QVBoxLayout()

        help_title = QLabel("Control Help")
        help_title.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        right_layout.addWidget(help_title)

        self.batch_help_text = QTextEdit()
        self.batch_help_text.setReadOnly(True)
        self.batch_help_text.setPlainText("Hover over any control to see its explanation here.")
        self.batch_help_text.setMaximumWidth(350)
        self.batch_help_text.setMinimumWidth(300)
        right_layout.addWidget(self.batch_help_text)

        right_panel.setLayout(right_layout)

        # Add panels to main layout
        main_layout.addWidget(left_panel, 3)  # 3/4 of width
        main_layout.addWidget(right_panel, 1)  # 1/4 of width

        tab.setLayout(main_layout)

        # Set up hover event handlers
        self.setup_batch_processing_hover_handlers()

    def setup_code_analysis_hover_handlers(self):
        """Set up hover event handlers for code analysis tab controls."""
        # TODO: Map controls to function names
        self.code_analysis_control_help = {}
        for control in self.code_analysis_control_help.keys():
            control.installEventFilter(self)


    def create_code_analysis_tab(self):
        """Create CodeCop code analysis tab."""
        tab = QWidget()
        self.tab_widget.addTab(tab, "🔍 Code Analysis")

        # Main horizontal layout - split into left panel (controls) and right panel (help)
        main_layout = QHBoxLayout()

        # Left panel - main controls
        left_panel = QWidget()
        layout = QVBoxLayout()

        # Title
        title_layout = QHBoxLayout()
        title = QLabel("Code Quality Analysis")
        title.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        title_layout.addWidget(title)
        title_layout.addStretch()
        help_btn = QPushButton("❓ Help")
        help_btn.clicked.connect(lambda: show_help_dialog(self, "Code"))
        title_layout.addWidget(help_btn)
        layout.addLayout(title_layout)

        # Analysis scope
        scope_group = QGroupBox("Analysis Scope")
        scope_layout = QHBoxLayout()
        self.code_target_label = QLabel("Target:")
        scope_layout.addWidget(self.code_target_label)
        self.code_target_combo = QComboBox()
        self.code_target_combo.addItems(["Current Project", "Custom Folder", "Specific Files"])
        scope_layout.addWidget(self.code_target_combo)
        self.code_target_input = QLineEdit()
        self.code_target_input.setPlaceholderText("Select target...")
        scope_layout.addWidget(self.code_target_input)
        self.code_browse_btn = QPushButton("Browse...")
        self.code_browse_btn.clicked.connect(self.browse_code_target)
        scope_layout.addWidget(self.code_browse_btn)
        scope_group.setLayout(scope_layout)
        layout.addWidget(scope_group)

        # Analysis options
        options_group = QGroupBox("Analysis Options")
        options_layout = QVBoxLayout()
        self.code_metrics_check = QCheckBox("Code metrics (complexity, coverage)")
        self.code_metrics_check.setChecked(True)
        options_layout.addWidget(self.code_metrics_check)
        self.code_structure_check = QCheckBox("Structure analysis")
        self.code_structure_check.setChecked(True)
        options_layout.addWidget(self.code_structure_check)
        self.code_docs_check = QCheckBox("Documentation coverage")
        self.code_docs_check.setChecked(True)
        options_layout.addWidget(self.code_docs_check)
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)

        # Progress and results
        results_group = QGroupBox("Analysis Results")
        results_layout = QVBoxLayout()
        self.code_progress = QProgressBar()
        results_layout.addWidget(self.code_progress)
        self.code_results = QTextEdit()
        results_layout.addWidget(self.code_results)
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)

        # Actions
        actions_layout = QHBoxLayout()
        self.code_analyze_btn = QPushButton("🔍 Run Analysis")
        self.code_analyze_btn.clicked.connect(self.run_code_analysis)
        actions_layout.addWidget(self.code_analyze_btn)

        self.code_report_btn = QPushButton("📊 Generate Report")
        self.code_report_btn.clicked.connect(self.generate_code_report)
        actions_layout.addWidget(self.code_report_btn)

        actions_layout.addStretch()
        layout.addLayout(actions_layout)

        layout.addStretch()
        left_panel.setLayout(layout)

        # Right panel - contextual help pane
        right_panel = QWidget()
        right_layout = QVBoxLayout()

        help_title = QLabel("Control Help")
        help_title.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        right_layout.addWidget(help_title)

        self.code_help_text = QTextEdit()
        self.code_help_text.setReadOnly(True)
        self.code_help_text.setPlainText("Hover over any control to see its explanation here.")
        self.code_help_text.setMaximumWidth(350)
        self.code_help_text.setMinimumWidth(300)
        right_layout.addWidget(self.code_help_text)

        right_panel.setLayout(right_layout)

        # Add panels to main layout
        main_layout.addWidget(left_panel, 3)  # 3/4 of width
        main_layout.addWidget(right_panel, 1)  # 1/4 of width

        tab.setLayout(main_layout)

        # Set up hover event handlers
        self.setup_code_analysis_hover_handlers()

    def setup_analytics_hover_handlers(self):
        """Set up hover event handlers for analytics tab controls."""
        # TODO: Map controls to function names
        self.analytics_control_help = {}
        for control in self.analytics_control_help.keys():
            control.installEventFilter(self)


    def create_analytics_tab(self):
        """Create analytics and reporting tab."""
        tab = QWidget()
        self.tab_widget.addTab(tab, "📊 Analytics")

        # Main horizontal layout - split into left panel (controls) and right panel (help)
        main_layout = QHBoxLayout()

        # Left panel - main controls
        left_panel = QWidget()
        layout = QVBoxLayout()

        # Title
        title_layout = QHBoxLayout()
        title = QLabel("Analytics & Reporting")
        title.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        title_layout.addWidget(title)
        title_layout.addStretch()
        help_btn = QPushButton("❓ Help")
        help_btn.clicked.connect(lambda: show_help_dialog(self, "Analytics"))
        title_layout.addWidget(help_btn)
        layout.addLayout(title_layout)

        # Statistics overview
        stats_group = QGroupBox("System Statistics")
        stats_layout = QFormLayout()
        self.stats_total_files = QLabel("0")
        self.stats_total_size = QLabel("0 GB")
        self.stats_last_scan = QLabel("Never")
        self.stats_audit_entries = QLabel("0")
        stats_layout.addRow("Total Files:", self.stats_total_files)
        stats_layout.addRow("Total Size:", self.stats_total_size)
        stats_layout.addRow("Last Scan:", self.stats_last_scan)
        stats_layout.addRow("Audit Entries:", self.stats_audit_entries)
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

        # Report tabs
        self.analytics_tabs = QTabWidget()

        # Organization report
        org_tab = QWidget()
        org_layout = QVBoxLayout()
        self.org_report_text = QTextEdit()
        self.org_report_text.setReadOnly(True)
        org_layout.addWidget(self.org_report_text)
        org_tab.setLayout(org_layout)
        self.analytics_tabs.addTab(org_tab, "Organization")

        # Subtitle report
        sub_tab = QWidget()
        sub_layout = QVBoxLayout()
        self.sub_report_text = QTextEdit()
        self.sub_report_text.setReadOnly(True)
        sub_layout.addWidget(self.sub_report_text)
        sub_tab.setLayout(sub_layout)
        self.analytics_tabs.addTab(sub_tab, "Subtitles")

        # Activity timeline
        timeline_tab = QWidget()
        timeline_layout = QVBoxLayout()
        self.timeline_text = QTextEdit()
        self.timeline_text.setReadOnly(True)
        timeline_layout.addWidget(self.timeline_text)
        timeline_tab.setLayout(timeline_layout)
        self.analytics_tabs.addTab(timeline_tab, "Timeline")

        layout.addWidget(self.analytics_tabs)

        # Actions
        actions_layout = QHBoxLayout()
        self.analytics_refresh_btn = QPushButton("🔄 Refresh Data")
        self.analytics_refresh_btn.clicked.connect(self.refresh_analytics)
        actions_layout.addWidget(self.analytics_refresh_btn)

        self.analytics_export_btn = QPushButton("📤 Export Report")
        self.analytics_export_btn.clicked.connect(self.export_analytics_report)
        actions_layout.addWidget(self.analytics_export_btn)

        actions_layout.addStretch()
        layout.addLayout(actions_layout)

        layout.addStretch()
        left_panel.setLayout(layout)

        # Right panel - contextual help pane
        right_panel = QWidget()
        right_layout = QVBoxLayout()

        help_title = QLabel("Control Help")
        help_title.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        right_layout.addWidget(help_title)

        self.analytics_help_text = QTextEdit()
        self.analytics_help_text.setReadOnly(True)
        self.analytics_help_text.setPlainText("Hover over any control to see its explanation here.")
        self.analytics_help_text.setMaximumWidth(350)
        self.analytics_help_text.setMinimumWidth(300)
        right_layout.addWidget(self.analytics_help_text)

        right_panel.setLayout(right_layout)

        # Add panels to main layout
        main_layout.addWidget(left_panel, 3)  # 3/4 of width
        main_layout.addWidget(right_panel, 1)  # 1/4 of width

        tab.setLayout(main_layout)

        # Set up hover event handlers
        self.setup_analytics_hover_handlers()

    def setup_memory_hover_handlers(self):
        """Set up hover event handlers for memory tab controls."""
        # TODO: Map controls to function names
        self.memory_control_help = {}
        for control in self.memory_control_help.keys():
            control.installEventFilter(self)

    # Memory tab removed - ChromaDB dependency removed from project

    def setup_settings_hover_handlers(self):
        """Set up hover event handlers for settings tab controls."""
        # TODO: Map controls to function names
        self.settings_control_help = {}
        for control in self.settings_control_help.keys():
            control.installEventFilter(self)


    def create_settings_tab(self):
        """Create settings and configuration tab."""
        tab = QWidget()
        self.tab_widget.addTab(tab, "⚙️ Settings")

        # Main horizontal layout - split into left panel (controls) and right panel (help)
        main_layout = QHBoxLayout()

        # Left panel - main controls
        left_panel = QWidget()
        layout = QVBoxLayout()

        # Title
        title_layout = QHBoxLayout()
        title = QLabel("Settings & Configuration")
        title.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        title_layout.addWidget(title)
        title_layout.addStretch()
        help_btn = QPushButton("❓ Help")
        help_btn.clicked.connect(lambda: show_help_dialog(self, "Settings"))
        title_layout.addWidget(help_btn)
        layout.addLayout(title_layout)

        # Media paths
        paths_group = QGroupBox("Media Paths")
        paths_layout = QFormLayout()
        self.settings_media_root = QLineEdit()
        self.settings_media_root.setText(self.settings.get("media_root", ""))
        paths_layout.addRow("Media Root:", self.settings_media_root)
        self.settings_movies_folder = QLineEdit()
        self.settings_movies_folder.setText(self.settings.get("movies_folder", "Movies"))
        paths_layout.addRow("Movies Folder:", self.settings_movies_folder)
        self.settings_tv_folder = QLineEdit()
        self.settings_tv_folder.setText(self.settings.get("tv_shows_folder", "TV Shows"))
        paths_layout.addRow("TV Shows Folder:", self.settings_tv_folder)
        paths_group.setLayout(paths_layout)
        layout.addWidget(paths_group)

        # API Credentials
        creds_group = QGroupBox("API Credentials")
        creds_layout = QVBoxLayout()

        # TMDB API Key
        tmdb_layout = QHBoxLayout()
        self.settings_tmdb_label = QLabel("TMDB API Key:")
        tmdb_layout.addWidget(self.settings_tmdb_label)
        self.settings_tmdb_api_key = QLineEdit()
        self.settings_tmdb_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.settings_tmdb_api_key.setPlaceholderText("Enter your TMDB API key")
        tmdb_api_key = self.settings.get_tmdb_api_key()
        if tmdb_api_key:
            self.settings_tmdb_api_key.setText(tmdb_api_key)
        tmdb_layout.addWidget(self.settings_tmdb_api_key)

        self.settings_show_key_btn = QPushButton("👁️")
        self.settings_show_key_btn.setFixedWidth(40)
        self.settings_show_key_btn.setCheckable(True)
        self.settings_show_key_btn.toggled.connect(
            lambda checked: self.settings_tmdb_api_key.setEchoMode(
                QLineEdit.Normal if checked else QLineEdit.EchoMode.Password
            )
        )
        tmdb_layout.addWidget(self.settings_show_key_btn)

        self.settings_test_key_btn = QPushButton("Test")
        self.settings_test_key_btn.clicked.connect(self.test_tmdb_api_key)
        tmdb_layout.addWidget(self.settings_test_key_btn)

        self.settings_get_key_btn = QPushButton("Get Key")
        self.settings_get_key_btn.clicked.connect(
            lambda: QDesktopServices.openUrl(
                QUrl("https://www.themoviedb.org/settings/api")
            )
        )
        tmdb_layout.addWidget(self.settings_get_key_btn)

        creds_layout.addLayout(tmdb_layout)

        self.settings_tmdb_help = QLabel("ℹ️ Get a free API key from TMDB to generate episode caches")
        self.settings_tmdb_help.setStyleSheet("color: #666; font-size: 11pt;")
        creds_layout.addWidget(self.settings_tmdb_help)

        creds_layout.addSpacing(10)

        # Other credentials
        self.creds_status = QLabel("Credentials status will be shown here")
        creds_layout.addWidget(self.creds_status)
        self.settings_manage_creds_btn = QPushButton("Manage Credentials")
        self.settings_manage_creds_btn.clicked.connect(self.manage_credentials)
        creds_layout.addWidget(self.settings_manage_creds_btn)
        creds_group.setLayout(creds_layout)
        layout.addWidget(creds_group)

        # Preferences
        prefs_group = QGroupBox("Preferences")
        prefs_layout = QFormLayout()
        self.pref_dry_run = QCheckBox("Enable dry-run by default")
        self.pref_dry_run.setChecked(self.settings.get("enable_dry_run", True))
        prefs_layout.addRow("Safety:", self.pref_dry_run)
        self.pref_verify = QCheckBox("Verify file integrity")
        self.pref_verify.setChecked(self.settings.get("verify_integrity", True))
        prefs_layout.addRow("Verification:", self.pref_verify)
        prefs_group.setLayout(prefs_layout)
        layout.addWidget(prefs_group)

        # Actions
        actions_layout = QHBoxLayout()
        self.settings_save_btn = QPushButton("💾 Save Settings")
        self.settings_save_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.settings_save_btn.clicked.connect(self.save_settings)
        actions_layout.addWidget(self.settings_save_btn)

        self.settings_reset_btn = QPushButton("🔄 Reset to Defaults")
        self.settings_reset_btn.clicked.connect(self.reset_settings)
        actions_layout.addWidget(self.settings_reset_btn)

        actions_layout.addStretch()
        layout.addLayout(actions_layout)

        layout.addStretch()
        left_panel.setLayout(layout)

        # Right panel - contextual help pane
        right_panel = QWidget()
        right_layout = QVBoxLayout()

        help_title = QLabel("Control Help")
        help_title.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        right_layout.addWidget(help_title)

        self.settings_help_text = QTextEdit()
        self.settings_help_text.setReadOnly(True)
        self.settings_help_text.setPlainText("Hover over any control to see its explanation here.")
        self.settings_help_text.setMaximumWidth(350)
        self.settings_help_text.setMinimumWidth(300)
        right_layout.addWidget(self.settings_help_text)

        right_panel.setLayout(right_layout)

        # Add panels to main layout
        main_layout.addWidget(left_panel, 3)  # 3/4 of width
        main_layout.addWidget(right_panel, 1)  # 1/4 of width

        tab.setLayout(main_layout)

        # Load initial data
        self.update_credentials_status()

        # Set up hover event handlers
        self.setup_settings_hover_handlers()

    def create_status_bar(self):
        """Create application status bar."""
        self.status_bar = self.statusBar()
        self.status_bar.setMaximumHeight(18)  # Compact status bar
        self.status_bar.showMessage("Ready")

    def apply_stylesheet(self):
        """Apply application stylesheet with proper UI font sizes."""
        # Font sizes following UI best practices - scaled by zoom
        # Tabs should stay readable, so we don't scale them as aggressively
        tab_font_size = int(9 * max(0.9, self.zoom_level))  # Min 8pt for tabs
        body_font_size = int(9 * self.zoom_level)  # Body text
        button_font_size = int(9 * self.zoom_level)  # Buttons
        groupbox_font_size = int(9 * self.zoom_level)  # GroupBox titles
        
        # Padding scales with zoom but has minimums
        button_padding = max(3, int(4 * self.zoom_level))
        tab_padding_v = max(4, int(5 * self.zoom_level))
        tab_padding_h = max(8, int(10 * self.zoom_level))
        
        style = f"""
        QMainWindow {{
            background-color: #f5f5f5;
            font-size: {body_font_size}pt;
        }}
        QTabWidget::pane {{
            border: 1px solid #cccccc;
        }}
        QTabBar::tab {{
            background-color: #e0e0e0;
            border: 1px solid #cccccc;
            padding: {tab_padding_v}px {tab_padding_h}px;
            font-size: {tab_font_size}pt;
            font-weight: normal;
            min-width: 120px;
        }}
        QTabBar::tab:selected {{
            background-color: #f5f5f5;
            border-bottom-color: #f5f5f5;
            font-weight: bold;
        }}
        QTabBar::tab:hover {{
            background-color: #d5d5d5;
        }}
        QGroupBox {{
            border: 1px solid #cccccc;
            border-radius: 3px;
            margin-top: 8px;
            padding-top: 8px;
            font-weight: bold;
            font-size: {groupbox_font_size}pt;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 2px 5px;
        }}
        QPushButton {{
            padding: {button_padding}px {button_padding * 2}px;
            background-color: #e0e0e0;
            border: 1px solid #999999;
            border-radius: 3px;
            font-weight: 500;
            min-height: 20px;
            font-size: {button_font_size}pt;
        }}
        QPushButton:hover {{
            background-color: #d0d0d0;
        }}
        QPushButton:pressed {{
            background-color: #c0c0c0;
        }}
        QLineEdit {{
            padding: {button_padding}px;
            border: 1px solid #cccccc;
            border-radius: 3px;
            font-size: {body_font_size}pt;
            background-color: white;
        }}
        QComboBox {{
            padding: {button_padding}px;
            border: 1px solid #cccccc;
            border-radius: 3px;
            font-size: {body_font_size}pt;
            background-color: white;
        }}
        QLabel {{
            font-size: {body_font_size}pt;
        }}
        QTextEdit, QListWidget {{
            font-size: {body_font_size}pt;
            border: 1px solid #cccccc;
            border-radius: 3px;
        }}
        QProgressBar {{
            border: 1px solid #cccccc;
            border-radius: 4px;
            text-align: center;
            height: 20px;
            font-size: {body_font_size}pt;
        }}
        QProgressBar::chunk {{
            background-color: #4CAF50;
        }}
        """
        self.setStyleSheet(style)

    # Event handlers and functionality would continue here...
    # This is a starting template - full implementation would include all the methods

    def browse_org_folder(self):
        """Browse for organization source folder."""
        folder = QFileDialog.getExistingDirectory(self, "Select Media Folder")
        if folder:
            self.org_folder_input.setText(folder)

    def scan_organization_folder(self):
        """Scan folder for media organization and generate structure summary."""
        folder = self.org_folder_input.text().strip()
        if not folder:
            QMessageBox.warning(self, "Input Error", "Please select a folder first")
            return

        self.org_log.clear()
        self.org_summary.clear()
        self.org_progress.setValue(0)

        # Import scanner
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent / "media"))
        from media_scanner import MediaFileScanner

        try:
            self.org_log.append("🔍 Scanning folder...")
            self.org_progress.setValue(10)

            # Scan files
            scanner = MediaFileScanner(folder)
            files = scanner.scan_files()

            self.org_log.append(f"📂 Found {len(files)} files")
            self.org_progress.setValue(40)

            # Analyze structure
            self.org_log.append("📊 Analyzing folder structure...")
            structure = scanner.analyze_folder_structure(files)

            self.org_progress.setValue(70)

            # Format and display summary
            summary = scanner.format_structure_summary(structure)
            self.org_summary.setPlainText(summary)

            self.org_log.append("✅ Structure analysis complete!")
            self.org_progress.setValue(100)

            # Store for later use
            self.current_scan_files = files
            self.current_scan_structure = structure

        except Exception as e:
            self.org_log.append(f"❌ Error: {str(e)}")
            QMessageBox.critical(self, "Scan Error", f"Failed to scan folder:\n{str(e)}")

    def update_org_log(self, message: str):
        """Update organization log."""
        cursor = self.org_log.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.org_log.setTextCursor(cursor)
        self.org_log.insertPlainText(f"{datetime.now().strftime('%H:%M:%S')} - {message}\n")

    def on_org_operation_complete(self, success: bool, message: str):
        """Handle organization operation completion."""
        if success:
            self.org_progress.setValue(100)
            QMessageBox.information(self, "Success", message)
        else:
            QMessageBox.critical(self, "Error", message)

    def organize_media(self):
        """Organize media files."""
        folder = self.org_folder_input.text().strip() if hasattr(self, 'org_folder_input') else ''
        if not folder:
            QMessageBox.warning(self, "Folder", "Select a folder or register managed folders first.")
            return
        self.org_log.clear()
        self.org_progress.setValue(0)
        organizer = MediaOrganizer()

        def progress(msg: str, pct: int):
            self.org_progress.setValue(pct)
            cursor = self.org_log.textCursor()
            cursor.movePosition(QTextCursor.End)
            self.org_log.setTextCursor(cursor)
            self.org_log.insertPlainText(f"{datetime.now().strftime('%H:%M:%S')} - {msg}\n")

        result = organizer.organize(
            folder_path=folder,
            org_type=self.media_type_combo.currentText(),
            dry_run=self.org_dry_run.isChecked(),
            create_snapshot=True,
            verify_integrity=self.org_verify.isChecked(),
            progress_callback=progress
        )
        self.org_log.insertPlainText(f"\nResult: {result}\n")
        if result.get("success"):
            QMessageBox.information(self, "Organize", f"Organized {result.get('files_moved',0)} media files")
            # Auto-journal organization action
            self.journal_action(
                f"Organized {result.get('files_moved',0)} files in {folder} ({self.media_type_combo.currentText()})",
                ["organization", self.media_type_combo.currentText().lower().replace(' ', '-')]
            )
        else:
            QMessageBox.critical(self, "Organize", f"Errors: {result.get('errors')}\n{result.get('error_details','')}")

    # Additional method stubs for completeness
    def browse_sub_folder(self):
        """Open a folder dialog to select media folder for subtitles."""
        path = QFileDialog.getExistingDirectory(self, "Select Media Folder", str(Path.home()))
        if path:
            self.sub_folder_input.setText(path)
    def detect_subtitle_coverage(self):
        """Run coverage detection via SubtitleBackend with progress updates."""
        folder = self.sub_folder_input.text().strip()
        if not folder:
            QMessageBox.warning(self, "Folder", "Select a media folder first.")
            return
        self.sub_log.clear()
        self.sub_progress.setValue(0)
        backend = SubtitleBackend()

        def progress(msg: str, pct: int):
            self.sub_progress.setValue(pct)
            cursor = self.sub_log.textCursor()
            cursor.movePosition(QTextCursor.End)
            self.sub_log.setTextCursor(cursor)
            self.sub_log.insertPlainText(f"{datetime.now().strftime('%H:%M:%S')} - {msg}\n")

        stats = backend.detect_coverage(folder, language=self.sub_language.currentText(), progress_callback=progress)
        summary = stats.to_dict()
        self.sub_log.insertPlainText(f"\nCoverage Summary: {summary}\n")
        QMessageBox.information(self, "Coverage", f"Coverage: {summary.get('coverage_percent',0):.1f}%")

    def download_subtitles(self):
        """Download subtitles using SubtitleBackend with progress updates (dry-run)."""
        folder = self.sub_folder_input.text().strip()
        if not folder:
            QMessageBox.warning(self, "Folder", "Select a media folder first.")
            return
        self.sub_log.clear()
        self.sub_progress.setValue(0)
        backend = SubtitleBackend()
        providers = [p for p, chk in self.provider_checks.items() if chk.isChecked()]
        language = self.sub_language.currentText()

        def progress(msg: str, pct: int):
            self.sub_progress.setValue(pct)
            cursor = self.sub_log.textCursor()
            cursor.movePosition(QTextCursor.End)
            self.sub_log.setTextCursor(cursor)
            self.sub_log.insertPlainText(f"{datetime.now().strftime('%H:%M:%S')} - {msg}\n")

        result = backend.download_subtitles(
            folder_path=folder,
            language=language,
            providers=providers,
            dry_run=not self.sub_live_mode.isChecked(),
            progress_callback=progress
        )
        self.sub_log.insertPlainText(f"\nResult: {result}\n")
        if result.get("success"):
            QMessageBox.information(self, "Download", f"Downloaded {result.get('downloaded')} subtitles")
            # Auto-journal subtitle action
            self.journal_action(f"Downloaded {result.get('downloaded')} subtitles for {folder} ({language})", ["subtitles", "download"])
        else:
            QMessageBox.critical(self, "Download", f"Errors: {result.get('errors')}\n{result.get('error','')}" )

    def browse_batch_source(self):
        """Browse for batch source folder."""
        path = QFileDialog.getExistingDirectory(self, "Select Source Folder", str(Path.home()))
        if path:
            self.batch_source_input.setText(path)
    def run_batch_analysis(self):
        """Analyze source folder and preview proposed structure using MediaFileScanner."""
        source = self.batch_source_input.text().strip()
        if not source:
            QMessageBox.warning(self, "Source", "Select a source folder to analyze.")
            return
        self.batch_log.clear()
        self.batch_progress.setValue(0)
        try:
            from media_scanner import MediaFileScanner  # RavenMaven component
        except Exception as e:
            self.batch_log.setPlainText(f"Missing RavenMaven scanner: {e}")
            return

        try:
            self.batch_log.append("🔍 Analyzing source...")
            self.batch_progress.setValue(20)

            scanner = MediaFileScanner(source)
            files = scanner.scan_files()
            ops = scanner.generate_reorganization_plan(files)

            self.batch_log.append(f"📂 Scanned {len(files)} files")
            self.batch_log.append(f"📋 Proposed {len(ops)} operations")
            self.batch_progress.setValue(50)

            # Populate editable action table
            self.batch_action_table.setRowCount(len(ops))

            for row, op in enumerate(ops):
                # Checkbox
                checkbox = QCheckBox()
                checkbox.setChecked(True)
                checkbox_widget = QWidget()
                checkbox_layout = QHBoxLayout(checkbox_widget)
                checkbox_layout.addWidget(checkbox)
                checkbox_layout.setAlignment(Qt.AlignCenter)
                checkbox_layout.setContentsMargins(0, 0, 0, 0)
                self.batch_action_table.setCellWidget(row, 0, checkbox_widget)

                # Filename
                filename = Path(op['source']).name
                self.batch_action_table.setItem(row, 1, QTableWidgetItem(filename))

                # Current path
                current_path = str(Path(op['source']).parent)
                self.batch_action_table.setItem(row, 2, QTableWidgetItem(current_path))

                # Proposed path
                proposed_path = str(Path(op['destination']).parent)
                self.batch_action_table.setItem(row, 3, QTableWidgetItem(proposed_path))

                # Action dropdown
                action_combo = QComboBox()
                action_combo.addItems(["Move", "Copy", "Skip", "Delete", "Review"])
                action_combo.setCurrentText(op.get('operation', 'move').title())
                self.batch_action_table.setCellWidget(row, 4, action_combo)

                # Status
                self.batch_action_table.setItem(row, 5, QTableWidgetItem("Ready"))

                # Store full operation data
                self.batch_action_table.item(row, 1).setData(Qt.UserRole, op)

            self.batch_log.append("✅ Action table populated!")
            self.batch_progress.setValue(100)

            # Store operations for execution
            self.current_batch_ops = ops

        except Exception as e:
            self.batch_log.append(f"❌ Analysis failed: {e}")
            QMessageBox.critical(self, "Analysis Error", str(e))

    def batch_bulk_select(self, enable: bool):
        """Select or deselect all checkboxes in the batch action table."""
        for row in range(self.batch_action_table.rowCount()):
            checkbox_widget = self.batch_action_table.cellWidget(row, 0)
            if checkbox_widget:
                checkbox = checkbox_widget.findChild(QCheckBox)
                if checkbox:
                    checkbox.setChecked(enable)

        action = "Selected" if enable else "Deselected"
        self.batch_log.append(f"{action} all {self.batch_action_table.rowCount()} actions")

    def batch_filter_actions(self):
        """Filter action table rows based on filename search."""
        filter_text = self.batch_filter_input.text().strip().lower()

        visible_count = 0
        for row in range(self.batch_action_table.rowCount()):
            filename_item = self.batch_action_table.item(row, 1)
            if filename_item:
                filename = filename_item.text().lower()
                should_show = filter_text in filename if filter_text else True
                self.batch_action_table.setRowHidden(row, not should_show)
                if should_show:
                    visible_count += 1

        if filter_text:
            self.batch_log.append(f"Filter: showing {visible_count} of {self.batch_action_table.rowCount()} actions")

    def batch_export_plan(self):
        """Export action plan to JSON file."""
        if self.batch_action_table.rowCount() == 0:
            QMessageBox.warning(self, "Export", "No action plan to export. Run analysis first.")
            return

        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Export Action Plan",
            "batch_action_plan.json",
            "JSON Files (*.json)"
        )

        if not filepath:
            return

        try:
            plan = []
            for row in range(self.batch_action_table.rowCount()):
                # Get checkbox state
                checkbox_widget = self.batch_action_table.cellWidget(row, 0)
                checkbox = checkbox_widget.findChild(QCheckBox) if checkbox_widget else None
                enabled = checkbox.isChecked() if checkbox else False

                # Get stored operation data
                filename_item = self.batch_action_table.item(row, 1)
                op_data = filename_item.data(Qt.UserRole) if filename_item else {}

                # Get action dropdown value
                action_combo = self.batch_action_table.cellWidget(row, 4)
                action = action_combo.currentText() if action_combo else "Move"

                # Build plan entry
                entry = {
                    'enabled': enabled,
                    'filename': filename_item.text() if filename_item else "",
                    'source': op_data.get('source', ''),
                    'destination': op_data.get('destination', ''),
                    'action': action,
                    'status': self.batch_action_table.item(row, 5).text() if self.batch_action_table.item(row, 5) else "Ready"
                }
                plan.append(entry)

            # Write to file
            import json
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(plan, f, indent=2, ensure_ascii=False)

            self.batch_log.append(f"✅ Exported {len(plan)} actions to: {filepath}")
            QMessageBox.information(self, "Export Complete", f"Action plan exported to:\n{filepath}")

        except Exception as e:
            self.batch_log.append(f"❌ Export failed: {e}")
            QMessageBox.critical(self, "Export Error", f"Failed to export action plan:\n{str(e)}")

    def batch_import_plan(self):
        """Import action plan from JSON file."""
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Import Action Plan",
            "",
            "JSON Files (*.json)"
        )

        if not filepath:
            return

        try:
            import json
            from pathlib import Path

            with open(filepath, 'r', encoding='utf-8') as f:
                plan = json.load(f)

            if not isinstance(plan, list):
                raise ValueError("Invalid plan format: expected list of actions")

            # Clear existing table
            self.batch_action_table.setRowCount(0)
            self.batch_action_table.setRowCount(len(plan))

            for row, entry in enumerate(plan):
                # Checkbox
                checkbox = QCheckBox()
                checkbox.setChecked(entry.get('enabled', True))
                checkbox_widget = QWidget()
                checkbox_layout = QHBoxLayout(checkbox_widget)
                checkbox_layout.addWidget(checkbox)
                checkbox_layout.setAlignment(Qt.AlignCenter)
                checkbox_layout.setContentsMargins(0, 0, 0, 0)
                self.batch_action_table.setCellWidget(row, 0, checkbox_widget)

                # Filename
                filename_item = QTableWidgetItem(entry.get('filename', ''))
                # Store operation data
                op_data = {
                    'source': entry.get('source', ''),
                    'destination': entry.get('destination', ''),
                    'operation': entry.get('action', 'move').lower()
                }
                filename_item.setData(Qt.UserRole, op_data)
                self.batch_action_table.setItem(row, 1, filename_item)

                # Current path
                current_path = str(Path(entry.get('source', '')).parent) if entry.get('source') else ""
                self.batch_action_table.setItem(row, 2, QTableWidgetItem(current_path))

                # Proposed path
                proposed_path = str(Path(entry.get('destination', '')).parent) if entry.get('destination') else ""
                self.batch_action_table.setItem(row, 3, QTableWidgetItem(proposed_path))

                # Action dropdown
                action_combo = QComboBox()
                action_combo.addItems(["Move", "Copy", "Skip", "Delete", "Review"])
                action_combo.setCurrentText(entry.get('action', 'Move'))
                self.batch_action_table.setCellWidget(row, 4, action_combo)

                # Status
                self.batch_action_table.setItem(row, 5, QTableWidgetItem(entry.get('status', 'Ready')))

            self.batch_log.append(f"✅ Imported {len(plan)} actions from: {filepath}")
            QMessageBox.information(self, "Import Complete", f"Loaded {len(plan)} actions from plan file")

        except Exception as e:
            self.batch_log.append(f"❌ Import failed: {e}")
            QMessageBox.critical(self, "Import Error", f"Failed to import action plan:\n{str(e)}")

    def execute_batch(self):
        """Execute batch operations with safety confirmation and snapshot."""
        dry_run = self.batch_dry_run.isChecked()

        # Collect enabled operations from action table
        operations = []
        for row in range(self.batch_action_table.rowCount()):
            # Check if row is enabled
            checkbox_widget = self.batch_action_table.cellWidget(row, 0)
            checkbox = checkbox_widget.findChild(QCheckBox) if checkbox_widget else None

            if not checkbox or not checkbox.isChecked():
                continue  # Skip disabled operations

            # Get action type
            action_combo = self.batch_action_table.cellWidget(row, 4)
            action = action_combo.currentText() if action_combo else "Move"

            # Skip operations marked as "Skip" or "Review"
            if action in ["Skip", "Review"]:
                continue

            # Get operation data
            filename_item = self.batch_action_table.item(row, 1)
            if filename_item:
                op_data = filename_item.data(Qt.UserRole)
                if op_data:
                    operations.append({
                        'source': op_data.get('source', ''),
                        'destination': op_data.get('destination', ''),
                        'action': action.lower(),
                        'filename': filename_item.text(),
                        'row': row
                    })

        if len(operations) == 0:
            QMessageBox.warning(self, "Batch", "No operations to execute. Enable some actions in the table first.")
            return

        total = len(operations)

        # Count by action type
        action_counts = {}
        for op in operations:
            action = op['action']
            action_counts[action] = action_counts.get(action, 0) + 1

        action_summary = ", ".join([f"{count} {action}" for action, count in action_counts.items()])

        if dry_run:
            self.batch_log.append(f"🔍 Dry-run: would execute {total} operations ({action_summary})")
            for op in operations:
                self.batch_log.append(f"  [{op['action'].upper()}] {op['filename']}")
            QMessageBox.information(self, "Batch", f"Dry-run complete.\n\n{total} operations planned:\n{action_summary}")
            return

        # Confirm live execution
        reply = QMessageBox.question(
            self,
            "Confirm Batch Execution",
            f"Execute {total} operations?\n\n{action_summary}\n\nA snapshot will be created for rollback.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        # Create snapshot
        source = self.batch_source_input.text().strip()
        try:
            snapshot_id = SnapshotManager.create_snapshot(
                media_root=source,
                snapshot_type="pre_batch_execution"
            )
            self.batch_log.append(f"📸 Snapshot created: {snapshot_id}")
        except Exception as e:
            QMessageBox.critical(self, "Snapshot Failed", f"Could not create snapshot: {e}")
            return

        # Execute operations
        try:
            import shutil
            from pathlib import Path

            success_count = 0
            failed_count = 0

            self.batch_log.append(f"⚡ Executing {total} operations...")
            self.batch_progress.setValue(0)

            for i, op in enumerate(operations):
                try:
                    source_path = Path(op['source'])
                    dest_path = Path(op['destination'])
                    action = op['action']
                    row = op['row']

                    # Create destination directory if needed
                    dest_path.parent.mkdir(parents=True, exist_ok=True)

                    # Execute based on action type
                    if action == 'move':
                        shutil.move(str(source_path), str(dest_path))
                        status_msg = "✅ Moved"
                    elif action == 'copy':
                        shutil.copy2(str(source_path), str(dest_path))
                        status_msg = "✅ Copied"
                    elif action == 'delete':
                        source_path.unlink()
                        status_msg = "🗑️ Deleted"
                    else:
                        status_msg = "⚠️ Unknown action"

                    # Update table status
                    status_item = self.batch_action_table.item(row, 5)
                    if status_item:
                        status_item.setText(status_msg)

                    self.batch_log.append(f"{status_msg}: {op['filename']}")
                    success_count += 1

                except Exception as e:
                    # Update table status
                    status_item = self.batch_action_table.item(op['row'], 5)
                    if status_item:
                        status_item.setText(f"❌ Failed")

                    self.batch_log.append(f"❌ Failed: {op['filename']} - {str(e)}")
                    failed_count += 1

                # Update progress
                progress = int(((i + 1) / total) * 100)
                self.batch_progress.setValue(progress)

            # Summary
            self.batch_log.append("")
            self.batch_log.append(f"✅ Execution complete: {success_count} succeeded, {failed_count} failed")

            if failed_count > 0:
                QMessageBox.warning(
                    self,
                    "Batch Complete with Errors",
                    f"Execution complete:\n\n✅ {success_count} succeeded\n❌ {failed_count} failed\n\nSnapshot: {snapshot_id}"
                )
            else:
                QMessageBox.information(
                    self,
                    "Batch Complete",
                    f"All {success_count} operations completed successfully!\n\nSnapshot: {snapshot_id}"
                )

            self.journal_action(f"Batch execution: {success_count} succeeded, {failed_count} failed (snapshot: {snapshot_id})", ["batch", "execution"])

        except Exception as e:
            self.batch_log.append(f"❌ Execution error: {e}")
            QMessageBox.critical(self, "Execution Failed", str(e))
    def browse_code_target(self):
        """Browse for code analysis target folder."""
        folder = QFileDialog.getExistingDirectory(self, "Select Code Folder")
        if folder:
            self.code_target_input.setText(folder)

    def run_code_analysis(self):
        """Run code analysis on selected target."""
        target = self.code_target_input.text().strip()
        if not target:
            QMessageBox.warning(self, "Input Required", "Please select a target folder for analysis.")
            return

        if not os.path.exists(target):
            QMessageBox.warning(self, "Invalid Path", f"Path does not exist:\n{target}")
            return

        self.code_results.setPlainText("Scanning Python files...\n")
        self.code_progress.setValue(10)

        try:
            # Scan for Python files
            py_files = []
            for root, dirs, files in os.walk(target):
                # Skip virtual environments and caches
                dirs[:] = [d for d in dirs if d not in ['.venv', 'venv', '__pycache__', '.git', 'node_modules']]
                for file in files:
                    if file.endswith('.py'):
                        py_files.append(os.path.join(root, file))

            if not py_files:
                self.code_results.setPlainText(f"No Python files found in:\n{target}")
                self.code_progress.setValue(100)
                return

            self.code_progress.setValue(30)

            # Analyze files
            total_lines = 0
            total_functions = 0
            total_classes = 0
            files_with_docstrings = 0
            issues = []

            for i, filepath in enumerate(py_files):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        lines = content.split('\n')
                        total_lines += len(lines)

                    # Parse with AST
                    tree = ast.parse(content, filename=filepath)

                    # Count functions and classes
                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef):
                            total_functions += 1
                            # Check for docstring
                            if not ast.get_docstring(node):
                                issues.append(f"{os.path.basename(filepath)}:{node.lineno} - Function '{node.name}' missing docstring")
                        elif isinstance(node, ast.ClassDef):
                            total_classes += 1
                            if not ast.get_docstring(node):
                                issues.append(f"{os.path.basename(filepath)}:{node.lineno} - Class '{node.name}' missing docstring")

                    # Check if file has module docstring
                    if ast.get_docstring(tree):
                        files_with_docstrings += 1

                except Exception as e:
                    issues.append(f"{os.path.basename(filepath)} - Parse error: {str(e)}")

                # Update progress
                progress = 30 + int((i / len(py_files)) * 60)
                self.code_progress.setValue(progress)

            # Generate report
            doc_coverage = (files_with_docstrings / len(py_files) * 100) if py_files else 0

            results = f"""Code Analysis Results for: {target}

Files Analyzed: {len(py_files)} Python files
Total Lines: {total_lines:,}
Total Functions: {total_functions}
Total Classes: {total_classes}

Documentation Coverage:
  Files with module docstrings: {files_with_docstrings}/{len(py_files)} ({doc_coverage:.1f}%)

"""

            if self.code_docs_check.isChecked() and issues:
                results += f"\nDocumentation Issues ({len(issues)}):\n"
                # Show first 20 issues
                for issue in issues[:20]:
                    results += f"  • {issue}\n"
                if len(issues) > 20:
                    results += f"\n  ... and {len(issues) - 20} more issues\n"

            self.code_results.setPlainText(results)
            self.code_progress.setValue(100)

        except Exception as e:
            QMessageBox.critical(self, "Analysis Failed", f"Error during analysis:\n{str(e)}")
            self.code_results.setPlainText(f"Analysis failed: {str(e)}")
            self.code_progress.setValue(0)

    def generate_code_report(self):
        """Generate and save code analysis report."""
        if not self.code_results.toPlainText() or "Running" in self.code_results.toPlainText():
            QMessageBox.warning(self, "No Results", "Please run code analysis first.")
            return

        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Code Report", "", "Text Files (*.txt);;Markdown Files (*.md)"
        )
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.code_results.toPlainText())
                QMessageBox.information(self, "Success", f"Report saved to:\n{filename}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save report:\n{str(e)}")
    def refresh_analytics(self):
        """Populate analytics with current statistics and reports."""
        try:
            # Update system stats (placeholder - would query audit log and scan results)
            self.stats_total_files.setText("Calculating...")
            self.stats_last_scan.setText(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            
            # Subtitle coverage summary
            sub_summary = (
                "Subtitle Coverage Summary\n"
                "==========================\n\n"
                "Run subtitle detection on folders to populate this report.\n\n"
                "Coverage by folder:\n"
                "  (No data yet)\n\n"
                "To generate coverage data:\n"
                "1. Go to Subtitles tab\n"
                "2. Select a media folder\n"
                "3. Click 'Detect Coverage'\n"
            )
            self.sub_report_text.setPlainText(sub_summary)
            
            # Organization summary
            org_summary = (
                "Organization Summary\n"
                "====================\n\n"
                "Run organization scans to populate this report.\n\n"
                "Recent operations:\n"
                "  (No data yet)\n\n"
                "Snapshots available:\n"
            )
            try:
                snapshots = SnapshotManager.list_snapshots()
                if snapshots:
                    for snap in snapshots[:5]:
                        org_summary += f"  • {snap['id']} ({snap['type']}) - {snap['total_media']} files\n"
                else:
                    org_summary += "  (No snapshots)\n"
            except Exception:
                org_summary += "  (Snapshot listing unavailable)\n"
            
            self.org_report_text.setPlainText(org_summary)
            
            # Activity timeline (ChromaDB removed)
            timeline = "Recent Activity\n===============\n\n"
            timeline += "(ChromaDB semantic search has been removed)\n"
            timeline += "(Memory/journal features disabled)\n"
            
            self.timeline_text.setPlainText(timeline)
            
            self.stats_total_files.setText("Analytics refreshed")
            QMessageBox.information(self, "Analytics", "Analytics refreshed successfully")
            
        except Exception as e:
            QMessageBox.critical(self, "Analytics Error", f"Failed to refresh: {e}")
    def export_analytics_report(self):
        """Export analytics data to a file."""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Analytics Report", "analytics_report.txt",
            "Text Files (*.txt);;Markdown Files (*.md);;CSV Files (*.csv)"
        )
        if filename:
            try:
                # Gather analytics data
                report = f"""Analytics Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'='*60}

System Statistics:
- Total Files: {self.stats_total_files.text()}
- Last Scan: {self.stats_last_scan.text()}

Subtitle Coverage:
{self.subtitle_coverage.toPlainText()}

Media Quality:
{self.media_quality.toPlainText()}

Recent Activity:
{self.recent_activity.toPlainText()}
"""
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(report)
                QMessageBox.information(self, "Success", f"Analytics report exported to:\n{filename}")
            except Exception as e:
                QMessageBox.critical(self, "Export Failed", f"Failed to export report:\n{str(e)}")

    # Memory tab functions removed - ChromaDB dependency removed from project

    def manage_credentials(self):
        """Open credential management dialog with full add/edit/delete functionality."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent / "_common"))

        try:
            from credential_manager import CredentialManager
            cred_mgr = CredentialManager()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load credential manager:\n{str(e)}")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Credential Manager")
        dialog.setMinimumWidth(600)
        dialog.setMinimumHeight(500)

        layout = QVBoxLayout()

        # Credential list
        list_group = QGroupBox("Stored Credentials")
        list_layout = QVBoxLayout()

        cred_list = QListWidget()

        def refresh_list():
            cred_list.clear()
            cred_list.addItem("TMDB API Key (managed in Settings)")
            stored_creds = cred_mgr.list_credentials()
            for cred_key in stored_creds:
                cred_list.addItem(cred_key)

        refresh_list()

        list_layout.addWidget(cred_list)

        # Delete button
        delete_btn = QPushButton("🗑️ Delete Selected")
        def delete_credential():
            current_item = cred_list.currentItem()
            if not current_item:
                return
            cred_key = current_item.text()
            if cred_key == "TMDB API Key (managed in Settings)":
                QMessageBox.information(dialog, "Info", "TMDB API Key is managed in Settings tab.")
                return

            reply = QMessageBox.question(
                dialog, "Confirm Delete",
                f"Delete credential '{cred_key}'?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                if cred_mgr.delete_credential(cred_key):
                    refresh_list()
                    QMessageBox.information(dialog, "Success", f"Deleted '{cred_key}'")
                else:
                    QMessageBox.warning(dialog, "Failed", "Failed to delete credential")

        delete_btn.clicked.connect(delete_credential)
        list_layout.addWidget(delete_btn)

        list_group.setLayout(list_layout)
        layout.addWidget(list_group)

        # Add new credential section
        add_group = QGroupBox("Add/Update Credential")
        add_layout = QFormLayout()

        key_input = QLineEdit()
        key_input.setPlaceholderText("e.g., opensubtitles_username, jellyfin_api_key")
        add_layout.addRow("Credential Key:", key_input)

        value_input = QLineEdit()
        value_input.setEchoMode(QLineEdit.EchoMode.Password)
        value_input.setPlaceholderText("Enter value (username, password, or API key)")
        add_layout.addRow("Value:", value_input)

        show_value_btn = QPushButton("👁️")
        show_value_btn.setFixedWidth(40)
        show_value_btn.setCheckable(True)
        show_value_btn.toggled.connect(
            lambda checked: value_input.setEchoMode(QLineEdit.Normal if checked else QLineEdit.EchoMode.Password)
        )

        value_layout = QHBoxLayout()
        value_layout.addWidget(value_input)
        value_layout.addWidget(show_value_btn)
        add_layout.addRow("", value_layout)

        def save_credential():
            key = key_input.text().strip()
            value = value_input.text().strip()

            if not key:
                QMessageBox.warning(dialog, "Input Required", "Please enter a credential key.")
                return

            if not value:
                QMessageBox.warning(dialog, "Input Required", "Please enter a value.")
                return

            try:
                cred_mgr.set_credential(key, value)
                refresh_list()
                key_input.clear()
                value_input.clear()
                QMessageBox.information(dialog, "Success", f"Credential '{key}' saved successfully.")
            except Exception as e:
                QMessageBox.critical(dialog, "Error", f"Failed to save credential:\n{str(e)}")

        add_btn = QPushButton("💾 Save Credential")
        add_btn.clicked.connect(save_credential)
        add_layout.addRow("", add_btn)

        add_group.setLayout(add_layout)
        layout.addWidget(add_group)

        # Help text
        help_text = QLabel(
            "💡 Credentials are encrypted and stored securely.\n"
            "Examples: opensubtitles_username, opensubtitles_password, jellyfin_url, jellyfin_api_key"
        )
        help_text.setWordWrap(True)
        help_text.setStyleSheet("color: #666; font-size: 10pt; padding: 10px;")
        layout.addWidget(help_text)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)

        dialog.setLayout(layout)
        dialog.exec()
    def save_settings(self):
        """Save current settings from UI to settings backend."""
        try:
            # Save TMDB API key
            api_key = self.settings_tmdb_api_key.text().strip()
            self.settings.set_tmdb_api_key(api_key)
            
            # Save to file
            if self.settings.save():
                QMessageBox.information(
                    self,
                    "Settings Saved",
                    "Settings have been saved successfully."
                )
                self.logger.info("Settings saved successfully")
            else:
                QMessageBox.warning(
                    self,
                    "Save Failed",
                    "Failed to save settings. Check logs for details."
                )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Error saving settings: {str(e)}"
            )
            self.logger.error(f"Error saving settings: {str(e)}")
    
    def load_settings_into_ui(self):
        """Load settings from backend into UI fields."""
        try:
            # Load TMDB API key
            tmdb_key = self.settings.get_tmdb_api_key()
            if tmdb_key:
                self.settings_tmdb_api_key.setText(tmdb_key)
            
            self.logger.info("Settings loaded into UI")
        except Exception as e:
            self.logger.error(f"Error loading settings into UI: {str(e)}")
    
    def reset_settings(self):
        """Reset all settings to default values."""
        reply = QMessageBox.question(
            self,
            "Reset Settings",
            "Are you sure you want to reset all settings to defaults?\n\nThis will clear:\n- TMDB API Key\n- All preferences\n\nThis action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                # Clear settings
                self.settings_tmdb_api_key.clear()
                self.pref_dry_run.setChecked(True)
                self.pref_verify.setChecked(True)

                # Reset backend
                self.settings.set_tmdb_api_key("")
                self.settings.save()

                QMessageBox.information(
                    self,
                    "Reset Complete",
                    "Settings have been reset to defaults."
                )
                self.logger.info("Settings reset to defaults")
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Reset Failed",
                    f"Failed to reset settings:\n{str(e)}"
                )
                self.logger.error(f"Error resetting settings: {str(e)}")
    
    def update_credentials_status(self): pass
    
    def test_tmdb_api_key(self):
        """Test the TMDB API key by attempting validation."""
        api_key = self.settings_tmdb_api_key.text().strip()
        
        if not api_key:
            QMessageBox.warning(
                self,
                "No API Key",
                "Please enter a TMDB API key first."
            )
            return
        
        try:
            # Test the API key using tmdb_backend
            from tmdb_backend import TMDBBackend
            
            tmdb = TMDBBackend()
            tmdb.set_api_key(api_key)
            
            if tmdb.validate_api_key():
                QMessageBox.information(
                    self,
                    "Success",
                    "✅ TMDB API key is valid!"
                )
                self.logger.info("TMDB API key validation successful")
            else:
                QMessageBox.warning(
                    self,
                    "Invalid Key",
                    "❌ TMDB API key is invalid. Please check and try again."
                )
                self.logger.warning("TMDB API key validation failed")
        
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Error testing API key: {str(e)}"
            )
            self.logger.error(f"Error testing TMDB API key: {str(e)}")

    # Menu actions removed: open_memory_query - ChromaDB dependency removed
    
    def open_tmdb_cache_dialog(self):
        """Open the TMDB Cache Generator dialog."""
        try:
            from dialogs.tmdb_cache_dialog import TMDBCacheDialog
            
            dialog = TMDBCacheDialog(self)
            result = dialog.exec()
            
            if result == QDialog.Accepted:
                self.logger.info("TMDB cache generation completed successfully")
                self.status_bar.showMessage("TMDB cache generated successfully", 3000)
            else:
                self.logger.info("TMDB cache dialog cancelled")
        
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Error opening TMDB Cache Generator:\n{str(e)}"
            )
            self.logger.error(f"Error opening TMDB cache dialog: {str(e)}")
    
    def open_episode_analyzer(self):
        """Open the Episode Title Analyzer dialog."""
        try:
            from dialogs.episode_analysis_dialog import EpisodeAnalysisDialog
            
            dialog = EpisodeAnalysisDialog(self)
            result = dialog.exec()
            
            if result == QDialog.Accepted:
                results = dialog.get_results()
                if results:
                    issues = results.get('issues_found', 0)
                    if issues > 0:
                        self.logger.info(f"Episode analysis found {issues} issues")
                        self.status_bar.showMessage(f"Analysis complete: {issues} issues found", 3000)
                    else:
                        self.logger.info("Episode analysis found no issues")
                        self.status_bar.showMessage("Analysis complete: No issues found", 3000)
            else:
                self.logger.info("Episode analyzer cancelled")
        
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Error opening Episode Analyzer:\n{str(e)}"
            )
            self.logger.error(f"Error opening episode analyzer: {str(e)}")
    
    def open_movie_analyzer(self):
        """Open the Movie Name Analyzer dialog."""
        try:
            from dialogs.movie_analysis_dialog import MovieAnalysisDialog
            
            dialog = MovieAnalysisDialog(self)
            result = dialog.exec()
            
            if result == QDialog.Accepted:
                results = dialog.get_results()
                if results:
                    summary = results.get('summary', {})
                    total = results.get('total_files', 0)
                    issues = total - summary.get('no_issues', 0)
                    
                    if issues > 0:
                        self.logger.info(f"Movie analysis found {issues}/{total} movies with issues")
                        self.status_bar.showMessage(
                            f"Analysis complete: {issues}/{total} movies have issues", 
                            3000
                        )
                    else:
                        self.logger.info(f"Movie analysis found no issues in {total} movies")
                        self.status_bar.showMessage(
                            f"Analysis complete: {total} movies, no issues found", 
                            3000
                        )
            else:
                self.logger.info("Movie analyzer cancelled")
        
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Error opening Movie Analyzer:\n{str(e)}"
            )
            self.logger.error(f"Error opening movie analyzer: {str(e)}")

    def journal_action(self, text: str, tags: List[str]):
        """Auto-journal removed - ChromaDB dependency removed from project."""
        pass  # Silently skip journaling

    def refresh_snapshots(self):
        """Refresh snapshot list in Organization tab."""
        try:
            self.snapshot_list.clear()
            snapshots = SnapshotManager.list_snapshots()
            for snap in snapshots:
                item_text = f"{snap['id']} | {snap['type']} | {snap['total_media']} files | {snap['timestamp']}"
                self.snapshot_list.addItem(item_text)
            if not snapshots:
                self.snapshot_list.addItem("(No snapshots available)")
        except Exception as e:
            QMessageBox.critical(self, "Snapshot Error", f"Failed to list snapshots: {e}")

    def restore_snapshot(self):
        """Restore selected snapshot."""
        selected = self.snapshot_list.currentItem()
        if not selected or selected.text().startswith("(No"):
            QMessageBox.warning(self, "Selection", "Select a snapshot to restore.")
            return

        # Extract snapshot ID (first part before |)
        snapshot_id = selected.text().split("|")[0].strip()

        reply = QMessageBox.question(
            self,
            "Confirm Restore",
            f"Restore snapshot {snapshot_id}?\n\nThis will verify files against the snapshot state.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                result = SnapshotManager.restore_snapshot(snapshot_id, dry_run=True)
                msg = f"Snapshot verification:\n\nVerified: {result['restored_files']}\nErrors: {len(result['errors'])}"
                if result['errors']:
                    msg += f"\n\nFirst errors:\n" + "\n".join(result['errors'][:5])
                QMessageBox.information(self, "Restore Complete", msg)
                self.journal_action(f"Restored snapshot {snapshot_id}", ["snapshot", "rollback"])
            except Exception as e:
                QMessageBox.critical(self, "Restore Failed", str(e))

    def delete_snapshot(self):
        """Delete selected snapshot."""
        selected = self.snapshot_list.currentItem()
        if not selected or selected.text().startswith("(No"):
            QMessageBox.warning(self, "Selection", "Select a snapshot to delete.")
            return

        snapshot_id = selected.text().split("|")[0].strip()

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Delete snapshot {snapshot_id}?\n\nThis cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            if SnapshotManager.delete_snapshot(snapshot_id):
                QMessageBox.information(self, "Deleted", f"Snapshot {snapshot_id} deleted.")
                self.refresh_snapshots()
            else:
                QMessageBox.warning(self, "Not Found", f"Snapshot {snapshot_id} not found.")

    def open_audit_viewer(self): pass
    def show_documentation(self): pass
    
    def open_tmdb_cache_dialog(self):
        """Open TMDB cache generator dialog."""
        if TMDBCacheDialog is None:
            QMessageBox.warning(self, "Not Available", "TMDB Cache Dialog not available.")
            return
        
        dialog = TMDBCacheDialog(self)
        dialog.exec()
    
    def open_wikipedia_cache_dialog(self):
        """Open Wikipedia cache generator dialog."""
        if WikipediaCacheDialog is None:
            QMessageBox.warning(self, "Not Available", "Wikipedia Cache Dialog not available.")
            return
        
        dialog = WikipediaCacheDialog(self)
        dialog.exec()
    
    def open_canonical_db_dialog(self):
        """Open canonical database builder dialog."""
        if CanonicalDBDialog is None:
            QMessageBox.warning(self, "Not Available", "Canonical Database Dialog not available.")
            return
        
        dialog = CanonicalDBDialog(self)
        dialog.exec()
    
    def open_episode_analyzer(self):
        """Open episode title analyzer dialog."""
        if EpisodeAnalysisDialog is None:
            QMessageBox.warning(self, "Not Available", "Episode Analysis Dialog not available.")
            return
        
        dialog = EpisodeAnalysisDialog(self)
        dialog.exec()
    
    def open_movie_analyzer(self):
        """Open movie name analyzer dialog."""
        if MovieAnalysisDialog is None:
            QMessageBox.warning(self, "Not Available", "Movie Analysis Dialog not available.")
            return
        
        dialog = MovieAnalysisDialog(self)
        dialog.exec()
    
    def show_about(self):
        QMessageBox.about(self, "About JellyRancher",
                         f"{APP_TITLE}\nVersion {APP_VERSION}\n\n"
                         "Unified Media Organization Platform\n\n"
                         "Features:\n"
                         "- Media Organization (Movies, TV, Anime)\n"
                         "- Subtitle Management\n"
                         "- AI-Powered Batch Processing\n"
                         "- Code Quality Analysis\n"
                         "- Analytics & Reporting\n"
                         "- Semantic Memory Search\n"
                         "- Immutable Audit Trail")

    def quick_scan(self):
        """Quick scan shortcut - switches to Organization tab and triggers scan."""
        try:
            # Switch to Organization tab
            for i in range(self.tab_widget.count()):
                if self.tab_widget.tabText(i).startswith("📁"):
                    self.tab_widget.setCurrentIndex(i)
                    break
            # Trigger scan if folder is set
            if hasattr(self, 'org_folder_input') and self.org_folder_input.text().strip():
                self.scan_organization_folder()
            else:
                QMessageBox.information(self, "Quick Scan",
                    "Please select a source folder in the Organization tab first.")
        except Exception as e:
            self.logger.error(f"Quick scan failed: {e}")

    def quick_organize(self):
        """Quick organize shortcut - switches to Organization tab and triggers organize."""
        try:
            # Switch to Organization tab
            for i in range(self.tab_widget.count()):
                if self.tab_widget.tabText(i).startswith("📁"):
                    self.tab_widget.setCurrentIndex(i)
                    break
            # Trigger organize if folder is set
            if hasattr(self, 'org_folder_input') and self.org_folder_input.text().strip():
                self.organize_media()
            else:
                QMessageBox.information(self, "Quick Organize",
                    "Please select a source folder in the Organization tab first.")
        except Exception as e:
            self.logger.error(f"Quick organize failed: {e}")
    
    def quick_subtitles(self):
        """Quick subtitles shortcut - switches to Subtitles tab."""
        try:
            # Switch to Subtitles tab
            for i in range(self.tab_widget.count()):
                if self.tab_widget.tabText(i).startswith("📺"):
                    self.tab_widget.setCurrentIndex(i)
                    break
            QMessageBox.information(self, "Subtitles",
                "1. Browse to select your media folder\n"
                "2. Click 'Detect Coverage' to see what's missing\n"
                "3. Select languages and click 'Download Subtitles'")
        except Exception as e:
            self.logger.error(f"Quick subtitles failed: {e}")
    
    def show_welcome_wizard_if_needed(self):
        """Show welcome wizard on first launch."""
        try:
            from getting_started_wizard import WelcomeWizard
            import json
            from pathlib import Path
            
            # Check if user has dismissed the wizard
            config_file = Path(__file__).parent / "config" / "wizard_settings.json"
            show_wizard = True
            
            if config_file.exists():
                try:
                    with open(config_file, 'r') as f:
                        settings = json.load(f)
                        show_wizard = settings.get('show_wizard', True)
                except:
                    pass
            
            if show_wizard:
                # Delay showing wizard until after window is shown
                QTimer.singleShot(500, self._show_wizard)
        except Exception as e:
            self.logger.warning(f"Could not load welcome wizard: {e}")
    
    def _show_wizard(self):
        """Actually show the wizard (called via timer)."""
        try:
            from getting_started_wizard import WelcomeWizard
            import json
            from pathlib import Path
            
            wizard = WelcomeWizard(self)
            result = wizard.exec()
            
            # Save preference if user doesn't want to see again
            if not wizard.should_show_again():
                config_file = Path(__file__).parent / "config" / "wizard_settings.json"
                config_file.parent.mkdir(parents=True, exist_ok=True)
                
                with open(config_file, 'w') as f:
                    json.dump({'show_wizard': False}, f)
                    
            # Handle selected quick action
            if result == QDialog.Accepted:
                action = wizard.get_selected_action()
                if action == "organize_movies":
                    self.tab_widget.setCurrentIndex(0)  # Go to Workflow tab
                elif action == "organize_tv":
                    self.tab_widget.setCurrentIndex(0)
                elif action == "download_subs":
                    # Switch to Subtitles tab
                    for i in range(self.tab_widget.count()):
                        if self.tab_widget.tabText(i).startswith("📺"):
                            self.tab_widget.setCurrentIndex(i)
                            break
        except Exception as e:
            self.logger.error(f"Error showing wizard: {e}")
    
    def show_quick_start_guide(self):
        """Show quick start guide dialog."""
        try:
            from getting_started_wizard import QuickStartDialog
            dialog = QuickStartDialog(self)
            dialog.exec()
        except ImportError:
            # Fallback if wizard module not available
            QMessageBox.information(
                self,
                "Quick Start Guide",
                "<h3>JellyRancher Quick Start</h3>"
                "<p><b>🎬 Organize Movies:</b></p>"
                "<ol><li>Go to <b>Workflow tab</b></li>"
                "<li>Add folder → Start Scan → Follow steps 1-8</li></ol>"
                "<p><b>💬 Download Subtitles:</b></p>"
                "<ol><li>Go to <b>Subtitles tab</b></li>"
                "<li>Select folder → Detect Coverage → Download</li></ol>"
                "<p><b>🔍 Simple Organization:</b></p>"
                "<ol><li>Go to <b>Organization tab</b></li>"
                "<li>Select media type → Browse folder → Organize</li></ol>"
            )


def main():
    """Main application entry point."""
    # Note: PyQt6 enables High DPI scaling automatically
    
    app = QApplication(sys.argv)
    
    # Set default font - ultra-compact for 1100x500
    default_font = QFont()
    default_font.setPointSize(7)  # Very small for compact layout
    app.setFont(default_font)
    
    window = JellyRancherMainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
