from app.db import DB

def check_data():
    print("\n--- SMS_Dept_Mst (Top 5) ---")
    try:
        depts = DB.fetch_all("SELECT TOP 5 pk_Deptid, Departmentname FROM SMS_Dept_Mst")
        for d in depts: print(d)
    except Exception as e: print(e)

    print("\n--- SMS_BranchMst (Top 5) ---")
    try:
        branches = DB.fetch_all("SELECT TOP 5 Pk_BranchId, Branchname FROM SMS_BranchMst")
        for b in branches: print(b)
    except Exception as e: print(e)

    print("\n--- SMS_Course_Mst Sample (Top 1) ---")
    try:
        course = DB.fetch_one("SELECT TOP 1 fk_Deptid, fk_MajorBranch FROM SMS_Course_Mst WHERE fk_Deptid IS NOT NULL OR fk_MajorBranch IS NOT NULL")
        print(course)
    except Exception as e: print(e)

if __name__ == "__main__":
    check_data()
