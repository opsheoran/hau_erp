from app.db import DB
print(DB.fetch_one("SELECT * FROM SMS_RollNumber_Dtl WHERE originalRollNo='BSP-101' OR RollNumber='BSP-101'"))
print(DB.fetch_one("SELECT * FROM SMS_Student_RollNo_Dtl WHERE rollno='BSP-101'"))
