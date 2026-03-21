from app.db import DB

student_id = 9791
curr_session = 77
fk_semesterid = 4 # Hardcoded for now based on student info

pow_courses = DB.fetch_all('''
    SELECT SCA.pk_stucourseapprove, C.pk_courseid, C.coursecode, SCA.courseplan, C.coursename
    FROM Sms_course_Approval SCA
    INNER JOIN SMS_Course_Mst C ON SCA.fk_courseid = C.pk_courseid
    WHERE SCA.fk_sturegid = ?
''', [student_id])

print('Testing Course -> Branch -> College logic:')

valid_courses = []

for p in pow_courses:
    c_id = p['pk_courseid']
    coursecode = p['coursecode']
    
    # Get all branches this course belongs to
    branches = DB.fetch_all('SELECT fk_branchid FROM SMS_Course_Mst_Dtl WHERE fk_courseid = ?', [c_id])
    
    offered = False
    for b in branches:
        branch_id = b['fk_branchid']
        
        # Get college for this branch
        col_map = DB.fetch_one('''
            SELECT TOP 1 M.fk_CollegeId 
            FROM SMS_CollegeDegreeBranchMap_dtl D
            INNER JOIN SMS_CollegeDegreeBranchMap_Mst M ON D.fk_Coldgbrmapid = M.PK_Coldgbrid
            WHERE D.fk_branchid = ?
        ''', [branch_id])
        
        if not col_map: continue
        college_id = col_map['fk_CollegeId']
        
        # Check if HOD offers it at this college in this semester
        is_offered = DB.fetch_one('''
            SELECT TOP 1 1 
            FROM SMS_CourseAllocationSemesterwiseByHOD M
            INNER JOIN SMS_CourseAllocationSemesterwiseByHOD_Dtl D ON M.Pk_courseallocid = D.fk_courseallocid
            WHERE M.fk_dgacasessionid = ? AND M.fk_semesterid = ? AND M.fk_collegeid = ? AND D.fk_courseid = ?
        ''', [curr_session, fk_semesterid, college_id, c_id])
        
        if is_offered:
            offered = True
            break
            
    if offered:
        valid_courses.append(f"{p['courseplan']}: {coursecode}")

print('\nValid Courses:')
for v in sorted(valid_courses):
    print(v)
