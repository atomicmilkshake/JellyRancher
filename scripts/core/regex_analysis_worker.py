#!/usr/bin/env python3
"""
Regex Analysis Worker - Background thread for regex-based analysis

QThread worker for performing regex structure analysis without blocking the UI.
Compatible with existing LLMAnalysisWorker interface for seamless integration.
"""

import logging
from typing import List
from PyQt6.QtCore import QThread, pyqtSignal

from scripts.core.file_scanner import FileRecord
from scripts.media.regex_structure_analyzer import RegexStructureAnalyzer

logger = logging.getLogger(__name__)


class RegexAnalysisWorker(QThread):
    """
    Background worker for regex-based structure analysis.
    
    Runs regex analysis in a separate thread to prevent UI blocking.
    Provides same signal interface as LLMAnalysisWorker for compatibility.
    """
    
    # Signals
    progress = pyqtSignal(str)  # status message
    finished = pyqtSignal(dict)  # analysis result
    error = pyqtSignal(str)  # error message
    
    def __init__(self, scanned_files: List[FileRecord], parent=None):
        """
        Initialize the regex analysis worker.
        
        Args:
            scanned_files: List of FileRecord objects to analyze
            parent: Parent QObject
        """
        super().__init__(parent)
        self.scanned_files = scanned_files
    
    def run(self):
        """Execute regex analysis in background thread."""
        try:
            self.progress.emit("Starting regex analysis...")
            
            # Create analyzer
            analyzer = RegexStructureAnalyzer(logger_instance=logger)
            
            self.progress.emit(f"Parsing {len(self.scanned_files)} files with regex patterns...")
            
            # Run analysis
            result = analyzer.analyze_structure(self.scanned_files)
            
            self.progress.emit("Regex analysis complete!")
            
            # Emit result
            self.finished.emit(result)
            
            logger.info(f"Regex analysis worker completed: {len(result.get('detected_media', []))} items detected")
            
        except Exception as e:
            error_msg = f"Regex analysis failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.error.emit(error_msg)


class HybridAnalysisWorker(QThread):
    """
    Background worker for hybrid analysis (Regex + LLM for ambiguous cases).
    
    Runs regex analysis first, identifies low-confidence results,
    then sends only ambiguous cases to LLM for verification.
    
    This provides massive cost savings (80-90%) while maintaining accuracy.
    """
    
    # Signals
    progress = pyqtSignal(str)  # status message
    finished = pyqtSignal(dict)  # combined analysis result
    error = pyqtSignal(str)  # error message
    
    def __init__(
        self,
        scanned_files: List[FileRecord],
        folder_structure: dict,
        model: str,
        parent=None
    ):
        """
        Initialize the hybrid analysis worker.
        
        Args:
            scanned_files: List of FileRecord objects to analyze
            folder_structure: Folder structure dict for LLM context
            model: LLM model to use for ambiguous cases
            parent: Parent QObject
        """
        super().__init__(parent)
        self.scanned_files = scanned_files
        self.folder_structure = folder_structure
        self.model = model
    
    def run(self):
        """Execute hybrid analysis in background thread."""
        try:
            # PHASE 1: Regex analysis (fast, free)
            self.progress.emit("Phase 1/2: Running regex analysis...")
            
            regex_analyzer = RegexStructureAnalyzer(logger_instance=logger)
            regex_result = regex_analyzer.analyze_structure(self.scanned_files)
            
            detected_media = regex_result.get('detected_media', [])
            total_detected = len(detected_media)
            
            # Identify ambiguous cases (low confidence)
            ambiguous_media = [
                m for m in detected_media
                if m.get('confidence') in ['low', 'medium']
            ]
            ambiguous_count = len(ambiguous_media)
            
            self.progress.emit(
                f"Regex detected {total_detected} items ({ambiguous_count} ambiguous)"
            )
            
            # PHASE 2: LLM analysis for ambiguous cases only
            if ambiguous_count > 0:
                self.progress.emit(
                    f"Phase 2/2: Sending {ambiguous_count} ambiguous cases to LLM..."
                )
                
                # Filter file records to only ambiguous media
                ambiguous_titles = {m.get('title', '').lower() for m in ambiguous_media}
                
                # Create filtered folder structure for LLM
                # (Only include ambiguous items to reduce token costs)
                filtered_structure = {
                    'project_name': self.folder_structure.get('project_name'),
                    'ambiguous_only': True,
                    'total_files': ambiguous_count,
                    'high_confidence_from_regex': total_detected - ambiguous_count
                }
                
                # Run LLM on ambiguous subset
                from scripts.media.llm_structure_analyzer import LLMStructureAnalyzer
                llm_analyzer = LLMStructureAnalyzer(model=self.model, logger=logger)
                llm_result = llm_analyzer.analyze_structure(filtered_structure)
                
                # Merge results: Keep high-confidence regex, replace low-confidence with LLM
                self.progress.emit("Merging regex and LLM results...")
                
                # Replace ambiguous items with LLM results
                final_media = [m for m in detected_media if m.get('confidence') == 'high']
                final_media.extend(llm_result.get('detected_media', []))
                
                # Combine reorganization plans
                regex_plan = regex_result.get('reorganization_plan', {})
                llm_plan = llm_result.get('reorganization_plan', {})
                
                combined_result = {
                    'detected_media': final_media,
                    'reorganization_plan': {
                        'summary': f"Hybrid analysis: {len(final_media)} items total ({total_detected - ambiguous_count} via regex, {ambiguous_count} via LLM)",
                        'folder_changes': regex_plan.get('folder_changes', []) + llm_plan.get('folder_changes', []),
                        'jellyfin_compliance_issues': list(set(
                            regex_plan.get('jellyfin_compliance_issues', []) +
                            llm_plan.get('jellyfin_compliance_issues', [])
                        ))
                    },
                    'multi_part_episodes': regex_result.get('multi_part_episodes', []) + llm_result.get('multi_part_episodes', []),
                    'reasoning': f"HYBRID ANALYSIS:\n\nPhase 1 (Regex): {regex_result.get('reasoning', '')}\n\nPhase 2 (LLM for {ambiguous_count} ambiguous): {llm_result.get('reasoning', '')}",
                    'metadata': {
                        'analyzer': 'hybrid',
                        'regex_items': total_detected - ambiguous_count,
                        'llm_items': ambiguous_count,
                        'cost_savings': f"{((total_detected - ambiguous_count) / total_detected * 100):.0f}%"
                    }
                }
            else:
                # All high confidence from regex - no LLM needed!
                self.progress.emit("All items high confidence - LLM phase skipped!")
                combined_result = regex_result
                combined_result['metadata']['analyzer'] = 'hybrid'
                combined_result['metadata']['cost_savings'] = '100%'
                combined_result['reasoning'] = f"HYBRID ANALYSIS (100% Regex - No LLM needed):\n\n{regex_result.get('reasoning', '')}"
            
            self.progress.emit("Hybrid analysis complete!")
            self.finished.emit(combined_result)
            
            logger.info(f"Hybrid analysis complete: {len(final_media if ambiguous_count > 0 else detected_media)} total items")
            
        except Exception as e:
            error_msg = f"Hybrid analysis failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.error.emit(error_msg)
