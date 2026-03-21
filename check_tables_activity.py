from app.db import DB

def list_tables():
    print("\nListing potential activity category tables:")
    try:
        conn = DB.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sys.tables WHERE name LIKE '%Activity%'")
        tables = cursor.fetchall()
        for t in tables:
            print(t[0])
            
        print("\nChecking SMS_Semester_Mst columns:")
        cursor.execute("SELECT TOP 1 * FROM SMS_Semester_Mst")
        cols = [column[0] for column in cursor.description]
        print(cols)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_tables()
