from app.db import DB
print(DB.fetch_all("SELECT TOP 5 B.pk_batchid, BD.pk_batchdtl, BD.name_of_batch FROM SMS_Batch_Mst B INNER JOIN SMS_Batch_Dtl BD ON B.pk_batchid = BD.fk_batchid"))
