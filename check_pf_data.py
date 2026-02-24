from app.db import DB

query = """
    SELECT TOP 10 E.empcode, E.empname, E.pfileno, G.gpfno, G.PFType
    FROM SAL_Employee_Mst E
    LEFT JOIN gpf_employee_details G ON E.pk_empid = G.fk_empid
    WHERE E.pfileno IS NOT NULL OR G.gpfno IS NOT NULL
"""
res = DB.fetch_all(query)
for r in res:
    print(f"Code: {r['empcode']}, Name: {r['empname']}, E.pfileno: {r['pfileno']}, G.gpfno: {r['gpfno']}, Type: {r['PFType']}")
