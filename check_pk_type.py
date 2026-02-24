from app.db import DB
res = DB.fetch_all("EXEC sp_columns 'SAL_FirstAppointment_Details'")
for r in res:
    if r['COLUMN_NAME'] == 'pk_appointmentid':
        print(f"Column: {r['COLUMN_NAME']}, Type: {r['TYPE_NAME']}, Length: {r['LENGTH']}")
