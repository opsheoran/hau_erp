from app.db import DB

dept = DB.fetch_one('''SELECT pk_branchid, branchname FROM SMS_BranchMst WHERE branchname LIKE '%Seed Science%' ''')
print('Department:', dept)

query2 = '''
SELECT M.fk_dgacasessionid, M.fk_semesterid, C.coursecode, C.coursename, C.crhr_theory, C.crhr_practical
FROM SMS_CourseAllocationSemesterwiseByHOD M
INNER JOIN SMS_CourseAllocationSemesterwiseByHOD_Dtl D ON M.Pk_courseallocid = D.fk_courseallocid
INNER JOIN SMS_Course_Mst C ON D.fk_courseid = C.pk_courseid
WHERE M.fk_dgacasessionid = 77 AND C.coursecode LIKE 'SST%' AND M.fk_semesterid = 2
ORDER BY C.coursecode
'''
print('\nSST Courses offered by HOD in Session 77, Semester 2:')
for r in DB.fetch_all(query2):
    print(r)

query3 = '''
SELECT M.fk_dgacasessionid, M.fk_semesterid, C.coursecode, C.coursename, C.crhr_theory, C.crhr_practical
FROM SMS_CourseAllocationSemesterwiseByHOD M
INNER JOIN SMS_CourseAllocationSemesterwiseByHOD_Dtl D ON M.Pk_courseallocid = D.fk_courseallocid
INNER JOIN SMS_Course_Mst C ON D.fk_courseid = C.pk_courseid
WHERE M.fk_dgacasessionid = 77 AND C.coursecode LIKE 'SST%' AND M.fk_semesterid = 4
ORDER BY C.coursecode
'''
print('\nSST Courses offered by HOD in Session 77, Semester 4:')
for r in DB.fetch_all(query3):
    print(r)
