#!/usr/bin/env python3
"""
Quick test for the analyze_batch_queue_structure fix
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from pathlib import Path
from batch_queue_processor import BatchQueueProcessor, BatchQueueItem

# Create a test batch queue processor
processor = BatchQueueProcessor()

# Create a test file list
test_list_path = Path("test_list.txt")
with open(test_list_path, 'w') as f:
    f.write("C:\\test\\file1.txt\n")
    f.write("C:\\test\\file2.txt\n")

# Add to queue
item = BatchQueueItem(test_list_path, "test_batch")
queue.add_batch(item)

print(f"Queue has {len(queue.queue)} items")
print(f"First item file_list_path: {queue.queue[0].file_list_path}")
print(f"First item name: {queue.queue[0].name}")

# Test accessing attributes (this should work now)
for batch in queue.queue:
    file_list_path = batch.file_list_path  # This should work
    print(f"Successfully accessed file_list_path: {file_list_path}")

# Clean up
test_list_path.unlink()
print("Test completed successfully!")