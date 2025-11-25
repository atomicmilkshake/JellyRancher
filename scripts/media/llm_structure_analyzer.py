#!/usr/bin/env python3
"""
LLM Structure Analyzer - Step 3 of JellyRancher Workflow

Takes folder structure summaries from FolderStructureScanner and submits them
to a reasoning LLM (via Poe API) to:
1. Propose Jellyfin-compliant reorganization
2. Detect and classify movies vs TV shows
3. Identify multi-part episodes that need special handling

Uses Grok-4.1-Fast-Reasoning or similar reasoning models for deep analysis.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging

# Add parent directories to path for imports
sys.path.append(str(Path(__file__).parent.parent / 'ai'))
from ravenmaven_client import PoeClient


class LLMStructureAnalyzer:
    """
    Analyzes media folder structures using LLM reasoning to propose
    Jellyfin-compliant organization.
    """
    
    def __init__(
        self, 
        model: str = "Grok-4.1-Fast-Reasoning",
        api_key: Optional[str] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the LLM analyzer.
        
        Args:
            model: LLM model to use (default: Grok-4.1-Fast-Reasoning)
            api_key: Poe API key (defaults to env var OPENAI_API_KEY)
            logger: Logger instance

        Raises:
            ValueError: If model name is invalid
            RuntimeError: If Poe client initialization fails
        """
        try:
            # Input validation
            if not model or not isinstance(model, str):
                raise ValueError(f"Invalid model name: {model}")
            
            self.model = model
            self.logger = logger or self._setup_logger()
            
            # Initialize Poe client with error handling
            try:
                self.client = PoeClient(
                    api_key=api_key,
                    default_model=model,
                    logger=self.logger
                )
            except Exception as e:
                raise RuntimeError(f"Failed to initialize Poe client: {e}")
            
            self.logger.info(f"LLM Structure Analyzer initialized with model: {model}")
            
        except ValueError as e:
            if logger:
                logger.error(f"Invalid input to LLMStructureAnalyzer: {e}", exc_info=True)
            raise
        except RuntimeError as e:
            if logger:
                logger.error(f"Failed to initialize LLMStructureAnalyzer: {e}", exc_info=True)
            raise
        except Exception as e:
            if logger:
                logger.error(f"Unexpected error initializing LLMStructureAnalyzer: {e}", exc_info=True)
            raise RuntimeError(f"Failed to initialize LLMStructureAnalyzer: {e}")
    
    def _setup_logger(self) -> logging.Logger:
        """Set up basic logger if none provided."""
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def analyze_structure(
        self, 
        structure_summary: Dict,
        additional_context: Optional[str] = None
    ) -> Dict:
        """
        Analyze folder structure and get LLM recommendations.
        
        Args:
            structure_summary: Structure summary from FolderStructureScanner
            additional_context: Optional additional context for the LLM
            
        Returns:
            Dictionary containing:
            - detected_media: List of detected movies and TV shows
            - reorganization_plan: Proposed Jellyfin-compliant structure
            - multi_part_episodes: Episodes requiring NFO files
            - reasoning: LLM's reasoning process

        Raises:
            TypeError: If structure_summary is not a dictionary
            ValueError: If structure_summary is empty
            RuntimeError: If LLM analysis fails
        """
        try:
            # Input validation
            if not isinstance(structure_summary, dict):
                raise TypeError(f"structure_summary must be a dict, got {type(structure_summary)}")
            
            if not structure_summary:
                raise ValueError("structure_summary cannot be empty")
            
            self.logger.info("Starting LLM structure analysis...")
            
            # Build comprehensive prompt for reasoning LLM
            try:
                prompt = self._build_analysis_prompt(structure_summary, additional_context)
            except Exception as e:
                raise RuntimeError(f"Failed to build analysis prompt: {e}")
            
            self.logger.info(f"Sending structure analysis request to {self.model}...")
            self.logger.debug(f"Prompt length: {len(prompt)} characters")
            
            # Send to LLM with extended timeout for reasoning
            try:
                response_text = self.client.send_message(
                    prompt=prompt,
                    model=self.model,
                    max_tokens=8000,  # Allow for detailed analysis
                    temperature=0.3,  # Lower temperature for more deterministic output
                    logger=self.logger
                )
            except Exception as e:
                raise RuntimeError(f"LLM API call failed: {e}")
            
            if not response_text or not isinstance(response_text, str):
                raise RuntimeError(f"Invalid LLM response: {type(response_text)}")
            
            self.logger.info("LLM analysis complete, parsing response...")
            
            # Parse the LLM response
            try:
                analysis_result = self._parse_llm_response(response_text)
            except Exception as e:
                raise RuntimeError(f"Failed to parse LLM response: {e}")
            
            # Add metadata with error handling
            try:
                analysis_result['metadata'] = {
                    'timestamp': datetime.now().isoformat(),
                    'model_used': self.model,
                    'prompt_length': len(prompt),
                    'response_length': len(response_text)
                }
            except Exception as e:
                self.logger.warning(f"Failed to add metadata to analysis result: {e}")
            
            detected_count = len(analysis_result.get('detected_media', []))
            self.logger.info(f"Analysis complete: {detected_count} media items detected")
            
            return analysis_result
            
        except (TypeError, ValueError) as e:
            self.logger.error(f"Invalid input to analyze_structure: {e}", exc_info=True)
            raise
        except RuntimeError as e:
            self.logger.error(f"Analysis failed: {e}", exc_info=True)
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during analysis: {e}", exc_info=True)
            raise RuntimeError(f"Failed to analyze structure: {e}")
    
    # Chunking constants
    MAX_FOLDERS_PER_CHUNK = 200
    
    def _chunk_folder_structure(self, structure_summary: Dict) -> List[Dict]:
        """
        Split a large folder structure into smaller chunks for processing.
        
        Args:
            structure_summary: Full folder structure dictionary
            
        Returns:
            List of chunk dictionaries, each containing a subset of folders
            plus metadata keys (project_name, scan_id, total_files)
        """
        # Separate metadata from folder data
        metadata_keys = {'project_name', 'scan_id', 'total_files'}
        metadata = {k: v for k, v in structure_summary.items() if k in metadata_keys}
        
        folders = [
            (k, v) for k, v in structure_summary.items()
            if k not in metadata_keys and isinstance(v, dict)
        ]
        
        if len(folders) <= self.MAX_FOLDERS_PER_CHUNK:
            return [structure_summary]  # No chunking needed
        
        # Split folders into chunks
        chunks = []
        for i in range(0, len(folders), self.MAX_FOLDERS_PER_CHUNK):
            chunk_folders = folders[i:i + self.MAX_FOLDERS_PER_CHUNK]
            
            # Build chunk dict with metadata + folder subset
            chunk_dict = dict(metadata)
            chunk_dict['_chunk_info'] = {
                'chunk_number': len(chunks) + 1,
                'total_chunks': (len(folders) + self.MAX_FOLDERS_PER_CHUNK - 1) // self.MAX_FOLDERS_PER_CHUNK,
                'folders_in_chunk': len(chunk_folders),
                'total_folders': len(folders)
            }
            
            for folder_path, folder_data in chunk_folders:
                chunk_dict[folder_path] = folder_data
            
            chunks.append(chunk_dict)
        
        self.logger.info(f"Split {len(folders)} folders into {len(chunks)} chunks")
        return chunks
    
    def analyze_structure_chunked(
        self, 
        structure_summary: Dict,
        additional_context: Optional[str] = None,
        progress_callback: Optional[callable] = None
    ) -> Dict:
        """
        Analyze folder structure with automatic chunking for large datasets.
        
        For structures with more than MAX_FOLDERS_PER_CHUNK folders, this method
        splits the data into chunks, processes each sequentially, and merges results.
        
        Args:
            structure_summary: Structure summary from FolderStructureScanner
            additional_context: Optional additional context for the LLM
            progress_callback: Optional callback(current_chunk, total_chunks, message)
            
        Returns:
            Merged dictionary containing combined results from all chunks
            
        Raises:
            TypeError: If structure_summary is not a dictionary
            ValueError: If structure_summary is empty
            RuntimeError: If LLM analysis fails
        """
        chunks = self._chunk_folder_structure(structure_summary)
        
        if len(chunks) == 1:
            # No chunking needed, use standard analysis
            return self.analyze_structure(structure_summary, additional_context)
        
        self.logger.info(f"Processing {len(chunks)} chunks for large structure analysis")
        
        # Process each chunk and collect results
        all_detected_media = []
        all_folder_changes = []
        all_compliance_issues = []
        all_multi_part_episodes = []
        all_reasoning = []
        
        for i, chunk in enumerate(chunks, 1):
            chunk_info = chunk.get('_chunk_info', {})
            chunk_num = chunk_info.get('chunk_number', i)
            total_chunks = chunk_info.get('total_chunks', len(chunks))
            
            if progress_callback:
                progress_callback(chunk_num, total_chunks, f"Analyzing chunk {chunk_num}/{total_chunks}...")
            
            self.logger.info(f"Processing chunk {chunk_num}/{total_chunks} ({chunk_info.get('folders_in_chunk', 0)} folders)")
            
            # Add chunk context to help LLM understand partial data
            chunk_context = (
                f"This is chunk {chunk_num} of {total_chunks} (total folders: {chunk_info.get('total_folders', 0)}).\n"
                f"Analyze only the folders in this chunk. Results will be merged later.\n"
            )
            if additional_context:
                chunk_context += f"\n{additional_context}"
            
            try:
                result = self.analyze_structure(chunk, chunk_context)
                
                # Collect results from this chunk
                all_detected_media.extend(result.get('detected_media', []))
                
                reorg_plan = result.get('reorganization_plan', {})
                all_folder_changes.extend(reorg_plan.get('folder_changes', []))
                all_compliance_issues.extend(reorg_plan.get('jellyfin_compliance_issues', []))
                
                all_multi_part_episodes.extend(result.get('multi_part_episodes', []))
                
                reasoning = result.get('reasoning', '')
                if reasoning:
                    all_reasoning.append(f"[Chunk {chunk_num}]: {reasoning}")
                    
            except Exception as e:
                self.logger.error(f"Failed to analyze chunk {chunk_num}: {e}")
                all_reasoning.append(f"[Chunk {chunk_num}]: ERROR - {e}")
        
        # Merge results
        merged_result = {
            'detected_media': all_detected_media,
            'reorganization_plan': {
                'summary': f"Merged analysis of {len(chunks)} chunks covering {chunk_info.get('total_folders', 0)} folders",
                'folder_changes': all_folder_changes,
                'jellyfin_compliance_issues': list(set(all_compliance_issues))  # Dedupe
            },
            'multi_part_episodes': all_multi_part_episodes,
            'reasoning': "\n\n".join(all_reasoning),
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'model_used': self.model,
                'chunks_processed': len(chunks),
                'total_folders': chunk_info.get('total_folders', 0),
                'detected_count': len(all_detected_media)
            }
        }
        
        self.logger.info(
            f"Chunked analysis complete: {len(all_detected_media)} media items "
            f"from {len(chunks)} chunks"
        )
        
        return merged_result
    
    def _build_analysis_prompt(
        self, 
        structure_summary: Dict,
        additional_context: Optional[str] = None,
        compact_json: bool = False,
        use_tree_format: bool = True  # NEW: Use token-efficient tree format
    ) -> str:
        """
        Build the prompt for LLM analysis.
        
        Args:
            structure_summary: Folder structure data
            additional_context: Optional additional context
            compact_json: If True, use compact JSON (for token estimation)
            use_tree_format: If True, use tree format (~60% fewer tokens)
            
        Returns:
            Complete prompt string

        Raises:
            TypeError: If structure_summary is not a dictionary
            ValueError: If JSON serialization fails
            RuntimeError: If prompt building fails
        """
        try:
            # Input validation
            if not isinstance(structure_summary, dict):
                raise TypeError(f"structure_summary must be a dict, got {type(structure_summary)}")
            
            # Use tree format for token efficiency
            if use_tree_format and not compact_json:
                return self._build_tree_prompt(structure_summary, additional_context)
            
            # Convert structure to readable format with error handling
            # Convert Path objects to strings for JSON serialization
            try:
                serializable_structure = self._make_json_serializable(structure_summary)
                indent = None if compact_json else 2
                structure_json = json.dumps(serializable_structure, indent=indent)
            except (TypeError, ValueError) as e:
                raise ValueError(f"Cannot serialize structure_summary to JSON: {e}")
            
            prompt = f"""You are an expert media librarian analyzing folder structures for Jellyfin media server organization.
        
TASK: Analyze the provided folder structure and generate a comprehensive reorganization plan.
        
FOLDER STRUCTURE DATA (includes per-folder statistics and, when available, MD5-based duplicate groups):
{structure_json}
        
JELLYFIN REQUIREMENTS:
1. Movies: Each movie in its own folder named "Movie Title (Year)/Movie Title (Year).ext"
2. TV Shows: "Show Name (Year)/Season XX/Show Name - sXXeYY - Episode Title.ext"
3. Multi-part episodes: Require NFO files to properly map parts (e.g., pilot episodes split into Part 1 & Part 2)

YOUR ANALYSIS MUST INCLUDE:

1. DETECTED MEDIA LIST:
   For each detected movie or TV show, provide:
   - title: The media title (cleaned and standardized)
   - type: "movie" or "tv_show"
   - year_estimate: Estimated year (if determinable from folder name)
   - current_location: Current folder path
   - confidence: How confident you are in the detection ("high", "medium", "low")
   - notes: Any special considerations

2. REORGANIZATION PLAN:
   Describe how the current structure should be reorganized for Jellyfin compliance.
   Be specific about:
   - Which folders need renaming
   - Which files need moving
   - Required folder structure changes
   - Season detection and organization

3. MULTI-PART EPISODES:
   Identify any episodes that appear to be multi-part (pilots, finales, etc.) that need NFO files.
   For each, specify:
   - show_title
   - season_number
   - episode_numbers: List of episode numbers that are actually parts of same episode
   - combined_episode_title
   - reason: Why you believe this is multi-part

4. REASONING:
   Explain your analysis process and any assumptions made.

{additional_context or ''}

RESPONSE FORMAT:
Provide your analysis as a JSON object with this exact structure:

{{
  "detected_media": [
    {{
      "title": "Example Movie",
      "type": "movie",
      "year_estimate": 2020,
      "current_location": "/path/to/folder",
      "confidence": "high",
      "notes": "Clear movie structure"
    }},
    {{
      "title": "Example TV Show",
      "type": "tv_show",
      "year_estimate": 2015,
      "current_location": "/path/to/show",
      "seasons_detected": 7,
      "confidence": "high",
      "notes": "Has 7 season folders"
    }}
  ],
  "reorganization_plan": {{
    "summary": "Overall reorganization approach",
    "folder_changes": [
      {{
        "current_path": "/old/path",
        "proposed_path": "/new/path",
        "action": "rename/move/restructure",
        "reason": "Why this change is needed"
      }}
    ],
    "jellyfin_compliance_issues": [
      "Issue 1: description",
      "Issue 2: description"
    ]
  }},
  "multi_part_episodes": [
    {{
      "show_title": "Star Trek The Next Generation",
      "season_number": 1,
      "episode_numbers": [1, 2],
      "combined_episode_title": "Encounter at Farpoint",
      "reason": "Two-part pilot episode stored as single file"
    }}
  ],
  "reasoning": "Your detailed reasoning and analysis process..."
}}

IMPORTANT: Return ONLY the JSON object, no additional text before or after.
"""
            
            return prompt
            
        except (TypeError, ValueError) as e:
            self.logger.error(f"Invalid input to _build_analysis_prompt: {e}", exc_info=True)
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error building prompt: {e}", exc_info=True)
            raise RuntimeError(f"Failed to build analysis prompt: {e}")
    
    def _build_tree_prompt(
        self,
        structure_summary: Dict,
        additional_context: Optional[str] = None
    ) -> str:
        """
        Build a tree-formatted prompt for LLM analysis.
        
        Tree format is ~60% more token-efficient than JSON while still
        being easily understood by LLMs (trained on `tree` command output).
        
        Args:
            structure_summary: Folder structure data
            additional_context: Optional additional context
            
        Returns:
            Complete prompt string in tree format
        """
        # Build tree representation
        tree_lines = []
        issues_detected = []
        stats = {'folders': 0, 'files': 0, 'total_size': 0}
        
        # Skip metadata keys
        metadata_keys = {'project_name', 'scan_id', 'total_files'}
        
        # Filter and sort folder entries (convert keys to strings for sorting)
        folder_items = [
            (folder_path, folder_data) 
            for folder_path, folder_data in structure_summary.items()
            if str(folder_path) not in metadata_keys and isinstance(folder_data, dict)
        ]
        folder_items.sort(key=lambda x: str(x[0]))
        
        for folder_path, folder_data in folder_items:
            
            stats['folders'] += 1
            folder_path_str = str(folder_path)
            
            # Get folder info
            files = folder_data.get('files', [])
            total_size = folder_data.get('total_size', 0)
            file_types = folder_data.get('file_types', {})
            
            stats['files'] += len(files)
            stats['total_size'] += total_size
            
            # Format size
            if total_size >= 1024**3:
                size_str = f"{total_size / 1024**3:.1f} GB"
            elif total_size >= 1024**2:
                size_str = f"{total_size / 1024**2:.1f} MB"
            else:
                size_str = f"{total_size / 1024:.1f} KB"
            
            # Build folder line with type hints
            types_str = ", ".join(f"{k}: {v}" for k, v in file_types.items()) if file_types else ""
            
            tree_lines.append(f"📁 {folder_path_str}")
            tree_lines.append(f"   └─ {len(files)} files | {size_str} | {types_str}")
            
            # List up to 5 files per folder (representative sample)
            for i, file_info in enumerate(files[:5]):
                if isinstance(file_info, dict):
                    fname = file_info.get('name', str(file_info))
                    fsize = file_info.get('size_bytes', 0)
                    if fsize >= 1024**3:
                        fsize_str = f"{fsize / 1024**3:.1f}GB"
                    elif fsize >= 1024**2:
                        fsize_str = f"{fsize / 1024**2:.0f}MB"
                    else:
                        fsize_str = f"{fsize / 1024:.0f}KB"
                    tree_lines.append(f"      ├─ {fname} [{fsize_str}]")
                else:
                    tree_lines.append(f"      ├─ {file_info}")
            
            if len(files) > 5:
                tree_lines.append(f"      └─ ... and {len(files) - 5} more files")
            
            # Check for potential issues
            folder_name = Path(folder_path_str).name
            if not any(c in folder_name for c in ['(', ')']):
                # Missing year in folder name
                issues_detected.append(f"⚠️ {folder_name}: Missing year in folder name")
            
        # Build statistics summary
        total_size_gb = stats['total_size'] / 1024**3
        
        # Build the complete tree prompt
        prompt = f"""You are an expert media librarian analyzing folder structures for Jellyfin media server organization.

=== FOLDER STRUCTURE ({stats['folders']} folders, {stats['files']} files, {total_size_gb:.1f} GB) ===

{chr(10).join(tree_lines)}

=== POTENTIAL ISSUES DETECTED ({len(issues_detected)}) ===
{chr(10).join(issues_detected) if issues_detected else 'None detected by pre-scan'}

=== JELLYFIN NAMING REQUIREMENTS ===
• Movies: "Movie Title (Year)/Movie Title (Year).ext"
• TV Shows: "Show Name/Season XX/Show Name - sXXeYY - Episode Title.ext"
• Multi-part episodes: Require NFO files to map parts properly

{additional_context or ''}

=== YOUR TASK ===
Analyze this structure and provide a JSON response with:

1. **detected_media**: List each movie/TV show with title, type, year, location, confidence
2. **reorganization_plan**: Specific folder/file changes needed for Jellyfin compliance
3. **multi_part_episodes**: Episodes that are multi-part (pilots, finales) needing NFO files
4. **reasoning**: Your analysis process

RESPONSE FORMAT (JSON only, no other text):
{{
  "detected_media": [{{"title": "...", "type": "movie|tv_show", "year_estimate": 2020, "current_location": "...", "confidence": "high|medium|low", "notes": "..."}}],
  "reorganization_plan": {{"summary": "...", "folder_changes": [{{"current_path": "...", "proposed_path": "...", "action": "...", "reason": "..."}}], "jellyfin_compliance_issues": []}},
  "multi_part_episodes": [{{"show_title": "...", "season_number": 1, "episode_numbers": [1,2], "combined_episode_title": "...", "reason": "..."}}],
  "reasoning": "..."
}}"""
        
        return prompt
    
    def _make_json_serializable(self, obj):
        """
        Recursively convert Path objects and other non-serializable types to strings.
        
        Args:
            obj: Object to make JSON serializable
        
        Returns:
            JSON-serializable version of obj
        """
        from pathlib import Path
        
        if isinstance(obj, Path):
            return str(obj)
        elif isinstance(obj, dict):
            return {str(k) if isinstance(k, Path) else k: self._make_json_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._make_json_serializable(item) for item in obj]
        elif isinstance(obj, set):
            return [self._make_json_serializable(item) for item in obj]
        else:
            return obj
    
    def _parse_llm_response(self, response_text: str) -> Dict:
        """
        Parse LLM response into structured data.
        
        Args:
            response_text: Raw response from LLM
            
        Returns:
            Parsed analysis dictionary
        """
        # Preserve original for error logging
        original_response = response_text
        
        try:
            # Try to extract JSON from response
            # LLMs sometimes wrap JSON in markdown code blocks
            # Some models (like Gemini-2.5-Pro) include thinking text before the JSON
            response_text = response_text.strip()
            
            # First, try to find a JSON code block (```json or ```JSON)
            # This handles cases where the response has thinking text before the JSON
            json_block_start = -1
            for marker in ['```json', '```JSON', '```']:
                pos = response_text.find(marker)
                if pos != -1:
                    json_block_start = pos
                    # Find the first newline after the opening fence
                    first_newline = response_text.find('\n', json_block_start)
                    if first_newline != -1:
                        start = first_newline + 1
                        # Find the closing ``` after the start
                        end = response_text.find('```', start)
                        if end > start:
                            response_text = response_text[start:end].strip()
                            break
                        else:
                            # No closing fence found, try to parse from start onwards
                            response_text = response_text[start:].strip()
                            break
            
            # If we didn't find a code block, try parsing the whole response
            # (maybe it's already pure JSON)
            if json_block_start == -1:
                response_text = response_text.strip()
            
            # Parse JSON
            result = json.loads(response_text)
            
            # Validate required keys
            required_keys = ['detected_media', 'reorganization_plan', 'multi_part_episodes', 'reasoning']
            for key in required_keys:
                if key not in result:
                    self.logger.warning(f"Missing expected key in LLM response: {key}")
                    result[key] = [] if key != 'reasoning' else "No reasoning provided"
            
            return result
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse LLM response as JSON: {e}")
            self.logger.debug(f"Original response (first 1000 chars): {original_response[:1000]}...")
            self.logger.debug(f"Original response (last 500 chars): ...{original_response[-500:]}")
            # Try to find where JSON might be
            json_markers = ['```json', '```JSON', '{', '[']
            for marker in json_markers:
                pos = original_response.find(marker)
                if pos != -1:
                    self.logger.debug(f"Found '{marker}' at position {pos}")
            
            # Return a structured error response
            return {
                'detected_media': [],
                'reorganization_plan': {
                    'summary': 'Failed to parse LLM response',
                    'folder_changes': [],
                    'jellyfin_compliance_issues': ['LLM response parsing failed']
                },
                'multi_part_episodes': [],
                'reasoning': f'Error: Failed to parse response - {str(e)}',
                'raw_response': original_response,
                'error': str(e)
            }
    
    def save_analysis(self, analysis_result: Dict, output_path: str):
        """
        Save analysis result to JSON file.
        
        Args:
            analysis_result: Analysis dictionary
            output_path: Path to save the file

        Raises:
            TypeError: If inputs are invalid
            ValueError: If output_path is empty
            OSError: If file cannot be written
            RuntimeError: If save operation fails
        """
        try:
            # Input validation
            if not isinstance(analysis_result, dict):
                raise TypeError(f"analysis_result must be a dict, got {type(analysis_result)}")
            
            if not output_path or not isinstance(output_path, str):
                raise ValueError(f"Invalid output_path: {output_path}")
            
            output_file = Path(output_path)
            
            # Create parent directory with error handling
            try:
                output_file.parent.mkdir(parents=True, exist_ok=True)
            except (PermissionError, OSError) as e:
                raise RuntimeError(f"Cannot create output directory {output_file.parent}: {e}")
            
            # Write file with error handling
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(analysis_result, f, indent=2, ensure_ascii=False)
            except (OSError, PermissionError) as e:
                raise RuntimeError(f"Cannot write to file {output_file}: {e}")
            except (TypeError, ValueError) as e:
                raise RuntimeError(f"Cannot serialize analysis_result to JSON: {e}")
            
            self.logger.info(f"Analysis saved to: {output_file}")
            
        except (TypeError, ValueError) as e:
            self.logger.error(f"Invalid input to save_analysis: {e}", exc_info=True)
            raise
        except RuntimeError as e:
            self.logger.error(f"Failed to save analysis: {e}", exc_info=True)
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error saving analysis: {e}", exc_info=True)
            raise RuntimeError(f"Failed to save analysis: {e}")


def main():
    """
    Example usage of LLM Structure Analyzer.
    """
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python llm_structure_analyzer.py <structure_summary.json>")
        print("\nExample:")
        print("  python llm_structure_analyzer.py data/scan_structure_20241108_120000.json")
        return
    
    # Load structure summary
    structure_file = Path(sys.argv[1])
    if not structure_file.exists():
        print(f"Error: File not found: {structure_file}")
        return
    
    print(f"Loading structure summary from: {structure_file}")
    with open(structure_file, 'r', encoding='utf-8') as f:
        structure_data = json.load(f)
    
    # Initialize analyzer
    analyzer = LLMStructureAnalyzer()
    
    # Perform analysis
    print("\n" + "="*80)
    print("ANALYZING FOLDER STRUCTURE WITH LLM...")
    print("="*80 + "\n")
    
    analysis = analyzer.analyze_structure(structure_data)
    
    # Display results summary
    print("\n" + "="*80)
    print("ANALYSIS RESULTS")
    print("="*80)
    
    print(f"\n📺 Detected Media: {len(analysis['detected_media'])} items")
    for media in analysis['detected_media'][:5]:  # Show first 5
        print(f"  - {media['title']} ({media['type']})")
    if len(analysis['detected_media']) > 5:
        print(f"  ... and {len(analysis['detected_media']) - 5} more")
    
    print(f"\n🔄 Folder Changes: {len(analysis['reorganization_plan'].get('folder_changes', []))}")
    
    print(f"\n⚠️  Multi-part Episodes: {len(analysis['multi_part_episodes'])}")
    for episode in analysis['multi_part_episodes']:
        print(f"  - {episode['show_title']} S{episode['season_number']:02d}E{episode['episode_numbers']}")
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"data/llm_analysis_{timestamp}.json"
    analyzer.save_analysis(analysis, output_path)
    
    print(f"\n💾 Analysis saved to: {output_path}")
    print("="*80)


if __name__ == "__main__":
    main()
