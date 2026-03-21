from app.db import DB

def check_columns(table_name):
    print(f"\nColumns for {table_name}:")
    try:
        conn = DB.get_connection()
        cursor = conn.cursor()
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

if __name__ == "__main__":
    check_columns('SMS_CourseActivity_Mst')
