from app.db import DB

def find_numeric_mapping():
    term = 'Agronomy'
    print(f"\n--- Searching for '{term}' with Numeric ID ---")
    try:
        # Search SMS_Dept_Mst for numeric mapping
        depts = DB.fetch_all("SELECT pk_Deptid, Departmentname FROM SMS_Dept_Mst WHERE Departmentname LIKE ?", [f'%{term}%'])
        for d in depts: print(f"SMS_Dept_Mst: {d}")
        
        # Search Branch for numeric mapping
        branches = DB.fetch_all("SELECT Pk_BranchId, Branchname FROM SMS_BranchMst WHERE Branchname LIKE ?", [f'%{term}%'])
        for b in branches: print(f"SMS_BranchMst: {b}")

    except Exception as e: print(e)

if __name__ == "__main__":
    find_numeric_mapping()
