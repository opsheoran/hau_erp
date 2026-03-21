from app.db import DB
student_id = 9791

student = DB.fetch_one('SELECT S.fk_collegeid, S.fk_branchid, S.fk_degreeid, S.fk_curr_session, DC.fk_semesterid FROM SMS_Student_Mst S LEFT JOIN SMS_DegreeCycle_Mst DC ON S.fk_degreecycleidcurrent = DC.pk_degreecycleid WHERE S.pk_sid = ?', [student_id])

advisory = DB.fetch_all('''
    SELECT D.fk_statusid, D.fk_deptid
    FROM SMS_Advisory_Committee_Mst M
    INNER JOIN SMS_Advisory_Committee_Dtl D ON M.pk_adcid = D.fk_adcid
    WHERE M.fk_stid = ?
''', [student_id])

minor_dept = None
support_dept = None
for a in advisory:
    if a['fk_statusid'] == 3: minor_dept = a['fk_deptid']
    if a['fk_statusid'] == 4: support_dept = a['fk_deptid']

def get_dept_college(dept_id, degree_id):
    if not dept_id: return None
    branch = DB.fetch_one('SELECT Pk_BranchId FROM SMS_BranchMst WHERE fk_deptidDdo = ?', [dept_id])
    if branch:
        col = DB.fetch_one('''
            SELECT TOP 1 M.fk_CollegeId 
            FROM SMS_CollegeDegreeBranchMap_dtl D
            INNER JOIN SMS_CollegeDegreeBranchMap_Mst M ON D.fk_Coldgbrmapid = M.PK_Coldgbrid
            WHERE D.fk_branchid = ? AND M.fk_Degreeid = ?
        ''', [branch['Pk_BranchId'], degree_id])
        if col: return col['fk_CollegeId']
    return None

major_college = student['fk_collegeid']
minor_college = get_dept_college(minor_dept, student['fk_degreeid'])
support_college = get_dept_college(support_dept, student['fk_degreeid'])

print(f'Colleges - Major: {major_college}, Minor: {minor_college}, Support: {support_college}')

curr_session = student['fk_curr_session']
fk_semesterid = student['fk_semesterid']

pow_courses = DB.fetch_all('''
    SELECT C.pk_courseid, C.coursecode, SCA.courseplan, C.coursename
    FROM Sms_course_Approval SCA
    INNER JOIN SMS_Course_Mst C ON SCA.fk_courseid = C.pk_courseid
    WHERE SCA.fk_sturegid = ?
''', [student_id])

print('\nCourses matching EXACT HOD logic per user:')
for p in pow_courses:
    cp = p['courseplan']
    c_id = p['pk_courseid']
    
    target_college = None
    if cp == 'MA': target_college = major_college
    elif cp == 'MI': target_college = minor_college
    elif cp == 'SU': target_college = support_college
    else: target_college = major_college
    
    if not target_college:
        continue
        
    offered = DB.fetch_one('''
        SELECT TOP 1 1 
        FROM SMS_CourseAllocationSemesterwiseByHOD M
        INNER JOIN SMS_CourseAllocationSemesterwiseByHOD_Dtl D ON M.Pk_courseallocid = D.fk_courseallocid
        WHERE M.fk_dgacasessionid = ? AND M.fk_semesterid = ? AND M.fk_collegeid = ? AND D.fk_courseid = ?
    ''', [curr_session, fk_semesterid, target_college, c_id])
    
    if offered:
        print(f"{cp}: {p['coursecode']} (College {target_college})")
