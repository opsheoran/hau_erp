from app.db import DB

query = """
SELECT TOP 5 
    todate, 
    ISNULL(CONVERT(varchar, TRY_CAST(todate as datetime), 103), todate) as date_fmt 
FROM SAL_LTC_Detail
"""
res = DB.fetch_all(query)
for r in res:
    print(r)
