"""
Tests for NFO Generator module.

Function Index Queries:
- search "NFO generator XML movie TV show metadata file" -> Found NFOGenerator at nfo_generator.py
- search "infer_nfo_path" -> Found method for converting media paths to NFO paths

Coverage Target: 80%+ line coverage
"""
import pytest
from pathlib import Path
from xml.etree import ElementTree as ET
from unittest.mock import Mock, patch
import logging

from scripts.media.nfo_generator import NFOGenerator


class TestNFOGeneratorInit:
    """Tests for NFOGenerator initialization."""
    
    @pytest.mark.unit
    def test_init_default_logger(self):
        """Should initialize with default logger."""
        generator = NFOGenerator()
        assert generator.logger is not None
    
    @pytest.mark.unit
    def test_init_custom_logger(self):
        """Should accept custom logger."""
        custom_logger = logging.getLogger("test_nfo")
        generator = NFOGenerator(logger=custom_logger)
        assert generator.logger == custom_logger


class TestGenerateMovieNFO:
    """Tests for generate_movie_nfo method."""
    
    @pytest.fixture
    def generator(self):
        """Create NFOGenerator instance."""
        return NFOGenerator()
    
    @pytest.mark.unit
    def test_generate_movie_nfo_basic(self, generator):
        """Should generate valid XML with basic info."""
        nfo = generator.generate_movie_nfo(
            title="Test Movie",
            year=2023
        )
        
        assert nfo is not None
        root = ET.fromstring(nfo)
        assert root.tag == "movie"
        assert root.find("title").text == "Test Movie"
        assert root.find("year").text == "2023"
    
    @pytest.mark.unit
    def test_generate_movie_nfo_with_ids(self, generator):
        """Should include TMDB and IMDb IDs."""
        nfo = generator.generate_movie_nfo(
            title="Test Movie",
            year=2023,
            tmdb_id="12345",
            imdb_id="tt1234567"
        )
        
        root = ET.fromstring(nfo)
        assert root.find("tmdbid").text == "12345"
        assert root.find("imdbid").text == "tt1234567"
    
    @pytest.mark.unit
    def test_generate_movie_nfo_with_overview(self, generator):
        """Should include plot overview."""
        nfo = generator.generate_movie_nfo(
            title="Test Movie",
            year=2023,
            overview="A test movie about testing."
        )
        
        root = ET.fromstring(nfo)
        assert root.find("plot").text == "A test movie about testing."
    
    @pytest.mark.unit
    def test_generate_movie_nfo_with_runtime(self, generator):
        """Should include runtime in minutes."""
        nfo = generator.generate_movie_nfo(
            title="Test Movie",
            year=2023,
            runtime=120
        )
        
        root = ET.fromstring(nfo)
        assert root.find("runtime").text == "120"
    
    @pytest.mark.unit
    def test_generate_movie_nfo_raises_on_empty_title(self, generator):
        """Should raise ValueError for empty title."""
        with pytest.raises(ValueError, match="title cannot be empty"):
            generator.generate_movie_nfo(title="", year=2023)
    
    @pytest.mark.unit
    def test_generate_movie_nfo_raises_on_invalid_year(self, generator):
        """Should raise ValueError for invalid year."""
        with pytest.raises(ValueError, match="Invalid year"):
            generator.generate_movie_nfo(title="Test", year=1800)
        
        with pytest.raises(ValueError, match="Invalid year"):
            generator.generate_movie_nfo(title="Test", year=2200)


class TestGenerateEpisodeNFO:
    """Tests for generate_episode_nfo method."""
    
    @pytest.fixture
    def generator(self):
        """Create NFOGenerator instance."""
        return NFOGenerator()
    
    @pytest.mark.unit
    def test_generate_episode_nfo_basic(self, generator):
        """Should generate valid XML with basic info."""
        nfo = generator.generate_episode_nfo(
            show_title="Test Show",
            season=1,
            episode=5
        )
        
        root = ET.fromstring(nfo)
        assert root.tag == "episodedetails"
        assert root.find("showtitle").text == "Test Show"
        assert root.find("season").text == "1"
        assert root.find("episode").text == "5"
    
    @pytest.mark.unit
    def test_generate_episode_nfo_with_title(self, generator):
        """Should include episode title."""
        nfo = generator.generate_episode_nfo(
            show_title="Test Show",
            season=1,
            episode=5,
            episode_title="The Test Episode"
        )
        
        root = ET.fromstring(nfo)
        assert root.find("title").text == "The Test Episode"
    
    @pytest.mark.unit
    def test_generate_episode_nfo_with_ids(self, generator):
        """Should include TVDB and TMDB IDs."""
        nfo = generator.generate_episode_nfo(
            show_title="Test Show",
            season=1,
            episode=5,
            tvdb_id="12345",
            tmdb_id="67890"
        )
        
        root = ET.fromstring(nfo)
        assert root.find("tvdbid").text == "12345"
        assert root.find("tmdbid").text == "67890"
    
    @pytest.mark.unit
    def test_generate_episode_nfo_with_air_date(self, generator):
        """Should include air date."""
        nfo = generator.generate_episode_nfo(
            show_title="Test Show",
            season=1,
            episode=5,
            air_date="2023-05-15"
        )
        
        root = ET.fromstring(nfo)
        assert root.find("aired").text == "2023-05-15"
    
    @pytest.mark.unit
    def test_generate_episode_nfo_multi_part(self, generator):
        """Should include multi-part indicators."""
        nfo = generator.generate_episode_nfo(
            show_title="Test Show",
            season=1,
            episode=1,
            is_multi_part=True,
            part_number=2
        )
        
        root = ET.fromstring(nfo)
        assert root.find("part").text == "2"
        assert root.find("multipart").text == "true"
    
    @pytest.mark.unit
    def test_generate_episode_nfo_raises_on_empty_show_title(self, generator):
        """Should raise ValueError for empty show title."""
        with pytest.raises(ValueError, match="Show title cannot be empty"):
            generator.generate_episode_nfo(show_title="", season=1, episode=1)
    
    @pytest.mark.unit
    def test_generate_episode_nfo_raises_on_negative_season(self, generator):
        """Should raise ValueError for negative season."""
        with pytest.raises(ValueError, match="Invalid season"):
            generator.generate_episode_nfo(show_title="Test", season=-1, episode=1)
    
    @pytest.mark.unit
    def test_generate_episode_nfo_raises_on_negative_episode(self, generator):
        """Should raise ValueError for negative episode."""
        with pytest.raises(ValueError, match="Invalid episode"):
            generator.generate_episode_nfo(show_title="Test", season=1, episode=-1)


class TestSaveNFO:
    """Tests for save_nfo method."""
    
    @pytest.fixture
    def generator(self):
        """Create NFOGenerator instance."""
        return NFOGenerator()
    
    @pytest.mark.unit
    def test_save_nfo_creates_file(self, generator, tmp_path):
        """Should save NFO content to file."""
        nfo_content = "<movie><title>Test</title></movie>"
        output_path = tmp_path / "test.nfo"
        
        result = generator.save_nfo(nfo_content, output_path)
        
        assert result is True
        assert output_path.exists()
        assert output_path.read_text(encoding='utf-8') == nfo_content
    
    @pytest.mark.unit
    def test_save_nfo_creates_parent_directories(self, generator, tmp_path):
        """Should create parent directories if they don't exist."""
        nfo_content = "<movie><title>Test</title></movie>"
        output_path = tmp_path / "subdir" / "nested" / "test.nfo"
        
        result = generator.save_nfo(nfo_content, output_path)
        
        assert result is True
        assert output_path.exists()
    
    @pytest.mark.unit
    def test_save_nfo_returns_false_on_empty_content(self, generator, tmp_path):
        """Should return False for empty content."""
        output_path = tmp_path / "test.nfo"
        
        result = generator.save_nfo("", output_path)
        
        assert result is False
        assert not output_path.exists()
    
    @pytest.mark.unit
    def test_save_nfo_returns_false_on_none_path(self, generator):
        """Should return False for None output path."""
        nfo_content = "<movie><title>Test</title></movie>"
        
        result = generator.save_nfo(nfo_content, None)
        
        assert result is False


class TestInferNFOPath:
    """Tests for infer_nfo_path method."""
    
    @pytest.fixture
    def generator(self):
        """Create NFOGenerator instance."""
        return NFOGenerator()
    
    @pytest.mark.unit
    def test_infer_nfo_path_from_mkv(self, generator):
        """Should convert .mkv to .nfo."""
        media_path = Path("/movies/Test Movie (2023)/Test Movie (2023).mkv")
        
        nfo_path = generator.infer_nfo_path(media_path)
        
        assert nfo_path.suffix == ".nfo"
        assert nfo_path.stem == "Test Movie (2023)"
    
    @pytest.mark.unit
    def test_infer_nfo_path_from_mp4(self, generator):
        """Should convert .mp4 to .nfo."""
        media_path = Path("/tv/Show/Season 01/Show - S01E01.mp4")
        
        nfo_path = generator.infer_nfo_path(media_path)
        
        assert nfo_path.suffix == ".nfo"
        assert nfo_path.stem == "Show - S01E01"
    
    @pytest.mark.unit
    def test_infer_nfo_path_custom_suffix(self, generator):
        """Should use custom suffix."""
        media_path = Path("/movies/test.mkv")
        
        nfo_path = generator.infer_nfo_path(media_path, suffix="xml")
        
        assert nfo_path.suffix == ".xml"
    
    @pytest.mark.unit
    def test_infer_nfo_path_raises_on_none(self, generator):
        """Should raise ValueError for None path."""
        with pytest.raises(ValueError, match="cannot be None"):
            generator.infer_nfo_path(None)


class TestDetectMultiPart:
    """Tests for detect_multi_part method."""
    
    @pytest.fixture
    def generator(self):
        """Create NFOGenerator instance."""
        return NFOGenerator()
    
    @pytest.mark.unit
    def test_detect_multi_part_s_e_format(self, generator):
        """Should detect S01E01-E02 format."""
        result = generator.detect_multi_part("Show Name S01E01-E03.mkv")
        
        assert result["is_multi_part"] is True
        assert result["part_count"] == 3
        assert len(result["individual_episodes"]) == 3
        assert result["individual_episodes"][0] == {"season": 1, "episode": 1}
        assert result["individual_episodes"][2] == {"season": 1, "episode": 3}
    
    @pytest.mark.unit
    def test_detect_multi_part_x_format(self, generator):
        """Should detect 1x01-02 format."""
        result = generator.detect_multi_part("Show Name 2x05-07.mkv")
        
        assert result["is_multi_part"] is True
        assert result["part_count"] == 3
        assert len(result["individual_episodes"]) == 3
        assert result["individual_episodes"][0] == {"season": 2, "episode": 5}
    
    @pytest.mark.unit
    def test_detect_multi_part_single_episode(self, generator):
        """Should return False for single episodes."""
        result = generator.detect_multi_part("Show Name S01E01.mkv")
        
        assert result["is_multi_part"] is False
        assert result["part_count"] == 1
        assert len(result["individual_episodes"]) == 0
    
    @pytest.mark.unit
    def test_detect_multi_part_empty_title(self, generator):
        """Should handle empty title gracefully."""
        result = generator.detect_multi_part("")
        
        assert result["is_multi_part"] is False
        assert result["part_count"] == 1
    
    @pytest.mark.unit
    def test_detect_multi_part_movie(self, generator):
        """Should return False for movies (no episode pattern)."""
        result = generator.detect_multi_part("Inception (2010).mkv")
        
        assert result["is_multi_part"] is False
        assert result["part_count"] == 1


class TestFormatXML:
    """Tests for _format_xml static method."""
    
    @pytest.mark.unit
    def test_format_xml_returns_valid_xml(self):
        """Should return valid XML."""
        xml_str = "<root><child>text</child></root>"
        
        result = NFOGenerator._format_xml(xml_str)
        
        # Should be parseable
        root = ET.fromstring(result)
        assert root.tag == "root"
    
    @pytest.mark.unit
    def test_format_xml_handles_empty_string(self):
        """Should handle empty string."""
        result = NFOGenerator._format_xml("")
        assert result == ""
    
    @pytest.mark.unit
    def test_format_xml_handles_invalid_xml(self):
        """Should return original for invalid XML."""
        invalid_xml = "not valid xml <<>>"
        
        result = NFOGenerator._format_xml(invalid_xml)
        
        # Should return original on error
        assert result == invalid_xml

