from app.db import DB

def test_query():
    query = """
    SELECT DISTINCT C.pk_courseid, C.coursecode, C.coursename, C.crhr_theory, C.crhr_practical,
           COUNT(DISTINCT A.fk_sturegid) as student_count,
           CASE WHEN MAX(CAST(ISNULL(D.islockedbyHOD, 0) AS INT)) = 1 THEN 1 ELSE 0 END as is_approved
    FROM SMS_StuCourseAllocation A
    INNER JOIN SMS_Course_Mst C ON A.fk_courseid = C.pk_courseid
    INNER JOIN SMS_StuExamMarks_Dtl D ON A.Pk_stucourseallocid = D.fk_stucourseallocid
    INNER JOIN SMS_DegreeCycle_Mst DC ON A.fk_degreecycleid = DC.pk_degreecycleid
    WHERE A.fk_dgacasessionid = 77 AND DC.fk_degreeid = 21 AND DC.fk_semesterid = 2 
    AND D.islocked = 1
    GROUP BY C.pk_courseid, C.coursecode, C.coursename, C.crhr_theory, C.crhr_practical
    """
    print(DB.fetch_all(query))

test_query()
