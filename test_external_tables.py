from app.db import DB
res = DB.fetch_all("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME LIKE '%External%'")
for r in res:
    print(r['TABLE_NAME'])
