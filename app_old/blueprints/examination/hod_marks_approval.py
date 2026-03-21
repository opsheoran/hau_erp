from flask import render_template, request, redirect, url_for, flash, session, jsonify
from app.blueprints.examination import examination_bp, permission_required
from app.models.examination import ExaminationModel
from app.models import AcademicsModel, InfrastructureModel
from app.db import DB
import json

@examination_bp.route('/hod_marks_approval', methods=['GET', 'POST'])
@permission_required('HOD Marks Approval')
def hod_marks_approval():
    emp_id = session.get('emp_id')
    default_session_id = str(InfrastructureModel.get_current_session_id() or '')

    loc_id = session.get('selected_loc', '')
    default_college = DB.fetch_one("SELECT pk_collegeid FROM SMS_College_Mst WHERE fk_locid = ?", [loc_id])
    default_college_id = str(default_college['pk_collegeid']) if default_college else ''

    filters = {
        'college_id': request.args.get('college_id', default_college_id),
        'session_id': request.args.get('session_id', default_session_id),
        'degree_id': request.args.get('degree_id', ''),
        'class_id': request.args.get('class_id', ''),
        'exam_type': request.args.get('exam_type', '1'),
        'exam_category': request.args.get('exam_category', '1') # 1=Reg/Back, 2=Supp, 3=Summer, 4=Igrade
    }

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'APPROVE':
            course_data = request.form.getlist('chkselectCourse')
            if course_data:
                count = 0
                for item in course_data:
                    parts = item.split('|')
                    if len(parts) == 3:
                        cid, sem_id, year_id = parts
                        DB.execute('''
                            UPDATE D
                            SET D.IsApprovedByHOD = 1, D.islockedbyHOD = 1
                            FROM SMS_StuExamMarks_Dtl D
                            INNER JOIN SMS_StuCourseAllocation A ON D.fk_stucourseallocid = A.Pk_stucourseallocid
                            INNER JOIN SMS_DegreeCycle_Mst DC ON A.fk_degreecycleid = DC.pk_degreecycleid
                            WHERE A.fk_dgacasessionid = ?
                            AND DC.fk_degreeid = ?
                            AND DC.fk_semesterid = ?
                            AND DC.fk_degreeyearid = ?
                            AND A.fk_courseid = ?
                            AND D.islocked = 1
                        ''', [filters['session_id'], filters['degree_id'], sem_id, year_id, cid])
                        count += 1
                flash(f'Successfully approved marks for {count} courses.', 'success')

        return redirect(url_for('examination.hod_marks_approval', **filters))

    exam_configs = []
    if filters['degree_id'] and filters['session_id']:
        exam_configs = ExaminationModel.get_formatted_exam_configs(filters['degree_id'], filters['session_id'])

    # HOD College Restriction
    hod_college = DB.fetch_all("SELECT pk_collegeid as id, collegename as name FROM SMS_College_Mst WHERE fk_locid = ?", [loc_id])
    if not hod_college:
         hod_college = AcademicsModel.get_colleges_simple()

    hod_degrees = DB.fetch_all("""
        SELECT DISTINCT D.pk_degreeid as id, D.degreename as name
        FROM SMS_CollegeDegreeBranchMap_Mst M
        INNER JOIN SMS_Degree_Mst D ON M.fk_degreeid = D.pk_degreeid
        WHERE M.fk_collegeid = ? AND D.degreename NOT LIKE '%---%'
        ORDER BY D.degreename
    """, [filters['college_id'] if filters['college_id'] else 0])

    lookups = {
        'colleges': hod_college,
        'sessions': InfrastructureModel.get_sessions(),
        'degrees': hod_degrees,
        'classes': [
            {'id': 'odd', 'name': 'Odd'},
            {'id': 'even', 'name': 'Even'}
        ],
        'exam_configs': exam_configs
    }
    
    return render_template('examination/hod_marks_approval.html', lookups=lookups, filters=filters)

@examination_bp.route('/api/get_hod_approval_courses')
def get_hod_approval_courses():
    college_id = request.args.get('college_id')
    session_id = request.args.get('session_id')
    degree_id = request.args.get('degree_id')
    class_id = request.args.get('class_id')
    exam_type = request.args.get('exam_type', '1') # 1 internal, 2 external
    exam_category = request.args.get('exam_category', '1')

    if not all([college_id, session_id, degree_id, class_id]):    
        return jsonify({'error': 'Missing parameters'})

    emp_id = session.get('emp_id')
    dept_ctx = AcademicsModel.get_hod_department_context(emp_id) if emp_id else {}
    sms_dept_ids = dept_ctx.get('sms_dept_ids', [])
    hr_dept_ids = [d['id'] for d in dept_ctx.get('hr_departments', [])]

    # Restrict completely if user is not HOD of any department
    if not sms_dept_ids and not hr_dept_ids:
        return jsonify({'pending': [], 'approved': [], 'error': 'You do not have HOD rights to approve marks for any department.'})

    alloc_filter = "A.fk_dgacasessionid = ? AND DC.fk_degreeid = ? AND S.fk_collegeid = ?"
    params = [session_id, degree_id, college_id]

    # Handle odd/even semester filtering
    if class_id == 'odd':
        alloc_filter += " AND DC.fk_semesterid IN (SELECT pk_semesterid FROM SMS_Semester_Mst WHERE semesterorder % 2 = 1)"
    elif class_id == 'even':
        alloc_filter += " AND DC.fk_semesterid IN (SELECT pk_semesterid FROM SMS_Semester_Mst WHERE semesterorder % 2 = 0)"
    else:
        alloc_filter += " AND DC.fk_semesterid = ?"
        params.append(class_id)

    # Filter by the Departments this HOD owns
    dept_conditions = []
    if sms_dept_ids:
        dept_placeholders = ','.join(['?'] * len(sms_dept_ids))
        dept_conditions.append(f"C.fk_Deptid IN ({dept_placeholders})")
        params.extend(sms_dept_ids)
    if hr_dept_ids:
        hr_placeholders = ','.join(['?'] * len(hr_dept_ids))
        dept_conditions.append(f"C.fk_DeptEmpid IN ({hr_placeholders})")
        params.extend(hr_dept_ids)

    if dept_conditions:
        alloc_filter += f" AND ({' OR '.join(dept_conditions)})"

    if exam_category == '1': # Regular/Back
        alloc_filter += " AND ISNULL(A.IsSummer, 0) = 0 AND ISNULL(A.IsSupplementary, 0) = 0 AND ISNULL(A.Is_Igrade, 0) = 0"
    elif exam_category == '2': # Supp
        alloc_filter += " AND A.IsSupplementary = 1"
    elif exam_category == '3': # Summer
        alloc_filter += " AND A.IsSummer = 1"
    elif exam_category == '4': # Igrade
        alloc_filter += " AND A.Is_Igrade = 1"

    exam_filter = "E.isinternal = 1" if exam_type == '1' else "(E.isinternal = 0 OR E.exam LIKE '%External%')"

    query = f'''
        SELECT C.pk_courseid as id, C.coursecode + ' || ' + C.coursename as name,
               C.crhr_theory, C.crhr_practical,
               COUNT(DISTINCT A.fk_sturegid) as student_count,
               MIN(CAST(ISNULL(D.islockedbyHOD, 0) AS INT)) as is_approved,
               Y.degreeyear_char as year_name,
               SM.semester_roman as semester_name,
               SM.pk_semesterid as semester_id,
               Y.pk_degreeyearid as degreeyear_id
        FROM SMS_StuCourseAllocation A
        INNER JOIN SMS_Course_Mst C ON A.fk_courseid = C.pk_courseid
        INNER JOIN SMS_DegreeCycle_Mst DC ON A.fk_degreecycleid = DC.pk_degreecycleid      
        INNER JOIN SMS_Student_Mst S ON A.fk_sturegid = S.pk_sid
        INNER JOIN SMS_DegreeYear_Mst Y ON DC.fk_degreeyearid = Y.pk_degreeyearid
        INNER JOIN SMS_Semester_Mst SM ON DC.fk_semesterid = SM.pk_semesterid
        INNER JOIN SMS_StuExamMarks_Dtl D ON A.Pk_stucourseallocid = D.fk_stucourseallocid 
        INNER JOIN SMS_DgExam_Mst M ON D.fk_dgexammapid = M.pk_dgexammapid
        INNER JOIN SMS_Exam_Mst E ON M.fk_examid = E.pk_examid
        WHERE {alloc_filter}
        AND D.islocked = 1
        AND {exam_filter}
        GROUP BY C.pk_courseid, C.coursecode, C.coursename, C.crhr_theory, C.crhr_practical, Y.degreeyear_char, SM.semester_roman, SM.pk_semesterid, Y.pk_degreeyearid
        ORDER BY C.coursecode, Y.degreeyear_char, SM.semester_roman
    '''

    courses = DB.fetch_all(query, params)

    pending = []
    approved = []

    sess_row = DB.fetch_one("SELECT sessionname FROM SMS_AcademicSession_Mst WHERE pk_sessionid = ?", [session_id])
    sess_name = sess_row['sessionname'] if sess_row else ''

    for c in courses:
        cat_str = 'Regular/Back Exam' if exam_category == '1' else ('Supplementary Exam' if exam_category == '2' else ('Summer Exam' if exam_category == '3' else 'Igrade Exam'))     
        c['category'] = cat_str
        c['session_name'] = sess_name
        # c['semester_name'] is directly fetched from the DB
        # c['year_name'] is directly fetched from the DB
        if c['is_approved'] == 1:
            approved.append(c)
        else:
            pending.append(c)

    return jsonify({'pending': pending, 'approved': approved})
