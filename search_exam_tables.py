import sys
import os
sys.path.insert(0, os.getcwd())
from app.db import DB

print("Searching for Exam tables:")
rows = DB.fetch_all("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME LIKE '%Exam%'")
for row in rows:
    table = row['TABLE_NAME']
    print(f"\n--- {table} ---")
    cols = DB.fetch_all("SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = ?", [table])
    for col in cols:
        print(f"  {col['COLUMN_NAME']} ({col['DATA_TYPE']})")
