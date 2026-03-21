from app.db import DB
print(DB.fetch_all("SELECT TOP 5 pk_degreetypeid, degreetype FROM SMS_DegreeType_Mst"))
print(DB.fetch_all("SELECT TOP 5 pk_degreeid, degreename, fk_degreetypeid FROM SMS_Degree_Mst WHERE fk_degreetypeid IN (1,2,4)"))
