from app.db import DB
print(DB.fetch_one("SELECT fk_employeeid FROM SMS_TCourseAlloc_Mst WHERE pk_tcourseallocid=75024"))
