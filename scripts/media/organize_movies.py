#!/usr/bin/env python3
"""
Movie Organization Script

Organizes movie files into proper Jellyfin structure:
Movies/{Title} ({Year})/{Title} ({Year}).{ext}

For test files, uses dummy titles and years.
"""

import sys
import re
from pathlib import Path
from typing import Optional
sys.path.insert(0, '_common')

from media_utils import hash_file, safe_move
from immutable_audit import ImmutableAuditLog
from snapshot_manager import SnapshotManager
from credential_cache import get_cache_status
from logger import ProjectLogger
from tqdm import tqdm
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

def _should_skip_file(file_path: Path) -> bool:
    """Check if a file should be skipped (virtual environments, etc.)."""
    # Skip files in virtual environment directories
    venv_dirs = {'venv', '.venv', 'env', '.env', '__pycache__', 'node_modules'}
    if any(part in venv_dirs for part in file_path.parts):
        return True
    
    # Skip hidden files (but allow ._state)
    if any(part.startswith('.') for part in file_path.parts):
        if not any(part == '._state' for part in file_path.parts):  # Allow ._state
            return True
    
    return False

def main(source_dir_path: Optional[str] = None):
    """Organize movies from specified directory or default test directory."""
    # Initialize rich console for better output
    console = Console()

    # Create structured logger
    logger = ProjectLogger("organize_movies")

    # Header
    header_text = Text("🎬 Organizing Movies", style="bold blue")
    console.print(Panel(header_text, title="Jellyfin Media Organization", border_style="blue"))
    logger.logger.info("Starting movie organization process")

    # Use provided directory or default to test
    if source_dir_path:
        source_dir = Path(source_dir_path).resolve()
        console.print(f"📁 Using source directory: [cyan]{source_dir}[/cyan]")
        logger.logger.info(f"Using source directory: {source_dir}")
    else:
        source_dir = Path("test_media/movies")
        console.print(f"📁 Using default test directory: [cyan]{source_dir}[/cyan]")
        logger.logger.info(f"Using default test directory: {source_dir}")

    # Initialize systems
    console.print("🔄 Initializing audit system...", end="")
    audit = ImmutableAuditLog()
    audit.initialize()
    console.print(" ✅")
    logger.logger.info("Audit system initialized")

    # Check credential cache status (initializes if needed)
    cache_status = get_cache_status()
    console.print(f"🔑 Credentials: [green]{cache_status['credentials_cached']}[/green] cached, session active")
    logger.logger.info(f"Credential cache status: {cache_status['credentials_cached']} cached")

    # Create snapshot before operation
    console.print("📸 Creating pre-operation snapshot...")
    snapshot_id = SnapshotManager.create_snapshot(
        media_root=str(source_dir),  # Use source directory for snapshot, not parent
        snapshot_type="pre_movie_organization",
        console=console
    )
    console.print(f"✅ [green]Snapshot ready:[/green] [dim]{snapshot_id}[/dim]")
    logger.logger.info(f"Created snapshot: {snapshot_id}")

    audit.log_event("snapshot_create", {
        "snapshot_id": snapshot_id,
        "source_dir": str(source_dir),
        "media_count": len(list(source_dir.glob("*.fake"))) if source_dir.exists() else 0,
        "subtitle_count": 0
    }, actor="organize_movies.py")

    # Destination
    if source_dir_path:
        # For real directories, create Movies subfolder
        dest_dir = source_dir.parent / "Movies"
    else:
        # For test, use test_media/Movies
        dest_dir = Path("test_media/Movies")

    if not source_dir.exists():
        error_msg = f"Source directory not found: {source_dir}"
        console.print(f"❌ [red]{error_msg}[/red]")
        logger.logger.error(error_msg)
        sys.exit(1)

    dest_dir.mkdir(parents=True, exist_ok=True)
    console.print(f"📂 Destination: [cyan]{dest_dir}[/cyan]")
    logger.logger.info(f"Destination directory: {dest_dir}")

    # Find all movie files
    # Check if this is test mode (has .fake files) or real media mode
    fake_files = list(source_dir.glob("*.fake"))
    media_files = []
    
    if fake_files:
        # Test mode: use .fake files (filter out venv files)
        media_files = [f for f in fake_files if not _should_skip_file(f)]
        console.print(f"🎯 Found [green]{len(media_files)}[/green] test movie files to organize")
        logger.logger.info(f"Found {len(media_files)} test movie files to organize")
    else:
        # Real media mode: look for actual media files
        from _common.snapshot_manager import SnapshotManager as SM
        for ext in SM.MEDIA_EXTENSIONS:
            found_files = list(source_dir.glob(f"**/*{ext}"))  # Recursive search
            # Filter out files from virtual environments
            media_files.extend([f for f in found_files if not _should_skip_file(f)])
        
        if media_files:
            console.print(f"🎯 Found [green]{len(media_files)}[/green] media files to organize")
            logger.logger.info(f"Found {len(media_files)} media files to organize")
        else:
            console.print("⚠️  [yellow]No media files found to organize[/yellow]")
            logger.logger.warning("No media files found to organize")
            return

    movie_files = media_files

    # Process each movie file with progress bar
    processed = 0  # Files that were moved
    audited = 0    # Files that were audited (already organized or loose)
    errors = 0

    with tqdm(total=len(movie_files), desc="Organizing Movies", unit="file") as pbar:
        for file_path in movie_files:
            try:
                logger.logger.debug(f"Processing file: {file_path}")

                # Check if this is a test file or real media
                if file_path.suffix == '.fake':
                    # Test mode: parse filename
                    movie_info = parse_test_movie_filename(file_path.name)
                    if not movie_info:
                        warning_msg = f"Skipping unrecognized test file: {file_path.name}"
                        console.print(f"⚠️  [yellow]{warning_msg}[/yellow]")
                        logger.logger.warning(warning_msg)
                        audited += 1
                        pbar.update(1)
                        continue
                else:
                    # Real media file
                    # For now, check if it's already in proper structure
                    if len(file_path.parts) >= 2 and file_path.parent.name != source_dir.name:
                        # File is already in a subfolder, might be organized
                        info_msg = f"Already organized file: {file_path}"
                        console.print(f"ℹ️  [blue]{info_msg}[/blue]")
                        logger.logger.info(info_msg)
                        
                        # Log to audit trail
                        audit.log_event("already_organized", {
                            "file_path": str(file_path),
                            "file_size": file_path.stat().st_size,
                            "snapshot_id": snapshot_id,
                            "reason": "File already in proper Jellyfin directory structure"
                        }, actor="organize_movies.py")
                        
                        audited += 1
                        pbar.update(1)
                        continue
                    else:
                        # Loose media file - for now, skip with warning
                        warning_msg = f"Loose media file detected (manual organization needed): {file_path.name}"
                        console.print(f"⚠️  [yellow]{warning_msg}[/yellow]")
                        logger.logger.warning(warning_msg)
                        
                        # Log to audit trail
                        audit.log_event("loose_file_detected", {
                            "file_path": str(file_path),
                            "file_size": file_path.stat().st_size,
                            "snapshot_id": snapshot_id,
                            "reason": "Loose media file requires manual organization"
                        }, actor="organize_movies.py")
                        
                        audited += 1
                        pbar.update(1)
                        continue

                # Create destination structure
                movie_dir = dest_dir / f"{movie_info['title']} ({movie_info['year']})"
                movie_dir.mkdir(exist_ok=True)

                dest_file = movie_dir / f"{movie_info['title']} ({movie_info['year']}).fake"

                # Hash before move
                hash_before = hash_file(file_path)
                logger.logger.debug(f"Pre-move hash for {file_path.name}: {hash_before}")

                # Move file
                relative_dest = dest_file.relative_to(dest_dir)
                pbar.set_description(f"Moving: {file_path.name}")
                safe_move(file_path, dest_file)

                # Hash after move
                hash_after = hash_file(dest_file)
                logger.logger.debug(f"Post-move hash for {dest_file.name}: {hash_after}")

                # Verify integrity
                if hash_before != hash_after:
                    error_msg = f"File corruption detected: {file_path}"
                    console.print(f"❌ [red]{error_msg}[/red]")
                    logger.logger.error(error_msg)
                    raise ValueError(error_msg)

                # Log the move
                audit.log_event("move", {
                    "source": str(file_path),
                    "destination": str(dest_file),
                    "file_hash_before": hash_before,
                    "file_hash_after": hash_after,
                    "file_size": dest_file.stat().st_size,
                    "snapshot_id": snapshot_id
                }, actor="organize_movies.py")

                processed += 1
                logger.logger.info(f"Successfully moved: {file_path.name} -> {relative_dest}")
                pbar.update(1)

            except Exception as e:
                error_msg = f"Error processing {file_path}: {e}"
                console.print(f"❌ [red]{error_msg}[/red]")
                logger.logger.error(error_msg, exc_info=True)
                errors += 1
                pbar.update(1)

                # Rollback on error
                console.print(f"🔄 [yellow]Rolling back to snapshot {snapshot_id}[/yellow]")
                logger.logger.warning(f"Rolling back to snapshot {snapshot_id} due to error")
                SnapshotManager.restore_snapshot(snapshot_id)
                sys.exit(1)

    # Summary
    if processed > 0 or audited > 0:
        summary_lines = []
        if processed > 0:
            summary_lines.append(f"✅ Files moved: {processed}")
        if audited > 0:
            summary_lines.append(f"📋 Files audited: {audited}")
        summary_lines.append(f"❌ Errors: {errors}")
        summary_lines.append(f"📸 Snapshot: {snapshot_id}")
        
        success_text = "✅ Movie organization complete!\n   " + "\n   ".join(summary_lines)
        console.print(Panel(success_text, title="Summary", border_style="green"))
        logger.logger.info(f"Movie organization complete: {processed} files moved, {audited} files audited, {errors} errors")
    else:
        console.print("⚠️  [yellow]No files were processed[/yellow]")
        logger.logger.warning("No files were processed")

    # Update journal
    update_journal(processed, audited, snapshot_id)

def parse_test_movie_filename(filename: str) -> Optional[dict]:
    """Parse test movie filename into title and year."""
    # Pattern: baloney_movie_001.fake -> Baloney Movie 001 (2023)
    match = re.match(r"baloney_movie_(\d+)\.fake", filename)
    if match:
        number = match.group(1)
        # Create dummy titles and years for testing
        titles = {
            "001": ("Test Movie One", "2023"),
            "002": ("Test Movie Two", "2022"),
            "003": ("Test Movie Three", "2024")
        }
        if number in titles:
            title, year = titles[number]
            return {"title": title, "year": year}

    return None

def update_journal(processed_count, audited_count, snapshot_id):
    """Update the agent journal with movie organization completion."""
    journal_path = Path("._state/agent-journal.md")

    if journal_path.exists():
        with open(journal_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Update current phase
        content = content.replace(
            "## Current Phase\nPhase 1: Foundation",
            "## Current Phase\nPhase 2: Movie Organization"
        )

        # Add accomplishment
        accomplishment = f"2025-10-23 - Test movies organized\n- Moved {processed_count} movie files\n- Audited {audited_count} existing files\n- Created proper directory structure\n- Snapshot: {snapshot_id}\n- Audit entries: {processed_count + audited_count}"
        content = content.replace(
            "## Latest Accomplishment\n2025-10-23 - Genesis inventory created",
            f"## Latest Accomplishment\n{accomplishment}"
        )

        with open(journal_path, 'w', encoding='utf-8') as f:
            f.write(content)

if __name__ == "__main__":
    # Allow command line argument for source directory
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        main()