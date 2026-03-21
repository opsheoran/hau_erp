import os
import re

with open('app/blueprints/student_portal/card_entry.py', 'r', encoding='utf-8') as f:
    code = f.read()

new_logic = """
    # Fetch offered courses for this semester (from HOD mapping)
    offered_courses = DB.fetch_all('''
        SELECT DISTINCT D.fk_courseid as pk_courseid, C.coursecode, C.coursename, C.crhr_theory, C.crhr_practical, 
               CP.Pk_coursetypeid as fk_coursetypeid, ISNULL(C.isNC, 0) as isNC
        FROM SMS_CourseAllocationSemesterwiseByHOD M
        INNER JOIN SMS_CourseAllocationSemesterwiseByHOD_Dtl D ON M.Pk_courseallocid = D.fk_courseallocid
        INNER JOIN SMS_Course_Mst C ON D.fk_courseid = C.pk_courseid
        LEFT JOIN COursePlan CP ON C.pk_courseid = CP.pk_courseid AND CP.courseplanidd = ?
        WHERE M.fk_dgacasessionid = ? AND M.fk_semesterid = ? AND M.fk_collegeid = ?
    ''', [student_id, curr_session, student['fk_semesterid'], student['fk_collegeid']])

    # Fetch what the student is ACTUALLY enrolled in for this session
    allocations = DB.fetch_all('''
        SELECT A.Pk_stucourseallocid, A.fk_courseid, A.isbacklog, A.isstudentApproved, A.fk_coursetypeid
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

    # Map the courses
    for o in offered_courses:
        c_id = o['pk_courseid']
        processed_course_ids.add(c_id)
        alloc = alloc_map.get(c_id)
        
        c = {
            'Pk_stucourseallocid': alloc['Pk_stucourseallocid'] if alloc else c_id,
            'coursecode': o['coursecode'],
            'coursename': o['coursename'],
            'crhr_theory': o['crhr_theory'],
            'crhr_practical': o['crhr_practical'],
            'fk_coursetypeid': alloc['fk_coursetypeid'] if alloc and alloc['fk_coursetypeid'] else o['fk_coursetypeid'],
            'isbacklog': alloc['isbacklog'] if alloc else False,
            'isstudentApproved': alloc['isstudentApproved'] if alloc else False,
            'isNC': o['isNC'],
            'cr_text': f"{o['crhr_theory']} + {o['crhr_practical']}",
            'total_cr': (o['crhr_theory'] or 0) + (o['crhr_practical'] or 0),
            'checked': 'checked' if alloc else ''
        }
        
        if c['isbacklog']:
            back_courses.append(c)
        elif c['fk_coursetypeid'] == 1:
            major_courses.append(c)
        elif c['fk_coursetypeid'] == 2:
            minor_courses.append(c)
        elif c['fk_coursetypeid'] == 7:
            support_courses.append(c)
        elif c['fk_coursetypeid'] == 36:
            deficiency_courses.append(c)
        elif c['fk_coursetypeid'] == 9 or c['isNC']:
            nc_courses.append(c)
        else:
            major_courses.append(c)
            
    # Also grab any backlog or manually added courses not actively offered by HOD but the student is enrolled in
    for a in allocations:
        c_id = a['fk_courseid']
        if c_id not in processed_course_ids:
            back_course_data = DB.fetch_one("SELECT coursecode, coursename, crhr_theory, crhr_practical, ISNULL(isNC, 0) as isNC FROM SMS_Course_Mst WHERE pk_courseid = ?", [c_id])
            if back_course_data:
                c = {
                    'Pk_stucourseallocid': a['Pk_stucourseallocid'],
                    'coursecode': back_course_data['coursecode'],
                    'coursename': back_course_data['coursename'],
                    'crhr_theory': back_course_data['crhr_theory'],
                    'crhr_practical': back_course_data['crhr_practical'],
                    'fk_coursetypeid': a['fk_coursetypeid'],
                    'isbacklog': a['isbacklog'],
                    'isstudentApproved': a['isstudentApproved'],
                    'isNC': back_course_data['isNC'],
                    'cr_text': f"{back_course_data['crhr_theory']} + {back_course_data['crhr_practical']}",
                    'total_cr': (back_course_data['crhr_theory'] or 0) + (back_course_data['crhr_practical'] or 0),
                    'checked': 'checked'
                }
                
                if c['isbacklog']:
                    back_courses.append(c)
                elif c['fk_coursetypeid'] == 1:
                    major_courses.append(c)
                elif c['fk_coursetypeid'] == 2:
                    minor_courses.append(c)
                elif c['fk_coursetypeid'] == 7:
                    support_courses.append(c)
                elif c['fk_coursetypeid'] == 36:
                    deficiency_courses.append(c)
                elif c['fk_coursetypeid'] == 9 or c['isNC']:
                    nc_courses.append(c)
                else:
                    major_courses.append(c)
"""

old_logic_pattern = re.compile(r"    # Fetch allocated courses.*?major_courses\.append\(c\)\n", re.DOTALL)
if old_logic_pattern.search(code):
    code = old_logic_pattern.sub(new_logic + "\n", code)
    with open('app/blueprints/student_portal/card_entry.py', 'w', encoding='utf-8') as f:
        f.write(code)
    print('Updated Card Entry logic successfully.')
else:
    print('Failed to locate regex block')