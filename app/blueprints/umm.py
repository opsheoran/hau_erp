from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from app.db import DB
from app.models import NavModel
from functools import wraps
from datetime import datetime
from werkzeug.utils import secure_filename
from app.utils import get_pagination, to_int
import hashlib

umm_bp = Blueprint('umm', __name__)

UMM_MENU_CONFIG = {
    'Create Master': {
        'Masters': {
            'Create Master': [
                'District Master', 'DDO Master', 'Office Type Master', 'Location Master',
                'Section Master', 'Department Master', 'Class Master', 'Grade Master',
                'Designation Master', 'Religion Master', 'DDO Location Mapping',
                'Country State District City Master', 'Designation Specialization Master',
                'Controlling Office Master'
            ]
        }
    },
    'Manage Users': {
        'User Management': {
            'Manage Users': [
                'User Master', 'Reset Password', 'Manage Page Rights', 'Page Type Master',
                'Role Page Rights', 'Role Level Master', 'Role Master', 'PageType-Role Link',
                'Module Master', 'Web Page Master', 'User Login Management', 'Module Rights Detail',
                'Fetch Password', 'Multiple Users Page Rights'
            ]
        }
    },
    'View User Logs': {
        'Logs': {
            'View User Logs': ['User Wise Log', 'Send Message']
        }
    }
}

@umm_bp.before_request
def ensure_module():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    session['current_module_id'] = 30

def permission_required(page_caption):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('auth.login'))
            user_id = session['user_id']
            loc_id = session.get('selected_loc')
            perm = NavModel.check_permission(user_id, loc_id, page_caption)
            if not perm or not perm.get('AllowView'):
                return redirect(url_for('main.index'))
            if request.method == 'POST':
                action = (request.form.get('action') or '').strip().upper()
                write_actions = {'SAVE', 'SUBMIT', 'ADD', 'CREATE', 'INSERT', 'UPDATE', 'EDIT', 'DELETE', 'REMOVE', 'RESET', 'UPLOAD'}
                if action in write_actions:
                    if action in {'DELETE', 'REMOVE'} and not perm.get('AllowDelete'):
                        flash('You do not have Delete permission for this page.', 'danger')
                        return redirect(url_for('main.index'))
                    if action in {'ADD', 'CREATE', 'INSERT'} and not perm.get('AllowAdd'):
                        flash('You do not have Add permission for this page.', 'danger')
                        return redirect(url_for('main.index'))
                    if action in {'SAVE', 'SUBMIT', 'UPDATE', 'EDIT', 'RESET', 'UPLOAD'} and not (perm.get('AllowAdd') or perm.get('AllowUpdate')):
                        flash('You do not have permission to perform this action.', 'danger')
                        return redirect(url_for('main.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# --- DDO MASTER ---
@umm_bp.route('/ddo_master', methods=['GET', 'POST'])
@permission_required('DDO Master')
def ddo_master():
    user_id = session['user_id']; loc_id = session.get('selected_loc'); perm = NavModel.check_permission(user_id, loc_id, 'DDO Master')
    if request.method == 'POST':
        action = (request.form.get('action') or '').strip().upper()
        if action == 'DELETE':
            delete_id = request.form.get('delete_id')
            try:
                DB.execute("DELETE FROM DDO_Mst WHERE pk_ddoid = ?", [delete_id])
                flash("DDO deleted successfully.", "success")
            except Exception as e: flash(f"Error: {str(e)}", "danger")
            return redirect(url_for('umm.ddo_master'))
        
        edit_id = request.form.get('edit_id')
        code = request.form.get('code'); desc = request.form.get('description'); dated = request.form.get('dated')
        alias = request.form.get('alias'); tan = request.form.get('tan'); dist_id = request.form.get('district_id')
        cont_off_id = request.form.get('controlling_id'); officer_id = request.form.get('officer_id'); remarks = request.form.get('remarks')
        
        params = [code, desc, dated, alias, tan, dist_id, cont_off_id, officer_id, remarks]
        try:
            if edit_id:
                DB.execute("""
                    UPDATE DDO_Mst SET Code=?, Description=?, Dated=?, ddoAlias=?, TANNo=?, 
                           fk_districid=?, fk_Controllid=?, fk_DDOOfficerID=?, Remarks=? 
                    WHERE pk_ddoid=?
                """, params + [edit_id])
                flash("Record Updated Successfully !", "success")
            else:
                DB.execute("""
                    INSERT INTO DDO_Mst (Code, Description, Dated, ddoAlias, TANNo, 
                           fk_districid, fk_Controllid, fk_DDOOfficerID, Remarks) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, params)
                flash("Record Saved Successfully !", "success")
        except Exception as e: flash(f"Error: {str(e)}", "danger")
        return redirect(url_for('umm.ddo_master'))
    
    page = to_int(request.args.get('page', 1)); pagination, sql_limit = get_pagination("DDO_Mst D", page, order_by="ORDER BY D.Description")
    ddos = DB.fetch_all(f"""
        SELECT D.pk_ddoid as id, D.Code, D.Description, DIST.Description as District, 
               CO.description as ContOffice, D.ddoAlias
        FROM DDO_Mst D
        LEFT JOIN distric_mst DIST ON D.fk_districid = DIST.pk_districid
        LEFT JOIN Sal_ControllingOffice_Mst CO ON D.fk_Controllid = CO.pk_Controllid
        {sql_limit}
    """)
    districts = DB.fetch_all("SELECT pk_districid as id, Description as name FROM distric_mst ORDER BY Description")
    cont_offices = DB.fetch_all("SELECT pk_Controllid as id, description as name FROM Sal_ControllingOffice_Mst ORDER BY description")
    
    edit_data = None; edit_id = request.args.get('edit_id')
    if edit_id:
        edit_data = DB.fetch_one("""
            SELECT D.*, E.empname as officer_name 
            FROM DDO_Mst D 
            LEFT JOIN SAL_Employee_Mst E ON D.fk_DDOOfficerID = E.pk_empid 
            WHERE D.pk_ddoid = ?
        """, [edit_id])
        
    return render_template('umm/ddo_master.html', ddos=ddos, districts=districts, cont_offices=cont_offices, edit_data=edit_data, perm=perm, pagination=pagination)

# --- OFFICE TYPE MASTER ---
@umm_bp.route('/office_type_master', methods=['GET', 'POST'])
@permission_required('Office Type Master')
def office_type_master():
    user_id = session['user_id']; loc_id = session.get('selected_loc'); perm = NavModel.check_permission(user_id, loc_id, 'Office Type Master')
    if request.method == 'POST':
        action = (request.form.get('action') or '').strip().upper()
        if action == 'DELETE':
            delete_id = request.form.get('delete_id')
            try:
                DB.execute("DELETE FROM OfficeTypeMaster WHERE OfficeTypeID = ?", [delete_id])
                flash("Office Type deleted successfully.", "success")
            except Exception as e: flash(f"Error: {str(e)}", "danger")
            return redirect(url_for('umm.office_type_master'))
        
        name = request.form.get('name'); code = request.form.get('code'); edit_id = request.form.get('edit_id')
        try:
            if edit_id:
                DB.execute("UPDATE OfficeTypeMaster SET OfficeName = ?, code = ? WHERE OfficeTypeID = ?", [name, code, edit_id])
                flash("Record Updated Successfully !", "success")
            else:
                DB.execute("INSERT INTO OfficeTypeMaster (OfficeName, code) VALUES (?, ?)", [name, code])
                flash("Record Saved Successfully !", "success")
        except Exception as e: flash(f"Error: {str(e)}", "danger")
        return redirect(url_for('umm.office_type_master'))
    
    page = to_int(request.args.get('page', 1)); pagination, sql_limit = get_pagination("OfficeTypeMaster", page, order_by="ORDER BY OfficeName")
    types = DB.fetch_all(f"SELECT OfficeTypeID as id, OfficeName as name, code FROM OfficeTypeMaster {sql_limit}")
    edit_data = None; edit_id = request.args.get('edit_id')
    if edit_id: edit_data = DB.fetch_one("SELECT OfficeTypeID as id, OfficeName as name, code FROM OfficeTypeMaster WHERE OfficeTypeID = ?", [edit_id])
    return render_template('umm/office_type_master.html', types=types, edit_data=edit_data, perm=perm, pagination=pagination)

# --- SECTION MASTER ---
@umm_bp.route('/section_master', methods=['GET', 'POST'])
@permission_required('Section Master')
def section_master():
    user_id = session['user_id']; loc_id = session.get('selected_loc'); perm = NavModel.check_permission(user_id, loc_id, 'Section Master')
    if request.method == 'POST':
        action = (request.form.get('action') or '').strip().upper()
        if action == 'DELETE':
            delete_id = request.form.get('delete_id')
            try:
                DB.execute("DELETE FROM SAL_Section_Mst WHERE pk_sectionid = ?", [delete_id])
                flash("Section deleted successfully.", "success")
            except Exception as e: flash(f"Error: {str(e)}", "danger")
            return redirect(url_for('umm.section_master'))
        
        edit_id = request.form.get('edit_id')
        dept_id = request.form.get('dept_id')
        description = request.form.get('description')
        sod_id = request.form.get('sod_id')
        email = request.form.get('email')
        alias = request.form.get('alias')
        
        try:
            if edit_id:
                DB.execute("""
                    UPDATE SAL_Section_Mst 
                    SET description = ?, fk_deptid = ?, SOD_Id = ?, Email_Id = ?, SectionAlias = ? 
                    WHERE pk_sectionid = ?
                """, [description, dept_id, sod_id, email, alias, edit_id])
                flash("Record Updated Successfully !", "success")
            else:
                new_id = f"SEC-{to_int(DB.fetch_scalar('SELECT COUNT(*) FROM SAL_Section_Mst')) + 1}"
                DB.execute("""
                    INSERT INTO SAL_Section_Mst (pk_sectionid, description, fk_deptid, SOD_Id, Email_Id, SectionAlias) 
                    VALUES (?, ?, ?, ?, ?, ?)
                """, [new_id, description, dept_id, sod_id, email, alias])
                flash("Record Saved Successfully !", "success")
        except Exception as e: flash(f"Error: {str(e)}", "danger")
        return redirect(url_for('umm.section_master'))
    
    page = to_int(request.args.get('page', 1)); pagination, sql_limit = get_pagination("SAL_Section_Mst S", page, order_by="ORDER BY S.description")
    sections = DB.fetch_all(f"""
        SELECT S.pk_sectionid as id, S.description, D.description as dept_name, 
               E.empcode + ' ~ ' + E.empname as officer_name, S.SectionAlias as alias
        FROM SAL_Section_Mst S
        LEFT JOIN Department_Mst D ON S.fk_deptid = D.pk_deptid
        LEFT JOIN SAL_Employee_Mst E ON S.SOD_Id = E.pk_empid
        {sql_limit}
    """)
    departments = DB.fetch_all("SELECT pk_deptid as id, description as name FROM Department_Mst ORDER BY description")
    
    edit_data = None; edit_id = request.args.get('edit_id')
    if edit_id:
        edit_data = DB.fetch_one("""
            SELECT S.*, E.empcode + ' ~ ' + E.empname as officer_name 
            FROM SAL_Section_Mst S 
            LEFT JOIN SAL_Employee_Mst E ON S.SOD_Id = E.pk_empid 
            WHERE S.pk_sectionid = ?
        """, [edit_id])
        
    return render_template('umm/section_master.html', sections=sections, departments=departments, edit_data=edit_data, perm=perm, pagination=pagination)

# --- GRADE MASTER ---
@umm_bp.route('/grade_master', methods=['GET', 'POST'])
@permission_required('Grade Master')
def grade_master():
    user_id = session['user_id']; loc_id = session.get('selected_loc'); perm = NavModel.check_permission(user_id, loc_id, 'Grade Master')
    
    if request.method == 'POST':
        action = (request.form.get('action') or '').strip().upper()
        edit_id = request.form.get('edit_id')
        
        if action == 'DELETE':
            delete_id = request.form.get('delete_id')
            try:
                DB.execute("DELETE FROM SAL_Grade_Mst WHERE pk_gradeid = ?", [delete_id])
                DB.execute("DELETE FROM Sal_Grade_Dtl WHERE fk_gradeid = ?", [delete_id])
                flash("Grade deleted successfully.", "success")
            except Exception as e: flash(f"Error: {str(e)}", "danger")
            return redirect(url_for('umm.grade_master'))
        
        if action == 'ADD_DETAIL':
            if not edit_id:
                flash("Please save the Grade Master first before adding details.", "warning")
                return redirect(url_for('umm.grade_master'))
            
            detail_id = request.form.get('detail_id')
            g1 = request.form.get('g1') or 0
            g2 = request.form.get('g2') or 0
            g3 = request.form.get('g3') or 0
            g4 = request.form.get('g4') or 0
            g5 = request.form.get('g5') or 0
            g6 = request.form.get('g6') or 0
            order = request.form.get('order') or 1
            
            try:
                if detail_id:
                    DB.execute("""
                        UPDATE Sal_Grade_Dtl 
                        SET G1amount=?, G2amount=?, G3amount=?, G4amount=?, G5amount=?, G6amount=?, Gorder=?
                        WHERE pk_gdtlid=?
                    """, [g1, g2, g3, g4, g5, g6, order, detail_id])
                    flash("Detail Updated Successfully !", "success")
                else:
                    DB.execute("""
                        INSERT INTO Sal_Grade_Dtl (fk_gradeid, G1amount, G2amount, G3amount, G4amount, G5amount, G6amount, Gorder)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, [edit_id, g1, g2, g3, g4, g5, g6, order])
                    flash("Detail Added Successfully !", "success")
            except Exception as e: flash(f"Error: {str(e)}", "danger")
            return redirect(url_for('umm.grade_master', edit_id=edit_id))

        if action == 'DELETE_DETAIL':
            detail_id = request.form.get('detail_id')
            try:
                DB.execute("DELETE FROM Sal_Grade_Dtl WHERE pk_gdtlid = ?", [detail_id])
                flash("Detail Deleted Successfully !", "success")
            except Exception as e: flash(f"Error: {str(e)}", "danger")
            return redirect(url_for('umm.grade_master', edit_id=edit_id))

        # Main Save/Update
        gname = request.form.get('gname')
        gpay = request.form.get('gpay')
        inc_type = request.form.get('inc_type')
        gcode = request.form.get('gcode')
        remarks = request.form.get('remarks')
        
        try:
            if edit_id:
                DB.execute("""
                    UPDATE SAL_Grade_Mst 
                    SET gradename = ?, gradepay = ?, inctype = ?, gradecode = ?, remarks = ?
                    WHERE pk_gradeid = ?
                """, [gname, gpay, inc_type, gcode, remarks, edit_id])
                flash("Record Updated Successfully !", "success")
            else:
                new_id = f"GR-{to_int(DB.fetch_scalar('SELECT COUNT(*) FROM SAL_Grade_Mst')) + 1}"
                DB.execute("""
                    INSERT INTO SAL_Grade_Mst (pk_gradeid, gradename, gradepay, inctype, gradecode, remarks) 
                    VALUES (?, ?, ?, ?, ?, ?)
                """, [new_id, gname, gpay, inc_type, gcode, remarks])
                flash("Record Saved Successfully !", "success")
                edit_id = new_id
        except Exception as e: flash(f"Error: {str(e)}", "danger")
        return redirect(url_for('umm.grade_master', edit_id=edit_id))
    
    page = to_int(request.args.get('page', 1)); pagination, sql_limit = get_pagination("SAL_Grade_Mst", page, order_by="ORDER BY gradename")
    grades = DB.fetch_all(f"SELECT pk_gradeid as id, gradename, gradedetails, gradepay, inctype FROM SAL_Grade_Mst {sql_limit}")
    
    edit_data = None; details = []; edit_id = request.args.get('edit_id')
    if edit_id:
        edit_data = DB.fetch_one("SELECT * FROM SAL_Grade_Mst WHERE pk_gradeid = ?", [edit_id])
        details = DB.fetch_all("SELECT * FROM Sal_Grade_Dtl WHERE fk_gradeid = ? ORDER BY Gorder", [edit_id])
        
    return render_template('umm/grade_master.html', grades=grades, edit_data=edit_data, details=details, perm=perm, pagination=pagination)
# --- DESIGNATION MASTER ---
@umm_bp.route('/designation_master', methods=['GET', 'POST'])
@permission_required('Designation Master')
def designation_master():
    user_id = session['user_id']; loc_id = session.get('selected_loc'); perm = NavModel.check_permission(user_id, loc_id, 'Designation Master')
    if request.method == 'POST':
        action = (request.form.get('action') or '').strip().upper()
        if action == 'DELETE':
            delete_id = request.form.get('delete_id')
            try:
                DB.execute("DELETE FROM SAL_Designation_Mst WHERE pk_desgid = ?", [delete_id])
                flash("Designation deleted successfully.", "success")
            except Exception as e: flash(f"Error: {str(e)}", "danger")
            return redirect(url_for('umm.designation_master'))
        
        edit_id = request.form.get('edit_id')
        name = request.form.get('name')
        grade_id = request.form.get('grade_id')
        cat_id = request.form.get('cat_id')
        class_id = request.form.get('class_id')
        retire_age = request.form.get('retire_age') or 60
        sen_level = request.form.get('sen_level') or 1
        qualification = request.form.get('qualification')
        remarks = request.form.get('remarks')
        is_auth = 1 if request.form.get('is_auth') else 0
        next_desg = request.form.get('next_desg') or None
        app_auth = request.form.get('app_auth') or ''
        
        # Determine if teaching based on category (logic from live DB seems to link it)
        is_teaching = 1 if cat_id == '9' else 0
        
        params = [name, grade_id, cat_id, class_id, retire_age, sen_level, qualification, remarks, is_auth, next_desg, app_auth, is_teaching]
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
        return redirect(url_for('umm.designation_master'))
    
    page = to_int(request.args.get('page', 1)); pagination, sql_limit = get_pagination("SAL_Designation_Mst D", page, order_by="ORDER BY D.designation")
    designations = DB.fetch_all(f"""
        SELECT D.pk_desgid as id, D.designation as name, C.description as cat_name, 
               CL.classname as class_name, G.gradedetails as grade_name, 
               D.senioritylevel, D.retireage
        FROM SAL_Designation_Mst D
        LEFT JOIN SAL_DesignationCat_Mst C ON D.fk_desgcat = C.pk_desgcat
        LEFT JOIN SAL_Class_Mst CL ON D.fk_classId = CL.pk_classid
        LEFT JOIN SAL_Grade_Mst G ON D.fk_gradeid = G.pk_gradeid
        {sql_limit}
    """)
    
    grades = DB.fetch_all("SELECT pk_gradeid as id, gradedetails as name, gradepay FROM SAL_Grade_Mst ORDER BY gradedetails")
    categories = DB.fetch_all("SELECT pk_desgcat as id, description as name FROM SAL_DesignationCat_Mst ORDER BY OrderNo")
    classes = DB.fetch_all("SELECT pk_classid as id, classname as name FROM SAL_Class_Mst ORDER BY classname")
    all_desgs = DB.fetch_all("SELECT pk_desgid as id, designation as name FROM SAL_Designation_Mst ORDER BY designation")
    
    edit_data = None; edit_id = request.args.get('edit_id')
    if edit_id:
        edit_data = DB.fetch_one("SELECT * FROM SAL_Designation_Mst WHERE pk_desgid = ?", [edit_id])
        
    return render_template('umm/designation_master.html', 
                           designations=designations, grades=grades, categories=categories, 
                           classes=classes, all_desgs=all_desgs, edit_data=edit_data, 
                           perm=perm, pagination=pagination)

# --- CONTROLLING OFFICE MASTER ---
@umm_bp.route('/controlling_office_master', methods=['GET', 'POST'])
@permission_required('Controlling Office Master')
def controlling_office_master():
    user_id = session['user_id']; loc_id = session.get('selected_loc'); perm = NavModel.check_permission(user_id, loc_id, 'Controlling Office Master')
    emp_search_results = []
    
    if request.method == 'POST':
        action = (request.form.get('action') or '').strip().upper()
        
        if action == 'RESET':
            return redirect(url_for('umm.controlling_office_master'))
            
        if action == 'SEARCH_EMP':
            # Employee search logic for the popup/modal
            e_code = (request.form.get('s_emp_code') or '').strip()
            e_name = (request.form.get('s_emp_name') or '').strip()
            where_e = ["1=1"]
            params_e = []
            if e_code: where_e.append("empcode LIKE ?"); params_e.append(f"%{e_code}%")
            if e_name: where_e.append("empname LIKE ?"); params_e.append(f"%{e_name}%")
            emp_search_results = DB.fetch_all(f"SELECT TOP 20 pk_empid, empcode, empname FROM SAL_Employee_Mst WHERE {' AND '.join(where_e)}", params_e)
            # We'll need to return this to the template to show the results
        
        elif action == 'DELETE':
            if not perm.get('AllowDelete'):
                flash("You do not have permission to delete.", "danger")
                return redirect(url_for('umm.controlling_office_master'))
            delete_id = request.form.get('delete_id')
            try:
                DB.execute("DELETE FROM Sal_ControllingOffice_Mst WHERE pk_Controllid = ?", [delete_id])
                flash("Controlling Office deleted successfully.", "success")
            except Exception as e: flash(f"Error: {str(e)}", "danger")
            return redirect(url_for('umm.controlling_office_master'))
        
        elif action == 'SAVE' or action == 'UPDATE':
            name = request.form.get('name')
            officer_id = request.form.get('officer_id')
            email = request.form.get('email')
            alias = request.form.get('alias')
            edit_id = request.form.get('edit_id')
            
            if edit_id and not perm.get('AllowUpdate'):
                flash("You do not have permission to update.", "danger")
                return redirect(url_for('umm.controlling_office_master'))
            if not edit_id and not perm.get('AllowAdd'):
                flash("You do not have permission to add.", "danger")
                return redirect(url_for('umm.controlling_office_master'))
            
            params = [name, officer_id, email, alias]
            try:
                if edit_id:
                    DB.execute("""
                        UPDATE Sal_ControllingOffice_Mst 
                        SET description = ?, ControllingOfficer_Id = ?, Email_Id = ?, Alias = ?,
                            fk_updUserID = ?, fk_updDateID = 'CO-1442'
                        WHERE pk_Controllid = ?
                    """, params + [user_id, edit_id])
                    flash("Record Updated Successfully !", "success")
                else:
                    new_id = f"CO-{to_int(DB.fetch_scalar('SELECT COUNT(*) FROM Sal_ControllingOffice_Mst')) + 1}"
                    DB.execute("""
                        INSERT INTO Sal_ControllingOffice_Mst (pk_Controllid, description, ControllingOfficer_Id, Email_Id, Alias, fk_insUserID, fk_insDateID) 
                        VALUES (?, ?, ?, ?, ?, ?, 'ab-428')
                    """, [new_id] + params + [user_id])
                    flash("Record Saved Successfully !", "success")
            except Exception as e: flash(f"Error: {str(e)}", "danger")
            return redirect(url_for('umm.controlling_office_master'))
    
    page = to_int(request.args.get('page', 1)); pagination, sql_limit = get_pagination("Sal_ControllingOffice_Mst C", page, order_by="ORDER BY C.description")
    offices = DB.fetch_all(f"""
        SELECT C.pk_Controllid as id, C.description as name, 
               E.empcode + ' ~ ' + E.empname as officer_name, C.Alias
        FROM Sal_ControllingOffice_Mst C
        LEFT JOIN SAL_Employee_Mst E ON C.ControllingOfficer_Id = E.pk_empid
        {sql_limit}
    """)
    
    edit_data = None; edit_id = request.args.get('edit_id')
    if edit_id:
        edit_data = DB.fetch_one("""
            SELECT C.pk_Controllid as id, C.description as name, C.ControllingOfficer_Id as officer_id,
                   E.empcode + ' ~ ' + E.empname as officer_text, C.Email_Id as email, C.Alias
            FROM Sal_ControllingOffice_Mst C
            LEFT JOIN SAL_Employee_Mst E ON C.ControllingOfficer_Id = E.pk_empid
            WHERE C.pk_Controllid = ?
        """, [edit_id])
        
    return render_template('umm/controlling_office_master.html', 
                           offices=offices, edit_data=edit_data, perm=perm, 
                           pagination=pagination, emp_search_results=emp_search_results)

# --- DDO LOCATION MAPPING ---
@umm_bp.route('/ddo_location_mapping', methods=['GET', 'POST'])
@permission_required('DDO Location Mapping')
def ddo_location_mapping():
    user_id = session['user_id']; loc_id = session.get('selected_loc'); perm = NavModel.check_permission(user_id, loc_id, 'DDO Location Mapping')
    
    selected_ddo = request.args.get('ddo_id') or request.form.get('ddo_id')
    
    if request.method == 'POST':
        action = (request.form.get('action') or '').strip().upper()
        if action == 'DELETE':
            delete_id = request.form.get('delete_id')
            try:
                DB.execute("DELETE FROM DDO_Loc_Mapping WHERE pk_mapid = ?", [delete_id])
                flash("Mapping deleted successfully.", "success")
            except Exception as e: flash(f"Error: {str(e)}", "danger")
            return redirect(url_for('umm.ddo_location_mapping'))
        
        edit_id = request.form.get('edit_id'); ddo_id = request.form.get('ddo_id'); loc_id_target = request.form.get('loc_id')
        try:
            if edit_id:
                DB.execute("UPDATE DDO_Loc_Mapping SET fk_ddoid = ?, fk_locid = ? WHERE pk_mapid = ?", [ddo_id, loc_id_target, edit_id])
                flash("Record Updated Successfully !", "success")
            else:
                existing = DB.fetch_one("SELECT pk_mapid FROM DDO_Loc_Mapping WHERE fk_ddoid = ? AND fk_locid = ?", [ddo_id, loc_id_target])
                if existing: flash("This mapping already exists.", "warning")
                else:
                    new_id = f"DM-{to_int(DB.fetch_scalar('SELECT COUNT(*) FROM DDO_Loc_Mapping')) + 1}"
                    DB.execute("INSERT INTO DDO_Loc_Mapping (pk_mapid, fk_ddoid, fk_locid) VALUES (?, ?, ?)", [new_id, ddo_id, loc_id_target])
                    flash("Record Saved Successfully !", "success")
        except Exception as e: flash(f"Error: {str(e)}", "danger")
        return redirect(url_for('umm.ddo_location_mapping', ddo_id=ddo_id))
    
    # Search + Pagination
    s_type = request.args.get('s_type', '--Select--')
    s_val = (request.args.get('s_val') or '').strip()
    
    where = ["1=1"]
    params = []
    
    # Priority 1: Filter by selected DDO (onchange behavior)
    if selected_ddo:
        where.append("M.fk_ddoid = ?")
        params.append(selected_ddo)
    # Priority 2: Manual search filters
    elif s_val and s_type != '--Select--':
        if s_type == 'DDOName':
            where.append("D.Description LIKE ?")
            params.append(f"%{s_val}%")
        elif s_type == 'LocName':
            where.append("L.locname LIKE ?")
            params.append(f"%{s_val}%")

    page = to_int(request.args.get('page', 1)); 
    pagination, sql_limit = get_pagination("DDO_Loc_Mapping M LEFT JOIN DDO_Mst D ON M.fk_ddoid = D.pk_ddoid LEFT JOIN Location_Mst L ON M.fk_locid = L.pk_locid", 
                                           page, where=" WHERE "+" AND ".join(where), params=params, order_by="ORDER BY D.Description, L.locname")
    
    mappings = DB.fetch_all(f"""
        SELECT M.pk_mapid as id, D.Description as ddo, L.locname as location
        FROM DDO_Loc_Mapping M
        LEFT JOIN DDO_Mst D ON M.fk_ddoid = D.pk_ddoid
        LEFT JOIN Location_Mst L ON M.fk_locid = L.pk_locid
        WHERE {" AND ".join(where)}
        {sql_limit}
    """, params)
    
    ddos = DB.fetch_all("SELECT pk_ddoid as id, '[ ' + Code + ' ] ' + Description as name FROM DDO_Mst ORDER BY Code ASC")
    
    # Logic for Location Dropdown (Specific 4 + DDO's primary location last)
    allowed_locations = []
    if selected_ddo:
        specific_ids = ['AX-79', 'CO-82', 'ES-70', 'NC-90']
        ddo_info = DB.fetch_one("SELECT Description FROM DDO_Mst WHERE pk_ddoid = ?", [selected_ddo])
        ddo_loc = None
        if ddo_info:
            s_name = ddo_info['Description'].replace('DDO, ', '').strip()
            ddo_loc = DB.fetch_one("SELECT TOP 1 pk_locid as id, locname as name FROM Location_Mst WHERE locname LIKE ?", [f"%{s_name}%"])
        
        exclude_id = ddo_loc['id'] if ddo_loc else ''
        allowed_locations = DB.fetch_all(f"""
            SELECT pk_locid as id, locname as name FROM Location_Mst 
            WHERE pk_locid IN ({",".join(["'"+id+"'" for id in specific_ids])}) AND pk_locid != ?
            ORDER BY CASE pk_locid WHEN 'AX-79' THEN 1 WHEN 'CO-82' THEN 2 WHEN 'ES-70' THEN 3 WHEN 'NC-90' THEN 4 END
        """, [exclude_id])
        if ddo_loc: allowed_locations.append(ddo_loc)
    
    edit_data = None; edit_id = request.args.get('edit_id')
    if edit_id: edit_data = DB.fetch_one("SELECT * FROM DDO_Loc_Mapping WHERE pk_mapid = ?", [edit_id])
    
    return render_template('umm/ddo_location_mapping.html', 
                           mappings=mappings, ddos=ddos, locations=allowed_locations, 
                           edit_data=edit_data, perm=perm, pagination=pagination,
                           s_type=s_type, s_val=s_val, selected_ddo=selected_ddo)

# --- COUNTRY STATE DISTRICT CITY MASTER ---
@umm_bp.route('/country_state_dist_city_master', methods=['GET', 'POST'])
@permission_required('Country State District City Master')
def country_state_dist_city_master():
    user_id = session['user_id']; loc_id = session.get('selected_loc'); perm = NavModel.check_permission(user_id, loc_id, 'Country State District City Master')
    if request.method == 'POST':
        action = (request.form.get('action') or '').strip().upper()
        if action == 'DELETE':
            delete_id = request.form.get('delete_id')
            try:
                DB.execute("DELETE FROM Comm_Country_State_City_Mst WHERE Pk_Id = ?", [delete_id])
                flash("Record deleted successfully.", "success")
            except Exception as e: flash(f"Error: {str(e)}", "danger")
            return redirect(url_for('umm.country_state_dist_city_master'))
        
        edit_id = request.form.get('edit_id'); fk_office_type = request.form.get('type'); description = request.form.get('name')
        parent_id = request.form.get('parent_id') or 0; nationality = request.form.get('nationality')
        is_default = 1 if request.form.get('is_default') else 0
        
        params = [fk_office_type, description, parent_id, nationality, is_default]
        try:
            if edit_id:
                DB.execute("UPDATE Comm_Country_State_City_Mst SET Fk_OfficeTypeId=?, Description=?, ParentId=?, Nationality=?, IsDefault=? WHERE Pk_Id=?", params + [edit_id])
                flash("Record Updated Successfully !", "success")
            else:
                new_id = f"CC-{to_int(DB.fetch_scalar('SELECT COUNT(*) FROM Comm_Country_State_City_Mst')) + 1}"
                DB.execute("INSERT INTO Comm_Country_State_City_Mst (Pk_Id, Fk_OfficeTypeId, Description, ParentId, Nationality, IsDefault) VALUES (?, ?, ?, ?, ?, ?)", [new_id] + params)
                flash("Record Saved Successfully !", "success")
        except Exception as e: flash(f"Error: {str(e)}", "danger")
        return redirect(url_for('umm.country_state_dist_city_master'))
    
    page = to_int(request.args.get('page', 1)); pagination, sql_limit = get_pagination("Comm_Country_State_City_Mst C", page, order_by="ORDER BY C.Description")
    entries = DB.fetch_all(f"""
        SELECT C.Pk_Id as id, C.Description as name, C.Nationality, C.IsDefault as is_default,
               P.Description as parent_name, T.OfficeName as type_name
        FROM Comm_Country_State_City_Mst C
        LEFT JOIN Comm_Country_State_City_Mst P ON C.ParentId = P.Pk_Id
        LEFT JOIN OfficeTypeMaster T ON C.Fk_OfficeTypeId = T.OfficeTypeID
        {sql_limit}
    """)
    types = DB.fetch_all("SELECT OfficeTypeID as id, OfficeName as name FROM OfficeTypeMaster ORDER BY OfficeName")
    parents = DB.fetch_all("SELECT Pk_Id as id, Description as name FROM Comm_Country_State_City_Mst ORDER BY Description")
    edit_data = None; edit_id = request.args.get('edit_id')
    if edit_id:
        edit_data = DB.fetch_one("SELECT Pk_Id as pk_countryid, Fk_OfficeTypeId as Type, Description as countryname, ParentId as parentid, Nationality, IsDefault as isdefault FROM Comm_Country_State_City_Mst WHERE Pk_Id = ?", [edit_id])
    return render_template('umm/country_state_dist_city_master.html', entries=entries, types=types, parents=parents, edit_data=edit_data, perm=perm, pagination=pagination)
# --- DISTRICT MASTER ---
@umm_bp.route('/district_master', methods=['GET', 'POST'])
@permission_required('District Master')
def district_master():
    user_id = session['user_id']
    loc_id = session.get('selected_loc')
    perm = NavModel.check_permission(user_id, loc_id, 'District Master')
    if request.method == 'POST':
        action = (request.form.get('action') or '').strip().upper()
        if action == 'DELETE':
            delete_id = request.form.get('delete_id')
            try:
                DB.execute("DELETE FROM distric_mst WHERE pk_districid = ?", [delete_id])
                flash("District deleted successfully.", "success")
            except Exception as e: flash(f"Error: {str(e)}", "danger")
            return redirect(url_for('umm.district_master'))
        code = request.form.get('code')
        name = request.form.get('name')
        edit_id = request.form.get('edit_id')
        try:
            if edit_id:
                DB.execute("UPDATE distric_mst SET District_Code = ?, Description = ? WHERE pk_districid = ?", [code, name, edit_id])
                flash("Record Updated Successfully !", "success")
            else:
                DB.execute("INSERT INTO distric_mst (District_Code, Description, fk_Stateid) VALUES (?, ?, 5)", [code, name])
                flash("Record Saved Successfully !", "success")
        except Exception as e: flash(f"Error: {str(e)}", "danger")
        return redirect(url_for('umm.district_master'))
    page = to_int(request.args.get('page', 1))
    search_type = request.args.get('search_type')
    search_val = request.args.get('search_val', '')
    where = ""
    params = []
    if search_type == 'Code' and search_val:
        where = " WHERE District_Code LIKE ?"; params.append(f'%{search_val}%')
    elif search_type == 'Description' and search_val:
        where = " WHERE Description LIKE ?"; params.append(f'%{search_val}%')
    pagination, sql_limit = get_pagination("distric_mst", page, where=where, params=params, order_by="ORDER BY Description")
    districts = DB.fetch_all(f"SELECT pk_districid as id, District_Code as code, Description as name FROM distric_mst {where} {sql_limit}", params)
    edit_data = None
    if request.args.get('edit_id'):
        edit_data = DB.fetch_one("SELECT pk_districid as id, District_Code as code, Description as name FROM distric_mst WHERE pk_districid = ?", [request.args.get('edit_id')])
    return render_template('umm/district_master.html', districts=districts, edit_data=edit_data, perm=perm, pagination=pagination)

# --- LOCATION MASTER ---
@umm_bp.route('/location_master', methods=['GET', 'POST'])
@permission_required('Location Master')
def location_master():
    user_id = session['user_id']
    loc_id = session.get('selected_loc')
    perm = NavModel.check_permission(user_id, loc_id, 'Location Master')
    if request.method == 'POST':
        action = (request.form.get('action') or '').strip().upper()
        if action == 'DELETE':
            delete_id = request.form.get('delete_id')
            try:
                DB.execute("DELETE FROM Location_Mst WHERE pk_locid = ?", [delete_id])
                flash("Location deleted successfully.", "success")
            except Exception as e: flash(f"Error: {str(e)}", "danger")
            return redirect(url_for('umm.location_master'))
        name = request.form.get('name'); office_id = request.form.get('office_id'); dist_id = request.form.get('dist_id')
        parent_id = request.form.get('parent_id') or None; alias = request.form.get('alias'); address = request.form.get('address')
        remarks = request.form.get('remarks'); holiday_loc_id = request.form.get('holiday_loc_id'); edit_id = request.form.get('edit_id')
        try:
            if edit_id:
                DB.execute("UPDATE Location_Mst SET locname = ?, fk_officeid = ?, fk_districid = ?, fk_locid = ?, locationAlias = ?, address = ?, remarks = ?, fk_holidaylocid = ? WHERE pk_locid = ?", [name, office_id, dist_id, parent_id, alias, address, remarks, holiday_loc_id, edit_id])
                flash("Record Updated Successfully !", "success")
            else:
                new_id = f"LOC-{to_int(DB.fetch_scalar('SELECT COUNT(*) FROM Location_Mst')) + 1}"
                DB.execute("INSERT INTO Location_Mst (pk_locid, locname, fk_officeid, fk_districid, fk_locid, locationAlias, address, remarks, fk_holidaylocid) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", [new_id, name, office_id, dist_id, parent_id, alias, address, remarks, holiday_loc_id])
                flash("Record Saved Successfully !", "success")
        except Exception as e: flash(f"Error: {str(e)}", "danger")
        return redirect(url_for('umm.location_master'))
    page = to_int(request.args.get('page', 1))
    pagination, sql_limit = get_pagination("Location_Mst L", page, order_by="ORDER BY L.locname")
    locations = DB.fetch_all(f"SELECT L.pk_locid as id, L.locname as name, L.locationAlias as alias, P.locname as parent_name FROM Location_Mst L LEFT JOIN Location_Mst P ON L.fk_locid = P.pk_locid {sql_limit}")
    offices = DB.fetch_all("SELECT OfficeTypeID as id, OfficeName as name FROM OfficeTypeMaster ORDER BY OfficeName")
    districts = DB.fetch_all("SELECT pk_districid as id, Description as name FROM distric_mst ORDER BY Description")
    parent_locations = DB.fetch_all("SELECT pk_locid as id, locname as name FROM Location_Mst ORDER BY locname")
    holiday_locations = DB.fetch_all("SELECT pk_holidaylocid as id, holidayloc as name FROM SAL_HolidayLocation_Mst ORDER BY holidayloc")
    edit_data = None
    if request.args.get('edit_id'):
        edit_data = DB.fetch_one("SELECT pk_locid as id, locname as name, fk_officeid as office_id, fk_districid as dist_id, fk_locid as parent_id, locationAlias as alias, address, remarks, fk_holidaylocid as holiday_loc_id FROM Location_Mst WHERE pk_locid = ?", [request.args.get('edit_id')])
    return render_template('umm/location_master.html', locations=locations, offices=offices, districts=districts, parent_locations=parent_locations, holiday_locations=holiday_locations, edit_data=edit_data, perm=perm, pagination=pagination)

# --- CLASS MASTER ---
@umm_bp.route('/class_master', methods=['GET', 'POST'])
@permission_required('Class Master')
def class_master():
    user_id = session['user_id']; loc_id = session.get('selected_loc'); perm = NavModel.check_permission(user_id, loc_id, 'Class Master')
    if request.method == 'POST':
        action = (request.form.get('action') or '').strip().upper()
        if action == 'DELETE':
            delete_id = request.form.get('delete_id')
            try:
                DB.execute("DELETE FROM SAL_Class_Mst WHERE pk_classid = ?", [delete_id])
                flash("Class deleted successfully.", "success")
            except Exception as e: flash(f"Error: {str(e)}", "danger")
            return redirect(url_for('umm.class_master'))
        name = request.form.get('name'); gad_id = request.form.get('gad_id'); is_teaching = 1 if request.form.get('is_teaching') else 0
        is_non_teaching = 1 if request.form.get('is_non_teaching') else 0; edit_id = request.form.get('edit_id')
        try:
            if edit_id:
                DB.execute("UPDATE SAL_Class_Mst SET classname = ?, fk_gadid = ?, isTeaching = ?, isOfficer = ? WHERE pk_classid = ?", [name, gad_id, is_teaching, is_non_teaching, edit_id])
                flash("Record Updated Successfully !", "success")
            else:
                new_id = f"CL-{to_int(DB.fetch_scalar('SELECT COUNT(*) FROM SAL_Class_Mst')) + 1}"
                DB.execute("INSERT INTO SAL_Class_Mst (pk_classid, classname, fk_gadid, isTeaching, isOfficer) VALUES (?, ?, ?, ?, ?)", [new_id, name, gad_id, is_teaching, is_non_teaching])
                flash("Record Saved Successfully !", "success")
        except Exception as e: flash(f"Error: {str(e)}", "danger")
        return redirect(url_for('umm.class_master'))
    classes = DB.fetch_all("SELECT C.pk_classid as id, C.classname as name, G.gadnongad as gad_name, CASE WHEN C.isTeaching = 1 THEN 'Yes' ELSE 'No' END as is_teaching, CASE WHEN C.isOfficer = 1 THEN 'Yes' ELSE 'No' END as is_non_teaching FROM SAL_Class_Mst C LEFT JOIN SAL_GadNongad_Mst G ON C.fk_gadid = G.pk_gadid ORDER BY C.classname")
    gad_list = DB.fetch_all("SELECT pk_gadid as id, gadnongad as name FROM SAL_GadNongad_Mst ORDER BY gadnongad")
    edit_data = None
    if request.args.get('edit_id'):
        edit_data = DB.fetch_one("SELECT pk_classid as id, classname as name, fk_gadid as gad_id, isTeaching as is_teaching, isOfficer as is_non_teaching FROM SAL_Class_Mst WHERE pk_classid = ?", [request.args.get('edit_id')])
    return render_template('umm/class_master.html', classes=classes, gad_list=gad_list, edit_data=edit_data, perm=perm)

# --- RELIGION MASTER ---
@umm_bp.route('/religion_master', methods=['GET', 'POST'])
@permission_required('Religion Master')
def religion_master():
    user_id = session['user_id']; loc_id = session.get('selected_loc'); perm = NavModel.check_permission(user_id, loc_id, 'Religion Master')
    if request.method == 'POST':
        action = (request.form.get('action') or '').strip().upper()
        if action == 'DELETE':
            delete_id = request.form.get('delete_id')
            try:
                DB.execute("DELETE FROM Religion_Mst WHERE pk_religionid = ?", [delete_id])
                flash("Religion deleted successfully.", "success")
            except Exception as e: flash(f"Error: {str(e)}", "danger")
            return redirect(url_for('umm.religion_master'))
        name = request.form.get('name'); edit_id = request.form.get('edit_id')
        try:
            if edit_id:
                DB.execute("UPDATE Religion_Mst SET religiontype = ? WHERE pk_religionid = ?", [name, edit_id])
                flash("Record Updated Successfully !", "success")
            else:
                new_id = f"RG-{to_int(DB.fetch_scalar('SELECT COUNT(*) FROM Religion_Mst')) + 1}"
                DB.execute("INSERT INTO Religion_Mst (pk_religionid, religiontype) VALUES (?, ?)", [new_id, name])
                flash("Record Saved Successfully !", "success")
        except Exception as e: flash(f"Error: {str(e)}", "danger")
        return redirect(url_for('umm.religion_master'))
    religions = DB.fetch_all("SELECT pk_religionid as id, religiontype as name FROM Religion_Mst ORDER BY religiontype")
    edit_data = None
    if request.args.get('edit_id'):
        edit_data = DB.fetch_one("SELECT pk_religionid as id, religiontype as name FROM Religion_Mst WHERE pk_religionid = ?", [request.args.get('edit_id')])
    return render_template('umm/religion_master.html', religions=religions, edit_data=edit_data, perm=perm)

# --- DESIGNATION SPECIALIZATION MASTER ---
@umm_bp.route('/designation_specialization_master', methods=['GET', 'POST'])
@permission_required('Designation Specialization Master')
def designation_specialization_master():
    user_id = session['user_id']; loc_id = session.get('selected_loc'); perm = NavModel.check_permission(user_id, loc_id, 'Designation Specialization Master')
    if request.method == 'POST':
        action = (request.form.get('action') or '').strip().upper()
        if action == 'RESET':
            return redirect(url_for('umm.designation_specialization_master'))
        if action == 'SEARCH':
            s_type = request.form.get('s_type')
            s_val = request.form.get('s_val')
            return redirect(url_for('umm.designation_specialization_master', s_type=s_type, s_val=s_val))
        if action == 'DELETE':
            if not perm.get('AllowDelete'):
                flash("You do not have permission to delete.", "danger")
                return redirect(url_for('umm.designation_specialization_master'))
            delete_id = request.form.get('delete_id')
            try:
                DB.execute("DELETE FROM SMS_BranchMst WHERE Pk_BranchId = ?", [delete_id])
                flash("Specialization deleted successfully.", "success")
            except Exception as e: flash(f"Error: {str(e)}", "danger")
            return redirect(url_for('umm.designation_specialization_master'))
        
        name = request.form.get('name'); edit_id = request.form.get('edit_id')
        try:
            if edit_id:
                if not perm.get('AllowUpdate'):
                    flash("You do not have permission to update.", "danger")
                    return redirect(url_for('umm.designation_specialization_master'))
                DB.execute("UPDATE SMS_BranchMst SET Branchname = ?, Remarks = ? WHERE Pk_BranchId = ?", [name, name, edit_id])
                flash("Record Updated Successfully !", "success")
            else:
                if not perm.get('AllowAdd'):
                    flash("You do not have permission to add.", "danger")
                    return redirect(url_for('umm.designation_specialization_master'))
                DB.execute("INSERT INTO SMS_BranchMst (Branchname, Remarks, Isactive) VALUES (?, ?, 1)", [name, name])
                flash("Record Saved Successfully !", "success")
        except Exception as e: flash(f"Error: {str(e)}", "danger")
        return redirect(url_for('umm.designation_specialization_master'))
    
    # Search + Pagination
    s_type = request.args.get('s_type', '--Select--')
    s_val = (request.args.get('s_val') or '').strip()
    
    where = " WHERE 1=1"
    params = []
    if s_val and s_type == 'Desig.Specialization':
        where += " AND Branchname LIKE ?"
        params.append(f"%{s_val}%")

    page = to_int(request.args.get('page', 1)); pagination, sql_limit = get_pagination("SMS_BranchMst", page, where=where, params=params, order_by="ORDER BY Branchname")
    specs = DB.fetch_all(f"SELECT Pk_BranchId as id, Branchname as name FROM SMS_BranchMst {where} {sql_limit}", params)
    
    edit_data = None; edit_id = request.args.get('edit_id')
    if edit_id:
        edit_data = DB.fetch_one("SELECT Pk_BranchId as id, Branchname as name FROM SMS_BranchMst WHERE Pk_BranchId = ?", [edit_id])
        
    return render_template('umm/designation_specialization_master.html', specs=specs, edit_data=edit_data, perm=perm, pagination=pagination, s_type=s_type, s_val=s_val)


# --- PAGE TYPE MASTER ---
@umm_bp.route('/page_type_master', methods=['GET', 'POST'])
@permission_required('Page Type Master')
def page_type_master():
    user_id = session['user_id']; loc_id = session.get('selected_loc'); perm = NavModel.check_permission(user_id, loc_id, 'Page Type Master')
    if request.method == 'POST':
        action = (request.form.get('action') or '').strip().upper()
        if action == 'DELETE':
            delete_id = request.form.get('delete_id')
            try:
                DB.execute("DELETE FROM UM_PageType_Mst WHERE pk_pagetypeId = ?", [delete_id])
                flash("Page Type deleted successfully.", "success")
            except Exception as e: flash(f"Error: {str(e)}", "danger")
            return redirect(url_for('umm.page_type_master'))
        page_type = request.form.get('page_type'); remarks = request.form.get('remarks'); edit_id = request.form.get('edit_id')
        try:
            if edit_id:
                DB.execute("UPDATE UM_PageType_Mst SET pagetypename = ?, remarks = ? WHERE pk_pagetypeId = ?", [page_type, remarks, edit_id])
                flash("Page Type updated successfully.", "success")
            else:
                DB.execute("INSERT INTO UM_PageType_Mst (pagetypename, remarks) VALUES (?, ?)", [page_type, remarks])
                flash("Page Type created successfully.", "success")
        except Exception as e: flash(f"Error: {str(e)}", "danger")
        return redirect(url_for('umm.page_type_master'))
    page = int(request.args.get('page', 1)); pagination, sql_limit = get_pagination("UM_PageType_Mst", page, order_by="ORDER BY pagetypename")
    page_types = DB.fetch_all(f"SELECT pk_pagetypeId as id, pagetypename, remarks FROM UM_PageType_Mst {sql_limit}")
    edit_data = None
    if request.args.get('edit_id'):
        edit_data = DB.fetch_one("SELECT pk_pagetypeId as id, pagetypename as pagetypename, remarks FROM UM_PageType_Mst WHERE pk_pagetypeId = ?", [request.args.get('edit_id')])
    return render_template('umm/page_type_master.html', page_types=page_types, edit_data=edit_data, perm=perm, pagination=pagination)

# --- ROLE MASTER ---
@umm_bp.route('/role_master', methods=['GET', 'POST'])
@permission_required('Role Master')
def role_master():
    user_id = session['user_id']; loc_id = session.get('selected_loc'); perm = NavModel.check_permission(user_id, loc_id, 'Role Master')
    if request.method == 'POST':
        action = (request.form.get('action') or '').strip().upper()
        if action == 'DELETE':
            delete_id = request.form.get('delete_id')
            try:
                DB.execute("DELETE FROM UM_Role_Mst WHERE pk_roleId = ?", [delete_id])
                flash("Role deleted successfully.", "success")
            except Exception as e: flash(f"Error: {str(e)}", "danger")
            return redirect(url_for('umm.role_master'))
        role_name = request.form.get('role_name'); alias = request.form.get('alias'); role_level = request.form.get('role_level'); remarks = request.form.get('remarks'); edit_id = request.form.get('edit_id')
        try:
            if edit_id:
                DB.execute("UPDATE UM_Role_Mst SET rolename = ?, mappedalias = ?, fk_rolelevelId = ?, remarks = ? WHERE pk_roleId = ?", [role_name, alias, role_level, remarks, edit_id])
                flash("Role updated successfully.", "success")
            else:
                DB.execute("INSERT INTO UM_Role_Mst (rolename, mappedalias, fk_rolelevelId, remarks) VALUES (?, ?, ?, ?)", [role_name, alias, role_level, remarks])
                flash("Role created successfully.", "success")
        except Exception as e: flash(f"Error: {str(e)}", "danger")
        return redirect(url_for('umm.role_master'))
    page = int(request.args.get('page', 1)); pagination, sql_limit = get_pagination("UM_Role_Mst R", page, order_by="ORDER BY R.rolename")
    roles = DB.fetch_all(f"SELECT R.pk_roleId as id, R.rolename, R.mappedalias as alias, L.rolelevelname as role_level, R.remarks FROM UM_Role_Mst R LEFT JOIN UM_RoleLevel_Mst L ON R.fk_rolelevelId = L.pk_rolelevelId {sql_limit}")
    role_levels = DB.fetch_all("SELECT pk_rolelevelId as id, rolelevelname as name FROM UM_RoleLevel_Mst ORDER BY pk_rolelevelId")
    edit_data = None
    if request.args.get('edit_id'):
        edit_data = DB.fetch_one("SELECT pk_roleId as id, rolename as role_name, mappedalias as alias, fk_rolelevelId as role_level, remarks FROM UM_Role_Mst WHERE pk_roleId = ?", [request.args.get('edit_id')])
    return render_template('umm/role_master.html', roles=roles, role_levels=role_levels, edit_data=edit_data, perm=perm, pagination=pagination)

# --- USER MASTER ---
@umm_bp.route('/user_master', methods=['GET', 'POST'])
@permission_required('User Master')
def user_master():
    user_id = session['user_id']; loc_id = session.get('selected_loc'); perm = NavModel.check_permission(user_id, loc_id, 'User Master')
    if request.method == 'POST':
        data = request.form; action = (data.get('action') or '').strip().upper() or 'SAVE'
        if action in {'DELETE', 'REMOVE'}:
            delete_id = data.get('delete_id')
            if delete_id:
                try:
                    DB.execute("DELETE FROM UM_Users_Mst WHERE pk_userId = ?", [delete_id])
                    flash("User deleted successfully.", "success")
                except Exception as e: flash(f"Error: {str(e)}", "danger")
            return redirect(url_for('umm.user_master'))
        if action == 'RESET': return redirect(url_for('umm.user_master'))
        edit_id = data.get('edit_id'); password_plain = (data.get('password_plain') or data.get('password') or '').strip()
        password_hash = (data.get('password_hash') or data.get('hash') or '').strip()
        if password_plain and not password_hash: password_hash = hashlib.sha1(password_plain.encode('utf-8')).hexdigest()
        if edit_id and not password_plain:
            existing = DB.fetch_one("SELECT password, Plain_text FROM UM_Users_Mst WHERE pk_userId = ?", [edit_id]) or {}
            password_hash = existing.get('password') or password_hash; password_plain = existing.get('Plain_text') or password_plain
        role_id = data.get('role'); login_id = (data.get('login_id') or '').strip(); active = 1 if data.get('active') else 0
        is_doctor = 1 if data.get('is_doctor') else 0; default_location = data.get('location'); ddo_id = data.get('ddo') or None; emp_id = data.get('emp_id') or None
        params_common = [role_id, login_id, password_hash, data.get('emp_name'), data.get('father_name'), data.get('department'), data.get('designation'), data.get('email'), active, data.get('remarks'), default_location, is_doctor, password_plain]
        try:
            if edit_id:
                try: DB.execute("UPDATE UM_Users_Mst SET fk_roleId = ?, loginname = ?, password = ?, name = ?, fathername = ?, dept = ?, desig = ?, email = ?, active = ?, remarks = ?, fk_defaultlocation = ?, Isdocstatus = ?, Plain_text = ?, fk_empId = ?, fk_ddoid = ? WHERE pk_userId = ?", params_common + [emp_id, ddo_id, edit_id])
                except Exception:
                    try: DB.execute("UPDATE UM_Users_Mst SET fk_roleId = ?, loginname = ?, password = ?, name = ?, fathername = ?, dept = ?, desig = ?, email = ?, active = ?, remarks = ?, fk_defaultlocation = ?, Isdocstatus = ?, Plain_text = ?, fk_empId = ? WHERE pk_userId = ?", params_common + [emp_id, edit_id])
                    except Exception: DB.execute("UPDATE UM_Users_Mst SET fk_roleId = ?, loginname = ?, password = ?, name = ?, fathername = ?, dept = ?, desig = ?, email = ?, active = ?, remarks = ?, fk_defaultlocation = ?, Isdocstatus = ?, Plain_text = ? WHERE pk_userId = ?", params_common + [edit_id])
                flash("User updated successfully.", "success")
            else:
                try: DB.execute("INSERT INTO UM_Users_Mst (fk_roleId, loginname, password, name, fathername, dept, desig, email, active, remarks, fk_defaultlocation, Isdocstatus, Plain_text, fk_empId, fk_ddoid, fk_insUserID, fk_insDateID) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'ab-428')", params_common + [emp_id, ddo_id, user_id])
                except Exception:
                    try: DB.execute("INSERT INTO UM_Users_Mst (fk_roleId, loginname, password, name, fathername, dept, desig, email, active, remarks, fk_defaultlocation, Isdocstatus, Plain_text, fk_empId, fk_insUserID, fk_insDateID) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'ab-428')", params_common + [emp_id, user_id])
                    except Exception: DB.execute("INSERT INTO UM_Users_Mst (fk_roleId, loginname, password, name, fathername, dept, desig, email, active, remarks, fk_defaultlocation, Isdocstatus, Plain_text, fk_insUserID, fk_insDateID) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'ab-428')", params_common + [user_id])
                flash("User created successfully.", "success")
        except Exception as e: flash(f"Error: {str(e)}", "danger")
        return redirect(url_for('umm.user_master'))
    locations = DB.fetch_all("SELECT pk_locid as id, locname as name FROM Location_Mst ORDER BY locname")
    roles = DB.fetch_all("SELECT pk_roleId as id, rolename as name FROM UM_Role_Mst ORDER BY rolename")
    ddos = DB.fetch_all("SELECT pk_ddoid as id, Description as name FROM DDO_Mst ORDER BY Description")
    s_login = (request.args.get('s_login') or '').strip(); s_name = (request.args.get('s_name') or '').strip(); s_dept = (request.args.get('s_dept') or '').strip(); s_desig = (request.args.get('s_desig') or '').strip(); s_role = (request.args.get('s_role') or '').strip(); s_active = (request.args.get('s_active') or '').strip()
    where = ["1=1"]; params = []
    if s_login: where.append("U.loginname LIKE ?"); params.append(f"%{s_login}%")
    if s_name: where.append("U.name LIKE ?"); params.append(f"%{s_name}%")
    if s_dept: where.append("U.dept LIKE ?"); params.append(f"%{s_dept}%")
    if s_desig: where.append("U.desig LIKE ?"); params.append(f"%{s_desig}%")
    if s_role and s_role.isdigit(): where.append("U.fk_roleId = ?"); params.append(s_role)
    if s_active in {'0', '1'}: where.append("U.active = ?"); params.append(int(s_active))
    page = to_int(request.args.get('page') or 1) or 1; per_page = 10; total = DB.fetch_scalar(f"SELECT COUNT(*) FROM UM_Users_Mst U WHERE {' AND '.join(where)}", params)
    pagination, sql_limit = get_pagination("UM_Users_Mst U", page, where=" WHERE "+" AND ".join(where), params=params, order_by="ORDER BY U.loginname")
    users = DB.fetch_all(f"SELECT U.pk_userId as id, U.loginname, U.name, U.dept as department, U.desig as designation, R.rolename as role, CASE WHEN U.active = 1 THEN 'Yes' ELSE 'No' END as active FROM UM_Users_Mst U LEFT JOIN UM_Role_Mst R ON R.pk_roleId = U.fk_roleId WHERE {' AND '.join(where)} {sql_limit}", params)
    edit_data = None; edit_id = request.args.get('edit_id')
    if edit_id:
        try: edit_data = DB.fetch_one("SELECT pk_userId as id, loginname as login_id, Plain_text as password, fk_roleId as role, fk_defaultlocation as location, active, name as emp_name, fathername as father_name, dept as department, desig as designation, email, remarks, Isdocstatus as is_doctor, fk_empId as emp_id, fk_ddoid as ddo FROM UM_Users_Mst WHERE pk_userId = ?", [edit_id])
        except Exception: edit_data = DB.fetch_one("SELECT pk_userId as id, loginname as login_id, Plain_text as password, fk_roleId as role, fk_defaultlocation as location, active, name as emp_name, fathername as father_name, dept as department, desig as designation, email, remarks, Isdocstatus as is_doctor FROM UM_Users_Mst WHERE pk_userId = ?", [edit_id])
    return render_template('umm/user_master.html', locations=locations, roles=roles, ddos=ddos, users=users, edit_data=edit_data, perm=perm, pagination=pagination, s_login=s_login, s_name=s_name, s_dept=s_dept, s_desig=s_desig, s_role=s_role, s_active=s_active)

# --- ROLE LEVEL MASTER ---
@umm_bp.route('/role_level_master', methods=['GET', 'POST'])
@permission_required('Role Level Master')
def role_level_master():
    user_id = session['user_id']; loc_id = session.get('selected_loc'); perm = NavModel.check_permission(user_id, loc_id, 'Role Level Master')
    if request.method == 'POST':
        action = (request.form.get('action') or '').strip().upper()
        if action == 'DELETE':
            delete_id = request.form.get('delete_id')
            try:
                DB.execute("DELETE FROM UM_RoleLevel_Mst WHERE pk_rolelevelId = ?", [delete_id])
                flash("Role Level deleted successfully.", "success")
            except Exception as e: flash(f"Error: {str(e)}", "danger")
            return redirect(url_for('umm.role_level_master'))
        name = request.form.get('level_name'); priority = request.form.get('priority'); remarks = request.form.get('remarks'); edit_id = request.form.get('edit_id')
        try:
            if edit_id:
                DB.execute("UPDATE UM_RoleLevel_Mst SET rolelevelname = ?, prioritylevel = ?, remarks = ? WHERE pk_rolelevelId = ?", [name, priority, remarks, edit_id])
                flash("Role Level updated successfully.", "success")
            else:
                DB.execute("INSERT INTO UM_RoleLevel_Mst (rolelevelname, prioritylevel, remarks) VALUES (?, ?, ?)", [name, priority, remarks])
                flash("Role Level created successfully.", "success")
        except Exception as e: flash(f"Error: {str(e)}", "danger")
        return redirect(url_for('umm.role_level_master'))
    page = int(request.args.get('page', 1)); pagination, sql_limit = get_pagination("UM_RoleLevel_Mst", page, order_by="ORDER BY prioritylevel")
    levels = DB.fetch_all(f"SELECT pk_rolelevelId as id, rolelevelname as name, prioritylevel as priority, remarks FROM UM_RoleLevel_Mst {sql_limit}")
    edit_data = None; edit_id = request.args.get('edit_id')
    if edit_id: edit_data = DB.fetch_one("SELECT pk_rolelevelId as id, rolelevelname as name, prioritylevel as priority, remarks FROM UM_RoleLevel_Mst WHERE pk_rolelevelId = ?", [edit_id])
    return render_template('umm/role_level_master.html', levels=levels, edit_data=edit_data, perm=perm, pagination=pagination)

# --- MODULE MASTER ---
@umm_bp.route('/module_master', methods=['GET', 'POST'])
@permission_required('Module Master')
def module_master():
    user_id = session['user_id']; loc_id = session.get('selected_loc'); perm = NavModel.check_permission(user_id, loc_id, 'Module Master')
    if request.method == 'POST':
        action = (request.form.get('action') or '').strip().upper()
        if action == 'DELETE':
            delete_id = request.form.get('delete_id')
            try:
                DB.execute("DELETE FROM UM_Module_Mst WHERE pk_moduleId = ?", [delete_id])
                flash("Module deleted successfully.", "success")
            except Exception as e: flash(f"Error: {str(e)}", "danger")
            return redirect(url_for('umm.module_master'))
        name = request.form.get('module_name'); m_type = 1 if request.form.get('type') == 'rdoWeb' else 0
        active = 1 if request.form.get('active') else 0; alias = request.form.get('alias'); remarks = request.form.get('remarks'); edit_id = request.form.get('edit_id')
        try:
            if edit_id:
                DB.execute("UPDATE UM_Module_Mst SET modulename = ?, remarks = ?, active = ?, moduletype = ?, mappedalias = ? WHERE pk_moduleId = ?", [name, remarks, active, m_type, alias, edit_id])
                flash("Record Updated Successfully !", "success")
            else:
                DB.execute("INSERT INTO UM_Module_Mst (modulename, remarks, active, moduletype, mappedalias) VALUES (?, ?, ?, ?, ?)", [name, remarks, active, m_type, alias])
                flash("Record Saved Successfully !", "success")
        except Exception as e: flash(f"Error: {str(e)}", "danger")
        return redirect(url_for('umm.module_master'))
    page = int(request.args.get('page', 1)); pagination, sql_limit = get_pagination("UM_Module_Mst", page, order_by="ORDER BY pk_moduleId")
    modules = DB.fetch_all(f"SELECT pk_moduleId as id, modulename as name, CASE WHEN moduletype = 1 THEN 'Web' ELSE 'Window' END as type, mappedalias as alias, CASE WHEN active = 1 THEN 'Yes' ELSE 'No' END as active, remarks FROM UM_Module_Mst {sql_limit}")
    edit_data = None; edit_id = request.args.get('edit_id')
    if edit_id: edit_data = DB.fetch_one("SELECT pk_moduleId as id, modulename as name, remarks, active, CASE WHEN moduletype = 1 THEN 'rdoWeb' ELSE 'rdoWin' END as type, mappedalias as alias FROM UM_Module_Mst WHERE pk_moduleId = ?", [edit_id])
    return render_template('umm/module_master.html', modules=modules, edit_data=edit_data, perm=perm, pagination=pagination)

# --- RESET PASSWORD ---
@umm_bp.route('/reset_password', methods=['GET', 'POST'])
@permission_required('Reset Password')
def reset_password():
    user_id = session['user_id']; loc_id = session.get('selected_loc'); perm = NavModel.check_permission(user_id, loc_id, 'Reset Password')
    new_pwd_display = None
    if request.method == 'POST':
        target_user_id = request.form.get('target_user_id'); new_pwd = "hau@123"
        try:
            pwd_hash = hashlib.sha1(new_pwd.encode('utf-8')).hexdigest()
            DB.execute("UPDATE UM_Users_Mst SET Plain_text = ?, password = ? WHERE pk_userId = ?", [new_pwd, pwd_hash, target_user_id])
            new_pwd_display = new_pwd; flash(f"Password reset successfully for selected user.", "success")
        except Exception as e: flash(f"Error: {str(e)}", "danger")
    users_list = DB.fetch_all("SELECT pk_userId as id, loginname FROM UM_Users_Mst ORDER BY active DESC, loginname ASC")
    return render_template('umm/reset_password.html', users_list=users_list, new_pwd_display=new_pwd_display, perm=perm)

# --- DEPARTMENT MASTER ---
@umm_bp.route('/department_master', methods=['GET', 'POST'])
@permission_required('Department Master')
def department_master():
    user_id = session['user_id']; loc_id = session.get('selected_loc'); perm = NavModel.check_permission(user_id, loc_id, 'Department Master')
    if request.method == 'POST':
        action = (request.form.get('action') or '').strip().upper()
        if action == 'DELETE':
            delete_id = request.form.get('delete_id')
            try:
                DB.execute("DELETE FROM Department_Mst WHERE pk_deptid = ?", [delete_id])
                flash("Department deleted successfully.", "success")
            except Exception as e: flash(f"Error: {str(e)}", "danger")
            return redirect(url_for('umm.department_master'))
        dept_name = request.form.get('department'); hod_id = request.form.get('hod_id'); email = request.form.get('email'); alias = request.form.get('alias'); edit_id = request.form.get('edit_id')
        try:
            if edit_id:
                DB.execute("UPDATE Department_Mst SET description = ?, Hod_Id = ?, Email_Id = ?, DeptAlias = ? WHERE pk_deptid = ?", [dept_name, hod_id, email, alias, edit_id])
                flash("Department updated successfully.", "success")
            else:
                DB.execute("INSERT INTO Department_Mst (description, Hod_Id, Email_Id, DeptAlias, fk_insUserID, fk_insDateID) VALUES (?, ?, ?, ?, ?, 'ab-428')", [dept_name, hod_id, email, alias, user_id])
                flash("Department created successfully.", "success")
        except Exception as e: flash(f"Error: {str(e)}", "danger")
        return redirect(url_for('umm.department_master'))
    page = int(request.args.get('page', 1)); pagination, sql_limit = get_pagination("Department_Mst D", page, order_by="ORDER BY D.description")
    departments = DB.fetch_all(f"SELECT D.pk_deptid as id, D.description as dept_name, E.empname as hod_name, E.empcode as hod_code, D.DeptAlias as alias FROM Department_Mst D LEFT JOIN SAL_Employee_Mst E ON D.Hod_Id = E.pk_empid {sql_limit}")
    edit_data = None; edit_id = request.args.get('edit_id')
    if edit_id: edit_data = DB.fetch_one("SELECT D.pk_deptid as id, D.description as department, D.Hod_Id as hod_id, E.empcode + ' ~ ' + E.empname as hod_text, D.Email_Id as email, D.DeptAlias as alias FROM Department_Mst D LEFT JOIN SAL_Employee_Mst E ON D.Hod_Id = E.pk_empid WHERE D.pk_deptid = ?", [edit_id])
    return render_template('umm/department_master.html', departments=departments, edit_data=edit_data, perm=perm, pagination=pagination)

# --- MODULE RIGHTS DETAIL ---
@umm_bp.route('/module_rights', methods=['GET', 'POST'])
@permission_required('Module Rights Detail')
def module_rights():
    user_id = session['user_id']; loc_id = session.get('selected_loc'); perm = NavModel.check_permission(user_id, loc_id, 'Module Rights Detail')
    if request.method == 'POST':
        target_user_id = request.form.get('target_user_id'); target_loc_id = request.form.get('target_loc_id'); selected_modules = request.form.getlist('module_ids')
        try:
            DB.execute("DELETE FROM UM_UserModuleDetails WHERE fk_userId = ? AND fk_locid = ?", [target_user_id, target_loc_id])
            for mid in selected_modules: DB.execute("INSERT INTO UM_UserModuleDetails (fk_userId, fk_locid, fk_moduleId, Fk_InsUserId, fk_insDateID) VALUES (?, ?, ?, ?, 'ab-428')", [target_user_id, target_loc_id, mid, user_id])
            flash("Module rights updated successfully.", "success")
        except Exception as e: flash(f"Error: {str(e)}", "danger")
        return redirect(url_for('umm.module_rights', user_id=target_user_id, loc_id=target_loc_id))
    users = DB.fetch_all("SELECT pk_userId as id, loginname, name FROM UM_Users_Mst ORDER BY active DESC, loginname ASC")
    locations = DB.fetch_all("SELECT pk_locid as id, locname as name FROM Location_Mst ORDER BY locname")
    all_modules = DB.fetch_all("SELECT pk_moduleId as id, modulename as name FROM UM_Module_Mst WHERE active = 1 ORDER BY modulename")
    selected_user = request.args.get('user_id'); selected_loc = request.args.get('loc_id'); assigned_module_ids = []
    if selected_user and selected_loc:
        res = DB.fetch_all("SELECT fk_moduleId FROM UM_UserModuleDetails WHERE fk_userId = ? AND fk_locid = ?", [selected_user, selected_loc])
        assigned_module_ids = [r['fk_moduleId'] for r in res]
    return render_template('umm/module_rights.html', users=users, locations=locations, all_modules=all_modules, selected_user=selected_user, selected_loc=selected_loc, assigned_module_ids=assigned_module_ids, perm=perm)

# --- MULTIPLE USERS PAGE RIGHTS ---
@umm_bp.route('/multiple_user_page_rights', methods=['GET', 'POST'])
@permission_required('Multiple Users Page Rights')
def multiple_user_page_rights():
    user_id = session['user_id']; loc_id = session.get('selected_loc'); perm = NavModel.check_permission(user_id, loc_id, 'Multiple Users Page Rights')
    if request.method == 'POST':
        module_id = request.form.get('module_id'); loc_id_target = request.form.get('loc_id'); user_ids = request.form.getlist('user_ids'); page_ids = request.form.getlist('page_ids')
        allow_view = 1 if request.form.get('allow_view') else 0; allow_add = 1 if request.form.get('allow_add') else 0
        allow_update = 1 if request.form.get('allow_update') else 0; allow_delete = 1 if request.form.get('allow_delete') else 0
        try:
            for uid in user_ids:
                mod_detail = DB.fetch_one("SELECT pk_usermoddetailId FROM UM_UserModuleDetails WHERE fk_userId = ? AND fk_locid = ? AND fk_moduleId = ?", [uid, loc_id_target, module_id])
                if not mod_detail:
                    DB.execute("INSERT INTO UM_UserModuleDetails (fk_userId, fk_locid, fk_moduleId, Fk_InsUserId, fk_insDateID) VALUES (?, ?, ?, ?, 'ab-428')", [uid, loc_id_target, module_id, user_id])
                    mod_detail = DB.fetch_one("SELECT TOP 1 pk_usermoddetailId FROM UM_UserModuleDetails WHERE fk_userId = ? AND fk_locid = ? AND fk_moduleId = ? ORDER BY pk_usermoddetailId DESC", [uid, loc_id_target, module_id])
                    mod_detail_id = mod_detail['pk_usermoddetailId'] if mod_detail else None
                else: mod_detail_id = mod_detail['pk_usermoddetailId']
                if not mod_detail_id: continue
                for pid in page_ids:
                    existing = DB.fetch_one("SELECT pk_pagerightid FROM UM_UserPageRights WHERE fk_usermoddetailId = ? AND fk_webpageId = ?", [mod_detail_id, pid])
                    if existing: DB.execute("UPDATE UM_UserPageRights SET AllowView=?, AllowAdd=?, AllowUpdate=?, AllowDelete=? WHERE pk_pagerightid = ?", [allow_view, allow_add, allow_update, allow_delete, existing['pk_pagerightid']])
                    else: DB.execute("INSERT INTO UM_UserPageRights (fk_usermoddetailId, fk_webpageId, AllowView, AllowAdd, AllowUpdate, AllowDelete) VALUES (?, ?, ?, ?, ?, ?)", [mod_detail_id, pid, allow_view, allow_add, allow_update, allow_delete])
            flash("Rights updated successfully for multiple users.", "success")
        except Exception as e: flash(f"Error: {str(e)}", "danger")
        return redirect(url_for('umm.multiple_user_page_rights', module_id=module_id, loc_id=loc_id_target))
    modules = DB.fetch_all("SELECT pk_moduleId as id, modulename as name FROM UM_Module_Mst WHERE active = 1 ORDER BY modulename")
    locations = DB.fetch_all("SELECT pk_locid as id, locname as name FROM Location_Mst ORDER BY locname")
    sel_module = request.args.get('module_id'); sel_loc = request.args.get('loc_id'); sel_type = request.args.get('user_type', 'HOD')
    users = []; pages = []
    if sel_module: pages = DB.fetch_all("SELECT W.pk_webpageId as id, W.menucaption as name, ISNULL(P.menucaption, 'Top Level') as parent_name FROM UM_WebPage_Mst W LEFT JOIN UM_WebPage_Mst P ON W.parentId = P.pk_webpageId WHERE W.fk_moduleId = ? AND ISNULL(W.activestatus, 1) = 1 AND ISNULL(W.selectable, 1) = 1 ORDER BY W.menucaption", [sel_module])
    if sel_loc:
        if sel_type == 'HOD': users = DB.fetch_all("SELECT DISTINCT U.pk_userId as id, U.loginname, U.name, D.description as dept_name FROM UM_Users_Mst U INNER JOIN Department_Mst D ON U.fk_empId = D.Hod_Id WHERE U.active = 1")
        else: users = DB.fetch_all("SELECT DISTINCT U.pk_userId as id, U.loginname, U.name, D.description as dept_name FROM UM_Users_Mst U INNER JOIN SAL_Employee_Mst E ON U.fk_empId = E.pk_empid LEFT JOIN Department_Mst D ON E.fk_deptid = D.pk_deptid INNER JOIN SAL_Designation_Mst DESG ON E.fk_desgid = DESG.pk_desgid WHERE U.active = 1 AND DESG.isteaching = 1")
    return render_template('umm/multiple_user_page_rights.html', modules=modules, locations=locations, users=users, pages=pages, sel_module=sel_module, sel_loc=sel_loc, sel_type=sel_type, perm=perm)

# --- PAGETYPE-ROLE LINK ---
@umm_bp.route('/page_type_role_link', methods=['GET', 'POST'])
@permission_required('PageType-Role Link')
def page_type_role_link():
    user_id = session['user_id']; loc_id = session.get('selected_loc'); perm = NavModel.check_permission(user_id, loc_id, 'PageType-Role Link')
    if request.method == 'POST':
        action = (request.form.get('action') or '').strip().upper(); role_id = request.form.get('role_id')
        if action == 'DELETE':
            try: DB.execute("DELETE FROM UM_PageTypeRoleDetails WHERE fk_roleId = ?", [role_id]); flash("Page type role mapping deleted successfully.", "success")
            except Exception as e: flash(f"Error: {str(e)}", "danger")
            return redirect(url_for('umm.page_type_role_link'))
        selected_page_types = request.form.getlist('page_type_ids')
        try:
            DB.execute("DELETE FROM UM_PageTypeRoleDetails WHERE fk_roleId = ?", [role_id])
            for ptid in selected_page_types: DB.execute("INSERT INTO UM_PageTypeRoleDetails (fk_roleId, fk_pagetypeId) VALUES (?, ?)", [role_id, ptid])
            flash("Page type role mapping updated.", "success")
        except Exception as e: flash(f"Error: {str(e)}", "danger")
        return redirect(url_for('umm.page_type_role_link', role_id=role_id))
    roles = DB.fetch_all("SELECT pk_roleId as id, rolename as name FROM UM_Role_Mst ORDER BY rolename"); page_types = DB.fetch_all("SELECT pk_pagetypeId as id, pagetypename as name FROM UM_PageType_Mst ORDER BY pagetypename")
    assigned_roles = DB.fetch_all("SELECT DISTINCT R.pk_roleId as id, R.rolename as name FROM UM_Role_Mst R INNER JOIN UM_PageTypeRoleDetails RD ON R.pk_roleId = RD.fk_roleId ORDER BY R.rolename")
    selected_role = request.args.get('role_id'); assigned_pt_ids = []
    if selected_role:
        res = DB.fetch_all("SELECT fk_pagetypeId FROM UM_PageTypeRoleDetails WHERE fk_roleId = ?", [selected_role])
        assigned_pt_ids = [str(r['fk_pagetypeId']) for r in res]
    return render_template('umm/page_type_role_link.html', roles=roles, page_types=page_types, assigned_roles=assigned_roles, selected_role=selected_role, assigned_pt_ids=assigned_pt_ids, perm=perm)

# --- ROLE PAGE RIGHTS ---
@umm_bp.route('/role_page_rights', methods=['GET', 'POST'])
@permission_required('Role Page Rights')
def role_page_rights():
    user_id = session['user_id']; loc_id = session.get('selected_loc'); perm = NavModel.check_permission(user_id, loc_id, 'Role Page Rights')
    if request.method == 'POST':
        sel_role = request.form.get('role_id'); sel_module = request.form.get('module_id')
        try:
            role_mod = DB.fetch_one("SELECT pk_rolemodid FROM UM_RoleModule_Details WHERE fk_roleId = ? AND fk_moduleId = ?", [sel_role, sel_module])
            if not role_mod:
                DB.execute("INSERT INTO UM_RoleModule_Details (fk_roleId, fk_moduleId) VALUES (?, ?)", [sel_role, sel_module])
                role_mod = DB.fetch_one("SELECT @@IDENTITY as id"); role_mod_id = role_mod['id']
            else: role_mod_id = role_mod['pk_rolemodid']
            pages = DB.fetch_all("SELECT pk_webpageId as id FROM UM_WebPage_Mst WHERE fk_moduleId = ?", [sel_module])
            for p in pages:
                pid = str(p['id']); allow_view = 1 if request.form.get(f'view_{pid}') else 0; allow_add = 1 if request.form.get(f'add_{pid}') else 0; allow_update = 1 if request.form.get(f'update_{pid}') else 0; allow_delete = 1 if request.form.get(f'delete_{pid}') else 0
                existing = DB.fetch_one("SELECT pk_rpagerightid FROM UM_RolePage_Rights WHERE fk_rolemodid = ? AND fk_webpageId = ?", [role_mod_id, pid])
                if existing: DB.execute("UPDATE UM_RolePage_Rights SET AllowView=?, AllowAdd=?, AllowUpdate=?, AllowDelete=? WHERE pk_rpagerightid = ?", [allow_view, allow_add, allow_update, allow_delete, existing['pk_rpagerightid']])
                elif allow_view or allow_add or allow_update or allow_delete: DB.execute("INSERT INTO UM_RolePage_Rights (fk_rolemodid, fk_webpageId, AllowView, AllowAdd, AllowUpdate, AllowDelete) VALUES (?, ?, ?, ?, ?, ?)", [role_mod_id, pid, allow_view, allow_add, allow_update, allow_delete])
            flash("Role rights updated.", "success")
        except Exception as e: flash(f"Error: {str(e)}", "danger")
        return redirect(url_for('umm.role_page_rights', role_id=sel_role, module_id=sel_module))
    roles = DB.fetch_all("SELECT pk_roleId as id, rolename as name FROM UM_Role_Mst ORDER BY rolename"); all_modules = DB.fetch_all("SELECT pk_moduleId as id, modulename as name FROM UM_Module_Mst WHERE active = 1 ORDER BY modulename")
    sel_role = request.args.get('role_id'); sel_module = request.args.get('module_id'); pages = []
    if sel_role and sel_module:
        role_mod = DB.fetch_one("SELECT pk_rolemodid FROM UM_RoleModule_Details WHERE fk_roleId = ? AND fk_moduleId = ?", [sel_role, sel_module])
        role_mod_id = role_mod['pk_rolemodid'] if role_mod else None; pages = DB.fetch_all("SELECT pk_webpageId as id, menucaption as name FROM UM_WebPage_Mst WHERE fk_moduleId = ? ORDER BY menucaption", [sel_module])
        for p in pages:
            p['rights'] = {'AllowView': 0, 'AllowAdd': 0, 'AllowUpdate': 0, 'AllowDelete': 0}
            if role_mod_id:
                rights = DB.fetch_one("SELECT AllowView, AllowAdd, AllowUpdate, AllowDelete FROM UM_RolePage_Rights WHERE fk_rolemodid = ? AND fk_webpageId = ?", [role_mod_id, p['id']])
                if rights: p['rights'] = rights
    return render_template('umm/role_page_rights.html', roles=roles, all_modules=all_modules, pages=pages, sel_role=sel_role, sel_module=sel_module, perm=perm)

# --- MANAGE PAGE RIGHTS ---
@umm_bp.route('/manage_page_rights', methods=['GET', 'POST'])
@permission_required('Manage Page Rights')
def manage_page_rights():
    user_id = session['user_id']; loc_id = session.get('selected_loc'); perm = NavModel.check_permission(user_id, loc_id, 'Manage Page Rights')
    if request.method == 'POST':
        sel_loc = request.form.get('loc_id'); sel_user = request.form.get('user_id'); sel_module = request.form.get('module_id'); action = (request.form.get('action') or '').strip().upper() or 'UPDATE'
        if action == 'RESET': return redirect(url_for('umm.manage_page_rights'))
        try:
            mod_detail = DB.fetch_one("SELECT pk_usermoddetailId FROM UM_UserModuleDetails WHERE fk_userId = ? AND fk_locid = ? AND fk_moduleId = ?", [sel_user, sel_loc, sel_module])
            if not mod_detail:
                DB.execute("INSERT INTO UM_UserModuleDetails (fk_userId, fk_locid, fk_moduleId, Fk_InsUserId, fk_insDateID) VALUES (?, ?, ?, ?, 'ab-428')", [sel_user, sel_loc, sel_module, user_id])
                mod_detail = DB.fetch_one("SELECT TOP 1 pk_usermoddetailId FROM UM_UserModuleDetails WHERE fk_userId = ? AND fk_locid = ? AND fk_moduleId = ? ORDER BY pk_usermoddetailId DESC", [sel_user, sel_loc, sel_module]); mod_detail_id = mod_detail['pk_usermoddetailId'] if mod_detail else None
            else: mod_detail_id = mod_detail['pk_usermoddetailId']
            if not mod_detail_id: raise RuntimeError("Unable to resolve user-module detail id.")
            pages = DB.fetch_all("SELECT pk_webpageId as id FROM UM_WebPage_Mst WHERE fk_moduleId = ?", [sel_module])
            for p in pages:
                pid = str(p['id']); allow_view = 1 if request.form.get(f'view_{pid}') else 0; allow_add = 1 if request.form.get(f'add_{pid}') else 0; allow_update = 1 if request.form.get(f'update_{pid}') else 0; allow_delete = 1 if request.form.get(f'delete_{pid}') else 0
                existing = DB.fetch_one("SELECT pk_pagerightid FROM UM_UserPageRights WHERE fk_usermoddetailId = ? AND fk_webpageId = ?", [mod_detail_id, pid])
                if existing: DB.execute("UPDATE UM_UserPageRights SET AllowView=?, AllowAdd=?, AllowUpdate=?, AllowDelete=? WHERE pk_pagerightid = ?", [allow_view, allow_add, allow_update, allow_delete, existing['pk_pagerightid']])
                elif allow_view or allow_add or allow_update or allow_delete: DB.execute("INSERT INTO UM_UserPageRights (fk_usermoddetailId, fk_webpageId, AllowView, AllowAdd, AllowUpdate, AllowDelete) VALUES (?, ?, ?, ?, ?, ?)", [mod_detail_id, pid, allow_view, allow_add, allow_update, allow_delete])
            flash("User page rights updated successfully.", "success")
        except Exception as e: flash(f"Error: {str(e)}", "danger")
        return redirect(url_for('umm.manage_page_rights', loc_id=sel_loc, user_id=sel_user, module_id=sel_module))
    locations = DB.fetch_all("SELECT pk_locid as id, locname as name FROM Location_Mst ORDER BY locname"); all_modules = DB.fetch_all("SELECT pk_moduleId as id, modulename as name FROM UM_Module_Mst WHERE active = 1 ORDER BY modulename")
    sel_loc = request.args.get('loc_id'); sel_user = request.args.get('user_id'); sel_module = request.args.get('module_id'); users = []
    if sel_loc: users = DB.fetch_all("SELECT DISTINCT U.pk_userId as id, U.loginname, U.name FROM UM_Users_Mst U INNER JOIN UM_UserModuleDetails UD ON U.pk_userId = UD.fk_userId WHERE UD.fk_locid = ? AND U.active = 1 ORDER BY U.loginname", [sel_loc])
    pages = []
    if sel_user and sel_loc and sel_module:
        mod_detail = DB.fetch_one("SELECT pk_usermoddetailId FROM UM_UserModuleDetails WHERE fk_userId = ? AND fk_locid = ? AND fk_moduleId = ?", [sel_user, sel_loc, sel_module]); mod_detail_id = mod_detail['pk_usermoddetailId'] if mod_detail else None
        pages = DB.fetch_all("SELECT W.pk_webpageId as id, W.menucaption as name, ISNULL(P.menucaption, '') as parent_name FROM UM_WebPage_Mst W LEFT JOIN UM_WebPage_Mst P ON W.parentId = P.pk_webpageId WHERE W.fk_moduleId = ? AND ISNULL(W.activestatus, 1) = 1 AND ISNULL(W.selectable, 1) = 1 ORDER BY W.menucaption", [sel_module])
        rights_map = {}
        if mod_detail_id and pages:
            placeholders = ",".join(["?"] * len(pages))
            rows = DB.fetch_all(f"SELECT fk_webpageId as id, AllowView, AllowAdd, AllowUpdate, AllowDelete FROM UM_UserPageRights WHERE fk_usermoddetailId = ? AND fk_webpageId IN ({placeholders})", [mod_detail_id] + [p['id'] for p in pages])
            rights_map = {str(r['id']): r for r in rows}
        for p in pages:
            rights = rights_map.get(str(p['id'])) or {}; p['rights'] = {'AllowView': int(rights.get('AllowView') or 0), 'AllowAdd': int(rights.get('AllowAdd') or 0), 'AllowUpdate': int(rights.get('AllowUpdate') or 0), 'AllowDelete': int(rights.get('AllowDelete') or 0)}
    return render_template('umm/manage_page_rights.html', locations=locations, users=users, all_modules=all_modules, pages=pages, sel_loc=sel_loc, sel_user=sel_user, sel_module=sel_module, perm=perm)

# --- WEB PAGE MASTER ---
@umm_bp.route('/web_page_master', methods=['GET', 'POST'])
@permission_required('Web Page Master')
def web_page_master():
    user_id = session['user_id']; loc_id = session.get('selected_loc'); perm = NavModel.check_permission(user_id, loc_id, 'Web Page Master')
    if request.method == 'POST':
        data = request.form; action = (data.get('action') or '').strip().upper()
        if action == 'DELETE':
            delete_id = data.get('delete_id')
            try: DB.execute("DELETE FROM UM_WebPage_Mst WHERE pk_webpageId = ?", [delete_id]); flash("Web Page deleted successfully.", "success")
            except Exception as e: flash(f"Error: {str(e)}", "danger")
            return redirect(url_for('umm.web_page_master'))
        edit_id = data.get('edit_id'); params = [data.get('caption'), data.get('page_name'), data.get('path'), data.get('tooltip'), data.get('parent_id') or 0, data.get('order') or 0, 1 if data.get('active') else 0, data.get('module_id'), data.get('page_type_id'), data.get('description'), 1 if data.get('selectable') else 0]
        try:
            if edit_id: DB.execute("UPDATE UM_WebPage_Mst SET menucaption=?, webpagename=?, pagepath=?, tooltip=?, parentId=?, displayorder=?, activestatus=?, fk_moduleId=?, fk_pagetypeId=?, pagedescription=?, selectable=? WHERE pk_webpageId=?", params + [edit_id]); flash("Web page updated successfully.", "success")
            else: DB.execute("INSERT INTO UM_WebPage_Mst (menucaption, webpagename, pagepath, tooltip, parentId, displayorder, activestatus, fk_moduleId, fk_pagetypeId, pagedescription, selectable) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", params); flash("Web page created successfully.", "success")
        except Exception as e: flash(f"Error: {str(e)}", "danger")
        return redirect(url_for('umm.web_page_master'))
    page = int(request.args.get('page', 1))
    pagination, sql_limit = get_pagination("UM_WebPage_Mst W LEFT JOIN UM_Module_Mst M ON W.fk_moduleId = M.pk_moduleId", 
                                           page, order_by="ORDER BY M.modulename, W.displayorder")
    
    modules = DB.fetch_all("SELECT pk_moduleId as id, modulename as name FROM UM_Module_Mst ORDER BY modulename")
    page_types = DB.fetch_all("SELECT pk_pagetypeId as id, pagetypename as name FROM UM_PageType_Mst ORDER BY pagetypename")
    parent_pages = DB.fetch_all("SELECT pk_webpageId as id, menucaption as name FROM UM_WebPage_Mst WHERE parentId = 0 OR parentId IS NULL ORDER BY menucaption")
    pages = DB.fetch_all(f"SELECT W.pk_webpageId as id, W.menucaption, M.modulename as modulename, W.displayorder, W.activestatus FROM UM_WebPage_Mst W LEFT JOIN UM_Module_Mst M ON W.fk_moduleId = M.pk_moduleId {sql_limit}")
    edit_data = None; edit_id = request.args.get('edit_id')
    if edit_id: edit_data = DB.fetch_one("SELECT * FROM UM_WebPage_Mst WHERE pk_webpageId = ?", [edit_id])
    return render_template('umm/web_page_master.html', pages=pages, modules=modules, page_types=page_types, parent_pages=parent_pages, edit_data=edit_data, perm=perm, pagination=pagination)

# --- API ENDPOINTS ---
@umm_bp.route('/api/ddo/available_locations')
def api_umm_available_locations_by_ddo():
    ddo_id = request.args.get('ddo')
    if not ddo_id: return jsonify([])
    
    # Specific locations required by the live template
    specific_ids = ['AX-79', 'CO-82', 'ES-70', 'NC-90']
    
    # 1. Find the "location of DDO selected" first
    ddo_info = DB.fetch_one("SELECT Description FROM DDO_Mst WHERE pk_ddoid = ?", [ddo_id])
    ddo_loc = None
    if ddo_info:
        search_name = ddo_info['Description'].replace('DDO, ', '').strip()
        ddo_loc = DB.fetch_one("""
            SELECT TOP 1 pk_locid as id, locname as name
            FROM Location_Mst
            WHERE locname LIKE ?
        """, [f"%{search_name}%"])

    # 2. Fetch the specific hardcoded locations (excluding the DDO's location to avoid duplicates)
    exclude_id = ddo_loc['id'] if ddo_loc else ''
    locations = DB.fetch_all(f"""
        SELECT pk_locid as id, locname as name 
        FROM Location_Mst 
        WHERE pk_locid IN ({",".join(["'"+id+"'" for id in specific_ids])})
        AND pk_locid != ?
        ORDER BY CASE pk_locid 
            WHEN 'AX-79' THEN 1 
            WHEN 'CO-82' THEN 2 
            WHEN 'ES-70' THEN 3 
            WHEN 'NC-90' THEN 4 
        END
    """, [exclude_id])

    # 3. Always add the DDO's location as the last item
    if ddo_loc:
        locations.append(ddo_loc)

    return jsonify(locations)

@umm_bp.route('/api/location/employees')
def api_umm_employees_by_location():
    loc_id = request.args.get('loc')
    ddo_id = request.args.get('ddo')
    where = ["1=1"]
    params = []
    if loc_id: where.append("fk_locid = ?"); params.append(loc_id)
    if ddo_id: where.append("fk_ddoid = ?"); params.append(ddo_id)
    
    query = f"SELECT pk_empid as id, empcode as code, empname as name FROM SAL_Employee_Mst WHERE {' AND '.join(where)} ORDER BY empname"
    return jsonify(DB.fetch_all(query, params))

@umm_bp.route('/api/employee/details/<emp_id>')
def api_umm_employee_details(emp_id):
    query = """
        SELECT E.empname as name, D.description as department, DG.designation, E.email
        FROM SAL_Employee_Mst E
        LEFT JOIN Department_Mst D ON E.fk_deptid = D.pk_deptid
        LEFT JOIN SAL_Designation_Mst DG ON E.fk_desgid = DG.pk_desgid
        WHERE E.pk_empid = ?
    """
    return jsonify(DB.fetch_one(query, [emp_id]) or {})
@umm_bp.route('/api/employee/details_by_code')
def api_umm_employee_details_by_code():
    code = request.args.get('code')
    res = DB.fetch_one("""
        SELECT pk_empid as id, empname as name FROM SAL_Employee_Mst WHERE empcode = ?
    """, [code])
    return jsonify(res or {})

@umm_bp.route('/api/location/users')
def api_umm_users_by_location():
    loc_id = request.args.get('loc')
    if not loc_id: return jsonify([])
    query = "SELECT DISTINCT U.pk_userId as id, U.loginname, U.name FROM UM_Users_Mst U INNER JOIN UM_UserModuleDetails UD ON U.pk_userId = UD.fk_userId WHERE UD.fk_locid = ? AND U.active = 1 ORDER BY U.loginname"
    return jsonify(DB.fetch_all(query, [loc_id]))

@umm_bp.route('/api/user/modules')
def api_umm_modules_by_user_loc():
    user_id = request.args.get('user_id'); loc_id = request.args.get('loc')
    if not user_id or not loc_id: return jsonify([])
    query = "SELECT DISTINCT M.pk_moduleId as id, M.modulename as name FROM UM_UserModuleDetails UD INNER JOIN UM_Module_Mst M ON UD.fk_moduleId = M.pk_moduleId WHERE UD.fk_userId = ? AND UD.fk_locid = ? ORDER BY M.modulename"
    return jsonify(DB.fetch_all(query, [user_id, loc_id]))

@umm_bp.route('/api/module/pages')
def api_umm_pages_by_module():
    module_id = request.args.get('module_id')
    if not module_id: return jsonify([])
    query = "SELECT pk_webpageId as id, menucaption as name FROM UM_WebPage_Mst WHERE fk_moduleId = ? AND ISNULL(activestatus, 1) = 1 ORDER BY menucaption"
    return jsonify(DB.fetch_all(query, [module_id]))

# --- OTHER ROUTES ---
@umm_bp.route('/fetch_password', methods=['GET', 'POST'])
@permission_required('Fetch Password')
def fetch_password():
    user_id = session['user_id']; loc_id = session.get('selected_loc'); perm = NavModel.check_permission(user_id, loc_id, 'Fetch Password')
    users_list = DB.fetch_all("SELECT pk_userId as id, loginname FROM UM_Users_Mst ORDER BY active DESC, loginname ASC")
    password_info = None; selected_user_id = None
    if request.method == 'POST':
        selected_user_id = request.form.get('target_user_id')
        if selected_user_id: password_info = DB.fetch_one("SELECT pk_userId as id, loginname, Plain_text as plain_text, password as password_hash FROM UM_Users_Mst WHERE pk_userId = ?", [selected_user_id])
    return render_template('umm/fetch_password.html', users_list=users_list, selected_user_id=selected_user_id, password_info=password_info, perm=perm)

@umm_bp.route('/user_wise_log', methods=['GET', 'POST'])
@permission_required('User Wise Log')
def user_wise_log():
    user_id = session['user_id']; loc_id = session.get('selected_loc'); perm = NavModel.check_permission(user_id, loc_id, 'User Wise Log')
    
    users = DB.fetch_all("SELECT pk_userId as id, loginname FROM UM_Users_Mst WHERE active = 1 ORDER BY loginname")
    
    logs = []
    sel_user = request.form.get('user_id') or request.args.get('user_id')
    from_date = request.form.get('from_date') or request.args.get('from_date') or datetime.now().strftime('%Y-%m-%d')
    to_date = request.form.get('to_date') or request.args.get('to_date') or datetime.now().strftime('%Y-%m-%d')
    
    if request.method == 'POST':
        action = (request.form.get('action') or '').strip().upper()
        if action == 'PRINT':
            # Logic for PDF can be added here or via a dedicated API
            pass
            
    where = ["1=1"]
    params = []
    if sel_user:
        where.append("L.fk_userid = ?")
        params.append(sel_user)
    if from_date:
        where.append("CAST(L.logintime AS DATE) >= ?")
        params.append(from_date)
    if to_date:
        where.append("CAST(L.logintime AS DATE) <= ?")
        params.append(to_date)
        
    query = f"""
        SELECT U.loginname as user_name, L.logintime, L.logouttime, L.UserIP
        FROM UM_UserLoginLog L
        LEFT JOIN UM_Users_Mst U ON L.fk_userid = U.pk_userId
        WHERE {' AND '.join(where)}
        ORDER BY L.logintime DESC
    """
    logs = DB.fetch_all(query, params)
    
    return render_template('umm/user_wise_log.html', 
                           users=users, logs=logs, 
                           sel_user=sel_user, from_date=from_date, to_date=to_date,
                           perm=perm)

@umm_bp.route('/send_message', methods=['GET', 'POST'])
@permission_required('Send Message')
def send_message():
    user_id = session['user_id']; loc_id = session.get('selected_loc'); perm = NavModel.check_permission(user_id, loc_id, 'Send Message')
    
    if request.method == 'POST':
        action = (request.form.get('action') or '').strip().upper()
        
        if action == 'RESET':
            return redirect(url_for('umm.send_message'))
            
        if action == 'DELETE':
            if not perm.get('AllowDelete'):
                flash("You do not have permission to delete.", "danger")
                return redirect(url_for('umm.send_message'))
            delete_id = request.form.get('delete_id')
            try:
                DB.execute("DELETE FROM UM_CommonMessaging WHERE Pk_MsgId = ?", [delete_id])
                flash("Message deleted successfully.", "success")
            except Exception as e: flash(f"Error: {str(e)}", "danger")
            return redirect(url_for('umm.send_message'))
            
        if action == 'SAVE' or action == 'UPDATE':
            msg = request.form.get('message')
            is_active = 1 if request.form.get('is_active') else 0
            pub_date = request.form.get('publish_date')
            edit_id = request.form.get('edit_id')
            
            if edit_id and not perm.get('AllowUpdate'):
                flash("You do not have permission to update.", "danger")
                return redirect(url_for('umm.send_message'))
            if not edit_id and not perm.get('AllowAdd'):
                flash("You do not have permission to add.", "danger")
                return redirect(url_for('umm.send_message'))
            
            try:
                if edit_id:
                    DB.execute("""
                        UPDATE UM_CommonMessaging 
                        SET Messages = ?, PublishDate = ?, isactive = ?
                        WHERE Pk_MsgId = ?
                    """, [msg, pub_date, is_active, edit_id])
                    flash("Message updated successfully.", "success")
                else:
                    DB.execute("""
                        INSERT INTO UM_CommonMessaging (Messages, PublishDate, isactive) 
                        VALUES (?, ?, ?)
                    """, [msg, pub_date, is_active])
                    flash("Message saved successfully.", "success")
            except Exception as e: flash(f"Error: {str(e)}", "danger")
            return redirect(url_for('umm.send_message'))
            
    messages_list = DB.fetch_all("""
        SELECT M.Pk_MsgId as id, M.Messages as message, M.PublishDate, M.isactive,
               D.Description as ddo_name, L.locname as loc_name
        FROM UM_CommonMessaging M
        LEFT JOIN DDO_Mst D ON M.fk_ddoid = D.pk_ddoid
        LEFT JOIN Location_Mst L ON M.fk_locid = L.pk_locid
        ORDER BY M.PublishDate DESC
    """)
    
    edit_data = None; edit_id = request.args.get('edit_id')
    if edit_id:
        edit_data = DB.fetch_one("SELECT Pk_MsgId as id, Messages as message, PublishDate, isactive FROM UM_CommonMessaging WHERE Pk_MsgId = ?", [edit_id])
        if edit_data and edit_data['PublishDate']:
            edit_data['PublishDate'] = edit_data['PublishDate'].strftime('%Y-%m-%d')
            
    return render_template('umm/send_message.html', 
                           messages_list=messages_list, edit_data=edit_data, 
                           perm=perm)

@umm_bp.route('/login_image_management', methods=['GET', 'POST'])
@permission_required('User Login Management')
def login_image_management():
    user_id = session['user_id']; loc_id = session.get('selected_loc'); perm = NavModel.check_permission(user_id, loc_id, 'User Login Management')
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'upload':
            file = request.files.get('image_file')
            if file and file.filename != '':
                filename = secure_filename(file.filename); path = f"/static/uploads/login_images/{filename}"
                DB.execute("INSERT INTO LoginPageImgManage_mst (ImageName, Imagepath, isActive, IsActiveStdPortal, UserId, Date) VALUES (?, ?, 0, 0, ?, GETDATE())", [filename, path, user_id]); flash("Image uploaded.", "success")
        elif action == 'update':
            DB.execute("UPDATE LoginPageImgManage_mst SET isActive = 0, IsActiveStdPortal = 0")
            for key in request.form:
                if key.startswith('active_'): iid = key.split('_')[1]; DB.execute("UPDATE LoginPageImgManage_mst SET isActive = 1 WHERE Pk_Lpgid = ?", [iid])
                if key.startswith('student_'): iid = key.split('_')[1]; DB.execute("UPDATE LoginPageImgManage_mst SET IsActiveStdPortal = 1 WHERE Pk_Lpgid = ?", [iid])
            flash("Settings updated.", "success")
        elif request.form.get('delete_id'): DB.execute("DELETE FROM LoginPageImgManage_mst WHERE Pk_Lpgid = ?", [request.form.get('delete_id')]); flash("Image deleted.", "success")
        return redirect(url_for('umm.login_image_management'))
    images = DB.fetch_all("SELECT Pk_Lpgid as id, ImageName as filename, Imagepath as url, isActive as active, IsActiveStdPortal as student_active FROM LoginPageImgManage_mst ORDER BY Pk_Lpgid DESC")
    return render_template('umm/login_image_management.html', images=images, perm=perm)
