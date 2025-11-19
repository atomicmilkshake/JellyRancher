#!/usr/bin/env python3
"""
LLM Structure Analyzer - Step 3 of JellyRancher Workflow

Takes folder structure summaries from FolderStructureScanner and submits them
to a reasoning LLM (via Poe API) to:
1. Propose Jellyfin-compliant reorganization
2. Detect and classify movies vs TV shows
3. Identify multi-part episodes that need special handling

Uses Claude-Sonnet-4.5 or gpt-4o-reasoning for deep analysis.
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
        model: str = "Claude-Sonnet-4.5",
        api_key: Optional[str] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the LLM analyzer.
        
        Args:
            model: LLM model to use (default: Claude-Sonnet-4.5 for reasoning)
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
    
    def _build_analysis_prompt(
        self, 
        structure_summary: Dict,
        additional_context: Optional[str] = None
    ) -> str:
        """
        Build the prompt for LLM analysis.
        
        Args:
            structure_summary: Folder structure data
            additional_context: Optional additional context
            
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
            
            # Convert structure to readable format with error handling
            # Convert Path objects to strings for JSON serialization
            try:
                serializable_structure = self._make_json_serializable(structure_summary)
                structure_json = json.dumps(serializable_structure, indent=2)
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
