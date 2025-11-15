#!/usr/bin/env python3
"""
Jellyfin Media Organization Agent - Main Orchestrator

Centralized multi-folder management system with JellyDive sessions.
Provides TUI interface for managing media folders across multiple volumes.

Features:
- Register and manage media folders
- Initiate JellyDive sessions for organization
- View audit logs and system status
- GUI/TUI interface using Rich

Usage:
    python main.py
"""

import sys
import json
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Any

# Rich imports for TUI
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.text import Text
from rich.layout import Layout
from rich.live import Live
from rich.spinner import Spinner

# Add _common to path
sys.path.insert(0, str(Path(__file__).parent / "_common"))

# Import foundation modules
from immutable_audit import ImmutableAuditLog
from credential_manager import CredentialManager
from snapshot_manager import SnapshotManager
from media_utils import hash_file, safe_move, normalize_windows_path
from logger import ProjectLogger

# Constants
MANAGED_FOLDERS_FILE = Path(__file__).parent / "managed_folders.json"
VERSION = "1.0.0"

class JellyfinOrganizer:
    """
    Main orchestrator for Jellyfin Media Organization Agent.

    Manages registered media folders and coordinates JellyDive sessions.
    """

    def __init__(self):
        self.console = Console()
        self.audit = None
        self.creds = None
        self.logger = ProjectLogger("main")

        # Initialize foundation systems
        self._initialize_systems()

        # Load managed folders
        self.managed_folders = self._load_managed_folders()

    def _initialize_systems(self):
        """Initialize audit, credentials, and other foundation systems."""
        try:
            self.console.print("[bold blue]Initializing Jellyfin Organizer...[/bold blue]")

            # Initialize audit system
            self.audit = ImmutableAuditLog()
            self.audit.initialize()
            self.console.print("✅ Audit system initialized")

            # Initialize credentials
            self.creds = CredentialManager()
            self.console.print("✅ Credential system initialized")

            self.console.print("[green]System initialization complete![/green]\n")

        except Exception as e:
            self.console.print(f"[red]❌ System initialization failed: {e}[/red]")
            sys.exit(1)

    def _load_managed_folders(self) -> Dict[str, Any]:
        """Load managed folders configuration."""
        if not MANAGED_FOLDERS_FILE.exists():
            # Create default structure
            default_data = {
                "version": VERSION,
                "last_updated": datetime.now().isoformat(),
                "folders": [],
                "metadata": {
                    "total_folders": 0,
                    "total_files": 0,
                    "total_size_bytes": 0,
                    "last_jellydive_session": None
                }
            }
            with open(MANAGED_FOLDERS_FILE, 'w') as f:
                json.dump(default_data, f, indent=2)
            return default_data

        with open(MANAGED_FOLDERS_FILE, 'r') as f:
            return json.load(f)

    def _save_managed_folders(self):
        """Save managed folders configuration."""
        self.managed_folders["last_updated"] = datetime.now().isoformat()
        with open(MANAGED_FOLDERS_FILE, 'w') as f:
            json.dump(self.managed_folders, f, indent=2)

    def show_main_menu(self):
        """Display the main menu interface."""
        while True:
            self.console.clear()

            # Header
            header = Panel.fit(
                f"[bold cyan]Jellyfin Media Organization Agent v{VERSION}[/bold cyan]\n"
                f"Managing {len(self.managed_folders['folders'])} folders across multiple volumes",
                title="🎬 JellyDive Central"
            )
            self.console.print(header)

            # Menu options
            menu_table = Table(title="Main Menu")
            menu_table.add_column("Option", style="cyan", no_wrap=True)
            menu_table.add_column("Description", style="white")

            menu_table.add_row("1", "View Registered Folders")
            menu_table.add_row("2", "Register New Folder")
            menu_table.add_row("3", "Start JellyDive Session")
            menu_table.add_row("4", "View System Status")
            menu_table.add_row("5", "View Audit Logs")
            menu_table.add_row("0", "Exit")

            self.console.print(menu_table)

            choice = Prompt.ask("\nSelect option", choices=["0", "1", "2", "3", "4", "5"])

            if choice == "0":
                self.console.print("[yellow]Goodbye! 🎬[/yellow]")
                break
            elif choice == "1":
                self.view_registered_folders()
            elif choice == "2":
                self.register_new_folder()
            elif choice == "3":
                self.start_jellydive_session()
            elif choice == "4":
                self.view_system_status()
            elif choice == "5":
                self.view_audit_logs()

            # Pause before showing menu again
            if choice != "0":
                self.console.print("\n[dim]Press Enter to continue...[/dim]")
                input()

    def view_registered_folders(self):
        """Display all registered media folders."""
        self.console.print("[bold]📁 Registered Media Folders[/bold]\n")

        if not self.managed_folders["folders"]:
            self.console.print("[yellow]No folders registered yet. Use option 2 to register your first folder.[/yellow]")
            return

        table = Table(title="Managed Folders")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Path", style="white", max_width=50)
        table.add_column("Volume", style="green")
        table.add_column("Type", style="blue")
        table.add_column("Status", style="yellow")
        table.add_column("Files", style="magenta", justify="right")

        for folder in self.managed_folders["folders"]:
            table.add_row(
                folder["id"][:8] + "...",
                str(Path(folder["path"]).name),
                folder["volume"],
                folder["type"],
                folder["status"],
                str(folder["file_count"])
            )

        self.console.print(table)

    def register_new_folder(self):
        """Register a new media folder."""
        self.console.print("[bold]📝 Register New Media Folder[/bold]\n")

        # Get folder path
        folder_path = Prompt.ask("Enter full path to media folder")
        folder_path = Path(folder_path)

        if not folder_path.exists():
            self.console.print(f"[red]❌ Path does not exist: {folder_path}[/red]")
            return

        if not folder_path.is_dir():
            self.console.print(f"[red]❌ Path is not a directory: {folder_path}[/red]")
            return

        # Get folder type
        folder_type = Prompt.ask(
            "Folder type",
            choices=["movies", "tv_shows", "anime", "mixed"],
            default="mixed"
        )

        # Get description
        description = Prompt.ask("Description (optional)", default="")

        # Create folder entry
        folder_id = f"folder_{len(self.managed_folders['folders']) + 1}"
        folder_entry = {
            "id": folder_id,
            "path": str(folder_path),
            "volume": str(folder_path.drive) if folder_path.drive else "unknown",
            "type": folder_type,
            "status": "registered",
            "last_scan": datetime.now().isoformat(),
            "file_count": 0,  # TODO: scan and count files
            "total_size_bytes": 0,  # TODO: calculate size
            "description": description,
            "tags": []
        }

        # Add to managed folders
        self.managed_folders["folders"].append(folder_entry)
        self.managed_folders["metadata"]["total_folders"] = len(self.managed_folders["folders"])
        self._save_managed_folders()

        # Log to audit
        self.audit.log_event("folder_register", {
            "folder_id": folder_id,
            "path": str(folder_path),
            "type": folder_type
        }, actor="main.py")

        self.console.print(f"[green]✅ Folder registered successfully: {folder_path}[/green]")

    def start_jellydive_session(self):
        """Start a JellyDive session for selected folders."""
        self.console.print("[bold]🚀 Start JellyDive Session[/bold]\n")

        if not self.managed_folders["folders"]:
            self.console.print("[yellow]No folders registered. Register folders first.[/yellow]")
            return

        # Show available folders
        self.view_registered_folders()

        # Let user select folders (simplified - select all for now)
        if Confirm.ask("Start JellyDive with all registered folders?", default=False):
            selected_folders = self.managed_folders["folders"]
        else:
            # TODO: Implement folder selection
            self.console.print("[yellow]Folder selection not implemented yet. Use all folders.[/yellow]")
            selected_folders = self.managed_folders["folders"]

        # Start JellyDive session
        session_id = f"jellydive_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        self.console.print(f"[green]🎬 Starting JellyDive Session: {session_id}[/green]")
        self.console.print(f"Selected {len(selected_folders)} folders for organization")

        # Log session start
        self.audit.log_event("jellydive_start", {
            "session_id": session_id,
            "folder_count": len(selected_folders),
            "folders": [f["id"] for f in selected_folders]
        }, actor="main.py")

        # TODO: Implement actual JellyDive logic
        self.console.print("[yellow]⚠️  JellyDive session logic not implemented yet[/yellow]")
        self.console.print("This would organize media files in the selected folders...")

        # Update metadata
        self.managed_folders["metadata"]["last_jellydive_session"] = session_id
        self._save_managed_folders()

    def view_system_status(self):
        """Display system status and health."""
        self.console.print("[bold]🔍 System Status[/bold]\n")

        # Audit status
        audit_integrity = self.audit.verify_chain_integrity()
        audit_status = "✅ OK" if audit_integrity["integrity_percentage"] == 100.0 else "❌ COMPROMISED"

        # Credentials status
        creds_status = "✅ Configured" if self.creds.list_credentials() else "⏳ Not configured"

        status_table = Table(title="System Health")
        status_table.add_column("Component", style="cyan")
        status_table.add_column("Status", style="green")
        status_table.add_column("Details", style="white")

        status_table.add_row("Audit Chain", audit_status,
                           f"{audit_integrity['total_entries']} entries, {audit_integrity['integrity_percentage']}% integrity")
        status_table.add_row("Credentials", creds_status,
                           f"{len(self.creds.list_credentials())} credentials stored")
        status_table.add_row("Managed Folders", "✅ OK",
                           f"{len(self.managed_folders['folders'])} folders registered")
        status_table.add_row("Virtual Environment", "✅ Active",
                           f"Python {sys.version.split()[0]}")

        self.console.print(status_table)

    def view_audit_logs(self):
        """Display recent audit log entries."""
        self.console.print("[bold]📋 Recent Audit Log Entries[/bold]\n")

        # Get recent entries (last 10)
        try:
            # This is a simplified view - in reality would need to search audit logs
            self.console.print("[yellow]Audit log viewing not fully implemented yet.[/yellow]")
            self.console.print("Recent entries would be displayed here...")
        except Exception as e:
            self.console.print(f"[red]Error reading audit logs: {e}[/red]")


def main():
    """Main entry point."""
    try:
        organizer = JellyfinOrganizer()
        organizer.show_main_menu()
    except KeyboardInterrupt:
        print("\nGoodbye! 🎬")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
