#!/usr/bin/env python3
"""
Extrapolation Engine - Convert folder-level LLM output to file-level actions.

This is the critical missing piece in the workflow: the LLM provides folder-level
reorganization suggestions, and this engine applies those suggestions to ALL 
individual files within those folders.

Example:
    LLM says: "Rename folder /media/STTNG to /media/Star Trek The Next Generation (1987)"
    Engine extrapolates: Apply rename to all 178 files under STTNG

Architecture:
    Folder Structure Summary → LLM → Folder-Level Plan → [EXTRAPOLATE] → File-Level Actions
"""

import logging
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple
from collections import defaultdict
from dataclasses import dataclass

from scripts.core.action_plan import ProposedOperation, ActionType, Confidence
from scripts.core.file_scanner import FileRecord

logger = logging.getLogger(__name__)

# Video and subtitle file extensions
VIDEO_EXTENSIONS = {'.mkv', '.mp4', '.avi', '.mov', '.wmv', '.flv', '.m4v', '.ts', '.mpg', '.mpeg', '.webm'}
SUBTITLE_EXTENSIONS = {'.srt', '.sub', '.idx', '.ass', '.ssa', '.vtt'}


@dataclass
class FolderChange:
    """Represents a single folder-level change from LLM output."""
    current_path: Path
    proposed_path: Optional[Path]
    action: str  # rename, move, delete, skip, review
    reason: str
    confidence: str  # high, medium, low
    subtitle_handling: str  # follow, separate, ignore


class ExtrapolationEngine:
    """
    Converts folder-level LLM reorganization plans to file-level operations.
    
    The LLM analyzes folder structure and proposes changes at the folder level.
    This engine takes those folder-level suggestions and applies them to every
    individual file, generating a complete list of ProposedOperations for review.
    """
    
    def __init__(self, scanned_files: List[FileRecord]):
        """
        Initialize the extrapolation engine.
        
        Args:
            scanned_files: List of FileRecord objects from the scan
        """
        if not scanned_files:
            raise ValueError("scanned_files cannot be empty")
        
        self.scanned_files = scanned_files
        self.operations: List[ProposedOperation] = []
        
        # Build indices for efficient lookups
        self._build_indices()
        
        logger.info(f"ExtrapolationEngine initialized with {len(scanned_files)} files")
    
    def _build_indices(self) -> None:
        """Build helper indices for efficient lookups."""
        # Index files by parent folder
        self.folder_to_files: Dict[Path, List[FileRecord]] = defaultdict(list)
        for record in self.scanned_files:
            self.folder_to_files[record.parent_folder].append(record)
        
        # Build subtitle map (video -> [subtitles])
        self.video_to_subtitles: Dict[Path, List[FileRecord]] = defaultdict(list)
        video_files: Dict[Path, FileRecord] = {}
        subtitle_files: List[FileRecord] = []
        
        for record in self.scanned_files:
            ext = record.extension.lower()
            if ext in VIDEO_EXTENSIONS:
                video_files[record.absolute_path] = record
            elif ext in SUBTITLE_EXTENSIONS:
                subtitle_files.append(record)
        
        # Match subtitles to videos by stem
        for sub_record in subtitle_files:
            sub_path = sub_record.absolute_path
            sub_stem = sub_path.stem
            
            # Handle language codes: "Movie.en.srt" -> "Movie"
            # Strip common markers: .en, .eng, .forced, .sdh, .cc, .hi
            base_stem = sub_stem
            for marker in ['.forced', '.sdh', '.cc', '.hi']:
                if base_stem.lower().endswith(marker):
                    base_stem = base_stem[:-len(marker)]
            
            # Strip language codes (2-3 letter codes at end)
            parts = base_stem.rsplit('.', 1)
            if len(parts) == 2 and len(parts[1]) <= 3:
                base_stem = parts[0]
            
            # Find matching video
            for ext in VIDEO_EXTENSIONS:
                potential_video = sub_path.parent / f"{base_stem}{ext}"
                if potential_video in video_files:
                    self.video_to_subtitles[potential_video].append(sub_record)
                    break
        
        logger.info(f"Built indices: {len(self.folder_to_files)} folders, "
                   f"{len(self.video_to_subtitles)} videos with subtitles")
    
    def extrapolate(
        self,
        reorganization_plan: Dict[str, Any],
        detected_media: Optional[List[Dict]] = None
    ) -> List[ProposedOperation]:
        """
        Convert folder-level LLM plan to file-level operations.
        
        Args:
            reorganization_plan: LLM output with folder_changes list
            detected_media: Optional list of detected movies/TV shows for context
            
        Returns:
            List of ProposedOperation objects for each file
        """
        self.operations = []
        folder_changes = reorganization_plan.get('folder_changes', [])
        
        if not folder_changes:
            logger.warning("No folder_changes in reorganization plan")
            return self._handle_no_changes()
        
        logger.info(f"Extrapolating {len(folder_changes)} folder changes to file operations")
        
        # Track which files have been processed
        processed_files: Set[Path] = set()
        
        # Process each folder change
        for change in folder_changes:
            change_obj = self._parse_folder_change(change)
            if change_obj:
                self._apply_folder_change(change_obj, processed_files, detected_media)
        
        # Handle any files not covered by folder changes
        self._handle_unprocessed_files(processed_files)
        
        # Sort operations by confidence (highest first) then by path
        self.operations.sort(key=lambda op: (
            -self._confidence_sort_key(op.confidence),
            str(op.source_path)
        ))
        
        logger.info(f"Generated {len(self.operations)} file-level operations")
        self._log_operation_summary()
        
        return self.operations
    
    def _parse_folder_change(self, change: Dict) -> Optional[FolderChange]:
        """Parse a folder change dict into a FolderChange object."""
        try:
            current_path = change.get('current_path') or change.get('source_path')
            proposed_path = change.get('proposed_path') or change.get('target_path')
            
            if not current_path:
                logger.warning(f"Folder change missing current_path: {change}")
                return None
            
            return FolderChange(
                current_path=Path(current_path),
                proposed_path=Path(proposed_path) if proposed_path else None,
                action=str(change.get('action', 'review')).lower(),
                reason=str(change.get('reason', '')),
                confidence=str(change.get('confidence', 'medium')).lower(),
                subtitle_handling=str(change.get('subtitle_rename', 'follow')).lower()
            )
        except Exception as e:
            logger.error(f"Failed to parse folder change: {e}")
            return None
    
    def _apply_folder_change(
        self,
        change: FolderChange,
        processed_files: Set[Path],
        detected_media: Optional[List[Dict]]
    ) -> None:
        """Apply a folder-level change to all files in that folder."""
        # Find all files that match this folder (including subfolders)
        matching_files = self._find_files_in_folder(change.current_path)
        
        if not matching_files:
            logger.debug(f"No files found for folder: {change.current_path}")
            return
        
        logger.debug(f"Applying '{change.action}' to {len(matching_files)} files in {change.current_path}")
        
        # Determine confidence level
        confidence = self._map_confidence(change.confidence)
        
        # Process each file
        for record in matching_files:
            if record.absolute_path in processed_files:
                continue
            
            processed_files.add(record.absolute_path)
            
            # Determine action type and destination
            action_type, dest_path = self._compute_file_destination(
                record, change
            )
            
            # Get associated subtitles
            subtitles = self.video_to_subtitles.get(record.absolute_path, [])
            subtitle_paths = [str(s.absolute_path) for s in subtitles]
            
            # Create the operation
            operation = ProposedOperation(
                source_path=record.absolute_path,
                destination_path=dest_path,
                action_type=action_type,
                confidence=confidence,
                notes=f"{change.reason}. Subtitles: {len(subtitles)}",
                jellyfin_status=getattr(record, 'jellyfin_status', 'Unknown'),
                jellyfin_id=getattr(record, 'jellyfin_id', None),
                current_md5=record.md5_hash,
            )
            
            self.operations.append(operation)
            
            # Process associated subtitles
            for sub_record in subtitles:
                if sub_record.absolute_path in processed_files:
                    continue
                processed_files.add(sub_record.absolute_path)
                
                sub_dest = self._compute_subtitle_destination(sub_record, dest_path) if dest_path else None
                
                sub_op = ProposedOperation(
                    source_path=sub_record.absolute_path,
                    destination_path=sub_dest,
                    action_type=action_type,
                    confidence=confidence,
                    notes=f"Subtitle follows: {record.absolute_path.name}",
                    current_md5=sub_record.md5_hash,
                )
                
                self.operations.append(sub_op)
    
    def _find_files_in_folder(self, folder_path: Path) -> List[FileRecord]:
        """Find all files that are in or under the given folder."""
        matching = []
        folder_str = str(folder_path).lower()
        
        for record in self.scanned_files:
            record_folder_str = str(record.parent_folder).lower()
            # Check if file is in this folder or any subfolder
            if record_folder_str == folder_str or record_folder_str.startswith(folder_str + '\\') or record_folder_str.startswith(folder_str + '/'):
                matching.append(record)
        
        return matching
    
    def _compute_file_destination(
        self,
        record: FileRecord,
        change: FolderChange
    ) -> Tuple[ActionType, Optional[Path]]:
        """Compute the destination path for a file based on folder change."""
        action = change.action.lower()
        
        if action in ('delete', 'remove'):
            return ActionType.DELETE, None
        
        if action in ('skip', 'ignore', 'do_nothing'):
            return ActionType.SKIP, None
        
        if action in ('review', 'manual'):
            return ActionType.REVIEW, None
        
        if action in ('move', 'rename', 'reorganize'):
            if not change.proposed_path:
                return ActionType.REVIEW, None
            
            # Compute relative path from old folder
            try:
                rel_path = record.absolute_path.relative_to(change.current_path)
            except ValueError:
                # File is not directly under the folder, use just the filename
                rel_path = Path(record.absolute_path.name)
            
            # Apply to new folder
            dest_path = change.proposed_path / rel_path
            
            return ActionType.MOVE, dest_path
        
        # Unknown action - mark for review
        return ActionType.REVIEW, None
    
    def _compute_subtitle_destination(
        self,
        sub_record: FileRecord,
        video_dest: Optional[Path]
    ) -> Optional[Path]:
        """Compute subtitle destination to follow its video file."""
        if not video_dest:
            return None
        
        # Preserve language code and markers from original subtitle filename
        sub_stem = sub_record.absolute_path.stem
        video_stem = video_dest.stem
        
        # Extract language/marker suffix from subtitle
        # e.g., "Movie.en.forced" -> ".en.forced"
        suffix = ""
        for marker in ['.forced', '.sdh', '.cc', '.hi']:
            if sub_stem.lower().endswith(marker):
                suffix = sub_stem[-len(marker):] + suffix
                sub_stem = sub_stem[:-len(marker)]
        
        # Check for language code
        parts = sub_stem.rsplit('.', 1)
        if len(parts) == 2 and len(parts[1]) <= 3:
            suffix = f".{parts[1]}{suffix}"
        
        # Build new subtitle path
        new_name = f"{video_stem}{suffix}{sub_record.extension}"
        return video_dest.parent / new_name
    
    def _map_confidence(self, confidence_str: str) -> Confidence:
        """Map string confidence to Confidence enum."""
        confidence_str = confidence_str.lower()
        if confidence_str in ('high', 'auto', 'auto-safe'):
            return Confidence.HIGH
        elif confidence_str in ('medium', 'review'):
            return Confidence.MEDIUM
        elif confidence_str in ('low', 'uncertain'):
            return Confidence.LOW
        elif confidence_str in ('manual', 'none'):
            return Confidence.MANUAL
        else:
            return Confidence.MEDIUM
    
    def _confidence_sort_key(self, confidence: Confidence) -> int:
        """Return sort key for confidence (higher = better)."""
        return {
            Confidence.HIGH: 4,
            Confidence.MEDIUM: 3,
            Confidence.LOW: 2,
            Confidence.MANUAL: 1,
            Confidence.NONE: 0,
        }.get(confidence, 2)
    
    def _handle_no_changes(self) -> List[ProposedOperation]:
        """Handle case where LLM provided no folder changes."""
        logger.info("No folder changes - marking all files for review")
        
        for record in self.scanned_files:
            operation = ProposedOperation(
                source_path=record.absolute_path,
                destination_path=None,
                action_type=ActionType.REVIEW,
                confidence=Confidence.LOW,
                notes="No reorganization suggested - needs manual review",
                current_md5=record.md5_hash,
            )
            self.operations.append(operation)
        
        return self.operations
    
    def _handle_unprocessed_files(self, processed_files: Set[Path]) -> None:
        """Handle files not covered by any folder change."""
        for record in self.scanned_files:
            if record.absolute_path in processed_files:
                continue
            
            # File wasn't covered by any folder change
            # Check if it might already be compliant
            is_compliant = self._check_jellyfin_compliance(record)
            
            if is_compliant:
                action_type = ActionType.SKIP
                confidence = Confidence.NONE
                notes = "File appears Jellyfin-compliant - no action needed"
            else:
                action_type = ActionType.REVIEW
                confidence = Confidence.LOW
                notes = "Not covered by reorganization plan - needs review"
            
            operation = ProposedOperation(
                source_path=record.absolute_path,
                destination_path=None,
                action_type=action_type,
                confidence=confidence,
                notes=notes,
                jellyfin_status=getattr(record, 'jellyfin_status', 'Unknown'),
                current_md5=record.md5_hash,
            )
            
            self.operations.append(operation)
    
    def _check_jellyfin_compliance(self, record: FileRecord) -> bool:
        """Check if a file appears to already be Jellyfin-compliant."""
        # Check if already matched in Jellyfin
        if getattr(record, 'jellyfin_matched', False):
            return True
        
        # Check common Jellyfin naming patterns
        path_str = str(record.absolute_path)
        
        # Movie pattern: /Movies/Title (Year)/Title (Year).ext
        movie_pattern = r'/Movies/[^/]+\s*\(\d{4}\)/[^/]+\.\w+$'
        if re.search(movie_pattern, path_str, re.IGNORECASE):
            return True
        
        # TV pattern: /TV Shows/Show/Season XX/Show - SXXEXX - Title.ext
        tv_pattern = r'/TV Shows?/[^/]+/Season\s*\d+/[^/]+-\s*S\d+E\d+.*\.\w+$'
        if re.search(tv_pattern, path_str, re.IGNORECASE):
            return True
        
        return False
    
    def _log_operation_summary(self) -> None:
        """Log summary of generated operations."""
        action_counts = defaultdict(int)
        confidence_counts = defaultdict(int)
        
        for op in self.operations:
            action_counts[op.action_type.name] += 1
            confidence_counts[op.confidence.name] += 1
        
        logger.info("Operation Summary:")
        for action, count in sorted(action_counts.items()):
            logger.info(f"  {action}: {count}")
        
        logger.info("Confidence Distribution:")
        for conf, count in sorted(confidence_counts.items()):
            logger.info(f"  {conf}: {count}")
    
    def get_operations_by_confidence(self) -> Dict[Confidence, List[ProposedOperation]]:
        """Group operations by confidence level for UI display."""
        grouped = defaultdict(list)
        for op in self.operations:
            grouped[op.confidence].append(op)
        return dict(grouped)
    
    def get_statistics(self) -> Dict[str, int]:
        """Get statistics about the extrapolated operations."""
        stats = {
            'total_files': len(self.operations),
            'move': sum(1 for op in self.operations if op.action_type == ActionType.MOVE),
            'delete': sum(1 for op in self.operations if op.action_type == ActionType.DELETE),
            'skip': sum(1 for op in self.operations if op.action_type == ActionType.SKIP),
            'review': sum(1 for op in self.operations if op.action_type == ActionType.REVIEW),
            'high_confidence': sum(1 for op in self.operations if op.confidence == Confidence.HIGH),
            'medium_confidence': sum(1 for op in self.operations if op.confidence == Confidence.MEDIUM),
            'low_confidence': sum(1 for op in self.operations if op.confidence == Confidence.LOW),
            'videos_with_subtitles': len(self.video_to_subtitles),
        }
        return stats

