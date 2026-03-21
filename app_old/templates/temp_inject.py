@app.context_processor
def inject_navigation():
    # Skip for static assets
    if request.path.startswith('/static'):
        return {}
    
    from app.blueprints.academics import ACADEMIC_MENU_CONFIG
    from app.utils import get_page_url, PAGE_URL_MAPPING

    # Template context variables
    ctx = {
        'menu': {},
        'current_mod': None,
        'announcements': [],
        'pending_leaves_count': 0,
        'assigned_modules': [],
        'current_mod_id': session.get('current_module_id'),
        'get_page_url': get_page_url
    }

    if 'user_id' not in session:
        return ctx
    
    user_id = session['user_id']
    emp_id = session.get('emp_id')
    selected_loc = session.get('selected_loc')
    current_mod_id = ctx['current_mod_id']
    
    if not selected_loc:
        return ctx

    # RESTORED CACHE logic
    all_rights = None
    if 'cached_nav' in session and session.get('cached_mod_id') == current_mod_id and session.get('cached_loc') == selected_loc:
        cache = session['cached_nav']
        ctx.update(cache)
        all_rights = session.get('current_user_rights')
    
    if not all_rights:
        selected_loc = str(selected_loc)
        if current_mod_id and str(current_mod_id).isdigit():
            ctx['current_mod'] = DB.fetch_one("SELECT pk_moduleId, modulename FROM UM_Module_Mst WHERE pk_moduleId = ?", [current_mod_id])

        all_rights = NavModel.get_user_page_rights(user_id, selected_loc)
        ctx['assigned_modules'] = NavModel.get_user_modules(user_id, selected_loc)
        session['current_user_rights'] = all_rights
        
        # MENU ENGINE
        menu = {}
        if current_mod_id:
            def build_configured_menu(config, all_rights):
                allowed_pages = {r['PageName'] for r in all_rights if r['AllowView']}
                built_menu = {}
                for main_cat, subs in config.items():
                    cat_obj = {'subs': [], 'pages': []}
                    for sub_cat, sub_subs in subs.items():
                        for folder_name, pages in sub_subs.items():
                            visible_pages = []
                            for p in pages:
                                if p in allowed_pages:
                                    visible_pages.append({'name': p, 'url': get_page_url(p)})
                            
                            if visible_pages:
                                cat_obj['subs'].append({
                                    'name': folder_name,
                                    'url': visible_pages[0]['url'],
                                    'pages': visible_pages
                                })
                    if cat_obj['subs']:
                        built_menu[main_cat] = cat_obj
                return built_menu

            if str(current_mod_id) == '55':
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
                # Standard 3-Tier Builder
                all_pages = [r for r in all_rights if str(r['fk_moduleId']) == str(current_mod_id) and r['AllowView']]
                for p in all_pages:
                    p['pk_webpageId'] = str(p['pk_webpageId'])
                    p['parentId'] = str(p['parentId']) if p['parentId'] is not None else '0'
                
                for p in all_pages:
                    if p['parentId'] == '0':
                        menu[p['pk_webpageId']] = {'name': p['PageName'], 'pages': [], 'subs': {}}
                
                for p in all_pages:
                    if p['parentId'] in menu:
                        has_children = any(child['parentId'] == p['pk_webpageId'] for child in all_pages)
                        if has_children:
                            menu[p['parentId']]['subs'][p['pk_webpageId']] = {'name': p['PageName'], 'pages': []}
                        else:
                            p['url'] = get_page_url(p['PageName'])
                            menu[p['parentId']]['pages'].append(p)
                
                for p in all_pages:
                    pid = p['parentId']
                    for cat_id, cat_data in menu.items():
                        if pid in cat_data['subs']:
                            p['url'] = get_page_url(p['PageName'])
                            cat_data['subs'][pid]['pages'].append(p)

                formatted = {}
                for cat_id, cat_data in menu.items():
                    if cat_data['pages'] or any(sd['pages'] for sd in cat_data['subs'].values()):
                        formatted[cat_data['name']] = {'pages': cat_data['pages'], 'subs': list(cat_data['subs'].values())}
                menu = formatted

        ctx['menu'] = menu
        ctx['announcements'] = DB.fetch_all("SELECT TOP 5 Messages FROM UM_CommonMessaging WHERE isactive = 1 ORDER BY PublishDate DESC")
        
        if emp_id:
            fy = NavModel.get_current_fin_year()
            ctx['pending_leaves_count'] = DB.fetch_scalar("SELECT COUNT(*) FROM SAL_Leave_Request_Mst WHERE fk_reportingto = ? AND leavestatus = 'S' AND fromdate BETWEEN ? AND ?", [emp_id, fy['date1'], fy['date2']])

        session['cached_nav'] = {
            'menu': ctx['menu'], 
            'current_mod': ctx['current_mod'], 
            'announcements': ctx['announcements'], 
            'pending_leaves_count': ctx['pending_leaves_count'], 
            'assigned_modules': ctx['assigned_modules']
        }

    # BREADCRUMBS & TABS LOGIC (Calculated on every request)
    ctx['academic_breadcrumb'] = []
    ctx['academic_tabs'] = []
    ctx['processed_academic_menu'] = []
    
    allowed_pages = {r['PageName'] for r in all_rights if r['AllowView']}
    
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

    # Build Top Menu AND Detect Active Tab Group
    for cat, subs in ACADEMIC_MENU_CONFIG.items():
        cat_item = {'name': cat, 'subs': []}
        for sub_cat, folders in subs.items():
            sub_item = {'name': sub_cat, 'folders': []}
            for folder, pages in folders.items():
                folder_pages = []
                is_active_folder = False
                for p in pages:
                    if p in allowed_pages:
                        p_url = get_page_url(p)
                        folder_pages.append({'name': p, 'url': p_url})
                        if current_page == p:
                            is_active_folder = True
                            ctx['academic_breadcrumb'] = [cat, sub_cat, folder, p]
                
                if folder_pages:
                    sub_item['folders'].append({
                        'name': folder,
                        'url': folder_pages[0]['url'],
                        'pages': folder_pages
                    })
                    if is_active_folder:
                        for fp in folder_pages:
                            ctx['academic_tabs'].append({
                                'name': fp['name'],
                                'url': fp['url'],
                                'active': (fp['name'] == current_page)
                            })
            if sub_item['folders']:
                cat_item['subs'].append(sub_item)
        if cat_item['subs']:
            ctx['processed_academic_menu'].append(cat_item)

    session['cached_mod_id'] = current_mod_id
    session['cached_loc'] = selected_loc
    session.modified = True
    
    return ctx
