from app.db import DB
res = DB.fetch_all("SELECT * FROM SAL_FirstAppointment_Details WHERE fk_empid = 'ES-271'")
print(f"Results count: {len(res)}")
for r in res:
    print("-" * 20)
    for k, v in r.items():
        if v: print(f"{k}: {v}")
