#!/usr/bin/env python3
"""
Episode Title Fixer Backend - Apply episode title corrections

Safely renames episode files based on analysis recommendations.
Supports dry-run mode, snapshots, and audit logging.

Features:
- Dry-run preview mode
- Automatic snapshot creation before changes
- Audit logging for all operations
- Rollback capability via snapshots
- Progress callbacks for GUI integration
- Safe filename validation

Usage:
    from episode_title_fixer import EpisodeTitleFixer
    
    fixer = EpisodeTitleFixer()
    results = fixer.apply_fixes(episodes_to_fix, dry_run=False)
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime

from _common.logger import ProjectLogger
from _common.immutable_audit import ImmutableAuditLog
from _common.snapshot_manager import SnapshotManager


class EpisodeTitleFixer:
    """Applies episode title corrections safely."""
    
    # Invalid filename characters (Windows + Unix)
    INVALID_CHARS = r'[<>:"/\\|?*]'
    
    # Max filename length (conservative for compatibility)
    MAX_FILENAME_LENGTH = 200
    
    def __init__(self):
        self.logger = ProjectLogger("episode_title_fixer")
        self.audit = ImmutableAuditLog()
        self.audit.initialize()
    
    def sanitize_title(self, title: str) -> str:
        """
        Sanitize title for safe filesystem use.
        
        Args:
            title: Episode title to sanitize
        
        Returns:
            Sanitized title safe for filenames
        """
        # Remove invalid characters
        sanitized = re.sub(self.INVALID_CHARS, '', title)
        
        # Replace multiple spaces with single space
        sanitized = re.sub(r'\s+', ' ', sanitized)
        
        # Trim whitespace
        sanitized = sanitized.strip()
        
        # Limit length
        if len(sanitized) > self.MAX_FILENAME_LENGTH:
            sanitized = sanitized[:self.MAX_FILENAME_LENGTH].rstrip()
        
        return sanitized
    
    def construct_new_filename(
        self,
        current_filename: str,
        new_title: str
    ) -> Optional[str]:
        """
        Construct new filename with updated title.
        
        Args:
            current_filename: Current filename
            new_title: New episode title
        
        Returns:
            New filename or None if parsing failed
        """
        # Sanitize the new title
        safe_title = self.sanitize_title(new_title)
        
        # Split extension
        name_parts = current_filename.rsplit('.', 1)
        base_name = name_parts[0]
        extension = name_parts[1] if len(name_parts) > 1 else 'mkv'
        
        # Pattern 1: "S01E01 - Episode Title" (Jellyfin standard)
        pattern1 = r'^(S\d+E\d+(?:-E\d+)?)\s*-\s*(.+)$'
        match1 = re.match(pattern1, base_name, re.IGNORECASE)
        
        if match1:
            episode_part = match1.group(1)
            return f"{episode_part} - {safe_title}.{extension}"
        
        # Pattern 2: "Show Title S01E01 Title" (with show prefix)
        pattern2 = r'^(.+?)\s+(S\d+E\d+(?:-E\d+)?)\s+(.+)$'
        match2 = re.match(pattern2, base_name, re.IGNORECASE)
        
        if match2:
            show_part = match2.group(1)
            episode_part = match2.group(2)
            return f"{show_part} {episode_part} {safe_title}.{extension}"
        
        # Pattern 3: "Show Title - S01E01 - Title" (full format)
        pattern3 = r'^(.+?)\s*-\s*(S\d+E\d+(?:-E\d+)?)\s*-\s*(.+)$'
        match3 = re.match(pattern3, base_name, re.IGNORECASE)
        
        if match3:
            show_part = match3.group(1)
            episode_part = match3.group(2)
            return f"{show_part} - {episode_part} - {safe_title}.{extension}"
        
        self.logger.warning(f"Could not parse filename pattern: {current_filename}")
        return None
    
    def validate_rename_operation(
        self,
        source_path: Path,
        target_path: Path
    ) -> tuple[bool, Optional[str]]:
        """
        Validate that a rename operation is safe.
        
        Args:
            source_path: Source file path
            target_path: Target file path
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check source exists
        if not source_path.exists():
            return False, f"Source file not found: {source_path}"
        
        # Check source is a file
        if not source_path.is_file():
            return False, f"Source is not a file: {source_path}"
        
        # Check target doesn't already exist
        if target_path.exists():
            return False, f"Target already exists: {target_path.name}"
        
        # Check target directory exists
        if not target_path.parent.exists():
            return False, f"Target directory not found: {target_path.parent}"
        
        # Check target directory is writable
        if not target_path.parent.is_dir():
            return False, f"Target parent is not a directory: {target_path.parent}"
        
        # Check filename length
        if len(target_path.name) > 255:  # OS limit
            return False, f"Target filename too long: {len(target_path.name)} chars"
        
        return True, None
    
    def apply_single_fix(
        self,
        episode: Dict[str, Any],
        dry_run: bool = True
    ) -> Dict[str, Any]:
        """
        Apply a single episode title fix.
        
        Args:
            episode: Episode data from analyzer with fix recommendation
            dry_run: If True, simulate without making changes
        
        Returns:
            Dict with operation result
        """
        result = {
            'episode': episode['file_name'],
            'success': False,
            'action': 'dry_run' if dry_run else 'rename',
            'error': None
        }
        
        # Get paths
        source_path = Path(episode['full_path'])
        
        # Determine new title
        new_title = episode.get('canonical_title') or episode.get('cleaned_title')
        if not new_title:
            result['error'] = "No new title available"
            return result
        
        # Construct new filename
        new_filename = self.construct_new_filename(source_path.name, new_title)
        if not new_filename:
            result['error'] = "Failed to construct new filename"
            return result
        
        target_path = source_path.parent / new_filename
        
        result['old_filename'] = source_path.name
        result['new_filename'] = new_filename
        result['old_title'] = episode.get('episode_title', 'Unknown')
        result['new_title'] = new_title
        
        # Validate operation
        is_valid, error = self.validate_rename_operation(source_path, target_path)
        if not is_valid:
            result['error'] = error
            return result
        
        # If dry run, just report what would happen
        if dry_run:
            result['success'] = True
            return result
        
        # Perform the rename
        try:
            source_path.rename(target_path)
            result['success'] = True
            result['new_path'] = str(target_path)
            
            # Log to audit
            self.audit.log_event("episode_title_fixed", {
                "old_path": str(source_path),
                "new_path": str(target_path),
                "old_title": result['old_title'],
                "new_title": result['new_title'],
                "timestamp": datetime.now().isoformat()
            }, actor="episode_title_fixer")
            
            self.logger.info(f"Renamed: {source_path.name} → {new_filename}")
        
        except Exception as e:
            result['error'] = str(e)
            self.logger.error(f"Failed to rename {source_path.name}: {e}")
        
        return result
    
    def apply_fixes(
        self,
        episodes: List[Dict[str, Any]],
        dry_run: bool = True,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> Dict[str, Any]:
        """
        Apply fixes to multiple episodes.
        
        Args:
            episodes: List of episodes to fix (from analyzer results)
            dry_run: If True, simulate without making changes
            progress_callback: Optional callback(current, total, message)
        
        Returns:
            Dict with overall results
        """
        self.logger.info(f"Applying fixes to {len(episodes)} episodes (dry_run={dry_run})")
        
        results = {
            'total': len(episodes),
            'successful': 0,
            'failed': 0,
            'dry_run': dry_run,
            'operations': []
        }
        
        for i, episode in enumerate(episodes, 1):
            if progress_callback:
                progress_callback(i, len(episodes), f"Processing {episode['file_name']}")
            
            # Apply fix
            operation_result = self.apply_single_fix(episode, dry_run)
            results['operations'].append(operation_result)
            
            if operation_result['success']:
                results['successful'] += 1
            else:
                results['failed'] += 1
        
        # Log batch completion
        if not dry_run:
            self.audit.log_event("episode_batch_fix_complete", {
                "total": results['total'],
                "successful": results['successful'],
                "failed": results['failed'],
                "timestamp": datetime.now().isoformat()
            }, actor="episode_title_fixer")
        
        self.logger.info(
            f"Fix operation complete: {results['successful']} successful, "
            f"{results['failed']} failed"
        )
        
        return results
    
    def create_snapshot_backup(
        self,
        show_path: Path,
        snapshot_type: str = "pre_title_fix"
    ) -> Optional[str]:
        """
        Create a snapshot backup before applying fixes.
        
        Args:
            show_path: Path to show folder
            snapshot_type: Type of snapshot
        
        Returns:
            Snapshot ID or None if failed
        """
        try:
            # Use the real snapshot manager
            snapshot_id = SnapshotManager.create_snapshot(
                media_root=str(show_path),
                snapshot_type=snapshot_type,
                include_media=True,
                include_subtitles=True
            )
            
            # Also log to audit
            self.audit.log_event("snapshot_created", {
                "snapshot_id": snapshot_id,
                "show_path": str(show_path),
                "snapshot_type": snapshot_type,
                "timestamp": datetime.now().isoformat()
            }, actor="episode_title_fixer")
            
            self.logger.info(f"Created snapshot: {snapshot_id}")
            return snapshot_id
        
        except Exception as e:
            self.logger.error(f"Failed to create snapshot: {e}")
            return None
    
    def export_fix_plan(
        self,
        operations: List[Dict[str, Any]],
        output_path: Path
    ) -> bool:
        """
        Export fix plan to JSON file.
        
        Args:
            operations: List of operations from apply_fixes result
            output_path: Path to save JSON file
        
        Returns:
            True if successful
        """
        try:
            export_data = {
                'generated': datetime.now().isoformat(),
                'total_operations': len(operations),
                'operations': operations
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Exported fix plan to {output_path}")
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to export fix plan: {e}")
            return False


if __name__ == "__main__":
    """Quick test of fixer."""
    fixer = EpisodeTitleFixer()
    
    # Test sanitization
    test_titles = [
        "Episode: The Beginning",
        "File/Name\\Problem",
        "Title with \"Quotes\"",
        "Multiple    Spaces",
    ]
    
    print("Title Sanitization Tests:")
    for title in test_titles:
        sanitized = fixer.sanitize_title(title)
        print(f"  '{title}' → '{sanitized}'")
    
    # Test filename construction
    test_filename = "S01E01 - Old Title [1080p].mkv"
    new_filename = fixer.construct_new_filename(test_filename, "New Title")
    print(f"\nFilename Construction:")
    print(f"  Old: {test_filename}")
    print(f"  New: {new_filename}")
