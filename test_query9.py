from app.db import DB
cols = DB.fetch_all("SELECT table_name FROM information_schema.tables WHERE table_name LIKE '%EMP%'")
print([c['table_name'] for c in cols])
