from flask import g, has_app_context
import pyodbc
import os
from dotenv import load_dotenv

load_dotenv()

class Database:
    def __init__(self):
        self.server = os.getenv('DB_SERVER')
        self.database = os.getenv('DB_NAME')
        self.username = os.getenv('DB_USERNAME')
        self.password = os.getenv('DB_PASSWORD')
        
    def get_connection(self):
        # If we're in a Flask request context, reuse the connection
        if has_app_context():
            if 'db_conn' not in g:
                g.db_conn = self._create_connection()
            else:
                try:
                    g.db_conn.cursor()
                except pyodbc.ProgrammingError:
                    g.db_conn = self._create_connection()
            return g.db_conn
        return self._create_connection()

    def _create_connection(self):
        conn_str = (
            f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={self.server};DATABASE={self.database};'
            f'Trusted_Connection=yes;Encrypt=no;TrustServerCertificate=yes;Pooling=True;Min Pool Size=5;Max Pool Size=100;'
        )
        if self.username:
            conn_str = (
                f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={self.server};DATABASE={self.database};'
                f'UID={self.username};PWD={self.password};Encrypt=no;TrustServerCertificate=yes;'
                f'Pooling=True;Min Pool Size=5;Max Pool Size=100;'
            )
        return pyodbc.connect(conn_str)

    def fetch_all(self, query, params=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        columns = [column[0] for column in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        if not has_app_context():
            conn.close()
        return results

    def fetch_one(self, query, params=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        columns = [column[0] for column in cursor.description]
        row = cursor.fetchone()
        
        result = None
        if row:
            result = dict(zip(columns, row))
        
        if not has_app_context():
            conn.close()
        return result

    def fetch_scalar(self, query, params=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        row = cursor.fetchone()
        result = row[0] if (row and row[0] is not None) else 0
        if not has_app_context():
            conn.close()
        return result

    def execute(self, query, params=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            if not has_app_context():
                conn.close()

DB = Database()

# Teardown to close connection if used in app context
def teardown_db(exception):
    db_conn = getattr(g, 'db_conn', None)
    if db_conn is not None:
        try:
            db_conn.close()
        except pyodbc.ProgrammingError:
            pass
