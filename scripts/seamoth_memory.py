#!/usr/bin/env python3
"""
Seamoth Memory Manager

Helper utilities for storing and retrieving memories from OpenMemory
during Jellydive development sessions.

This allows the AI agent to:
- Remember architectural decisions
- Learn from errors (store solutions)
- Track performance optimizations
- Reflect on lessons learned
- Query past context instead of guessing
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List
import time

# Setup OpenMemory SDK - already installed via pip in venv
try:
    from openmemory import OpenMemory
    OPENMEMORY_AVAILABLE = True
except ImportError:
    OPENMEMORY_AVAILABLE = False
    print("WARNING: OpenMemory SDK not available")


class SeamothMemoryManager:
    """
    Memory management for Seamoth development.
    
    Handles:
    - Storing decisions, errors, optimizations, lessons
    - Querying patterns, solutions, context
    - Memory lifecycle (reinforce, delete, audit)
    - Session tracking and summaries
    """
    
    def __init__(self, base_url: str = "http://localhost:8080"):
        """Initialize memory manager"""
        if not OPENMEMORY_AVAILABLE:
            raise RuntimeError("OpenMemory SDK not available")
        
        self.om = OpenMemory(base_url=base_url)
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_start = time.time()
        self._verify_backend()
    
    def _verify_backend(self):
        """Verify backend is running"""
        try:
            health = self.om.health()
            if not health.get('ok'):
                raise RuntimeError("OpenMemory backend unhealthy")
        except Exception as e:
            raise RuntimeError(f"Cannot reach OpenMemory: {e}")
    
    # =====================================================================
    # MEMORY STORAGE OPERATIONS
    # =====================================================================
    
    def store_decision(self, decision_text: str, category: str, 
                      confidence: float = 0.9, reasoning: str = "") -> str:
        """
        Store a development decision.
        
        Args:
            decision_text: What decision was made
            category: Type (architecture, naming, workflow, etc.)
            confidence: How confident (0.0-1.0)
            reasoning: Why this decision
        
        Returns:
            Memory ID
        """
        content = f"DECISION: {decision_text}"
        if reasoning:
            content += f"\n\nREASONING: {reasoning}"
        
        result = self.om.add(
            content=content,
            tags=["decision", category, "seamoth"],
            metadata={
                "session": self.session_id,
                "timestamp": datetime.now().isoformat(),
                "type": "decision",
                "category": category,
                "confidence": confidence,
                "sector": "semantic"  # Decisions are facts
            },
            salience=min(0.95, 0.7 + confidence * 0.25)  # Higher confidence = higher salience
        )
        
        return result.get('id', 'unknown')
    
    def store_error_solution(self, error_type: str, error_message: str, 
                            solution: str, recovery_time_seconds: float,
                            file_or_component: str = "unknown") -> str:
        """
        Store error and its solution for future reference.
        
        Args:
            error_type: Exception type or error code
            error_message: What the error was
            solution: How to fix/prevent it
            recovery_time_seconds: How long recovery took
            file_or_component: What failed
        
        Returns:
            Memory ID
        """
        content = f"ERROR: {error_type}\n\n"
        content += f"MESSAGE: {error_message}\n\n"
        content += f"SOLUTION: {solution}"
        
        result = self.om.add(
            content=content,
            tags=["error", "solution", "troubleshooting", "seamoth"],
            metadata={
                "session": self.session_id,
                "timestamp": datetime.now().isoformat(),
                "type": "error_solution",
                "error_type": error_type,
                "recovery_time": recovery_time_seconds,
                "component": file_or_component,
                "sector": "procedural"  # Procedures to follow
            },
            salience=0.8  # Errors are important
        )
        
        return result.get('id', 'unknown')
    
    def store_optimization(self, pattern: str, description: str,
                          speedup_factor: float = 1.0,
                          before_after: Dict[str, any] = None) -> str:
        """
        Store a performance optimization.
        
        Args:
            pattern: Name of optimization pattern
            description: How it works
            speedup_factor: Performance improvement (e.g., 100x)
            before_after: Benchmark data {before: value, after: value}
        
        Returns:
            Memory ID
        """
        content = f"OPTIMIZATION: {pattern}\n\n"
        content += f"DESCRIPTION: {description}"
        
        if before_after:
            content += f"\n\nBENCHMARK:"
            content += f"\n  Before: {before_after.get('before', 'N/A')}"
            content += f"\n  After: {before_after.get('after', 'N/A')}"
            content += f"\n  Speedup: {speedup_factor}x"
        
        result = self.om.add(
            content=content,
            tags=["optimization", "performance", "pattern", "seamoth"],
            metadata={
                "session": self.session_id,
                "timestamp": datetime.now().isoformat(),
                "type": "optimization",
                "pattern": pattern,
                "speedup_factor": speedup_factor,
                "sector": "procedural"
            },
            salience=0.85 if speedup_factor > 1.5 else 0.75  # Big gains = higher priority
        )
        
        return result.get('id', 'unknown')
    
    def store_lesson(self, lesson_text: str, importance: str = "medium",
                     applies_to: List[str] = None) -> str:
        """
        Store a lesson learned from development.
        
        Args:
            lesson_text: What we learned
            importance: critical, high, medium, low
            applies_to: Components this applies to
        
        Returns:
            Memory ID
        """
        salience_map = {
            "critical": 0.95,
            "high": 0.85,
            "medium": 0.7,
            "low": 0.5
        }
        
        content = f"LESSON: {lesson_text}"
        if applies_to:
            content += f"\n\nAPPLIES TO: {', '.join(applies_to)}"
        
        result = self.om.add(
            content=content,
            tags=["lesson", "reflection", importance.lower(), "seamoth"],
            metadata={
                "session": self.session_id,
                "timestamp": datetime.now().isoformat(),
                "type": "lesson",
                "importance": importance,
                "applies_to": applies_to or [],
                "sector": "reflective"
            },
            salience=salience_map.get(importance.lower(), 0.7)
        )
        
        return result.get('id', 'unknown')
    
    def store_codebase_insight(self, insight: str, file_or_module: str,
                              risk_level: str = "none") -> str:
        """
        Store insights about codebase for future reference.
        
        Args:
            insight: What we learned about the code
            file_or_module: Where this applies
            risk_level: Risk if ignored (none, low, medium, high)
        
        Returns:
            Memory ID
        """
        content = f"CODEBASE INSIGHT: {insight}\n\n"
        content += f"LOCATION: {file_or_module}"
        if risk_level != "none":
            content += f"\n\nRISK IF IGNORED: {risk_level}"
        
        result = self.om.add(
            content=content,
            tags=["codebase", "insight", risk_level, "seamoth"],
            metadata={
                "session": self.session_id,
                "timestamp": datetime.now().isoformat(),
                "type": "codebase_insight",
                "file": file_or_module,
                "risk": risk_level,
                "sector": "semantic"
            },
            salience=0.75 if risk_level != "none" else 0.6
        )
        
        return result.get('id', 'unknown')
    
    # =====================================================================
    # MEMORY RETRIEVAL OPERATIONS
    # =====================================================================
    
    def query_pattern(self, pattern_name: str, top_k: int = 3) -> List[Dict]:
        """
        Query for a specific design pattern or code pattern.
        
        Args:
            pattern_name: What pattern to look for
            top_k: Number of results
        
        Returns:
            List of matching memories
        """
        results = self.om.query(
            query=pattern_name,
            k=top_k,
            filters={'sector': 'procedural'}
        )
        return results.get('matches', []) if results else []
    
    def query_solution(self, problem: str, top_k: int = 3) -> List[Dict]:
        """
        Query for solutions to a problem.
        
        Args:
            problem: Problem description
            top_k: Number of solutions to return
        
        Returns:
            List of possible solutions
        """
        results = self.om.query(
            query=problem,
            k=top_k,
            filters={'tags': ['solution', 'error']}
        )
        return results.get('matches', []) if results else []
    
    def query_sector(self, sector: str, query_text: str = "", 
                     top_k: int = 5) -> List[Dict]:
        """
        Query specific memory sector.
        
        Args:
            sector: episodic, semantic, procedural, emotional, reflective
            query_text: Search query (optional, can be empty)
            top_k: Results to return
        
        Returns:
            List of memories from sector
        """
        if query_text:
            results = self.om.query_sector(query_text, sector, top_k)
        else:
            results = self.om.get_by_sector(sector, limit=top_k)
        
        return results.get('matches', []) if results else []
    
    def query_by_tag(self, tag: str, top_k: int = 5) -> List[Dict]:
        """Query memories by tag"""
        results = self.om.query(
            query=tag,
            k=top_k,
            filters={'tags': [tag]}
        )
        return results.get('matches', []) if results else []
    
    # =====================================================================
    # MEMORY LIFECYCLE OPERATIONS
    # =====================================================================
    
    def reinforce_memory(self, memory_id: str, boost: float = 0.2) -> bool:
        """
        Reinforce a memory (increase salience, delay decay).
        
        Used when: Memory successfully used, proven correct, needs to stay fresh
        
        Args:
            memory_id: ID of memory to reinforce
            boost: How much to boost (typical 0.1-0.3)
        
        Returns:
            Success status
        """
        try:
            result = self.om.reinforce(memory_id, boost)
            return result.get('success', False)
        except Exception:
            return False
    
    def reinforce_by_tag(self, tag: str, boost: float = 0.1) -> int:
        """
        Reinforce all memories with a specific tag.
        
        Used when: Pattern works repeatedly
        
        Args:
            tag: Tag to reinforce
            boost: How much per memory
        
        Returns:
            Number of memories reinforced
        """
        memories = self.query_by_tag(tag, top_k=100)
        count = 0
        for mem in memories:
            if self.reinforce_memory(mem.get('id'), boost):
                count += 1
        return count
    
    def delete_memory(self, memory_id: str) -> bool:
        """
        Delete/forget a memory.
        
        Used when: Information is wrong, outdated, or superseded
        
        Args:
            memory_id: ID to delete
        
        Returns:
            Success status
        """
        try:
            result = self.om.delete(memory_id)
            return result.get('success', False)
        except Exception:
            return False
    
    def mark_deprecated(self, memory_id: str, reason: str = ""):
        """
        Mark a memory as deprecated instead of deleting.
        
        Args:
            memory_id: ID to mark
            reason: Why it's deprecated
        """
        mem = self.om.all(limit=1, offset=0)  # Get one to find structure
        # Add deprecated marker
        self.om.add(
            content=f"DEPRECATED: Memory {memory_id}. {reason}",
            tags=["deprecated", memory_id],
            salience=0.2  # Low priority - don't use
        )
    
    # =====================================================================
    # SESSION MANAGEMENT
    # =====================================================================
    
    def session_summary(self) -> Dict:
        """Get summary of current session and memory status"""
        try:
            health = self.om.health()
            session_duration = time.time() - self.session_start
            
            return {
                "session_id": self.session_id,
                "duration_seconds": session_duration,
                "duration_minutes": round(session_duration / 60, 2),
                "backend_status": "healthy" if health.get('ok') else "unhealthy",
                "memory_count": health.get('total_memories', 'unknown'),
                "version": health.get('version', 'unknown')
            }
        except Exception as e:
            return {
                "session_id": self.session_id,
                "error": str(e),
                "status": "error"
            }
    
    def export_session_memories(self, output_file: Path = None) -> Dict:
        """
        Export all memories from this session.
        
        Args:
            output_file: Optional file to save to
        
        Returns:
            Dictionary of exported data
        """
        import json
        
        session_mems = self.om.query(
            query=self.session_id,
            k=1000,
            filters={'tags': ['seamoth']}
        )
        
        data = {
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "memories": session_mems.get('matches', [])
        }
        
        if output_file:
            output_file.write_text(json.dumps(data, indent=2))
        
        return data
    
    # =====================================================================
    # MEMORY ANALYTICS
    # =====================================================================
    
    def sector_summary(self) -> Dict[str, int]:
        """Get count of memories per sector"""
        summary = {}
        for sector in ["episodic", "semantic", "procedural", "emotional", "reflective"]:
            try:
                results = self.om.get_by_sector(sector, limit=1)
                # Count would be in response if available
                summary[sector] = results.get('count', len(results.get('matches', [])))
            except:
                summary[sector] = 0
        return summary
    
    def get_high_salience_memories(self, min_salience: float = 0.8, 
                                  limit: int = 10) -> List[Dict]:
        """Get most important memories"""
        results = self.om.all(limit=limit)
        if results and 'matches' in results:
            return [m for m in results['matches'] 
                   if m.get('salience', 0) >= min_salience]
        return []
    
    def memory_health_report(self) -> str:
        """Generate a report on memory system health"""
        try:
            summary = self.session_summary()
            sectors = self.sector_summary()
            high_sal = self.get_high_salience_memories()
            
            report = f"""
SEAMOTH MEMORY HEALTH REPORT
════════════════════════════════════════════════════

Session: {summary['session_id']}
Duration: {summary['duration_minutes']} minutes
Status: {summary['backend_status']}
Total Memories: {summary['memory_count']}

MEMORIES BY SECTOR:
"""
            for sector, count in sectors.items():
                report += f"  {sector:15s}: {count:5d}\n"
            
            report += f"\nHIGH SALIENCE MEMORIES ({len(high_sal)}): \n"
            for mem in high_sal[:5]:
                content_preview = mem.get('content', '')[:60]
                report += f"  - {content_preview}... (salience: {mem.get('salience', 0):.2f})\n"
            
            return report
        
        except Exception as e:
            return f"ERROR: Could not generate report: {e}"


# ============================================================================
# CONVENIENCE FUNCTIONS (Quick access)
# ============================================================================

_manager = None

def init_memory(base_url: str = "http://localhost:8080"):
    """Initialize global memory manager"""
    global _manager
    _manager = SeamothMemoryManager(base_url)
    return _manager

def store_decision(decision: str, category: str, **kwargs) -> str:
    """Quick access to store decision"""
    if not _manager:
        init_memory()
    return _manager.store_decision(decision, category, **kwargs)

def store_error(error_type: str, message: str, solution: str, 
               recovery_time: float, **kwargs) -> str:
    """Quick access to store error solution"""
    if not _manager:
        init_memory()
    return _manager.store_error_solution(error_type, message, solution, 
                                         recovery_time, **kwargs)

def query_solution(problem: str) -> List[Dict]:
    """Quick access to query solutions"""
    if not _manager:
        init_memory()
    return _manager.query_solution(problem)

def memory_health() -> str:
    """Quick access to health report"""
    if not _manager:
        init_memory()
    return _manager.memory_health_report()


if __name__ == "__main__":
    # Demo
    print("Seamoth Memory Manager - Demo")
    print("=" * 60)
    
    try:
        mm = SeamothMemoryManager()
        
        # Store some test memories
        print("\n1. Storing decision...")
        dec_id = mm.store_decision(
            "Use synthetic embeddings instead of API keys for OpenMemory",
            "architecture",
            confidence=0.95,
            reasoning="No API keys needed, faster local testing"
        )
        print(f"   Stored: {dec_id}")
        
        print("\n2. Querying solutions...")
        solutions = mm.query_solution("Windows 260 character path")
        print(f"   Found {len(solutions)} solutions")
        if solutions:
            print(f"   First result: {solutions[0].get('content', '')[:100]}...")
        
        print("\n3. Session summary...")
        summary = mm.session_summary()
        print(f"   {summary}")
        
        print("\n4. Memory health report:")
        print(mm.memory_health_report())
        
    except Exception as e:
        print(f"Demo failed: {e}")
        print("\nChromaDB memory system should be automatically initialized.")
        print("No separate server required - using local vector database.")
