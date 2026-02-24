from app import app
from app.db import DB

with app.app_context():
    print("--- Head Types ---")
    heads = DB.fetch_all("SELECT DISTINCT headtype FROM SAL_Head_Mst")
    print(heads)
    
    print("\n--- Sample Emp with Heads ---")
    emp = DB.fetch_one("SELECT TOP 1 fk_empid FROM SAL_EmployeeHead_Details")
    print(emp)
    
    if emp:
        print("\n--- Heads for this Emp ---")
        details = DB.fetch_all("SELECT H.description, H.headtype, EH.amount FROM SAL_EmployeeHead_Details EH INNER JOIN SAL_Head_Mst H ON EH.fk_headid = H.pk_headid WHERE EH.fk_empid = ?", [emp['fk_empid']])
        for d in details:
            print(d)
