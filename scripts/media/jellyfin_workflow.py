#!/usr/bin/env python3
"""
Jellyfin Media Organization Workflow - Complete Pipeline

Orchestrates the complete workflow from folder scanning to reorganization planning:

Step 1-2: Scan folders and generate structure summary (FolderStructureScanner)
Step 3:   Analyze structure with LLM reasoning (LLMStructureAnalyzer)
Step 4:   Lookup accurate metadata (MediaMetadataLookup)
Step 4:   Generate NFO files for multi-part episodes (NFOGenerator)

Outputs:
- Complete reorganization plan
- Canonical metadata database
- NFO files for special cases
- Dry-run report for safe preview
"""

import sys
import json
import logging
from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime
import argparse

# Import workflow modules
from folder_structure_scanner import FolderStructureScanner
sys.path.append(str(Path(__file__).parent.parent / 'ai'))
from llm_structure_analyzer import LLMStructureAnalyzer
from media_metadata_lookup import MediaMetadataLookup
from nfo_generator import NFOGenerator


class JellyfinWorkflow:
    """
    Complete workflow orchestrator for Jellyfin media organization.
    """
    
    def __init__(
        self,
        llm_model: str = "Grok-4.1-Fast-Reasoning",
        output_dir: str = "data/workflow_output",
        dry_run: bool = True,
        log_level: str = "INFO"
    ):
        """
        Initialize workflow orchestrator.
        
        Args:
            llm_model: LLM model to use for structure analysis
            output_dir: Directory for all output files
            dry_run: If True, don't make actual file changes
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        """
        self.llm_model = llm_model
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.dry_run = dry_run
        
        # Set up logging
        self.logger = self._setup_logger(log_level)
        
        # Timestamp for this workflow run
        self.run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Initialize components
        self.scanner = None
        self.llm_analyzer = None
        self.metadata_lookup = None
        self.nfo_generator = None
        
        self.logger.info("="*80)
        self.logger.info("JELLYFIN MEDIA ORGANIZATION WORKFLOW")
        self.logger.info("="*80)
        self.logger.info(f"LLM Model: {llm_model}")
        self.logger.info(f"Output Directory: {self.output_dir}")
        self.logger.info(f"Dry Run: {dry_run}")
        self.logger.info(f"Run ID: {self.run_timestamp}")
        self.logger.info("="*80)
    
    def _setup_logger(self, log_level: str) -> logging.Logger:
        """Set up comprehensive logger."""
        logger = logging.getLogger("JellyfinWorkflow")
        logger.setLevel(getattr(logging, log_level.upper()))
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, log_level.upper()))
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        # File handler
        log_file = self.output_dir / f"workflow_{self.run_timestamp}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
        return logger
    
    def run_complete_workflow(
        self,
        folders_to_scan: List[str],
        additional_llm_context: Optional[str] = None
    ) -> Dict:
        """
        Run the complete workflow from scan to reorganization plan.
        
        Args:
            folders_to_scan: List of folder paths to scan
            additional_llm_context: Optional additional context for LLM
            
        Returns:
            Dictionary containing all workflow results
        """
        workflow_results = {
            'run_id': self.run_timestamp,
            'folders_scanned': folders_to_scan,
            'dry_run': self.dry_run,
            'steps_completed': []
        }
        
        try:
            # Step 1-2: Scan and summarize folder structure
            self.logger.info("\n" + "="*80)
            self.logger.info("STEP 1-2: SCANNING FOLDER STRUCTURE")
            self.logger.info("="*80)
            
            scan_results = self.step_scan_folders(folders_to_scan)
            workflow_results['scan_results'] = scan_results
            workflow_results['steps_completed'].append('scan')
            
            # Step 3: LLM analysis
            self.logger.info("\n" + "="*80)
            self.logger.info("STEP 3: LLM STRUCTURE ANALYSIS")
            self.logger.info("="*80)
            
            llm_analysis = self.step_llm_analysis(
                scan_results['structure_summary'],
                additional_llm_context
            )
            workflow_results['llm_analysis'] = llm_analysis
            workflow_results['steps_completed'].append('llm_analysis')
            
            # Step 4a: Metadata lookup
            self.logger.info("\n" + "="*80)
            self.logger.info("STEP 4A: METADATA LOOKUP")
            self.logger.info("="*80)
            
            canonical_db = self.step_metadata_lookup(
                llm_analysis['detected_media']
            )
            workflow_results['canonical_database'] = canonical_db
            workflow_results['steps_completed'].append('metadata_lookup')
            
            # Step 4b: Generate NFO files
            self.logger.info("\n" + "="*80)
            self.logger.info("STEP 4B: NFO FILE GENERATION")
            self.logger.info("="*80)
            
            nfo_results = self.step_generate_nfos(
                canonical_db,
                llm_analysis['multi_part_episodes']
            )
            workflow_results['nfo_generation'] = nfo_results
            workflow_results['steps_completed'].append('nfo_generation')
            
            # Generate final reorganization plan
            self.logger.info("\n" + "="*80)
            self.logger.info("STEP 5: GENERATING REORGANIZATION PLAN")
            self.logger.info("="*80)
            
            reorg_plan = self.step_create_reorganization_plan(
                scan_results,
                llm_analysis,
                canonical_db,
                nfo_results
            )
            workflow_results['reorganization_plan'] = reorg_plan
            workflow_results['steps_completed'].append('reorganization_plan')
            
            # Save complete workflow results
            self.save_workflow_results(workflow_results)
            
            # Print summary
            self.print_workflow_summary(workflow_results)
            
            workflow_results['status'] = 'success'
            
        except Exception as e:
            self.logger.error(f"Workflow failed: {e}", exc_info=True)
            workflow_results['status'] = 'error'
            workflow_results['error'] = str(e)
        
        return workflow_results
    
    def step_scan_folders(self, folders: List[str]) -> Dict:
        """Execute Step 1-2: Folder scanning and structure summary."""
        self.scanner = FolderStructureScanner(folders)
        
        self.logger.info(f"Scanning {len(folders)} folder(s)...")
        video_files, structure = self.scanner.scan_all()
        
        self.logger.info("Generating structure summary...")
        structure_summary = self.scanner.generate_structure_summary()
        
        # Save scan results
        file_list_path = self.output_dir / f"scan_file_list_{self.run_timestamp}.txt"
        structure_path = self.output_dir / f"scan_structure_{self.run_timestamp}.json"
        
        self.scanner.save_file_list(str(file_list_path))
        self.scanner.save_structure_summary(str(structure_path))
        
        self.logger.info(f"✓ Found {len(video_files)} video files")
        self.logger.info(f"✓ Scan results saved")
        
        return {
            'video_files': video_files,
            'structure_summary': structure_summary,
            'file_list_path': str(file_list_path),
            'structure_path': str(structure_path)
        }
    
    def step_llm_analysis(
        self, 
        structure_summary: Dict,
        additional_context: Optional[str] = None
    ) -> Dict:
        """Execute Step 3: LLM structure analysis."""
        self.llm_analyzer = LLMStructureAnalyzer(
            model=self.llm_model,
            logger=self.logger
        )
        
        self.logger.info(f"Analyzing structure with {self.llm_model}...")
        analysis = self.llm_analyzer.analyze_structure(
            structure_summary,
            additional_context
        )
        
        # Save analysis results
        analysis_path = self.output_dir / f"llm_analysis_{self.run_timestamp}.json"
        self.llm_analyzer.save_analysis(analysis, str(analysis_path))
        
        self.logger.info(f"✓ Detected {len(analysis.get('detected_media', []))} media items")
        self.logger.info(f"✓ Identified {len(analysis.get('multi_part_episodes', []))} multi-part episodes")
        self.logger.info(f"✓ Analysis saved")
        
        return analysis
    
    def step_metadata_lookup(self, detected_media: List[Dict]) -> Dict:
        """Execute Step 4a: Metadata lookup."""
        self.metadata_lookup = MediaMetadataLookup(logger=self.logger)
        
        self.logger.info(f"Looking up metadata for {len(detected_media)} items...")
        
        canonical_db_path = self.output_dir / f"canonical_metadata_{self.run_timestamp}.json"
        canonical_db = self.metadata_lookup.build_canonical_database(
            detected_media,
            output_path=str(canonical_db_path)
        )
        
        self.logger.info(f"✓ Movies: {len(canonical_db['movies'])}")
        self.logger.info(f"✓ TV Shows: {len(canonical_db['tv_shows'])}")
        self.logger.info(f"✓ Lookup failures: {len(canonical_db['lookup_failures'])}")
        self.logger.info(f"✓ Canonical database saved")
        
        return canonical_db
    
    def step_generate_nfos(
        self,
        canonical_db: Dict,
        multipart_episodes: List[Dict]
    ) -> Dict:
        """Execute Step 4b: NFO file generation."""
        self.nfo_generator = NFOGenerator(logger=self.logger)
        
        if not multipart_episodes:
            self.logger.info("No multi-part episodes to generate NFOs for")
            return {'nfo_files': [], 'count': 0}
        
        self.logger.info(f"Generating NFO files for {len(multipart_episodes)} multi-part episodes...")
        
        nfo_output_dir = self.output_dir / "nfo_files"
        results = self.nfo_generator.generate_nfos_for_multipart_episodes(
            canonical_db=canonical_db,
            multipart_episodes=multipart_episodes,
            output_dir=str(nfo_output_dir),
            dry_run=self.dry_run
        )
        
        success_count = sum(1 for r in results if r['status'] == 'success')
        self.logger.info(f"✓ NFO files generated: {success_count}/{len(results)}")
        
        return {
            'nfo_files': results,
            'count': len(results),
            'success_count': success_count
        }
    
    def step_create_reorganization_plan(
        self,
        scan_results: Dict,
        llm_analysis: Dict,
        canonical_db: Dict,
        nfo_results: Dict
    ) -> Dict:
        """Create final reorganization plan based on all gathered data."""
        self.logger.info("Creating comprehensive reorganization plan...")
        
        plan = {
            'timestamp': datetime.now().isoformat(),
            'run_id': self.run_timestamp,
            'summary': {
                'total_video_files': len(scan_results['video_files']),
                'detected_movies': len([m for m in llm_analysis.get('detected_media', []) if m.get('type') == 'movie']),
                'detected_tv_shows': len([m for m in llm_analysis.get('detected_media', []) if m.get('type') == 'tv_show']),
                'nfo_files_needed': nfo_results['count'],
                'folder_changes_recommended': len(llm_analysis.get('reorganization_plan', {}).get('folder_changes', []))
            },
            'llm_recommendations': llm_analysis.get('reorganization_plan', {}),
            'canonical_metadata': {
                'movies': canonical_db['movies'],
                'tv_shows': canonical_db['tv_shows']
            },
            'nfo_files': nfo_results['nfo_files'],
            'execution_instructions': {
                'dry_run': self.dry_run,
                'steps': [
                    "1. Review the reorganization plan carefully",
                    "2. Verify detected media and metadata accuracy",
                    "3. Place NFO files in appropriate folders",
                    "4. Execute folder reorganization (use dry-run first!)",
                    "5. Scan library in Jellyfin"
                ]
            }
        }
        
        # Save reorganization plan
        plan_path = self.output_dir / f"reorganization_plan_{self.run_timestamp}.json"
        with open(plan_path, 'w', encoding='utf-8') as f:
            json.dump(plan, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"✓ Reorganization plan saved to: {plan_path}")
        
        return plan
    
    def save_workflow_results(self, results: Dict):
        """Save complete workflow results."""
        results_path = self.output_dir / f"workflow_complete_{self.run_timestamp}.json"
        
        with open(results_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"✓ Complete workflow results saved to: {results_path}")
    
    def print_workflow_summary(self, results: Dict):
        """Print a comprehensive workflow summary."""
        self.logger.info("\n" + "="*80)
        self.logger.info("WORKFLOW COMPLETE - SUMMARY")
        self.logger.info("="*80)
        
        if results.get('status') == 'success':
            plan = results.get('reorganization_plan', {})
            summary = plan.get('summary', {})
            
            self.logger.info(f"\n📊 STATISTICS:")
            self.logger.info(f"  Total video files: {summary.get('total_video_files', 0)}")
            self.logger.info(f"  Movies detected: {summary.get('detected_movies', 0)}")
            self.logger.info(f"  TV shows detected: {summary.get('detected_tv_shows', 0)}")
            self.logger.info(f"  Multi-part episodes: {summary.get('nfo_files_needed', 0)}")
            self.logger.info(f"  Folder changes recommended: {summary.get('folder_changes_recommended', 0)}")
            
            self.logger.info(f"\n📁 OUTPUT FILES:")
            self.logger.info(f"  Workflow results: workflow_complete_{self.run_timestamp}.json")
            self.logger.info(f"  Reorganization plan: reorganization_plan_{self.run_timestamp}.json")
            self.logger.info(f"  Canonical metadata: canonical_metadata_{self.run_timestamp}.json")
            self.logger.info(f"  LLM analysis: llm_analysis_{self.run_timestamp}.json")
            self.logger.info(f"  Structure summary: scan_structure_{self.run_timestamp}.json")
            self.logger.info(f"  File list: scan_file_list_{self.run_timestamp}.txt")
            
            self.logger.info(f"\n✅ All files saved to: {self.output_dir}")
            
            if self.dry_run:
                self.logger.info("\n⚠️  DRY RUN MODE: No actual file changes were made")
                self.logger.info("    Review the reorganization plan and run again with --execute to apply changes")
        else:
            self.logger.error(f"\n❌ WORKFLOW FAILED: {results.get('error', 'Unknown error')}")
        
        self.logger.info("\n" + "="*80)


def main():
    """Main entry point for workflow execution."""
    parser = argparse.ArgumentParser(
        description="Jellyfin Media Organization Workflow",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scan and analyze (dry run):
  python jellyfin_workflow.py "V:\\#MEDIA\\TV Shows" "V:\\#MEDIA\\Movies"
  
  # With custom LLM model:
  python jellyfin_workflow.py "V:\\#MEDIA\\TV Shows" --model gpt-4o-reasoning
  
  # Execute actual changes (not dry run):
  python jellyfin_workflow.py "V:\\#MEDIA\\TV Shows" --execute
  
  # With additional context for LLM:
  python jellyfin_workflow.py "V:\\#MEDIA\\TV Shows" --context "Focus on anime shows"
        """
    )
    
    parser.add_argument(
        'folders',
        nargs='+',
        help='Folders to scan (one or more paths)'
    )
    
    parser.add_argument(
        '--model',
        default='Grok-4.1-Fast-Reasoning',
        help='LLM model to use for analysis (default: Grok-4.1-Fast-Reasoning)'
    )
    
    parser.add_argument(
        '--output-dir',
        default='data/workflow_output',
        help='Output directory for all generated files (default: data/workflow_output)'
    )
    
    parser.add_argument(
        '--execute',
        action='store_true',
        help='Execute actual changes (default is dry-run mode)'
    )
    
    parser.add_argument(
        '--context',
        help='Additional context to provide to LLM for analysis'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level (default: INFO)'
    )
    
    args = parser.parse_args()
    
    # Initialize workflow
    workflow = JellyfinWorkflow(
        llm_model=args.model,
        output_dir=args.output_dir,
        dry_run=not args.execute,
        log_level=args.log_level
    )
    
    # Run complete workflow
    results = workflow.run_complete_workflow(
        folders_to_scan=args.folders,
        additional_llm_context=args.context
    )
    
    # Exit with appropriate code
    sys.exit(0 if results.get('status') == 'success' else 1)


if __name__ == "__main__":
    main()
