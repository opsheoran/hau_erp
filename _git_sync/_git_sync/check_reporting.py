from app.db import DB
emp = DB.fetch_one("SELECT pk_empid, empname, fk_deptid, reportingto FROM SAL_Employee_Mst WHERE empcode = 'HAU00212'")
if emp:
    print(f"Employee: {emp}")
    # Also check Department HOD
    if emp['fk_deptid']:
        dept = DB.fetch_one("SELECT Hod_Id, Description FROM Department_Mst WHERE pk_deptid = ?", [emp['fk_deptid']])
        print(f"Department: {dept}")
else:
    print("Employee HAU00212 not found")
