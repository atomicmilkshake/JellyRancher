-- JellyRancher Database Schema
-- Project Management Tables for Phase 32A

-- ============================================================================
-- PROJECTS TABLE
-- ============================================================================
-- Core project metadata and lifecycle management
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_opened TIMESTAMP,
    state TEXT DEFAULT 'active' CHECK(state IN ('active', 'archived', 'template')),
    settings_json TEXT  -- Project-specific settings (JSON)
);

CREATE INDEX IF NOT EXISTS idx_projects_state ON projects(state);
CREATE INDEX IF NOT EXISTS idx_projects_last_opened ON projects(last_opened DESC);


-- ============================================================================
-- PROJECT SCAN SESSIONS TABLE
-- ============================================================================
-- Links scan sessions to projects, tracks scan metadata
CREATE TABLE IF NOT EXISTS project_scan_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    scan_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    scan_end TIMESTAMP,
    total_files INTEGER DEFAULT 0,
    total_size_bytes INTEGER DEFAULT 0,
    scan_options_json TEXT,  -- MD5 enabled, deep scan, etc. (JSON)
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_scan_sessions_project ON project_scan_sessions(project_id);
CREATE INDEX IF NOT EXISTS idx_scan_sessions_date ON project_scan_sessions(scan_start DESC);


-- ============================================================================
-- PROJECT ANALYSES TABLE
-- ============================================================================
-- Stores LLM analysis results for comparison and history
CREATE TABLE IF NOT EXISTS project_analyses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    scan_session_id INTEGER,
    model_name TEXT NOT NULL,
    analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    prompt_text TEXT,
    response_text TEXT,
    parsed_json TEXT,  -- Structured analysis results (JSON)
    confidence TEXT CHECK(confidence IN ('HIGH', 'MEDIUM', 'LOW')),
    issues_found INTEGER DEFAULT 0,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (scan_session_id) REFERENCES project_scan_sessions(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_analyses_project ON project_analyses(project_id);
CREATE INDEX IF NOT EXISTS idx_analyses_date ON project_analyses(analysis_date DESC);
CREATE INDEX IF NOT EXISTS idx_analyses_confidence ON project_analyses(confidence);


-- ============================================================================
-- PROJECT ACTION PLANS TABLE
-- ============================================================================
-- Groups proposed operations into reviewable action plans
CREATE TABLE IF NOT EXISTS project_action_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    analysis_id INTEGER,
    plan_name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_operations INTEGER DEFAULT 0,
    approved_count INTEGER DEFAULT 0,
    rejected_count INTEGER DEFAULT 0,
    executed BOOLEAN DEFAULT 0,
    execution_timestamp TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (analysis_id) REFERENCES project_analyses(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_action_plans_project ON project_action_plans(project_id);
CREATE INDEX IF NOT EXISTS idx_action_plans_executed ON project_action_plans(executed);


-- ============================================================================
-- PROJECT OPERATIONS TABLE
-- ============================================================================
-- Individual file operations within action plans
CREATE TABLE IF NOT EXISTS project_operations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action_plan_id INTEGER NOT NULL,
    operation_type TEXT NOT NULL CHECK(operation_type IN ('RENAME', 'MOVE', 'NFO', 'DELETE', 'COPY')),
    current_path TEXT,
    proposed_path TEXT,
    current_md5 TEXT,
    proposed_md5 TEXT,
    confidence TEXT CHECK(confidence IN ('HIGH', 'MEDIUM', 'LOW')),
    user_approved BOOLEAN DEFAULT NULL,  -- NULL=pending, 0=rejected, 1=approved
    executed BOOLEAN DEFAULT 0,
    execution_timestamp TIMESTAMP,
    rollback_data_json TEXT,  -- For undo capability (JSON)
    notes TEXT,
    FOREIGN KEY (action_plan_id) REFERENCES project_action_plans(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_operations_plan ON project_operations(action_plan_id);
CREATE INDEX IF NOT EXISTS idx_operations_approved ON project_operations(user_approved);
CREATE INDEX IF NOT EXISTS idx_operations_executed ON project_operations(executed);


-- ============================================================================
-- PROJECT STATE TABLE
-- ============================================================================
-- Preserves UI state and workflow position for resume capability
CREATE TABLE IF NOT EXISTS project_state (
    project_id INTEGER PRIMARY KEY,
    current_view TEXT,  -- Last active view/tab
    ui_state_json TEXT,  -- Window size, splitter positions, etc. (JSON)
    last_scan_session_id INTEGER,
    last_analysis_id INTEGER,
    last_action_plan_id INTEGER,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (last_scan_session_id) REFERENCES project_scan_sessions(id) ON DELETE SET NULL,
    FOREIGN KEY (last_analysis_id) REFERENCES project_analyses(id) ON DELETE SET NULL,
    FOREIGN KEY (last_action_plan_id) REFERENCES project_action_plans(id) ON DELETE SET NULL
);


-- ============================================================================
-- LINK SCANNED FILES TO PROJECTS
-- ============================================================================
-- Add project_id to existing scanned_files table (if it exists)
-- This allows existing scan data to be associated with projects

-- Note: This migration will be handled by the migration script
-- ALTER TABLE scanned_files ADD COLUMN project_id INTEGER REFERENCES projects(id);
-- CREATE INDEX IF NOT EXISTS idx_scanned_files_project ON scanned_files(project_id);

