from app.db import DB
res = DB.fetch_one("SELECT COLUMNPROPERTY(OBJECT_ID('SAL_FirstAppointment_Details'), 'pk_appointmentid', 'IsIdentity') as is_identity")
print(res)
