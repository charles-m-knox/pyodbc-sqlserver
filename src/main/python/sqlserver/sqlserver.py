import pyodbc
import datetime
import copy


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
        except Exception as e:
            raise Exception('__init__(): SqlServer {},{}, db {} failed with exception while initializing: {}'
                            .format(self.server,
                                    str(self.port),
                                    self.database,
                                    str(e)))

    def close(self):
        """Closes the SQL Server connection.
        """
        try:
            self._connection.close()
        except Exception as e:
            raise Exception('close(): SqlServer {},{}, db {} failed with exception while closing: {}'
                            .format(self.server,
                                    str(self.port),
                                    self.database,
                                    str(e)))

    def truncate_table(self, table_name):
        """Truncates a specified table. Synonymous with deleting all records in a table.

        This is a destructive action, use care.

        Args:
            table_name (str): Name of the table to truncate.

        Returns:
            bool: If it succeeds this function will always return True.
        """
        try:
            self.do_query('TRUNCATE TABLE {}'.format(table_name), commit=True)
            return True
        except Exception as e:
            raise Exception('truncate_table(): SqlServer {}, db {} failed with exception: {}'
                            .format(self.server,
                                    self.database,
                                    str(e)))

    def do_query(self, query, **kwargs):
        """Performs a given SQL query. Can be a pre-parameterized query (recommended for avoiding SQL Injection)

        Args:
            query (str): A normal SQL Query
            **kwargs: Arbitrary keyword arguments:
                parameters_list (list): List of values to write. pyodbc will parameterize by replacing ? characters
                                              with their proper data types. Requires the fields to already be filled in.
                                              Can also be a list of lists, see execute_many
                                              For example: INSERT INTO [{}].[dbo].[{}] (Field1, Field2, Field3) VALUES (?, ?, ?)
                execute_many (bool): If True, and if parameters_list is a list of lists, will use executemany()
                                     to parameterize & execute all items in parameters_list
                commit (bool): If True, will write tell the query to write (commit) records to the database

        Returns:
            list: A list of rows, each row being a SQL Query result
        """
        try:
            execute_many = False
            parameters_list = None
            commit = False

            if kwargs is not None:
                for key, value in kwargs.items():
                    if key == 'execute_many' and value is True:
                        execute_many = True
                    if key == 'parameters_list':
                        parameters_list = value
                    if key == 'commit' and value is True:
                        commit = True

            # Do one of three things: Execute a simple query (read),
            # parameterize a query (write one),
            # or executemany & parameterize (writing many records)
            _cursor = self._connection.cursor()
            if type(parameters_list) is list:
                if execute_many is True:
                    if len(parameters_list) > 0:
                        if type(parameters_list[0]) is list:
                            _cursor.executemany(query, parameters_list)
                        else:
                            raise Exception('execute_many=True, but at least one item in parameters_list was not a list. Requires a list of lists.')
                    else:
                        raise Exception('execute_many=True, but len(parameters_list)=0. Requires a list with non-zero length.')
                else:
                    _cursor.execute(query, parameters_list)
            else:
                _cursor.execute(query)

            if commit is True:
                _cursor.commit()

            rows = None
            try:
                rows = _cursor.fetchall()
            except pyodbc.ProgrammingError:
                if _cursor.nextset():
                    rows = _cursor.fetchall()
            _cursor.close()
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
                commit (bool): If True, will write tell the query to write (commit) records to the database

        Returns:
            list: A list of rows, each row being a SQL Query result
            index: The current index, will be a multiple of page_size. Pass this result into this function in a loop
        """
        try:
            execute_many = False
            parameters_list = None
            commit = False

            if kwargs is not None:
                for key, value in kwargs.items():
                    if key == 'execute_many' and value is True:
                        execute_many = True
                    if key == 'parameters_list':
                        parameters_list = value
                    if key == 'commit':
                        commit = value

            if 'order by' not in query.lower():
                raise Exception('Paginated queries must have an ORDER BY clause')

            paginated_query = '{} OFFSET {} ROWS FETCH NEXT {} ROWS ONLY'.format(query, str(index), str(page_size))
            rows = self.do_query(paginated_query, parameters_list=parameters_list, commit=commit, execute_many=execute_many)
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

    def mirror_table(self, source_table, source_column_names, dest_sql_server, dest_table, order_by_column_index=0, **kwargs):
        """Takes records from a table (belonging to this sql server),
        and puts them into a target SQL Server table.

        By default this action truncates dest_table.

        Args:
            source_table (str): A normal SQL Query
            source_column_names (list): A list containing all of the names of the fields from source_table.
                                        Expect dest_table to contain all of these fields, in addition to a date column,
                                        if specified
            dest_sql_server (SqlServer): Number of results per SQL Query. 100 is a good number
            dest_table (str): The name of the table to write to, must be accessible in dest_sql_server
            order_by_column_index (int): The column to sort by when doing the mirror process, ascending by default
                                         See the kwarg order_by_desc to change order
            **kwargs: Arbitrary keyword arguments:
                page_size (int): Bulk number of items to process at once, default 100
                add_dtm_column (bool): If True, a value of datetime.now() will be inserted as the first item (column).
                                       Recommended to set this field to datetime2(7) in SQL Server.
                                       See add_dtm_column_index for changing the index.
                add_dtm_column_index (int): Specify the 0-based index of the dtm column, default 0.
                order_by_desc (bool): If True, the column specified by order_by_column_index will be sorted DESC instead
                                      of ASC
                limit (int): Impose a limit on how many rows can be written to dest_table
                truncate (bool): If False, will not truncate dest_table. Defaults to True.
                where_conditional (str): A string containing a simple WHERE clause. Example: "ColumnA <> 'T' AND ColumnB <> 'R'"
        Returns:
            records_written (int): The number of records written.
        """
        try:
            page_size = 100
            add_dtm_column = False
            add_dtm_column_index = 0
            order_by_desc = 'DESC'
            limit = None
            truncate = True
            where_conditional = None

            if kwargs is not None:
                for key, value in kwargs.items():
                    if key == 'page_size':
                        page_size = int(value)
                        if page_size <= 0:
                            page_size = 100
                    if key == 'add_dtm_column' and value is True:
                        add_dtm_column = True
                    if key == 'add_dtm_column_index':
                        add_dtm_column_index = int(value)
                    if key == 'order_by_desc' and value is True:
                        order_by_desc = 'ASC'
                    if key == 'limit':
                        limit = int(value)
                    if key == 'truncate' and value is False:
                        truncate = False
                    if key == 'where_conditional' and type(value) is str:
                        where_conditional = str(value)

            # Input validation
            if type(source_column_names) is not list:
                raise Exception('source_column_names was not a list')
            try:
                order_by_column_name = '[{}]'.format(source_column_names[order_by_column_index])
            except Exception as e:
                raise Exception('Setting order_by_column_name threw an exception: {}'.format(str(e)))

            # This will erase the records on the target table
            # Don't mess this up or you'll regret it!
            if truncate is True:
                dest_sql_server.truncate_table(dest_table)

            where_conditional_str = ''
            if where_conditional is not None:
                where_conditional_str += 'WHERE {}'.format(where_conditional)
            # TODO: support custom queries, or just support custom schema (i.e. not dbo)
            query = 'SELECT * FROM [{}].[dbo].[{}] {} ORDER BY {} {}'.format(self.database,
                                                                             source_table,
                                                                             where_conditional_str,
                                                                             order_by_column_name,
                                                                             order_by_desc)

            # Keep track of this and return it at the end
            records_written = 0

            # Start by getting the first page of results from source_table on this sql server
            index = 0
            source_table_results_rows = self.do_query_paginated(query, index=index, page_size=page_size)
            source_table_results = []
            for row in source_table_results_rows[0]:
                source_table_results.append([x for x in row])

            # If the add_dtm_column is true, then add a datetime column at the index specified (0 default)
            # TODO: make this column name a constant
            dest_columns = copy.copy(source_column_names)
            if add_dtm_column is True:
                dest_columns.insert(add_dtm_column_index, 'as_of_dtm')

            # Columns with spaces in them need to have brackets.
            # It's safe to just put brackets around everything
            _dest_columns = []
            for dest_column in dest_columns:
                _dest_columns.append('[{}]'.format(dest_column))

            # Begin the repetitive data read/write process
            while len(source_table_results) > 0:
                # Abort if we have written or will write more records than our limit
                if type(limit) is int:
                    if (records_written + page_size) >= limit:
                        break

                if add_dtm_column is True:
                    _now = datetime.datetime.now()
                    # For each item in the source table, insert the current date at index specified
                    for result in source_table_results:
                        result.insert(add_dtm_column_index, _now)

                dest_sql_query = 'INSERT INTO [{}].[dbo].[{}] ({}) VALUES ({})'.format(dest_sql_server.database,
                                                                                       dest_table,
                                                                                       ', '.join(_dest_columns),
                                                                                       SqlServerDataHelper.get_pre_parameterized_values(_dest_columns))
                # Attempt to write this set of results to the target database
                try:
                    dest_sql_server.do_query(dest_sql_query, parameters_list=source_table_results, execute_many=True, commit=True)
                except Exception as e:
                    raise Exception('Failed to write {} records to the target database {} due to exception: {}'
                                    .format(str(len(source_table_results)), dest_sql_server.database, str(e)))

                records_written += len(source_table_results)

                # Get the next set of records from the source database and continue the while loop
                index += page_size
                source_table_results_rows = self.do_query_paginated(query, index=index, page_size=page_size)
                source_table_results = []
                for row in source_table_results_rows[0]:
                    source_table_results.append([x for x in row])

            return records_written
        except Exception as e:
            raise Exception('mirror_table(): SqlServer {}, db {}, index={}, page_size={}, failed with exception {} while doing query:\n{}'
                            .format(self.server,
                                    self.database,
                                    str(index),
                                    str(page_size),
                                    str(e),
                                    query))

    def write_records(self, records, columns, table_name, **kwargs):
        """Writes a list of records to a given table. Utilizes paginated queries to write.

        Args:
            records (list): List of lists, each list being a record to write
            columns (list): List of strings, each the name of a column
            table_name (str): Name of the table to which the records will be written

            **kwargs: Arbitrary keyword arguments:
                page_size (int): Bulk number of items to process at once, default 100
                add_dtm_column (bool): If True, a value of datetime.now() will be inserted as the first item (column).
                                       Don't include this column in your columns argument.
                                       Recommended to set this field to datetime2(7) in SQL Server.
                add_dtm_column_index (int): Specify the 0-based index of the dtm column, default 0.
                truncate (bool): If True, will truncate table_name before writing records. Defaults to False.
        """
        try:
            page_size = 100
            add_dtm_column = False
            add_dtm_column_index = 0
            truncate = False

            if kwargs is not None:
                for key, value in kwargs.items():
                    if key == 'page_size':
                        page_size = int(value)
                        if page_size <= 0:
                            page_size = 100
                    if key == 'add_dtm_column' and value is True:
                        add_dtm_column = True
                    if key == 'add_dtm_column_index':
                        add_dtm_column_index = int(value)
                    if key == 'truncate' and value is True:
                        truncate = True

            # Input validation
            if type(records) is not list:
                raise Exception('records was not a list')
            if type(columns) is not list:
                raise Exception('columns was not a list')

            # This will erase the records on the target table
            # Don't mess this up or you'll regret it!
            if truncate is True:
                self.truncate_table(table_name)

            # If the add_dtm_column is true, then add a datetime column at the index specified (0 default)
            # TODO: refactor this (duplicated) code
            dest_columns = copy.copy(columns)
            if add_dtm_column is True:
                dest_columns.insert(add_dtm_column_index, 'as_of_dtm')

            # Columns with spaces in them need to have brackets.
            # It's safe to just put brackets around everything
            _dest_columns = []
            for dest_column in dest_columns:
                _dest_columns.append('[{}]'.format(dest_column))

            dest_sql_query = 'INSERT INTO [{}].[dbo].[{}] ({}) VALUES ({})'.format(self.database,
                                                                                   table_name,
                                                                                   ', '.join(_dest_columns),
                                                                                   SqlServerDataHelper.get_pre_parameterized_values(_dest_columns))
            # Write all of the records in the list, using a loop.
            records_written = 0
            index = 0
            while (index + page_size) <= (len(records) + page_size):
                try:
                    _current_records = records[index:index + page_size]
                    if len(_current_records) > 0:
                        # Insert the current datetime for this batch if desired
                        if add_dtm_column is True:
                            _now = datetime.datetime.now()
                            _current_records = copy.copy(records[index:index + page_size])
                            for _record in _current_records:
                                _record.insert(add_dtm_column_index, _now)
                        # Write the records
                        self.do_query(dest_sql_query, parameters_list=_current_records, execute_many=True, commit=True)
                        records_written += len(_current_records)
                    index += page_size
                except Exception as e:
                    raise Exception('Failed to write records[{}:{}] to the target database {} due to exception: {}'
                                    .format(str(index), str(index + page_size), self.database, str(e)))
            return records_written
        except Exception as e:
            raise Exception('write_records(): SqlServer {},{}, db {} failed with exception: {}'
                            .format(self.server,
                                    str(self.port),
                                    self.database,
                                    str(e)))


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

    @staticmethod
    def get_pre_parameterized_values(values):
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

    @staticmethod
    def none_to_dict(value):
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

    @staticmethod
    def get_none_or_int(value):
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

    @staticmethod
    def get_none_or_float(value):
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

    @staticmethod
    def get_none_or_date(value, format='%Y-%m-%d %H:%M:%S.%f'):
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
            return datetime.datetime.strptime(value, format)
        except Exception as e:
            raise Exception('get_none_or_date({}): Exception occurred: {}'.format(str(value), str(e)))

    @classmethod
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

    @staticmethod
    def get_none_or_sql_server_bit(value, yes_no=False):
        """Takes any input value and attempts return a 1 or 0

        Used for propagating either boolean or NULL values to SQL Server

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

    @staticmethod
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
