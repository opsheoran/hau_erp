from flask import g, has_app_context
import pyodbc
import os
from dotenv import load_dotenv
from functools import lru_cache

load_dotenv()

def _env_bool(name: str, default: bool) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return str(v).strip().lower() in {"1", "true", "t", "yes", "y", "on"}

def _env_int(name: str, default: int) -> int:
    v = os.getenv(name)
    if v is None or str(v).strip() == "":
        return default
    try:
        return int(str(v).strip())
    except Exception:
        return default

class Database:
    def __init__(self):
        self.server = os.getenv('DB_SERVER')
        self.database = os.getenv('DB_NAME')
        self.username = os.getenv('DB_USERNAME')
        self.password = os.getenv('DB_PASSWORD')
        self.driver = os.getenv('DB_DRIVER') or 'ODBC Driver 17 for SQL Server'
        self.encrypt = _env_bool('DB_ENCRYPT', False)
        self.trust_server_certificate = _env_bool('DB_TRUST_SERVER_CERT', True)
        self.pooling = _env_bool('DB_POOLING', True)
        self.mars = _env_bool('DB_MARS', False)
        self.app_name = os.getenv('DB_APP_NAME') or 'hau_erp'
        self.query_timeout = _env_int('DB_COMMAND_TIMEOUT', 0)
        
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
        # If provided, use an explicit ODBC connection string.
        # Example (closest ODBC equivalent of SSMS string):
        # DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=HAU_Client_Backup;
        # Trusted_Connection=yes;Pooling=no;MARS_Connection=no;Encrypt=yes;TrustServerCertificate=yes;APP=SQL Server Management Studio;
        explicit = os.getenv("DB_ODBC_CONN_STR")
        if explicit and explicit.strip():
            return pyodbc.connect(explicit.strip())

        encrypt = "yes" if self.encrypt else "no"
        trust = "yes" if self.trust_server_certificate else "no"
        pooling = "yes" if self.pooling else "no"
        mars = "yes" if self.mars else "no"

        conn_str = (
            f'DRIVER={{{self.driver}}};SERVER={self.server};DATABASE={self.database};'
            f'Trusted_Connection=yes;Encrypt={encrypt};TrustServerCertificate={trust};'
            f'Pooling={pooling};MARS_Connection={mars};APP={self.app_name};'
        )
        if self.username:
            conn_str = (
                f'DRIVER={{{self.driver}}};SERVER={self.server};DATABASE={self.database};'
                f'UID={self.username};PWD={self.password};Encrypt={encrypt};TrustServerCertificate={trust};'
                f'Pooling={pooling};MARS_Connection={mars};APP={self.app_name};'
            )
        return pyodbc.connect(conn_str)

    def _apply_timeout(self, cursor):
        if self.query_timeout and self.query_timeout >= 0:
            try:
                cursor.timeout = int(self.query_timeout)
            except Exception:
                pass

    def fetch_all(self, query, params=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        self._apply_timeout(cursor)
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
        self._apply_timeout(cursor)
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
        self._apply_timeout(cursor)
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
        self._apply_timeout(cursor)
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

    @lru_cache(maxsize=256)
    def get_table_columns(self, table_name, schema='dbo'):
        query = """
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?
            ORDER BY ORDINAL_POSITION
        """
        rows = self.fetch_all(query, [schema, table_name])
        return [r['COLUMN_NAME'] for r in rows]

DB = Database()

# Teardown to close connection if used in app context
def teardown_db(exception):
    db_conn = getattr(g, 'db_conn', None)
    if db_conn is not None:
        try:
            db_conn.close()
        except pyodbc.ProgrammingError:
            pass
