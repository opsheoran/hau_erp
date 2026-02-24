from app.db import DB
emp = DB.fetch_one("SELECT pk_empid, empname FROM SAL_Employee_Mst WHERE empcode = 'HAU00213'")
if not emp:
    print("Employee HAU00213 not found.")
else:
    eid = emp['pk_empid']
    print(f"Employee Found: {emp['empname']} ({eid})")
    print("\n--- Order Numbers Found ---")
    
    res1 = DB.fetch_all("SELECT OrderNo FROM SAL_FirstAppointment_Details WHERE fk_empid = ?", [eid])
    for r in res1: print(f"SAL_FirstAppointment_Details: {r['OrderNo']}")
    
    res2 = DB.fetch_all("SELECT OrderNo FROM SAL_EmployeeOther_Details WHERE fk_empid = ?", [eid])
    for r in res2: print(f"SAL_EmployeeOther_Details: {r['OrderNo']}")
    
    res3 = DB.fetch_all("SELECT OrderNo FROM SAL_Appointing_Authority WHERE fk_EmpId = ?", [eid])
    for r in res3: print(f"SAL_Appointing_Authority: {r['OrderNo']}")
