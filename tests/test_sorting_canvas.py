#!/usr/bin/env python3
"""
Tests for the Sorting Canvas - the "secret weapon" for media categorization.

Tests cover:
- BucketManager: Bucket creation, item management, auto-categorization
- BucketItem: Serialization, creation from various sources
- PerBucketPrompts: Prompt generation for each category
- SortingCanvasView: UI interactions, drag-drop, signals
"""

import pytest
import tempfile
import sqlite3
from pathlib import Path
from typing import Dict, Any

from scripts.core.bucket_manager import (
    BucketManager, BucketType, BucketItem, Bucket
)
from scripts.core.per_bucket_prompts import (
    PromptBuilder, build_folder_summary_for_bucket, PerBucketAnalyzer
)


# =============================================================================
# BucketType Tests
# =============================================================================

class TestBucketType:
    """Tests for BucketType enum."""
    
    def test_all_types_defined(self):
        """All expected bucket types exist."""
        expected = ['MOVIES', 'TV_SHOWS', 'GAMES', 'MUSIC', 'BOOKS', 'UNSORTED']
        for name in expected:
            assert hasattr(BucketType, name)
    
    def test_from_string_valid(self):
        """from_string converts valid strings."""
        assert BucketType.from_string('movies') == BucketType.MOVIES
        assert BucketType.from_string('tv_shows') == BucketType.TV_SHOWS
        assert BucketType.from_string('TV Shows') == BucketType.TV_SHOWS
        assert BucketType.from_string('games') == BucketType.GAMES
        assert BucketType.from_string('MUSIC') == BucketType.MUSIC
    
    def test_from_string_invalid(self):
        """from_string defaults to UNSORTED for invalid strings."""
        assert BucketType.from_string('invalid') == BucketType.UNSORTED
        assert BucketType.from_string('') == BucketType.UNSORTED
        assert BucketType.from_string('xyz') == BucketType.UNSORTED


# =============================================================================
# BucketItem Tests
# =============================================================================

class TestBucketItem:
    """Tests for BucketItem dataclass."""
    
    def test_create_file_item(self):
        """Create a file bucket item."""
        item = BucketItem(
            path=Path("/media/movies/Inception.mkv"),
            name="Inception.mkv",
            is_folder=False,
            size_bytes=1024 * 1024 * 1500,  # 1.5 GB
            file_count=1
        )
        
        assert item.path == Path("/media/movies/Inception.mkv")
        assert item.name == "Inception.mkv"
        assert not item.is_folder
        assert item.size_bytes == 1024 * 1024 * 1500
        assert item.file_count == 1
        assert not item.auto_assigned
    
    def test_create_folder_item(self):
        """Create a folder bucket item."""
        item = BucketItem(
            path=Path("/media/tv/Breaking Bad"),
            name="Breaking Bad",
            is_folder=True,
            size_bytes=50 * 1024 * 1024 * 1024,  # 50 GB
            file_count=62,
            auto_assigned=True
        )
        
        assert item.is_folder
        assert item.file_count == 62
        assert item.auto_assigned
    
    def test_to_dict_roundtrip(self):
        """Serialize and deserialize preserves data."""
        original = BucketItem(
            path=Path("/media/test.mkv"),
            name="test.mkv",
            is_folder=False,
            size_bytes=1000,
            file_count=1,
            original_bucket=BucketType.MOVIES,
            auto_assigned=True
        )
        
        data = original.to_dict()
        restored = BucketItem.from_dict(data)
        
        assert restored.path == original.path
        assert restored.name == original.name
        assert restored.is_folder == original.is_folder
        assert restored.size_bytes == original.size_bytes
        assert restored.original_bucket == original.original_bucket
        assert restored.auto_assigned == original.auto_assigned


# =============================================================================
# Bucket Tests
# =============================================================================

class TestBucket:
    """Tests for Bucket dataclass."""
    
    def test_bucket_name_property(self):
        """Bucket name property returns human-readable name."""
        bucket = Bucket(BucketType.MOVIES)
        assert "Movies" in bucket.name
        assert "🎬" in bucket.name
        
        bucket = Bucket(BucketType.TV_SHOWS)
        assert "TV Shows" in bucket.name
        assert "📺" in bucket.name
    
    def test_add_and_remove_items(self):
        """Add and remove items from bucket."""
        bucket = Bucket(BucketType.MOVIES)
        
        item1 = BucketItem(Path("/test1.mkv"), "test1.mkv", False, 1000, 1)
        item2 = BucketItem(Path("/test2.mkv"), "test2.mkv", False, 2000, 1)
        
        bucket.add_item(item1)
        bucket.add_item(item2)
        
        assert len(bucket.items) == 2
        assert bucket.total_files == 2
        assert bucket.total_size_bytes == 3000
        
        removed = bucket.remove_item(Path("/test1.mkv"))
        assert removed == item1
        assert len(bucket.items) == 1
    
    def test_clear_bucket(self):
        """Clear removes all items."""
        bucket = Bucket(BucketType.GAMES)
        bucket.add_item(BucketItem(Path("/game1"), "game1", True, 10000, 5))
        bucket.add_item(BucketItem(Path("/game2"), "game2", True, 20000, 10))
        
        bucket.clear()
        
        assert len(bucket.items) == 0
        assert bucket.total_files == 0
    
    def test_to_dict_roundtrip(self):
        """Serialize and deserialize bucket."""
        bucket = Bucket(BucketType.TV_SHOWS)
        bucket.add_item(BucketItem(Path("/show1"), "Show 1", True, 5000, 12))
        bucket.add_item(BucketItem(Path("/show2"), "Show 2", True, 6000, 24))
        
        data = bucket.to_dict()
        restored = Bucket.from_dict(data)
        
        assert restored.bucket_type == bucket.bucket_type
        assert len(restored.items) == 2
        assert restored.items[0].name == "Show 1"


# =============================================================================
# BucketManager Tests
# =============================================================================

class TestBucketManager:
    """Tests for BucketManager class."""
    
    def test_initialization(self):
        """Manager initializes with all bucket types."""
        manager = BucketManager()
        
        for bt in BucketType:
            assert bt in manager.buckets
            assert isinstance(manager.buckets[bt], Bucket)
    
    def test_add_item_to_bucket(self):
        """Add item to specific bucket."""
        manager = BucketManager()
        item = BucketItem(Path("/movie.mkv"), "movie.mkv", False, 1000, 1)
        
        manager.add_item(BucketType.MOVIES, item)
        
        assert len(manager.buckets[BucketType.MOVIES].items) == 1
        assert manager.find_item_bucket(Path("/movie.mkv")) == BucketType.MOVIES
    
    def test_move_item_between_buckets(self):
        """Move item from one bucket to another."""
        manager = BucketManager()
        item = BucketItem(Path("/media.mkv"), "media.mkv", False, 1000, 1)
        
        manager.add_item(BucketType.UNSORTED, item)
        assert manager.find_item_bucket(Path("/media.mkv")) == BucketType.UNSORTED
        
        manager.move_item(Path("/media.mkv"), BucketType.UNSORTED, BucketType.MOVIES)
        
        assert manager.find_item_bucket(Path("/media.mkv")) == BucketType.MOVIES
        assert len(manager.buckets[BucketType.UNSORTED].items) == 0
    
    def test_move_to_same_bucket(self):
        """Move to same bucket does nothing."""
        manager = BucketManager()
        item = BucketItem(Path("/test.mkv"), "test.mkv", False, 1000, 1)
        
        manager.add_item(BucketType.MOVIES, item)
        result = manager.move_item(Path("/test.mkv"), BucketType.MOVIES, BucketType.MOVIES)
        
        assert result is True
        assert len(manager.buckets[BucketType.MOVIES].items) == 1
    
    def test_remove_item(self):
        """Remove item from manager."""
        manager = BucketManager()
        item = BucketItem(Path("/to_remove.mkv"), "to_remove.mkv", False, 1000, 1)
        
        manager.add_item(BucketType.TV_SHOWS, item)
        removed = manager.remove_item(Path("/to_remove.mkv"))
        
        assert removed is not None
        assert removed.name == "to_remove.mkv"
        assert manager.find_item_bucket(Path("/to_remove.mkv")) is None
    
    def test_clear_all(self):
        """Clear all buckets."""
        manager = BucketManager()
        manager.add_item(BucketType.MOVIES, BucketItem(Path("/m1"), "m1", False))
        manager.add_item(BucketType.TV_SHOWS, BucketItem(Path("/t1"), "t1", False))
        manager.add_item(BucketType.GAMES, BucketItem(Path("/g1"), "g1", False))
        
        manager.clear_all()
        
        for bucket in manager.buckets.values():
            assert len(bucket.items) == 0
    
    def test_get_non_empty_buckets(self):
        """Get only buckets with items."""
        manager = BucketManager()
        manager.add_item(BucketType.MOVIES, BucketItem(Path("/m1"), "m1", False))
        manager.add_item(BucketType.TV_SHOWS, BucketItem(Path("/t1"), "t1", False))
        
        non_empty = manager.get_non_empty_buckets()
        
        assert len(non_empty) == 2
        bucket_types = [b.bucket_type for b in non_empty]
        assert BucketType.MOVIES in bucket_types
        assert BucketType.TV_SHOWS in bucket_types
        assert BucketType.GAMES not in bucket_types
    
    def test_statistics(self):
        """Get statistics about bucket contents."""
        manager = BucketManager()
        manager.add_item(BucketType.MOVIES, BucketItem(
            Path("/m1"), "m1", True, 1000, 5, auto_assigned=True
        ))
        manager.add_item(BucketType.MOVIES, BucketItem(
            Path("/m2"), "m2", True, 2000, 10, auto_assigned=False
        ))
        
        stats = manager.get_statistics()
        
        assert stats['total_items'] == 2
        assert stats['total_files'] == 15
        assert stats['total_size_bytes'] == 3000
        assert stats['buckets']['movies']['item_count'] == 2
        assert stats['buckets']['movies']['auto_assigned'] == 1
        assert stats['buckets']['movies']['user_assigned'] == 1


# =============================================================================
# Auto-Categorization Tests
# =============================================================================

class TestAutoCategorization:
    """Tests for auto-categorization logic."""
    
    @pytest.fixture
    def manager(self):
        return BucketManager()
    
    def test_tv_show_patterns(self, manager):
        """Recognize TV show naming patterns."""
        # S01E01 format
        assert manager.auto_categorize_item(
            Path("/Breaking.Bad.S01E01.mkv"), "Breaking.Bad.S01E01.mkv", False
        ) == BucketType.TV_SHOWS
        
        # Season folder
        assert manager.auto_categorize_item(
            Path("/Season 1"), "Season 1", True
        ) == BucketType.TV_SHOWS
        
        # 1x01 format
        assert manager.auto_categorize_item(
            Path("/Show.1x01.mkv"), "Show.1x01.mkv", False
        ) == BucketType.TV_SHOWS
    
    def test_movie_patterns(self, manager):
        """Recognize movie naming patterns."""
        # Year in parentheses
        assert manager.auto_categorize_item(
            Path("/Inception (2010)"), "Inception (2010)", True
        ) == BucketType.MOVIES
        
        # Year with dots
        assert manager.auto_categorize_item(
            Path("/Movie.2020.1080p.BluRay.mkv"), "Movie.2020.1080p.BluRay.mkv", False
        ) == BucketType.MOVIES
        
        # Quality tag
        assert manager.auto_categorize_item(
            Path("/Film.720p.WEB-DL.mkv"), "Film.720p.WEB-DL.mkv", False
        ) == BucketType.MOVIES
    
    def test_music_by_extension(self, manager):
        """Categorize music by file extensions."""
        music_exts = {'.mp3', '.flac'}
        
        result = manager.auto_categorize_item(
            Path("/Album"), "Album", True, file_extensions=music_exts
        )
        assert result == BucketType.MUSIC
    
    def test_books_by_extension(self, manager):
        """Categorize books by file extensions."""
        book_exts = {'.epub', '.mobi'}
        
        result = manager.auto_categorize_item(
            Path("/Books"), "Books", True, file_extensions=book_exts
        )
        assert result == BucketType.BOOKS
    
    def test_games_by_pattern(self, manager):
        """Recognize game patterns."""
        assert manager.auto_categorize_item(
            Path("/Game.ISO"), "Game.ISO", False
        ) == BucketType.GAMES
    
    def test_unsorted_fallback(self, manager):
        """Unknown content goes to unsorted."""
        assert manager.auto_categorize_item(
            Path("/random_stuff"), "random_stuff", True
        ) == BucketType.UNSORTED
    
    def test_auto_categorize_all(self, manager):
        """Batch auto-categorization."""
        items = [
            {'path': '/Show.S01E01.mkv', 'name': 'Show.S01E01.mkv', 'is_folder': False},
            {'path': '/Movie.2020.mkv', 'name': 'Movie.2020.mkv', 'is_folder': False},
            {'path': '/Album', 'name': 'Album', 'is_folder': True, 'extensions': ['.mp3']},
        ]
        
        manager.auto_categorize_all(items)
        
        assert len(manager.buckets[BucketType.TV_SHOWS].items) == 1
        assert len(manager.buckets[BucketType.MOVIES].items) == 1
        assert len(manager.buckets[BucketType.MUSIC].items) == 1


# =============================================================================
# Undo/Redo Tests
# =============================================================================

class TestUndoRedo:
    """Tests for undo/redo functionality."""
    
    def test_undo_move(self):
        """Undo reverses a move operation."""
        manager = BucketManager()
        item = BucketItem(Path("/test"), "test", False)
        
        manager.add_item(BucketType.UNSORTED, item)
        manager.move_item(Path("/test"), BucketType.UNSORTED, BucketType.MOVIES)
        
        assert manager.find_item_bucket(Path("/test")) == BucketType.MOVIES
        
        manager.undo()
        
        assert manager.find_item_bucket(Path("/test")) == BucketType.UNSORTED
    
    def test_redo_after_undo(self):
        """Redo reapplies an undone operation."""
        manager = BucketManager()
        item = BucketItem(Path("/test"), "test", False)
        
        manager.add_item(BucketType.UNSORTED, item)
        manager.move_item(Path("/test"), BucketType.UNSORTED, BucketType.MOVIES)
        manager.undo()
        manager.redo()
        
        assert manager.find_item_bucket(Path("/test")) == BucketType.MOVIES
    
    def test_undo_empty_stack(self):
        """Undo with empty stack returns False."""
        manager = BucketManager()
        assert manager.undo() is False
    
    def test_redo_empty_stack(self):
        """Redo with empty stack returns False."""
        manager = BucketManager()
        assert manager.redo() is False


# =============================================================================
# Database Persistence Tests
# =============================================================================

class TestDatabasePersistence:
    """Tests for saving/loading bucket assignments to database."""
    
    @pytest.fixture
    def temp_db(self, tmp_path):
        """Create a temporary database."""
        return tmp_path / "test_data.db"
    
    def test_save_to_database(self, temp_db):
        """Save bucket assignments to database."""
        manager = BucketManager()
        manager.add_item(BucketType.MOVIES, BucketItem(
            Path("/movie1.mkv"), "movie1.mkv", False, 1000, 1
        ))
        manager.add_item(BucketType.TV_SHOWS, BucketItem(
            Path("/show1"), "show1", True, 5000, 10
        ))
        
        success = manager.save_to_database(temp_db)
        
        assert success
        assert temp_db.exists()
        
        # Verify data in database
        conn = sqlite3.connect(str(temp_db))
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM bucket_assignments')
        count = cursor.fetchone()[0]
        conn.close()
        
        assert count == 2
    
    def test_load_from_database(self, temp_db):
        """Load bucket assignments from database."""
        # First save some data
        manager1 = BucketManager()
        manager1.add_item(BucketType.MOVIES, BucketItem(
            Path("/movie.mkv"), "movie.mkv", False, 2000, 1, auto_assigned=True
        ))
        manager1.save_to_database(temp_db)
        
        # Load into new manager
        manager2 = BucketManager()
        success = manager2.load_from_database(temp_db)
        
        assert success
        assert len(manager2.buckets[BucketType.MOVIES].items) == 1
        assert manager2.buckets[BucketType.MOVIES].items[0].name == "movie.mkv"
        assert manager2.buckets[BucketType.MOVIES].items[0].auto_assigned
    
    def test_load_nonexistent_database(self, tmp_path):
        """Load from non-existent database returns False."""
        manager = BucketManager()
        result = manager.load_from_database(tmp_path / "nonexistent.db")
        assert result is False


# =============================================================================
# Per-Bucket Prompts Tests
# =============================================================================

class TestPerBucketPrompts:
    """Tests for per-bucket LLM prompts."""
    
    def test_base_prompt_content(self):
        """Base prompt contains required elements."""
        prompt = PromptBuilder.get_base_prompt()
        
        assert "media library organizer" in prompt.lower()
        assert "Jellyfin" in prompt
        assert "confidence" in prompt.lower()
        assert "JSON" in prompt
    
    def test_movie_prompt_contains_movie_patterns(self):
        """Movie prompt includes movie-specific patterns."""
        prompt = PromptBuilder.get_movie_prompt("Test folder structure")
        
        assert "MOVIES" in prompt
        assert "Year" in prompt or "year" in prompt
        assert "720p" in prompt or "1080p" in prompt
        assert "BluRay" in prompt.lower() or "bluray" in prompt.lower()
    
    def test_tv_show_prompt_contains_episode_patterns(self):
        """TV show prompt includes episode patterns."""
        prompt = PromptBuilder.get_tv_show_prompt("Test folder structure")
        
        assert "TV SHOW" in prompt.upper()
        assert "S01E01" in prompt or "episode" in prompt.lower()
        assert "season" in prompt.lower()
    
    def test_game_prompt_contains_platform_info(self):
        """Game prompt includes platform information."""
        prompt = PromptBuilder.get_game_prompt("Test folder structure")
        
        assert "GAME" in prompt.upper()
        assert "PC" in prompt or "PlayStation" in prompt
    
    def test_music_prompt_contains_artist_info(self):
        """Music prompt includes artist/album information."""
        prompt = PromptBuilder.get_music_prompt("Test folder structure")
        
        assert "MUSIC" in prompt.upper()
        assert "Artist" in prompt or "artist" in prompt
        assert "Album" in prompt or "album" in prompt
    
    def test_book_prompt_contains_author_info(self):
        """Book prompt includes author information."""
        prompt = PromptBuilder.get_book_prompt("Test folder structure")
        
        assert "BOOK" in prompt.upper()
        assert "Author" in prompt or "author" in prompt
    
    def test_get_prompt_for_bucket(self):
        """Get appropriate prompt for each bucket type."""
        for bt in BucketType:
            prompt = PromptBuilder.get_prompt_for_bucket(bt, "Test data")
            assert len(prompt) > 100  # Reasonable length
            assert "JSON" in prompt  # All prompts require JSON output


# =============================================================================
# Folder Summary Builder Tests
# =============================================================================

class TestFolderSummaryBuilder:
    """Tests for building folder summaries."""
    
    def test_build_summary_for_files(self):
        """Build summary for file items."""
        items = [
            BucketItem(Path("/movie1.mkv"), "Movie 1.mkv", False, 1024*1024*1500, 1),
            BucketItem(Path("/movie2.mkv"), "Movie 2.mkv", False, 1024*1024*2000, 1),
        ]
        
        summary = build_folder_summary_for_bucket(items)
        
        assert "Movie 1.mkv" in summary
        assert "Movie 2.mkv" in summary
        assert "📄" in summary  # File icon
    
    def test_build_summary_for_folders(self):
        """Build summary for folder items."""
        items = [
            BucketItem(Path("/TV Show 1"), "TV Show 1", True, 50*1024**3, 62),
            BucketItem(Path("/TV Show 2"), "TV Show 2", True, 30*1024**3, 48),
        ]
        
        summary = build_folder_summary_for_bucket(items)
        
        assert "TV Show 1" in summary
        assert "62 files" in summary
        assert "📁" in summary  # Folder icon
    
    def test_summary_respects_max_items(self):
        """Summary truncates when exceeding max_items."""
        items = [BucketItem(Path(f"/item{i}"), f"item{i}", False) for i in range(150)]
        
        summary = build_folder_summary_for_bucket(items, max_items=100)
        
        assert "50 more items" in summary


# =============================================================================
# PerBucketAnalyzer Tests
# =============================================================================

class TestPerBucketAnalyzer:
    """Tests for PerBucketAnalyzer class."""
    
    def test_analyze_empty_bucket(self):
        """Analyze empty bucket returns empty status."""
        analyzer = PerBucketAnalyzer()
        result = analyzer.analyze_bucket(BucketType.MOVIES, [])
        
        assert result['status'] == 'empty'
        assert result['detected_media'] == []
    
    def test_analyze_bucket_without_llm(self):
        """Analyze bucket without LLM returns prompt."""
        analyzer = PerBucketAnalyzer()
        items = [BucketItem(Path("/movie.mkv"), "Movie.mkv", False, 1000, 1)]
        
        result = analyzer.analyze_bucket(BucketType.MOVIES, items)
        
        assert 'prompt' in result
        assert result['item_count'] == 1
    
    def test_analyze_all_buckets(self):
        """Analyze all non-empty buckets."""
        manager = BucketManager()
        manager.add_item(BucketType.MOVIES, BucketItem(Path("/m1"), "m1", False))
        manager.add_item(BucketType.TV_SHOWS, BucketItem(Path("/t1"), "t1", False))
        
        analyzer = PerBucketAnalyzer()
        results = analyzer.analyze_all_buckets(manager)
        
        assert 'buckets' in results
        assert 'movies' in results['buckets']
        assert 'tv_shows' in results['buckets']
        assert results['total_items'] == 2


# =============================================================================
# Integration Tests
# =============================================================================

class TestSortingCanvasIntegration:
    """Integration tests for the complete Sorting Canvas workflow."""
    
    def test_complete_workflow(self):
        """Test complete categorization workflow."""
        # 1. Create manager
        manager = BucketManager()
        
        # 2. Add items to unsorted
        items = [
            {'path': '/Show.S01E01.mkv', 'name': 'Show.S01E01.mkv', 'is_folder': False,
             'size_bytes': 1000, 'file_count': 1},
            {'path': '/Movie.2020.mkv', 'name': 'Movie.2020.mkv', 'is_folder': False,
             'size_bytes': 2000, 'file_count': 1},
            {'path': '/Unknown', 'name': 'Unknown', 'is_folder': True,
             'size_bytes': 500, 'file_count': 3},
        ]
        manager.auto_categorize_all(items)
        
        # 3. Verify categorization
        assert len(manager.buckets[BucketType.TV_SHOWS].items) == 1
        assert len(manager.buckets[BucketType.MOVIES].items) == 1
        assert len(manager.buckets[BucketType.UNSORTED].items) == 1
        
        # 4. User manually moves item
        manager.move_item(Path('/Unknown'), BucketType.UNSORTED, BucketType.GAMES)
        assert manager.find_item_bucket(Path('/Unknown')) == BucketType.GAMES
        
        # 5. Generate prompts for non-empty buckets
        for bucket in manager.get_non_empty_buckets():
            prompt = PromptBuilder.get_prompt_for_bucket(
                bucket.bucket_type,
                build_folder_summary_for_bucket(bucket.items)
            )
            assert len(prompt) > 100
        
        # 6. Get statistics
        stats = manager.get_statistics()
        assert stats['total_items'] == 3


# =============================================================================
# GUI Tests (require pytest-qt)
# =============================================================================

@pytest.mark.requires_gui
class TestSortingCanvasViewGUI:
    """GUI tests for SortingCanvasView (requires pytest-qt)."""
    
    @pytest.fixture
    def mock_project(self):
        """Create a mock project for testing."""
        class MockProject:
            def __init__(self):
                self.roundup = None
                self.name = "Test Project"
        return MockProject()
    
    @pytest.fixture
    def mock_manager(self):
        """Create a mock project manager for testing."""
        class MockManager:
            pass
        return MockManager()
    
    def test_sorting_canvas_view_creates(self, qtbot, mock_project, mock_manager):
        """SortingCanvasView creates without error."""
        from scripts.ui.sorting_canvas_view import SortingCanvasView
        
        view = SortingCanvasView(mock_project, mock_manager)
        qtbot.addWidget(view)
        
        # Verify basic UI elements
        assert view.auto_sort_btn is not None
        assert view.reset_btn is not None
        assert view.analyze_btn is not None
    
    def test_bucket_widgets_created(self, qtbot, mock_project, mock_manager):
        """All bucket widgets are created."""
        from scripts.ui.sorting_canvas_view import SortingCanvasView
        
        view = SortingCanvasView(mock_project, mock_manager)
        qtbot.addWidget(view)
        
        assert len(view.bucket_widgets) == len(BucketType)
        for bt in BucketType:
            assert bt in view.bucket_widgets
    
    def test_auto_sort_button_works(self, qtbot, mock_project, mock_manager):
        """Auto-sort button triggers categorization."""
        from scripts.ui.sorting_canvas_view import SortingCanvasView
        from scripts.core.file_scanner import FileRecord
        from datetime import datetime
        
        # Create view with some test files
        test_files = [
            FileRecord(
                absolute_path=Path("/test/Show.S01E01.mkv"),
                size_bytes=1000,
                extension=".mkv",
                parent_folder=Path("/test"),
                scan_timestamp=datetime.now()
            )
        ]
        
        view = SortingCanvasView(
            mock_project, mock_manager, scanned_files=test_files
        )
        qtbot.addWidget(view)
        
        # Click auto-sort
        view.auto_sort_btn.click()
        qtbot.wait(100)
        
        # Verify something happened (stats updated)
        assert "items" in view.stats_label.text().lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

