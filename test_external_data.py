from app.db import DB
res = DB.fetch_all("SELECT TOP 5 * FROM SMS_ExternalExaminarCourse_Dtl")
print("SMS_ExternalExaminarCourse_Dtl:", res)
res2 = DB.fetch_all("SELECT TOP 5 * FROM SMS_ExternalExaminer_Mst")
print("SMS_ExternalExaminer_Mst:", res2)
