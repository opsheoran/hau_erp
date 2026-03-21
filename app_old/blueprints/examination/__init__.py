from flask import Blueprint, render_template, request, session, redirect, url_for, flash

from app.utils import get_page_url

from app.models import NavModel

from functools import wraps



examination_bp = Blueprint('examination', __name__, template_folder='../../templates/examination')



@examination_bp.before_request

def ensure_module():

    if 'user_id' not in session:

        return redirect(url_for('auth.login'))

    session['current_module_id'] = 56



def permission_required(page_caption):

    def decorator(f):

        @wraps(f)

        def decorated_function(*args, **kwargs):

            perm = NavModel.check_permission(session.get('user_id'), session.get('selected_loc'), page_caption)

            if not perm or not perm.get('AllowView'):

                return redirect(url_for('main.index'))

            return f(*args, **kwargs)

        return decorated_function

    return decorator



# --- EXAMINATION MODULE MENU CONFIGURATION ---

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

                'DeanPGS Marks Approval'

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

        return dict(examination_tabs=[], examination_breadcrumb=[])



    rights = session.get('current_user_rights', [])

    allowed_pages = {r['PageName'] for r in rights if r['AllowView']}

    curr_path = request.path.rstrip('/').lower()

    

    examination_tabs = []

    examination_breadcrumb = []



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

                    

                    # Custom alias logic for background pages

                    is_current = (curr_path == p_url.lower())

                    if not is_current and p_name == 'COE Marks Approval' and 'coe_approval_form' in curr_path:

                        is_current = True

                    if not is_current and p_name == 'DeanPGS Marks Approval' and 'deanpgs_approval_form' in curr_path:

                        is_current = True

                        

                    active = is_current

                    tab_list.append({'name': p_name, 'url': p_url, 'active': active})

                    if active:

                        is_active_group = True

                        examination_breadcrumb = [main_cat, folder_name, p_name]

                

                if is_active_group:

                    examination_tabs = tab_list

                    break

            if examination_tabs: break

        if examination_tabs: break



    return dict(examination_tabs=examination_tabs, examination_breadcrumb=examination_breadcrumb)



@examination_bp.route('/exam_generic/<path:page_name>')

def generic_page_handler(page_name):

    return render_template('examination/generic_page.html', title=page_name)



# Import routes down here to avoid circular dependencies

from app.blueprints.examination import exam_master

from app.blueprints.examination import degree_exam_master

from app.blueprints.examination import exam_config_master

from app.blueprints.examination import degree_exam_wise_weightage

from app.blueprints.examination import external_examiner_detail

from app.blueprints.examination import update_weightage_post_marks_entry

from app.blueprints.examination import external_examiner_communication

from app.blueprints.examination import student_marks_entry_coe

from app.blueprints.examination import student_marks_entry_ug

from app.blueprints.examination import student_marks_entry_pg_phd

from app.blueprints.examination import student_marks_entry_re_evaluation

from app.blueprints.examination import student_marks_entry_supplementary

from app.blueprints.examination import student_marks_entry_external_user

from app.blueprints.examination import teacher_assigned_courses_pgphd

from app.blueprints.examination import student_marks_entry_revised

from app.blueprints.examination import student_marks_entry_igrade

from app.blueprints.examination import student_marks_entry_revised_pg_phd

from app.blueprints.examination import student_marks_entry_pg_phd_summer

from app.blueprints.examination import student_marks_entry_ncc_nss

from app.blueprints.examination import hod_marks_approval

from app.blueprints.examination import coe_marks_approval

from app.blueprints.examination import registrar_marks_approval

from app.blueprints.examination import deanpgs_marks_approval

from app.blueprints.examination import marks_process_ug_mba


from app.blueprints.examination import marks_process_pg_phd
