from app.db import DB

student_id = 9791
student = DB.fetch_one('SELECT fk_collegeid, fk_branchid, fk_degreeid, fk_curr_session FROM SMS_Student_Mst WHERE pk_sid = ?', [student_id])
print('Student:', student)

# Get Minor and Supporting departments from Advisory
advisory = DB.fetch_all('''
    SELECT D.fk_statusid, D.fk_deptid
    FROM SMS_Advisory_Committee_Mst M
    INNER JOIN SMS_Advisory_Committee_Dtl D ON M.pk_adcid = D.fk_adcid
    WHERE M.fk_stid = ?
''', [student_id])

major_branch = student['fk_branchid']
major_college = student['fk_collegeid']

minor_dept = None
support_dept = None

for a in advisory:
    if a['fk_statusid'] == 3: minor_dept = a['fk_deptid']
    if a['fk_statusid'] == 4: support_dept = a['fk_deptid']

print('Minor Dept:', minor_dept, 'Support Dept:', support_dept)

def get_dept_college(dept_id):
    if not dept_id: return None
    branch = DB.fetch_one('SELECT Pk_BranchId FROM SMS_BranchMst WHERE fk_deptidDdo = ?', [dept_id])
    if branch:
        col_map = DB.fetch_one('SELECT TOP 1 fk_CollegeId FROM SMS_CollegeDegreeBranchMap_Mst WHERE fk_Degreeid = ?', [student['fk_degreeid']])
        # Actually wait, if we want to map branch to college, we can just use SMS_CollegeDegreeBranchMap_Mst with fk_Branchid? No, the column doesn't exist.
        # Let's just find the college by checking SMS_Student_Mst for students in that branch? Or SMS_Advisory_Committee_Mst.
        # How about we just look at the HOD mappings directly to find the collegeid?
    return None

minor_college = get_dept_college(minor_dept)
support_college = get_dept_college(support_dept)

print(f'Major College: {major_college}, Minor College: {minor_college}, Support College: {support_college}')

curr_session = student['fk_curr_session']
fk_semesterid = 4 # Hardcoded for now based on student

pow_courses = DB.fetch_all('''
    SELECT C.pk_courseid, C.coursecode, SCA.courseplan, C.coursename
    FROM Sms_course_Approval SCA
    INNER JOIN SMS_Course_Mst C ON SCA.fk_courseid = C.pk_courseid
    WHERE SCA.fk_sturegid = ?
''', [student_id])

print('\nPOW Check:')
for p in pow_courses:
    cp = p['courseplan']
    c_id = p['pk_courseid']
    target_college = None
    
    if cp == 'MA': target_college = major_college
    elif cp == 'MI': target_college = minor_college
    elif cp == 'SU': target_college = support_college
    else: target_college = major_college # Default fallback
    
    if not target_college:
        continue
        
    # Check if this course is offered by HOD in the target college in this semester
    offered = DB.fetch_one('''
        SELECT TOP 1 1 
        FROM SMS_CourseAllocationSemesterwiseByHOD M
        INNER JOIN SMS_CourseAllocationSemesterwiseByHOD_Dtl D ON M.Pk_courseallocid = D.fk_courseallocid
        WHERE M.fk_dgacasessionid = ? AND M.fk_semesterid = ? AND M.fk_collegeid = ? AND D.fk_courseid = ?
    ''', [curr_session, fk_semesterid, target_college, c_id])
    
    if offered:
        print(f"{cp}: {p['coursecode']} (College {target_college})")
