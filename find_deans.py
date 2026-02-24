from app.db import DB
res = DB.fetch_all("""
    SELECT E.pk_empid, E.empname, D.designation 
    FROM SAL_Employee_Mst E 
    INNER JOIN SAL_Designation_Mst D ON E.fk_desgid = D.pk_desgid 
    WHERE D.designation LIKE '%Dean%'
""")
for r in res:
    print(r)
