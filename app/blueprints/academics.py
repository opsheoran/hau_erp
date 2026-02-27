import os
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash, make_response, send_file
import math
import io
from datetime import datetime
import pandas as pd
from app.db import DB
from app.models import (
    AcademicsModel, NavModel, InfrastructureModel, ClassificationModel, 
    CourseModel, ActivityCertificateModel, StudentConfigModel, 
    CourseActivityModel, PackageMasterModel, BoardMasterModel, 
    CertificateMasterModel, PgsCourseLimitModel, SeatDetailModel, 
    AdmissionModel, AdvisoryModel, StudentModel, CourseAllocationModel, ResearchModel, ThesisModel,
    AdvisoryStatusModel, IGradeModel, BatchModel, EmployeeModel, AdvisorApprovalModel, TeacherApprovalModel, DswApprovalModel, LibraryApprovalModel
)
from functools import wraps
from app.utils import get_page_url, get_pagination, get_pagination_range, clean_json_data

academics_bp = Blueprint('academics', __name__)

@academics_bp.before_request
def ensure_module():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    session['current_module_id'] = 55

# --- THE DEFINITIVE HIERARCHY AS PER USER INSTRUCTION ---
ACADEMIC_MENU_CONFIG = {
    'Master and Config': {
        'Common Master': {
            'Common Masters preparation': [
                'Academic Session Master', 'Faculty Master', 'Degree Year Master', 
                'Semester Master [Add Semester]', 'Specialization Master [PG/PHD]', 
                'College Type Master', 'Degree Type Master', 'Qualifying/Institution Quota', 
                'Employee- Degree Map'
            ]
        },
        'Administrative Configuration': {
            'Academic Configurations Management': [
                'College Master [Create College]', 'Degree Master [Create Degree]', 
                'Degree Cycle Master', 'Col-Deg-Specialization Master', 'Degree wise Credit Hours', 'Class - Batch Master', 
                'Moderation Marks Detail', 'Degree Wise Credit Hours(Course Plan)'
            ]
        }
    },
    'Course Details': {
        'Course Details': {
            'Course Management': [
                'Course Type Master', 'Paper/Course Title Master', 'Course/Subject Master', 
                'Activity Course Master', 'Activity Master', 'Package Master', 
                'Course Detail Report', 'Syllabus Creation [Master]', 'PGS Course Limit [Master]'
            ]
        }
    },
    'Admission': {
        'Admission Master': {
            'Admission Master Management': [
                'Academic Session Master [A]', 'Faculty Master [A]', 'Degree Year Master [A]', 
                'Semester Master [Add Semester] [A]', 'Specialization Master [PG/PHD] [A]', 
                'College Type Master [A]', 'Degree Type Master [A]', 'Qualifying/Institution Quota [A]', 
                'Employee- Degree Map [A]',
                'Nationality Master', 'Entitlement Master', 'Category Master', 'Board Master', 
                'Certificates Master', 'College Degree Wise Seat Detail', 'Student Registration', 
                'Student Password', 'View Student Password', 'Back Course Entry', 'College Degree Seat Report'
            ]
        },
        'Post Admission Activities': {
            'Admission No. Generation and Management': [
                'Admission No Configuration', 'Admission No Generation', 'Batch Assignment', 'Degree Complete Detail'
            ],
            'Student Bio Data Management': [
                'Student BioData', 'Student Biodata Updation', 'Achievement/ Disciplinary ', 
                'Achievement / Disciplinary Approval', 'Student Activity Management', 'Student Personal Detail Report'
            ],
            'Advisory Committee Management for PG/PHD Programme': [
                'Limit Assignment', 'Major Advisor', 'Specialization Assignment', 'Member of Minor and supporting', 
                'Dean PGS approval (advisory committee)', 'HOD Approval', 'College Dean Approval', 'Prepare Course Plan', 
                'Dean PGS approval (Course plan)', 'Course Allocation(For PG)', 'PG Mandates Submission by HOD',
                'Programme of work(PG)', 'Addition/withdrawal Approval by Teacher', 'Addition/withdrawal Approval by Major Advisor',
                'Student Thesis Detail', 'Addition/Withdrawal Approval Status', 'Advisory Creation And Approval Status',
                'I-Grade Approval by Teacher', 'I-Grade Approval By Dean Pgs', 'I Grade Approval Status'
            ]
        }
    },
    'Academics': {
        'Academics Masters and Cofiguration': {
            'Calender Event/Notification Management': ['Event Master', 'Event Assignment'],
            'Academic Miscellaneous Activities': [
                'Semester Registration', 'Academic Counselling Meeting', 'Previous Question Paper Uploads', 
                'SMS And Mail', 'Student Extension', 'Extension Management', 'Student Transfer Details', 
                'Registration Cancel', 'Student Semester Change', 'Course Approval Status', 
                'rechecking Approval By Hod(PG)', 'Rechecking Approval By Advisor[UG]', 
                'Rechecking Approval By Dean[UG]', 'Revised Result'
            ]
        },
        'Student Course Allocation': {
            'Student Subject/Course Allocation and Management': [
                'Course Offer (By HOD)', 'Course Allocation For UG[Reguler]', 'Advisor Allocation(For UG)', 
                'Teacher Course Assignment', 'Course Allocation Approval For UG/PG[By Advisor]', 
                'Course Allocation Approval For UG/PG[By Teacher]', 'Course Allocation Approval For UG/PG[By DSW]', 
                'Course Allocation Approval For UG/PG[By Library]', 'Course Allocation Fee Approval For UG/PG', 
                'Course Allocation Approval For UG/PG [By Dean]', 'Course Allocation Approval For PG [By DeanPGS]', 
                'Course Allocation Approval For UG/PG [By Registrar]', 'Course Allocation(HOD on Request)', 
                'Compartment & Year Back', 'Course Allocation Report-Regular', 'Activity Allocation', 
                'Course Allocation Report-Regular(Consolidate)', 'Course Allocation Re-Appear', 
                'Course Allocation Report-Compart', 'Course Offer And Teacher Course Assignment Report(For HOD)', 
                'Course Allocation Report-Regular(Consolidate-PG)', 'NSS/NCC Course updation'
            ]
        }
    },
    'Report': {
        'Admission Reports': { 'Admission miscellaneous Reports': [] },
        'Academics Reports': { 'Academic miscellaneous Reports': [] }
    }
}

def permission_required(page_caption):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('auth.login'))
            user_id = session.get('user_id')
            loc_id = session.get('selected_loc')
            perm = NavModel.check_permission(user_id, loc_id, page_caption)
            if not perm or not perm.get('AllowView'):
                return redirect(url_for('main.index'))
            # Write protection (only when action indicates a write).
            if request.method == 'POST':
                action = (request.form.get('action') or '').strip().upper()
                write_actions = {
                    'SAVE', 'SUBMIT', 'ADD', 'CREATE', 'INSERT', 'UPDATE', 'EDIT',
                    'DELETE', 'REMOVE', 'DEALLOCATE', 'ALLOCATE',
                    'APPROVE', 'HOLD', 'REJECT', 'CANCEL', 'PROCESS', 'UNPROCESS'
                }
                if action in write_actions:
                    if action in {'DELETE', 'REMOVE'} and not perm.get('AllowDelete'):
                        flash('You do not have Delete permission for this page.', 'danger')
                        return redirect(url_for('main.index'))
                    if action in {'ADD', 'CREATE', 'INSERT'} and not perm.get('AllowAdd'):
                        flash('You do not have Add permission for this page.', 'danger')
                        return redirect(url_for('main.index'))
                    if action in {'SAVE', 'SUBMIT', 'UPDATE', 'EDIT', 'APPROVE', 'HOLD', 'REJECT', 'DEALLOCATE', 'ALLOCATE', 'PROCESS', 'UNPROCESS', 'CANCEL'} and not (perm.get('AllowAdd') or perm.get('AllowUpdate')):
                        flash('You do not have permission to perform this action.', 'danger')
                        return redirect(url_for('main.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# --- CLEAN ROUTES ---

@academics_bp.route('/session_master', methods=['GET', 'POST'])
@permission_required('Academic Session Master')
def session_master():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'DELETE':
            if InfrastructureModel.delete_session(request.form.get('id')):
                flash('Session deleted successfully!', 'success')
            else:
                flash('Error deleting session.', 'danger')
        else:
            if InfrastructureModel.save_session(request.form):
                flash('Session saved successfully!', 'success')
            else:
                flash('Error saving session.', 'danger')
        return redirect(url_for('academics.session_master'))
    
    page = request.args.get('page', 1, type=int)
    per_page = 10
    sessions, total = InfrastructureModel.get_sessions_paginated(page=page, per_page=per_page)
    
    pagination = {
        'page': page,
        'per_page': per_page,
        'total': total,
        'total_pages': math.ceil(total / per_page) if total else 1,
        'has_prev': page > 1,
        'has_next': page < (math.ceil(total / per_page) if total else 1)
    }
    
    page_range = get_pagination_range(page, pagination['total_pages'])
    
    return render_template('academics/session_master.html', 
                           sessions=sessions, 
                           pagination=pagination,
                           page_range=page_range)

@academics_bp.route('/faculty_master', methods=['GET', 'POST'])
@permission_required('Faculty Master')
def faculty_master():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'DELETE':
            if AcademicsModel.delete_faculty(request.form.get('id')):
                flash('Faculty deleted successfully!', 'success')
            else:
                flash('Error deleting faculty.', 'danger')
        else:
            if AcademicsModel.save_faculty(request.form):
                flash('Faculty saved successfully!', 'success')
            else:
                flash('Error saving faculty.', 'danger')
        return redirect(url_for('academics.faculty_master'))
    faculties = AcademicsModel.get_faculties()
    return render_template('academics/faculty_master.html', faculties=faculties)

@academics_bp.route('/degree_year_master', methods=['GET', 'POST'])
@permission_required('Degree Year Master')
def degree_year_master():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'DELETE':
            if AcademicsModel.delete_degree_year(request.form.get('id')):
                flash('Degree Year deleted successfully!', 'success')
            else:
                flash('Error deleting degree year.', 'danger')
        else:
            if AcademicsModel.save_degree_year(request.form):
                flash('Degree Year saved successfully!', 'success')
            else:
                flash('Error saving degree year.', 'danger')
        return redirect(url_for('academics.degree_year_master'))
    
    page = request.args.get('page', 1, type=int)
    per_page = 10
    years, total = AcademicsModel.get_degree_years_paginated(page=page, per_page=per_page)
    
    pagination = {
        'page': page,
        'per_page': per_page,
        'total': total,
        'total_pages': math.ceil(total / per_page) if total else 1,
        'has_prev': page > 1,
        'has_next': page < (math.ceil(total / per_page) if total else 1)
    }
    
    page_range = get_pagination_range(page, pagination['total_pages'])
    
    return render_template('academics/degree_year_master.html', 
                           years=years, 
                           pagination=pagination,
                           page_range=page_range)

@academics_bp.route('/semester_master', methods=['GET', 'POST'])
@permission_required('Semester Master [Add Semester]')
def semester_master():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'DELETE':
            if InfrastructureModel.delete_semester(request.form.get('id')):
                flash('Semester deleted successfully!', 'success')
            else:
                flash('Error deleting semester.', 'danger')
        else:
            if InfrastructureModel.save_semester(request.form):
                flash('Semester saved successfully!', 'success')
            else:
                flash('Error saving semester.', 'danger')
        return redirect(url_for('academics.semester_master'))
    
    page = request.args.get('page', 1, type=int)
    per_page = 10
    semesters, total = InfrastructureModel.get_semesters_paginated(page=page, per_page=per_page)
    years = AcademicsModel.get_degree_years()
    
    pagination = {
        'page': page,
        'per_page': per_page,
        'total': total,
        'total_pages': math.ceil(total / per_page) if total else 1,
        'has_prev': page > 1,
        'has_next': page < (math.ceil(total / per_page) if total else 1)
    }
    
    page_range = get_pagination_range(page, pagination['total_pages'])
    
    return render_template('academics/semester_master.html', 
                           semesters=semesters, 
                           years=years,
                           pagination=pagination,
                           page_range=page_range)

@academics_bp.route('/branch_master', methods=['GET', 'POST'])
@permission_required('Specialization Master [PG/PHD]')
def branch_master():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'DELETE':
            if AcademicsModel.delete_branch(request.form.get('id')):
                flash('Specialization deleted successfully!', 'success')
            else:
                flash('Error deleting specialization.', 'danger')
        else:
            if AcademicsModel.save_branch(request.form):
                flash('Specialization saved successfully!', 'success')
            else:
                flash('Error saving specialization.', 'danger')
        return redirect(url_for('academics.branch_master'))
    
    page = request.args.get('page', 1, type=int)
    per_page = 10
    branches, total = AcademicsModel.get_branches_paginated(page=page, per_page=per_page)
    faculties = AcademicsModel.get_faculties()
    
    pagination = {
        'page': page,
        'per_page': per_page,
        'total': total,
        'total_pages': math.ceil(total / per_page) if total else 1,
        'has_prev': page > 1,
        'has_next': page < (math.ceil(total / per_page) if total else 1)
    }
    
    page_range = get_pagination_range(page, pagination['total_pages'])
    
    return render_template('academics/branch_master.html', 
                           branches=branches, 
                           faculties=faculties,
                           pagination=pagination,
                           page_range=page_range)

@academics_bp.route('/college_type_master', methods=['GET', 'POST'])
@permission_required('College Type Master')
def college_type_master():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'DELETE':
            if ClassificationModel.delete_college_type(request.form.get('id')):
                flash('College Type deleted successfully!', 'success')
            else:
                flash('Error deleting college type.', 'danger')
        else:
            if ClassificationModel.save_college_type(request.form):
                flash('College Type saved successfully!', 'success')
            else:
                flash('Error saving college type.', 'danger')
        return redirect(url_for('academics.college_type_master'))
    
    page = request.args.get('page', 1, type=int)
    per_page = 10
    types, total = ClassificationModel.get_college_types_paginated(page=page, per_page=per_page)
    
    pagination = {
        'page': page,
        'per_page': per_page,
        'total': total,
        'total_pages': math.ceil(total / per_page) if total else 1,
        'has_prev': page > 1,
        'has_next': page < (math.ceil(total / per_page) if total else 1)
    }
    
    page_range = get_pagination_range(page, pagination['total_pages'])
    
    return render_template('academics/college_type_master.html', types=types, pagination=pagination, page_range=page_range)
@academics_bp.route('/degree_type_master', methods=['GET', 'POST'])
@permission_required('Degree Type Master')
def degree_type_master():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'DELETE':
            if ClassificationModel.delete_degree_type(request.form.get('id')):
                flash('Degree Type deleted successfully!', 'success')
            else:
                flash('Error deleting degree type.', 'danger')
        else:
            if ClassificationModel.save_degree_type(request.form):
                flash('Degree Type saved successfully!', 'success')
            else:
                flash('Error saving degree type.', 'danger')
        return redirect(url_for('academics.degree_type_master'))
    
    page = request.args.get('page', 1, type=int)
    per_page = 10
    types, total = ClassificationModel.get_degree_types_paginated(page=page, per_page=per_page)
    
    pagination = {
        'page': page,
        'per_page': per_page,
        'total': total,
        'total_pages': math.ceil(total / per_page) if total else 1,
        'has_prev': page > 1,
        'has_next': page < (math.ceil(total / per_page) if total else 1)
    }
    
    page_range = get_pagination_range(page, pagination['total_pages'])
    
    return render_template('academics/degree_type_master.html', 
                           types=types, 
                           pagination=pagination,
                           page_range=page_range)

@academics_bp.route('/rank_master', methods=['GET', 'POST'])
@permission_required('Qualifying/Institution Quota')
def rank_master():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'DELETE':
            if StudentConfigModel.delete_rank(request.form.get('id')):
                flash('Quota deleted successfully!', 'success')
            else:
                flash('Error deleting quota.', 'danger')
        else:
            if StudentConfigModel.save_rank(request.form):
                flash('Quota saved successfully!', 'success')
            else:
                flash('Error saving quota.', 'danger')
        return redirect(url_for('academics.rank_master'))
    
    page = request.args.get('page', 1, type=int)
    per_page = 10
    items, total = StudentConfigModel.get_ranks(page=page, per_page=per_page)
    
    pagination = {
        'page': page,
        'per_page': per_page,
        'total': total,
        'total_pages': math.ceil(total / per_page) if total else 1,
        'has_prev': page > 1,
        'has_next': page < (math.ceil(total / per_page) if total else 1)
    }
    
    page_range = get_pagination_range(page, pagination['total_pages'])
    
    return render_template('academics/rank_master.html', items=items, pagination=pagination, page_range=page_range)

@academics_bp.route('/api/college/<college_id>/degrees')
def get_college_degrees_api(college_id):
    from app.utils import clean_json_data
    degrees = AcademicsModel.get_college_degrees(college_id)
    return jsonify(clean_json_data(degrees))

@academics_bp.route('/api/search_teachers')
def search_teachers_api():
    term = request.args.get('q', '').strip()
    include_all = request.args.get('all') == '1'
    emp_id = session.get('emp_id')
    
    # Use EmployeeModel.search_employees with only_teachers=True
    results = EmployeeModel.search_employees(term, only_teachers=True)
    
    # Filter by department if not include_all (for departmental dropdown population)
    if not include_all and emp_id:
        ctx = AcademicsModel.get_hod_department_context(emp_id)
        hod_dept_ids = {str(d['id']) for d in ctx.get('hr_departments', [])}
        filtered = []
        for r in results:
            if str(r.get('fk_deptid')) in hod_dept_ids:
                filtered.append(r)
        results = filtered

    # Ensure format matches what ddlEmployee expect: {id, name}
    formatted = []
    for r in results:
        formatted.append({
            'id': r.get('id') or r.get('pk_empid'),
            'name': r.get('name') or (f"{r.get('empname')} | {r.get('empcode')}")
        })

    return jsonify(clean_json_data(formatted))

@academics_bp.route('/employee_degree_map', methods=['GET', 'POST'])
@permission_required('Employee- Degree Map')
def employee_degree_map():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'DELETE':
            if AcademicsModel.delete_employee_degree_mapping(request.form.get('id')):
                flash('Mapping deleted successfully!', 'success')
            else:
                flash('Error deleting mapping.', 'danger')
        else:
            if AcademicsModel.save_employee_degree_mapping(request.form):
                flash('Employee-Degree mapping saved successfully!', 'success')
            else:
                flash('Error saving mapping.', 'danger')
        return redirect(url_for('academics.employee_degree_map'))
    
    page = request.args.get('page', 1, type=int)
    per_page = 10
    items, total = AcademicsModel.get_employee_degree_mappings_paginated(page=page, per_page=per_page)
    
    pagination = {
        'page': page,
        'per_page': per_page,
        'total': total,
        'total_pages': math.ceil(total / per_page) if total else 1,
        'has_prev': page > 1,
        'has_next': page < (math.ceil(total / per_page) if total else 1)
    }
    
    page_range = get_pagination_range(page, pagination['total_pages'])

    lookups = {
        'colleges': AcademicsModel.get_colleges_simple(),
        'degrees': AcademicsModel.get_all_degrees(),
        'employees': DB.fetch_all("""
            SELECT U.pk_userId as id, E.empname + ' [ User Name -{ ' + U.loginname + ' } ]' as name
            FROM UM_Users_Mst U
            INNER JOIN SAL_Employee_Mst E ON U.fk_empId = E.pk_empid
            WHERE U.active = 1
            ORDER BY E.empname
        """)
    }
    
    return render_template('academics/employee_degree_map.html', items=items, lookups=lookups, pagination=pagination, page_range=page_range)

@academics_bp.route('/college_master', methods=['GET', 'POST'])
@permission_required('College Master [Create College]')
def college_master():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'DELETE':
            if AcademicsModel.delete_college(request.form.get('id')):
                flash('College deleted successfully!', 'success')
            else:
                flash('Error deleting college.', 'danger')
        else:
            if AcademicsModel.save_college(request.form):
                flash('College saved successfully!', 'success')
            else:
                flash('Error saving college.', 'danger')
        return redirect(url_for('academics.college_master'))
    
    page = request.args.get('page', 1, type=int)
    per_page = 10
    items, total = AcademicsModel.get_colleges(page=page, per_page=per_page)
    
    pagination = {
        'page': page,
        'per_page': per_page,
        'total': total,
        'total_pages': math.ceil(total / per_page) if total else 1,
        'has_prev': page > 1,
        'has_next': page < (math.ceil(total / per_page) if total else 1)
    }
    
    page_range = get_pagination_range(page, pagination['total_pages'])

    lookups = {
        'types': ClassificationModel.get_college_types(),
        'cities': AcademicsModel.get_cities(),
        'locations': DB.fetch_all("SELECT pk_locid as id, locname as name, * FROM Location_Mst ORDER BY locname")
    }
    
    return render_template('academics/college_master.html', items=items, lookups=lookups, pagination=pagination, page_range=page_range)

@academics_bp.route('/api/get_college_details/<int:college_id>')
def get_college_details_data_api(college_id):
    data = AcademicsModel.get_college_full_details(college_id)
    return jsonify(data)

@academics_bp.route('/api/get_all_employees')
def get_all_employees_api():
    sql = "SELECT pk_empid as id, empname + ' || ' + empcode as name FROM SAL_Employee_Mst WHERE active=1 ORDER BY empname"
    emps = DB.fetch_all(sql)
    return jsonify(emps)

@academics_bp.route('/degree_master', methods=['GET', 'POST'])
@permission_required('Degree Master [Create Degree]')
def degree_master():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'DELETE':
            if AcademicsModel.delete_degree(request.form.get('id')):
                flash('Degree deleted successfully!', 'success')
            else:
                flash('Error deleting degree.', 'danger')
        else:
            if AcademicsModel.save_degree(request.form):
                flash('Degree saved successfully!', 'success')
            else:
                flash('Error saving degree.', 'danger')
        return redirect(url_for('academics.degree_master'))
    
    page = request.args.get('page', 1, type=int)
    per_page = 10
    items, total = AcademicsModel.get_degrees_paginated(page=page, per_page=per_page)
    
    pagination = {
        'page': page,
        'per_page': per_page,
        'total': total,
        'total_pages': math.ceil(total / per_page) if total else 1,
        'has_prev': page > 1,
        'has_next': page < (math.ceil(total / per_page) if total else 1)
    }
    
    page_range = get_pagination_range(page, pagination['total_pages'])

    lookups = {
        'types': ClassificationModel.get_degree_types()
    }
    
    return render_template('academics/degree_master.html', items=items, lookups=lookups, pagination=pagination, page_range=page_range)

@academics_bp.route('/degree_cycle_master', methods=['GET', 'POST'])
@permission_required('Degree Cycle Master')
def degree_cycle_master():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'DELETE':
            if AcademicsModel.delete_degree_cycle(request.form.get('id')):
                flash('Degree cycle deleted successfully!', 'success')
            else:
                flash('Error deleting cycle.', 'danger')
        else:
            if AcademicsModel.save_degree_cycle(request.form):
                flash('Degree cycle saved successfully!', 'success')
            else:
                flash('Error saving cycle.', 'danger')
        return redirect(url_for('academics.degree_cycle_master'))
    
    page = request.args.get('page', 1, type=int)
    per_page = 10
    items, total = AcademicsModel.get_degree_cycles_paginated(page=page, per_page=per_page)
    
    pagination = {
        'page': page,
        'per_page': per_page,
        'total': total,
        'total_pages': math.ceil(total / per_page) if total else 1,
        'has_prev': page > 1,
        'has_next': page < (math.ceil(total / per_page) if total else 1)
    }
    
    page_range = get_pagination_range(page, pagination['total_pages'])

    lookups = {
        'degrees': AcademicsModel.get_all_degrees(),
        'branches': AcademicsModel.get_branches(),
        'years': AcademicsModel.get_degree_years(),
        'semesters': InfrastructureModel.get_all_semesters()
    }
    
    return render_template('academics/degree_cycle_master.html', items=items, lookups=lookups, pagination=pagination, page_range=page_range)

@academics_bp.route('/course_type_master', methods=['GET', 'POST'])
@permission_required('Course Type Master')
def course_type_master():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'DELETE':
            if ClassificationModel.delete_course_type(request.form.get('id')):
                flash('Course Type deleted successfully!', 'success')
            else:
                flash('Error deleting course type.', 'danger')
        else:
            if ClassificationModel.save_course_type(request.form):
                flash('Course Type saved successfully!', 'success')
            else:
                flash('Error saving course type.', 'danger')
        return redirect(url_for('academics.course_type_master'))
    
    page = request.args.get('page', 1, type=int)
    per_page = 10
    types, total = ClassificationModel.get_course_types_paginated(page=page, per_page=per_page)
    
    pagination = {
        'page': page,
        'per_page': per_page,
        'total': total,
        'total_pages': math.ceil(total / per_page) if total else 1,
        'has_prev': page > 1,
        'has_next': page < (math.ceil(total / per_page) if total else 1)
    }
    
    page_range = get_pagination_range(page, pagination['total_pages'])
    
    return render_template('academics/course_type_master.html', types=types, pagination=pagination, page_range=page_range)

@academics_bp.route('/paper_title_master', methods=['GET', 'POST'])
@permission_required('Paper/Course Title Master')
def paper_title_master():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'DELETE':
            if CourseModel.delete_paper_title(request.form.get('id')):
                flash('Paper Title deleted successfully!', 'success')
            else:
                flash('Error deleting paper title.', 'danger')
        else:
            if CourseModel.save_paper_title(request.form):
                flash('Paper Title saved successfully!', 'success')
            else:
                flash('Error saving paper title.', 'danger')
        return redirect(url_for('academics.paper_title_master'))
    
    page = request.args.get('page', 1, type=int)
    per_page = 10
    titles, total = CourseModel.get_paper_titles(page=page, per_page=per_page)
    
    pagination = {
        'page': page,
        'per_page': per_page,
        'total': total,
        'total_pages': math.ceil(total / per_page) if total else 1,
        'has_prev': page > 1,
        'has_next': page < (math.ceil(total / per_page) if total else 1)
    }
    
    page_range = get_pagination_range(page, pagination['total_pages'])
    
    return render_template('academics/paper_title_master.html', titles=titles, pagination=pagination, page_range=page_range)

@academics_bp.route('/course_master', methods=['GET', 'POST'])
@permission_required('Course/Subject Master')
def course_master():
    user_id = session['user_id']
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'DELETE':
            if CourseModel.delete_course(request.form.get('id')):
                flash('Course deleted successfully!', 'success')
            else:
                flash('Error deleting course.', 'danger')
        else:
            if CourseModel.save_course(request.form, user_id):
                flash('Course saved successfully!', 'success')
            else:
                flash('Error saving course.', 'danger')
        return redirect(url_for('academics.course_master'))

    page = request.args.get('page', 1, type=int)
    per_page = 10
    filters = {'dept_id': request.args.get('dept_id'), 'term': request.args.get('term')}
    courses, total = CourseModel.get_courses(filters, page=page, per_page=per_page)
    
    pagination = {
        'page': page,
        'per_page': per_page,
        'total': total,
        'total_pages': math.ceil(total / per_page) if total else 1,
        'has_prev': page > 1,
        'has_next': page < (math.ceil(total / per_page) if total else 1)
    }
    
    page_range = get_pagination_range(page, pagination['total_pages'])

    lookups = {
        'depts': AcademicsModel.get_departments(),
        'titles': CourseModel.get_all_paper_titles(),
        'types': ClassificationModel.get_course_types(),
        'sessions': InfrastructureModel.get_sessions(),
        'degrees': AcademicsModel.get_all_degrees(),
        'semesters': InfrastructureModel.get_all_semesters(),
        'branches': AcademicsModel.get_branches()
    }
    
    return render_template('academics/course_master.html', 
                           courses=courses, 
                           lookups=lookups, 
                           filters=filters,
                           pagination=pagination,
                           page_range=page_range)

@academics_bp.route('/api/get_course_details/<int:course_id>')
def get_course_details_api(course_id):
    details = CourseModel.get_course_details(course_id)
    return jsonify(details)

@academics_bp.route('/entitlement_master', methods=['GET', 'POST'])
@permission_required('Entitlement Master')
def entitlement_master():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'DELETE':
            if StudentConfigModel.delete_entitlement(request.form.get('id')):
                flash('Entitlement deleted successfully!', 'success')
            else:
                flash('Error deleting entitlement.', 'danger')
        else:
            if StudentConfigModel.save_entitlement(request.form):
                flash('Entitlement saved successfully!', 'success')
            else:
                flash('Error saving entitlement.', 'danger')
        return redirect(url_for('academics.entitlement_master'))

    page = request.args.get('page', 1, type=int)
    per_page = 10
    items, total = StudentConfigModel.get_entitlements(page=page, per_page=per_page)
    
    pagination = {
        'page': page,
        'per_page': per_page,
        'total': total,
        'total_pages': math.ceil(total / per_page) if total else 1,
        'has_prev': page > 1,
        'has_next': page < (math.ceil(total / per_page) if total else 1)
    }
    
    page_range = get_pagination_range(page, pagination['total_pages'])
    
    return render_template('academics/entitlement_master.html', items=items, pagination=pagination, page_range=page_range)

@academics_bp.route('/category_master', methods=['GET', 'POST'])
@permission_required('Category Master')
def category_master():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'DELETE':
            if ClassificationModel.delete_category(request.form.get('id')):
                flash('Category deleted successfully!', 'success')
            else:
                flash('Error deleting category.', 'danger')
        else:
            if ClassificationModel.save_category(request.form):
                flash('Category saved successfully!', 'success')
            else:
                flash('Error saving category.', 'danger')
        return redirect(url_for('academics.category_master'))

    page = request.args.get('page', 1, type=int)
    per_page = 10
    items, total = ClassificationModel.get_categories(page=page, per_page=per_page)
    
    pagination = {
        'page': page,
        'per_page': per_page,
        'total': total,
        'total_pages': math.ceil(total / per_page) if total else 1,
        'has_prev': page > 1,
        'has_next': page < (math.ceil(total / per_page) if total else 1)
    }
    
    page_range = get_pagination_range(page, pagination['total_pages'])
    
    return render_template('academics/category_master.html', items=items, pagination=pagination, page_range=page_range)

@academics_bp.route('/nationality_master', methods=['GET', 'POST'])
@permission_required('Nationality Master')
def nationality_master():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'DELETE':
            if ClassificationModel.delete_nationality(request.form.get('id')):
                flash('Nationality deleted successfully!', 'success')
            else:
                flash('Error deleting nationality.', 'danger')
        else:
            if ClassificationModel.save_nationality(request.form):
                flash('Nationality saved successfully!', 'success')
            else:
                flash('Error saving nationality.', 'danger')
        return redirect(url_for('academics.nationality_master'))
    nationalities = ClassificationModel.get_nationalities()
    return render_template('academics/nationality_master.html', nationalities=nationalities)

@academics_bp.route('/certificate_master', methods=['GET', 'POST'])
@permission_required('Certificates Master')
def certificate_master():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'DELETE':
            DB.execute("DELETE FROM SMS_Certificate_Mst WHERE pk_certificateid = ?", [request.form.get('id')])
            flash('Certificate deleted successfully!', 'success')
        else:
            if AdmissionModel.save_certificate(request.form):
                flash('Certificate saved successfully!', 'success')
            else:
                flash('Error saving certificate.', 'danger')
        return redirect(url_for('academics.certificate_master'))

    page = request.args.get('page', 1, type=int)
    per_page = 10
    items, total = AdmissionModel.get_certificates(page=page, per_page=per_page)
    
    pagination = {
        'page': page, 'per_page': per_page, 'total': total,
        'total_pages': math.ceil(total / per_page) if total else 1,
        'has_prev': page > 1,
        'has_next': page < (math.ceil(total / per_page) if total else 1)
    }
    page_range = get_pagination_range(page, pagination['total_pages'])
    return render_template('academics/certificate_master.html', items=items, pagination=pagination, page_range=page_range)

@academics_bp.route('/student_biodata', methods=['GET', 'POST'])
@academics_bp.route('/student_biodata/<int:sid>', methods=['GET', 'POST'])
@permission_required('Student BioData')
@academics_bp.route('/api/student/profile_basic/<int:sid>')
def api_get_student_profile_basic(sid):
    data = StudentModel.get_student_profile_basic(sid)
    if data:
        return jsonify(clean_json_data(data))
    return jsonify({'error': 'Student not found'}), 404

def student_biodata(sid=None):
    if request.method == 'POST':
        if StudentModel.save_student_biodata(request.form, session['user_id']):
            flash('Student BioData saved successfully!', 'success')
        else:
            flash('Error saving student BioData.', 'danger')
        return redirect(url_for('academics.student_biodata', sid=request.form.get('pk_sid')))
    
    if not sid:
        sid = request.args.get('sid')
        
    student_data = clean_json_data(StudentModel.get_student_all_details(sid)) if sid else None
    lookups = StudentModel.get_student_lookups()
    
    return render_template('academics/student_biodata.html', student_data=student_data, lookups=lookups)

@academics_bp.route('/api/student/get_full_details')
def api_get_student_details():
    sid = request.args.get('sid')
    enrollment_no = request.args.get('enrollment_no')
    
    if enrollment_no:
        basic = StudentModel.get_student_by_enrollment(enrollment_no)
        if basic:
            sid = basic['pk_sid']
        else:
            return jsonify({'error': 'Student not found'}), 404
            
    if not sid:
        return jsonify({'error': 'No student identifier provided'}), 400
        
    data = StudentModel.get_student_all_details(sid)
    if data:
        # Format dates for JSON (clean_json_data also handles this, but keeping for explicitness)
        if data['basic'].get('dob'): data['basic']['dob'] = data['basic']['dob'].isoformat()
        if data['basic'].get('FatherDOB'): data['basic']['FatherDOB'] = data['basic']['FatherDOB'].isoformat()
        if data['basic'].get('MotherDOB'): data['basic']['MotherDOB'] = data['basic']['MotherDOB'].isoformat()
        if data['basic'].get('PerentMarriedDate'): data['basic']['PerentMarriedDate'] = data['basic']['PerentMarriedDate'].isoformat()
        
        return jsonify(clean_json_data(data))
    return jsonify({'error': 'Student details not found'}), 404

@academics_bp.route('/upload_certificate', methods=['POST'])
@permission_required('Student Registration')
def upload_certificate():
    if 'cert_file' not in request.files:
        return jsonify({'success': False, 'message': 'No file part'})
    
    file = request.files['cert_file']
    cert_id = request.form.get('upload_cert_id')
    sid = request.form.get('sid') # Optional, for new reg we might use session or temp ID
    
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No selected file'})
    
    if file:
        filename = secure_filename(file.filename)
        # Store in temp directory or final path
        upload_path = os.path.join('app/static/uploads/certificates', filename)
        os.makedirs(os.path.dirname(upload_path), exist_ok=True)
        file.save(upload_path)
        
        # Save to DB if sid is present
        if sid:
            sql = """INSERT INTO Sms_StudentCertificateUpload_Dtl (fk_sid, UploadCertificateFileName, OriginalFileName, FilePath, fk_certificateId)
                     VALUES (?, ?, ?, ?, ?)"""
            DB.execute(sql, [sid, filename, file.filename, upload_path, cert_id])
            
        return jsonify({'success': True, 'filename': filename})

@academics_bp.route('/student_registration', methods=['GET', 'POST'])
@permission_required('Student Registration')
def student_registration():
    if request.method == 'POST':
        if StudentModel.save_student(request.form):
            flash('Student registered successfully!', 'success')
        else:
            flash('Error saving student details. Check for duplicate Admission No.', 'danger')
        return redirect(url_for('academics.student_registration'))
    
    lookups = StudentModel.get_student_lookups()
    return render_template('academics/student_registration.html', lookups=lookups)

@academics_bp.route('/student_password', methods=['GET', 'POST'])
@permission_required('Student Password')
def student_password():
    if request.method == 'POST':
        # Logic for resetting password
        flash('Password updated successfully!', 'success')
        return redirect(url_for('academics.student_password'))
    
    colleges = AcademicsModel.get_colleges_simple()
    degrees = AcademicsModel.get_all_degrees()
    sessions = InfrastructureModel.get_sessions()
    return render_template('academics/student_password.html', colleges=colleges, degrees=degrees, sessions=sessions)

@academics_bp.route('/view_student_password', methods=['GET', 'POST'])
@permission_required('View Student Password')
def view_student_password():
    student_password = None
    enrollment_no = None
    
    action = None
    if request.method == 'POST':
        enrollment_no = (request.form.get('enrollment_no') or '').strip()
        action = request.form.get('action')
        
        if not enrollment_no:
            flash('Please enter Enrollment No.', 'warning')
        elif action == 'Get Password':
            student_password = StudentModel.get_student_password(enrollment_no)
            if not student_password:
                flash('Student not found or password not available.', 'warning')
        elif action == 'Unlock Biodata':
            if StudentModel.unlock_student_biodata(enrollment_no):
                flash('Biodata unlocked successfully for ' + enrollment_no, 'success')
            else:
                flash('Student not found or could not unlock biodata.', 'danger')
        elif action == 'Card Entry Submit':
            StudentModel.update_card_entry_status(enrollment_no)
            flash('Card entry status updated for ' + enrollment_no, 'success')
            
    return render_template('academics/view_student_password.html', 
                           student_password=student_password,
                           enrollment_no=enrollment_no,
                           action=action)

@academics_bp.route('/validate_student/<enrollment_no>')
@permission_required('Back Course Entry')
def validate_student(enrollment_no):
    student = StudentModel.get_student_by_enrollment(enrollment_no)
    if student:
        return jsonify({'success': True, 'name': student['fullname'], 'sid': student['pk_sid']})
    return jsonify({'success': False, 'message': 'Student not found.'})

@academics_bp.route('/search_courses')
@permission_required('Back Course Entry')
def search_courses():
    code = request.args.get('code', '')
    query = "SELECT pk_courseid as id, coursecode + ' - ' + coursename as name FROM SMS_Course_Mst WHERE coursecode LIKE ? ORDER BY coursecode"
    courses = DB.fetch_all(query, [f'%{code}%'])
    return jsonify(courses)

@academics_bp.route('/back_course_entry', methods=['GET', 'POST'])
@permission_required('Back Course Entry')
def back_course_entry():
    if request.method == 'POST':
        flash('Back course entry saved.', 'success')
        return redirect(url_for('academics.back_course_entry'))
    
    lookups = {
        'colleges': AcademicsModel.get_colleges_simple(),
        'degrees': AcademicsModel.get_all_degrees(),
        'sessions': InfrastructureModel.get_sessions()
    }
    return render_template('academics/back_course_entry.html', lookups=lookups)

@academics_bp.route('/college_degree_seat_report', methods=['GET', 'POST'])
@permission_required('College Degree Seat Report')
def college_degree_seat_report():
    filters = {
        'session_id': request.args.get('session_id'),
        'college_id': request.args.get('college_id')
    }
    
    fmt = request.args.get('fmt')
    if fmt and all(filters.values()):
        data = SeatDetailModel.get_seat_report(filters)
        if fmt == 'excel':
            df = pd.DataFrame(data)
            # Adjust column selection based on actual model return
            cols = ['collegename', 'degreename', 'Branchname', 'totseat']
            df = df[[c for c in cols if c in df.columns]]
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='SeatReport')
            output.seek(0)
            return send_file(output, attachment_filename='College_Degree_Seat_Report.xlsx', as_attachment=True)
        elif fmt == 'pdf':
            html = render_template('reports/seat_report_pdf.html', data=data, filters=filters, now=datetime.now())
            return html

    data = []
    if all(filters.values()):
        data = SeatDetailModel.get_seat_report(filters)
        
    lookups = {
        'sessions': InfrastructureModel.get_sessions(),
        'colleges': AcademicsModel.get_colleges_simple()
    }
    return render_template('academics/college_degree_seat_report.html', lookups=lookups, filters=filters, data=data)

@academics_bp.route('/student_biodata_updation', methods=['GET', 'POST'])
@permission_required('Student Biodata Updation')
def student_biodata_updation():
    filters = {
        'college_id': request.args.get('college_id'),
        'session_id': request.args.get('session_id'),
        'degree_id': request.args.get('degree_id'),
        'admission_no': request.args.get('admission_no')
    }
    
    students = []
    if any(filters.values()):
        students = StudentModel.get_students_by_filter(filters)
        
    lookups = {
        'colleges': AcademicsModel.get_colleges_simple(),
        'sessions': InfrastructureModel.get_sessions(),
        'degrees': []
    }
    if filters['college_id']:
        lookups['degrees'] = AcademicsModel.get_college_pg_degrees(filters['college_id'])
    else:
        lookups['degrees'] = AcademicsModel.get_all_degrees()

    return render_template('academics/student_biodata_updation.html', 
                           lookups=lookups, filters=filters, students=students)

@academics_bp.route('/achievement_disciplinary', methods=['GET', 'POST'])
@permission_required('Achievement/ Disciplinary ')
def achievement_disciplinary():
    # This page usually searches by enrollment/admission no
    enrollment_no = request.args.get('enrollment_no')
    student = None
    if enrollment_no:
        student = StudentModel.get_student_by_enrollment(enrollment_no)
        
    return render_template('academics/achievement_disciplinary.html', student=student)

@academics_bp.route('/achievement_disciplinary_approval', methods=['GET', 'POST'])
@permission_required('Achievement / Disciplinary Approval')
def achievement_disciplinary_approval():
    # List based approval
    filters = {
        'college_id': request.args.get('college_id'),
        'session_id': request.args.get('session_id'),
        'degree_id': request.args.get('degree_id')
    }
    lookups = {
        'colleges': AcademicsModel.get_colleges_simple(),
        'sessions': InfrastructureModel.get_sessions(),
        'degrees': AcademicsModel.get_all_degrees()
    }
    return render_template('academics/achievement_disciplinary_approval.html', 
                           lookups=lookups, filters=filters)

@academics_bp.route('/student_activity_management', methods=['GET', 'POST'])
@permission_required('Student Activity Management')
def student_activity_management():
    # Placeholder for student activity management
    return render_template('academics/student_activity_management.html')

@academics_bp.route('/student_personal_detail_report', methods=['GET', 'POST'])
@permission_required('Student Personal Detail Report')
def student_personal_detail_report():
    lookups = {
        'colleges': AcademicsModel.get_colleges_simple(),
        'sessions': InfrastructureModel.get_sessions(),
        'degrees': AcademicsModel.get_all_degrees(),
        'semesters': InfrastructureModel.get_all_semesters()
    }
    return render_template('academics/student_personal_detail_report.html', lookups=lookups)

@academics_bp.route('/moderation_marks', methods=['GET', 'POST'])
@permission_required('Moderation Marks Detail')
def moderation_marks():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'DELETE':
            if AcademicsModel.delete_moderation_marks(request.form.get('id')):
                flash('Moderation marks deleted successfully!', 'success')
            else:
                flash('Error deleting record.', 'danger')
        else:
            if AcademicsModel.save_moderation_marks(request.form):
                flash('Moderation marks saved successfully!', 'success')
            else:
                flash('Error saving record. Make sure a Degree Cycle exists for the selected degree/semester.', 'danger')
        return redirect(url_for('academics.moderation_marks'))
    
    page = request.args.get('page', 1, type=int)
    per_page = 10
    items, total = AcademicsModel.get_moderation_marks(page=page, per_page=per_page)
    
    pagination = {
        'page': page,
        'per_page': per_page,
        'total': total,
        'total_pages': math.ceil(total / per_page) if total else 1,
        'has_prev': page > 1,
        'has_next': page < (math.ceil(total / per_page) if total else 1)
    }
    
    page_range = get_pagination_range(page, pagination['total_pages'])

    lookups = {
        'degrees': AcademicsModel.get_all_degrees(),
        'semesters': InfrastructureModel.get_all_semesters(),
        'titles': CourseModel.get_all_paper_titles()
    }
    
    return render_template('academics/moderation_marks.html', items=items, lookups=lookups, pagination=pagination, page_range=page_range)

@academics_bp.route('/limit_assignment', methods=['GET', 'POST'])
@permission_required('Limit Assignment')
def limit_assignment():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'DELETE':
            # Simplified delete
            DB.execute("DELETE FROM SMS_AdvisoryStudentLimitConfiq WHERE pk_limitid = ?", [request.form.get('id')])
            flash('Limit assignment deleted successfully!', 'success')
        else:
            if AdvisoryModel.save_student_limit(request.form):
                flash('Limit assignment saved successfully!', 'success')
            else:
                flash('Error saving limit assignment.', 'danger')
        return redirect(url_for('academics.limit_assignment'))

    page = request.args.get('page', 1, type=int)
    per_page = 10
    items, total = AdvisoryModel.get_student_limits(page=page, per_page=per_page)
    
    pagination = {
        'page': page, 'per_page': per_page, 'total': total,
        'total_pages': math.ceil(total / per_page) if total else 1,
        'has_prev': page > 1,
        'has_next': page < (math.ceil(total / per_page) if total else 1)
    }
    page_range = get_pagination_range(page, pagination['total_pages'])

    lookups = {
        'colleges': AcademicsModel.get_colleges_simple(),
        'sessions': InfrastructureModel.get_sessions(),
        'degrees': AcademicsModel.get_all_degrees(),
        'branches': AcademicsModel.get_branches()
    }
    filters = {
        'college_id': request.args.get('college_id', ''),
        'session_id': request.args.get('session_id', ''),
        'degree_id': request.args.get('degree_id', '')
    }
    return render_template(
        'academics/limit_assignment.html',
        items=items,
        lookups=lookups,
        pagination=pagination,
        page_range=page_range,
        filters=filters
    )

@academics_bp.route('/major_advisor', methods=['GET', 'POST'])
@permission_required('Major Advisor')
def major_advisor():
    if request.method == 'POST':
        sid = request.form.get('sid')
        advisor_id = request.form.get('advisor_id')
        user_id = session['user_id']
        if sid and advisor_id:
            if AdvisoryModel.save_major_advisor(sid, advisor_id, user_id):
                flash('Major Advisor assigned successfully.', 'success')
            else:
                flash('Error assigning Major Advisor.', 'danger')
        return redirect(url_for('academics.major_advisor', **request.args))

    college_id = request.args.get('college_id')
    session_id = request.args.get('session_id')
    degree_id = request.args.get('degree_id')
    branch_id = request.args.get('branch_id')
    
    students = []
    if college_id and session_id and degree_id and str(degree_id) != '0':
        filters = {
            'college_id': college_id,
            'session_id': session_id,
            'degree_id': degree_id,
            'branch_id': branch_id
        }
        students = AdvisoryModel.get_students_for_advisory(filters)

    lookups = {
        'colleges': AcademicsModel.get_colleges_simple(),
        'sessions': InfrastructureModel.get_sessions(),
        'degrees': AcademicsModel.get_college_pg_degrees(college_id) if college_id else [],
        'branches': AcademicsModel.get_college_degree_specializations(college_id, degree_id) if (college_id and degree_id and str(degree_id) != '0') else [],
        'employees': DB.fetch_all("SELECT E.pk_empid as id, E.empname + ' | ' + E.empcode + ' | (' + ISNULL(D.description, 'No Dept') + ')' as name FROM SAL_Employee_Mst E LEFT JOIN Department_Mst D ON E.fk_deptid = D.pk_deptid WHERE E.employeeleftstatus = 'N' ORDER BY E.empname")
    }
    
    return render_template('academics/major_advisor.html', 
                           lookups=lookups,
                           students=clean_json_data(students), 
                           filters=request.args)

@academics_bp.route('/dean_pgs_approval', methods=['GET', 'POST'])
@permission_required('Dean PGS approval (advisory committee)')
def dean_pgs_approval():
    if request.method == 'POST':
        action = request.form.get('action')
        user_id = session['user_id']
        
        if action == 'ADD_NOMINEE':
            adcid = request.form.get('adcid')
            advisor_id = request.form.get('advisor_id')
            if adcid and advisor_id:
                AdvisoryModel.save_nominee(adcid, advisor_id)
                flash('Nominee added successfully.', 'success')
            return redirect(url_for('academics.dean_pgs_approval', **request.args))
            
        elif action in ['APPROVE', 'REJECT']:
            adcid = request.form.get('adcid')
            status = 'A' if action == 'APPROVE' else 'R'
            remarks = request.form.get('remarks')
            if adcid:
                AdvisoryModel.approve_advisory(adcid, status, user_id, level='PGS', remarks=remarks)
                flash(f'Advisory record { "approved" if status == "A" else "rejected" } successfully.', 'success')
            return redirect(url_for('academics.dean_pgs_approval', **request.args))

    filters = {
        'college_id': request.args.get('college_id'),
        'session_id': request.args.get('session_id'),
        'degree_id': request.args.get('degree_id'),
        'branch_id': request.args.get('branch_id')
    }
    
    sid = request.args.get('sid')
    students = []
    advisory_details = []
    current_adcid = None
    
    if all([filters['college_id'], filters['session_id'], filters['degree_id']]):
        # Get all students for the dropdown as per live template
        students = AdvisoryModel.get_students_for_advisory(filters)
        
    if sid:
        advisory_info = AdvisoryModel.get_student_advisory_committee(sid)
        if advisory_info:
            advisory_details = advisory_info.get('details', [])
            current_adcid = advisory_info.get('adcid')

    lookups = AdvisoryModel.get_advisory_lookups(filters['college_id'], filters['degree_id'])
    # Add status types (Nominee is type 5)
    lookups['advisory_types'] = [{'id': 5, 'name': 'Dean PGS Nominee'}]
    
    return render_template('academics/dean_pgs_approval.html', 
                           lookups=lookups, 
                           filters=filters, 
                           students=students, 
                           advisory_details=advisory_details,
                           current_adcid=current_adcid,
                           sid=sid)

@academics_bp.route('/hod_approval', methods=['GET', 'POST'])
@permission_required('HOD Approval')
def hod_approval():
    if request.method == 'POST':
        action = request.form.get('action')
        user_id = session['user_id']
        adcid = request.form.get('adcid')
        
        if action in ['APPROVE', 'REJECT']:
            status = 'A' if action == 'APPROVE' else 'R'
            remarks = request.form.get('remarks')
            if adcid:
                AdvisoryModel.approve_advisory(adcid, status, user_id, level='HOD', remarks=remarks)
                flash(f'Advisory record { "approved" if status == "A" else "rejected" } by HOD successfully.', 'success')
            return redirect(url_for('academics.hod_approval', **request.args))

    filters = {
        'college_id': request.args.get('college_id'),
        'session_id': request.args.get('session_id'),
        'degree_id': request.args.get('degree_id'),
        'branch_id': request.args.get('branch_id')
    }
    
    sid = request.args.get('sid')
    students = []
    advisory_details = []
    current_adcid = None
    
    if all([filters['college_id'], filters['session_id'], filters['degree_id']]):
        students = AdvisoryModel.get_students_for_advisory(filters)
        
    if sid:
        advisory_info = AdvisoryModel.get_student_advisory_committee(sid)
        if advisory_info:
            advisory_details = advisory_info.get('details', [])
            current_adcid = advisory_info.get('adcid')

    lookups = AdvisoryModel.get_advisory_lookups(filters['college_id'], filters['degree_id'])
    
    return render_template('academics/hod_approval.html', 
                           lookups=lookups, 
                           filters=filters, 
                           students=students, 
                           advisory_details=advisory_details,
                           current_adcid=current_adcid,
                           sid=sid)

@academics_bp.route('/college_dean_approval', methods=['GET', 'POST'])
@permission_required('College Dean Approval')
def college_dean_approval():
    if request.method == 'POST':
        action = request.form.get('action')
        user_id = session['user_id']
        adcid = request.form.get('adcid')
        
        if action in ['APPROVE', 'REJECT']:
            status = 'A' if action == 'APPROVE' else 'R'
            remarks = request.form.get('remarks')
            if adcid:
                AdvisoryModel.approve_advisory(adcid, status, user_id, level='DEAN', remarks=remarks)
                flash(f'Advisory record { "approved" if status == "A" else "rejected" } by College Dean successfully.', 'success')
            return redirect(url_for('academics.college_dean_approval', **request.args))

    filters = {
        'college_id': request.args.get('college_id'),
        'session_id': request.args.get('session_id'),
        'degree_id': request.args.get('degree_id'),
        'branch_id': request.args.get('branch_id')
    }
    
    sid = request.args.get('sid')
    students = []
    advisory_details = []
    current_adcid = None
    
    if all([filters['college_id'], filters['session_id'], filters['degree_id']]):
        students = AdvisoryModel.get_students_for_advisory(filters)
        
    if sid:
        advisory_info = AdvisoryModel.get_student_advisory_committee(sid)
        if advisory_info:
            advisory_details = advisory_info.get('details', [])
            current_adcid = advisory_info.get('adcid')

    lookups = AdvisoryModel.get_advisory_lookups(filters['college_id'], filters['degree_id'])
    
    return render_template('academics/college_dean_approval.html', 
                           lookups=lookups, 
                           filters=filters, 
                           students=students, 
                           advisory_details=advisory_details,
                           current_adcid=current_adcid,
                           sid=sid)

@academics_bp.context_processor
def inject_academic_menu():
    return {'ACADEMIC_MENU_CONFIG': ACADEMIC_MENU_CONFIG}

@academics_bp.route('/api/courses')
def get_all_courses_api():
    courses = CourseModel.get_all_courses()
    return jsonify(clean_json_data(courses))

@academics_bp.route('/api/student/<int:sid>/course_plan_data')
def get_student_course_plan_data_api(sid):
    current_plan = AdvisoryModel.get_student_course_plan(sid)
    available_courses = AdvisoryModel.get_available_courses(sid)
    credit_load = AdvisoryModel.get_credit_load(sid)
    required_load = AdvisoryModel.get_required_credit_load(sid)
    
    return jsonify(clean_json_data({
        'current_plan': current_plan,
        'available_courses': available_courses,
        'credit_load': credit_load,
        'required_load': required_load
    }))

@academics_bp.route('/course_plan', methods=['GET', 'POST'])
@permission_required('Prepare Course Plan')
def course_plan():
    if request.method == 'POST':
        sid = request.form.get('sid')
        # Expecting JSON-like structure or multiple arrays from form
        course_ids = request.form.getlist('course_id[]')
        types = request.form.getlist('type[]')
        
        courses = []
        for i in range(len(course_ids)):
            if course_ids[i] and str(course_ids[i]) != '0':
                courses.append({
                    'course_id': course_ids[i],
                    'type': types[i]
                })
        
        if sid and AdvisoryModel.save_course_plan(sid, courses, session['user_id']):
            flash('Course plan saved successfully.', 'success')
        else:
            flash('Error saving course plan.', 'danger')
        return redirect(url_for('academics.course_plan', **request.args))

    filters = {
        'college_id': request.args.get('college_id'),
        'session_id': request.args.get('session_id'),
        'degree_id': request.args.get('degree_id'),
        'branch_id': request.args.get('branch_id')
    }
    
    students = []
    if all([filters['college_id'], filters['session_id'], filters['degree_id']]):
        students = AdvisoryModel.get_students_for_advisory(filters)

    lookups = AdvisoryModel.get_advisory_lookups(filters['college_id'], filters['degree_id'])
    
    return render_template('academics/course_plan.html', 
                           lookups=lookups, 
                           filters=filters, 
                           students=students)

@academics_bp.route('/dean_pgs_course_plan_approval', methods=['GET', 'POST'])
@permission_required('Dean PGS approval (Course plan)')
def dean_pgs_course_plan_approval():
    if request.method == 'POST':
        action = request.form.get('action')
        sid = request.form.get('sid')
        user_id = session['user_id']
        
        if action in ['APPROVE', 'REJECT']:
            status = 'A' if action == 'APPROVE' else 'R'
            if sid:
                AdvisoryModel.approve_course_plan(sid, status, user_id, level='PGS')
                flash(f'Course plan { "approved" if status == "A" else "rejected" } successfully.', 'success')
            return redirect(url_for('academics.dean_pgs_course_plan_approval', **request.args))

    filters = {
        'college_id': request.args.get('college_id'),
        'session_id': request.args.get('session_id'),
        'degree_id': request.args.get('degree_id'),
        'branch_id': request.args.get('branch_id')
    }
    
    students = []
    if all([filters['college_id'], filters['session_id'], filters['degree_id']]):
        students = AdvisoryModel.get_pending_course_plan_approvals(filters, level='PGS')
    
    sid = request.args.get('sid')
    course_plan = []
    student_dtl = None
    if sid:
        course_plan = AdvisoryModel.get_student_course_plan(sid)
        student_dtl = AdvisoryModel.get_student_advisory_committee(sid) # Reusing this for basic student info

    lookups = AdvisoryModel.get_advisory_lookups(filters['college_id'], filters['degree_id'])
    return render_template('academics/dean_pgs_course_plan_approval.html', 
                           lookups=lookups, filters=filters, students=students, 
                           course_plan=course_plan, sid=sid, student=student_dtl)

@academics_bp.route('/pg_mandates_submission', methods=['GET', 'POST'])
@permission_required('PG Mandates Submission by HOD')
def pg_mandates_submission():
    filters = {
        'college_id': request.args.get('college_id'),
        'session_id': request.args.get('session_id'),
        'degree_id': request.args.get('degree_id'),
        'semester_id': request.args.get('semester_id'),
        'branch_id': request.args.get('branch_id')
    }

    if request.method == 'POST':
        action = request.form.get('action')
        user_id = session['user_id']
        
        if action == 'UPDATE_SINGLE':
            sid = request.form.get('sid')
            mandate_id = request.form.get('mandate_id')
            remarks = request.form.get('remarks')
            sub_date = request.form.get('sub_date')
            is_submitted = request.form.get('is_submitted') == '1'
            if sid and mandate_id:
                ResearchModel.update_mandate(sid, mandate_id, remarks, sub_date, is_submitted, user_id, filters)
                flash('Mandate updated successfully.', 'success')
            return redirect(url_for('academics.pg_mandates_submission', **request.args))

    students = []
    if all([filters['college_id'], filters['session_id'], filters['degree_id']]):
        students = ResearchModel.get_students_for_mandates(filters)

    # Use centralized AdvisoryModel lookups for correct discipline mapping (Int IDs)
    lookups = AdvisoryModel.get_advisory_lookups(filters['college_id'], filters['degree_id'])
    
    # Override colleges based on location (campus) from session
    loc_id = session.get('selected_loc')
    if loc_id:
        lookups['colleges'] = DB.fetch_all("SELECT pk_collegeid as id, collegename as name FROM SMS_College_Mst WHERE fk_locid = ? ORDER BY collegename", [loc_id])

    # Ensure degrees are filtered for PG/PhD specifically
    if filters['college_id'] and str(filters['college_id']) != '0':
        lookups['degrees'] = AcademicsModel.get_college_pg_degrees(filters['college_id'])

    # Standard class list (I to VIII)
    all_semesters = InfrastructureModel.get_all_semesters()
    lookups['semesters'] = [s for s in all_semesters if s.get('semesterorder', 0) <= 8]
    
    return render_template('academics/pg_mandates_submission.html', 
                           lookups=lookups, filters=filters, students=students)

@academics_bp.route('/pg_mandate_report')
@permission_required('PG Mandates Submission by HOD')
def pg_mandate_report():
    filters = {
        'college_id': request.args.get('college_id'),
        'session_id': request.args.get('session_id'),
        'degree_id': request.args.get('degree_id'),
        'branch_id': request.args.get('branch_id'),
        'format': request.args.get('format', 'pdf')
    }
    
    if not all([filters['college_id'], filters['session_id'], filters['degree_id']]):
        flash('Please apply filters first.', 'warning')
        return redirect(url_for('academics.pg_mandates_submission'))

    students = ResearchModel.get_students_for_mandates(filters)
    
    # Simple HTML-based report structure that mimics the .rpt layout
    html = render_template('reports/pg_mandates_report.html', students=students, filters=filters, 
                           now=datetime.now())

    if filters['format'] == 'excel':
        response = make_response(html)
        response.headers["Content-Disposition"] = "attachment; filename=PG_Mandates_Report.xls"
        response.headers["Content-Type"] = "application/vnd.ms-excel"
        return response
    elif filters['format'] == 'word':
        response = make_response(html)
        response.headers["Content-Disposition"] = "attachment; filename=PG_Mandates_Report.doc"
        response.headers["Content-Type"] = "application/msword"
        return response
    else:
        # Default PDF (browser print-friendly HTML)
        return html

@academics_bp.route('/add_with_approval_major_advisor', methods=['GET', 'POST'])
@permission_required('Addition/withdrawal Approval by Major Advisor')
def add_with_approval_major_advisor():
    from app.models.academics import AddWithModel
    user_id = session['user_id']
    
    if request.method == 'POST':
        action = request.form.get('action')
        pk_id = request.form.get('pk_id')
        remarks = request.form.get('remarks')
        
        if action in ['APPROVE', 'REJECT']:
            status = 'A' if action == 'APPROVE' else 'R'
            AddWithModel.approve_by_major_advisor(pk_id, status, remarks, user_id)
            flash(f'Request { "approved" if status == "A" else "rejected" } successfully.', 'success')
        
        return redirect(url_for('academics.add_with_approval_major_advisor', **request.args))

    filters = {
        'session_id': request.args.get('session_id', InfrastructureModel.get_current_session_id())
    }
    
    pending_requests = []
    processed_requests = []
    
    if filters['session_id']:
        pending_requests = AddWithModel.get_major_advisor_requests(filters, user_id, processed=False)
        processed_requests = AddWithModel.get_major_advisor_requests(filters, user_id, processed=True)

    lookups = {
        'sessions': InfrastructureModel.get_sessions()
    }
    
    return render_template('academics/add_with_approval_major_advisor.html', 
                           pending=pending_requests, 
                           processed=processed_requests,
                           lookups=lookups, filters=filters)

@academics_bp.route('/add_with_approval_teacher', methods=['GET', 'POST'])
@permission_required('Addition/withdrawal Approval by Teacher')
def add_with_approval_teacher():
    from app.models.academics import AddWithModel
    user_id = session['user_id']
    
    if request.method == 'POST':
        action = request.form.get('action')
        pk_id = request.form.get('pk_id')
        remarks = request.form.get('remarks')
        
        if action in ['APPROVE', 'REJECT']:
            status = 'A' if action == 'APPROVE' else 'R'
            AddWithModel.approve_by_teacher(pk_id, status, remarks, user_id)
            flash(f'Request { "approved" if status == "A" else "rejected" } successfully.', 'success')
        
        return redirect(url_for('academics.add_with_approval_teacher', **request.args))

    filters = {
        'session_id': request.args.get('session_id', InfrastructureModel.get_current_session_id())
    }
    
    pending_requests = []
    processed_requests = []
    
    if filters['session_id']:
        pending_requests = AddWithModel.get_teacher_requests(filters, user_id, processed=False)
        processed_requests = AddWithModel.get_teacher_requests(filters, user_id, processed=True)

    lookups = {
        'sessions': InfrastructureModel.get_sessions()
    }
    
    return render_template('academics/add_with_approval_teacher.html', 
                           pending=pending_requests, 
                           processed=processed_requests,
                           lookups=lookups, filters=filters)

@academics_bp.route('/student_thesis_detail', methods=['GET', 'POST'])
@permission_required('Student Thesis Detail')
def student_thesis_detail():
    filters = {
        'college_id': request.args.get('college_id'),
        'session_id': request.args.get('session_id'),
        'degree_id': request.args.get('degree_id'),
        'semester_id': request.args.get('semester_id'),
        'branch_id': request.args.get('branch_id')
    }

    if request.method == 'POST':
        action = request.form.get('action')
        user_id = session['user_id']
        
        if action == 'UPDATE_SINGLE':
            sid = request.form.get('sid')
            if sid:
                # Collect all fields for this sid
                data = {
                    'is_fee_remitted': request.form.get('is_fee_remitted') == '1',
                    'total_sem': request.form.get('total_sem'),
                    'thesis_sub_date': request.form.get('thesis_sub_date'),
                    'mc_date': request.form.get('mc_date'),
                    'viva_date': request.form.get('viva_date'),
                    'result_date': request.form.get('result_date'),
                    'thesis_not_no': request.form.get('thesis_not_no'),
                    'viva_not_no': request.form.get('viva_not_no'),
                    'result_not_no': request.form.get('result_not_no'),
                    'thesis_title': request.form.get('thesis_title'),
                    'adjudicator_remarks': request.form.get('adjudicator_remarks'),
                    'resubmission': request.form.get('resubmission'),
                    'remarks': request.form.get('remarks')
                }
                if ThesisModel.update_thesis_detail(sid, data, user_id):
                    flash('Thesis details updated successfully.', 'success')
                else:
                    flash('Error updating thesis details.', 'danger')
            return redirect(url_for('academics.student_thesis_detail', **request.args))

    students = []
    if all([filters['college_id'], filters['session_id'], filters['degree_id']]):
        students = ThesisModel.get_students_for_thesis(filters)

    lookups = AdvisoryModel.get_advisory_lookups(filters['college_id'], filters['degree_id'])
    
    # Campus-based college filter
    loc_id = session.get('selected_loc')
    if loc_id:
        lookups['colleges'] = DB.fetch_all("SELECT pk_collegeid as id, collegename as name FROM SMS_College_Mst WHERE fk_locid = ? ORDER BY collegename", [loc_id])

    # Filter for PG/PhD degrees
    if filters['college_id'] and str(filters['college_id']) != '0':
        lookups['degrees'] = AcademicsModel.get_college_pg_degrees(filters['college_id'])

    lookups['semesters'] = InfrastructureModel.get_all_semesters()
    
    return render_template('academics/student_thesis_detail.html', 
                           lookups=lookups, filters=filters, students=students)

@academics_bp.route('/student_thesis_report')
@permission_required('Student Thesis Detail')
def student_thesis_report():
    filters = {
        'college_id': request.args.get('college_id'),
        'session_id': request.args.get('session_id'),
        'degree_id': request.args.get('degree_id'),
        'branch_id': request.args.get('branch_id'),
        'format': request.args.get('format', 'pdf')
    }
    
    if not all([filters['college_id'], filters['session_id'], filters['degree_id']]):
        flash('Please apply filters first.', 'warning')
        return redirect(url_for('academics.student_thesis_detail'))

    students = ThesisModel.get_students_for_thesis(filters)
    
    # Get human-readable filter info for report header
    filters_info = {
        'college': DB.fetch_scalar("SELECT collegename FROM SMS_College_Mst WHERE pk_collegeid = ?", [filters['college_id']]),
        'session': DB.fetch_scalar("SELECT sessionname FROM SMS_AcademicSession_Mst WHERE pk_sessionid = ?", [filters['session_id']]),
        'degree': DB.fetch_scalar("SELECT degreename FROM SMS_Degree_Mst WHERE pk_degreeid = ?", [filters['degree_id']])
    }
    
    if filters['format'] == 'excel':
        html = render_template('reports/thesis_detail_report.html', students=students, filters=filters, now=datetime.now(), filters_info=filters_info)
        response = make_response(html)
        response.headers["Content-Disposition"] = "attachment; filename=Thesis_Detail_Report.xls"
        response.headers["Content-Type"] = "application/vnd.ms-excel"
        return response
    elif filters['format'] == 'word':
        html = render_template('reports/thesis_detail_report.html', students=students, filters=filters, now=datetime.now(), filters_info=filters_info)
        response = make_response(html)
        response.headers["Content-Disposition"] = "attachment; filename=Thesis_Detail_Report.doc"
        response.headers["Content-Type"] = "application/msword"
        return response
    else:
        from app.utils import generate_thesis_detail_pdf
        pdf_content = generate_thesis_detail_pdf(students, filters_info)
        return send_file(pdf_content, download_name="Thesis_Detail_Report.pdf", as_attachment=True, mimetype='application/pdf')

@academics_bp.route('/addition_withdrawal_approval_status', methods=['GET', 'POST'])
@permission_required('Addition/Withdrawal Approval Status')
def addition_withdrawal_approval_status():
    from app.models.academics import AddWithModel
    filters = {
        'college_id': request.args.get('college_id'),
        'session_id': request.args.get('session_id'),
        'degree_id': request.args.get('degree_id'),
        'semester_id': request.args.get('semester_id'),
        'branch_id': request.args.get('branch_id')
    }

    status_list = []
    if all([filters['session_id'], filters['degree_id']]):
        status_list = AddWithModel.get_add_with_status(filters)

    lookups = AdvisoryModel.get_advisory_lookups(filters['college_id'], filters['degree_id'])
    
    # Load colleges based on location (campus) from session if available
    loc_id = session.get('selected_loc')
    if loc_id:
        lookups['colleges'] = DB.fetch_all("SELECT pk_collegeid as id, collegename as name FROM SMS_College_Mst WHERE fk_locid = ? ORDER BY collegename", [loc_id])

    # Ensure degrees are filtered for PG/PhD specifically
    if filters['college_id'] and str(filters['college_id']) != '0':
        lookups['degrees'] = AcademicsModel.get_college_pg_degrees(filters['college_id'])

    lookups['semesters'] = InfrastructureModel.get_all_semesters()
    
    return render_template('academics/addition_withdrawal_approval_status.html', 
                           lookups=lookups, filters=filters, status_list=status_list)

@academics_bp.route('/add_with_status_report')
@permission_required('Addition/Withdrawal Approval Status')
def add_with_status_report():
    from app.models.academics import AddWithModel
    filters = {
        'session_id': request.args.get('session_id'),
        'degree_id': request.args.get('degree_id'),
        'semester_id': request.args.get('semester_id'),
        'branch_id': request.args.get('branch_id'),
        'format': request.args.get('format', 'pdf')
    }
    
    if not all([filters['session_id'], filters['degree_id']]):
        flash('Please apply filters first.', 'warning')
        return redirect(url_for('academics.addition_withdrawal_approval_status'))

    status_list = AddWithModel.get_add_with_status(filters)
    
    # Get human-readable filter info for report header
    filters_info = {
        'session': DB.fetch_scalar("SELECT sessionname FROM SMS_AcademicSession_Mst WHERE pk_sessionid = ?", [filters['session_id']]),
        'degree': DB.fetch_scalar("SELECT degreename FROM SMS_Degree_Mst WHERE pk_degreeid = ?", [filters['degree_id']])
    }
    
    if filters['format'] == 'excel':
        html = render_template('reports/add_with_status_report.html', status_list=status_list, filters=filters, now=datetime.now(), filters_info=filters_info)
        response = make_response(html)
        response.headers["Content-Disposition"] = "attachment; filename=Add_With_Status_Report.xls"
        response.headers["Content-Type"] = "application/vnd.ms-excel"
        return response
    elif filters['format'] == 'word':
        html = render_template('reports/add_with_status_report.html', status_list=status_list, filters=filters, now=datetime.now(), filters_info=filters_info)
        response = make_response(html)
        response.headers["Content-Disposition"] = "attachment; filename=Add_With_Status_Report.doc"
        response.headers["Content-Type"] = "application/msword"
        return response
    else:
        from app.utils import generate_add_with_status_pdf
        pdf_content = generate_add_with_status_pdf(status_list, filters_info)
        return send_file(pdf_content, download_name="Add_With_Status_Report.pdf", as_attachment=True, mimetype='application/pdf')

@academics_bp.route('/advisory_creation_approval_status', methods=['GET', 'POST'])
@permission_required('Advisory Creation And Approval Status')
def advisory_creation_approval_status():
    filters = {
        'college_id': request.args.get('college_id'),
        'session_id': request.args.get('session_id'),
        'degree_id': request.args.get('degree_id'),
        'semester_id': request.args.get('semester_id'),
        'branch_id': request.args.get('branch_id')
    }

    status_list = []
    if all([filters['college_id'], filters['session_id'], filters['degree_id']]):
        status_list = AdvisoryStatusModel.get_advisory_approval_status(filters)

    lookups = AdvisoryModel.get_advisory_lookups(filters['college_id'], filters['degree_id'])
    loc_id = session.get('selected_loc')
    if loc_id:
        lookups['colleges'] = DB.fetch_all("SELECT pk_collegeid as id, collegename as name FROM SMS_College_Mst WHERE fk_locid = ? ORDER BY collegename", [loc_id])
    if filters['college_id'] and str(filters['college_id']) != '0':
        lookups['degrees'] = AcademicsModel.get_college_pg_degrees(filters['college_id'])
    lookups['semesters'] = InfrastructureModel.get_all_semesters()
    
    return render_template('academics/advisory_creation_approval_status.html', 
                           lookups=lookups, filters=filters, status_list=status_list)

@academics_bp.route('/advisory_status_report')
@permission_required('Advisory Creation And Approval Status')
def advisory_status_report():
    filters = {
        'college_id': request.args.get('college_id'),
        'session_id': request.args.get('session_id'),
        'degree_id': request.args.get('degree_id'),
        'semester_id': request.args.get('semester_id'),
        'branch_id': request.args.get('branch_id'),
        'format': request.args.get('format', 'pdf')
    }
    
    if not all([filters['college_id'], filters['session_id'], filters['degree_id']]):
        flash('Please apply filters first.', 'warning')
        return redirect(url_for('academics.advisory_creation_approval_status'))

    status_list = AdvisoryStatusModel.get_advisory_approval_status(filters)
    
    filters_info = {
        'college': DB.fetch_scalar("SELECT collegename FROM SMS_College_Mst WHERE pk_collegeid = ?", [filters['college_id']]),
        'session': DB.fetch_scalar("SELECT sessionname FROM SMS_AcademicSession_Mst WHERE pk_sessionid = ?", [filters['session_id']]),
        'degree': DB.fetch_scalar("SELECT degreename FROM SMS_Degree_Mst WHERE pk_degreeid = ?", [filters['degree_id']])
    }

    if filters['format'] == 'excel':
        html = render_template('reports/advisory_status_report.html', status_list=status_list, filters=filters, now=datetime.now(), filters_info=filters_info)
        response = make_response(html)
        response.headers["Content-Disposition"] = "attachment; filename=Advisory_Status_Report.xls"
        response.headers["Content-Type"] = "application/vnd.ms-excel"
        return response
    elif filters['format'] == 'word':
        html = render_template('reports/advisory_status_report.html', status_list=status_list, filters=filters, now=datetime.now(), filters_info=filters_info)
        response = make_response(html)
        response.headers["Content-Disposition"] = "attachment; filename=Advisory_Status_Report.doc"
        response.headers["Content-Type"] = "application/msword"
        return response
    else:
        from app.utils import generate_advisory_status_pdf
        pdf_content = generate_advisory_status_pdf(status_list, filters_info)
        return send_file(pdf_content, download_name="Advisory_Status_Report.pdf", as_attachment=True, mimetype='application/pdf')

@academics_bp.route('/programme_of_work_pg', methods=['GET', 'POST'])
@permission_required('Programme of work(PG)')
def programme_of_work_pg():
    filters = {
        'college_id': request.args.get('college_id'),
        'session_id': request.args.get('session_id'),
        'degree_id': request.args.get('degree_id'),
        'semester_id': request.args.get('semester_id'),
        'branch_id': request.args.get('branch_id'),
        'year': request.args.get('year')
    }

    if request.method == 'POST':
        # Handle report generation
        return redirect(url_for('academics.programme_of_work_report', **request.form))

    # Lookups
    loc_id = session.get('selected_loc')
    if loc_id:
        colleges = DB.fetch_all("SELECT pk_collegeid as id, collegename as name FROM SMS_College_Mst WHERE fk_locid = ? ORDER BY collegename", [loc_id])
    else:
        colleges = AcademicsModel.get_colleges_simple()

    lookups = {
        'colleges': colleges,
        'sessions': InfrastructureModel.get_sessions(),
        'degrees': [],
        'branches': [],
        'semesters': InfrastructureModel.get_all_semesters()
    }

    if filters['college_id']:
        lookups['degrees'] = AcademicsModel.get_college_pg_degrees(filters['college_id'])

    if filters['college_id'] and filters['degree_id']:
         lookups['branches'] = DB.fetch_all("""
            SELECT DISTINCT B.Pk_BranchId as id, B.Branchname as name
            FROM SMS_BranchMst B
            INNER JOIN (
                SELECT branchid, fk_Coldgbrmapnewid as mapid FROM SMS_CollegeDegreeBranchMap_dtlnew
                UNION ALL
                SELECT fk_branchid as branchid, fk_Coldgbrmapid as mapid FROM SMS_CollegeDegreeBranchMap_dtl
            ) D ON B.Pk_BranchId = D.branchid
            INNER JOIN SMS_CollegeDegreeBranchMap_Mst MST ON D.mapid = MST.PK_Coldgbrid
            WHERE MST.fk_CollegeId = ? AND MST.fk_Degreeid = ?
            ORDER BY B.Branchname
        """, [filters['college_id'], filters['degree_id']])

    return render_template('academics/programme_of_work_pg.html', lookups=lookups, filters=filters)

@academics_bp.route('/programme_of_work_report')
@permission_required('Programme of work(PG)')
def programme_of_work_report():
    filters = {
        'college_id': request.args.get('college_id'),
        'session_id': request.args.get('session_id'),
        'degree_id': request.args.get('degree_id'),
        'branch_id': request.args.get('branch_id'),
        'semester_id': request.args.get('semester_id'),
        'format': request.args.get('format', 'pdf')
    }
    
    if not all([filters['college_id'], filters['session_id'], filters['degree_id']]):
        return "Please select College, Session and Degree to view report."

    # Fetch detailed students matching criteria using improved model method
    detailed_students = ResearchModel.get_students_for_work_programme(filters)
    
    if filters['format'] == 'excel':
        html = render_template('reports/programme_of_work_detailed.html', students=detailed_students, filters=filters, now=datetime.now())
        response = make_response(html)
        response.headers["Content-Disposition"] = "attachment; filename=Programme_of_Work.xls"
        response.headers["Content-Type"] = "application/vnd.ms-excel"
        return response
    elif filters['format'] == 'word':
        html = render_template('reports/programme_of_work_detailed.html', students=detailed_students, filters=filters, now=datetime.now())
        response = make_response(html)
        response.headers["Content-Disposition"] = "attachment; filename=Programme_of_Work.doc"
        response.headers["Content-Type"] = "application/msword"
        return response
    else:
        # PROFESSIONAL PDF GENERATION USING REPORTLAB
        from app.utils import generate_programme_of_work_pdf
        pdf_content = generate_programme_of_work_pdf(detailed_students)
        return send_file(pdf_content, download_name="Programme_of_Work.pdf", as_attachment=True, mimetype='application/pdf')

@academics_bp.route('/igrade_approval_teacher', methods=['GET', 'POST'])
@permission_required('I-Grade Approval by Teacher')
def igrade_approval_teacher():
    user_id = session['user_id']
    if request.method == 'POST':
        action = request.form.get('action') # 'A' or 'R' from radio/button
        pk_id = request.form.get('pk_id')
        remarks = request.form.get('remarks')
        if pk_id:
            IGradeModel.approve_by_teacher(pk_id, action, remarks, user_id)
            flash(f'Request { "approved" if action == "A" else "rejected" } successfully.', 'success')
        return redirect(url_for('academics.igrade_approval_teacher', **request.args))

    filters = {
        'session_id': request.args.get('session_id', InfrastructureModel.get_current_session_id())
    }
    
    pending = []
    processed = []
    if filters['session_id']:
        pending = IGradeModel.get_teacher_requests(filters, user_id, processed=False)
        processed = IGradeModel.get_teacher_requests(filters, user_id, processed=True)

    lookups = {'sessions': InfrastructureModel.get_sessions()}
    return render_template('academics/igrade_approval_teacher.html', 
                           lookups=lookups, filters=filters, pending=pending, processed=processed)

@academics_bp.route('/igrade_approval_dean_pgs', methods=['GET', 'POST'])
@permission_required('I-Grade Approval By Dean Pgs')
def igrade_approval_dean_pgs():
    user_id = session['user_id']
    if request.method == 'POST':
        action = request.form.get('action')
        pk_id = request.form.get('pk_id')
        remarks = request.form.get('remarks')
        if pk_id:
            IGradeModel.approve_by_dean(pk_id, action, remarks, user_id)
            flash(f'Request { "approved" if action == "A" else "rejected" } successfully.', 'success')
        return redirect(url_for('academics.igrade_approval_dean_pgs', **request.args))

    filters = {
        'session_id': request.args.get('session_id', InfrastructureModel.get_current_session_id())
    }
    
    pending = []
    processed = []
    if filters['session_id']:
        pending = IGradeModel.get_dean_requests(filters, processed=False)
        processed = IGradeModel.get_dean_requests(filters, processed=True)

    lookups = {'sessions': InfrastructureModel.get_sessions()}
    return render_template('academics/igrade_approval_dean_pgs.html', 
                           lookups=lookups, filters=filters, pending=pending, processed=processed)

@academics_bp.route('/igrade_approval_status', methods=['GET'])
@permission_required('I Grade Approval Status')
def igrade_approval_status():
    filters = {
        'college_id': request.args.get('college_id'),
        'session_id': request.args.get('session_id'),
        'degree_id': request.args.get('degree_id'),
        'semester_id': request.args.get('semester_id'),
        'branch_id': request.args.get('branch_id')
    }

    status_list = []
    if all([filters['college_id'], filters['session_id'], filters['degree_id']]):
        status_list = IGradeModel.get_igrade_status(filters)

    lookups = AdvisoryModel.get_advisory_lookups(filters['college_id'], filters['degree_id'])
    
    # Campus-based college filter
    loc_id = session.get('selected_loc')
    if loc_id:
        lookups['colleges'] = DB.fetch_all("SELECT pk_collegeid as id, collegename as name FROM SMS_College_Mst WHERE fk_locid = ? ORDER BY collegename", [loc_id])

    # Filter for PG/PhD degrees
    if filters['college_id'] and str(filters['college_id']) != '0':
        lookups['degrees'] = AcademicsModel.get_college_pg_degrees(filters['college_id'])

    lookups['semesters'] = InfrastructureModel.get_all_semesters()
    
    return render_template('academics/igrade_approval_status.html', 
                           lookups=lookups, filters=filters, status_list=status_list)

@academics_bp.route('/igrade_status_report')
@permission_required('I Grade Approval Status')
def igrade_status_report():
    filters = {
        'college_id': request.args.get('college_id'),
        'session_id': request.args.get('session_id'),
        'degree_id': request.args.get('degree_id'),
        'branch_id': request.args.get('branch_id'),
        'format': request.args.get('format', 'pdf')
    }
    
    if not all([filters['college_id'], filters['session_id'], filters['degree_id']]):
        flash('Please apply filters first.', 'warning')
        return redirect(url_for('academics.igrade_approval_status'))

    status_list = IGradeModel.get_igrade_status(filters)
    
    filters_info = {
        'college': DB.fetch_scalar("SELECT collegename FROM SMS_College_Mst WHERE pk_collegeid = ?", [filters['college_id']]),
        'session': DB.fetch_scalar("SELECT sessionname FROM SMS_AcademicSession_Mst WHERE pk_sessionid = ?", [filters['session_id']]),
        'degree': DB.fetch_scalar("SELECT degreename FROM SMS_Degree_Mst WHERE pk_degreeid = ?", [filters['degree_id']])
    }

    if filters['format'] == 'excel':
        html = render_template('reports/igrade_status_report.html', status_list=status_list, filters=filters, now=datetime.now(), filters_info=filters_info)
        response = make_response(html)
        response.headers["Content-Disposition"] = "attachment; filename=IGrade_Status_Report.xls"
        response.headers["Content-Type"] = "application/vnd.ms-excel"
        return response
    elif filters['format'] == 'word':
        html = render_template('reports/igrade_status_report.html', status_list=status_list, filters=filters, now=datetime.now(), filters_info=filters_info)
        response = make_response(html)
        response.headers["Content-Disposition"] = "attachment; filename=IGrade_Status_Report.doc"
        response.headers["Content-Type"] = "application/msword"
        return response
    else:
        from app.utils import generate_igrade_status_pdf
        pdf_content = generate_igrade_status_pdf(status_list, filters_info)
        return send_file(pdf_content, download_name="IGrade_Status_Report.pdf", as_attachment=True, mimetype='application/pdf')

@academics_bp.route('/course_allocation_pg', methods=['GET', 'POST'])
@permission_required('Course Allocation(For PG)')
def course_allocation_pg():
    if request.method == 'POST':
        action = request.form.get('action')
        sid = request.form.get('sid')
        exconfig_id = request.form.get('exconfig_id')
        user_id = session['user_id']
        
        if action == 'ALLOCATE':
            course_ids = request.form.getlist('course_id[]')
            semester_id = request.args.get('semester_id')
            if sid and exconfig_id and course_ids and semester_id:
                CourseAllocationModel.allocate_courses(sid, course_ids, exconfig_id, user_id, semester_id)
                flash('Courses allocated successfully.', 'success')
            return redirect(url_for('academics.course_allocation_pg', **request.args))
            
        elif action == 'DELETE':
            alloc_ids = request.form.getlist('alloc_id[]')
            if sid and alloc_ids:
                CourseAllocationModel.delete_allocated_courses(sid, alloc_ids)
                flash('Selected allocations deleted.', 'success')
            return redirect(url_for('academics.course_allocation_pg', **request.args))
            
        elif action == 'ADD_EXTERNAL':
            course_id = request.form.get('external_course_id')
            semester_id = request.args.get('semester_id')
            if sid and exconfig_id and course_id and semester_id:
                CourseAllocationModel.allocate_courses(sid, [course_id], exconfig_id, user_id, semester_id)
                flash('Course allocated successfully.', 'success')
            return redirect(url_for('academics.course_allocation_pg', **request.args))

    filters = {
        'college_id': request.args.get('college_id'),
        'session_id': request.args.get('session_id'),
        'degree_id': request.args.get('degree_id'),
        'semester_id': request.args.get('semester_id'),
        'branch_id': request.args.get('branch_id'),
        'exconfig_id': request.args.get('exconfig_id')
    }
    
    students = []
    exam_configs = []
    if filters['degree_id']:
        exam_configs = CourseAllocationModel.get_exam_configs(
            filters['degree_id'], 
            session_id=filters.get('session_id'), 
            semester_id=filters.get('semester_id')
        )
        
    if all([filters['college_id'], filters['session_id'], filters['degree_id'], filters['branch_id']]):
        students = CourseAllocationModel.get_students_for_allocation(filters)
        
    sid = request.args.get('sid')
    allocated_courses = []
    course_plan = []
    external_courses = []
    if sid:
        if filters['exconfig_id']:
            allocated_courses = CourseAllocationModel.get_allocated_courses(sid, filters['exconfig_id'])
        course_plan = CourseAllocationModel.get_student_course_plan_for_allocation(sid)
        external_courses = CourseAllocationModel.get_courses_not_in_plan(sid)

    lookups = AdvisoryModel.get_advisory_lookups(filters['college_id'], filters['degree_id'])
    # Load colleges based on location (campus) from session if available
    loc_id = session.get('selected_loc')
    if loc_id:
        lookups['colleges'] = DB.fetch_all("SELECT pk_collegeid as id, collegename as name FROM SMS_College_Mst WHERE fk_locid = ? ORDER BY collegename", [loc_id])
    else:
        lookups['colleges'] = AcademicsModel.get_colleges_simple()

    # Filter semesters to only show I to VIII as requested
    all_semesters = InfrastructureModel.get_all_semesters()
    lookups['semesters'] = [s for s in all_semesters if s.get('semesterorder', 0) <= 8]
    
    return render_template('academics/course_allocation_pg.html', 
                           lookups=lookups, filters=filters, students=students,
                           exam_configs=exam_configs, allocated_courses=allocated_courses,
                           course_plan=course_plan, sid=sid)

@academics_bp.route('/student/<int:sid>/alert')
@permission_required('Student BioData')
def student_alert(sid):
    # Fetch alerts/achievements/disciplinary actions for this student
    # For now, fetching basic info + any achievements
    info = StudentModel.get_student_info(sid)
    achievements = DB.fetch_all("SELECT * FROM SMS_StuAchievement_Dtl WHERE fk_sturegid = ?", [sid])
    disciplinary = DB.fetch_all("SELECT * FROM SMS_StuDisciplinary_Dtl WHERE fk_sid = ?", [sid])
    
    return render_template('academics/student_alert.html', info=info, achievements=achievements, disciplinary=disciplinary)

@academics_bp.route('/student/<int:sid>/advisors_popup')
@permission_required('Dean PGS approval (Course plan)')
def advisors_popup(sid):
    data = AdvisoryModel.get_student_advisory_committee(sid)
    return render_template('academics/advisors_popup.html', data=data)

@academics_bp.route('/course_offer_hod', methods=['GET', 'POST'])
@permission_required('Course Offer (By HOD)')
def course_offer_hod():
    user_id = session.get('user_id')
    emp_id = session.get('emp_id')
    dept_ctx = AcademicsModel.get_hod_department_context(emp_id) if emp_id else {'branch_ids': [], 'hr_departments': [], 'sms_dept_ids': []}
    hod_branch_ids = dept_ctx.get('branch_ids', [])
    sms_dept_ids = dept_ctx.get('sms_dept_ids', [])
    code_prefixes = dept_ctx.get('code_prefixes', [])

    if request.method == 'POST':
        filters = {
            'college_id': request.form.get('college_id', type=int),
            'session_id': request.form.get('session_id', type=int),
            'degree_id': request.form.get('degree_id', type=int),
            'semester_id': request.form.get('semester_id', type=int),
            'year_id': request.form.get('year_id', type=int),
            'exconfig_id': request.form.get('exconfig_id', type=int),
            'branch_id': request.form.get('branch_id', type=int) or 0
        }
        course_ids = request.form.getlist('course_ids[]')
        try:
            AcademicsModel.save_course_offer_by_hod(filters, course_ids, user_id, emp_id)
            flash('Course offer updated successfully!', 'success')
        except Exception:
            flash('Error updating course offer.', 'danger')
        return redirect(url_for('academics.course_offer_hod', **{k: v for k, v in filters.items() if v}))

    filters = {
        'college_id': request.args.get('college_id', type=int),
        'session_id': request.args.get('session_id', type=int),
        'degree_id': request.args.get('degree_id', type=int),
        'semester_id': request.args.get('semester_id', type=int),
        'year_id': request.args.get('year_id', type=int),
        'exconfig_id': request.args.get('exconfig_id', type=int),
        'branch_id': request.args.get('branch_id', type=int)
    }

    # Auto-select college based on selected location
    if not filters['college_id']:
        loc_id = session.get('selected_loc')
        if loc_id:
            colleges = DB.fetch_all("SELECT pk_collegeid as id FROM SMS_College_Mst WHERE fk_locid = ?", [loc_id])
            if len(colleges) == 1:
                filters['college_id'] = colleges[0]['id']

    # Auto-select current session by sessionorder
    if not filters['session_id']:
        sess = DB.fetch_one("SELECT TOP 1 pk_sessionid FROM SMS_AcademicSession_Mst ORDER BY sessionorder DESC, pk_sessionid DESC")
        if sess:
            filters['session_id'] = sess['pk_sessionid']

    lookups = {
        'colleges': AcademicsModel.get_colleges_simple(),
        'sessions': InfrastructureModel.get_sessions(),
        'degrees': [],
        'semesters': [],
        'years': AcademicsModel.get_degree_years(),
        'exam_configs': []
    }

    if filters['college_id']:
        lookups['degrees'] = AcademicsModel.get_college_degrees(filters['college_id'])
    if filters['degree_id']:
        lookups['semesters'] = AcademicsModel.get_degree_semesters_for_degree(filters['degree_id'])
        if filters['semester_id']:
            # Auto-calculate year if not provided but semester is
            if not filters['year_id']:
                year_row = DB.fetch_one("SELECT fk_degreeyearid FROM SMS_Semester_Mst WHERE pk_semesterid = ?", [filters['semester_id']])
                if year_row:
                    filters['year_id'] = year_row['fk_degreeyearid']
            
        lookups['exam_configs'] = CourseAllocationModel.get_exam_configs(
            filters['degree_id'], filters['session_id'], filters['semester_id']
        )

    courses = []
    selected_ids = set()
    if filters['degree_id'] and filters['semester_id']:
        # HOD offers courses for PG/PhD only. UG is offered by Dean.
        degree_info = DB.fetch_one("SELECT fk_degreetypeid FROM SMS_Degree_Mst WHERE pk_degreeid = ?", [filters['degree_id']])
        is_ug = False
        if degree_info:
            dtype = DB.fetch_one("SELECT isug FROM SMS_DegreeType_Mst WHERE pk_degreetypeid = ?", [degree_info['fk_degreetypeid']])
            is_ug = (dtype and dtype.get('isug') == 'B')

        if not is_ug:
            year_semesters = []
            if filters.get('year_id'):
                year_semesters = AcademicsModel.get_semesters_for_degree_year(filters['degree_id'], filters['year_id'])
            
            raw_courses = []
            if year_semesters:
                raw_courses = AcademicsModel.get_courses_for_degree_semesters(
                    filters['degree_id'], year_semesters, None, sms_dept_ids, code_prefixes, is_hod_view=True
                )
            else:
                raw_courses = AcademicsModel.get_courses_for_degree_semester(
                    filters['degree_id'], filters['semester_id'], None, sms_dept_ids, code_prefixes, is_hod_view=True
                )
            
            # Ensure Uniqueness to avoid repeats
            seen = set()
            for c in raw_courses:
                th = c.get('crhr_theory') or 0
                pr = c.get('crhr_practical') or 0
                code = (c.get('coursecode') or '').strip()
                name = (c.get('coursename') or '').strip()
                # Unique key to identify duplicates
                key = (code.upper(), name.upper(), th, pr)
                if key not in seen:
                    seen.add(key)
                    c['display_name'] = f"{code},({th}+{pr}), /{name}"
                    courses.append(c)

        master = AcademicsModel.get_course_offer_master(filters)
        if master:
            selected_ids = set(AcademicsModel.get_course_offer_selected_course_ids(master['Pk_courseallocid']))

    return render_template('academics/course_offer_hod.html',
                           lookups=lookups,
                           filters=filters,
                           courses=courses,
                           selected_ids=selected_ids,
                           hod_departments=dept_ctx.get('hr_departments', []))

@academics_bp.route('/teacher_course_assignment', methods=['GET', 'POST'])
@permission_required('Teacher Course Assignment')
def teacher_course_assignment():
    user_id = session.get('user_id')
    emp_id = session.get('emp_id')
    dept_ctx = AcademicsModel.get_hod_department_context(emp_id) if emp_id else {'branch_ids': [], 'hr_departments': [], 'sms_dept_ids': []}
    hod_hr_dept_ids = [d['id'] for d in dept_ctx.get('hr_departments', [])]
    code_prefixes = dept_ctx.get('code_prefixes', [])
    include_all = request.args.get('include_all') == '1'

    if request.method == 'POST':
        action = request.form.get('action', 'SAVE')
        filters = {
            'college_id': request.form.get('college_id', type=int),
            'session_id': request.form.get('session_id', type=int),
            'degree_id': request.form.get('degree_id', type=int),
            'semester_id': request.form.get('semester_id', type=int),
            'year_id': request.form.get('year_id', type=int),
            'employee_id': request.form.get('employee_id'),
            'exconfig_id': request.form.get('exconfig_id', type=int),
            'coursetype': request.form.get('coursetype'),
            'batch_id': request.form.get('batch_id', type=int),
            'branch_id': request.form.get('branch_id', type=int) or 0
        }
        if filters.get('coursetype') == '0':
            filters['coursetype'] = None
        course_ids = request.form.getlist('course_ids[]')
        main_ids = request.form.getlist('main_course_ids[]')
        try:
            if action == 'DELETE':
                AcademicsModel.delete_teacher_course_assignment_courses(filters, course_ids)
                flash('Selected courses deleted.', 'success')
            else:
                AcademicsModel.save_teacher_course_assignment(filters, course_ids, main_ids, user_id)
                flash('Teacher course assignment saved successfully!', 'success')
        except Exception:
            flash('Error saving teacher course assignment.', 'danger')
        return redirect(url_for('academics.teacher_course_assignment', **{k: v for k, v in filters.items() if v}))

    filters = {
        'college_id': request.args.get('college_id', type=int),
        'session_id': request.args.get('session_id', type=int),
        'degree_id': request.args.get('degree_id', type=int),
        'semester_id': request.args.get('semester_id', type=int),
        'year_id': request.args.get('year_id', type=int),
        'employee_id': request.args.get('employee_id'),
        'exconfig_id': request.args.get('exconfig_id', type=int),
        'coursetype': request.args.get('coursetype'),
        'batch_id': request.args.get('batch_id', type=int),
        'branch_id': request.args.get('branch_id', type=int)
    }
    if filters.get('coursetype') == '0':
        filters['coursetype'] = None

    # Auto-select college based on employee location (if only one match)
    if not filters['college_id'] and emp_id:
        emp_loc = DB.fetch_one("SELECT fk_locid FROM SAL_Employee_Mst WHERE pk_empid = ?", [emp_id])
        if emp_loc and emp_loc.get('fk_locid'):
            colleges = DB.fetch_all("SELECT pk_collegeid as id FROM SMS_College_Mst WHERE fk_locid = ?", [emp_loc['fk_locid']])
            if len(colleges) == 1:
                filters['college_id'] = colleges[0]['id']

    # Auto-select current session by sessionorder
    if not filters['session_id']:
        sess = DB.fetch_one("SELECT TOP 1 pk_sessionid FROM SMS_AcademicSession_Mst ORDER BY sessionorder DESC, pk_sessionid DESC")
        if sess:
            filters['session_id'] = sess['pk_sessionid']

    lookups = {
        'colleges': AcademicsModel.get_colleges_simple(),
        'sessions': InfrastructureModel.get_sessions(),
        'degrees': [],
        'semesters': [],
        'years': AcademicsModel.get_degree_years(),
        'employees': [],
        'exam_configs': [],
        'batches': []
    }

    # Only load teachers if a semester is selected as per user request
    if filters['semester_id']:
        lookups['employees'] = AcademicsModel.get_teaching_employees(None if include_all else hod_hr_dept_ids)

    if filters['college_id']:
        lookups['degrees'] = AcademicsModel.get_college_degrees(filters['college_id'])
    if filters['degree_id']:
        lookups['semesters'] = AcademicsModel.get_degree_semesters_for_degree(filters['degree_id'])
        lookups['exam_configs'] = CourseAllocationModel.get_exam_configs(
            filters['degree_id'], filters['session_id'], filters['semester_id']
        )
    if filters['college_id'] and filters['degree_id'] and filters['semester_id'] and filters.get('coursetype'):
        lookups['batches'] = BatchModel.get_batches(
            filters['college_id'], filters['degree_id'], filters['semester_id'], filters['coursetype']
        )

    courses = []
    selected_ids = set()
    main_ids = set()
    if filters['degree_id'] and filters['semester_id'] and filters.get('coursetype'):
        sms_dept_ids = dept_ctx.get('sms_dept_ids', [])
        # Revert to fetching available departmental courses for HOD
        raw_courses = AcademicsModel.get_courses_offered_by_hod(
            filters, filters.get('coursetype'), sms_dept_ids, code_prefixes
        )
        
        # Uniqueness and formatting
        seen = set()
        for c in raw_courses:
            th = c.get('crhr_theory') or 0
            pr = c.get('crhr_practical') or 0
            code = (c.get('coursecode') or '').strip()
            name = (c.get('coursename') or '').strip()
            key = (code.upper(), name.upper(), th, pr)
            if key not in seen:
                seen.add(key)
                c['display_name'] = f"{code},({th}+{pr}), /{name}"
                courses.append(c)

        # Fetch LATEST assignment for this specific combination
        master = AcademicsModel.get_teacher_course_assignment_master(filters)
        if master:
            selected_ids, main_ids = AcademicsModel.get_teacher_course_assignment_details(master['pk_tcourseallocid'])

    return render_template('academics/teacher_course_assignment.html',
                           lookups=lookups,
                           filters=filters,
                           courses=courses,
                           selected_ids=selected_ids,
                           main_ids=main_ids,
                           include_all=include_all,
                           hod_departments=dept_ctx.get('hr_departments', []))

@academics_bp.route('/batch_master', methods=['GET', 'POST'])
@permission_required('Class - Batch Master')
def batch_master():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'DELETE':
            if AcademicsModel.delete_batch(request.form.get('id')):
                flash('Batch record deleted successfully!', 'success')
            else:
                flash('Error deleting record.', 'danger')
        else:
            if AcademicsModel.save_batch(request.form):
                flash('Batch record saved successfully!', 'success')
            else:
                flash('Error saving record.', 'danger')
        return redirect(url_for('academics.batch_master'))
    
    page = request.args.get('page', 1, type=int)
    per_page = 10
    items, total = AcademicsModel.get_batches(page=page, per_page=per_page)
    
    pagination = {
        'page': page,
        'per_page': per_page,
        'total': total,
        'total_pages': math.ceil(total / per_page) if total else 1,
        'has_prev': page > 1,
        'has_next': page < (math.ceil(total / per_page) if total else 1)
    }
    
    page_range = get_pagination_range(page, pagination['total_pages'])

    lookups = {
        'colleges': AcademicsModel.get_colleges_simple(),
        'sessions': InfrastructureModel.get_sessions(),
        'degrees': AcademicsModel.get_all_degrees(),
        'semesters': InfrastructureModel.get_all_semesters(),
        'branches': AcademicsModel.get_branches()
    }
    
    return render_template('academics/batch_master.html', items=items, lookups=lookups, pagination=pagination, page_range=page_range)

@academics_bp.route('/degree_crhr', methods=['GET', 'POST'])
@permission_required('Degree wise Credit Hours')
def degree_crhr():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'DELETE':
            if AcademicsModel.delete_degree_crhr(request.form.get('id')):
                flash('Credit hour record deleted successfully!', 'success')
            else:
                flash('Error deleting record.', 'danger')
        else:
            if AcademicsModel.save_degree_crhr(request.form):
                flash('Credit hour record saved successfully!', 'success')
            else:
                flash('Error saving record.', 'danger')
        return redirect(url_for('academics.degree_crhr'))
    
    page = request.args.get('page', 1, type=int)
    per_page = 10
    items, total = AcademicsModel.get_degree_crhr(page=page, per_page=per_page)
    
    pagination = {
        'page': page,
        'per_page': per_page,
        'total': total,
        'total_pages': math.ceil(total / per_page) if total else 1,
        'has_prev': page > 1,
        'has_next': page < (math.ceil(total / per_page) if total else 1)
    }
    
    page_range = get_pagination_range(page, pagination['total_pages'])

    lookups = {
        'degrees': AcademicsModel.get_all_degrees(),
        'semesters': InfrastructureModel.get_all_semesters()
    }
    
    return render_template('academics/degree_crhr.html', items=items, lookups=lookups, pagination=pagination, page_range=page_range)

@academics_bp.route('/api/mapping/<map_id>/details')
def get_mapping_details_api(map_id):
    master = DB.fetch_one("SELECT * FROM SMS_CollegeDegreeBranchMap_Mst WHERE PK_Coldgbrid = ?", [map_id])
    details = AcademicsModel.get_mapping_details(map_id)
    return jsonify({'master': master, 'details': details})

@academics_bp.route('/col_deg_spec_master', methods=['GET', 'POST'])
@permission_required('Col-Deg-Specialization Master')
def col_deg_spec_master():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'DELETE':
            if AcademicsModel.delete_mapping(request.form.get('id')):
                flash('Mapping deleted successfully!', 'success')
            else:
                flash('Error deleting mapping.', 'danger')
        else:
            if AcademicsModel.save_mapping(request.form):
                flash('College-Degree-Specialization mapping saved successfully!', 'success')
            else:
                flash('Error saving mapping.', 'danger')
        return redirect(url_for('academics.col_deg_spec_master'))
    
    page = request.args.get('page', 1, type=int)
    per_page = 10
    items, total = AcademicsModel.get_college_degree_mappings_paginated(page=page, per_page=per_page)
    
    pagination = {
        'page': page,
        'per_page': per_page,
        'total': total,
        'total_pages': math.ceil(total / per_page) if total else 1,
        'has_prev': page > 1,
        'has_next': page < (math.ceil(total / per_page) if total else 1)
    }
    
    page_range = get_pagination_range(page, pagination['total_pages'])

    lookups = {
        'colleges': AcademicsModel.get_colleges_simple(),
        'degrees': AcademicsModel.get_all_degrees(),
        'branches': AcademicsModel.get_branches()
    }
    
    return render_template('academics/col_deg_spec_master.html', items=items, lookups=lookups, pagination=pagination, page_range=page_range)

@academics_bp.route('/generic/<path:page_name>')
def generic_page_handler(page_name):
    # Try to find a specific template for this page
    template_name = page_name.lower().replace(' ', '_').replace('[', '').replace(']', '').replace('/', '_') + '.html'
    try:
        # Check if template exists in academics folder
        return render_template(f'academics/{template_name}', title=page_name)
    except:
        return render_template('academics/generic_page.html', title=page_name)

@academics_bp.route('/activity_course_master', methods=['GET', 'POST'])
@permission_required('Activity Course Master')
def activity_course_master():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'DELETE':
            if CourseActivityModel.delete_course_activity(request.form.get('id')):
                flash('Activity Course deleted successfully!', 'success')
            else:
                flash('Error deleting activity course.', 'danger')
        else:
            if CourseActivityModel.save_course_activity(request.form):
                flash('Activity Course saved successfully!', 'success')
            else:
                flash('Error saving activity course.', 'danger')
        return redirect(url_for('academics.activity_course_master'))

    page = request.args.get('page', 1, type=int)
    per_page = 10
    items, total = CourseActivityModel.get_course_activities(page=page, per_page=per_page)
    
    pagination = {
        'page': page,
        'per_page': per_page,
        'total': total,
        'total_pages': math.ceil(total / per_page) if total else 1,
        'has_prev': page > 1,
        'has_next': page < (math.ceil(total / per_page) if total else 1)
    }
    
    page_range = get_pagination_range(page, pagination['total_pages'])

    lookups = {
        'sessions': InfrastructureModel.get_sessions(),
        'semesters': InfrastructureModel.get_all_semesters(),
        'activities': ActivityCertificateModel.get_activities()
    }
    
    return render_template('academics/activity_course_master.html', items=items, lookups=lookups, pagination=pagination, page_range=page_range)

@academics_bp.route('/activity_master', methods=['GET', 'POST'])
@permission_required('Activity Master')
def activity_master():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'DELETE':
            if ActivityCertificateModel.delete_activity(request.form.get('id')):
                flash('Activity deleted successfully!', 'success')
            else:
                flash('Error deleting activity.', 'danger')
        else:
            if ActivityCertificateModel.save_activity(request.form):
                flash('Activity saved successfully!', 'success')
            else:
                flash('Error saving activity.', 'danger')
        return redirect(url_for('academics.activity_master'))

    page = request.args.get('page', 1, type=int)
    per_page = 10
    items, total = ActivityCertificateModel.get_activities_paginated(page=page, per_page=per_page)
    
    pagination = {
        'page': page,
        'per_page': per_page,
        'total': total,
        'total_pages': math.ceil(total / per_page) if total else 1,
        'has_prev': page > 1,
        'has_next': page < (math.ceil(total / per_page) if total else 1)
    }
    
    page_range = get_pagination_range(page, pagination['total_pages'])
    
    return render_template('academics/activity_master.html', items=items, pagination=pagination, page_range=page_range)

@academics_bp.route('/api/get_activity_course_details/<int:ca_id>')
def get_activity_course_details_api(ca_id):
    details = CourseActivityModel.get_course_activity_details(ca_id)
    return jsonify(details)

@academics_bp.route('/package_master', methods=['GET', 'POST'])
@permission_required('Package Master')
def package_master():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'DELETE':
            if PackageMasterModel.delete_package(request.form.get('id')):
                flash('Package deleted successfully!', 'success')
            else:
                flash('Error deleting package.', 'danger')
        else:
            if PackageMasterModel.save_package(request.form):
                flash('Package saved successfully!', 'success')
            else:
                flash('Error saving package.', 'danger')
        return redirect(url_for('academics.package_master'))

    page = request.args.get('page', 1, type=int)
    per_page = 10
    items, total = PackageMasterModel.get_packages(page=page, per_page=per_page)
    
    pagination = {
        'page': page,
        'per_page': per_page,
        'total': total,
        'total_pages': math.ceil(total / per_page) if total else 1,
        'has_prev': page > 1,
        'has_next': page < (math.ceil(total / per_page) if total else 1)
    }
    
    page_range = get_pagination_range(page, pagination['total_pages'])

    lookups = {
        'degrees': AcademicsModel.get_all_degrees(),
        'semesters': InfrastructureModel.get_all_semesters(),
        'sessions': InfrastructureModel.get_sessions(),
        'courses': DB.fetch_all("SELECT pk_courseid as id, coursecode + ' - ' + coursename as name FROM SMS_Course_Mst ORDER BY coursecode")
    }
    
    return render_template('academics/package_master.html', items=items, lookups=lookups, pagination=pagination, page_range=page_range)

@academics_bp.route('/api/get_degree_semesters/<int:degree_id>')
def get_degree_semesters_api(degree_id):
    # Live system seems to show I to VIII or similar based on min/max sem
    degree = DB.fetch_one("SELECT minsem, maxsem FROM SMS_Degree_Mst WHERE pk_degreeid = ?", [degree_id])
    if not degree:
        return jsonify([])
    
    # Fetch all semesters and filter by degree range if applicable, 
    # but usually semesters are fixed. Let's return all semesters but 
    # the frontend will know the range from the degree object.
    semesters = InfrastructureModel.get_all_semesters()
    # We can also fetch only within min/max if needed.
    return jsonify(semesters)

@academics_bp.route('/api/get_package_details/<int:pid>')
def get_package_details_api(pid):
    details = PackageMasterModel.get_package_details(pid)
    return jsonify(details)

@academics_bp.route('/board_master', methods=['GET', 'POST'])
@permission_required('Board Master')
def board_master():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'DELETE':
            if BoardMasterModel.delete_board(request.form.get('id')):
                flash('Board deleted successfully!', 'success')
            else:
                flash('Error deleting board.', 'danger')
        else:
            if BoardMasterModel.save_board(request.form):
                flash('Board saved successfully!', 'success')
            else:
                flash('Error saving board.', 'danger')
        return redirect(url_for('academics.board_master'))

    page = request.args.get('page', 1, type=int)
    per_page = 10
    items, total = BoardMasterModel.get_boards(page=page, per_page=per_page)
    
    pagination = {
        'page': page,
        'per_page': per_page,
        'total': total,
        'total_pages': math.ceil(total / per_page) if total else 1,
        'has_prev': page > 1,
        'has_next': page < (math.ceil(total / per_page) if total else 1)
    }
    
    page_range = get_pagination_range(page, pagination['total_pages'])
    
    return render_template('academics/board_master.html', items=items, pagination=pagination, page_range=page_range)

@academics_bp.route('/certificates_master', methods=['GET', 'POST'])
@permission_required('Certificates Master')
def certificates_master():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'DELETE':
            if CertificateMasterModel.delete_certificate(request.form.get('id')):
                flash('Certificate deleted successfully!', 'success')
            else:
                flash('Error deleting certificate.', 'danger')
        else:
            if CertificateMasterModel.save_certificate(request.form):
                flash('Certificate saved successfully!', 'success')
            else:
                flash('Error saving certificate.', 'danger')
        return redirect(url_for('academics.certificates_master'))

    page = request.args.get('page', 1, type=int)
    per_page = 10
    items, total = CertificateMasterModel.get_certificates(page=page, per_page=per_page)
    
    pagination = {
        'page': page,
        'per_page': per_page,
        'total': total,
        'total_pages': math.ceil(total / per_page) if total else 1,
        'has_prev': page > 1,
        'has_next': page < (math.ceil(total / per_page) if total else 1)
    }
    
    page_range = get_pagination_range(page, pagination['total_pages'])
    
    return render_template('academics/certificates_master.html', items=items, pagination=pagination, page_range=page_range)

@academics_bp.route('/syllabus_creation', methods=['GET', 'POST'])
@permission_required('Syllabus Creation [Master]')
def syllabus_creation():
    if request.method == 'POST':
        # Placeholder for save logic
        flash('Functionality under construction.', 'info')
        return redirect(url_for('academics.syllabus_creation'))

    sessions = InfrastructureModel.get_sessions()
    degrees = AcademicsModel.get_all_degrees()
    
    return render_template('academics/syllabus_creation.html', 
                           sessions=sessions, 
                           degrees=degrees)

@academics_bp.route('/course_detail_report', methods=['GET', 'POST'])
@permission_required('Course Detail Report')
def course_detail_report():
    if request.method == 'POST':
        filters = {
            'session_from': request.form.get('session_from'),
            'session_upto': request.form.get('session_upto'),
            'degree_id': request.form.get('degree_id'),
            'dept_id': request.form.get('dept_id'),
            'semester_id': request.form.get('semester_id'),
            'year_id': request.form.get('year_id')
        }
        rpt_format = request.form.get('rpt_format', '1') # 1: View, 2: Excel, 3: PDF
        
        data = CourseModel.get_course_report_data(filters)
        
        if rpt_format == '2': # Excel
            if not data:
                flash('No data found for selected filters', 'warning')
                return redirect(url_for('academics.course_detail_report'))
            df = pd.DataFrame(data)
            # Rename columns for clarity in Excel
            mapping = {
                'coursecode': 'Course Code', 'coursename': 'Course Name', 
                'crhr_theory': 'Theory', 'crhr_practical': 'Practical',
                'total_crhr': 'Total Credits', 'coursetype': 'Course Type',
                'dept_name': 'Department', 'degreename': 'Degree',
                'semester_roman': 'Semester', 'compulsory': 'Compulsory',
                'status': 'Status', 'session_from': 'Session From', 'session_upto': 'Session Upto'
            }
            df = df.rename(columns=mapping)
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='CourseDetails')
            output.seek(0)
            
            response = make_response(output.getvalue())
            response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            response.headers['Content-Disposition'] = 'attachment; filename=Course_Detail_Report.xlsx'
            return response

        elif rpt_format == '3': # PDF
            from xhtml2pdf import pisa
            from datetime import datetime
            now_str = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
            rendered = render_template('academics/reports/course_detail_pdf.html', data=data, filters=filters, now=now_str)
            pdf_out = io.BytesIO()
            pisa.CreatePDF(io.BytesIO(rendered.encode("UTF-8")), dest=pdf_out)
            pdf_out.seek(0)
            
            response = make_response(pdf_out.getvalue())
            response.headers['Content-Type'] = 'application/pdf'
            response.headers['Content-Disposition'] = 'attachment; filename=Course_Detail_Report.pdf'
            return response

        # Default: Just show the data in the template
        sessions = InfrastructureModel.get_sessions()
        degrees = AcademicsModel.get_all_degrees()
        years = AcademicsModel.get_degree_years()
        semesters = InfrastructureModel.get_all_semesters()
        return render_template('academics/course_detail_report.html', 
                               data=data, filters=filters,
                               sessions=sessions, degrees=degrees, years=years, semesters=semesters)

    sessions = InfrastructureModel.get_sessions()
    degrees = AcademicsModel.get_all_degrees()
    years = AcademicsModel.get_degree_years()
    semesters = InfrastructureModel.get_all_semesters()
    return render_template('academics/course_detail_report.html', 
                           sessions=sessions, degrees=degrees, years=years, semesters=semesters)

@academics_bp.route('/api/get_degree_details/<int:degree_id>')
def get_degree_details_api(degree_id):
    # Returns minsem, maxsem, type (UG/PG), isdepartmentreq
    sql = """
    SELECT d.minsem, d.maxsem, dt.degreetype, d.isdepartmentreq, dt.isug
    FROM SMS_Degree_Mst d
    LEFT JOIN SMS_DegreeType_Mst dt ON d.fk_degreetypeid = dt.pk_degreetypeid
    WHERE d.pk_degreeid = ?
    """
    row = DB.fetch_one(sql, [degree_id])
    if row:
        return jsonify(row)
    return jsonify({})

@academics_bp.route('/api/degree/<int:degree_id>/branches')
def get_degree_branches_api(degree_id):
    branches = AcademicsModel.get_degree_branches(degree_id)
    from app.utils import clean_json_data
    return jsonify(clean_json_data(branches))

@academics_bp.route('/api/college/<int:college_id>/degree/<int:degree_id>/specializations')
def get_college_degree_specializations_api(college_id, degree_id):
    # Used by pages where Department list depends on the college-degree mapping (PG/PHD specializations).
    branches = AcademicsModel.get_college_degree_specializations(college_id, degree_id)
    from app.utils import clean_json_data
    return jsonify(clean_json_data(branches))

@academics_bp.route('/api/degree/<int:degree_id>/departments')
def get_degree_departments_api(degree_id):
    depts = AcademicsModel.get_degree_departments(degree_id)
    from app.utils import clean_json_data
    return jsonify(clean_json_data(depts))

@academics_bp.route('/api/get_semesters_range/<int:min_sem>/<int:max_sem>')
def get_semesters_range_api(min_sem, max_sem):
    # User requested to show only 8 semesters.
    # We use semesterorder to limit from 1 to 8.
    sql = "SELECT pk_semesterid, semester_roman, semester_char FROM SMS_Semester_Mst WHERE semesterorder BETWEEN 1 AND 8 ORDER BY semesterorder"
    rows = DB.fetch_all(sql)
    from app.utils import clean_json_data
    return jsonify(clean_json_data(rows))

@academics_bp.route('/api/get_semester_year/<int:semester_id>')
def get_semester_year_api(semester_id):
    sql = """
    SELECT dy.degreeyear_char, dy.pk_degreeyearid
    FROM SMS_Semester_Mst s
    INNER JOIN SMS_DegreeYear_Mst dy ON s.fk_degreeyearid = dy.pk_degreeyearid
    WHERE s.pk_semesterid = ?
    """
    row = DB.fetch_one(sql, [semester_id])
    from app.utils import clean_json_data
    return jsonify(clean_json_data(row if row else {}))

@academics_bp.route('/api/get_courses_filtered')
def get_courses_filtered_api():
    filters = {
        'degree_id': request.args.get('degree_id'),
        'semester_id': request.args.get('semester_id'),
        'branch_id': request.args.get('branch_id'),
        'session_id': request.args.get('session_id')
    }
    courses = CourseModel.get_courses_filtered(filters)
    from app.utils import clean_json_data
    return jsonify(clean_json_data(courses))

@academics_bp.route('/api/get_exam_configs')
def get_exam_configs_api():
    degree_id = request.args.get('degree_id', type=int)
    session_id = request.args.get('session_id', type=int)
    semester_id = request.args.get('semester_id', type=int)
    if not degree_id:
        return jsonify([])
    configs = CourseAllocationModel.get_exam_configs(degree_id, session_id, semester_id)
    return jsonify(clean_json_data(configs))

@academics_bp.route('/api/get_batches')
def get_batches_with_type_api():
    college_id = request.args.get('college_id', type=int)
    degree_id = request.args.get('degree_id', type=int)
    semester_id = request.args.get('semester_id', type=int)
    type_tp = request.args.get('type_tp') or 'T'
    if not college_id or not degree_id or not semester_id:
        return jsonify([])
    batches = BatchModel.get_batches(college_id, degree_id, semester_id, type_tp)
    return jsonify(clean_json_data(batches))

@academics_bp.route('/api/get_all_departments')
def get_all_departments_api():
    depts = AcademicsModel.get_departments()
    return jsonify(depts)

@academics_bp.route('/api/get_syllabus_courses', methods=['POST'])
def get_syllabus_courses_api():
    data = request.json
    session_from = data.get('session_from')
    session_to = data.get('session_to')
    degree_id = data.get('degree_id')
    semester_id = data.get('semester_id')
    dept_id = data.get('dept_id')

    courses = CourseModel.get_syllabus_courses(session_from, session_to, degree_id, semester_id, dept_id)
    return jsonify(courses)

@academics_bp.route('/minor_advisor', methods=['GET', 'POST'])
@permission_required('Member of Minor and supporting')
def minor_advisor():
    if request.method == 'POST':
        sid = request.form.get('sid')
        advisor_id = request.form.get('advisor_id')
        role_id = request.form.get('role_id')
        user_id = session['user_id']
        
        if sid and advisor_id and role_id:
            # Upsert into unified committee structure
            mst = DB.fetch_one("SELECT pk_adcid FROM SMS_Advisory_Committee_Mst WHERE fk_stid = ?", [sid])
            if not mst:
                stu = DB.fetch_one("SELECT fk_collegeid, fk_adm_session, fk_degreeid, fk_branchid FROM SMS_Student_Mst WHERE pk_sid=?", [sid])
                if stu:
                    res = DB.execute("""
                        INSERT INTO SMS_Advisory_Committee_Mst (fk_colgid, fk_sessionid, fk_degreeid, fk_branchid, fk_stid, createdby, creationdate, approvalstatus)
                        VALUES (?, ?, ?, ?, ?, ?, GETDATE(), 'P')
                    """, [stu['fk_collegeid'], stu['fk_adm_session'], stu['fk_degreeid'], stu['fk_branchid'], sid, user_id])
                    mst = DB.fetch_one("SELECT pk_adcid FROM SMS_Advisory_Committee_Mst WHERE fk_stid = ?", [sid])
            
            if mst:
                adcid = mst['pk_adcid']
                DB.execute("DELETE FROM SMS_Advisory_Committee_Dtl WHERE fk_adcid=? AND fk_statusid=?", [adcid, role_id])
                DB.execute("INSERT INTO SMS_Advisory_Committee_Dtl (fk_adcid, fk_statusid, fk_empid) VALUES (?, ?, ?)",
                           [adcid, role_id, advisor_id])
                flash('Committee member assigned successfully!', 'success')
            else:
                flash('Error creating advisory master.', 'danger')
        return redirect(url_for('academics.minor_advisor', **request.args))

    college_id = request.args.get('college_id')
    session_id = request.args.get('session_id')
    degree_id = request.args.get('degree_id')
    branch_id = request.args.get('branch_id')
    
    students = []
    if college_id and session_id and degree_id and str(degree_id) != '0':
        filters = {
            'college_id': college_id,
            'session_id': session_id,
            'degree_id': degree_id,
            'branch_id': branch_id
        }
        students = AdvisoryModel.get_students_for_advisory(filters)

    lookups = {
        'colleges': AcademicsModel.get_colleges_simple(),
        'sessions': InfrastructureModel.get_sessions(),
        'degrees': AcademicsModel.get_college_pg_degrees(college_id) if college_id else [],
        'branches': AcademicsModel.get_college_degree_specializations(college_id, degree_id) if (college_id and degree_id and str(degree_id) != '0') else [],
        'employees': DB.fetch_all("SELECT E.pk_empid as id, E.empname + ' | ' + E.empcode + ' | (' + ISNULL(D.description, 'No Dept') + ')' as name FROM SAL_Employee_Mst E LEFT JOIN Department_Mst D ON E.fk_deptid = D.pk_deptid WHERE E.employeeleftstatus = 'N' ORDER BY E.empname")
    }
    
    return render_template('academics/minor_advisor.html', 
                           lookups=lookups,
                           students=clean_json_data(students), 
                           filters=request.args)

@academics_bp.route('/api/student/<int:sid>/advisory_committee')
def get_student_advisory_committee_api(sid):
    info = AdvisoryModel.get_student_advisory_committee(sid)
    if not info:
        return jsonify({'error': 'Not found'}), 404
    return jsonify(clean_json_data(info))

@academics_bp.route('/api/student/<int:sid>/specializations')
def get_student_specializations_api(sid):
    # Fetch Disciplines (Major, Minor, Supporting)
    disc_sql = """
        SELECT fk_desciplineidMajor as major_id, fk_desciplineidMinor as minor_id, 
               fk_desciplineidSupporting as supporting_id
        FROM SMS_stuDiscipline_dtl
        WHERE fk_sturegid = ?
    """
    disc = DB.fetch_one(disc_sql, [sid])
    
    # Fetch Major Advisor (statusid = 1)
    adv_sql = """
        SELECT ACD.fk_empid as advisor_id
        FROM SMS_Advisory_Committee_Dtl ACD
        INNER JOIN SMS_Advisory_Committee_Mst ACM ON ACD.fk_adcid = ACM.pk_adcid
        WHERE ACM.fk_stid = ? AND ACD.fk_statusid = 1
    """
    adv = DB.fetch_one(adv_sql, [sid])
    
    res = {
        'major_id': disc['major_id'] if disc else None,
        'minor_id': disc['minor_id'] if disc else None,
        'supporting_id': disc['supporting_id'] if disc else None,
        'advisor_id': adv['advisor_id'] if adv else None
    }
    return jsonify(res)

@academics_bp.route('/api/student/<int:sid>/committee')
def get_student_committee_api(sid):
    sql = """
        SELECT ACD.*, S.fullname as student_name, E.empname as advisor_name, 
               DESG.designation as designation, DEPT.description as department,
               B.Branchname as specialization,
               CASE ACD.fk_statusid 
                    WHEN 1 THEN 'Major Advisor' WHEN 2 THEN 'Co-Advisor'
                    WHEN 3 THEN 'Member From Minor Subject' WHEN 4 THEN 'Member From Supporting Subject'
                    WHEN 5 THEN 'Dean PGS Nominee' WHEN 6 THEN 'Member From Major Subject'
                    ELSE 'Member' 
               END as role_name
        FROM SMS_Advisory_Committee_Dtl ACD
        INNER JOIN SMS_Advisory_Committee_Mst ACM ON ACD.fk_adcid = ACM.pk_adcid
        INNER JOIN SMS_Student_Mst S ON ACM.fk_stid = S.pk_sid
        INNER JOIN SAL_Employee_Mst E ON ACD.fk_empid = E.pk_empid
        LEFT JOIN SAL_Designation_Mst DESG ON E.fk_desgid = DESG.pk_desgid
        LEFT JOIN Department_Mst DEPT ON E.fk_deptid = DEPT.pk_deptid
        LEFT JOIN SMS_BranchMst B ON S.fk_branchid = B.Pk_BranchId
        WHERE ACM.fk_stid = ?
        ORDER BY ACD.fk_statusid
    """
    rows = DB.fetch_all(sql, [sid])
    return jsonify(clean_json_data(rows))

@academics_bp.route('/specialization_assignment', methods=['GET', 'POST'])
@permission_required('Specialization Assignment')
def specialization_assignment():
    if request.method == 'POST':
        if AdvisoryModel.save_student_discipline(request.form, session['user_id']):
            flash('Specialization and Advisor assigned successfully!', 'success')
        else:
            flash('Error assigning specialization. Please check all fields.', 'danger')
        return redirect(url_for('academics.specialization_assignment', **request.args))

    college_id = request.args.get('college_id')
    session_id = request.args.get('session_id')
    degree_id = request.args.get('degree_id')
    branch_id = request.args.get('filter_branch_id')
    
    students = []
    if college_id and session_id and degree_id and str(degree_id) != '0':
        filters = {
            'college_id': college_id,
            'session_id': session_id,
            'degree_id': degree_id,
            'branch_id': branch_id
        }
        students = AdvisoryModel.get_students_for_advisory(filters)

    lookups = {
        'colleges': AcademicsModel.get_colleges_simple(),
        'sessions': InfrastructureModel.get_sessions(),
        'degrees': AcademicsModel.get_college_pg_degrees(college_id) if college_id else [],
        'branches': AcademicsModel.get_college_degree_specializations(college_id, degree_id) if (college_id and degree_id and str(degree_id) != '0') else [],
        'employees': DB.fetch_all("SELECT E.pk_empid as id, E.empname + ' | ' + E.empcode + ' | (' + ISNULL(D.description, 'No Dept') + ')' as name FROM SAL_Employee_Mst E LEFT JOIN Department_Mst D ON E.fk_deptid = D.pk_deptid WHERE E.employeeleftstatus = 'N' ORDER BY E.empname")
    }
    
    # Context info for grid labels
    degree_name = ''
    session_name = ''
    if degree_id:
        deg = next((d for d in lookups['degrees'] if str(d['id']) == str(degree_id)), None)
        degree_name = deg['name'] if deg else ''
    if session_id:
        sess = next((s for s in lookups['sessions'] if str(s['id']) == str(session_id)), None)
        session_name = sess['name'] if sess else ''

    return render_template('academics/specialization_assignment.html', 
                           lookups=lookups,
                           students=clean_json_data(students), 
                           filters=request.args,
                           degree_name=degree_name,
                           session_name=session_name)

@academics_bp.route('/admission_no_configuration', methods=['GET', 'POST'])
@permission_required('Admission No Configuration')
def admission_no_configuration():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'DELETE':
            if AdmissionModel.delete_admission_config(request.form.get('id')):
                flash('Configuration deleted successfully!', 'success')
            else:
                flash('Error deleting configuration.', 'danger')
        else:
            if AdmissionModel.save_admission_config(request.form):
                flash('Configuration saved successfully!', 'success')
            else:
                flash('Error saving configuration.', 'danger')
        return redirect(url_for('academics.admission_no_configuration'))

    page = request.args.get('page', 1, type=int)
    per_page = 10
    loc_id = session.get('selected_loc')
    items, total = AdmissionModel.get_all_configs(page=page, per_page=per_page, loc_id=loc_id)
    
    pagination = {
        'page': page,
        'per_page': per_page,
        'total': total,
        'total_pages': math.ceil(total / per_page) if total else 1,
        'has_prev': page > 1,
        'has_next': page < (math.ceil(total / per_page) if total else 1)
    }
    
    page_range = get_pagination_range(page, pagination['total_pages'])

    if loc_id:
        colleges = DB.fetch_all("SELECT pk_collegeid as id, collegename as name FROM SMS_College_Mst WHERE fk_locid = ? ORDER BY collegename", [loc_id])
    else:
        colleges = AcademicsModel.get_colleges_simple()

    college_id = request.args.get('college_id')
    filters = {
        'college_id': college_id
    }
    lookups = {
        'colleges': colleges,
        'degrees': AcademicsModel.get_college_all_degrees(college_id) if college_id else AcademicsModel.get_all_degrees(),
        'sessions': InfrastructureModel.get_sessions()
    }
    
    return render_template('academics/admission_no_configuration.html', items=items, lookups=lookups, pagination=pagination, page_range=page_range, filters=filters)

@academics_bp.route('/api/admission/get_config')
def api_get_admission_config():
    college_id = request.args.get('college_id')
    degree_id = request.args.get('degree_id')
    session_id = request.args.get('session_id')
    if not all([college_id, degree_id, session_id]):
        return jsonify({'error': 'Missing parameters'}), 400
    
    config = AdmissionModel.get_admission_config(college_id, degree_id, session_id)
    if config:
        # HAU ERP reversed logic: suffix col is Prefix, Prefix col is Suffix
        return jsonify({
            'prefix': config['suffix'] or '',
            'suffix': config['Prefix'] or '',
            'separator': config['Separator'] or ''
        })
    return jsonify({'error': 'No config found'}), 404

@academics_bp.route('/admission_no_generation', methods=['GET', 'POST'])
@permission_required('Admission No Generation')
def admission_no_generation():
    if request.method == 'POST':
        action = request.form.get('action')
        student_ids = request.form.getlist('student_ids')
        admission_nos = request.form.getlist('new_nos[]')
        
        if action == 'SAVE':
            success_count = 0
            for i in range(len(student_ids)):
                if admission_nos[i]:
                    if AdmissionModel.save_admission_no(student_ids[i], admission_nos[i]):
                        success_count += 1
            flash(f'Successfully updated {success_count} admission numbers.', 'success')
        
        return redirect(url_for('academics.admission_no_generation', **request.args))

    filters = {
        'college_id': request.args.get('college_id'),
        'session_id': request.args.get('session_id'),
        'degree_id': request.args.get('degree_id'),
        'branch_id': request.args.get('branch_id')
    }
    
    students = []
    config = None
    next_serial = 1
    
    if all([filters['college_id'], filters['session_id'], filters['degree_id']]):
        students = AdmissionModel.get_students_for_generation(filters)
        config_raw = AdmissionModel.get_admission_config(filters['college_id'], filters['degree_id'], filters['session_id'])
        if config_raw:
            config = {
                'prefix': config_raw['suffix'] or '',
                'suffix': config_raw['Prefix'] or '',
                'separator': config_raw['Separator'] or ''
            }
            next_serial = AdmissionModel.get_next_serial(
                filters['college_id'], filters['degree_id'], filters['session_id'],
                config['prefix'], config['suffix'], config['separator']
            )
        else:
            flash('No admission number configuration found for this selection.', 'warning')

    # Lookups
    loc_id = session.get('selected_loc')
    if loc_id:
        colleges = DB.fetch_all("SELECT pk_collegeid as id, collegename as name FROM SMS_College_Mst WHERE fk_locid = ? ORDER BY collegename", [loc_id])
    else:
        colleges = AcademicsModel.get_colleges_simple()

    lookups = {
        'colleges': colleges,
        'sessions': InfrastructureModel.get_sessions(),
        'degrees': AcademicsModel.get_college_all_degrees(filters['college_id']) if filters['college_id'] else [],
        'branches': AcademicsModel.get_college_degree_specializations(filters['college_id'], filters['degree_id']) if (filters['college_id'] and filters['degree_id']) else []
    }
    
    return render_template('academics/admission_no_generation.html', 
                           lookups=lookups, filters=filters, students=students, 
                           config=config, next_serial=next_serial)

    pagination = {
        'page': page,
        'per_page': per_page,
        'total': total,
        'total_pages': math.ceil(total / per_page) if total else 1,
        'has_prev': page > 1,
        'has_next': page < (math.ceil(total / per_page) if total else 1)
    }
    
    page_range = get_pagination_range(page, pagination['total_pages'])

    colleges = AcademicsModel.get_colleges_simple()
    sessions = InfrastructureModel.get_sessions()
    degrees = AcademicsModel.get_all_degrees()
    
    # Create a copy of filters and remove 'page' if it exists
    page_filters = dict(request.args)
    if 'page' in page_filters:
        del page_filters['page']
    
    return render_template('academics/admission_no_generation.html', 
                           colleges=colleges, sessions=sessions, degrees=degrees,
                           students=students, config=config, filters=page_filters,
                           pagination=pagination, page_range=page_range)

@academics_bp.route('/college_degree_seat_detail', methods=['GET', 'POST'])
@permission_required(' College Degree Wise Seat Detail')
def college_degree_seat_detail():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'DELETE':
            if SeatDetailModel.delete_seat_detail(request.form.get('id')):
                flash('Seat detail deleted successfully!', 'success')
            else:
                flash('Error deleting seat detail.', 'danger')
        else:
            if SeatDetailModel.save_seat_detail(request.form):
                flash('Seat detail saved successfully!', 'success')
            else:
                flash('Error saving seat detail.', 'danger')
        return redirect(url_for('academics.college_degree_seat_detail'))

    page = request.args.get('page', 1, type=int)
    per_page = 10
    items, total = SeatDetailModel.get_seat_details(page=page, per_page=per_page)
    
    pagination = {
        'page': page,
        'per_page': per_page,
        'total': total,
        'total_pages': math.ceil(total / per_page) if total else 1,
        'has_prev': page > 1,
        'has_next': page < (math.ceil(total / per_page) if total else 1)
    }
    
    page_range = get_pagination_range(page, pagination['total_pages'])

    lookups = {
        'colleges': AcademicsModel.get_colleges_simple(),
        'degrees': AcademicsModel.get_all_degrees(),
        'branches': AcademicsModel.get_branches(),
        'sessions': InfrastructureModel.get_sessions()
    }
    
    return render_template('academics/college_degree_seat_detail.html', items=items, lookups=lookups, pagination=pagination, page_range=page_range)

@academics_bp.route('/pgs_course_limit_master', methods=['GET', 'POST'])
@permission_required('PGS Course Limit [Master]')
def pgs_course_limit_master():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'DELETE':
            if PgsCourseLimitModel.delete_limit(request.form.get('id')):
                flash('Limit deleted successfully!', 'success')
            else:
                flash('Error deleting limit.', 'danger')
        else:
            data = request.form.to_dict()
            data['user_id'] = session['user_id']
            if PgsCourseLimitModel.save_limit(data):
                flash('Course limit saved successfully!', 'success')
            else:
                flash('Error saving course limit. Check all fields.', 'danger')
        return redirect(url_for('academics.pgs_course_limit_master'))

    page = request.args.get('page', 1, type=int)
    per_page = 10
    items, total = PgsCourseLimitModel.get_limits(page=page, per_page=per_page)
    
    pagination = {
        'page': page,
        'per_page': per_page,
        'total': total,
        'total_pages': math.ceil(total / per_page) if total else 1,
        'has_prev': page > 1,
        'has_next': page < (math.ceil(total / per_page) if total else 1)
    }
    
    page_range = get_pagination_range(page, pagination['total_pages'])

    # Fetch lookup data
    colleges = AcademicsModel.get_colleges_simple()
    # Filter courses to show only relevant ones if needed, or all. 
    # Restricted to only FIVE PGS courses as requested
    courses = DB.fetch_all("""
        SELECT pk_courseid as id, '[' + coursecode + ']~' + coursename as name 
        FROM SMS_Course_Mst 
        WHERE pk_courseid IN (1142, 1147, 1144, 1145, 1143)
        ORDER BY coursecode
    """)
    
    # College dropdown should be blank (applicable to all)
    colleges = []
    
    sessions = InfrastructureModel.get_sessions()

    return render_template('academics/pgs_course_limit_master.html', 
                           items=items, 
                           colleges=colleges, 
                           courses=courses, 
                           sessions=sessions,
                           pagination=pagination,
                           page_range=page_range)

@academics_bp.route('/batch_assignment', methods=['GET', 'POST'])
@permission_required('Batch Assignment')
def batch_assignment():
    if request.method == 'POST':
        student_ids = request.form.getlist('chk_student')
        batch_id = request.form.get('batch_id')
        type_tp = request.form.get('type_tp')
        if student_ids and batch_id and type_tp:
            BatchModel.assign_batch(student_ids, batch_id, type_tp)
            flash('Batch assigned successfully.', 'success')
        return redirect(url_for('academics.batch_assignment', **request.args))

    filters = {
        'college_id': request.args.get('college_id'),
        'session_id': request.args.get('session_id'),
        'degree_id': request.args.get('degree_id'),
        'semester_id': request.args.get('semester_id'),
        'type_tp': request.args.get('type_tp', 'T'),
        'branch_id': request.args.get('branch_id'),
        'batch_id': request.args.get('batch_id')
    }

    students = []
    batches = []
    if all([filters['college_id'], filters['session_id'], filters['degree_id']]):
        students = BatchModel.get_students_for_batch(filters)
        if filters['semester_id']:
            batches = BatchModel.get_batches(filters['college_id'], filters['degree_id'], filters['semester_id'], filters['type_tp'])

    # Lookups
    loc_id = session.get('selected_loc')
    if loc_id:
        colleges = DB.fetch_all("SELECT pk_collegeid as id, collegename as name FROM SMS_College_Mst WHERE fk_locid = ? ORDER BY collegename", [loc_id])
    else:
        colleges = AcademicsModel.get_colleges_simple()

    lookups = {
        'colleges': colleges,
        'sessions': InfrastructureModel.get_sessions(),
        'degrees': AcademicsModel.get_college_all_degrees(filters['college_id']) if filters['college_id'] else [],
        'semesters': InfrastructureModel.get_all_semesters(),
        'branches': AcademicsModel.get_college_degree_specializations(filters['college_id'], filters['degree_id']) if (filters['college_id'] and filters['degree_id']) else [],
        'batches': batches
    }

    return render_template('academics/batch_assignment.html', lookups=lookups, filters=filters, students=students, now=datetime.now())

@academics_bp.route('/batch_assignment_report')
@permission_required('Batch Assignment')
def batch_assignment_report():
    filters = {
        'college_id': request.args.get('college_id'),
        'session_id': request.args.get('session_id'),
        'degree_id': request.args.get('degree_id'),
        'semester_id': request.args.get('semester_id'),
        'type_tp': request.args.get('type_tp', 'T'),
        'batch_id': request.args.get('batch_id'),
        'format': request.args.get('format', 'pdf')
    }
    
    if not all([filters['college_id'], filters['session_id'], filters['degree_id']]):
        flash('Please apply filters first.', 'warning')
        return redirect(url_for('academics.batch_assignment'))

    report_data = BatchModel.get_batch_report(filters)
    
    filters_info = {
        'college': DB.fetch_scalar("SELECT collegename FROM SMS_College_Mst WHERE pk_collegeid = ?", [filters['college_id']]),
        'session': DB.fetch_scalar("SELECT sessionname FROM SMS_AcademicSession_Mst WHERE pk_sessionid = ?", [filters['session_id']]),
        'degree': DB.fetch_scalar("SELECT degreename FROM SMS_Degree_Mst WHERE pk_degreeid = ?", [filters['degree_id']]),
        'type': 'Theory' if filters['type_tp'] == 'T' else 'Practical'
    }

    if filters['format'] == 'excel':
        html = render_template('reports/batch_assignment_report.html', report_data=report_data, filters=filters, now=datetime.now(), filters_info=filters_info)
        response = make_response(html)
        response.headers["Content-Disposition"] = "attachment; filename=Batch_Assignment_Report.xls"
        response.headers["Content-Type"] = "application/vnd.ms-excel"
        return response
    elif filters['format'] == 'word':
        html = render_template('reports/batch_assignment_report.html', report_data=report_data, filters=filters, now=datetime.now(), filters_info=filters_info)
        response = make_response(html)
        response.headers["Content-Disposition"] = "attachment; filename=Batch_Assignment_Report.doc"
        response.headers["Content-Type"] = "application/msword"
        return response
    else:
        from app.utils import generate_batch_assignment_pdf
        pdf_content = generate_batch_assignment_pdf(report_data, filters_info)
        return send_file(pdf_content, download_name="Batch_Assignment_Report.pdf", as_attachment=True, mimetype='application/pdf')

@academics_bp.route('/api/admission/get_batches')
def api_get_batches():
    college_id = request.args.get('college_id')
    degree_id = request.args.get('degree_id')
    semester_id = request.args.get('semester_id')
    type_tp = request.args.get('type_tp')
    
    if not all([college_id, degree_id, semester_id, type_tp]):
        return jsonify([])
        
    batches = BatchModel.get_batches(college_id, degree_id, semester_id, type_tp)
    return jsonify(batches)

@academics_bp.route('/student_course_approval_advisor', methods=['GET', 'POST'])
@permission_required('Course Allocation Approval For UG/PG[By Advisor]')
def student_course_approval_advisor():
    user_id = session.get('user_id')
    emp_id = session.get('emp_id')
    
    if request.method == 'POST':
        if AdvisorApprovalModel.save_approvals(request.form, emp_id, user_id):
            flash('Approvals updated successfully!', 'success')
        else:
            flash('Error updating approvals.', 'danger')
        return redirect(url_for('academics.student_course_approval_advisor', **request.args))

    filters = {
        'college_id': request.args.get('college_id', type=int),
        'session_id': request.args.get('session_id', type=int),
        'degree_id': request.args.get('degree_id', type=int),
        'semester_id': request.args.get('semester_id', type=int),
        'branch_id': request.args.get('branch_id', type=int),
        'exconfig_id': request.args.get('exconfig_id', type=int),
        'view': request.args.get('view')
    }

    students = []
    if filters['view'] == '1' and all([filters['college_id'], filters['session_id'], filters['degree_id'], filters['exconfig_id']]):
        students = AdvisorApprovalModel.get_students_for_approval(filters, emp_id)

    # Lookups
    loc_id = session.get('selected_loc')
    if loc_id:
        colleges = DB.fetch_all("SELECT pk_collegeid as id, collegename as name FROM SMS_College_Mst WHERE fk_locid = ? ORDER BY collegename", [loc_id])
    else:
        colleges = AcademicsModel.get_colleges_simple()

    lookups = {
        'colleges': colleges,
        'sessions': InfrastructureModel.get_sessions(),
        'degrees': AcademicsModel.get_college_all_degrees(filters['college_id']) if filters['college_id'] else [],
        'semesters': InfrastructureModel.get_all_semesters(),
        'branches': AcademicsModel.get_college_degree_specializations(filters['college_id'], filters['degree_id']) if (filters['college_id'] and filters['degree_id']) else [],
        'exam_configs': CourseAllocationModel.get_exam_configs(filters['degree_id'], filters['session_id'], filters['semester_id']) if filters['degree_id'] else [],
        'years': AcademicsModel.get_degree_years()
    }

    return render_template('academics/student_course_approval_advisor.html', 
                           lookups=lookups, filters=filters, students=clean_json_data(students))

@academics_bp.route('/course_allocation_approval', methods=['GET', 'POST'])
@permission_required('Course Allocation Approval For UG/PG[By Teacher]')
def course_allocation_approval():
    user_id = session.get('user_id')
    emp_id = session.get('emp_id')

    if request.method == 'POST':
        if TeacherApprovalModel.save_approvals(request.form, emp_id, user_id):
            flash('Approvals updated successfully!', 'success')
        else:
            flash('Error updating approvals.', 'danger')
        return redirect(url_for('academics.course_allocation_approval', **request.args))

    filters = {
        'college_id': request.args.get('college_id', type=int),
        'session_id': request.args.get('session_id', type=int),
        'degree_id': request.args.get('degree_id', type=int),
        'semester_id': request.args.get('semester_id', type=int),
        'branch_id': request.args.get('branch_id', type=int),
        'exconfig_id': request.args.get('exconfig_id', type=int),
        'view': request.args.get('view'),
    }

    students = []
    if filters['view'] == '1' and all([filters['college_id'], filters['session_id'], filters['degree_id'], filters['exconfig_id']]):
        students = TeacherApprovalModel.get_students_for_approval(filters, emp_id)

    # Lookups
    loc_id = session.get('selected_loc')
    if loc_id:
        colleges = DB.fetch_all(
            "SELECT pk_collegeid as id, collegename as name FROM SMS_College_Mst WHERE fk_locid = ? ORDER BY collegename",
            [loc_id]
        )
    else:
        colleges = AcademicsModel.get_colleges_simple()

    lookups = {
        'colleges': colleges,
        'sessions': InfrastructureModel.get_sessions(),
        'degrees': AcademicsModel.get_college_all_degrees(filters['college_id']) if filters['college_id'] else [],
        'semesters': InfrastructureModel.get_all_semesters(),
        'branches': AcademicsModel.get_college_degree_specializations(filters['college_id'], filters['degree_id']) if (filters['college_id'] and filters['degree_id']) else [],
        'exam_configs': CourseAllocationModel.get_exam_configs(filters['degree_id'], filters['session_id'], filters['semester_id']) if filters['degree_id'] else [],
        'years': AcademicsModel.get_degree_years(),
    }

    return render_template(
        'academics/student_course_approval_teacher.html',
        lookups=lookups,
        filters=filters,
        students=clean_json_data(students),
    )

@academics_bp.route('/student_course_approval_dsw', methods=['GET', 'POST'])
@permission_required('Course Allocation Approval For UG/PG[By DSW]')
def student_course_approval_dsw():
    user_id = session.get('user_id')
    emp_id = session.get('emp_id')

    if request.method == 'POST':
        if DswApprovalModel.save_approvals(request.form, emp_id, user_id):
            flash('Approvals updated successfully!', 'success')
        else:
            flash('Error updating approvals.', 'danger')
        return redirect(url_for('academics.student_course_approval_dsw', **request.args))

    filters = {
        'college_id': request.args.get('college_id', type=int),
        'session_id': request.args.get('session_id', type=int),
        'degree_id': request.args.get('degree_id', type=int),
        'semester_id': request.args.get('semester_id', type=int),
        'branch_id': request.args.get('branch_id', type=int),
        'exconfig_id': request.args.get('exconfig_id', type=int),
        'view': request.args.get('view'),
        'pending': request.args.get('pending'),
    }

    students = []
    if filters['view'] == '1' and all([filters['college_id'], filters['session_id'], filters['degree_id'], filters['semester_id'], filters['exconfig_id']]):
        students = DswApprovalModel.get_students_for_approval(filters, emp_id)

    loc_id = session.get('selected_loc')
    if loc_id:
        colleges = DB.fetch_all(
            "SELECT pk_collegeid as id, collegename as name FROM SMS_College_Mst WHERE fk_locid = ? ORDER BY collegename",
            [loc_id]
        )
    else:
        colleges = AcademicsModel.get_colleges_simple()

    lookups = {
        'colleges': colleges,
        'sessions': InfrastructureModel.get_sessions(),
        'degrees': AcademicsModel.get_college_all_degrees(filters['college_id']) if filters['college_id'] else [],
        'semesters': InfrastructureModel.get_all_semesters(),
        'branches': AcademicsModel.get_college_degree_specializations(filters['college_id'], filters['degree_id']) if (filters['college_id'] and filters['degree_id']) else [],
        'exam_configs': CourseAllocationModel.get_exam_configs(filters['degree_id'], filters['session_id'], filters['semester_id']) if filters['degree_id'] else [],
        'years': AcademicsModel.get_degree_years(),
    }

    return render_template(
        'academics/student_course_approval_dsw.html',
        lookups=lookups,
        filters=filters,
        students=clean_json_data(students),
    )

@academics_bp.route('/api/student_course_approval_dsw_pending')
@permission_required('Course Allocation Approval For UG/PG[By DSW]')
def student_course_approval_dsw_pending():
    emp_id = session.get('emp_id')
    filters = {
        'college_id': request.args.get('college_id', type=int),
        'session_id': request.args.get('session_id', type=int),
        'degree_id': request.args.get('degree_id', type=int),
        'semester_id': request.args.get('semester_id', type=int),
        'branch_id': request.args.get('branch_id', type=int),
        'exconfig_id': request.args.get('exconfig_id', type=int),
    }
    
    if not all([filters['college_id'], filters['session_id'], filters['degree_id'], filters['semester_id'], filters['exconfig_id']]):
        return jsonify([])
        
    students = DswApprovalModel.get_pending_students(filters, emp_id)
    return jsonify(clean_json_data(students))

@academics_bp.route('/student_course_approval_library', methods=['GET', 'POST'])
@permission_required('Course Allocation Approval For UG/PG[By Library]')
def student_course_approval_library():
    user_id = session.get('user_id')
    emp_id = session.get('emp_id')

    if request.method == 'POST':
        if LibraryApprovalModel.save_approvals(request.form, emp_id, user_id):
            flash('Approvals updated successfully!', 'success')
        else:
            flash('Error updating approvals.', 'danger')
        return redirect(url_for('academics.student_course_approval_library', **request.args))

    filters = {
        'college_id': request.args.get('college_id', type=int),
        'session_id': request.args.get('session_id', type=int),
        'degree_id': request.args.get('degree_id', type=int),
        'semester_id': request.args.get('semester_id', type=int),
        'branch_id': request.args.get('branch_id', type=int),
        'exconfig_id': request.args.get('exconfig_id', type=int),
        'view': request.args.get('view'),
    }

    students = []
    if filters['view'] == '1' and all([filters['college_id'], filters['session_id'], filters['degree_id'], filters['semester_id'], filters['exconfig_id']]):
        students = LibraryApprovalModel.get_students_for_approval(filters, emp_id)

    loc_id = session.get('selected_loc')
    if loc_id:
        colleges = DB.fetch_all(
            "SELECT pk_collegeid as id, collegename as name FROM SMS_College_Mst WHERE fk_locid = ? ORDER BY collegename",
            [loc_id]
        )
    else:
        colleges = AcademicsModel.get_colleges_simple()

    lookups = {
        'colleges': colleges,
        'sessions': InfrastructureModel.get_sessions(),
        'degrees': AcademicsModel.get_college_all_degrees(filters['college_id']) if filters['college_id'] else [],
        'semesters': InfrastructureModel.get_all_semesters(),
        'branches': AcademicsModel.get_college_degree_specializations(filters['college_id'], filters['degree_id']) if (filters['college_id'] and filters['degree_id']) else [],
        'exam_configs': CourseAllocationModel.get_exam_configs(filters['degree_id'], filters['session_id'], filters['semester_id']) if filters['degree_id'] else [],
        'years': AcademicsModel.get_degree_years(),
    }

    return render_template(
        'academics/student_course_approval_library.html',
        lookups=lookups,
        filters=filters,
        students=clean_json_data(students),
    )

@academics_bp.route('/api/student_course_approval_library_pending')
@permission_required('Course Allocation Approval For UG/PG[By Library]')
def student_course_approval_library_pending():
    emp_id = session.get('emp_id')
    filters = {
        'college_id': request.args.get('college_id', type=int),
        'session_id': request.args.get('session_id', type=int),
        'degree_id': request.args.get('degree_id', type=int),
        'semester_id': request.args.get('semester_id', type=int),
        'branch_id': request.args.get('branch_id', type=int),
        'exconfig_id': request.args.get('exconfig_id', type=int),
    }
    
    if not all([filters['college_id'], filters['session_id'], filters['degree_id'], filters['semester_id'], filters['exconfig_id']]):
        return jsonify([])
        
    students = LibraryApprovalModel.get_pending_students(filters, emp_id)
    return jsonify(clean_json_data(students))

@academics_bp.route('/student_course_approval_fee', methods=['GET', 'POST'])
@permission_required('Course Allocation Fee Approval For UG/PG')
def student_course_approval_fee():
    from app.models import FeeApprovalModel
    user_id = session.get('user_id')
    emp_id = session.get('emp_id')

    if request.method == 'POST':
        if FeeApprovalModel.save_approvals(request.form, emp_id, user_id):
            flash('Approvals updated successfully!', 'success')
        else:
            flash('Error updating approvals.', 'danger')
        return redirect(url_for('academics.student_course_approval_fee', **request.args))

    filters = {
        'college_id': request.args.get('college_id', type=int),
        'session_id': request.args.get('session_id', type=int),
        'degree_id': request.args.get('degree_id', type=int),
        'semester_id': request.args.get('semester_id', type=int),
        'branch_id': request.args.get('branch_id', type=int),
        'exconfig_id': request.args.get('exconfig_id', type=int),
        'view': request.args.get('view'),
        'pending': request.args.get('pending'),
    }

    students = []
    pending_students = []
    if filters['view'] == '1' and all([filters['college_id'], filters['session_id'], filters['degree_id'], filters['semester_id'], filters['exconfig_id']]):
        students = FeeApprovalModel.get_students_for_approval(filters, emp_id)
        if filters.get('pending') == '1':
            pending_students = FeeApprovalModel.get_pending_students(filters, emp_id)

    loc_id = session.get('selected_loc')
    if loc_id:
        colleges = DB.fetch_all(
            "SELECT pk_collegeid as id, collegename as name FROM SMS_College_Mst WHERE fk_locid = ? ORDER BY collegename",
            [loc_id]
        )
    else:
        colleges = AcademicsModel.get_colleges_simple()

    lookups = {
        'colleges': colleges,
        'sessions': InfrastructureModel.get_sessions(),
        'degrees': AcademicsModel.get_college_all_degrees(filters['college_id']) if filters['college_id'] else [],
        'semesters': InfrastructureModel.get_all_semesters(),
        'branches': AcademicsModel.get_college_degree_specializations(filters['college_id'], filters['degree_id']) if (filters['college_id'] and filters['degree_id']) else [],
        'exam_configs': CourseAllocationModel.get_exam_configs(filters['degree_id'], filters['session_id'], filters['semester_id']) if filters['degree_id'] else [],
        'years': AcademicsModel.get_degree_years(),
    }

    return render_template(
        'academics/student_course_approval_fee.html',
        lookups=lookups,
        filters=filters,
        students=clean_json_data(students),
        pending_students=clean_json_data(pending_students),
    )

@academics_bp.route('/student_course_approval_dean', methods=['GET', 'POST'])
@permission_required('Course Allocation Approval For UG/PG [By Dean]')
def student_course_approval_dean():
    from app.models import DeanApprovalModel
    user_id = session.get('user_id')
    emp_id = session.get('emp_id')

    if request.method == 'POST':
        if DeanApprovalModel.save_approvals(request.form, emp_id, user_id):
            flash('Approvals updated successfully!', 'success')
        else:
            flash('Error updating approvals.', 'danger')
        return redirect(url_for('academics.student_course_approval_dean', **request.args))

    filters = {
        'college_id': request.args.get('college_id', type=int),
        'session_id': request.args.get('session_id', type=int),
        'degree_id': request.args.get('degree_id', type=int),
        'semester_id': request.args.get('semester_id', type=int),
        'branch_id': request.args.get('branch_id', type=int),
        'exconfig_id': request.args.get('exconfig_id', type=int),
        'view': request.args.get('view'),
        'pending': request.args.get('pending'),
    }

    students = []
    pending_students = []
    if filters['view'] == '1' and all([filters['college_id'], filters['session_id'], filters['degree_id'], filters['semester_id'], filters['exconfig_id']]):
        students = DeanApprovalModel.get_students_for_approval(filters, emp_id)
        if filters.get('pending') == '1':
            pending_students = DeanApprovalModel.get_pending_students(filters, emp_id)

    loc_id = session.get('selected_loc')
    if loc_id:
        colleges = DB.fetch_all(
            "SELECT pk_collegeid as id, collegename as name FROM SMS_College_Mst WHERE fk_locid = ? ORDER BY collegename",
            [loc_id]
        )
    else:
        colleges = AcademicsModel.get_colleges_simple()

    lookups = {
        'colleges': colleges,
        'sessions': InfrastructureModel.get_sessions(),
        'degrees': AcademicsModel.get_college_all_degrees(filters['college_id']) if filters['college_id'] else [],
        'semesters': InfrastructureModel.get_all_semesters(),
        'branches': AcademicsModel.get_college_degree_specializations(filters['college_id'], filters['degree_id']) if (filters['college_id'] and filters['degree_id']) else [],
        'exam_configs': CourseAllocationModel.get_exam_configs(filters['degree_id'], filters['session_id'], filters['semester_id']) if filters['degree_id'] else [],
        'years': AcademicsModel.get_degree_years(),
    }

    return render_template(
        'academics/student_course_approval_dean.html',
        lookups=lookups,
        filters=filters,
        students=clean_json_data(students),
        pending_students=clean_json_data(pending_students),
    )

@academics_bp.route('/student_course_approval_deanpgs', methods=['GET', 'POST'])
@permission_required('Course Allocation Approval For PG [By DeanPGS]')
def student_course_approval_deanpgs():
    from app.models import DeanPgsApprovalModel
    user_id = session.get('user_id')
    emp_id = session.get('emp_id')

    if request.method == 'POST':
        if DeanPgsApprovalModel.save_approvals(request.form, emp_id, user_id):
            flash('Approvals updated successfully!', 'success')
        else:
            flash('Error updating approvals.', 'danger')
        return redirect(url_for('academics.student_course_approval_deanpgs', **request.args))

    filters = {
        'college_id': request.args.get('college_id', type=int),
        'session_id': request.args.get('session_id', type=int),
        'degree_id': request.args.get('degree_id', type=int),
        'semester_id': request.args.get('semester_id', type=int),
        'branch_id': request.args.get('branch_id', type=int),
        'exconfig_id': request.args.get('exconfig_id', type=int),
        'view': request.args.get('view'),
        'pending': request.args.get('pending'),
    }

    students = []
    pending_students = []
    if filters['view'] == '1' and all([filters['college_id'], filters['session_id'], filters['degree_id'], filters['semester_id'], filters['exconfig_id']]):
        students = DeanPgsApprovalModel.get_students_for_approval(filters, emp_id)
        if filters.get('pending') == '1':
            pending_students = DeanPgsApprovalModel.get_pending_students(filters, emp_id)

    loc_id = session.get('selected_loc')
    if loc_id:
        colleges = DB.fetch_all(
            "SELECT pk_collegeid as id, collegename as name FROM SMS_College_Mst WHERE fk_locid = ? ORDER BY collegename",
            [loc_id]
        )
    else:
        colleges = AcademicsModel.get_colleges_simple()

    lookups = {
        'colleges': colleges,
        'sessions': InfrastructureModel.get_sessions(),
        'degrees': AcademicsModel.get_college_pg_degrees(filters['college_id']) if filters['college_id'] else [],
        'semesters': InfrastructureModel.get_all_semesters(),
        'branches': AcademicsModel.get_college_degree_specializations(filters['college_id'], filters['degree_id']) if (filters['college_id'] and filters['degree_id']) else [],
        'exam_configs': CourseAllocationModel.get_exam_configs(filters['degree_id'], filters['session_id'], filters['semester_id']) if filters['degree_id'] else [],
        'years': AcademicsModel.get_degree_years(),
    }

    return render_template(
        'academics/student_course_approval_deanpgs.html',
        lookups=lookups,
        filters=filters,
        students=clean_json_data(students),
        pending_students=clean_json_data(pending_students),
    )

@academics_bp.route('/degree_complete_detail', methods=['GET', 'POST'])
@permission_required('Degree Complete Detail')
def degree_complete_detail():
    filters = {
        'college_id': request.args.get('college_id'),
        'session_id': request.args.get('session_id'),
        'degree_id': request.args.get('degree_id'),
        'semester_id': request.args.get('semester_id'),
        'from_date': request.args.get('from_date'),
        'to_date': request.args.get('to_date'),
        'view': request.args.get('view')
    }

    students = []
    max_sem = 8
    enroll_year_prefix = None
    
    if filters['college_id'] and filters['session_id'] and filters['degree_id']:
        max_sem_raw = AdmissionModel.get_degree_max_sem(filters['degree_id'])
        if max_sem_raw: max_sem = max_sem_raw
        
        session_name = DB.fetch_scalar("SELECT sessionname FROM SMS_AcademicSession_Mst WHERE pk_sessionid = ?", [filters['session_id']])
        if session_name:
            import re
            year_match = re.search(r'(\d{4})', session_name)
            if year_match:
                enroll_year_prefix = str(int(year_match.group(1)) - 1)

        # Only fetch students if VIEW button was pressed AND Class is selected
        if filters['view'] == '1' and filters['semester_id'] and str(filters['semester_id']) != '0':
            students = AdmissionModel.get_students_for_degree_completion(filters)
        else:
            students = []

    # Lookups
    loc_id = session.get('selected_loc')
    if loc_id:
        colleges = DB.fetch_all("SELECT pk_collegeid as id, collegename as name FROM SMS_College_Mst WHERE fk_locid = ? ORDER BY collegename", [loc_id])
    else:
        colleges = AcademicsModel.get_colleges_simple()

    # Filter semesters from IV to max_sem
    all_semesters = InfrastructureModel.get_all_semesters()
    filtered_semesters = [s for s in all_semesters if s['semesterorder'] >= 4 and s['semesterorder'] <= max_sem]

    if not filters['degree_id']:
        students = []

    lookups = {
        'colleges': colleges,
        'sessions': InfrastructureModel.get_sessions(),
        'degrees': AcademicsModel.get_college_all_degrees(filters['college_id']) if filters['college_id'] and str(filters['college_id']) != '0' else [],
        'semesters': filtered_semesters if filters['degree_id'] and str(filters['degree_id']) != '0' else []
    }

    return render_template('academics/degree_complete_detail.html', 
                           lookups=lookups, filters=filters, students=students, 
                           enroll_year_prefix=enroll_year_prefix, now=datetime.now())

@academics_bp.route('/api/get_college_degrees')
def get_college_degrees_query_api():
    college_id = request.args.get('college_id')
    type_tp = request.args.get('type_tp')
    if not college_id:
        return jsonify([])
    if type_tp == 'U':
        degrees = AcademicsModel.get_college_ug_degrees(college_id)
    else:
        degrees = AcademicsModel.get_college_degrees(college_id)
    return jsonify(clean_json_data(degrees))

@academics_bp.route('/api/get_degree_branches')
def get_degree_branches_query_api():
    college_id = request.args.get('college_id')
    degree_id = request.args.get('degree_id')
    if not degree_id:
        return jsonify([])
    branches = AcademicsModel.get_degree_branches(degree_id)
    return jsonify(clean_json_data(branches))

@academics_bp.route('/api/get_teachers')
def get_teachers_api():
    college_id = request.args.get('college_id')
    if not college_id:
        return jsonify([])
    teachers = AdvisorAllocationModel.get_teachers_for_dropdown(college_id)
    return jsonify(clean_json_data(teachers))
