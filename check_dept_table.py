from app.db import DB

def check_dept_table():
    print("\n--- Columns of Department_Mst ---")
    try:
        conn = DB.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT TOP 1 * FROM Department_Mst")
        cols = [c[0] for c in cursor.description]
        print(cols)
        
        row = cursor.execute("SELECT TOP 1 * FROM Department_Mst").fetchone()
        print(f"Sample row: {row}")
        
        print("\n--- Sample from SMS_Dept_Mst ---")
        cursor.execute("SELECT TOP 5 pk_Deptid, Departmentname FROM SMS_Dept_Mst")
        for r in cursor.fetchall(): print(r)

    except Exception as e: print(e)

if __name__ == "__main__":
    check_dept_table()
