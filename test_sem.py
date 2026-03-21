from app.db import DB
print(DB.fetch_all("SELECT COLUMN_NAME FROM information_schema.columns WHERE TABLE_NAME='SMS_Semester_Mst'"))
