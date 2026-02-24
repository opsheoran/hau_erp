from app.db import DB
res = DB.fetch_all("SELECT * FROM SAL_FirstAppointment_Description_Details WHERE fk_appointmentid = 'CB-68'")
print(f"Results: {len(res)}")
for r in res:
    print(r)
