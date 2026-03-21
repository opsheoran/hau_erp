from app.db import DB
print(DB.fetch_all("SELECT TOP 10 * FROM DepartmentHeadMapping WHERE fk_EmpId = 'ES-271'"))
