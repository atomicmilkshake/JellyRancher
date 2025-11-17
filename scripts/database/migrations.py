#!/usr/bin/env python3
"""
Database Migration Manager for JellyRancher

Handles schema migrations and upgrades for the project management system.
Ensures backward compatibility with existing data.

Usage:
    from scripts.database.migrations import DatabaseMigrator
    
    migrator = DatabaseMigrator("data/media_library.db")
    migrator.migrate_to_latest()
"""

import sqlite3
import logging
from pathlib import Path
from typing import Optional
from contextlib import contextmanager
from datetime import datetime

logger = logging.getLogger(__name__)


class DatabaseMigrator:
    """
    Manages database schema migrations for JellyRancher.
    
    Responsibilities:
    - Apply schema migrations incrementally
    - Track migration history
    - Ensure data integrity during migrations
    - Support rollback if needed
    """
    
    # Current schema version
    CURRENT_VERSION = 2  # Version 2 adds project management tables
    
    def __init__(self, db_path: str = "data/media_library.db"):
        """
        Initialize database migrator.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"DatabaseMigrator initialized: {self.db_path}")
    
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
            logger.error(f"Migration error: {e}", exc_info=True)
            raise
        finally:
            conn.close()
    
    def _initialize_migration_table(self, conn: sqlite3.Connection):
        """Create migration tracking table if it doesn't exist."""
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                description TEXT
            )
        ''')
        conn.commit()
    
    def get_current_version(self) -> int:
        """Get the current schema version from the database."""
        with self._get_connection() as conn:
            self._initialize_migration_table(conn)
            cursor = conn.cursor()
            cursor.execute('SELECT MAX(version) as version FROM schema_migrations')
            row = cursor.fetchone()
            return row['version'] if row['version'] is not None else 0
    
    def _record_migration(self, conn: sqlite3.Connection, version: int, description: str):
        """Record a successful migration in the tracking table."""
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO schema_migrations (version, description)
            VALUES (?, ?)
        ''', (version, description))
        logger.info(f"Migration v{version} applied: {description}")
    
    def _migration_v1_base_schema(self, conn: sqlite3.Connection):
        """
        Migration v1: Base schema (existing tables)
        
        This migration ensures existing tables are recognized.
        It doesn't create them, just records that they exist.
        """
        cursor = conn.cursor()
        
        # Check if scanned_files table exists (from inventory_repository.py)
        cursor.execute('''
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='scanned_files'
        ''')
        
        if cursor.fetchone():
            logger.info("Existing scanned_files table detected")
            self._record_migration(conn, 1, "Base schema with scanned_files table")
        else:
            # If no existing tables, this is a fresh install
            logger.info("No existing tables detected - fresh installation")
            self._record_migration(conn, 1, "Fresh installation - base schema")
    
    def _migration_v2_project_management(self, conn: sqlite3.Connection):
        """
        Migration v2: Add project management tables
        
        Adds:
        - projects
        - project_scan_sessions
        - project_analyses
        - project_action_plans
        - project_operations
        - project_state
        
        Also links existing scanned_files to a default project if they exist.
        """
        cursor = conn.cursor()
        
        logger.info("Applying migration v2: Project management tables")
        
        # Read and execute schema.sql
        schema_path = Path(__file__).parent / "schema.sql"
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        # Execute schema (CREATE TABLE IF NOT EXISTS statements)
        cursor.executescript(schema_sql)
        
        # Check if scanned_files table exists and needs project_id column
        cursor.execute('''
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='scanned_files'
        ''')
        
        if cursor.fetchone():
            # Check if project_id column already exists
            cursor.execute('PRAGMA table_info(scanned_files)')
            columns = [row[1] for row in cursor.fetchall()]
            
            if 'project_id' not in columns:
                logger.info("Adding project_id column to scanned_files table")
                cursor.execute('''
                    ALTER TABLE scanned_files 
                    ADD COLUMN project_id INTEGER REFERENCES projects(id)
                ''')
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_scanned_files_project 
                    ON scanned_files(project_id)
                ''')
                
                # Create a default project for existing scans
                cursor.execute('''
                    INSERT INTO projects (name, description, created_at, last_opened, state)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    "Legacy Scans",
                    "Auto-created project for existing scan data",
                    datetime.now().isoformat(),
                    datetime.now().isoformat(),
                    "active"
                ))
                default_project_id = cursor.lastrowid
                
                # Link existing scanned files to default project
                cursor.execute('''
                    UPDATE scanned_files 
                    SET project_id = ? 
                    WHERE project_id IS NULL
                ''', (default_project_id,))
                
                rows_updated = cursor.rowcount
                logger.info(f"Linked {rows_updated} existing files to 'Legacy Scans' project")
        
        self._record_migration(conn, 2, "Project management system with 6 new tables")
    
    def migrate_to_latest(self) -> bool:
        """
        Apply all pending migrations to bring database to latest version.
        
        Returns:
            True if migrations were successful, False otherwise
        """
        try:
            current_version = self.get_current_version()
            logger.info(f"Current schema version: {current_version}")
            logger.info(f"Target schema version: {self.CURRENT_VERSION}")
            
            if current_version >= self.CURRENT_VERSION:
                logger.info("Database is already at latest version")
                return True
            
            with self._get_connection() as conn:
                # Apply migrations in order
                if current_version < 1:
                    self._migration_v1_base_schema(conn)
                
                if current_version < 2:
                    self._migration_v2_project_management(conn)
                
                logger.info(f"Successfully migrated from v{current_version} to v{self.CURRENT_VERSION}")
                return True
                
        except Exception as e:
            logger.error(f"Migration failed: {e}", exc_info=True)
            return False
    
    def get_migration_status(self) -> dict:
        """
        Get detailed migration status information.
        
        Returns:
            Dictionary with current version, target version, and migration history
        """
        current_version = self.get_current_version()
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT version, applied_at, description 
                FROM schema_migrations 
                ORDER BY version
            ''')
            history = [
                {
                    'version': row['version'],
                    'applied_at': row['applied_at'],
                    'description': row['description']
                }
                for row in cursor.fetchall()
            ]
        
        return {
            'current_version': current_version,
            'target_version': self.CURRENT_VERSION,
            'up_to_date': current_version >= self.CURRENT_VERSION,
            'migration_history': history
        }


def main():
    """CLI entry point for running migrations."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 70)
    print("JellyRancher Database Migration Tool")
    print("=" * 70)
    
    migrator = DatabaseMigrator()
    
    # Show current status
    status = migrator.get_migration_status()
    print(f"\nCurrent Version: {status['current_version']}")
    print(f"Target Version:  {status['target_version']}")
    print(f"Status:          {'[OK] Up to date' if status['up_to_date'] else '[PENDING] Migrations pending'}")
    
    if status['migration_history']:
        print("\nMigration History:")
        for migration in status['migration_history']:
            print(f"  v{migration['version']}: {migration['description']}")
            print(f"           Applied at {migration['applied_at']}")
    
    # Run migrations if needed
    if not status['up_to_date']:
        print(f"\nApplying migrations from v{status['current_version']} to v{status['target_version']}...")
        success = migrator.migrate_to_latest()
        
        if success:
            print("\n[SUCCESS] Migration completed successfully!")
        else:
            print("\n[ERROR] Migration failed. Check logs for details.")
            return 1
    else:
        print("\n[OK] Database is already at latest version. No migrations needed.")
    
    print("=" * 70)
    return 0


if __name__ == "__main__":
    exit(main())

