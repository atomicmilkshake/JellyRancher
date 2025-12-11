#!/usr/bin/env python3
"""
Sorting Canvas View - The "Secret Weapon" for media categorization.

The Sorting Canvas allows users to drag-and-drop files/folders into category
"buckets" before LLM analysis. Each bucket gets a specialized prompt optimized
for that media type (movies vs TV shows vs games, etc.).

This is Step 2.5 in the workflow, inserted between Scan Results and Analysis.

Features:
- Drag-drop files/folders from "Unsorted" to category buckets
- Auto-categorization based on name patterns
- Visual feedback with bucket statistics
- Per-bucket specialized LLM prompts
- Undo/redo support
- Save/load bucket assignments
"""

import logging
from pathlib import Path
from typing import List, Optional, Dict, Any, Set
from collections import defaultdict

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTreeWidget, QTreeWidgetItem, QHeaderView, QGroupBox,
    QMessageBox, QFrame, QSplitter, QProgressBar, QMenu,
    QScrollArea, QSizePolicy, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QMimeData, QByteArray
from PyQt6.QtGui import QFont, QColor, QDrag, QDragEnterEvent, QDropEvent, QPixmap

from scripts.core.bucket_manager import BucketManager, BucketType, BucketItem, Bucket
from scripts.core.per_bucket_prompts import PromptBuilder, build_folder_summary_for_bucket
from scripts.core.project_manager import ProjectManager, Project
from scripts.core.file_scanner import FileRecord

logger = logging.getLogger(__name__)


# Color scheme for buckets
BUCKET_COLORS = {
    BucketType.MOVIES: "#e74c3c",      # Red
    BucketType.TV_SHOWS: "#3498db",    # Blue
    BucketType.GAMES: "#9b59b6",       # Purple
    BucketType.MUSIC: "#1abc9c",       # Teal
    BucketType.BOOKS: "#f39c12",       # Orange
    BucketType.UNSORTED: "#95a5a6",    # Gray
}

BUCKET_ICONS = {
    BucketType.MOVIES: "🎬",
    BucketType.TV_SHOWS: "📺",
    BucketType.GAMES: "🎮",
    BucketType.MUSIC: "🎵",
    BucketType.BOOKS: "📚",
    BucketType.UNSORTED: "❓",
}


class DraggableTreeWidget(QTreeWidget):
    """TreeWidget that supports drag operations for bucket items."""
    
    item_dropped = pyqtSignal(str, str)  # source_path, target_bucket
    
    def __init__(self, bucket_type: BucketType, parent=None):
        super().__init__(parent)
        self.bucket_type = bucket_type
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QTreeWidget.DragDropMode.DragDrop)
        self.setSelectionMode(QTreeWidget.SelectionMode.ExtendedSelection)
        self.setHeaderLabels(["Name", "Size", "Files"])
        self.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.header().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.header().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        
        # Store item data for drag operations
        self.item_data: Dict[str, BucketItem] = {}
    
    def add_bucket_item(self, item: BucketItem):
        """Add a BucketItem to the tree."""
        tree_item = QTreeWidgetItem()
        
        # Icon + name
        icon = "📁" if item.is_folder else "📄"
        tree_item.setText(0, f"{icon} {item.name}")
        
        # Size
        size_mb = item.size_bytes / (1024 * 1024)
        if size_mb < 1024:
            tree_item.setText(1, f"{size_mb:.1f} MB")
        else:
            tree_item.setText(1, f"{size_mb/1024:.2f} GB")
        
        # File count
        tree_item.setText(2, str(item.file_count))
        
        # Store path for drag/drop
        tree_item.setData(0, Qt.ItemDataRole.UserRole, str(item.path))
        
        # Style based on auto vs manual assignment
        if item.auto_assigned:
            tree_item.setForeground(0, QColor("#888888"))
        
        self.addTopLevelItem(tree_item)
        self.item_data[str(item.path)] = item
    
    def clear_items(self):
        """Clear all items from the tree."""
        self.clear()
        self.item_data.clear()
    
    def mimeTypes(self) -> List[str]:
        """Return supported MIME types."""
        return ["application/x-bucket-item"]
    
    def mimeData(self, items: List[QTreeWidgetItem]) -> QMimeData:
        """Create MIME data for drag operation."""
        mime_data = QMimeData()
        paths = []
        for item in items:
            path = item.data(0, Qt.ItemDataRole.UserRole)
            if path:
                paths.append(path)
        
        # Store paths as newline-separated string
        mime_data.setData("application/x-bucket-item", 
                         "\n".join(paths).encode('utf-8'))
        mime_data.setText(f"source_bucket:{self.bucket_type.value}")
        return mime_data
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter."""
        if event.mimeData().hasFormat("application/x-bucket-item"):
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dragMoveEvent(self, event):
        """Handle drag move."""
        if event.mimeData().hasFormat("application/x-bucket-item"):
            event.acceptProposedAction()
    
    def dropEvent(self, event: QDropEvent):
        """Handle drop - emit signal with paths and target bucket."""
        if event.mimeData().hasFormat("application/x-bucket-item"):
            data = event.mimeData().data("application/x-bucket-item").data().decode('utf-8')
            paths = data.split("\n")
            
            # Get source bucket from text
            source_text = event.mimeData().text()
            source_bucket = source_text.replace("source_bucket:", "")
            
            for path in paths:
                if path:
                    self.item_dropped.emit(path, self.bucket_type.value)
            
            event.acceptProposedAction()
        else:
            event.ignore()


class BucketWidget(QGroupBox):
    """Widget representing a single bucket with drag-drop tree."""
    
    item_moved = pyqtSignal(str, str)  # path, target_bucket
    
    def __init__(self, bucket_type: BucketType, parent=None):
        super().__init__(parent)
        self.bucket_type = bucket_type
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the bucket UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 12, 8, 8)
        layout.setSpacing(4)
        
        # Header with icon, name, and stats
        header_layout = QHBoxLayout()
        
        icon = BUCKET_ICONS.get(self.bucket_type, "📦")
        name = self.bucket_type.value.replace("_", " ").title()
        self.title_label = QLabel(f"{icon} {name}")
        self.title_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch()
        
        self.stats_label = QLabel("0 items")
        self.stats_label.setStyleSheet("color: #888;")
        header_layout.addWidget(self.stats_label)
        
        layout.addLayout(header_layout)
        
        # Tree widget
        self.tree = DraggableTreeWidget(self.bucket_type)
        self.tree.item_dropped.connect(self._on_item_dropped)
        layout.addWidget(self.tree)
        
        # Style the groupbox
        color = BUCKET_COLORS.get(self.bucket_type, "#666")
        self.setStyleSheet(f"""
            BucketWidget {{
                border: 2px solid {color};
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 8px;
            }}
            BucketWidget::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px;
            }}
        """)
    
    def _on_item_dropped(self, path: str, target_bucket: str):
        """Handle item dropped into this bucket."""
        self.item_moved.emit(path, target_bucket)
    
    def update_from_bucket(self, bucket: Bucket):
        """Update the widget from a Bucket object."""
        self.tree.clear_items()
        
        for item in bucket.items:
            self.tree.add_bucket_item(item)
        
        # Update stats
        total_files = bucket.total_files
        total_size = bucket.total_size_bytes / (1024 * 1024 * 1024)  # GB
        self.stats_label.setText(f"{len(bucket.items)} items • {total_files} files • {total_size:.2f} GB")
    
    def get_selected_paths(self) -> List[str]:
        """Get paths of selected items."""
        paths = []
        for item in self.tree.selectedItems():
            path = item.data(0, Qt.ItemDataRole.UserRole)
            if path:
                paths.append(path)
        return paths


class SortingCanvasView(QWidget):
    """
    The Sorting Canvas - drag-drop categorization of media before LLM analysis.
    
    This view sits between Scan Results and Analysis in the workflow.
    Users can drag files/folders from Unsorted into category buckets.
    Each bucket will then be analyzed with a specialized LLM prompt.
    
    Signals:
        send_to_analysis: Emitted when user clicks "Analyze" with bucket data
        canvas_saved: Emitted when bucket assignments are saved
    """
    
    send_to_analysis = pyqtSignal(dict)  # Bucket assignments dict
    canvas_saved = pyqtSignal()
    
    def __init__(self, project: Project, project_manager: ProjectManager,
                 scanned_files: List[FileRecord] = None,
                 folder_structure: Dict[str, Any] = None,
                 parent=None):
        """
        Initialize the Sorting Canvas.
        
        Args:
            project: Current project
            project_manager: Project manager for persistence
            scanned_files: List of scanned FileRecord objects
            folder_structure: Folder structure dict from scan
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.project = project
        self.project_manager = project_manager
        self.scanned_files = scanned_files or []
        self.folder_structure = folder_structure or {}
        
        # Initialize bucket manager
        self.bucket_manager = BucketManager()
        
        # Bucket widgets
        self.bucket_widgets: Dict[BucketType, BucketWidget] = {}
        
        self._init_ui()
        self._populate_from_scan_data()
        
        logger.info("SortingCanvasView initialized")
    
    def _init_ui(self):
        """Build the UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)
        
        # === Header Section ===
        header_layout = QHBoxLayout()
        
        title = QLabel("🎯 Sorting Canvas")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Instructions
        instructions = QLabel(
            "Drag items between buckets to categorize. "
            "Each bucket uses a specialized LLM prompt for better analysis."
        )
        instructions.setStyleSheet("color: #888; font-style: italic;")
        header_layout.addWidget(instructions)
        
        main_layout.addLayout(header_layout)
        
        # === Toolbar ===
        toolbar_layout = QHBoxLayout()
        
        self.auto_sort_btn = QPushButton("🔄 Auto-Sort All")
        self.auto_sort_btn.setToolTip("Automatically categorize items based on name patterns")
        self.auto_sort_btn.clicked.connect(self._on_auto_sort)
        self.auto_sort_btn.setStyleSheet("background-color: #3498db; color: white; font-weight: bold;")
        toolbar_layout.addWidget(self.auto_sort_btn)
        
        self.reset_btn = QPushButton("↩ Reset to Unsorted")
        self.reset_btn.setToolTip("Move all items back to Unsorted bucket")
        self.reset_btn.clicked.connect(self._on_reset)
        toolbar_layout.addWidget(self.reset_btn)
        
        self.undo_btn = QPushButton("⬅ Undo")
        self.undo_btn.setToolTip("Undo last move")
        self.undo_btn.clicked.connect(self._on_undo)
        toolbar_layout.addWidget(self.undo_btn)
        
        self.redo_btn = QPushButton("➡ Redo")
        self.redo_btn.setToolTip("Redo last undone move")
        self.redo_btn.clicked.connect(self._on_redo)
        toolbar_layout.addWidget(self.redo_btn)
        
        toolbar_layout.addStretch()
        
        self.stats_label = QLabel("")
        self.stats_label.setStyleSheet("color: #27ae60; font-weight: bold;")
        toolbar_layout.addWidget(self.stats_label)
        
        main_layout.addLayout(toolbar_layout)
        
        # === Main Content - Bucket Grid ===
        # Use splitter for resizable buckets
        bucket_splitter = QSplitter(Qt.Orientation.Horizontal)
        bucket_splitter.setChildrenCollapsible(False)
        
        # Left side: Source (Unsorted)
        left_frame = QFrame()
        left_layout = QVBoxLayout(left_frame)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        unsorted_widget = BucketWidget(BucketType.UNSORTED)
        unsorted_widget.item_moved.connect(self._on_item_moved)
        self.bucket_widgets[BucketType.UNSORTED] = unsorted_widget
        left_layout.addWidget(unsorted_widget)
        
        bucket_splitter.addWidget(left_frame)
        
        # Right side: Target buckets (2 columns)
        right_frame = QFrame()
        right_layout = QHBoxLayout(right_frame)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)
        
        # Column 1: Movies, TV Shows, Games
        col1_layout = QVBoxLayout()
        for bt in [BucketType.MOVIES, BucketType.TV_SHOWS, BucketType.GAMES]:
            widget = BucketWidget(bt)
            widget.item_moved.connect(self._on_item_moved)
            self.bucket_widgets[bt] = widget
            col1_layout.addWidget(widget)
        right_layout.addLayout(col1_layout)
        
        # Column 2: Music, Books
        col2_layout = QVBoxLayout()
        for bt in [BucketType.MUSIC, BucketType.BOOKS]:
            widget = BucketWidget(bt)
            widget.item_moved.connect(self._on_item_moved)
            self.bucket_widgets[bt] = widget
            col2_layout.addWidget(widget)
        col2_layout.addStretch()
        right_layout.addLayout(col2_layout)
        
        bucket_splitter.addWidget(right_frame)
        
        # Set initial sizes (1:2 ratio)
        bucket_splitter.setSizes([400, 800])
        
        main_layout.addWidget(bucket_splitter, 1)
        
        # === Bottom Action Bar ===
        action_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("💾 Save Assignments")
        self.save_btn.setToolTip("Save bucket assignments to Round-Up")
        self.save_btn.clicked.connect(self._on_save)
        action_layout.addWidget(self.save_btn)
        
        action_layout.addStretch()
        
        # Analysis button with per-bucket info
        self.analyze_btn = QPushButton("🚀 Analyze Per-Bucket")
        self.analyze_btn.setToolTip("Send each bucket to LLM with specialized prompts")
        self.analyze_btn.clicked.connect(self._on_analyze)
        self.analyze_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                font-size: 12pt;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
        """)
        action_layout.addWidget(self.analyze_btn)
        
        main_layout.addLayout(action_layout)
    
    def _populate_from_scan_data(self):
        """Populate buckets from scanned files."""
        if not self.scanned_files:
            self._update_all_widgets()
            self._update_stats()
            return
        
        # Group files by parent folder
        folder_items: Dict[Path, Dict[str, Any]] = defaultdict(lambda: {
            'files': [],
            'size': 0,
            'extensions': set()
        })
        
        for record in self.scanned_files:
            # Handle both FileRecord (absolute_path) and dict-like objects (path)
            path = getattr(record, 'absolute_path', None) or getattr(record, 'path', None)
            if path is None:
                continue
            parent = path.parent
            folder_items[parent]['files'].append(record)
            folder_items[parent]['size'] += getattr(record, 'size_bytes', 0)
            folder_items[parent]['extensions'].add(path.suffix.lower())
        
        # Create bucket items for each folder
        items_to_categorize = []
        for folder_path, data in folder_items.items():
            items_to_categorize.append({
                'path': folder_path,
                'name': folder_path.name,
                'is_folder': True,
                'size_bytes': data['size'],
                'file_count': len(data['files']),
                'extensions': list(data['extensions'])
            })
        
        # Auto-categorize all items
        self.bucket_manager.auto_categorize_all(items_to_categorize)
        
        # Update all widgets
        self._update_all_widgets()
        self._update_stats()
        
        logger.info(f"Populated canvas with {len(items_to_categorize)} folder groups")
    
    def _update_all_widgets(self):
        """Update all bucket widgets from manager state."""
        for bucket_type, widget in self.bucket_widgets.items():
            bucket = self.bucket_manager.get_bucket(bucket_type)
            widget.update_from_bucket(bucket)
    
    def _update_stats(self):
        """Update the statistics label."""
        stats = self.bucket_manager.get_statistics()
        
        non_empty = len(self.bucket_manager.get_non_empty_buckets())
        self.stats_label.setText(
            f"📊 {stats['total_items']} items in {non_empty} buckets • "
            f"{stats['total_files']} files • "
            f"{stats['total_size_bytes'] / (1024**3):.2f} GB"
        )
    
    def _on_item_moved(self, path: str, target_bucket: str):
        """Handle item moved between buckets."""
        path_obj = Path(path)
        target_type = BucketType.from_string(target_bucket)
        
        # Find current bucket
        current_bucket = self.bucket_manager.find_item_bucket(path_obj)
        if current_bucket:
            self.bucket_manager.move_item(path_obj, current_bucket, target_type)
            self._update_all_widgets()
            self._update_stats()
            logger.debug(f"Moved {path_obj.name} to {target_bucket}")
    
    def _on_auto_sort(self):
        """Auto-sort all items based on name patterns."""
        # Collect all items currently in Unsorted
        unsorted_bucket = self.bucket_manager.get_bucket(BucketType.UNSORTED)
        items_to_resort = list(unsorted_bucket.items)
        
        for item in items_to_resort:
            # Get file extensions for this item
            extensions = set()
            if item.is_folder:
                # Find files in this folder from scanned_files
                for record in self.scanned_files:
                    path = getattr(record, 'absolute_path', None) or getattr(record, 'path', None)
                    if path and str(path).startswith(str(item.path)):
                        extensions.add(path.suffix.lower())
            else:
                extensions.add(item.path.suffix.lower())
            
            # Get suggested bucket
            suggested = self.bucket_manager.auto_categorize_item(
                item.path, item.name, item.is_folder,
                item.size_bytes, item.file_count, extensions
            )
            
            if suggested != BucketType.UNSORTED:
                self.bucket_manager.move_item(item.path, BucketType.UNSORTED, suggested)
        
        self._update_all_widgets()
        self._update_stats()
        
        self._set_status(f"Auto-sorted {len(items_to_resort)} items")
    
    def _on_reset(self):
        """Move all items back to Unsorted bucket."""
        # Collect all items from all buckets except Unsorted
        items_to_move = []
        for bt in BucketType:
            if bt != BucketType.UNSORTED:
                bucket = self.bucket_manager.get_bucket(bt)
                items_to_move.extend([(item.path, bt) for item in bucket.items])
        
        # Move all to Unsorted
        for path, from_bucket in items_to_move:
            self.bucket_manager.move_item(path, from_bucket, BucketType.UNSORTED)
        
        self._update_all_widgets()
        self._update_stats()
        
        self._set_status(f"Reset {len(items_to_move)} items to Unsorted")
    
    def _on_undo(self):
        """Undo last move."""
        if self.bucket_manager.undo():
            self._update_all_widgets()
            self._update_stats()
            self._set_status("Undo successful")
        else:
            self._set_status("Nothing to undo")
    
    def _on_redo(self):
        """Redo last undone move."""
        if self.bucket_manager.redo():
            self._update_all_widgets()
            self._update_stats()
            self._set_status("Redo successful")
        else:
            self._set_status("Nothing to redo")
    
    def _on_save(self):
        """Save bucket assignments to Round-Up database."""
        try:
            # Get database path from project
            db_path = None
            if hasattr(self.project, 'roundup') and self.project.roundup:
                db_path = self.project.roundup.path / "data.db"
            
            if db_path:
                success = self.bucket_manager.save_to_database(db_path)
                if success:
                    self._set_status("Bucket assignments saved ✓")
                    self.canvas_saved.emit()
                else:
                    self._set_status("Failed to save assignments", level='error')
            else:
                self._set_status("No Round-Up database available", level='warning')
                
        except Exception as e:
            logger.error(f"Failed to save bucket assignments: {e}")
            self._set_status(f"Save error: {e}", level='error')
    
    def _on_analyze(self):
        """Send bucket data to analysis with per-bucket prompts."""
        non_empty = self.bucket_manager.get_non_empty_buckets()
        
        if not non_empty:
            self._set_status("No items to analyze - add files to buckets first", level='warning')
            return
        
        # Build bucket data for analysis
        bucket_data = {
            'buckets': {},
            'total_items': 0
        }
        
        for bucket in non_empty:
            # Build folder summary for this bucket
            folder_summary = build_folder_summary_for_bucket(bucket.items)
            
            # Get specialized prompt
            prompt = PromptBuilder.get_prompt_for_bucket(bucket.bucket_type, folder_summary)
            
            # Collect file paths
            file_paths = []
            for item in bucket.items:
                if item.is_folder:
                    # Get all files in this folder from scanned_files
                    for record in self.scanned_files:
                        path = getattr(record, 'absolute_path', None) or getattr(record, 'path', None)
                        if path and str(path).startswith(str(item.path)):
                            file_paths.append(str(path))
                else:
                    file_paths.append(str(item.path))
            
            bucket_data['buckets'][bucket.bucket_type.value] = {
                'items': [item.to_dict() for item in bucket.items],
                'file_paths': file_paths,
                'prompt': prompt,
                'item_count': len(bucket.items),
                'file_count': bucket.total_files,
                'size_bytes': bucket.total_size_bytes
            }
            bucket_data['total_items'] += len(bucket.items)
        
        # Emit signal with bucket data
        self.send_to_analysis.emit(bucket_data)
        
        self._set_status(f"Sending {len(non_empty)} buckets to analysis...")
        logger.info(f"Emitting send_to_analysis with {len(non_empty)} buckets")
    
    def _set_status(self, message: str, level: str = 'info'):
        """Set status message in main window's status bar."""
        try:
            main_window = self.window()
            if main_window and hasattr(main_window, 'status_label'):
                main_window.status_label.setText(message)
                if level == 'error':
                    main_window.status_label.setStyleSheet("color: #e74c3c;")
                elif level == 'warning':
                    main_window.status_label.setStyleSheet("color: #f39c12;")
                else:
                    main_window.status_label.setStyleSheet("color: #27ae60;")
        except Exception:
            pass
    
    def load_from_database(self):
        """Load bucket assignments from Round-Up database."""
        try:
            db_path = None
            if hasattr(self.project, 'roundup') and self.project.roundup:
                db_path = self.project.roundup.path / "data.db"
            
            if db_path and self.bucket_manager.load_from_database(db_path):
                self._update_all_widgets()
                self._update_stats()
                self._set_status("Loaded saved bucket assignments")
                return True
                
        except Exception as e:
            logger.error(f"Failed to load bucket assignments: {e}")
        
        return False
    
    def set_scanned_files(self, files: List[FileRecord], folder_structure: Dict[str, Any] = None):
        """Update with new scanned files."""
        self.scanned_files = files
        self.folder_structure = folder_structure or {}
        self.bucket_manager.clear_all()
        self._populate_from_scan_data()

