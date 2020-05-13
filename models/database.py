from psycopg2 import pool


class Database:

    __connection_pool = None
    default_schema = 'public'

    @staticmethod
    def check_table(table_name):
        with CursorFromConnectionPool() as cursor:

            cursor.execute(
                f'''SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE  table_schema = '{Database.default_schema}'
            AND    table_name   = '{table_name}');''')
            table_exist = cursor.fetchone()[0]
            if table_exist:
                return True
            else:
                if table_name == 'author':
                    cursor.execute(
                        f'''CREATE TABLE {Database.default_schema}.author(
                        author_id INTEGER NOT NULL PRIMARY KEY,
                        full_name VARCHAR NOT NULL,
                        job_title VARCHAR,
                        linkedin VARCHAR,
                        contact VARCHAR,
                        articles_counter INTEGER
                        );''')
                elif table_name == 'article':
                    cursor.execute(
                        f'''CREATE TABLE {Database.default_schema}.article(
                        article_id INTEGER NOT NULL PRIMARY KEY,
                        title VARCHAR NOT NULL,
                        url VARCHAR NOT NULL,
                        text VARCHAR NOT NULL,
                        publication_date DATE NOT NULL,
                        author_id INTEGER NOT NULL REFERENCES author(author_id),
                        tag VARCHAR
                        );''')
                else:
                    print(f'"{table_name}" table? Are you sure?')
                return False


    @staticmethod
    def initialise(**kwargs):
        Database.__connection_pool = pool.SimpleConnectionPool(1, 10, **kwargs)
        author_exist = Database.check_table(table_name='author')
        article_exist = Database.check_table(table_name='article')
        if author_exist is False or article_exist is False:
            return False
        else:
            return True



    @staticmethod
    def get_connection():
        return Database.__connection_pool.getconn()

    @staticmethod
    def return_connection(connection):
        Database.__connection_pool.putconn(connection)

    @staticmethod
    def close_all_connections():
        Database.__connection_pool.closeall()


class CursorFromConnectionPool:
    def __init__(self):
        self.conn = None
        self.cursor = None

    def __enter__(self):
        self.conn = Database.get_connection()
        self.cursor = self.conn.cursor()
        return self.cursor

    def __exit__(self, exception_type, exception_value, exception_traceback):
        if exception_value:  # This is equivalent to `if exception_value is not None`
            self.conn.rollback()
        else:
            self.cursor.close()
            self.conn.commit()
        Database.return_connection(self.conn)