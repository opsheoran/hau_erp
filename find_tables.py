from app.db import DB
res = DB.fetch_all("SELECT table_name FROM information_schema.tables WHERE table_name LIKE '%Teacher%'")
print([r['table_name'] for r in res])
