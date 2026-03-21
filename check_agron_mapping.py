from app.db import DB

def check_agron_mapping():
    print("\n--- Searching for 'Agronomy' in Department_Mst ---")
    try:
        depts = DB.fetch_all("SELECT pk_deptid, description FROM Department_Mst WHERE description LIKE '%Agronomy%'")
        for d in depts: print(f"Department_Mst: {d}")
    except Exception as e: print(e)

    print("\n--- Checking 'AGRON 101 old' in SMS_Course_Mst ---")
    try:
        course = DB.fetch_one("SELECT pk_courseid, coursecode, coursename, fk_Deptid, fk_MajorBranch FROM SMS_Course_Mst WHERE coursecode = 'AGRON 101 old'")
        print(f"Course Data: {course}")
    except Exception as e: print(e)

if __name__ == "__main__":
    check_agron_mapping()
