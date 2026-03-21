from app.db import DB
print(DB.fetch_all("SELECT pk_degreeid, degreename, fk_degreetypeid FROM SMS_Degree_Mst WHERE fk_degreetypeid = 1"))
