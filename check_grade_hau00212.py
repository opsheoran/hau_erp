from app.db import DB

def check_hau00212():
    user = DB.fetch_one("SELECT * FROM UM_Users_Mst WHERE loginname = 'HAU00212'")
    print("USER:", user)
    if user:
        emp = DB.fetch_one("SELECT pk_empid, empcode, empname FROM SAL_Employee_Mst WHERE pk_empid = ?", [user['fk_empId']])
        print("EMP:", emp)
        
        # Check what departments they are HOD of
        hod_depts = DB.fetch_all("SELECT description FROM Department_Mst WHERE Hod_Id = ?", [user['fk_empId']])
        print("HOD OF DEPTS:", hod_depts)

        # Let's see what the HOD approval returns for them for session 77
        query = f'''
            SELECT C.pk_courseid as id, C.coursecode + ' || ' + C.coursename as name,
                   C.crhr_theory, C.crhr_practical,
                   COUNT(DISTINCT A.fk_sturegid) as student_count,
                   MIN(CAST(ISNULL(D.islockedbyHOD, 0) AS INT)) as is_approved
            FROM SMS_StuCourseAllocation A
            INNER JOIN SMS_Course_Mst C ON A.fk_courseid = C.pk_courseid
            INNER JOIN SMS_DegreeCycle_Mst DC ON A.fk_degreecycleid = DC.pk_degreecycleid
            INNER JOIN SMS_Student_Mst S ON A.fk_sturegid = S.pk_sid
            INNER JOIN SMS_StuExamMarks_Dtl D ON A.Pk_stucourseallocid = D.fk_stucourseallocid
            INNER JOIN SMS_DgExam_Mst M ON D.fk_dgexammapid = M.pk_dgexammapid
            INNER JOIN SMS_Exam_Mst E ON M.fk_examid = E.pk_examid
            WHERE A.fk_dgacasessionid = 77
            AND D.islocked = 1
            AND ISNULL(A.IsSummer, 0) = 0 AND ISNULL(A.IsSupplementary, 0) = 0 AND ISNULL(A.Is_Igrade, 0) = 0
            AND E.isinternal = 1
            AND C.fk_Deptid IN (
                SELECT pk_deptid FROM SMS_Dept_Mst WHERE fk_deptidDdo IN (
                    SELECT pk_deptid FROM Department_Mst WHERE Hod_Id = ?
                )
            )
            GROUP BY C.pk_courseid, C.coursecode, C.coursename, C.crhr_theory, C.crhr_practical
            ORDER BY C.coursecode
        '''
        courses = DB.fetch_all(query, [user['fk_empId']])
        print(f"COURSES PENDING/APPROVED (session 77): {len(courses)}")
        for c in courses:
            print(c)

check_hau00212()
