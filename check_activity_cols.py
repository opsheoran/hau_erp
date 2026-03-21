import pyodbc
import os
from dotenv import load_dotenv

load_dotenv()

def check_columns(table_name):
    conn_str = f"DRIVER={{SQL Server}};SERVER={os.getenv('DB_SERVER')};DATABASE={os.getenv('DB_NAME')};UID={os.getenv('DB_USER')};PWD={os.getenv('DB_PASSWORD')}"
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    
    print(f"\nColumns for {table_name}:")
    try:
        cursor.execute(f"SELECT TOP 1 * FROM {table_name}")
        columns = [column[0] for column in cursor.description]
        print(columns)
        
        # Also check SMS_Activity_Mst just in case
        if table_name == 'SMS_CourseActivity_Mst':
            print("\nColumns for SMS_Activity_Mst:")
            cursor.execute(f"SELECT TOP 1 * FROM SMS_Activity_Mst")
            columns = [column[0] for column in cursor.description]
            print(columns)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_columns('SMS_CourseActivity_Mst')
