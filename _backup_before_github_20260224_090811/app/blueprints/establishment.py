from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
from app.models import (
    EstablishmentModel, NavModel, EmployeeModel, DesignationCategoryModel, 
    EmployeeDocumentModel, EmployeeQualificationModel, EmployeePermissionModel, 
    EmployeeFamilyModel, EmployeeNomineeModel, EmployeeBookModel, LTCModel, 
    PreviousJobModel, ForeignVisitModel, TrainingModel, DeptExamModel, 
    ServiceVerificationModel, SARModel, FirstAppointmentModel, IncrementModel, 
    NoDuesModel, EarnedLeaveModel, DisciplinaryModel, LoanModel, BookGrantModel, BonusModel
)
from app.db import DB
from app.utils import get_pagination, to_int
from functools import wraps
import math

establishment_bp = Blueprint('establishment', __name__)

ESTABLISHMENT_MENU_CONFIG = {
    'Masters': {
        'Masters': {
            'Establishment Masters': [
                'City Category Master', 'City Master', 'Salutation Master', 'Religion Master',
                'Relation Master', 'Category Master', 'Gad-Nongad Master', 'Class Master', 'Discipline Master',
                'Marital Status Master', 'Funds Sponsor Master', 'ExamType Master', 'Designation Category Master'
            ],
            'Employee Masters': [
                'Department Master', 'Section Master', 'Designation Master', 'Employee Master',
                'Employee Master Scheme Wise', 'Recruitment Employee Import'
            ],
            'SAR Masters': [
                'SAR Category Master', 'SAR Activity Master', 'SAR Grade Master', 'SAR Employee Master'
            ]
        }
    },
    'Transactions': {
        'Transactions': {
            'Personal Details': [
                'Employee Demographic Details', 'Employee Document Details', 'Education Qualification Details',
                'Employee Permission of Qualification Details', 'Employee Family Details',
                'Employee Nominee Details', 'Employee Books Details', 'LTC Detail'
            ],
            'Job Details': [
                'Employee Previous Job Details', 'Employee Foreign Visit Details', 'Employee Training Details',
                'Employee Departmental Exam Details', 'Employee Service Verification Details',
                'Disciplinary Action/Reward Details', 'Employee Loan Details', 'Employee Book Grant Amount Details'
            ],
            'Increment/Promotion': [
                'SAR/ACR Admin Transaction', 'Employee First Appointment Details', 'Emp Increment Payrevision',
                'Employee Promotion/Financial Up-gradation', 'Employee No-Dues Detail',
                'Appointing Authority', 'Controlling DDO Department Reliving', 'Controlling DDO Department Joining'
            ]
        }
    },
    'Reports': {
        'Reports': {
            'Reports': [
                'Employee Service Book Report', 'Establishment OfficeWise Report', 'Organisation Data',
                'Generate Seniority List'
            ]
        }
    }
}

def permission_required(page_caption):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session: return redirect(url_for('auth.login'))
            user_id = session['user_id']
            loc_id = session.get('selected_loc')
            perm = NavModel.check_permission(user_id, loc_id, page_caption)
            if not perm or not perm.get('AllowView'): return redirect(url_for('main.index'))
            request.page_perms = perm
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@establishment_bp.route('/api/employee/search')
def api_employee_search():
    term = request.args.get('term', '')
    if len(term) < 2: return jsonify([])
    query = """
        SELECT E.pk_empid as id, E.empname as name, E.empcode as code, D.designation
        FROM SAL_Employee_Mst E
        LEFT JOIN SAL_Designation_Mst D ON E.fk_desgid = D.pk_desgid
        WHERE (E.empname LIKE ? OR E.empcode LIKE ?) AND E.employeeleftstatus = 'N'
    """
    return jsonify(DB.fetch_all(query, [f'%{term}%', f'%{term}%']))

@establishment_bp.route('/employee_demographic_details', methods=['GET', 'POST'])
@permission_required('Employee Demographic Details')
def employee_demographic_details():
    user_id = session.get('user_id'); loc_id = session.get('selected_loc'); perm = request.page_perms
    emp_id = request.args.get('emp_id')
    edit_id = request.args.get('edit_id')
    
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'RESET':
            return redirect(url_for('establishment.employee_demographic_details'))
        
        target_emp_id = request.form.get('emp_id')
        if not target_emp_id:
            flash('Please select an employee first.', 'warning')
            return redirect(url_for('establishment.employee_demographic_details'))
            
        try:
            EmployeeModel.save_demographic_details(request.form, user_id)
            flash('Data updated successfully.', 'success')
            return redirect(url_for('establishment.employee_demographic_details', emp_id=target_emp_id))
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
            return redirect(url_for('establishment.employee_demographic_details', emp_id=target_emp_id))

    filters = {
        's_emp_code': (request.args.get('s_emp_code') or '').strip(),
        's_manual_code': (request.args.get('s_manual_code') or '').strip(),
        's_emp_name': (request.args.get('s_emp_name') or '').strip(),
        's_ddo_id': (request.args.get('s_ddo_id') or '').strip(),
        's_loc_id': (request.args.get('s_loc_id') or '').strip(),
        's_dept_id': (request.args.get('s_dept_id') or '').strip(),
        's_desg_id': (request.args.get('s_desg_id') or '').strip(),
        's_sort_by': request.args.get('s_sort_by', 'name')
    }

    where = " WHERE E.employeeleftstatus = 'N'"
    params = []
    if filters['s_emp_code']: where += ' AND E.empcode LIKE ?'; params.append(f"%{filters['s_emp_code']}%")
    if filters['s_manual_code']: where += ' AND E.manualempcode LIKE ?'; params.append(f"%{filters['s_manual_code']}%")
    if filters['s_emp_name']: where += ' AND E.empname LIKE ?'; params.append(f"%{filters['s_emp_name']}%")
    if filters['s_ddo_id']: where += ' AND E.fk_ddoid = ?'; params.append(filters['s_ddo_id'])
    if filters['s_loc_id']: where += ' AND E.fk_locid = ?'; params.append(filters['s_loc_id'])
    if filters['s_dept_id']: where += ' AND E.fk_deptid = ?'; params.append(filters['s_dept_id'])
    if filters['s_desg_id']: where += ' AND E.fk_desgid = ?'; params.append(filters['s_desg_id'])

    order_by = "E.empname" if filters['s_sort_by'] == 'name' else "E.manualempcode"

    page = to_int(request.args.get('page', 1))
    per_page = 10
    total_count = to_int(DB.fetch_scalar(f"SELECT COUNT(*) FROM SAL_Employee_Mst E {where}", params) or 0)
    total_pages = max(1, math.ceil(total_count / per_page)) if total_count else 1
    offset = (page - 1) * per_page

    employees = DB.fetch_all(f'''
        SELECT E.pk_empid as id, E.empcode, E.manualempcode, E.empname, 
               D.description as dept_name, DS.designation as desg_name, 
               LOC.locname as location_name, ST.saltype as salary_type
        FROM SAL_Employee_Mst E
        LEFT JOIN Department_Mst D ON E.fk_deptid = D.pk_deptid
        LEFT JOIN SAL_Designation_Mst DS ON E.fk_desgid = DS.pk_desgid
        LEFT JOIN Location_Mst LOC ON E.fk_locid = LOC.pk_locid
        LEFT JOIN SAL_SalaryType_Mst ST ON E.fk_saltypeid = ST.pk_saltypeid
        {where} ORDER BY {order_by} OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY
    ''', params)

    for emp in employees:
        emp['edit_url'] = url_for('establishment.employee_demographic_details', edit_id=emp['id'], **filters)

    edit_data = EmployeeModel.get_employee_full_details(edit_id or emp_id) if (edit_id or emp_id) else None
    lookups = EmployeeModel.get_full_lookups()
    
    # Pagination helpers
    page_links = []
    start_page = max(1, page - 2)
    end_page = min(total_pages, start_page + 4)
    if end_page - start_page < 4: start_page = max(1, end_page - 4)
    
    for p in range(start_page, end_page + 1):
        f_copy = filters.copy()
        f_copy['page'] = p
        page_links.append({'page': p, 'url': url_for('establishment.employee_demographic_details', **f_copy), 'active': p == page})

    prev_url = None
    if page > 1:
        f_copy = filters.copy()
        f_copy['page'] = page - 1
        prev_url = url_for('establishment.employee_demographic_details', **f_copy)

    next_url = None
    if page < total_pages:
        f_copy = filters.copy()
        f_copy['page'] = page + 1
        next_url = url_for('establishment.employee_demographic_details', **f_copy)

    return render_template('establishment/employee_demographic_details.html', 
                         edit_data=edit_data, lookups=lookups, perm=perm, 
                         employees=employees, filters=filters, 
                         page=page, total_pages=total_pages, total_count=total_count,
                         page_links=page_links, prev_url=prev_url, next_url=next_url)

@establishment_bp.route('/employee_document_details', methods=['GET', 'POST'])
@permission_required('Employee Document Details')
def employee_document_details():
    user_id = session.get('user_id'); perm = request.page_perms
    emp_id = request.args.get('emp_id')
    edit_id = request.args.get('edit_id')
    delete_id = request.args.get('delete_id')

    if delete_id and perm.get('AllowDelete'):
        try:
            EmployeeDocumentModel.delete(delete_id)
            flash('Document deleted successfully.', 'success')
        except Exception as e:
            flash(f'Error deleting document: {str(e)}', 'danger')
        return redirect(url_for('establishment.employee_document_details', emp_id=emp_id))

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'RESET':
            return redirect(url_for('establishment.employee_document_details'))
        
        target_emp_id = request.form.get('target_emp_id')
        if not target_emp_id:
            flash('Please select an employee first.', 'warning')
            return redirect(url_for('establishment.employee_document_details'))

        doc_id = request.form.get('doc_id')
        cat_id = request.form.get('doc_cat_id')
        att_desig = request.form.get('att_designation')
        
        file = request.files.get('document_file')
        filename = None
        if file and file.filename:
            import os
            from werkzeug.utils import secure_filename
            ext = os.path.splitext(file.filename)[1].lower()
            if ext not in ['.jpg', '.jpeg', '.pjpeg', '.bmp', '.gif', '.png', '.pdf']:
                flash('Invalid file type.', 'danger')
                return redirect(url_for('establishment.employee_document_details', emp_id=target_emp_id))
            
            # 2MB for images, 5MB for PDF
            max_size = 5 * 1024 * 1024 if ext == '.pdf' else 2 * 1024 * 1024
            file.seek(0, os.SEEK_END); size = file.tell(); file.seek(0)
            if size > max_size:
                flash(f'File size exceeds limit ({max_size//(1024*1024)}MB).', 'danger')
                return redirect(url_for('establishment.employee_document_details', emp_id=target_emp_id))

            filename = secure_filename(f"{target_emp_id}_{cat_id}_{file.filename}")
            upload_path = os.path.join('app', 'static', 'uploads', 'employee_docs')
            if not os.path.exists(upload_path): os.makedirs(upload_path)
            file.save(os.path.join(upload_path, filename))

        try:
            data = {
                'emp_id': target_emp_id,
                'doc_id': doc_id,
                'cat_id': cat_id,
                'filename': filename,
                'att_desig': att_desig
            }
            EmployeeDocumentModel.save(data, user_id)
            flash('Document saved successfully.', 'success')
            return redirect(url_for('establishment.employee_document_details', emp_id=target_emp_id))
        except Exception as e:
            flash(f'Error saving document: {str(e)}', 'danger')
            return redirect(url_for('establishment.employee_document_details', emp_id=target_emp_id))

    employee_info = EmployeeModel.get_employee_full_details(emp_id) if emp_id else None
    documents = EmployeeDocumentModel.get_employee_documents(emp_id) if emp_id else []
    edit_data = EmployeeDocumentModel.get_by_id(edit_id) if edit_id else None
    lookups = {
        'doc_categories': EmployeeDocumentModel.get_categories()
    }
    return render_template('establishment/employee_document_details.html', 
                         employee_info=employee_info, documents=documents, 
                         edit_data=edit_data, lookups=lookups, perm=perm, emp_id=emp_id)

@establishment_bp.route('/employee_qualification_details', methods=['GET', 'POST'])
@permission_required('Education Qualification Details')
def employee_qualification_details():
    user_id = session.get('user_id'); perm = request.page_perms
    emp_id = request.args.get('emp_id')
    edit_id = request.args.get('edit_id')
    delete_id = request.args.get('delete_id')

    if delete_id and perm.get('AllowDelete'):
        try:
            EmployeeQualificationModel.delete(delete_id)
            flash('Qualification deleted successfully.', 'success')
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('establishment.employee_qualification_details', emp_id=emp_id))

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'RESET':
            return redirect(url_for('establishment.employee_qualification_details'))
        
        target_emp_id = request.form.get('target_emp_id')
        if not target_emp_id:
            flash('Please select an employee first.', 'warning')
            return redirect(url_for('establishment.employee_qualification_details'))

        file = request.files.get('document_file')
        filename = None
        if file and file.filename:
            import os
            from werkzeug.utils import secure_filename
            filename = secure_filename(f"QUAL_{target_emp_id}_{file.filename}")
            upload_path = os.path.join('app', 'static', 'uploads', 'employee_qualifications')
            if not os.path.exists(upload_path): os.makedirs(upload_path)
            file.save(os.path.join(upload_path, filename))

        try:
            data = request.form.to_dict()
            data['emp_id'] = target_emp_id
            data['filename'] = filename
            data['quali_id'] = request.form.get('quali_id')
            EmployeeQualificationModel.save(data, user_id)
            flash('Qualification saved successfully.', 'success')
            return redirect(url_for('establishment.employee_qualification_details', emp_id=target_emp_id))
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
            return redirect(url_for('establishment.employee_qualification_details', emp_id=target_emp_id))

    employee_info = EmployeeModel.get_employee_full_details(emp_id) if emp_id else None
    qualifications = EmployeeQualificationModel.get_employee_qualifications(emp_id) if emp_id else []
    edit_data = EmployeeQualificationModel.get_by_id(edit_id) if edit_id else None
    return render_template('establishment/employee_qualification_details.html', 
                         employee_info=employee_info, qualifications=qualifications, 
                         edit_data=edit_data, perm=perm, emp_id=emp_id)

@establishment_bp.route('/employee_permission_details', methods=['GET', 'POST'])
@permission_required('Employee Permission of Qualification Details')
def employee_permission_details():
    user_id = session.get('user_id'); perm = request.page_perms
    emp_id = request.args.get('emp_id')
    edit_id = request.args.get('edit_id')
    delete_id = request.args.get('delete_id')

    if delete_id and perm.get('AllowDelete'):
        try:
            EmployeePermissionModel.delete(delete_id)
            flash('Record deleted successfully.', 'success')
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('establishment.employee_permission_details', emp_id=emp_id))

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'RESET':
            return redirect(url_for('establishment.employee_permission_details'))
        
        target_emp_id = request.form.get('target_emp_id')
        if not target_emp_id:
            flash('Please select an employee first.', 'warning')
            return redirect(url_for('establishment.employee_permission_details'))

        file = request.files.get('document_file')
        filename = None
        if file and file.filename:
            import os
            from werkzeug.utils import secure_filename
            filename = secure_filename(f"PERM_{target_emp_id}_{file.filename}")
            upload_path = os.path.join('app', 'static', 'uploads', 'employee_permissions')
            if not os.path.exists(upload_path): os.makedirs(upload_path)
            file.save(os.path.join(upload_path, filename))

        try:
            data = request.form.to_dict()
            data['emp_id'] = target_emp_id
            data['filename'] = filename
            data['edu_id'] = request.form.get('edu_id')
            EmployeePermissionModel.save(data, user_id)
            flash('Record saved successfully.', 'success')
            return redirect(url_for('establishment.employee_permission_details', emp_id=target_emp_id))
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
            return redirect(url_for('establishment.employee_permission_details', emp_id=target_emp_id))

    employee_info = EmployeeModel.get_employee_full_details(emp_id) if emp_id else None
    permissions = EmployeePermissionModel.get_employee_permissions(emp_id) if emp_id else []
    edit_data = EmployeePermissionModel.get_by_id(edit_id) if edit_id else None
    return render_template('establishment/employee_permission_details.html', 
                         employee_info=employee_info, permissions=permissions, 
                         edit_data=edit_data, perm=perm, emp_id=emp_id)

@establishment_bp.route('/employee_family_details', methods=['GET', 'POST'])
@permission_required('Employee Family Details')
def employee_family_details():
    user_id = session.get('user_id'); perm = request.page_perms
    emp_id = request.args.get('emp_id')
    edit_id = request.args.get('edit_id')
    delete_id = request.args.get('delete_id')

    if delete_id and perm.get('AllowDelete'):
        try:
            EmployeeFamilyModel.delete(delete_id)
            flash('Family member deleted successfully.', 'success')
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('establishment.employee_family_details', emp_id=emp_id))

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'RESET':
            return redirect(url_for('establishment.employee_family_details'))
        
        target_emp_id = request.form.get('target_emp_id')
        if not target_emp_id:
            flash('Please select an employee first.', 'warning')
            return redirect(url_for('establishment.employee_family_details'))

        file = request.files.get('document_file')
        filename = None
        if file and file.filename:
            import os
            from werkzeug.utils import secure_filename
            filename = secure_filename(f"FAM_{target_emp_id}_{file.filename}")
            upload_path = os.path.join('app', 'static', 'uploads', 'employee_family')
            if not os.path.exists(upload_path): os.makedirs(upload_path)
            file.save(os.path.join(upload_path, filename))

        try:
            data = request.form.to_dict()
            data['emp_id'] = target_emp_id
            data['filename'] = filename
            data['family_id'] = request.form.get('family_id')
            EmployeeFamilyModel.save(data, user_id)
            flash('Family details saved successfully.', 'success')
            return redirect(url_for('establishment.employee_family_details', emp_id=target_emp_id))
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
            return redirect(url_for('establishment.employee_family_details', emp_id=target_emp_id))

    employee_info = EmployeeModel.get_employee_full_details(emp_id) if emp_id else None
    family = EmployeeFamilyModel.get_employee_family(emp_id) if emp_id else []
    edit_data = EmployeeFamilyModel.get_by_id(edit_id) if edit_id else None
    lookups = {
        'relations': DB.fetch_all("SELECT Pk_Relid as id, Relation_name as name FROM Relation_MST ORDER BY Relation_name")
    }
    return render_template('establishment/employee_family_details.html', 
                         employee_info=employee_info, family=family, 
                         edit_data=edit_data, lookups=lookups, perm=perm, emp_id=emp_id)

@establishment_bp.route('/employee_nominee_details', methods=['GET', 'POST'])
@permission_required('Employee Nominee Details')
def employee_nominee_details():
    user_id = session.get('user_id'); perm = request.page_perms
    emp_id = request.args.get('emp_id')
    edit_name = request.args.get('edit_name')
    delete_name = request.args.get('delete_name')

    if delete_name and perm.get('AllowDelete'):
        try:
            EmployeeNomineeModel.delete(emp_id, delete_name)
            flash('Nominee deleted successfully.', 'success')
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('establishment.employee_nominee_details', emp_id=emp_id))

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'RESET':
            return redirect(url_for('establishment.employee_nominee_details'))
        
        target_emp_id = request.form.get('target_emp_id')
        if not target_emp_id:
            flash('Please select an employee first.', 'warning')
            return redirect(url_for('establishment.employee_nominee_details'))

        file = request.files.get('document_file')
        filename = None
        if file and file.filename:
            import os
            from werkzeug.utils import secure_filename
            filename = secure_filename(f"NOM_{target_emp_id}_{file.filename}")
            upload_path = os.path.join('app', 'static', 'uploads', 'employee_nominees')
            if not os.path.exists(upload_path): os.makedirs(upload_path)
            file.save(os.path.join(upload_path, filename))

        try:
            data = request.form.to_dict()
            data['emp_id'] = target_emp_id
            data['filename'] = filename
            data['old_nominee_name'] = request.form.get('old_nominee_name')
            EmployeeNomineeModel.save(data, user_id)
            flash('Nominee details saved successfully.', 'success')
            return redirect(url_for('establishment.employee_nominee_details', emp_id=target_emp_id))
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
            return redirect(url_for('establishment.employee_nominee_details', emp_id=target_emp_id))

    employee_info = EmployeeModel.get_employee_full_details(emp_id) if emp_id else None
    if employee_info:
        # Additional logic for PF type and number display
        pf_type_map = {10: 'GPF', 125: 'CPF', 107: 'NPS'}
        employee_info['pftype_desc'] = pf_type_map.get(employee_info.get('fk_fundid'), 'N/A')
        employee_info['pfileno_display'] = employee_info.get('pfileno') or 'N/A'

    nominees = EmployeeNomineeModel.get_employee_nominees(emp_id) if emp_id else []
    edit_data = EmployeeNomineeModel.get_by_name(emp_id, edit_name) if (emp_id and edit_name) else None
    
    lookups = {
        'relations': DB.fetch_all("SELECT Pk_Relid as id, Relation_name as name FROM Relation_MST ORDER BY Relation_name"),
        'nominee_types': DB.fetch_all("SELECT pk_headid as id, description as name FROM SAL_Head_Mst WHERE pk_headid IN (10, 14, 15, 27, 92, 94, 107, 125, 137, 138) ORDER BY description")
    }
    return render_template('establishment/employee_nominee_details.html', 
                         employee_info=employee_info, nominees=nominees, 
                         edit_data=edit_data, lookups=lookups, perm=perm, emp_id=emp_id)

@establishment_bp.route('/employee_book_details', methods=['GET', 'POST'])
@permission_required('Employee Books Details')
def employee_book_details():
    user_id = session.get('user_id'); perm = request.page_perms
    emp_id = request.args.get('emp_id')
    edit_id = request.args.get('edit_id')
    delete_id = request.args.get('delete_id')

    if delete_id and perm.get('AllowDelete'):
        try:
            EmployeeBookModel.delete(delete_id)
            flash('Record deleted successfully.', 'success')
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('establishment.employee_book_details', emp_id=emp_id))

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'RESET':
            return redirect(url_for('establishment.employee_book_details'))
        
        target_emp_id = request.form.get('target_emp_id')
        if not target_emp_id:
            flash('Please select an employee first.', 'warning')
            return redirect(url_for('establishment.employee_book_details'))

        file = request.files.get('document_file')
        filename = None
        if file and file.filename:
            import os
            from werkzeug.utils import secure_filename
            filename = secure_filename(f"BOOK_{target_emp_id}_{file.filename}")
            upload_path = os.path.join('app', 'static', 'uploads', 'employee_books')
            if not os.path.exists(upload_path): os.makedirs(upload_path)
            file.save(os.path.join(upload_path, filename))

        try:
            data = request.form.to_dict()
            data['emp_id'] = target_emp_id
            data['filename'] = filename
            data['issue_id'] = request.form.get('issue_id')
            EmployeeBookModel.save(data, user_id)
            flash('Book details saved successfully.', 'success')
            return redirect(url_for('establishment.employee_book_details', emp_id=target_emp_id))
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
            return redirect(url_for('establishment.employee_book_details', emp_id=target_emp_id))

    employee_info = EmployeeModel.get_employee_full_details(emp_id) if emp_id else None
    books = EmployeeBookModel.get_employee_books(emp_id) if emp_id else []
    edit_data = EmployeeBookModel.get_by_id(edit_id) if edit_id else None
    return render_template('establishment/employee_book_details.html', 
                         employee_info=employee_info, books=books, 
                         edit_data=edit_data, perm=perm, emp_id=emp_id)

@establishment_bp.route('/employee_ltc_details', methods=['GET', 'POST'])
@permission_required('LTC Detail')
def employee_ltc_details():
    user_id = session.get('user_id'); perm = request.page_perms
    emp_id = request.args.get('emp_id')
    edit_id = request.args.get('edit_id')
    delete_id = request.args.get('delete_id')

    if delete_id and perm.get('AllowDelete'):
        try:
            LTCModel.delete(delete_id)
            flash('LTC record deleted successfully.', 'success')
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('establishment.employee_ltc_details', emp_id=emp_id))

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'RESET':
            return redirect(url_for('establishment.employee_ltc_details'))
        
        target_emp_id = request.form.get('emp_id')
        if not target_emp_id:
            flash('Please select an employee first.', 'warning')
            return redirect(url_for('establishment.employee_ltc_details'))

        try:
            data = request.form.to_dict()
            data['emp_id'] = target_emp_id
            data['ltc_id'] = request.form.get('ltc_id')
            LTCModel.save(data, user_id)
            flash('LTC details saved successfully.', 'success')
            return redirect(url_for('establishment.employee_ltc_details', emp_id=target_emp_id))
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
            return redirect(url_for('establishment.employee_ltc_details', emp_id=target_emp_id))

    employee_info = EmployeeModel.get_employee_full_details(emp_id) if emp_id else None
    ltc_records = LTCModel.get_employee_ltc(emp_id) if emp_id else []
    edit_data = LTCModel.get_by_id(edit_id) if edit_id else None
    return render_template('establishment/ltc_detail.html', 
                         emp=employee_info, ltc_records=ltc_records, 
                         edit_data=edit_data, perm=perm, emp_id=emp_id)

@establishment_bp.route('/employee_earned_leave_details', methods=['GET', 'POST'])
@permission_required('Earned Leave Details')
def employee_earned_leave_details():
    user_id = session.get('user_id'); perm = request.page_perms
    emp_id = request.args.get('emp_id')
    edit_id = request.args.get('edit_id')
    delete_id = request.args.get('delete_id')

    if delete_id and perm.get('AllowDelete'):
        try:
            EarnedLeaveModel.delete(delete_id)
            flash('Record deleted successfully.', 'success')
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('establishment.employee_earned_leave_details', emp_id=emp_id))

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'RESET':
            return redirect(url_for('establishment.employee_earned_leave_details'))
        
        target_emp_id = request.form.get('target_emp_id')
        if not target_emp_id:
            flash('Please select an employee first.', 'warning')
            return redirect(url_for('establishment.employee_earned_leave_details'))

        try:
            data = request.form.to_dict()
            data['emp_id'] = target_emp_id
            data['el_id'] = request.form.get('el_id')
            EarnedLeaveModel.save(data, user_id)
            flash('Earned leave details saved successfully.', 'success')
            return redirect(url_for('establishment.employee_earned_leave_details', emp_id=target_emp_id))
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
            return redirect(url_for('establishment.employee_earned_leave_details', emp_id=target_emp_id))

    employee_info = EmployeeModel.get_employee_full_details(emp_id) if emp_id else None
    el_records = EarnedLeaveModel.get_employee_el_details(emp_id) if emp_id else []
    edit_data = EarnedLeaveModel.get_by_id(edit_id) if edit_id else None
    
    return render_template('establishment/earned_leave_details.html', 
                         emp=employee_info, el_records=el_records, 
                         edit_data=edit_data, perm=perm, emp_id=emp_id)

@establishment_bp.route('/employee_previous_job_details', methods=['GET', 'POST'])
@permission_required('Employee Previous Job Details')
def employee_previous_job_details():
    user_id = session.get('user_id'); perm = request.page_perms
    emp_id = request.args.get('emp_id')
    edit_id = request.args.get('edit_id')
    delete_id = request.args.get('delete_id')

    if delete_id and perm.get('AllowDelete'):
        try:
            PreviousJobModel.delete(delete_id)
            flash('Record deleted successfully.', 'success')
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('establishment.employee_previous_job_details', emp_id=emp_id))

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'RESET':
            return redirect(url_for('establishment.employee_previous_job_details'))
        
        target_emp_id = request.form.get('target_emp_id')
        if not target_emp_id:
            flash('Please select an employee first.', 'warning')
            return redirect(url_for('establishment.employee_previous_job_details'))

        try:
            data = request.form.to_dict()
            data['emp_id'] = target_emp_id
            data['job_id'] = request.form.get('job_id')
            PreviousJobModel.save(data, user_id)
            flash('Previous job details saved successfully.', 'success')
            return redirect(url_for('establishment.employee_previous_job_details', emp_id=target_emp_id))
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
            return redirect(url_for('establishment.employee_previous_job_details', emp_id=target_emp_id))

    employee_info = EmployeeModel.get_employee_full_details(emp_id) if emp_id else None
    jobs = PreviousJobModel.get_employee_previous_jobs(emp_id) if emp_id else []
    edit_data = PreviousJobModel.get_by_id(edit_id) if edit_id else None
    return render_template('establishment/employee_previous_job_details.html', 
                         employee_info=employee_info, jobs=jobs, 
                         edit_data=edit_data, perm=perm, emp_id=emp_id)

@establishment_bp.route('/employee_foreign_visit_details', methods=['GET', 'POST'])
@permission_required('Employee Foreign Visit Details')
def employee_foreign_visit_details():
    user_id = session.get('user_id'); perm = request.page_perms
    emp_id = request.args.get('emp_id')
    edit_id = request.args.get('edit_id')
    delete_id = request.args.get('delete_id')

    if delete_id and perm.get('AllowDelete'):
        try:
            ForeignVisitModel.delete(delete_id)
            flash('Record deleted successfully.', 'success')
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('establishment.employee_foreign_visit_details', emp_id=emp_id))

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'RESET':
            return redirect(url_for('establishment.employee_foreign_visit_details'))
        
        target_emp_id = request.form.get('target_emp_id')
        if not target_emp_id:
            flash('Please select an employee first.', 'warning')
            return redirect(url_for('establishment.employee_foreign_visit_details'))

        try:
            data = request.form.to_dict()
            data['emp_id'] = target_emp_id
            data['visit_id'] = request.form.get('visit_id')
            ForeignVisitModel.save(data, user_id)
            flash('Visit details saved successfully.', 'success')
            return redirect(url_for('establishment.employee_foreign_visit_details', emp_id=target_emp_id))
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
            return redirect(url_for('establishment.employee_foreign_visit_details', emp_id=target_emp_id))

    employee_info = EmployeeModel.get_employee_full_details(emp_id) if emp_id else None
    visits = ForeignVisitModel.get_employee_foreign_visits(emp_id) if emp_id else []
    edit_data = ForeignVisitModel.get_by_id(edit_id) if edit_id else None
    lookups = {
        'sponsors': DB.fetch_all("SELECT Pk_FSponsor_Id as id, SponsorName as name FROM SAL_FundsSponsor_Mst ORDER BY SponsorName")
    }
    return render_template('establishment/employee_foreign_visit_details.html', 
                         employee_info=employee_info, visits=visits, 
                         edit_data=edit_data, lookups=lookups, perm=perm, emp_id=emp_id)

@establishment_bp.route('/employee_training_details', methods=['GET', 'POST'])
@permission_required('Employee Training Details')
def employee_training_details():
    user_id = session.get('user_id'); perm = request.page_perms
    emp_id = request.args.get('emp_id')
    edit_id = request.args.get('edit_id')
    delete_id = request.args.get('delete_id')

    if delete_id and perm.get('AllowDelete'):
        try:
            TrainingModel.delete(delete_id)
            flash('Record deleted successfully.', 'success')
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('establishment.employee_training_details', emp_id=emp_id))

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'RESET':
            return redirect(url_for('establishment.employee_training_details'))
        
        target_emp_id = request.form.get('target_emp_id')
        if not target_emp_id:
            flash('Please select an employee first.', 'warning')
            return redirect(url_for('establishment.employee_training_details'))

        try:
            data = request.form.to_dict()
            data['emp_id'] = target_emp_id
            data['training_id'] = request.form.get('training_id')
            TrainingModel.save(data, user_id)
            flash('Training details saved successfully.', 'success')
            return redirect(url_for('establishment.employee_training_details', emp_id=target_emp_id))
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
            return redirect(url_for('establishment.employee_training_details', emp_id=target_emp_id))

    employee_info = EmployeeModel.get_employee_full_details(emp_id) if emp_id else None
    trainings = TrainingModel.get_employee_trainings(emp_id) if emp_id else []
    edit_data = TrainingModel.get_by_id(edit_id) if edit_id else None
    lookups = {
        'sponsors': DB.fetch_all("SELECT Pk_FSponsor_Id as id, SponsorName as name FROM SAL_FundsSponsor_Mst ORDER BY SponsorName")
    }
    return render_template('establishment/employee_training_details.html', 
                         employee_info=employee_info, trainings=trainings, 
                         edit_data=edit_data, lookups=lookups, perm=perm, emp_id=emp_id)

@establishment_bp.route('/employee_departmental_exam_details', methods=['GET', 'POST'])
@permission_required('Employee Departmental Exam Details')
def employee_departmental_exam_details():
    user_id = session.get('user_id'); perm = request.page_perms
    emp_id = request.args.get('emp_id')
    edit_id = request.args.get('edit_id')
    delete_id = request.args.get('delete_id')

    if delete_id and perm.get('AllowDelete'):
        try:
            DeptExamModel.delete(delete_id)
            flash('Record deleted successfully.', 'success')
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('establishment.employee_departmental_exam_details', emp_id=emp_id))

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'RESET':
            return redirect(url_for('establishment.employee_departmental_exam_details'))
        
        target_emp_id = request.form.get('target_emp_id')
        if not target_emp_id:
            flash('Please select an employee first.', 'warning')
            return redirect(url_for('establishment.employee_departmental_exam_details'))

        try:
            data = request.form.to_dict()
            data['emp_id'] = target_emp_id
            data['exam_id'] = request.form.get('exam_id')
            DeptExamModel.save(data, user_id)
            flash('Exam details saved successfully.', 'success')
            return redirect(url_for('establishment.employee_departmental_exam_details', emp_id=target_emp_id))
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
            return redirect(url_for('establishment.employee_departmental_exam_details', emp_id=target_emp_id))

    employee_info = EmployeeModel.get_employee_full_details(emp_id) if emp_id else None
    exams = DeptExamModel.get_employee_exams(emp_id) if emp_id else []
    edit_data = DeptExamModel.get_by_id(edit_id) if edit_id else None
    lookups = {
        'exam_types': DB.fetch_all("SELECT Pk_EType_Id as id, ExamType as name FROM SAL_ExamType_Mst ORDER BY ExamType")
    }
    return render_template('establishment/employee_departmental_exam_details.html', 
                         employee_info=employee_info, exams=exams, 
                         edit_data=edit_data, lookups=lookups, perm=perm, emp_id=emp_id)

@establishment_bp.route('/employee_service_verification_details', methods=['GET', 'POST'])
@permission_required('Employee Service Verification Details')
def employee_service_verification_details():
    user_id = session.get('user_id'); perm = request.page_perms
    emp_id = request.args.get('emp_id')
    edit_id = request.args.get('edit_id')
    delete_id = request.args.get('delete_id')

    if delete_id and perm.get('AllowDelete'):
        try:
            ServiceVerificationModel.delete(delete_id)
            flash('Record deleted successfully.', 'success')
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('establishment.employee_service_verification_details', emp_id=emp_id))

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'RESET':
            return redirect(url_for('establishment.employee_service_verification_details'))
        
        target_emp_id = request.form.get('target_emp_id')
        if not target_emp_id:
            flash('Please select an employee first.', 'warning')
            return redirect(url_for('establishment.employee_service_verification_details'))

        try:
            data = request.form.to_dict()
            data['emp_id'] = target_emp_id
            data['ver_id'] = request.form.get('ver_id')
            ServiceVerificationModel.save(data, user_id)
            flash('Service verification details saved successfully.', 'success')
            return redirect(url_for('establishment.employee_service_verification_details', emp_id=target_emp_id))
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
            return redirect(url_for('establishment.employee_service_verification_details', emp_id=target_emp_id))

    employee_info = EmployeeModel.get_employee_full_details(emp_id) if emp_id else None
    verifications = ServiceVerificationModel.get_employee_service_verifications(emp_id) if emp_id else []
    edit_data = ServiceVerificationModel.get_by_id(edit_id) if edit_id else None
    lookups = {
        'natures': DB.fetch_all("SELECT pk_natureid as id, nature as name FROM SAL_Nature_Mst ORDER BY nature")
    }
    return render_template('establishment/employee_service_verification_details.html', 
                         employee_info=employee_info, verifications=verifications, 
                         edit_data=edit_data, lookups=lookups, perm=perm, emp_id=emp_id)

@establishment_bp.route('/employee_disciplinary_details', methods=['GET', 'POST'])
@permission_required('Disciplinary Action/Reward Details')
def employee_disciplinary_details():
    user_id = session.get('user_id'); perm = request.page_perms
    emp_id = request.args.get('emp_id')
    edit_id = request.args.get('edit_id')
    delete_id = request.args.get('delete_id')

    if delete_id and perm.get('AllowDelete'):
        try:
            DisciplinaryModel.delete(delete_id)
            flash('Record deleted successfully.', 'success')
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('establishment.employee_disciplinary_details', emp_id=emp_id))

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'RESET':
            return redirect(url_for('establishment.employee_disciplinary_details'))
        
        target_emp_id = request.form.get('target_emp_id')
        if not target_emp_id:
            flash('Please select an employee first.', 'warning')
            return redirect(url_for('establishment.employee_disciplinary_details'))

        file = request.files.get('document_file')
        filename = None
        if file and file.filename:
            import os
            from werkzeug.utils import secure_filename
            filename = secure_filename(f"DISC_{target_emp_id}_{file.filename}")
            upload_path = os.path.join('app', 'static', 'uploads', 'employee_disciplinary')
            if not os.path.exists(upload_path): os.makedirs(upload_path)
            file.save(os.path.join(upload_path, filename))

        try:
            data = request.form.to_dict()
            data['emp_id'] = target_emp_id
            data['filename'] = filename
            data['disc_id'] = request.form.get('disc_id')
            DisciplinaryModel.save(data, user_id)
            flash('Disciplinary record saved successfully.', 'success')
            return redirect(url_for('establishment.employee_disciplinary_details', emp_id=target_emp_id))
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
            return redirect(url_for('establishment.employee_disciplinary_details', emp_id=target_emp_id))

    employee_info = EmployeeModel.get_employee_full_details(emp_id) if emp_id else None
    records = DisciplinaryModel.get_employee_records(emp_id) if emp_id else []
    edit_data = DisciplinaryModel.get_by_id(edit_id) if edit_id else None
    return render_template('establishment/disciplinary_action_details.html', 
                         emp=employee_info, records=records, 
                         edit_data=edit_data, perm=perm, emp_id=emp_id)

@establishment_bp.route('/employee_loan_details', methods=['GET', 'POST'])
@permission_required('Employee Loan Details')
def employee_loan_details():
    user_id = session.get('user_id'); perm = request.page_perms
    emp_id = request.args.get('emp_id')
    edit_id = request.args.get('edit_id')
    delete_id = request.args.get('delete_id')

    if delete_id and perm.get('AllowDelete'):
        try:
            EmployeeLoanModel.delete(delete_id)
            flash('Record deleted successfully.', 'success')
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('establishment.employee_loan_details', emp_id=emp_id))

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'RESET':
            return redirect(url_for('establishment.employee_loan_details'))
        
        target_emp_id = request.form.get('target_emp_id')
        if not target_emp_id:
            flash('Please select an employee first.', 'warning')
            return redirect(url_for('establishment.employee_loan_details'))

        try:
            data = request.form.to_dict()
            data['emp_id'] = target_emp_id
            data['loan_id'] = request.form.get('loan_id')
            EmployeeLoanModel.save(data, user_id)
            flash('Loan details saved successfully.', 'success')
            return redirect(url_for('establishment.employee_loan_details', emp_id=target_emp_id))
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
            return redirect(url_for('establishment.employee_loan_details', emp_id=target_emp_id))

    employee_info = EmployeeModel.get_employee_full_details(emp_id) if emp_id else None
    loans = EmployeeLoanModel.get_employee_loans(emp_id) if emp_id else []
    edit_data = EmployeeLoanModel.get_by_id(edit_id) if edit_id else None
    return render_template('establishment/employee_loan_details.html', 
                         employee_info=employee_info, loans=loans, 
                         edit_data=edit_data, perm=perm, emp_id=emp_id)

@establishment_bp.route('/employee_book_grant_details', methods=['GET', 'POST'])
@permission_required('Employee Book Grant Amount Details')
def employee_book_grant_details():
    user_id = session.get('user_id'); perm = request.page_perms
    emp_id = request.args.get('emp_id')
    edit_id = request.args.get('edit_id')
    delete_id = request.args.get('delete_id')

    if delete_id and perm.get('AllowDelete'):
        try:
            BookGrantModel.delete(delete_id)
            flash('Record deleted successfully.', 'success')
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('establishment.employee_book_grant_details', emp_id=emp_id))

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'RESET':
            return redirect(url_for('establishment.employee_book_grant_details'))
        
        target_emp_id = request.form.get('target_emp_id')
        if not target_emp_id:
            flash('Please select an employee first.', 'warning')
            return redirect(url_for('establishment.employee_book_grant_details'))

        try:
            data = request.form.to_dict()
            data['emp_id'] = target_emp_id
            data['grant_id'] = request.form.get('grant_id')
            BookGrantModel.save(data, user_id)
            flash('Grant details saved successfully.', 'success')
            return redirect(url_for('establishment.employee_book_grant_details', emp_id=target_emp_id))
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
            return redirect(url_for('establishment.employee_book_grant_details', emp_id=target_emp_id))

    employee_info = EmployeeModel.get_employee_full_details(emp_id) if emp_id else None
    grants = BookGrantModel.get_employee_grants(emp_id) if emp_id else []
    edit_data = BookGrantModel.get_by_id(edit_id) if edit_id else None
    return render_template('establishment/employee_book_grant_details.html', 
                         employee_info=employee_info, grants=grants, 
                         edit_data=edit_data, perm=perm, emp_id=emp_id)

@establishment_bp.route('/employee_bonus_details', methods=['GET', 'POST'])
@permission_required('Employee Bonus Amount Details')
def employee_bonus_details():
    user_id = session.get('user_id'); perm = request.page_perms
    emp_id = request.args.get('emp_id')
    edit_id = request.args.get('edit_id')
    delete_id = request.args.get('delete_id')

    if delete_id and perm.get('AllowDelete'):
        try:
            BonusModel.delete(delete_id)
            flash('Record deleted successfully.', 'success')
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('establishment.employee_bonus_details', emp_id=emp_id))

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'RESET':
            return redirect(url_for('establishment.employee_bonus_details'))
        
        target_emp_id = request.form.get('target_emp_id')
        if not target_emp_id:
            flash('Please select an employee first.', 'warning')
            return redirect(url_for('establishment.employee_bonus_details'))

        try:
            data = request.form.to_dict()
            data['emp_id'] = target_emp_id
            data['bonus_id'] = request.form.get('bonus_id')
            BonusModel.save(data, user_id)
            flash('Bonus details saved successfully.', 'success')
            return redirect(url_for('establishment.employee_bonus_details', emp_id=target_emp_id))
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
            return redirect(url_for('establishment.employee_bonus_details', emp_id=target_emp_id))

    employee_info = EmployeeModel.get_employee_full_details(emp_id) if emp_id else None
    bonuses = BonusModel.get_employee_bonuses(emp_id) if emp_id else []
    edit_data = BonusModel.get_by_id(edit_id) if edit_id else None
    return render_template('establishment/employee_bonus_details.html', 
                         emp=employee_info, bonuses=bonuses, 
                         edit_data=edit_data, perm=perm, emp_id=emp_id)

@establishment_bp.route('/api/sar/details/<int:sar_id>')
def api_sar_details(sar_id):
    details = SARModel.get_sar_details(sar_id)
    if not details: return "<div style='color:red; text-align:center; padding:20px;'>There is no row at position 0.</div>", 404
    return render_template('establishment/sar_details_popup.html', main=details['main'], publications=details['publications'], activities=details['activities'])

@establishment_bp.route('/sar_admin_transaction', methods=['GET', 'POST'])
@permission_required('SAR/ACR Admin Transaction')
def sar_admin_transaction():
    perm = request.page_perms
    category = request.args.get('category', 'T')
    session_id = request.args.get('session_id')
    dept_id = request.args.get('dept_id')
    
    sar_data = SARModel.get_sar_lists(category)
    
    # Filter by session and department if provided
    # (Note: model currently doesn't filter by these, but we could add if needed)
    
    lookups = {
        'sessions': DB.fetch_all("SELECT pk_sessionid, sessionname FROM SMS_Session_Mst ORDER BY sessionname DESC"),
        'departments': DB.fetch_all("SELECT pk_deptid, description as dept_name FROM Department_Mst ORDER BY description"),
        'categories': [
            {'id': 'T', 'name': 'Teaching'},
            {'id': 'N', 'name': 'Non Teaching'},
            {'id': 'F', 'name': 'Fourth Class'}
        ]
    }
    
    return render_template('establishment/sar_admin_transaction.html', 
                         sar_data=sar_data, category=category, 
                         lookups=lookups, perm=perm)

@establishment_bp.route('/employee_first_appointment_details', methods=['GET', 'POST'])
@permission_required('Employee First Appointment Details')
def employee_first_appointment_details():
    user_id = session.get('user_id'); perm = request.page_perms
    emp_id = request.args.get('emp_id'); edit_id = request.args.get('edit')
    ddos = EstablishmentModel.get_ddos()
    if request.method == 'POST':
        action = request.form.get('action', 'SAVE'); target_emp_id = request.form.get('emp_id')
        if action == 'DELETE':
            FirstAppointmentModel.delete(request.form.get('edit_id')); flash("Record Deleted Successfully !", "success")
            return redirect(url_for('establishment.employee_first_appointment_details', emp_id=target_emp_id))
        form_data = { 'emp_id': target_emp_id, 'title': request.form.get('title', '').strip(), 'remarks': request.form.get('remarks', '').strip(), 'joining_date': request.form.get('joining_date'), 'order_no': request.form.get('order_no', '').strip(), 'appointment_date': request.form.get('appointment_date'), 'ddo': request.form.get('appointment_ddo', '').strip(), 'designation': request.form.get('appointment_designation', '').strip(), 'department': request.form.get('appointment_department', '').strip(), 'basic': request.form.get('basic') or 0, 'pay_scale': request.form.get('pay_scale', '').strip(), 'probation_date': request.form.get('probation_date'), 'due_date_pp': request.form.get('due_date_pp'), 'joining_time': request.form.get('joining_time'), 'sr_no': request.form.get('sr_no', '').strip() }
        from datetime import datetime
        for key in ['joining_date', 'appointment_date', 'probation_date', 'due_date_pp']:
            if form_data[key]:
                try: form_data[key] = datetime.strptime(form_data[key], '%d/%m/%Y').strftime('%Y-%m-%d')
                except: form_data[key] = None
        try:
            current_app_id = None; existing = DB.fetch_one("SELECT pk_appointmentid FROM SAL_FirstAppointment_Details WHERE fk_empid = ?", [target_emp_id])
            if existing: current_app_id = FirstAppointmentModel.update(existing['pk_appointmentid'], form_data, user_id); flash('Record Updated Successfully !', 'success')
            else: current_app_id = FirstAppointmentModel.save(form_data, user_id); flash('Record Saved Successfully !', 'success')
            terms = request.form.getlist('prob_term[]'); fulfills = request.form.getlist('prob_fulfill[]')
            FirstAppointmentModel.save_probation_terms(current_app_id, terms, fulfills)
            return redirect(url_for('establishment.employee_first_appointment_details', emp_id=target_emp_id))
        except Exception as e: flash(f'Error: {str(e)}', 'danger')
    employee_info = None; appointments = []; edit_data = None; terms = []
    if emp_id:
        employee_info = DB.fetch_one("SELECT E.*, D.description as dept_name, DS.designation, DD.Description as ddo_name FROM SAL_Employee_Mst E LEFT JOIN Department_Mst D ON E.fk_deptid = D.pk_deptid LEFT JOIN SAL_Designation_Mst DS ON E.fk_desgid = DS.pk_desgid LEFT JOIN DDO_Mst DD ON E.fk_ddoid = DD.pk_ddoid WHERE E.pk_empid = ?", [emp_id])
        edit_data = FirstAppointmentModel.get_appointment_by_id(edit_id) if edit_id else None
        if not edit_data:
            existing = DB.fetch_one("SELECT pk_appointmentid FROM SAL_FirstAppointment_Details WHERE fk_empid = ?", [emp_id])
            if existing: edit_data = FirstAppointmentModel.get_appointment_by_id(existing['pk_appointmentid'])
        if not edit_data:
            hist = DB.fetch_one("SELECT TOP 1 OrdeNo as OrderNo, CONVERT(varchar, DateofJoinning, 103) as joining_date_fmt, CONVERT(varchar, DateofAppointment, 103) as appointment_date_fmt, NewBasic as BasicPay, NewPayScale as PayScale, NewDDO as DDO, NewDesignation as Designation, NewDepartment as Department, JoiningTime, SrNo, CONVERT(varchar, DueDatePP, 103) as due_date_pp_fmt FROM sal_emp_promotion_increment_payrevision_detail WHERE fk_empid = ? ORDER BY DateofJoinning ASC", [emp_id])
            if hist: edit_data = hist
            else:
                other = DB.fetch_one("SELECT OrderNo, CONVERT(varchar, dateofjoining, 103) as joining_date_fmt, CONVERT(varchar, dateofappointment, 103) as appointment_date_fmt, AppointmentTime FROM SAL_EmployeeOther_Details WHERE fk_empid = ?", [emp_id])
                if other or employee_info: edit_data = { 'joining_date_fmt': other['joining_date_fmt'] if other else None, 'OrderNo': other['OrderNo'] if other else None, 'appointment_date_fmt': other['appointment_date_fmt'] if other else None, 'DDO': employee_info['ddo_name'] if employee_info else None, 'Designation': employee_info['designation'] if employee_info else None, 'Department': employee_info['dept_name'] if employee_info else None, 'BasicPay': employee_info['curbasic'] if employee_info else None, 'JoiningTime': 'Fore Noon' if other and other['AppointmentTime'] == 'F' else 'After Noon' }
        if edit_data and edit_data.get('pk_appointmentid'): terms = FirstAppointmentModel.get_probation_terms(edit_data['pk_appointmentid'])
        appointments = FirstAppointmentModel.get_employee_appointments(emp_id)
    return render_template('establishment/employee_first_appointment_details.html', emp=employee_info, appointments=appointments, record=edit_data, terms=terms, ddos=ddos, perm=perm)

@establishment_bp.route('/employee_increment_payrevision', methods=['GET', 'POST'])
@permission_required('Emp Increment Payrevision')
def employee_increment_payrevision():
    user_id = session.get('user_id'); perm = request.page_perms
    emp_id = request.args.get('emp_id')
    edit_id = request.args.get('edit_id')
    delete_id = request.args.get('delete_id')

    if delete_id and perm.get('AllowDelete'):
        try:
            IncrementModel.delete(delete_id)
            flash('Record deleted successfully.', 'success')
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('establishment.employee_increment_payrevision', emp_id=emp_id))

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'RESET':
            return redirect(url_for('establishment.employee_increment_payrevision'))
        
        target_emp_id = request.form.get('target_emp_id')
        if not target_emp_id:
            flash('Please select an employee first.', 'warning')
            return redirect(url_for('establishment.employee_increment_payrevision'))

        try:
            data = request.form.to_dict()
            data['emp_id'] = target_emp_id
            data['pid'] = request.form.get('pid')
            data['promo_type'] = request.form.get('promo_type', 'I') # Default to Increment
            IncrementModel.save(data, user_id)
            flash('Increment details saved successfully.', 'success')
            return redirect(url_for('establishment.employee_increment_payrevision', emp_id=target_emp_id))
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
            return redirect(url_for('establishment.employee_increment_payrevision', emp_id=target_emp_id))

    employee_info = EmployeeModel.get_employee_full_details(emp_id) if emp_id else None
    increments = IncrementModel.get_employee_increments(emp_id, 'I') if emp_id else []
    edit_data = IncrementModel.get_by_id(edit_id) if edit_id else None
    
    return render_template('establishment/employee_increment_payrevision.html', 
                         employee_info=employee_info, increments=increments, 
                         edit_data=edit_data, perm=perm, emp_id=emp_id)

@establishment_bp.route('/employee_promotion_details', methods=['GET', 'POST'])
@permission_required('Employee Promotion/Financial Up-gradation')
def employee_promotion_details():
    user_id = session.get('user_id'); perm = request.page_perms
    emp_id = request.args.get('emp_id')
    edit_id = request.args.get('edit_id')
    delete_id = request.args.get('delete_id')

    if delete_id and perm.get('AllowDelete'):
        try:
            IncrementModel.delete(delete_id)
            flash('Record deleted successfully.', 'success')
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('establishment.employee_promotion_details', emp_id=emp_id))

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'RESET':
            return redirect(url_for('establishment.employee_promotion_details'))
        
        target_emp_id = request.form.get('target_emp_id')
        if not target_emp_id:
            flash('Please select an employee first.', 'warning')
            return redirect(url_for('establishment.employee_promotion_details'))

        try:
            data = request.form.to_dict()
            data['emp_id'] = target_emp_id
            data['pid'] = request.form.get('pid')
            data['promo_type'] = request.form.get('status', 'P') # Use selected status as promo_type
            IncrementModel.save(data, user_id)
            flash('Promotion details saved successfully.', 'success')
            return redirect(url_for('establishment.employee_promotion_details', emp_id=target_emp_id))
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
            return redirect(url_for('establishment.employee_promotion_details', emp_id=target_emp_id))

    employee_info = EmployeeModel.get_employee_full_details(emp_id) if emp_id else None
    # For list, we might want to show all including 'P', 'H', 'RD' etc.
    # But usually 'P' status is used for the main list here.
    promotions = IncrementModel.get_employee_increments(emp_id, promo_type='P') if emp_id else []
    edit_data = IncrementModel.get_by_id(edit_id) if edit_id else None
    
    return render_template('establishment/employee_promotion_details.html', 
                         employee_info=employee_info, promotions=promotions, 
                         edit_data=edit_data, perm=perm, emp_id=emp_id)

@establishment_bp.route('/employee_no_dues_details', methods=['GET', 'POST'])
@permission_required('Employee No-Dues Detail')
def employee_no_dues_details():
    user_id = session.get('user_id'); perm = request.page_perms
    emp_id = request.args.get('emp_id')
    edit_id = request.args.get('edit_id')
    delete_id = request.args.get('delete_id')

    if delete_id and perm.get('AllowDelete'):
        try:
            NoDuesModel.delete(delete_id)
            flash('Record deleted successfully.', 'success')
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('establishment.employee_no_dues_details', emp_id=emp_id))

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'RESET':
            return redirect(url_for('establishment.employee_no_dues_details'))
        
        target_emp_id = request.form.get('target_emp_id')
        if not target_emp_id:
            flash('Please select an employee first.', 'warning')
            return redirect(url_for('establishment.employee_no_dues_details'))

        try:
            data = request.form.to_dict()
            data['emp_id'] = target_emp_id
            data['due_id'] = request.form.get('due_id')
            NoDuesModel.save(data, user_id)
            flash('No-dues details saved successfully.', 'success')
            return redirect(url_for('establishment.employee_no_dues_details', emp_id=target_emp_id))
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
            return redirect(url_for('establishment.employee_no_dues_details', emp_id=target_emp_id))

    employee_info = EmployeeModel.get_employee_full_details(emp_id) if emp_id else None
    dues = NoDuesModel.get_employee_dues(emp_id) if emp_id else []
    edit_data = NoDuesModel.get_by_id(edit_id) if edit_id else None
    
    # Retiring employees logic
    retiring_employees = DB.fetch_all("""
        SELECT E.pk_empid, E.empcode, E.empname, DS.designation, D.description as dept_name, 
               CONVERT(varchar, O.dateofretirement, 103) as dor_fmt 
        FROM SAL_Employee_Mst E 
        INNER JOIN SAL_EmployeeOther_Details O ON E.pk_empid = O.fk_empid 
        LEFT JOIN SAL_Designation_Mst DS ON E.fk_desgid = DS.pk_desgid 
        LEFT JOIN Department_Mst D ON E.fk_deptid = D.pk_deptid 
        WHERE O.dateofretirement BETWEEN GETDATE() AND DATEADD(month, 6, GETDATE()) 
        ORDER BY O.dateofretirement
    """)

    lookups = {
        'departments': DB.fetch_all("SELECT pk_deptid as id, description as name FROM Department_Mst ORDER BY description")
    }
    return render_template('establishment/employee_no_dues_details.html', 
                         employee_info=employee_info, dues=dues, 
                         retiring_employees=retiring_employees,
                         edit_data=edit_data, lookups=lookups, perm=perm, emp_id=emp_id)


# --- RESTORED MASTERS ---
def list_masters():
    user_id = session['user_id']
    loc_id = session.get('selected_loc')
    
    # Map of key -> Page Caption
    masters_list = [
        ('Department', 'department'), ('Designation', 'designation'), 
        ('District', 'district'), ('Location', 'location'),
        ('DDO', 'ddo'), ('Section', 'section'), ('Grade', 'grade'),
        ('Class', 'class'), ('Religion', 'religion'),
        ('Controlling Office', 'controlling_office'),
        ('Office Type', 'office_type')
    ]
    
    allowed = {}
    for caption, key in masters_list:
        p = NavModel.check_permission(user_id, loc_id, f"{caption} Master")
        if p and p.get('AllowView'):
            allowed[key] = EstablishmentModel.MASTER_TABLES.get(key)
            
    return render_template('establishment/list.html', masters=allowed)

@establishment_bp.route('/manage/<key>', methods=['GET', 'POST'])
def manage_master(key):
    # Mapping logic
    page_map = {
        'department': 'Department Master', 'designation': 'Designation Master',
        'district': 'District Master', 'location': 'Location Master',
        'ddo': 'DDO Master', 'section': 'Section Master', 'grade': 'Grade Master',
        'class': 'Class Master', 'religion': 'Religion Master',
        'controlling_office': 'Controlling Office Master',
        'office_type': 'Office Type Master',
        'city_category': 'City-Category Master', 'city': 'City Master',
        'salutation': 'Salutation Master', 'relation': 'Relation Master',
        'category': 'Category Master', 'gad_nongad': 'Gad-Nongad Master',
        'discipline': 'Discipline Master'
    }
    
    page_name = page_map.get(key)
    if not page_name: return redirect(url_for('main.index'))

    user_id = session['user_id']
    loc_id = session.get('selected_loc')
    perms = NavModel.check_permission(user_id, loc_id, page_name)
    
    if not perms or not perms.get('AllowView'):
        flash(f"Access denied to {page_name}.", "danger")
        return redirect(url_for('main.index'))

    cfg = EstablishmentModel.MASTER_TABLES.get(key)
    
    if request.method == 'POST':
        if not perms.get('AllowAdd') and not perms.get('AllowUpdate'):
            flash("Permission denied.", "danger")
        else:
            if EstablishmentModel.save_record(key, request.form):
                flash(f"Record saved successfully.", "success")
            else:
                flash("Save failed.", "danger")
        return redirect(url_for(f'establishment.{key}_master'))

    # Pagination Logic
    page = int(request.args.get('page', 1))
    pagination, sql_limit = get_pagination(cfg['table'], page)
    
    data = DB.fetch_all(f"SELECT * FROM {cfg['table']} ORDER BY {cfg['name']} {sql_limit}")
    
    record = None
    edit_id = request.args.get('id')
    if edit_id:
        record = EstablishmentModel.get_record(key, edit_id)

    return render_template('establishment/manage.html', 
                           key=key, cfg=cfg, data=data, record=record, 
                           perms=perms, pagination=pagination)

@establishment_bp.route('/delete/<key>/<id>', methods=['POST'])
def delete_generic_master(key, id):
    page_map = {
        'department': 'Department Master', 'designation': 'Designation Master',
        'district': 'District Master', 'location': 'Location Master',
        'ddo': 'DDO Master', 'section': 'Section Master', 'grade': 'Grade Master',
        'class': 'Class Master', 'religion': 'Religion Master',
        'controlling_office': 'Controlling Office Master',
        'office_type': 'Office Type Master',
        'city_category': 'City-Category Master', 'city': 'City Master',
        'salutation': 'Salutation Master', 'relation': 'Relation Master',
        'category': 'Category Master', 'gad_nongad': 'Gad-Nongad Master',
        'discipline': 'Discipline Master'
    }
    perms = NavModel.check_permission(session['user_id'], session.get('selected_loc'), page_map.get(key))
    
    if perms and perms.get('AllowDelete'):
        EstablishmentModel.delete_record(key, id)
        flash("Record deleted.", "success")
    else:
        flash("Delete permission denied.", "danger")
    return redirect(url_for(f'establishment.{key}_master'))

@establishment_bp.route('/city_category_master', methods=['GET', 'POST'])
@permission_required('City-Category Master')
def city_category_master(): return manage_master('city_category')

@establishment_bp.route('/city_master', methods=['GET', 'POST'])
@permission_required('City Master')
def city_master():
    user_id = session['user_id']; loc_id = session.get('selected_loc'); perm = NavModel.check_permission(user_id, loc_id, 'City Master')
    
    if request.method == 'POST':
        action = (request.form.get('action') or '').strip().upper()
        if action == 'RESET':
            return redirect(url_for('establishment.city_master'))
            
        if action == 'DELETE':
            if not perm.get('AllowDelete'):
                flash("You do not have permission to delete.", "danger")
                return redirect(url_for('establishment.city_master'))
            delete_id = request.form.get('delete_id')
            try:
                DB.execute("DELETE FROM SAL_City_Mst WHERE pk_cityid = ?", [delete_id])
                flash("City deleted successfully.", "success")
            except Exception as e: flash(f"Error: {str(e)}", "danger")
            return redirect(url_for('establishment.city_master'))
            
        if action == 'SAVE' or action == 'UPDATE':
            edit_id = request.form.get('edit_id')
            fk_ccid = request.form.get('fk_ccid')
            cityname = request.form.get('cityname')
            address1 = request.form.get('address1')
            address2 = request.form.get('address2')
            metro = 1 if request.form.get('metro') else 0
            other = 1 if request.form.get('other') else 0
            
            if edit_id and not perm.get('AllowUpdate'):
                flash("You do not have permission to update.", "danger")
                return redirect(url_for('establishment.city_master'))
            if not edit_id and not perm.get('AllowAdd'):
                flash("You do not have permission to add.", "danger")
                return redirect(url_for('establishment.city_master'))
                
            try:
                if edit_id:
                    DB.execute("""
                        UPDATE SAL_City_Mst 
                        SET fk_ccid = ?, cityname = ?, address1 = ?, address2 = ?, metro = ?, other = ?,
                            fk_updUserID = ?, fk_updDateID = 'ab-428'
                        WHERE pk_cityid = ?
                    """, [fk_ccid, cityname, address1, address2, metro, other, user_id, edit_id])
                    flash("Record Updated Successfully !", "success")
                else:
                    new_id = f"CTY-{to_int(DB.fetch_scalar('SELECT COUNT(*) FROM SAL_City_Mst')) + 1}"
                    DB.execute("""
                        INSERT INTO SAL_City_Mst (pk_cityid, fk_ccid, cityname, address1, address2, metro, other, fk_insUserID, fk_insDateID) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'ab-428')
                    """, [new_id, fk_ccid, cityname, address1, address2, metro, other, user_id])
                    flash("Record Saved Successfully !", "success")
            except Exception as e: flash(f"Error: {str(e)}", "danger")
            return redirect(url_for('establishment.city_master'))
            
    page = to_int(request.args.get('page', 1)); pagination, sql_limit = get_pagination("SAL_City_Mst", page)
    
    cities = DB.fetch_all(f"""
        SELECT C.pk_cityid as id, CC.citycategory as category_name, C.cityname, C.metro, C.other 
        FROM SAL_City_Mst C
        LEFT JOIN SAL_CityCategory_Mst CC ON C.fk_ccid = CC.pk_ccid
        ORDER BY C.cityname {sql_limit}
    """)
    
    categories = DB.fetch_all("SELECT pk_ccid as id, citycategory as name FROM SAL_CityCategory_Mst ORDER BY citycategory")
    
    edit_data = None; edit_id = request.args.get('edit_id')
    if edit_id:
        edit_data = DB.fetch_one("SELECT pk_cityid as id, fk_ccid, cityname, address1, address2, metro, other FROM SAL_City_Mst WHERE pk_cityid = ?", [edit_id])
        
    return render_template('establishment/city_master.html', 
                           cities=cities, categories=categories, 
                           edit_data=edit_data, perm=perm, pagination=pagination)

@establishment_bp.route('/salutation_master', methods=['GET', 'POST'])
@permission_required('Salutation Master')
def salutation_master(): return manage_master('salutation')

@establishment_bp.route('/relation_master', methods=['GET', 'POST'])
@permission_required('Relation Master')
def relation_master():
    user_id = session['user_id']; loc_id = session.get('selected_loc'); perm = NavModel.check_permission(user_id, loc_id, 'Relation Master')
    
    if request.method == 'POST':
        action = (request.form.get('action') or '').strip().upper()
        if action == 'RESET':
            return redirect(url_for('establishment.relation_master'))
            
        if action == 'DELETE':
            if not perm.get('AllowDelete'):
                flash("You do not have permission to delete.", "danger")
                return redirect(url_for('establishment.relation_master'))
            delete_id = request.form.get('delete_id')
            try:
                DB.execute("DELETE FROM Relation_MST WHERE Pk_Relid = ?", [delete_id])
                flash("Relation deleted successfully.", "success")
            except Exception as e: flash(f"Error: {str(e)}", "danger")
            return redirect(url_for('establishment.relation_master'))
            
        if action == 'SAVE' or action == 'UPDATE':
            edit_id = request.form.get('edit_id')
            relation_name = request.form.get('relation_name')
            remarks = request.form.get('remarks')
            
            if edit_id and not perm.get('AllowUpdate'):
                flash("You do not have permission to update.", "danger")
                return redirect(url_for('establishment.relation_master'))
            if not edit_id and not perm.get('AllowAdd'):
                flash("You do not have permission to add.", "danger")
                return redirect(url_for('establishment.relation_master'))
                
            try:
                if edit_id:
                    DB.execute("""
                        UPDATE Relation_MST SET Relation_name = ?, Remarks = ? WHERE Pk_Relid = ?
                    """, [relation_name, remarks, edit_id])
                    flash("Record Updated Successfully !", "success")
                else:
                    new_id = to_int(DB.fetch_scalar('SELECT MAX(Pk_Relid) FROM Relation_MST') or 0) + 1
                    DB.execute("""
                        INSERT INTO Relation_MST (Pk_Relid, Relation_name, Remarks) VALUES (?, ?, ?)
                    """, [new_id, relation_name, remarks])
                    flash("Record Saved Successfully !", "success")
            except Exception as e: flash(f"Error: {str(e)}", "danger")
            return redirect(url_for('establishment.relation_master'))
            
    page = to_int(request.args.get('page', 1)); pagination, sql_limit = get_pagination("Relation_MST", page)
    relations = DB.fetch_all(f"SELECT Pk_Relid as id, Relation_name as name, Remarks FROM Relation_MST ORDER BY Relation_name {sql_limit}")
    
    edit_data = None; edit_id = request.args.get('edit_id')
    if edit_id:
        edit_data = DB.fetch_one("SELECT Pk_Relid as id, Relation_name as name, Remarks FROM Relation_MST WHERE Pk_Relid = ?", [edit_id])
        
    return render_template('establishment/relation_master.html', 
                           relations=relations, edit_data=edit_data, 
                           perm=perm, pagination=pagination)

@establishment_bp.route('/category_master', methods=['GET', 'POST'])
@permission_required('Category Master')
def category_master():
    user_id = session['user_id']; loc_id = session.get('selected_loc'); perm = NavModel.check_permission(user_id, loc_id, 'Category Master')
    
    if request.method == 'POST':
        action = (request.form.get('action') or '').strip().upper()
        if action == 'RESET':
            return redirect(url_for('establishment.category_master'))
            
        if action == 'DELETE':
            if not perm.get('AllowDelete'):
                flash("You do not have permission to delete.", "danger")
                return redirect(url_for('establishment.category_master'))
            delete_id = request.form.get('delete_id')
            try:
                DB.execute("DELETE FROM SAL_Category_Mst WHERE pk_catid = ?", [delete_id])
                flash("Category deleted successfully.", "success")
            except Exception as e: flash(f"Error: {str(e)}", "danger")
            return redirect(url_for('establishment.category_master'))
            
        if action == 'SAVE' or action == 'UPDATE':
            edit_id = request.form.get('edit_id')
            cat_name = request.form.get('category_name')
            
            if edit_id and not perm.get('AllowUpdate'):
                flash("You do not have permission to update.", "danger")
                return redirect(url_for('establishment.category_master'))
            if not edit_id and not perm.get('AllowAdd'):
                flash("You do not have permission to add.", "danger")
                return redirect(url_for('establishment.category_master'))
                
            try:
                if edit_id:
                    DB.execute("""
                        UPDATE SAL_Category_Mst SET category = ?, fk_updUserID = ?, fk_updDateID = 'ab-428' 
                        WHERE pk_catid = ?
                    """, [cat_name, user_id, edit_id])
                    flash("Record Updated Successfully !", "success")
                else:
                    new_id = f"CAT-{to_int(DB.fetch_scalar('SELECT COUNT(*) FROM SAL_Category_Mst')) + 1}"
                    DB.execute("""
                        INSERT INTO SAL_Category_Mst (pk_catid, category, fk_insUserID, fk_insDateID) 
                        VALUES (?, ?, ?, 'ab-428')
                    """, [new_id, cat_name, user_id])
                    flash("Record Saved Successfully !", "success")
            except Exception as e: flash(f"Error: {str(e)}", "danger")
            return redirect(url_for('establishment.category_master'))
            
    page = to_int(request.args.get('page', 1)); pagination, sql_limit = get_pagination("SAL_Category_Mst", page)
    categories = DB.fetch_all(f"SELECT pk_catid as id, category as name FROM SAL_Category_Mst ORDER BY category {sql_limit}")
    
    edit_data = None; edit_id = request.args.get('edit_id')
    if edit_id:
        edit_data = DB.fetch_one("SELECT pk_catid as id, category as name FROM SAL_Category_Mst WHERE pk_catid = ?", [edit_id])
        
    return render_template('establishment/category_master.html', 
                           categories=categories, edit_data=edit_data, 
                           perm=perm, pagination=pagination)

@establishment_bp.route('/gad_nongad_master', methods=['GET', 'POST'])
@permission_required('Gad-Nongad Master')
def gad_nongad_master(): return manage_master('gad_nongad')

@establishment_bp.route('/discipline_master', methods=['GET', 'POST'])
@permission_required('Discipline Master')
def discipline_master(): return manage_master('discipline')

@establishment_bp.route('/department_master', methods=['GET', 'POST'])
@permission_required('Department Master')
def department_master():
    user_id = session['user_id']; loc_id = session.get('selected_loc'); perm = NavModel.check_permission(user_id, loc_id, 'Department Master')
    emp_search_results = []
    
    if request.method == 'POST':
        action = (request.form.get('action') or '').strip().upper()
        if action == 'RESET':
            return redirect(url_for('establishment.department_master'))
            
        if action == 'SEARCH_HOD':
            e_code = (request.form.get('s_emp_code') or '').strip()
            e_name = (request.form.get('s_emp_name') or '').strip()
            where_e = ["1=1"]
            params_e = []
            if e_code: where_e.append("empcode LIKE ?"); params_e.append(f"%{e_code}%")
            if e_name: where_e.append("empname LIKE ?"); params_e.append(f"%{e_name}%")
            emp_search_results = DB.fetch_all(f"SELECT TOP 20 pk_empid, empcode, empname FROM SAL_Employee_Mst WHERE {' AND '.join(where_e)}", params_e)
            
        elif action == 'DELETE':
            if not perm.get('AllowDelete'):
                flash("You do not have permission to delete.", "danger")
                return redirect(url_for('establishment.department_master'))
            delete_id = request.form.get('delete_id')
            try:
                DB.execute("DELETE FROM Department_Mst WHERE pk_deptid = ?", [delete_id])
                flash("Department deleted successfully.", "success")
            except Exception as e: flash(f"Error: {str(e)}", "danger")
            return redirect(url_for('establishment.department_master'))
            
        elif action == 'SAVE' or action == 'UPDATE':
            edit_id = request.form.get('edit_id')
            dept_name = request.form.get('department')
            hod_id = request.form.get('hod_id')
            email = request.form.get('email')
            alias = request.form.get('alias')
            
            if edit_id and not perm.get('AllowUpdate'):
                flash("You do not have permission to update.", "danger")
                return redirect(url_for('establishment.department_master'))
            if not edit_id and not perm.get('AllowAdd'):
                flash("You do not have permission to add.", "danger")
                return redirect(url_for('establishment.department_master'))
                
            try:
                if edit_id:
                    DB.execute("""
                        UPDATE Department_Mst SET description = ?, Hod_Id = ?, Email_Id = ?, DeptAlias = ?,
                               fk_updUserID = ?, fk_updDateID = 'ab-428' 
                        WHERE pk_deptid = ?
                    """, [dept_name, hod_id, email, alias, user_id, edit_id])
                    flash("Record Updated Successfully !", "success")
                else:
                    new_id = f"DE-{to_int(DB.fetch_scalar('SELECT COUNT(*) FROM Department_Mst')) + 1}"
                    DB.execute("""
                        INSERT INTO Department_Mst (pk_deptid, description, Hod_Id, Email_Id, DeptAlias, fk_insUserID, fk_insDateID) 
                        VALUES (?, ?, ?, ?, ?, ?, 'ab-428')
                    """, [new_id, dept_name, hod_id, email, alias, user_id])
                    flash("Record Saved Successfully !", "success")
            except Exception as e: flash(f"Error: {str(e)}", "danger")
            return redirect(url_for('establishment.department_master'))
            
    # Search + Pagination
    s_type = request.args.get('s_type', '--Select--')
    s_val = (request.args.get('s_val') or '').strip()
    where = " WHERE 1=1"
    params = []
    if s_val and s_type == 'Department':
        where += " AND description LIKE ?"
        params.append(f"%{s_val}%")

    page = to_int(request.args.get('page', 1)); pagination, sql_limit = get_pagination("Department_Mst", page, where=where, params=params)
    departments = DB.fetch_all(f"""
        SELECT D.pk_deptid as id, D.description as dept_name, 
               E.empcode + ' ~ ' + E.empname as hod_name, D.DeptAlias as alias
        FROM Department_Mst D
        LEFT JOIN SAL_Employee_Mst E ON D.Hod_Id = E.pk_empid
        {where}
        ORDER BY D.description {sql_limit}
    """, params)
    
    edit_data = None; edit_id = request.args.get('edit_id')
    if edit_id:
        edit_data = DB.fetch_one("""
            SELECT D.pk_deptid as id, D.description as department, D.Hod_Id as hod_id, 
                   E.empcode + ' ~ ' + E.empname as hod_text, D.Email_Id as email, D.DeptAlias as alias 
            FROM Department_Mst D 
            LEFT JOIN SAL_Employee_Mst E ON D.Hod_Id = E.pk_empid 
            WHERE D.pk_deptid = ?
        """, [edit_id])
        
    return render_template('establishment/department_master.html', 
                           departments=departments, edit_data=edit_data, 
                           perm=perm, pagination=pagination, 
                           emp_search_results=emp_search_results,
                           s_type=s_type, s_val=s_val)

@establishment_bp.route('/designation_master', methods=['GET', 'POST'])
@permission_required('Designation Master')
def designation_master():
    user_id = session['user_id']; loc_id = session.get('selected_loc'); perm = NavModel.check_permission(user_id, loc_id, 'Designation Master')
    
    if request.method == 'POST':
        action = (request.form.get('action') or '').strip().upper()
        if action == 'RESET':
            return redirect(url_for('establishment.designation_master'))
            
        if action == 'DELETE':
            if not perm.get('AllowDelete'):
                flash("You do not have permission to delete.", "danger")
                return redirect(url_for('establishment.designation_master'))
            delete_id = request.form.get('delete_id')
            try:
                DB.execute("DELETE FROM SAL_Designation_Mst WHERE pk_desgid = ?", [delete_id])
                flash("Designation deleted successfully.", "success")
            except Exception as e: flash(f"Error: {str(e)}", "danger")
            return redirect(url_for('establishment.designation_master'))
            
        if action == 'SAVE' or action == 'UPDATE':
            edit_id = request.form.get('edit_id')
            designation = request.form.get('designation')
            grade_id = request.form.get('grade_id')
            desg_cat_id = request.form.get('desg_cat_id')
            class_id = request.form.get('class_id')
            retire_age = request.form.get('retire_age') or 60
            seniority_level = request.form.get('seniority_level') or 1
            qualification = request.form.get('qualification')
            remarks = request.form.get('remarks')
            is_authority = 1 if request.form.get('is_authority') else 0
            next_desg_id = request.form.get('next_desg_id') or None
            appointing_auth_id = request.form.get('appointing_auth_id') or None
            
            # Additional logic for 'isteaching' based on category (9 is usually teaching)
            is_teaching = 1 if desg_cat_id == '9' else 0
            
            if edit_id and not perm.get('AllowUpdate'):
                flash("You do not have permission to update.", "danger")
                return redirect(url_for('establishment.designation_master'))
            if not edit_id and not perm.get('AllowAdd'):
                flash("You do not have permission to add.", "danger")
                return redirect(url_for('establishment.designation_master'))
                
            params = [designation, grade_id, desg_cat_id, class_id, retire_age, seniority_level, qualification, remarks, is_authority, next_desg_id, appointing_auth_id, is_teaching]
            try:
                if edit_id:
                    DB.execute("""
                        UPDATE SAL_Designation_Mst 
                        SET designation = ?, fk_gradeid = ?, fk_desgcat = ?, fk_classId = ?, 
                            retireage = ?, senioritylevel = ?, qualification = ?, remarks = ?, 
                            Chk_AppointingAuth = ?, fk_Prodesig = ?, Appointing_Auth = ?, isteaching = ?
                        WHERE pk_desgid = ?
                    """, params + [edit_id])
                    flash("Record Updated Successfully !", "success")
                else:
                    new_id = f"DS-{to_int(DB.fetch_scalar('SELECT COUNT(*) FROM SAL_Designation_Mst')) + 1}"
                    DB.execute("""
                        INSERT INTO SAL_Designation_Mst (pk_desgid, designation, fk_gradeid, fk_desgcat, fk_classId, 
                                                       retireage, senioritylevel, qualification, remarks, 
                                                       Chk_AppointingAuth, fk_Prodesig, Appointing_Auth, isteaching) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, [new_id] + params)
                    flash("Record Saved Successfully !", "success")
            except Exception as e: flash(f"Error: {str(e)}", "danger")
            return redirect(url_for('establishment.designation_master'))
            
    page = to_int(request.args.get('page', 1)); pagination, sql_limit = get_pagination("SAL_Designation_Mst", page)
    
    designations = DB.fetch_all(f"""
        SELECT D.pk_desgid as id, D.designation, C.description as cat_name, CL.classname as class_name, 
               G.gradedetails as grade_name, D.senioritylevel, D.retireage
        FROM SAL_Designation_Mst D
        LEFT JOIN SAL_DesignationCat_Mst C ON D.fk_desgcat = C.pk_desgcat
        LEFT JOIN SAL_Class_Mst CL ON D.fk_classId = CL.pk_classid
        LEFT JOIN SAL_Grade_Mst G ON D.fk_gradeid = G.pk_gradeid
        ORDER BY D.designation {sql_limit}
    """)
    
    grades = DB.fetch_all("SELECT pk_gradeid as id, gradedetails as name FROM SAL_Grade_Mst ORDER BY gradedetails")
    categories = DB.fetch_all("SELECT pk_desgcat as id, description as name FROM SAL_DesignationCat_Mst ORDER BY OrderNo")
    classes = DB.fetch_all("SELECT pk_classid as id, classname as name FROM SAL_Class_Mst ORDER BY classname")
    all_designations = DB.fetch_all("SELECT pk_desgid as id, designation as name FROM SAL_Designation_Mst ORDER BY designation")
    
    # Only show Registrar and VC as appointing authorities as seen in live
    appointing_authorities = [
        {'id': 'VC-336', 'name': 'Registrar'},
        {'id': 'VC-417', 'name': 'Vice Chancellor'}
    ]
    
    edit_data = None; edit_id = request.args.get('edit_id')
    if edit_id:
        edit_data = DB.fetch_one("SELECT * FROM SAL_Designation_Mst WHERE pk_desgid = ?", [edit_id])
        
    return render_template('establishment/designation_master.html', 
                           designations=designations, grades=grades, categories=categories, 
                           classes=classes, all_designations=all_designations, 
                           appointing_authorities=appointing_authorities,
                           edit_data=edit_data, perm=perm, pagination=pagination)

@establishment_bp.route('/district_master', methods=['GET', 'POST'])
@permission_required('District Master')
def district_master(): return manage_master('district')

@establishment_bp.route('/location_master', methods=['GET', 'POST'])
@permission_required('Location Master')
def location_master(): return manage_master('location')

@establishment_bp.route('/ddo_master', methods=['GET', 'POST'])
@permission_required('DDO Master')
def ddo_master(): return manage_master('ddo')

@establishment_bp.route('/class_master', methods=['GET', 'POST'])
@permission_required('Class Master')
def class_master():
    user_id = session['user_id']; loc_id = session.get('selected_loc'); perm = NavModel.check_permission(user_id, loc_id, 'Class Master')
    
    if request.method == 'POST':
        action = (request.form.get('action') or '').strip().upper()
        if action == 'RESET':
            return redirect(url_for('establishment.class_master'))
            
        if action == 'DELETE':
            if not perm.get('AllowDelete'):
                flash("You do not have permission to delete.", "danger")
                return redirect(url_for('establishment.class_master'))
            delete_id = request.form.get('delete_id')
            try:
                DB.execute("DELETE FROM SAL_Class_Mst WHERE pk_classid = ?", [delete_id])
                flash("Class deleted successfully.", "success")
            except Exception as e: flash(f"Error: {str(e)}", "danger")
            return redirect(url_for('establishment.class_master'))
            
        if action == 'SAVE' or action == 'UPDATE':
            edit_id = request.form.get('edit_id')
            name = request.form.get('name')
            gad_id = request.form.get('gad_id')
            is_teaching = 1 if request.form.get('is_teaching') else 0
            is_officer = 1 if request.form.get('is_officer') else 0
            
            if edit_id and not perm.get('AllowUpdate'):
                flash("You do not have permission to update.", "danger")
                return redirect(url_for('establishment.class_master'))
            if not edit_id and not perm.get('AllowAdd'):
                flash("You do not have permission to add.", "danger")
                return redirect(url_for('establishment.class_master'))
                
            try:
                if edit_id:
                    DB.execute("""
                        UPDATE SAL_Class_Mst SET classname = ?, fk_gadid = ?, isTeaching = ?, isOfficer = ? 
                        WHERE pk_classid = ?
                    """, [name, gad_id, is_teaching, is_officer, edit_id])
                    flash("Record Updated Successfully !", "success")
                else:
                    new_id = f"CL-{to_int(DB.fetch_scalar('SELECT COUNT(*) FROM SAL_Class_Mst')) + 1}"
                    DB.execute("""
                        INSERT INTO SAL_Class_Mst (pk_classid, classname, fk_gadid, isTeaching, isOfficer) 
                        VALUES (?, ?, ?, ?, ?)
                    """, [new_id, name, gad_id, is_teaching, is_officer])
                    flash("Record Saved Successfully !", "success")
            except Exception as e: flash(f"Error: {str(e)}", "danger")
            return redirect(url_for('establishment.class_master'))
            
    page = to_int(request.args.get('page', 1)); pagination, sql_limit = get_pagination("SAL_Class_Mst", page)
    
    classes = DB.fetch_all(f"""
        SELECT C.pk_classid as id, C.classname, G.gadnongad as gad_name, C.isTeaching, C.isOfficer
        FROM SAL_Class_Mst C
        LEFT JOIN SAL_GadNongad_Mst G ON C.fk_gadid = G.pk_gadid
        ORDER BY C.classname {sql_limit}
    """)
    
    gad_list = DB.fetch_all("SELECT pk_gadid as id, gadnongad as name FROM SAL_GadNongad_Mst ORDER BY gadnongad")
    
    edit_data = None; edit_id = request.args.get('edit_id')
    if edit_id:
        edit_data = DB.fetch_one("SELECT pk_classid as id, classname as name, fk_gadid as gad_id, isTeaching as is_teaching, isOfficer as is_officer FROM SAL_Class_Mst WHERE pk_classid = ?", [edit_id])
        
    return render_template('establishment/class_master.html', 
                           classes=classes, gad_list=gad_list, 
                           edit_data=edit_data, perm=perm, pagination=pagination)

@establishment_bp.route('/grade_master', methods=['GET', 'POST'])
@permission_required('Grade Master')
def grade_master(): return manage_master('grade')

@establishment_bp.route('/section_master', methods=['GET', 'POST'])
@permission_required('Section Master')
def section_master():
    user_id = session['user_id']; loc_id = session.get('selected_loc'); perm = NavModel.check_permission(user_id, loc_id, 'Section Master')
    emp_search_results = []
    
    if request.method == 'POST':
        action = (request.form.get('action') or '').strip().upper()
        if action == 'RESET':
            return redirect(url_for('establishment.section_master'))
            
        if action == 'SEARCH_SO':
            e_code = (request.form.get('s_emp_code') or '').strip()
            e_name = (request.form.get('s_emp_name') or '').strip()
            where_e = ["1=1"]
            params_e = []
            if e_code: where_e.append("empcode LIKE ?"); params_e.append(f"%{e_code}%")
            if e_name: where_e.append("empname LIKE ?"); params_e.append(f"%{e_name}%")
            emp_search_results = DB.fetch_all(f"SELECT TOP 20 pk_empid, empcode, empname FROM SAL_Employee_Mst WHERE {' AND '.join(where_e)}", params_e)
            
        elif action == 'DELETE':
            if not perm.get('AllowDelete'):
                flash("You do not have permission to delete.", "danger")
                return redirect(url_for('establishment.section_master'))
            delete_id = request.form.get('delete_id')
            try:
                DB.execute("DELETE FROM SAL_Section_Mst WHERE pk_sectionid = ?", [delete_id])
                flash("Section deleted successfully.", "success")
            except Exception as e: flash(f"Error: {str(e)}", "danger")
            return redirect(url_for('establishment.section_master'))
            
        elif action == 'SAVE' or action == 'UPDATE':
            edit_id = request.form.get('edit_id')
            dept_id = request.form.get('dept_id')
            description = request.form.get('description')
            so_id = request.form.get('so_id')
            email = request.form.get('email')
            alias = request.form.get('alias')
            
            if edit_id and not perm.get('AllowUpdate'):
                flash("You do not have permission to update.", "danger")
                return redirect(url_for('establishment.section_master'))
            if not edit_id and not perm.get('AllowAdd'):
                flash("You do not have permission to add.", "danger")
                return redirect(url_for('establishment.section_master'))
                
            try:
                if edit_id:
                    DB.execute("""
                        UPDATE SAL_Section_Mst 
                        SET description = ?, fk_deptid = ?, SOD_Id = ?, Email_Id = ?, SectionAlias = ?
                        WHERE pk_sectionid = ?
                    """, [description, dept_id, so_id, email, alias, edit_id])
                    flash("Record Updated Successfully !", "success")
                else:
                    new_id = f"SEC-{to_int(DB.fetch_scalar('SELECT COUNT(*) FROM SAL_Section_Mst')) + 1}"
                    DB.execute("""
                        INSERT INTO SAL_Section_Mst (pk_sectionid, description, fk_deptid, SOD_Id, Email_Id, SectionAlias) 
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, [new_id, description, dept_id, so_id, email, alias])
                    flash("Record Saved Successfully !", "success")
            except Exception as e: flash(f"Error: {str(e)}", "danger")
            return redirect(url_for('establishment.section_master'))
            
    page = to_int(request.args.get('page', 1)); pagination, sql_limit = get_pagination("SAL_Section_Mst", page)
    sections = DB.fetch_all(f"""
        SELECT S.pk_sectionid as id, S.description, D.description as dept_name, 
               E.empcode + ' ~ ' + E.empname as so_name, S.SectionAlias as alias
        FROM SAL_Section_Mst S
        LEFT JOIN Department_Mst D ON S.fk_deptid = D.pk_deptid
        LEFT JOIN SAL_Employee_Mst E ON S.SOD_Id = E.pk_empid
        ORDER BY S.description {sql_limit}
    """)
    
    departments = DB.fetch_all("SELECT pk_deptid as id, description as name FROM Department_Mst ORDER BY description")
    
    edit_data = None; edit_id = request.args.get('edit_id')
    if edit_id:
        edit_data = DB.fetch_one("""
            SELECT S.pk_sectionid as id, S.description, S.fk_deptid as dept_id, S.SOD_Id as so_id,
                   E.empcode + ' ~ ' + E.empname as so_text, S.Email_Id as email, S.SectionAlias as alias 
            FROM SAL_Section_Mst S 
            LEFT JOIN SAL_Employee_Mst E ON S.SOD_Id = E.pk_empid 
            WHERE S.pk_sectionid = ?
        """, [edit_id])
        
    return render_template('establishment/section_master.html', 
                           sections=sections, departments=departments, edit_data=edit_data, 
                           perm=perm, pagination=pagination, emp_search_results=emp_search_results)

@establishment_bp.route('/religion_master', methods=['GET', 'POST'])
@permission_required('Religion Master')
def religion_master(): return manage_master('religion')

@establishment_bp.route('/controlling_office_master', methods=['GET', 'POST'])
@permission_required('Controlling Office Master')
def controlling_office_master(): return manage_master('controlling_office')

@establishment_bp.route('/office_type_master', methods=['GET', 'POST'])
@permission_required('Office Type Master')
def office_type_master():
    user_id = session['user_id']; loc_id = session.get('selected_loc'); perm = NavModel.check_permission(user_id, loc_id, 'Office Type Master')
    
    if request.method == 'POST':
        action = (request.form.get('action') or '').strip().upper()
        if action == 'RESET':
            return redirect(url_for('establishment.office_type_master'))
            
        if action == 'DELETE':
            if not perm.get('AllowDelete'):
                flash("You do not have permission to delete.", "danger")
                return redirect(url_for('establishment.office_type_master'))
            delete_id = request.form.get('delete_id')
            try:
                DB.execute("DELETE FROM OfficeTypeMaster WHERE OfficeTypeID = ?", [delete_id])
                flash("Office Type deleted successfully.", "success")
            except Exception as e: flash(f"Error: {str(e)}", "danger")
            return redirect(url_for('establishment.office_type_master'))
            
        if action == 'SAVE' or action == 'UPDATE':
            edit_id = request.form.get('edit_id')
            code = request.form.get('code')
            name = request.form.get('name')
            
            if edit_id and not perm.get('AllowUpdate'):
                flash("You do not have permission to update.", "danger")
                return redirect(url_for('establishment.office_type_master'))
            if not edit_id and not perm.get('AllowAdd'):
                flash("You do not have permission to add.", "danger")
                return redirect(url_for('establishment.office_type_master'))
                
            try:
                if edit_id:
                    DB.execute("""
                        UPDATE OfficeTypeMaster SET code = ?, OfficeName = ? WHERE OfficeTypeID = ?
                    """, [code, name, edit_id])
                    flash("Record Updated Successfully !", "success")
                else:
                    DB.execute("""
                        INSERT INTO OfficeTypeMaster (code, OfficeName) VALUES (?, ?)
                    """, [code, name])
                    flash("Record Saved Successfully !", "success")
            except Exception as e: flash(f"Error: {str(e)}", "danger")
            return redirect(url_for('establishment.office_type_master'))
            
    page = to_int(request.args.get('page', 1)); pagination, sql_limit = get_pagination("OfficeTypeMaster", page)
    types = DB.fetch_all(f"SELECT OfficeTypeID as id, code, OfficeName as name FROM OfficeTypeMaster ORDER BY OfficeName {sql_limit}")
    
    edit_data = None; edit_id = request.args.get('edit_id')
    if edit_id:
        edit_data = DB.fetch_one("SELECT OfficeTypeID as id, code, OfficeName as name FROM OfficeTypeMaster WHERE OfficeTypeID = ?", [edit_id])
        
    return render_template('establishment/office_type_master.html', 
                           types=types, edit_data=edit_data, 
                           perm=perm, pagination=pagination)

@establishment_bp.route('/employee_master')
@establishment_bp.route('/employee_master', methods=['GET', 'POST'])
@permission_required('Employee Master')
def employee_master():
    from app.models.hrms import EmployeeModel

    user_id = session['user_id']
    loc_id = session.get('selected_loc')
    perm = NavModel.check_permission(user_id, loc_id, 'Employee Master')

    def get_action():
        vals = [(v or '').strip().upper() for v in request.form.getlist('action')]
        vals = [v for v in vals if v]
        return vals[-1] if vals else ''

    def sval(name):
        return (request.form.get(name) or '').strip()

    def sid(name):
        v = sval(name)
        return v or None

    def sbit(name):
        v = (request.form.get(name) or '').strip().lower()
        return 1 if v in ('1', 'on', 'true', 'yes', 'y') else 0

    if request.method == 'POST':
        action = get_action()

        if action == 'RESET':
            return redirect(url_for('establishment.employee_master'))

        if action in ('SEARCH', 'VIEW'):
            args = {
                's_emp_code': sval('s_emp_code'),
                's_emp_name': sval('s_emp_name'),
                's_dept_id': sval('s_dept_id'),
                's_desg_id': sval('s_desg_id'),
                's_ctrl_id': sval('s_ctrl_id'),
                'page': 1
            }
            args = {k: v for k, v in args.items() if v}
            return redirect(url_for('establishment.employee_master', **args))

        if action in ('SAVE', 'UPDATE'):
            emp_id = sval('edit_id')
            is_new = not emp_id

            if is_new and action == 'UPDATE':
                flash('Please select an employee to update.', 'danger')
                return redirect(url_for('establishment.employee_master'))

            if is_new and not perm.get('AllowAdd'):
                flash('You do not have permission to add.', 'danger')
                return redirect(url_for('establishment.employee_master'))

            if (not is_new) and not perm.get('AllowUpdate'):
                flash('You do not have permission to update.', 'danger')
                return redirect(url_for('establishment.employee_master', edit_id=emp_id))

            try:
                if is_new:
                    empcode = sval('empcode')
                    if not empcode:
                        flash('Employee Code is required for new employee.', 'danger')
                        return redirect(url_for('establishment.employee_master'))

                    new_id = to_int(DB.fetch_scalar('SELECT ISNULL(MAX(CAST(pk_empid AS INT)), 0) FROM SAL_Employee_Mst') or 0) + 1
                    emp_id = str(new_id)
                    DB.execute('''
                        INSERT INTO SAL_Employee_Mst (pk_empid, empcode, employeeleftstatus, fk_insUserID, fk_insDateID)
                        VALUES (?, ?, 'N', ?, GETDATE())
                    ''', [emp_id, empcode, user_id])

                DB.execute('''
                    UPDATE SAL_Employee_Mst
                    SET manualempcode = ?,
                        fK_Salutation_ID = ?,
                        empname = ?,
                        fathername = ?,
                        idcard = ?,
                        panno = ?,
                        ecrno = ?,
                        AadhaarNo = ?,
                        ecrpageno = ?,
                        LibraryCardNo = ?,
                        remarks = ?,
                        paymode = ?,
                        bankaccountno = ?,
                        fk_bankid = ?,
                        fk_controllingid = ?,
                        fk_postedcontrollingid = ?,
                        fk_ddoid = ?,
                        postingddo = ?,
                        fk_locid = ?,
                        postinglocation = ?,
                        fk_deptid = ?,
                        fk_Pdeptid = ?,
                        fk_sectionid = ?,
                        fk_postedsectionid = ?,
                        fk_disid = ?,
                        fk_natureid = ?,
                        fk_fundid = ?,
                        fk_subanc = ?,
                        leftdate = TRY_CONVERT(date, NULLIF(?, ''), 103),
                        employeeleftstatus = ?,
                        leftreason = ?,
                        leftremarks = ?,
                        reportingto = ?,
                        incdate = TRY_CONVERT(date, NULLIF(?, ''), 103),
                        pfileno = ?,
                        mbfno = ?,
                        pgteachercode = ?,
                        sipremno = ?,
                        fK_Asso_ID = ?,
                        addcharge = ?,
                        typeofallowance = ?,
                        stopsalary = ?,
                        ishandicap = ?,
                        stoppf = ?,
                        stopattendance = ?,
                        hrahrdnotapplicable = ?,
                        isgazetted = ?,
                        ondeputation = ?,
                        workdetails = ?,
                        fk_saltypeid = ?,
                        fk_cityid = ?,
                        fk_pdesgid = ?,
                        fk_desgid = ?,
                        fK_DesignspecId = ?,
                        fK_PDesignspecId = ?,
                        fk_gradeid = ?,
                        fk_cgradeid = ?,
                        level_type = ?,
                        level_name = ?,
                        cell_number = ?,
                        gradepay = TRY_CONVERT(decimal(18,2), NULLIF(?, '')),
                        cgradepay = TRY_CONVERT(decimal(18,2), NULLIF(?, '')),
                        curbasic = TRY_CONVERT(decimal(18,2), NULLIF(?, '')),
                        nextincamount = TRY_CONVERT(decimal(18,2), NULLIF(?, '')),
                        cspecialpay = TRY_CONVERT(decimal(18,2), NULLIF(?, '')),
                        cuca = TRY_CONVERT(decimal(18,2), NULLIF(?, '')),
                        cspecialallowance = TRY_CONVERT(decimal(18,2), NULLIF(?, '')),
                        PhdAllowance = TRY_CONVERT(decimal(18,2), NULLIF(?, '')),
                        associationfee = TRY_CONVERT(decimal(18,2), NULLIF(?, '')),
                        email = ?,
                        fk_updUserID = ?,
                        fk_updDateID = GETDATE()
                    WHERE pk_empid = ?
                ''', [
                    sid('manualcode'), sid('salutation_id'), sid('empname'), sid('fathername'), sid('idcard'),
                    sid('panno'), sid('ecrno'), sid('aadhaarno'), sid('ecrpageno'), sid('libcardno'),
                    sid('remarks'), sid('paymode'), sid('accno'), sid('bank_id'),
                    sid('actual_ctrl_id'), sid('posted_ctrl_id'), sid('actual_ddo_id'), sid('posted_ddo_id'),
                    sid('actual_loc_id'), sid('posted_loc_id'), sid('actual_dept_id'), sid('posted_dept_id'),
                    sid('section_id'), sid('posted_section_id'),
                    sid('discipline_id'), sid('nature_id'), sid('fund_id'), sid('scheme_id'),
                    sval('left_date'), sid('left_status'), sid('left_reason'), sid('left_remarks'), sid('reporting_to'),
                    sval('inc_date'), sid('pf_no'), sid('welfare_no'), sid('pg_teacher_code'), sid('si_prem_no'),
                    sid('asso_id'), sid('add_charge'), sid('medical_allowance_type'),
                    sbit('stop_salary'), sbit('is_handicap'), sbit('stop_gpf'), sbit('stop_attendance'), sbit('hra_not_app'),
                    sbit('is_gazetted'), sbit('on_deputation'), sid('work_details'),
                    sid('sal_type_id'), sid('posting_city_id'), sid('post_desg_id'), sid('working_desg_id'),
                    sid('spec_id'), sid('posted_spec_id'), sid('grade_id'), sid('current_grade_id'),
                    sid('level_type'), sid('level_name'), sid('cell_number'),
                    sval('gradepay'), sval('cgradepay'), sval('basic'),
                    sval('inc_percentage'), sval('cspecialpay'), sval('cuca'), sval('cspecialallowance'), sval('phd_allowance'), sval('gpf_share'),
                    sid('email'), user_id, emp_id
                ])

                other_exists = int(DB.fetch_scalar('SELECT COUNT(*) FROM SAL_EmployeeOther_Details WHERE fk_empid = ?', [emp_id]) or 0) > 0

                if other_exists:
                    DB.execute('''
                        UPDATE SAL_EmployeeOther_Details
                        SET gender = ?,
                            fk_catid = ?,
                            fk_religionid = ?,
                            dateofbirth = TRY_CONVERT(date, NULLIF(?, ''), 103),
                            dateofappointment = TRY_CONVERT(date, NULLIF(?, ''), 103),
                            dateofjoining = TRY_CONVERT(date, NULLIF(?, ''), 103),
                            dateofretirement = TRY_CONVERT(date, NULLIF(?, ''), 103),
                            dateoflastappointment = TRY_CONVERT(date, NULLIF(?, ''), 103),
                            dateoflastjoining = TRY_CONVERT(date, NULLIF(?, ''), 103),
                            OrderNo = ?,
                            fk_quarterid = ?,
                            QuarterEffecDate = TRY_CONVERT(date, NULLIF(?, ''), 103),
                            AppointmentTime = ?,
                            remarks = ?,
                            fk_updUserID = ?,
                            fk_updDateID = GETDATE()
                        WHERE fk_empid = ?
                    ''', [
                        sid('gender'), sid('cat_id'), sid('rel_id'),
                        sval('dob'), sval('doa'), sval('doj'), sval('dor'), sval('last_doa'), sval('last_doj'),
                        sid('orderno'), sid('quarter_id'), sval('qtr_eff_date'), sid('joining_time'), sid('remarks'),
                        user_id, emp_id
                    ])
                else:
                    DB.execute('''
                        INSERT INTO SAL_EmployeeOther_Details (
                            fk_empid, gender, fk_catid, fk_religionid,
                            dateofbirth, dateofappointment, dateofjoining, dateofretirement,
                            dateoflastappointment, dateoflastjoining,
                            OrderNo, fk_quarterid, QuarterEffecDate, AppointmentTime, remarks,
                            fk_updUserID, fk_updDateID
                        ) VALUES (
                            ?, ?, ?, ?,
                            TRY_CONVERT(date, NULLIF(?, ''), 103),
                            TRY_CONVERT(date, NULLIF(?, ''), 103),
                            TRY_CONVERT(date, NULLIF(?, ''), 103),
                            TRY_CONVERT(date, NULLIF(?, ''), 103),
                            TRY_CONVERT(date, NULLIF(?, ''), 103),
                            TRY_CONVERT(date, NULLIF(?, ''), 103),
                            ?, ?,
                            TRY_CONVERT(date, NULLIF(?, ''), 103),
                            ?, ?,
                            ?, GETDATE()
                        )
                    ''', [
                        emp_id, sid('gender'), sid('cat_id'), sid('rel_id'),
                        sval('dob'), sval('doa'), sval('doj'), sval('dor'), sval('last_doa'), sval('last_doj'),
                        sid('orderno'), sid('quarter_id'), sval('qtr_eff_date'), sid('joining_time'), sid('remarks'),
                        user_id
                    ])

                

                # Save Salary Heads (Earnings/Deductions)
                try:
                    def upsert_head(head_id, amount_str, effect_str, is_manual):
                        exists_hd = int(DB.fetch_scalar('SELECT COUNT(*) FROM SAL_EmployeeHead_Details WHERE fk_empid = ? AND fk_headid = ?', [emp_id, head_id]) or 0) > 0
                        if exists_hd:
                            DB.execute('''
                                UPDATE SAL_EmployeeHead_Details
                                SET amount = TRY_CONVERT(decimal(18,2), NULLIF(?, '')),
                                    effectdate = TRY_CONVERT(date, NULLIF(?, ''), 103),
                                    ismanual = ?,
                                    fk_updUserID = ?,
                                    fk_updDateID = GETDATE()
                                WHERE fk_empid = ? AND fk_headid = ?
                            ''', [amount_str, effect_str, 1 if is_manual else 0, user_id, emp_id, head_id])
                        else:
                            new_pk = to_int(DB.fetch_scalar('SELECT ISNULL(MAX(CAST(Pk_EmpHeadId AS INT)), 0) FROM SAL_EmployeeHead_Details') or 0) + 1
                            DB.execute('''
                                INSERT INTO SAL_EmployeeHead_Details (Pk_EmpHeadId, fk_empid, fk_headid, amount, effectdate, ismanual, fk_updUserID, fk_updDateID)
                                VALUES (?, ?, ?, TRY_CONVERT(decimal(18,2), NULLIF(?, '')), TRY_CONVERT(date, NULLIF(?, ''), 103), ?, ?, GETDATE())
                            ''', [new_pk, emp_id, head_id, amount_str, effect_str, 1 if is_manual else 0, user_id])

                    for hid in request.form.getlist('earn_head_id'):
                        hid = (hid or '').strip()
                        if not hid:
                            continue
                        amt = (request.form.get(f'earn_amount_{hid}') or '').strip()
                        eff = (request.form.get(f'earn_effect_{hid}') or '').strip()
                        man = request.form.get(f'earn_manual_{hid}') is not None
                        if amt or eff or man:
                            upsert_head(hid, amt, eff, man)

                    for hid in request.form.getlist('ded_head_id'):
                        hid = (hid or '').strip()
                        if not hid:
                            continue
                        amt = (request.form.get(f'ded_amount_{hid}') or '').strip()
                        eff = (request.form.get(f'ded_effect_{hid}') or '').strip()
                        man = request.form.get(f'ded_manual_{hid}') is not None
                        if amt or eff or man:
                            upsert_head(hid, amt, eff, man)
                except Exception:
                    pass

                flash('Record Processed Successfully !', 'success')
            except Exception as e:
                flash(f'Error: {str(e)}', 'danger')

            return redirect(url_for('establishment.employee_master', edit_id=emp_id))

    filters = {
        'empcode': (request.args.get('s_emp_code') or request.form.get('s_emp_code') or '').strip(),
        'empname': (request.args.get('s_emp_name') or request.form.get('s_emp_name') or '').strip(),
        'dept_id': (request.args.get('s_dept_id') or request.form.get('s_dept_id') or '').strip(),
        'desg_id': (request.args.get('s_desg_id') or request.form.get('s_desg_id') or '').strip(),
        'ctrl_id': (request.args.get('s_ctrl_id') or request.form.get('s_ctrl_id') or '').strip()
    }

    page = to_int(request.args.get('page', 1))
    edit_id = request.args.get('edit_id')

    total = DB.fetch_scalar('SELECT COUNT(*) FROM SAL_Employee_Mst')
    pagination = {'page': page, 'per_page': 10, 'total': total, 'total_pages': (total // 10) + 1}
    sql_limit = f"OFFSET {(page-1)*10} ROWS FETCH NEXT 10 ROWS ONLY"

    employees = EmployeeModel.search_employees_detailed(filters, sql_limit)
    lookups = EmployeeModel.get_full_lookups()
    lookups['quarters'] = DB.fetch_all("SELECT pk_quarterid as id, quarterno + ' || ' + (SELECT TOP 1 cityname FROM SAL_City_Mst WHERE pk_cityid=fk_cityid) as name FROM SAL_Quarter_Mst ORDER BY quarterno")

    curr_month, curr_year = EmployeeModel.get_current_month_year()

    edit_data = None
    earning_heads = []
    deduction_heads = []
    total_earnings = 0
    total_deductions = 0
    net_pay = 0
    income_tax = 0.00

    if edit_id:
        edit_data = EmployeeModel.get_employee_full_details(edit_id)
        if edit_data:
            all_heads = DB.fetch_all('''
                SELECT H.pk_headid as head_id, H.description, H.headtype, H.mapping,
                       EH.amount, CONVERT(varchar, EH.effectdate, 23) as effect_date,
                       EH.ismanual
                FROM SAL_Head_Mst H
                LEFT JOIN SAL_EmployeeHead_Details EH
                  ON EH.fk_headid = H.pk_headid AND EH.fk_empid = ?
                WHERE H.headtype IN ('E', 'D')
                ORDER BY H.headtype DESC, H.displayorder
            ''', [edit_id])
            earning_heads = [h for h in all_heads if h.get('headtype') == 'E']
            deduction_heads = [h for h in all_heads if h.get('headtype') == 'D']
            total_earnings = sum((h.get('amount') or 0) for h in earning_heads)
            total_deductions = sum((h.get('amount') or 0) for h in deduction_heads)
            net_pay = total_earnings - total_deductions

    return render_template(
        'establishment/employee_master.html',
        employees=employees,
        lookups=lookups,
        edit_data=edit_data,
        perm=perm,
        pagination=pagination,
        filters=filters,
        earning_heads=earning_heads,
        deduction_heads=deduction_heads,
        total_earnings=total_earnings,
        total_deductions=total_deductions,
        income_tax=income_tax,
        net_pay=net_pay,
        curr_month=curr_month,
        curr_year=curr_year,
        edit_id=edit_id
    )


@establishment_bp.route('/designation_spec')
@permission_required('Designation Specialization Master')
def designation_spec_master():
    cfg = {'title': 'Designation Specialization', 'table': 'SMS_BranchMst', 'pk': 'Pk_BranchId', 'name': 'Branchname'}
    # Reusing generic logic for specific branch table
    page = int(request.args.get('page', 1))
    pagination, sql_limit = get_pagination(cfg['table'], page)
    data = DB.fetch_all(f"SELECT * FROM {cfg['table']} ORDER BY {cfg['name']} {sql_limit}")
    return render_template('establishment/designation_spec_master.html', data=data, pagination=pagination)

@establishment_bp.route('/employee_master_scheme_wise', methods=['GET', 'POST'])
@permission_required('Employee Master Scheme Wise')
def employee_master_scheme_wise():
    from app.models.hrms import EmployeeModel

    user_id = session['user_id']
    loc_id = session.get('selected_loc')
    perm = NavModel.check_permission(user_id, loc_id, 'Employee Master Scheme Wise')

def manage_standard_master(key, title, table, pk, name_col, order_col=None):
    user_id = session['user_id']; loc_id = session.get('selected_loc'); perm = NavModel.check_permission(user_id, loc_id, title)
    if request.method == 'POST':
        action = (request.form.get('action') or '').strip().upper()
        if action == 'RESET': return redirect(url_for(f'establishment.{key}_master'))
        if action == 'DELETE':
            if not perm.get('AllowDelete'): flash("No permission to delete.", "danger")
            else:
                try: 
                    DB.execute(f"DELETE FROM {table} WHERE {pk} = ?", [request.form.get('delete_id')])
                    flash("Deleted Successfully.", "success")
                except Exception as e: flash(str(e), "danger")
            return redirect(url_for(f'establishment.{key}_master'))
        if action in ['SAVE', 'UPDATE']:
            eid = request.form.get('edit_id'); val = request.form.get('name')
            ord_val = request.form.get('order_no') or 0
            if eid and not perm.get('AllowUpdate'): flash("No permission to update.", "danger")
            elif not eid and not perm.get('AllowAdd'): flash("No permission to add.", "danger")
            else:
                try:
                    if eid:
                        sql = f"UPDATE {table} SET {name_col} = ?"
                        params = [val]
                        if order_col: sql += f", {order_col} = ?"; params.append(ord_val)
                        sql += f" WHERE {pk} = ?"; params.append(eid)
                        DB.execute(sql, params); flash("Updated Successfully.", "success")
                    else:
                        new_id = to_int(DB.fetch_scalar(f"SELECT ISNULL(MAX(CAST({pk} AS INT)), 0) FROM {table}")) + 1
                        sql = f"INSERT INTO {table} ({pk}, {name_col}"
                        params = [new_id, val]
                        if order_col: sql += f", {order_col}) VALUES (?, ?, ?)"; params.append(ord_val)
                        else: sql += ") VALUES (?, ?)"
                        DB.execute(sql, params); flash("Saved Successfully.", "success")
                except Exception as e: flash(str(e), "danger")
            return redirect(url_for(f'establishment.{key}_master'))

    page = to_int(request.args.get('page', 1)); pagination, sql_limit = get_pagination(table, page)
    order_by = order_col if order_col else name_col
    data = DB.fetch_all(f"SELECT {pk} as id, {name_col} as name" + (f", {order_col} as order_no" if order_col else "") + f" FROM {table} ORDER BY {order_by} {sql_limit}")
    edit_data = DB.fetch_one(f"SELECT {pk} as id, {name_col} as name" + (f", {order_col} as order_no" if order_col else "") + f" FROM {table} WHERE {pk} = ?", [request.args.get('edit_id')]) if request.args.get('edit_id') else None
    return render_template(f'establishment/standard_master.html', key=key, title=title, data=data, edit_data=edit_data, perm=perm, pagination=pagination, has_order=(order_col is not None))

@establishment_bp.route('/marital_status_master', methods=['GET', 'POST'])
@permission_required('Marital Status Master')
def marital_status_master():
    return manage_standard_master('marital_status', 'Marital Status Master', 'GIS_Marital_Status_Mst', 'PK_MS_ID', 'Marital_Status')

@establishment_bp.route('/fund_sponsor_master', methods=['GET', 'POST'])
@permission_required('Funds Sponsor Master')
def fund_sponsor_master():
    return manage_standard_master('fund_sponsor', 'Funds Sponsor Master', 'SAL_FundSponsor_Mst', 'PK_FSponsor_Id', 'FName', 'DisplayOrder')

@establishment_bp.route('/exam_type_master', methods=['GET', 'POST'])
@permission_required('ExamType Master')
def exam_type_master():
    return manage_standard_master('exam_type', 'ExamType Master', 'SAL_ExamType_Mst', 'PK_EType_Id', 'ExamType', 'DisplayOrder')

    def nval(v):
        v = (v or '').strip()
        return v if v else None

    def nid(v):
        v = (v or '').strip()
        return v if v else None

    if request.method == 'POST':
        action = (request.form.get('action') or '').strip().upper()
        if action == 'RESET':
            return redirect(url_for('establishment.employee_demographic_details'))

        if action in ('SAVE', 'UPDATE'):
            emp_id = (request.form.get('emp_id') or '').strip()
            if not emp_id:
                flash('Please select an employee to update.', 'danger')
                return redirect(url_for('establishment.employee_demographic_details'))

            if not perm.get('AllowAdd') and not perm.get('AllowUpdate'):
                flash('You do not have permission to add/update.', 'danger')
                return redirect(url_for('establishment.employee_demographic_details', edit_id=emp_id))

            payload = {
                'fk_quarterid': nid(request.form.get('quarter_id')),
                'joininglocation': nval(request.form.get('joining_location')),
                'fk_desgid_j': nid(request.form.get('joining_desg_id')),
                'fk_religionid': nid(request.form.get('religion_id')),
                'gender': nval(request.form.get('gender')),
                'fk_catid': nid(request.form.get('category_id')),
                'dateofappointment': nval(request.form.get('doa')),
                'dateofjoining': nval(request.form.get('doj')),
                'dateOfConfirmation': nval(request.form.get('doc')),
                'dateofretirement': nval(request.form.get('dor')),
                'dateoflastappointment': nval(request.form.get('dola')),
                'dateoflastjoining': nval(request.form.get('dolj')),
                'corresContactNo': nval(request.form.get('contact1')),
                'permanentContactNo': nval(request.form.get('contact2')),
                'econtactnum': nval(request.form.get('mobile')),
                'PersonalEmail': nval(request.form.get('personal_email')),
                'voteridnumber': nval(request.form.get('voter_id')),
                'uidnumber': nval(request.form.get('uid_no')),
                'technicalQualifications': nval(request.form.get('tech_qualification')),
                'scholarships': nval(request.form.get('scholarship')),
                'height': nval(request.form.get('height')),
                'IdentificationMarks': nval(request.form.get('identification_mark')),
                'remarks': nval(request.form.get('remarks')),
                'reference': nval(request.form.get('reference')),
                'mothername': nval(request.form.get('mother_name')),
                'txtHusbWifeName': nval(request.form.get('spouse_name')),
            }

            official_email = nval(request.form.get('official_email'))

            try:
                exists = to_int(DB.fetch_scalar('SELECT COUNT(*) FROM SAL_EmployeeOther_Details WHERE fk_empid = ?', [emp_id])) > 0
                if exists:
                    DB.execute('''
                        UPDATE SAL_EmployeeOther_Details
                        SET fk_quarterid = ?, joininglocation = ?, fk_desgid_j = ?, fk_religionid = ?, gender = ?, fk_catid = ?,
                            dateofappointment = TRY_CONVERT(date, NULLIF(?, ''), 103),
                            dateofjoining = TRY_CONVERT(date, NULLIF(?, ''), 103),
                            dateOfConfirmation = TRY_CONVERT(date, NULLIF(?, ''), 103),
                            dateofretirement = TRY_CONVERT(date, NULLIF(?, ''), 103),
                            dateoflastappointment = TRY_CONVERT(date, NULLIF(?, ''), 103),
                            dateoflastjoining = TRY_CONVERT(date, NULLIF(?, ''), 103),
                            corresContactNo = ?, permanentContactNo = ?, econtactnum = ?, PersonalEmail = ?,
                            voteridnumber = ?, uidnumber = ?, technicalQualifications = ?, scholarships = ?, height = ?,
                            IdentificationMarks = ?, remarks = ?, reference = ?, mothername = ?, txtHusbWifeName = ?,
                            fk_updUserID = ?, fk_updDateID = GETDATE()
                        WHERE fk_empid = ?
                    ''', [
                        payload['fk_quarterid'], payload['joininglocation'], payload['fk_desgid_j'], payload['fk_religionid'], payload['gender'], payload['fk_catid'],
                        payload['dateofappointment'], payload['dateofjoining'], payload['dateOfConfirmation'], payload['dateofretirement'], payload['dateoflastappointment'], payload['dateoflastjoining'],
                        payload['corresContactNo'], payload['permanentContactNo'], payload['econtactnum'], payload['PersonalEmail'],
                        payload['voteridnumber'], payload['uidnumber'], payload['technicalQualifications'], payload['scholarships'], payload['height'],
                        payload['IdentificationMarks'], payload['remarks'], payload['reference'], payload['mothername'], payload['txtHusbWifeName'],
                        user_id, emp_id
                    ])
                else:
                    DB.execute('''
                        INSERT INTO SAL_EmployeeOther_Details (
                            fk_empid, fk_quarterid, joininglocation, fk_desgid_j, fk_religionid, gender, fk_catid,
                            dateofappointment, dateofjoining, dateOfConfirmation, dateofretirement,
                            dateoflastappointment, dateoflastjoining,
                            corresContactNo, permanentContactNo, econtactnum, PersonalEmail,
                            voteridnumber, uidnumber, technicalQualifications, scholarships,
                            height, IdentificationMarks, remarks, reference, mothername, txtHusbWifeName,
                            fk_updUserID, fk_updDateID
                        ) VALUES (
                            ?, ?, ?, ?, ?, ?, ?,
                            TRY_CONVERT(date, NULLIF(?, ''), 103),
                            TRY_CONVERT(date, NULLIF(?, ''), 103),
                            TRY_CONVERT(date, NULLIF(?, ''), 103),
                            TRY_CONVERT(date, NULLIF(?, ''), 103),
                            TRY_CONVERT(date, NULLIF(?, ''), 103),
                            TRY_CONVERT(date, NULLIF(?, ''), 103),
                            ?, ?, ?, ?,
                            ?, ?, ?, ?,
                            ?, ?, ?, ?,
                            ?, GETDATE()
                        )
                    ''', [
                        emp_id, payload['fk_quarterid'], payload['joininglocation'], payload['fk_desgid_j'], payload['fk_religionid'], payload['gender'], payload['fk_catid'],
                        payload['dateofappointment'], payload['dateofjoining'], payload['dateOfConfirmation'], payload['dateofretirement'], payload['dateoflastappointment'], payload['dateoflastjoining'],
                        payload['corresContactNo'], payload['permanentContactNo'], payload['econtactnum'], payload['PersonalEmail'],
                        payload['voteridnumber'], payload['uidnumber'], payload['technicalQualifications'], payload['scholarships'],
                        payload['height'], payload['IdentificationMarks'], payload['remarks'], payload['reference'], payload['mothername'], payload['txtHusbWifeName'],
                        user_id
                    ])

                if official_email is not None:
                    DB.execute('UPDATE SAL_Employee_Mst SET email = ?, fk_updUserID = ?, fk_updDateID = GETDATE() WHERE pk_empid = ?', [official_email, user_id, emp_id])

                flash('Record Processed Successfully !', 'success')
            except Exception as e:
                flash(f'Error: {str(e)}', 'danger')

            return redirect(url_for('establishment.employee_demographic_details', edit_id=emp_id))

    filters = {
        's_emp_code': (request.args.get('s_emp_code') or '').strip(),
        's_manual_code': (request.args.get('s_manual_code') or '').strip(),
        's_emp_name': (request.args.get('s_emp_name') or '').strip(),
        's_ddo_id': (request.args.get('s_ddo_id') or '').strip(),
        's_loc_id': (request.args.get('s_loc_id') or '').strip(),
        's_dept_id': (request.args.get('s_dept_id') or '').strip(),
        's_desg_id': (request.args.get('s_desg_id') or '').strip(),
        's_sort_by': ((request.args.get('s_sort_by') or 'name').strip().lower())
    }

    where = " WHERE E.employeeleftstatus = 'N'"
    params = []
    if filters['s_emp_code']:
        where += ' AND E.empcode LIKE ?'; params.append(f"%{filters['s_emp_code']}%")
    if filters['s_manual_code']:
        where += ' AND E.manualempcode LIKE ?'; params.append(f"%{filters['s_manual_code']}%")
    if filters['s_emp_name']:
        where += ' AND E.empname LIKE ?'; params.append(f"%{filters['s_emp_name']}%")
    if filters['s_ddo_id']:
        where += ' AND E.fk_ddoid = ?'; params.append(filters['s_ddo_id'])
    if filters['s_loc_id']:
        where += ' AND E.fk_locid = ?'; params.append(filters['s_loc_id'])
    if filters['s_dept_id']:
        where += ' AND E.fk_deptid = ?'; params.append(filters['s_dept_id'])
    if filters['s_desg_id']:
        where += ' AND E.fk_desgid = ?'; params.append(filters['s_desg_id'])

    sort_col = 'E.empname' if filters['s_sort_by'] != 'manual' else 'E.manualempcode'

    page = to_int(request.args.get('page', 1))
    per_page = 10
    total_count = to_int(DB.fetch_scalar(f"SELECT COUNT(*) FROM SAL_Employee_Mst E {where}", params) or 0)
    total_pages = max(1, math.ceil(total_count / per_page)) if total_count else 1
    page = max(1, min(page, total_pages))
    offset = (page - 1) * per_page

    employees = DB.fetch_all(f'''
        SELECT E.pk_empid as id, E.manualempcode, E.empname,
               L.locname as location_name, D.description as dept_name,
               DS.designation as desg_name, ST.saltype as salary_type
        FROM SAL_Employee_Mst E
        LEFT JOIN Location_Mst L ON E.fk_locid = L.pk_locid
        LEFT JOIN Department_Mst D ON E.fk_deptid = D.pk_deptid
        LEFT JOIN SAL_Designation_Mst DS ON E.fk_desgid = DS.pk_desgid
        LEFT JOIN SAL_SalaryType_Mst ST ON E.fk_saltypeid = ST.pk_saltypeid
        {where}
        ORDER BY {sort_col}
        OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY
    ''', params)

    edit_id = request.args.get('edit_id')
    edit_data = None
    if edit_id:
        edit_data = EmployeeModel.get_employee_full_details(edit_id)

    lookups = EmployeeModel.get_full_lookups()
    lookups['quarters'] = DB.fetch_all("SELECT pk_quarterid as id, quarterno + ' || ' + (SELECT TOP 1 cityname FROM SAL_City_Mst WHERE pk_cityid=fk_cityid) as name FROM SAL_Quarter_Mst ORDER BY quarterno")
    lookups['genders'] = [{'id': 'M', 'name': 'MALE'}, {'id': 'F', 'name': 'FEMALE'}, {'id': 'O', 'name': 'OTHER'}]

    base_args = {k: v for k, v in filters.items() if v}
    prev_url = url_for('establishment.employee_demographic_details', page=page - 1, **base_args) if page > 1 else None
    next_url = url_for('establishment.employee_demographic_details', page=page + 1, **base_args) if page < total_pages else None

    page_links = []
    if total_pages > 1:
        start_page = max(1, page - 2)
        end_page = min(total_pages, start_page + 4)
        if end_page == total_pages:
            start_page = max(1, end_page - 4)
        for p in range(start_page, end_page + 1):
            page_links.append({'page': p, 'url': url_for('establishment.employee_demographic_details', page=p, **base_args), 'active': (p == page)})

    for e in employees:
        e['edit_url'] = url_for('establishment.employee_demographic_details', edit_id=e['id'], page=page, **base_args)

    return render_template('establishment/employee_demographic_details.html', edit_data=edit_data, lookups=lookups, perm=perm,
                          employees=employees, filters=filters, page=page, total_pages=total_pages, total_count=total_count,
                          prev_url=prev_url, next_url=next_url, page_links=page_links)

@establishment_bp.route('/designation_category', methods=['GET', 'POST'])
@permission_required('Designation Category Master')
def designation_category_master():
    perm = session.get('permissions', {}).get('Designation Category Master', {})
    user_id = session.get('user_id')
    edit_id = request.args.get('edit_id')
    delete_id = request.args.get('delete_id')

    if delete_id and perm.get('AllowDelete'):
        try:
            DesignationCategoryModel.delete(delete_id)
            flash('Record Deleted Successfully !', 'success')
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('establishment.designation_category_master'))

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'RESET':
            return redirect(url_for('establishment.designation_category_master'))
        
        data = {
            'description': request.form.get('description', '').strip(),
            'order_no': request.form.get('order_no', '').strip(),
            'using_recruitment': 1 if request.form.get('using_recruitment') else 0
        }

        try:
            if edit_id:
                DesignationCategoryModel.update(edit_id, data, user_id)
                flash('Record Updated Successfully !', 'success')
            else:
                DesignationCategoryModel.save(data, user_id)
                flash('Record Saved Successfully !', 'success')
            return redirect(url_for('establishment.designation_category_master'))
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')

    edit_data = None
    if edit_id:
        edit_data = DesignationCategoryModel.get_by_id(edit_id)

    categories = DesignationCategoryModel.get_all()
    return render_template('establishment/designation_category.html', categories=categories, edit_data=edit_data, perm=perm)

@establishment_bp.route('/earned_leave_details', methods=['GET', 'POST'])
@permission_required('Earned Leave Details')
def earned_leave_details():
    user_id = session.get('user_id')
    loc_id = session.get('selected_loc')
    perm = NavModel.check_permission(user_id, loc_id, 'Earned Leave Details')
    emp_id = request.args.get('emp_id')

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'RESET':
            return redirect(url_for('establishment.earned_leave_details'))
        
        target_emp_id = request.form.get('target_emp_id')
        if not target_emp_id:
            flash('Please select an employee first.', 'warning')
            return redirect(url_for('establishment.earned_leave_details'))

        # Basic save logic (actual calculation logic might be complex)
        data = {
            'emp_id': target_emp_id,
            'duty_from': request.form.get('duty_from'),
            'duty_to': request.form.get('duty_to'),
            'total_days': request.form.get('total_days') or 0,
            'duty_days': request.form.get('duty_days') or 0,
            'el_earned': request.form.get('el_earned') or 0,
            'el_total': request.form.get('el_total') or 0,
            'leave_from': request.form.get('leave_from'),
            'leave_to': request.form.get('leave_to'),
            'leave_days': request.form.get('leave_days') or 0,
            'el_balance': request.form.get('el_balance') or 0
        }

        try:
            EarnedLeaveModel.save(data, user_id)
            flash('Record Saved Successfully !', 'success')
            return redirect(url_for('establishment.earned_leave_details', emp_id=target_emp_id))
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')

    employee_info = None
    el_list = []
    if emp_id:
        employee_info = EmployeeModel.get_employee_full_details(emp_id)
        el_list = EarnedLeaveModel.get_employee_el_details(emp_id)

    from app.models import LeaveModel
    leave_types = LeaveModel.get_leave_types()

    return render_template('establishment/earned_leave_details.html', 
                          employee_info=employee_info, el_list=el_list, 
                          leave_types=leave_types, perm=perm, emp_id=emp_id)

@establishment_bp.route('/employee_dept_exam_details', methods=['GET', 'POST'])
@permission_required('Employee Departmental Exam Details')
def employee_dept_exam_details():
    user_id = session.get('user_id')
    loc_id = session.get('selected_loc')
    perm = NavModel.check_permission(user_id, loc_id, 'Employee Departmental Exam Details')
    emp_id = request.args.get('emp_id')
    edit_id = request.args.get('edit_id')
    delete_id = request.args.get('delete_id')

    if delete_id and perm.get('AllowDelete'):
        try:
            DeptExamModel.delete(delete_id)
            flash('Record Deleted Successfully !', 'success')
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('establishment.employee_dept_exam_details', emp_id=emp_id))

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'RESET':
            return redirect(url_for('establishment.employee_dept_exam_details'))
        
        target_emp_id = request.form.get('target_emp_id')
        if not target_emp_id:
            flash('Please select an employee first.', 'warning')
            return redirect(url_for('establishment.employee_dept_exam_details'))

        data = {
            'emp_id': target_emp_id,
            'type_id': request.form.get('type_id'),
            'examname': request.form.get('examname', '').strip(),
            'rollno': request.form.get('rollno', '').strip(),
            'passingyear': request.form.get('passingyear'),
            'subject': request.form.get('subject', '').strip(),
            'orderno': request.form.get('orderno', '').strip(),
            'remarks': request.form.get('remarks', '').strip()
        }

        try:
            if edit_id:
                DeptExamModel.update(edit_id, data, user_id)
                flash('Record Updated Successfully !', 'success')
            else:
                DeptExamModel.save(data, user_id)
                flash('Record Saved Successfully !', 'success')
            return redirect(url_for('establishment.employee_dept_exam_details', emp_id=target_emp_id))
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')

    employee_info = None
    exams = []
    if emp_id:
        employee_info = EmployeeModel.get_employee_full_details(emp_id)
        exams = DeptExamModel.get_employee_exams(emp_id)

    edit_data = None
    if edit_id:
        edit_data = DeptExamModel.get_exam_by_id(edit_id)

    lookups = {
        'exam_types': DeptExamModel.get_exam_types()
    }

    return render_template('establishment/employee_dept_exam_details.html', 
                          employee_info=employee_info, exams=exams, 
                          edit_data=edit_data, lookups=lookups, perm=perm, emp_id=emp_id)

@establishment_bp.route('/disciplinary_action_details', methods=['GET', 'POST'])
@permission_required('Disciplinary Action/Reward Details')
def disciplinary_action_details():
    user_id = session.get('user_id')
    loc_id = session.get('selected_loc')
    perm = NavModel.check_permission(user_id, loc_id, 'Disciplinary Action/Reward Details')
    emp_id = request.args.get('emp_id')
    delete_id = request.args.get('delete_id')

    if delete_id and perm.get('AllowDelete'):
        try:
            DisciplinaryModel.delete(delete_id)
            flash('Record Deleted Successfully !', 'success')
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('establishment.disciplinary_action_details', emp_id=emp_id))

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'RESET':
            return redirect(url_for('establishment.disciplinary_action_details'))
        
        target_emp_id = request.form.get('target_emp_id')
        if not target_emp_id:
            flash('Please select an employee first.', 'warning')
            return redirect(url_for('establishment.disciplinary_action_details'))

        data = {
            'emp_id': target_emp_id,
            'type': request.form.get('type', '').strip(),
            'description': request.form.get('description', '').strip(),
            'date': request.form.get('date'),
            'authority': request.form.get('authority', '').strip(),
            'remarks': request.form.get('remarks', '').strip()
        }

        try:
            DisciplinaryModel.save(data, user_id)
            flash('Record Saved Successfully !', 'success')
            return redirect(url_for('establishment.disciplinary_action_details', emp_id=target_emp_id))
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')

    employee_info = None
    records = []
    if emp_id:
        employee_info = EmployeeModel.get_employee_full_details(emp_id)
        records = DisciplinaryModel.get_employee_records(emp_id)

    return render_template('establishment/disciplinary_action_details.html', 
                          employee_info=employee_info, records=records, 
                          perm=perm, emp_id=emp_id)

