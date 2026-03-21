from app.db import DB
student_id = 9791
curr_session = 77

offered_map = {o['fk_courseid'] for o in DB.fetch_all('SELECT DISTINCT D.fk_courseid FROM SMS_CourseAllocationSemesterwiseByHOD M INNER JOIN SMS_CourseAllocationSemesterwiseByHOD_Dtl D ON M.Pk_courseallocid = D.fk_courseallocid WHERE M.fk_dgacasessionid = 77 AND M.fk_semesterid = 4')}
pow_courses = DB.fetch_all('SELECT C.pk_courseid, C.coursecode, SCA.courseplan FROM Sms_course_Approval SCA INNER JOIN SMS_Course_Mst C ON SCA.fk_courseid = C.pk_courseid WHERE SCA.fk_sturegid = 9791')
allocs = DB.fetch_all('SELECT fk_courseid FROM SMS_StuCourseAllocation WHERE fk_sturegid = 9791 AND fk_dgacasessionid = 77')
alloc_map = {a['fk_courseid']: a for a in allocs}

final_list = []
for p in pow_courses:
    c_id = p['pk_courseid']
    if c_id not in offered_map and c_id not in alloc_map:
        continue
    if c_id not in alloc_map:
        if DB.fetch_one('SELECT TOP 1 ispassed FROM SMS_StuCourseAllocation WHERE fk_sturegid = 9791 AND fk_courseid = ? AND ispassed = 1', [c_id]):
            continue
    final_list.append(f"{p['courseplan']}: {p['coursecode']}")

for a in allocs:
    if a['fk_courseid'] not in {p['pk_courseid'] for p in pow_courses}:
        course = DB.fetch_one('SELECT coursecode FROM SMS_Course_Mst WHERE pk_courseid = ?', [a['fk_courseid']])
        final_list.append(f"MANUAL: {course['coursecode']}")

for f in sorted(final_list):
    print(f)