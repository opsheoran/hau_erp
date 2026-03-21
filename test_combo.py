from app.db import DB
student_id = 9791
curr_session = 77
fk_semesterid = 4 # Even

# 1. Get student and colleges
student = DB.fetch_one('SELECT fk_collegeid, fk_branchid, fk_degreeid FROM SMS_Student_Mst WHERE pk_sid = ?', [student_id])
major_college = student['fk_collegeid']

advisory = DB.fetch_all('''
    SELECT D.fk_statusid, D.fk_deptid
    FROM SMS_Advisory_Committee_Mst M
    INNER JOIN SMS_Advisory_Committee_Dtl D ON M.pk_adcid = D.fk_adcid
    WHERE M.fk_stid = ?
''', [student_id])

minor_dept = next((a['fk_deptid'] for a in advisory if a['fk_statusid'] == 3), None)
support_dept = next((a['fk_deptid'] for a in advisory if a['fk_statusid'] == 4), None)

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

minor_college = get_dept_college(minor_dept, student['fk_degreeid'])
support_college = get_dept_college(support_dept, student['fk_degreeid'])

print(f'Major Col: {major_college}, Minor Col: {minor_college}, Support Col: {support_college}')

pow_courses = DB.fetch_all('''
    SELECT C.pk_courseid, C.coursecode, SCA.courseplan, C.coursename
    FROM Sms_course_Approval SCA
    INNER JOIN SMS_Course_Mst C ON SCA.fk_courseid = C.pk_courseid
    WHERE SCA.fk_sturegid = ? AND SCA.courseplan != 'CP'
''', [student_id])

for p in pow_courses:
    cp = p['courseplan']
    c_id = p['pk_courseid']
    target_college = None
    
    if cp == 'MA': target_college = major_college
    elif cp == 'MI': target_college = minor_college
    elif cp == 'SU': target_college = support_college
    else: target_college = major_college
    
    # Check if HOD offers it at this college in THIS SESSION (ignoring semester id on HOD table to allow VSC 502)
    # AND Master Parity matches.
    is_offered = DB.fetch_one('''
        SELECT TOP 1 1 
        FROM SMS_CourseAllocationSemesterwiseByHOD M
        INNER JOIN SMS_CourseAllocationSemesterwiseByHOD_Dtl D ON M.Pk_courseallocid = D.fk_courseallocid
        LEFT JOIN SMS_Course_Mst_Dtl CDTL ON D.fk_courseid = CDTL.fk_courseid AND CDTL.fk_degreeid = ?
        WHERE M.fk_dgacasessionid = ? AND M.fk_collegeid = ? AND D.fk_courseid = ?
          AND (CDTL.fk_semesterid % 2) = (? % 2)
    ''', [student['fk_degreeid'], curr_session, target_college, c_id, fk_semesterid])
    
    if is_offered or 'Thesis' in p['coursecode']:
        print(f"{cp}: {p['coursecode']}")