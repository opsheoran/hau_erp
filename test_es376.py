from app.db import DB

query = """
    SELECT DISTINCT c.coursecode, d.degreename, class.semester_roman
    FROM SMS_TCourseAlloc_Dtl ad
    JOIN SMS_TCourseAlloc_Mst a ON a.pk_tcourseallocid = ad.fk_tcourseallocid
    JOIN SMS_Course_Mst c ON c.pk_courseid = ad.fk_courseid
    JOIN SMS_Degree_Mst d ON d.pk_degreeid = a.fk_degreeid
    JOIN SMS_Semester_Mst class ON class.pk_semesterid = a.fk_semesterid
    WHERE a.fk_employeeid = 'ES-376'
"""
res = DB.fetch_all(query)
print("Total rows:", len(res))
for i, r in enumerate(res):
    print(i+1, r['coursecode'], r['degreename'], r['semester_roman'])
