from app.db import DB
tables = ['SAL_EmployeeEducation_Details', 'SAL_Appointing_Authority', 'SAL_EmployeeOther_Details', 'SAL_FirstAppointment_Details']
for t in tables:
    try:
        res = DB.fetch_all(f"SELECT * FROM {t} WHERE OrderNo LIKE '%9337%'")
        if res:
            print(f"Found in {t}: {res}")
    except:
        pass
