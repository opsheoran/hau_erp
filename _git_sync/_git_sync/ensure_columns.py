from app.db import DB
cols_res = DB.fetch_all("EXEC sp_columns 'SAL_FirstAppointment_Details'")
cols = [c['COLUMN_NAME'].lower() for c in cols_res]
to_add = [
    ('JoiningDate', 'datetime'), ('OrderNo', 'varchar(500)'), 
    ('AppointmentDate', 'datetime'), ('DDO', 'varchar(500)'), 
    ('Designation', 'varchar(500)'), ('Department', 'varchar(500)'), 
    ('BasicPay', 'decimal(18,2)'), ('PayScale', 'varchar(200)'), 
    ('ProbationDate', 'datetime'), ('DueDatePP', 'datetime'), 
    ('SrNo', 'varchar(50)'), ('JoiningTime', 'varchar(50)')
]
for col, dtype in to_add:
    if col.lower() not in cols:
        print(f"Adding column {col}...")
        DB.execute(f"ALTER TABLE SAL_FirstAppointment_Details ADD {col} {dtype}")
print("Table check complete.")
