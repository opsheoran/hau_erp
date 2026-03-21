from app.db import DB
res = DB.fetch_one("SELECT enrollmentno, enrollmentnoWithSeparator, manualRegno, MennualAddNo, provisionalno, AdmissionNo FROM SMS_Student_Mst WHERE pk_sid=11681")
print(res)
