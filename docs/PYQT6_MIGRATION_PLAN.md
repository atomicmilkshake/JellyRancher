# JellyRancher PyQt6 Migration & Cleanup Plan

**Date:** November 12, 2025  
**Goal:** Transition GUI framework from PyQt5 to PyQt6 and clean up the project structure

---

## 📊 Current State Analysis

### Project Statistics (from cleanup report)
- **Total Files:** 32,156 files (2,212.87 MB)
- **Core Scripts to Keep:** 74 files (1.20 MB)
- **Recommended for Deletion:** 114 files (2.05 MB)
- **Recommended for Archive:** 678 files (12.27 MB)
- **Needs Review:** 30,940 files (2,184.73 MB)

### Current GUI Stack
- **Framework:** PyQt5 (3,568 lines in `jelly_rancher_main.py`)
- **Entry Point:** `launch_gui.py` → `scripts.core.jelly_rancher_main.main()`
- **Legacy GUIs:** 
  - `scripts/tools/ravenmaven/ravenmaven_gui.py` (CustomTkinter)
  - `scripts/ai/structure_preview_gui.py` (Tkinter)
  - `code_cop/tools/audit/codecop_gui.py` (Tkinter)
  - `scripts/core/gui_main.py` (old implementation)

---

## 🎯 Phase 1: Pre-Migration Cleanup (IMMEDIATE)

### 1.1 Execute Cleanup Script Recommendations

**DELETE (114 files - 2.05 MB):**
```powershell
# Run the generated deletion script
.\cleanup_reports\cleanup_delete_20251112_144153.ps1
```

Key deletions:
- 106 duplicate files in `RavenMaven/lists/` (chunk*_processed.json)
- 8 temp files in `temp/` directory
- Backup credential files (`.enc.bak`, `.salt.bak`)

**ARCHIVE (678 files - 12.27 MB):**
```powershell
# Create archive directory
mkdir V:\JellyRancher_Archive\2025-11-12_pre-pyqt6

# Move to archive:
- code_cop/jellyfin_organizer_* files (legacy analysis)
- Jellyfin Organizer/.coverage and test artifacts
- archive/documentation_2025-11-09/ and 2025-11-11/
- All legacy summaries and reports in code_cop/summaries/
```

### 1.2 Remove Obsolete GUI Files

**To DELETE (Legacy GUI implementations):**
```
❌ scripts/tools/ravenmaven/ravenmaven_gui.py (CustomTkinter - 550+ lines)
❌ scripts/ai/structure_preview_gui.py (Tkinter - 270 lines)
❌ code_cop/tools/audit/codecop_gui.py (Tkinter - legacy)
❌ scripts/core/gui_main.py (old Tkinter implementation)
❌ scripts/utils/before_after_preview.py (Tkinter utility)
❌ backups/scripts_backup_20251110/core/launch_gui.py (old backup)
```

### 1.3 Clean ChromaDB Duplicates

**Review and consolidate:**
- 3 ChromaDB instances found:
  - `chroma_db/chroma.sqlite3` (main)
  - `scripts/chroma_db/chroma.sqlite3` (duplicate?)
  - `scripts/core/chroma_db/` (active?)
  
**Action:** Keep only ONE ChromaDB instance, merge if needed

---

## 🚀 Phase 2: PyQt6 Migration (CORE WORK)

### 2.1 Update Dependencies

**Current `requirements-jelly-rancher.txt`:**
```diff
- PyQt5>=5.15.0
+ PyQt6>=6.6.0
+ PyQt6-Qt6>=6.6.0
```

**Install PyQt6:**
```powershell
& V:/JellyRancher/.venv/Scripts/python.exe -m pip install PyQt6
& V:/JellyRancher/.venv/Scripts/python.exe -m pip uninstall PyQt5 -y
```

### 2.2 Code Migration Strategy

**Primary File to Migrate:** `scripts/core/jelly_rancher_main.py` (3,568 lines)

**PyQt5 → PyQt6 Import Changes:**
```python
# OLD (PyQt5)
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, ...
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, ...
from PyQt5.QtGui import QIcon, QFont, QColor, ...

# NEW (PyQt6)
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, ...
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, ...
from PyQt6.QtGui import QIcon, QFont, QColor, ...
```

**Key API Changes to Handle:**

1. **Enum Values:**
   ```python
   # PyQt5
   Qt.AlignCenter
   
   # PyQt6
   Qt.AlignmentFlag.AlignCenter
   ```

2. **exec() Method:**
   ```python
   # PyQt5
   sys.exit(app.exec_())
   
   # PyQt6
   sys.exit(app.exec())
   ```

3. **Signal/Slot Connections (same, but verify):**
   ```python
   # Both work the same
   button.clicked.connect(self.handler)
   ```

### 2.3 File-by-File Migration Checklist

**Core Files to Update:**
- [ ] `scripts/core/jelly_rancher_main.py` (main GUI - 3,568 lines)
- [ ] `launch_gui.py` (update import error message)
- [ ] `requirements-jelly-rancher.txt` (update PyQt6)
- [ ] `scripts/core/jellyfin_ui.py` (if still used - 1,656 lines)

**Backend Files (verify compatibility):**
- [ ] `scripts/core/subtitle_backend.py`
- [ ] `scripts/core/tools_backend.py`
- [ ] `scripts/core/analytics_backend.py`
- [ ] `scripts/core/settings_backend.py`

**Test Files:**
- [ ] Update any GUI tests to use PyQt6
- [ ] Update `pytest.ini` if needed

---

## 🔧 Phase 3: Modernization Improvements

### 3.1 New PyQt6 Features to Leverage

**Consider adding:**
1. **Better High-DPI Support** (PyQt6 improved default handling)
2. **Modern Widgets** (QTableView improvements, better styling)
3. **Dark Mode Detection** (native OS theme integration)
4. **Improved Threading** (QThreadPool enhancements)

### 3.2 Code Quality Improvements

**While migrating, modernize:**
- [ ] Type hints for all methods
- [ ] Docstrings for all classes
- [ ] Extract hardcoded strings to constants
- [ ] Split large files (jelly_rancher_main.py is 3,568 lines!)
- [ ] Add unit tests for GUI components

### 3.3 Suggested Refactoring

**Split `jelly_rancher_main.py` into modules:**
```
scripts/core/gui/
├── __init__.py
├── main_window.py          # Main window class
├── tabs/
│   ├── __init__.py
│   ├── media_tab.py        # Media organization tab
│   ├── subtitle_tab.py     # Subtitle management tab
│   ├── batch_tab.py        # Batch processing tab
│   ├── analytics_tab.py    # Analytics tab
│   └── settings_tab.py     # Settings tab
├── dialogs/
│   ├── __init__.py
│   ├── preferences.py
│   └── about.py
└── widgets/
    ├── __init__.py
    ├── log_viewer.py
    └── progress_bar.py
```

---

## 📝 Phase 4: Testing & Validation

### 4.1 Testing Checklist

**Functional Tests:**
- [ ] Launch GUI successfully
- [ ] All tabs load without errors
- [ ] Media organization workflows work
- [ ] Subtitle download functionality works
- [ ] Batch processing with AI works
- [ ] Settings save/load correctly
- [ ] ChromaDB integration works

**Visual Tests:**
- [ ] UI renders correctly on Windows
- [ ] High-DPI displays work properly
- [ ] Dark/light themes render well
- [ ] All icons and images display
- [ ] Font sizes are readable

**Performance Tests:**
- [ ] GUI remains responsive during heavy operations
- [ ] Threading works correctly
- [ ] Memory usage is acceptable
- [ ] Large file lists don't cause lag

### 4.2 Regression Testing

**Test these critical workflows:**
1. **Media Organization:**
   - Scan folder
   - Identify media
   - Generate structure
   - Execute reorganization

2. **Subtitle Management:**
   - Search for subtitles
   - Download from multiple providers
   - Verify file placement

3. **Batch Processing:**
   - Load file list
   - Process with AI
   - Execute changes

---

## 🗑️ Phase 5: Final Cleanup

### 5.1 Remove After Successful Migration

**Delete these once PyQt6 works:**
```
❌ All PyQt5 imports (if any remain)
❌ All CustomTkinter/Tkinter GUI files
❌ Old GUI backup files
❌ Unused backend files
```

### 5.2 Update Documentation

**Update these files:**
- [ ] `USER_GUIDE.md` - Update screenshots if UI changed
- [ ] `bootstrap.md` - Update GUI entry point documentation
- [ ] `requirements-jelly-rancher.txt` - Finalize dependencies
- [ ] `README.md` - Update installation instructions
- [ ] `CHANGELOG.md` - Document migration

### 5.3 Archive Old Components

**Move to archive:**
```
V:\JellyRancher_Archive\2025-11-12_legacy-guis/
├── ravenmaven_gui.py
├── structure_preview_gui.py
├── codecop_gui.py
├── gui_main.py
└── README.md (explanation of archived files)
```

---

## 📊 Migration Risk Assessment

### Low Risk
✅ Simple import changes (PyQt5 → PyQt6)
✅ Enum value updates (add namespace)
✅ exec_() → exec() change

### Medium Risk
⚠️ Custom widgets may need adjustments
⚠️ Signal/slot connections (verify all work)
⚠️ Style sheets may need updates

### High Risk
🔴 Third-party integrations (PoeClient, etc.)
🔴 Threading and worker patterns
🔴 File dialogs and OS integration

---

## 📅 Estimated Timeline

| Phase | Duration | Priority |
|-------|----------|----------|
| Phase 1: Cleanup | 1-2 hours | HIGH |
| Phase 2: PyQt6 Migration | 4-6 hours | HIGH |
| Phase 3: Modernization | 2-4 hours | MEDIUM |
| Phase 4: Testing | 2-3 hours | HIGH |
| Phase 5: Final Cleanup | 1 hour | LOW |

**Total Estimated Time:** 10-16 hours

---

## 🚦 Recommended Next Steps

1. **IMMEDIATE:** Run cleanup deletion script to remove duplicates
2. **TODAY:** Backup current working state
3. **TODAY:** Install PyQt6 in virtual environment
4. **TODAY:** Start migration of `jelly_rancher_main.py`
5. **TOMORROW:** Test and validate
6. **TOMORROW:** Update documentation

---

## 🎯 Success Criteria

✅ GUI launches without errors
✅ All major features work (media org, subtitles, batch processing)
✅ No PyQt5 or Tkinter/CustomTkinter code remains
✅ Project size reduced by removing duplicates and legacy code
✅ Documentation updated
✅ Tests pass

---

## 📞 Support Resources

- **PyQt6 Documentation:** https://www.riverbankcomputing.com/static/Docs/PyQt6/
- **Migration Guide:** https://www.riverbankcomputing.com/static/Docs/PyQt6/pyqt5_differences.html
- **Qt6 Changes:** https://doc.qt.io/qt-6/portingguide.html

---

**Ready to proceed?** Start with Phase 1 cleanup, then we'll tackle the PyQt6 migration systematically.
