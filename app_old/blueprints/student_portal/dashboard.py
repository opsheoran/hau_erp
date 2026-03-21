from flask import render_template, request, session, redirect, url_for, flash
from app.blueprints.student_portal import student_portal_bp, student_login_required
from app.db import DB

@student_portal_bp.route('/dashboard')
@student_login_required
def dashboard():
    return render_template('dashboard.html')
