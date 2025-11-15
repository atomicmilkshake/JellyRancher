# Function Index Usage Guide

The LLM function index provides comprehensive documentation for 1,010 functions across 115 files. This guide shows how to use the query tool to search and explore the index.

## Quick Start

```bash
# Show index statistics
python tools/query_function_index.py stats

# Search by function name
python tools/query_function_index.py name analyze_movie_names

# Get full details about a function
python tools/query_function_index.py get analyze_movie_names

# Search by description keyword
python tools/query_function_index.py description "media organization"

# List all functions in a file
python tools/query_function_index.py file scripts/core/jellyfin_ui.py

# Search by capability
python tools/query_function_index.py capability "subtitle"
```

## Commands

### Statistics
View index overview:
```bash
python tools/query_function_index.py stats
```

Output:
- Total functions indexed
- Coverage statistics (descriptions, parameters, examples)
- Number of files and unique function names

### Search by Name
Find functions by name (supports partial matching):
```bash
# Partial match (default)
python tools/query_function_index.py name analyze

# Exact match only
python tools/query_function_index.py name analyze_movie_names --exact

# Show full details
python tools/query_function_index.py name analyze --details
```

### Get Function Details
Get complete information about a specific function:
```bash
# Search all files
python tools/query_function_index.py get analyze_movie_names

# Search specific file
python tools/query_function_index.py get analyze_movie_names --file scripts/core/movie_name_backend.py
```

Shows:
- Function name, file path, line number
- Full description
- Implementation details
- Parameters with types and descriptions
- Return values
- Usage examples
- Notes

### Search by Description
Find functions by keyword in description or implementation:
```bash
python tools/query_function_index.py description "media organization"
python tools/query_function_index.py description "Jellyfin" --details
```

### Search by File
List all functions in a file:
```bash
# Exact file path
python tools/query_function_index.py file scripts/core/jellyfin_ui.py

# Partial match (finds all matching files)
python tools/query_function_index.py file jellyfin_ui

# Show full details
python tools/query_function_index.py file scripts/core/jellyfin_ui.py --details
```

### Search by Capability
Find functions related to a specific capability or domain:
```bash
python tools/query_function_index.py capability "subtitle"
python tools/query_function_index.py capability "metadata" --details
python tools/query_function_index.py capability "cache"
```

Searches in:
- Function descriptions
- Implementation details
- Notes

### List All Functions
List all functions in the index:
```bash
# All functions
python tools/query_function_index.py list

# Limited results
python tools/query_function_index.py list | head -20
```

## Python API

You can also use the index programmatically:

```python
from tools.query_function_index import FunctionIndexQuery

# Initialize
query = FunctionIndexQuery('data/llm_function_index.json')

# Search by name
results = query.search_by_name('analyze', exact=False)
for func in results:
    print(f"{func['name']} in {func['file_path']}")

# Search by description
results = query.search_by_description('media organization')

# Get specific function
func = query.get_function_details('analyze_movie_names')
if func:
    print(func['description'])

# Get all functions in a file
funcs = query.search_by_file('scripts/core/jellyfin_ui.py')

# Get statistics
stats = query.get_statistics()
print(f"Total functions: {stats['total_functions']}")
```

## Examples

### Find all subtitle-related functions
```bash
python tools/query_function_index.py capability subtitle --details
```

### Find functions that handle file operations
```bash
python tools/query_function_index.py description "file" | grep -i "rename\|move\|copy"
```

### Explore a specific module
```bash
# List all functions
python tools/query_function_index.py file scripts/core/jellyfin_ui.py

# Get details on a specific function
python tools/query_function_index.py get create_scan_tab --file scripts/core/jellyfin_ui.py
```

### Find test functions
```bash
python tools/query_function_index.py name test_ --details
```

## Index Structure

The index file (`data/llm_function_index.json`) contains:

1. **Metadata**: Build information and statistics
2. **Functions**: Organized by file path
3. **Index by Name**: Quick lookup by function name

Each function entry includes:
- Name and location (file path + line number)
- Description (`what_it_does`)
- Implementation details (`how_it_works`)
- Parameters/inputs with types and descriptions
- Return values/outputs
- Usage examples
- Dependencies and side effects
- Enhanced docstrings
- Notes

## Tips

1. **Use partial matching** for broader searches
2. **Use `--details`** to see complete function documentation
3. **Combine searches** to narrow down results
4. **Use `grep` or `head`** to filter CLI output
5. **Use the Python API** for programmatic access

## Integration

The index can be integrated into:
- IDE plugins for code navigation
- Documentation generators
- Code analysis tools
- Search interfaces
- AI assistants for code understanding

