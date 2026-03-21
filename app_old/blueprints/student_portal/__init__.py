from flask import Blueprint, render_template, request, session, redirect, url_for, flash

from functools import wraps



student_portal_bp = Blueprint('student_portal', __name__, template_folder='../../templates/student_portal', static_folder='../../static/student_portal')



def student_login_required(f):

    @wraps(f)

    def decorated_function(*args, **kwargs):

        if 'student_id' not in session:

            return redirect(url_for('student_portal.login'))

        return f(*args, **kwargs)

    return decorated_function



from app.blueprints.student_portal import auth

from app.blueprints.student_portal import dashboard

from app.blueprints.student_portal import profile

from app.blueprints.student_portal import card_entry

from app.blueprints.student_portal import course_add_withdrawal