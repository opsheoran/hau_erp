from app.db import DB
res = DB.fetch_one("""
    SELECT E.fk_gradeid, G.gradename, G.gradedetails 
    FROM SAL_Employee_Mst E 
    LEFT JOIN SAL_Grade_Mst G ON E.fk_gradeid = G.pk_gradeid 
    WHERE E.empcode = 'HAU00212'
""")
print(res)
