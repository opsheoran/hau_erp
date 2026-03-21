from app.db import DB
res = DB.fetch_all("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'SMS_Exam_Mst'")
print([r['COLUMN_NAME'] for r in res])
