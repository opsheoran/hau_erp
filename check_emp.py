from app.db import DB
res = DB.fetch_one("SELECT pk_empid, empid, empcode, manualempcode, empname FROM SAL_Employee_Mst WHERE empcode='HA-131' OR pk_empid='HA-131' OR manualempcode='HA-131'")
print(res)
