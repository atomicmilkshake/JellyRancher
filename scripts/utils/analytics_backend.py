#!/usr/bin/env python3
"""
Analytics Backend - Query and analyze audit trail data

Provides high-level analytics and reporting from immutable audit trail.

Features:
- Audit trail statistics
- Organization operation metrics
- Subtitle coverage tracking
- Timeline analysis
- Trend detection

Usage (from UI):
    from analytics_backend import AnalyticsBackend
    
    analytics = AnalyticsBackend()
    stats = analytics.get_statistics()
    org_report = analytics.get_organization_report()
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from collections import defaultdict

# Add common modules to path
sys.path.insert(0, str(Path(__file__).parent / "_common"))

from immutable_audit import ImmutableAuditLog
from logger import ProjectLogger


class AnalyticsBackend:
    """Analytics interface for audit trail analysis."""

    def __init__(self):
        self.audit = ImmutableAuditLog()
        self.audit.initialize()
        self.logger = ProjectLogger("analytics_backend")

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics from audit trail.
        
        Returns:
            Dict with operational statistics
        """
        try:
            results = self.audit.search()
            
            if not results:
                return {
                    "success": True,
                    "total_events": 0,
                    "unique_actors": 0,
                    "event_types": {},
                    "first_event": None,
                    "last_event": None
                }

            # Count event types
            event_counts = defaultdict(int)
            actors = set()
            
            for entry in results:
                event_type = entry.get("event_type", "unknown")
                event_counts[event_type] += 1
                actor = entry.get("actor", "unknown")
                actors.add(actor)

            # Get time range
            sorted_entries = sorted(results, key=lambda x: x.get("timestamp", ""))
            first_event = sorted_entries[0].get("timestamp") if sorted_entries else None
            last_event = sorted_entries[-1].get("timestamp") if sorted_entries else None

            return {
                "success": True,
                "total_events": len(results),
                "unique_actors": len(actors),
                "event_types": dict(event_counts),
                "first_event": first_event,
                "last_event": last_event
            }

        except Exception as e:
            error_msg = f"Failed to get statistics: {str(e)}"
            self.logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "total_events": 0
            }

    def get_organization_report(self) -> Dict[str, Any]:
        """
        Get organization operation report.
        
        Returns:
            Dict with organization metrics
        """
        try:
            results = self.audit.search(event_type="move")
            
            total_files = len(results)
            total_size_moved = 0
            media_types = defaultdict(int)
            
            # Analyze moves
            for entry in results:
                details = entry.get("details", {})
                size = details.get("file_size", 0)
                total_size_moved += size
                
                # Guess media type from source path
                source = details.get("source", "")
                if "Movies" in source:
                    media_types["Movies"] += 1
                elif "TV" in source or "Shows" in source:
                    media_types["TV Shows"] += 1
                elif "Anime" in source:
                    media_types["Anime"] += 1
                else:
                    media_types["Other"] += 1

            # Convert size to GB
            total_size_gb = total_size_moved / (1024 ** 3)

            return {
                "success": True,
                "total_files_moved": total_files,
                "total_size_gb": round(total_size_gb, 2),
                "media_types": dict(media_types),
                "operations": results[:5]  # Last 5 operations
            }

        except Exception as e:
            error_msg = f"Failed to get organization report: {str(e)}"
            self.logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "total_files_moved": 0
            }

    def get_subtitle_report(self) -> Dict[str, Any]:
        """
        Get subtitle operations report.
        
        Returns:
            Dict with subtitle metrics
        """
        try:
            results = self.audit.search(event_type="subtitle_download")
            
            total_downloads = len(results)
            successful = 0
            failed = 0
            languages = defaultdict(int)
            
            for entry in results:
                details = entry.get("details", {})
                if details.get("success", False):
                    successful += 1
                else:
                    failed += 1
                
                language = details.get("language", "unknown")
                languages[language] += 1

            return {
                "success": True,
                "total_downloads": total_downloads,
                "successful": successful,
                "failed": failed,
                "success_rate": round((successful / max(total_downloads, 1)) * 100, 1),
                "languages": dict(languages)
            }

        except Exception as e:
            error_msg = f"Failed to get subtitle report: {str(e)}"
            self.logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "total_downloads": 0
            }

    def get_timeline_analysis(
        self,
        days: int = 7,
        progress_callback: Optional[Callable[[str, int], None]] = None
    ) -> Dict[str, Any]:
        """
        Analyze operations over time.
        
        Args:
            days: Number of days to analyze
            progress_callback: Optional callback(message, percent)
        
        Returns:
            Dict with timeline data
        """
        try:
            if progress_callback:
                progress_callback("Analyzing timeline...", 0)

            results = self.audit.search()
            
            # Group by day
            timeline = defaultdict(int)
            cutoff_date = datetime.now() - timedelta(days=days)
            
            for entry in results:
                timestamp_str = entry.get("timestamp", "")
                try:
                    entry_date = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                    if entry_date >= cutoff_date:
                        date_key = entry_date.strftime("%Y-%m-%d")
                        timeline[date_key] += 1
                except:
                    pass

            if progress_callback:
                progress_callback("Timeline analysis complete", 100)

            # Sort by date
            sorted_timeline = sorted(timeline.items())
            
            return {
                "success": True,
                "days_analyzed": days,
                "timeline": dict(sorted_timeline),
                "total_events": sum(timeline.values()),
                "average_per_day": round(sum(timeline.values()) / max(len(timeline), 1), 1)
            }

        except Exception as e:
            error_msg = f"Failed to analyze timeline: {str(e)}"
            self.logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "timeline": {}
            }

    def get_actor_summary(self) -> List[Dict[str, Any]]:
        """
        Get summary of operations by actor (script).
        
        Returns:
            List of actor summaries
        """
        try:
            results = self.audit.search()
            
            actor_stats = defaultdict(lambda: {"count": 0, "last_event": None, "event_types": defaultdict(int)})
            
            for entry in results:
                actor = entry.get("actor", "unknown")
                actor_stats[actor]["count"] += 1
                actor_stats[actor]["last_event"] = entry.get("timestamp")
                
                event_type = entry.get("event_type", "unknown")
                actor_stats[actor]["event_types"][event_type] += 1

            # Convert to list format
            summary = []
            for actor, stats in sorted(actor_stats.items(), key=lambda x: x[1]["count"], reverse=True):
                summary.append({
                    "actor": actor,
                    "total_events": stats["count"],
                    "last_event": stats["last_event"],
                    "event_types": dict(stats["event_types"])
                })

            return summary

        except Exception as e:
            self.logger.error(f"Failed to get actor summary: {str(e)}")
            return []

    def get_integrity_status(self) -> Dict[str, Any]:
        """
        Get audit trail integrity status.
        
        Returns:
            Dict with integrity information
        """
        try:
            integrity_info = self.audit.verify_chain_integrity()
            integrity_pct = integrity_info['integrity_percentage']
            
            return {
                "success": True,
                "chain_integrity": integrity_info,
                "status": "✓ VERIFIED" if integrity_pct >= 99.9 else "⚠ WARNING" if integrity_pct >= 95 else "✗ CRITICAL",
                "integrity_percent": round(integrity_pct, 2)
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "status": "✗ ERROR"
            }

    def export_report(
        self,
        report_type: str = "summary",
        output_format: str = "json"
    ) -> Dict[str, Any]:
        """
        Export comprehensive report.
        
        Args:
            report_type: "summary", "detailed", or "full"
            output_format: "json", "csv", or "text"
        
        Returns:
            Dict with export status and path
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_name = f"analytics_report_{report_type}_{timestamp}"
            
            # Collect all data
            report_data = {
                "timestamp": timestamp,
                "statistics": self.get_statistics(),
                "organization": self.get_organization_report(),
                "subtitles": self.get_subtitle_report(),
                "integrity": self.get_integrity_status(),
                "actors": self.get_actor_summary()
            }

            # Format report
            if output_format == "json":
                import json
                report_path = Path("reports") / f"{report_name}.json"
                report_path.parent.mkdir(exist_ok=True)
                with open(report_path, 'w') as f:
                    json.dump(report_data, f, indent=2)
            else:
                # Text format
                report_path = Path("reports") / f"{report_name}.txt"
                report_path.parent.mkdir(exist_ok=True)
                with open(report_path, 'w') as f:
                    f.write("ANALYTICS REPORT\n")
                    f.write(f"Generated: {timestamp}\n")
                    f.write("=" * 80 + "\n\n")
                    
                    stats = report_data["statistics"]
                    f.write("OVERALL STATISTICS\n")
                    f.write(f"Total Events: {stats.get('total_events', 0)}\n")
                    f.write(f"Unique Actors: {stats.get('unique_actors', 0)}\n")
                    f.write("\n")

            return {
                "success": True,
                "report_path": str(report_path),
                "format": output_format,
                "type": report_type
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


# Test the backend
if __name__ == "__main__":
    analytics = AnalyticsBackend()
    
    print("Getting statistics...")
    stats = analytics.get_statistics()
    print(f"Total events: {stats['total_events']}")
    print(f"Unique actors: {stats['unique_actors']}\n")
    
    print("Organization Report:")
    org = analytics.get_organization_report()
    print(f"Files moved: {org.get('total_files_moved', 0)}\n")
    
    print("Subtitle Report:")
    subs = analytics.get_subtitle_report()
    print(f"Downloads: {subs.get('total_downloads', 0)}\n")
    
    print("Integrity Status:")
    integrity = analytics.get_integrity_status()
    print(f"Status: {integrity.get('status', 'Unknown')}")
    print(f"Integrity: {integrity.get('integrity_percent', 0)}%")
