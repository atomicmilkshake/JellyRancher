# JellyRancher GUI Redesign - Comprehensive Analysis & Plan

**Date:** 2025-11-16 20:50:40  
**Status:** Planning Phase  
**Priority:** Critical - User Experience Overhaul

---

## 📊 Executive Summary

**Problem Statement:**  
Current GUI is "janky, counterintuitive, rigid/inflexible, and desperately calls for modernization." User must rescan entire library every session, cannot save progress, and workflow is inflexible.

**Core Issues:**
1. **No state persistence** - Everything lost on close
2. **Rigid workflow** - Forced linear progression through 9 steps
3. **Poor UX** - Basic widgets, no polish, clunky interactions
4. **Rescanning pain** - Must rescan 1.3TB (4,188 files) every session
5. **No project concept** - Can't save/resume work

**Recommended Solution:**  
Incremental modernization with project management system as foundation, followed by UI polish and workflow flexibility.

---

## 🔍 Current State Analysis

### Architecture Overview

**File:** `jelly_rancher_clean.py` (2,445 lines)

**Structure:**
```
jelly_rancher_clean.py
├── FolderContentSelectionDialog (QDialog) - Lines 77-195
│   └── Subfolder/file selection UI
├── ScanWorker (QThread) - Lines 198-404
│   └── Background file scanning
├── MultiScanWorker (QThread) - Lines 407-442
│   └── Multi-folder scanning coordinator
├── LLMAnalysisWorker (QThread) - Lines 445-571
│   └── LLM structure analysis
├── MetadataWorker (QThread) - Lines 574-718
│   └── TMDB/TVDB metadata lookup
├── ActionPlanWorker (QThread) - Lines 721-752
│   └── Generate reorganization plan
└── JellyRancherClean (QMainWindow) - Lines 755-2445
    ├── Data storage (in-memory only)
    ├── 5 tabs (scan, metadata, review, execute, subtitles)
    ├── ~60 methods for UI creation and event handling
    └── No persistence layer

```

### Current Workflow (9-Point System)

**Tab 1-2: Scan & Overview**
- Add folders → Scan → View results
- Problem: Must repeat every session

**Tab 3-4: LLM & Metadata**
- LLM analysis → Metadata lookup
- Problem: Results not saved, can't compare different LLM models

**Tab 5: Review Actions**
- Review proposed operations → Approve/reject
- Problem: Approval state lost on close

**Tab 6-7: Snapshot & Execute**
- Create snapshot → Execute operations
- Problem: No way to track execution history

**Tab 8-9: Subtitles**
- Analyze coverage → Download subtitles
- Problem: Separate from main workflow

### Data Flow Analysis

**What's Persisted:**
- ✅ Scan sessions → SQLite (`data/inventory.db`)
  - Files, folders, MD5 hashes
  - Can query by session ID
- ✅ LLM analysis → JSON files (`data/llm_analysis_*.json`)
  - One-off saves, not linked to workflow
- ✅ Jellyfin config → JSON (`data/jellyfin_config.json`)

**What's Lost:**
- ❌ Selected folders for scanning
- ❌ Excluded subfolders
- ❌ LLM analysis results (in memory)
- ❌ Detected media list
- ❌ Action plan with user approvals
- ❌ Workflow progress (which step)
- ❌ UI state (tab position, table sorting, etc.)

### User Pain Points (Documented)

**From Phase 31G (Nov 16):**
- "GUI looks pretty unsophisticated and shitty"
- Progress bar didn't work
- Couldn't resize columns
- No model selection for LLM

**From Phase 32 (Nov 16):**
- "Janky and counterintuitive"
- "Rigid/inflexible"
- "Desperately calls for modernization"
- Rescanning is inconvenient
- Can't save/resume work

**Historical Issues:**
- Phase 2.0.0: "I don't know what order to do things in"
- Phase 2.0.1: Snapshot functionality was removed
- Phase 2.0.2: Needed numbered workflow buttons

---

## 🎯 Design Goals

### Primary Objectives

1. **State Persistence**
   - Save all workflow state
   - Resume from any point
   - No data loss on close/crash

2. **Workflow Flexibility**
   - Non-linear progression
   - Skip/reorder steps
   - Multiple analysis versions
   - Side-by-side comparisons

3. **Modern UX**
   - Professional appearance
   - Intuitive interactions
   - Visual feedback
   - Responsive design

4. **Project Management**
   - Create/open/save projects
   - Recent projects list
   - Auto-save functionality
   - Export/import capability

5. **Performance**
   - Fast loading from database
   - Responsive UI (no freezing)
   - Efficient memory usage
   - Background operations

### Secondary Objectives

- Keyboard shortcuts
- Contextual help
- Undo/redo capability
- Search/filter functionality
- Batch operations
- Customizable layouts
- Dark mode support
- Accessibility features

---

## 🏗️ Proposed Architecture

### Option 1: Modern PyQt6 (Recommended)

**Approach:** Incremental modernization

**Components:**

```
jelly_rancher_v2/
├── core/
│   ├── project_manager.py          # NEW: Project state management
│   ├── state_serializer.py         # NEW: Save/load state
│   └── workflow_engine.py          # NEW: Non-linear workflow
├── gui/
│   ├── main_window.py              # Refactored main window
│   ├── project_dialog.py           # NEW: Project management UI
│   ├── modern_theme.qss            # NEW: Modern stylesheet
│   ├── widgets/
│   │   ├── scan_panel.py           # Modular scan UI
│   │   ├── analysis_panel.py       # Modular analysis UI
│   │   ├── review_panel.py         # Modular review UI
│   │   └── comparison_view.py      # NEW: Side-by-side comparison
│   └── docks/
│       ├── folder_dock.py          # Dockable folder browser
│       ├── progress_dock.py        # Dockable progress viewer
│       └── log_dock.py             # Dockable log viewer
├── models/
│   ├── project.py                  # Project data model
│   ├── scan_session.py             # Scan session model
│   └── analysis_version.py         # Analysis version model
└── database/
    ├── schema_v2.sql               # Updated schema
    └── migrations/                 # Database migrations
```

**Database Schema (Extended):**

```sql
-- Projects table
CREATE TABLE projects (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    created_at DATETIME,
    last_opened DATETIME,
    workflow_step INTEGER,
    notes TEXT
);

-- Project scan sessions (many-to-many)
CREATE TABLE project_scan_sessions (
    project_id INTEGER,
    scan_session_id INTEGER,
    added_at DATETIME,
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (scan_session_id) REFERENCES scan_sessions(id)
);

-- Project state (serialized workflow state)
CREATE TABLE project_state (
    project_id INTEGER PRIMARY KEY,
    selected_folders JSON,
    excluded_subfolders JSON,
    workflow_data JSON,
    ui_state JSON,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

-- Analysis versions (multiple LLM runs)
CREATE TABLE analysis_versions (
    id INTEGER PRIMARY KEY,
    project_id INTEGER,
    version_number INTEGER,
    model_name TEXT,
    created_at DATETIME,
    analysis_json_path TEXT,
    notes TEXT,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

-- Action plans (with user approvals)
CREATE TABLE action_plans (
    id INTEGER PRIMARY KEY,
    project_id INTEGER,
    analysis_version_id INTEGER,
    created_at DATETIME,
    actions JSON,
    user_approvals JSON,
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (analysis_version_id) REFERENCES analysis_versions(id)
);
```

**Pros:**
- Incremental migration (less risky)
- Keeps existing PyQt6 knowledge
- Can reuse existing workers/backends
- Faster implementation timeline
- Maintains desktop app benefits

**Cons:**
- Still limited by PyQt6 constraints
- Requires significant refactoring
- QSS styling has limitations
- Not as modern as web UI

**Timeline:** 2-3 weeks
- Week 1: Project management system
- Week 2: UI modernization
- Week 3: Workflow flexibility + polish

---

### Option 2: Web-Based UI

**Approach:** Complete rewrite with modern web stack

**Stack:**
- **Backend:** FastAPI (Python)
- **Frontend:** React + TypeScript
- **UI Library:** Material-UI or Ant Design
- **State Management:** Redux or Zustand
- **API:** RESTful + WebSockets for progress

**Architecture:**

```
jellyrancher-web/
├── backend/
│   ├── api/
│   │   ├── projects.py
│   │   ├── scans.py
│   │   ├── analysis.py
│   │   └── actions.py
│   ├── services/
│   │   ├── scan_service.py
│   │   ├── llm_service.py
│   │   └── metadata_service.py
│   └── database/
│       └── models.py
└── frontend/
    ├── src/
    │   ├── components/
    │   │   ├── ProjectManager/
    │   │   ├── ScanPanel/
    │   │   ├── AnalysisPanel/
    │   │   └── ReviewPanel/
    │   ├── pages/
    │   │   ├── Dashboard.tsx
    │   │   ├── Project.tsx
    │   │   └── Settings.tsx
    │   ├── store/
    │   │   └── projectSlice.ts
    │   └── api/
    │       └── client.ts
    └── public/
```

**Pros:**
- Modern, beautiful UI
- Responsive design
- Better UX possibilities
- Can run remotely
- Easier to iterate on design
- Rich component libraries

**Cons:**
- Complete rewrite (high risk)
- New tech stack to learn
- Longer implementation time
- Requires browser
- More complex deployment

**Timeline:** 4-6 weeks
- Week 1-2: Backend API + database
- Week 3-4: Frontend core features
- Week 5-6: Polish + testing

---

### Option 3: Hybrid Approach

**Approach:** PyQt6 + embedded web views

**Components:**
- PyQt6 main window and core functionality
- QWebEngineView for complex visualizations
- FastAPI backend for web components
- React components for specific UIs

**Use Cases:**
- Main UI: PyQt6 (traditional desktop)
- Comparison views: Web component
- Analysis visualizations: Web component
- Settings: PyQt6 dialog

**Pros:**
- Best of both worlds
- Gradual migration path
- Can modernize piece by piece
- Keeps desktop app benefits

**Cons:**
- Two tech stacks to maintain
- Complexity in communication
- Larger application size
- More potential bugs

**Timeline:** 3-4 weeks

---

## 📋 Implementation Phases

### Phase 32A: Project Management Foundation (Week 1)

**Goal:** Eliminate rescanning pain point

**Tasks:**
1. **Database Schema** (4 hours)
   - Add projects, project_state, analysis_versions tables
   - Create migration script
   - Test schema with sample data

2. **ProjectManager Class** (6 hours)
   - CRUD operations for projects
   - Save/load project state
   - Link scan sessions to projects
   - Auto-save functionality

3. **GUI Integration** (8 hours)
   - File menu (New/Open/Save/Recent)
   - Project selector widget
   - Auto-save on workflow progress
   - Unsaved changes warning

4. **State Serialization** (6 hours)
   - Serialize all workflow state
   - Deserialize and restore state
   - Handle version compatibility
   - Error handling

**Deliverables:**
- Working project system
- Can save/load complete state
- No more rescanning required
- Recent projects list

**Success Metrics:**
- User can close and reopen project
- All state restored correctly
- Load time < 2 seconds
- No data loss

---

### Phase 32B: UI Modernization (Week 2)

**Goal:** Make GUI look professional

**Tasks:**
1. **Modern Theme** (8 hours)
   - Create QSS stylesheet
   - Dark/light mode support
   - Color palette design
   - Typography improvements

2. **Widget Replacement** (10 hours)
   - Replace QTableWidget with QTreeView
   - Add sortable/filterable tables
   - Implement search functionality
   - Better progress indicators

3. **Layout Improvements** (8 hours)
   - Replace tabs with dock system
   - Flexible panel arrangement
   - Splitters for resizing
   - Save/restore layout

4. **Visual Polish** (6 hours)
   - Icons for all actions
   - Animations for feedback
   - Tooltips everywhere
   - Status indicators

**Deliverables:**
- Modern, professional appearance
- Flexible layout system
- Better visual feedback
- Improved usability

**Success Metrics:**
- User satisfaction with appearance
- Faster task completion
- Fewer UX complaints
- Positive feedback

---

### Phase 32C: Workflow Flexibility (Week 3)

**Goal:** Make workflow non-linear and powerful

**Tasks:**
1. **Non-Linear Workflow** (8 hours)
   - Remove forced step progression
   - Enable skip/reorder
   - Smart validation
   - Dependency checking

2. **Analysis Versions** (8 hours)
   - Save multiple LLM analyses
   - Version comparison UI
   - Switch between versions
   - Diff visualization

3. **Comparison Tools** (8 hours)
   - Side-by-side analysis view
   - Diff highlighting
   - Merge capabilities
   - Export comparisons

4. **Quick Actions** (6 hours)
   - Keyboard shortcuts
   - Context menus
   - Batch operations
   - Undo/redo

**Deliverables:**
- Flexible workflow engine
- Multiple analysis versions
- Comparison tools
- Power user features

**Success Metrics:**
- Can skip steps safely
- Can compare analyses
- Faster workflow completion
- More experimentation

---

## 🎨 UI/UX Design Principles

### Visual Design

**Color Palette:**
```
Primary:   #2196F3 (Blue)
Secondary: #4CAF50 (Green)
Accent:    #FF9800 (Orange)
Error:     #F44336 (Red)
Warning:   #FFC107 (Amber)

Background (Light): #FAFAFA
Background (Dark):  #121212
Surface (Light):    #FFFFFF
Surface (Dark):     #1E1E1E
```

**Typography:**
```
Headings:  Segoe UI Bold, 18-24pt
Body:      Segoe UI Regular, 11pt
Monospace: Consolas, 10pt
```

**Spacing:**
```
Tight:  4px
Normal: 8px
Loose:  16px
Wide:   24px
```

### Interaction Patterns

**Feedback:**
- Immediate visual response to all actions
- Progress indicators for long operations
- Success/error notifications
- Hover states on all interactive elements

**Consistency:**
- Same action = same button style
- Same data = same visualization
- Same pattern throughout app

**Efficiency:**
- Keyboard shortcuts for common actions
- Context menus for quick access
- Batch operations where applicable
- Smart defaults

### Information Architecture

**Dashboard View:**
```
┌─────────────────────────────────────────────────┐
│  JellyRancher                    [Project: ▼]  │
├─────────────────────────────────────────────────┤
│  Recent Projects  │  Quick Actions              │
│  ─────────────────┼──────────────────────────   │
│  • Media Cleanup  │  🔍 Scan Folders            │
│  • TV Shows 2025  │  🤖 Run LLM Analysis        │
│  • Movie Library  │  📋 Review Actions          │
│                   │  ▶️  Execute Plan           │
└───────────────────┴─────────────────────────────┘
```

**Project View:**
```
┌─────────────────────────────────────────────────┐
│  Project: Media Cleanup 2025        [Save] [⚙️] │
├──────┬──────────────────────────────────────────┤
│ Scan │  Selected Folders:                       │
│ LLM  │  • W:\#MEDIA (4,188 files, 1.3TB)       │
│ Meta │  • W:\#MEDIA2 (2,341 files, 800GB)      │
│ Plan │                                          │
│ Exec │  Analysis Versions:                      │
│      │  • v1: Claude-Sonnet-4.5 (81s)          │
│      │  • v2: Gemini-2.5-Pro (65s) [Active]    │
│      │                                          │
│      │  Action Plan: 150 operations             │
│      │  ✓ Approved: 120  ⏸ Pending: 30         │
└──────┴──────────────────────────────────────────┘
```

---

## 🔄 Migration Strategy

### Approach: Gradual Refactoring

**Step 1: Extract Core Logic**
- Move business logic out of GUI
- Create service layer
- Separate concerns

**Step 2: Add Project System**
- Implement database schema
- Create ProjectManager
- Add save/load functionality

**Step 3: Refactor GUI**
- Split monolithic file
- Create modular components
- Apply modern theme

**Step 4: Enhance Features**
- Add flexibility
- Improve UX
- Polish interactions

### Backward Compatibility

**Data Migration:**
- Existing scan sessions preserved
- LLM analysis files imported
- Settings migrated
- No data loss

**Feature Parity:**
- All current features maintained
- Enhanced, not removed
- Gradual rollout of new features

---

## 📊 Success Criteria

### Must Have (MVP)

- ✅ Project save/load functionality
- ✅ No rescanning required
- ✅ Resume from any point
- ✅ Modern appearance
- ✅ All existing features work

### Should Have

- ✅ Non-linear workflow
- ✅ Multiple analysis versions
- ✅ Comparison tools
- ✅ Keyboard shortcuts
- ✅ Dark mode

### Nice to Have

- ⭐ Export/import projects
- ⭐ Project templates
- ⭐ Advanced filtering
- ⭐ Batch operations
- ⭐ Analytics dashboard

---

## 🎯 Next Steps

### Immediate Actions

1. **User Feedback** (This document)
   - Review proposed approach
   - Confirm priorities
   - Identify must-haves

2. **Detailed Design** (If approved)
   - Wireframes for key screens
   - Database schema finalization
   - API design (if web-based)

3. **Prototype** (Week 1)
   - Project management proof-of-concept
   - Basic save/load functionality
   - User testing

4. **Implementation** (Weeks 2-3)
   - Full project system
   - UI modernization
   - Workflow flexibility

### Questions for User

1. **Approach:** Modern PyQt6, Web-based, or Hybrid?
2. **Timeline:** How urgent? (2 weeks vs 4-6 weeks)
3. **Priority:** Project system first, or UI polish first?
4. **Inspiration:** Any apps with UX you admire?
5. **Features:** Which "nice to have" features are actually critical?
6. **Risk Tolerance:** Incremental or revolutionary change?

---

## 📚 References

- Current Implementation: `jelly_rancher_clean.py` (2,445 lines)
- Legacy Implementation: `scripts/core/jelly_rancher_main.py` (3,568 lines)
- Database Schema: `scripts/core/inventory_repository.py`
- User Guide: `docs/USER_GUIDE.md`
- Previous Migration: `docs/PYQT6_MIGRATION_PLAN.md`
- User Feedback: `agent-journal.md` (Phases 31G, 32)

---

**Document Version:** 1.0  
**Last Updated:** 2025-11-16 20:50:40  
**Status:** Awaiting User Feedback

