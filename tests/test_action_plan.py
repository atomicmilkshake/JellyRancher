"""
Tests for action_plan data models.

Function Index Queries:
- search "action plan proposed operation action type confidence" -> Found usage in review_view.py, 
  execution_view.py, workers.py. No existing tests found.
- search "dataclass test enum" -> No specific test patterns found.

Coverage Target: 100% (pure data classes)
"""
import pytest
from pathlib import Path

from scripts.core.action_plan import ActionType, Confidence, ProposedOperation


class TestActionType:
    """Tests for ActionType enum."""
    
    @pytest.mark.unit
    def test_action_type_values_exist(self):
        """ActionType should have all expected action types."""
        expected_types = {'MOVE', 'RENAME', 'DELETE', 'CREATE_NFO', 'SKIP', 'REVIEW'}
        actual_types = {member.name for member in ActionType}
        assert actual_types == expected_types
    
    @pytest.mark.unit
    def test_action_type_unique_values(self):
        """Each ActionType should have a unique value."""
        values = [member.value for member in ActionType]
        assert len(values) == len(set(values))
    
    @pytest.mark.unit
    def test_action_type_is_enum(self):
        """ActionType members should be proper enum instances."""
        assert ActionType.MOVE != ActionType.RENAME
        assert ActionType.MOVE == ActionType.MOVE


class TestConfidence:
    """Tests for Confidence enum."""
    
    @pytest.mark.unit
    def test_confidence_values_exist(self):
        """Confidence should have all expected levels."""
        expected_levels = {'HIGH', 'MEDIUM', 'LOW', 'MANUAL', 'NONE'}
        actual_levels = {member.name for member in Confidence}
        assert actual_levels == expected_levels
    
    @pytest.mark.unit
    def test_confidence_unique_values(self):
        """Each Confidence level should have a unique value."""
        values = [member.value for member in Confidence]
        assert len(values) == len(set(values))
    
    @pytest.mark.unit
    def test_confidence_hierarchy_implied(self):
        """Confidence levels should be distinguishable for sorting."""
        # Not strictly ordered by value, but should be distinguishable
        assert Confidence.HIGH != Confidence.LOW
        assert Confidence.MANUAL != Confidence.NONE


class TestProposedOperation:
    """Tests for ProposedOperation dataclass."""
    
    @pytest.mark.unit
    def test_creation_with_path_object(self):
        """ProposedOperation should accept Path objects."""
        source = Path("/media/movies/test.mkv")
        op = ProposedOperation(source_path=source)
        
        assert op.source_path == source
        assert isinstance(op.source_path, Path)
    
    @pytest.mark.unit
    def test_creation_with_string_path_converts_to_path(self):
        """ProposedOperation should convert string paths to Path objects."""
        op = ProposedOperation(source_path="/media/movies/test.mkv")
        
        assert isinstance(op.source_path, Path)
        # Use Path comparison to handle cross-platform separators
        assert op.source_path == Path("/media/movies/test.mkv")
    
    @pytest.mark.unit
    def test_destination_path_string_converts_to_path(self):
        """Destination path strings should be converted to Path objects."""
        op = ProposedOperation(
            source_path="/source/test.mkv",
            destination_path="/dest/test.mkv"
        )
        
        assert isinstance(op.destination_path, Path)
        # Use Path comparison to handle cross-platform separators
        assert op.destination_path == Path("/dest/test.mkv")
    
    @pytest.mark.unit
    def test_destination_path_none_allowed(self):
        """Destination path can be None."""
        op = ProposedOperation(source_path="/media/test.mkv")
        
        assert op.destination_path is None
    
    @pytest.mark.unit
    def test_default_action_type_is_skip(self):
        """Default action type should be SKIP."""
        op = ProposedOperation(source_path="/media/test.mkv")
        
        assert op.action_type == ActionType.SKIP
    
    @pytest.mark.unit
    def test_default_confidence_is_none(self):
        """Default confidence should be NONE."""
        op = ProposedOperation(source_path="/media/test.mkv")
        
        assert op.confidence == Confidence.NONE
    
    @pytest.mark.unit
    def test_default_jellyfin_status(self):
        """Default jellyfin_status should be 'Unknown'."""
        op = ProposedOperation(source_path="/media/test.mkv")
        
        assert op.jellyfin_status == "Unknown"
    
    @pytest.mark.unit
    def test_default_provider_ids_empty_dicts(self):
        """Provider IDs should default to empty dicts."""
        op = ProposedOperation(source_path="/media/test.mkv")
        
        assert op.current_provider_ids == {}
        assert op.proposed_provider_ids == {}
        # Verify they're independent instances
        op.current_provider_ids['tmdb'] = '12345'
        assert op.proposed_provider_ids == {}
    
    @pytest.mark.unit
    def test_default_md5_fields_none(self):
        """MD5 fields should default to None."""
        op = ProposedOperation(source_path="/media/test.mkv")
        
        assert op.current_md5 is None
        assert op.proposed_md5 is None
    
    @pytest.mark.unit
    def test_default_user_approved_none(self):
        """User approval should default to None (no action taken)."""
        op = ProposedOperation(source_path="/media/test.mkv")
        
        assert op.user_approved is None
    
    @pytest.mark.unit
    def test_full_construction(self):
        """ProposedOperation should accept all fields."""
        op = ProposedOperation(
            source_path=Path("/source/movie.mkv"),
            destination_path=Path("/dest/Movie (2020)/Movie (2020).mkv"),
            action_type=ActionType.MOVE,
            confidence=Confidence.HIGH,
            notes="Matched via TMDB",
            jellyfin_status="New",
            jellyfin_id="abc123",
            current_provider_ids={"imdb": "tt1234567"},
            proposed_provider_ids={"tmdb": "12345", "imdb": "tt1234567"},
            current_md5="abc123def456",
            proposed_md5="abc123def456",
            canonical_metadata={"title": "Movie", "year": 2020},
            user_approved=True
        )
        
        assert op.source_path == Path("/source/movie.mkv")
        assert op.destination_path == Path("/dest/Movie (2020)/Movie (2020).mkv")
        assert op.action_type == ActionType.MOVE
        assert op.confidence == Confidence.HIGH
        assert op.notes == "Matched via TMDB"
        assert op.jellyfin_status == "New"
        assert op.jellyfin_id == "abc123"
        assert op.current_provider_ids == {"imdb": "tt1234567"}
        assert op.proposed_provider_ids == {"tmdb": "12345", "imdb": "tt1234567"}
        assert op.current_md5 == "abc123def456"
        assert op.canonical_metadata == {"title": "Movie", "year": 2020}
        assert op.user_approved is True
    
    @pytest.mark.unit
    def test_mutable_default_factory_isolation(self):
        """Each instance should have independent mutable defaults."""
        op1 = ProposedOperation(source_path="/test1.mkv")
        op2 = ProposedOperation(source_path="/test2.mkv")
        
        op1.current_provider_ids['tmdb'] = '111'
        op1.proposed_provider_ids['imdb'] = 'tt111'
        
        # op2 should not be affected
        assert op2.current_provider_ids == {}
        assert op2.proposed_provider_ids == {}
    
    @pytest.mark.unit
    def test_equality(self):
        """Two ProposedOperations with same values should be equal."""
        op1 = ProposedOperation(
            source_path="/test.mkv",
            action_type=ActionType.MOVE,
            confidence=Confidence.HIGH
        )
        op2 = ProposedOperation(
            source_path="/test.mkv",
            action_type=ActionType.MOVE,
            confidence=Confidence.HIGH
        )
        
        assert op1 == op2
    
    @pytest.mark.unit
    def test_inequality(self):
        """ProposedOperations with different values should not be equal."""
        op1 = ProposedOperation(source_path="/test1.mkv")
        op2 = ProposedOperation(source_path="/test2.mkv")
        
        assert op1 != op2


class TestProposedOperationEdgeCases:
    """Edge case tests for ProposedOperation."""
    
    @pytest.mark.unit
    def test_windows_path_handling(self):
        """Should handle Windows-style paths."""
        op = ProposedOperation(source_path="C:\\Media\\Movies\\test.mkv")
        
        assert isinstance(op.source_path, Path)
        # Path normalizes separators
        assert "test.mkv" in str(op.source_path)
    
    @pytest.mark.unit
    def test_relative_path_handling(self):
        """Should handle relative paths."""
        op = ProposedOperation(source_path="movies/test.mkv")
        
        assert isinstance(op.source_path, Path)
        assert not op.source_path.is_absolute()
    
    @pytest.mark.unit
    def test_empty_notes(self):
        """Empty notes should be allowed."""
        op = ProposedOperation(source_path="/test.mkv", notes="")
        
        assert op.notes == ""
    
    @pytest.mark.unit
    def test_canonical_metadata_none(self):
        """Canonical metadata can be None."""
        op = ProposedOperation(source_path="/test.mkv")
        
        assert op.canonical_metadata is None
    
    @pytest.mark.unit
    def test_canonical_metadata_complex(self):
        """Canonical metadata can hold complex nested data."""
        metadata = {
            "title": "Test Movie",
            "year": 2020,
            "genres": ["Action", "Drama"],
            "cast": [
                {"name": "Actor One", "role": "Lead"},
                {"name": "Actor Two", "role": "Support"}
            ]
        }
        op = ProposedOperation(
            source_path="/test.mkv",
            canonical_metadata=metadata
        )
        
        assert op.canonical_metadata["genres"] == ["Action", "Drama"]
        assert len(op.canonical_metadata["cast"]) == 2

