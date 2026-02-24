from app.db import DB
res = DB.fetch_all("SELECT * FROM SAL_Employee_SeventhPayFixation WHERE fk_empid = 'ES-271'")
for r in res: print(r)
