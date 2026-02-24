from app.db import DB
print("--- SAL_EmployeeOther_Details Sample ---")
res = DB.fetch_all("SELECT TOP 3 dateofjoining, OrderNo, AppointmentTime, joiningddo FROM SAL_EmployeeOther_Details WHERE dateofjoining IS NOT NULL")
for r in res: print(r)

emp_ids = ['ES-271', 'ES-347', 'AG-5984']
for eid in emp_ids:
    print(f"\nChecking eid {eid} in Service Book details...")
    try:
        sb = DB.fetch_all("SELECT * FROM EST_EmpServiceBookDigitizedView_Details WHERE fk_empid = ?", [eid])
        if sb:
            for row in sb:
                # print non-null items
                print({k: v for k, v in row.items() if v})
    except Exception as e:
        print(f"Error: {e}")
