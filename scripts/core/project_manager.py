#!/usr/bin/env python3
"""
Project Manager - CRUD operations and lifecycle management for JellyRancher projects

Provides high-level API for creating, loading, saving, and managing projects.
Integrates with the project management database schema from Phase 32A.

Usage:
    from scripts.core.project_manager import ProjectManager, Project
    
    pm = ProjectManager()
    
    # Create new project
    project = pm.create_project("My Media Library", "Organizing my collection")
    
    # Save project state
    pm.save_project(project)
    
    # Load existing project
    project = pm.load_project("My Media Library")
    
    # List all projects
    projects = pm.list_projects()
"""

import sqlite3
import logging
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict, field
from datetime import datetime
from contextlib import contextmanager

logger = logging.getLogger(__name__)


@dataclass
class Project:
    """
    Represents a JellyRancher project.
    
    A project encapsulates all workflow state:
    - Scanned folders and file inventory
    - LLM analyses
    - Action plans
    - Execution history
    - UI state
    """
    id: Optional[int] = None
    name: str = ""
    description: str = ""
    created_at: Optional[str] = None
    last_opened: Optional[str] = None
    state: str = "active"  # active, archived, template
    settings: Dict[str, Any] = field(default_factory=dict)
    
    # Runtime state (not persisted directly)
    scan_sessions: List[int] = field(default_factory=list)
    analyses: List[int] = field(default_factory=list)
    action_plans: List[int] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at,
            'last_opened': self.last_opened,
            'state': self.state,
            'settings': self.settings
        }


@dataclass
class ProjectState:
    """
    UI state for a project (for resume capability).
    """
    project_id: int
    current_view: Optional[str] = None
    ui_state: Dict[str, Any] = field(default_factory=dict)
    last_scan_session_id: Optional[int] = None
    last_analysis_id: Optional[int] = None
    last_action_plan_id: Optional[int] = None
    updated_at: Optional[str] = None


class ProjectManager:
    """
    Manages project lifecycle and persistence.
    
    Responsibilities:
    - Create, read, update, delete projects
    - Save and load project state
    - Track project history
    - Manage project metadata
    """
    
    def __init__(self, db_path: str = "data/media_library.db"):
        """
        Initialize project manager.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"ProjectManager initialized: {self.db_path}")
    
    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}", exc_info=True)
            raise
        finally:
            conn.close()
    
    def create_project(
        self, 
        name: str, 
        description: str = "",
        settings: Optional[Dict[str, Any]] = None
    ) -> Project:
        """
        Create a new project.
        
        Args:
            name: Project name (must be unique)
            description: Optional project description
            settings: Optional project-specific settings
        
        Returns:
            Created Project instance
        
        Raises:
            ValueError: If project name already exists or invalid
            RuntimeError: If database operation fails
        """
        try:
            if not name or not name.strip():
                raise ValueError("Project name cannot be empty")
            
            # Check if project already exists
            existing = self.get_project_by_name(name)
            if existing:
                raise ValueError(f"Project '{name}' already exists")
            
            now = datetime.now().isoformat()
            settings_json = json.dumps(settings or {})
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO projects (name, description, created_at, last_opened, state, settings_json)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (name, description, now, now, 'active', settings_json))
                
                project_id = cursor.lastrowid
                
                # Initialize project state
                cursor.execute('''
                    INSERT INTO project_state (project_id, updated_at)
                    VALUES (?, ?)
                ''', (project_id, now))
                
                logger.info(f"Created project: {name} (ID: {project_id})")
            
            return Project(
                id=project_id,
                name=name,
                description=description,
                created_at=now,
                last_opened=now,
                state='active',
                settings=settings or {}
            )
        except ValueError:
            # Re-raise validation errors
            raise
        except ValueError as e:
            logger.error(f"Failed to serialize project settings: {e}", exc_info=True)
            raise ValueError(f"Invalid project settings: {e}")
        except Exception as e:
            logger.error(f"Unexpected error creating project '{name}': {e}", exc_info=True)
            raise RuntimeError(f"Failed to create project: {e}")
    
    def load_project(self, project_id: Optional[int] = None, name: Optional[str] = None) -> Optional[Project]:
        """
        Load a project by ID or name.
        
        Args:
            project_id: Project ID
            name: Project name (used if project_id not provided)
        
        Returns:
            Project instance or None if not found
        """
        try:
            if not project_id and not name:
                raise ValueError("Must provide either project_id or name")
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                if project_id:
                    cursor.execute('SELECT * FROM projects WHERE id = ?', (project_id,))
                else:
                    cursor.execute('SELECT * FROM projects WHERE name = ?', (name,))
                
                row = cursor.fetchone()
                if not row:
                    logger.debug(f"Project not found: id={project_id}, name={name}")
                    return None
                
                # Update last_opened timestamp
                now = datetime.now().isoformat()
                cursor.execute(
                    'UPDATE projects SET last_opened = ? WHERE id = ?',
                    (now, row['id'])
                )
                
                # Load related data counts
                cursor.execute('''
                    SELECT id FROM project_scan_sessions 
                    WHERE project_id = ? 
                    ORDER BY scan_start DESC
                ''', (row['id'],))
                scan_sessions = [r['id'] for r in cursor.fetchall()]
                
                cursor.execute('''
                    SELECT id FROM project_analyses 
                    WHERE project_id = ? 
                    ORDER BY analysis_date DESC
                ''', (row['id'],))
                analyses = [r['id'] for r in cursor.fetchall()]
                
                cursor.execute('''
                    SELECT id FROM project_action_plans 
                    WHERE project_id = ? 
                    ORDER BY created_at DESC
                ''', (row['id'],))
                action_plans = [r['id'] for r in cursor.fetchall()]
                
                # Parse settings JSON
                settings = {}
                if row['settings_json']:
                    try:
                        settings = json.loads(row['settings_json'])
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse settings JSON for project {row['id']}: {e}")
                        settings = {}
                
                logger.info(f"Loaded project: {row['name']} (ID: {row['id']})")
                
                return Project(
                    id=row['id'],
                    name=row['name'],
                    description=row['description'],
                    created_at=row['created_at'],
                    last_opened=now,
                    state=row['state'],
                    settings=settings,
                    scan_sessions=scan_sessions,
                    analyses=analyses,
                    action_plans=action_plans
                )
        except ValueError:
            # Re-raise validation errors
            raise
        except Exception as e:
            logger.error(f"Unexpected error loading project (id={project_id}, name={name}): {e}", exc_info=True)
            return None
    
    def save_project(self, project: Project) -> bool:
        """
        Save project metadata (not full state, just metadata).
        
        Args:
            project: Project instance to save
        
        Returns:
            True if successful
        
        Raises:
            ValueError: If project has no ID
            RuntimeError: If save operation fails
        """
        try:
            if not project.id:
                raise ValueError("Cannot save project without ID. Use create_project() first.")
            
            settings_json = json.dumps(project.settings)
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE projects 
                    SET name = ?, description = ?, state = ?, settings_json = ?, last_opened = ?
                    WHERE id = ?
                ''', (
                    project.name,
                    project.description,
                    project.state,
                    settings_json,
                    datetime.now().isoformat(),
                    project.id
                ))
                
                if cursor.rowcount == 0:
                    logger.warning(f"No project found with ID {project.id} to update")
                    return False
                
                logger.info(f"Saved project: {project.name} (ID: {project.id})")
                return True
        except ValueError:
            # Re-raise validation errors
            raise
        except json.JSONEncodeError as e:
            logger.error(f"Failed to serialize project settings for {project.name}: {e}", exc_info=True)
            raise ValueError(f"Invalid project settings: {e}")
        except Exception as e:
            logger.error(f"Unexpected error saving project {project.name} (ID: {project.id}): {e}", exc_info=True)
            raise RuntimeError(f"Failed to save project: {e}")
    
    def delete_project(self, project_id: int) -> bool:
        """
        Delete a project and all associated data.
        
        Args:
            project_id: ID of project to delete
        
        Returns:
            True if successful
        
        Note:
            This cascades to all related tables due to ON DELETE CASCADE
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM projects WHERE id = ?', (project_id,))
                
                if cursor.rowcount > 0:
                    logger.info(f"Deleted project ID: {project_id}")
                    return True
                else:
                    logger.warning(f"Project ID {project_id} not found for deletion")
                    return False
        except Exception as e:
            logger.error(f"Unexpected error deleting project ID {project_id}: {e}", exc_info=True)
            raise RuntimeError(f"Failed to delete project: {e}")
    
    def list_projects(
        self, 
        state: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Project]:
        """
        List all projects, optionally filtered by state.
        
        Args:
            state: Filter by state ('active', 'archived', 'template')
            limit: Maximum number of projects to return
        
        Returns:
            List of Project instances, ordered by last_opened (most recent first)
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                query = 'SELECT * FROM projects'
                params = []
                
                if state:
                    query += ' WHERE state = ?'
                    params.append(state)
                
                query += ' ORDER BY last_opened DESC'
                
                if limit:
                    query += ' LIMIT ?'
                    params.append(limit)
                
                cursor.execute(query, params)
                
                projects = []
                for row in cursor.fetchall():
                    settings = {}
                    if row['settings_json']:
                        try:
                            settings = json.loads(row['settings_json'])
                        except json.JSONDecodeError as e:
                            logger.warning(f"Failed to parse settings JSON for project {row['id']}: {e}")
                            settings = {}
                    
                    projects.append(Project(
                        id=row['id'],
                        name=row['name'],
                        description=row['description'],
                        created_at=row['created_at'],
                        last_opened=row['last_opened'],
                        state=row['state'],
                        settings=settings
                    ))
                
                logger.info(f"Listed {len(projects)} projects")
                return projects
        except Exception as e:
            logger.error(f"Unexpected error listing projects (state={state}, limit={limit}): {e}", exc_info=True)
            return []
    
    def get_project_by_name(self, name: str) -> Optional[Project]:
        """
        Get a project by name (convenience method).
        
        Args:
            name: Project name
        
        Returns:
            Project instance or None if not found
        """
        return self.load_project(name=name)
    
    def save_project_state(self, state: ProjectState) -> bool:
        """
        Save UI state for a project (for resume capability).
        
        Args:
            state: ProjectState instance
        
        Returns:
            True if successful
        """
        try:
            ui_state_json = json.dumps(state.ui_state)
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO project_state 
                    (project_id, current_view, ui_state_json, last_scan_session_id, 
                     last_analysis_id, last_action_plan_id, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    state.project_id,
                    state.current_view,
                    ui_state_json,
                    state.last_scan_session_id,
                    state.last_analysis_id,
                    state.last_action_plan_id,
                    datetime.now().isoformat()
                ))
                
                logger.info(f"Saved state for project ID: {state.project_id}")
                return True
        except (TypeError, ValueError) as e:
            logger.error(f"Failed to serialize UI state for project {state.project_id}: {e}", exc_info=True)
            raise ValueError(f"Invalid UI state: {e}")
        except Exception as e:
            logger.error(f"Unexpected error saving project state for {state.project_id}: {e}", exc_info=True)
            raise RuntimeError(f"Failed to save project state: {e}")
    
    def load_project_state(self, project_id: int) -> Optional[ProjectState]:
        """
        Load UI state for a project.
        
        Args:
            project_id: Project ID
        
        Returns:
            ProjectState instance or None if not found
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM project_state WHERE project_id = ?', (project_id,))
                
                row = cursor.fetchone()
                if not row:
                    logger.debug(f"No state found for project ID: {project_id}")
                    return None
                
                ui_state = {}
                if row['ui_state_json']:
                    try:
                        ui_state = json.loads(row['ui_state_json'])
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse UI state JSON for project {project_id}: {e}")
                        ui_state = {}
                
                return ProjectState(
                    project_id=row['project_id'],
                    current_view=row['current_view'],
                    ui_state=ui_state,
                    last_scan_session_id=row['last_scan_session_id'],
                    last_analysis_id=row['last_analysis_id'],
                    last_action_plan_id=row['last_action_plan_id'],
                    updated_at=row['updated_at']
                )
        except Exception as e:
            logger.error(f"Unexpected error loading project state for {project_id}: {e}", exc_info=True)
            return None

    def get_scan_summary(self, session_id: int) -> dict:
        """Get scan statistics summary by session ID."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'SELECT total_files, total_size_bytes FROM project_scan_sessions WHERE id = ?',
                    (session_id,)
                )
                row = cursor.fetchone()
                if row:
                    return {
                        'files': row[0],
                        'size_gb': row[1] / (1024**3) if row[1] else 0.0
                    }
                return {'files': 0, 'size_gb': 0.0}
        except Exception as e:
            logger.error(f"Failed to get scan summary for {session_id}: {e}")
            return {'files': 0, 'size_gb': 0.0}

    def get_analysis_summary(self, analysis_id: int) -> dict:
        """Get analysis summary by ID."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'SELECT issues_found, confidence FROM project_analyses WHERE id = ?',
                    (analysis_id,)
                )
                row = cursor.fetchone()
                if row:
                    return {
                        'issues': row[0] or 0,
                        'confidence': row[1] or 'UNKNOWN'
                    }
                return {'issues': 0, 'confidence': 'UNKNOWN'}
        except Exception as e:
            logger.error(f"Failed to get analysis summary for {analysis_id}: {e}")
            return {'issues': 0, 'confidence': 'UNKNOWN'}
    
    def get_recent_projects(self, limit: int = 5) -> List[Project]:
        """
        Get recently opened projects.
        
        Args:
            limit: Maximum number of projects to return
        
        Returns:
            List of Project instances
        """
        return self.list_projects(state='active', limit=limit)
    
    def archive_project(self, project_id: int) -> bool:
        """
        Archive a project (soft delete).
        
        Args:
            project_id: Project ID
        
        Returns:
            True if successful
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'UPDATE projects SET state = ? WHERE id = ?',
                    ('archived', project_id)
                )
                
                if cursor.rowcount > 0:
                    logger.info(f"Archived project ID: {project_id}")
                    return True
                logger.warning(f"Project ID {project_id} not found for archiving")
                return False
        except Exception as e:
            logger.error(f"Unexpected error archiving project ID {project_id}: {e}", exc_info=True)
            raise RuntimeError(f"Failed to archive project: {e}")
    
    def unarchive_project(self, project_id: int) -> bool:
        """
        Unarchive a project.
        
        Args:
            project_id: Project ID
        
        Returns:
            True if successful
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'UPDATE projects SET state = ? WHERE id = ?',
                    ('active', project_id)
                )
                
                if cursor.rowcount > 0:
                    logger.info(f"Unarchived project ID: {project_id}")
                    return True
                logger.warning(f"Project ID {project_id} not found for unarchiving")
                return False
        except Exception as e:
            logger.error(f"Unexpected error unarchiving project ID {project_id}: {e}", exc_info=True)
            raise RuntimeError(f"Failed to unarchive project: {e}")


def main():
    """CLI entry point for testing ProjectManager."""
    try:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        print("=" * 70)
        print("JellyRancher Project Manager Test")
        print("=" * 70)
        
        pm = ProjectManager()
        
        # Create a test project
        print("\n1. Creating test project...")
        try:
            project = pm.create_project(
                "Test Project",
                "A test project for Phase 32A",
                settings={'theme': 'dark', 'auto_save': True}
            )
            print(f"   Created: {project.name} (ID: {project.id})")
        except ValueError as e:
            print(f"   Project already exists, loading instead...")
            project = pm.get_project_by_name("Test Project")
            if not project:
                print("   ERROR: Could not create or load test project")
                return
        
        # List all projects
        print("\n2. Listing all projects...")
        projects = pm.list_projects()
        for p in projects:
            print(f"   - {p.name} (ID: {p.id}, State: {p.state}, Last opened: {p.last_opened})")
        
        # Save project state
        print("\n3. Saving project state...")
        state = ProjectState(
            project_id=project.id,
            current_view='scan_view',
            ui_state={'window_width': 1200, 'window_height': 800}
        )
        if pm.save_project_state(state):
            print(f"   Saved state for project: {project.name}")
        else:
            print("   ERROR: Failed to save project state")
        
        # Load project state
        print("\n4. Loading project state...")
        loaded_state = pm.load_project_state(project.id)
        if loaded_state:
            print(f"   Current view: {loaded_state.current_view}")
            print(f"   UI state: {loaded_state.ui_state}")
        else:
            print("   No state found")
        
        # Get recent projects
        print("\n5. Getting recent projects...")
        recent = pm.get_recent_projects(limit=3)
        for p in recent:
            print(f"   - {p.name} (Last opened: {p.last_opened})")
        
        print("\n" + "=" * 70)
        print("[SUCCESS] ProjectManager test completed!")
        print("=" * 70)
    except Exception as e:
        logger.error(f"Unexpected error in ProjectManager test: {e}", exc_info=True)
        print(f"\n[ERROR] Test failed: {e}")
        print("Check logs for details")


if __name__ == "__main__":
    main()

