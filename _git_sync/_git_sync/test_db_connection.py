import os
import pyodbc
from dotenv import load_dotenv

# 1. Load environment variables from .env
load_dotenv()

SERVER = os.getenv('DB_SERVER', 'localhost')
DATABASE = os.getenv('DB_NAME')
USERNAME = os.getenv('DB_USERNAME')
PASSWORD = os.getenv('DB_PASSWORD')

def get_connection_string():
    driver = '{ODBC Driver 17 for SQL Server}'
    # Check if we are using SQL Auth (Username/Password) or Windows Auth (Trusted)
    if USERNAME:
        return (
            f'DRIVER={driver};SERVER={SERVER};DATABASE={DATABASE};'
            f'UID={USERNAME};PWD={PASSWORD};'
            'Encrypt=no;TrustServerCertificate=yes;'
        )
    else:
        return (
            f'DRIVER={driver};SERVER={SERVER};DATABASE={DATABASE};'
            'Trusted_Connection=yes;Encrypt=no;TrustServerCertificate=yes;'
        )

def main():
    print("--- Database Connection Test ---")
    print(f"Target: {SERVER} -> {DATABASE}")
    
    conn_str = get_connection_string()
    
    try:
        # 2. Attempt Connection
        print("Connecting...", end=" ")
        conn = pyodbc.connect(conn_str, timeout=10)
        print("SUCCESS!\n")
        
        cursor = conn.cursor()

        # 3. Check Version
        cursor.execute("SELECT @@VERSION")
        ver = cursor.fetchone()[0]
        # Just print the first line of the version string
        print(f"SQL Server Version: {ver.splitlines()[0]}")

        # 4. Check Current Database Context
        cursor.execute("SELECT DB_NAME()")
        db_context = cursor.fetchone()[0]
        print(f"Connected Database Context: {db_context}")

        # 5. List first 5 user tables to prove read access
        print("\nSample Tables:")
        cursor.execute("SELECT TOP 5 TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE'")
        tables = cursor.fetchall()
        
        if tables:
            for t in tables:
                print(f" - {t[0]}")
        else:
            print("Connected, but no tables found (empty database?).")

        conn.close()
        print("\n--- Test Complete: OK ---")

    except Exception as e:
        print(f"\nFAILED: {e}")
        print("\nTroubleshooting Tips:")
        print("1. Check if SQL Server is running.")
        print("2. Verify the DB_NAME in .env matches your SQL Server database.")
        print("3. If using Windows Auth, ensure the current user has permission.")
        print("4. If using SQL Auth, check DB_USERNAME and DB_PASSWORD.")

if __name__ == "__main__":
    main()
