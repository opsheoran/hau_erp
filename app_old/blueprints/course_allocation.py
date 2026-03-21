from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
from app.db import DB
from app.models import AcademicsModel, InfrastructureModel, CourseAllocationModel, StudentModel, NavModel
from app.utils import clean_json_data
from functools import wraps

course_allocation_bp = Blueprint('course_allocation', __name__)

@course_allocation_bp.before_request
def ensure_module():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    session['current_module_id'] = 55

def permission_required(page_caption):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('auth.login'))
            perm = NavModel.check_permission(session['user_id'], session.get('selected_loc'), page_caption)
            if not perm or not perm.get('AllowView'):
                return redirect(url_for('main.index'))
            if request.method == 'POST':
                action = (request.form.get('action') or '').strip().upper()
                write_actions = {
                    'SAVE', 'SUBMIT', 'ADD', 'CREATE', 'INSERT', 'UPDATE', 'EDIT',
                    'DELETE', 'REMOVE', 'DEALLOCATE', 'ALLOCATE', 'PROCESS', 'UNPROCESS', 'CANCEL'
                }
                if action in write_actions:
                    if action in {'DELETE', 'REMOVE'} and not perm.get('AllowDelete'):
                        flash('You do not have Delete permission for this page.', 'danger')
                        return redirect(url_for('main.index'))
                    if action in {'ADD', 'CREATE', 'INSERT'} and not perm.get('AllowAdd'):
                        flash('You do not have Add permission for this page.', 'danger')
                        return redirect(url_for('main.index'))
                    if action in {'SAVE', 'SUBMIT', 'UPDATE', 'EDIT', 'DEALLOCATE', 'ALLOCATE', 'PROCESS', 'UNPROCESS', 'CANCEL'} and not (perm.get('AllowAdd') or perm.get('AllowUpdate')):
                        flash('You do not have permission to perform this action.', 'danger')
                        return redirect(url_for('main.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@course_allocation_bp.route('/course_allocation_ug_regular', methods=['GET', 'POST'])
@permission_required('Course Allocation For UG[Reguler]')
def course_allocation_ug_regular():
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'SAVE':
            filters = {
                'college_id': request.form.get('college_id'),
                'session_id': request.form.get('session_id'),
                'degree_id': request.form.get('degree_id'),
                'branch_id': request.form.get('branch_id'),
                'semester_id': request.form.get('semester_id'),
                'year': request.form.get('year'),
                'exconfig_id': request.form.get('exconfig_id')
            }
            
            # student_ids is list of selected students
            # course_ids is list of selected courses
            student_ids = request.form.getlist('student_ids')
            course_ids = request.form.getlist('course_ids')
            
            if not student_ids or not course_ids:
                flash('Please select at least one student and one course.', 'warning')
            else:
                user_id = session.get('user_id')
                success, msg = CourseAllocationModel.save_ug_regular_allocation(filters, student_ids, course_ids, user_id)
                if success:
                    flash(msg, 'success')
                else:
                    flash(msg, 'danger')

            filters['fetch'] = '1'
            return redirect(url_for('course_allocation.course_allocation_ug_regular', **filters))
            
        elif action == 'DEALLOCATE':
            # Logic for deallocation (unprocess)
            sid = request.form.get('deallocate_sid')
            exconfig_id = request.form.get('exconfig_id')
            if sid and exconfig_id:
                user_id = session.get('user_id')
                if CourseAllocationModel.deallocate_student_courses(sid, exconfig_id, user_id):
                    flash('Student courses deallocated successfully.', 'success')
                else:
                    flash('Error deallocating courses.', 'danger')

            redirect_filters = {
                'college_id': request.form.get('college_id'),
                'session_id': request.form.get('session_id'),
                'degree_id': request.form.get('degree_id'),
                'branch_id': request.form.get('branch_id'),
                'semester_id': request.form.get('semester_id'),
                'year': request.form.get('year'),
                'exconfig_id': request.form.get('exconfig_id'),
                'fetch': request.form.get('fetch') or '1',
            }
            return redirect(url_for('course_allocation.course_allocation_ug_regular', **redirect_filters))

    filters = {
        'college_id': request.values.get('college_id'),
        'session_id': request.values.get('session_id'),
        'degree_id': request.values.get('degree_id'),
        'branch_id': request.values.get('branch_id'),
        'semester_id': request.values.get('semester_id'),
        'year': request.values.get('year'),
        'exconfig_id': request.values.get('exconfig_id'),
        'fetch': request.values.get('fetch')
    }

    # Match live behavior: Year is derived from selected Class(Semester)
    if filters.get('semester_id'):
        year_row = DB.fetch_one("SELECT fk_degreeyearid FROM SMS_Semester_Mst WHERE pk_semesterid = ?", [filters['semester_id']])
        if year_row and year_row.get('fk_degreeyearid'):
            filters['year'] = str(year_row['fk_degreeyearid'])

    students = []
    courses = []
    allocated_students = []
    
    # Load students and courses only if mandatory filters are present
    if all([filters['college_id'], filters['session_id'], filters['degree_id'], filters['semester_id']]):
        # Get pending students (not yet fully allocated or all eligible?)
        # Live site "GET STUDENT" button fetches list.
        # Check fetch in values (supports POST persistence)
        if request.values.get('fetch') == '1':
            students = CourseAllocationModel.get_students_for_allocation(filters)
            courses = CourseAllocationModel.get_courses_for_allocation(filters)
        
        # Always fetch already allocated list
        allocated_students = CourseAllocationModel.get_allocated_students(filters)

    loc_id = session.get('selected_loc')
    if loc_id:
        colleges = DB.fetch_all(
            "SELECT pk_collegeid as id, collegename + ' (' + ISNULL(collegecode, '') + ')' as name FROM SMS_College_Mst WHERE fk_locid = ? ORDER BY collegename",
            [loc_id],
        )
    else:
        colleges = DB.fetch_all("SELECT pk_collegeid as id, collegename + ' (' + ISNULL(collegecode, '') + ')' as name FROM SMS_College_Mst ORDER BY collegename")

    all_semesters = InfrastructureModel.get_all_semesters()
    semesters = [s for s in all_semesters if s.get('semesterorder', 0) <= 8]

    years = AcademicsModel.get_degree_years()
    if filters.get('year'):
        years = [y for y in years if str(y.get('pk_degreeyearid')) == str(filters['year'])]

    lookups = {
        'colleges': colleges,
        'sessions': InfrastructureModel.get_sessions(),
        'degrees': AcademicsModel.get_college_all_degrees(filters['college_id']) if filters['college_id'] else [],
        'semesters': semesters,
        'branches': AcademicsModel.get_college_degree_specializations(filters['college_id'], filters['degree_id']) if (filters['college_id'] and filters['degree_id']) else [],
        'years': years,
        'exam_configs': CourseAllocationModel.get_exam_configs(filters['degree_id'], filters['session_id'], filters['semester_id']) if filters['degree_id'] else []
    }

    return render_template('academics/course_allocation_ug_regular.html', 
                           lookups=lookups, 
                           filters=filters, 
                           students=clean_json_data(students), 
                           courses=clean_json_data(courses),
                           allocated_students=clean_json_data(allocated_students))
