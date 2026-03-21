from app.db import DB
print(DB.fetch_all("SELECT TOP 5 fk_batchid_Th, fk_batchid_Pr FROM SMS_Student_Mst WHERE fk_batchid_Th IS NOT NULL"))
