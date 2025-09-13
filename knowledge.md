# iSeries Python Library Knowledge

## Project Overview
This is a Python library for connecting to iSeries (AS/400) IBM servers using ODBC. It provides a simplified interface over pyODBC with additional iSeries-specific functionality.

## Recent Improvements (v1.2.0)

### Code Quality
- Added comprehensive type hints throughout the codebase
- Improved docstrings with proper Google-style documentation
- Added logging support for better debugging
- Enhanced error handling with specific exception types
- Improved security by avoiding plain text password storage as instance variables

### Key Features
- Context manager support for automatic connection cleanup
- Generator-based query results for memory efficiency
- Comprehensive CL command support
- Built-in FTP functionality
- Type-safe method signatures

### Security Considerations
- Passwords are stored in private attributes (`_password` instead of `__password__`)
- Connection validation before operations
- Proper resource cleanup in context managers
- FTP operations use context managers for secure connection handling

### Best Practices
- Always use context managers when possible
- Check connection status before operations
- Use parameterized queries to prevent SQL injection
- Enable logging for production debugging
- Handle specific exception types appropriately

## Package Structure
- `iseries/iseries.py`: Main module with Connect class and utility functions
- `iseries/__init__.py`: Package initialization with explicit exports
- `setup.py`: Modern packaging configuration with proper metadata
- `README.md`: Comprehensive documentation with examples

## Development Guidelines
- Maintain Python 3.7+ compatibility
- Use type hints for all public methods
- Include comprehensive docstrings
- Add logging for important operations
- Handle errors gracefully with meaningful messages
- Test with actual iSeries connections when possible
