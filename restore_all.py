import re

with open('app/models/academics.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. PgsCourseLimitModel update
pgs_old = '''    def get_limits(page=1, per_page=10):
        offset = (page - 1) * per_page
        total = DB.fetch_scalar("SELECT COUNT(*) FROM SMS_Sessionwise_PGS_CourseLimit_Mst")
        query = f"""
            SELECT L.pk_PgsId, L.CourseCapacity,
                   ISNULL(C.collegename, 'Applicable to All') as collegename,
                   CO.coursename, S.sessionname
            FROM SMS_Sessionwise_PGS_CourseLimit_Mst L
            LEFT JOIN SMS_College_Mst C ON L.fk_collegeid = C.pk_collegeid
            LEFT JOIN SMS_Course_Mst CO ON L.fk_courseId = CO.pk_courseid
            LEFT JOIN SMS_AcademicSession_Mst S ON L.fk_SessionId = S.pk_sessionid
            ORDER BY L.pk_PgsId DESC
            OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY
        """
        return DB.fetch_all(query), total'''

pgs_new = '''    def get_limits(page=1, per_page=10):
        offset = (page - 1) * per_page
        total = DB.fetch_scalar("SELECT COUNT(*) FROM SMS_Sessionwise_PGS_CourseLimit_Mst")
        query = f"""
            SELECT L.pk_PgsId, L.CourseCapacity, L.fk_classId,
                   ISNULL(C.collegename, 'Applicable to All') as collegename,
                   CO.coursecode, CO.coursename, S.sessionname,
                   CASE WHEN L.fk_classId = 1 THEN 'Odd Semester'
                        WHEN L.fk_classId = 2 THEN 'Even Semester'
                        ELSE '' END as classname
            FROM SMS_Sessionwise_PGS_CourseLimit_Mst L
            LEFT JOIN SMS_College_Mst C ON L.fk_collegeid = C.pk_collegeid
            LEFT JOIN SMS_Course_Mst CO ON L.fk_courseId = CO.pk_courseid
            LEFT JOIN SMS_AcademicSession_Mst S ON L.fk_SessionId = S.pk_sessionid
            ORDER BY L.pk_PgsId DESC
            OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY
        """
        return DB.fetch_all(query), total

    @staticmethod
    def get_limit_by_id(limit_id):
        return DB.fetch_one("""
            SELECT pk_PgsId, fk_collegeid, fk_courseId, fk_SessionId, fk_classId, CourseCapacity
            FROM SMS_Sessionwise_PGS_CourseLimit_Mst
            WHERE pk_PgsId = ?
        """, [limit_id])'''
if 'get_limit_by_id' not in content:
    content = content.replace(pgs_old, pgs_new)

# 2. Activity_type fix
act_type_old = "return DB.fetch_all(\"SELECT PK_Actid as id, Activity_name as name, Remarks FROM SMS_Activity_Mst ORDER BY Activity_name\")"
act_type_new = "return DB.fetch_all(\"SELECT PK_Actid as id, Activity_name + ' || ' + ISNULL(Activity_code, '') as name, Remarks FROM SMS_Activity_Mst ORDER BY Activity_name\")"
content = content.replace(act_type_old, act_type_new)

# 3. get_degree_branches fix
content = content.replace(
    'INNER JOIN SMS_DegreeCycle_Mst C ON B.Pk_BranchId = C.fk_branchid\n            WHERE C.fk_degreeid = ?',
    'INNER JOIN SMS_CollegeDegreeBranchMap_dtl D ON B.Pk_BranchId = D.fk_branchid\n            INNER JOIN SMS_CollegeDegreeBranchMap_Mst M ON D.fk_Coldgbrmapid = M.PK_Coldgbrid\n            WHERE M.fk_Degreeid = ?'
)

# 4. get_course_activities fix
act_old = '''SELECT M.*, S.sessionname, SEM.semester_roman, CAT.ActivityCategory_Desc
            FROM SMS_CourseActivity_Mst M
            LEFT JOIN SMS_AcademicSession_Mst S ON M.sessionid = S.pk_sessionid
            LEFT JOIN SMS_Semester_Mst SEM ON M.semesterid = SEM.pk_semesterid'''
act_new = '''SELECT M.*, S.sessionname, CAT.ActivityCategory_Desc,
                   CASE WHEN M.semesterid = 1 THEN 'Odd'
                        WHEN M.semesterid = 2 THEN 'Even'
                        ELSE '' END as classname
            FROM SMS_CourseActivity_Mst M
            LEFT JOIN SMS_AcademicSession_Mst S ON M.sessionid = S.pk_sessionid'''
content = content.replace(act_old, act_new)

# 5. get_student_advisory_committee fix
adv_old = '''CASE D.fk_statusid 
                        WHEN 1 THEN 'Major Advisor'
                        WHEN 2 THEN 'Minor Advisor'
                        WHEN 3 THEN 'Member From Major Subject'
                        WHEN 4 THEN 'Member From Minor Subject'
                        WHEN 5 THEN 'Member From Supporting Subject'
                        WHEN 6 THEN 'Dean PGS Nominee'
                        ELSE 'Member'
                   END as role_name
            FROM SMS_Advisory_Committee_Dtl D
            LEFT JOIN SAL_Employee_Mst E ON D.fk_empid = E.pk_empid
            LEFT JOIN SAL_Designation_Mst DESG ON E.fk_desgid = DESG.pk_desgid
            LEFT JOIN Department_Mst DEPT ON E.fk_deptid = DEPT.pk_deptid
            LEFT JOIN SMS_Advisory_Committee_Mst ACM ON D.fk_adcid = ACM.pk_adcid
            LEFT JOIN SMS_BranchMst B ON ACM.fk_branchid = B.Pk_BranchId'''
adv_new = '''STAT.statusname as role_name
            FROM SMS_Advisory_Committee_Dtl D
            LEFT JOIN SAL_Employee_Mst E ON D.fk_empid = E.pk_empid
            LEFT JOIN SAL_Designation_Mst DESG ON E.fk_desgid = DESG.pk_desgid
            LEFT JOIN Department_Mst DEPT ON E.fk_deptid = DEPT.pk_deptid
            LEFT JOIN SMS_Advisory_Committee_Mst ACM ON D.fk_adcid = ACM.pk_adcid
            LEFT JOIN SMS_BranchMst B ON ACM.fk_branchid = B.Pk_BranchId
            LEFT JOIN SMS_AdvisoryStatus_Mst STAT ON D.fk_statusid = STAT.pk_stid'''
content = content.replace(adv_old, adv_new)

with open('app/models/academics.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Restored fixes to app/models/academics.py")
