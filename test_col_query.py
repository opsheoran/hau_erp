from app.db import DB
print(DB.fetch_all("SELECT TOP 10 pk_collegeid, collegename, fk_locid FROM SMS_College_Mst WHERE fk_locid = 'VC-3'"))
