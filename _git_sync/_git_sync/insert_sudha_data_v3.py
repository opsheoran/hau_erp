from app.db import DB
res = DB.fetch_all("SELECT pk_appointmentid FROM SAL_FirstAppointment_Details WHERE pk_appointmentid LIKE 'EST-%'")
max_num = 0
for r in res:
    try:
        num = int(r['pk_appointmentid'].split('-')[1])
        if num > max_num: max_num = num
    except: continue

next_id = f"EST-{max_num + 1}"
emp_id = 'AG-5984'
sql = """
INSERT INTO SAL_FirstAppointment_Details (
    pk_appointmentid, fk_empid, title, remarks, JoiningDate, OrderNo, 
    AppointmentDate, DDO, Designation, Department, BasicPay, PayScale, JoiningTime
) VALUES (
    ?, ?, 'First Appointment - Sudha Bishnoi', 'Sample Data Entry', 
    '2024-07-04', 'ORD/2024/001', '2024-07-03', 
    'Regional Director, CRS Sirsa', 'Assistant Scientist', 
    'Cotton Research Station, Sirsa', 59400.00, 
    '67700-191000-0SP-NPA-CA-SA', 'Fore Noon'
)
"""
DB.execute(sql, [next_id, emp_id])
print(f"Data for Sudha Bishnoi inserted with ID {next_id}.")
