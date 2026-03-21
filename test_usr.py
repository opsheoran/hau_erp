from app.db import DB
print(DB.fetch_one("SELECT * FROM UM_Users_Mst WHERE loginname = 'HAU00212'"))
