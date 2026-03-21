from app.db import DB
print(DB.fetch_one("SELECT FirstName, MiddleName, LastName FROM EMP_Employee_Mst WHERE EmpId='HA-131'"))
print(DB.fetch_one("SELECT * FROM EMP_Employee_Mst WHERE EmpId='HA-131'"))
