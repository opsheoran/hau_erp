from app.db import DB

try:
    print("SMS_Student_RollNo_Dtl:", DB.fetch_one("SELECT * FROM SMS_Student_RollNo_Dtl WHERE rollno='BSP-101'"))
except Exception as e:
    print("Error 1", e)

print([c['column_name'] for c in DB.fetch_all("SELECT column_name FROM information_schema.columns WHERE table_name = 'SMS_Student_RollNo_Dtl'")])
