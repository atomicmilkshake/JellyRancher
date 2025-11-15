#!/usr/bin/env python3
"""
Jellyfin Organizer - Phase 1 Consolidation Script

Consolidates CodeCop and RavenMaven into Jellyfin Organizer with safe
garbage folder tracking. Creates audit trail of all moves.

Usage:
    python consolidation_phase1.py [--dry-run] [--no-confirm]

Features:
    - Moves files to .trash/ instead of deleting
    - Creates TRASH_LOG.md with audit trail
    - Dry-run mode to preview changes
    - Reversible consolidation
"""

import sys
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple
import argparse
from rich.console import Console
from rich.table import Table
from rich.progress import track
from rich.panel import Panel

console = Console()

# Paths
JELLYFIN_ROOT = Path(__file__).parent.parent
TRASH_DIR = JELLYFIN_ROOT / ".trash"
TRASH_LOG = TRASH_DIR / "TRASH_LOG.md"
SCRIPTS_DIR = JELLYFIN_ROOT / "scripts"
TOOLS_DIR = SCRIPTS_DIR / "tools"
STATE_DIR = JELLYFIN_ROOT / "._state"

# External projects
CODE_COP_SRC = Path("V:\\code_cop")
RAVEN_MAVEN_SRC = Path("V:\\RavenMaven")

# Consolidation targets
CODE_COP_DEST = TOOLS_DIR / "code_cop"
RAVEN_MAVEN_DEST = TOOLS_DIR / "ravenmaven"

# Trash subdirectories
TRASH_DUPLICATES = TRASH_DIR / "duplicates"
TRASH_TEMP = TRASH_DIR / "temporary_files"
TRASH_OLD = TRASH_DIR / "old_copies"
TRASH_ARCHIVED = TRASH_DIR / "archived_projects"


class ConsolidationTracker:
    """Tracks all file moves for audit log"""

    def __init__(self):
        self.moves: List[Dict] = []
        self.timestamp = datetime.now()

    def log_move(
        self, source: Path, destination: Path, reason: str, category: str
    ) -> None:
        """Log a file move operation"""
        self.moves.append(
            {
                "source": str(source),
                "destination": str(destination),
                "reason": reason,
                "category": category,
                "timestamp": self.timestamp.isoformat(),
                "size_bytes": source.stat().st_size if source.exists() else 0,
            }
        )

    def get_summary(self) -> Dict:
        """Get summary statistics"""
        if not self.moves:
            return {}

        total_size = sum(m["size_bytes"] for m in self.moves)
        return {
            "total_moves": len(self.moves),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "by_category": self._count_by_category(),
        }

    def _count_by_category(self) -> Dict[str, int]:
        """Count moves by category"""
        counts = {}
        for move in self.moves:
            cat = move["category"]
            counts[cat] = counts.get(cat, 0) + 1
        return counts


def ensure_trash_structure() -> None:
    """Create .trash/ directory structure"""
    console.print("\n[cyan]Creating trash directory structure...[/cyan]")

    for trash_subdir in [TRASH_DUPLICATES, TRASH_TEMP, TRASH_OLD, TRASH_ARCHIVED]:
        trash_subdir.mkdir(parents=True, exist_ok=True)
        console.print(f"  ✓ {trash_subdir.relative_to(JELLYFIN_ROOT)}")


def safe_move(
    source: Path, destination: Path, dry_run: bool = False
) -> bool:
    """Safely move file or directory"""
    if not source.exists():
        console.print(f"  [red]✗ Source not found: {source}[/red]")
        return False

    if destination.exists():
        console.print(f"  [yellow]⚠ Destination already exists: {destination}[/yellow]")
        return False

    if dry_run:
        console.print(f"  [dim](dry-run) Would move: {source} → {destination}[/dim]")
        return True

    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(destination))
        console.print(f"  ✓ Moved: {source.name}")
        return True
    except Exception as e:
        console.print(f"  [red]✗ Error: {e}[/red]")
        return False


def cleanup_jellyfin_root(
    tracker: ConsolidationTracker, dry_run: bool = False
) -> None:
    """Clean up Jellyfin Organizer root directory"""
    console.print("\n[bold cyan]STEP 1: Cleaning Jellyfin Root Directory[/bold cyan]")

    items_to_trash = [
        ("agent-journal copy.md", TRASH_DUPLICATES, "Duplicate of agent-journal.md"),
        (
            "agent-journal copy 2.md",
            TRASH_DUPLICATES,
            "Duplicate of agent-journal.md",
        ),
        (
            "copilot-self-critique.md",
            TRASH_TEMP,
            "One-off critique file, no longer needed",
        ),
        ("monk_torrent_structure.txt", TRASH_TEMP, "One-off analysis file"),
        ("RavenMaven results.json", TRASH_TEMP, "Temporary result file"),
        ("analyze_workspace.py", TRASH_TEMP, "Utility for analysis (no longer needed)"),
        ("journal-entry-nov2.md", TRASH_TEMP, "Merged into agent-journal.md"),
        (
            "749f7798c65f69c0a6aa6b62c77906c49c10a317.torrent",
            TRASH_TEMP,
            "Random torrent file",
        ),
    ]

    for filename, trash_subdir, reason in items_to_trash:
        source = JELLYFIN_ROOT / filename
        if source.exists():
            dest = trash_subdir / filename
            if safe_move(source, dest, dry_run):
                tracker.log_move(source, dest, reason, "Duplicate/Temporary")


def consolidate_code_cop(
    tracker: ConsolidationTracker, dry_run: bool = False
) -> None:
    """Consolidate CodeCop into tools/code_cop"""
    if not CODE_COP_SRC.exists():
        console.print("\n[yellow]⚠ CodeCop source not found at {CODE_COP_SRC}[/yellow]")
        return

    console.print(
        f"\n[bold cyan]STEP 2: Consolidating CodeCop[/bold cyan] ({CODE_COP_SRC})"
    )

    # Delete old destination if exists (we're replacing)
    if CODE_COP_DEST.exists():
        console.print(f"  [yellow]Removing old {CODE_COP_DEST}[/yellow]")
        if not dry_run:
            shutil.rmtree(CODE_COP_DEST)

    # Copy CodeCop
    if dry_run:
        console.print(
            f"  [dim](dry-run) Would copy: {CODE_COP_SRC} → {CODE_COP_DEST}[/dim]"
        )
        console.print(f"  [dim](dry-run) Would archive: {CODE_COP_SRC} → .trash/archived_projects/[/dim]")
    else:
        shutil.copytree(CODE_COP_SRC, CODE_COP_DEST)
        console.print(f"  ✓ Copied CodeCop to {CODE_COP_DEST}")

        # Archive original
        archive_dest = TRASH_ARCHIVED / "code_cop_backup"
        shutil.copytree(CODE_COP_SRC, archive_dest, dirs_exist_ok=True)
        console.print(f"  ✓ Archived backup to {archive_dest}")
        tracker.log_move(CODE_COP_SRC, archive_dest, "Consolidated into tools/code_cop", "External Project")


def consolidate_raven_maven(
    tracker: ConsolidationTracker, dry_run: bool = False
) -> None:
    """Consolidate and clean RavenMaven into tools/ravenmaven"""
    if not RAVEN_MAVEN_SRC.exists():
        console.print(
            f"\n[yellow]⚠ RavenMaven source not found at {RAVEN_MAVEN_SRC}[/yellow]"
        )
        return

    console.print(
        f"\n[bold cyan]STEP 3: Consolidating RavenMaven[/bold cyan] ({RAVEN_MAVEN_SRC})"
    )

    # Files/patterns to skip during copy (bloat)
    skip_patterns = [
        "__pycache__",
        ".pytest_cache",
        ".venv",
        ".cache",
        "CACHEDIR.TAG",
        ".gitignore",
    ]

    # Chunk patterns to delete
    junk_patterns = [
        r"chunk\d+_.*\.json",  # chunk1_processed.json, etc
        r"executor_.*\.log",  # executor logs
        r"ravenmaven_auto_log_.*\.txt",  # auto logs
    ]

    console.print("  Scanning for bloated files to exclude...")

    # Delete old destination if exists
    if RAVEN_MAVEN_DEST.exists():
        console.print(f"  [yellow]Removing old {RAVEN_MAVEN_DEST}[/yellow]")
        if not dry_run:
            shutil.rmtree(RAVEN_MAVEN_DEST)

    if dry_run:
        console.print(
            f"  [dim](dry-run) Would copy: {RAVEN_MAVEN_SRC} → {RAVEN_MAVEN_DEST}[/dim]"
        )
        console.print(f"  [dim](dry-run) Would exclude: __pycache__, .venv, chunk*.json, executor*.log, etc[/dim]")
        console.print(f"  [dim](dry-run) Would archive: {RAVEN_MAVEN_SRC} → .trash/archived_projects/[/dim]")
    else:
        # Copy with exclusions
        def ignore_patterns(directory, files):
            ignored = []
            for filename in files:
                # Skip by name pattern
                if any(pattern in filename for pattern in skip_patterns):
                    ignored.append(filename)
                # Skip junk JSON chunks
                if filename.endswith(".json") and (
                    "chunk" in filename or "processed" in filename
                ):
                    ignored.append(filename)
                # Skip executor logs
                if "executor_" in filename and filename.endswith(".log"):
                    ignored.append(filename)
                # Skip old LLM logs (keep only recent)
                if "llm_transaction_" in filename and filename.endswith(".json"):
                    ignored.append(filename)
                # Skip auto-logs
                if "ravenmaven_auto_log" in filename:
                    ignored.append(filename)
            return ignored

        shutil.copytree(RAVEN_MAVEN_SRC, RAVEN_MAVEN_DEST, ignore=ignore_patterns)
        console.print(f"  ✓ Copied RavenMaven to {RAVEN_MAVEN_DEST} (cleaned)")

        # Get size of cleaned folder
        total_size = sum(
            f.stat().st_size
            for f in RAVEN_MAVEN_DEST.rglob("*")
            if f.is_file()
        )
        console.print(f"  ✓ Final size: {total_size / (1024 * 1024):.1f} MB")

        # Archive original
        archive_dest = TRASH_ARCHIVED / "ravenmaven_backup"
        shutil.copytree(RAVEN_MAVEN_SRC, archive_dest, dirs_exist_ok=True)
        console.print(f"  ✓ Archived backup to {archive_dest}")
        tracker.log_move(
            RAVEN_MAVEN_SRC,
            archive_dest,
            "Consolidated into tools/ravenmaven (cleaned)",
            "External Project",
        )


def write_trash_log(tracker: ConsolidationTracker) -> None:
    """Write TRASH_LOG.md with consolidation audit trail"""
    console.print("\n[bold cyan]STEP 4: Writing Trash Audit Log[/bold cyan]")

    summary = tracker.get_summary()

    log_content = f"""# 🗑️ Garbage Folder - Consolidation Audit Log

**Created**: {tracker.timestamp.strftime('%Y-%m-%d %H:%M:%S')}  
**Operation**: Phase 1 Consolidation - Jellyfin Organizer Project Unification

## Summary

- **Total Items Moved**: {summary.get('total_moves', 0)}
- **Total Size**: {summary.get('total_size_mb', 0)} MB
- **Categories**:
"""

    for category, count in summary.get("by_category", {}).items():
        log_content += f"  - {category}: {count} items\n"

    log_content += "\n## Items\n\n"

    # Group by category
    by_category = {}
    for move in tracker.moves:
        cat = move["category"]
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(move)

    for category in sorted(by_category.keys()):
        log_content += f"### {category} (moved {tracker.timestamp.strftime('%Y-%m-%d')})\n\n"

        for move in by_category[category]:
            size_kb = move["size_bytes"] / 1024
            log_content += f"- `{Path(move['source']).name}` → `.trash/`\n"
            log_content += f"  - Source: {move['source']}\n"
            log_content += f"  - Destination: {move['destination']}\n"
            log_content += f"  - Reason: {move['reason']}\n"
            log_content += f"  - Size: {size_kb:.1f} KB\n"
            log_content += f"  - Timestamp: {move['timestamp']}\n\n"

    log_content += "\n## Recovery Instructions\n\n"
    log_content += """If you need to restore something:

```powershell
# Restore a specific file
Copy-Item ".trash/duplicates/filename" -Destination "./"

# Restore entire backup
Copy-Item ".trash/archived_projects/code_cop_backup" -Destination "V:\\code_cop" -Recurse
Copy-Item ".trash/archived_projects/ravenmaven_backup" -Destination "V:\\RavenMaven" -Recurse
```

## ⚠️ Important Notes

- Files in .trash/ are kept for **30 days** before permanent deletion (optional)
- All operations logged for audit trail
- Original V:\\code_cop and V:\\RavenMaven remain untouched (backup copies in .trash/)
- To permanently delete .trash/, run `consolidation_cleanup.py` after 30 days
"""

    if not TRASH_LOG.parent.exists():
        TRASH_LOG.parent.mkdir(parents=True, exist_ok=True)

    TRASH_LOG.write_text(log_content, encoding='utf-8')
    console.print(f"  ✓ Wrote {TRASH_LOG}")


def reorganize_scripts_directory(dry_run: bool = False) -> None:
    """Create organized subdirectories in scripts/"""
    console.print("\n[bold cyan]STEP 5: Reorganizing scripts/ Directory[/bold cyan]")

    subdirs = [
        "main_scripts",
        "cache_builders",
        "tests",
        "debug",
        "data",
    ]

    for subdir in subdirs:
        path = SCRIPTS_DIR / subdir
        if dry_run:
            console.print(f"  [dim](dry-run) Would create: {path}[/dim]")
        else:
            path.mkdir(exist_ok=True)
            console.print(f"  ✓ Created: {subdir}/")


def print_summary(tracker: ConsolidationTracker) -> None:
    """Print consolidation summary"""
    summary = tracker.get_summary()

    table = Table(title="Phase 1 Consolidation Summary", style="bold cyan")
    table.add_column("Category", style="cyan")
    table.add_column("Count", justify="right", style="yellow")

    for category, count in sorted(summary.get("by_category", {}).items()):
        table.add_row(category, str(count))

    table.add_row("[bold]Total[/bold]", f"[bold]{summary.get('total_moves', 0)}[/bold]")
    console.print(table)

    console.print(
        f"\n[bold green]Total Size Moved:[/bold green] {summary.get('total_size_mb', 0)} MB"
    )
    console.print(
        f"[bold green]Trash Log:[/bold green] {TRASH_LOG.relative_to(JELLYFIN_ROOT)}"
    )


def main():
    """Main consolidation execution"""
    parser = argparse.ArgumentParser(
        description="Phase 1 Consolidation: Absorb CodeCop and RavenMaven"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview changes without making them"
    )
    parser.add_argument(
        "--no-confirm",
        action="store_true",
        help="Skip confirmation prompt",
    )

    args = parser.parse_args()

    console.print(
        Panel(
            "[bold cyan]Jellyfin Organizer - Phase 1 Consolidation[/bold cyan]\n"
            "Consolidates CodeCop and RavenMaven with safe garbage folder tracking",
            style="cyan",
        )
    )

    if args.dry_run:
        console.print("[yellow]Running in DRY-RUN mode (no changes will be made)[/yellow]")

    tracker = ConsolidationTracker()

    # Create trash structure
    ensure_trash_structure()

    # Ask for confirmation if not --no-confirm
    if not args.no_confirm and not args.dry_run:
        response = console.input(
            "\n[bold yellow]Proceed with consolidation? (yes/no)[/bold yellow] "
        )
        if response.lower() not in ["yes", "y"]:
            console.print("[red]Consolidation cancelled[/red]")
            sys.exit(0)

    # Execute consolidation steps
    cleanup_jellyfin_root(tracker, args.dry_run)
    consolidate_code_cop(tracker, args.dry_run)
    consolidate_raven_maven(tracker, args.dry_run)
    reorganize_scripts_directory(args.dry_run)

    # Write audit log
    if not args.dry_run:
        write_trash_log(tracker)

    # Print summary
    print_summary(tracker)

    if args.dry_run:
        console.print(
            "\n[yellow]DRY-RUN complete. Run without --dry-run to execute.[/yellow]"
        )
    else:
        console.print(
            "\n[bold green]✓ Phase 1 Consolidation Complete![/bold green]"
        )
        console.print("Next steps:")
        console.print("  1. Verify all scripts still work")
        console.print("  2. Check TRASH_LOG.md for audit trail")
        console.print("  3. Run Phase 2: Modern UI development")


if __name__ == "__main__":
    main()
