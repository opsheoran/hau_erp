from app.db import DB
from flask import jsonify

with open('app/blueprints/examination/marks_process_ug_mba.py', 'r', encoding='utf-8') as main_f:
    code = main_f.read()

new_api = """
@examination_bp.route('/api/get_student_courses_ug_mba')
def get_student_courses_ug_mba():
    student_id = request.args.get('student_id')
    session_id = request.args.get('session_id')
    semester_id = request.args.get('semester_id')
    degreeyear_id = request.args.get('year_id')
    degree_id = request.args.get('degree_id')
    
    if not all([student_id, session_id, semester_id, degreeyear_id]):
        return jsonify([])

    query = '''
        SELECT A.Pk_stucourseallocid, C.coursecode, C.coursename, C.crhr_theory, C.crhr_practical
        FROM SMS_StuCourseAllocation A
        INNER JOIN SMS_Course_Mst C ON A.fk_courseid = C.pk_courseid
        WHERE A.fk_sturegid = ? AND A.fk_dgacasessionid = ?
    '''
    courses = DB.fetch_all(query, [student_id, session_id])
    
    alloc_ids = [str(c['Pk_stucourseallocid']) for c in courses]
    
    marks_dict = {}
    if alloc_ids:
        placeholders = ','.join(['?'] * len(alloc_ids))
        marks = DB.fetch_all(f'''
            SELECT D.fk_stucourseallocid, D.marks_obt, D.isabsentt, E.exam, M.maxmarks_th, M.maxmarks_pr, E.istheory
            FROM SMS_StuExamMarks_Dtl D
            INNER JOIN SMS_DgExam_Mst DEM ON D.fk_dgexammapid = DEM.pk_dgexammapid
            INNER JOIN SMS_Exam_Mst E ON DEM.fk_examid = E.pk_examid
            INNER JOIN SMS_DgExamWei_WithCourse M ON DEM.pk_dgexammapid = M.fk_dgexammapid AND M.fk_courseid = (SELECT fk_courseid FROM SMS_StuCourseAllocation WHERE Pk_stucourseallocid = D.fk_stucourseallocid)
            WHERE D.fk_stucourseallocid IN ({placeholders})
        ''', alloc_ids)
        
        for m in marks:
            alloc_id = m['fk_stucourseallocid']
            if alloc_id not in marks_dict:
                marks_dict[alloc_id] = {}
            exam_name = m['exam'].strip().lower()
            marks_dict[alloc_id][exam_name] = {
                'val': m['marks_obt'],
                'absent': m['isabsentt'] == 1,
                'max_th': m['maxmarks_th'],
                'max_pr': m['maxmarks_pr']
            }

    result = []
    for c in courses:
        alloc_id = c['Pk_stucourseallocid']
        m_data = marks_dict.get(alloc_id, {})
        
        in_th = m_data.get('internal theory') or m_data.get('internal  theory') or m_data.get('internal')
        in_pr = m_data.get('internal practical') or m_data.get('internal  practical')
        ex_th = m_data.get('external theory') or m_data.get('external  theory') or m_data.get('external')
        ex_pr = m_data.get('external practical') or m_data.get('external  practical')
        
        in_th_val = f"{in_th['val']}/{in_th['max_th']}" if in_th and in_th['val'] is not None else ''
        in_pr_val = f"{in_pr['val']}/{in_pr['max_pr']}" if in_pr and in_pr['val'] is not None else ''
        ex_th_val = f"{ex_th['val']}/{ex_th['max_th']}" if ex_th and ex_th['val'] is not None else ''
        ex_pr_val = f"{ex_pr['val']}/{ex_pr['max_pr']}" if ex_pr and ex_pr['val'] is not None else ''
        
        result.append({
            'coursecode': c['coursecode'],
            'coursename': c['coursename'],
            'in_th': in_th_val,
            'in_pr': in_pr_val,
            'ex_th': ex_th_val,
            'ex_pr': ex_pr_val,
            'gp': '', 
            'cp': '',
            'gpa': '',
            'ogpa': '',
            'passed': 'Pending'
        })
    return jsonify(result)
"""
if 'get_student_courses_ug_mba' not in code:
    code += '\n' + new_api
    with open('app/blueprints/examination/marks_process_ug_mba.py', 'w', encoding='utf-8') as out_f:
        out_f.write(code)
    print('Updated API.')