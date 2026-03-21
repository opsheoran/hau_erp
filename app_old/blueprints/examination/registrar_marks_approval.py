from flask import render_template, request, redirect, url_for, flash, session, jsonify
from app.blueprints.examination import examination_bp, permission_required
from app.models.examination import ExaminationModel
from app.models import AcademicsModel, InfrastructureModel
from app.db import DB
import json

@examination_bp.route('/registrar_approval', methods=['GET', 'POST'])
@permission_required('Registrar Approval')
def registrar_approval():
    loc_id = session.get('selected_loc', '')
    default_college = DB.fetch_one("SELECT pk_collegeid FROM SMS_College_Mst WHERE fk_locid = ?", [loc_id])
    default_college_id = str(default_college['pk_collegeid']) if default_college else ''
    default_session_id = str(InfrastructureModel.get_current_session_id() or '')

    if request.method == 'POST':
        action = request.form.get('btnAction', '').strip().upper()
        if action == 'APPROVE & SUBMIT':
            try:
                user_id = session.get('user_id')
                alloc_ids_str = request.form.get('alloc_ids')
                if alloc_ids_str:
                    alloc_ids = json.loads(alloc_ids_str)
                    exam_map_ids = json.loads(request.form.get('exam_map_ids'))
                    
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
                                
                                DB.execute("""
                                    UPDATE SMS_StuExamMarks_Dtl 
                                    SET marks_obt = ?, maxmarks = ?, isabsentt = ?, 
                                        IsApprovedByRegistrar = 1, islockedbyRegistrar = 1, fk_userid = ?, feeddate = GETDATE()
                                    WHERE fk_stucourseallocid = ? AND fk_dgexammapid = ?
                                """, [mark_val, max_val, 1 if is_absent else 0, user_id, alloc_id, emap_id])
                    
                    flash('Marks approved successfully by Registrar.', 'success')
            except Exception as e:
                flash(f"Error approving marks: {str(e)}", 'danger')

        elif action == 'UNLOCK':
            try:
                alloc_ids_str = request.form.get('alloc_ids')
                if alloc_ids_str:
                    alloc_ids = json.loads(alloc_ids_str)
                    exam_map_ids = json.loads(request.form.get('exam_map_ids'))
                    
                    for alloc_id in alloc_ids:
                        for emap_id in exam_map_ids:
                            DB.execute("""
                                UPDATE SMS_StuExamMarks_Dtl 
                                SET IsApprovedByRegistrar = NULL, islockedbyRegistrar = NULL,
                                    IsApprovedByCOE = NULL, islockedbyCOE = NULL,
                                    IsApprovedByHOD = NULL, islockedbyHOD = NULL,
                                    islocked = NULL
                                WHERE fk_stucourseallocid = ? AND fk_dgexammapid = ?
                            """, [alloc_id, emap_id])
                    flash('Marks unlocked successfully. Please submit the marks again at Teacher, HOD, COE, and Registrar level.', 'success')
            except Exception as e:
                flash(f"Error unlocking marks: {str(e)}", 'danger')

        return redirect(url_for('examination.registrar_approval',
                                college_id=request.form.get('college_id'),
                                session_id=request.form.get('session_id'),
                                degree_id=request.form.get('degree_id'),
                                class_id=request.form.get('class_id'),
                                department_id=request.form.get('department_id'),
                                year_id=request.form.get('year_id'),
                                exam_config_id=request.form.get('exam_config_id'),
                                exam_category=request.form.get('exam_category', '1'),
                                course_id=request.form.get('course_id')))

    filters = {
        'college_id': request.args.get('college_id', default_college_id),
        'session_id': request.args.get('session_id', default_session_id),
        'degree_id': request.args.get('degree_id', ''),
        'class_id': request.args.get('class_id', ''),
        'department_id': request.args.get('department_id', ''),
        'year_id': request.args.get('year_id', ''),
        'exam_config_id': request.args.get('exam_config_id', ''),
        'exam_category': request.args.get('exam_category', '1'),
        'course_id': request.args.get('course_id', '')
    }

    course_name = ''
    if filters['course_id']:
        c_row = DB.fetch_one("SELECT coursecode + ' || ' + coursename as name FROM SMS_Course_Mst WHERE pk_courseid = ?", [filters['course_id']])
        if c_row:
            course_name = c_row['name']

    filters['course_name'] = course_name

    exam_configs = []
    if filters['degree_id'] and filters['session_id']:
        exam_configs = ExaminationModel.get_formatted_exam_configs(filters['degree_id'], filters['session_id'])
        if not filters['exam_config_id'] and exam_configs:
            filters['exam_config_id'] = str(exam_configs[0]['id'])

    degrees = []
    if filters['college_id']:
        degrees = DB.fetch_all("""
            SELECT DISTINCT D.pk_degreeid as id, D.degreename as name
            FROM SMS_CollegeDegreeBranchMap_Mst M
            INNER JOIN SMS_Degree_Mst D ON M.fk_degreeid = D.pk_degreeid
            WHERE M.fk_collegeid = ? AND D.degreename NOT LIKE '%---%' AND (D.fk_degreetypeid = 3 OR D.degreename LIKE '%MBA%')
            ORDER BY D.degreename
        """, [filters['college_id']])

    lookups = {
        'colleges': DB.fetch_all("SELECT pk_collegeid as id, collegename as name FROM SMS_College_Mst WHERE fk_locid = ? ORDER BY collegename", [loc_id]) if loc_id else DB.fetch_all("SELECT pk_collegeid as id, collegename as name FROM SMS_College_Mst ORDER BY collegename"),
        'sessions': InfrastructureModel.get_sessions(),
        'degrees': degrees,
        'classes': DB.fetch_all("SELECT pk_semesterid as id, semester_roman as name, semesterorder as [order] FROM SMS_Semester_Mst ORDER BY semesterorder"),
        'departments': DB.fetch_all("SELECT pk_deptid as id, description as name FROM Department_Mst ORDER BY description"),
        'years': DB.fetch_all("SELECT pk_degreeyearid as id, degreeyear_char as name FROM SMS_DegreeYear_Mst ORDER BY dgyearorder"),
        'exam_configs': exam_configs
    }

    return render_template('examination/registrar_approval_form.html', lookups=lookups, filters=filters)

@examination_bp.route('/api/get_registrar_courses')
def get_registrar_courses():
    college_id = request.args.get('college_id')
    session_id = request.args.get('session_id')
    degree_id = request.args.get('degree_id')
    class_id = request.args.get('class_id')
    department_id = request.args.get('department_id')
    year_id = request.args.get('year_id')
    exam_category = request.args.get('exam_category', '1')

    if not all([college_id, session_id, degree_id, class_id]):
        return jsonify([])

    alloc_filter = "A.fk_dgacasessionid = ? AND DC.fk_degreeid = ? AND S.fk_collegeid = ?"
    params = [session_id, degree_id, college_id]

    if class_id == '1': # Odd
        alloc_filter += " AND DC.fk_semesterid IN (SELECT pk_semesterid FROM SMS_Semester_Mst WHERE semesterorder % 2 = 1)"
    elif class_id == '2': # Even
        alloc_filter += " AND DC.fk_semesterid IN (SELECT pk_semesterid FROM SMS_Semester_Mst WHERE semesterorder % 2 = 0)"
    else:
        alloc_filter += " AND DC.fk_semesterid = ?"
        params.append(class_id)

    if department_id:
        alloc_filter += " AND C.fk_Deptid = ?"
        params.append(department_id)

    if year_id:
        alloc_filter += " AND DC.fk_degreeyearid = ?"
        params.append(year_id)

    if exam_category == '1': # Regular/Back
        alloc_filter += " AND ISNULL(A.IsSummer, 0) = 0 AND ISNULL(A.IsSupplementary, 0) = 0 AND ISNULL(A.Is_Igrade, 0) = 0"
    elif exam_category == '2': # Supple/Summer
        alloc_filter += " AND (A.IsSupplementary = 1 OR A.IsSummer = 1)"
    elif exam_category == '3': # Revised
        alloc_filter += " AND A.Is_Revised = 1" 

    # Only show courses where COE has approved at least some marks, or specifically Registrar courses
    # We will fetch courses that have `islockedbyCOE = 1`.
    # And specifically handle the logic for "NCC/NSS/Other college" if that's a hard requirement, 
    # but based on DB analysis, Registrar can approve any course that COE approved. The filtering by department is what restricts it.
    
    query = f'''
        SELECT DISTINCT C.pk_courseid as id, C.coursecode + ' || ' + C.coursename as name
        FROM SMS_StuCourseAllocation A
        INNER JOIN SMS_Course_Mst C ON A.fk_courseid = C.pk_courseid
        INNER JOIN SMS_DegreeCycle_Mst DC ON A.fk_degreecycleid = DC.pk_degreecycleid      
        INNER JOIN SMS_Student_Mst S ON A.fk_sturegid = S.pk_sid
        INNER JOIN SMS_StuExamMarks_Dtl D ON A.Pk_stucourseallocid = D.fk_stucourseallocid 
        WHERE {alloc_filter}
        AND ISNULL(D.islockedbyCOE, 0) = 1
        ORDER BY name
    '''
    
    courses = DB.fetch_all(query, params)
    return jsonify(courses)

@examination_bp.route('/api/get_students_for_registrar_approval')
def get_students_for_registrar_approval():
    college_id = request.args.get('college_id')
    session_id = request.args.get('session_id')
    degree_id = request.args.get('degree_id')
    class_id = request.args.get('class_id')
    course_id = request.args.get('course_id')
    year_id = request.args.get('year_id')
    department_id = request.args.get('department_id')

    if not all([college_id, session_id, degree_id, class_id, course_id, year_id]):
        return jsonify({'error': 'Missing parameters'})

    exams_query = """
        SELECT DISTINCT M.pk_dgexammapid, E.exam, W.maxmarks_th, W.maxmarks_pr, E.istheory, E.ispractical, E.examorder
        FROM SMS_DgExamWei_WithCourse W
        INNER JOIN SMS_DgExam_Mst M ON W.fk_dgexammapid = M.pk_dgexammapid
        INNER JOIN SMS_Exam_Mst E ON M.fk_examid = E.pk_examid
        WHERE W.fk_courseid = ? AND M.fk_acasessionid_from = ? AND M.fk_degreeid = ? AND E.isinternal = 1
        ORDER BY E.examorder
    """
    exams = DB.fetch_all(exams_query, [course_id, session_id, degree_id])
    
    students_query = """
        SELECT A.Pk_stucourseallocid, S.enrollmentno, S.AdmissionNo, S.fullname, RND.originalRollNo, RND.encryptuniv
        FROM SMS_StuCourseAllocation A
        INNER JOIN SMS_Student_Mst S ON A.fk_sturegid = S.pk_sid
        INNER JOIN SMS_DegreeCycle_Mst DC ON A.fk_degreecycleid = DC.pk_degreecycleid
        OUTER APPLY (SELECT TOP 1 originalRollNo, encryptuniv FROM SMS_RollNumber_Dtl WHERE fk_sturegid = S.pk_sid ORDER BY pk_rollnodtlid DESC) RND
        WHERE A.fk_courseid = ? AND A.fk_dgacasessionid = ? AND DC.fk_degreeid = ? AND ISNULL(S.IsRegCancel, 0) = 0 AND ISNULL(S.isdgcompleted, 0) = 0 AND A.fk_packageId = 0 
        AND S.fk_collegeid = ? AND DC.fk_semesterid = ? AND DC.fk_degreeyearid = ?
        ORDER BY RND.encryptuniv, S.enrollmentno
    """
    params = [course_id, session_id, degree_id, college_id, class_id, year_id]
    students = DB.fetch_all(students_query, params)

    alloc_ids = [s['Pk_stucourseallocid'] for s in students]
    marks = []
    if alloc_ids:
        placeholders = ','.join(['?'] * len(alloc_ids))
        marks = DB.fetch_all(f"""
            SELECT fk_stucourseallocid, fk_dgexammapid, marks_obt, isabsentt, IsApprovedByRegistrar, islockedbyRegistrar
            FROM SMS_StuExamMarks_Dtl
            WHERE fk_stucourseallocid IN ({placeholders}) AND ISNULL(islockedbyCOE, 0) = 1
        """, alloc_ids)

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
            'encryptuniv': s.get('encryptuniv', ''),
            'marks': {},
            'is_approved_by_registrar': False
        }
        has_locked_marks = False
        for m in marks:
            if m['fk_stucourseallocid'] == s['Pk_stucourseallocid']:
                has_locked_marks = True
                s_data['marks'][str(m['fk_dgexammapid'])] = {
                    'val': m['marks_obt'],
                    'absent': m['isabsentt'] == 1
                }
                if m['IsApprovedByRegistrar'] == 1 or m.get('islockedbyRegistrar') == 1:
                    s_data['is_approved_by_registrar'] = True
        if has_locked_marks:
            formatted_students.append(s_data)

    return jsonify({
        'columns': exam_columns,
        'students': formatted_students,
        'alloc_ids': alloc_ids,
        'exam_map_ids': exam_map_ids,
        'student_count': len(formatted_students)
    })
