"""
Tests for JellyfinValidator and related validation classes.

Phase 59: JellyBase Code Quality Refinement - Phase 1 Test Infrastructure

Coverage Target: 85%+ line coverage
Test Count: 20 tests
"""
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from datetime import datetime

from scripts.core.jellyfin_validator import (
    JellyfinValidator,
    ValidationResult,
    ValidationIssue,
    VIDEO_EXTENSIONS
)
from scripts.core.jellyfin_client import JellyfinClient
from scripts.utils.transaction_manager import FileHasher


class TestValidationIssue:
    """Tests for ValidationIssue dataclass."""

    @pytest.mark.unit
    def test_create_critical_file_issue(self):
        """ValidationIssue should correctly store critical file issues."""
        issue = ValidationIssue(
            severity='critical',
            category='file',
            message='File does not exist',
            item_id='test-id-123',
            item_title='Test Movie (2023)'
        )

        assert issue.severity == 'critical'
        assert issue.category == 'file'
        assert issue.message == 'File does not exist'
        assert issue.item_id == 'test-id-123'
        assert issue.item_title == 'Test Movie (2023)'

    @pytest.mark.unit
    def test_create_warning_metadata_issue(self):
        """ValidationIssue should support warning severity for metadata."""
        issue = ValidationIssue(
            severity='warning',
            category='metadata',
            message='Missing TMDb ID',
            item_id='item-456',
            item_title='TV Show S01E01'
        )

        assert issue.severity == 'warning'
        assert issue.category == 'metadata'


class TestValidationResult:
    """Tests for ValidationResult dataclass."""

    @pytest.mark.unit
    def test_create_minimal_result(self):
        """ValidationResult should work with minimal required fields."""
        item = {'Id': 'test-id', 'Name': 'Test Movie', 'Path': '/movies/test.mkv'}
        result = ValidationResult(
            item=item,
            jellyfin_id='test-id',
            title='Test Movie',
            jellyfin_path='/movies/test.mkv',
            valid=True,
            issues=[]
        )

        assert result.jellyfin_id == 'test-id'
        assert result.title == 'Test Movie'
        assert result.valid is True
        assert result.issues == []
        assert result.subtitle_languages == []  # Post-init default

    @pytest.mark.unit
    def test_create_full_result(self):
        """ValidationResult should store all optional fields."""
        item = {'Id': 'id-1', 'Name': 'Movie', 'Path': '/test.mkv'}
        issues = [ValidationIssue('warning', 'metadata', 'Missing year', 'id-1', 'Movie')]

        result = ValidationResult(
            item=item,
            jellyfin_id='id-1',
            title='Movie',
            jellyfin_path='/test.mkv',
            valid=True,
            issues=issues,
            file_size=1024000,
            actual_path='/resolved/test.mkv',
            resolution='1080p',
            codec='hevc',
            has_subtitles=True,
            subtitle_languages=['en', 'es']
        )

        assert result.file_size == 1024000
        assert result.actual_path == '/resolved/test.mkv'
        assert result.resolution == '1080p'
        assert result.codec == 'hevc'
        assert result.has_subtitles is True
        assert result.subtitle_languages == ['en', 'es']

    @pytest.mark.unit
    def test_to_dict_conversion(self):
        """ValidationResult.to_dict() should convert to JSON-serializable dict."""
        item = {'Id': 'id-1', 'Name': 'Movie', 'Path': '/test.mkv'}
        issue = ValidationIssue('critical', 'file', 'Not found', 'id-1', 'Movie')

        result = ValidationResult(
            item=item,
            jellyfin_id='id-1',
            title='Movie',
            jellyfin_path='/test.mkv',
            valid=False,
            issues=[issue],
            file_size=2048,
            resolution='720p'
        )

        result_dict = result.to_dict()

        assert result_dict['jellyfin_id'] == 'id-1'
        assert result_dict['title'] == 'Movie'
        assert result_dict['valid'] is False
        assert len(result_dict['issues']) == 1
        assert result_dict['issues'][0]['severity'] == 'critical'
        assert result_dict['file_size'] == 2048


class TestJellyfinValidatorInit:
    """Tests for JellyfinValidator initialization."""

    @pytest.mark.unit
    def test_initialization_with_client(self):
        """JellyfinValidator should initialize with JellyfinClient."""
        mock_client = MagicMock(spec=JellyfinClient)

        validator = JellyfinValidator(mock_client)

        assert validator.client == mock_client
        assert isinstance(validator.hasher, FileHasher)

    @pytest.mark.unit
    def test_initialization_creates_hasher(self):
        """JellyfinValidator should create FileHasher instance."""
        mock_client = MagicMock(spec=JellyfinClient)

        validator = JellyfinValidator(mock_client)

        assert validator.hasher is not None
        assert hasattr(validator.hasher, 'calculate_hash')


class TestValidateItemBasic:
    """Tests for JellyfinValidator.validate_item() basic functionality."""

    @pytest.mark.unit
    def test_validate_item_with_valid_file(self, tmp_path):
        """validate_item() should pass for valid file."""
        # Create test file
        test_file = tmp_path / "test_movie.mkv"
        test_file.write_bytes(b"test video content")

        item = {
            'Id': 'valid-id',
            'Name': 'Test Movie',
            'Path': str(test_file),
            'Type': 'Movie'
        }

        mock_client = MagicMock(spec=JellyfinClient)
        validator = JellyfinValidator(mock_client)

        result = validator.validate_item(item, check_metadata=False,
                                        check_quality=False, check_subtitles=False)

        assert result.jellyfin_id == 'valid-id'
        assert result.title == 'Test Movie'
        assert result.valid is True
        assert len(result.issues) == 0

    @pytest.mark.unit
    def test_validate_item_missing_file(self):
        """validate_item() should fail for missing file."""
        item = {
            'Id': 'missing-id',
            'Name': 'Missing Movie',
            'Path': '/nonexistent/path/movie.mkv',
            'Type': 'Movie'
        }

        mock_client = MagicMock(spec=JellyfinClient)
        validator = JellyfinValidator(mock_client)

        result = validator.validate_item(item, check_metadata=False,
                                        check_quality=False, check_subtitles=False)

        assert result.valid is False
        assert len(result.issues) >= 1
        assert any(issue.severity == 'critical' for issue in result.issues)
        assert any('does not exist' in issue.message.lower() for issue in result.issues)

    @pytest.mark.unit
    def test_validate_item_no_path(self):
        """validate_item() should fail when no path in metadata."""
        item = {
            'Id': 'no-path-id',
            'Name': 'Movie Without Path',
            'Type': 'Movie'
            # No 'Path' key
        }

        mock_client = MagicMock(spec=JellyfinClient)
        validator = JellyfinValidator(mock_client)

        result = validator.validate_item(item, check_metadata=False,
                                        check_quality=False, check_subtitles=False)

        assert result.valid is False
        assert len(result.issues) == 1
        assert result.issues[0].severity == 'critical'
        assert 'No path' in result.issues[0].message

    @pytest.mark.unit
    def test_validate_item_path_is_directory(self, tmp_path):
        """validate_item() should fail when path points to directory."""
        test_dir = tmp_path / "movie_folder"
        test_dir.mkdir()

        item = {
            'Id': 'dir-id',
            'Name': 'Directory Not File',
            'Path': str(test_dir),
            'Type': 'Movie'
        }

        mock_client = MagicMock(spec=JellyfinClient)
        validator = JellyfinValidator(mock_client)

        result = validator.validate_item(item, check_metadata=False,
                                        check_quality=False, check_subtitles=False)

        assert result.valid is False
        assert any('directory' in issue.message.lower() for issue in result.issues)

    @pytest.mark.unit
    def test_validate_item_invalid_extension(self, tmp_path):
        """validate_item() should warn for non-video extension."""
        test_file = tmp_path / "not_video.txt"
        test_file.write_text("not a video")

        item = {
            'Id': 'txt-id',
            'Name': 'Text File',
            'Path': str(test_file),
            'Type': 'Movie'
        }

        mock_client = MagicMock(spec=JellyfinClient)
        validator = JellyfinValidator(mock_client)

        result = validator.validate_item(item, check_metadata=False,
                                        check_quality=False, check_subtitles=False)

        # Should have warning (not critical) for invalid extension
        assert len(result.issues) >= 1
        assert any(issue.category == 'file' for issue in result.issues)
        assert any('extension' in issue.message.lower() or '.txt' in issue.message for issue in result.issues)


class TestValidateItemMetadata:
    """Tests for metadata validation in validate_item()."""

    @pytest.mark.unit
    def test_metadata_check_missing_provider_ids(self, tmp_path):
        """validate_item() should detect missing ProviderIds."""
        test_file = tmp_path / "movie.mkv"
        test_file.write_bytes(b"video")

        item = {
            'Id': 'no-prov-id',
            'Name': 'Movie No TMDb',
            'Path': str(test_file),
            'Type': 'Movie'
            # No ProviderIds key
        }

        mock_client = MagicMock(spec=JellyfinClient)
        validator = JellyfinValidator(mock_client)

        result = validator.validate_item(item, check_metadata=True,
                                        check_quality=False, check_subtitles=False)

        # Should have metadata warning for missing ProviderIds
        metadata_issues = [i for i in result.issues if i.category == 'metadata']
        assert len(metadata_issues) >= 1

    @pytest.mark.unit
    def test_metadata_check_missing_year(self, tmp_path):
        """validate_item() should detect missing production year."""
        test_file = tmp_path / "movie.mkv"
        test_file.write_bytes(b"video")

        item = {
            'Id': 'no-year-id',
            'Name': 'Movie No Year',
            'Path': str(test_file),
            'Type': 'Movie',
            'ProviderIds': {'Tmdb': '12345'}
            # No ProductionYear key
        }

        mock_client = MagicMock(spec=JellyfinClient)
        validator = JellyfinValidator(mock_client)

        result = validator.validate_item(item, check_metadata=True,
                                        check_quality=False, check_subtitles=False)

        # Should detect missing year
        metadata_issues = [i for i in result.issues if i.category == 'metadata']
        assert any('year' in i.message.lower() or 'productionyear' in i.message.lower()
                   for i in metadata_issues)

    @pytest.mark.unit
    def test_metadata_check_complete(self, tmp_path):
        """validate_item() should pass with complete metadata."""
        test_file = tmp_path / "movie.mkv"
        test_file.write_bytes(b"video")

        item = {
            'Id': 'complete-id',
            'Name': 'Complete Movie',
            'Path': str(test_file),
            'Type': 'Movie',
            'ProviderIds': {'Tmdb': '12345'},
            'ProductionYear': 2023,
            'Genres': ['Action', 'Adventure'],
            'Overview': 'A thrilling adventure movie'
        }

        mock_client = MagicMock(spec=JellyfinClient)
        validator = JellyfinValidator(mock_client)

        result = validator.validate_item(item, check_metadata=True,
                                        check_quality=False, check_subtitles=False)

        # Should have no metadata issues
        metadata_issues = [i for i in result.issues if i.category == 'metadata']
        assert len(metadata_issues) == 0


class TestValidateItemQuality:
    """Tests for quality analysis in validate_item()."""

    @pytest.mark.unit
    def test_quality_analysis_extracts_resolution(self, tmp_path):
        """validate_item() should extract video resolution."""
        test_file = tmp_path / "movie_1080p.mkv"
        test_file.write_bytes(b"video")

        item = {
            'Id': 'quality-id',
            'Name': 'HD Movie',
            'Path': str(test_file),
            'Type': 'Movie',
            'MediaSources': [
                {
                    'MediaStreams': [
                        {'Type': 'Video', 'Width': 1920, 'Height': 1080, 'Codec': 'h264'}
                    ]
                }
            ]
        }

        mock_client = MagicMock(spec=JellyfinClient)
        validator = JellyfinValidator(mock_client)

        result = validator.validate_item(item, check_metadata=False,
                                        check_quality=True, check_subtitles=False)

        # Should extract resolution
        assert result.resolution is not None
        assert '1080' in result.resolution or result.resolution == '1080p'

    @pytest.mark.unit
    def test_quality_analysis_extracts_codec(self, tmp_path):
        """validate_item() should extract video codec."""
        test_file = tmp_path / "movie_hevc.mkv"
        test_file.write_bytes(b"video")

        item = {
            'Id': 'codec-id',
            'Name': 'HEVC Movie',
            'Path': str(test_file),
            'Type': 'Movie',
            'MediaSources': [
                {
                    'MediaStreams': [
                        {'Type': 'Video', 'Width': 1920, 'Height': 1080, 'Codec': 'hevc'}
                    ]
                }
            ]
        }

        mock_client = MagicMock(spec=JellyfinClient)
        validator = JellyfinValidator(mock_client)

        result = validator.validate_item(item, check_metadata=False,
                                        check_quality=True, check_subtitles=False)

        # Should extract codec
        assert result.codec is not None
        assert 'hevc' in result.codec.lower() or 'h265' in result.codec.lower()


class TestValidateItemSubtitles:
    """Tests for subtitle coverage validation in validate_item()."""

    @pytest.mark.unit
    def test_subtitle_check_detects_english(self, tmp_path):
        """validate_item() should detect English subtitles."""
        test_file = tmp_path / "movie_with_subs.mkv"
        test_file.write_bytes(b"video")

        item = {
            'Id': 'subs-id',
            'Name': 'Movie With Subs',
            'Path': str(test_file),
            'Type': 'Movie',
            'MediaSources': [
                {
                    'MediaStreams': [
                        {'Type': 'Video', 'Width': 1920, 'Height': 1080, 'Codec': 'h264'},
                        {'Type': 'Subtitle', 'Language': 'eng', 'DisplayTitle': 'English'}
                    ]
                }
            ]
        }

        mock_client = MagicMock(spec=JellyfinClient)
        validator = JellyfinValidator(mock_client)

        result = validator.validate_item(item, check_metadata=False,
                                        check_quality=False, check_subtitles=True)

        assert result.has_subtitles is True
        assert 'eng' in result.subtitle_languages or 'en' in result.subtitle_languages

    @pytest.mark.unit
    def test_subtitle_check_no_subtitles(self, tmp_path):
        """validate_item() should detect missing subtitles."""
        test_file = tmp_path / "movie_no_subs.mkv"
        test_file.write_bytes(b"video")

        item = {
            'Id': 'no-subs-id',
            'Name': 'Movie No Subs',
            'Path': str(test_file),
            'Type': 'Movie',
            'MediaStreams': [
                {'Type': 'Video', 'Width': 1920, 'Height': 1080, 'Codec': 'h264'}
            ]
        }

        mock_client = MagicMock(spec=JellyfinClient)
        validator = JellyfinValidator(mock_client)

        result = validator.validate_item(item, check_metadata=False,
                                        check_quality=False, check_subtitles=True)

        assert result.has_subtitles is False
        assert result.subtitle_languages == []


# Mark this test file for pytest collection
pytest_plugins = []
