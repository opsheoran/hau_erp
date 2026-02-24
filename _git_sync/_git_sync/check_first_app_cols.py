from app.db import DB
res = DB.fetch_all("SELECT TOP 0 * FROM SAL_FirstAppointment_Details")
if res:
    print(res[0].keys())
else:
    # If no rows, check sp_columns
    cols = DB.fetch_all("EXEC sp_columns 'SAL_FirstAppointment_Details'")
    print([c['COLUMN_NAME'] for c in cols])
