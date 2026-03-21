from app.db import DB
print(DB.fetch_all("SELECT TOP 5 pk_batchdtl, name_of_batch FROM SMS_Batch_Dtl"))
