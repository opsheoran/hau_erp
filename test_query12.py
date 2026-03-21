from app.db import DB
print(DB.fetch_all("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'SAL_Employee_Mst' AND column_name IN ('empid', 'pk_empid')"))
print(DB.fetch_all("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'SMS_Course_Mst' AND column_name = 'fk_DeptEmpid'"))
