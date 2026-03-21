import os

with open('app/blueprints/student_portal/card_entry.py', 'r', encoding='utf-8') as f:
    code = f.read()

old_query = """    # Fetch allocated courses
    courses = DB.fetch_all('''
        SELECT A.Pk_stucourseallocid, C.coursecode, C.coursename, C.crhr_theory, C.crhr_practical,
               A.fk_coursetypeid, A.isbacklog, A.isstudentApproved, ISNULL(C.isNC, 0) as isNC
        FROM SMS_StuCourseAllocation A
        INNER JOIN SMS_Course_Mst C ON A.fk_courseid = C.pk_courseid
        WHERE A.fk_sturegid = ? AND A.fk_dgacasessionid = ?
    ''', [student_id, curr_session])"""

new_query = """    # Fetch allocated courses
    courses = DB.fetch_all('''
        SELECT A.Pk_stucourseallocid, C.coursecode, C.coursename, C.crhr_theory, C.crhr_practical,
               A.fk_coursetypeid, A.isbacklog, A.isstudentApproved, ISNULL(C.isNC, 0) as isNC
        FROM SMS_StuCourseAllocation A
        INNER JOIN SMS_Course_Mst C ON A.fk_courseid = C.pk_courseid
        WHERE A.fk_sturegid = ? AND A.ispassed = 0 AND ISNULL(A.isstudentApproved, 0) = 0
    ''', [student_id])"""

if old_query.strip() in code:
    code = code.replace(old_query.strip(), new_query.strip())
    with open('app/blueprints/student_portal/card_entry.py', 'w', encoding='utf-8') as f:
        f.write(code)
    print('Updated query successfully')
else:
    print('Failed to find query to replace')