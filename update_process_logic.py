import os
import re

with open('app/blueprints/student_portal/card_entry.py', 'r', encoding='utf-8') as f:
    code = f.read()

new_logic = """
    # --- DYNAMIC COLLEGE MAPPING BASED ON ADVISORY ---
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

    minor_college = get_dept_college(minor_dept, student['fk_degreeid']) or major_college
    support_college = get_dept_college(support_dept, student['fk_degreeid']) or major_college

    # 1. Base Query: Fetch all courses defined in the student's officially approved Programme of Work
    pow_courses_query = '''
        SELECT SCA.pk_stucourseapprove, C.pk_courseid, C.coursecode, C.coursename, 
               SCA.crhrth as master_th, SCA.crhrpr as master_pr,
               SCA.courseplan, ISNULL(C.isNC, 0) as isNC
        FROM Sms_course_Approval SCA
        INNER JOIN SMS_Course_Mst C ON SCA.fk_courseid = C.pk_courseid
        WHERE SCA.fk_sturegid = ? AND SCA.courseplan != 'CP'
    '''
    pow_courses = DB.fetch_all(pow_courses_query, [student_id])

    # 3. Fetch what the student has actually Ticked/Enrolled in for THIS SPECIFIC current session
    allocations = DB.fetch_all('''
        SELECT A.Pk_stucourseallocid, A.fk_courseid, A.isbacklog, A.isstudentApproved, A.fk_coursetypeid,
               A.crhrth1, A.crhrpr1
        FROM SMS_StuCourseAllocation A
        WHERE A.fk_sturegid = ? AND A.fk_dgacasessionid = ? AND A.fk_degreecycleid_alloc = (
            SELECT fk_degreecycleidcurrent FROM SMS_Student_Mst WHERE pk_sid = ?
        )
    ''', [student_id, curr_session, student_id])
    
    # Map allocations by course id
    alloc_map = {a['fk_courseid']: a for a in allocations}

    major_courses = []
    minor_courses = []
    support_courses = []
    nc_courses = []
    deficiency_courses = []
    back_courses = []

    processed_course_ids = set()

    for p in pow_courses:
        c_id = p['pk_courseid']
        cp = p['courseplan']
        
        target_college = major_college
        if cp == 'MI': target_college = minor_college
        elif cp == 'SU': target_college = support_college
        
        # Check if HOD offers it at this college in THIS SESSION AND Master Parity matches.
        is_offered = DB.fetch_one('''
            SELECT TOP 1 1 
            FROM SMS_CourseAllocationSemesterwiseByHOD M
            INNER JOIN SMS_CourseAllocationSemesterwiseByHOD_Dtl D ON M.Pk_courseallocid = D.fk_courseallocid
            LEFT JOIN SMS_Course_Mst_Dtl CDTL ON D.fk_courseid = CDTL.fk_courseid AND CDTL.fk_degreeid = ?
            WHERE M.fk_dgacasessionid = ? AND M.fk_collegeid = ? AND D.fk_courseid = ?
              AND (CDTL.fk_semesterid % 2) = (? % 2)
        ''', [student['fk_degreeid'], curr_session, target_college, c_id, student['fk_semesterid']])
        
        alloc = alloc_map.get(c_id)
        
        # Only show the course if it matches HOD+Parity OR the student explicitly selected it this semester.
        if not is_offered and not alloc and 'Thesis' not in p['coursecode']:
            continue
            
        processed_course_ids.add(c_id)
        
        # Override credits if custom research fractional credits exist for this semester
        crhr_th = p['master_th']
        crhr_pr = p['master_pr']
        if alloc and alloc.get('crhrth1') is not None:
            crhr_th = alloc['crhrth1']
        if alloc and alloc.get('crhrpr1') is not None:
            crhr_pr = alloc['crhrpr1']
            
        # Treat Thesis as a Major course, bypassing the NC flag.
        is_nc = p['isNC']
        if 'Thesis' in p['coursename'] or 'Thesis' in p['coursecode']:
            is_nc = False
            
        c = {
            'Pk_stucourseallocid': alloc['Pk_stucourseallocid'] if alloc else c_id,
            'coursecode': p['coursecode'],
            'coursename': p['coursename'],
            'crhr_theory': crhr_th,
            'crhr_practical': crhr_pr,
            'fk_coursetypeid': alloc['fk_coursetypeid'] if alloc and alloc['fk_coursetypeid'] else None,
            'isbacklog': alloc['isbacklog'] if alloc else False,
            'isstudentApproved': alloc['isstudentApproved'] if alloc else False,
            'isNC': is_nc,
            'cr_text': f"{crhr_th} + {crhr_pr}",
            'total_cr': (crhr_th or 0) + (crhr_pr or 0),
            'checked': 'checked' if alloc else ''
        }
        
        if c['isbacklog']:
            back_courses.append(c)
        elif cp == 'MA' or ('Thesis' in p['coursecode']):
            major_courses.append(c)
        elif cp == 'MI':
            minor_courses.append(c)
        elif cp == 'SU':
            support_courses.append(c)
        elif is_nc or cp in ('NC', 'CP'):
            nc_courses.append(c)
        elif cp == 'DF':
            deficiency_courses.append(c)
        else:
            major_courses.append(c)
            
    # Guarantee display of any manually allocated courses for THIS session that weren't in the POW net
    # (e.g., they manually picked up an extra non-credit course)
    for a in allocations:
        c_id = a['fk_courseid']
        if c_id not in processed_course_ids:
            back_course_data = DB.fetch_one("SELECT coursecode, coursename, crhr_theory, crhr_practical, ISNULL(isNC, 0) as isNC FROM SMS_Course_Mst WHERE pk_courseid = ?", [c_id])
            if back_course_data:
                
                crhr_th = a['crhrth1'] if a.get('crhrth1') is not None else back_course_data['crhr_theory']
                crhr_pr = a['crhrpr1'] if a.get('crhrpr1') is not None else back_course_data['crhr_practical']
                
                is_nc = back_course_data['isNC']
                if 'Thesis' in back_course_data['coursename'] or 'Thesis' in back_course_data['coursecode']:
                    is_nc = False
                
                c = {
                    'Pk_stucourseallocid': a['Pk_stucourseallocid'],
                    'coursecode': back_course_data['coursecode'],
                    'coursename': back_course_data['coursename'],
                    'crhr_theory': crhr_th,
                    'crhr_practical': crhr_pr,
                    'fk_coursetypeid': a['fk_coursetypeid'],
                    'isbacklog': a['isbacklog'],
                    'isstudentApproved': a['isstudentApproved'],
                    'isNC': is_nc,
                    'cr_text': f"{crhr_th} + {crhr_pr}",
                    'total_cr': (crhr_th or 0) + (crhr_pr or 0),
                    'checked': 'checked'
                }
                
                if c['isbacklog']:
                    back_courses.append(c)
                elif c['fk_coursetypeid'] == 1 or ('Thesis' in c['coursecode']):
                    major_courses.append(c)
                elif c['fk_coursetypeid'] == 2:
                    minor_courses.append(c)
                elif c['fk_coursetypeid'] == 7:
                    support_courses.append(c)
                elif c['fk_coursetypeid'] == 36:
                    deficiency_courses.append(c)
                elif c['fk_coursetypeid'] == 9 or is_nc:
                    nc_courses.append(c)
                else:
                    major_courses.append(c)
"""

# Extract the part we want to replace
start_idx = code.find("    # 1. Base Query:")
end_idx = code.find("    return render_template('student_portal/card_entry.html'")

if start_idx != -1 and end_idx != -1:
    new_file = code[:start_idx] + new_logic + "\n" + code[end_idx:]
    with open('app/blueprints/student_portal/card_entry.py', 'w', encoding='utf-8') as f:
        f.write(new_file)
    print("Successfully replaced logic!")
else:
    print("Failed to find bounds.")
