"""
Media File Utilities

Helper functions for media file operations:
- File hashing (SHA-256)
- Safe file moves with verification
- Windows long path handling
- Path validation

Usage:
    from _common.media_utils import hash_file, safe_move, normalize_windows_path
"""

import hashlib
import shutil
import os
import mmap
import re
import binascii
from pathlib import Path
from typing import Optional, List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import json


def hash_file(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Calculate cryptographic hash of a file.
    
    Args:
        file_path: Path to file
        algorithm: Hash algorithm (default: sha256)
    
    Returns:
        Hash string in format "algorithm:hexdigest"
    
    Example:
        hash_file(Path("movie.mkv"))
        # Returns: "sha256:abc123def456..."
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    hasher = hashlib.new(algorithm)
    
    # Read in chunks to handle large files
    with open(file_path, 'rb') as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    
    return f"{algorithm}:{hasher.hexdigest()}"


def hash_file_crc32(file_path: Path) -> str:
    """
    Calculate CRC32 checksum of a file (fast, non-cryptographic).
    
    Args:
        file_path: Path to file
    
    Returns:
        CRC32 string in format "crc32:hexdigest"
    
    Example:
        hash_file_crc32(Path("movie.mkv"))
        # Returns: "crc32:abc123def"
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    crc = 0
    
    # Read in chunks to handle large files
    with open(file_path, 'rb') as f:
        while chunk := f.read(8192):
            crc = binascii.crc32(chunk, crc)
    
    return f"crc32:{crc:08x}"


def hash_file_fast(file_path: Path, algorithm: str = "sha256", use_mmap: bool = True) -> str:
    """
    Fast cryptographic hash using memory mapping for large files.

    Args:
        file_path: Path to file
        algorithm: Hash algorithm (default: sha256)
        use_mmap: Use memory mapping for faster I/O (default: True)

    Returns:
        Hash string in format "algorithm:hexdigest"
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    file_size = file_path.stat().st_size

    # For small files, use regular reading
    if file_size < 50 * 1024 * 1024:  # 50MB threshold
        return hash_file(file_path, algorithm)

    # For large files, try memory mapping (faster for sequential access)
    if use_mmap:
        try:
            with open(file_path, 'rb') as f:
                # Memory map the file
                with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                    hasher = hashlib.new(algorithm)
                    # Read in larger chunks for better performance
                    chunk_size = 256 * 1024  # 256KB chunks
                    for i in range(0, file_size, chunk_size):
                        chunk = mm[i:i + chunk_size]
                        hasher.update(chunk)
                    return f"{algorithm}:{hasher.hexdigest()}"
        except (OSError, OverflowError):
            # Fallback to regular reading if mmap fails
            pass

    # Fallback: regular chunked reading with larger chunks
    hasher = hashlib.new(algorithm)
    chunk_size = 256 * 1024  # 256KB chunks (larger than original 8KB)

    with open(file_path, 'rb') as f:
        while chunk := f.read(chunk_size):
            hasher.update(chunk)

    return f"{algorithm}:{hasher.hexdigest()}"


def hash_files_parallel(file_paths: List[Path],
                       algorithm: str = "sha256",
                       max_workers: int = 4,
                       use_fast: bool = True) -> dict:
    """
    Hash multiple files in parallel using thread pool.

    Args:
        file_paths: List of file paths to hash
        algorithm: Hash algorithm (default: sha256)
        max_workers: Maximum concurrent threads (default: 4)
        use_fast: Use optimized hashing (default: True)

    Returns:
        Dictionary mapping file_path -> hash_string
    """
    results = {}
    hash_func = hash_file_fast if use_fast else hash_file

    def hash_single_file(file_path):
        try:
            return file_path, hash_func(file_path, algorithm)
        except Exception as e:
            return file_path, f"error:{str(e)}"

    # Use ThreadPoolExecutor for I/O bound operations
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all hashing tasks
        future_to_path = {executor.submit(hash_single_file, path): path for path in file_paths}

        # Collect results as they complete
        for future in as_completed(future_to_path):
            file_path, result = future.result()
            results[file_path] = result

    return results


def is_same_filesystem(path1: Path, path2: Path) -> bool:
    """
    Check if two paths are on the same filesystem.

    Args:
        path1: First path
        path2: Second path

    Returns:
        True if same filesystem, False otherwise
    """
    try:
        # Get device IDs for both paths
        stat1 = os.stat(path1)
        stat2 = os.stat(path2)
        return stat1.st_dev == stat2.st_dev
    except OSError:
        # If we can't stat, assume different filesystems for safety
        return False


def safe_move_optimized(source: Path, destination: Path,
                       skip_hash_same_fs: bool = True) -> bool:
    """
    Optimized safe move with conditional hashing.

    Args:
        source: Source file path
        destination: Destination file path
        skip_hash_same_fs: Skip full hashing if same filesystem (default: True)

    Returns:
        True if move succeeded
    """
    source = normalize_windows_path(Path(source))
    destination = normalize_windows_path(Path(destination))

    # Ensure destination directory exists
    destination.parent.mkdir(parents=True, exist_ok=True)

    if destination.exists():
        raise FileExistsError(f"Destination already exists: {destination}")

    # Check if we can skip full hashing
    skip_full_hash = skip_hash_same_fs and is_same_filesystem(source, destination)

    if skip_full_hash:
        # Lightweight verification: check file size before/after
        size_before = source.stat().st_size
        shutil.move(str(source), str(destination))
        size_after = destination.stat().st_size

        if size_before != size_after:
            raise ValueError(f"File size changed during move: {size_before} -> {size_after}")

        # Return minimal hash info for logging
        return {
            'hash_before': f'size:{size_before}',
            'hash_after': f'size:{size_after}',
            'verified': True
        }
    else:
        # Full verification for cross-filesystem moves
        hash_before = hash_file_fast(source)
        shutil.move(str(source), str(destination))
        hash_after = hash_file_fast(destination)

        if hash_before != hash_after:
            raise ValueError(f"File corruption detected: {hash_before} != {hash_after}")

        return {
            'hash_before': hash_before,
            'hash_after': hash_after,
            'verified': True
        }


class HashCache:
    """Cache for file hashes to avoid re-hashing unchanged files."""
    
    def __init__(self, cache_file: Path = None):
        if cache_file is None:
            cache_file = Path("._state/hash_cache.json")
        self.cache_file = cache_file
        self.cache = self._load_cache()
        self._lock = threading.Lock()
    
    def _load_cache(self) -> Dict[str, Dict[str, Any]]:
        """Load hash cache from disk."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return {}
        return {}
    
    def _save_cache(self) -> None:
        """Save hash cache to disk."""
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, indent=2)
    
    def get_cached_hash(self, file_path: Path) -> Optional[str]:
        """Get cached hash if file hasn't changed."""
        cache_key = str(file_path.resolve())
        
        with self._lock:
            if cache_key in self.cache:
                cached_data = self.cache[cache_key]
                
                # Check if file still exists and metadata matches
                if file_path.exists():
                    stat = file_path.stat()
                    if (stat.st_size == cached_data['size'] and 
                        stat.st_mtime == cached_data['mtime']):
                        return cached_data['hash']
        
        return None
    
    def cache_hash(self, file_path: Path, hash_value: str) -> None:
        """Cache a file hash with its metadata."""
        cache_key = str(file_path.resolve())
        
        if file_path.exists():
            stat = file_path.stat()
            cache_entry = {
                'hash': hash_value,
                'size': stat.st_size,
                'mtime': stat.st_mtime,
                'algorithm': 'sha256'
            }
            
            with self._lock:
                self.cache[cache_key] = cache_entry
                # Save to disk periodically (every 10 entries)
                if len(self.cache) % 10 == 0:
                    self._save_cache()
    
    def cleanup_stale_entries(self) -> int:
        """Remove cache entries for files that no longer exist."""
        removed = 0
        with self._lock:
            keys_to_remove = []
            for cache_key in self.cache:
                if not Path(cache_key).exists():
                    keys_to_remove.append(cache_key)
            
            for key in keys_to_remove:
                del self.cache[key]
                removed += 1
            
            if removed > 0:
                self._save_cache()
        
        return removed


class DeferredHashQueue:
    """Queue for deferred file hashing operations."""
    
    def __init__(self, max_workers: int = 2):
        self.queue = []
        self.results = {}
        self.max_workers = max_workers
        self._lock = threading.Lock()
    
    def add_file(self, file_path: Path, operation_id: str) -> str:
        """Add a file to the deferred hashing queue."""
        with self._lock:
            self.queue.append((file_path, operation_id))
            return f"deferred:{operation_id}:{len(self.queue)}"
    
    def process_queue(self) -> Dict[str, str]:
        """Process all deferred hashing operations in parallel."""
        if not self.queue:
            return {}
        
        with self._lock:
            files_to_hash = self.queue.copy()
            self.queue.clear()
        
        # Hash files in parallel
        file_paths = [fp for fp, _ in files_to_hash]
        hashes = hash_files_parallel(file_paths, max_workers=self.max_workers)
        
        # Store results
        results = {}
        for (file_path, operation_id), hash_result in zip(files_to_hash, hashes.values()):
            results[operation_id] = hash_result
        
        return results
    
    def get_result(self, operation_id: str) -> Optional[str]:
        """Get the result for a specific operation."""
        return self.results.get(operation_id)


# Global deferred hash queue
_deferred_queue = None

def get_deferred_queue() -> DeferredHashQueue:
    """Get the global deferred hash queue instance."""
    global _deferred_queue
    if _deferred_queue is None:
        _deferred_queue = DeferredHashQueue()
    return _deferred_queue


def hash_file_deferred(file_path: Path, operation_id: str, algorithm: str = "sha256") -> str:
    """
    Add file to deferred hashing queue.
    
    Returns a placeholder that will be resolved later.
    """
    queue = get_deferred_queue()
    return queue.add_file(file_path, operation_id)


def resolve_deferred_hashes() -> Dict[str, str]:
    """
    Process all deferred hashing operations and return results.
    
    Call this when you need the actual hash values.
    """
    queue = get_deferred_queue()
    return queue.process_queue()


# Global hash cache instance
_hash_cache = None

def get_hash_cache() -> HashCache:
    """Get the global hash cache instance."""
    global _hash_cache
    if _hash_cache is None:
        _hash_cache = HashCache()
    return _hash_cache


def hash_file_incremental(file_path: Path, algorithm: str = "sha256", use_cache: bool = True) -> str:
    """
    Hash a file with incremental optimization using cache.
    
    Args:
        file_path: Path to file
        algorithm: Hash algorithm (default: sha256)
        use_cache: Use hash cache for unchanged files (default: True)
    
    Returns:
        Hash string in format "algorithm:hexdigest"
    """
    if use_cache:
        cache = get_hash_cache()
        cached_hash = cache.get_cached_hash(file_path)
        if cached_hash:
            return cached_hash
    
    # Compute fresh hash
    hash_value = hash_file_fast(file_path, algorithm)
    
    # Cache the result
    if use_cache:
        cache.cache_hash(file_path, hash_value)
    
    return hash_value


def safe_move_incremental(source: Path, destination: Path,
                         use_cache: bool = True,
                         skip_hash_same_fs: bool = True) -> Dict[str, Any]:
    """
    Optimized safe move with incremental hashing and caching.
    
    Args:
        source: Source file path
        destination: Destination file path
        use_cache: Use hash cache for optimization
        skip_hash_same_fs: Skip full hashing if same filesystem
    
    Returns:
        Dictionary with move results and verification info
    """
    source = normalize_windows_path(Path(source))
    destination = normalize_windows_path(Path(destination))

    # Ensure destination directory exists
    destination.parent.mkdir(parents=True, exist_ok=True)

    if destination.exists():
        raise FileExistsError(f"Destination already exists: {destination}")

    # Check if we can skip full hashing
    skip_full_hash = skip_hash_same_fs and is_same_filesystem(source, destination)

    if skip_full_hash:
        # Lightweight verification: check file size before/after
        size_before = source.stat().st_size
        shutil.move(str(source), str(destination))
        size_after = destination.stat().st_size

        if size_before != size_after:
            raise ValueError(f"File size changed during move: {size_before} -> {size_after}")

        # Return minimal verification info
        return {
            'hash_before': f'size:{size_before}',
            'hash_after': f'size:{size_after}',
            'verified': True,
            'method': 'size_only_same_fs'
        }
    else:
        # Full verification with caching
        hash_before = hash_file_incremental(source, use_cache=use_cache)
        shutil.move(str(source), str(destination))
        hash_after = hash_file_incremental(destination, use_cache=use_cache)

        if hash_before != hash_after:
            raise ValueError(f"File corruption detected: {hash_before} != {hash_after}")

        return {
            'hash_before': hash_before,
            'hash_after': hash_after,
            'verified': True,
            'method': 'full_hash_cached'
        }


def normalize_windows_path(path: Path) -> Path:
    r"""
    Convert to extended-length path format for Windows long path support.
    
    Windows has a 260-character limit for paths unless using extended-length
    path syntax (\\?\ prefix).
    
    Args:
        path: Path object
    
    Returns:
        Normalized path (extended-length if > 260 chars)
    """
    path_str = str(path.resolve())
    
    # If already extended-length, return as-is
    if path_str.startswith("\\\\?\\"):
        return Path(path_str)
    
    # If path is long, convert to extended-length
    if len(path_str) > 260:
        if path_str.startswith("\\\\"):  # UNC path
            return Path("\\\\?\\UNC\\" + path_str[2:])
        else:
            return Path("\\\\?\\" + path_str)
    
    return path


def safe_move(source: Path, destination: Path, 
              verify_hash: bool = True) -> bool:
    """
    Safely move a file with validation and optional hash verification.
    
    Args:
        source: Source file path
        destination: Destination file path
        verify_hash: If True, verify file hash before/after move
    
    Returns:
        True if move succeeded
    
    Raises:
        FileNotFoundError: If source doesn't exist
        FileExistsError: If destination already exists
        ValueError: If hash verification fails
    """
    source = normalize_windows_path(Path(source))
    destination = normalize_windows_path(Path(destination))
    
    # Validation
    if not source.exists():
        raise FileNotFoundError(f"Source file not found: {source}")
    
    if destination.exists():
        raise FileExistsError(f"Destination already exists: {destination}")
    
    # Create destination directory
    destination.parent.mkdir(parents=True, exist_ok=True)
    
    # Hash before move (if requested)
    hash_before = None
    if verify_hash:
        hash_before = hash_file(source)
    
    # Execute move
    shutil.move(str(source), str(destination))
    
    # Hash after move (if requested)
    if verify_hash:
        hash_after = hash_file(destination)
        if hash_before != hash_after:
            raise ValueError(
                f"File corruption detected during move!\n"
                f"  Before: {hash_before}\n"
                f"  After:  {hash_after}"
            )
    
    return True


def safe_case_rename(source: Path, new_name: str) -> Path:
    """
    Safely rename with only case change on Windows.
    
    NTFS is case-preserving but case-insensitive, so renaming
    "movie.mkv" to "Movie.mkv" requires a temporary rename.
    
    Args:
        source: Source file path
        new_name: New filename (only case different)
    
    Returns:
        Path to renamed file
    """
    source = normalize_windows_path(Path(source))
    destination = source.with_name(new_name)
    
    if source.name.lower() == new_name.lower():
        # Case-only rename requires temp file on Windows
        temp_name = source.with_name(f"_temp_{new_name}")
        source.rename(temp_name)
        temp_name.rename(destination)
    else:
        source.rename(destination)
    
    return destination


def validate_path_length(path: Path, max_length: int = 260) -> bool:
    """
    Check if path exceeds Windows path length limit.
    
    Args:
        path: Path to validate
        max_length: Maximum path length (default: 260)
    
    Returns:
        True if path is acceptable
    
    Raises:
        ValueError: If path is too long
    """
    path_str = str(path.resolve())
    
    if len(path_str) > max_length:
        raise ValueError(
            f"Path exceeds {max_length} character limit: {len(path_str)} chars\n"
            f"  Path: {path_str}\n"
            f"  Consider enabling Windows long path support or shortening path."
        )
    
    return True


def safe_move_ultimate(source: Path, destination: Path,
                      operation_id: str = None,
                      use_cache: bool = True,
                      skip_hash_same_fs: bool = True,
                      deferred: bool = False) -> Dict[str, Any]:
    """
    Ultimate optimized safe move combining all performance optimizations.
    
    Args:
        source: Source file path
        destination: Destination file path
        operation_id: Unique ID for this operation (for deferred hashing)
        use_cache: Use hash cache for optimization
        skip_hash_same_fs: Skip full hashing if same filesystem
        deferred: Use deferred hashing (return immediately, hash later)
    
    Returns:
        Dictionary with move results and verification info
    """
    source = normalize_windows_path(Path(source))
    destination = normalize_windows_path(Path(destination))

    # Ensure destination directory exists
    destination.parent.mkdir(parents=True, exist_ok=True)

    if destination.exists():
        raise FileExistsError(f"Destination already exists: {destination}")

    # Check if we can skip full hashing
    skip_full_hash = skip_hash_same_fs and is_same_filesystem(source, destination)

    if skip_full_hash:
        # Fast CRC32 verification for same filesystem (much faster than SHA256)
        crc_before = hash_file_crc32(source)
        shutil.move(str(source), str(destination))
        crc_after = hash_file_crc32(destination)

        if crc_before != crc_after:
            raise ValueError(f"File corruption detected during move: {crc_before} != {crc_after}")

        return {
            "hash_before": crc_before,
            "hash_after": crc_after,
            "verified": True,
            "method": "crc32_same_fs",
            "deferred": False
        }
    
    # For cross-filesystem moves, use optimizations
    if deferred and operation_id:
        # Deferred hashing: add to queue and move immediately
        deferred_id_before = hash_file_deferred(source, f"{operation_id}_before")
        shutil.move(str(source), str(destination))
        deferred_id_after = hash_file_deferred(destination, f"{operation_id}_after")
        
        return {
            "hash_before": deferred_id_before,
            "hash_after": deferred_id_after,
            "verified": False,  # Will be verified later
            "method": "deferred_hash",
            "deferred": True,
            "operation_id": operation_id
        }
    else:
        # Immediate hashing with caching
        hash_before = hash_file_incremental(source, use_cache=use_cache)
        shutil.move(str(source), str(destination))
        hash_after = hash_file_incremental(destination, use_cache=use_cache)

        if hash_before != hash_after:
            raise ValueError(f"File corruption detected: {hash_before} != {hash_after}")

        return {
            "hash_before": hash_before,
            "hash_after": hash_after,
            "verified": True,
            "method": "incremental_cached_hash",
            "deferred": False
        }


def clean_episode_title(title: str) -> str:
    """
    Clean episode title by removing technical tags, quality indicators, and normalizing formatting.
    
    Removes common technical tags found in episode titles:
    - Quality tags: 2160p, 1080p, 720p, 480p, SD, HD, UHD, 4K
    - Release tags: DSNP, Vyndros, WEB-DL, BluRay, HDTV, WEBRip, DVDRip
    - File tags: x264, x265, HEVC, AVC, AAC, DTS, AC3
    - Scene tags: PROPER, REPACK, INTERNAL, READNFO
    - Size/format tags: DD5.1, DTS-HD, TrueHD
    - Parenthetical notes: (Part 1), (1), (2), etc.
    
    Also normalizes whitespace and punctuation.
    
    Args:
        title: Raw episode title
        
    Returns:
        Cleaned episode title
        
    Examples:
        "Heart of Ice (1)" → "Heart of Ice"
        "The Last Laugh 2160p DSNP" → "The Last Laugh"
        "Cat Scratch Fever WEB-DL" → "Cat Scratch Fever"
    """
    if not title:
        return title
    
    # Make a copy to work with
    cleaned = title.strip()
    
    # Remove parenthetical numbers at the end (Part 1, (1), etc.)
    cleaned = re.sub(r'\s*\([^)]*\d+[^)]*\)\s*$', '', cleaned)
    cleaned = re.sub(r'\s*\(Part\s+\d+\)\s*$', '', cleaned, flags=re.IGNORECASE)
    
    # Common technical tags to remove (case insensitive)
    technical_tags = [
        # Quality
        r'\b2160p\b', r'\b1080p\b', r'\b720p\b', r'\b480p\b', r'\b4K\b', r'\bUHD\b', r'\bHD\b', r'\bSD\b',
        # Release groups/sources
        r'\bDSNP\b', r'\bVyndros\b', r'\bWEB-DL\b', r'\bBluRay\b', r'\bHDTV\b', r'\bWEBRip\b', r'\bDVDRip\b',
        r'\bBDRip\b', r'\bHDRip\b', r'\bTVRip\b', r'\bPDTV\b', r'\bSATRip\b',
        # Codecs/containers
        r'\bx264\b', r'\bx265\b', r'\bHEVC\b', r'\bAVC\b', r'\bAAC\b', r'\bDTS\b', r'\bAC3\b', r'\bDD5\.1\b',
        r'\bDTS-HD\b', r'\bTrueHD\b', r'\bFLAC\b', r'\bMP3\b', r'\bVorbis\b',
        # Scene tags
        r'\bPROPER\b', r'\bREPACK\b', r'\bINTERNAL\b', r'\bREADNFO\b', r'\bLIMITED\b', r'\bCOMPLETE\b',
        # Other common tags
        r'\bMULTi\b', r'\bDUAL\b', r'\bSUBS\b', r'\bSYNC\b', r'\bFIX\b', r'\bEXTENDED\b', r'\bUNCUT\b',
        r'\bDIRECTORS\b', r'\bCUT\b', r'\bTHEATRICAL\b', r'\bUNRATED\b'
    ]
    
    # Remove all technical tags
    for tag in technical_tags:
        cleaned = re.sub(tag, '', cleaned, flags=re.IGNORECASE)
    
    # Clean up extra whitespace and punctuation
    # Remove multiple spaces
    cleaned = re.sub(r'\s+', ' ', cleaned)
    
    # Remove trailing/leading punctuation except apostrophes and hyphens in words
    cleaned = re.sub(r'^[^\w\'-]+|[^\w\'-]+$', '', cleaned)
    
    # Normalize ellipses
    cleaned = re.sub(r'\.{3,}', '...', cleaned)
    cleaned = re.sub(r'…', '...', cleaned)
    
    # Fix common punctuation issues
    cleaned = re.sub(r'\s*,\s*', ', ', cleaned)  # Normalize commas
    cleaned = re.sub(r'\s*:\s*', ': ', cleaned)  # Normalize colons
    
    # Final cleanup
    cleaned = cleaned.strip()
    
    # Don't return empty strings
    return cleaned if cleaned else title


def compare_episode_titles(current_title: str, canonical_title: str, cleaned_title: str = None) -> Dict[str, Any]:
    """
    Compare current episode title with canonical title and provide recommendations.
    
    Args:
        current_title: Current title from filename
        canonical_title: Canonical title from cache
        cleaned_title: Pre-cleaned version (optional, will clean if not provided)
        
    Returns:
        Dict with comparison results and recommendations
    """
    if cleaned_title is None:
        cleaned_title = clean_episode_title(current_title)
    
    # Exact matches
    exact_match_cleaned = cleaned_title.lower() == canonical_title.lower()
    exact_match_current = current_title.lower() == canonical_title.lower()
    
    # Fuzzy matching (contains)
    cleaned_contains_canonical = canonical_title.lower() in cleaned_title.lower()
    canonical_contains_cleaned = cleaned_title.lower() in canonical_title.lower()
    
    # Determine recommendation
    if exact_match_cleaned:
        recommendation = "keep_cleaned"
        confidence = "high"
    elif exact_match_current:
        recommendation = "keep_current" 
        confidence = "high"
    elif cleaned_contains_canonical and len(cleaned_title) > len(canonical_title) * 1.5:
        # Cleaned title is much longer and contains canonical - probably has extra junk
        recommendation = "use_canonical"
        confidence = "medium"
    elif canonical_contains_cleaned:
        recommendation = "use_canonical"
        confidence = "medium"
    else:
        recommendation = "review_manual"
        confidence = "low"
    
    return {
        "current_title": current_title,
        "cleaned_title": cleaned_title,
        "canonical_title": canonical_title,
        "exact_match_cleaned": exact_match_cleaned,
        "exact_match_current": exact_match_current,
        "cleaned_contains_canonical": cleaned_contains_canonical,
        "canonical_contains_cleaned": canonical_contains_cleaned,
        "recommendation": recommendation,
        "confidence": confidence,
        "needs_rename": recommendation in ["use_canonical", "keep_cleaned"] and not exact_match_current
    }

