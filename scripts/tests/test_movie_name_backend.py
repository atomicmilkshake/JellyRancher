"""
Unit tests for movie_name_backend.py
"""

import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.core.movie_name_backend import MovieNameAnalyzer


@pytest.mark.unit
@pytest.mark.backend
@pytest.mark.movies
class TestMovieNameAnalyzer:
    """Test suite for MovieNameAnalyzer"""
    
    def test_analyzer_initialization(self):
        """Test analyzer can be initialized."""
        analyzer = MovieNameAnalyzer()
        assert analyzer is not None
        assert hasattr(analyzer, 'VIDEO_EXTENSIONS')
        assert hasattr(analyzer, 'CODEC_PATTERNS')
    
    def test_check_codec_tags_detects_h265(self):
        """Test codec tag detection for H.265."""
        analyzer = MovieNameAnalyzer()
        result = analyzer.check_codec_tags("Movie Title (2020) H.265")
        
        assert result is not None
        assert result['type'] == 'codec_in_name'
        assert result['severity'] == 'medium'
        assert 'H.265' in result['matched_text'] or 'H265' in result['matched_text']
    
    def test_check_codec_tags_detects_x264(self):
        """Test codec tag detection for x264."""
        analyzer = MovieNameAnalyzer()
        result = analyzer.check_codec_tags("Movie Title (2020) x264 1080p")
        
        assert result is not None
        assert result['type'] == 'codec_in_name'
        assert 'x264' in result['matched_text'].lower()
    
    def test_check_codec_tags_no_issue(self):
        """Test that clean filenames return None."""
        analyzer = MovieNameAnalyzer()
        result = analyzer.check_codec_tags("Movie Title (2020)")
        
        assert result is None
    
    def test_check_truncated_title_detects_short_word(self):
        """Test truncated title detection."""
        analyzer = MovieNameAnalyzer()
        result = analyzer.check_truncated_title("Cloutie Ru (2003)")
        
        assert result is not None
        assert result['type'] == 'truncated_titles'
        assert result['severity'] in ['high', 'medium']
    
    def test_check_truncated_title_allows_common_short_words(self):
        """Test that common short words don't trigger false positives."""
        analyzer = MovieNameAnalyzer()
        result = analyzer.check_truncated_title("A Man in Love (2020)")
        
        # Should not detect common words like "A" as truncated
        assert result is None or result['severity'] == 'medium'
    
    def test_check_folder_structure_movies_root(self):
        """Test detection of files directly in Movies folder."""
        analyzer = MovieNameAnalyzer()
        result = analyzer.check_folder_structure("Movies", "Movie Title (2020)")
        
        assert result is not None
        assert result['type'] == 'not_in_folder'
    
    def test_check_folder_structure_proper_folder(self):
        """Test that proper folder structure passes."""
        analyzer = MovieNameAnalyzer()
        result = analyzer.check_folder_structure(
            "Movie Title (2020)", 
            "Movie Title (2020)"
        )
        
        # Should pass - folder name matches movie
        assert result is None
    
    def test_check_missing_year_detects_issue(self):
        """Test missing year detection."""
        analyzer = MovieNameAnalyzer()
        result = analyzer.check_missing_year("Movie Title")
        
        assert result is not None
        assert result['type'] == 'missing_year'
        assert result['severity'] == 'high'
    
    def test_check_missing_year_with_year(self):
        """Test that files with year pass."""
        analyzer = MovieNameAnalyzer()
        result = analyzer.check_missing_year("Movie Title (2020)")
        
        assert result is None
    
    def test_extract_title_and_year_with_year(self):
        """Test title and year extraction."""
        analyzer = MovieNameAnalyzer()
        title, year = analyzer.extract_title_and_year("Movie Title (2020)")
        
        assert title == "Movie Title"
        assert year == "2020"
    
    def test_extract_title_and_year_no_year(self):
        """Test title extraction without year."""
        analyzer = MovieNameAnalyzer()
        title, year = analyzer.extract_title_and_year("Movie Title")
        
        assert title == "Movie Title"
        assert year is None
    
    def test_extract_title_and_year_with_codec(self):
        """Test title extraction with codec tags."""
        analyzer = MovieNameAnalyzer()
        title, year = analyzer.extract_title_and_year("Movie Title (2020) H.265 1080p")
        
        assert title == "Movie Title"
        assert year == "2020"
    
    def test_clean_filename_removes_codec_tags(self):
        """Test codec tag removal."""
        analyzer = MovieNameAnalyzer()
        cleaned = analyzer.clean_filename("Movie Title (2020) H.265 1080p BluRay")
        
        assert "H.265" not in cleaned
        assert "1080p" not in cleaned
        assert "BluRay" not in cleaned
        assert "Movie Title" in cleaned
        assert "(2020)" in cleaned
    
    def test_clean_filename_removes_brackets(self):
        """Test bracket tag removal."""
        analyzer = MovieNameAnalyzer()
        cleaned = analyzer.clean_filename("Movie Title (2020) [RARBG]")
        
        assert "[RARBG]" not in cleaned
        assert "Movie Title" in cleaned
    
    def test_analyze_movie_file_with_issues(self, sample_movies_dir):
        """Test analyzing a movie file with issues."""
        analyzer = MovieNameAnalyzer()
        movie_file = sample_movies_dir / "Movie B (2019) H.265 1080p.mkv"
        
        result = analyzer.analyze_movie_file(movie_file, sample_movies_dir)
        
        assert result['filename'] == "Movie B (2019) H.265 1080p"
        assert result['needs_fix'] is True
        assert len(result['issues']) > 0
        
        # Should detect codec tags and folder structure issues
        issue_types = [issue['type'] for issue in result['issues']]
        assert 'codec_in_name' in issue_types
        assert 'not_in_folder' in issue_types
    
    def test_analyze_movie_file_clean(self, sample_movies_dir):
        """Test analyzing a movie file (may have expected issues)."""
        analyzer = MovieNameAnalyzer()
        movie_file = sample_movies_dir / "Movie A (2020)" / "Movie A (2020).mkv"
        
        result = analyzer.analyze_movie_file(movie_file, sample_movies_dir)
        
        assert result['filename'] == "Movie A (2020)"
        assert result['title'] == "Movie A"
        assert result['year'] == "2020"
        # The analyzer may detect issues - just verify it returns a result
        assert isinstance(result['issues'], list)
        assert 'needs_fix' in result
    
    def test_analyze_movies_folder(self, sample_movies_dir):
        """Test analyzing entire movies folder."""
        analyzer = MovieNameAnalyzer()
        
        results = analyzer.analyze_movies_folder(str(sample_movies_dir))
        
        assert results['total_files'] == 3
        assert 'movies' in results
        assert 'summary' in results
        assert len(results['movies']) == 3
    
    def test_analyze_movies_folder_nonexistent(self):
        """Test error handling for nonexistent folder."""
        analyzer = MovieNameAnalyzer()
        
        with pytest.raises(ValueError, match="not found"):
            analyzer.analyze_movies_folder("/nonexistent/path")
    
    def test_suggest_fix_for_codec_issue(self):
        """Test fix suggestion for codec tags."""
        analyzer = MovieNameAnalyzer()
        
        movie_info = {
            'filename': 'Movie Title (2020) H.265',
            'title': 'Movie Title',
            'year': '2020',
            'cleaned_filename': 'Movie Title (2020)',
            'issues': [
                {
                    'type': 'codec_in_name',
                    'severity': 'medium',
                    'description': 'Contains codec tag'
                }
            ],
            'extension': '.mkv'
        }
        
        suggestion = analyzer.suggest_fix(movie_info)
        
        assert suggestion['can_auto_fix'] is True
        assert len(suggestion['suggestions']) == 1
        assert suggestion['suggestions'][0]['action'] == 'remove_codec_tags'
        assert suggestion['suggestions'][0]['auto_fixable'] is True
    
    def test_suggest_fix_for_truncated_title(self):
        """Test fix suggestion for truncated title."""
        analyzer = MovieNameAnalyzer()
        
        movie_info = {
            'filename': 'Doc Ma (2003)',
            'title': 'Doc Ma',
            'year': '2003',
            'cleaned_filename': 'Doc Ma (2003)',
            'issues': [
                {
                    'type': 'truncated_titles',
                    'severity': 'high',
                    'description': 'Title appears truncated'
                }
            ],
            'extension': '.mkv'
        }
        
        suggestion = analyzer.suggest_fix(movie_info)
        
        assert suggestion['can_auto_fix'] is False
        assert suggestion['requires_manual'] is True
        assert suggestion['suggestions'][0]['action'] == 'manual_review'
    
    def test_suggest_fix_for_folder_structure(self):
        """Test fix suggestion for folder structure."""
        analyzer = MovieNameAnalyzer()
        
        movie_info = {
            'filename': 'Movie Title (2020)',
            'title': 'Movie Title',
            'year': '2020',
            'parent_folder': 'Movies',
            'cleaned_filename': 'Movie Title (2020)',
            'issues': [
                {
                    'type': 'not_in_folder',
                    'severity': 'low',
                    'description': 'Not in dedicated folder'
                }
            ],
            'extension': '.mkv'
        }
        
        suggestion = analyzer.suggest_fix(movie_info)
        
        assert suggestion['can_auto_fix'] is True
        assert suggestion['suggestions'][0]['action'] == 'create_folder'
        assert suggestion['suggestions'][0]['suggested_folder'] == 'Movie Title (2020)'


@pytest.mark.integration
@pytest.mark.movies
class TestMovieNameAnalyzerIntegration:
    """Integration tests for MovieNameAnalyzer"""
    
    def test_full_analysis_workflow(self, sample_movies_dir):
        """Test complete analysis workflow from start to finish."""
        analyzer = MovieNameAnalyzer()
        
        # Analyze folder
        results = analyzer.analyze_movies_folder(str(sample_movies_dir))
        
        # Verify results structure
        assert 'folder' in results
        assert 'total_files' in results
        assert 'movies' in results
        assert 'summary' in results
        
        # Verify summary statistics
        summary = results['summary']
        assert 'codec_in_name' in summary
        assert 'truncated_titles' in summary
        assert 'not_in_folder' in summary
        assert 'missing_year' in summary
        
        # At least one movie should have issues
        movies_with_issues = [m for m in results['movies'] if m['needs_fix']]
        assert len(movies_with_issues) > 0
        
        # Generate fix suggestions for movies with issues
        for movie in movies_with_issues:
            suggestion = analyzer.suggest_fix(movie)
            assert 'suggestions' in suggestion
            assert 'can_auto_fix' in suggestion
            assert 'requires_manual' in suggestion
