from flask import render_template, request, session, redirect, url_for, flash
from app.blueprints.student_portal import student_portal_bp
from app.models.academics import StudentModel
from app.db import DB
import datetime

@student_portal_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Please enter Enrollment No. and Password', 'danger')
            return redirect(url_for('student_portal.login'))

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
            # Carry over previous login time before overwriting
            prev_login = session.get('current_login', '')
            session['student_id']         = student_data['pk_sid']
            session['student_name']        = student_data['fullname']
            session['student_enrollment']  = student_data['enrollmentno']
            session['student_photo']       = student_data.get('photoimage') or ''
            session['last_login']          = prev_login
            session['current_login']       = datetime.datetime.now().strftime('%d-%b-%Y %I:%M %p')
            return redirect(url_for('student_portal.dashboard'))
        else:
            flash('Invalid Enrollment No. or Password.', 'danger')
            
    return render_template('login.html')

@student_portal_bp.route('/logout')
def logout():
    session.pop('student_id', None)
    session.pop('student_name', None)
    session.pop('student_enrollment', None)
    session.pop('student_photo', None)
    session.pop('last_login', None)
    session.pop('current_login', None)
    return redirect(url_for('student_portal.login'))
