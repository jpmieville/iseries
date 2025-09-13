import datetime
import ftplib
import logging
import os
import random
from typing import Generator, List, Optional, Union, Any

import pyodbc

__author__ = 'Jean-Paul Miéville'
__version__ = '1.2.0'

# Set up logging
logger = logging.getLogger(__name__)


def rand_filename(length: int = 6) -> str:
    """
    Generate a random filename consisting of uppercase letters.
    
    Args:
        length: The length of the filename (default: 6)
        
    Returns:
        A random string of uppercase letters
        
    Raises:
        ValueError: If length is less than 1
    """
    if length < 1:
        raise ValueError("Length must be at least 1")
    return "".join([chr(random.randint(65, 90)) for _ in range(length)])


def today() -> int:
    """
    Get today's date as an integer in YYYYMMDD format.
    
    Returns:
        Today's date as an integer (e.g., 20231215)
    """
    return int(datetime.datetime.now().strftime('%Y%m%d'))


def now() -> int:
    """
    Get the current time as an integer in HHMMSS format.
    
    Returns:
        Current time as an integer (e.g., 143025 for 14:30:25)
    """
    return int(datetime.datetime.now().strftime('%H%M%S'))


class Connect:
    odbcString = "driver={iSeries Access ODBC Driver};SYSTEM=%s;" \
                 "UserID=%s;PWD=%s;AllowUnsupportedChar=1;DBQ=%s" \
                 ";XDYNAMIC=0;NAM=%i"

    def __init__(self, host: str, user: str, pwd: str, lib: str, 
                 naming: int = 1, autocommit: bool = False) -> None:
        """
        Initialize the connection to an iSeries/AS400 system.

        Args:
            host: The hostname or IP address of the iSeries system
            user: Username for authentication
            pwd: Password for authentication
            lib: Default library to use
            naming: Naming convention (0=SQL naming, 1=DB2 naming)
            autocommit: Whether to enable autocommit mode
            
        Raises:
            pyodbc.Error: If connection fails
            ValueError: If invalid parameters are provided
            
        Note:
            Connection keywords documentation:
            http://publib.boulder.ibm.com/infocenter/iseries/v5r3/index.jsp?topic=/rzaik/connectkeywords.htm
        """
        if not all([host, user, pwd, lib]):
            raise ValueError("All connection parameters (host, user, pwd, lib) are required")
        
        if naming not in (0, 1):
            raise ValueError("Naming convention must be 0 (SQL) or 1 (DB2)")
            
        self.autocommit = autocommit
        self.host = host
        self.user = user.upper()
        self.lib = lib
        self.naming = naming
        self.closed = False
        self.outputLibrary = 'QTEMP'
        self.query_header: Optional[List[str]] = None
        
        # Store password securely (consider using keyring or environment variables in production)
        self._password = pwd
        
        try:
            logger.info(f"Connecting to iSeries host: {host} as user: {user}")
            self.connect = pyodbc.connect(
                Connect.odbcString % (host, user, pwd, lib, naming),
                autocommit=autocommit
            )
            self.cursor = self.connect.cursor()
            logger.info("Successfully connected to iSeries")
        except pyodbc.Error as e:
            logger.error(f"Failed to connect to iSeries: {e}")
            raise

    def close(self) -> None:
        """
        Close the database connection and cursor.
        
        This method is safe to call multiple times.
        """
        if not self.closed:
            try:
                if hasattr(self, 'cursor') and self.cursor:
                    self.cursor.close()
                if hasattr(self, 'connect') and self.connect:
                    self.connect.close()
                logger.info("Connection closed successfully")
            except Exception as e:
                logger.warning(f"Error while closing connection: {e}")
            finally:
                self.closed = True

    def __enter__(self) -> 'Connect':
        return self

    def __exit__(self, exc_type: Optional[type], exc_val: Optional[Exception], 
                 exc_tb: Optional[Any]) -> None:
        self.close()

    def query(self, statement: str, *parameters: Any) -> Generator[Any, None, None]:
        """
        Execute a SQL query and return results as a generator.
        
        Args:
            statement: SQL statement to execute
            *parameters: Parameters for the SQL statement
            
        Returns:
            Generator yielding database rows
            
        Raises:
            pyodbc.Error: If query execution fails
        """
        if self.closed:
            raise RuntimeError("Cannot execute query on closed connection")
            
        # Use a separate cursor to avoid collision with other operations
        cursor = self.connect.cursor()
        
        try:
            logger.debug(f"Executing query: {statement[:100]}...")
            if parameters:
                cursor.execute(statement, parameters)
            else:
                cursor.execute(statement)
            
            try:
                # SELECT statement - has description
                self.query_header = [d[0] for d in cursor.description]
                logger.debug(f"Query returned {len(self.query_header)} columns")
            except TypeError:
                # Non-SELECT statement (UPDATE, INSERT, etc.)
                self.query_header = None
                logger.debug("Query executed successfully (non-SELECT)")
            
            return (row for row in cursor)
            
        except pyodbc.Error as e:
            logger.error(f"Query execution failed: {e}")
            raise
        finally:
            cursor.close()

    def dspfd(self, library: str, output: str, file_name: str = '*ALL', 
              file_type: str = '*MBR', file_attribute: str = '*ALL') -> Optional[Generator[Any, None, None]]:
        """
        'QSYS/DSPFD FILE(MVXBDTA010/*ALL) TYPE(*MBR) OUTPUT(*OUTFILE) OUTFILE(QTEMP/JP12345)'

        DSPFD FILE(MVXCDTA400/*ALL) TYPE(*ACCPTH) OUTPUT(*OUTFILE) FILEATR(*LF) OUTFILE(QTEMP/LOGICAL)
        DSPFD FILE(MVXCDTA001/*ALL) TYPE(*MBR) OUTPUT(*OUTFILE) FILEATR(*PF) OUTFILE(QTEMP/DSPFD)
        """
        #
        dspfd = 'QSYS/DSPFD FILE(%s/%s) TYPE(%s) OUTPUT(*OUTFILE) FILEATR(%s) OUTFILE(%s/%s)'
        cmd = dspfd % (library, file_name, file_type, file_attribute,
                       self.outputLibrary, output)
        #
        return self.executeCLCmd(cmd, output)

    def dspobjd(self, library: str, object: str, object_type: str, output: str, 
                output_member: str = "*REPLACE") -> Optional[Generator[Any, None, None]]:
        """
        DSPOBJD = Display Object Description

        DSPOBJD OBJ(*USRLIBL/APMNGI04) OBJTYPE(*PGM) DETAIL(*FULL) OUTPUT(*OUTFILE)
        OUTFILE(JPM/DPSOBJDFIL) OUTMBR(*FIRST *ADD)

        :param library:
        :param object:
        :return:
        """

        cmd_string = "DSPOBJD OBJ({library}/{object}) OBJTYPE({object_type}) DETAIL(*FULL) OUTPUT(*OUTFILE) " \
                     "OUTFILE({output_lib}/{output}) OUTMBR(*FIRST {output_member})"
        cmd = cmd_string.format(library=library, object=object, object_type=object_type, output_lib=self.outputLibrary,
                                output=output, output_member=output_member)
        return self.executeCLCmd(cmd, output)

    def dspffd(self, library: str, output: str, file_name: str = '*ALL') -> Optional[Generator[Any, None, None]]:
        """
        Execute the CL command DSPFFD - Display File Field Description

        The Display File Field Description (DSPFFD) command shows, prints,
        or places in a database file field-level
        information for one or more files in a specific library or all
        the libraries to which the user has access.

        http://publib.boulder.ibm.com/infocenter/iseries/v5r3/index.jsp?topic=%2Fcl%2Fdspffd.htm

        Example:
        'DSPFFD FILE(MVXBDTA010/MITMAS*) OUTPUT(*OUTFILE) OUTFILE(JMIEVILLE/TEST)'

        """
        dspffd = "QSYS/DSPFFD FILE(%s/%s) OUTPUT(*OUTFILE) OUTFILE(%s/%s)"
        cmd = dspffd % (library, file_name, self.outputLibrary, output)
        return self.executeCLCmd(cmd, output)

    def cpyf(self, from_table: str, from_lib: str, to_table: str, to_lib: str, 
             mbropt: str, crtfile: str) -> None:
        """

        :param from_table:
        :param from_lib:
        :param to_table:
        :param to_lib:
        :param mbropt:
        :param crtfile:
        """
        #
        # 'CPYF FROMFILE(QTEMP/%(table)s700) TOFILE(%(mvxLib)s/%(table)s) MBROPT(*ADD) CRTFILE(*NO) OUTFMT(*CHAR)'
        # 'CPYF FROMFILE(%(fromLib)s/%(table)s) TOFILE(%(toLib)s/%(table)s)
        #  MBROPT(*REPLACE) CRTFILE(*YES) OUTFMT(*CHAR)'
        #
        if mbropt not in ('*NONE', '*ADD', '*REPLACE', '*UPDADD'):
            raise AttributeError('Option %s for MBROPT is not valid' % mbropt)
        if crtfile not in ('*NO', '*YES'):
            raise AttributeError('Option %s for CRTFILE is not valid' % crtfile)
        cmd = 'CPYF FROMFILE({from_lib}/{from_table}) ' \
              'TOFILE({to_lib}/{to_table}) ' \
              'MBROPT({mbropt}) ' \
              'CRTFILE({crtfile}) ' \
              'OUTFMT(*CHAR)'.format(from_lib=from_lib,
                                     from_table=from_table,
                                     to_lib=to_lib,
                                     to_table=to_table,
                                     mbropt=mbropt,
                                     crtfile=crtfile)
        #
        self.executeCLCmd(cmd, output=None)

    def chgdtaara(self, data_area: str, library: str, value: str) -> None:
        """

        :param data_area:
        :param library:
        :param value:
        """
        cmd = "CHGDTAARA DTAARA({library}/{data_area}) VALUE('{value}')".format(library=library,
                                                                                data_area=data_area,
                                                                                value=value)
        self.executeCLCmd(cmd, output=None)

    def executeCLCmd(self, cmd: str, output: Optional[str] = None) -> Optional[Generator[Any, None, None]]:
        """
        Execute a CL (Control Language) command on the iSeries.
        
        Args:
            cmd: CL command to execute
            output: Optional output file name to create in QTEMP
            
        Returns:
            Generator of result rows if output is specified, None otherwise
            
        Raises:
            ValueError: If using DB2 naming convention (not supported)
            pyodbc.Error: If command execution fails
        """
        if self.closed:
            raise RuntimeError("Cannot execute CL command on closed connection")
            
        if self.naming == 1:
            raise ValueError("CL command execution is not supported with DB2 naming convention (naming=1)")
        
        # Escape single quotes in the command
        cmd_escape = cmd.replace("'", "''")
        cl_command = "CALL QSYS.QCMDEXC('%s',%010i.00000)"
        
        try:
            logger.info(f"Executing CL command: {cmd}")
            self.cursor.execute(cl_command % (cmd_escape, len(cmd)))
            
            if output:
                logger.debug(f"Retrieving output from {self.outputLibrary}.{output}")
                self.cursor.execute(f'SELECT * FROM {self.outputLibrary}.{output}')
                return (row for row in self.cursor)
            
            logger.info("CL command executed successfully")
            return None
            
        except pyodbc.Error as e:
            logger.error(f"CL command execution failed: {e}")
            raise

    def ftpSend(self, file_path: str, library: str) -> None:
        """
        Upload a file to the iSeries via FTP.
        
        Args:
            file_path: Local path to the file to upload
            library: Target library on the iSeries
            
        Raises:
            FileNotFoundError: If the local file doesn't exist
            ftplib.all_errors: If FTP operation fails
            
        Warning:
            This method uses FTP credentials from the connection.
            Consider using more secure file transfer methods in production.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        file_name = os.path.basename(file_path)
        
        try:
            logger.info(f"Starting FTP upload of {file_name} to library {library}")
            with ftplib.FTP(self.host, self.user, self._password) as ftp:
                ftp.cwd(library)
                with open(file_path, 'r', encoding='utf-8') as file_handle:
                    ftp.storlines(f'STOR {file_name}', file_handle)
            logger.info(f"Successfully uploaded {file_name}")
        except ftplib.all_errors as e:
            logger.error(f"FTP upload failed: {e}")
            raise
