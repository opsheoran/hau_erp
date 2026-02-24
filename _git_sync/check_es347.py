from app.db import DB
res = DB.fetch_one("""
    SELECT E.empname, E.empcode, D.designation 
    FROM SAL_Employee_Mst E 
    INNER JOIN SAL_Designation_Mst D ON E.fk_desgid = D.pk_desgid 
    WHERE E.pk_empid = 'ES-347'
""")
print(res)
