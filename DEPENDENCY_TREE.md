# JellyRancher Studio Dependency Tree

**Main Entry Point:** `jelly_rancher_studio.py`

**Note:** Views import `ProjectManager` and `Project` for legacy compatibility, but these are actually `RoundUpProjectAdapter` and `RoundUpManagerAdapter` classes defined in `jelly_rancher_studio.py` that make RoundUp objects look like the old Project interface.

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
    ├── scripts.core.project_manager (ProjectManager, Project) [Adapter - legacy compatibility]
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
│   ├── sqlite3
│   ├── pathlib.Path
│   ├── typing (List, Optional, Dict)
│   ├── datetime
│   └── collections (defaultdict)
│
├── PyQt6
│   ├── QtWidgets (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QCheckBox, QLineEdit, QFileDialog, QProgressBar, QMessageBox, QTreeWidget, QTreeWidgetItem, QTableWidget, QTableWidgetItem)
│   ├── QtCore (Qt, pyqtSignal, QThread)
│   └── QtGui (QFont)
│
└── JellyRancher Modules
    ├── scripts.core.project_manager (ProjectManager, Project) [Adapter - legacy compatibility]
    ├── scripts.core.file_scanner (FileScanner, FileRecord, ScanStatistics)
    ├── scripts.core.app_config (AppConfigManager)
    ├── scripts.core.inventory_repository (InventoryRepository)
    ├── scripts.core.jellyfin_client (JellyfinClient)
    ├── scripts.core.jellyfin_config (JellyfinConfigManager)
    └── scripts.core.workers (MultiScanWorker)
```

### scripts.ui.scan_results_view
```
scan_results_view.py
├── Standard Library
│   ├── logging
│   ├── json
│   ├── sqlite3
│   ├── csv
│   ├── pathlib.Path
│   ├── typing (List, Optional, Dict, Any, Set)
│   ├── datetime
│   └── collections (defaultdict)
│
├── PyQt6
│   ├── QtWidgets (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QCheckBox, QSpinBox, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QTreeWidget, QTreeWidgetItem)
│   ├── QtCore (Qt, pyqtSignal)
│   └── QtGui (QFont, QColor)
│
└── JellyRancher Modules
    ├── scripts.core.project_manager (ProjectManager, Project) [Adapter - legacy compatibility]
    ├── scripts.core.file_scanner (FileRecord, ScanStatistics)
    ├── scripts.core.inventory_repository (InventoryRepository)
    ├── scripts.core.jellyfin_config (JellyfinConfigManager)
    └── scripts.core.workers (ScanResultsLoadWorker)
```

### scripts.ui.review_view
```
review_view.py
├── Standard Library
│   ├── logging
│   ├── json
│   ├── sqlite3
│   ├── pathlib.Path
│   ├── datetime
│   └── typing (List)
│
├── PyQt6
│   ├── QtWidgets (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox, QMessageBox, QTextEdit, QComboBox)
│   ├── QtCore (Qt, pyqtSignal)
│   └── QtGui (QFont, QColor, QBrush)
│
└── JellyRancher Modules
    ├── scripts.core.project_manager (ProjectManager, Project) [Adapter - legacy compatibility]
    ├── scripts.core.action_plan (ProposedOperation, ActionType, Confidence)
    ├── scripts.core.inventory_repository (InventoryRepository)
    ├── scripts.core.app_config (AppConfigManager)
    ├── scripts.core.file_scanner (FileRecord)
    └── scripts.core.workers (ActionPlanWorker)
```

### scripts.ui.execution_view
```
execution_view.py
├── Standard Library
│   ├── logging
│   ├── sqlite3
│   ├── shutil
│   ├── pathlib.Path
│   ├── datetime
│   └── typing (List, Optional, Dict, Any)
│
├── PyQt6
│   ├── QtWidgets (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QProgressBar, QTextEdit, QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox)
│   ├── QtCore (Qt, pyqtSignal, QThread)
│   └── QtGui (QFont, QColor)
│
└── JellyRancher Modules
    ├── scripts.core.project_manager (ProjectManager, Project) [Adapter - legacy compatibility]
    ├── scripts.utils.transaction_manager (TransactionManager, Operation, OperationType)
    ├── scripts.core.jellyfin_client (JellyfinClient)
    └── scripts.core.jellyfin_config (JellyfinConfigManager)
```

### scripts.ui.subtitles_view
```
subtitles_view.py
├── Standard Library
│   ├── logging
│   ├── pathlib.Path
│   └── typing (Optional, List)
│
├── PyQt6
│   ├── QtWidgets (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QProgressBar, QCheckBox, QListWidget, QListWidgetItem, QMessageBox, QSpinBox)
│   ├── QtCore (Qt, QThread, pyqtSignal)
│   └── QtGui (QFont, QColor)
│
└── JellyRancher Modules
    ├── scripts.core.project_manager (ProjectManager, Project) [Adapter - legacy compatibility]
    ├── scripts.core.roundup_manager (RoundUpManager)
    ├── scripts.media.subtitle_coverage_analyzer (SubtitleCoverageAnalyzer)
    └── scripts.media.subtitle_downloader (SubtitleDownloader, SUBLIMINAL_AVAILABLE)
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
    ├── scripts.core.inventory_repository (InventoryRepository)
    ├── scripts.media.llm_structure_analyzer (LLMStructureAnalyzer)
    ├── scripts.media.media_metadata_lookup (MediaMetadataLookup)
    ├── scripts.core.action_plan (ProposedOperation)
    ├── scripts.core.action_plan_generator (ActionPlanGenerator)
    └── scripts.core.app_config (AppConfigManager)
```

### scripts.core.regex_analysis_worker
```
regex_analysis_worker.py
├── Standard Library
│   ├── logging
│   └── typing (List, Dict, Any)
│
├── PyQt6
│   └── QtCore (QThread, pyqtSignal)
│
└── JellyRancher Modules
    ├── scripts.media.regex_structure_analyzer (RegexStructureAnalyzer)
    └── scripts.media.llm_structure_analyzer (LLMStructureAnalyzer)
```

### scripts.core.extrapolation_engine
```
extrapolation_engine.py
├── Standard Library
│   ├── logging
│   ├── re
│   ├── pathlib.Path
│   ├── typing (List, Dict, Any, Optional, Set, Tuple)
│   └── collections (defaultdict)
│
└── JellyRancher Modules
    ├── scripts.core.file_scanner (FileRecord)
    └── scripts.core.action_plan (ProposedOperation, ActionType, Confidence)
```

### scripts.media.subtitle_coverage_analyzer
```
subtitle_coverage_analyzer.py
├── Standard Library
│   ├── logging
│   ├── json
│   ├── pathlib.Path
│   ├── typing (List, Dict, Optional)
│   └── subprocess
│
└── External Dependencies
    └── ffprobe (via subprocess - for embedded subtitle detection)
```

### scripts.media.subtitle_downloader
```
subtitle_downloader.py
├── Standard Library
│   ├── logging
│   ├── pathlib.Path
│   ├── typing (List, Dict, Optional, Callable)
│   └── time
│
└── External Dependencies
    └── subliminal (optional - for OpenSubtitles downloads)
```

## External Dependencies

### Required Python Packages
- **PyQt6** - GUI framework
- **sqlite3** - Database (built-in)
- **requests** - HTTP client (for API calls)
- **subliminal** - Subtitle download library (optional, for OpenSubtitles)

### External Tools
- **ffprobe** - FFmpeg tool for media analysis (subtitle detection)

### API Dependencies
- **Poe API** - LLM service (via `scripts.ai.ravenmaven_client`)
- **OpenSubtitles API** - Subtitle downloads (via `subliminal` library)

## Architecture Layers

```
┌─────────────────────────────────────────────────────────┐
│                    jelly_rancher_studio.py              │
│                    (Main Application)                   │
│              (RoundUpProjectAdapter,                    │
│               RoundUpManagerAdapter)                    │
└───────────────────────┬─────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
┌───────▼───────┐ ┌────▼──────┐ ┌──────▼──────┐
│   UI Views    │ │  Core      │ │   Media     │
│               │ │  Managers  │ │   Analysis  │
│ - scan_view   │ │            │ │             │
│ - scan_       │ │ - roundup_ │ │ - llm_      │
│   results_    │ │   manager  │ │   structure │
│   view        │ │ - workers  │ │   analyzer  │
│ - analysis_   │ │ - file_    │ │ - regex_    │
│   view        │ │   scanner  │ │   analyzer  │
│ - review_view │ │ - extra-   │ │ - subtitle_ │
│ - execution_  │ │   polation │ │   coverage  │
│   view        │ │   engine   │ │   analyzer  │
│ - subtitles_  │ │ - action_  │ │ - subtitle_ │
│   view        │ │   plan_    │ │   downloader│
│               │ │   generator│ │             │
└───────────────┘ └────────────┘ └─────────────┘
        │               │               │
        └───────────────┼───────────────┘
                        │
        ┌───────────────▼───────────────┐
        │      Round-Up Database         │
        │      (SQLite: data.db)         │
        │   ~/JellyRancher/roundups/     │
        │   {name}.roundup/              │
        └───────────────────────────────┘
```

## Data Flow

1. **User Action** → `jelly_rancher_studio.py`
2. **Studio** → Routes to appropriate View (ScanView, AnalysisView, etc.)
3. **View** → Uses Core Managers (RoundUpManager, FileScanner, etc.)
   - Views receive `RoundUpProjectAdapter` (looks like Project) and `RoundUpManagerAdapter` (looks like ProjectManager)
4. **Managers** → Interact with Round-Up Database or External APIs
5. **Results** → Flow back through Managers → Views → Studio → User

## Key Design Patterns

- **Adapter Pattern**: `RoundUpProjectAdapter` and `RoundUpManagerAdapter` bridge Round-Up system with legacy Project/ProjectManager interface for backward compatibility
- **Worker Pattern**: Background tasks (QThread) for long-running operations (scanning, analysis, metadata lookup, execution)
- **Signal/Slot**: Qt signals for async communication between components
- **Manager Pattern**: Centralized managers for Round-Ups, files, actions, transactions
- **Extrapolation Pattern**: Folder-level LLM suggestions → File-level operations via ExtrapolationEngine

## Document Scope & Finding Function-Level Dependencies

**Scope**: This document shows module and class-level dependencies only (what imports what). It does not include function-level call details.

**Why not function-level**: Function calls are discoverable via code search and function index tools, making detailed function-level documentation redundant for coding assistants that can search the codebase.

**How to find function calls**:
- `grep "function_name" scripts/` - Find all call sites of a specific function
- `codebase_search "query about function usage"` - Semantic search for function usage patterns
- `.venv\Scripts\python.exe tools/query_function_index_semantic.py search "query"` - Function index semantic search
- Read source files directly - Most direct way to see function implementations and call sites

**When function-level is useful**: For workflow documentation showing end-to-end data flow (see `agent-journal.md` for 8-step workflow details with function call chains).
