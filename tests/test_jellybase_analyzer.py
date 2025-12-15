"""
Tests for JellyBase analyzer functions.

Phase 59: JellyBase Code Quality Refinement - Phase 1 Test Infrastructure

Coverage Target: 85%+ line coverage
Test Count: 12 tests
"""
import pytest
from unittest.mock import MagicMock, patch
from scripts.core.jellybase_analyzer import (
    detect_content_duplicates,
    analyze_quality_distribution,
    analyze_coverage,
    calculate_health_score
)
from scripts.core.jellyfin_client import JellyfinClient
from scripts.core.jellyfin_validator import JellyfinValidator


class TestDetectContentDuplicates:
    """Tests for detect_content_duplicates()."""

    @pytest.mark.unit
    def test_detect_content_duplicates_delegates_to_validator(self):
        """detect_content_duplicates() should delegate to JellyfinValidator."""
        mock_client = MagicMock(spec=JellyfinClient)
        items = [{'Id': 'item-1'}, {'Id': 'item-2'}]
        
        # Mock validator's detect_content_duplicates
        with patch('scripts.core.jellybase_analyzer.JellyfinValidator') as MockValidator:
            mock_validator_instance = MagicMock()
            mock_validator_instance.detect_content_duplicates.return_value = [
                ('hash-123', ['item-1', 'item-2'])
            ]
            MockValidator.return_value = mock_validator_instance
            
            result = detect_content_duplicates(mock_client, items)
            
            assert len(result) == 1
            assert result[0][0] == 'hash-123'
            assert result[0][1] == ['item-1', 'item-2']
            MockValidator.assert_called_once_with(mock_client)

    @pytest.mark.unit
    def test_detect_content_duplicates_returns_empty_on_error(self):
        """detect_content_duplicates() should return empty list on error."""
        mock_client = MagicMock(spec=JellyfinClient)
        items = [{'Id': 'item-1'}]
        
        with patch('scripts.core.jellybase_analyzer.JellyfinValidator') as MockValidator:
            MockValidator.side_effect = Exception("Validator error")
            
            result = detect_content_duplicates(mock_client, items)
            
            assert result == []


class TestAnalyzeQualityDistribution:
    """Tests for analyze_quality_distribution()."""

    @pytest.mark.unit
    def test_analyze_quality_distribution_4k(self):
        """analyze_quality_distribution() should detect 4K resolution."""
        mock_client = MagicMock(spec=JellyfinClient)
        items = [{
            'Id': 'item-1',
            'MediaSources': [{
                'MediaStreams': [
                    {'Type': 'Video', 'Width': 3840, 'Height': 2160, 'Codec': 'hevc'}
                ]
            }]
        }]
        
        result = analyze_quality_distribution(mock_client, items)
        
        assert result['total_items'] == 1
        assert result['resolution_distribution']['4K'] == 1
        assert result['codec_distribution']['hevc'] == 1

    @pytest.mark.unit
    def test_analyze_quality_distribution_1080p(self):
        """analyze_quality_distribution() should detect 1080p resolution."""
        mock_client = MagicMock(spec=JellyfinClient)
        items = [{
            'Id': 'item-1',
            'MediaSources': [{
                'MediaStreams': [
                    {'Type': 'Video', 'Width': 1920, 'Height': 1080, 'Codec': 'h264'}
                ]
            }]
        }]
        
        result = analyze_quality_distribution(mock_client, items)
        
        assert result['total_items'] == 1
        assert result['resolution_distribution']['1080p'] == 1
        assert result['codec_distribution']['h264'] == 1

    @pytest.mark.unit
    def test_analyze_quality_distribution_720p(self):
        """analyze_quality_distribution() should detect 720p resolution."""
        mock_client = MagicMock(spec=JellyfinClient)
        items = [{
            'Id': 'item-1',
            'MediaSources': [{
                'MediaStreams': [
                    {'Type': 'Video', 'Width': 1280, 'Height': 720, 'Codec': 'h264'}
                ]
            }]
        }]
        
        result = analyze_quality_distribution(mock_client, items)
        
        assert result['total_items'] == 1
        assert result['resolution_distribution']['720p'] == 1

    @pytest.mark.unit
    def test_analyze_quality_distribution_multiple_items(self):
        """analyze_quality_distribution() should aggregate multiple items."""
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
                        {'Type': 'Video', 'Width': 1920, 'Height': 1080, 'Codec': 'hevc'}
                    ]
                }]
            }
        ]
        
        result = analyze_quality_distribution(mock_client, items)
        
        assert result['total_items'] == 2
        assert result['resolution_distribution']['1080p'] == 2
        assert result['codec_distribution']['h264'] == 1
        assert result['codec_distribution']['hevc'] == 1

    @pytest.mark.unit
    def test_analyze_quality_distribution_no_media_sources(self):
        """analyze_quality_distribution() should handle items without MediaSources."""
        mock_client = MagicMock(spec=JellyfinClient)
        items = [{'Id': 'item-1'}]  # No MediaSources
        
        result = analyze_quality_distribution(mock_client, items)
        
        assert result['total_items'] == 0
        assert result['resolution_distribution'] == {}
        assert result['codec_distribution'] == {}


class TestAnalyzeCoverage:
    """Tests for analyze_coverage()."""

    @pytest.mark.unit
    def test_analyze_coverage_calculates_percentages(self):
        """analyze_coverage() should calculate coverage percentages."""
        mock_client = MagicMock(spec=JellyfinClient)
        items = [
            {
                'Id': 'item-1',
                'ProviderIds': {'tmdb': '123'},
                'Overview': 'Movie description',
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
                # Missing ProviderIds, Overview, Year, Genres, Subtitles
                'MediaSources': [{
                    'MediaStreams': []
                }]
            }
        ]
        
        result = analyze_coverage(mock_client, items)
        
        assert result['total_items'] == 2
        assert result['metadata_coverage']['provider_ids']['missing'] == 1
        assert result['metadata_coverage']['provider_ids']['coverage_percent'] == 50.0
        assert result['subtitle_coverage']['missing'] == 1
        assert result['subtitle_coverage']['coverage_percent'] == 50.0

    @pytest.mark.unit
    def test_analyze_coverage_empty_items(self):
        """analyze_coverage() should handle empty items list."""
        mock_client = MagicMock(spec=JellyfinClient)
        items = []
        
        result = analyze_coverage(mock_client, items)
        
        assert result['total_items'] == 0
        assert result['metadata_coverage']['provider_ids']['coverage_percent'] == 0


class TestCalculateHealthScore:
    """Tests for calculate_health_score()."""

    @pytest.mark.unit
    def test_calculate_health_score_perfect_library(self):
        """calculate_health_score() should return 100 for perfect library."""
        mock_validator = MagicMock(spec=JellyfinValidator)
        
        # Create perfect validation results
        perfect_result = MagicMock()
        perfect_result.valid = True
        perfect_result.has_subtitles = True
        perfect_result.item = {
            'ProviderIds': {'tmdb': '123'},
            'Overview': 'Description',
            'ProductionYear': 2020
        }
        
        mock_validator.validate_item.return_value = perfect_result
        items = [{'Id': f'item-{i}'} for i in range(10)]
        
        score = calculate_health_score(mock_validator, items)
        
        # Should be close to 100 (file: 40, metadata: 30, subtitles: 20, duplicates: 10)
        assert score == 100

    @pytest.mark.unit
    def test_calculate_health_score_empty_library(self):
        """calculate_health_score() should return 0 for empty library."""
        mock_validator = MagicMock(spec=JellyfinValidator)
        items = []
        
        score = calculate_health_score(mock_validator, items)
        
        assert score == 0

    @pytest.mark.unit
    def test_calculate_health_score_samples_first_100(self):
        """calculate_health_score() should sample first 100 items for performance."""
        mock_validator = MagicMock(spec=JellyfinValidator)
        
        perfect_result = MagicMock()
        perfect_result.valid = True
        perfect_result.has_subtitles = True
        perfect_result.item = {
            'ProviderIds': {'tmdb': '123'},
            'Overview': 'Description',
            'ProductionYear': 2020
        }
        mock_validator.validate_item.return_value = perfect_result
        
        # Create 150 items
        items = [{'Id': f'item-{i}'} for i in range(150)]
        
        score = calculate_health_score(mock_validator, items)
        
        # Should only call validate_item 100 times (first 100 items)
        assert mock_validator.validate_item.call_count == 100
        assert score == 100
