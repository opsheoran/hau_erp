from flask import render_template, request, redirect, url_for, flash, session, jsonify
from app.blueprints.examination import examination_bp, permission_required
from app.models.examination import ExaminationModel
from app.models import AcademicsModel, InfrastructureModel
from app.db import DB
from app.utils import get_pagination
import json

@examination_bp.route('/student_marks_entry_pg_phd', methods=['GET', 'POST'])
@permission_required('Student Marks Entry(PG/PHD) By Teacher')
def student_marks_entry_pg_phd():
    if request.method == 'POST':
        action = request.form.get('action', '').strip().upper()
        
        if action in ['SAVE', 'SUBMIT']:
            try:
                user_id = session.get('user_id')
                alloc_ids_str = request.form.get('alloc_ids')
                if alloc_ids_str:
                    alloc_ids = json.loads(alloc_ids_str)
                    exam_map_ids = json.loads(request.form.get('exam_map_ids'))
                    
                    is_submit = (action == 'SUBMIT')

                    for alloc_id in alloc_ids:
                        for emap_id in exam_map_ids:
                            mark_key = f"marks_{alloc_id}_{emap_id}"
                            absent_key = f"absent_{alloc_id}_{emap_id}"
                            max_key = f"max_{alloc_id}_{emap_id}"
                            
                            mark_val = request.form.get(mark_key)
                            is_absent = request.form.get(absent_key) == '1'
                            max_val = request.form.get(max_key)
                            
                            if is_absent:
                                mark_val = '0'
                                
                            if mark_val is not None and mark_val != '':
                                try:
                                    if float(mark_val) > float(max_val):
                                        flash(f"Marks cannot exceed {max_val} for allocation {alloc_id}.", "danger")
                                        continue
                                except ValueError:
                                    flash(f"Invalid marks format for allocation {alloc_id}.", "danger")
                                    continue
                                
                                existing = DB.fetch_one("""
                                    SELECT Pk_Stumarksdtlid FROM SMS_StuExamMarks_Dtl 
                                    WHERE fk_stucourseallocid = ? AND fk_dgexammapid = ?
                                """, [alloc_id, emap_id])
                                
                                if existing:
                                    DB.execute("""
                                        UPDATE SMS_StuExamMarks_Dtl 
                                        SET marks_obt = ?, maxmarks = ?, isabsentt = ?, 
                                            isStudentMarksLocked = ?, islocked = ?, IsmarksfeedforPG_PHD = 1, fk_userid = ?, feeddate = GETDATE()
                                        WHERE Pk_Stumarksdtlid = ?
                                    """, [mark_val, max_val, 1 if is_absent else 0, 1 if is_submit else 0, 1 if is_submit else 0, user_id, existing['Pk_Stumarksdtlid']])
                                else:
                                    DB.execute("""
                                        INSERT INTO SMS_StuExamMarks_Dtl
                                        (fk_stucourseallocid, fk_dgexammapid, marks_obt, maxmarks, isabsentt, isStudentMarksLocked, islocked, IsmarksfeedforPG_PHD, fk_userid, feeddate)
                                        VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, GETDATE())
                                    """, [alloc_id, emap_id, mark_val, max_val, 1 if is_absent else 0, 1 if is_submit else 0, 1 if is_submit else 0, user_id])
                    
                    flash(f'Marks {"submitted" if action == "SUBMIT" else "saved"} successfully.', 'success')
            except Exception as e:
                flash(f"Error saving marks: {str(e)}", 'danger')
                
        # Preserve filters on reload
        return redirect(url_for('examination.student_marks_entry_pg_phd',
                                college_id=request.form.get('college_id'),
                                session_id=request.form.get('session_id'),
                                degree_id=request.form.get('degree_id'),
                                class_id=request.form.get('class_id'),
                                department_id=request.form.get('department_id'),
                                year_id=request.form.get('year_id'),
                                exam_config_id=request.form.get('exam_config_id'),
                                course_id=request.form.get('course_id')))

    # GET Request logic
    filters = {
        'college_id': request.args.get('college_id', ''),
        'session_id': request.args.get('session_id', ''),
        'degree_id': request.args.get('degree_id', ''),
        'class_id': request.args.get('class_id', ''),
        'department_id': request.args.get('department_id', ''),
        'year_id': request.args.get('year_id', ''),
        'exam_config_id': request.args.get('exam_config_id', ''),
        'course_id': request.args.get('course_id', '')
    }

    exam_configs = []
    if filters['degree_id'] and filters['session_id']:
        exam_configs = ExaminationModel.get_formatted_exam_configs(filters['degree_id'], filters['session_id'])

    lookups = {
        'colleges': AcademicsModel.get_colleges_simple(),
        'sessions': InfrastructureModel.get_sessions(),
        'degrees': AcademicsModel.get_all_degrees(),
        'classes': DB.fetch_all("SELECT pk_semesterid as id, semester_roman as name FROM SMS_Semester_Mst ORDER BY semesterorder"),
        'departments': AcademicsModel.get_departments(),
        'years': DB.fetch_all("SELECT pk_degreeyearid as id, degreeyear_char as name FROM SMS_DegreeYear_Mst ORDER BY dgyearorder"),
        'exam_configs': exam_configs
    }

    return render_template('examination/student_marks_entry_pg_phd.html', 
                           lookups=lookups, filters=filters)



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
        SELECT DISTINCT A.Pk_stucourseallocid, S.enrollmentno, S.AdmissionNo, S.fullname
        FROM SMS_StuCourseAllocation A
        INNER JOIN SMS_Student_Mst S ON A.fk_sturegid = S.pk_sid
        INNER JOIN SMS_DegreeCycle_Mst DC ON A.fk_degreecycleid = DC.pk_degreecycleid
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
            SELECT fk_stucourseallocid, fk_dgexammapid, marks_obt, isabsentt, isStudentMarksLocked, islocked
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
                if m['isStudentMarksLocked'] == 1 or m['islocked'] == 1:
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
        SELECT DISTINCT A.Pk_stucourseallocid, S.enrollmentno, S.AdmissionNo, S.fullname
        FROM SMS_StuCourseAllocation A
        INNER JOIN SMS_Student_Mst S ON A.fk_sturegid = S.pk_sid
        INNER JOIN SMS_DegreeCycle_Mst DC ON A.fk_degreecycleid = DC.pk_degreecycleid
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
        SELECT C.coursecode, C.coursename, C.crhr_theory, C.crhr_practical
        FROM SMS_Course_Mst C
        WHERE C.pk_courseid = ?
    ''', [course_id])
    
    instructor_row = DB.fetch_one("SELECT name FROM UM_Users_Mst WHERE pk_userId = ?", [session.get('user_id')])
    
    course_info = {
        'session_name': sess_name,
        'semester_name': sem_name,
        'degree_name': deg_name,
        'dept_name': 'Dean Office',  
        'instructor_name': instructor_row['name'] if instructor_row else '',
        'course_code': c_row['coursecode'] if c_row else '',
        'course_name': c_row['coursename'] if c_row else '',
        'crhr_theory': c_row['crhr_theory'] if c_row else 0,
        'crhr_practical': c_row['crhr_practical'] if c_row else 0,
        'total_max_marks': int(total_max) if total_max.is_integer() else total_max
    }
    
    from .marks_report import generate_internal_marks_report_pdf
    return generate_internal_marks_report_pdf(course_info, students, exam_columns, is_submitted, is_pg_phd=True)
