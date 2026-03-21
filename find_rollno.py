from app.db import DB
cols = DB.fetch_all("SELECT table_name, column_name FROM information_schema.columns WHERE column_name LIKE '%roll%'")
print(cols)
