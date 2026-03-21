from app.db import DB
res = DB.fetch_all("SELECT DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'UM_Location_Mst' AND COLUMN_NAME = 'Pk_LocId'")
print(res)
