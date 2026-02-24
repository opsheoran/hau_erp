from flask import Flask, session, request, abort, get_flashed_messages
from flask_session import Session
import os
import secrets
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
secret_key = os.getenv('SECRET_KEY')
if not secret_key:
    raise RuntimeError('SECRET_KEY is required')
app.secret_key = secret_key

# --- SERVER-SIDE SESSION CONFIGURATION ---
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = os.path.join(os.getcwd(), 'sessions')
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = os.getenv('SESSION_COOKIE_SECURE', 'false').lower() == 'true'
Session(app)

# Import and Register Blueprints
from app.blueprints.auth import auth_bp
from app.blueprints.main import main_bp
from app.blueprints.hrms import hrms_bp
from app.blueprints.leave import leave_bp
from app.blueprints.establishment import establishment_bp
from app.blueprints.payroll import payroll_bp
from app.blueprints.umm import umm_bp
from app.blueprints.academics import academics_bp
from app.blueprints.academics_mgmt import academics_mgmt_bp
from app.blueprints.course_allocation import course_allocation_bp
from app.blueprints.examination import examination_bp

app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(main_bp) # Main remains at root
app.register_blueprint(hrms_bp, url_prefix='/hrms')
app.register_blueprint(leave_bp, url_prefix='/leave')
app.register_blueprint(establishment_bp, url_prefix='/establishment')
app.register_blueprint(payroll_bp, url_prefix='/payroll')
app.register_blueprint(umm_bp, url_prefix='/umm')
app.register_blueprint(academics_bp, url_prefix='/academics')
app.register_blueprint(academics_mgmt_bp, url_prefix='/academics')
app.register_blueprint(course_allocation_bp, url_prefix='/academics')
app.register_blueprint(examination_bp, url_prefix='/examination')

# Global context processor for persistent navigation
from app.db import DB, teardown_db
from app.models import NavModel
from app.utils import get_page_url
from flask import url_for

app.teardown_appcontext(teardown_db)

@app.before_request
def csrf_init():
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_urlsafe(32)
        session.modified = True

@app.before_request
def normalize_double_prefixed_paths():
    # Backward-compat for mistakenly generated URLs like /umm/umm/...
    # Normalize to /umm/... so users don't see blank pages or template errors.
    from flask import redirect
    p = request.path or ''
    for seg in ('umm', 'establishment', 'hrms', 'leave', 'payroll', 'academics', 'examination', 'auth'):
        double = f"/{seg}/{seg}/"
        if p.startswith(double):
            return redirect(p.replace(double, f"/{seg}/", 1), code=302)
    return None

@app.before_request
def csrf_protect():

    if request.method in ('POST', 'PUT', 'PATCH', 'DELETE'):
        # Skip only if explicitly exempted.
        if getattr(request.endpoint and app.view_functions.get(request.endpoint), '_csrf_exempt', False):
            return None
        
        token = session.get('_csrf_token')
        submitted = request.form.get('_csrf_token') or request.headers.get('X-CSRF-Token')
        
        if not token or not submitted or token != submitted:
            # Descriptive error for developer (visible in browser during debug)
            abort(400, description=f"CSRF Error: Session Token {'Missing' if not token else 'Present'}, Submitted Token {'Missing' if not submitted else 'Present'}. Please refresh the page.")

@app.context_processor
def inject_csrf_token():
    return {'csrf_token': session.get('_csrf_token')}

@app.context_processor
def inject_navigation():
    # Skip for static assets
    if request.path.startswith('/static'):
        return {}
    
    from app.blueprints.academics import ACADEMIC_MENU_CONFIG
    from app.blueprints.umm import UMM_MENU_CONFIG
    from app.utils import get_page_url, PAGE_URL_MAPPING

    NAV_CACHE_VERSION = '2026-02-20-nav-v2'

    # Template context variables
    ctx = {
        'menu': {},
        'current_mod': None,
        'current_mod_icon': None,
        'announcements': [],
        'pending_leaves_count': 0,
        'assigned_modules': [],
        'current_mod_id': session.get('current_module_id'),
        'get_page_url': get_page_url,
        'processed_academic_menu': [],
        'processed_umm_menu': [],
        'academic_tabs': [],
        'umm_tabs': [],
        'academic_breadcrumb': [],
        'umm_breadcrumb': [],
        # Default so templates never crash if a route forgets to pass pagination
        'pagination': {'page': 1, 'per_page': 10, 'total': 0, 'total_pages': 1, 'has_prev': False, 'has_next': False}
    }

    module_icon_map = {
        'Admission & Academics': 'Admission_Academics.png',
        'Employee Portal': 'Employee_Portal.png',
        'Financial Accounts': 'Financial_Accounts.png',
        'PF': 'PF.png',
        'Research': 'Research.png',
        'Student Attendance': 'Student_Attendance.png',
        'Agriculture Farm Management': 'Agriculture_Farm_Management.png',
        'Establishment': 'Establishment.png',
        'HRMS': 'HRMS.png',
        'PreAdmission': 'PreAdmission.png',
        'RTI': 'RTI.png',
        'Tax Management': 'Tax_Management.png',
        'Bill Tracking': 'Bill_Tracking.png',
        'Examination & Results': 'Examination_Results.png',
        'Leave Management': 'Leave_Management.png',
        'Pre-Examination': 'Pre_Examination.png',
        'SAR Module': 'SAR_Module.png',
        'User Management': 'User_Management.png',
        'Budget Management': 'Budget_Management.png',
        'Fee Management': 'Fee_Management.png',
        'Pension Management': 'Pension_Management.png'
    }

    def _norm(s):
        # Case-insensitive normalization for caption matching between DB and menu configs.
        return " ".join(str(s or "").strip().split()).lower()

    if 'user_id' not in session:
        return ctx
    
    user_id = session['user_id']
    emp_id = session.get('emp_id')
    selected_loc = session.get('selected_loc')
    current_mod_id = ctx['current_mod_id']
    
    if not selected_loc:
        return ctx

    all_rights = session.get('current_user_rights')
    
    if not all_rights or session.get('cached_loc') != selected_loc:
        all_rights = NavModel.get_user_page_rights(user_id, selected_loc)
        session['current_user_rights'] = all_rights
        session['cached_loc'] = selected_loc

    if current_mod_id and str(current_mod_id).isdigit():
        ctx['current_mod'] = DB.fetch_one("SELECT pk_moduleId, modulename FROM UM_Module_Mst WHERE pk_moduleId = ?", [current_mod_id])
        if ctx['current_mod']:
            m_name = ctx['current_mod']['modulename'].strip()
            for key, icon in module_icon_map.items():
                if key.lower() in m_name.lower() or m_name.lower() in key.lower():
                    ctx['current_mod_icon'] = icon
                    break

    ctx['assigned_modules'] = NavModel.get_user_modules(user_id, selected_loc)

    # MENU ENGINE
    menu = {}
    if current_mod_id:
        def build_configured_menu(config, all_rights):
            is_super = NavModel._is_super_admin(user_id)
            allowed_pages = {r['PageName'] for r in all_rights if r['AllowView']}
            allowed_pages_norm = {_norm(p) for p in allowed_pages}
            built_menu = {}
            for main_cat, subs in config.items():
                cat_obj = {'subs': [], 'pages': []}
                for sub_cat, sub_subs in subs.items():
                    # Check if 'sub_subs' is actually a list (flat) or a dict (nested folders)
                    if isinstance(sub_subs, list):
                        visible_pages = []
                        for p in sub_subs:
                            if is_super or _norm(p) in allowed_pages_norm:
                                visible_pages.append({'name': p, 'url': get_page_url(p)})
                        if visible_pages:
                            # If sub_cat is "Main Menu", we might want to put pages directly in cat_obj.pages
                            if sub_cat == 'Main Menu':
                                cat_obj['pages'].extend(visible_pages)
                            else:
                                cat_obj['subs'].append({
                                    'name': sub_cat,
                                    'url': visible_pages[0]['url'],
                                    'pages': visible_pages
                                })
                    elif isinstance(sub_subs, dict):
                        for folder_name, pages in sub_subs.items():
                            visible_pages = []
                            for p in pages:
                                if is_super or _norm(p) in allowed_pages_norm:
                                    visible_pages.append({'name': p, 'url': get_page_url(p)})
                            if visible_pages:
                                # If folder name matches the main category or is "Main Menu", 
                                # pull pages up to the top level to avoid double menu entries.
                                if _norm(folder_name) == _norm(main_cat) or _norm(folder_name) == 'main menu':
                                    cat_obj['pages'].extend(visible_pages)
                                else:
                                    cat_obj['subs'].append({
                                        'name': folder_name,
                                        'url': visible_pages[0]['url'],
                                        'pages': visible_pages
                                    })
                if cat_obj['subs'] or cat_obj['pages']:
                    built_menu[main_cat] = cat_obj
            return built_menu

        if str(current_mod_id) == '30':
            menu = {}
        elif str(current_mod_id) == '55':
            from app.blueprints.academics import ACADEMIC_MENU_CONFIG
            menu = build_configured_menu(ACADEMIC_MENU_CONFIG, all_rights)
        elif str(current_mod_id) == '56':
            from app.blueprints.examination import EXAMINATION_MENU_CONFIG
            menu = build_configured_menu(EXAMINATION_MENU_CONFIG, all_rights)
        elif str(current_mod_id) == '75':
            from app.blueprints.leave import LEAVE_MENU_CONFIG
            menu = build_configured_menu(LEAVE_MENU_CONFIG, all_rights)
        elif str(current_mod_id) == '63':
            from app.blueprints.auth import PORTAL_MENU_CONFIG
            menu = build_configured_menu(PORTAL_MENU_CONFIG, all_rights)
        else:
            # Truly Recursive N-Tier Builder
            all_pages = [r for r in all_rights if str(r['fk_moduleId']) == str(current_mod_id) and r['AllowView']]
            for p in all_pages:
                p['pk_webpageId'] = str(p['pk_webpageId'])
                p['parentId'] = str(p['parentId']) if p['parentId'] is not None and str(p['parentId']) != 'None' else '0'
            
            pages_by_parent = {}
            for p in all_pages:
                pid = p['parentId']
                if pid not in pages_by_parent:
                    pages_by_parent[pid] = []
                pages_by_parent[pid].append(p)

            def build_recursive(pid):
                node = {'pages': [], 'subs': []}
                for p in pages_by_parent.get(pid, []):
                    if p['pk_webpageId'] in pages_by_parent:
                        child_node = build_recursive(p['pk_webpageId'])
                        node['subs'].append({
                            'name': p['PageName'],
                            'pages': child_node['pages'],
                            'subs': child_node['subs']
                        })
                    else:
                        page_name = p.get('PageName')
                        node['pages'].append({'name': page_name, 'url': get_page_url(page_name)})
                return node

            root = build_recursive('0')
            menu = {}
            for sub in root['subs']:
                menu[sub['name']] = {'pages': sub['pages'], 'subs': sub['subs']}
            if root['pages']:
                menu['General'] = {'pages': root['pages'], 'subs': []}

    ctx['menu'] = menu

    if emp_id:
        fy = NavModel.get_current_fin_year()
        if fy:
            ctx['pending_leaves_count'] = DB.fetch_scalar(
                "SELECT COUNT(*) FROM SAL_Leave_Request_Mst WHERE fk_reportingto = ? AND leavestatus = 'S' AND fromdate BETWEEN ? AND ?",
                [emp_id, fy['date1'], fy['date2']]
            )

    # BREADCRUMBS & TABS LOGIC (Calculated on every request)
    ctx['academic_breadcrumb'] = []
    ctx['academic_tabs'] = []
    ctx['processed_academic_menu'] = []
    ctx['umm_tabs'] = []
    ctx['establishment_tabs'] = []
    ctx['processed_establishment_menu'] = []
    ctx['establishment_breadcrumb'] = []
    ctx['leave_tabs'] = []
    ctx['processed_leave_menu'] = []
    ctx['leave_breadcrumb'] = []
    
    allowed_pages = {r['PageName'] for r in all_rights if r['AllowView']}
    allowed_pages_norm = {_norm(p) for p in allowed_pages}
    
    current_page = None
    if request.endpoint:
        # Reverse lookup from PAGE_URL_MAPPING
        for p_name, endpoint in PAGE_URL_MAPPING.items():
            if endpoint == request.endpoint:
                if endpoint == 'academics.generic_page_handler':
                    if request.view_args.get('page_name') == p_name:
                        current_page = p_name
                        break
                else:
                    current_page = p_name
                    break
        
        if not current_page and 'generic_page_handler' in request.endpoint:
            current_page = request.view_args.get('page_name')

        # Disambiguate pages that share the same caption across modules.
        if request.endpoint == 'umm.department_master':
            current_page = 'Department Master'
        
        # Establishment specific disambiguation
        if str(session.get('current_module_id')) == '72':
            mapping = {
                'establishment.category_master': 'Category Master',
                'establishment.religion_master': 'Religion Master',
                'establishment.class_master': 'Class Master',
                'establishment.section_master': 'Section Master',
                'establishment.department_master': 'Department Master',
                'establishment.designation_master': 'Designation Master',
                'establishment.marital_status_master': 'Marital Status Master',
                'establishment.fund_sponsor_master': 'Funds Sponsor Master',
                'establishment.exam_type_master': 'ExamType Master',
                'establishment.designation_category_master': 'Designation Category Master'
            }
            if request.endpoint in mapping:
                current_page = mapping[request.endpoint]

    # Provide per-page permission info to templates (for UI control)
    ctx['perm'] = NavModel.check_permission(user_id, selected_loc, current_page) if current_page else None

    # Expose for templates/partials
    ctx['current_page'] = current_page
    ctx['allowed_pages'] = allowed_pages
    ctx['all_rights'] = all_rights

    # Build Top Menu AND Detect Active Tab Group
    if str(current_mod_id) in ['30', '55', '72', '75']:
        is_super = NavModel._is_super_admin(user_id)
        if str(current_mod_id) == '30':
            config = UMM_MENU_CONFIG
            processed_menu_key = 'processed_umm_menu'
            tabs_key = 'umm_tabs'
            breadcrumb_key = 'umm_breadcrumb'
        elif str(current_mod_id) == '55':
            config = ACADEMIC_MENU_CONFIG
            processed_menu_key = 'processed_academic_menu'
            tabs_key = 'academic_tabs'
            breadcrumb_key = 'academic_breadcrumb'
        elif str(current_mod_id) == '75':
            from app.blueprints.leave import LEAVE_MENU_CONFIG
            config = LEAVE_MENU_CONFIG
            processed_menu_key = 'processed_leave_menu'
            tabs_key = 'leave_tabs'
            breadcrumb_key = 'leave_breadcrumb'
        else: # 72
            from app.blueprints.establishment import ESTABLISHMENT_MENU_CONFIG
            config = ESTABLISHMENT_MENU_CONFIG
            processed_menu_key = 'processed_establishment_menu'
            tabs_key = 'establishment_tabs'
            breadcrumb_key = 'establishment_breadcrumb'
        
        ctx[processed_menu_key] = []
        ctx[tabs_key] = []
        ctx[breadcrumb_key] = []

        for cat, subs in config.items():
            cat_item = {'name': cat, 'subs': [], 'pages': []}
            
            if isinstance(subs, list):
                # Flat list of pages directly under Category
                for p in subs:
                    norm_p = _norm(p)
                    if is_super or norm_p in allowed_pages_norm:
                        p_url = get_page_url(p)
                        is_active = (current_page == p)
                        if is_active:
                            ctx[breadcrumb_key] = [cat, p]
                        cat_item['pages'].append({'name': p, 'url': p_url})
            elif isinstance(subs, dict):
                # Standard Nested structure
                for sub_cat, folders in subs.items():
                    sub_item = {'name': sub_cat, 'subs': []}
                    for folder, pages in folders.items():
                        folder_pages = []
                        is_active_folder = False
                        for p in pages:
                            norm_p = _norm(p)
                            if is_super or norm_p in allowed_pages_norm:
                                p_url = get_page_url(p)
                                folder_pages.append({'name': p, 'url': p_url})
                                
                                is_active = (current_page == p)
                                if not is_active and str(current_mod_id) == '30' and p == 'Department Master (UMM)' and current_page == 'Department Master':
                                    is_active = True
                                    
                                if is_active:
                                    is_active_folder = True
                                    ctx[breadcrumb_key] = [cat, sub_cat, folder, p]
                        
                        if folder_pages:
                            sub_item['subs'].append({
                                'name': folder,
                                'url': folder_pages[0]['url'],
                                'pages': folder_pages
                            })
                            if is_active_folder:
                                for fp in folder_pages:
                                    is_fp_active = (fp['name'] == current_page)
                                    if not is_fp_active and str(current_mod_id) == '30' and fp['name'] == 'Department Master (UMM)' and current_page == 'Department Master':
                                        is_fp_active = True
                                        
                                    ctx[tabs_key].append({
                                        'name': fp['name'],
                                        'url': fp['url'],
                                        'active': is_fp_active
                                    })
                    if sub_item['subs']:
                        cat_item['subs'].append(sub_item)
            
            if cat_item['subs'] or cat_item['pages']:
                ctx[processed_menu_key].append(cat_item)

    session['cached_mod_id'] = current_mod_id
    session['cached_loc'] = selected_loc
    session.modified = True
    
    return ctx
