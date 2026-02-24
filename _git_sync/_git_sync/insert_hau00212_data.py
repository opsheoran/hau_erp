from app.db import DB
res = DB.fetch_all("SELECT pk_appointmentid FROM SAL_FirstAppointment_Details WHERE pk_appointmentid LIKE 'EST-%'")
max_num = 0
for r in res:
    try:
        num = int(r['pk_appointmentid'].split('-')[1])
        if num > max_num: max_num = num
    except: continue

next_id = f"EST-{max_num + 1}"
emp_id = 'ES-271' # HAU00212
sql = """
INSERT INTO SAL_FirstAppointment_Details (
    pk_appointmentid, fk_empid, title, remarks, JoiningDate, OrderNo, 
    AppointmentDate, DDO, Designation, Department, BasicPay, PayScale, JoiningTime,
    fk_insUserID, fk_insDateID, fk_updUserID, fk_updDateID
) VALUES (
    ?, ?, 'First Appointment', 'Historical Record', 
    '2000-12-20', 'r1/94/9337-41 dated18/08/1994', '2000-12-20', 
    'A&AO, COBS&H', 'Professor', 
    'Mathematics and Statistics', 2000.00, 
    '2000-3200', 'Fore Noon',
    1, GETDATE(), 1, GETDATE()
)
"""
DB.execute(sql, [next_id, emp_id])
print(f"Data for HAU00212 inserted successfully with ID {next_id}.")
