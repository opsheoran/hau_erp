from app.db import DB
print([c['column_name'] for c in DB.fetch_all("SELECT column_name FROM information_schema.columns WHERE table_name = 'SMS_TCourseAlloc_Mst'")])
print(DB.fetch_all("SELECT * FROM SMS_TCourseAlloc_Mst WHERE fk_courseid=4022"))
