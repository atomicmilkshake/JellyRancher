"""
Tests for FileScanner and related classes.

Function Index Queries:
- search "file scanner scan folder MD5 hash file record" -> Found FileHasher in 
  transaction_manager.py (used by FileScanner), MediaFileScanner variant exists
- search "sample movies dir fixture" -> Found sample_movies_dir in conftest.py

Coverage Target: 80%+ line coverage
"""
import pytest
from pathlib import Path
from datetime import datetime

from scripts.core.file_scanner import FileScanner, FileRecord, ScanStatistics


class TestFileRecord:
    """Tests for FileRecord dataclass."""
    
    @pytest.mark.unit
    def test_creation_with_path_objects(self, tmp_path):
        """FileRecord should accept Path objects."""
        file_path = tmp_path / "test.mkv"
        file_path.write_bytes(b"test content")
        
        record = FileRecord(
            absolute_path=file_path,
            size_bytes=12,
            extension=".mkv",
            parent_folder=tmp_path,
            scan_timestamp=datetime.now()
        )
        
        assert isinstance(record.absolute_path, Path)
        assert isinstance(record.parent_folder, Path)
    
    @pytest.mark.unit
    def test_string_path_converts_to_path(self, tmp_path):
        """FileRecord should convert string paths to Path objects."""
        record = FileRecord(
            absolute_path=str(tmp_path / "test.mkv"),
            size_bytes=100,
            extension=".mkv",
            parent_folder=str(tmp_path),
            scan_timestamp=datetime.now()
        )
        
        assert isinstance(record.absolute_path, Path)
        assert isinstance(record.parent_folder, Path)
    
    @pytest.mark.unit
    def test_default_md5_is_none(self, tmp_path):
        """MD5 hash should default to None."""
        record = FileRecord(
            absolute_path=tmp_path / "test.mkv",
            size_bytes=100,
            extension=".mkv",
            parent_folder=tmp_path,
            scan_timestamp=datetime.now()
        )
        
        assert record.md5_hash is None
    
    @pytest.mark.unit
    def test_jellyfin_fields_default_values(self, tmp_path):
        """Jellyfin integration fields should have sensible defaults."""
        record = FileRecord(
            absolute_path=tmp_path / "test.mkv",
            size_bytes=100,
            extension=".mkv",
            parent_folder=tmp_path,
            scan_timestamp=datetime.now()
        )
        
        assert record.jellyfin_id is None
        assert record.jellyfin_item_type is None
        assert record.jellyfin_matched is False
        assert record.jellyfin_provider_ids == {}


class TestScanStatistics:
    """Tests for ScanStatistics dataclass."""
    
    @pytest.mark.unit
    def test_initial_values(self):
        """ScanStatistics should have zero initial values."""
        stats = ScanStatistics()
        
        assert stats.total_files == 0
        assert stats.total_size_bytes == 0
        assert stats.folders_scanned == 0
        assert stats.scan_duration_seconds == 0.0
        assert stats.errors == []
    
    @pytest.mark.unit
    def test_add_file_increments_count(self):
        """add_file should increment total_files."""
        stats = ScanStatistics()
        stats.add_file(Path("test.mkv"), 1000)
        
        assert stats.total_files == 1
    
    @pytest.mark.unit
    def test_add_file_accumulates_size(self):
        """add_file should accumulate total_size_bytes."""
        stats = ScanStatistics()
        stats.add_file(Path("test1.mkv"), 1000)
        stats.add_file(Path("test2.mkv"), 2000)
        
        assert stats.total_size_bytes == 3000
    
    @pytest.mark.unit
    def test_add_file_tracks_file_types(self):
        """add_file should track counts by extension."""
        stats = ScanStatistics()
        stats.add_file(Path("test1.mkv"), 1000)
        stats.add_file(Path("test2.mkv"), 1000)
        stats.add_file(Path("test.mp4"), 500)
        
        assert stats.file_types[".mkv"] == 2
        assert stats.file_types[".mp4"] == 1


class TestFileScannerInit:
    """Tests for FileScanner initialization."""
    
    @pytest.mark.unit
    def test_default_extensions(self):
        """FileScanner should have default video extensions."""
        scanner = FileScanner()
        
        assert ".mkv" in scanner.extensions
        assert ".mp4" in scanner.extensions
        assert ".avi" in scanner.extensions
    
    @pytest.mark.unit
    def test_includes_subtitles_by_default(self):
        """FileScanner should include subtitle extensions by default."""
        scanner = FileScanner()
        
        assert ".srt" in scanner.extensions
        assert ".sub" in scanner.extensions
    
    @pytest.mark.unit
    def test_includes_metadata_by_default(self):
        """FileScanner should include metadata extensions by default."""
        scanner = FileScanner()
        
        assert ".nfo" in scanner.extensions
        assert ".jpg" in scanner.extensions
    
    @pytest.mark.unit
    def test_custom_extensions(self):
        """FileScanner should accept custom extensions."""
        scanner = FileScanner(
            extensions={".custom", ".test"},
            include_subtitles=False,
            include_metadata=False
        )
        
        assert ".custom" in scanner.extensions
        assert ".test" in scanner.extensions
        assert ".mkv" not in scanner.extensions
    
    @pytest.mark.unit
    def test_raises_on_invalid_extensions_type(self):
        """FileScanner should raise TypeError for non-set extensions."""
        with pytest.raises(TypeError, match="extensions must be a set"):
            FileScanner(extensions=[".mkv"])
    
    @pytest.mark.unit
    def test_md5_calculation_flag(self):
        """FileScanner should store MD5 calculation preference."""
        scanner_without = FileScanner(calculate_md5=False)
        scanner_with = FileScanner(calculate_md5=True)
        
        assert scanner_without.calculate_md5 is False
        assert scanner_with.calculate_md5 is True


class TestFileScannerScan:
    """Tests for FileScanner.scan_folder method."""
    
    @pytest.mark.integration
    def test_scan_empty_folder(self, tmp_path):
        """Scanning empty folder should return empty list."""
        scanner = FileScanner()
        results = scanner.scan_folder(tmp_path)
        
        assert results == []
        assert scanner.statistics.total_files == 0
    
    @pytest.mark.integration
    def test_scan_with_files(self, sample_movies_dir):
        """Scanning folder with files should return FileRecords."""
        scanner = FileScanner()
        results = scanner.scan_folder(sample_movies_dir)
        
        assert len(results) > 0
        assert all(isinstance(r, FileRecord) for r in results)
    
    @pytest.mark.integration
    def test_scan_filters_by_extension(self, tmp_path):
        """Scanner should only include files with matching extensions."""
        # Create files with various extensions
        (tmp_path / "video.mkv").write_bytes(b"video")
        (tmp_path / "text.txt").write_text("text")
        (tmp_path / "doc.pdf").write_bytes(b"pdf")
        
        scanner = FileScanner(
            extensions={".mkv"},
            include_subtitles=False,
            include_metadata=False
        )
        results = scanner.scan_folder(tmp_path)
        
        assert len(results) == 1
        assert results[0].extension == ".mkv"
    
    @pytest.mark.integration
    def test_scan_recursive(self, tmp_path):
        """Recursive scan should find files in subdirectories."""
        # Create nested structure
        subdir = tmp_path / "subdir" / "nested"
        subdir.mkdir(parents=True)
        (tmp_path / "root.mkv").write_bytes(b"root")
        (subdir / "nested.mkv").write_bytes(b"nested")
        
        scanner = FileScanner(
            extensions={".mkv"},
            include_subtitles=False,
            include_metadata=False
        )
        results = scanner.scan_folder(tmp_path, recursive=True)
        
        assert len(results) == 2
    
    @pytest.mark.integration
    def test_scan_non_recursive(self, tmp_path):
        """Non-recursive scan should only find files in root folder."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (tmp_path / "root.mkv").write_bytes(b"root")
        (subdir / "nested.mkv").write_bytes(b"nested")
        
        scanner = FileScanner(
            extensions={".mkv"},
            include_subtitles=False,
            include_metadata=False
        )
        results = scanner.scan_folder(tmp_path, recursive=False)
        
        assert len(results) == 1
        assert "root.mkv" in str(results[0].absolute_path)
    
    @pytest.mark.integration
    def test_scan_calculates_md5_when_enabled(self, tmp_path):
        """Scanner should calculate hash when enabled (BLAKE3 since Phase 48-A)."""
        test_file = tmp_path / "test.mkv"
        test_file.write_bytes(b"test content for hashing")

        scanner = FileScanner(
            extensions={".mkv"},
            include_subtitles=False,
            include_metadata=False,
            calculate_md5=True
        )
        results = scanner.scan_folder(tmp_path)

        assert len(results) == 1
        assert results[0].md5_hash is not None
        assert len(results[0].md5_hash) == 64  # BLAKE3 hex length (was 32 for MD5)
    
    @pytest.mark.integration
    def test_scan_skips_md5_when_disabled(self, tmp_path):
        """Scanner should not calculate MD5 when disabled."""
        test_file = tmp_path / "test.mkv"
        test_file.write_bytes(b"test content")
        
        scanner = FileScanner(
            extensions={".mkv"},
            include_subtitles=False,
            include_metadata=False,
            calculate_md5=False
        )
        results = scanner.scan_folder(tmp_path)
        
        assert len(results) == 1
        assert results[0].md5_hash is None
    
    @pytest.mark.unit
    def test_scan_raises_on_nonexistent_folder(self, tmp_path):
        """Scanner should raise FileNotFoundError for missing folder."""
        scanner = FileScanner()
        
        with pytest.raises(FileNotFoundError):
            scanner.scan_folder(tmp_path / "nonexistent")
    
    @pytest.mark.unit
    def test_scan_raises_on_file_path(self, tmp_path):
        """Scanner should raise NotADirectoryError for file path."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        
        scanner = FileScanner()
        
        with pytest.raises(NotADirectoryError):
            scanner.scan_folder(test_file)
    
    @pytest.mark.integration
    def test_scan_updates_statistics(self, tmp_path):
        """Scanning should populate statistics."""
        (tmp_path / "test1.mkv").write_bytes(b"x" * 1000)
        (tmp_path / "test2.mkv").write_bytes(b"x" * 2000)
        
        scanner = FileScanner(
            extensions={".mkv"},
            include_subtitles=False,
            include_metadata=False
        )
        scanner.scan_folder(tmp_path)
        
        stats = scanner.get_statistics()
        assert stats.total_files == 2
        assert stats.total_size_bytes == 3000
        assert stats.file_types[".mkv"] == 2


class TestFileScannerFolderStructure:
    """Tests for folder structure analysis methods."""
    
    @pytest.mark.integration
    def test_get_folder_structure(self, sample_movies_dir):
        """get_folder_structure should aggregate files by folder."""
        scanner = FileScanner()
        records = scanner.scan_folder(sample_movies_dir)
        structure = scanner.get_folder_structure(records)
        
        assert len(structure) > 0
        for folder, stats in structure.items():
            assert isinstance(folder, Path)
            assert "total_size" in stats
            assert "file_count" in stats
            assert "file_types" in stats
    
    @pytest.mark.unit
    def test_get_folder_structure_empty_list(self):
        """get_folder_structure should handle empty list."""
        scanner = FileScanner()
        structure = scanner.get_folder_structure([])
        
        assert structure == {}
    
    @pytest.mark.unit
    def test_get_folder_structure_raises_on_invalid_input(self):
        """get_folder_structure should raise TypeError for non-list."""
        scanner = FileScanner()
        
        with pytest.raises(TypeError, match="must be a list"):
            scanner.get_folder_structure("not a list")
    
    @pytest.mark.integration
    def test_format_folder_structure(self, sample_movies_dir):
        """format_folder_structure should return string output."""
        scanner = FileScanner()
        records = scanner.scan_folder(sample_movies_dir)
        structure = scanner.get_folder_structure(records)
        formatted = scanner.format_folder_structure(structure)
        
        assert isinstance(formatted, str)
        assert "FOLDER STRUCTURE ANALYSIS" in formatted
    
    @pytest.mark.unit
    def test_format_folder_structure_raises_on_invalid_input(self):
        """format_folder_structure should raise TypeError for non-dict."""
        scanner = FileScanner()
        
        with pytest.raises(TypeError, match="must be a dict"):
            scanner.format_folder_structure([])


class TestFileScannerExclusions:
    """Tests for path exclusion functionality."""
    
    @pytest.mark.integration
    def test_excludes_specified_paths(self, tmp_path):
        """Scanner should skip excluded paths."""
        # Create structure
        include_dir = tmp_path / "include"
        exclude_dir = tmp_path / "exclude"
        include_dir.mkdir()
        exclude_dir.mkdir()
        
        (include_dir / "keep.mkv").write_bytes(b"keep")
        (exclude_dir / "skip.mkv").write_bytes(b"skip")
        
        scanner = FileScanner(
            extensions={".mkv"},
            include_subtitles=False,
            include_metadata=False,
            exclude_paths={exclude_dir}
        )
        results = scanner.scan_folder(tmp_path)
        
        assert len(results) == 1
        assert "keep.mkv" in str(results[0].absolute_path)


class TestFileScannerFormatSize:
    """Tests for size formatting utility."""
    
    @pytest.mark.unit
    def test_format_bytes(self):
        """Should format small sizes in bytes."""
        result = FileScanner._format_size(500)
        assert "B" in result
    
    @pytest.mark.unit
    def test_format_kilobytes(self):
        """Should format KB sizes."""
        result = FileScanner._format_size(1024 * 5)
        assert "KB" in result
    
    @pytest.mark.unit
    def test_format_megabytes(self):
        """Should format MB sizes."""
        result = FileScanner._format_size(1024 * 1024 * 100)
        assert "MB" in result
    
    @pytest.mark.unit
    def test_format_gigabytes(self):
        """Should format GB sizes."""
        result = FileScanner._format_size(1024 * 1024 * 1024 * 5)
        assert "GB" in result

