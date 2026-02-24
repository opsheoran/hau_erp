from app.db import DB
max_id = DB.fetch_one("SELECT MAX(pk_appointmentid) as mid FROM SAL_FirstAppointment_Details")['mid']
next_id = (max_id or 0) + 1
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
