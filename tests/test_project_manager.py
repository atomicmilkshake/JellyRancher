#!/usr/bin/env python3
"""
Comprehensive unit and integration tests for ProjectManager and Project classes.

Tests cover:
- Project creation, loading, saving, and deletion
- Database operations with proper error handling
- JSON serialization/deserialization
- Project state management
- Archive/unarchive functionality
- Integration between components
- Error conditions and edge cases
"""

import unittest
import tempfile
import shutil
import json
import sqlite3
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
from datetime import datetime

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.core.project_manager import (
    ProjectManager,
    Project,
    ProjectState,
    logger
)


class TestProject(unittest.TestCase):
    """Test cases for Project dataclass."""

    def test_project_creation(self):
        """Test basic project creation and serialization."""
        project = Project(
            name="Test Project",
            description="A test project",
            created_at="2025-11-19T12:00:00"
        )

        self.assertEqual(project.name, "Test Project")
        self.assertEqual(project.description, "A test project")
        self.assertEqual(project.created_at, "2025-11-19T12:00:00")
        self.assertEqual(project.state, "active")

    def test_project_to_dict(self):
        """Test project serialization to dictionary."""
        project = Project(
            id=1,
            name="Test Project",
            description="A test project",
            created_at="2025-11-19T12:00:00",
            last_opened="2025-11-19T12:30:00",
            state="active",
            settings={"theme": "dark"}
        )

        data = project.to_dict()

        self.assertEqual(data['id'], 1)
        self.assertEqual(data['name'], "Test Project")
        self.assertEqual(data['description'], "A test project")
        self.assertEqual(data['created_at'], "2025-11-19T12:00:00")
        self.assertEqual(data['last_opened'], "2025-11-19T12:30:00")
        self.assertEqual(data['state'], "active")
        self.assertEqual(data['settings'], {"theme": "dark"})


class TestProjectManager(unittest.TestCase):
    """Test cases for ProjectManager class."""

    def setUp(self):
        """Create temporary database for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test.db"
        self.pm = ProjectManager(db_path=str(self.db_path))

        # Create tables
        with self.pm._get_connection() as conn:
            # Projects table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT,
                    created_at TEXT NOT NULL,
                    last_opened TEXT NOT NULL,
                    state TEXT NOT NULL DEFAULT 'active',
                    settings_json TEXT DEFAULT '{}'
                )
            ''')
            
            # Project state table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS project_state (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL UNIQUE,
                    current_view TEXT,
                    ui_state_json TEXT DEFAULT '{}',
                    last_scan_session_id INTEGER,
                    last_analysis_id INTEGER,
                    last_action_plan_id INTEGER,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
                )
            ''')
            
            # Related tables (simplified for testing)
            conn.execute('''
                CREATE TABLE IF NOT EXISTS project_scan_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    scan_start TEXT NOT NULL,
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS project_analyses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    analysis_date TEXT NOT NULL,
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS project_action_plans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
                )
            ''')

    def tearDown(self):
        """Clean up temporary database."""
        shutil.rmtree(self.temp_dir)

    def test_init(self):
        """Test ProjectManager initialization."""
        pm = ProjectManager()
        self.assertIsInstance(pm.db_path, Path)
        self.assertTrue(pm.db_path.parent.exists())

    def test_get_connection_context_manager(self):
        """Test database connection context manager."""
        with self.pm._get_connection() as conn:
            self.assertIsInstance(conn, sqlite3.Connection)
            # Test that we can execute queries
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            self.assertEqual(result[0], 1)

    @patch('scripts.core.project_manager.logger')
    def test_create_project_success(self, mock_logger):
        """Test successful project creation."""
        project = self.pm.create_project("Test Project", "A test project")

        self.assertIsInstance(project, Project)
        self.assertEqual(project.name, "Test Project")
        self.assertEqual(project.description, "A test project")
        self.assertIsNotNone(project.id)
        self.assertIsNotNone(project.created_at)
        self.assertIsNotNone(project.last_opened)

        # Verify in database
        with self.pm._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM projects WHERE id = ?", (project.id,))
            row = cursor.fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row['name'], "Test Project")

    def test_create_project_validation_error(self):
        """Test project creation with invalid parameters."""
        with self.assertRaises(ValueError):
            self.pm.create_project("", "description")

        with self.assertRaises(ValueError):
            self.pm.create_project("name", "")

    @patch('scripts.core.project_manager.sqlite3.connect')
    def test_create_project_database_error(self, mock_connect):
        """Test project creation with database error."""
        mock_connect.side_effect = sqlite3.Error("Database error")

        result = self.pm.create_project("Test Project", "description")
        self.assertIsNone(result)

    def test_load_project_by_id(self):
        """Test loading project by ID."""
        # Create a project first
        created = self.pm.create_project("Test Project", "description")
        self.assertIsNotNone(created)

        # Load it back
        loaded = self.pm.load_project(project_id=created.id)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.id, created.id)
        self.assertEqual(loaded.name, created.name)

    def test_load_project_by_name(self):
        """Test loading project by name."""
        # Create a project first
        created = self.pm.create_project("Test Project", "description")
        self.assertIsNotNone(created)

        # Load it back
        loaded = self.pm.load_project(name="Test Project")
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.name, "Test Project")

    def test_load_project_not_found(self):
        """Test loading non-existent project."""
        loaded = self.pm.load_project(project_id=999)
        self.assertIsNone(loaded)

        loaded = self.pm.load_project(name="Non-existent")
        self.assertIsNone(loaded)

    @patch('scripts.core.project_manager.json.loads')
    def test_load_project_json_error(self, mock_json_loads):
        """Test loading project with JSON parsing error."""
        # Create a project first
        created = self.pm.create_project("Test Project", "description")

        # Mock JSON parsing to fail
        mock_json_loads.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)

        loaded = self.pm.load_project(project_id=created.id)
        self.assertIsNone(loaded)

    def test_save_project_success(self):
        """Test successful project saving."""
        project = Project(
            name="Test Project",
            description="A test project"
        )

        result = self.pm.save_project(project)
        self.assertTrue(result)
        self.assertIsNotNone(project.id)

    def test_save_project_validation_error(self):
        """Test saving project with validation error."""
        project = Project(name="", description="test")

        result = self.pm.save_project(project)
        self.assertFalse(result)

    @patch('scripts.core.project_manager.sqlite3.connect')
    def test_save_project_database_error(self, mock_connect):
        """Test saving project with database error."""
        mock_connect.side_effect = sqlite3.Error("Database error")

        project = Project(name="Test", description="test")
        result = self.pm.save_project(project)
        self.assertFalse(result)

    def test_delete_project_success(self):
        """Test successful project deletion."""
        # Create a project first
        created = self.pm.create_project("Test Project", "description")

        # Delete it
        result = self.pm.delete_project(created.id)
        self.assertTrue(result)

        # Verify it's gone
        loaded = self.pm.load_project(project_id=created.id)
        self.assertIsNone(loaded)

    def test_delete_project_not_found(self):
        """Test deleting non-existent project."""
        result = self.pm.delete_project(999)
        self.assertFalse(result)

    def test_list_projects_empty(self):
        """Test listing projects when none exist."""
        projects = self.pm.list_projects()
        self.assertEqual(len(projects), 0)

    def test_list_projects_with_data(self):
        """Test listing projects with data."""
        # Create multiple projects
        p1 = self.pm.create_project("Project 1", "desc1")
        p2 = self.pm.create_project("Project 2", "desc2")

        projects = self.pm.list_projects()
        self.assertEqual(len(projects), 2)

        names = [p.name for p in projects]
        self.assertIn("Project 1", names)
        self.assertIn("Project 2", names)

    def test_list_projects_archived_only(self):
        """Test listing only archived projects."""
        # Create projects
        p1 = self.pm.create_project("Project 1", "desc1")
        p2 = self.pm.create_project("Project 2", "desc2")

        # Archive one
        self.pm.archive_project(p1.id)

        archived = self.pm.list_projects(archived_only=True)
        self.assertEqual(len(archived), 1)
        self.assertEqual(archived[0].name, "Project 1")

        active = self.pm.list_projects(archived_only=False)
        self.assertEqual(len(active), 1)
        self.assertEqual(active[0].name, "Project 2")

    @patch('scripts.core.project_manager.json.loads')
    def test_list_projects_json_error(self, mock_json_loads):
        """Test listing projects with JSON parsing error."""
        # Create a project
        self.pm.create_project("Test", "desc")

        # Mock JSON parsing to fail
        mock_json_loads.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)

        projects = self.pm.list_projects()
        self.assertEqual(len(projects), 0)  # Should return empty list on error

    def test_get_project_by_name(self):
        """Test getting project by name."""
        # Create a project
        created = self.pm.create_project("Test Project", "description")

        # Get it by name
        found = self.pm.get_project_by_name("Test Project")
        self.assertIsNotNone(found)
        self.assertEqual(found.id, created.id)

    def test_get_project_by_name_not_found(self):
        """Test getting non-existent project by name."""
        found = self.pm.get_project_by_name("Non-existent")
        self.assertIsNone(found)

    def test_save_project_state(self):
        """Test saving project state."""
        # Create a project first
        project = self.pm.create_project("Test", "desc")

        state = ProjectState(
            project_id=project.id,
            ui_state={"tab": "scan"},
            workflow_state={"step": 1}
        )

        result = self.pm.save_project_state(state)
        self.assertTrue(result)
        self.assertIsNotNone(state.id)

    def test_load_project_state(self):
        """Test loading project state."""
        # Create project and state
        project = self.pm.create_project("Test", "desc")
        state = ProjectState(
            project_id=project.id,
            ui_state={"tab": "scan"},
            workflow_state={"step": 1}
        )
        self.pm.save_project_state(state)

        # Load it back
        loaded = self.pm.load_project_state(project.id)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.ui_state, {"tab": "scan"})
        self.assertEqual(loaded.workflow_state, {"step": 1})

    def test_load_project_state_not_found(self):
        """Test loading state for non-existent project."""
        loaded = self.pm.load_project_state(999)
        self.assertIsNone(loaded)

    def test_get_recent_projects(self):
        """Test getting recent projects."""
        # Create multiple projects
        p1 = self.pm.create_project("Project 1", "desc1")
        p2 = self.pm.create_project("Project 2", "desc2")
        p3 = self.pm.create_project("Project 3", "desc3")

        recent = self.pm.get_recent_projects(limit=2)
        self.assertEqual(len(recent), 2)
        # Should be ordered by creation time (most recent first)
        self.assertEqual(recent[0].name, "Project 3")
        self.assertEqual(recent[1].name, "Project 2")

    def test_archive_project(self):
        """Test archiving a project."""
        # Create a project
        project = self.pm.create_project("Test", "desc")

        # Archive it
        result = self.pm.archive_project(project.id)
        self.assertTrue(result)

        # Verify it's archived
        with self.pm._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT archived FROM projects WHERE id = ?", (project.id,))
            row = cursor.fetchone()
            self.assertEqual(row['archived'], 1)

    def test_archive_project_not_found(self):
        """Test archiving non-existent project."""
        result = self.pm.archive_project(999)
        self.assertFalse(result)

    def test_unarchive_project(self):
        """Test unarchiving a project."""
        # Create and archive a project
        project = self.pm.create_project("Test", "desc")
        self.pm.archive_project(project.id)

        # Unarchive it
        result = self.pm.unarchive_project(project.id)
        self.assertTrue(result)

        # Verify it's unarchived
        with self.pm._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT archived FROM projects WHERE id = ?", (project.id,))
            row = cursor.fetchone()
            self.assertEqual(row['archived'], 0)

    def test_unarchive_project_not_found(self):
        """Test unarchiving non-existent project."""
        result = self.pm.unarchive_project(999)
        self.assertFalse(result)


class TestProjectManagerIntegration(unittest.TestCase):
    """Integration tests for ProjectManager."""

    def setUp(self):
        """Create temporary database for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test.db"
        self.pm = ProjectManager(db_path=str(self.db_path))

    def tearDown(self):
        """Clean up temporary database."""
        shutil.rmtree(self.temp_dir)

    def test_full_project_lifecycle(self):
        """Test complete project lifecycle: create, save, load, modify, save, delete."""
        # Create project
        project = self.pm.create_project("Lifecycle Test", "Testing full lifecycle")
        self.assertIsNotNone(project)
        original_id = project.id

        # Modify project
        project.description = "Modified description"

        # Save changes
        result = self.pm.save_project(project)
        self.assertTrue(result)

        # Load and verify changes
        loaded = self.pm.load_project(project_id=original_id)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.description, "Modified description")

        # Save state
        state = ProjectState(
            project_id=project.id,
            ui_state={"current_tab": "analysis"},
            workflow_state={"current_step": 3}
        )
        state_result = self.pm.save_project_state(state)
        self.assertTrue(state_result)

        # Load state
        loaded_state = self.pm.load_project_state(project.id)
        self.assertIsNotNone(loaded_state)
        self.assertEqual(loaded_state.ui_state["current_tab"], "analysis")

        # Archive project
        archive_result = self.pm.archive_project(project.id)
        self.assertTrue(archive_result)

        # Verify archived status
        archived_projects = self.pm.list_projects(archived_only=True)
        self.assertEqual(len(archived_projects), 1)
        self.assertEqual(archived_projects[0].id, project.id)

        # Unarchive
        unarchive_result = self.pm.unarchive_project(project.id)
        self.assertTrue(unarchive_result)

        # Delete project
        delete_result = self.pm.delete_project(project.id)
        self.assertTrue(delete_result)

        # Verify deletion
        final_load = self.pm.load_project(project_id=original_id)
        self.assertIsNone(final_load)

    def test_multiple_projects_workflow(self):
        """Test workflow with multiple projects."""
        # Create multiple projects
        projects = []
        for i in range(3):
            project = self.pm.create_project(f"Project {i}", f"Description {i}")
            projects.append(project)

        # List all
        all_projects = self.pm.list_projects()
        self.assertEqual(len(all_projects), 3)

        # Archive middle project
        self.pm.archive_project(projects[1].id)

        # Check counts
        active = self.pm.list_projects(archived_only=False)
        archived = self.pm.list_projects(archived_only=True)
        self.assertEqual(len(active), 2)
        self.assertEqual(len(archived), 1)

        # Recent projects
        recent = self.pm.get_recent_projects(limit=2)
        self.assertEqual(len(recent), 2)
        self.assertEqual(recent[0].name, "Project 2")  # Most recent


if __name__ == '__main__':
    unittest.main()