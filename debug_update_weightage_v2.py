import sys, os
sys.path.insert(0, os.getcwd())
from app.db import DB

print('Searching for Course STAT 502:')
rows = DB.fetch_all("SELECT pk_courseid, coursecode, coursename FROM SMS_Course_Mst WHERE coursecode LIKE 'STAT 502%'")
print(rows)

if rows:
    course_id = rows[0]['pk_courseid']
    dgmapid = 3070 # from previous debug
    print(f'\nChecking students marks for dgmapid {dgmapid} and course {course_id}:')
    query = """
        SELECT COUNT(*) as cnt
        FROM SMS_StuExamMarks_Dtl D
        INNER JOIN SMS_StuCourseAllocation A ON D.fk_stucourseallocid = A.pk_stucourseallocid
        WHERE D.fk_dgexammapid = ? AND A.fk_courseid = ?
    """
    cnt = DB.fetch_scalar(query, [dgmapid, course_id])
    print('Count:', cnt)
