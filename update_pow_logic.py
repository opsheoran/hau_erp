import os
import re

with open('app/blueprints/student_portal/card_entry.py', 'r', encoding='utf-8') as f:
    code = f.read()

new_logic = """
    # 1. Base Query: Fetch all courses defined in the student's officially approved Programme of Work
    # This ensures ONLY courses the student has explicitly committed to in their POW show up.
    pow_courses_query = '''
        SELECT SCA.pk_stucourseapprove, C.pk_courseid, C.coursecode, C.coursename, 
               SCA.crhrth as master_th, SCA.crhrpr as master_pr,
               SCA.courseplan, ISNULL(C.isNC, 0) as isNC
        FROM Sms_course_Approval SCA
        INNER JOIN SMS_Course_Mst C ON SCA.fk_courseid = C.pk_courseid
        WHERE SCA.fk_sturegid = ?
    '''
    pow_courses = DB.fetch_all(pow_courses_query, [student_id])

    # 2. Check which of these POW courses are actually offered by the HODs right now for this Session and Semester Type (Odd/Even)
    offered_map = set()
    offered_query = '''
        SELECT DISTINCT D.fk_courseid
        FROM SMS_CourseAllocationSemesterwiseByHOD M
        INNER JOIN SMS_CourseAllocationSemesterwiseByHOD_Dtl D ON M.Pk_courseallocid = D.fk_courseallocid
        WHERE M.fk_dgacasessionid = ? AND (M.fk_semesterid % 2) = (? % 2) AND M.fk_collegeid = ?
    '''
    offered_data = DB.fetch_all(offered_query, [curr_session, student['fk_semesterid'], student['fk_collegeid']])
    for o in offered_data:
        offered_map.add(o['fk_courseid'])

    # 3. Fetch what the student has actually Ticked/Enrolled in for THIS SPECIFIC current session
    allocations = DB.fetch_all('''
        SELECT A.Pk_stucourseallocid, A.fk_courseid, A.isbacklog, A.isstudentApproved, A.fk_coursetypeid,
               A.crhrth1, A.crhrpr1
        FROM SMS_StuCourseAllocation A
        WHERE A.fk_sturegid = ? AND A.fk_dgacasessionid = ?
    ''', [student_id, curr_session])
    
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
        
        # Only show the course if it is being offered this semester OR the student already selected it this semester.
        if c_id not in offered_map and c_id not in alloc_map:
            continue
            
        processed_course_ids.add(c_id)
        alloc = alloc_map.get(c_id)
        
        # Override credits if custom research fractional credits exist for this semester
        crhr_th = p['master_th']
        crhr_pr = p['master_pr']
        if alloc and alloc.get('crhrth1') is not None:
            crhr_th = alloc['crhrth1']
        if alloc and alloc.get('crhrpr1') is not None:
            crhr_pr = alloc['crhrpr1']
            
        # Treat Thesis as a Major course, bypassing the NC flag
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
        elif p['courseplan'] == 'MA' or ('Thesis' in p['coursecode']):
            major_courses.append(c)
        elif p['courseplan'] == 'MI':
            minor_courses.append(c)
        elif p['courseplan'] == 'SU':
            support_courses.append(c)
        elif is_nc or p['courseplan'] == 'NC':
            nc_courses.append(c)
        elif p['courseplan'] == 'DF':
            deficiency_courses.append(c)
        else:
            major_courses.append(c)
            
    # Guarantee display of any manually allocated courses for THIS session that weren't caught in the POW net
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

old_logic_pattern = re.compile(r"    # 1\. Base Query: Fetch all courses.*?major_courses\.append\(c\)\n", re.DOTALL)

if old_logic_pattern.search(code):
    code = old_logic_pattern.sub(new_logic, code)
    with open('app/blueprints/student_portal/card_entry.py', 'w', encoding='utf-8') as f:
        f.write(code)
    print('Successfully applied rigorous POW checking for the current session only.')
else:
    print('Regex failed to match.')
