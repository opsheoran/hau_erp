from app.db import DB
print(DB.fetch_all("SELECT TOP 5 * FROM SMS_TCourseAlloc_Mst WHERE fk_batchdtlid IS NOT NULL"))
