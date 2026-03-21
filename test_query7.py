from app.db import DB

print(DB.fetch_all("SELECT column_name FROM information_schema.columns WHERE table_name = 'SMS_RollNumber_Dtl'"))
print(DB.fetch_all("SELECT column_name FROM information_schema.columns WHERE table_name = 'SMS_RollNumber_Mst'"))
