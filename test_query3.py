from app.db import DB
res = DB.fetch_one("SELECT * FROM SMS_Student_Mst WHERE enrollmentno='2025BSP01BIV'")
print([(k, v) for k, v in res.items() if isinstance(v, str)])
