from app.db import DB
from datetime import datetime
next_id = 'EST-1' # Hardcoded for first entry if none exists with this prefix
emp_id = 'AG-5984'
sql = """
INSERT INTO SAL_FirstAppointment_Details (
    pk_appointmentid, fk_empid, title, remarks, JoiningDate, OrderNo, 
    AppointmentDate, DDO, Designation, Department, BasicPay, PayScale, JoiningTime,
    fk_insUserID, fk_insDateID
) VALUES (
    ?, ?, 'First Appointment - Sudha Bishnoi', 'Sample Data Entry', 
    '2024-07-04', 'ORD/2024/001', '2024-07-03', 
    'Regional Director, CRS Sirsa', 'Assistant Scientist', 
    'Cotton Research Station, Sirsa', 59400.00, 
    '67700-191000-0SP-NPA-CA-SA', 'Fore Noon',
    1, GETDATE()
)
"""
DB.execute(sql, [next_id, emp_id])
print(f"Data for Sudha Bishnoi inserted successfully.")
