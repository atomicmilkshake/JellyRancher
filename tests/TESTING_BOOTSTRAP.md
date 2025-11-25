# Testing Bootstrap Protocol
**Version:** 1.0 (2025-11-24)

**Role:** You are testing the JellyRancher backend. Philosophy: **"Query before you code, test before you trust."**

---

## MANDATORY STARTUP SEQUENCE

```
1. Read this file completely (you are here)
2. Verify test infrastructure:
   .venv\Scripts\python.exe -m pytest tests/ -v --collect-only
3. Run existing tests to establish baseline:
   .venv\Scripts\python.exe -m pytest tests/ -v
4. Check coverage gaps:
   .venv\Scripts\python.exe -m pytest tests/ --cov=scripts --cov-report=term-missing
5. Identify next module to test from dependency order (see below)
```

---

## IRON RULE #1: Query Function Index FIRST

**Before writing ANY test or implementation, you MUST query the function index.**

The index contains 1,823 functions from earlier iterations. Many are battle-tested and powerful. Reinventing existing functionality wastes time and introduces bugs.

### Required Workflow

```
STEP 1: Query BEFORE implementing
  .venv\Scripts\python.exe tools/query_function_index_semantic.py search "[description]"

STEP 2: Review results for:
  - Existing implementation that does what you need (Score > 0.2 = highly relevant)
  - Similar function to extend
  - Test files in results (existing tests to build on)
  - conftest.py hits (fixtures to reuse)

STEP 3: Document decision in test file docstring:
  # Function Index Query: "search query here"
  # Decision: Using existing X from Y / No suitable code because Z

STEP 4: Queries auto-logged to data/function_index_queries.log
```

### Common Pre-Test Queries

| Before Testing... | Run This Query |
|-------------------|----------------|
| File hashing | `search "MD5 hash calculate verify"` |
| Filename parsing | `search "parse episode filename"` |
| Path generation | `search "generate path jellyfin"` |
| Title cleaning | `search "clean title sanitize"` |
| Database ops | `search "sqlite connection context"` |
| Test fixtures | `search "sample test fixture mock"` |
| Round-Up ops | `search "roundup create save load"` |

**NO EXCEPTIONS. Every test file must document queries performed.**

---

## IRON RULE #2: Test Dependency Order

You cannot reliably test module B if module A (which B depends on) is untested.

### Dependency Tree (Test in This Order)

```
Tier 0: Pure Data Classes (no dependencies)
└── action_plan.py - ProposedOperation, ActionType, Confidence

Tier 1: Core Backend (no Qt dependencies)
├── file_scanner.py - FileScanner, FileRecord (foundational)
├── roundup_manager.py - RoundUpManager, RoundUp (persistence)
├── inventory_repository.py - database layer
├── app_config.py - configuration
├── extrapolation_engine.py - depends on action_plan, file_scanner
└── action_plan_generator.py - depends on action_plan, file_scanner

Tier 2: Media Processing (no Qt)
├── regex_structure_analyzer.py - no mocking needed
├── nfo_generator.py - string generation
└── llm_structure_analyzer.py - mock PoeClient

Tier 3: Workers (Qt mocking required)
└── workers.py - mock QThread

Already Tested (reference these):
└── transaction_manager.py - 20+ tests in tests/test_transaction_manager.py
```

---

## IRON RULE #3: Never Mock What You Can Test Directly

- **Pure functions**: Test directly with real inputs
- **File I/O**: Use pytest `tmp_path` fixture (creates real temp directories)
- **Databases**: Use in-memory SQLite or temp files
- **Qt**: Only mock if absolutely necessary

---

## IRON RULE #4: One Test = One Concept

**Bad:**
```python
def test_scanner_does_everything():
    # 50 lines testing 10 different behaviors
```

**Good:**
```python
def test_scanner_excludes_hidden_files():
    # 5 lines testing one specific behavior

def test_scanner_calculates_md5_when_enabled():
    # 5 lines testing one specific behavior
```

---

## IRON RULE #5: Fixtures Over Repetition

If you copy-paste setup code twice, make it a fixture in `tests/conftest.py`.

Available fixtures (see conftest.py for full list):
- `tmp_path` - pytest built-in temp directory
- `sample_movies_dir` - temp Movies/ structure
- `sample_tv_shows_dir` - temp TV Shows/ structure
- `sample_mixed_media_dir` - comprehensive media structure
- `roundup_base_dir` - temp Round-Up storage location
- `sample_roundup_dir` - pre-created Round-Up with database
- `roundup_manager` - RoundUpManager instance with temp storage
- `mock_logger` - captures log messages
- `in_memory_db` - SQLite in-memory connection

---

## TEST FILE TEMPLATE

```python
"""
Tests for [module_name].

Function Index Queries:
- search "query 1" -> Found X at Y:line (used/not used because Z)
- search "query 2" -> No relevant results

Coverage Target: 80%+ line coverage
"""
import pytest
from pathlib import Path

# Import module under test
from scripts.core.module_name import ClassName


class TestClassName:
    """Tests for ClassName."""
    
    @pytest.fixture
    def instance(self, tmp_path):
        """Create test instance."""
        return ClassName(tmp_path)
    
    @pytest.mark.unit
    def test_method_happy_path(self, instance):
        """Method should return expected result for valid input."""
        # Arrange
        input_data = "valid input"
        
        # Act
        result = instance.method(input_data)
        
        # Assert
        assert result is not None
        assert result.attribute == "expected"
    
    @pytest.mark.unit
    def test_method_raises_on_invalid_input(self, instance):
        """Method should raise ValueError for invalid input."""
        with pytest.raises(ValueError, match="specific error message"):
            instance.method(None)
    
    @pytest.mark.integration
    def test_method_with_filesystem(self, instance, sample_movies_dir):
        """Method should correctly process real filesystem structure."""
        result = instance.method(sample_movies_dir)
        assert len(result) > 0
```

---

## COMMANDS QUICK REFERENCE

```bash
# Run all tests
.venv\Scripts\python.exe -m pytest tests/ -v

# Run single file
.venv\Scripts\python.exe -m pytest tests/test_roundup_manager.py -v

# Run single test
.venv\Scripts\python.exe -m pytest tests/test_roundup_manager.py::TestRoundUpManager::test_create -v

# Run by marker
.venv\Scripts\python.exe -m pytest tests/ -m "unit" -v
.venv\Scripts\python.exe -m pytest tests/ -m "integration" -v

# With coverage
.venv\Scripts\python.exe -m pytest tests/ --cov=scripts --cov-report=html

# Include slow tests
.venv\Scripts\python.exe -m pytest tests/ --run-slow -v

# Skip network tests
.venv\Scripts\python.exe -m pytest tests/ --no-network -v

# Query function index
.venv\Scripts\python.exe tools/query_function_index_semantic.py search "your query"
```

---

## WORKFLOW EXAMPLE

**Task:** Add tests for `RoundUpManager.create()`

### Step 1: Query Function Index
```bash
.venv\Scripts\python.exe tools/query_function_index_semantic.py search "create roundup project initialize test"
```

**Results:**
- `sample_roundup_dir` in conftest.py (Score 0.25) - existing fixture
- `test_create_project` in test_project_manager.py (Score 0.18) - similar pattern

### Step 2: Review Existing Code
Read the fixture and existing test to understand patterns.

### Step 3: Write Test
```python
"""
Tests for RoundUpManager.

Function Index Queries:
- search "create roundup project initialize test" -> Found sample_roundup_dir fixture, test_create_project pattern
- search "roundup metadata json" -> Found RoundUp dataclass structure
"""
import pytest
from scripts.core.roundup_manager import RoundUpManager, RoundUp


class TestRoundUpManagerCreate:
    """Tests for RoundUpManager.create() method."""
    
    @pytest.mark.unit
    def test_create_makes_roundup_directory(self, roundup_base_dir):
        """create() should create .roundup directory structure."""
        # Function Index: Using roundup_base_dir fixture from conftest.py
        manager = RoundUpManager(base_path=roundup_base_dir)
        
        roundup = manager.create("Test Project")
        
        assert roundup.path.exists()
        assert roundup.path.is_dir()
        assert roundup.path.suffix == ".roundup"
    
    @pytest.mark.unit
    def test_create_initializes_metadata_json(self, roundup_base_dir):
        """create() should create valid metadata.json file."""
        manager = RoundUpManager(base_path=roundup_base_dir)
        
        roundup = manager.create("Test Project")
        
        metadata_path = roundup.path / "metadata.json"
        assert metadata_path.exists()
```

### Step 4: Run and Iterate
```bash
.venv\Scripts\python.exe -m pytest tests/test_roundup_manager.py -v
```

---

## WHEN STUCK

1. **Check existing tests**: `tests/test_transaction_manager.py` is the gold standard
2. **Check conftest.py**: Full list of available fixtures
3. **Query function index**: Look for helpers, similar implementations
4. **Read module docstrings**: Often explain intended behavior
5. **Check agent-journal.md**: Phase history may explain design decisions
6. **Ask user**: If truly blocked after above steps

---

## COVERAGE GOALS

| Tier | Target | Rationale |
|------|--------|-----------|
| Tier 0-1 (Core) | 80%+ | Critical path, must be solid |
| Tier 2 (Media) | 70%+ | Important but less critical |
| Tier 3 (Workers) | 60%+ | Qt mocking makes full coverage harder |
| Pure functions | 100% | No excuse, they're easy |

---

## SUCCESS CRITERIA

Before considering testing complete for a module:

- [ ] Function index queried and documented in test file
- [ ] All public methods have at least one test
- [ ] Happy path tested
- [ ] Error cases tested (invalid input, edge cases)
- [ ] Line coverage meets tier target
- [ ] Tests pass: `.venv\Scripts\python.exe -m pytest tests/test_[module].py -v`
- [ ] No flaky tests (run 3x to verify)

---

## CHANGELOG

**v1.0 (2025-11-24):**
- Initial bootstrap document
- Function index mandate codified
- Dependency order established
- Template and workflow examples added

