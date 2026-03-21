from app.db import DB

def debug_student(enrollment):
    print("--- Debugging Student: " + str(enrollment) + " ---")
    stu = DB.fetch_one("SELECT pk_sid, fullname, fk_collegeid, fk_degreeid, fk_curr_session FROM SMS_Student_Mst WHERE enrollmentno = ?", [enrollment])
    if not stu:
        print("Student not found in SMS_Student_Mst")
        return
    
    sid = stu['pk_sid']
    print("ID: " + str(sid) + ", Name: " + str(stu['fullname']) + ", College: " + str(stu['fk_collegeid']) + ", Degree: " + str(stu['fk_degreeid']) + ", Master Session: " + str(stu['fk_curr_session']))
    
    allocs = DB.fetch_all("""
        SELECT SCA.Pk_stucourseallocid, SCA.fk_courseid, C.coursecode, SCA.fk_dgacasessionid, SCA.fk_exconfigid, SCA.fk_degreecycleid, DC.fk_semesterid
        FROM SMS_StuCourseAllocation SCA
        INNER JOIN SMS_Course_Mst C ON SCA.fk_courseid = C.pk_courseid
        LEFT JOIN SMS_DegreeCycle_Mst DC ON SCA.fk_degreecycleid = DC.pk_degreecycleid
        WHERE SCA.fk_sturegid = ?
    """, [sid])
    
    print("\nAllocations found: " + str(len(allocs)))
    for a in allocs:
        print(" - Course: " + str(a['coursecode']) + ", Session: " + str(a['fk_dgacasessionid']) + ", ExConfig: " + str(a['fk_exconfigid']) + ", Sem: " + str(a['fk_semesterid']))
        
        # Check approvals
        apps = DB.fetch_all("""
            SELECT * FROM SMS_StuCourseAllocation_Approval_staffwise 
            WHERE fk_sturegid = ? AND fk_courseid = ? AND fk_exconfigid = ?
        """, [sid, a['fk_courseid'], a['fk_exconfigid']])
        
        if apps:
            for app in apps:
                print("   Approval Row Found ID: " + str(app.get('Pk_stucoursealloc_staffid')) + " DSW: " + str(app.get('dsw_approvalstatus')) + " Lib: " + str(app.get('lib_approvalstatus')) + " Fee: " + str(app.get('fee_approvalstatus')))
        else:
            print("   No approval row found in staffwise table.")

if __name__ == "__main__":
    debug_student('2025BS05M')
