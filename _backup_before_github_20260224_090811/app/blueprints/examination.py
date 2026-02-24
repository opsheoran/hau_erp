from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from app.db import DB
from functools import wraps
from app.utils import get_page_url
from app.models import ExaminationModel, NavModel

examination_bp = Blueprint('examination', __name__)

@examination_bp.before_request
def ensure_module():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    session['current_module_id'] = 56

def permission_required(page_caption):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            perm = NavModel.check_permission(session['user_id'], session.get('selected_loc'), page_caption)
            if not perm or not perm.get('AllowView'):
                return redirect(url_for('main.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# --- EXAMINATION MODULE MENU CONFIGURATION ---
# Structure: Main Menu -> Sub Group -> Sub-Menu Name -> [Pages]
EXAMINATION_MENU_CONFIG = {
    'Examination Masters & Config': {
        'Config': {
            'Master and Configuration Management': [
                'Exam Master', 'Degree Exam Master', 'Degree Exam Wise Weightage',
                'Exam Config Master', 'External Examiner Detail', 'External Examiner Communication',
                'Update Weightage Post Marks Entry'
            ]
        }
    },
    'Marks Entries': {
        'Marks': {
            'Student Marks Entry(@COE)': [
                'Student Marks Entry(@COE)', 'Student Marks Entry(UG and MBA)', 
                'Student Marks Entry(ExternalUser)', 'Teacher Assigned Courses for Student Marks Entry(PG/PHD)',
                'Student Marks Entry(PG/PHD) By Teacher', 'Student Marks Entry(Re-Evaluation)',
                'Student Marks Entry (Supplementary)', 'Student Marks Entry(Revised)',
                'Student Marks Entry(Igrade)', 'Student Marks Entry(Revised PG/PHD)',
                'Student Marks Entry PG/PhD Summer', 'Student Grading (NCC/NSS)'
            ]
        }
    },
    'Post Examination Activities': {
        'Activities': {
            'Marks Entry Approval': [
                'HOD Marks Approval', 'COE Marks Approval', 'Registrar Approval',
                'DeanPGS Marks Approval', 'DeanPGS Approval'
            ],
            'Marks Process': [
                'Marks Process for UG and MBA', 'Marks Process for PG',
                'Marks Process for Summer', 'Marks Process for Supplementary'
            ],
            'Others': [
                'Grace Marks', 'RollNumber Encryption', 'Print Result Report',
                'Encrypted Roll Number Report', 'Grace Marks(Supplementary/Summer)',
                'Rechecking Status'
            ]
        }
    },
    'Results & Grade Reports': {
        'Reports': {
            'Marks Entry Status': [
                'Marks Entry Status for UG and MBA', 'Marks Entry Status For PG/PHD',
                'Marks Entry Status for Supplementary/Summer'
            ],
            'Results': [
                'Student Result for UG', 'Student Result for Supplementary',
                'Student Result for PG and MBA', 'Student Result for Summer'
            ],
            'Others': [
                'Consolidate Results', 'DMC & Notification Report', 
                'Print Degree Certificates for UG', 'Print Degree Certificates for PG',
                'Weightage Consolidate Report', 'College/Subject Wise Topper List',
                'Student Certificate Report', 'Revised & ReChecking Old_New Marks Report',
                'UMC Report'
            ]
        }
    }
}

@examination_bp.app_context_processor
def inject_examination_navigation():
    if 'user_id' not in session or str(session.get('current_module_id')) != '56':
        return dict(exam_tabs=[], exam_breadcrumb=[])

    rights = session.get('current_user_rights', [])
    allowed_pages = {r['PageName'] for r in rights if r['AllowView']}
    curr_path = request.path.rstrip('/').lower()
    
    exam_tabs = []
    exam_breadcrumb = []

    # Detect position in 4-tier structure
    for main_cat, subs in EXAMINATION_MENU_CONFIG.items():
        for sub_cat, sub_subs in subs.items():
            for folder_name, pages in sub_subs.items():
                if not pages: continue
                
                is_active_group = False
                tab_list = []
                for p_name in pages:
                    # if p_name not in allowed_pages: continue 
                    p_url = get_page_url(p_name).rstrip('/')
                    active = (curr_path == p_url.lower())
                    tab_list.append({'name': p_name, 'url': p_url, 'active': active})
                    if active:
                        is_active_group = True
                        exam_breadcrumb = [main_cat, folder_name, p_name]
                
                if is_active_group:
                    exam_tabs = tab_list
                    break
            if exam_tabs: break
        if exam_tabs: break

    return dict(exam_tabs=exam_tabs, exam_breadcrumb=exam_breadcrumb)


@examination_bp.route('/exam_generic/<page_name>')
def generic_page_handler(page_name):
    return render_template('examination/generic_page.html', title=page_name)

@examination_bp.route('/exam_master', methods=['GET', 'POST'])
@permission_required('Exam Master')
def exam_master():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'DELETE':
            if ExaminationModel.delete_exam(request.form.get('id')):
                flash('Exam deleted successfully!', 'success')
            else:
                flash('Error deleting exam.', 'danger')
        else:
            if ExaminationModel.save_exam(request.form):
                flash('Exam saved successfully!', 'success')
            else:
                flash('Error saving exam.', 'danger')
        return redirect(url_for('examination.exam_master'))
    
    exams = ExaminationModel.get_exams()
    return render_template('examination/exam_master.html', exams=exams)

@examination_bp.route('/marks_entry_ug', methods=['GET', 'POST'])
@permission_required('Student Marks Entry(UG and MBA)')
def marks_entry_ug():
    from app.models import AcademicsModel, InfrastructureModel, CourseModel
    if request.method == 'POST' and 'alloc_id[]' in request.form:
        if ExaminationModel.save_marks(request.form, session['user_id']):
            flash('Marks saved successfully!', 'success')
        else:
            flash('Error saving marks.', 'danger')
        return redirect(url_for('examination.marks_entry_ug', **request.args))

    # Filters from URL
    filters = {
        'session_id': request.args.get('session_id'),
        'degree_id': request.args.get('degree_id'),
        'semester_id': request.args.get('semester_id'),
        'branch_id': request.args.get('branch_id'),
        'course_id': request.args.get('course_id'),
        'exam_id': request.args.get('exam_id')
    }

    data = None
    if all([filters['session_id'], filters['degree_id'], filters['semester_id'], filters['course_id'], filters['exam_id']]):
        data = ExaminationModel.get_students_for_marks_entry(filters)
        if not data:
            flash('No exam configuration found for this degree and exam type.', 'warning')

    lookups = {
        'sessions': InfrastructureModel.get_sessions(),
        'degrees': AcademicsModel.get_all_degrees(),
        'semesters': InfrastructureModel.get_all_semesters(),
        'branches': AcademicsModel.get_branches(),
        'courses': CourseModel.get_all_courses(),
        'exams': ExaminationModel.get_exams()
    }

    return render_template('examination/marks_entry_ug.html', 
                           lookups=lookups, filters=filters, data=data)
