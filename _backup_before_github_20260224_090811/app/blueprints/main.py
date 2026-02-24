from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from app.models import NavModel
from app.db import DB
from app.utils import get_page_url

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    user_id = session['user_id']
    emp_id = session.get('emp_id')
    
    # Handle Location Switching
    loc_id = request.args.get('loc_id')
    if loc_id:
        session['selected_loc'] = str(loc_id)
        session.pop('current_module_id', None)
        session.pop('ui_mode', None)
        return redirect(url_for('main.index'))

    selected_loc = session.get('selected_loc')
    locations = NavModel.get_assigned_locations(user_id)
    if not selected_loc and locations:
        selected_loc = session.get('default_loc') or locations[0]['id']
        session['selected_loc'] = str(selected_loc)
    
    if selected_loc: selected_loc = str(selected_loc)

    # Handle Module Selection
    mod_id = request.args.get('module_id')
    if mod_id and str(mod_id).isdigit():
        session['current_module_id'] = mod_id
        # Set UI Mode based on module
        mod = DB.fetch_one("SELECT modulename FROM UM_Module_Mst WHERE pk_moduleId = ?", [mod_id])
        if mod and mod['modulename'].strip() in ['Employee Portal', 'HRMS', 'Leave Management']:
            session['ui_mode'] = 'portal'
        else:
            session['ui_mode'] = 'standard'
        return redirect(url_for('main.index'))

    current_mod_id = session.get('current_module_id')
    modules = NavModel.get_user_modules(user_id, selected_loc)
    
    # Stage 1: My Modules Selection Grid
    if not current_mod_id:
        return render_template('main/modules_grid.html', 
                               locations=locations, 
                               selected_loc=selected_loc,
                               modules=modules)
    
    current_mod = next((m for m in modules if str(m['pk_moduleId']) == str(current_mod_id)), None)
    
    # Fetch all rights for the selected module to display in standard dashboard
    all_rights = NavModel.get_user_page_rights(user_id, selected_loc)
    for r in all_rights:
        r['url'] = get_page_url(r['PageName'])

    pending_leaves = 0
    if emp_id:
        fy = NavModel.get_current_fin_year()
        d1, d2 = fy['date1'], fy['date2']
        pending_leaves = DB.fetch_scalar("""
            SELECT COUNT(*) FROM SAL_Leave_Request_Mst 
            WHERE fk_reportingto = ? AND leavestatus = 'S'
            AND fromdate BETWEEN ? AND ?
        """, [emp_id, d1, d2])
    
    # Stage 2: Module Dashboard / Landing Page
    # For Academics and Examination, we want ONLY the menus to show, so we return a clean template
    if str(current_mod_id) in ['55', '56']:
        return render_template('main/dashboard_clean.html', current_mod=current_mod)

    # Render dashboard based on mode for other modules
    if session.get('ui_mode') == 'portal':
        template = 'hrms/employee_portal.html'
    else:
        template = 'main/module_dashboard.html'
    
    return render_template(template, 
                           locations=locations, 
                           selected_loc=selected_loc,
                           current_mod=current_mod,
                           all_rights=all_rights,
                           pending_leaves=pending_leaves)

@main_bp.route('/reset_module')
def reset_module():
    session.pop('current_module_id', None)
    session.pop('ui_mode', None)
    return redirect(url_for('main.index'))

@main_bp.route('/api/pending_leaves_count')
def pending_leaves_count():
    emp_id = session.get('emp_id')
    if not emp_id: return jsonify({'count': 0})
    
    fy = NavModel.get_current_fin_year()
    d1, d2 = fy['date1'], fy['date2']
    
    count = DB.fetch_scalar("""
        SELECT COUNT(*) FROM SAL_Leave_Request_Mst 
        WHERE fk_reportingto = ? AND leavestatus = 'S' 
        AND fromdate BETWEEN ? AND ?
    """, [emp_id, d1, d2])
    return {'count': count or 0}
