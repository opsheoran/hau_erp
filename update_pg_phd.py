import re

with open('app/templates/examination/student_marks_entry_pg_phd.html', 'r') as f:
    content = f.read()

# Add Is Research and Is Deficiency to the Course Selection table
old_course_selection = """            <tr class="courseSelectionRow" style="display: none;">
                <td class="vtext">Is NC</td>
                <td class="colon">:</td>
                <td class="required">
                    <span class="chkbox"><input id="chkIsNC" type="checkbox" name="chkIsNC" disabled="disabled"></span>
                </td>
                <td class="vtext">Exam Type</td>
                <td class="colon">:</td>
                <td>
                    <select name="ddlExamType" id="ddlExamType" class="dropdown" style="width: 150px;">
                        <option value="1" selected>Internal</option>
                        <option value="2">External</option>
                    </select>
                </td>
            </tr>"""

new_course_selection = """            <tr class="courseSelectionRow" style="display: none;">
                <td class="vtext">Is NC</td>
                <td class="colon">:</td>
                <td class="required">
                    <span class="chkbox"><input id="chkIsNC" type="checkbox" name="chkIsNC" disabled="disabled"></span>
                </td>
                <td class="vtext">Exam Type</td>
                <td class="colon">:</td>
                <td>
                    <select name="ddlExamType" id="ddlExamType" class="dropdown" style="width: 150px;">
                        <option value="1" selected>Internal</option>
                        <option value="2">External</option>
                    </select>
                </td>
            </tr>
            <tr class="courseSelectionRow" style="display: none;">
                <td class="vtext">Is Research</td>
                <td class="colon">:</td>
                <td class="required">
                    <span class="chkbox"><input id="chkIsResearch" type="checkbox" name="chkIsResearch" disabled="disabled"></span>
                </td>
                <td class="vtext">Is Deficiency</td>
                <td class="colon">:</td>
                <td class="required">
                    <span class="chkbox"><input id="chkIsDeficiency" type="checkbox" name="chkIsDeficiency" disabled="disabled"></span>
                </td>
            </tr>"""

content = content.replace(old_course_selection, new_course_selection)

content = content.replace("url_for('examination.get_courses_for_marks_entry')", "url_for('examination.get_courses_for_marks_entry_pg_phd')")
content = content.replace("url_for('examination.get_students_for_marks_entry')", "url_for('examination.get_students_for_marks_entry_pg_phd')")
content = content.replace("url_for('examination.generate_marks_report_internal')", "url_for('examination.generate_marks_report_pg_phd')")

# Add JS logic for Is Research / Is Deficiency
content = content.replace("document.getElementById('chkIsNC').checked = (selectedOpt.getAttribute('data-nc') === '1' || selectedOpt.getAttribute('data-nc') === 'true');", 
                          """document.getElementById('chkIsNC').checked = (selectedOpt.getAttribute('data-nc') === '1' || selectedOpt.getAttribute('data-nc') === 'true');
    document.getElementById('chkIsResearch').checked = (selectedOpt.getAttribute('data-research') === '1' || selectedOpt.getAttribute('data-research') === 'true');
    document.getElementById('chkIsDeficiency').checked = (selectedOpt.getAttribute('data-deficiency') === '1' || selectedOpt.getAttribute('data-deficiency') === 'true');""")

content = content.replace("document.getElementById('chkIsNC').checked = false;", 
                          """document.getElementById('chkIsNC').checked = false;
        document.getElementById('chkIsResearch').checked = false;
        document.getElementById('chkIsDeficiency').checked = false;""")

content = content.replace("html += `<option value=\"${c.id}\" data-th=\"${c.crhr_theory}\" data-pr=\"${c.crhr_practical}\" data-nc=\"${c.is_nc}\" data-type=\"${c.exam_type}\">${c.name}</option>`;", 
                          "html += `<option value=\"${c.id}\" data-th=\"${c.crhr_theory}\" data-pr=\"${c.crhr_practical}\" data-nc=\"${c.is_nc}\" data-research=\"${c.is_research}\" data-deficiency=\"${c.is_deficiency}\" data-type=\"${c.exam_type}\">${c.name}</option>`;")

with open('app/templates/examination/student_marks_entry_pg_phd.html', 'w') as f:
    f.write(content)
print("Updated student_marks_entry_pg_phd.html")

# Update Python Blueprint
with open('app/blueprints/examination/student_marks_entry_pg_phd.py', 'r') as f:
    code = f.read()

code = code.replace("url_for('examination.student_marks_entry_coe", "url_for('examination.student_marks_entry_pg_phd")

code += """
@examination_bp.route('/api/get_courses_for_marks_entry_pg_phd')
def get_courses_for_marks_entry_pg_phd():
    college_id = request.args.get('college_id')
    session_id = request.args.get('session_id')
    degree_id = request.args.get('degree_id')
    class_id = request.args.get('class_id')
    department_id = request.args.get('department_id')
    year_id = request.args.get('year_id')
    exam_config_id = request.args.get('exam_config_id')
    
    if not all([college_id, session_id, degree_id, class_id, year_id, exam_config_id]):
        return jsonify({'error': 'Missing required parameters.'})

    query = '''
        SELECT DISTINCT C.pk_courseid as id, C.coursecode + ' || ' + C.coursename as name,
               C.crhr_theory, C.crhr_practical, ISNULL(C.isNC, 0) as is_nc,
               ISNULL(C.IsResearch, 0) as is_research, ISNULL(C.Isdeficiency, 0) as is_deficiency,
               'Internal' as exam_type
        FROM SMS_StuCourseAllocation A
        INNER JOIN SMS_Course_Mst C ON A.fk_courseid = C.pk_courseid
        INNER JOIN SMS_DegreeCycle_Mst DC ON A.fk_degreecycleid = DC.pk_degreecycleid
        INNER JOIN SMS_Student_Mst S ON A.fk_sturegid = S.pk_sid
        WHERE A.fk_dgacasessionid = ? AND DC.fk_degreeid = ? AND S.fk_collegeid = ?
        AND DC.fk_semesterid = ? AND DC.fk_degreeyearid = ?
    '''
    params = [session_id, degree_id, college_id, class_id, year_id]
    
    if department_id:
        query += " AND S.fk_deptid = ?"
        params.append(department_id)
        
    query += " ORDER BY name"
    courses = DB.fetch_all(query, params)
    
    return jsonify({'courses': courses})

@examination_bp.route('/api/get_students_for_marks_entry_pg_phd')
def get_students_for_marks_entry_pg_phd():
    college_id = request.args.get('college_id')
    session_id = request.args.get('session_id')
    degree_id = request.args.get('degree_id')
    class_id = request.args.get('class_id')
    course_id = request.args.get('course_id')
    year_id = request.args.get('year_id')
    department_id = request.args.get('department_id')

    if not all([college_id, session_id, degree_id, class_id, course_id, year_id]):
        return jsonify({'error': 'Missing parameters'})

    exams_query = '''
        SELECT DISTINCT M.pk_dgexammapid, E.exam, W.maxmarks_th, W.maxmarks_pr, E.istheory, E.ispractical, E.examorder
        FROM SMS_DgExamWei_WithCourse W
        INNER JOIN SMS_DgExam_Mst M ON W.fk_dgexammapid = M.pk_dgexammapid
        INNER JOIN SMS_Exam_Mst E ON M.fk_examid = E.pk_examid
        WHERE W.fk_courseid = ? AND M.fk_acasessionid_from = ? AND M.fk_degreeid = ? AND E.isinternal = 1
        ORDER BY E.examorder
    '''
    exams = DB.fetch_all(exams_query, [course_id, session_id, degree_id])
    
    students_query = '''
        SELECT A.Pk_stucourseallocid, S.enrollmentno, S.AdmissionNo, S.fullname, RND.originalRollNo
        FROM SMS_StuCourseAllocation A
        INNER JOIN SMS_Student_Mst S ON A.fk_sturegid = S.pk_sid
        INNER JOIN SMS_DegreeCycle_Mst DC ON A.fk_degreecycleid = DC.pk_degreecycleid
        LEFT JOIN SMS_RollNumber_Dtl RND ON S.pk_sid = RND.fk_sturegid
        WHERE A.fk_courseid = ? AND A.fk_dgacasessionid = ? AND DC.fk_degreeid = ? 
        AND S.fk_collegeid = ? AND DC.fk_semesterid = ? AND DC.fk_degreeyearid = ?
    '''
    params = [course_id, session_id, degree_id, college_id, class_id, year_id]
    if department_id:
        students_query += " AND S.fk_deptid = ?"
        params.append(department_id)
        
    students_query += " ORDER BY S.enrollmentno"
    students = DB.fetch_all(students_query, params)

    alloc_ids = [s['Pk_stucourseallocid'] for s in students]
    marks = []
    if alloc_ids:
        placeholders = ','.join(['?'] * len(alloc_ids))
        marks = DB.fetch_all(f'''
            SELECT fk_stucourseallocid, fk_dgexammapid, marks_obt, isabsentt, isStudentMarksLocked
            FROM SMS_StuExamMarks_Dtl
            WHERE fk_stucourseallocid IN ({placeholders})
        ''', alloc_ids)

    formatted_students = []
    exam_columns = []
    exam_map_ids = []
    for ex in exams:
        max_val = ex['maxmarks_th'] if ex['istheory'] else ex['maxmarks_pr']
        if float(max_val or 0) > 0:
            exam_columns.append({
                'id': ex['pk_dgexammapid'],
                'name': ex['exam'],
                'max_val': max_val
            })
            exam_map_ids.append(ex['pk_dgexammapid'])

    for s in students:
        roll_no = s.get('originalRollNo', '')
        if not roll_no:
            roll_no = s.get('AdmissionNo', '')
        if not roll_no:
            roll_no = ''
            
        s_data = {
            'alloc_id': s['Pk_stucourseallocid'],
            'enrollmentno': s['enrollmentno'] if s['enrollmentno'] else '',
            'fullname': s['fullname'] if s['fullname'] else '',
            'roll_no': roll_no,
            'marks': {},
            'is_locked': False
        }
        for m in marks:
            if m['fk_stucourseallocid'] == s['Pk_stucourseallocid']:
                s_data['marks'][str(m['fk_dgexammapid'])] = {
                    'val': m['marks_obt'],
                    'absent': m['isabsentt'] == 1
                }
                if m['isStudentMarksLocked'] == 1:
                    s_data['is_locked'] = True
        formatted_students.append(s_data)

    deg_row = DB.fetch_one("SELECT degreename FROM SMS_Degree_Mst WHERE pk_degreeid = ?", [degree_id])
    deg_name = deg_row['degreename'] if deg_row else ''
    sem_row = DB.fetch_one("SELECT semester_roman FROM SMS_Semester_Mst WHERE pk_semesterid = ?", [class_id])
    sem_name = sem_row['semester_roman'] if sem_row else ''
    
    return jsonify({
        'columns': exam_columns,
        'students': formatted_students,
        'alloc_ids': alloc_ids,
        'exam_map_ids': exam_map_ids,
        'degree_name': deg_name,
        'semester_name': sem_name,
        'student_count': len(students)
    })

@examination_bp.route('/api/generate_marks_report_pg_phd')
def generate_marks_report_pg_phd():
    college_id = request.args.get('college_id')
    session_id = request.args.get('session_id')
    degree_id = request.args.get('degree_id')
    class_id = request.args.get('class_id')
    course_id = request.args.get('course_id')
    year_id = request.args.get('year_id')
    department_id = request.args.get('department_id')

    if not all([college_id, session_id, degree_id, class_id, course_id, year_id]):
        return "Missing parameters", 400

    exams_query = '''
        SELECT DISTINCT M.pk_dgexammapid, E.exam, W.maxmarks_th, W.maxmarks_pr, E.istheory, E.ispractical, E.examorder
        FROM SMS_DgExamWei_WithCourse W
        INNER JOIN SMS_DgExam_Mst M ON W.fk_dgexammapid = M.pk_dgexammapid
        INNER JOIN SMS_Exam_Mst E ON M.fk_examid = E.pk_examid
        WHERE W.fk_courseid = ? AND M.fk_acasessionid_from = ? AND M.fk_degreeid = ? AND E.isinternal = 1
        ORDER BY E.examorder
    '''
    exams = DB.fetch_all(exams_query, [course_id, session_id, degree_id])
    
    students_query = '''
        SELECT A.Pk_stucourseallocid, S.enrollmentno, S.AdmissionNo, S.fullname, RND.originalRollNo
        FROM SMS_StuCourseAllocation A
        INNER JOIN SMS_Student_Mst S ON A.fk_sturegid = S.pk_sid
        INNER JOIN SMS_DegreeCycle_Mst DC ON A.fk_degreecycleid = DC.pk_degreecycleid
        LEFT JOIN SMS_RollNumber_Dtl RND ON S.pk_sid = RND.fk_sturegid
        WHERE A.fk_courseid = ? AND A.fk_dgacasessionid = ? AND DC.fk_degreeid = ? 
        AND S.fk_collegeid = ? AND DC.fk_semesterid = ? AND DC.fk_degreeyearid = ?
    '''
    params = [course_id, session_id, degree_id, college_id, class_id, year_id]
    if department_id:
        students_query += " AND S.fk_deptid = ?"
        params.append(department_id)
        
    students_query += " ORDER BY S.enrollmentno"
    students = DB.fetch_all(students_query, params)

    alloc_ids = [s['Pk_stucourseallocid'] for s in students]
    marks = []
    if alloc_ids:
        placeholders = ','.join(['?'] * len(alloc_ids))
        marks = DB.fetch_all(f'''
            SELECT fk_stucourseallocid, fk_dgexammapid, marks_obt, isabsentt, isStudentMarksLocked
            FROM SMS_StuExamMarks_Dtl
            WHERE fk_stucourseallocid IN ({placeholders})
        ''', alloc_ids)

    exam_columns = []
    total_max = 0
    for ex in exams:
        max_val = ex['maxmarks_th'] if ex['istheory'] else ex['maxmarks_pr']
        if float(max_val or 0) > 0:
            exam_columns.append({
                'id': ex['pk_dgexammapid'],
                'name': ex['exam'],
                'max_val': max_val
            })
            total_max += float(max_val)

    is_submitted = False
    for s in students:
        s['marks'] = {}
        for m in marks:
            if m['fk_stucourseallocid'] == s['Pk_stucourseallocid']:
                s['marks'][str(m['fk_dgexammapid'])] = {
                    'val': m['marks_obt'],
                    'absent': m['isabsentt'] == 1
                }
                if m['isStudentMarksLocked'] == 1:
                    is_submitted = True

    deg_row = DB.fetch_one("SELECT degreename FROM SMS_Degree_Mst WHERE pk_degreeid = ?", [degree_id])
    deg_name = deg_row['degreename'] if deg_row else ''
    sem_row = DB.fetch_one("SELECT semester_roman FROM SMS_Semester_Mst WHERE pk_semesterid = ?", [class_id])
    sem_name = sem_row['semester_roman'] if sem_row else ''
    sess_row = DB.fetch_one("SELECT sessionname FROM SMS_AcademicSession_Mst WHERE pk_sessionid = ?", [session_id])
    sess_name = sess_row['sessionname'] if sess_row else ''
    
    c_row = DB.fetch_one('''
        SELECT C.coursecode, C.coursename, C.crhr_theory, C.crhr_practical, E.empname as instructor_name
        FROM SMS_Course_Mst C
        LEFT JOIN SMS_TCourseAlloc_Dtl TD ON C.pk_courseid = TD.fk_courseid
        LEFT JOIN SMS_TCourseAlloc_Mst TM ON TD.fk_tcourseallocid = TM.pk_tcourseallocid AND TM.fk_sessionid = ? AND TM.fk_degreeid = ?
        LEFT JOIN SAL_Employee_Mst E ON TM.fk_employeeid = E.pk_empid
        WHERE C.pk_courseid = ?
    ''', [session_id, degree_id, course_id])
    
    course_info = {
        'session_name': sess_name,
        'semester_name': sem_name,
        'degree_name': deg_name,
        'dept_name': 'Dean Office',  
        'instructor_name': c_row['instructor_name'] if c_row and c_row['instructor_name'] else '',
        'course_code': c_row['coursecode'] if c_row else '',
        'course_name': c_row['coursename'] if c_row else '',
        'crhr_theory': c_row['crhr_theory'] if c_row else 0,
        'crhr_practical': c_row['crhr_practical'] if c_row else 0,
        'total_max_marks': int(total_max) if total_max.is_integer() else total_max
    }
    
    from .marks_report import generate_internal_marks_report_pdf
    return generate_internal_marks_report_pdf(course_info, students, exam_columns, is_submitted)
"""

with open('app/blueprints/examination/student_marks_entry_pg_phd.py', 'w') as f:
    f.write(code)
print("Updated student_marks_entry_pg_phd.py")
