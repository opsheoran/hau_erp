from app.db import DB
res = DB.fetch_all("SELECT TOP 5 c.coursecode, c.coursename FROM SMS_TCourseAlloc_Dtl ad JOIN SMS_TCourseAlloc_Mst a ON a.pk_tcourseallocid = ad.fk_tcourseallocid JOIN SMS_Course_Mst c ON c.pk_courseid = ad.fk_courseid")
print(res)