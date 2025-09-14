# iSeries Python Library

[![Python Version](https://img.shields.io/badge/python-3.7%2B-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

This modern, type-annotated Python library streamlines ODBC connectivity to IBM iSeries (AS/400) servers. Built on top of pyODBC, it offers a clean, Pythonic interface for seamless interaction with iSeries systems.

On Windows, this library eliminates the need to manually configure user or system DSNs in the ODBC Administrator, allowing direct connections with simple Python code.

## Features

- 🔒 **Secure Connection Management**: Context manager support with automatic cleanup
- 📝 **Type Hints**: Full type annotation support for better IDE experience
- 🛡️ **Error Handling**: Comprehensive exception handling with detailed logging
- 🔧 **CL Command Support**: Execute iSeries CL commands directly from Python
- 📊 **Query Interface**: Simple, generator-based query execution
- 📁 **File Operations**: Built-in support for common iSeries file operations (DSPFD, DSPFFD, etc.)
- 🌐 **FTP Integration**: Upload files to iSeries via FTP
- 📚 **Well Documented**: Comprehensive docstrings and examples

## Installation

```bash
pip install iseries
```

### Requirements

- Python 3.7+
- pyodbc 4.0+
- iSeries Access ODBC Driver

## Quick Start

### Basic Connection

```python
from iseries import Connect

# Using context manager (recommended)
with Connect(host='your-iseries', user='username', 
             pwd='password', lib='MYLIB') as conn:
    # Execute a query
    results = conn.query("SELECT * FROM MYTABLE")
    for row in results:
        print(row)
```

### Manual Connection Management

```python
from iseries import Connect

conn = Connect(host='your-iseries', user='username', 
               pwd='password', lib='MYLIB')
try:
    results = conn.query("SELECT COUNT(*) FROM MYTABLE")
    count = next(results)[0]
    print(f"Table has {count} rows")
finally:
    conn.close()
```

### Executing CL Commands

```python
with Connect(host='your-iseries', user='username', 
             pwd='password', lib='MYLIB') as conn:
    # Display file field description
    results = conn.dspffd('MYLIB', 'OUTFILE', 'MYTABLE')
    for row in results:
        print(row)
```

### File Upload via FTP

```python
with Connect(host='your-iseries', user='username', 
             pwd='password', lib='MYLIB') as conn:
    conn.ftpSend('/path/to/local/file.txt', 'TARGETLIB')
```

## Advanced Usage

### Custom Naming Convention

```python
# Use SQL naming convention (default is DB2)
with Connect(host='your-iseries', user='username', 
             pwd='password', lib='MYLIB', naming=0) as conn:
    results = conn.query("SELECT * FROM MYLIB.MYTABLE")
```

### Parameterized Queries

```python
with Connect(host='your-iseries', user='username', 
             pwd='password', lib='MYLIB') as conn:
    results = conn.query("SELECT * FROM MYTABLE WHERE ID = ?", 123)
    for row in results:
        print(row)
```

## Utility Functions

```python
from iseries import rand_filename, today, now

# Generate random filename
filename = rand_filename(8)  # e.g., 'ABCD1234'

# Get current date as integer (YYYYMMDD)
current_date = today()  # e.g., 20231215

# Get current time as integer (HHMMSS)
current_time = now()  # e.g., 143025
```

## Error Handling

The library provides comprehensive error handling:

```python
import pyodbc
from iseries import Connect

try:
    with Connect(host='invalid-host', user='user', 
                 pwd='pwd', lib='LIB') as conn:
        results = conn.query("SELECT * FROM NONEXISTENT")
except pyodbc.Error as e:
    print(f"Database error: {e}")
except ValueError as e:
    print(f"Configuration error: {e}")
except FileNotFoundError as e:
    print(f"File operation error: {e}")
```

## API Reference

### Connect Class

#### Constructor

```python
Connect(host, user, pwd, lib, naming=1, autocommit=False)
```

**Parameters:**

- `host` (str): iSeries hostname or IP address
- `user` (str): Username for authentication
- `pwd` (str): Password for authentication  
- `lib` (str): Default library
- `naming` (int): Naming convention (0=SQL, 1=DB2, default=1)
- `autocommit` (bool): Enable autocommit mode (default=False)

#### Methods

- `query(statement, *parameters)`: Execute SQL query
- `executeCLCmd(cmd, output=None)`: Execute CL command
- `dspfd(library, output, file_name='*ALL', ...)`: Display file description
- `dspffd(library, output, file_name='*ALL')`: Display file field description
- `dspobjd(library, object, object_type, output, ...)`: Display object description
- `cpyf(from_table, from_lib, to_table, to_lib, mbropt, crtfile)`: Copy file
- `chgdtaara(data_area, library, value)`: Change data area
- `ftpSend(file_path, library)`: Upload file via FTP
- `close()`: Close connection

## Security Considerations

⚠️ **Important**: This library stores credentials in memory during execution. For production use, consider:

- Using environment variables for credentials
- Implementing credential management systems
- Using encrypted configuration files
- Regular credential rotation

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

### Version 1.2.0

- Added comprehensive type hints
- Improved error handling and logging
- Enhanced documentation
- Better security practices
- Updated package metadata

### Version 1.1

- Initial release
