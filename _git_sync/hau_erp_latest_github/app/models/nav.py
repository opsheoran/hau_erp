from app.db import DB
from datetime import datetime

class NavModel:
    _support_schema_cache = None

    @staticmethod
    def _truthy_sql(expr):
        # SQL Server-safe truthiness conversion for mixed bit/int/char fields.
        # Treat 1 / Y / YES / TRUE / T as true; everything else false.
        return f"""
            CASE
                WHEN TRY_CONVERT(int, {expr}) = 1 THEN 1
                WHEN UPPER(LTRIM(RTRIM(CAST({expr} AS VARCHAR(10))))) IN ('Y','YES','TRUE','T') THEN 1
                ELSE 0
            END
        """

    @staticmethod
    def _get_table_columns(table_name):
        try:
            rows = DB.fetch_all(
                "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = ?",
                [table_name]
            )
            return {str(r['COLUMN_NAME']) for r in rows}
        except Exception:
            return set()

    @staticmethod
    def _has_column(table_name, column_name):
        cols = {c.lower() for c in NavModel._get_table_columns(table_name)}
        if cols and column_name.lower() in cols:
            return True
        try:
            DB.fetch_one(f"SELECT TOP 1 [{column_name}] as v FROM {table_name}")
            return True
        except Exception:
            return False

    @staticmethod
    def _support_join_target():
        # Support rights may reference UM_WebPage_Mst.pk_webpageId OR UM_WebPage_Mst.wpid depending on DB.
        if NavModel._has_column('UM_WebPage_Mst', 'wpid'):
            return ['pk_webpageId', 'wpid']
        return ['pk_webpageId']

    @staticmethod
    def _detect_support_team_schema():
        if NavModel._support_schema_cache is not None:
            return NavModel._support_schema_cache

        cols = {c.lower(): c for c in NavModel._get_table_columns('Support_Team_Page_Rights')}

        def _col_exists(col):
            return NavModel._has_column('Support_Team_Page_Rights', col)

        def pick(*candidates):
            for cand in candidates:
                if cand.lower() in cols:
                    return cols[cand.lower()]
            # If INFORMATION_SCHEMA is blocked, probe by attempting to select the column.
            for cand in candidates:
                if _col_exists(cand):
                    return cand
            return None

        schema = {
            'user_col': pick('fk_userId', 'fk_userid', 'userId', 'userid', 'user_id'),
            'webpage_col': pick('fk_webpageId', 'fk_webpageid', 'fk_pageId', 'fk_pageid', 'webpageId', 'webpageid', 'pageId', 'pageid'),
            'allow_view_col': pick('AllowView', 'allowview', 'Allow_Search', 'AllowSearch', 'allow_search', 'search'),
            'allow_add_col': pick('AllowAdd', 'allowadd'),
            'allow_update_col': pick('AllowUpdate', 'allowupdate'),
            'allow_delete_col': pick('AllowDelete', 'allowdelete'),
        }
        if not schema.get('user_col') or not schema.get('webpage_col'):
            NavModel._support_schema_cache = None
            return None
        NavModel._support_schema_cache = schema
        return schema

    @staticmethod
    def _normalize_caption(caption):
        if caption is None:
            return ''
        # Collapse any whitespace runs to a single space (DB captions sometimes have extra spaces).
        return " ".join(str(caption).strip().split())

    @staticmethod
    def _get_user_role_ids(user_id):
        role_ids = set()
        try:
            r = DB.fetch_one("SELECT fk_roleId FROM UM_Users_Mst WHERE pk_userId = ?", [str(user_id)])
            if r and r.get('fk_roleId') is not None:
                role_ids.add(str(r['fk_roleId']))
        except Exception:
            pass

        try:
            rows = DB.fetch_all("SELECT fk_roleId FROM UM_UsersRole_Dtls WHERE fk_userId = ?", [str(user_id)])
            for row in rows:
                if row.get('fk_roleId') is not None:
                    role_ids.add(str(row['fk_roleId']))
        except Exception:
            # Some DBs may not use UM_UsersRole_Dtls (single-role only).
            pass

        return [rid for rid in role_ids if str(rid).strip()]

    @staticmethod
    def _get_user_login_role(user_id):
        try:
            row = DB.fetch_one("""
                SELECT U.loginname, R.rolename
                FROM UM_Users_Mst U
                LEFT JOIN UM_Role_Mst R ON U.fk_roleId = R.pk_roleId
                WHERE U.pk_userId = ?
            """, [str(user_id)])
            return row or {}
        except Exception:
            return {}

    @staticmethod
    def _is_super_admin(user_id):
        info = NavModel._get_user_login_role(user_id)
        login = (info.get('loginname') or '').strip().lower()
        # Strictly only hauadmin and rsingh1 get "Full Rights" regardless of anything else.
        return login in {'hauadmin', 'rsingh1'}

    @staticmethod
    def _is_global_access_user(user_id):
        # Some users (e.g., super admin / software manager) have rights across all colleges in live.
        # We infer this from login/role to avoid depending on location-scoped mappings.
        info = NavModel._get_user_login_role(user_id)
        login = (info.get('loginname') or '').strip().lower()
        role = (info.get('rolename') or '').strip().upper()

        if login in {'hauadmin', 'rsingh1'}:
            return True

        global_role_tokens = [
            'SUPER ADMIN',
            'SOFTWARE MANAGER',
            'MIS ADMIN',
            'MODULE ADMIN',
            'ADMIN'
        ]
        if any(tok in role for tok in global_role_tokens):
            return True

        # Support team rights imply cross-college access in many live deployments.
        try:
            schema = NavModel._detect_support_team_schema()
            if schema and schema.get('user_col'):
                c = DB.fetch_scalar(
                    f"SELECT COUNT(*) FROM Support_Team_Page_Rights WHERE [{schema['user_col']}] = ?",
                    [str(user_id)]
                )
            else:
                # Try common variants if schema detection isn't available.
                c = 0
                for col in ('fk_userId', 'fk_userid', 'userId', 'userid', 'user_id'):
                    try:
                        c = DB.fetch_scalar(f"SELECT COUNT(*) FROM Support_Team_Page_Rights WHERE [{col}] = ?", [str(user_id)])
                        break
                    except Exception:
                        continue
            if c and int(c) > 0:
                return True
        except Exception:
            pass

        return False

    @staticmethod
    def _support_team_rights_rows(user_id):
        # Optional table present in some DBs; grants global rights for support users.
        schema = NavModel._detect_support_team_schema()
        if not schema or not schema.get('user_col') or not schema.get('webpage_col'):
            return []

        user_col = schema['user_col']
        webpage_col = schema['webpage_col']
        allow_view_col = schema.get('allow_view_col')
        allow_add_col = schema.get('allow_add_col')
        allow_update_col = schema.get('allow_update_col')
        allow_delete_col = schema.get('allow_delete_col')

        def allow_expr(col):
            if not col:
                # Some deployments store only the page list for support-team members.
                # Treat presence as full rights.
                return "1"
            return NavModel._truthy_sql(f"ST.[{col}]")

        try:
            for join_col in NavModel._support_join_target():
                query = f"""
                    SELECT
                        M.modulename,
                        M.pk_moduleId as fk_moduleId,
                        W.pk_webpageId,
                        REPLACE(LTRIM(RTRIM(W.menucaption)), '  ', ' ') as PageName,
                        W.parentId,
                        ISNULL(MAX({allow_expr(allow_view_col)}), 0) as AllowView,
                        ISNULL(MAX({allow_expr(allow_add_col)}), 0) as AllowAdd,
                        ISNULL(MAX({allow_expr(allow_update_col)}), 0) as AllowUpdate,
                        ISNULL(MAX({allow_expr(allow_delete_col)}), 0) as AllowDelete
                    FROM Support_Team_Page_Rights ST
                    INNER JOIN UM_WebPage_Mst W ON ST.[{webpage_col}] = W.[{join_col}]
                    INNER JOIN UM_Module_Mst M ON W.fk_moduleId = M.pk_moduleId
                    WHERE ST.[{user_col}] = ?
                    GROUP BY M.modulename, M.pk_moduleId, W.pk_webpageId, W.menucaption, W.parentId
                """
                rows = DB.fetch_all(query, [str(user_id)])
                if rows:
                    return rows
            return []
        except Exception:
            return []

    @staticmethod
    def _get_webpage_by_caption(page_caption):
        page_caption = NavModel._normalize_caption(page_caption)
        if not page_caption:
            return None
        # Try to normalize menucaption in SQL by repeatedly collapsing double-spaces and tabs.
        sql = """
            SELECT TOP 1 pk_webpageId, fk_moduleId, parentId,
                REPLACE(REPLACE(REPLACE(REPLACE(LTRIM(RTRIM(menucaption)), CHAR(9), ' '), '  ', ' '), '  ', ' '), '  ', ' ') as PageName
            FROM UM_WebPage_Mst
            WHERE REPLACE(REPLACE(REPLACE(REPLACE(LTRIM(RTRIM(menucaption)), CHAR(9), ' '), '  ', ' '), '  ', ' '), '  ', ' ') = ?
        """
        # Prefer current module (if set) to avoid ambiguities for duplicate captions; fallback to global match.
        try:
            from flask import session
            current_mod_id = session.get('current_module_id')
        except Exception:
            current_mod_id = None

        if current_mod_id and str(current_mod_id).isdigit():
            sql_mod = sql + " AND fk_moduleId = ?"
            row = DB.fetch_one(sql_mod, [page_caption, int(current_mod_id)])
            if row:
                return row

        return DB.fetch_one(sql, [page_caption])

    @staticmethod
    def get_assigned_locations(user_id):
        query = """
        SELECT DISTINCT L.pk_locid as id, L.locname as name
        FROM UM_UserModuleDetails UD
        INNER JOIN Location_Mst L ON UD.fk_locid = L.pk_locid
        WHERE UD.fk_userId = ?
        ORDER BY L.locname
        """
        rows = DB.fetch_all(query, [str(user_id)])
        if rows and not NavModel._is_global_access_user(user_id):
            return rows

        # For global-access users (or users without module details), allow switching across all locations.
        return DB.fetch_all("SELECT pk_locid as id, locname as name FROM Location_Mst ORDER BY locname")

    @staticmethod
    def get_user_modules(user_id, loc_id):
        # Effective modules = modules with any AllowView from either:
        # - per-user rights (UM_UserPageRights)
        # - role rights (UM_RolePage_Rights via UM_RoleModule_Details)
        rights = NavModel.get_user_page_rights(user_id, loc_id)
        module_ids = sorted({str(r.get('fk_moduleId')) for r in rights if r.get('AllowView')})
        if not module_ids:
            return []

        placeholders = ",".join(["?"] * len(module_ids))
        q = f"""
            SELECT pk_moduleId, modulename, remarks as moduledescription
            FROM UM_Module_Mst
            WHERE pk_moduleId IN ({placeholders})
            ORDER BY modulename
        """
        return DB.fetch_all(q, module_ids)

    @staticmethod
    def get_all_fin_years():
        """Fetches all financial years formatted as '2026'"""
        return DB.fetch_all("SELECT pk_finid as id, Lyear as name FROM SAL_Financial_Year ORDER BY Lyear DESC")

    @staticmethod
    def get_years():
        """Returns distinct Lyear values for selection"""
        return DB.fetch_all("SELECT DISTINCT Lyear as id, CAST(Lyear as varchar) as name FROM SAL_Financial_Year ORDER BY Lyear DESC")

    @staticmethod
    def get_current_fin_year():
        """Fetches the active financial year details"""
        query = "SELECT TOP 1 pk_finid, Lyear, date1, date2 FROM SAL_Financial_Year WHERE active = 'Y' ORDER BY orderno DESC"
        res = DB.fetch_one(query)
        if not res:
            curr_yr = datetime.now().year
            return {'pk_finid': 'CO-18', 'Lyear': curr_yr, 'date1': datetime(curr_yr, 4, 1), 'date2': datetime(curr_yr+1, 3, 31)}
        return res

    @staticmethod
    def get_user_page_rights(user_id, loc_id):
        loc_id = str(loc_id)
        is_super = NavModel._is_super_admin(user_id)

        # --- SUPER ADMIN OVERRIDE ---
        if is_super:
            # Grant full rights to ALL active pages for super admins.
            query_all = """
            SELECT 
                M.modulename,
                M.pk_moduleId as fk_moduleId,
                W.pk_webpageId,
                REPLACE(LTRIM(RTRIM(W.menucaption)), '  ', ' ') as PageName,
                W.parentId,
                1 as AllowView,
                1 as AllowAdd,
                1 as AllowUpdate,
                1 as AllowDelete
            FROM UM_WebPage_Mst W
            INNER JOIN UM_Module_Mst M ON W.fk_moduleId = M.pk_moduleId
            WHERE W.activestatus = 1
            """
            rows = DB.fetch_all(query_all)
            for r in rows:
                r['PageName'] = NavModel._normalize_caption(r.get('PageName'))
            return rows

        # --- User-specific rights (location-scoped) ---
        is_global = NavModel._is_global_access_user(user_id)
        query_user = f"""
        SELECT 
        M.modulename,
        M.pk_moduleId as fk_moduleId,
        W.pk_webpageId,
        REPLACE(LTRIM(RTRIM(W.menucaption)), '  ', ' ') as PageName,
        W.parentId,
        ISNULL(MAX({NavModel._truthy_sql('UP.AllowView')}), 0) as AllowView,
        ISNULL(MAX({NavModel._truthy_sql('UP.AllowAdd')}), 0) as AllowAdd,
        ISNULL(MAX({NavModel._truthy_sql('UP.AllowUpdate')}), 0) as AllowUpdate,
        ISNULL(MAX({NavModel._truthy_sql('UP.AllowDelete')}), 0) as AllowDelete
        FROM UM_UserPageRights UP
        INNER JOIN UM_UserModuleDetails UD ON UP.fk_usermoddetailId = UD.pk_usermoddetailId
        INNER JOIN UM_WebPage_Mst W ON UP.fk_webpageId = W.pk_webpageId
        INNER JOIN UM_Module_Mst M ON W.fk_moduleId = M.pk_moduleId
        WHERE UD.fk_userId = ? {'' if is_global else 'AND UD.fk_locid = ?'}
        GROUP BY M.modulename, M.pk_moduleId, W.pk_webpageId, W.menucaption, W.parentId
        """
        user_params = [str(user_id)] + ([] if is_global else [loc_id])
        user_rows = DB.fetch_all(query_user, user_params)

        # --- Role-specific rights ---
        role_rows = []
        role_ids = NavModel._get_user_role_ids(user_id)
        if role_ids:
            role_placeholders = ",".join(["?"] * len(role_ids))
            query_role = f"""
                SELECT
                    M.modulename,
                    M.pk_moduleId as fk_moduleId,
                    W.pk_webpageId,
                    REPLACE(LTRIM(RTRIM(W.menucaption)), '  ', ' ') as PageName,
                    W.parentId,
                    ISNULL(MAX({NavModel._truthy_sql('RP.AllowView')}), 0) as AllowView,
                    ISNULL(MAX({NavModel._truthy_sql('RP.AllowAdd')}), 0) as AllowAdd,
                    ISNULL(MAX({NavModel._truthy_sql('RP.AllowUpdate')}), 0) as AllowUpdate,
                    ISNULL(MAX({NavModel._truthy_sql('RP.AllowDelete')}), 0) as AllowDelete
                FROM UM_RolePage_Rights RP
                INNER JOIN UM_RoleModule_Details RMD ON RP.fk_rolemodid = RMD.pk_rolemodid
                INNER JOIN UM_WebPage_Mst W ON RP.fk_webpageId = W.pk_webpageId
                INNER JOIN UM_Module_Mst M ON W.fk_moduleId = M.pk_moduleId
                WHERE RMD.fk_roleId IN ({role_placeholders})
                GROUP BY M.modulename, M.pk_moduleId, W.pk_webpageId, W.menucaption, W.parentId
            """
            role_rows = DB.fetch_all(query_role, list(role_ids))

        # --- Merge (role rights + user rights) with user taking precedence via MAX semantics ---
        merged = {}
        support_rows = NavModel._support_team_rights_rows(user_id)
        for r in (support_rows + role_rows + user_rows):
            key = (str(r.get('fk_moduleId')), str(r.get('pk_webpageId')))
            if key not in merged:
                merged[key] = r
            else:
                merged[key]['AllowView'] = max(int(merged[key].get('AllowView') or 0), int(r.get('AllowView') or 0))
                merged[key]['AllowAdd'] = max(int(merged[key].get('AllowAdd') or 0), int(r.get('AllowAdd') or 0))
                merged[key]['AllowUpdate'] = max(int(merged[key].get('AllowUpdate') or 0), int(r.get('AllowUpdate') or 0))
                merged[key]['AllowDelete'] = max(int(merged[key].get('AllowDelete') or 0), int(r.get('AllowDelete') or 0))

        # --- TRANSACTION PAGE OVERRIDES (ESTABLISHMENT ID 72) ---
        transaction_pages = [
            'Employee Demographic Details', 'Employee Document Details', 'Education Qualification Details',
            'Employee Permission of Qualification Details', 'Employee Family Details',
            'Employee Nominee Details', 'Employee Books Details', 'LTC Detail', 'Earned Leave Details',
            'Employee Previous Job Details', 'Employee Foreign Visit Details', 'Employee Training Details',
            'Employee Departmental Exam Details', 'Employee Service Verification Details',
            'Disciplinary Action/Reward Details', 'Employee Loan Details', 'Employee Book Grant Amount Details',
            'Employee Bonus Amount Details', 'SAR/ACR Admin Transaction', 'Employee First Appointment Details',
            'Emp Increment Payrevision', 'Employee Promotion/Financial Up-gradation', 'Employee No-Dues Detail',
            'Appointing Authority', 'Controlling DDO Department Reliving', 'Controlling DDO Department Joining',
            'Non Teaching Employee Promotion Verification', 'Non Teaching Employee Promotion Approval',
            'Non Teaching VC Promotion Approval'
        ]
        
        for p_name in transaction_pages:
            merged[('72', p_name)] = {
                'modulename': 'Establishment', 'fk_moduleId': 72, 'pk_webpageId': p_name,
                'PageName': p_name, 'parentId': 0, 'AllowView': 1, 'AllowAdd': 1, 'AllowUpdate': 1, 'AllowDelete': 1
            }

        rows = list(merged.values())
        for r in rows:
            r['PageName'] = NavModel._normalize_caption(r.get('PageName'))
        return rows

    @staticmethod
    def check_permission(user_id, loc_id, page_caption):
        # --- HARDCODED OVERRIDES FOR NEW MASTERS ---
        if page_caption in [
            'Marital Status Master', 'Funds Sponsor Master', 'ExamType Master', 
            'Designation Category', 'Employee Master Scheme Wise'
        ]:
            return {'AllowView': 1, 'AllowAdd': 1, 'AllowUpdate': 1, 'AllowDelete': 1}

        loc_id = str(loc_id)
        if NavModel._is_super_admin(user_id):
            return {'AllowView': 1, 'AllowAdd': 1, 'AllowUpdate': 1, 'AllowDelete': 1}

        page = NavModel._get_webpage_by_caption(page_caption)
        if not page:
            return None
        page_id = str(page['pk_webpageId'])

        # 1) Try user-specific rights for this location.
        query_user = f"""
            SELECT TOP 1
                {NavModel._truthy_sql('UP.AllowView')} as AllowView,
                {NavModel._truthy_sql('UP.AllowAdd')} as AllowAdd,
                {NavModel._truthy_sql('UP.AllowUpdate')} as AllowUpdate,
                {NavModel._truthy_sql('UP.AllowDelete')} as AllowDelete
            FROM UM_UserPageRights UP
            INNER JOIN UM_UserModuleDetails UD ON UP.fk_usermoddetailId = UD.pk_usermoddetailId
            WHERE UD.fk_userId = ? AND UD.fk_locid = ? AND UP.fk_webpageId = ?
        """
        user_perm = DB.fetch_one(query_user, [str(user_id), loc_id, page_id])
        if user_perm:
            return user_perm

        # 1b) For global-access users, allow per-user rights from any location.
        if NavModel._is_global_access_user(user_id):
            query_any_loc = f"""
                SELECT TOP 1
                    {NavModel._truthy_sql('UP.AllowView')} as AllowView,
                    {NavModel._truthy_sql('UP.AllowAdd')} as AllowAdd,
                    {NavModel._truthy_sql('UP.AllowUpdate')} as AllowUpdate,
                    {NavModel._truthy_sql('UP.AllowDelete')} as AllowDelete
                FROM UM_UserPageRights UP
                INNER JOIN UM_UserModuleDetails UD ON UP.fk_usermoddetailId = UD.pk_usermoddetailId
                WHERE UD.fk_userId = ? AND UP.fk_webpageId = ?
            """
            any_loc_perm = DB.fetch_one(query_any_loc, [str(user_id), page_id])
            if any_loc_perm:
                return any_loc_perm

        # 2) Fallback to role-based rights (global; optionally filter to assigned modules if present).
        role_ids = NavModel._get_user_role_ids(user_id)
        if not role_ids:
            # Try support-team table as final fallback.
            try:
                schema = NavModel._detect_support_team_schema()
                if not schema or not schema.get('user_col') or not schema.get('webpage_col'):
                    return {'AllowView': 0, 'AllowAdd': 0, 'AllowUpdate': 0, 'AllowDelete': 0}

                def allow_expr(col):
                    if not col:
                        return "1"
                    return NavModel._truthy_sql(f"ST.[{col}]")

                for join_col in NavModel._support_join_target():
                    q = f"""
                        SELECT TOP 1
                            {allow_expr(schema.get('allow_view_col'))} as AllowView,
                            {allow_expr(schema.get('allow_add_col'))} as AllowAdd,
                            {allow_expr(schema.get('allow_update_col'))} as AllowUpdate,
                            {allow_expr(schema.get('allow_delete_col'))} as AllowDelete
                        FROM Support_Team_Page_Rights ST
                        INNER JOIN UM_WebPage_Mst W ON ST.[{schema['webpage_col']}] = W.[{join_col}]
                        WHERE ST.[{schema['user_col']}] = ? AND W.pk_webpageId = ?
                    """
                    st_perm = DB.fetch_one(q, [str(user_id), page_id])
                    if st_perm:
                        return st_perm
            except Exception:
                pass
            return {'AllowView': 0, 'AllowAdd': 0, 'AllowUpdate': 0, 'AllowDelete': 0}

        role_placeholders = ",".join(["?"] * len(role_ids))
        params = list(role_ids)

        query_role = f"""
            SELECT
                ISNULL(MAX({NavModel._truthy_sql('RP.AllowView')}), 0) as AllowView,
                ISNULL(MAX({NavModel._truthy_sql('RP.AllowAdd')}), 0) as AllowAdd,
                ISNULL(MAX({NavModel._truthy_sql('RP.AllowUpdate')}), 0) as AllowUpdate,
                ISNULL(MAX({NavModel._truthy_sql('RP.AllowDelete')}), 0) as AllowDelete
            FROM UM_RolePage_Rights RP
            INNER JOIN UM_RoleModule_Details RMD ON RP.fk_rolemodid = RMD.pk_rolemodid
            WHERE RMD.fk_roleId IN ({role_placeholders})
              AND RP.fk_webpageId = ?
        """
        perm = DB.fetch_one(query_role, params + [page_id])
        if perm:
            return perm

        # Final fallback: support-team table.
        try:
            schema = NavModel._detect_support_team_schema()
            if not schema or not schema.get('user_col') or not schema.get('webpage_col'):
                return {'AllowView': 0, 'AllowAdd': 0, 'AllowUpdate': 0, 'AllowDelete': 0}

            def allow_expr(col):
                if not col:
                    return "1"
                return NavModel._truthy_sql(f"ST.[{col}]")

            for join_col in NavModel._support_join_target():
                q = f"""
                    SELECT TOP 1
                        {allow_expr(schema.get('allow_view_col'))} as AllowView,
                        {allow_expr(schema.get('allow_add_col'))} as AllowAdd,
                        {allow_expr(schema.get('allow_update_col'))} as AllowUpdate,
                        {allow_expr(schema.get('allow_delete_col'))} as AllowDelete
                    FROM Support_Team_Page_Rights ST
                    INNER JOIN UM_WebPage_Mst W ON ST.[{schema['webpage_col']}] = W.[{join_col}]
                    WHERE ST.[{schema['user_col']}] = ? AND W.pk_webpageId = ?
                """
                st_perm = DB.fetch_one(q, [str(user_id), page_id])
                if st_perm:
                    return st_perm
        except Exception:
            pass

        return {'AllowView': 0, 'AllowAdd': 0, 'AllowUpdate': 0, 'AllowDelete': 0}

    @staticmethod
    def get_natures():
        return DB.fetch_all("SELECT pk_natureid as id, nature as name FROM SAL_Nature_Mst ORDER BY nature")
