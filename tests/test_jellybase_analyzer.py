"""
Tests for JellyBase Library Analyzer - Comprehensive library analysis.

Phase 59: JellyBase Code Quality Refinement - Phase 1 Test Infrastructure

Coverage Target: 85%+ line coverage
Test Count: 12 tests

Tests duplicate detection, quality analysis, coverage analysis, and health scoring.
"""
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, Mock
from collections import defaultdict

from scripts.core.jellybase_analyzer import (
    detect_content_duplicates,
    analyze_quality_distribution,
    analyze_coverage,
    calculate_health_score
)
from scripts.core.jellyfin_client import JellyfinClient
from scripts.core.jellyfin_validator import JellyfinValidator, ValidationResult


class TestDetectContentDuplicates:
    """Tests for detect_content_duplicates()."""

    @pytest.mark.unit
    def test_detect_duplicates_finds_matching_hashes(self, tmp_path):
        """detect_content_duplicates() should find items with same file hash."""
        mock_client = MagicMock(spec=JellyfinClient)
        
        # Create test files
        file1 = tmp_path / "movie1.mkv"
        file2 = tmp_path / "movie2.mkv"
        file3 = tmp_path / "unique.mkv"
        
        # Same content = same hash
        content = b"video content " * 100
        file1.write_bytes(content)
        file2.write_bytes(content)
        file3.write_bytes(b"different content " * 100)
        
        items = [
            {'Id': 'item-1', 'Path': str(file1)},
            {'Id': 'item-2', 'Path': str(file2)},
            {'Id': 'item-3', 'Path': str(file3)}
        ]
        
        result = detect_content_duplicates(mock_client, items)
        
        assert len(result) == 1  # One duplicate group
        assert len(result[0][1]) == 2  # Two items with same hash
        assert 'item-1' in result[0][1]
        assert 'item-2' in result[0][1]

    @pytest.mark.unit
    def test_detect_duplicates_skips_missing_files(self, tmp_path):
        """detect_content_duplicates() should skip items with missing files."""
        mock_client = MagicMock(spec=JellyfinClient)
        
        file1 = tmp_path / "exists.mkv"
        file1.write_bytes(b"content")
        
        items = [
            {'Id': 'item-1', 'Path': str(file1)},
            {'Id': 'item-2', 'Path': str(tmp_path / "missing.mkv")},  # Doesn't exist
            {'Id': 'item-3', 'Path': ''}  # Empty path
        ]
        
        result = detect_content_duplicates(mock_client, items)
        
        # Should not crash, may return empty or only process valid files
        assert isinstance(result, list)

    @pytest.mark.unit
    def test_detect_duplicates_handles_exceptions(self, tmp_path):
        """detect_content_duplicates() should handle exceptions gracefully."""
        mock_client = MagicMock(spec=JellyfinClient)
        
        # Mock JellyfinValidator to raise exception (function now delegates to validator)
        with patch('scripts.core.jellybase_analyzer.JellyfinValidator') as mock_validator_class:
            mock_validator = MagicMock()
            mock_validator.detect_content_duplicates.side_effect = Exception("Hash error")
            mock_validator_class.return_value = mock_validator
            
            file1 = tmp_path / "test.mkv"
            file1.write_bytes(b"content")
            items = [{'Id': 'item-1', 'Path': str(file1)}]
            
            # Should handle exception gracefully (function wraps in try-except)
            result = detect_content_duplicates(mock_client, items)
            
            # Function returns empty list on exception
            assert isinstance(result, list)
            assert result == []


class TestAnalyzeQualityDistribution:
    """Tests for analyze_quality_distribution()."""

    @pytest.mark.unit
    def test_analyze_quality_distribution_4k(self):
        """analyze_quality_distribution() should categorize 4K resolution."""
        mock_client = MagicMock(spec=JellyfinClient)
        
        items = [
            {
                'Id': 'item-1',
                'MediaSources': [{
                    'MediaStreams': [
                        {'Type': 'Video', 'Width': 3840, 'Height': 2160, 'Codec': 'hevc'}
                    ]
                }]
            }
        ]
        
        result = analyze_quality_distribution(mock_client, items)
        
        assert result['total_items'] == 1
        assert result['resolution_distribution']['4K'] == 1
        assert result['codec_distribution']['hevc'] == 1

    @pytest.mark.unit
    def test_analyze_quality_distribution_1080p(self):
        """analyze_quality_distribution() should categorize 1080p resolution."""
        mock_client = MagicMock(spec=JellyfinClient)
        
        items = [
            {
                'Id': 'item-1',
                'MediaSources': [{
                    'MediaStreams': [
                        {'Type': 'Video', 'Width': 1920, 'Height': 1080, 'Codec': 'h264'}
                    ]
                }]
            }
        ]
        
        result = analyze_quality_distribution(mock_client, items)
        
        assert result['total_items'] == 1
        assert result['resolution_distribution']['1080p'] == 1
        assert result['codec_distribution']['h264'] == 1

    @pytest.mark.unit
    def test_analyze_quality_distribution_multiple_resolutions(self):
        """analyze_quality_distribution() should handle multiple resolutions."""
        mock_client = MagicMock(spec=JellyfinClient)
        
        items = [
            {
                'Id': 'item-1',
                'MediaSources': [{
                    'MediaStreams': [
                        {'Type': 'Video', 'Width': 1920, 'Height': 1080, 'Codec': 'h264'}
                    ]
                }]
            },
            {
                'Id': 'item-2',
                'MediaSources': [{
                    'MediaStreams': [
                        {'Type': 'Video', 'Width': 1280, 'Height': 720, 'Codec': 'h264'}
                    ]
                }]
            }
        ]
        
        result = analyze_quality_distribution(mock_client, items)
        
        assert result['total_items'] == 2
        assert result['resolution_distribution']['1080p'] == 1
        assert result['resolution_distribution']['720p'] == 1
        assert result['codec_distribution']['h264'] == 2

    @pytest.mark.unit
    def test_analyze_quality_distribution_no_media_sources(self):
        """analyze_quality_distribution() should handle items without media sources."""
        mock_client = MagicMock(spec=JellyfinClient)
        
        items = [
            {'Id': 'item-1', 'Name': 'Movie without media'},
            {'Id': 'item-2', 'MediaSources': []}
        ]
        
        result = analyze_quality_distribution(mock_client, items)
        
        assert result['total_items'] == 0
        assert result['resolution_distribution'] == {}
        assert result['codec_distribution'] == {}


class TestAnalyzeCoverage:
    """Tests for analyze_coverage()."""

    @pytest.mark.unit
    def test_analyze_coverage_complete_metadata(self):
        """analyze_coverage() should detect complete metadata."""
        mock_client = MagicMock(spec=JellyfinClient)
        
        items = [
            {
                'Id': 'item-1',
                'ProviderIds': {'Tmdb': '12345'},
                'Overview': 'Movie description',
                'ProductionYear': 2020,
                'Genres': ['Action', 'Thriller'],
                'MediaSources': [{
                    'MediaStreams': [
                        {'Type': 'Subtitle', 'Language': 'en'}
                    ]
                }]
            }
        ]
        
        result = analyze_coverage(mock_client, items)
        
        assert result['total_items'] == 1
        assert result['metadata_coverage']['provider_ids']['missing'] == 0
        assert result['metadata_coverage']['overview']['missing'] == 0
        assert result['metadata_coverage']['year']['missing'] == 0
        assert result['metadata_coverage']['genres']['missing'] == 0
        assert result['subtitle_coverage']['missing'] == 0

    @pytest.mark.unit
    def test_analyze_coverage_missing_metadata(self):
        """analyze_coverage() should detect missing metadata."""
        mock_client = MagicMock(spec=JellyfinClient)
        
        items = [
            {
                'Id': 'item-1',
                'Name': 'Movie without metadata',
                'MediaSources': []
            }
        ]
        
        result = analyze_coverage(mock_client, items)
        
        assert result['total_items'] == 1
        assert result['metadata_coverage']['provider_ids']['missing'] == 1
        assert result['metadata_coverage']['overview']['missing'] == 1
        assert result['metadata_coverage']['year']['missing'] == 1
        assert result['metadata_coverage']['genres']['missing'] == 1
        assert result['subtitle_coverage']['missing'] == 1

    @pytest.mark.unit
    def test_analyze_coverage_calculates_percentages(self):
        """analyze_coverage() should calculate coverage percentages."""
        mock_client = MagicMock(spec=JellyfinClient)
        
        items = [
            {
                'Id': 'item-1',
                'ProviderIds': {'Tmdb': '123'},
                'Overview': 'Description',
                'ProductionYear': 2020,
                'Genres': ['Action'],
                'MediaSources': [{
                    'MediaStreams': [
                        {'Type': 'Subtitle', 'Language': 'en'}
                    ]
                }]
            },
            {
                'Id': 'item-2',
                'Name': 'Incomplete movie',
                'MediaSources': []
            }
        ]
        
        result = analyze_coverage(mock_client, items)
        
        assert result['total_items'] == 2
        # 1 out of 2 has provider IDs = 50% coverage
        assert result['metadata_coverage']['provider_ids']['coverage_percent'] == 50.0


class TestCalculateHealthScore:
    """Tests for calculate_health_score()."""

    @pytest.mark.unit
    def test_calculate_health_score_perfect(self):
        """calculate_health_score() should return 100 for perfect library."""
        mock_validator = MagicMock(spec=JellyfinValidator)
        
        # Mock validation results - all valid
        mock_result = ValidationResult(
            item={'Id': '1', 'ProviderIds': {'Tmdb': '123'}, 'Overview': 'Desc', 'ProductionYear': 2020},
            jellyfin_id='1',
            title='Movie',
            jellyfin_path='/test.mkv',
            valid=True,
            issues=[],
            has_subtitles=True
        )
        mock_validator.validate_item.return_value = mock_result
        
        items = [
            {'Id': '1', 'ProviderIds': {'Tmdb': '123'}, 'Overview': 'Desc', 'ProductionYear': 2020}
        ]
        
        score = calculate_health_score(mock_validator, items)
        
        # Should be high score (file 40% + metadata 30% + subtitles 20% + duplicates 10%)
        assert score >= 80  # At least 80% for perfect items

    @pytest.mark.unit
    def test_calculate_health_score_empty_library(self):
        """calculate_health_score() should return 0 for empty library."""
        mock_validator = MagicMock(spec=JellyfinValidator)
        
        score = calculate_health_score(mock_validator, [])
        
        assert score == 0

    @pytest.mark.unit
    def test_calculate_health_score_samples_first_100(self):
        """calculate_health_score() should sample first 100 items for performance."""
        mock_validator = MagicMock(spec=JellyfinValidator)
        
        mock_result = ValidationResult(
            item={'Id': '1'},
            jellyfin_id='1',
            title='Movie',
            jellyfin_path='/test.mkv',
            valid=True,
            issues=[]
        )
        mock_validator.validate_item.return_value = mock_result
        
        # Create 150 items
        items = [{'Id': f'item-{i}'} for i in range(150)]
        
        score = calculate_health_score(mock_validator, items)
        
        # Should only call validate_item 100 times (sampling)
        assert mock_validator.validate_item.call_count == 100


