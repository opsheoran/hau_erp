from app.db import DB
print([c['column_name'] for c in DB.fetch_all("SELECT column_name FROM information_schema.columns WHERE table_name = 'SAL_Employee_Mst'")])
