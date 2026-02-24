from app.db import DB
emp_id = 'ES-271' # HAU00212
sql = """
UPDATE SAL_FirstAppointment_Details 
SET JoiningDate = '2000-12-20',
    OrderNo = 'r1/94/9337-41 dated18/08/1994',
    AppointmentDate = '2000-12-20',
    DDO = 'A&AO, COBS&H',
    Designation = 'Professor',
    Department = 'Mathematics and Statistics',
    BasicPay = 2000.00,
    PayScale = '2000-3200',
    JoiningTime = 'Fore Noon',
    fk_updUserID = 1,
    fk_updDateID = GETDATE()
WHERE fk_empid = ?
"""
DB.execute(sql, [emp_id])
print(f"Data for HAU00212 updated successfully.")
