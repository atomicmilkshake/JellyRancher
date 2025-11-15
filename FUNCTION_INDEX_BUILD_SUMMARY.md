# Function Index Build Summary

**Date:** 2025-11-13  
**Source:** LLM io logs  
**Output File:** `data/llm_function_index.json`

---

## Build Results

### Processing Statistics
- **Total log files processed:** 89
- **Files containing function data:** 32 (36%)
- **Total function entries found:** 1,906
- **Unique functions indexed:** 1,010
- **Duplicates merged:** 890

### Index Quality
- **Functions with descriptions:** 1,010 (100%)
- **Functions with implementation details:** 1,010 (100%)
- **Functions with parameter documentation:** 880 (87%)
- **Functions with usage examples:** 957 (95%)

---

## Top Files by Function Count

1. `scripts/core/jelly_rancher_main.py`: 91 functions
2. `scripts/core/jellyfin_ui.py`: 71 functions
3. `scripts/tests/test_backends.py`: 42 functions
4. `scripts/core/dialogs/episode_analysis_dialog.py`: 24 functions
5. `scripts/tests/test_movie_name_backend.py`: 23 functions
6. `scripts/seamoth_memory.py`: 23 functions
7. `scripts/core/dialogs/tmdb_cache_dialog.py`: 22 functions
8. `scripts/tests/test_episode_title_backend.py`: 20 functions
9. `scripts/core/dialogs/movie_analysis_dialog.py`: 20 functions
10. `scripts/core/dialogs/wikipedia_cache_dialog.py`: 20 functions

---

## Index Structure

The index is organized in three ways:

### 1. By File Path
Functions are grouped by their source file for easy navigation:
```json
{
  "functions": {
    "scripts/core/jellyfin_ui.py": [
      {
        "name": "function_name",
        "line": 123,
        "description": "...",
        "implementation": "...",
        ...
      }
    ]
  }
}
```

### 2. By Function Name
Quick lookup index for finding all occurrences of a function name:
```json
{
  "index_by_name": {
    "function_name": [
      {
        "file_path": "scripts/core/jellyfin_ui.py",
        "line": 123,
        "key": "function_name::scripts/core/jellyfin_ui.py"
      }
    ]
  }
}
```

### 3. Metadata
Comprehensive statistics and build information:
```json
{
  "metadata": {
    "generated": "2025-11-13T00:13:21.719912",
    "source": "LLM io logs",
    "total_functions": 1010,
    "statistics": {...},
    "build_stats": {...}
  }
}
```

---

## Function Entry Structure

Each function entry includes:

- **name**: Function name
- **line**: Line number in source file
- **description**: What the function does (`what_it_does`)
- **implementation**: How it works (`how_it_works`)
- **docstring**: Enhanced docstring
- **usage_example**: Code usage example
- **notes**: Additional context notes
- **inputs**: Complete parameter specifications
  - parameters: List with name, type, description, required, constraints
  - side_effects: What gets modified
  - dependencies: External dependencies
- **outputs**: Return value specifications
  - return_value: Type, description, examples
  - exceptions: Exception types and conditions
  - side_effects: Output side effects
- **class_name**: If it's a method, the class name
- **is_method**: Boolean indicating if it's a method
- **sources**: List of log files that contributed this data

---

## Usage

### Search by Function Name
```python
import json

with open('data/llm_function_index.json', 'r') as f:
    index = json.load(f)

# Find all occurrences of a function
function_name = "analyze_movie_names"
if function_name in index['index_by_name']:
    for occurrence in index['index_by_name'][function_name]:
        file_path = occurrence['file_path']
        line = occurrence['line']
        # Get full details from functions dict
        functions = index['functions'].get(file_path, [])
        for func in functions:
            if func['name'] == function_name and func['line'] == line:
                print(func['description'])
```

### Browse by File
```python
# Get all functions in a file
file_path = "scripts/core/jellyfin_ui.py"
functions = index['functions'].get(file_path, [])
for func in functions:
    print(f"{func['name']} (line {func['line']})")
```

### Search by Description
```python
# Find functions by keyword in description
keyword = "analyze"
for file_path, funcs in index['functions'].items():
    for func in funcs:
        if keyword.lower() in func.get('description', '').lower():
            print(f"{func['name']} in {file_path}")
```

---

## Next Steps

1. ✅ **Index Built** - Complete
2. ⏭️ **Integration** - Merge with existing `function_index.json` if needed
3. ⏭️ **Search Interface** - Build search/query interface
4. ⏭️ **Capability Tags** - Add capability/category tags
5. ⏭️ **Documentation** - Generate API documentation from index

---

## Notes

- Duplicate functions (same name + file path) were automatically merged
- When merging, the most complete data was preserved
- All source log files are tracked in the `sources` field
- File paths are normalized to use forward slashes
- Line numbers are extracted from file_path strings when present

