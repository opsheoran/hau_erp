from app.db import DB
print([c['column_name'] for c in DB.fetch_all("SELECT column_name FROM information_schema.columns WHERE table_name = 'SMS_TCourseAlloc_Dtl'")])
print(DB.fetch_all("SELECT D.* FROM SMS_TCourseAlloc_Dtl D WHERE D.fk_courseid=4022"))
