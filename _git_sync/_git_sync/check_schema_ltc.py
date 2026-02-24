from app.db import DB

query = """
SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'SAL_LTC_Detail'
"""
cols = DB.fetch_all(query)
for c in cols:
    print(c)
