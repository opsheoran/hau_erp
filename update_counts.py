import os

with open('app/blueprints/examination/marks_process_ug_mba.py', 'r', encoding='utf-8') as f:
    code = f.read()

new_query_logic = '''
                query = """
                    SELECT DISTINCT S.pk_sid, S.fullname, S.enrollmentno, S.AdmissionNo
                    FROM SMS_Student_Mst S
                    INNER JOIN SMS_StuCourseAllocation A ON S.pk_sid = A.fk_sturegid
                    INNER JOIN SMS_DegreeCycle_Mst DC ON A.fk_degreecycleid = DC.pk_degreecycleid
                    INNER JOIN SMS_StuExamMarks_Cld CLD ON A.Pk_stucourseallocid = CLD.fk_stucourseallocid
                    WHERE S.fk_collegeid = ? AND A.fk_dgacasessionid = ? AND DC.fk_degreeid = ? 
                      AND DC.fk_semesterid = ? AND DC.fk_degreeyearid = ?
                      AND ISNULL(A.IsSummer, 0) = 0 AND ISNULL(A.IsSupplementary, 0) = 0
                """
'''

old_query_logic = '''
                query = """
                    SELECT DISTINCT S.pk_sid, S.fullname, S.enrollmentno, S.AdmissionNo
                    FROM SMS_Student_Mst S
                    INNER JOIN SMS_StuCourseAllocation A ON S.pk_sid = A.fk_sturegid
                    INNER JOIN SMS_DegreeCycle_Mst DC ON A.fk_degreecycleid = DC.pk_degreecycleid
                    WHERE S.fk_collegeid = ? AND A.fk_dgacasessionid = ? AND DC.fk_degreeid = ? 
                      AND DC.fk_semesterid = ? AND DC.fk_degreeyearid = ?
                      AND ISNULL(A.IsSummer, 0) = 0 AND ISNULL(A.IsSupplementary, 0) = 0
                      AND ISNULL(S.IsRegCancel, 0) = 0 AND ISNULL(S.isdgcompleted, 0) = 0
                """
'''

if old_query_logic.strip() in code:
    code = code.replace(old_query_logic.strip(), new_query_logic.strip())
    
    old_fail_check = '''
                    fail_check = DB.fetch_one("""
                        SELECT COUNT(*) as c
                        FROM SMS_StuCourseAllocation A
                        INNER JOIN SMS_DegreeCycle_Mst DC ON A.fk_degreecycleid = DC.pk_degreecycleid
                        WHERE A.fk_sturegid = ? AND A.fk_dgacasessionid = ? AND DC.fk_degreeid = ? AND DC.fk_semesterid = ? AND A.ispassed = 0 AND A.isbacklog = 1
                    """, [r['pk_sid'], filters['session_id'], filters['degree_id'], filters['class_id']])
'''

    new_fail_check = '''
                    fail_check = DB.fetch_one("""
                        SELECT COUNT(*) as c
                        FROM SMS_StuCourseAllocation A
                        INNER JOIN SMS_DegreeCycle_Mst DC ON A.fk_degreecycleid = DC.pk_degreecycleid
                        INNER JOIN SMS_StuExamMarks_Cld CLD ON A.Pk_stucourseallocid = CLD.fk_stucourseallocid
                        WHERE A.fk_sturegid = ? AND A.fk_dgacasessionid = ? AND DC.fk_degreeid = ? AND DC.fk_semesterid = ? AND CLD.ispassed = 0
                    """, [r['pk_sid'], filters['session_id'], filters['degree_id'], filters['class_id']])
'''
    code = code.replace(old_fail_check.strip(), new_fail_check.strip())
    
    with open('app/blueprints/examination/marks_process_ug_mba.py', 'w', encoding='utf-8') as f:
        f.write(code)
    print('Updated fetch query to use exact CLD marks count logic.')
else:
    print('Failed to find query to replace.')