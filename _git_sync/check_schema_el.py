from app.db import DB

query = """
SELECT COLUMN_NAME, DATA_TYPE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'SAL_EarnedLeave_Details'
"""
cols = DB.fetch_all(query)
for c in cols:
    print(c)
