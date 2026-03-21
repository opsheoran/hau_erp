from app.db import DB

def check_hod_courses():
    sms_dept_ids = [20, 21]
    dept_placeholders = ','.join(['?'] * len(sms_dept_ids))
    params = [77]
    params.extend(sms_dept_ids)
    
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
        WHERE A.fk_dgacasessionid = ?
        AND C.fk_Deptid IN ({dept_placeholders})
        AND D.islocked = 1
        AND ISNULL(A.IsSummer, 0) = 0 AND ISNULL(A.IsSupplementary, 0) = 0 AND ISNULL(A.Is_Igrade, 0) = 0
        AND E.isinternal = 1
        GROUP BY C.pk_courseid, C.coursecode, C.coursename, C.crhr_theory, C.crhr_practical
        ORDER BY C.coursecode
    '''
    
    courses = DB.fetch_all(query, params)
    print(f"Courses found for HOD of Mathematics and Statistics: {len(courses)}")
    for c in courses:
        print(c)

check_hod_courses()
