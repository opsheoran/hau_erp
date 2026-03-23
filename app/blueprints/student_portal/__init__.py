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
from app.blueprints.student_portal import course_plan
from app.blueprints.student_portal import course_details
from app.blueprints.student_portal import faculty_details
from app.blueprints.student_portal import results
from app.blueprints.student_portal import igrade
from app.blueprints.student_portal import supplementary
from app.blueprints.student_portal import fee_details
from app.blueprints.student_portal import notifications
from app.blueprints.student_portal import question_papers
from app.blueprints.student_portal import certificate_request
from app.blueprints.student_portal import online_fee_payment
from app.blueprints.student_portal import change_password
from app.blueprints.student_portal import attendance
