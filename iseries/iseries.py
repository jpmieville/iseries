import datetime
import ftplib
import os
import random

import pyodbc

__author__ = 'Jean-Paul Miéville'


def rand_filename(length: int = 6) -> str:
    """

    :param length:
    :return:  Return a random filename with a length equal to the parameter length
    """
    return "".join([chr(random.randint(65, 90)) for _ in range(length)])


def today() -> int:
    """

    :return: Return today date in the format of an integer YYYYMMDD
    """
    return int(datetime.datetime.now().strftime('%Y%m%d'))


def now() -> int:
    """

    :rtype: Return the current time with the format HHMMSS
    """
    return int(datetime.datetime.now().strftime('%H%M%S'))


class Connect(object):
    odbcString = "driver={iSeries Access ODBC Driver};SYSTEM=%s;" \
                 "UserID=%s;PWD=%s;AllowUnsupportedChar=1;DBQ=%s" \
                 ";XDYNAMIC=0;NAM=%i"

    def __init__(self, host, user, pwd, lib, naming=1, autocommit=False):
        """
        Initialize the connection with the as400

        naming = Specifies the naming convention used when referring to
                 tables.
                 0 = SQL naming (default)
                 1 = DB2 Naming

        Connection keyword in
        http://publib.boulder.ibm.com/infocenter/iseries/v5r3/index.jsp?topic=/rzaik/connectkeywords.htm

        :param host:
        :param user:
        :param pwd:
        :param lib:
        :param naming:
        :param autocommit:
        """
        self.autocommit = autocommit
        self.host = host
        self.user = user.upper()
        self.lib = lib
        self.__password__ = pwd
        self.naming = naming
        self.connect = pyodbc.connect(Connect.odbcString % (host,
                                                            user,
                                                            pwd,
                                                            lib,
                                                            naming),
                                      autocommit=autocommit)
        self.cursor = self.connect.cursor()
        self.closed = False
        #
        self.outputLibrary = 'QTEMP'
        #
        self.query_header = None

    def close(self):
        """
        Close the connection
        """
        if not self.closed:
            self.cursor.close()
        self.connect.close()
        self.closed = True

    def __enter__(self):
        return self

    def __exit__(self, error, msg, traceback):
        self.close()

    def query(self, statement, *parameters):
        """

        :param statement:
        :param parameters:
        :return:
        """
        # the query method is using its own cursor to avoid collision if the user uses
        cursor = self.connect.cursor()
        if parameters:
            cursor.execute(statement, parameters)
        else:
            cursor.execute(statement)
        try:
            # select statement
            self.query_header = [d[0] for d in cursor.description]
        except TypeError:
            # other statement like update, insert
            self.query_header = None
        return (row for row in cursor)

    def dspfd(self, library, output, file_name='*ALL', file_type='*MBR', file_attribute='*ALL'):
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

    def dspobjd(self, library, object, object_type, output, output_menber="*REPLACE"):
        """
        DSPOBJD = Display Object Description

        DSPOBJD OBJ(*USRLIBL/APMNGI04) OBJTYPE(*PGM) DETAIL(*FULL) OUTPUT(*OUTFILE)
        OUTFILE(JPM/DPSOBJDFIL) OUTMBR(*FIRST *ADD)

        :param library:
        :param object:
        :return:
        """

        cmd_string = "DSPOBJD OBJ({library}/{object}) OBJTYPE({object_type}) DETAIL(*FULL) OUTPUT(*OUTFILE) " \
                     "OUTFILE({output_lib}/{output}) OUTMBR(*FIRST {output_menber})"
        cmd = cmd_string.format(library=library, object=object, object_type=object_type, output_lib=self.outputLibrary,
                                output=output, output_menber=output_menber)
        return self.executeCLCmd(cmd, output)

    def dspffd(self, library, output, file_name='*ALL'):
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

    def cpyf(self, from_table, from_lib, to_table, to_lib, mbropt, crtfile):
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

    def chgdtaara(self, data_area, library, value):
        """

        :param data_area:
        :param library:
        :param value:
        """
        cmd = "CHGDTAARA DTAARA({library}/{data_area}) VALUE('{value}')".format(library=library,
                                                                                data_area=data_area,
                                                                                value=value)
        self.executeCLCmd(cmd, output=None)

    def executeCLCmd(self, cmd, output=None):
        """
        Execute a CL command
        """
        cmd_escape = cmd.replace("'", "''")
        if self.naming:
            raise ValueError("The execution of CL command is not supported with the naming convention 1")
        cl_command = "CALL QSYS.QCMDEXC('%s',%010i.00000)"
        self.cursor.execute(cl_command % (cmd_escape, len(cmd)))
        #
        if output:
            self.cursor.execute('select * from %s.%s' % (self.outputLibrary,
                                                         output))
            return (row for row in self.cursor)

    def ftpSend(self, file_path, library):
        """
        Put a file by FTP on the i5 on the specified library using
        the user and password defined when an instance of the class is created.
        This not the safest way, but the most convenient.

        """
        ftp = ftplib.FTP(self.host, self.user, self.__password__)
        ftp.cwd(library)
        file_name = os.path.split(file_path)[1]
        with open(file_path, 'r') as file_handle:
            ftp.storlines('STOR %s' % file_name, file_handle)
