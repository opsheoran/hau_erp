from app.db import DB
eid = 'ES-272'
res = DB.fetch_all("SELECT TOP 5 * FROM SAL_Employee_Increment WHERE fk_empid = ? ORDER BY dated ASC", [eid])
for r in res:
    print(r)
