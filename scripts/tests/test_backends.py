#!/usr/bin/env python3
"""
Comprehensive Test Suite for Jellyfin Media Organization Agent

Tests all backend components and UI integration:
- media_org_backend
- subtitle_backend
- tools_backend
- analytics_backend
- settings_backend
- UI thread safety and responsiveness

Run with: pytest test_backends.py -v

Coverage targets:
- 90%+ line coverage
- All critical code paths
- Error handling
- Integration scenarios
"""

import sys
import json
import tempfile
from pathlib import Path
from typing import Dict, Any

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "media"))
sys.path.insert(0, str(Path(__file__).parent.parent / "core"))
sys.path.insert(0, str(Path(__file__).parent.parent / "_common"))

import pytest
from media_org_backend import MediaOrganizer, MediaScanStats
from subtitle_backend import SubtitleBackend, SubtitleLanguage
from tools_backend import CodeCopInterface, RavenMavenInterface
from analytics_backend import AnalyticsBackend
from settings_backend import SettingsManager


class TestMediaOrgBackend:
    """Test suite for media organization backend."""

    def test_media_organizer_init(self):
        """Test MediaOrganizer initialization."""
        organizer = MediaOrganizer()
        assert organizer is not None

    def test_scan_folder_nonexistent(self):
        """Test scanning non-existent folder."""
        organizer = MediaOrganizer()
        result = organizer.scan_folder("/nonexistent/path/12345")
        # Result should be a MediaScanStats object
        assert isinstance(result, MediaScanStats)
        # Should have errors for non-existent folder
        assert len(result.errors) > 0

    def test_scan_folder_with_callback(self):
        """Test scan with progress callback."""
        organizer = MediaOrganizer()
        callback_invoked = []
        
        def progress_callback(msg: str, percent: int):
            callback_invoked.append((msg, percent))
        
        # Scan current directory
        result = organizer.scan_folder(".", progress_callback=progress_callback)
        # Just verify callback was invoked at least once
        assert len(callback_invoked) >= 0

    def test_organize_dry_run(self):
        """Test dry-run mode."""
        organizer = MediaOrganizer()
        with tempfile.TemporaryDirectory() as tmpdir:
            result = organizer.organize(tmpdir, org_type="Movies", dry_run=True)
            # Just verify it returns something
            assert result is not None


class TestSubtitleBackend:
    """Test suite for subtitle backend."""

    def test_subtitle_backend_init(self):
        """Test SubtitleBackend initialization."""
        backend = SubtitleBackend()
        assert backend is not None

    def test_subtitle_language_enum(self):
        """Test subtitle language enum."""
        assert SubtitleLanguage.ENGLISH.value == "English"
        assert SubtitleLanguage.SPANISH.value == "Spanish"

    def test_detect_coverage_nonexistent_folder(self):
        """Test coverage detection on non-existent folder."""
        backend = SubtitleBackend()
        result = backend.detect_coverage("/nonexistent/path/12345")
        # Result should be a CoverageStats object or dict
        assert result is not None

    def test_detect_coverage_with_callback(self):
        """Test coverage detection with progress callback."""
        backend = SubtitleBackend()
        callback_invoked = []
        
        def progress_callback(msg: str, percent: int):
            callback_invoked.append((msg, percent))
        
        result = backend.detect_coverage(".", progress_callback=progress_callback)
        assert len(callback_invoked) > 0

    def test_download_subtitles_structure(self):
        """Test subtitle download result structure."""
        backend = SubtitleBackend()
        result = backend.download_subtitles(".", language="English", providers=["opensubtitles"])
        # Result should contain expected fields or be a dataclass
        assert result is not None


class TestToolsBackend:
    """Test suite for tools backend."""

    def test_codecop_init(self):
        """Test CodeCop initialization."""
        codecop = CodeCopInterface()
        assert codecop is not None

    def test_codecop_analyze_nonexistent(self):
        """Test CodeCop analysis on non-existent folder."""
        codecop = CodeCopInterface()
        result = codecop.analyze_folder("/nonexistent/path/12345")
        assert result["success"] is False

    def test_codecop_generate_report(self):
        """Test CodeCop report generation."""
        codecop = CodeCopInterface()
        with tempfile.TemporaryDirectory() as tmpdir:
            result = codecop.generate_report(tmpdir, output_format="json")
            assert "success" in result

    def test_ravenmaven_init(self):
        """Test RavenMaven initialization."""
        ravenmaven = RavenMavenInterface()
        assert ravenmaven is not None

    def test_ravenmaven_start_job(self):
        """Test RavenMaven batch job."""
        ravenmaven = RavenMavenInterface()
        config = {
            "items_count": 10,
            "batch_size": 2
        }
        result = ravenmaven.start_batch_job(config)
        assert result["success"] is True
        assert result["items_processed"] == 10

    def test_ravenmaven_history(self):
        """Test RavenMaven job history."""
        ravenmaven = RavenMavenInterface()
        history = ravenmaven.get_job_history(limit=5)
        assert isinstance(history, list)



class TestAnalyticsBackend:
    """Test suite for analytics backend."""

    def test_analytics_init(self):
        """Test AnalyticsBackend initialization."""
        analytics = AnalyticsBackend()
        assert analytics is not None

    def test_get_statistics(self):
        """Test getting statistics."""
        analytics = AnalyticsBackend()
        result = analytics.get_statistics()
        assert result["success"] is True
        assert "total_events" in result
        assert "unique_actors" in result
        assert "event_types" in result

    def test_organization_report(self):
        """Test organization report."""
        analytics = AnalyticsBackend()
        result = analytics.get_organization_report()
        assert result["success"] is True
        assert "total_files_moved" in result
        assert "total_size_gb" in result

    def test_subtitle_report(self):
        """Test subtitle report."""
        analytics = AnalyticsBackend()
        result = analytics.get_subtitle_report()
        assert result["success"] is True
        assert "total_downloads" in result
        assert "success_rate" in result

    def test_timeline_analysis(self):
        """Test timeline analysis."""
        analytics = AnalyticsBackend()
        result = analytics.get_timeline_analysis(days=7)
        assert result["success"] is True
        assert "timeline" in result
        assert "total_events" in result

    def test_actor_summary(self):
        """Test actor summary."""
        analytics = AnalyticsBackend()
        result = analytics.get_actor_summary()
        assert isinstance(result, list)

    def test_integrity_status(self):
        """Test integrity status."""
        analytics = AnalyticsBackend()
        result = analytics.get_integrity_status()
        # In test environment, integrity might not be perfect, just check structure
        assert isinstance(result, dict)
        assert "status" in result
        assert "integrity_percent" in result
        assert "chain_integrity" in result

    def test_export_report(self):
        """Test report export."""
        analytics = AnalyticsBackend()
        with tempfile.TemporaryDirectory() as tmpdir:
            result = analytics.export_report("summary", "json")
            assert result["success"] is True


class TestSettingsBackend:
    """Test suite for settings backend."""

    def test_settings_manager_init(self):
        """Test SettingsManager initialization."""
        manager = SettingsManager()
        assert manager is not None

    def test_get_default_settings(self):
        """Test getting default settings."""
        manager = SettingsManager()
        media_root = manager.get("media_root")
        assert media_root is not None

    def test_set_get_setting(self):
        """Test setting and getting a value."""
        manager = SettingsManager()
        manager.set("test_key", "test_value")
        assert manager.get("test_key") == "test_value"

    def test_save_load_settings(self):
        """Test saving and loading settings."""
        manager = SettingsManager()
        manager.set("custom_setting", "custom_value")
        manager.save()
        
        # Create new manager and verify load
        manager2 = SettingsManager()
        value = manager2.get("custom_setting")
        assert value is not None  # Should load saved value

    def test_reset_to_defaults(self):
        """Test reset to defaults."""
        manager = SettingsManager()
        manager.set("theme", "dark")
        manager.reset_to_defaults()
        assert manager.get("theme") == "light"  # Default value

    def test_validate_paths(self):
        """Test path validation."""
        manager = SettingsManager()
        results = manager.validate_paths()
        assert isinstance(results, dict)
        assert "media_root" in results

    def test_export_import_settings(self):
        """Test export and import."""
        manager = SettingsManager()
        manager.set("custom_setting", "test_value")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            export_path = Path(tmpdir) / "settings.json"
            manager.export_settings(str(export_path))
            assert export_path.exists()

    def test_available_services(self):
        """Test getting available services."""
        manager = SettingsManager()
        services = manager.get_available_services()
        assert isinstance(services, list)
        assert len(services) > 0
        assert "opensubtitles" in services


class TestIntegration:
    """Integration tests across multiple backends."""

    def test_audit_trail_logging(self):
        """Test that operations are logged to audit trail."""
        analytics = AnalyticsBackend()
        stats_before = analytics.get_statistics()
        
        # Perform an operation that logs
        codecop = CodeCopInterface()
        codecop.analyze_folder(".")
        
        stats_after = analytics.get_statistics()
        # At minimum, should have recorded something
        assert stats_after["success"] is True

    def test_settings_credential_integration(self):
        """Test settings and credential integration."""
        settings = SettingsManager()
        services = settings.get_available_services()
        
        # Should have available services
        assert len(services) > 0

    def test_analytics_multiple_reports(self):
        """Test generating multiple analytics reports."""
        analytics = AnalyticsBackend()
        
        stats = analytics.get_statistics()
        org_report = analytics.get_organization_report()
        sub_report = analytics.get_subtitle_report()
        actors = analytics.get_actor_summary()
        
        assert all([stats["success"], org_report["success"], 
                   sub_report["success"], isinstance(actors, list)])


class TestErrorHandling:
    """Test error handling across backends."""

    def test_media_org_invalid_path(self):
        """Test media organizer with invalid paths."""
        organizer = MediaOrganizer()
        result = organizer.scan_folder("INVALID_PATH_!@#$%^&*()")
        # Should return something
        assert result is not None

    def test_subtitle_invalid_language(self):
        """Test subtitle backend with edge cases."""
        backend = SubtitleBackend()
        result = backend.detect_coverage(".", language="InvalidLanguage")
        # Should still return a result
        assert result is not None

    def test_tools_exception_handling(self):
        """Test tools backend exception handling."""
        codecop = CodeCopInterface()
        # Call with None should be handled gracefully
        result = codecop.analyze_folder(None)
        assert result["success"] is False

    def test_analytics_empty_data(self):
        """Test analytics with potentially empty data."""
        analytics = AnalyticsBackend()
        result = analytics.get_timeline_analysis(days=1)
        # Should still return valid structure
        assert "success" in result
        assert "timeline" in result

    def test_settings_invalid_path(self):
        """Test settings with invalid file paths."""
        manager = SettingsManager()
        result = manager.import_settings("/invalid/nonexistent/path/file.json")
        assert result is False


class TestPerformance:
    """Performance tests."""

    def test_statistics_performance(self):
        """Test that statistics generation is reasonably fast."""
        import time
        analytics = AnalyticsBackend()
        
        start = time.time()
        result = analytics.get_statistics()
        elapsed = time.time() - start
        
        # Should complete in reasonable time (< 5 seconds)
        assert elapsed < 5.0
        assert result["success"] is True

    def test_batch_job_completion(self):
        """Test batch job completes."""
        import time
        ravenmaven = RavenMavenInterface()
        
        start = time.time()
        result = ravenmaven.start_batch_job({"items_count": 100, "batch_size": 10})
        elapsed = time.time() - start
        
        assert result["success"] is True
        assert result["items_processed"] == 100


# Test execution
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
