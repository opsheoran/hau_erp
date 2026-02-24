import os
import pyodbc
import sys
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    driver = '{ODBC Driver 17 for SQL Server}'
    server = os.getenv('DB_SERVER', 'localhost')
    database = os.getenv('DB_NAME')
    username = os.getenv('DB_USERNAME')
    password = os.getenv('DB_PASSWORD')
    
    if username:
        conn_str = f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password};Encrypt=no;TrustServerCertificate=yes;'
    else:
        conn_str = f'DRIVER={driver};SERVER={server};DATABASE={database};Trusted_Connection=yes;Encrypt=no;TrustServerCertificate=yes;'
    return pyodbc.connect(conn_str)

conn = get_connection()
cursor = conn.cursor()

tables = sys.argv[1:] if len(sys.argv) > 1 else [
    'Religion_Mst', 'SAL_Nature_Mst', 'SAL_Bank_Mst', 'fundtype_master', 
    'SAL_Category_Mst', 'SAL_Salutation_Mst', 'SAL_Designation_Mst'
]

for table in tables:
    try:
        print(f"--- {table} ---")
        cursor.execute(f"SELECT TOP 0 * FROM {table}")
        for column in cursor.description:
            print(column[0])
    except Exception as e:
        print(f"ERROR: {e}")
    print()

conn.close()
