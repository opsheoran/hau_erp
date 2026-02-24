from app.db import DB
import sys

col_name = sys.argv[1] if len(sys.argv) > 1 else 'pftype'
query = "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE COLUMN_NAME = ?"
res = DB.fetch_all(query, [col_name])
if res:
    print(f"Column '{col_name}' found in tables:")
    for r in res:
        print(f"- {r['TABLE_NAME']}")
else:
    print(f"Column '{col_name}' not found in any table.")
