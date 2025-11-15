"""
Batch Queue Processor for RavenMaven
Handles sequential processing of multiple file lists as separate batches.
"""

import os
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Callable, Optional
from datetime import datetime


class BatchQueueItem:
    """Represents a single file list in the processing queue."""
    
    def __init__(self, file_list_path: Path, name: Optional[str] = None, custom_prompt: Optional[str] = None):
        self.file_list_path = Path(file_list_path)
        self.name = name or self.file_list_path.stem
        self.status = "pending"  # pending, processing, completed, failed
        self.file_count = 0
        self.actions_count = 0
        self.output_dir = None
        self.error_message = None
        self.started_at = None
        self.completed_at = None
        self.custom_prompt = custom_prompt  # Custom prompt to prepend to file list
        
        # Calculate file count
        if self.file_list_path.exists():
            with open(self.file_list_path, 'r', encoding='utf-8') as f:
                self.file_count = sum(1 for line in f if line.strip())
    
    def __str__(self):
        status_icon = {
            "pending": "⏳",
            "processing": "🔄",
            "completed": "✅",
            "failed": "❌"
        }.get(self.status, "❓")
        return f"{status_icon} {self.name} ({self.file_count} files)"
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            "file_list_path": str(self.file_list_path),
            "name": self.name,
            "status": self.status,
            "file_count": self.file_count,
            "actions_count": self.actions_count,
            "output_dir": str(self.output_dir) if self.output_dir else None,
            "error_message": self.error_message,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "custom_prompt": self.custom_prompt
        }


class BatchQueueProcessor:
    """Manages and processes a queue of file lists as separate batches."""
    
    def __init__(self, logger=None):
        self.queue: List[BatchQueueItem] = []
        self.logger = logger
        self.current_batch: Optional[BatchQueueItem] = None
        self.total_files_processed = 0
        self.total_actions_generated = 0
        
    def add_to_queue(self, file_list_paths: List[Path], names: Optional[List[str]] = None, 
                     custom_prompts: Optional[List[str]] = None):
        """Add one or more file lists to the processing queue."""
        if names is None:
            names = [None] * len(file_list_paths)
        if custom_prompts is None:
            custom_prompts = [None] * len(file_list_paths)
        
        for path, name, prompt in zip(file_list_paths, names, custom_prompts):
            if not Path(path).exists():
                if self.logger:
                    self.logger.warning(f"File list not found: {path}")
                continue
            
            item = BatchQueueItem(path, name, prompt)
            self.queue.append(item)
            if self.logger:
                self.logger.info(f"Added to queue: {item}")
    
    def remove_from_queue(self, index: int):
        """Remove an item from the queue by index."""
        if 0 <= index < len(self.queue):
            removed = self.queue.pop(index)
            if self.logger:
                self.logger.info(f"Removed from queue: {removed}")
            return removed
        return None
    
    def clear_queue(self):
        """Clear all items from the queue."""
        count = len(self.queue)
        self.queue.clear()
        if self.logger:
            self.logger.info(f"Cleared queue ({count} items)")
    
    def get_queue_summary(self) -> Dict:
        """Get summary statistics for the queue."""
        return {
            "total_batches": len(self.queue),
            "total_files": sum(item.file_count for item in self.queue),
            "pending": sum(1 for item in self.queue if item.status == "pending"),
            "processing": sum(1 for item in self.queue if item.status == "processing"),
            "completed": sum(1 for item in self.queue if item.status == "completed"),
            "failed": sum(1 for item in self.queue if item.status == "failed")
        }
    
    def process_queue(self, 
                     process_callback: Callable[[BatchQueueItem], Dict],
                     progress_callback: Optional[Callable[[int, int, BatchQueueItem], None]] = None,
                     stop_on_error: bool = False) -> List[Dict]:
        """
        Process all items in the queue sequentially.
        
        Args:
            process_callback: Function that processes a single BatchQueueItem and returns results dict
            progress_callback: Optional function called after each batch with (current, total, item)
            stop_on_error: If True, stop processing queue on first error
            
        Returns:
            List of result dictionaries from each batch
        """
        results = []
        total = len(self.queue)
        
        if self.logger:
            self.logger.info(f"Starting batch queue processing: {total} batches")
        
        for index, item in enumerate(self.queue):
            self.current_batch = item
            item.status = "processing"
            item.started_at = datetime.now()
            
            if self.logger:
                self.logger.info(f"Processing batch {index + 1}/{total}: {item.name}")
            
            try:
                # Call the processing callback
                result = process_callback(item)
                
                # Update item status
                item.status = "completed"
                item.completed_at = datetime.now()
                item.actions_count = result.get("actions_count", 0)
                item.output_dir = result.get("output_dir")
                
                # Update totals
                self.total_files_processed += item.file_count
                self.total_actions_generated += item.actions_count
                
                results.append(result)
                
                if self.logger:
                    self.logger.info(f"Completed batch {index + 1}/{total}: {item.actions_count} actions")
                
            except Exception as e:
                item.status = "failed"
                item.completed_at = datetime.now()
                item.error_message = str(e)
                
                if self.logger:
                    self.logger.error(f"Failed batch {index + 1}/{total}: {e}")
                
                results.append({"error": str(e), "batch": item.name})
                
                if stop_on_error:
                    if self.logger:
                        self.logger.error("Stopping queue processing due to error")
                    break
            
            finally:
                # Call progress callback
                if progress_callback:
                    progress_callback(index + 1, total, item)
        
        self.current_batch = None
        
        if self.logger:
            self.logger.info(f"Batch queue processing complete: {len(results)} batches processed")
        
        return results
    
    def generate_report(self, output_dir: Path = None) -> str:
        """Generate a summary report of the batch queue processing."""
        summary = self.get_queue_summary()
        
        report_lines = [
            "=" * 80,
            "BATCH QUEUE PROCESSING REPORT",
            "=" * 80,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "SUMMARY",
            "-" * 80,
            f"Total Batches:       {summary['total_batches']}",
            f"Total Files:         {summary['total_files']}",
            f"Completed Batches:   {summary['completed']}",
            f"Failed Batches:      {summary['failed']}",
            f"Pending Batches:     {summary['pending']}",
            f"Total Actions:       {self.total_actions_generated}",
            "",
            "BATCH DETAILS",
            "-" * 80
        ]
        
        for index, item in enumerate(self.queue, 1):
            duration = ""
            if item.started_at and item.completed_at:
                delta = item.completed_at - item.started_at
                duration = f" ({delta.total_seconds():.1f}s)"
            
            report_lines.extend([
                f"{index}. {item.name}",
                f"   Status: {item.status}{duration}",
                f"   Files: {item.file_count}",
                f"   Actions: {item.actions_count}",
                f"   Output: {item.output_dir or 'N/A'}"
            ])
            
            if item.error_message:
                report_lines.append(f"   Error: {item.error_message}")
            
            report_lines.append("")
        
        report_lines.append("=" * 80)
        
        report_text = "\n".join(report_lines)
        
        # Save report to file if output_dir provided
        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(exist_ok=True)
            report_file = output_dir / f"batch_queue_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report_text)
            if self.logger:
                self.logger.info(f"Batch queue report saved: {report_file}")
        
        return report_text
    
    def save_queue_state(self, filepath: Path):
        """Save the current queue state to a JSON file."""
        state = {
            "saved_at": datetime.now().isoformat(),
            "queue": [item.to_dict() for item in self.queue],
            "total_files_processed": self.total_files_processed,
            "total_actions_generated": self.total_actions_generated
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2)
        
        if self.logger:
            self.logger.info(f"Queue state saved: {filepath}")
    
    def load_queue_state(self, filepath: Path):
        """Load a previously saved queue state from a JSON file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            state = json.load(f)
        
        self.queue.clear()
        for item_data in state.get("queue", []):
            item = BatchQueueItem(Path(item_data["file_list_path"]), 
                                item_data.get("name"),
                                item_data.get("custom_prompt"))
            item.status = item_data.get("status", "pending")
            item.file_count = item_data.get("file_count", 0)
            item.actions_count = item_data.get("actions_count", 0)
            item.output_dir = Path(item_data["output_dir"]) if item_data.get("output_dir") else None
            item.error_message = item_data.get("error_message")
            if item_data.get("started_at"):
                item.started_at = datetime.fromisoformat(item_data["started_at"])
            if item_data.get("completed_at"):
                item.completed_at = datetime.fromisoformat(item_data["completed_at"])
            self.queue.append(item)
        
        self.total_files_processed = state.get("total_files_processed", 0)
        self.total_actions_generated = state.get("total_actions_generated", 0)
        
        if self.logger:
            self.logger.info(f"Queue state loaded: {filepath} ({len(self.queue)} batches)")
