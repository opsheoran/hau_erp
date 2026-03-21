from app.db import DB
student_id = 9791

student = DB.fetch_one('SELECT fk_branchid, fk_collegeid FROM SMS_Student_Mst WHERE pk_sid = ?', [student_id])
print('Student Major Branch:', student['fk_branchid'], 'College:', student['fk_collegeid'])

advisory = DB.fetch_all('''
    SELECT D.fk_statusid, D.fk_deptid
    FROM SMS_Advisory_Committee_Mst M
    INNER JOIN SMS_Advisory_Committee_Dtl D ON M.pk_adcid = D.fk_adcid
    WHERE M.fk_stid = ?
''', [student_id])

for adv in advisory:
    dept_id = adv['fk_deptid']
    if not dept_id: continue
    dept_info = DB.fetch_one('SELECT * FROM Department_Mst WHERE pk_deptid = ?', [dept_id])
    if dept_info:
        print(f'Dept {dept_id}: {dept_info.get("description")}')
    
    branch = DB.fetch_one('SELECT * FROM SMS_BranchMst WHERE fk_deptidDdo = ?', [dept_id])
    if branch:
        print(f'  -> Mapped to Branch: {branch.get("Branchname")}, pk_branchid: {branch.get("Pk_BranchId")}')
        college_map = DB.fetch_one('SELECT TOP 1 fk_collegeid FROM SMS_CollegeDegreeBranchMap_dtl WHERE fk_branchid = ?', [branch['Pk_BranchId']])
        print(f'  -> Mapped to College (from degree branch map): {college_map}')
