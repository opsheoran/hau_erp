from app.db import DB
print(DB.fetch_one("SELECT TOP 1 * FROM SMS_Exam_Mst"))
