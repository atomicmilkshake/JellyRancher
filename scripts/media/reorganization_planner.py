#!/usr/bin/env python3
"""
Reorganization Planner - Step 5

Takes LLM analysis results and canonical metadata database to produce an editable
reorganization plan with proposed actions for each file.

Actions:
- MOVE: Move and rename file to target location
- DELETE: Mark file for deletion (duplicate, poor quality, etc.)
- SKIP: Do nothing, keep file as-is
- REVIEW: Needs manual review (ambiguous, unrecognized)

Features:
- Detects subtitle files (srt, sub, vtt, ass, ssa) associated with video files
- Ensures subtitles follow video files with proper Jellyfin naming
- Handles multi-part episodes (e.g., Episode 1-2.mkv)
- Validates target paths for conflicts
- Supports bulk action changes
- Exports to editable JSON/CSV format
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
from collections import defaultdict


logger = logging.getLogger(__name__)


# Subtitle extensions recognized by Jellyfin
SUBTITLE_EXTENSIONS = {'.srt', '.sub', '.vtt', '.ass', '.ssa', '.idx'}

# Video extensions
VIDEO_EXTENSIONS = {'.mkv', '.mp4', '.avi', '.m4v', '.mov', '.wmv', '.flv', '.webm', '.mpg', '.mpeg', '.ts'}


@dataclass
class ReorganizationAction:
    """
    Represents a single file operation in the reorganization plan.
    """
    source_path: str
    target_path: Optional[str]
    action: str  # MOVE, DELETE, SKIP, REVIEW
    media_type: str  # movie, tv_show, subtitle, other
    status: str  # pending, completed, failed, skipped
    reason: str  # Why this action was suggested
    related_files: List[str]  # Associated files (e.g., subtitles for video)
    metadata: Dict  # Additional metadata (title, season, episode, etc.)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


class ReorganizationPlanner:
    """
    Creates an editable reorganization plan from LLM analysis and metadata.
    """
    
    def __init__(self, output_dir: str = "data/reorganization_plans"):
        """
        Initialize planner.
        
        Args:
            output_dir: Directory to save reorganization plans
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.actions: List[ReorganizationAction] = []
        self.subtitle_map: Dict[str, List[str]] = {}  # video_path -> [subtitle_paths]
        self.path_conflicts: Dict[str, List[str]] = defaultdict(list)  # target -> [sources]
        
        logger.info(f"Initialized ReorganizationPlanner with output dir: {self.output_dir}")
    
    def create_plan(
        self,
        llm_analysis: Dict,
        canonical_db: Dict,
        scan_results: Optional[Dict] = None
    ) -> List[ReorganizationAction]:
        """
        Create reorganization plan from analysis results.
        
        Args:
            llm_analysis: Results from LLMStructureAnalyzer
            canonical_db: Results from MediaMetadataLookup
            scan_results: Optional scan results from FolderStructureScanner
        
        Returns:
            List of ReorganizationAction objects
        """
        logger.info("Creating reorganization plan...")
        
        self.actions = []
        self.subtitle_map = {}
        self.path_conflicts = defaultdict(list)
        
        # Step 1: Build subtitle map from scan results
        if scan_results:
            self._build_subtitle_map(scan_results)
        
        # Step 2: Process detected media from LLM analysis
        detected_media = llm_analysis.get('detected_media', [])
        logger.info(f"Processing {len(detected_media)} detected media items")
        
        for media_item in detected_media:
            self._process_media_item(media_item, canonical_db)
        
        # Step 3: Process unrecognized files
        unrecognized = llm_analysis.get('unrecognized_files', [])
        logger.info(f"Processing {len(unrecognized)} unrecognized files")
        
        for file_path in unrecognized:
            self._process_unrecognized_file(file_path)
        
        # Step 4: Detect conflicts
        self._detect_conflicts()
        
        logger.info(f"Created plan with {len(self.actions)} actions")
        logger.info(f"  MOVE: {sum(1 for a in self.actions if a.action == 'MOVE')}")
        logger.info(f"  DELETE: {sum(1 for a in self.actions if a.action == 'DELETE')}")
        logger.info(f"  SKIP: {sum(1 for a in self.actions if a.action == 'SKIP')}")
        logger.info(f"  REVIEW: {sum(1 for a in self.actions if a.action == 'REVIEW')}")
        
        return self.actions
    
    def _build_subtitle_map(self, scan_results: Dict):
        """
        Build map of video files to their associated subtitle files.
        
        Jellyfin naming conventions:
        - Movie.srt (default subtitle)
        - Movie.en.srt (English subtitle)
        - Movie.en.forced.srt (forced English subtitle)
        - Movie.en.sdh.srt (SDH subtitle)
        """
        logger.info("Building subtitle map...")
        
        all_files = scan_results.get('all_files', [])
        video_files = {Path(f) for f in scan_results.get('video_files', [])}
        
        for file_path_str in all_files:
            file_path = Path(file_path_str)
            
            # Check if it's a subtitle file
            if file_path.suffix.lower() not in SUBTITLE_EXTENSIONS:
                continue
            
            # Find matching video file (same name, different extension)
            video_stem = file_path.stem
            
            # Handle language codes (e.g., "Movie.en.srt" -> "Movie")
            parts = video_stem.split('.')
            if len(parts) > 1:
                # Try removing language/forced/sdh markers
                for i in range(len(parts), 0, -1):
                    potential_stem = '.'.join(parts[:i])
                    potential_video = file_path.parent / f"{potential_stem}{ext}"
                    
                    for ext in VIDEO_EXTENSIONS:
                        potential_video = file_path.parent / f"{potential_stem}{ext}"
                        if potential_video in video_files:
                            video_key = str(potential_video)
                            if video_key not in self.subtitle_map:
                                self.subtitle_map[video_key] = []
                            self.subtitle_map[video_key].append(file_path_str)
                            logger.debug(f"Mapped subtitle {file_path.name} to {potential_video.name}")
                            break
            else:
                # Direct match (no language code)
                for ext in VIDEO_EXTENSIONS:
                    potential_video = file_path.parent / f"{video_stem}{ext}"
                    if potential_video in video_files:
                        video_key = str(potential_video)
                        if video_key not in self.subtitle_map:
                            self.subtitle_map[video_key] = []
                        self.subtitle_map[video_key].append(file_path_str)
                        logger.debug(f"Mapped subtitle {file_path.name} to {potential_video.name}")
                        break
        
        logger.info(f"Built subtitle map with {len(self.subtitle_map)} video files having subtitles")
    
    def _process_media_item(self, media_item: Dict, canonical_db: Dict):
        """
        Process a single detected media item from LLM analysis.
        
        Creates MOVE actions for video files and their associated subtitles.
        """
        media_type = media_item.get('type', 'unknown')
        file_paths = media_item.get('files', [])
        
        if media_type == 'movie':
            self._process_movie(media_item, canonical_db)
        elif media_type == 'tv_show':
            self._process_tv_show(media_item, canonical_db)
        else:
            # Unknown media type - mark for review
            for file_path in file_paths:
                action = ReorganizationAction(
                    source_path=file_path,
                    target_path=None,
                    action='REVIEW',
                    media_type='unknown',
                    status='pending',
                    reason=f"Unknown media type: {media_type}",
                    related_files=[],
                    metadata=media_item
                )
                self.actions.append(action)
    
    def _process_movie(self, media_item: Dict, canonical_db: Dict):
        """Process movie files."""
        title = media_item.get('title', 'Unknown Movie')
        file_paths = media_item.get('files', [])
        
        # Look up metadata
        movies_db = canonical_db.get('movies', {})
        metadata = movies_db.get(title, {})
        
        if not metadata:
            # No metadata found - mark for review
            for file_path in file_paths:
                action = ReorganizationAction(
                    source_path=file_path,
                    target_path=None,
                    action='REVIEW',
                    media_type='movie',
                    status='pending',
                    reason=f"No metadata found for: {title}",
                    related_files=self.subtitle_map.get(file_path, []),
                    metadata=media_item
                )
                self.actions.append(action)
            return
        
        # Generate target path: Movies/Title (Year)/Title (Year).ext
        year = metadata.get('year', '')
        canonical_title = metadata.get('title', title)
        folder_name = f"{canonical_title} ({year})" if year else canonical_title
        
        for file_path in file_paths:
            source = Path(file_path)
            target_filename = f"{folder_name}{source.suffix}"
            target_path = Path("Movies") / folder_name / target_filename
            
            # Get associated subtitles
            subtitles = self.subtitle_map.get(file_path, [])
            
            action = ReorganizationAction(
                source_path=file_path,
                target_path=str(target_path),
                action='MOVE',
                media_type='movie',
                status='pending',
                reason=f"Organize movie: {canonical_title}",
                related_files=subtitles,
                metadata={
                    'title': canonical_title,
                    'year': year,
                    'tmdb_id': metadata.get('tmdb_id'),
                    'imdb_id': metadata.get('imdb_id')
                }
            )
            self.actions.append(action)
            
            # Track target path for conflict detection
            self.path_conflicts[str(target_path)].append(file_path)
            
            # Create actions for subtitle files
            for subtitle_path in subtitles:
                sub_action = self._create_subtitle_action(
                    subtitle_path, 
                    target_path.parent, 
                    target_path.stem
                )
                self.actions.append(sub_action)
    
    def _process_tv_show(self, media_item: Dict, canonical_db: Dict):
        """Process TV show files."""
        title = media_item.get('title', 'Unknown Show')
        episodes = media_item.get('episodes', [])
        
        # Look up metadata
        tv_shows_db = canonical_db.get('tv_shows', {})
        show_metadata = tv_shows_db.get(title, {})
        
        if not show_metadata:
            # No metadata found - mark for review
            for episode in episodes:
                file_path = episode.get('file_path', '')
                action = ReorganizationAction(
                    source_path=file_path,
                    target_path=None,
                    action='REVIEW',
                    media_type='tv_show',
                    status='pending',
                    reason=f"No metadata found for show: {title}",
                    related_files=self.subtitle_map.get(file_path, []),
                    metadata=episode
                )
                self.actions.append(action)
            return
        
        canonical_title = show_metadata.get('title', title)
        seasons_metadata = show_metadata.get('seasons', {})
        
        for episode in episodes:
            file_path = episode.get('file_path', '')
            season_num = episode.get('season', 0)
            episode_nums = episode.get('episodes', [])  # Can be list for multi-part
            
            if not episode_nums:
                # No episode number - mark for review
                action = ReorganizationAction(
                    source_path=file_path,
                    target_path=None,
                    action='REVIEW',
                    media_type='tv_show',
                    status='pending',
                    reason=f"No episode number found",
                    related_files=self.subtitle_map.get(file_path, []),
                    metadata=episode
                )
                self.actions.append(action)
                continue
            
            # Generate target path
            # TV Shows/Show Name/Season 01/Show Name S01E01 - Episode Title.ext
            source = Path(file_path)
            season_folder = f"Season {season_num:02d}"
            
            # Handle multi-part episodes
            if len(episode_nums) > 1:
                episode_str = f"E{episode_nums[0]:02d}-E{episode_nums[-1]:02d}"
            else:
                episode_str = f"E{episode_nums[0]:02d}"
            
            # Get episode title from metadata if available
            episode_title = ""
            if str(season_num) in seasons_metadata:
                season_episodes = seasons_metadata[str(season_num)].get('episodes', {})
                if episode_nums:
                    first_ep = season_episodes.get(str(episode_nums[0]), {})
                    episode_title = first_ep.get('title', '')
            
            filename_parts = [canonical_title, f"S{season_num:02d}{episode_str}"]
            if episode_title:
                filename_parts.append(f"- {episode_title}")
            
            target_filename = ' '.join(filename_parts) + source.suffix
            target_path = Path("TV Shows") / canonical_title / season_folder / target_filename
            
            # Get associated subtitles
            subtitles = self.subtitle_map.get(file_path, [])
            
            action = ReorganizationAction(
                source_path=file_path,
                target_path=str(target_path),
                action='MOVE',
                media_type='tv_show',
                status='pending',
                reason=f"Organize TV episode: {canonical_title} S{season_num:02d}{episode_str}",
                related_files=subtitles,
                metadata={
                    'title': canonical_title,
                    'season': season_num,
                    'episodes': episode_nums,
                    'episode_title': episode_title,
                    'tmdb_id': show_metadata.get('tmdb_id'),
                    'imdb_id': show_metadata.get('imdb_id')
                }
            )
            self.actions.append(action)
            
            # Track target path for conflict detection
            self.path_conflicts[str(target_path)].append(file_path)
            
            # Create actions for subtitle files
            for subtitle_path in subtitles:
                sub_action = self._create_subtitle_action(
                    subtitle_path,
                    target_path.parent,
                    target_path.stem
                )
                self.actions.append(sub_action)
    
    def _create_subtitle_action(
        self, 
        subtitle_path: str, 
        target_dir: Path, 
        video_stem: str
    ) -> ReorganizationAction:
        """
        Create action for subtitle file to follow video file.
        
        Preserves language codes and markers (forced, sdh, etc.)
        """
        source = Path(subtitle_path)
        
        # Extract language code and markers from original subtitle filename
        # e.g., "Movie.en.forced.srt" -> ".en.forced"
        subtitle_stem = source.stem
        video_stem_simple = Path(subtitle_path).stem.split('.')[0]  # Get base name
        
        # Extract everything after the base name (language, forced, sdh, etc.)
        extra_parts = subtitle_stem.replace(video_stem_simple, '', 1)
        
        # Construct target filename: new_video_stem + language_markers + extension
        target_filename = f"{video_stem}{extra_parts}{source.suffix}"
        target_path = target_dir / target_filename
        
        action = ReorganizationAction(
            source_path=subtitle_path,
            target_path=str(target_path),
            action='MOVE',
            media_type='subtitle',
            status='pending',
            reason=f"Move subtitle with video file",
            related_files=[],
            metadata={'original_video': str(target_dir / f"{video_stem}{source.suffix}")}
        )
        
        return action
    
    def _process_unrecognized_file(self, file_path: str):
        """Process unrecognized files - mark for review."""
        action = ReorganizationAction(
            source_path=file_path,
            target_path=None,
            action='REVIEW',
            media_type='other',
            status='pending',
            reason="Unrecognized file - needs manual review",
            related_files=[],
            metadata={}
        )
        self.actions.append(action)
    
    def _detect_conflicts(self):
        """Detect target path conflicts (multiple sources mapping to same target)."""
        conflicts_found = 0
        
        for target_path, source_paths in self.path_conflicts.items():
            if len(source_paths) > 1:
                conflicts_found += 1
                logger.warning(f"Conflict detected: {len(source_paths)} files map to {target_path}")
                
                # Mark all conflicting actions for review
                for action in self.actions:
                    if action.source_path in source_paths:
                        action.action = 'REVIEW'
                        action.reason = f"Conflict: Multiple files map to same target ({len(source_paths)} files)"
        
        if conflicts_found:
            logger.warning(f"Found {conflicts_found} path conflicts - marked for review")
    
    def update_action(self, source_path: str, new_action: str, new_target: Optional[str] = None):
        """
        Update an action in the plan (for user editing).
        
        Args:
            source_path: Source file path to update
            new_action: New action (MOVE, DELETE, SKIP, REVIEW)
            new_target: New target path (for MOVE actions)
        """
        for action in self.actions:
            if action.source_path == source_path:
                action.action = new_action
                if new_target:
                    action.target_path = new_target
                logger.info(f"Updated action for {source_path}: {new_action}")
                return True
        
        logger.warning(f"Action not found for source: {source_path}")
        return False
    
    def bulk_update_actions(self, action_type: str, new_action: str):
        """
        Bulk update all actions of a specific type.
        
        Args:
            action_type: Current action type to update (MOVE, DELETE, SKIP, REVIEW)
            new_action: New action to set
        """
        updated = 0
        for action in self.actions:
            if action.action == action_type:
                action.action = new_action
                updated += 1
        
        logger.info(f"Bulk updated {updated} actions from {action_type} to {new_action}")
        return updated
    
    def save_plan(self, filename: Optional[str] = None) -> str:
        """
        Save reorganization plan to JSON file.
        
        Args:
            filename: Optional filename (default: timestamp-based)
        
        Returns:
            Path to saved file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"reorganization_plan_{timestamp}.json"
        
        output_path = self.output_dir / filename
        
        plan_data = {
            'created': datetime.now().isoformat(),
            'total_actions': len(self.actions),
            'action_summary': {
                'MOVE': sum(1 for a in self.actions if a.action == 'MOVE'),
                'DELETE': sum(1 for a in self.actions if a.action == 'DELETE'),
                'SKIP': sum(1 for a in self.actions if a.action == 'SKIP'),
                'REVIEW': sum(1 for a in self.actions if a.action == 'REVIEW')
            },
            'actions': [action.to_dict() for action in self.actions]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(plan_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved reorganization plan to: {output_path}")
        return str(output_path)
    
    def load_plan(self, filepath: str) -> List[ReorganizationAction]:
        """
        Load reorganization plan from JSON file.
        
        Args:
            filepath: Path to plan file
        
        Returns:
            List of ReorganizationAction objects
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            plan_data = json.load(f)
        
        self.actions = []
        for action_dict in plan_data.get('actions', []):
            action = ReorganizationAction(**action_dict)
            self.actions.append(action)
        
        logger.info(f"Loaded reorganization plan with {len(self.actions)} actions from: {filepath}")
        return self.actions
    
    def export_to_csv(self, filename: Optional[str] = None) -> str:
        """
        Export plan to CSV for easy editing in Excel/spreadsheet.
        
        Args:
            filename: Optional filename (default: timestamp-based)
        
        Returns:
            Path to saved CSV file
        """
        import csv
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"reorganization_plan_{timestamp}.csv"
        
        output_path = self.output_dir / filename
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Source Path', 'Target Path', 'Action', 'Media Type', 
                'Status', 'Reason', 'Related Files', 'Metadata'
            ])
            
            for action in self.actions:
                writer.writerow([
                    action.source_path,
                    action.target_path or '',
                    action.action,
                    action.media_type,
                    action.status,
                    action.reason,
                    ';'.join(action.related_files),
                    json.dumps(action.metadata)
                ])
        
        logger.info(f"Exported plan to CSV: {output_path}")
        return str(output_path)
    
    def get_statistics(self) -> Dict:
        """Get statistics about the reorganization plan."""
        return {
            'total_actions': len(self.actions),
            'by_action': {
                'MOVE': sum(1 for a in self.actions if a.action == 'MOVE'),
                'DELETE': sum(1 for a in self.actions if a.action == 'DELETE'),
                'SKIP': sum(1 for a in self.actions if a.action == 'SKIP'),
                'REVIEW': sum(1 for a in self.actions if a.action == 'REVIEW')
            },
            'by_media_type': {
                'movie': sum(1 for a in self.actions if a.media_type == 'movie'),
                'tv_show': sum(1 for a in self.actions if a.media_type == 'tv_show'),
                'subtitle': sum(1 for a in self.actions if a.media_type == 'subtitle'),
                'other': sum(1 for a in self.actions if a.media_type == 'other')
            },
            'files_with_subtitles': len(self.subtitle_map),
            'total_subtitle_files': sum(len(subs) for subs in self.subtitle_map.values()),
            'path_conflicts': sum(1 for sources in self.path_conflicts.values() if len(sources) > 1)
        }


def main():
    """CLI interface for testing."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Create reorganization plan from analysis results')
    parser.add_argument('--llm-analysis', required=True, help='Path to LLM analysis JSON')
    parser.add_argument('--canonical-db', required=True, help='Path to canonical metadata DB JSON')
    parser.add_argument('--scan-results', help='Optional scan results JSON')
    parser.add_argument('--output', default='data/reorganization_plans', help='Output directory')
    parser.add_argument('--format', choices=['json', 'csv', 'both'], default='both', help='Output format')
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Load inputs
    with open(args.llm_analysis, 'r', encoding='utf-8') as f:
        llm_analysis = json.load(f)
    
    with open(args.canonical_db, 'r', encoding='utf-8') as f:
        canonical_db = json.load(f)
    
    scan_results = None
    if args.scan_results:
        with open(args.scan_results, 'r', encoding='utf-8') as f:
            scan_results = json.load(f)
    
    # Create planner and generate plan
    planner = ReorganizationPlanner(output_dir=args.output)
    planner.create_plan(llm_analysis, canonical_db, scan_results)
    
    # Display statistics
    stats = planner.get_statistics()
    print("\n=== Reorganization Plan Statistics ===")
    print(f"Total actions: {stats['total_actions']}")
    print(f"\nBy Action:")
    for action, count in stats['by_action'].items():
        print(f"  {action}: {count}")
    print(f"\nBy Media Type:")
    for media_type, count in stats['by_media_type'].items():
        print(f"  {media_type}: {count}")
    print(f"\nSubtitles:")
    print(f"  Files with subtitles: {stats['files_with_subtitles']}")
    print(f"  Total subtitle files: {stats['total_subtitle_files']}")
    print(f"\nConflicts: {stats['path_conflicts']}")
    
    # Save plan
    if args.format in ['json', 'both']:
        json_path = planner.save_plan()
        print(f"\nSaved JSON plan: {json_path}")
    
    if args.format in ['csv', 'both']:
        csv_path = planner.export_to_csv()
        print(f"Saved CSV plan: {csv_path}")


if __name__ == '__main__':
    main()
