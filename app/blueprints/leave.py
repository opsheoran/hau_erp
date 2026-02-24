from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash, make_response
from app.db import DB
from app.models import LeaveModel, NavModel, EmployeeModel, LeaveAssignmentModel, LeaveEncashmentModel, LeaveReportModel, LeaveConfigModel, HolidayModel
from functools import wraps
from datetime import datetime, timedelta
import math

leave_bp = Blueprint('leave', __name__)

LEAVE_MENU_CONFIG = {
    'Master': {
        'Main Menu': {
            'Leave Masters': [
                'Common Holidays Master', 'Holiday Location Master', 
                'Location Wise Holidays Master', 'Weekly Off Master', 'Leave Type Master'
            ]
        }
    },
    'Transaction': {
        'Main Menu': {
            'Leave Transactions': [
                'Employee Previous Leave Assign', 'Leave Request', 'Service Departure Details',
                'Employee Leave Assignment', 'Service Departure Status', 'Service Departure from Admin',
                'Employee CPL Assignment', 'Service Joining Date', 'Leave Approval',
                'Service Joining Status', 'Leave Adjustment Request', 'Leave Adjustment Approval',
                'Leave Extend Request', 'Cancel Approved Leaves', 'Leave Encashment',
                'Service Joining from Admin', 'Leave Transaction', 'Update Earned Leave Balance'
            ]
        }
    },
    'Reports': {
        'Main Menu': {
            'Leave Reports': [
                'Leave Transaction Reports', 'Leave Reconcilliation Report', 'Employee Leave Details'
            ]
        }
    }
}

@leave_bp.before_request
def ensure_module():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    # Check if we are in Portal or Admin mode
    if session.get('ui_mode') == 'portal':
        session['current_module_id'] = 63
    else:
        # Admin Leave Management ID
        session['current_module_id'] = 75

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
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@leave_bp.route('/api/request_details/<req_id>')
def api_request_details(req_id):
    res = LeaveModel.get_request_details(req_id)
    return jsonify(res)

@leave_bp.route('/api/employee/search')
def api_employee_search():
    term = request.args.get('term', '')
    if len(term) < 2:
        return jsonify([])
    results = EmployeeModel.search_employees(term)
    return jsonify(results)

@leave_bp.route('/api/employee/search_advanced')
def api_employee_search_advanced():
    code = (request.args.get('emp_code') or '').strip()
    manual = (request.args.get('manual_code') or '').strip()
    name = (request.args.get('emp_name') or '').strip()
    ddo = (request.args.get('ddo_id') or '').strip()
    loc = (request.args.get('loc_id') or '').strip()
    dept = (request.args.get('dept_id') or '').strip()
    desg = (request.args.get('desg_id') or '').strip()

    where = ["E.employeeleftstatus = 'N'"]
    params = []

    if code:
        where.append("E.empcode LIKE ?")
        params.append(f"%{code}%")
    if manual:
        where.append("E.manualempcode LIKE ?")
        params.append(f"%{manual}%")
    if name:
        where.append("E.empname LIKE ?")
        params.append(f"%{name}%")
    if ddo:
        where.append("E.fk_ddoid = ?")
        params.append(ddo)
    if loc:
        where.append("E.fk_locid = ?")
        params.append(loc)
    if dept:
        where.append("E.fk_deptid = ?")
        params.append(dept)
    if desg:
        where.append("E.fk_desgid = ?")
        params.append(desg)

    query = f"""
        SELECT TOP 100
            E.pk_empid as id,
            E.empcode,
            E.manualempcode,
            E.empname,
            ISNULL(DS.designation, '') as designation,
            (E.empname + ' | ' + E.empcode + ' | ' + ISNULL(DS.designation, '')) as display
        FROM SAL_Employee_Mst E
        LEFT JOIN SAL_Designation_Mst DS ON E.fk_desgid = DS.pk_desgid
        WHERE {' AND '.join(where)}
        ORDER BY E.empname
    """
    return jsonify(DB.fetch_all(query, params))

@leave_bp.route('/api/holiday_details/<locholiday_id>')
def api_holiday_details(locholiday_id):
    query = """
        SELECT C.pk_commonholidayid, C.commonholiday as Holiday, 
               HT.holidaytype as HolidayType,
               CONVERT(varchar, T.holidaydate, 23) as FromDate,
               CONVERT(varchar, T.todate, 23) as ToDate,
               T.remarks as Remarks
        FROM SAL_CommonHolidays_Mst C
        LEFT JOIN SAL_LocationWiseHolidays_Trn T ON C.pk_commonholidayid = T.fk_commonholidayid 
             AND T.fk_locholidayid = ?
        LEFT JOIN SAL_HolidayType_Mst HT ON C.fk_holidaytypeid = HT.pk_holidaytypeid
        ORDER BY C.displayorder
    """
    return jsonify(DB.fetch_all(query, [locholiday_id]))

@leave_bp.route('/api/el_balance')
def api_el_balance():
    emp_id = session.get('emp_id')
    res = DB.fetch_one("SELECT TOP 1 el_balance FROM SAL_EarnedLeave_Details WHERE fk_empid = ? ORDER BY sno_for_emp DESC", [emp_id])
    balance = float(res['el_balance']) if res else 0.0
    return jsonify({'balance': f"{balance:.3f}"})

@leave_bp.route('/api/holiday_locations')
def api_holiday_locations():
    return jsonify(HolidayModel.get_holiday_locations())

@leave_bp.route('/api/calculate_days')
def api_calculate_days():
    f, t = request.args.get('from'), request.args.get('to')
    loc = request.args.get('loc_id') or session.get('selected_loc')
    leave_id = request.args.get('leave_id')
    emp_id = session.get('emp_id')
    is_short = request.args.get('short') == 'true'
    if not (f and t and loc and emp_id and leave_id):
        return jsonify({'days': 0, 'total_days': 0, 'rows': []})

    leave_days, total_days, rows = LeaveModel.calculate_breakup(
        f, t, loc_id=loc, emp_id=emp_id, leave_id=leave_id, is_short=is_short
    )
    return jsonify({'days': leave_days, 'total_days': total_days, 'rows': rows})

@leave_bp.route('/leave_request', methods=['GET', 'POST'])
def leave_request():
    emp_id = session.get('emp_id')
    if not emp_id:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        action = (request.form.get('action') or 'SUBMIT').upper().strip()
        req_id = request.form.get('req_id')

        if action == 'DELETE':
            try:
                if req_id and LeaveModel.cancel_leave_request(req_id, session['user_id']):
                    flash("Leave request cancelled.", "success")
                else:
                    flash("Unable to cancel this leave request (only pending requests can be cancelled).", "danger")
            except Exception as e:
                flash(f"Error: {str(e)}", "danger")
            return redirect(url_for('leave.leave_request'))

        sh = request.form.get('s_hour')
        sm = request.form.get('s_min')
        sa = request.form.get('s_ampm')
        is_short = request.form.get('is_short') == 'on'
        if is_short:
            if sh in (None, '', '00', '0') or sm in (None, '', '00') or sa in (None, ''):
                flash("Please select Start Time for Short Leave.", "danger")
                return redirect(url_for('leave.leave_request', edit_id=req_id) if req_id else url_for('leave.leave_request'))
            req_time = f"{sh}:{sm} {sa}"
        else:
            req_time = None

        def compose_time(prefix):
            hh = request.form.get(f'{prefix}_hour')
            mm = request.form.get(f'{prefix}_min')
            ap = request.form.get(f'{prefix}_ampm')
            if hh in (None, '', '0', '00') or mm in (None, '', '00') or ap in (None, ''):
                return None
            return f"{hh}:{mm} {ap}"

        data = {
            'emp_id': request.form.get('emp_id'),
            'leave_id': request.form.get('leave_id'),
            'from_date': request.form.get('from_date'),
            'to_date': request.form.get('to_date'),
            'total_days': request.form.get('total_days', 0),
            'leave_days': request.form.get('leave_days', 0),
            'reason': request.form.get('reason'),
            'contact': request.form.get('contact'),
            'reporting_to': request.form.get('reporting_to'),
            'loc_id': request.form.get('loc_id'),
            'rec1': request.form.get('rec1'),
            'rec2': request.form.get('rec2'),
            'rec3': request.form.get('rec3'),
            'station_from': request.form.get('station_from'),
            'station_to': request.form.get('station_to'),
            'is_medical': request.form.get('is_medical') == 'on',
            'is_study': request.form.get('is_study') == 'on',
            'is_commuted': request.form.get('is_commuted') == 'on',
            'add_inst': request.form.get('add_inst'),
            'is_short': is_short,
            'req_time': req_time,
            'station_start_time': compose_time('station_start'),
            'station_end_time': compose_time('station_end'),
        }
        try:
            try:
                leave_days_val = float(data.get('leave_days') or 0)
            except Exception:
                leave_days_val = 0.0
            if leave_days_val <= 0:
                flash("Please click CALCULATE before submitting.", "danger")
                return redirect(url_for('leave.leave_request', edit_id=req_id) if req_id else url_for('leave.leave_request'))

            if req_id:
                if LeaveModel.update_leave_request(req_id, data, session['user_id']):
                    flash("Leave request updated successfully.", "success")
                else:
                    flash("Unable to update this leave request (only pending requests can be updated).", "danger")
            else:
                if LeaveModel.save_leave_request(data, session['user_id']):
                    flash("Leave request submitted successfully.", "success")
        except Exception as e:
            flash(f"Error: {str(e)}", "danger")
        return redirect(url_for('leave.leave_request'))

    emp_details = LeaveModel.get_employee_full_details(emp_id)
    leave_summary = LeaveModel.get_leave_summary(emp_id)
    leave_types = LeaveModel.get_leave_types()
    approvers = LeaveConfigModel.get_approvers()
    reporting_to = LeaveModel.get_reporting_officer(emp_id)
    
    edit_id = request.args.get('edit_id')
    edit_req = None
    if edit_id:
        try:
            edit_req = LeaveModel.get_leave_request_for_edit(edit_id, session['user_id'])
        except Exception:
            edit_req = None

    page = request.args.get('page', 1, type=int)
    per_page = 10
    requests, total_requests = LeaveModel.get_user_leaves(session['user_id'], page=page, per_page=per_page)
    recommended = LeaveModel.get_recommended_for(emp_id)
    
    pagination = {
        'page': page,
        'total': total_requests,
        'total_pages': math.ceil(total_requests / per_page) if total_requests else 1,
        'has_prev': page > 1,
        'has_next': page < math.ceil(total_requests / per_page) if total_requests else False,
    }

    search_lookups = {
        'ddos': EmployeeModel.get_all_ddos(),
        'depts': EmployeeModel.get_all_departments(),
        'desgs': EmployeeModel.get_all_designations(),
        'locs': EmployeeModel.get_lookups()['locations']
    }

    return render_template('leave/leave_request.html', 
                           emp=emp_details, 
                           summary=leave_summary, 
                           leave_types=leave_types,
                           approvers=approvers,
                           requests=requests,
                           recommended=recommended,
                           ro=reporting_to,
                           pagination=pagination,
                           lookups=search_lookups,
                           edit_req=edit_req)

@leave_bp.route('/adjustment', methods=['GET', 'POST'])
@permission_required('Leave Adjustment Request')
def leave_adjustment():
    user_id = session['user_id']
    emp_id = session.get('emp_id')
    loc_id = session.get('selected_loc')
    
    if request.method == 'POST':
        try:
            data = {
                'leave_id': request.form.get('leave_id'),
                'adj_days': request.form.get('adj_days'),
                'remarks': request.form.get('remarks')
            }
            LeaveModel.create_adj_request(data, emp_id, user_id, loc_id)
            flash("Adjustment request submitted.", "success")
        except Exception as e:
            flash(f"Error: {str(e)}", "danger")
        return redirect(url_for('leave.leave_adjustment'))

    selected_leave_id = request.args.get('leave_id')
    daywise_details = None
    if selected_leave_id:
        daywise_details = LeaveModel.get_leave_daywise_details_by_taken_id(selected_leave_id)

    page = request.args.get('page', 1, type=int)
    leaves_for_adj = LeaveModel.get_approved_leaves_for_adj(emp_id)
    adj_history, total_adj = LeaveModel.get_adj_requests(emp_id, page=page)
    balances = LeaveModel.get_leave_balance(emp_id)
    reporting_to = LeaveModel.get_reporting_officer(emp_id)
    
    per_page = 10
    pagination = {
        'page': page,
        'total': total_adj,
        'total_pages': math.ceil(total_adj / per_page) if total_adj else 1,
        'has_prev': page > 1,
        'has_next': page < math.ceil(total_adj / per_page) if total_adj else False,
    }

    return render_template('leave/leave_adjustment.html', 
                           leaves=leaves_for_adj, 
                           history=adj_history, 
                           balances=balances,
                           reporting_to=reporting_to,
                           selected_leave_id=selected_leave_id,
                           daywise_details=daywise_details,
                           pagination=pagination)

@leave_bp.route('/cancel', methods=['GET', 'POST'])
@permission_required('Leave Cancel Request')
def leave_cancel():
    user_id = session['user_id']
    emp_id = session.get('emp_id')
    loc_id = session.get('selected_loc')
    
    if request.method == 'POST':
        try:
            data = {
                'leave_id': request.form.get('leave_id'),
                'remarks': request.form.get('remarks')
            }
            LeaveModel.create_cancel_request(data, emp_id, user_id, loc_id)
            flash("Cancellation request submitted.", "success")
        except Exception as e:
            flash(f"Error: {str(e)}", "danger")
        return redirect(url_for('leave.leave_cancel'))

    selected_leave_id = request.args.get('leave_id')
    daywise_details = None
    if selected_leave_id:
        daywise_details = LeaveModel.get_leave_daywise_details_by_taken_id(selected_leave_id)

    page = request.args.get('page', 1, type=int)
    leaves_for_cancel = LeaveModel.get_approved_leaves_for_adj(emp_id) 
    cancel_history, total_cancel = LeaveModel.get_cancel_requests(emp_id, page=page)
    balances = LeaveModel.get_leave_balance(emp_id)
    reporting_to = LeaveModel.get_reporting_officer(emp_id)
    
    per_page = 10
    pagination = {
        'page': page,
        'total': total_cancel,
        'total_pages': math.ceil(total_cancel / per_page) if total_cancel else 1,
        'has_prev': page > 1,
        'has_next': page < math.ceil(total_cancel / per_page) if total_cancel else False,
    }

    return render_template('leave/leave_cancel.html', 
                           leaves=leaves_for_cancel, 
                           history=cancel_history,
                           balances=balances,
                           reporting_to=reporting_to,
                           selected_leave_id=selected_leave_id,
                           daywise_details=daywise_details,
                           pagination=pagination)

@leave_bp.route('/api/balance/<leave_id>')
def api_get_balance(leave_id):
    emp_id = session.get('emp_id')
    balances = LeaveModel.get_leave_balance(emp_id)
    # Find the specific leave type
    bal = next((b for b in balances if str(b['pk_leaveid']) == str(leave_id)), None)
    return jsonify(bal or {'balance': 0})

@leave_bp.route('/transaction', methods=['GET', 'POST'])
@permission_required('Leave Transaction')
def leave_transaction():
    emp_id = session.get('emp_id')
    user_id = session['user_id']
    
    if request.method == 'POST':
        # Logic for saving transaction directly (similar to leave_request)
        # But usually transactions might be admin-only or slightly different.
        # Following the user's form description.
        pass

    emp_details = LeaveModel.get_employee_full_details(emp_id)
    balances = LeaveModel.get_leave_balance(emp_id)
    leave_types = LeaveModel.get_leave_types(is_admin=True)
    
    page = request.args.get('page', 1, type=int)
    history, total = LeaveModel.get_leaves_taken(emp_id, page=page)
    
    pagination = {
        'page': page,
        'total': total,
        'total_pages': math.ceil(total / 10) if total else 1,
        'has_prev': page > 1,
        'has_next': total > page * 10,
    }

    return render_template('leave/leave_transaction.html', 
                           emp=emp_details,
                           balances=balances, 
                           leave_types=leave_types,
                           history=history,
                           pagination=pagination)

@leave_bp.route('/cancel_approved', methods=['GET', 'POST'])
@permission_required('Cancel Approved Leaves')
def cancel_approved():
    emp_id = session.get('emp_id')
    return redirect(url_for('leave.leave_cancel'))

@leave_bp.route('/joining_date', methods=['GET', 'POST'])
@permission_required('Service Joining Date')
def service_joining_date():
    user_id = session['user_id']
    emp_id = session.get('emp_id')
    
    if request.method == 'POST':
        req_id = request.form.get('req_id')
        j_date = request.form.get('joining_date')
        j_remark = request.form.get('joining_remark')
        if LeaveModel.submit_joining_date(req_id, j_date, j_remark, user_id):
            flash("Joining date submitted successfully.", "success")
        else:
            flash("Failed to submit joining date.", "danger")
        return redirect(url_for('leave.service_joining_date'))

    req_id = request.args.get('req_id')
    selected_req = None
    if req_id:
        res = LeaveModel.get_request_details(req_id)
        if res:
            selected_req = res['master']

    pending = LeaveModel.get_approved_leaves_pending_joining(emp_id)
    history, total = LeaveModel.get_joining_history(emp_id, page=1)
    
    pagination = {
        'page': 1,
        'total': total,
        'total_pages': math.ceil(total / 10) if total else 1,
        'has_prev': False,
        'has_next': total > 10 if total else False,
    }
    return render_template('leave/service_joining_date.html', pending=pending, selected_req=selected_req, history=history, pagination=pagination)

@leave_bp.route('/joining_status')
@permission_required('Service Joining Status')
def service_joining_status():
    emp_id = session.get('emp_id')
    page = request.args.get('page', 1, type=int)
    
    history, total = LeaveModel.get_ro_joining_status(emp_id, page=page)
    
    pagination = {
        'page': page,
        'total': total,
        'total_pages': math.ceil(total / 10) if total else 1,
        'has_prev': page > 1,
        'has_next': page < math.ceil(total / 10) if total else False,
    }
    return render_template('leave/service_joining_status.html', history=history, pagination=pagination)

@leave_bp.route('/joining_report/<req_id>')
def download_joining_report(req_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    emp_id = session.get('emp_id')
    
    res = LeaveModel.get_request_details(req_id)
    if not res:
        return "Report not found", 404
    req = res['master']
    
    if str(req.get('fk_reqempid')) != str(emp_id):
        return "Access denied", 403

    import io
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import inch
    import os

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    margin = 1 * inch
    curr_y = height - margin

    logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'images', 'logo.png')
    if os.path.exists(logo_path):
        c.drawImage(logo_path, width/2 - 0.3*inch, curr_y - 0.6*inch, width=0.6*inch, height=0.6*inch, mask='auto')
    
    curr_y -= 0.8*inch
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(width/2, curr_y, "Chaudhary Charan Singh Haryana Agricultural University, HISAR")
    
    curr_y -= 0.4*inch
    c.setFont("Helvetica", 11)
    c.drawString(margin, curr_y, "To")
    curr_y -= 0.2*inch
    c.drawString(margin + 0.2*inch, curr_y, f"{req.get('ReportingName', '')}")
    curr_y -= 0.2*inch
    c.drawString(margin + 0.2*inch, curr_y, "CCSHAU, HISAR")
    
    curr_y -= 0.5*inch
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin, curr_y, "Subject: Joining Report")
    
    curr_y -= 0.4*inch
    c.setFont("Helvetica", 11)
    
    from_date_val = req.get('fromdate')
    to_date_val = req.get('todate')
    from_date = from_date_val.strftime('%d/%m/%Y') if hasattr(from_date_val, 'strftime') else str(from_date_val)
    to_date = to_date_val.strftime('%d/%m/%Y') if hasattr(to_date_val, 'strftime') else str(to_date_val)
    j_val = req.get('JoiningDate')
    j_date = j_val.strftime('%d/%m/%Y') if j_val and hasattr(j_val, 'strftime') else "__________"
    
    period = "(FN)"
    if j_val and hasattr(j_val, 'hour') and j_val.hour >= 12:
        period = "(AN)"

    text = f"After availing {req.get('LeaveTypeName', '')} from {from_date} to {to_date} (along with prefix and sufix holiday)."
    c.drawString(margin, curr_y, text)
    curr_y -= 0.3*inch
    text2 = f"I hereby submit my joining report today i.e. {j_date} {period}. This is for your information, please."
    c.drawString(margin, curr_y, text2)
    
    curr_y -= 1.5*inch
    c.setFont("Helvetica-Bold", 11)
    c.drawRightString(width - margin, curr_y, f"({req.get('RequesterName', '')})")
    curr_y -= 0.2*inch
    c.drawRightString(width - margin, curr_y, f"{req.get('RequesterCode', '')}")
    
    c.showPage()
    c.save()
    pdf_out = buffer.getvalue()
    buffer.close()
    
    response = make_response(pdf_out)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=Joining_Report_{req_id}.pdf'
    return response

@leave_bp.route('/departure_admin', methods=['GET', 'POST'])
@permission_required('Service Departure from Admin')
def departure_admin():
    user_id = session['user_id']
    emp_id = session.get('emp_id')
    
    if request.method == 'POST':
        req_id = request.form.get('req_id')
        d_date = request.form.get('date')
        period = request.form.get('period')
        remark = request.form.get('remark')
        try:
            if LeaveModel.submit_departure_details(req_id, d_date, period, remark, user_id):
                flash("Departure details submitted successfully.", "success")
            else:
                flash("Failed to submit details.", "danger")
        except Exception as e:
            flash(f"Error: {str(e)}", "danger")
        return redirect(url_for('leave.departure_admin'))

    selected_req = None
    req_id = request.args.get('req_id')
    if req_id:
        res = LeaveModel.get_request_details(req_id)
        if res:
            selected_req = res['master']

    page = request.args.get('page', 1, type=int)
    history, total = LeaveModel.get_ro_departure_list(emp_id, page=page)
    
    pagination = {
        'page': page,
        'total': total,
        'total_pages': math.ceil(total / 10) if total else 1,
        'has_prev': page > 1,
        'has_next': page < math.ceil(total / 10) if total else False,
    }
    return render_template('leave/departure_admin.html', history=history, selected_req=selected_req, pagination=pagination)

@leave_bp.route('/departure_details', methods=['GET', 'POST'])
def service_departure_details():
    user_id = session['user_id']
    emp_id = session.get('emp_id')
    loc_id = session.get('selected_loc')
    
    perm = None
    for caption in ['Service Departure Details', 'Service Departure Status', 'Service Departure from Admin']:
        perm = NavModel.check_permission(user_id, loc_id, caption)
        if perm and perm.get('AllowView'):
            break
    
    if not perm or not perm.get('AllowView'):
        flash("Access Denied: No permission for Service Departure.", "danger")
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        req_id = request.form.get('req_id')
        d_date = request.form.get('departure_date')
        d_remark = request.form.get('departure_remark')
        try:
            if LeaveModel.submit_departure_date(req_id, d_date, d_remark, user_id):
                flash("Departure date submitted successfully.", "success")
            else:
                flash("Failed to submit departure date.", "danger")
        except Exception as e:
            flash(f"Error: {str(e)}", "danger")
        return redirect(url_for('leave.service_departure_details'))

    req_id = request.args.get('req_id')
    selected_req = None
    if req_id:
        res = LeaveModel.get_request_details(req_id)
        if res:
            selected_req = res['master']

    pending = LeaveModel.get_approved_leaves_pending_departure(emp_id)
    history, total = LeaveModel.get_departure_history(emp_id, page=1)
    
    pagination = {
        'page': 1,
        'total': total,
        'total_pages': math.ceil(total / 10) if total else 1,
        'has_prev': False,
        'has_next': total > 10 if total else False,
    }
    return render_template('leave/service_departure_details.html', pending=pending, history=history, selected_req=selected_req, pagination=pagination)

@leave_bp.route('/departure_status')
@permission_required('Service Departure Status')
def service_departure_status():
    emp_id = session.get('emp_id')
    page = request.args.get('page', 1, type=int)
    
    history, total = LeaveModel.get_ro_departure_list(emp_id, page=page)
    
    pagination = {
        'page': page,
        'total': total,
        'total_pages': math.ceil(total / 10) if total else 1,
        'has_prev': page > 1,
        'has_next': page < math.ceil(total / 10) if total else False,
    }
    return render_template('leave/service_departure_status.html', history=history, pagination=pagination)

@leave_bp.route('/departure_report/<req_id>')
def download_departure_report(req_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    emp_id = session.get('emp_id')
    
    res = LeaveModel.get_request_details(req_id)
    if not res:
        return "Report not found", 404
    req = res['master']
    
    if str(req.get('fk_reqempid')) != str(emp_id):
        return "Access denied", 403

    import io
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import inch
    import os

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    margin = 1 * inch
    curr_y = height - margin

    logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'images', 'logo.png')
    if os.path.exists(logo_path):
        c.drawImage(logo_path, width/2 - 0.3*inch, curr_y - 0.6*inch, width=0.6*inch, height=0.6*inch, mask='auto')
    
    curr_y -= 0.8*inch
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(width/2, curr_y, "Chaudhary Charan Singh Haryana Agricultural University,")
    curr_y -= 0.2*inch
    c.drawCentredString(width/2, curr_y, "HISAR")
    
    curr_y -= 0.4*inch
    c.setFont("Helvetica", 11)
    c.drawString(margin, curr_y, "To")
    curr_y -= 0.2*inch
    c.drawString(margin + 0.2*inch, curr_y, "The Assistant Scientist")
    
    curr_y -= 0.5*inch
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin, curr_y, "Subject: Departure Report")
    
    curr_y -= 0.4*inch
    c.setFont("Helvetica", 11)
    
    from_date_val = req.get('fromdate')
    to_date_val = req.get('todate')
    from_date = from_date_val.strftime('%d/%m/%Y') if hasattr(from_date_val, 'strftime') else str(from_date_val)
    to_date = to_date_val.strftime('%d/%m/%Y') if hasattr(to_date_val, 'strftime') else str(to_date_val)
    d_val = req.get('DepartureDate')
    d_date = d_val.strftime('%d/%m/%Y') if d_val and hasattr(d_val, 'strftime') else from_date 
    
    period = "(FN)"
    if d_val and hasattr(d_val, 'hour') and d_val.hour >= 12:
        period = "(AN)"

    text = f"I hereby submit my departure report today i.e dated {d_date} {period} to avail {req.get('LeaveTypeName', '')}"
    c.drawString(margin, curr_y, text)
    curr_y -= 0.2*inch
    total_days = req.get('totalleavedays', 0)
    text2 = f"for {float(total_days):.2f} days from {from_date} to {to_date} along with prefix and suffix holiday."
    c.drawString(margin, curr_y, text2)
    
    curr_y -= 0.3*inch
    c.drawString(margin, curr_y, "This for your information please.")
    
    curr_y -= 0.5*inch
    c.drawString(margin, curr_y, "Thanking you")
    curr_y -= 0.3*inch
    c.drawString(margin, curr_y, "Your faithfully")
    
    curr_y -= 0.5*inch
    c.setFont("Helvetica-Bold", 11)
    c.drawRightString(width - margin, curr_y, "CCSHAU, HISAR")
    
    c.showPage()
    c.save()
    
    pdf_out = buffer.getvalue()
    buffer.close()
    
    response = make_response(pdf_out)
    response.headers['Content-Type'] = 'application/pdf'
    filename = f"Departure_Report_{req_id}.pdf"
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    return response

@leave_bp.route('/approvals', methods=['GET', 'POST'])
@permission_required('Leave Approval')
def approvals():
    user_id = session['user_id']
    emp_id = session.get('emp_id')
    loc_id = session.get('selected_loc')
    perm = NavModel.check_permission(user_id, loc_id, 'Leave Approval')
    
    if request.method == 'POST':
        action = request.form.get('action')
        req_id = request.form.get('req_id')
        comments = request.form.get('comments', '')
        
        try:
            if action == 'M':
                conn = DB.get_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE SAL_Leave_Request_Mst SET leavestatus = 'M', fk_responseby = ?, responsedate = GETDATE() WHERE pk_leavereqid = ?", [user_id, req_id])
                conn.commit()
                conn.close()
                flash("Request Recommended successfully.", "success")
            elif LeaveModel.take_action(req_id, action, user_id, emp_id, comments):
                flash(f"Request {'Approved' if action=='A' else 'Rejected'} successfully.", "success")
            else:
                flash("Action failed.", "danger")
        except Exception as e:
            flash(f"Error: {str(e)}", "danger")
        return redirect(url_for('leave.approvals'))

    selected_req = None
    req_id = request.args.get('req_id')
    if req_id:
        selected_req = LeaveModel.get_request_details(req_id)

    page = request.args.get('page', 1, type=int)
    pending = LeaveModel.get_pending_approvals(emp_id)
    history, total_history = LeaveModel.get_approved_recent(emp_id, page=page)
    
    per_page = 10
    pagination = {
        'page': page,
        'total': total_history,
        'total_pages': math.ceil(total_history / per_page) if total_history else 1,
        'has_prev': page > 1,
        'has_next': page < math.ceil(total_history / per_page) if total_history else False,
    }

    return render_template('leave/leave_approvals.html', 
                           pending=pending, 
                           history=history, 
                           pagination=pagination,
                           perm=perm,
                           selected_req=selected_req)

@leave_bp.route('/adj_approvals', methods=['GET', 'POST'])
@permission_required('Leave Adjustment Approval')
def adj_approvals():
    user_id = session['user_id']
    emp_id = session.get('emp_id')
    loc_id = session.get('selected_loc')
    perm = NavModel.check_permission(user_id, loc_id, 'Leave Adjustment Approval')
    
    if request.method == 'POST':
        action = request.form.get('action')
        adj_id = request.form.get('adj_id')
        comments = request.form.get('comments', '')
        status = 'A' if action == 'APPROVE' else 'R'
        
        try:
            if LeaveModel.take_adj_action(adj_id, status, user_id, emp_id, comments):
                flash("Adjustment request processed.", "success")
            else:
                flash("Error processing request.", "danger")
        except Exception as e:
            flash(f"Error: {str(e)}", "danger")
        return redirect(url_for('leave.adj_approvals'))

    adj_id = request.args.get('adj_id')
    selected_adj = None
    if adj_id:
        pending_all = LeaveModel.get_pending_adj_approvals(emp_id)
        selected_adj = next((item for item in pending_all if str(item.get('adj_id')) == adj_id), None)

    page = request.args.get('page', 1, type=int)
    pending = LeaveModel.get_pending_adj_approvals(emp_id)
    history, total_history = LeaveModel.get_adj_approval_history(emp_id, page=page)
    
    per_page = 10
    pagination = {
        'page': page,
        'total': total_history,
        'total_pages': math.ceil(total_history / per_page) if total_history else 1,
        'has_prev': page > 1,
        'has_next': page < math.ceil(total_history / per_page) if total_history else False,
    }
    
    return render_template('leave/leave_adj_approvals.html', 
                           pending=pending, history=history, perm=perm, 
                           selected_adj=selected_adj, pagination=pagination)

@leave_bp.route('/cancel_approvals', methods=['GET', 'POST'])
@permission_required('Leave Cancel Approval')
def cancel_approvals():
    user_id = session['user_id']
    emp_id = session.get('emp_id')
    loc_id = session.get('selected_loc')
    perm = NavModel.check_permission(user_id, loc_id, 'Leave Cancel Approval')
    
    if request.method == 'POST':
        action = request.form.get('action')
        adj_id = request.form.get('adj_id')
        comments = request.form.get('comments', '')
        status = 'A' if action == 'APPROVE' else 'R'
        
        try:
            if LeaveModel.take_cancel_action(adj_id, status, user_id, emp_id, comments):
                flash("Cancellation request processed.", "success")
            else:
                flash("Error processing request.", "danger")
        except Exception as e:
            flash(f"Error: {str(e)}", "danger")
        return redirect(url_for('leave.cancel_approvals'))

    adj_id = request.args.get('adj_id')
    selected_adj = None
    balances = None
    daywise = None
    if adj_id:
        pending_all = LeaveModel.get_pending_cancel_approvals(emp_id)
        selected_adj = next((item for item in pending_all if str(item.get('adj_id')) == adj_id), None)
        if selected_adj:
            balances = LeaveModel.get_leave_balance(selected_adj.get('requester_empid'))
            taken_res = DB.fetch_one("SELECT fk_leavetakenid FROM SAL_LeaveAdjustmentRequest_Mst WHERE pk_leaveadjreqid = ?", [adj_id])
            if taken_res:
                daywise = LeaveModel.get_leave_daywise_details_by_taken_id(taken_res.get('fk_leavetakenid'))

    page = request.args.get('page', 1, type=int)
    pending = LeaveModel.get_pending_cancel_approvals(emp_id)
    history, total_history = LeaveModel.get_cancel_approval_history(emp_id, page=page)
    
    per_page = 10
    pagination = {
        'page': page,
        'total': total_history,
        'total_pages': math.ceil(total_history / per_page) if total_history else 1,
        'has_prev': page > 1,
        'has_next': page < math.ceil(total_history / per_page) if total_history else False,
    }
    
    return render_template('leave/leave_cancel_approvals.html', 
                           pending=pending, history=history, perm=perm, 
                           selected_adj=selected_adj, balances=balances, daywise=daywise,
                           pagination=pagination)

@leave_bp.route('/assignment', methods=['GET', 'POST'])
@permission_required('Employee Leave Assignment')
def leave_assignment():
    user_id = session['user_id']
    
    selected_ddo = request.form.get('ddo') or request.args.get('ddo')
    selected_loc = request.form.get('location') or request.args.get('location')
    selected_dept = request.form.get('dept') or request.args.get('dept')
    selected_leave = request.form.get('leave_type') or request.args.get('leave_type')
    selected_fin = request.form.get('fin_year') or request.args.get('fin_year')
    selected_emp = request.form.get('emp_id') or request.args.get('emp_id')
    selected_emp_name = request.form.get('emp_name') or request.args.get('emp_name', '')

    leave_types = LeaveModel.get_leave_types(is_admin=True)
    locations = DB.fetch_all("SELECT pk_locid as id, locname as name FROM Location_Mst ORDER BY locname")
    
    ddo_query = "SELECT DISTINCT DM.pk_ddoid as id, DM.Description as name FROM DDO_Mst DM"
    ddo_params = []
    if selected_loc:
        ddo_query += " INNER JOIN DDO_Loc_Mapping LM ON DM.pk_ddoid = LM.fk_ddoid WHERE LM.fk_locid = ?"
        ddo_params.append(selected_loc)
    ddo_query += " ORDER BY DM.Description"
    ddos = DB.fetch_all(ddo_query, ddo_params)

    dept_query = """
        SELECT DISTINCT D.pk_deptid as id, D.description as name
        FROM Department_Mst D
        INNER JOIN SAL_Employee_Mst E ON D.pk_deptid = E.fk_deptid
        WHERE 1=1
    """
    dept_params = []
    if selected_ddo:
        dept_query += " AND E.fk_ddoid = ?"
        dept_params.append(selected_ddo)
    if selected_loc:
        dept_query += " AND E.fk_locid = ?"
        dept_params.append(selected_loc)
    dept_query += " ORDER BY D.description"
    depts = DB.fetch_all(dept_query, dept_params)

    fin_years = NavModel.get_all_fin_years()
    
    if request.method == 'POST':
        action = request.form.get('action')
        emp_ids = request.form.getlist('emp_ids[]')
        days = request.form.get('leave_days', 0)
        
        try:
            if not emp_ids:
                flash("Please select at least one employee.", "warning")
            elif action == 'ASSIGN' or action == 'UPDATE':
                LeaveAssignmentModel.save_assignments(emp_ids, selected_leave, selected_fin, days, user_id)
                flash(f"Successfully {action.lower()}ed leave for {len(emp_ids)} employees.", "success")
            elif action == 'PROCESS':
                LeaveAssignmentModel.process_assignments(emp_ids, selected_leave, selected_fin, user_id)
                flash(f"Successfully processed (locked) leave for {len(emp_ids)} employees.", "success")
            elif action == 'UNPROCESS':
                LeaveAssignmentModel.unprocess_assignments(emp_ids, selected_leave, selected_fin)
                flash(f"Successfully unprocessed (unlocked) leave for {len(emp_ids)} employees.", "success")
        except Exception as e:
            flash(f"Error: {str(e)}", "danger")

    unassigned = []
    assigned = []
    if selected_leave and selected_fin and (selected_ddo or selected_loc or selected_dept or selected_emp):
        unassigned = LeaveAssignmentModel.get_unassigned_employees(selected_leave, selected_fin, selected_ddo, selected_loc, selected_dept, selected_emp)
        assigned = LeaveAssignmentModel.get_assigned_employees(selected_leave, selected_fin, selected_ddo, selected_loc, selected_dept, selected_emp)

    return render_template('leave/leave_assignment.html',
                           ddos=ddos, locations=locations, depts=depts, fin_years=fin_years, leave_types=leave_types,
                           unassigned=unassigned, assigned=assigned,
                           selected_leave=selected_leave, selected_fin=selected_fin,
                           selected_ddo=selected_ddo, selected_loc=selected_loc,
                           selected_dept=selected_dept, selected_emp=selected_emp,
                           selected_emp_name=selected_emp_name)

@leave_bp.route('/type_master', methods=['GET', 'POST'])
@permission_required('Leave Type Master')
def leave_type_master():
    user_id = session['user_id']
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'SAVE':
            try:
                data = {
                    'pk_leaveid': request.form.get('pk_leaveid'),
                    'name': request.form.get('name'),
                    'short': request.form.get('short'),
                    'nature': request.form.get('nature'),
                    'gender': request.form.get('gender'),
                    'remarks': request.form.get('remarks')
                }
                LeaveConfigModel.save_leave_type(data, user_id)
                flash("Leave type details saved successfully.", "success")
            except Exception as e:
                flash(f"Error: {str(e)}", "danger")
        return redirect(url_for('leave.leave_type_master'))

    types = LeaveConfigModel.get_leave_types_full()
    natures = NavModel.get_natures()
    
    selected_id = request.args.get('leave_id')
    details = []
    if selected_id:
        details = LeaveConfigModel.get_leave_type_details(selected_id)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify(details)

    return render_template('leave/leave_type_master.html', leave_types=types, natures=natures, details=details)

@leave_bp.route('/report/transactions')
@permission_required('Leave Transaction Reports')
def leave_report_transactions():
    filters = {
        'from_date': request.args.get('from_date'),
        'to_date': request.args.get('to_date'),
        'emp_id': request.args.get('emp_id'),
        'leave_id': request.args.get('leave_id'),
        'ddo_id': request.args.get('ddo_id')
    }
    selected_emp_name = request.args.get('emp_name', '')
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    total = LeaveReportModel.get_leave_transactions_count(filters)
    per_page = 20
    offset = (page - 1) * per_page
    sql_limit = f"OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY"
    
    pagination = {
        'page': page,
        'per_page': per_page,
        'total': total,
        'total_pages': math.ceil(total / per_page) if total else 1,
        'has_prev': page > 1,
        'has_next': total > page * per_page,
    }

    transactions = LeaveReportModel.get_leave_transactions(filters, sql_limit)
    leave_types = LeaveModel.get_leave_types(is_admin=True)
    ddos = DB.fetch_all("SELECT pk_ddoid as id, Description as name FROM DDO_Mst ORDER BY Description")
    
    return render_template('leave/report_transactions.html', 
                           transactions=transactions, 
                           leave_types=leave_types, 
                           ddos=ddos, 
                           filters=filters,
                           selected_emp_name=selected_emp_name,
                           pagination=pagination)

@leave_bp.route('/report/el_reconciliation')
@permission_required('Leave Reconcilliation Report')
def leave_report_el_reconciliation():
    emp_id = request.args.get('emp_id')
    results = LeaveReportModel.get_el_reconciliation(emp_id)
    return render_template('leave/report_el_reconciliation.html', results=results, selected_emp=emp_id)

@leave_bp.route('/report/emp_details')
@permission_required('Employee Leave Details')
def employee_leave_details():
    emp_id = request.args.get('emp_id')
    details = []
    summary = []
    if emp_id:
        # In a real system, this would fetch comprehensive leave history for the employee
        details, _ = LeaveModel.get_leaves_taken(emp_id, page=1, per_page=100)
        summary = LeaveModel.get_leave_summary(emp_id)
    
    return render_template('leave/report_employee_leave_details.html', 
                           details=details, 
                           summary=summary, 
                           selected_emp=emp_id)

@leave_bp.route('/update_el', methods=['GET', 'POST'])
@permission_required('Update Earned Leave Balance')
def leave_update_el():
    user_id = session['user_id']
    if request.method == 'POST':
        emp_id = request.form.get('emp_id')
        if not emp_id:
            flash("Please select an employee.", "warning")
        else:
            try:
                if LeaveReportModel.update_el_balance(emp_id, user_id):
                    flash("EL balance updated successfully based on 1/11 logic.", "success")
                else:
                    flash("No new days to calculate for this employee.", "info")
            except Exception as e:
                flash(f"Error: {str(e)}", "danger")
        return redirect(url_for('leave.leave_update_el'))

    return render_template('leave/update_el_balance.html')

@leave_bp.route('/workflow', methods=['GET', 'POST'])
@permission_required('Leave Work Flow')
def leave_workflow():
    user_id = session['user_id']
    if request.method == 'POST':
        emp_id = request.form.get('emp_id')
        approver_id = request.form.get('approver_id')
        if not emp_id or not approver_id:
            flash("Please select both Employee and Reporting Officer.", "warning")
        else:
            try:
                if LeaveConfigModel.update_workflow(emp_id, approver_id, user_id):
                    flash("Workflow updated successfully.", "success")
                else:
                    flash("Failed to update workflow.", "danger")
            except Exception as e:
                flash(f"Error: {str(e)}", "danger")
        return redirect(url_for('leave.leave_workflow'))

    approvers = LeaveConfigModel.get_approvers()
    return render_template('leave/leave_workflow.html', approvers=approvers)

@leave_bp.route('/encashment', methods=['GET', 'POST'])
@permission_required('Leave Encashment')
def leave_encashment():
    user_id = session['user_id']
    emp_id = request.args.get('emp_id')
    
    if request.method == 'POST':
        try:
            data = {
                'emp_id': request.form.get('emp_id'),
                'leave_id': request.form.get('leave_id'),
                'days': request.form.get('days'),
                'basic': request.form.get('basic'),
                'amount': request.form.get('amount'),
                'remarks': request.form.get('remarks')
            }
            LeaveEncashmentModel.apply_encashment(data, user_id)
            flash("Leave encashment record created.", "success")
        except Exception as e:
            flash(f"Error: {str(e)}", "danger")
        return redirect(url_for('leave.leave_encashment', emp_id=request.form.get('emp_id')))

    history = []
    balances = []
    if emp_id:
        history = LeaveEncashmentModel.get_encashment_history(emp_id)
        balances = LeaveModel.get_leave_balance(emp_id)

    return render_template('leave/leave_encashment.html', history=history, balances=balances, selected_emp=emp_id)

@leave_bp.route('/common_holiday_master', methods=['GET', 'POST'])
@permission_required('Common Holidays Master')
def common_holiday_master():
    if request.method == 'POST':
        data = {
            'id': request.form.get('id'),
            'type_id': request.form.get('type_id'),
            'name': request.form.get('name'),
            'order': request.form.get('order'),
            'remarks': request.form.get('remarks')
        }
        try:
            if HolidayModel.save_common_holiday(data):
                flash("Holiday saved successfully.", "success")
        except Exception as e:
            flash(f"Error: {str(e)}", "danger")
        return redirect(url_for('leave.common_holiday_master'))
    
    holidays = HolidayModel.get_common_holidays()
    types = HolidayModel.get_holiday_types()
    return render_template('leave/master_common_holiday.html', holidays=holidays, types=types)

@leave_bp.route('/holiday_location_master', methods=['GET', 'POST'])
@permission_required('Holiday Location Master')
def holiday_location_master():
    if request.method == 'POST':
        data = {
            'id': request.form.get('id'),
            'name': request.form.get('name'),
            'order': request.form.get('order'),
            'remarks': request.form.get('remarks')
        }
        try:
            if HolidayModel.save_holiday_location(data):
                flash("Location saved successfully.", "success")
        except Exception as e:
            flash(f"Error: {str(e)}", "danger")
        return redirect(url_for('leave.holiday_location_master'))
    
    locations = HolidayModel.get_holiday_locations()
    return render_template('leave/master_holiday_location.html', locations=locations)

@leave_bp.route('/loc_wise_holiday_master', methods=['GET', 'POST'])
@permission_required('Location Wise Holidays Master')
def loc_wise_holiday_master():
    user_id = session['user_id']
    if request.method == 'POST':
        action = request.form.get('action')
        try:
            if action == 'SAVE':
                data = {
                    'pk_locholidayid': request.form.get('pk_locholidayid'),
                    'holiday_loc_id': request.form.get('holiday_loc_id'),
                    'year_id': request.form.get('year_id'),
                    'loc_id': request.form.get('loc_id'),
                    'remarks': request.form.get('remarks')
                }
                loc_holiday_id = HolidayModel.save_loc_wise_holiday(data, user_id)
                
                # Handle details if submitted in lists
                h_ids = request.form.getlist('h_ids[]')
                f_dates = request.form.getlist('f_dates[]')
                t_dates = request.form.getlist('t_dates[]')
                h_remarks = request.form.getlist('h_remarks[]')
                
                if h_ids:
                    for i in range(len(h_ids)):
                        if i < len(f_dates) and f_dates[i]: 
                            detail_data = {
                                'loc_holiday_id': loc_holiday_id,
                                'common_holiday_id': h_ids[i],
                                'holiday_date': f_dates[i],
                                'to_date': t_dates[i] if i < len(t_dates) else None,
                                'remarks': h_remarks[i] if i < len(h_remarks) else ''
                            }
                            exists = DB.fetch_one("SELECT pk_locholidaytrnid FROM SAL_LocationWiseHolidays_Trn WHERE fk_locholidayid=? AND fk_commonholidayid=?", 
                                                [loc_holiday_id, h_ids[i]])
                            if exists:
                                detail_data['pk_locholidaytrnid'] = exists['pk_locholidaytrnid']
                            
                            HolidayModel.save_loc_holiday_detail(detail_data, user_id)
                
                flash("Location-wise holiday and details saved.", "success")
            elif action == 'SAVE_DETAIL':
                data = {
                    'pk_locholidaytrnid': request.form.get('pk_locholidaytrnid'),
                    'loc_holiday_id': request.form.get('loc_holiday_id'),
                    'common_holiday_id': request.form.get('common_holiday_id'),
                    'holiday_date': request.form.get('holiday_date'),
                    'to_date': request.form.get('to_date'),
                    'remarks': request.form.get('detail_remarks')
                }
                HolidayModel.save_loc_holiday_detail(data, user_id)
                flash("Holiday detail saved.", "success")
            elif action == 'DELETE':
                DB.execute("DELETE FROM SAL_LocationWiseHolidays_Trn WHERE fk_locholidayid = ?", [request.form.get('id')])
                DB.execute("DELETE FROM SAL_LocationWiseHolidays_Mst WHERE pk_locholidayid = ?", [request.form.get('id')])
                flash("Location-wise holiday deleted.", "success")
            elif action == 'DELETE_DETAIL':
                HolidayModel.delete_loc_holiday_detail(request.form.get('trn_id'))
                flash("Holiday detail deleted.", "success")
        except Exception as e:
            flash(f"Error: {str(e)}", "danger")
        # To avoid confusion, redirect without specific filters or ensure parameter names match the GET expected ones
        return redirect(url_for('leave.loc_wise_holiday_master', hloc_id=request.form.get('holiday_loc_id'), lyear=request.form.get('year_id')))

    hloc_id = request.args.get('hloc_id') # Filter for Holiday Location (Int)
    lyear = request.args.get('lyear')
    univ_loc_id = request.args.get('univ_loc_id') # Filter for University Location (Varchar)
    
    # Fallback for old templates or links using 'loc_id'
    if not hloc_id and request.args.get('loc_id'):
        raw_val = request.args.get('loc_id')
        if str(raw_val).isdigit():
            hloc_id = raw_val
        else:
            univ_loc_id = raw_val

    holidays = HolidayModel.get_loc_wise_holidays(hloc_id=hloc_id, lyear=lyear, univ_loc_id=univ_loc_id)
    locations = DB.fetch_all("SELECT pk_locid as id, locname as name FROM Location_Mst ORDER BY locname")
    holiday_locations = HolidayModel.get_holiday_locations()
    years = NavModel.get_years()
    common_holidays = HolidayModel.get_common_holidays()
    
    selected_locholiday_id = request.args.get('locholiday_id')
    holiday_details = []
    if selected_locholiday_id:
        holiday_details = HolidayModel.get_loc_holiday_details(selected_locholiday_id)
    
    return render_template('leave/master_loc_wise_holiday.html', 
                           holidays=holidays, 
                           locations=locations, 
                           holiday_locations=holiday_locations,
                           years=years,
                           common_holidays=common_holidays,
                           holiday_details=holiday_details,
                           selected_locholiday_id=selected_locholiday_id,
                           selected_loc=hloc_id or univ_loc_id,
                           selected_year=lyear)

@leave_bp.route('/weekly_off_master', methods=['GET', 'POST'])
@permission_required('Weekly Off Master')
def weekly_off_master():
    return render_template('leave/master_weekly_off.html')

@leave_bp.route('/extend_request', methods=['GET', 'POST'])

@permission_required('Leave Extend Request')

def leave_extend_request():

    user_id = session['user_id']

    emp_id = session.get('emp_id')

    loc_id = session.get('selected_loc')

    

    if request.method == 'POST':

        try:

            req_id = request.form.get('req_id')

            extend_to = request.form.get('extend_date')

            reason = request.form.get('reason')

            

            # Fetch original request details

            res = LeaveModel.get_request_details(req_id)

            if not res:

                flash("Original request not found.", "danger")

                return redirect(url_for('leave.leave_extend_request'))

            

            orig = res['master']

            

            # New From Date is next day of original To Date

            from_dt = orig['todate'] + timedelta(days=1)

            

            # Calculate days for the extension period

            total_days = (datetime.strptime(extend_to, '%Y-%m-%d') - from_dt).days + 1

            

            if total_days <= 0:

                flash("Extension date must be after original to-date.", "warning")

                return redirect(url_for('leave.leave_extend_request'))



            data = {

                'emp_id': emp_id,

                'leave_id': orig['fk_leaveid'],

                'from_date': from_dt.strftime('%Y-%m-%d'),

                'to_date': extend_to,

                'total_days': total_days,

                'leave_days': total_days, # Simplification

                'reason': f"Extension: {reason}",

                'contact': orig['contactno'],

                'reporting_to': orig['fk_reportingto'],

                'loc_id': loc_id,

                'extend_id': req_id # Pass this to link

            }

            

            new_req_id = LeaveModel.save_leave_request(data, user_id)

            flash(f"Extension request submitted successfully. New Request ID: {new_req_id}", "success")

        except Exception as e:

            flash(f"Error: {str(e)}", "danger")

        return redirect(url_for('leave.leave_extend_request'))

    

    approved_leaves = LeaveModel.get_approved_leaves_for_adj(emp_id)

    return render_template('leave/leave_extend_request.html', leaves=approved_leaves)
