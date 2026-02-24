from app.db import DB
tables = DB.fetch_all("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME LIKE '%Message%' OR TABLE_NAME LIKE '%Comm%'")
for t in tables:
    name = t['TABLE_NAME']
    try:
        count = DB.fetch_scalar(f"SELECT COUNT(*) FROM [{name}]")
        print(f"{name}: {count}")
    except:
        print(f"{name}: Error")
