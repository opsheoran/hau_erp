from app.db import DB
print(DB.fetch_one("SELECT FirstName, MiddleName, LastName FROM SAL_Employee_Mst WHERE EmpId='HA-131'"))
