"""
Tests for JellyBase grouping functions.

Phase 59: JellyBase Code Quality Refinement - Phase 3 Input Validation

Coverage: Input validation for all 5 grouping functions
Test Count: 15 tests (2-3 per function)
"""

import pytest
from unittest.mock import MagicMock
from typing import List, Dict

from scripts.core.jellybase_grouping import (
    group_by_genre,
    group_by_series,
    group_by_franchise,
    group_by_director,
    apply_custom_grouping_rules
)
from scripts.core.jellyfin_client import JellyfinClient


class TestGroupByGenreValidation:
    """Tests for group_by_genre() input validation."""

    @pytest.mark.unit
    def test_group_by_genre_validates_items_type(self):
        """group_by_genre() should raise TypeError for invalid items type."""
        with pytest.raises(TypeError, match="items must be list"):
            group_by_genre(None, "Action")

    @pytest.mark.unit
    def test_group_by_genre_validates_genre_type(self):
        """group_by_genre() should raise TypeError for invalid genre type."""
        items = []
        with pytest.raises(TypeError, match="genre must be str"):
            group_by_genre(items, 123)

    @pytest.mark.unit
    def test_group_by_genre_validates_empty_genre(self):
        """group_by_genre() should raise ValueError for empty genre."""
        items = []
        with pytest.raises(ValueError, match="genre must be non-empty string"):
            group_by_genre(items, "")

    @pytest.mark.unit
    def test_group_by_genre_validates_whitespace_genre(self):
        """group_by_genre() should raise ValueError for whitespace-only genre."""
        items = []
        with pytest.raises(ValueError, match="genre must be non-empty string"):
            group_by_genre(items, "   ")

    @pytest.mark.unit
    def test_group_by_genre_validates_fuzzy_type(self):
        """group_by_genre() should raise TypeError for invalid fuzzy type."""
        items = []
        with pytest.raises(TypeError, match="fuzzy must be bool"):
            group_by_genre(items, "Action", fuzzy="yes")


class TestGroupBySeriesValidation:
    """Tests for group_by_series() input validation."""

    @pytest.mark.unit
    def test_group_by_series_validates_items_type(self):
        """group_by_series() should raise TypeError for invalid items type."""
        with pytest.raises(TypeError, match="items must be list"):
            group_by_series(None)


class TestGroupByFranchiseValidation:
    """Tests for group_by_franchise() input validation."""

    @pytest.mark.unit
    def test_group_by_franchise_validates_items_type(self):
        """group_by_franchise() should raise TypeError for invalid items type."""
        with pytest.raises(TypeError, match="items must be list"):
            group_by_franchise(None)


class TestGroupByDirectorValidation:
    """Tests for group_by_director() input validation."""

    @pytest.mark.unit
    def test_group_by_director_validates_items_type(self):
        """group_by_director() should raise TypeError for invalid items type."""
        with pytest.raises(TypeError, match="items must be list"):
            group_by_director(None)


class TestApplyCustomGroupingRulesValidation:
    """Tests for apply_custom_grouping_rules() input validation."""

    @pytest.mark.unit
    def test_apply_custom_rules_validates_items_type(self):
        """apply_custom_grouping_rules() should raise TypeError for invalid items type."""
        with pytest.raises(TypeError, match="items must be list"):
            apply_custom_grouping_rules(None, [])

    @pytest.mark.unit
    def test_apply_custom_rules_validates_rules_type(self):
        """apply_custom_grouping_rules() should raise TypeError for invalid rules type."""
        items = []
        with pytest.raises(TypeError, match="rules must be list"):
            apply_custom_grouping_rules(items, "not a list")

    @pytest.mark.unit
    def test_apply_custom_rules_validates_empty_rules(self):
        """apply_custom_grouping_rules() should raise ValueError for empty rules list."""
        items = []
        with pytest.raises(ValueError, match="rules must be non-empty list"):
            apply_custom_grouping_rules(items, [])

    @pytest.mark.unit
    def test_apply_custom_rules_validates_rule_is_dict(self):
        """apply_custom_grouping_rules() should raise TypeError if rule is not dict."""
        items = []
        with pytest.raises(TypeError, match="rules\\[0\\] must be dict"):
            apply_custom_grouping_rules(items, ["not a dict"])

    @pytest.mark.unit
    def test_apply_custom_rules_validates_required_fields(self):
        """apply_custom_grouping_rules() should raise ValueError for missing required fields."""
        items = []
        # Missing 'name' field
        with pytest.raises(ValueError, match="rules\\[0\\] missing required field: name"):
            apply_custom_grouping_rules(items, [{"field": "genre", "operator": "equals", "value": "Action"}])
        
        # Missing 'field' field
        with pytest.raises(ValueError, match="rules\\[0\\] missing required field: field"):
            apply_custom_grouping_rules(items, [{"name": "Test", "operator": "equals", "value": "Action"}])
        
        # Missing 'operator' field
        with pytest.raises(ValueError, match="rules\\[0\\] missing required field: operator"):
            apply_custom_grouping_rules(items, [{"name": "Test", "field": "genre", "value": "Action"}])
        
        # Missing 'value' field
        with pytest.raises(ValueError, match="rules\\[0\\] missing required field: value"):
            apply_custom_grouping_rules(items, [{"name": "Test", "field": "genre", "operator": "equals"}])

