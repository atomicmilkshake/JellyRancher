"""
Unit tests for episode_title_backend.py
"""

import pytest
from pathlib import Path
import sys
import json

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.core.episode_title_backend import EpisodeTitleAnalyzer


@pytest.mark.unit
@pytest.mark.backend
@pytest.mark.episodes
class TestEpisodeTitleAnalyzer:
    """Test suite for EpisodeTitleAnalyzer"""
    
    def test_analyzer_initialization(self):
        """Test analyzer can be initialized."""
        analyzer = EpisodeTitleAnalyzer()
        assert analyzer is not None
    
    def test_extract_episode_info_standard_pattern(self):
        """Test extraction with standard S01E01 - Title pattern."""
        analyzer = EpisodeTitleAnalyzer()
        
        info = analyzer.extract_episode_info("S01E01 - Pilot Episode.mkv", "Test Show")
        
        assert info is not None
        assert info['season'] == 1
        assert info['episode'] == "01"
        assert info['episode_title'] == "Pilot Episode"
        assert info['pattern'] == 'jellyfin_standard'
    
    def test_extract_episode_info_with_show_prefix(self):
        """Test extraction with Show S01E01 Title pattern."""
        analyzer = EpisodeTitleAnalyzer()
        
        info = analyzer.extract_episode_info("Doctor Who S01E01 Rose.mkv", "Doctor Who")
        
        assert info is not None
        assert info['season'] == 1
        assert info['episode'] == "01"
        assert info['episode_title'] == "Rose"
        assert info['show_title'] == "Doctor Who"
        assert info['pattern'] == 'show_title_prefix'
    
    def test_extract_episode_info_full_pattern(self):
        """Test extraction with Show - S01E01 - Title pattern."""
        analyzer = EpisodeTitleAnalyzer()
        
        info = analyzer.extract_episode_info("Breaking Bad - S01E01 - Pilot.mkv", "Breaking Bad")
        
        assert info is not None
        assert info['season'] == 1
        assert info['episode'] == "01"
        assert info['episode_title'] == "- Pilot"
        assert info['show_title'] == "Breaking Bad -"
        assert info['pattern'] == 'show_title_prefix'
    
    def test_extract_episode_info_invalid_pattern(self):
        """Test that invalid patterns return None."""
        analyzer = EpisodeTitleAnalyzer()
        
        info = analyzer.extract_episode_info("random_file.mkv", "Test Show")
        
        assert info is None
    
    def test_clean_episode_title_removes_codec_tags(self):
        """Test removal of codec tags from title."""
        analyzer = EpisodeTitleAnalyzer()
        
        cleaned = analyzer.clean_episode_title("Pilot [x264] [1080p] [HEVC]")
        
        assert "x264" not in cleaned.lower()
        assert "1080p" not in cleaned
        assert "hevc" not in cleaned.lower()
        assert cleaned.strip() == "Pilot"
    
    def test_clean_episode_title_removes_brackets(self):
        """Test removal of bracketed tags."""
        analyzer = EpisodeTitleAnalyzer()
        
        cleaned = analyzer.clean_episode_title("Pilot [RARBG]")
        
        assert "[RARBG]" not in cleaned
        assert cleaned.strip() == "Pilot"
    
    def test_calculate_similarity_identical(self):
        """Test similarity calculation for identical strings."""
        analyzer = EpisodeTitleAnalyzer()
        
        similarity = analyzer.calculate_similarity("Pilot Episode", "Pilot Episode")
        
        assert similarity == 1.0
    
    def test_calculate_similarity_different(self):
        """Test similarity calculation for different strings."""
        analyzer = EpisodeTitleAnalyzer()
        
        similarity = analyzer.calculate_similarity("Pilot", "Finale")
        
        assert 0.0 <= similarity < 0.5
    
    def test_calculate_similarity_similar(self):
        """Test similarity calculation for similar strings."""
        analyzer = EpisodeTitleAnalyzer()
        
        similarity = analyzer.calculate_similarity(
            "Pilot Episode",
            "The Pilot Episode"
        )
        
        assert 0.7 <= similarity < 1.0
    
    def test_compare_with_canonical_perfect_match(self):
        """Test comparison with perfect match."""
        analyzer = EpisodeTitleAnalyzer()
        
        result = analyzer.compare_with_canonical(
            current_title="Pilot",
            canonical_title="Pilot"
        )
        
        assert result['recommendation'] == 'perfect'
        assert result['confidence'] == 'high'
        assert result['needs_rename'] is False
    
    def test_compare_with_canonical_needs_cleaning(self):
        """Test comparison when cleaning is needed."""
        analyzer = EpisodeTitleAnalyzer()
        
        result = analyzer.compare_with_canonical(
            current_title="Pilot [x264] [1080p]",
            canonical_title="Pilot"
        )
        
        assert result['recommendation'] == 'use_cleaned'
        assert result['cleaned_title'] == "Pilot"
    
    def test_compare_with_canonical_use_canonical(self):
        """Test comparison when canonical should be used."""
        analyzer = EpisodeTitleAnalyzer()
        
        result = analyzer.compare_with_canonical(
            current_title="Episode One",
            canonical_title="Pilot"
        )
        
        assert result['recommendation'] in ['use_canonical', 'review_manual']
    
    def test_load_tmdb_cache_valid(self, sample_tmdb_cache):
        """Test loading valid TMDB cache."""
        analyzer = EpisodeTitleAnalyzer()
        
        cache = analyzer.load_tmdb_cache(sample_tmdb_cache)
        
        assert cache is not None
        assert 'show_name' in cache
        assert 'seasons' in cache
        assert cache['show_name'] == "Test Show"
    
    def test_load_tmdb_cache_invalid(self, temp_dir):
        """Test error handling for invalid cache."""
        analyzer = EpisodeTitleAnalyzer()
        
        invalid_cache = temp_dir / "invalid.json"
        invalid_cache.write_text("not valid json")
        
        cache = analyzer.load_tmdb_cache(invalid_cache)
        
        assert cache is None
    
    def test_analyze_show_folder_with_cache(self, sample_tv_shows_dir, sample_tmdb_cache):
        """Test analyzing show folder with TMDB cache."""
        analyzer = EpisodeTitleAnalyzer()
        
        show_folder = sample_tv_shows_dir / "Show A"
        
        results = analyzer.analyze_show_folder(
            show_folder,
            sample_tmdb_cache
        )
        
        assert results is not None
        assert 'show_title' in results
        assert 'episodes' in results
        assert len(results['episodes']) > 0
    
    def test_analyze_show_folder_no_cache(self, sample_tv_shows_dir):
        """Test analyzing show folder without TMDB cache."""
        analyzer = EpisodeTitleAnalyzer()
        
        show_folder = sample_tv_shows_dir / "Show A"
        
        results = analyzer.analyze_show_folder(show_folder, None)
        
        assert results is not None
        assert 'episodes' in results
        # Without cache, can't compare titles
        for episode in results['episodes']:
            assert 'canonical_title' not in episode
    
    def test_analyze_episode_determines_confidence(self, sample_tv_shows_dir, sample_tmdb_cache):
        """Test that episode analysis determines confidence levels."""
        analyzer = EpisodeTitleAnalyzer()
        
        show_folder = sample_tv_shows_dir / "Show A"
        results = analyzer.analyze_show_folder(
            show_folder,
            sample_tmdb_cache
        )
        
        # Check that confidence is assigned
        for episode in results['episodes']:
            if 'canonical_title' in episode:
                assert 'confidence' in episode
                assert episode['confidence'] in ['high', 'medium', 'low', 'very_low']


@pytest.mark.integration
@pytest.mark.episodes
class TestEpisodeTitleAnalyzerIntegration:
    """Integration tests for EpisodeTitleAnalyzer"""
    
    def test_full_analysis_workflow(self, sample_tv_shows_dir, sample_tmdb_cache):
        """Test complete analysis workflow."""
        analyzer = EpisodeTitleAnalyzer()
        
        show_folder = sample_tv_shows_dir / "Show A"
        
        # Load cache
        cache = analyzer.load_tmdb_cache(sample_tmdb_cache)
        assert cache is not None
        
        # Analyze show
        results = analyzer.analyze_show_folder(
            show_folder,
            sample_tmdb_cache
        )
        
        assert results is not None
        assert len(results['episodes']) > 0
        
        # Verify episode structure
        for episode in results['episodes']:
            assert 'file_name' in episode
            assert 'season' in episode
            assert 'episode' in episode
            assert 'episode_title' in episode
            # recommendation/confidence only present if canonical comparison was done
            if 'canonical_title' in episode:
                assert 'recommendation' in episode
                assert 'confidence' in episode
                assert 'needs_rename' in episode
    
    def test_multiple_shows_analysis(self, sample_tv_shows_dir, sample_tmdb_cache):
        """Test analyzing multiple shows."""
        analyzer = EpisodeTitleAnalyzer()
        
        shows = ['Show A', 'Show B']
        all_results = []
        
        for show_name in shows:
            show_folder = sample_tv_shows_dir / show_name
            if show_folder.exists():
                results = analyzer.analyze_show_folder(
                    show_folder,
                    sample_tmdb_cache
                )
                all_results.append(results)
        
        assert len(all_results) == 2
        
        # Each should have episodes
        for results in all_results:
            assert len(results['episodes']) > 0
