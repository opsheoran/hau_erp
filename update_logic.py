import os
import re

with open('app/blueprints/examination/marks_process_ug_mba.py', 'r', encoding='utf-8') as f:
    code = f.read()

new_query_logic = '''
                query = """
                    SELECT DISTINCT S.pk_sid, S.fullname, S.enrollmentno, S.AdmissionNo
                    FROM SMS_Student_Mst S
                    INNER JOIN SMS_StuCourseAllocation A ON S.pk_sid = A.fk_sturegid
                    INNER JOIN SMS_DegreeCycle_Mst DC ON A.fk_degreecycleid = DC.pk_degreecycleid
                    WHERE S.fk_collegeid = ? AND S.fk_curr_session = ? AND DC.fk_degreeid = ? 
                      AND DC.fk_semesterid = ? AND DC.fk_degreeyearid = ? AND A.fk_dgacasessionid = ?
                      AND ISNULL(A.IsSummer, 0) = 0 AND ISNULL(A.IsSupplementary, 0) = 0
                """
                params = [filters['college_id'], filters['session_id'], filters['degree_id'], filters['class_id'], filters['year_id'], filters['session_id']]
                
                if filters['branch_id']:
                    query += " AND DC.fk_branchid = ?"
                    params.append(filters['branch_id'])
                    
                query += " ORDER BY S.fullname, S.enrollmentno"
                
                rows = DB.fetch_all(query, params)
                fail_count = 0
                
                for r in rows:
                    # Check actual failure from allocation table
                    fail_check = DB.fetch_one("""
                        SELECT COUNT(*) as c
                        FROM SMS_StuCourseAllocation A
                        INNER JOIN SMS_DegreeCycle_Mst DC ON A.fk_degreecycleid = DC.pk_degreecycleid
                        WHERE A.fk_sturegid = ? AND A.fk_dgacasessionid = ? AND DC.fk_degreeid = ? AND DC.fk_semesterid = ? AND A.ispassed = 0 AND A.isbacklog = 1
                    """, [r['pk_sid'], filters['session_id'], filters['degree_id'], filters['class_id']])
                    
                    is_fail = fail_check['c'] > 0 if fail_check else False
                    
                    if is_fail:
                        fail_count += 1

                    students.append({
                        'id': r['pk_sid'],
                        'name': f"{r['fullname']}|{r['enrollmentno']}",
                        'last_process_date': '', # Placeholder
                        'is_fail': is_fail
                    })
                
                filters['total_students'] = len(students)
                filters['fail_students'] = fail_count
'''

old_query_logic_start = "query = '''"
old_query_logic_end = "filters['fail_students'] = fail_count"

start_idx = code.find(old_query_logic_start)
end_idx = code.find(old_query_logic_end) + len(old_query_logic_end)

if start_idx != -1 and end_idx != -1:
    old_block = code[start_idx:end_idx]
    code = code.replace(old_block, new_query_logic.strip())
    with open('app/blueprints/examination/marks_process_ug_mba.py', 'w', encoding='utf-8') as f:
        f.write(code)
    print('Replaced student logic successfully')
else:
    print('Could not find block to replace')
