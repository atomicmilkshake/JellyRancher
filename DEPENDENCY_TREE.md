# JellyRancher Studio Dependency Tree

**Main Entry Point:** `jelly_rancher_studio.py`

## Top-Level Dependencies

```
jelly_rancher_studio.py
├── Standard Library
│   ├── sys
│   ├── logging
│   ├── json
│   ├── pathlib.Path
│   ├── typing (Optional, List, Dict, Any)
│   └── datetime
│
├── PyQt6 (GUI Framework)
│   ├── QtWidgets (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QTreeWidget, QTreeWidgetItem, QTabWidget, QLabel, QMenuBar, QMenu, QStatusBar, QPushButton, QMessageBox, QDialog, QLineEdit, QTextEdit, QDialogButtonBox, QStackedWidget)
│   ├── QtCore (Qt, QTimer, pyqtSignal, QEvent)
│   └── QtGui (QAction, QFont, QShortcut, QKeySequence)
│
└── JellyRancher Modules
    ├── scripts.core.roundup_manager (RoundUpManager, RoundUp)
    ├── scripts._common.logger (MasterLogger)
    ├── scripts.ui.welcome_screen (WelcomeScreen)
    ├── scripts.ui.styles (apply_stylesheet)
    ├── scripts.ui.scan_view (ScanView)
    ├── scripts.ui.scan_results_view (ScanResultsView)
    ├── scripts.ui.analysis_view (AnalysisView)
    ├── scripts.ui.review_view (ReviewView)
    ├── scripts.ui.execution_view (ExecutionView)
    ├── scripts.ui.subtitles_view (SubtitlesView)
    └── scripts.core.dialogs.jellyfin_settings_dialog (JellyfinSettingsDialog)
```

## Core Module Dependencies

### scripts.core.roundup_manager
```
roundup_manager.py
├── Standard Library
│   ├── sqlite3
│   ├── logging
│   ├── json
│   ├── shutil
│   ├── pathlib.Path
│   ├── typing (Optional, List, Dict, Any)
│   ├── dataclasses (dataclass, field)
│   ├── datetime
│   ├── contextlib (contextmanager)
│   └── enum (Enum)
│
└── No JellyRancher dependencies (core module)
```

### scripts.ui.analysis_view
```
analysis_view.py
├── Standard Library
│   ├── logging
│   ├── json
│   ├── os
│   ├── datetime
│   ├── pathlib.Path
│   └── typing (List, Optional, Dict, Any)
│
├── PyQt6
│   ├── QtWidgets (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QProgressBar, QTableWidget, QTableWidgetItem, QHeaderView, QTextEdit, QTabWidget, QStatusBar, QDialog, QMessageBox, QApplication)
│   ├── QtGui (QFont, QColor, QBrush)
│   └── QtCore (Qt, pyqtSignal)
│
└── JellyRancher Modules
    ├── scripts.core.project_manager (ProjectManager, Project)
    ├── scripts.core.file_scanner (FileScanner, FileRecord)
    ├── scripts.core.roundup_manager (RoundUpManager)
    ├── scripts.core.action_plan (ProposedOperation, ActionType, Confidence)
    ├── scripts.core.extrapolation_engine (ExtrapolationEngine)
    ├── scripts.ai.ravenmaven_client (PoeClient)
    ├── scripts.core.workers (LLMAnalysisWorker, MetadataLookupWorker)
    ├── scripts.core.regex_analysis_worker (RegexAnalysisWorker, HybridAnalysisWorker)
    └── scripts.media.llm_structure_analyzer (LLMStructureAnalyzer)
```

### scripts.ui.scan_view
```
scan_view.py
├── Standard Library
│   ├── logging
│   ├── json
│   ├── pathlib.Path
│   ├── typing (List, Optional, Dict, Any)
│   └── datetime
│
├── PyQt6
│   ├── QtWidgets (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QCheckBox, QLineEdit, QFileDialog, QProgressBar, QMessageBox, QTreeWidget, QTreeWidgetItem)
│   ├── QtCore (Qt, pyqtSignal, QThread)
│   └── QtGui (QFont)
│
└── JellyRancher Modules
    ├── scripts.core.project_manager (ProjectManager, Project)
    ├── scripts.core.file_scanner (FileScanner, FileRecord, ScanStatistics)
    ├── scripts.core.roundup_manager (RoundUpManager)
    └── scripts.core.workers (ScanWorker)
```

### scripts.ui.review_view
```
review_view.py
├── Standard Library
│   ├── logging
│   ├── json
│   ├── sqlite3
│   ├── pathlib.Path
│   └── typing (List, Optional, Dict, Any)
│
├── PyQt6
│   ├── QtWidgets (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox, QMessageBox, QTextEdit, QComboBox)
│   ├── QtCore (Qt, pyqtSignal)
│   └── QtGui (QFont, QColor, QBrush)
│
└── JellyRancher Modules
    ├── scripts.core.project_manager (ProjectManager, Project)
    ├── scripts.core.file_scanner (FileRecord)
    ├── scripts.core.roundup_manager (RoundUpManager)
    ├── scripts.core.action_plan (ProposedOperation, ActionType, Confidence)
    └── scripts.core.action_plan_generator (ActionPlanGenerator)
```

### scripts.ui.execution_view
```
execution_view.py
├── Standard Library
│   ├── logging
│   ├── sqlite3
│   ├── pathlib.Path
│   └── typing (List, Optional, Dict, Any)
│
├── PyQt6
│   ├── QtWidgets (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QProgressBar, QTextEdit, QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView)
│   ├── QtCore (Qt, pyqtSignal, QThread)
│   └── QtGui (QFont, QColor)
│
└── JellyRancher Modules
    ├── scripts.core.project_manager (ProjectManager, Project)
    ├── scripts.core.roundup_manager (RoundUpManager)
    ├── scripts.core.transaction_manager (TransactionManager)
    └── scripts.core.jellyfin_client (JellyfinClient)
```

## Secondary Dependencies

### scripts.media.llm_structure_analyzer
```
llm_structure_analyzer.py
├── Standard Library
│   ├── json
│   ├── sys
│   ├── pathlib.Path
│   ├── typing (Dict, List, Optional, Tuple)
│   └── datetime
│
└── JellyRancher Modules
    └── scripts.ai.ravenmaven_client (PoeClient)
```

### scripts.core.workers
```
workers.py
├── Standard Library
│   ├── logging
│   ├── json
│   ├── sqlite3
│   ├── pathlib.Path
│   ├── typing (List, Optional, Dict, Any)
│   └── datetime
│
├── PyQt6
│   └── QtCore (QThread, pyqtSignal)
│
└── JellyRancher Modules
    ├── scripts.core.file_scanner (FileRecord, FileScanner)
    ├── scripts.core.roundup_manager (RoundUpManager)
    ├── scripts.media.llm_structure_analyzer (LLMStructureAnalyzer)
    ├── scripts.media.regex_structure_analyzer (RegexStructureAnalyzer)
    └── scripts.media.media_metadata_lookup (MediaMetadataLookup)
```

### scripts.core.extrapolation_engine
```
extrapolation_engine.py
├── Standard Library
│   ├── logging
│   ├── pathlib.Path
│   └── typing (List, Optional, Dict, Any)
│
└── JellyRancher Modules
    ├── scripts.core.file_scanner (FileRecord)
    └── scripts.core.action_plan (ProposedOperation, ActionType, Confidence)
```

## External Dependencies

### Required Python Packages
- **PyQt6** - GUI framework
- **sqlite3** - Database (built-in)
- **requests** - HTTP client (for API calls, if used)

### API Dependencies
- **Poe API** - LLM service (via `scripts.ai.ravenmaven_client`)

## Architecture Layers

```
┌─────────────────────────────────────────────────────────┐
│                    jelly_rancher_studio.py              │
│                    (Main Application)                   │
└───────────────────────┬─────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
┌───────▼───────┐ ┌────▼──────┐ ┌──────▼──────┐
│   UI Views    │ │  Core      │ │   Media     │
│               │ │  Managers  │ │   Analysis  │
│ - scan_view   │ │            │ │             │
│ - analysis_   │ │ - roundup_ │ │ - llm_      │
│   view        │ │   manager  │ │   structure │
│ - review_view │ │ - workers  │ │   analyzer  │
│ - execution_  │ │ - file_    │ │ - regex_    │
│   view        │ │   scanner  │ │   analyzer  │
└───────────────┘ └────────────┘ └─────────────┘
        │               │               │
        └───────────────┼───────────────┘
                        │
        ┌───────────────▼───────────────┐
        │      Round-Up Database         │
        │      (SQLite: data.db)         │
        └───────────────────────────────┘
```

## Data Flow

1. **User Action** → `jelly_rancher_studio.py`
2. **Studio** → Routes to appropriate View (ScanView, AnalysisView, etc.)
3. **View** → Uses Core Managers (RoundUpManager, FileScanner, etc.)
4. **Managers** → Interact with Round-Up Database or External APIs
5. **Results** → Flow back through Managers → Views → Studio → User

## Key Design Patterns

- **Adapter Pattern**: `RoundUpProjectAdapter` bridges Round-Up system with legacy Project interface
- **Worker Pattern**: Background tasks (QThread) for long-running operations
- **Signal/Slot**: Qt signals for async communication between components
- **Manager Pattern**: Centralized managers for Round-Ups, files, actions

