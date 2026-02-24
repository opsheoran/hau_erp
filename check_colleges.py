from app.db import DB
res = DB.fetch_all("SELECT pk_collegeid, collegename, fk_deanid FROM SMS_College_Mst")
for r in res:
    print(r)
