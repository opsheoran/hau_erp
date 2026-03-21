from app.db import DB
cols = DB.fetch_all("SELECT column_name FROM information_schema.columns WHERE table_name = 'SMS_Batch_Mst'")
print("SMS_Batch_Mst columns:", [c['column_name'] for c in cols])
cols2 = DB.fetch_all("SELECT column_name FROM information_schema.columns WHERE table_name = 'SMS_Batch_Dtl'")
print("SMS_Batch_Dtl columns:", [c['column_name'] for c in cols2])
