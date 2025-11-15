import os
from pathlib import Path

def cleanup_empty_dirs():
    base_path = Path("E:/MOVIES")
    removed = 0
    
    for dirpath in sorted(base_path.rglob('*'), key=lambda x: len(x.parts), reverse=True):
        if dirpath.is_dir():
            try:
                if not any(dirpath.iterdir()):
                    dirpath.rmdir()
                    removed += 1
                    print(f"Removed empty directory: {dirpath}")
            except:
                pass
    
    print(f"Cleanup complete: {removed} empty directories removed")

if __name__ == "__main__":
    cleanup_empty_dirs()
