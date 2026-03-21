from app.db import DB

def check_semester_data():
    print("\n--- Semester Data for 6 ---")
    try:
        sems = DB.fetch_all("SELECT pk_semesterid, semester_roman, semesterorder FROM SMS_Semester_Mst WHERE pk_semesterid = 6 OR semesterorder = 6")
        for s in sems: print(s)
    except Exception as e: print(e)

if __name__ == "__main__":
    check_semester_data()
