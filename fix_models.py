import re

with open('app/models/academics.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_method = '''    def get_courses_for_degree_semester(degree_id, semester_id, course_type=None, sms_dept_ids=None, code_prefixes=None, is_hod_view=False):
        sql = """
            SELECT C.pk_courseid, C.coursecode, C.coursename,
                   C.crhr_theory, C.crhr_practical
            FROM SMS_Course_Mst C
            LEFT JOIN SMS_Course_Mst_Dtl D ON C.pk_courseid = D.fk_courseid
            WHERE ISNULL(C.isobsolete, 0) = 0 AND C.coursecode NOT LIKE '%deleted%' AND C.coursename NOT LIKE '%deleted%'
        """
        params = []
        
        if is_hod_view and sms_dept_ids:
            placeholders = ",".join(["?"] * len(sms_dept_ids))
            sql += f" AND C.fk_Deptid IN ({placeholders})"
            params.extend(sms_dept_ids)
        else:
            sql += " AND D.fk_degreeid = ? AND D.fk_semesterid = ?"
            params.extend([degree_id, semester_id])

        if course_type == 'T':
            sql += " AND ISNULL(C.crhr_theory, 0) > 0"
        elif course_type == 'P':
            sql += " AND ISNULL(C.crhr_practical, 0) > 0"
            
        sql += " GROUP BY C.pk_courseid, C.coursecode, C.coursename, C.crhr_theory, C.crhr_practical"
        sql += " ORDER BY CASE WHEN C.coursecode = 'deleted' THEN 1 ELSE 2 END, C.coursecode COLLATE Latin1_General_BIN ASC, C.coursename COLLATE Latin1_General_BIN ASC"
        return DB.fetch_all(sql, params)

    @staticmethod
    def get_courses_for_degree_semesters(degree_id, semester_ids, course_type=None, sms_dept_ids=None, code_prefixes=None, is_hod_view=False):
        if not semester_ids: return []
        sql = """
            SELECT C.pk_courseid, C.coursecode, C.coursename,
                   C.crhr_theory, C.crhr_practical
            FROM SMS_Course_Mst C
            LEFT JOIN SMS_Course_Mst_Dtl D ON C.pk_courseid = D.fk_courseid
            WHERE ISNULL(C.isobsolete, 0) = 0 AND C.coursecode NOT LIKE '%deleted%' AND C.coursename NOT LIKE '%deleted%'
        """
        params = []
        
        if is_hod_view and sms_dept_ids:
            placeholders_dept = ",".join(["?"] * len(sms_dept_ids))
            sql += f" AND C.fk_Deptid IN ({placeholders_dept})"
            params.extend(sms_dept_ids)
        else:
            placeholders_sem = ",".join(["?"] * len(semester_ids))
            sql += f" AND D.fk_degreeid = ? AND D.fk_semesterid IN ({placeholders_sem})"
            params.extend([degree_id] + list(semester_ids))

        if course_type == 'T':
            sql += " AND ISNULL(C.crhr_theory, 0) > 0"
        elif course_type == 'P':
            sql += " AND ISNULL(C.crhr_practical, 0) > 0"

        sql += " GROUP BY C.pk_courseid, C.coursecode, C.coursename, C.crhr_theory, C.crhr_practical"
        sql += " ORDER BY CASE WHEN C.coursecode = 'deleted' THEN 1 ELSE 2 END, C.coursecode COLLATE Latin1_General_BIN ASC, C.coursename COLLATE Latin1_General_BIN ASC"
        return DB.fetch_all(sql, params)'''

start_idx = content.find('    def get_courses_for_degree_semester(')
end_idx = content.find('    def get_course_offer_master(', start_idx)

if start_idx != -1 and end_idx != -1:
    real_end_idx = content.rfind('    @staticmethod', start_idx, end_idx)
    content = content[:start_idx] + new_method + '\n\n' + content[real_end_idx:]
    with open('app/models/academics.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Updated get_courses_for_degree_semester')
