# JellyRancher Common Pitfalls & Solutions

**Date:** November 12, 2025

---

## Pitfalls to Avoid

### 1. ❌ DON'T Commit .venv/ to Git

**Problem:** Your `.git/` folder balloons to 800MB+

**Solution:**
```bash
# Add to .gitignore
.venv/
venv/
env/
.env/
```

**Fix existing repo:**
```bash
git rm -r --cached .venv/
git commit -m "Remove .venv from tracking"
```

---

### 2. ❌ DON'T Nest Sub-Projects

**Problem:** CodeCop and RavenMaven nested inside JellyRancher causes duplication

**Bad:**
```
JellyRancher/
  ├─ CodeCop/          # ❌ Nested
  └─ RavenMaven/       # ❌ Nested
```

**Good:**
```
Projects/
  ├─ JellyRancher/        # ✅ Separate
  ├─ CodeCop/          # ✅ Separate
  └─ RavenMaven/       # ✅ Separate
```

**Already nested?** Move to `V:\JellyRancher_Archive\`

---

### 3. ❌ DON'T Create Unnecessary Cache Directories

**Problem:** Multiple cache instances eating 500MB+ total

**Solution:** Plan your caching strategy upfront

**Fix:** Archive duplicates to `V:\JellyRancher_Archive\`

---

### 4. ❌ DON'T Archive Inside Working Directory

**Problem:** `archive/` folder inside project keeps growing

**Bad:**
```
JellyRancher/
  └─ archive/          # ❌ Inside project
      ├─ old_code/
      └─ backups/
```

**Good:**
```
V:/JellyRancher_Archive/  # ✅ External drive
  └─ 2025-11-12_pre-pyqt6/
```

**Why:** Keeps working directory clean, archives can be on external storage

---

### 5. ❌ DON'T Skip Dry-Run Testing

**Problem:** Execute file operations without previewing, cause irreversible damage

**Solution:** ALWAYS test with dry-run first
```python
def reorganize_files(action_plan, dry_run=True):
    if dry_run:
        print("DRY RUN - No files will be modified")
        for action in action_plan:
            print(f"Would move: {action.source} → {action.dest}")
        return
    
    # Actual execution only if dry_run=False
    execute_plan(action_plan)
```

**Rule:** User must explicitly approve AND disable dry-run mode

---

### 6. ❌ DON'T Ignore Rate Limits

**Problem:** Hammer APIs without rate limiting, get IP banned

**TMDB:** 40 requests per 10 seconds  
**TVDB:** Check current limits  
**OpenSubtitles:** Check current limits

**Solution:** Use decorators
```python
from tenacity import retry, stop_after_attempt, wait_exponential
from ratelimit import limits, sleep_and_retry

@sleep_and_retry
@limits(calls=40, period=10)  # Enforce limit
@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=60)
)
def query_tmdb_safe(movie_name):
    # Your API call
    pass
```

---

### 7. ❌ DON'T Move Files Without MD5 Verification

**Problem:** File corruption during move goes undetected

**Solution:** Always verify
```python
import hashlib
import shutil

def move_file_safe(source, dest):
    # Hash before
    md5_before = md5_hash_file(source)
    
    # Move
    shutil.move(source, dest)
    
    # Hash after
    md5_after = md5_hash_file(dest)
    
    # Verify
    if md5_before != md5_after:
        raise Exception(f"File corrupted during move: {source}")
    
    return md5_before
```

---

### 8. ❌ DON'T Modify Source Files Before User Approval

**Problem:** User rejects plan AFTER files have been modified

**Solution:** Two-phase approach
1. **Planning Phase:** Read-only operations, build action plan
2. **Execution Phase:** Only after user approval

```python
# Phase 1: Planning (read-only)
action_plan = generate_action_plan(files)
display_to_user(action_plan)

# Phase 2: Execution (only if approved)
if user_approved():
    execute_plan(action_plan)
```

---

### 9. ❌ DON'T Use String Paths

**Problem:** Path manipulation with strings is error-prone

**Bad:**
```python
path = '/folder/file.mkv'
new_path = path.replace('/folder/', '/new_folder/')  # ❌ Fragile
```

**Good:**
```python
from pathlib import Path

path = Path('/folder/file.mkv')
new_path = Path('/new_folder') / path.name  # ✅ Robust
```

**Why:** `pathlib` handles cross-platform paths, normalization, etc.

---

### 10. ❌ DON'T Load Entire Files into Memory

**Problem:** Hashing 50GB files causes memory overflow

**Bad:**
```python
with open('huge_file.mkv', 'rb') as f:
    data = f.read()  # ❌ Loads entire file
    md5 = hashlib.md5(data).hexdigest()
```

**Good:**
```python
def md5_hash_file(filepath, chunk_size=8192):
    md5 = hashlib.md5()
    with open(filepath, 'rb') as f:
        while chunk := f.read(chunk_size):  # ✅ Chunked
            md5.update(chunk)
    return md5.hexdigest()
```

---

### 11. ❌ DON'T Forget to Close Database Connections

**Problem:** SQLite database locks preventing access

**Bad:**
```python
conn = sqlite3.connect('db.sqlite')
cursor = conn.cursor()
cursor.execute('SELECT * FROM table')
# ❌ Never closed
```

**Good:**
```python
with sqlite3.connect('db.sqlite') as conn:
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM table')
    # ✅ Auto-closes on exit
```

---

### 12. ❌ DON'T Use os.path with PyQt

**Problem:** PyQt uses Qt path separators, os.path uses OS-specific

**Bad:**
```python
import os
path = os.path.join('folder', 'file.mkv')  # ❌ Mixed separators
```

**Good:**
```python
from pathlib import Path

path = Path('folder') / 'file.mkv'  # ✅ Always works
```

**Or use Qt:**
```python
from PyQt6.QtCore import QDir

path = QDir.cleanPath('folder/file.mkv')  # ✅ Qt-native
```

---

### 13. ❌ DON'T Block the GUI Thread

**Problem:** API calls freeze the entire application

**Bad:**
```python
def on_button_click():
    # ❌ Blocks GUI for minutes
    results = query_tmdb_for_1000_movies()
    display_results(results)
```

**Good:**
```python
from PyQt6.QtCore import QThread, pyqtSignal

class APIWorker(QThread):
    finished = pyqtSignal(list)
    
    def run(self):
        results = query_tmdb_for_1000_movies()
        self.finished.emit(results)

def on_button_click():
    # ✅ Background thread
    worker = APIWorker()
    worker.finished.connect(display_results)
    worker.start()
```

---

### 14. ❌ DON'T Use Permanent Deletion

**Problem:** `os.remove()` is irreversible

**Bad:**
```python
import os
os.remove('file.mkv')  # ❌ Gone forever
```

**Good:**
```python
from send2trash import send2trash

send2trash('file.mkv')  # ✅ Goes to recycle bin
```

**Why:** Users can recover from mistakes

---

### 15. ❌ DON'T Ignore Subtitle Types

**Problem:** Treating regular and forced subtitles the same

**Regular Subtitles:** Full dialogue transcription  
**Forced Subtitles:** Only foreign language parts (Klingon in Star Trek, etc.)

**Solution:** Detect and handle separately
```python
# Check ffprobe output
for sub in subtitle_streams:
    forced = sub.get('disposition', {}).get('forced', 0)
    if forced:
        # Download/handle forced subs
        pass
    else:
        # Download/handle regular subs
        pass
```

**Jellyfin naming:**
- Regular: `movie.en.srt`
- Forced: `movie.en.forced.srt`

---

## Quick Fixes for Common Errors

### Error: "ModuleNotFoundError: No module named 'PyQt5'"

**Fix:** You migrated to PyQt6 but imports still say PyQt5
```python
# Change:
from PyQt5.QtWidgets import ...  # ❌
# To:
from PyQt6.QtWidgets import ...  # ✅
```

---

### Error: "AttributeError: 'Qt' object has no attribute 'AlignCenter'"

**Fix:** PyQt6 uses enum namespaces
```python
# Change:
Qt.AlignCenter  # ❌ PyQt5 style
# To:
Qt.AlignmentFlag.AlignCenter  # ✅ PyQt6 style
```

---

### Error: "FileNotFoundError: [Errno 2] No such file or directory: '/path'"

**Fix:** Path doesn't exist - create parent directories
```python
from pathlib import Path

dest = Path('/path/to/file.mkv')
dest.parent.mkdir(parents=True, exist_ok=True)  # Create parents
shutil.move(source, dest)
```

---

### Error: "sqlite3.OperationalError: database is locked"

**Fix:** Close previous connection or use context manager
```python
# Use with statement:
with sqlite3.connect('db.sqlite') as conn:
    # Operations here
    pass  # Auto-closes
```

---

### Error: "requests.exceptions.HTTPError: 429 Too Many Requests"

**Fix:** You exceeded rate limit
```python
# Add rate limiting:
from ratelimit import limits, sleep_and_retry

@sleep_and_retry
@limits(calls=40, period=10)
def query_api():
    # Will automatically wait if limit exceeded
    pass
```

---

### Error: "UnicodeDecodeError: 'charmap' codec can't decode byte"

**Fix:** Use UTF-8 encoding explicitly
```python
# Change:
with open('file.txt', 'r') as f:  # ❌ Uses system default
# To:
with open('file.txt', 'r', encoding='utf-8') as f:  # ✅
```

---

## Success Indicators

You're on the right track when:

✅ `.git/` folder is < 50MB  
✅ `.venv/` is in `.gitignore`  
✅ Zero file duplicates (run consolidation audit)  
✅ Dry-run mode works before execution  
✅ API calls respect rate limits  
✅ MD5 verification on all moves  
✅ Transaction logs exist for rollback  
✅ GUI doesn't freeze during operations  
✅ Tests pass without modifying real files  

---

## Emergency Rollback

If something goes wrong during execution:

```python
# Read transaction log in reverse
with sqlite3.connect('transaction_log.db') as conn:
    cursor = conn.cursor()
    cursor.execute('''
        SELECT source_path, destination_path, source_md5
        FROM transactions
        WHERE completed = 1
        ORDER BY timestamp DESC
    ''')
    
    for source, dest, md5 in cursor:
        # Reverse the operation
        shutil.move(dest, source)
        
        # Verify
        if md5_hash_file(source) != md5:
            print(f"WARNING: MD5 mismatch for {source}")
```

---

**Remember:** Small, tested increments beat grand designs that collapse.
