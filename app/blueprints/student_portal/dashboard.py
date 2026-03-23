from flask import render_template, session
from app.blueprints.student_portal import student_portal_bp, student_login_required

@student_portal_bp.route('/dashboard')
@student_login_required
def dashboard():
    last_login = session.get('last_login', '')
    return render_template('student_portal/dashboard.html', last_login=last_login)
