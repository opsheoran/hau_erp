import re

with open('app/blueprints/student_portal/course_add_withdrawal.py', 'r', encoding='utf-8') as f:
    code = f.read()

logic = """    # Calculate current credits
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
                           max_cr=max_cr)"""

code = re.sub(r"    return render_template\('student_portal/course_addition_withdrawal\.html'.*?history=history\)", logic, code, flags=re.DOTALL)

with open('app/blueprints/student_portal/course_add_withdrawal.py', 'w', encoding='utf-8') as f:
    f.write(code)

print('Updated python variables for template.')
