from flask import render_template, request, session, redirect, url_for, jsonify, flash
from app.blueprints.examination import examination_bp, permission_required
from app.models.academics import AcademicsModel
from app.models.academics import InfrastructureModel
from app.db import DB

@examination_bp.route('/marks_process_ug_mba', methods=['GET', 'POST'])
@permission_required('Marks Process for UG and MBA')
def marks_process_ug_mba():
    loc_id = session.get('selected_loc', '')
    lookups = {
        'colleges': DB.fetch_all("SELECT pk_collegeid as id, collegename + ' (' + ISNULL(collegecode, '') + ')' as name FROM SMS_College_Mst WHERE fk_locid = ?", [loc_id]),
        'sessions': InfrastructureModel.get_sessions(),
        'classes': DB.fetch_all("SELECT pk_semesterid as id, semester_roman as name FROM SMS_Semester_Mst WHERE semesterorder <= 8 ORDER BY semesterorder"),
        'years': DB.fetch_all("SELECT pk_degreeyearid as id, degreeyear_char as name FROM SMS_DegreeYear_Mst ORDER BY dgyearorder")
    }

    filters = {
        'college_id': request.args.get('college_id') or request.form.get('college_id', ''),
        'session_id': request.args.get('session_id') or request.form.get('session_id', ''),
        'degree_id': request.args.get('degree_id') or request.form.get('degree_id', ''),
        'class_id': request.args.get('class_id') or request.form.get('class_id', ''),
        'branch_id': request.args.get('branch_id') or request.form.get('branch_id', ''),
        'year_id': request.args.get('year_id') or request.form.get('year_id', ''),
        'exam_config_id': request.args.get('exam_config_id') or request.form.get('exam_config_id', ''),
        'exam_type': request.args.get('exam_type') or request.form.get('exam_type', '1') # 1: Regular/Back, 2: ReEvaluation, 3: Revised
    }

    students = []
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'GET_STUDENTS':
            if all([filters['college_id'], filters['session_id'], filters['degree_id'], filters['class_id'], filters['year_id']]):
                query = """
                    SELECT DISTINCT S.pk_sid, S.fullname, S.enrollmentno, S.AdmissionNo
                    FROM SMS_Student_Mst S
                    INNER JOIN SMS_StuCourseAllocation A ON S.pk_sid = A.fk_sturegid
                    INNER JOIN SMS_DegreeCycle_Mst DC ON A.fk_degreecycleid = DC.pk_degreecycleid
                    INNER JOIN SMS_StuExamMarks_Cld CLD ON A.Pk_stucourseallocid = CLD.fk_stucourseallocid
                    WHERE S.fk_collegeid = ? AND A.fk_dgacasessionid = ? AND DC.fk_degreeid = ? 
                      AND DC.fk_semesterid = ? AND DC.fk_degreeyearid = ?
                      AND ISNULL(A.IsSummer, 0) = 0 AND ISNULL(A.IsSupplementary, 0) = 0
                """
                params = [filters['college_id'], filters['session_id'], filters['degree_id'], filters['class_id'], filters['year_id']]
                
                if filters['branch_id']:
                    query += " AND DC.fk_branchid = ?"
                    params.append(filters['branch_id'])
                    
                query += " ORDER BY S.fullname, S.enrollmentno"
                
                rows = DB.fetch_all(query, params)
                fail_count = 0
                
                for r in rows:
                    # Check actual failure from allocation table
                    fail_check = DB.fetch_one("""
                        SELECT COUNT(*) as c
                        FROM SMS_StuCourseAllocation A
                        INNER JOIN SMS_DegreeCycle_Mst DC ON A.fk_degreecycleid = DC.pk_degreecycleid
                        INNER JOIN SMS_StuExamMarks_Cld CLD ON A.Pk_stucourseallocid = CLD.fk_stucourseallocid
                        WHERE A.fk_sturegid = ? AND A.fk_dgacasessionid = ? AND DC.fk_degreeid = ? AND DC.fk_semesterid = ? AND CLD.ispassed = 0
                    """, [r['pk_sid'], filters['session_id'], filters['degree_id'], filters['class_id']])
                    
                    is_fail = fail_check['c'] > 0 if fail_check else False
                    
                    if is_fail:
                        fail_count += 1

                    students.append({
                        'id': r['pk_sid'],
                        'name': f"{r['fullname']}|{r['enrollmentno']}",
                        'last_process_date': '', # Placeholder
                        'is_fail': is_fail
                    })
                
                filters['total_students'] = len(students)
                filters['fail_students'] = fail_count
                    
        elif action == 'PROCESS':
            student_ids = request.form.getlist('chk_student[]')
            if not student_ids:
                flash("Please select at least one student to process marks.", "danger")
            else:
                user_id = session.get('user_id')
                session_id = filters['session_id']
                count = 0
                for sid in student_ids:
                    # 1. Fetch allocated courses for this student in this session
                    courses = DB.fetch_all('''
                        SELECT A.Pk_stucourseallocid, C.crhr_theory, C.crhr_practical, ISNULL(C.isNC, 0) as isNC
                        FROM SMS_StuCourseAllocation A
                        INNER JOIN SMS_Course_Mst C ON A.fk_courseid = C.pk_courseid
                        WHERE A.fk_sturegid = ? AND A.fk_dgacasessionid = ?
                    ''', [sid, session_id])
                    
                    if not courses:
                        continue
                        
                    alloc_ids = [str(c['Pk_stucourseallocid']) for c in courses]
                    placeholders = ','.join(['?'] * len(alloc_ids))
                    
                    # 2. Fetch marks
                    marks = DB.fetch_all(f'''
                        SELECT D.fk_stucourseallocid, D.marks_obt, D.maxmarks, E.pk_examid
                        FROM SMS_StuExamMarks_Dtl D
                        INNER JOIN SMS_DgExam_Mst DEM ON D.fk_dgexammapid = DEM.pk_dgexammapid
                        INNER JOIN SMS_Exam_Mst E ON DEM.fk_examid = E.pk_examid
                        WHERE D.fk_stucourseallocid IN ({placeholders})
                    ''', alloc_ids)
                    
                    marks_dict = {}
                    for m in marks:
                        aid = m['fk_stucourseallocid']
                        if aid not in marks_dict:
                            marks_dict[aid] = {}
                        marks_dict[aid][m['pk_examid']] = {
                            'val': float(m['marks_obt']) if m['marks_obt'] is not None else 0.0,
                            'max': float(m['maxmarks']) if m['maxmarks'] is not None else 0.0
                        }

                    total_cp = 0.0
                    total_cr = 0.0
                    
                    # 3. Process each course
                    for c in courses:
                        aid = c['Pk_stucourseallocid']
                        m_data = marks_dict.get(aid, {})
                        
                        ith = m_data.get(1) or m_data.get(14) or m_data.get(18) or m_data.get(13) or {'val':0.0, 'max':0.0}
                        ipr = m_data.get(2) or m_data.get(16) or {'val':0.0, 'max':0.0}
                        eth = m_data.get(3) or m_data.get(15) or {'val':0.0, 'max':0.0}
                        epr = m_data.get(7) or {'val':0.0, 'max':0.0}
                        
                        crhr_th = float(c['crhr_theory'] or 0)
                        crhr_pr = float(c['crhr_practical'] or 0)
                        is_nc = c['isNC']
                        
                        total_obt = ith['val'] + ipr['val'] + eth['val'] + epr['val']
                        total_max = ith['max'] + ipr['max'] + eth['max'] + epr['max']
                        
                        # Rule A: 10-Point Scale
                        gp = (total_obt / total_max * 10.0) if total_max > 0 else 0.0
                        cp = gp * (crhr_th + crhr_pr)
                        
                        # Rule B: 50% Component Passing
                        th_fail = False
                        if ith['max'] > 0 and (ith['val'] / ith['max']) < 0.5: th_fail = True
                        if eth['max'] > 0 and (eth['val'] / eth['max']) < 0.5: th_fail = True
                        
                        pr_fail = False
                        if ipr['max'] > 0 and (ipr['val'] / ipr['max']) < 0.5: pr_fail = True
                        if epr['max'] > 0 and (epr['val'] / epr['max']) < 0.5: pr_fail = True
                        
                        # If a component doesn't exist (max=0), it doesn't fail the student.
                        is_passed = not (th_fail or pr_fail)
                        
                        th_pf = 'F' if th_fail else 'P'
                        pr_pf = 'F' if pr_fail else 'P'
                        
                        # Update SMS_StuExamMarks_Cld
                        cld_exists = DB.fetch_one("SELECT ID FROM SMS_StuExamMarks_Cld WHERE fk_stucourseallocid = ?", [aid])
                        if cld_exists:
                            DB.execute('''
                                UPDATE SMS_StuExamMarks_Cld 
                                SET gp = ?, CP = ?, ispassed = ?, ThPassFail = ?, PrPassFail = ?, 
                                    ith = ?, ith_max = ?, ipr = ?, ipr_max = ?, 
                                    eth = ?, eth_max = ?, epr = ?, epr_max = ?
                                WHERE fk_stucourseallocid = ?
                            ''', [gp, cp, 1 if is_passed else 0, th_pf, pr_pf, 
                                  ith['val'], ith['max'], ipr['val'], ipr['max'],
                                  eth['val'], eth['max'], epr['val'], epr['max'], aid])
                        else:
                            DB.execute('''
                                INSERT INTO SMS_StuExamMarks_Cld 
                                (fk_stucourseallocid, gp, CP, ispassed, ThPassFail, PrPassFail,
                                 ith, ith_max, ipr, ipr_max, eth, eth_max, epr, epr_max)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ''', [aid, gp, cp, 1 if is_passed else 0, th_pf, pr_pf,
                                  ith['val'], ith['max'], ipr['val'], ipr['max'],
                                  eth['val'], eth['max'], epr['val'], epr['max']])
                                  
                        # Update SMS_StuCourseAllocation
                        DB.execute("UPDATE SMS_StuCourseAllocation SET ispassed = ?, isbacklog = ? WHERE Pk_stucourseallocid = ?", [1 if is_passed else 0, 0 if is_passed else 1, aid])
                        
                        # Rule C: NC courses do not accumulate into main GPA
                        if not is_nc:
                            total_cp += cp
                            total_cr += (crhr_th + crhr_pr)
                            
                    # Rule D: GPA Calculation
                    gpa = (total_cp / total_cr) if total_cr > 0 else 0.0
                    
                    for c in courses:
                        DB.execute("UPDATE SMS_StuExamMarks_Cld SET gpa = ? WHERE fk_stucourseallocid = ?", [gpa, c['Pk_stucourseallocid']])
                    
                    count += 1

                flash(f"Marks successfully processed for {count} student(s). GP, CP, and Pass/Fail constraints applied.", "success")
                
            return redirect(url_for('examination.marks_process_ug_mba', **filters))

    return render_template('examination/marks_process_ug_mba.html', lookups=lookups, filters=filters, students=students)


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
        INNER JOIN SMS_DegreeCycle_Mst DC ON A.fk_degreecycleid = DC.pk_degreecycleid
        WHERE A.fk_sturegid = ? AND A.fk_dgacasessionid = ? AND DC.fk_semesterid = ?
    '''
    courses = DB.fetch_all(query, [student_id, session_id, semester_id])
    
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
            if m_obj and m_obj.get('absent'):
                return "A"
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
            'gp': f"{float(gp):.3f}" if gp is not None and str(gp).strip() != '' else '', 
            'cp': f"{float(cp):.2f}" if cp is not None and str(cp).strip() != '' else '',
            'gpa': f"{float(gpa):.3f}" if gpa is not None and str(gpa).strip() != '' else '',
            'ogpa': f"{float(ogpa):.3f}" if ogpa is not None and str(ogpa).strip() != '' else '0.000',
            'passed': passed_str
        })
    return jsonify(result)


@examination_bp.route('/api/get_college_ug_mba_degrees')
def get_college_ug_mba_degrees():
    college_id = request.args.get('college_id')
    if not college_id:
        return jsonify([])
    query = '''
        SELECT DISTINCT D.pk_degreeid as id, D.degreename as name
        FROM SMS_CollegeDegreeBranchMap_Mst M
        INNER JOIN SMS_Degree_Mst D ON M.fk_degreeid = D.pk_degreeid
        WHERE M.fk_collegeid = ? AND (D.fk_degreetypeid IN (1, 3, 5) OR D.degreename LIKE '%MBA%' OR D.degreename LIKE '%M.B.A%')
        ORDER BY D.degreename
    '''
    degrees = DB.fetch_all(query, [college_id])
    from app.utils import clean_json_data
    return jsonify(clean_json_data(degrees))
