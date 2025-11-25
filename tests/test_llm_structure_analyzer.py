"""
Tests for LLM Structure Analyzer module.

Function Index Queries:
- search "LLM structure analyzer folder summary Poe API analyze" -> Found LLMStructureAnalyzer
- search "ravenmaven_client PoeClient" -> Found PoeClient for mocking

Coverage Target: 70%+ line coverage (external API mocking required)
"""
import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import logging
import sys


class TestLLMStructureAnalyzerInit:
    """Tests for LLMStructureAnalyzer initialization."""
    
    @pytest.mark.unit
    def test_init_custom_model(self):
        """Should accept custom model name."""
        with patch('scripts.media.llm_structure_analyzer.PoeClient'):
            from scripts.media.llm_structure_analyzer import LLMStructureAnalyzer
            analyzer = LLMStructureAnalyzer(model="gpt-4o")
            assert analyzer.model == "gpt-4o"
    
    @pytest.mark.unit
    def test_init_with_custom_logger(self):
        """Should accept custom logger."""
        custom_logger = logging.getLogger("test_llm")
        with patch('scripts.media.llm_structure_analyzer.PoeClient'):
            from scripts.media.llm_structure_analyzer import LLMStructureAnalyzer
            analyzer = LLMStructureAnalyzer(logger=custom_logger)
            assert analyzer.logger == custom_logger
    
    @pytest.mark.unit
    def test_init_raises_on_invalid_model(self):
        """Should raise ValueError for invalid model name."""
        with patch('scripts.media.llm_structure_analyzer.PoeClient'):
            from scripts.media.llm_structure_analyzer import LLMStructureAnalyzer
            with pytest.raises(ValueError, match="Invalid model"):
                LLMStructureAnalyzer(model="")


class TestMakeJsonSerializable:
    """Tests for _make_json_serializable method."""
    
    @pytest.fixture
    def analyzer(self):
        """Create analyzer with mocked client."""
        with patch('scripts.media.llm_structure_analyzer.PoeClient'):
            from scripts.media.llm_structure_analyzer import LLMStructureAnalyzer
            return LLMStructureAnalyzer()
    
    @pytest.mark.unit
    def test_converts_path_to_string(self, analyzer):
        """Should convert Path objects to strings."""
        test_path = Path("/test/path")
        data = {"path": test_path}
        
        result = analyzer._make_json_serializable(data)
        
        # Compare as paths to handle platform differences
        assert Path(result["path"]) == test_path
        assert isinstance(result["path"], str)
    
    @pytest.mark.unit
    def test_handles_nested_paths(self, analyzer):
        """Should convert nested Path objects."""
        data = {
            "folder": {
                "path": Path("/nested/path"),
                "children": [Path("/child1"), Path("/child2")]
            }
        }
        
        result = analyzer._make_json_serializable(data)
        
        # Compare as paths
        assert Path(result["folder"]["path"]) == Path("/nested/path")
        assert Path(result["folder"]["children"][0]) == Path("/child1")
    
    @pytest.mark.unit
    def test_handles_path_keys(self, analyzer):
        """Should convert Path keys to strings."""
        test_path = Path("/key/path")
        data = {test_path: "value"}
        
        result = analyzer._make_json_serializable(data)
        
        # Key should now be a string representation
        assert str(test_path) in result
    
    @pytest.mark.unit
    def test_handles_sets(self, analyzer):
        """Should convert sets to lists."""
        data = {"items": {1, 2, 3}}
        
        result = analyzer._make_json_serializable(data)
        
        assert isinstance(result["items"], list)
        assert set(result["items"]) == {1, 2, 3}
    
    @pytest.mark.unit
    def test_preserves_primitives(self, analyzer):
        """Should preserve primitive types."""
        data = {
            "string": "hello",
            "number": 42,
            "float": 3.14,
            "bool": True,
            "none": None
        }
        
        result = analyzer._make_json_serializable(data)
        
        assert result == data


class TestBuildAnalysisPrompt:
    """Tests for _build_analysis_prompt method."""
    
    @pytest.fixture
    def analyzer(self):
        """Create analyzer with mocked client."""
        with patch('scripts.media.llm_structure_analyzer.PoeClient'):
            from scripts.media.llm_structure_analyzer import LLMStructureAnalyzer
            return LLMStructureAnalyzer()
    
    @pytest.mark.unit
    def test_builds_prompt_with_structure(self, analyzer):
        """Should build prompt containing structure data."""
        # Use structure format that tree renderer expects
        structure = {
            "/media/Movies": {
                "files": ["movie1.mkv", "movie2.mkv"],
                "total_size": 1024**3,
                "file_types": {".mkv": 2}
            }
        }
        
        prompt = analyzer._build_analysis_prompt(structure)
        
        assert "Movies" in prompt
        # Updated to match current tree format prompt text
        assert "JELLYFIN NAMING REQUIREMENTS" in prompt
        assert "detected_media" in prompt
    
    @pytest.mark.unit
    def test_includes_additional_context(self, analyzer):
        """Should include additional context if provided."""
        structure = {"folders": []}
        context = "This library contains anime only."
        
        prompt = analyzer._build_analysis_prompt(structure, context)
        
        assert context in prompt
    
    @pytest.mark.unit
    def test_raises_on_non_dict_structure(self, analyzer):
        """Should raise TypeError for non-dict structure."""
        with pytest.raises(TypeError, match="must be a dict"):
            analyzer._build_analysis_prompt("not a dict")
    
    @pytest.mark.unit
    def test_handles_path_objects_in_structure(self, analyzer):
        """Should serialize Path objects in structure."""
        # Use structure format that tree renderer expects, with Path as key
        structure = {
            Path("/media/movies"): {
                "files": ["test.mkv"],
                "total_size": 1024**2,
                "file_types": {".mkv": 1}
            }
        }
        
        prompt = analyzer._build_analysis_prompt(structure)
        
        # Should not raise and should contain path representation
        # Path keys are converted to strings by tree renderer
        assert "media" in prompt and "movies" in prompt


class TestParseLLMResponse:
    """Tests for _parse_llm_response method."""
    
    @pytest.fixture
    def analyzer(self):
        """Create analyzer with mocked client."""
        with patch('scripts.media.llm_structure_analyzer.PoeClient'):
            from scripts.media.llm_structure_analyzer import LLMStructureAnalyzer
            return LLMStructureAnalyzer()
    
    @pytest.mark.unit
    def test_parses_valid_json(self, analyzer):
        """Should parse valid JSON response."""
        response = json.dumps({
            "detected_media": [{"title": "Test Movie", "type": "movie"}],
            "reorganization_plan": {"summary": "Plan"},
            "multi_part_episodes": [],
            "reasoning": "Analysis complete"
        })
        
        result = analyzer._parse_llm_response(response)
        
        assert len(result["detected_media"]) == 1
        assert result["detected_media"][0]["title"] == "Test Movie"
    
    @pytest.mark.unit
    def test_parses_json_in_code_block(self, analyzer):
        """Should extract JSON from markdown code blocks."""
        response = '''Here's my analysis:

```json
{
    "detected_media": [{"title": "Movie", "type": "movie"}],
    "reorganization_plan": {"summary": "Test"},
    "multi_part_episodes": [],
    "reasoning": "Done"
}
```'''
        
        result = analyzer._parse_llm_response(response)
        
        assert len(result["detected_media"]) == 1
    
    @pytest.mark.unit
    def test_handles_missing_keys(self, analyzer):
        """Should add default values for missing keys."""
        response = json.dumps({"detected_media": []})
        
        result = analyzer._parse_llm_response(response)
        
        assert "reorganization_plan" in result
        assert "multi_part_episodes" in result
        assert "reasoning" in result
    
    @pytest.mark.unit
    def test_handles_invalid_json(self, analyzer):
        """Should return error structure for invalid JSON."""
        response = "This is not JSON at all"
        
        result = analyzer._parse_llm_response(response)
        
        assert "error" in result
        assert result["detected_media"] == []
    
    @pytest.mark.unit
    def test_handles_thinking_text_before_json(self, analyzer):
        """Should handle models that output thinking before JSON."""
        response = '''Let me analyze this structure...

After careful consideration, here is my analysis:

```json
{
    "detected_media": [{"title": "Show", "type": "tv_show"}],
    "reorganization_plan": {"summary": "Reorganize"},
    "multi_part_episodes": [],
    "reasoning": "Analyzed"
}
```

I hope this helps!'''
        
        result = analyzer._parse_llm_response(response)
        
        assert len(result["detected_media"]) == 1
        assert result["detected_media"][0]["type"] == "tv_show"


class TestAnalyzeStructure:
    """Tests for analyze_structure method."""
    
    @pytest.mark.unit
    def test_analyze_raises_on_non_dict(self):
        """Should raise TypeError for non-dict structure."""
        with patch('scripts.media.llm_structure_analyzer.PoeClient'):
            from scripts.media.llm_structure_analyzer import LLMStructureAnalyzer
            analyzer = LLMStructureAnalyzer()
            with pytest.raises(TypeError, match="must be a dict"):
                analyzer.analyze_structure("not a dict")
    
    @pytest.mark.unit
    def test_analyze_raises_on_empty_dict(self):
        """Should raise ValueError for empty structure."""
        with patch('scripts.media.llm_structure_analyzer.PoeClient'):
            from scripts.media.llm_structure_analyzer import LLMStructureAnalyzer
            analyzer = LLMStructureAnalyzer()
            with pytest.raises(ValueError, match="cannot be empty"):
                analyzer.analyze_structure({})
    
    @pytest.mark.unit
    def test_analyze_validates_inputs(self):
        """Should validate structure input before calling API."""
        with patch('scripts.media.llm_structure_analyzer.PoeClient'):
            from scripts.media.llm_structure_analyzer import LLMStructureAnalyzer
            analyzer = LLMStructureAnalyzer()
            
            # These should raise before hitting the API
            with pytest.raises(TypeError):
                analyzer.analyze_structure(None)
            
            with pytest.raises(TypeError):
                analyzer.analyze_structure([1, 2, 3])


class TestSaveAnalysis:
    """Tests for save_analysis method."""
    
    @pytest.fixture
    def analyzer(self):
        """Create analyzer with mocked client."""
        with patch('scripts.media.llm_structure_analyzer.PoeClient'):
            from scripts.media.llm_structure_analyzer import LLMStructureAnalyzer
            return LLMStructureAnalyzer()
    
    @pytest.mark.unit
    def test_saves_to_file(self, analyzer, tmp_path):
        """Should save analysis to JSON file."""
        analysis = {
            "detected_media": [{"title": "Test"}],
            "reasoning": "Test analysis"
        }
        output_path = str(tmp_path / "analysis.json")
        
        analyzer.save_analysis(analysis, output_path)
        
        assert Path(output_path).exists()
        with open(output_path) as f:
            saved = json.load(f)
        assert saved["detected_media"][0]["title"] == "Test"
    
    @pytest.mark.unit
    def test_creates_parent_directories(self, analyzer, tmp_path):
        """Should create parent directories if needed."""
        analysis = {"detected_media": []}
        output_path = str(tmp_path / "nested" / "dir" / "analysis.json")
        
        analyzer.save_analysis(analysis, output_path)
        
        assert Path(output_path).exists()
    
    @pytest.mark.unit
    def test_raises_on_non_dict_analysis(self, analyzer, tmp_path):
        """Should raise TypeError for non-dict analysis."""
        output_path = str(tmp_path / "analysis.json")
        
        with pytest.raises(TypeError, match="must be a dict"):
            analyzer.save_analysis("not a dict", output_path)
    
    @pytest.mark.unit
    def test_raises_on_empty_path(self, analyzer):
        """Should raise ValueError for empty path."""
        with pytest.raises(ValueError, match="Invalid output_path"):
            analyzer.save_analysis({}, "")


class TestSetupLogger:
    """Tests for _setup_logger method."""
    
    @pytest.mark.unit
    def test_setup_logger_returns_logger(self):
        """Should return a logger instance."""
        with patch('scripts.media.llm_structure_analyzer.PoeClient'):
            from scripts.media.llm_structure_analyzer import LLMStructureAnalyzer
            analyzer = LLMStructureAnalyzer()
        
        # The analyzer should have a working logger
        assert analyzer.logger is not None
        assert hasattr(analyzer.logger, 'info')
        assert hasattr(analyzer.logger, 'error')
