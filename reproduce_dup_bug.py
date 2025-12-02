
import sys
import os
from pathlib import Path
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.getcwd())

from scripts.ui.jellyfin_cleanup_view import ValidationWorker

def test_duplicate_detection_logic():
    print("Testing duplicate detection logic...")
    
    # Mock results simulating a case-sensitive duplicate scenario
    # Item 1: Correct case, exists -> VALID
    # Item 2: Wrong case, does not exist (on case-sensitive FS) -> MISSING
    
    results = [
        {
            'jellyfin_id': '1',
            'title': 'Movie',
            'path': '/media/movies/Movie.mkv',
            'status': 'VALID',
            'issue': ''
        },
        {
            'jellyfin_id': '2',
            'title': 'Movie',
            'path': '/media/movies/movie.mkv', # Wrong case
            'status': 'MISSING', # Would be MISSING if file system is case-sensitive
            'issue': 'File does not exist'
        }
    ]
    
    # Instantiate worker (we only need the method)
    worker = ValidationWorker(MagicMock(), [])
    
    # Run detection
    worker._detect_duplicates(results)
    
    # Check results
    duplicates_found = 0
    for res in results:
        if res['status'] == 'DUPLICATE':
            duplicates_found += 1
            print(f"Found duplicate: {res['path']} ({res['issue']})")
            
    if duplicates_found == 0:
        print("FAIL: No duplicates detected! The logic ignored the MISSING item.")
    elif duplicates_found == 2:
        print("SUCCESS: Both items marked as duplicates.")
    else:
        print(f"PARTIAL: Found {duplicates_found} duplicates.")

if __name__ == "__main__":
    test_duplicate_detection_logic()
