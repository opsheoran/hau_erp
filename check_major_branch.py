from app.db import DB

def check_major_branch():
    print("\n--- Checking fk_MajorBranch for Courses ---")
    try:
        data = DB.fetch_all("SELECT DISTINCT fk_MajorBranch FROM SMS_Course_Mst WHERE fk_MajorBranch IS NOT NULL")
        print(data)
        
        print("\n--- Checking Sample with fk_MajorBranch ---")
        sample = DB.fetch_all("SELECT TOP 5 coursecode, coursename, fk_Deptid, fk_MajorBranch FROM SMS_Course_Mst WHERE fk_MajorBranch IS NOT NULL")
        for s in sample: print(s)
        
    except Exception as e: print(e)

if __name__ == "__main__":
    check_major_branch()
