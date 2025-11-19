# JellyRancher Error Handling Guidelines

## Overview
This document outlines the comprehensive error handling patterns implemented across the JellyRancher codebase during Phase 33E. These patterns ensure application robustness, graceful degradation, and clear user feedback when errors occur.

## Core Principles

### 1. **Defensive Programming**
- Validate all inputs before processing
- Use safe defaults when operations fail
- Never let a single error crash the entire application
- Log errors with full context for debugging

### 2. **Specific Exception Handling**
- Catch specific exceptions before generic ones
- Handle known error types appropriately
- Provide meaningful error messages to users
- Log technical details for developers

### 3. **Graceful Degradation**
- Continue operation with reduced functionality when possible
- Provide fallback behaviors
- Maintain UI responsiveness during errors
- Clear error indicators without overwhelming users

## Error Handling Patterns

### Pattern 1: Input Validation with Early Return
```python
def method_name(param1, param2):
    try:
        if not param1 or not param1.strip():
            raise ValueError("Parameter cannot be empty")
        if not isinstance(param2, int) or param2 < 0:
            raise ValueError(f"Invalid parameter: {param2}")
        
        # Process with validated inputs
        return process_data(param1, param2)
        
    except ValueError as e:
        logger.error(f"Invalid parameters: {e}")
        return None  # or appropriate default
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return None
```

### Pattern 2: Resource Operations with Specific Error Types
```python
def file_operation(file_path):
    try:
        # Validate path
        if not file_path:
            raise ValueError("File path cannot be None")
        
        # Create directories
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Perform file operation
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        return True
        
    except PermissionError as e:
        logger.error(f"Permission denied: {file_path} - {e}")
        return False
    except OSError as e:
        logger.error(f"OS error: {file_path} - {e}")
        return False
    except UnicodeEncodeError as e:
        logger.error(f"Encoding error: {file_path} - {e}")
        return False
    except ValueError as e:
        logger.error(f"Invalid parameters: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return False
```

### Pattern 3: API/Network Operations
```python
def api_call(endpoint, params):
    try:
        # Validate inputs
        if not endpoint:
            raise ValueError("Endpoint cannot be empty")
        
        # Make request with timeout
        response = requests.get(endpoint, params=params, timeout=10)
        response.raise_for_status()
        
        # Parse response
        data = response.json()
        return data
        
    except requests.exceptions.Timeout as e:
        logger.warning(f"API timeout: {endpoint} - {e}")
        return None
    except requests.exceptions.ConnectionError as e:
        logger.warning(f"API connection error: {endpoint} - {e}")
        return None
    except requests.exceptions.HTTPError as e:
        logger.warning(f"API HTTP error: {endpoint} - {e}")
        return None
    except json.JSONDecodeError as e:
        logger.warning(f"Invalid JSON response: {endpoint} - {e}")
        return None
    except ValueError as e:
        logger.error(f"Invalid parameters: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected API error: {endpoint} - {e}", exc_info=True)
        return None
```

### Pattern 4: UI Operations with Safe State Restoration
```python
def update_ui_component(self, data):
    try:
        # Validate data
        if not data:
            logger.warning("No data provided for UI update")
            return
        
        # Update UI components
        self.table.setRowCount(len(data))
        for row, item in enumerate(data):
            try:
                self.table.setItem(row, 0, QTableWidgetItem(str(item.get('name', 'Unknown'))))
                # ... more UI updates
            except Exception as e:
                logger.warning(f"Error updating UI row {row}: {e}")
                # Fill with error indicators
                self.table.setItem(row, 0, QTableWidgetItem("ERROR"))
        
        logger.debug(f"Updated UI with {len(data)} items")
        
    except Exception as e:
        logger.error(f"Failed to update UI: {e}", exc_info=True)
        # Show user-friendly error
        QMessageBox.warning(self, "Update Error", f"Failed to update display:\n\n{str(e)}")
```

## Exception Types by Category

### Network/API Errors
- `requests.exceptions.Timeout`
- `requests.exceptions.ConnectionError`
- `requests.exceptions.HTTPError`
- `json.JSONDecodeError`

### File System Errors
- `PermissionError`
- `OSError` (includes `FileNotFoundError`, `IsADirectoryError`)
- `UnicodeEncodeError`
- `UnicodeDecodeError`

### Data Validation Errors
- `ValueError`
- `TypeError`
- `KeyError`
- `IndexError`

### UI/PyQt Errors
- `AttributeError` (missing UI components)
- Component-specific exceptions

### Database Errors
- `sqlite3.Error`
- `sqlite3.OperationalError`
- `sqlite3.IntegrityError`

## Logging Guidelines

### Log Levels
- **DEBUG**: Detailed information for troubleshooting
- **INFO**: Normal operation confirmations
- **WARNING**: Recoverable errors that don't stop operation
- **ERROR**: Serious errors that prevent normal operation
- **CRITICAL**: System-threatening errors

### Log Content
- Include relevant context (file paths, IDs, parameters)
- Use `exc_info=True` for unexpected exceptions
- Avoid logging sensitive information
- Use consistent message formats

### Example Logging Patterns
```python
# Success operations
logger.debug(f"Processed {count} items successfully")
logger.info(f"Connected to database: {db_path}")

# Recoverable errors
logger.warning(f"Cache miss for key: {key}")
logger.warning(f"API rate limited, retrying in {delay}s")

# Serious errors
logger.error(f"Database connection failed: {e}", exc_info=True)
logger.error(f"File operation failed: {file_path} - {e}")

# Critical errors
logger.critical(f"Application state corrupted: {e}", exc_info=True)
```

## User Feedback Guidelines

### Error Message Principles
1. **Clear**: Explain what went wrong in simple terms
2. **Actionable**: Suggest what the user can do (if anything)
3. **Non-technical**: Avoid jargon and stack traces
4. **Contextual**: Relate to the user's current action

### Error Dialog Patterns
```python
# For user-actionable errors
QMessageBox.warning(self, "File Error", 
    f"Cannot save file:\n{filename}\n\nPlease check permissions and try again.")

# For system errors
QMessageBox.critical(self, "Connection Error", 
    f"Cannot connect to service:\n\n{str(e)}\n\nPlease check your internet connection.")

# For validation errors
QMessageBox.information(self, "Invalid Input", 
    f"Please provide a valid title.\n\nTitles cannot be empty.")
```

## Testing Error Conditions

### Unit Test Patterns
```python
def test_error_conditions(self):
    # Test invalid inputs
    with self.assertRaises(ValueError):
        self.component.process_data(None)
    
    # Test file system errors
    with patch('builtins.open', side_effect=PermissionError):
        result = self.component.save_file('/restricted/path')
        self.assertFalse(result)
    
    # Test network errors
    with patch('requests.get', side_effect=requests.exceptions.Timeout):
        result = self.component.api_call('http://example.com')
        self.assertIsNone(result)
```

### Integration Test Patterns
```python
def test_graceful_degradation(self):
    # Test with corrupted data
    corrupted_data = {"invalid": "data"}
    result = self.system.process_data(corrupted_data)
    
    # Should not crash, should log error and continue
    self.assertIsNotNone(result)  # Or appropriate fallback
    # Check that error was logged
    # Check that system remains functional
```

## Implementation Checklist

### For Each Method
- [ ] Input validation at method start
- [ ] Specific exception handling for known error types
- [ ] Appropriate logging with context
- [ ] Safe return values or graceful degradation
- [ ] User feedback for UI methods
- [ ] Unit tests for error conditions

### For Each Module
- [ ] Comprehensive error handling in all public methods
- [ ] Consistent logging throughout
- [ ] Clear error messages for users
- [ ] Fallback behaviors for critical operations
- [ ] Documentation of error conditions

## Maintenance

### Regular Reviews
- Review error logs for new exception patterns
- Update error handling as new error types are discovered
- Ensure error messages remain user-friendly
- Test error recovery scenarios

### Code Reviews
- Check for missing error handling in new code
- Verify logging is appropriate and consistent
- Ensure user-facing errors are clear and actionable
- Validate that errors don't break application flow

## Metrics and Monitoring

### Error Tracking
- Count of different error types
- Frequency of specific errors
- User impact assessment
- Recovery success rates

### Alerting
- High-frequency errors
- New error types
- Critical system errors
- User-facing error spikes

This guidelines document should be updated as new error patterns are discovered and handled in the codebase.