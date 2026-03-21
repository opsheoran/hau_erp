from app.db import DB
res = DB.fetch_one("SELECT * FROM SMS_Student_Mst WHERE enrollmentno='2025BSP01BIV'")
for k, v in res.items():
    print(f"{k} = {v}")
