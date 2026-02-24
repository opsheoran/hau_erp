from app.db import DB
eid = 'ES-272'
tables = [
    ('SAL_EmpPromotion_Details', 'OrderNo'),
    ('SAL_EmployeeServiceVerification_Details', 'OrderNo'),
    ('EST_Disciplinary_Action_Details', 'OrderNo'),
    ('SAL_EmployeeEducation_Details', 'OrderNo'),
    ('SAL_LoanOrder_Mst', 'OrderNo'),
    ('SAL_Employee_SeventhPayFixation', 'OrderNo'), # Checking if exists
    ('EMP_NonTeachingACPVerify_Mst', 'OrderNo')
]

print(f"Ram Niwas ({eid}) Order Records:")
for table, col in tables:
    try:
        res = DB.fetch_all(f"SELECT {col} FROM {table} WHERE fk_empid = ?", [eid])
        for r in res:
            if r[col]: print(f"{table}: {r[col]}")
    except:
        # Retry with fk_EmpId case
        try:
            res = DB.fetch_all(f"SELECT {col} FROM {table} WHERE fk_EmpId = ?", [eid])
            for r in res:
                if r[col]: print(f"{table}: {r[col]}")
        except:
            pass
