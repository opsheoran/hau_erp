from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash, make_response
import math
from datetime import datetime
from app.db import DB
from app.models import (
    AcademicsModel, InfrastructureModel, EventModel, EventAssignmentModel, SemesterRegistrationModel, CounsellingModel, PaperUploadModel, CourseModel, MessagingModel, StudentExtensionModel, ExtensionManagementModel, MiscAcademicsModel, RecheckingModel, RevisedResultModel, AdvisorAllocationModel
)
from app.models import NavModel
from app.utils import get_pagination_range, clean_json_data
from functools import wraps

academics_mgmt_bp = Blueprint('academics_mgmt', __name__)

@academics_mgmt_bp.before_request
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
                    'DELETE', 'REMOVE', 'APPROVE', 'HOLD', 'REJECT', 'CANCEL'
                }
                if action in write_actions:
                    if action in {'DELETE', 'REMOVE'} and not perm.get('AllowDelete'):
                        flash('You do not have Delete permission for this page.', 'danger')
                        return redirect(url_for('main.index'))
                    if action in {'ADD', 'CREATE', 'INSERT'} and not perm.get('AllowAdd'):
                        flash('You do not have Add permission for this page.', 'danger')
                        return redirect(url_for('main.index'))
                    if action in {'SAVE', 'SUBMIT', 'UPDATE', 'EDIT', 'APPROVE', 'HOLD', 'REJECT', 'CANCEL'} and not (perm.get('AllowAdd') or perm.get('AllowUpdate')):
                        flash('You do not have permission to perform this action.', 'danger')
                        return redirect(url_for('main.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@academics_mgmt_bp.route('/event_master', methods=['GET', 'POST'])
@permission_required('Event Master')
def event_master():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'DELETE':
            if EventModel.delete_event(request.form.get('id')):
                flash('Event deleted successfully!', 'success')
            else:
                flash('Error deleting event.', 'danger')
        else:
            if EventModel.save_event(request.form):
                flash('Event saved successfully!', 'success')
            else:
                flash('Error saving event.', 'danger')
        return redirect(url_for('academics_mgmt.event_master'))

    page = request.args.get('page', 1, type=int)
    per_page = 10
    items, total = EventModel.get_events_paginated(page=page, per_page=per_page)
    
    pagination = {
        'page': page,
        'per_page': per_page,
        'total': total,
        'total_pages': math.ceil(total / per_page) if total else 1,
        'has_prev': page > 1,
        'has_next': page < (math.ceil(total / per_page) if total else 1)
    }
    
    page_range = get_pagination_range(page, pagination['total_pages'])

    return render_template('academics/event_master.html', 
                           items=clean_json_data(items), 
                           pagination=pagination, 
                           page_range=page_range)

@academics_mgmt_bp.route('/event_assignment', methods=['GET', 'POST'])
@permission_required('Event Assignment')
def event_assignment():
    user_id = session.get('user_id')
    if request.method == 'POST':
        filters = {
            'college_id': request.form.get('college_id', type=int),
            'session_id': request.form.get('session_id', type=int),
            'degree_id': request.form.get('degree_id', type=int),
            'year_id': request.form.get('year_id', type=int)
        }
        event_ids = request.form.getlist('event_ids')
        event_data = []
        for eid in event_ids:
            event_data.append({
                'event_id': int(eid),
                'odd_from': request.form.get(f'odd_from_{eid}'),
                'odd_to': request.form.get(f'odd_to_{eid}'),
                'even_from': request.form.get(f'even_from_{eid}'),
                'even_to': request.form.get(f'even_to_{eid}'),
                'remarks': request.form.get(f'remarks_{eid}'),
                'events_for': request.form.get(f'events_for_{eid}', 'A')
            })
        if EventAssignmentModel.save_assignment(filters, event_data, user_id):
            flash('Event assignments saved successfully!', 'success')
        else:
            flash('Error saving event assignments.', 'danger')
        return redirect(url_for('academics_mgmt.event_assignment', **{k:v for k,v in filters.items() if v}))

    filters = {
        'college_id': request.args.get('college_id', type=int),
        'session_id': request.args.get('session_id', type=int),
        'degree_id': request.args.get('degree_id', type=int),
        'year_id': request.args.get('year_id', type=int)
    }

    lookups = {
        'colleges': AcademicsModel.get_colleges_simple(),
        'sessions': InfrastructureModel.get_sessions(),
        'degrees': AcademicsModel.get_college_degrees(filters['college_id']) if filters['college_id'] else [],
        'years': AcademicsModel.get_degree_years()
    }

    events = []
    assignments = {}
    if all([filters['college_id'], filters['session_id'], filters['degree_id'], filters['year_id']]):
        events = EventModel.get_all_events()
        master = EventAssignmentModel.get_assignment_master(filters)
        if master:
            assignments = EventAssignmentModel.get_assignment_details(master['pk_dwceid'])

    return render_template('academics/event_assignment.html', 
                           lookups=lookups, filters=filters, events=events, assignments=assignments)

@academics_mgmt_bp.route('/semester_registration', methods=['GET', 'POST'])
@permission_required('Semester Registration')
def semester_registration():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'DELETE':
            if SemesterRegistrationModel.delete_registration(request.form.get('id')):
                flash('Registration deleted successfully!', 'success')
            else:
                flash('Error deleting registration.', 'danger')
        else:
            if SemesterRegistrationModel.save_registration(request.form):
                flash('Registration saved successfully!', 'success')
            else:
                flash('Error saving registration.', 'danger')
        return redirect(url_for('academics_mgmt.semester_registration'))

    page = request.args.get('page', 1, type=int)
    per_page = 10
    items, total = SemesterRegistrationModel.get_registrations_paginated(page=page, per_page=per_page)
    
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
        'years': AcademicsModel.get_degree_years()
    }

    return render_template('academics/semester_registration.html', 
                           items=clean_json_data(items), 
                           pagination=pagination, 
                           page_range=page_range, 
                           lookups=lookups)

@academics_mgmt_bp.route('/academic_counselling_meeting', methods=['GET', 'POST'])
@permission_required('Academic Counselling Meeting')
def academic_counselling_meeting():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'DELETE':
            if CounsellingModel.delete_meeting(request.form.get('id')):
                flash('Meeting deleted successfully!', 'success')
            else:
                flash('Error deleting meeting.', 'danger')
        else:
            pk_id = (request.form.get('id') or '').strip()
            meeting_name = (request.form.get('meeting_name') or '').strip()
            meeting_date = (request.form.get('meeting_date') or '').strip()
            meeting_agenda = (request.form.get('meeting_agenda') or '').strip()

            if not meeting_name or not meeting_date or not meeting_agenda:
                flash('Please fill all required fields.', 'danger')
                return redirect(url_for('academics_mgmt.academic_counselling_meeting'))

            file = request.files.get('report_file')
            filename = None
            if file and file.filename:
                import os
                from werkzeug.utils import secure_filename

                ext = os.path.splitext(file.filename)[1].lower()
                if ext != '.pdf':
                    flash('Only PDF files are allowed.', 'danger')
                    return redirect(url_for('academics_mgmt.academic_counselling_meeting'))

                # Enforce 2MB max upload, mirroring legacy behavior.
                try:
                    file.stream.seek(0, os.SEEK_END)
                    size = file.stream.tell()
                    file.stream.seek(0)
                except Exception:
                    size = None
                if size is not None and size > 2 * 1024 * 1024:
                    flash('File should not be more than 2MB.', 'danger')
                    return redirect(url_for('academics_mgmt.academic_counselling_meeting'))

                filename = secure_filename(file.filename)
                upload_path = os.path.join('app', 'static', 'uploads', 'counselling')
                if not os.path.exists(upload_path):
                    os.makedirs(upload_path)
                file.save(os.path.join(upload_path, filename))
            elif not pk_id:
                flash('Please select a PDF file to upload.', 'danger')
                return redirect(url_for('academics_mgmt.academic_counselling_meeting'))
            
            if CounsellingModel.save_meeting(request.form, filename):
                flash('Meeting saved successfully!', 'success')
            else:
                flash('Error saving meeting.', 'danger')
        return redirect(url_for('academics_mgmt.academic_counselling_meeting'))

    page = request.args.get('page', 1, type=int)
    search_term = request.args.get('q')
    per_page = 10
    items, total = CounsellingModel.get_meetings_paginated(search_term=search_term, page=page, per_page=per_page)
    
    pagination = {
        'page': page,
        'per_page': per_page,
        'total': total,
        'total_pages': math.ceil(total / per_page) if total else 1,
        'has_prev': page > 1,
        'has_next': page < (math.ceil(total / per_page) if total else 1)
    }
    
    page_range = get_pagination_range(page, pagination['total_pages'])

    return render_template('academics/academic_counselling_meeting.html', 
                           items=clean_json_data(items), 
                           pagination=pagination, 
                           page_range=page_range,
                           search_term=search_term)

@academics_mgmt_bp.route('/previous_paper_uploads', methods=['GET', 'POST'])
@permission_required('Previous Question Paper Uploads')
def previous_paper_uploads():
    user_id = session.get('user_id')
    if request.method == 'POST':
        file = request.files.get('report_file')
        if file and file.filename:
            import os
            from werkzeug.utils import secure_filename
            filename = secure_filename(file.filename)
            upload_path = os.path.join('app', 'static', 'uploads', 'papers')
            if not os.path.exists(upload_path):
                os.makedirs(upload_path)
            file.save(os.path.join(upload_path, filename))
            
            if PaperUploadModel.save_paper(request.form, filename, user_id):
                flash('Question paper uploaded successfully!', 'success')
            else:
                flash('Error uploading question paper.', 'danger')
        return redirect(url_for('academics_mgmt.previous_paper_uploads', **request.args))

    filters = {
        'college_id': request.args.get('college_id', type=int),
        'session_id': request.args.get('session_id', type=int),
        'degree_id': request.args.get('degree_id', type=int),
        'semester_id': request.args.get('semester_id', type=int),
        'branch_id': request.args.get('branch_id', type=int),
        'course_id': request.args.get('course_id', type=int)
    }

    items = []
    if any(filters.values()):
        items = PaperUploadModel.get_uploaded_papers(filters)

    lookups = {
        'colleges': AcademicsModel.get_colleges_simple(),
        'sessions': InfrastructureModel.get_sessions(),
        'degrees': AcademicsModel.get_college_all_degrees(filters['college_id']) if filters['college_id'] else [],
        'semesters': InfrastructureModel.get_all_semesters(),
        'branches': AcademicsModel.get_college_degree_specializations(filters['college_id'], filters['degree_id']) if (filters['college_id'] and filters['degree_id']) else [],
        'courses': CourseModel.get_courses_filtered(filters) if filters['degree_id'] else []
    }

    return render_template('academics/previous_paper_uploads.html', 
                           lookups=lookups, filters=filters, items=clean_json_data(items))

@academics_mgmt_bp.route('/sms_and_mail', methods=['GET', 'POST'])
@permission_required('SMS And Mail')
def sms_and_mail():
    if request.method == 'POST' and 'message' in request.form:
        if MessagingModel.log_message(request.form):
            flash('Message(s) sent and logged successfully!', 'success')
        else:
            flash('Error sending message(s).', 'danger')
        return redirect(url_for('academics_mgmt.sms_and_mail', **{k:v for k,v in request.form.items() if k != 'message'}))

    filters = {
        'college_id': request.args.get('college_id', type=int),
        'session_id': request.args.get('session_id', type=int),
        'degree_id': request.args.get('degree_id', type=int),
        'semester_id': request.args.get('semester_id', type=int),
        'branch_id': request.args.get('branch_id', type=int)
    }

    students = []
    if all([filters['college_id'], filters['session_id'], filters['degree_id']]):
        students = MessagingModel.get_students_for_messaging(filters)

    lookups = {
        'colleges': AcademicsModel.get_colleges_simple(),
        'sessions': InfrastructureModel.get_sessions(),
        'degrees': AcademicsModel.get_college_all_degrees(filters['college_id']) if filters['college_id'] else [],
        'semesters': InfrastructureModel.get_all_semesters(),
        'branches': AcademicsModel.get_college_degree_specializations(filters['college_id'], filters['degree_id']) if (filters['college_id'] and filters['degree_id']) else []
    }

    return render_template('academics/sms_and_mail.html', 
                           lookups=lookups, filters=filters, students=clean_json_data(students))

@academics_mgmt_bp.route('/student_extension', methods=['GET', 'POST'])
@permission_required('Student Extension')
def student_extension():
    if request.method == 'POST':
        if StudentExtensionModel.save_extensions(request.form):
            flash('Extension saved successfully!', 'success')
        else:
            flash('Please select student(s) and semester.', 'danger')

        return redirect(url_for('academics_mgmt.student_extension', **{k: v for k, v in request.form.items() if k != 'student_ids'}))

    filters = {
        'college_id': request.args.get('college_id', type=int),
        'session_id': request.args.get('session_id', type=int),
        'degree_id': request.args.get('degree_id', type=int),
        'semester_id': request.args.get('semester_id', type=int),
        'branch_id': request.args.get('branch_id', type=int),
        'enrollment_no': request.args.get('enrollment_no', type=str)
    }

    students = []
    if all([filters['college_id'], filters['session_id'], filters['degree_id'], filters['semester_id']]):
        students = StudentExtensionModel.get_students_for_extension(filters)

    lookups = {
        'colleges': AcademicsModel.get_colleges_simple(),
        'sessions': InfrastructureModel.get_sessions(),
        'degrees': AcademicsModel.get_college_all_degrees(filters['college_id']) if filters['college_id'] else [],
        'semesters': InfrastructureModel.get_all_semesters(),
        'branches': AcademicsModel.get_college_degree_specializations(filters['college_id'], filters['degree_id']) if (filters['college_id'] and filters['degree_id']) else [],
        'ext_semesters': InfrastructureModel.get_extension_semesters()
    }

    return render_template('academics/student_extension.html',
                           lookups=lookups,
                           filters=filters,
                           students=clean_json_data(students))

@academics_mgmt_bp.route('/student_transfer', methods=['GET', 'POST'])
@permission_required('Student Transfer Details')
def student_transfer_details():
    if request.method == 'POST':
        action = (request.form.get('action') or '').upper()

        # --- Transfer single student (Admission No. update) ---
        if action == 'TRANSFER_SINGLE':
            college_id = request.form.get('single_college_id', type=int)
            old_no = request.form.get('old_admission_no')
            new_no = request.form.get('new_admission_no')
            ok, msg = MiscAcademicsModel.transfer_single_student(college_id, old_no, new_no, session.get('user_id'))
            flash(msg, 'success' if ok else 'danger')
            return redirect(url_for('academics_mgmt.student_transfer_details'))

        # --- Swap Admission No. between two students ---
        if action == 'SWAP':
            college_id = request.form.get('swap_college_id', type=int)
            adm1 = request.form.get('admission_no_1')
            adm2 = request.form.get('admission_no_2')
            ok, msg = MiscAcademicsModel.swap_students(college_id, adm1, adm2, session.get('user_id'))
            flash(msg, 'success' if ok else 'danger')
            return redirect(url_for('academics_mgmt.student_transfer_details'))

        # --- View report (PDF/Excel/Word) ---
        if action == 'VIEW_REPORT':
            import io
            rpt_format = (request.form.get('rpt_format') or '3').strip()  # 1=Word,2=Excel,3=PDF

            filters = {
                'college_id': request.form.get('college_id', type=int),
                'session_id': request.form.get('session_id', type=int),
                'degree_id': request.form.get('degree_id', type=int),
                'semester_id': request.form.get('semester_id', type=int),
                'branch_id': request.form.get('branch_id', type=int),
            }
            search = {
                'admission_no': request.form.get('admission_no') or '',
                'student_name': request.form.get('student_name') or '',
            }

            data = MiscAcademicsModel.get_students_for_transfer(filters, search=search)
            if not data:
                flash('No data found for selected filters.', 'warning')
                return redirect(url_for('academics_mgmt.student_transfer_details', **{k: v for k, v in filters.items() if v}))

            # Resolve names for the report header
            colleges = {c['id']: c['name'] for c in AcademicsModel.get_colleges_simple()}
            sessions = {s['id']: s['name'] for s in InfrastructureModel.get_sessions()}
            degrees = {d['id']: d['name'] for d in (AcademicsModel.get_college_all_degrees(filters['college_id']) if filters.get('college_id') else [])}
            semesters = {s['id']: s['name'] for s in InfrastructureModel.get_all_semesters()}
            branches = {b['id']: b['name'] for b in (AcademicsModel.get_college_degree_specializations(filters['college_id'], filters['degree_id']) if (filters.get('college_id') and filters.get('degree_id')) else [])}

            hdr = {
                'college': colleges.get(filters.get('college_id')),
                'session': sessions.get(filters.get('session_id')),
                'degree': degrees.get(filters.get('degree_id')),
                'semester': semesters.get(filters.get('semester_id')),
                'branch': branches.get(filters.get('branch_id')),
            }

            now_str = datetime.now().strftime('%d/%m/%Y %H:%M:%S')

            if rpt_format == '2':  # Excel
                import pandas as pd
                df = pd.DataFrame(data)
                # Keep only user-facing columns
                keep = ['fullname', 'AdmissionNo', 'enrollmentno', 'semester_roman', 'department_name']
                cols = [c for c in keep if c in df.columns]
                df = df[cols].rename(columns={
                    'fullname': 'Student Name',
                    'AdmissionNo': 'Admission No.',
                    'enrollmentno': 'Enrollment No.',
                    'semester_roman': 'Class',
                    'department_name': 'Department',
                })
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False, sheet_name='Students')
                output.seek(0)
                resp = make_response(output.getvalue())
                resp.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                resp.headers['Content-Disposition'] = 'attachment; filename=Student_Transfer_Details.xlsx'
                return resp

            # Word format: download HTML as .doc (simple, like many legacy systems)
            if rpt_format == '1':
                rendered = render_template('academics/reports/student_transfer_report.html', data=clean_json_data(data), hdr=hdr, now=now_str)
                resp = make_response(rendered)
                resp.headers['Content-Type'] = 'application/msword'
                resp.headers['Content-Disposition'] = 'attachment; filename=Student_Transfer_Details.doc'
                return resp

            # Default: PDF
            from xhtml2pdf import pisa
            rendered = render_template('academics/reports/student_transfer_report.html', data=clean_json_data(data), hdr=hdr, now=now_str, pdf=True)
            pdf_out = io.BytesIO()
            pisa.CreatePDF(io.BytesIO(rendered.encode('UTF-8')), dest=pdf_out)
            pdf_out.seek(0)
            resp = make_response(pdf_out.getvalue())
            resp.headers['Content-Type'] = 'application/pdf'
            resp.headers['Content-Disposition'] = 'attachment; filename=Student_Transfer_Details.pdf'
            return resp

    # --- GET: filters + list ---
    filters = {
        'college_id': request.args.get('college_id', type=int),
        'session_id': request.args.get('session_id', type=int),
        'degree_id': request.args.get('degree_id', type=int),
        'semester_id': request.args.get('semester_id', type=int),
        'branch_id': request.args.get('branch_id', type=int),
    }
    search = {
        'admission_no': request.args.get('admission_no') or '',
        'student_name': request.args.get('student_name') or '',
    }

    page = request.args.get('page', 1, type=int)
    per_page = 20
    required_ok = all([filters['college_id'], filters['session_id'], filters['degree_id'], filters['semester_id']])

    items, total = ([], 0)
    if required_ok:
        items, total = MiscAcademicsModel.get_students_for_transfer_paginated(filters, search=search, page=page, per_page=per_page)

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
        'degrees': AcademicsModel.get_college_all_degrees(filters['college_id']) if filters['college_id'] else [],
        'semesters': InfrastructureModel.get_all_semesters(),
        'branches': AcademicsModel.get_college_degree_specializations(filters['college_id'], filters['degree_id']) if (filters['college_id'] and filters['degree_id']) else [],
    }

    return render_template('academics/student_transfer.html',
                           lookups=lookups,
                           filters=filters,
                           search=search,
                           items=clean_json_data(items),
                           pagination=pagination,
                           page_range=page_range)

@academics_mgmt_bp.route('/api/student_lookup', methods=['GET'])
@permission_required('Student Transfer Details')
def student_lookup():
    college_id = request.args.get('college_id', type=int)
    admission_no = request.args.get('admission_no') or ''
    row = MiscAcademicsModel.find_student_by_admission_no(college_id, admission_no)
    return jsonify(clean_json_data(row if row else {}))

@academics_mgmt_bp.route('/registration_cancel', methods=['GET', 'POST'])
@permission_required('Student Registration Cancel')
def registration_cancel():
    if request.method == 'POST':
        action = (request.form.get('action') or '').upper()
        if action == 'UPDATE':
            redirect_filters = {
                'college_id': request.form.get('college_id', type=int),
                'session_id': request.form.get('session_id', type=int),
                'degree_id': request.form.get('degree_id', type=int),
                'semester_id': request.form.get('semester_id', type=int),
                'branch_id': request.form.get('branch_id', type=int),
                'page': request.form.get('page', type=int) or 1
            }
            student_ids = request.form.getlist('student_ids')
            selected_rows = []
            for sid in student_ids:
                try:
                    sid_int = int(sid)
                except Exception:
                    continue
                selected_rows.append({
                    'pk_sid': sid_int,
                    'remarks': request.form.get(f'remarks_{sid}', ''),
                    'returnAmount': request.form.get(f'amount_{sid}', 0),
                })

            ok, msg = MiscAcademicsModel.update_registration_cancel(selected_rows, user_id=session.get('user_id'))
            flash(msg, 'success' if ok else 'danger')

        return redirect(url_for('academics_mgmt.registration_cancel', **{k: v for k, v in (redirect_filters or {}).items() if v is not None}))

    filters = {
        'college_id': request.args.get('college_id', type=int),
        'session_id': request.args.get('session_id', type=int),
        'degree_id': request.args.get('degree_id', type=int),
        'semester_id': request.args.get('semester_id', type=int),
        'branch_id': request.args.get('branch_id', type=int),
    }

    page = request.args.get('page', 1, type=int)
    per_page = 20
    required_ok = all([filters['college_id'], filters['session_id'], filters['degree_id'], filters['semester_id']])

    items, total = ([], 0)
    if required_ok:
        items, total = MiscAcademicsModel.get_students_for_registration_cancel(filters, page=page, per_page=per_page)

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
        'degrees': AcademicsModel.get_college_all_degrees(filters['college_id']) if filters['college_id'] else [],
        'semesters': InfrastructureModel.get_all_semesters(),
        'branches': AcademicsModel.get_college_degree_specializations(filters['college_id'], filters['degree_id']) if (filters['college_id'] and filters['degree_id']) else [],
    }

    return render_template('academics/registration_cancel.html',
                           lookups=lookups,
                           filters=filters,
                           items=clean_json_data(items),
                           pagination=pagination,
                           page_range=page_range)

@academics_mgmt_bp.route('/student_semester_change', methods=['GET', 'POST'])
@permission_required('Student Semester Change')
def student_semester_change():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    items, total = MiscAcademicsModel.get_semester_changes_paginated(page=page, per_page=per_page)
    
    pagination = {
        'page': page,
        'per_page': per_page,
        'total': total,
        'total_pages': math.ceil(total / per_page) if total else 1,
        'has_prev': page > 1,
        'has_next': page < (math.ceil(total / per_page) if total else 1)
    }
    page_range = get_pagination_range(page, pagination['total_pages'])

    return render_template('academics/student_semester_change.html', items=clean_json_data(items), pagination=pagination, page_range=page_range)

@academics_mgmt_bp.route('/extension_management', methods=['GET'])
@permission_required('Extension Management')
def extension_management():
    action = (request.args.get('action') or '').upper()

    filters = {
        'college_id': request.args.get('college_id', type=int),
        'session_id': request.args.get('session_id', type=int),
        'degree_id': request.args.get('degree_id', type=int),
        'branch_id': request.args.get('branch_id', type=int),
        'semester_id': request.args.get('semester_id', type=int),
        'student_id': request.args.get('student_id', type=int)
    }

    students = []
    courses = []

    required_ok = all([filters['college_id'], filters['session_id'], filters['degree_id'], filters['semester_id']])
    if required_ok and (action in ('GET_STUDENT', 'VIEW_COURSES') or filters['student_id']):
        students = ExtensionManagementModel.get_students(filters)

    if required_ok and action == 'VIEW_COURSES' and filters['student_id']:
        courses = ExtensionManagementModel.get_courses(filters)

    lookups = {
        'colleges': AcademicsModel.get_colleges_simple(),
        'sessions': InfrastructureModel.get_sessions(),
        'degrees': AcademicsModel.get_college_all_degrees(filters['college_id']) if filters['college_id'] else [],
        'branches': AcademicsModel.get_college_degree_specializations(filters['college_id'], filters['degree_id']) if (filters['college_id'] and filters['degree_id']) else [],
        'semesters': InfrastructureModel.get_extension_semesters()
    }

    return render_template('academics/extension_management.html',
                           lookups=lookups,
                           filters=filters,
                           students=clean_json_data(students),
                           courses=clean_json_data(courses))

@academics_mgmt_bp.route('/course_approval_status', methods=['GET'])
@permission_required('Course Approval Status')
def course_approval_status():
    filters = {
        'college_id': request.args.get('college_id', type=int),
        'session_id': request.args.get('session_id', type=int),
        'degree_id': request.args.get('degree_id', type=int),
        'sem_type': request.args.get('sem_type', type=int),  # 1 odd, 2 even
        'exconfig_id': request.args.get('exconfig_id', type=int),
        'detail_semester_id': request.args.get('detail_semester_id', type=int),
        'detail_student_id': request.args.get('detail_student_id', type=int),
        'view': request.args.get('view')
    }

    rows = []
    pending_students = []
    student_courses = []

    required_ok = all([filters['college_id'], filters['session_id'], filters['degree_id'], filters['sem_type'], filters['exconfig_id']])
    if required_ok and filters['view'] == '1':
        rows = MiscAcademicsModel.get_course_approval_status_degree_semesterwise(filters)

    if required_ok and filters.get('detail_semester_id'):
        pending_students = MiscAcademicsModel.get_course_approval_pending_students(filters, filters['detail_semester_id'])
        if filters.get('detail_student_id'):
            student_courses = MiscAcademicsModel.get_course_approval_student_courses(filters, filters['detail_semester_id'], filters['detail_student_id'])

    from app.models import CourseAllocationModel
    lookups = {
        'colleges': AcademicsModel.get_colleges_simple(),
        'sessions': InfrastructureModel.get_sessions(),
        'degrees': AcademicsModel.get_college_all_degrees(filters['college_id']) if filters['college_id'] else [],
        'exam_configs': CourseAllocationModel.get_exam_configs(filters['degree_id'], filters['session_id']) if filters['degree_id'] else []
    }

    return render_template('academics/course_approval_status.html',
                           lookups=lookups,
                           filters=filters,
                           rows=clean_json_data(rows),
                           pending_students=clean_json_data(pending_students),
                           student_courses=clean_json_data(student_courses))

@academics_mgmt_bp.route('/rechecking_approval_hod_pg', methods=['GET', 'POST'])
@permission_required('rechecking Approval By Hod(PG)')
def rechecking_approval_hod_pg():
    if request.method == 'POST':
        action = (request.form.get('action') or '').upper()
        if action == 'DECIDE':
            pk_id = request.form.get('pk_id', type=int)
            decision = request.form.get('decision') or 'A'
            remarks = request.form.get('remarks') or ''
            ok, msg = RecheckingModel.update_hod_decision(pk_id, decision, remarks, user_id=session.get('user_id'))
            flash(msg, 'success' if ok else 'danger')

        redirect_filters = {
            'college_id': request.form.get('college_id', type=int),
            'session_id': request.form.get('session_id', type=int),
            'degree_id': request.form.get('degree_id', type=int),
            'view': request.form.get('view') or '1'
        }
        return redirect(url_for('academics_mgmt.rechecking_approval_hod_pg', **{k: v for k, v in redirect_filters.items() if v}))

    filters = {
        'college_id': request.args.get('college_id', type=int),
        'session_id': request.args.get('session_id', type=int),
        'degree_id': request.args.get('degree_id', type=int),
        'role': 'HOD',
        'programme': 'PG'
    }
    view = request.args.get('view')
    pending = []
    processed = []
    if view == '1' and all([filters['college_id'], filters['session_id'], filters['degree_id']]):
        pending = RecheckingModel.get_rechecking_requests(filters, processed=False)
        processed = RecheckingModel.get_rechecking_requests(filters, processed=True)
    
    lookups = {
        'colleges': AcademicsModel.get_colleges_simple(),
        'sessions': InfrastructureModel.get_sessions(),
        'degrees': AcademicsModel.get_college_all_degrees(filters['college_id']) if filters['college_id'] else []
    }
    return render_template('academics/rechecking_approval_hod_pg.html',
                           title='Rechecking Course Approval By HOD',
                           lookups=lookups,
                           filters=filters,
                           view=view,
                           pending=clean_json_data(pending),
                           processed=clean_json_data(processed))

@academics_mgmt_bp.route('/rechecking_approval_advisor_ug', methods=['GET'])
@permission_required('Rechecking Approval By Advisor[UG]')
def rechecking_approval_advisor_ug():
    filters = {
        'college_id': request.args.get('college_id', type=int),
        'session_id': request.args.get('session_id', type=int),
        'degree_id': request.args.get('degree_id', type=int),
        'role': 'Advisor',
        'programme': 'UG'
    }
    items = []
    if all([filters['college_id'], filters['session_id'], filters['degree_id']]):
        items = RecheckingModel.get_rechecking_requests(filters)
    
    lookups = {
        'colleges': AcademicsModel.get_colleges_simple(),
        'sessions': InfrastructureModel.get_sessions(),
        'degrees': AcademicsModel.get_college_all_degrees(filters['college_id']) if filters['college_id'] else []
    }
    return render_template('academics/rechecking_approval.html', title='Rechecking Approval By Advisor[UG]', items=clean_json_data(items), lookups=lookups, filters=filters)

@academics_mgmt_bp.route('/rechecking_approval_dean_ug', methods=['GET'])
@permission_required('Rechecking Approval By Dean[UG]')
def rechecking_approval_dean_ug():
    filters = {
        'college_id': request.args.get('college_id', type=int),
        'session_id': request.args.get('session_id', type=int),
        'degree_id': request.args.get('degree_id', type=int),
        'role': 'Dean',
        'programme': 'UG'
    }
    items = []
    if all([filters['college_id'], filters['session_id'], filters['degree_id']]):
        items = RecheckingModel.get_rechecking_requests(filters)
    
    lookups = {
        'colleges': AcademicsModel.get_colleges_simple(),
        'sessions': InfrastructureModel.get_sessions(),
        'degrees': AcademicsModel.get_college_all_degrees(filters['college_id']) if filters['college_id'] else []
    }
    return render_template('academics/rechecking_approval.html', title='Rechecking Approval By Dean[UG]', items=clean_json_data(items), lookups=lookups, filters=filters)

@academics_mgmt_bp.route('/advisor_allocation_ug', methods=['GET', 'POST'])
@permission_required('Advisor Allocation(For UG)')
def advisor_allocation_ug():
    user_id = session.get('user_id')
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action in ('SAVE', 'UPDATE'):
            filters = {
                'college_id': request.form.get('college_id'),
                'session_id': request.form.get('session_id'),
                'degree_id': request.form.get('degree_id'),
                'branch_id': request.form.get('branch_id')
            }
            student_ids = request.form.getlist('student_ids')
            teacher_id = request.form.get('teacher_id')
            
            success, msg = AdvisorAllocationModel.save_advisor_allocation(filters, student_ids, teacher_id, user_id)
            if success:
                flash(msg, 'success')
            else:
                flash(msg, 'danger')
            
            return redirect(url_for('academics_mgmt.advisor_allocation_ug', **filters))

    filters = {
        'college_id': request.values.get('college_id'),
        'session_id': request.values.get('session_id'),
        'degree_id': request.values.get('degree_id'),
        'branch_id': request.values.get('branch_id'),
        'teacher_id': request.values.get('teacher_id'),
        'fetch': request.values.get('fetch')
    }

    students = []
    if filters['fetch'] == '1' and all([filters['college_id'], filters['session_id'], filters['degree_id']]):
        students = AdvisorAllocationModel.get_students_for_advisor_allocation(filters)

    loc_id = session.get('selected_loc')
    if loc_id:
        colleges = DB.fetch_all(
            "SELECT pk_collegeid as id, collegename as name FROM SMS_College_Mst WHERE fk_locid = ? ORDER BY collegename",
            [loc_id],
        )
    else:
        colleges = AcademicsModel.get_colleges_simple()

    lookups = {
        'colleges': colleges,
        'sessions': InfrastructureModel.get_sessions(),
        'degrees': AcademicsModel.get_college_ug_degrees(filters['college_id']) if filters['college_id'] else [],
        'teachers': AdvisorAllocationModel.get_teachers_for_dropdown(filters['college_id'])
    }

    return render_template('academics/advisor_allocation_ug.html', 
                           lookups=lookups, 
                           filters=filters, 
                           students=clean_json_data(students))

@academics_mgmt_bp.route('/revised_result', methods=['GET'])
@permission_required('Revised Result')
def revised_result():
    filters = {
        'college_id': request.args.get('college_id', type=int),
        'session_id': request.args.get('session_id', type=int),
        'degree_id': request.args.get('degree_id', type=int),
        'is_pg': request.args.get('programme') == 'PG'
    }
    items = []
    if all([filters['college_id'], filters['session_id'], filters['degree_id']]):
        items = RevisedResultModel.get_revised_results(filters)
    
    lookups = {
        'colleges': AcademicsModel.get_colleges_simple(),
        'sessions': InfrastructureModel.get_sessions(),
        'degrees': AcademicsModel.get_college_all_degrees(filters['college_id']) if filters['college_id'] else []
    }
    return render_template('academics/revised_result.html', items=clean_json_data(items), lookups=lookups, filters=filters)
