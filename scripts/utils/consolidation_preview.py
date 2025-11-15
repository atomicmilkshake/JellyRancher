#!/usr/bin/env python3
"""
Preview the consolidation without making changes.
Useful for reviewing exactly what will be moved and where.
"""

import sys
from pathlib import Path

# Add _common to path
sys.path.insert(0, str(Path(__file__).parent / "_common"))

# Now run consolidation in dry-run mode
from consolidation_phase1 import main

if __name__ == "__main__":
    # Override sys.argv to force dry-run
    sys.argv = [sys.argv[0], "--dry-run", "--no-confirm"]
    main()
