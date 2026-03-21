import os
import re

with open('app/blueprints/examination/marks_process_ug_mba.py', 'r', encoding='utf-8') as main_f:
    code = main_f.read()

new_api = """@examination_bp.route('/api/get_student_courses_ug_mba')
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
    cld_dict = {}
    if alloc_ids:
        placeholders = ','.join(['?'] * len(alloc_ids))
        marks = DB.fetch_all(f'''
            SELECT D.fk_stucourseallocid, D.marks_obt, D.maxmarks, D.isabsentt, E.pk_examid
            FROM SMS_StuExamMarks_Dtl D
            INNER JOIN SMS_DgExam_Mst DEM ON D.fk_dgexammapid = DEM.pk_dgexammapid
            INNER JOIN SMS_Exam_Mst E ON DEM.fk_examid = E.pk_examid
            WHERE D.fk_stucourseallocid IN ({placeholders})
        ''', alloc_ids)
        
        for m in marks:
            alloc_id = m['fk_stucourseallocid']
            if alloc_id not in marks_dict:
                marks_dict[alloc_id] = {}
            exam_id = m['pk_examid']
            marks_dict[alloc_id][exam_id] = {
                'val': m['marks_obt'],
                'absent': m['isabsentt'] == 1,
                'max': m['maxmarks']
            }
            
        clds = DB.fetch_all(f'''
            SELECT fk_stucourseallocid, gp, CP, gpa, OGPA, ispassed, ThPassFail, PrPassFail 
            FROM SMS_StuExamMarks_Cld WHERE fk_stucourseallocid IN ({placeholders})
        ''', alloc_ids)
        for cld in clds:
            cld_dict[cld['fk_stucourseallocid']] = cld

    result = []
    for c in courses:
        alloc_id = c['Pk_stucourseallocid']
        m_data = marks_dict.get(alloc_id, {})
        cld_data = cld_dict.get(alloc_id, {})
        
        # Mapping exam ids: 1: Internal Theory, 2: Internal Practical, 3: External Theory, 7: External Practical
        # 13: Assignment, 14: Midterm Theory PG, 15: Final Theory PG, 16: Practical PG, 18: Final Theory Internal
        in_th = m_data.get(1) or m_data.get(14) or m_data.get(18) or m_data.get(13)
        in_pr = m_data.get(2) or m_data.get(16)
        ex_th = m_data.get(3) or m_data.get(15)
        ex_pr = m_data.get(7)
        
        def format_mark(m_obj):
            if m_obj and m_obj['val'] is not None:
                val = float(m_obj['val'])
                max_val = float(m_obj['max'] or 0)
                if val == 0 and max_val == 0:
                    return "0.000/0"
                max_str = f"{int(max_val)}" if max_val.is_integer() else f"{max_val}"
                return f"{val:.2f}/{max_str}"
            return '0.000/0'

        in_th_val = format_mark(in_th)
        in_pr_val = format_mark(in_pr)
        ex_th_val = format_mark(ex_th)
        ex_pr_val = format_mark(ex_pr)
        
        gp = cld_data.get('gp')
        cp = cld_data.get('CP')
        gpa = cld_data.get('gpa')
        ogpa = cld_data.get('OGPA')
        ispassed = cld_data.get('ispassed')
        
        th_pf = cld_data.get('ThPassFail', '')
        pr_pf = cld_data.get('PrPassFail', '')
        passed_str = 'Pending'
        if ispassed is not None:
            if th_pf and pr_pf:
                passed_str = f"{th_pf} + {pr_pf} = {'P' if ispassed else 'F'}"
            else:
                passed_str = 'P' if ispassed else 'F'
        
        result.append({
            'coursecode': c['coursecode'],
            'coursename': c['coursename'],
            'in_th': in_th_val,
            'in_pr': in_pr_val,
            'ex_th': ex_th_val,
            'ex_pr': ex_pr_val,
            'gp': f"{float(gp):.3f}" if gp is not None else '', 
            'cp': f"{float(cp):.2f}" if cp is not None else '',
            'gpa': f"{float(gpa):.3f}" if gpa is not None else '',
            'ogpa': f"{float(ogpa):.3f}" if ogpa is not None else '',
            'passed': passed_str
        })
    return jsonify(result)
"""

pattern = re.compile(r"@examination_bp\.route\('/api/get_student_courses_ug_mba'\).*?return jsonify\(result\)\n", re.DOTALL)
if pattern.search(code):
    code = pattern.sub(new_api, code)
    with open('app/blueprints/examination/marks_process_ug_mba.py', 'w', encoding='utf-8') as out_f:
        out_f.write(code)
    print('Updated get_student_courses_ug_mba successfully')
else:
    print('Failed to find replace target')
