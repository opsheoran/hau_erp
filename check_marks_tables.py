import sys, os
sys.path.insert(0, os.getcwd())
from app.db import DB
tables = DB.fetch_all("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME LIKE '%Marks%'")
print([t['TABLE_NAME'] for t in tables])
