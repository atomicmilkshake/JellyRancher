"""
Tests for workers module (QThread-based workers).

Function Index Queries:
- search "worker thread QThread scan progress signal emit" -> Found MultiScanWorker usage
  in scan_view.py, test_scan_folder_with_callback in test_backends.py
- search "mock QThread pytest" -> No specific results, using unittest.mock

Coverage Target: 60%+ (Tier 3: Workers with Qt mocking)

Note: These workers use PyQt6 QThread and signals. Tests mock Qt components to avoid
requiring a QApplication instance.
"""
import pytest
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from scripts.core.workers import (
    MultiScanWorker,
    LLMAnalysisWorker,
    MetadataLookupWorker,
    ActionPlanWorker,
    ScanResultsLoadWorker
)
from scripts.core.file_scanner import FileRecord


def make_file_record(path: Path, extension: str = ".mkv", size: int = 1000) -> FileRecord:
    """Helper to create FileRecord instances."""
    return FileRecord(
        absolute_path=path,
        size_bytes=size,
        extension=extension,
        parent_folder=path.parent,
        scan_timestamp=datetime.now(),
        md5_hash=None
    )


class TestMultiScanWorker:
    """Tests for MultiScanWorker."""
    
    @pytest.fixture
    def mock_qthread(self):
        """Mock QThread base class."""
        with patch('scripts.core.workers.QThread.__init__', return_value=None):
            yield
    
    @pytest.mark.unit
    def test_init_stores_parameters(self, mock_qthread, tmp_path):
        """Should store folder paths and configuration."""
        folders = [tmp_path / "folder1", tmp_path / "folder2"]
        worker = MultiScanWorker(folder_paths=folders, recursive=True)
        
        assert worker.folder_paths == folders
        assert worker.recursive is True
        assert worker.repository is not None
    
    @pytest.mark.unit
    def test_init_with_excluded_subfolders(self, mock_qthread, tmp_path):
        """Should store excluded subfolders."""
        folders = [tmp_path / "folder1"]
        excluded = [tmp_path / "folder1" / "skip"]
        worker = MultiScanWorker(folder_paths=folders, excluded_subfolders=excluded)
        
        assert len(worker.excluded_subfolders) == 1
    
    @pytest.mark.unit
    def test_progress_callback_exists(self, mock_qthread, tmp_path):
        """Should have _progress_callback method for formatting."""
        worker = MultiScanWorker(folder_paths=[tmp_path], recursive=False)
        
        # Verify method exists and is callable
        assert hasattr(worker, '_progress_callback')
        assert callable(worker._progress_callback)
        
        # Method should accept correct parameters
        import inspect
        sig = inspect.signature(worker._progress_callback)
        params = list(sig.parameters.keys())
        assert 'message' in params
        assert 'current' in params
        assert 'total' in params
        assert 'folder_idx' in params
        assert 'total_folders' in params


class TestLLMAnalysisWorker:
    """Tests for LLMAnalysisWorker."""
    
    @pytest.fixture
    def mock_qthread(self):
        """Mock QThread base class."""
        with patch('scripts.core.workers.QThread.__init__', return_value=None):
            yield
    
    @pytest.mark.unit
    def test_init_stores_parameters(self, mock_qthread):
        """Should store folder structure and scanned files."""
        folder_structure = {Path("/test"): {"file_count": 1}}
        scanned_files = []
        
        worker = LLMAnalysisWorker(
            folder_structure=folder_structure,
            scanned_files=scanned_files,
            api_key="test-key",
            model="test-model"
        )
        
        assert worker.folder_structure == folder_structure
        assert worker.scanned_files == scanned_files
        assert worker.api_key == "test-key"
        assert worker.model == "test-model"
    
    @pytest.mark.unit
    def test_build_structure_summary(self, mock_qthread, tmp_path):
        """Should convert folder structure to LLM format."""
        folder = tmp_path / "movies"
        folder.mkdir()
        file1 = folder / "movie.mkv"
        file1.write_bytes(b"content")
        
        record = make_file_record(file1)
        folder_structure = {
            folder: {
                "file_count": 1,
                "total_size": 1000,
                "file_types": {".mkv": 1},
                "file_type_sizes": {".mkv": 1000}
            }
        }
        
        worker = LLMAnalysisWorker(
            folder_structure=folder_structure,
            scanned_files=[record]
        )
        
        summary = worker._build_structure_summary()
        
        assert "folders" in summary
        assert len(summary["folders"]) == 1
        assert summary["folders"][0]["file_count"] == 1


class TestMetadataLookupWorker:
    """Tests for MetadataLookupWorker."""
    
    @pytest.fixture
    def mock_qthread(self):
        """Mock QThread base class."""
        with patch('scripts.core.workers.QThread.__init__', return_value=None):
            yield
    
    @pytest.mark.unit
    def test_init_stores_parameters(self, mock_qthread):
        """Should store detected media and scanned files."""
        detected_media = []
        scanned_files = []
        worker = MetadataLookupWorker(
            detected_media=detected_media,
            scanned_files=scanned_files,
            tmdb_api_key="test-key",
            omdb_api_key="test-omdb"
        )
        
        assert worker.detected_media == detected_media
        assert worker.scanned_files == scanned_files
        assert worker.tmdb_api_key == "test-key"
        assert worker.omdb_api_key == "test-omdb"


class TestActionPlanWorker:
    """Tests for ActionPlanWorker."""
    
    @pytest.fixture
    def mock_qthread(self):
        """Mock QThread base class."""
        with patch('scripts.core.workers.QThread.__init__', return_value=None):
            yield
    
    @pytest.mark.unit
    def test_init_stores_parameters(self, mock_qthread):
        """Should store scanned files, LLM analysis, and canonical database."""
        scanned_files = []
        llm_analysis = {}
        canonical_db = {}
        
        worker = ActionPlanWorker(
            scanned_files=scanned_files,
            llm_analysis=llm_analysis,
            canonical_database=canonical_db
        )
        
        assert worker.scanned_files == scanned_files
        assert worker.llm_analysis == llm_analysis
        assert worker.canonical_database == canonical_db


class TestScanResultsLoadWorker:
    """Tests for ScanResultsLoadWorker."""
    
    @pytest.fixture
    def mock_qthread(self):
        """Mock QThread base class."""
        with patch('scripts.core.workers.QThread.__init__', return_value=None):
            yield
    
    @pytest.mark.unit
    def test_init_stores_parameters(self, mock_qthread, tmp_path):
        """Should store scan session ID and inventory repository."""
        from scripts.core.inventory_repository import InventoryRepository
        
        repo = InventoryRepository(str(tmp_path / "test.db"))
        worker = ScanResultsLoadWorker(
            scan_session_id=1,
            inventory_repo=repo
        )
        
        assert worker.scan_session_id == 1
        assert worker.inventory_repo == repo

