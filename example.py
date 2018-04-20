from sqlserver import SqlServer  # , SqlServerDataHelper
import yaml
import argparse


def main():
    config = None

    parser = argparse.ArgumentParser(description='Logs into a SQL Server and runs a basic query')
    parser.add_argument('--config', default='config.yml', help='name of config file')
    args = parser.parse_args()
    args_dict = vars(args)

    with open(args_dict['config'], 'r') as stream:
        config = yaml.safe_load(stream)

    if config is None:
        raise Exception('Config could not be loaded')

    server = config.get('sql_server', {}).get('server', None)
    database = config.get('sql_server', {}).get('database', None)
    username = config.get('sql_server', {}).get('username', None)
    password = config.get('sql_server', {}).get('password', None)
    port = config.get('sql_server', {}).get('port', None)

    print('Logging in...')

    my_sql_server = SqlServer(server, database, username, password, port)

    my_sql_query_results = my_sql_server.do_query('SELECT 1')

    for result in my_sql_query_results:
        print(result[0])

    # records_written = my_sql_server.mirror_table('Table_1', source_column_names, my_sql_server, 'Table_2', where_conditional="something <> NULL")
    # print(records_written)

    # my_sql_server.truncate_table('Table_1')
    # my_sql_server.write_records([[str(x)] for x in range(0, 500)], ['test'], 'Table_3', page_size=200)


if __name__ == '__main__':
    main()
