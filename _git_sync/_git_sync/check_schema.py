from app.db import DB
res = DB.fetch_all("SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'PA_Education_Specialization_Mst'")
for r in res:
    print(r)
