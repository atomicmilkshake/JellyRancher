#!/usr/bin/env python3
"""Quick test to check Round-Up database paths."""
from pathlib import Path
from scripts.core.roundup_manager import RoundUpManager

rm = RoundUpManager()
roundups = rm.list_all()
print(f"Found {len(roundups)} roundups:")
for r in roundups:
    db_path = r.path / "data.db"
    print(f"  - {r.name}")
    print(f"    Path: {r.path}")
    print(f"    DB: {db_path}")
    print(f"    DB exists: {db_path.exists()}")
    
    if db_path.exists():
        import sqlite3
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM scan_files')
        count = cursor.fetchone()[0]
        print(f"    scan_files count: {count}")
        conn.close()

