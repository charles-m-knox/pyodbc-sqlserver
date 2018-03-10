import pyodbc
import datetime


class SqlServer:
    def __init__(self, server, database, username, password, port=1433):
        """Connects to a given SQL Server, unencrypted

        Args:
            server (str): SQL Server hostname or IP
            port (int): Port to connect to
            database (str): Name of the database to connect to
            username (str): Username, must be a local account (Kerberos is not supported at this time)
            password (str): Password
        """
        try:
            self.server = server
            self.database = database
            self.username = username
            self.password = password
            self.port = port

            self._connection = pyodbc.connect('DRIVER={ODBC Driver 13 for SQL Server};' +
                                              'SERVER={},{};DATABASE={};UID={};PWD={}'
                                              .format(self.server,
                                                      str(self.port),
                                                      self.database,
                                                      self.username,
                                                      self.password))
            self._cursor = self._connection.cursor()
        except Exception as e:
            raise Exception('__init__(): SqlServer {},{}, db {} failed with exception while initializing: {}'
                            .format(self.server,
                                    str(self.port),
                                    self.database,
                                    str(e)))

    def do_query(self, query, **kwargs):
        """Performs a given SQL query. Can be a pre-parameterized query (recommended for avoiding SQL Injection)

        Args:
            query (str): A normal SQL Query
            **kwargs: Arbitrary keyword arguments:
                parameters_list (list): List of values to write. pyodbc will parameterize by replacing ? characters
                                        with their proper data types. Requires the fields to already be filled in.
                                        For example: INSERT INTO [{}].[dbo].[{}] (Field1, Field2, Field3) VALUES (?, ?, ?)

        Returns:
            list: A list of rows, each row being a SQL Query result
        """
        try:
            parameters_list = None
            commit = False

            if kwargs is not None:
                for key, value in kwargs.items():
                    if key == 'parameters_list':
                        parameters_list = value
                    if key == 'commit':
                        commit = True

            if type(parameters_list) is list:
                self._cursor.execute(query, parameters_list)
            else:
                self._cursor.execute(query)

            if commit is True:
                self._cursor.commit()

            rows = None
            try:
                rows = self._cursor.fetchall()
            except pyodbc.ProgrammingError:
                if self._cursor.nextset():
                    rows = self._cursor.fetchall()
            return rows
        except Exception as e:
            raise Exception('do_query(): SqlServer {}, db {} failed with exception {} while doing query:\n{}'
                            .format(self.server,
                                    self.database,
                                    str(e),
                                    query))

    def do_query_paginated(self, query, index=0, page_size=100, **kwargs):
        """Automatically paginates a normal SQL query.

        Args:
            query (str): A normal SQL Query
            index (int): An index, starting at 0. Use the value returned from this function in a loop
            page_size (int): Number of results per SQL Query. 100 is a good number
            **kwargs: Arbitrary keyword arguments:
                parameters_list (list): Passthrough. See documentation for SqlServer.do_query()
        Returns:
            list: A list of rows, each row being a SQL Query result
            index: The current index, will be a multiple of page_size. Pass this result into this function in a loop
        """
        try:
            parameters_list = None
            commit = False

            if kwargs is not None:
                for key, value in kwargs.items():
                    if key == 'parameters_list':
                        parameters_list = value
                    if key == 'commit':
                        commit = True

            if 'order by' not in query.lower():
                raise Exception('Paginated queries must have an ORDER BY clause')

            paginated_query = '{} OFFSET {} ROWS FETCH NEXT {} ROWS ONLY;'.format(query, str(index), str(page_size))
            rows = self.do_query(paginated_query, parameters_list=parameters_list, commit=commit)
            index += page_size
            return rows, index
        except Exception as e:
            raise Exception('do_query_paginated(): SqlServer {}, db {}, index={}, page_size={}, failed with exception {} while doing query:\n{}'
                            .format(self.server,
                                    self.database,
                                    str(index),
                                    str(page_size),
                                    str(e),
                                    query))


class SqlServerDataHelper:
    def __init__(self):
        """Does nothing currently

        Placeholder for future potential functionality

        Args:
            N/A
        """
        try:
            pass
        except Exception as e:
            raise Exception('__init__(): SqlServerDataHelper failed with exception while initializing: {}'
                            .format(str(e)))

    def get_pre_parameterized_values(self, values):
        """Converts a list of variables into comma-separated question marks, used for parameterization

        Args:
            values (list): Any list

        Returns:
            str: Example: '?, ?, ?, ?' etc
        """
        try:
            return ', '.join(list(map(lambda x: '?', values)))
        except Exception as e:
            raise Exception('get_pre_parameterized_values({}): Exception occurred: {}'
                            .format(str(values), str(e)))

    def none_to_dict(self, value):
        """If the input is None, returns an empty dictionary

        Useful for chaining multiple x.get().get() operations

        Args:
            value (object): Anything

        Returns:
            object: Only if value is None will the output be {}, otherwise value will be returned
        """
        try:
            if value is None:
                return {}
            return value
        except Exception as e:
            raise Exception('none_to_dict({}): Exception occurred: {}'.format(str(value), str(e)))

    def get_none_or_int(self, value):
        """Takes any input value and attempts return an integer or None

        Used for propagating either integers or NULL values to SQL Server

        Args:
            value (object): Any input that can be parsed by int()

        Returns:
            int: or None if None was passed in originally
        """
        try:
            if value is None:
                return None
            return int(value)
        except Exception as e:
            raise Exception('get_none_or_int({}): Exception occurred: {}'.format(str(value), str(e)))

    def get_none_or_float(self, value):
        """Takes any input value and attempts return a float or None

        Used for propagating either floats or NULL values to SQL Server

        Args:
            value (object): Any input that can be parsed by float()

        Returns:
            float: or None if None was passed in originally
        """
        try:
            if value is None:
                return None
            return float(value)
        except Exception as e:
            raise Exception('get_none_or_float({}): Exception occurred: {}'.format(str(value), str(e)))

    def get_none_or_date(self, value, format='%Y-%m-%d %H:%M:%S.%f'):
        """Takes any input value and attempts return a datetime or None

        Used for propagating either datetimes or NULL values to SQL Server

        Args:
            value (object): Any input that can be parsed by strptime() or None, preferably a string

        Returns:
            datetime: or None if None was passed in originally
        """
        try:
            if value is None:
                return None
            return datetime.datetime.strptime(value, format),
        except Exception as e:
            raise Exception('get_none_or_date({}): Exception occurred: {}'.format(str(value), str(e)))

    def get_iso_date(self, value):
        """Takes any input value and attempts return an ISO 8601 date

        Used for propagating either datetimes or NULL values to SQL Server

        Args:
            value (object): Any input that can be parsed by strptime(), preferably a string with ISO 8601 date format

        Returns:
            datetime: or None if None was passed in originally
        """
        try:
            if value is None:
                return None
            return self.get_none_or_date(value, '%Y-%m-%dT%H:%M:%S.%fZ')
        except Exception as e:
            raise Exception('get_iso_date({}): Exception occurred: {}'.format(str(value), str(e)))

    def get_none_or_sql_server_bit(self, value, yes_no=False):
        """Takes any input value and attempts return a 1 or 0

        Used for propagating either datetimes or NULL values to SQL Server

        Args:
            value (object): Boolean inputs are convetted to 1/0; None is propagated
            yes_no (bool): If True, returns 'Y' or 'N'

        Returns:
            object: Either a 1 or 0, or a string if yes_no is True, or None if None was passed in originally
        """
        if value is True:
            if yes_no is True:
                return 'Y'
            return 1
        elif value is False:
            if yes_no is True:
                return 'N'
            return 0
        return None

    def get_capitalized_uuid(value):
        """Capitalizes any string, or propagates None if given.

        Used primarily for converting UUID's from Python into acceptable SQL Server format

        Args:
            value (object): Strings are converted to uppercase; None is propagated

        Returns:
            object: Either a 1 or 0, or a string if yes_no is True, or None if None was passed in originally
        """
        try:
            if value is not None:
                return str(value).upper()
            return value
        except Exception as e:
            raise Exception('get_capitalized_uuid({}): Exception occurred: {}'.format(str(value), str(e)))
