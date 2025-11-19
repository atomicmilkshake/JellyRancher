#!/usr/bin/env python3
"""
Action Plan Generator - Point 5 of JellyRancher Workflow

Generates a list of proposed file operations based on the file inventory,
LLM analysis, and canonical metadata database.

Implements Jellyfin-aware reorganization with:
- Jellyfin status detection (Already in Library, New, Path Mismatch)
- ProviderIds-based matching
- MD5 duplicate detection
- Subtitle file association
- NFO generation for multi-part episodes

Architecture:
    Per Jellyfin API Integration Plan, this uses Phase 1 context (Jellyfin data
    already retrieved during scan) to make intelligent decisions.
"""

import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from collections import defaultdict
from rapidfuzz import fuzz

from scripts.core.action_plan import ProposedOperation, ActionType, Confidence
from scripts.core.file_scanner import FileRecord
from scripts.core.app_config import AppConfigManager

logger = logging.getLogger(__name__)


# Video and subtitle file extensions
VIDEO_EXTENSIONS = {'.mkv', '.mp4', '.avi', '.mov', '.wmv', '.flv', '.m4v', '.ts', '.mpg', '.mpeg'}
SUBTITLE_EXTENSIONS = {'.srt', '.sub', '.idx', '.ass', '.ssa', '.vtt'}


class ActionPlanGenerator:
    """
    Generates an action plan for media file reorganization.

    Uses Jellyfin data (from FileRecord.jellyfin_*), LLM analysis, and canonical
    metadata to propose intelligent file operations with confidence scoring.
    """

    def __init__(
        self,
        scanned_files: List[FileRecord],
        llm_analysis: Dict[str, Any],
        canonical_database: Dict[str, Any],
        app_config: Optional[AppConfigManager] = None
    ):
        """
        Initialize the action plan generator.

        Args:
            scanned_files: List of FileRecord objects from the initial scan.
            llm_analysis: Dictionary containing the LLM's reorganization proposal.
            canonical_database: Dictionary containing the canonical metadata.
            app_config: Application configuration manager (optional, will create if None)

        Raises:
            TypeError: If inputs are of incorrect type
            ValueError: If required inputs are empty
            RuntimeError: If initialization fails
        """
        try:
            # Input validation
            if not isinstance(scanned_files, list):
                raise TypeError(f"scanned_files must be a list, got {type(scanned_files)}")
            
            if not isinstance(llm_analysis, dict):
                raise TypeError(f"llm_analysis must be a dict, got {type(llm_analysis)}")
            
            if not isinstance(canonical_database, dict):
                raise TypeError(f"canonical_database must be a dict, got {type(canonical_database)}")
            
            if not scanned_files:
                raise ValueError("scanned_files cannot be empty")
            
            self.scanned_files = scanned_files
            self.llm_analysis = llm_analysis
            self.canonical_database = canonical_database
            
            # Initialize or use provided config
            try:
                self.app_config = app_config or AppConfigManager()
            except Exception as e:
                raise RuntimeError(f"Failed to initialize AppConfigManager: {e}")
            
            self.action_plan: List[ProposedOperation] = []

            # Build helper indices
            try:
                self._build_indices()
            except Exception as e:
                raise RuntimeError(f"Failed to build indices: {e}")
                
            logger.info(f"ActionPlanGenerator initialized with {len(scanned_files)} files")
            
        except (TypeError, ValueError) as e:
            logger.error(f"Invalid input to ActionPlanGenerator: {e}", exc_info=True)
            raise
        except RuntimeError as e:
            logger.error(f"Failed to initialize ActionPlanGenerator: {e}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Unexpected error initializing ActionPlanGenerator: {e}", exc_info=True)
            raise RuntimeError(f"Failed to initialize ActionPlanGenerator: {e}")

    def _build_indices(self):
        """
        Build helper indices for efficient lookups.

        Raises:
            RuntimeError: If index building fails
        """
        try:
            # MD5 hash index for duplicate detection
            self.md5_index: Dict[str, List[FileRecord]] = defaultdict(list)
            errors = 0
            
            for record in self.scanned_files:
                try:
                    if record.md5_hash:
                        self.md5_index[record.md5_hash].append(record)
                except (AttributeError, TypeError) as e:
                    logger.warning(f"Error adding record to MD5 index: {e}")
                    errors += 1
                    continue

            # Video file to subtitle file mapping (based on basename)
            self.video_to_subs: Dict[Path, List[FileRecord]] = defaultdict(list)
            video_files = {}
            subtitle_files = []

            for record in self.scanned_files:
                try:
                    ext = record.extension.lower()
                    if ext in VIDEO_EXTENSIONS:
                        video_files[record.absolute_path.parent / record.absolute_path.stem] = record
                    elif ext in SUBTITLE_EXTENSIONS:
                        subtitle_files.append(record)
                except (AttributeError, TypeError) as e:
                    logger.warning(f"Error categorizing file record: {e}")
                    errors += 1
                    continue

            # Match subtitles to video files by stem (filename without extension)
            for sub_record in subtitle_files:
                try:
                    # Try to find matching video file
                    sub_stem = sub_record.absolute_path.stem
                    # Handle .en.srt style names
                    base_stem = re.sub(r'\.[a-z]{2}(-[A-Z]{2})?$', '', sub_stem)

                    video_base = sub_record.absolute_path.parent / base_stem
                    if video_base in video_files:
                        video_record = video_files[video_base]
                        self.video_to_subs[video_record.absolute_path].append(sub_record)
                except (AttributeError, TypeError, KeyError) as e:
                    logger.warning(f"Error matching subtitle to video: {e}")
                    errors += 1
                    continue

            if errors > 0:
                logger.warning(f"Built indices with {errors} errors: {len(self.md5_index)} MD5 groups, {len(self.video_to_subs)} videos with subtitles")
            else:
                logger.info(f"Built indices: {len(self.md5_index)} MD5 groups, {len(self.video_to_subs)} videos with subtitles")
                
        except Exception as e:
            logger.error(f"Failed to build indices: {e}", exc_info=True)
            raise RuntimeError(f"Failed to build indices: {e}")

    def generate_plan(self) -> List[ProposedOperation]:
        """
        Generate the full action plan.

        This is the main entry point that orchestrates the plan generation.

        Returns:
            List of ProposedOperation objects

        Raises:
            RuntimeError: If plan generation fails
        """
        try:
            logger.info("Generating action plan...")

            # Reset action plan
            self.action_plan = []

            # Step 1: Detect duplicates and mark for review/deletion
            try:
                duplicate_files = self._handle_duplicates()
            except Exception as e:
                logger.error(f"Error handling duplicates: {e}", exc_info=True)
                duplicate_files = set()  # Continue with empty set

            # Step 2: Process video files (main media files)
            processed_videos = set()
            errors = 0
            
            for record in self.scanned_files:
                try:
                    if record.extension.lower() in VIDEO_EXTENSIONS:
                        # Skip if already handled as duplicate
                        if record.absolute_path in duplicate_files:
                            continue

                        operation = self._process_video_file(record)
                        if operation:
                            self.action_plan.append(operation)
                            processed_videos.add(record.absolute_path)
                            
                except Exception as e:
                    logger.warning(f"Error processing video file {record.absolute_path}: {e}")
                    errors += 1
                    continue

            # Step 3: Process subtitle files (associated with videos)
            for record in self.scanned_files:
                try:
                    if record.extension.lower() in SUBTITLE_EXTENSIONS:
                        # Skip if already handled as duplicate
                        if record.absolute_path in duplicate_files:
                            continue

                        operation = self._process_subtitle_file(record, processed_videos)
                        if operation:
                            self.action_plan.append(operation)
                            
                except Exception as e:
                    logger.warning(f"Error processing subtitle file {record.absolute_path}: {e}")
                    errors += 1
                    continue

            # Step 4: Generate NFO creation operations for multi-part episodes
            try:
                nfo_ops = self._generate_nfo_operations()
                self.action_plan.extend(nfo_ops)
            except Exception as e:
                logger.error(f"Error generating NFO operations: {e}", exc_info=True)
                # Continue without NFO ops

            if errors > 0:
                logger.warning(f"Generated {len(self.action_plan)} operations with {errors} errors")
            else:
                logger.info(f"Generated {len(self.action_plan)} proposed operations.")
            
            return self.action_plan
            
        except Exception as e:
            logger.error(f"Failed to generate action plan: {e}", exc_info=True)
            raise RuntimeError(f"Failed to generate action plan: {e}")

    def _handle_duplicates(self) -> set:
        """
        Detect and mark duplicate files for deletion or review.

        Returns:
            Set of file paths that have been handled as duplicates

        Raises:
            RuntimeError: If duplicate handling fails catastrophically
        """
        try:
            handled = set()
            errors = 0
            
            try:
                duplicate_strategy = self.app_config.get_duplicate_strategy()
            except Exception as e:
                logger.warning(f"Failed to get duplicate strategy, using default 'review': {e}")
                duplicate_strategy = "review"

            for md5_hash, records in self.md5_index.items():
                try:
                    if len(records) < 2:
                        continue  # Not a duplicate

                    logger.info(f"Found {len(records)} duplicates with MD5 {md5_hash[:8]}...")

                    # Sort records by priority (Jellyfin first, then by size)
                    try:
                        sorted_records = sorted(
                            records,
                            key=lambda r: (
                                not r.jellyfin_matched,  # Jellyfin files first (False sorts before True)
                                -r.size_bytes  # Larger files first
                            )
                        )
                    except (AttributeError, TypeError) as e:
                        logger.warning(f"Error sorting duplicates for {md5_hash}: {e}")
                        sorted_records = records  # Use unsorted

                    # Keep the first one, mark others for deletion or review
                    keeper = sorted_records[0]
                    duplicates = sorted_records[1:]

                    for dup in duplicates:
                        try:
                            action_type = ActionType.REVIEW  # Default
                            confidence = Confidence.MEDIUM
                            notes = f"Duplicate of {keeper.absolute_path.name}"

                            # Apply strategy
                            if duplicate_strategy == "jellyfin_first" and keeper.jellyfin_matched:
                                action_type = ActionType.DELETE
                                confidence = Confidence.HIGH
                                notes += f" (auto-marked: keeping Jellyfin file)"
                            elif duplicate_strategy == "largest_file" and keeper.size_bytes > dup.size_bytes:
                                action_type = ActionType.DELETE
                                confidence = Confidence.HIGH
                                notes += f" (auto-marked: keeping larger file)"
                            else:
                                notes += f" (manual review required)"

                            operation = ProposedOperation(
                                source_path=dup.absolute_path,
                                destination_path=None,
                                action_type=action_type,
                                confidence=confidence,
                                notes=notes,
                                jellyfin_status=self._determine_jellyfin_status(dup),
                                jellyfin_id=dup.jellyfin_id,
                                current_provider_ids=dup.jellyfin_provider_ids or {},
                                current_md5=dup.md5_hash  # MD5 for verification
                            )

                            self.action_plan.append(operation)
                            handled.add(dup.absolute_path)
                            
                        except Exception as e:
                            logger.warning(f"Error creating operation for duplicate {dup.absolute_path}: {e}")
                            errors += 1
                            continue
                            
                except Exception as e:
                    logger.warning(f"Error processing duplicate group {md5_hash}: {e}")
                    errors += 1
                    continue

            if errors > 0:
                logger.warning(f"Handled duplicates with {errors} errors, {len(handled)} files marked")
                
            return handled
            
        except Exception as e:
            logger.error(f"Failed to handle duplicates: {e}", exc_info=True)
            raise RuntimeError(f"Failed to handle duplicates: {e}")

    def _process_video_file(self, record: FileRecord) -> Optional[ProposedOperation]:
        """
        Process a single video file and generate a proposed operation.

        Args:
            record: FileRecord for the video file

        Returns:
            ProposedOperation or None
        """
        # Determine Jellyfin status
        jellyfin_status = self._determine_jellyfin_status(record)

        # Try to match to canonical metadata
        matched_metadata, match_confidence = self._match_to_canonical(record)

        # Generate destination path
        dest_path = self._generate_destination_path(record, matched_metadata)

        # Determine action and confidence
        action_type, overall_confidence, notes = self._determine_action(
            record, dest_path, jellyfin_status, match_confidence, matched_metadata
        )

        return ProposedOperation(
            source_path=record.absolute_path,
            destination_path=dest_path,
            action_type=action_type,
            confidence=overall_confidence,
            notes=notes,
            jellyfin_status=jellyfin_status,
            jellyfin_id=record.jellyfin_id,
            current_provider_ids=record.jellyfin_provider_ids or {},
            proposed_provider_ids=self._extract_provider_ids(matched_metadata) if matched_metadata else {},
            current_md5=record.md5_hash,  # MD5 for verification
            canonical_metadata=matched_metadata
        )

    def _process_subtitle_file(self, record: FileRecord, processed_videos: set) -> Optional[ProposedOperation]:
        """
        Process a subtitle file.

        Subtitle files follow their associated video file. If the video is being moved,
        the subtitle gets moved too. If shown in table, it's greyed out and auto-approved.

        Args:
            record: FileRecord for subtitle file
            processed_videos: Set of video file paths that have been processed

        Returns:
            ProposedOperation or None (if not showing subtitles in table)
        """
        if not self.app_config.is_show_subtitles_in_table():
            # Subtitles will be handled invisibly during video file move
            return None

        # Find the associated video file (already done in indices)
        associated_video = None
        for video_path, sub_records in self.video_to_subs.items():
            if record in sub_records:
                associated_video = video_path
                break

        if not associated_video:
            # Orphaned subtitle
            return ProposedOperation(
                source_path=record.absolute_path,
                destination_path=None,
                action_type=ActionType.REVIEW,
                confidence=Confidence.MANUAL,
                notes="Orphaned subtitle - no matching video file found",
                jellyfin_status="Unknown",
                current_md5=record.md5_hash  # MD5 for verification
            )

        # Find the video's operation in the action plan
        video_op = None
        for op in self.action_plan:
            if op.source_path == associated_video:
                video_op = op
                break

        if not video_op or video_op.action_type == ActionType.SKIP:
            # Video isn't moving, subtitle stays put
            return ProposedOperation(
                source_path=record.absolute_path,
                destination_path=None,
                action_type=ActionType.SKIP,
                confidence=Confidence.NONE,
                notes=f"Associated with {associated_video.name} (no move needed)",
                jellyfin_status="N/A (Subtitle)",
                current_md5=record.md5_hash  # MD5 for verification
            )

        # Video is moving, subtitle follows
        # Generate subtitle destination based on video destination
        video_dest = video_op.destination_path
        if video_dest:
            # Preserve subtitle naming (e.g., .en.srt)
            sub_dest = video_dest.parent / (video_dest.stem + record.absolute_path.suffix)

            return ProposedOperation(
                source_path=record.absolute_path,
                destination_path=sub_dest,
                action_type=ActionType.MOVE,
                confidence=Confidence.HIGH,
                notes=f"Follows {associated_video.name} (auto-approved)",
                jellyfin_status="N/A (Subtitle)",
                current_md5=record.md5_hash,  # MD5 for verification
                user_approved=self.app_config.is_subtitle_auto_approve()
            )

        return None

    def _generate_nfo_operations(self) -> List[ProposedOperation]:
        """
        Generate NFO file creation operations for multi-part episodes.

        Returns:
            List of ProposedOperation objects for NFO creation
        """
        nfo_ops = []

        multi_part_episodes = self.canonical_database.get('multi_part_episodes', [])
        if not multi_part_episodes:
            return nfo_ops

        logger.info(f"Generating NFO operations for {len(multi_part_episodes)} multi-part episodes")

        for episode_data in multi_part_episodes:
            # Find the corresponding file operation in the action plan
            show_title = episode_data.get('show_title', '')
            season = episode_data.get('season_number', 0)
            episode = episode_data.get('episode_number', 0)

            # NFO will be created next to the destination file
            # Look for the file operation that matches this episode
            for op in self.action_plan:
                if op.destination_path and self._matches_episode(op, show_title, season, episode):
                    nfo_path = op.destination_path.with_suffix('.nfo')

                    nfo_op = ProposedOperation(
                        source_path=nfo_path,  # NFO doesn't exist yet
                        destination_path=nfo_path,
                        action_type=ActionType.CREATE_NFO,
                        confidence=Confidence.HIGH,
                        notes=f"Multi-part episode NFO for S{season:02d}E{episode:02d}",
                        jellyfin_status="Required for Jellyfin",
                        canonical_metadata=episode_data
                    )
                    nfo_ops.append(nfo_op)
                    break

        return nfo_ops

    def _determine_jellyfin_status(self, record: FileRecord) -> str:
        """
        Determine the Jellyfin status of a file.

        Per Jellyfin API Integration Plan, statuses are:
        - "Already in Library": File is in Jellyfin and path is compliant
        - "Path Mismatch": File is in Jellyfin but path doesn't follow conventions
        - "New": File not in Jellyfin
        - "Unknown": Cannot determine

        Args:
            record: FileRecord to check

        Returns:
            Status string
        """
        if not record.jellyfin_matched:
            return "New"

        # File is in Jellyfin - check if path matches conventions
        # We'll do a simple check: does the path look Jellyfin-compliant?
        # Full check would compare to proposed destination path
        path_str = str(record.absolute_path)

        # Simple heuristics for Jellyfin compliance:
        # Movies: contains (YEAR) in path
        # TV: contains Season XX and SXXEXX pattern
        has_year_pattern = bool(re.search(r'\(\d{4}\)', path_str))
        has_season_folder = bool(re.search(r'Season\s+\d+', path_str, re.IGNORECASE))
        has_episode_pattern = bool(re.search(r'S\d+E\d+', path_str, re.IGNORECASE))

        is_movie = record.jellyfin_item_type == "Movie"
        is_episode = record.jellyfin_item_type == "Episode"

        if is_movie and has_year_pattern:
            return "Already in Library"
        elif is_episode and has_season_folder and has_episode_pattern:
            return "Already in Library"
        else:
            return "Path Mismatch"

    def _match_to_canonical(self, record: FileRecord) -> Tuple[Optional[Dict], float]:
        """
        Match a FileRecord to canonical metadata.

        Uses ProviderIds from Jellyfin if available, otherwise fuzzy matches.

        Args:
            record: FileRecord to match

        Returns:
            Tuple of (matched_metadata_dict, confidence_score)
        """
        # Priority 1: Use Jellyfin ProviderIds for exact match
        if record.jellyfin_provider_ids:
            tmdb_id = record.jellyfin_provider_ids.get('Tmdb')
            tvdb_id = record.jellyfin_provider_ids.get('Tvdb')

            if tmdb_id or tvdb_id:
                # Search canonical database for matching ProviderIds
                matched = self._find_by_provider_ids(tmdb_id, tvdb_id)
                if matched:
                    return matched, 1.0  # 100% confidence with ProviderIds

        # Priority 2: Fuzzy match by filename
        # Extract title from filename
        filename_title = self._extract_title_from_filename(record.absolute_path)
        if filename_title:
            matched, score = self._fuzzy_match_canonical(filename_title)
            return matched, score

        return None, 0.0

    def _find_by_provider_ids(self, tmdb_id: Optional[str], tvdb_id: Optional[str]) -> Optional[Dict]:
        """Find metadata in canonical database by provider IDs."""
        movies = self.canonical_database.get('movies', [])
        tv_shows = self.canonical_database.get('tv_shows', [])

        if tmdb_id:
            for movie in movies:
                if str(movie.get('tmdb_id')) == str(tmdb_id):
                    return movie

            for show in tv_shows:
                if str(show.get('tmdb_id')) == str(tmdb_id):
                    return show

        if tvdb_id:
            for show in tv_shows:
                if str(show.get('tvdb_id')) == str(tvdb_id):
                    return show

        return None

    def _extract_title_from_filename(self, path: Path) -> Optional[str]:
        """Extract media title from filename."""
        filename = path.stem

        # Remove common patterns
        # Remove year
        filename = re.sub(r'\(?\d{4}\)?', '', filename)
        # Remove quality markers
        filename = re.sub(r'\b(1080p|720p|2160p|4K|BluRay|WEB-DL|WEBRip|HDTV)\b', '', filename, flags=re.IGNORECASE)
        # Remove episode patterns
        filename = re.sub(r'S\d+E\d+', '', filename, flags=re.IGNORECASE)
        # Remove brackets and parentheses content
        filename = re.sub(r'[\[\(].*?[\]\)]', '', filename)
        # Replace dots/underscores with spaces
        filename = filename.replace('.', ' ').replace('_', ' ')
        # Clean up whitespace
        filename = ' '.join(filename.split())

        return filename.strip() if filename.strip() else None

    def _fuzzy_match_canonical(self, title: str) -> Tuple[Optional[Dict], float]:
        """Fuzzy match a title against canonical database."""
        best_match = None
        best_score = 0.0

        movies = self.canonical_database.get('movies', [])
        tv_shows = self.canonical_database.get('tv_shows', [])

        all_items = list(movies) + list(tv_shows)

        for item in all_items:
            item_title = item.get('title', '')
            score = fuzz.ratio(title.lower(), item_title.lower()) / 100.0

            if score > best_score:
                best_score = score
                best_match = item

        return best_match, best_score

    def _generate_destination_path(self, record: FileRecord, metadata: Optional[Dict]) -> Optional[Path]:
        """
        Generate Jellyfin-compliant destination path.

        Args:
            record: FileRecord
            metadata: Matched canonical metadata (or None)

        Returns:
            Destination path or None
        """
        if not metadata:
            return None

        media_type = metadata.get('type', 'unknown')

        if media_type == 'movie':
            return self._generate_movie_path(record, metadata)
        elif media_type == 'tv_show':
            return self._generate_tv_path(record, metadata)
        else:
            return None

    def _generate_movie_path(self, record: FileRecord, metadata: Dict) -> Optional[Path]:
        """
        Generate movie path: {base}/Movie Title (Year)/Movie Title (Year).ext

        Args:
            record: FileRecord
            metadata: Movie metadata

        Returns:
            Path or None
        """
        base = self.app_config.get_movies_base()
        if not base:
            return None

        title = metadata.get('title', 'Unknown')
        year = metadata.get('year', '')

        folder_name = f"{title} ({year})" if year else title
        filename = f"{folder_name}{record.extension}"

        return base / folder_name / filename

    def _generate_tv_path(self, record: FileRecord, metadata: Dict) -> Optional[Path]:
        """
        Generate TV path: {base}/Show Name/Season XX/Show Name - SXXEXX - Episode Title.ext

        This is simplified - in reality we'd need to parse episode info from filename.

        Args:
            record: FileRecord
            metadata: TV show metadata

        Returns:
            Path or None
        """
        base = self.app_config.get_tv_base()
        if not base:
            return None

        show_title = metadata.get('title', 'Unknown')

        # Try to extract season/episode from filename
        filename = record.absolute_path.stem
        match = re.search(r'S(\d+)E(\d+)', filename, re.IGNORECASE)

        if not match:
            # Can't determine episode - return None (will be manual review)
            return None

        season_num = int(match.group(1))
        episode_num = int(match.group(2))

        # Try to find episode title from metadata
        episode_title = self._find_episode_title(metadata, season_num, episode_num)

        season_folder = f"Season {season_num:02d}"
        if episode_title:
            filename = f"{show_title} - S{season_num:02d}E{episode_num:02d} - {episode_title}{record.extension}"
        else:
            filename = f"{show_title} - S{season_num:02d}E{episode_num:02d}{record.extension}"

        return base / show_title / season_folder / filename

    def _find_episode_title(self, show_metadata: Dict, season_num: int, episode_num: int) -> Optional[str]:
        """Find episode title from show metadata."""
        seasons = show_metadata.get('seasons', [])
        for season in seasons:
            if season.get('season_number') == season_num:
                episodes = season.get('episodes', [])
                for episode in episodes:
                    if episode.get('episode_number') == episode_num:
                        return episode.get('episode_title')
        return None

    def _determine_action(
        self,
        record: FileRecord,
        dest_path: Optional[Path],
        jellyfin_status: str,
        match_confidence: float,
        metadata: Optional[Dict]
    ) -> Tuple[ActionType, Confidence, str]:
        """
        Determine the action type, overall confidence, and notes.

        Args:
            record: FileRecord
            dest_path: Proposed destination path
            jellyfin_status: Jellyfin status string
            match_confidence: Metadata match confidence (0.0-1.0)
            metadata: Matched metadata

        Returns:
            Tuple of (ActionType, Confidence, notes_string)
        """
        notes = []

        # Already in library and compliant - skip
        if jellyfin_status == "Already in Library" and dest_path:
            # Check if current path matches destination
            if record.absolute_path.resolve() == dest_path.resolve():
                return ActionType.SKIP, Confidence.NONE, "File already correctly organized"

        # New file or path mismatch - move
        if jellyfin_status in ["New", "Path Mismatch"] and dest_path:
            # Confidence based on metadata match
            if match_confidence >= 0.95:
                confidence = Confidence.HIGH
                notes.append("High confidence match via ProviderIds" if record.jellyfin_provider_ids else "High confidence fuzzy match")
            elif match_confidence >= 0.80:
                confidence = Confidence.MEDIUM
                notes.append("Medium confidence fuzzy match")
            elif match_confidence >= 0.70:
                confidence = Confidence.LOW
                notes.append("Low confidence match")
            else:
                confidence = Confidence.MANUAL
                notes.append("Poor match - manual review recommended")

            if jellyfin_status == "Path Mismatch":
                notes.append("File in Jellyfin but path needs correction")
            else:
                notes.append("New file - not yet in Jellyfin")

            return ActionType.MOVE, confidence, "; ".join(notes)

        # No metadata match - review
        if not metadata:
            return ActionType.REVIEW, Confidence.MANUAL, "Could not match to canonical metadata"

        # No destination path (config not set)
        if not dest_path:
            return ActionType.REVIEW, Confidence.MANUAL, "Destination base path not configured"

        # Fallback
        return ActionType.REVIEW, Confidence.MANUAL, "Manual review required"

    def _extract_provider_ids(self, metadata: Optional[Dict]) -> Dict[str, str]:
        """Extract ProviderIds from metadata."""
        if not metadata:
            return {}

        provider_ids = {}
        if 'tmdb_id' in metadata:
            provider_ids['Tmdb'] = str(metadata['tmdb_id'])
        if 'tvdb_id' in metadata:
            provider_ids['Tvdb'] = str(metadata['tvdb_id'])
        if 'imdb_id' in metadata:
            provider_ids['Imdb'] = str(metadata['imdb_id'])

        return provider_ids

    def _matches_episode(self, operation: ProposedOperation, show_title: str, season: int, episode: int) -> bool:
        """Check if an operation matches a specific episode."""
        if not operation.destination_path:
            return False

        path_str = str(operation.destination_path)
        return (show_title.lower() in path_str.lower() and
                f"S{season:02d}E{episode:02d}" in path_str)
