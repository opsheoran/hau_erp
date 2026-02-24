from app.db import DB
res = DB.fetch_one("SELECT pk_empid, empname, empcode, manualempcode FROM SAL_Employee_Mst WHERE empcode = 'HAU04855' OR manualempcode = 'HAU04855' OR empname LIKE '%Sudha Bishnoi%'")
if res:
    print(f"Employee Found: {res}")
    emp_id = res['pk_empid']
    # Check for appointment details
    appts = DB.fetch_all("SELECT * FROM SAL_FirstAppointment_Details WHERE fk_empid = ?", [emp_id])
    print(f"Appointment Count: {len(appts)}")
    for a in appts:
        print(a)
else:
    print("Employee Sudha Bishnoi (HAU04855) not found.")
