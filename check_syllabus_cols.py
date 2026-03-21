from app.db import DB

def check_syllabus_cols():
    print("\n--- Columns ---")
    try:
        mst = DB.fetch_all("SELECT TOP 1 * FROM SMS_syllabusCreation_forCourses_Mst")
        print("Mst:", mst)
        
        trn = DB.fetch_all("SELECT TOP 1 * FROM SMS_syllabusCreation_forCourses_Trn")
        print("Trn:", trn)
    except Exception as e: print(e)

if __name__ == "__main__":
    check_syllabus_cols()
