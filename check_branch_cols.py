from app.db import DB

def check_columns(table_name):
    print(f"\nColumns for {table_name}:")
    try:
        conn = DB.get_connection()
        cursor = conn.cursor()
        cursor.execute(f"SELECT TOP 1 * FROM {table_name}")
        columns = [column[0] for column in cursor.description]
        print(columns)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_columns('SMS_BranchMst')
