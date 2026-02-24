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

def find_tables(pattern):
    print(f"--- Searching for tables like '{pattern}' ---")
    cursor.execute(f"SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME LIKE '%{pattern}%'")
    for row in cursor.fetchall():
        print(row[0])
    print()

if len(sys.argv) > 1:
    find_tables(sys.argv[1])
else:
    patterns = ["Religion", "Nature", "Bank", "Fund", "Designation", "Salutation", "Category", "Scheme"]
    for p in patterns:
        find_tables(p)

conn.close()
