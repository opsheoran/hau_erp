from app.db import DB
student_id = 9791
curr_session = 77
fk_semesterid = 4
fk_degreeid = 33

offered_query = '''
    SELECT DISTINCT C.pk_courseid
    FROM SMS_Course_Mst C
    LEFT JOIN SMS_Course_Mst_Dtl CDTL ON C.pk_courseid = CDTL.fk_courseid AND CDTL.fk_degreeid = ?
    WHERE (CDTL.fk_semesterid % 2) = (? % 2)
'''
offered_data = DB.fetch_all(offered_query, [fk_degreeid, fk_semesterid])
offered_map = {o['pk_courseid'] for o in offered_data}

pow_query = '''
    SELECT C.pk_courseid, C.coursecode, SCA.courseplan, C.coursename
    FROM Sms_course_Approval SCA
    INNER JOIN SMS_Course_Mst C ON SCA.fk_courseid = C.pk_courseid
    WHERE SCA.fk_sturegid = ?
'''
pow_courses = DB.fetch_all(pow_query, [student_id])

alloc_query = '''
    SELECT A.fk_courseid
    FROM SMS_StuCourseAllocation A
    WHERE A.fk_sturegid = ? AND A.fk_dgacasessionid = ?
'''
allocations = DB.fetch_all(alloc_query, [student_id, curr_session])
alloc_map = {a['fk_courseid']: a for a in allocations}

print('=== FINAL LIST OUTPUT BY SCRIPT ===')
for p in pow_courses:
    c_id = p['pk_courseid']
    if c_id not in offered_map and c_id not in alloc_map:
        continue
    if p['courseplan'] == 'CP':
        continue
    print(f"{p['courseplan']}: {p['coursename']} ({p['coursecode']})")
