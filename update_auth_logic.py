import os

with open('app/blueprints/student_portal/auth.py', 'r', encoding='utf-8') as f:
    code = f.read()

new_logic = """
        # In this system, get_student_password fetches the plain text password (or decrypts it)
        plain_pass = StudentModel.get_student_password(username)
        
        # Fallback to checking DOB natively if no explicit password matches
        student_data = DB.fetch_one('''
            SELECT pk_sid, fullname, enrollmentno, AdmissionNo, photoimage, dob
            FROM SMS_Student_Mst 
            WHERE enrollmentno = ? OR AdmissionNo = ?
        ''', [username, username])

        is_authenticated = False
        
        if plain_pass and plain_pass == password:
            is_authenticated = True
        elif student_data and student_data.get('dob'):
            dob_val = student_data['dob']
            dob_str1 = dob_val.strftime('%d/%m/%Y')
            dob_str2 = dob_val.strftime('%d-%m-%Y')
            dob_str3 = dob_val.strftime('%Y-%m-%d')
            # The user requested DOB as default password
            if password in [dob_str1, dob_str2, dob_str3]:
                is_authenticated = True
                
        if is_authenticated and student_data:
            session['student_id'] = student_data['pk_sid']
            session['student_name'] = student_data['fullname']
            session['student_enrollment'] = student_data['enrollmentno']
            return redirect(url_for('student_portal.dashboard'))
        else:
            flash('Invalid Enrollment No. or Password.', 'danger')
"""

old_logic = """
        # In this system, get_student_password fetches the plain text password (or decrypts it)
        plain_pass = StudentModel.get_student_password(username)
        
        if plain_pass and plain_pass == password:
            # Login successful
            # Fetch basic student details to store in session
            student_data = DB.fetch_one(\"\"\"
                SELECT pk_sid, fullname, enrollmentno, AdmissionNo, photoimage 
                FROM SMS_Student_Mst 
                WHERE enrollmentno = ? OR AdmissionNo = ?
            \"\"\", [username, username])
            
            if student_data:
                session['student_id'] = student_data['pk_sid']
                session['student_name'] = student_data['fullname']
                session['student_enrollment'] = student_data['enrollmentno']
                return redirect(url_for('student_portal.dashboard'))
            else:
                flash('Student details not found.', 'danger')
        else:
            flash('Invalid Enrollment No. or Password.', 'danger')
"""

if old_logic.strip() in code:
    code = code.replace(old_logic.strip(), new_logic.strip())
    with open('app/blueprints/student_portal/auth.py', 'w', encoding='utf-8') as f:
        f.write(code)
    print('Updated authentication logic successfully')
else:
    print('Failed to find logic block')
