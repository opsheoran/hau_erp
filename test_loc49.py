from app.db import DB
try:
    print("Trying location 49")
    res = DB.fetch_all("SELECT Pk_LocId, LocationName FROM UM_Location_Mst WHERE Pk_LocId = 49")
    print(res)
except Exception as e:
    print(e)
