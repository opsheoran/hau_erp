from app.db import DB
emp_id = 'AG-5984'
# Insert Sudha's detailed appointment as requested
sql = """
INSERT INTO SAL_FirstAppointment_Details (
    fk_empid, title, remarks, JoiningDate, OrderNo, AppointmentDate, 
    DDO, Designation, Department, BasicPay, PayScale, JoiningTime
) VALUES (
    ?, 'First Appointment - Sudha Bishnoi', 'Sample Data Entry', 
    '2024-07-04', 'ORD/2024/001', '2024-07-03', 
    'Regional Director, CRS Sirsa', 'Assistant Scientist', 
    'Cotton Research Station, Sirsa', 59400.00, 
    '67700-191000-0SP-NPA-CA-SA', 'Fore Noon'
)
"""
DB.execute(sql, [emp_id])
print("Sudha Bishnoi appointment data inserted successfully.")
