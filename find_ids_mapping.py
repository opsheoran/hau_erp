from app.db import DB

def find_ids():
    terms = ['Mathematics and Statistics', 'Computer Section', 'COA Associate Dean', 'CBNT']
    print(f"\n--- IDs for terms in Department_Mst ---")
    try:
        for t in terms:
            dept = DB.fetch_one("SELECT pk_deptid, description FROM Department_Mst WHERE description LIKE ?", [f'%{t}%'])
            print(dept)
            
            if dept:
                # Search where this ID is used in Course Master
                # Alphanumeric like 'VC-81'
                course_count = DB.fetch_scalar(f"SELECT COUNT(*) FROM SMS_Course_Mst WHERE fk_Deptid = ?", [dept['pk_deptid']])
                print(f"Course count in fk_Deptid: {course_count}")
                
                # Check other possible columns
                for col in ['fk_MajorBranch', 'fk_degreecycleid', 'fk_DeptEmpid']:
                     try:
                         count = DB.fetch_scalar(f"SELECT COUNT(*) FROM SMS_Course_Mst WHERE {col} = ?", [dept['pk_deptid']])
                         if count > 0: print(f"Found {count} in {col}")
                     except: continue

    except Exception as e: print(e)

if __name__ == "__main__":
    find_ids()
