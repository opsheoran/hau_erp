from app.db import DB
codes = ['HAU00212', 'HAU00245', 'HAU04855']
for code in codes:
    print(f"\n--- Checking data for {code} ---")
    emp = DB.fetch_one("SELECT pk_empid, empname, curbasic FROM SAL_Employee_Mst WHERE empcode = ?", [code])
    if not emp:
        print("Employee not found.")
        continue
    
    eid = emp['pk_empid']
    other = DB.fetch_one("""
        SELECT dateofappointment, dateofjoining, OrderNo, joiningddo, AppointmentTime 
        FROM SAL_EmployeeOther_Details WHERE fk_empid = ?
    """, [eid])
    print(f"SAL_Employee_Mst: {emp}")
    print(f"SAL_EmployeeOther_Details: {other}")
    
    first_app = DB.fetch_one("SELECT * FROM SAL_FirstAppointment_Details WHERE fk_empid = ?", [eid])
    if first_app:
        print("SAL_FirstAppointment_Details record exists.")
    else:
        print("No record in SAL_FirstAppointment_Details.")
