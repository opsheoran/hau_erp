from flask import render_template, request, session, redirect, url_for, flash, jsonify
from app.blueprints.student_portal import student_portal_bp, student_login_required
from app.db import DB
from datetime import datetime

@student_portal_bp.route('/course_addition_withdrawal', methods=['GET', 'POST'])
@student_login_required
def course_addition_withdrawal():
    student_id = session.get('student_id')
    
    # Get student info
    student = DB.fetch_one("""
        SELECT S.fullname, S.enrollmentno, 
               D.degreename, B.branchname, SM.semester_roman, S.fk_curr_session,
               S.fk_collegeid, S.fk_degreeid, DC.fk_semesterid, S.fk_branchid,
               S.CardEntrySubmit
        FROM SMS_Student_Mst S
        LEFT JOIN SMS_DegreeCycle_Mst DC ON S.fk_degreecycleidcurrent = DC.pk_degreecycleid
        LEFT JOIN SMS_Degree_Mst D ON S.fk_degreeid = D.pk_degreeid
        LEFT JOIN SMS_BranchMst B ON S.fk_branchid = B.pk_branchid
        LEFT JOIN SMS_Semester_Mst SM ON DC.fk_semesterid = SM.pk_semesterid
        WHERE S.pk_sid = ?
    """, [student_id])

    if not student:
        flash('Student details not found.', 'danger')
        return redirect(url_for('student_portal.dashboard'))
        
    curr_session = student['fk_curr_session']
    
    # Handle API request for dropdown population
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        action_type = request.form.get('action_type')
        
        # Fetch current allocations
        allocations = DB.fetch_all('''
            SELECT A.Pk_stucourseallocid, A.fk_courseid, C.coursecode, C.coursename, 
                   C.crhr_theory, C.crhr_practical, A.crhrth1, A.crhrpr1
            FROM SMS_StuCourseAllocation A
            INNER JOIN SMS_Course_Mst C ON A.fk_courseid = C.pk_courseid
            WHERE A.fk_sturegid = ? AND A.fk_dgacasessionid = ? AND A.fk_degreecycleid_alloc = (
                SELECT fk_degreecycleidcurrent FROM SMS_Student_Mst WHERE pk_sid = ?
            )
        ''', [student_id, curr_session, student_id])
        
        alloc_map = {a['fk_courseid']: a for a in allocations}
        
        if action_type == 'W':  # Withdrawal
            # Return current allocations that can be withdrawn
            withdrawable = []
            for a in allocations:
                cr_th = a['crhrth1'] if a.get('crhrth1') is not None else a['crhr_theory']
                cr_pr = a['crhrpr1'] if a.get('crhrpr1') is not None else a['crhr_practical']
                withdrawable.append({
                    'id': a['fk_courseid'],
                    'text': f"{a['coursename']} [ {a['coursecode']} ] {{ {cr_th} + {cr_pr} }}"
                })
            return jsonify({'courses': withdrawable})
            
        elif action_type == 'A':  # Addition
            # --- DYNAMIC COLLEGE MAPPING BASED ON ADVISORY ---
            major_college = student['fk_collegeid']
            advisory = DB.fetch_all('''
                SELECT D.fk_statusid, D.fk_deptid
                FROM SMS_Advisory_Committee_Mst M
                INNER JOIN SMS_Advisory_Committee_Dtl D ON M.pk_adcid = D.fk_adcid
                WHERE M.fk_stid = ?
            ''', [student_id])

            minor_dept = next((a['fk_deptid'] for a in advisory if a['fk_statusid'] == 3), None)
            support_dept = next((a['fk_deptid'] for a in advisory if a['fk_statusid'] == 4), None)

            def get_dept_college(dept_id, degree_id):
                if not dept_id: return None
                branch = DB.fetch_one('SELECT Pk_BranchId FROM SMS_BranchMst WHERE fk_deptidDdo = ?', [dept_id])
                if branch:
                    col = DB.fetch_one('''
                        SELECT TOP 1 M.fk_CollegeId 
                        FROM SMS_CollegeDegreeBranchMap_dtl D
                        INNER JOIN SMS_CollegeDegreeBranchMap_Mst M ON D.fk_Coldgbrmapid = M.PK_Coldgbrid
                        WHERE D.fk_branchid = ? AND M.fk_Degreeid = ?
                    ''', [branch['Pk_BranchId'], degree_id])
                    if col: return col['fk_CollegeId']
                return None

            minor_college = get_dept_college(minor_dept, student['fk_degreeid']) or major_college
            support_college = get_dept_college(support_dept, student['fk_degreeid']) or major_college

            pow_courses = DB.fetch_all('''
                SELECT SCA.pk_stucourseapprove, C.pk_courseid, C.coursecode, C.coursename, 
                       SCA.crhrth as master_th, SCA.crhrpr as master_pr,
                       SCA.courseplan, ISNULL(C.isNC, 0) as isNC
                FROM Sms_course_Approval SCA
                INNER JOIN SMS_Course_Mst C ON SCA.fk_courseid = C.pk_courseid
                WHERE SCA.fk_sturegid = ? AND SCA.courseplan != 'CP'
            ''', [student_id])

            addable = []
            for p in pow_courses:
                c_id = p['pk_courseid']
                
                # Cannot add if already allocated this semester
                if c_id in alloc_map:
                    continue
                    
                # Cannot add if already passed
                passed_check = DB.fetch_one("SELECT TOP 1 ispassed FROM SMS_StuCourseAllocation WHERE fk_sturegid = ? AND fk_courseid = ? AND ispassed = 1", [student_id, c_id])
                if passed_check:
                    continue

                cp = p['courseplan']
                target_college = major_college
                if cp == 'MI': target_college = minor_college
                elif cp == 'SU': target_college = support_college
                
                is_offered = DB.fetch_one('''
                    SELECT TOP 1 1 
                    FROM SMS_CourseAllocationSemesterwiseByHOD M
                    INNER JOIN SMS_CourseAllocationSemesterwiseByHOD_Dtl D ON M.Pk_courseallocid = D.fk_courseallocid
                    LEFT JOIN SMS_Course_Mst_Dtl CDTL ON D.fk_courseid = CDTL.fk_courseid AND CDTL.fk_degreeid = ?
                    WHERE M.fk_dgacasessionid = ? AND M.fk_collegeid = ? AND D.fk_courseid = ?
                      AND (CDTL.fk_semesterid % 2) = (? % 2)
                ''', [student['fk_degreeid'], curr_session, target_college, c_id, student['fk_semesterid']])
                
                if is_offered or 'Thesis' in p['coursecode']:
                    cr_th = p['master_th']
                    cr_pr = p['master_pr']
                    addable.append({
                        'id': c_id,
                        'text': f"{p['coursename']} [ {p['coursecode']} ] {{ {cr_th} + {cr_pr} }}"
                    })
            return jsonify({'courses': addable})

    # Standard form submission (Apply)
    if request.method == 'POST' and not request.headers.get('X-Requested-With'):
        action_type = request.form.get('change_type') # 'A' or 'W'
        course_id = request.form.get('course')
        reason = request.form.get('reason')
        crhr_th = request.form.get('crhr_th', 0)
        crhr_pr = request.form.get('crhr_pr', 0)
        
        if course_id and course_id != "0" and reason:
            # Insert into SMS_CourseAdditionWithdrawal_Mst
            DB.execute('''
                INSERT INTO SMS_CourseAdditionWithdrawal_Mst 
                (fk_courseid, fk_Stid, fk_sessionid, fk_semesterid, fk_degreeid, Addwith_type, DateOfApply, Approval, Reason, crhr_th, crhr_pr)
                VALUES (?, ?, ?, ?, ?, ?, GETDATE(), 0, ?, ?, ?)
            ''', [course_id, student_id, curr_session, student['fk_semesterid'], student['fk_degreeid'], 
                  'A ' if action_type == 'A' else 'W ', reason, crhr_th, crhr_pr])
            flash('Request submitted successfully!', 'success')
            return redirect(url_for('student_portal.course_addition_withdrawal'))
        else:
            flash('Please fill all required fields.', 'danger')

    # Fetch History for the Grid
    history = DB.fetch_all('''
        SELECT AW.Pk_AddWith, C.coursecode, C.coursename, C.crhr_theory, C.crhr_practical, 
               SESS.sessionname as Session, SM.semester_roman,
               AW.Addwith_type, AW.Approval, AW.Teach_approv, AW.dean_approv, AW.DateOfApply
        FROM SMS_CourseAdditionWithdrawal_Mst AW
        INNER JOIN SMS_Course_Mst C ON AW.fk_courseid = C.pk_courseid
        LEFT JOIN SMS_AcademicSession_Mst SESS ON AW.fk_sessionid = SESS.pk_sessionid
        LEFT JOIN SMS_Semester_Mst SM ON AW.fk_semesterid = SM.pk_semesterid
        WHERE AW.fk_Stid = ?
        ORDER BY AW.DateOfApply DESC
    ''', [student_id])

    # Calculate current credits
    allocations_for_credits = DB.fetch_all('''
        SELECT A.fk_courseid, C.isNC, C.crhr_theory, C.crhr_practical, A.crhrth1, A.crhrpr1
        FROM SMS_StuCourseAllocation A
        INNER JOIN SMS_Course_Mst C ON A.fk_courseid = C.pk_courseid
        WHERE A.fk_sturegid = ? AND A.fk_dgacasessionid = ? AND A.fk_degreecycleid_alloc = (
            SELECT fk_degreecycleidcurrent FROM SMS_Student_Mst WHERE pk_sid = ?
        )
    ''', [student_id, curr_session, student_id])
    
    total_current_credits = 0
    for a in allocations_for_credits:
        # Ignore non-credit for total sum unless specifically handled
        if not a['isNC']:
            th = a['crhrth1'] if a.get('crhrth1') is not None else a['crhr_theory']
            pr = a['crhrpr1'] if a.get('crhrpr1') is not None else a['crhr_practical']
            total_current_credits += (th or 0) + (pr or 0)
            
    # Find min/max credits for this degree
    credit_limits = DB.fetch_one('''
        SELECT mincrhr, maxcrhr 
        FROM SMS_Degreewise_crhr_Trn_CP
        WHERE fk_degreeid = ? AND fk_semesterid = ?
    ''', [student['fk_degreeid'], student['fk_semesterid']])
    
    min_cr = credit_limits['mincrhr'] if credit_limits else 9
    max_cr = credit_limits['maxcrhr'] if credit_limits else 22

    return render_template('student_portal/course_addition_withdrawal.html', 
                           student=student,
                           history=history,
                           total_current_credits=total_current_credits,
                           min_cr=min_cr,
                           max_cr=max_cr)
