from app.db import DB

def check_course_columns():
    for table in ['SMS_Course_Mst', 'SMS_Course_Mst_Dtl']:
        print(f"\nColumns for {table}:")
        try:
            conn = DB.get_connection()
            cursor = conn.cursor()
            cursor.execute(f"SELECT TOP 1 * FROM {table}")
            cols = [column[0] for column in cursor.description]
            print(cols)
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    check_course_columns()
