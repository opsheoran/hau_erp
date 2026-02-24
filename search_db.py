from app.db import DB
res = DB.fetch_all("SELECT TABLE_NAME, COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE DATA_TYPE IN ('char', 'varchar', 'nchar', 'nvarchar')")
for r in res:
    try:
        row = DB.fetch_one(f"SELECT TOP 1 1 FROM [{r['TABLE_NAME']}] WHERE [{r['COLUMN_NAME']}] LIKE '%AAH/Fish%'")
        if row:
            print(f"FOUND: {r['TABLE_NAME']}.{r['COLUMN_NAME']}")
    except:
        pass
