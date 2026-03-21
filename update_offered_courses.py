import re

with open('app/blueprints/student_portal/card_entry.py', 'r', encoding='utf-8') as f:
    code = f.read()

new_query = """    offered_courses = DB.fetch_all('''
        SELECT DISTINCT D.fk_courseid as pk_courseid, C.coursecode, C.coursename, C.crhr_theory, C.crhr_practical, 
               CP.Pk_coursetypeid as fk_coursetypeid, ISNULL(C.isNC, 0) as isNC,
               CDTL.fk_branchid
        FROM SMS_CourseAllocationSemesterwiseByHOD M
        INNER JOIN SMS_CourseAllocationSemesterwiseByHOD_Dtl D ON M.Pk_courseallocid = D.fk_courseallocid
        INNER JOIN SMS_Course_Mst C ON D.fk_courseid = C.pk_courseid
        LEFT JOIN SMS_Course_Mst_Dtl CDTL ON C.pk_courseid = CDTL.fk_courseid
        LEFT JOIN COursePlan CP ON C.pk_courseid = CP.pk_courseid
        WHERE M.fk_dgacasessionid = ? AND M.fk_collegeid = ? AND (M.fk_semesterid % 2) = (? % 2)
    ''', [curr_session, student['fk_collegeid'], student['fk_semesterid']])"""

pattern = re.compile(r"    offered_courses = DB\.fetch_all\('''\n        SELECT DISTINCT D.*?WHERE M\.fk_dgacasessionid = \? AND M\.fk_semesterid = \? AND M\.fk_collegeid = \?\n    ''', \[curr_session, student\['fk_semesterid'\], student\['fk_collegeid'\]\]\)", re.DOTALL)

if pattern.search(code):
    code = pattern.sub(new_query, code)
    with open('app/blueprints/student_portal/card_entry.py', 'w', encoding='utf-8') as f:
        f.write(code)
    print('Updated offered_courses query to odd/even matching.')
else:
    print('Failed to find offered_courses query.')
