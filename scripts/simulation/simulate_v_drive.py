#!/usr/bin/env python3
"""
V: Drive Analysis Simulation

Runs a non-destructive analysis on the V: drive to simulate a full-library organization.
Excludes known non-media folders (Games, Code, System).
"""

import sys
import logging
import json
from pathlib import Path
from datetime import datetime

# Add parent directory to path to allow imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from scripts.core.file_scanner import FileScanner
from scripts.media.regex_structure_analyzer import RegexStructureAnalyzer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('v_drive_simulation.log', encoding='utf-8')
    ]
)
logger = logging.getLogger("Simulation")

def main():
    start_time = datetime.now()
    logger.info("Starting V: Drive Analysis Simulation")
    
    # Define exclusions
    exclusions = {
        Path("V:/Bloodborne [DODI Repack]"),
        Path("V:/Crysis.Remastered.Trilogy.GOG-InsaneRamZes"),
        Path("V:/Cyberpunk.2077.GOG-InsaneRamZes"),
        Path("V:/JellyRancher"),
        Path("V:/Autogen"),
        Path("V:/BookmarkRancher"),
        Path("V:/SCRIPTPOCALYPTO"),
        Path("V:/Anemone"),
        Path("V:/System Volume Information"),
        Path("V:/$RECYCLE.BIN"),
        Path("V:/Config.Msi"),
        Path("V:/msdownld.tmp")
    }
    
    # Initialize Scanner
    logger.info("Initializing FileScanner...")
    scanner = FileScanner(
        exclude_paths=exclusions,
        include_subtitles=True,
        include_metadata=True,
        progress_callback=lambda msg, cur, tot: print(f"\r{msg} ({cur} files)", end="") if cur % 100 == 0 else None
    )
    
    # Scan V: Drive
    scan_root = Path("V:/")
    logger.info(f"Scanning {scan_root} (excluding {len(exclusions)} folders)...")
    
    try:
        file_records = scanner.scan_folder(scan_root, recursive=True)
        print() # Newline after progress
        logger.info(f"Scan complete. Found {len(file_records)} files.")
    except Exception as e:
        logger.error(f"Scan failed: {e}", exc_info=True)
        return
    
    # Run Analysis
    logger.info("Running RegexStructureAnalyzer...")
    analyzer = RegexStructureAnalyzer(logger_instance=logger)
    
    try:
        result = analyzer.analyze_structure(
            file_records,
            base_output_path=Path("V:/JellyRancher_Organized_Simulation")
        )
        
        # Save results
        output_file = Path("data/simulation_results.json")
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, default=str)
            
        logger.info(f"Analysis complete. Results saved to {output_file}")
        
        # Print Summary
        detected_media = result.get('detected_media', [])
        movies = [m for m in detected_media if m['type'] == 'movie']
        shows = [m for m in detected_media if m['type'] == 'tv_show']
        
        print("\n" + "="*60)
        print("SIMULATION RESULTS SUMMARY")
        print("="*60)
        print(f"Total Files Scanned: {len(file_records)}")
        print(f"Total Media Detected: {len(detected_media)}")
        print(f"  - Movies: {len(movies)}")
        print(f"  - TV Shows: {len(shows)}")
        print(f"  - Other: {len(detected_media) - len(movies) - len(shows)}")
        print("-" * 60)
        
        print("\nSample Detected Movies:")
        for m in movies[:5]:
            print(f"  - {m['title']} ({m.get('year_estimate', 'Unknown')})")
            
        print("\nSample Detected TV Shows:")
        for s in shows[:5]:
            print(f"  - {s['title']} ({s.get('seasons_detected', 0)} seasons)")
            
        print("\nSample Proposed Changes:")
        changes = result.get('reorganization_plan', {}).get('folder_changes', [])
        for c in changes[:5]:
            print(f"  {c['action'].upper()}: {Path(c['current_path']).name} -> {Path(c['proposed_path']).name}")
            
        print("\n" + "="*60)
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        
    duration = datetime.now() - start_time
    logger.info(f"Simulation completed in {duration}")

if __name__ == "__main__":
    main()
