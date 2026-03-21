from app.db import DB

def check_package_columns():
    print("\n--- SMS_CoursePackage_MST Columns ---")
    try:
        conn = DB.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT TOP 1 * FROM SMS_CoursePackage_MST")
        cols = [c[0] for c in cursor.description]
        print(cols)
    except Exception as e: print(e)

if __name__ == "__main__":
    check_package_columns()
