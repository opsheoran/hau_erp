import re

with open('app/blueprints/student_portal/card_entry.py', 'r', encoding='utf-8') as f:
    code = f.read()

new_offered_query = """    # 2. Check which of these POW courses are actually offered by the HODs right now for this Session and Semester Type (Odd/Even)
    offered_map = set()
    offered_query = '''
        SELECT DISTINCT D.fk_courseid
        FROM SMS_CourseAllocationSemesterwiseByHOD M
        INNER JOIN SMS_CourseAllocationSemesterwiseByHOD_Dtl D ON M.Pk_courseallocid = D.fk_courseallocid
        INNER JOIN SMS_Course_Mst C ON D.fk_courseid = C.pk_courseid
        LEFT JOIN SMS_Course_Mst_Dtl CDTL ON C.pk_courseid = CDTL.fk_courseid AND CDTL.fk_degreeid = ?
        WHERE M.fk_dgacasessionid = ? AND M.fk_collegeid = ? AND M.degreeid = ?
          AND (CDTL.fk_semesterid % 2) = (? % 2)
    '''
    offered_data = DB.fetch_all(offered_query, [student['fk_degreeid'], curr_session, student['fk_collegeid'], student['fk_degreeid'], student['fk_semesterid']])
    for o in offered_data:
        offered_map.add(o['fk_courseid'])

    # 3. Fetch what the student has actually Ticked/Enrolled in for THIS SPECIFIC current semester (not just the whole year session)
    allocations = DB.fetch_all('''
        SELECT A.Pk_stucourseallocid, A.fk_courseid, A.isbacklog, A.isstudentApproved, A.fk_coursetypeid,
               A.crhrth1, A.crhrpr1
        FROM SMS_StuCourseAllocation A
        WHERE A.fk_sturegid = ? AND A.fk_dgacasessionid = ? AND A.fk_degreecycleid_alloc = (
            SELECT fk_degreecycleidcurrent FROM SMS_Student_Mst WHERE pk_sid = ?
        )
    ''', [student_id, curr_session, student_id])"""

code = re.sub(r"    # 2\. Check which of these POW courses.*?    ''', \[student_id, curr_session\]\)", new_offered_query, code, flags=re.DOTALL)

# Fix the CP allocation routing to NC courses
code = code.replace("elif is_nc or p['courseplan'] == 'NC':", "elif is_nc or p['courseplan'] in ('NC', 'CP'):")

with open('app/blueprints/student_portal/card_entry.py', 'w', encoding='utf-8') as f:
    f.write(code)

print('Updated logic')
