from app.db import DB

cols_sal = DB.fetch_all('''SELECT COLUMN_NAME FROM information_schema.columns WHERE TABLE_NAME='SAL_Employee_Mst' ''')
print('SAL_Employee_Mst:', [c['COLUMN_NAME'] for c in cols_sal])

print('---')
dept_map = DB.fetch_all('''
SELECT TOP 5 D.fk_courseid, C.coursecode, C.fk_Deptid, M.fk_Empid, E.fk_officeid
FROM SMS_CourseAllocationSemesterwiseByHOD_Dtl D
INNER JOIN SMS_CourseAllocationSemesterwiseByHOD M ON D.fk_courseallocid = M.Pk_courseallocid
INNER JOIN SMS_Course_Mst C ON D.fk_courseid = C.pk_courseid
LEFT JOIN UM_Employee_Mst E ON M.fk_Empid = E.pk_empid
WHERE C.coursecode IN ('STAT 502 BSMA', 'VSC 502 BSMA', 'VSC 511 BSMA', 'GPB 504 BSMA') AND M.fk_dgacasessionid = 72
''')
for d in dept_map: print(d)
