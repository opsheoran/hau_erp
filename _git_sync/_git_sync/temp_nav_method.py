    @staticmethod
    def get_user_page_rights(user_id, loc_id):
        loc_id = str(loc_id)
        is_super = NavModel._is_super_admin(user_id)

        # --- SUPER ADMIN OVERRIDE ---
        if is_super:
            query_all = """
            SELECT 
                M.modulename, M.pk_moduleId as fk_moduleId, W.pk_webpageId,
                REPLACE(LTRIM(RTRIM(W.menucaption)), '  ', ' ') as PageName,
                W.parentId, 1 as AllowView, 1 as AllowAdd, 1 as AllowUpdate, 1 as AllowDelete
            FROM UM_WebPage_Mst W
            INNER JOIN UM_Module_Mst M ON W.fk_moduleId = M.pk_moduleId
            WHERE W.activestatus = 1
            """
            rows = DB.fetch_all(query_all)
            for r in rows:
                r['PageName'] = NavModel._normalize_caption(r.get('PageName'))
            return rows

        # 1. User-specific rights
        is_global = NavModel._is_global_access_user(user_id)
        query_user = f"""
            SELECT M.modulename, M.pk_moduleId as fk_moduleId, W.pk_webpageId,
            REPLACE(LTRIM(RTRIM(W.menucaption)), '  ', ' ') as PageName, W.parentId,
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

        # 2. Role-specific rights
        role_rows = []
        role_ids = NavModel._get_user_role_ids(user_id)
        if role_ids:
            role_placeholders = ",".join(["?"] * len(role_ids))
            query_role = f"""
                SELECT M.modulename, M.pk_moduleId as fk_moduleId, W.pk_webpageId,
                REPLACE(LTRIM(RTRIM(W.menucaption)), '  ', ' ') as PageName, W.parentId,
                ISNULL(MAX({NavModel._truthy_sql('RP.AllowView')}), 0) as AllowView,
                ISNULL(MAX({NavModel._truthy_sql('RP.AllowAdd')}), 0) as AllowAdd,
                ISNULL(MAX({NavModel._truthy_sql('RP.AllowUpdate')}), 0) as AllowUpdate,
                ISNULL(MAX({NavModel._truthy_sql('RP.AllowDelete')}), 0) as AllowDelete
                FROM UM_RolePage_Rights RP
                INNER JOIN UM_WebPage_Mst W ON RP.fk_webpageId = W.pk_webpageId
                INNER JOIN UM_Module_Mst M ON W.fk_moduleId = M.pk_moduleId
                WHERE RP.fk_roleId IN ({role_placeholders})
                GROUP BY M.modulename, M.pk_moduleId, W.pk_webpageId, W.menucaption, W.parentId
            """
            role_rows = DB.fetch_all(query_role, list(role_ids))

        # 3. Support rights
        support_rows = NavModel._support_team_rights_rows(user_id)

        # Merge all
        merged = {}
        for r in (support_rows + role_rows + user_rows):
            # Using PageName as part of key if webpageId is inconsistent across sources
            key = (str(r.get('fk_moduleId')), str(r.get('pk_webpageId')))
            if key not in merged:
                merged[key] = r
            else:
                for action in ['AllowView', 'AllowAdd', 'AllowUpdate', 'AllowDelete']:
                    merged[key][action] = max(int(merged[key].get(action) or 0), int(r.get(action) or 0))

        # --- TRANSACTION PAGE OVERRIDES (Module 72) ---
        transaction_pages = [
            'Employee Demographic Details', 'Employee Document Details', 'Education Qualification Details',
            'Employee Permission of Qualification Details', 'Employee Family Details',
            'Employee Nominee Details', 'Employee Books Details', 'LTC Detail', 'Earned Leave Details',
            'Employee Previous Job Details', 'Employee Foreign Visit Details', 'Employee Training Details',
            'Employee Departmental Exam Details', 'Employee Service Verification Details',
            'Disciplinary Action/Reward Details', 'Employee Loan Details', 'Employee Book Grant Amount Details',
            'Employee Bonus Amount Details', 'SAR/ACR Admin Transaction', 'Employee First Appointment Details', 
            'Emp Increment Payrevision', 'Employee Promotion/Financial Up-gradation', 'Employee No-Dues Detail'
        ]
        for p_name in transaction_pages:
            merged[('72', p_name)] = {
                'modulename': 'Establishment', 'fk_moduleId': 72, 'pk_webpageId': p_name,
                'PageName': p_name, 'parentId': 0, 'AllowView': 1, 'AllowAdd': 1, 'AllowUpdate': 1, 'AllowDelete': 1
            }

        final_rows = list(merged.values())
        for r in final_rows:
            r['PageName'] = NavModel._normalize_caption(r.get('PageName'))
        return final_rows
