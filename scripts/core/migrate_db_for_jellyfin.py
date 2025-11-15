#!/usr/bin/env python3
"""
Database Migration: Add Jellyfin Support

Adds Jellyfin-related columns to files table in inventory.db.

Migration adds:
- jellyfin_id: Jellyfin item ID for cross-reference
- jellyfin_library_id: Jellyfin library ID
- jellyfin_item_type: Item type (Movie, Episode, Series, etc.)
- jellyfin_matched: Boolean flag for whether file matched in Jellyfin
- jellyfin_provider_ids: JSON string of provider IDs (TMDb, TVDb, IMDb)

Safe to run multiple times - checks if columns already exist.
"""

import sqlite3
import logging
from pathlib import Path


def migrate_database(db_path: str = "data/inventory.db", logger: logging.Logger = None):
    """
    Add Jellyfin columns to files table.

    Args:
        db_path: Path to inventory database
        logger: Logger instance
    """
    if logger is None:
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)

    db_path = Path(db_path)

    if not db_path.exists():
        logger.error(f"Database not found: {db_path}")
        logger.info("Run JellyRancher scan first to create database")
        return False

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if migrations already applied
        cursor.execute("PRAGMA table_info(files)")
        columns = [col[1] for col in cursor.fetchall()]

        migrations = []

        # Define migrations
        if 'jellyfin_id' not in columns:
            migrations.append(
                ("ALTER TABLE files ADD COLUMN jellyfin_id TEXT", "jellyfin_id")
            )

        if 'jellyfin_library_id' not in columns:
            migrations.append(
                ("ALTER TABLE files ADD COLUMN jellyfin_library_id TEXT", "jellyfin_library_id")
            )

        if 'jellyfin_item_type' not in columns:
            migrations.append(
                ("ALTER TABLE files ADD COLUMN jellyfin_item_type TEXT", "jellyfin_item_type")
            )

        if 'jellyfin_matched' not in columns:
            migrations.append(
                ("ALTER TABLE files ADD COLUMN jellyfin_matched BOOLEAN DEFAULT 0", "jellyfin_matched")
            )

        if 'jellyfin_provider_ids' not in columns:
            migrations.append(
                ("ALTER TABLE files ADD COLUMN jellyfin_provider_ids TEXT", "jellyfin_provider_ids")
            )

        # Execute migrations
        if migrations:
            logger.info(f"Applying {len(migrations)} migrations to {db_path}")
            for sql, column_name in migrations:
                logger.info(f"  Adding column: {column_name}")
                cursor.execute(sql)

            # Create index on jellyfin_id for faster lookups
            try:
                logger.info("  Creating index: idx_files_jellyfin_id")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_jellyfin_id ON files(jellyfin_id)")
            except sqlite3.OperationalError:
                logger.warning("  Index already exists (skipping)")

            conn.commit()
            logger.info(f"[OK] Database migrated successfully: {len(migrations)} columns added")
            return True
        else:
            logger.info("[OK] Database already migrated (no changes needed)")
            return True

    except sqlite3.OperationalError as e:
        logger.error(f"Migration failed: {e}")
        conn.rollback()
        return False
    except Exception as e:
        logger.error(f"Unexpected error during migration: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def verify_migration(db_path: str = "data/inventory.db", logger: logging.Logger = None):
    """
    Verify that migration completed successfully.

    Args:
        db_path: Path to inventory database
        logger: Logger instance

    Returns:
        True if all Jellyfin columns exist
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    db_path = Path(db_path)

    if not db_path.exists():
        logger.error(f"Database not found: {db_path}")
        return False

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute("PRAGMA table_info(files)")
        columns = [col[1] for col in cursor.fetchall()]

        required_columns = [
            'jellyfin_id',
            'jellyfin_library_id',
            'jellyfin_item_type',
            'jellyfin_matched',
            'jellyfin_provider_ids'
        ]

        missing = [col for col in required_columns if col not in columns]

        if missing:
            logger.error(f"Migration incomplete. Missing columns: {', '.join(missing)}")
            return False
        else:
            logger.info("[OK] Migration verified: all Jellyfin columns present")
            return True

    except Exception as e:
        logger.error(f"Verification failed: {e}")
        return False
    finally:
        conn.close()


def rollback_migration(db_path: str = "data/inventory.db", logger: logging.Logger = None):
    """
    Rollback migration by removing Jellyfin columns.

    Args:
        db_path: Path to inventory database
        logger: Logger instance

    Warning:
        This is destructive and cannot be undone!
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    logger.warning("Rollback not supported in SQLite for ALTER TABLE DROP COLUMN")
    logger.warning("To rollback, restore from backup or recreate database")
    return False


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    logger = logging.getLogger(__name__)

    print("=" * 70)
    print("Jellyfin Database Migration")
    print("=" * 70)
    print()

    # Check if database exists
    db_path = Path("data/inventory.db")
    if not db_path.exists():
        print(f"[FAIL] Database not found: {db_path}")
        print()
        print("Please run JellyRancher and scan folders first to create the database.")
        exit(1)

    # Run migration
    print("Running migration...")
    print()
    success = migrate_database(db_path=str(db_path), logger=logger)

    if success:
        print()
        print("Verifying migration...")
        print()
        verify_success = verify_migration(db_path=str(db_path), logger=logger)

        if verify_success:
            print()
            print("=" * 70)
            print("[OK] Migration completed successfully!")
            print("=" * 70)
            print()
            print("Jellyfin integration columns added:")
            print("  - jellyfin_id")
            print("  - jellyfin_library_id")
            print("  - jellyfin_item_type")
            print("  - jellyfin_matched")
            print("  - jellyfin_provider_ids")
            print()
            print("You can now enable Jellyfin integration in JellyRancher GUI.")
        else:
            print()
            print("[WARN] Migration verification failed. Please check logs.")
            exit(1)
    else:
        print()
        print("[FAIL] Migration failed. Please check logs and try again.")
        exit(1)
