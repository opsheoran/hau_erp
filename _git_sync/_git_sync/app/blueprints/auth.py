from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.models import AuthModel, NavModel

auth_bp = Blueprint('auth', __name__)

PORTAL_MENU_CONFIG = {
    'HRMS': {
        'Main Menu': {
            'HRMS': [
                'My Profile', 'Download Salary Slip', 'Download Document', 'Employee Qualification Details',
                'Download Service Book', 'Employee Abroad Visit Details', 'Leave Request', 'Leave Approval',
                'Leave Transaction', 'Leave Cancel Request', 'Leave Cancel Approval', 'Leave Adjustment Request',
                'Service Joining Date', 'Service Joining Status', 'Cancel Approved Leaves', 'Service Departure Details',
                'Leave Request Verification', 'GPF/CPF/NPS Detail', 'Service Departure Status', 
                'Service Departure from Admin', 'Loan Apply', 'Employee Award Details', 'Insurance Transaction',
                'Income Tax Certificate', 'Leave & Task Alerts', 'Employee Task List', 'Apply for LTC',
                'TA Bill', 'Investment Document Detail', 'House Rent Detail Submission', 'Employee Memo Details',
                'Employee Retirement No-Dues Verification', 'Form 16', 'Tax Declaration Form', 
                'Tax Declaration Approval Form', 'Promotion Request', 'Promotion Approval', 'IQAC Meeting Proceed',
                'Request For Pension', 'Request For Transfer', 'Request For Education Allowance',
                'Employee Pending Request', 'Initiate Case for ACP', 'ACP Pending Approval', 
                'Service Joining from Admin', 'Annual Property Return Form', 'Annual Property Return Approval Form'
            ]
        }
    },
    'Poll': {
        'Main Menu': {
            'Poll': [
                'Create New Poll', 'Edit/Update Poll', 'Poll Result', 'Current Poll'
            ]
        }
    },
    'Learning Management': {
        'Main Menu': {
            'Learning Management': [
                'View Assigned Courses', 'Manage Course Plan', 'Employee Time Table',
                'Manage Course Weekly Contents', 'View Course Wise Student List',
                'Create & Manage Notice', 'Student List'
            ]
        }
    },
    'SAR': {
        'Main Menu': {
            'SAR': [
                'SAR Form', 'SAR Reviewed Form', 'Confidential Certificate', 'ACR ClassD Performa',
                'ACR Form', 'SAR Report', 'SAR Report Controller', 'Teacher Assessment Performa',
                'SAR Undo Submit', 'Approval Performa', 'Grade A Performa', 'Employee SAR Status'
            ]
        }
    }
}

@auth_bp.route('/splash')
def splash():
    session['splash_shown'] = True
    return render_template('auth/splash.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # If splash screen hasn't been shown in this session, redirect to it
    if not session.get('splash_shown'):
        return redirect(url_for('auth.splash'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = AuthModel.authenticate(username, password)
        
        if user:
            session.permanent = True
            session['user_id'] = user['pk_userId']
            session['user_name'] = user['empname'] or user['name']
            session['login_name'] = user['loginname']
            session['role'] = user['rolename']
            session['emp_id'] = user['pk_empid']
            session['photo'] = user['photo']
            
            # Live behavior: prefer explicit default login location set for the user,
            # then fall back to employee's current location.
            default_loc = user.get('fk_defaultlocation') or user.get('DefaultLocID')
            session['default_loc'] = default_loc
            
            # AUTOMATICALLY SELECT LOCATION
            if default_loc:
                session['selected_loc'] = str(default_loc)
            else:
                # Fallback to first assigned if no default set
                assigned = NavModel.get_assigned_locations(user['pk_userId'])
                if assigned:
                    session['selected_loc'] = str(assigned[0]['id'])
            
            # Log login
            AuthModel.log_login(user['pk_userId'], request.remote_addr)
            
            # Always start at My Modules (Modules Grid)
            session.pop('current_module_id', None) 
            return redirect(url_for('main.index'))
        else:
            flash('Invalid Username or Password', 'danger')
            
    return render_template('auth/login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))
