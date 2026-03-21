import sys, os
sys.path.insert(0, os.getcwd())
from app.db import DB
tables = DB.fetch_all("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME LIKE '%Month%' OR TABLE_NAME LIKE '%Year%'")
for t in tables:
    print(t['TABLE_NAME'])
