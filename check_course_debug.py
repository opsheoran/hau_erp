from app.db import DB

def check_course_data():
    course_code = 'AAH 503 BSMA'
    print(f"\n--- Checking Course: {course_code} ---")
    try:
        course = DB.fetch_one("SELECT * FROM SMS_Course_Mst WHERE coursecode = ?", [course_code])
        if course:
            print(f"Course Data: {course}")
            
            # Check Department
            dept_id = course.get('fk_Deptid') or course.get('fk_deptid')
            if dept_id:
                dept = DB.fetch_one("SELECT pk_Deptid, Departmentname FROM SMS_Dept_Mst WHERE pk_Deptid = ?", [dept_id])
                print(f"Department in SMS_Dept_Mst: {dept}")
            
            # Check Session From
            sess_from_id = course.get('appfrom_sessionid')
            if sess_from_id:
                sess = DB.fetch_one("SELECT pk_sessionid, sessionname FROM SMS_AcademicSession_Mst WHERE pk_sessionid = ?", [sess_from_id])
                print(f"Session From in SMS_AcademicSession_Mst: {sess}")
        else:
            print("Course not found.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_course_data()
