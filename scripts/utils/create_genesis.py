#!/usr/bin/env python3
"""
Genesis Inventory Creation Script

Creates initial inventory of all media and subtitle files.
This establishes the baseline state for audit trail integrity.

Usage:
    python create_genesis.py [media_root]

    media_root: Path to media directory (default: test_media)
"""

import sys
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
sys.path.insert(0, '_common')

from media_utils import hash_file
from immutable_audit import ImmutableAuditLog

def is_media_file(file_path: Path) -> bool:
    """Check if file is a media file (video)."""
    media_extensions = {'.mkv', '.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.fake'}
    return file_path.suffix.lower() in media_extensions

def is_subtitle_file(file_path: Path) -> bool:
    """Check if file is a subtitle file."""
    subtitle_extensions = {'.srt', '.sub', '.ass', '.ssa', '.vtt'}
    return file_path.suffix.lower() in subtitle_extensions

def main():
    print("📊 Creating Genesis Inventory")
    print("=" * 40)

    # Get media root from command line or default
    media_root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("test_media")

    if not media_root.exists():
        print(f"❌ Media root not found: {media_root}")
        sys.exit(1)

    print(f"📁 Scanning media root: {media_root}")

    # Initialize audit system
    audit = ImmutableAuditLog()
    audit.initialize()

    # Scan all files
    media_files = []
    subtitle_files = []

    print("🔍 Scanning files...")
    for file_path in media_root.rglob("*"):
        if file_path.is_file():
            try:
                # Get file info
                stat = file_path.stat()
                file_hash = hash_file(file_path)

                file_info = {
                    "path": str(file_path.relative_to(media_root.parent)),
                    "hash": file_hash,
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                }

                # Classify as media or subtitle
                if is_media_file(file_path):
                    media_files.append(file_info)
                elif is_subtitle_file(file_path):
                    subtitle_files.append(file_info)

            except Exception as e:
                print(f"⚠️  Warning: Could not process {file_path}: {e}")

    # Create inventory
    inventory = {
        "created_at": datetime.now().isoformat(),
        "media_root": str(media_root),
        "media_files": media_files,
        "subtitle_files": subtitle_files,
        "total_media": len(media_files),
        "total_subtitles": len(subtitle_files),
        "total_size_bytes": sum(f["size"] for f in media_files + subtitle_files)
    }

    # Save inventory
    inventory_path = Path("._state/genesis_inventory.json")
    inventory_path.parent.mkdir(parents=True, exist_ok=True)

    with open(inventory_path, 'w', encoding='utf-8') as f:
        json.dump(inventory, f, indent=2, ensure_ascii=False)

    print(f"💾 Inventory saved: {inventory_path}")

    # Log genesis transaction
    audit.log_event("genesis_inventory", {
        "inventory_file": str(inventory_path),
        "total_media_files": len(media_files),
        "total_subtitle_files": len(subtitle_files),
        "total_size_bytes": inventory["total_size_bytes"],
        "media_root": str(media_root)
    }, actor="create_genesis.py")

    # Summary
    print("\n✅ Genesis inventory created!")
    print(f"   Media files: {len(media_files)}")
    print(f"   Subtitle files: {len(subtitle_files)}")
    print(f"   Total size: {inventory['total_size_bytes']:,} bytes")
    print(f"   Audit entry logged")

    # Update journal
    update_journal(inventory)

def update_journal(inventory):
    """Update the agent journal with genesis inventory completion."""
    journal_path = Path("._state/agent-journal.md")

    if journal_path.exists():
        with open(journal_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Update status
        content = content.replace(
            "Genesis inventory: 🔄 Not yet created",
            f"Genesis inventory: ✅ Created ({inventory['total_media']} media, {inventory['total_subtitles']} subtitles)"
        )

        # Add accomplishment
        accomplishment = f"2025-10-23 - Genesis inventory created\n- Scanned {inventory['total_media']} media files\n- Scanned {inventory['total_subtitles']} subtitle files\n- Total size: {inventory['total_size_bytes']:,} bytes\n- Inventory saved to ._state/genesis_inventory.json"
        content = content.replace(
            "## Latest Accomplishment\n2025-10-23 - Credential store configured",
            f"## Latest Accomplishment\n{accomplishment}"
        )

        with open(journal_path, 'w', encoding='utf-8') as f:
            f.write(content)

if __name__ == "__main__":
    main()