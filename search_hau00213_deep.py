from app.db import DB
eid = 'ES-272'
search_tables = [
    'EST_EmpServiceBookDigitizedView_Details',
    'EmployeeRecord_Details_Master',
    'sal_emp_TeachersPromotion_EmpRecord_detail',
    'LRS_Service_Details',
    'SAL_EmployeeServiceVerification_Details'
]

print(f"Deep Search for Ram Niwas ({eid}):")
for table in search_tables:
    try:
        cols_res = DB.fetch_all(f"EXEC sp_columns '{table}'")
        cols = [c['COLUMN_NAME'] for c in cols_res]
        id_col = None
        for c in ['fk_empid', 'fk_EmpId', 'EmpId', 'fk_eid']:
            if c.lower() in [col.lower() for col in cols]:
                id_col = c
                break
        
        if id_col:
            res = DB.fetch_all(f"SELECT * FROM {table} WHERE {id_col} = ?", [eid])
            if res:
                print(f"\n--- Found in {table} ---")
                for r in res:
                    print(r)
    except Exception as e:
        print(f"Error checking {table}: {e}")
