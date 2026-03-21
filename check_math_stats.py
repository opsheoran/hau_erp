from app.db import DB

def check_math_stats():
    print("\n--- Searching for 'Mathematics and Statistics' in SMS_Dept_Mst ---")
    try:
        depts = DB.fetch_all("SELECT pk_Deptid, Departmentname FROM SMS_Dept_Mst WHERE Departmentname LIKE '%Mathematics%'")
        for d in depts: print(d)
    except Exception as e: print(e)

if __name__ == "__main__":
    check_math_stats()
