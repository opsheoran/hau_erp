from app.db import DB

def check_activity_tables():
    for table in ['SMS_ActivityCategory_Mst', 'SMS_ActivityType_Mst']:
        print(f"\nColumns for {table}:")
        try:
            conn = DB.get_connection()
            cursor = conn.cursor()
            cursor.execute(f"SELECT TOP 1 * FROM {table}")
            cols = [column[0] for column in cursor.description]
            print(cols)
            data = cursor.execute(f"SELECT TOP 5 * FROM {table}").fetchall()
            print("Data:", data)
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    check_activity_tables()
