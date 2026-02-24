from app.db import DB
eid = 'ES-272'
search_tables = [
    'SAL_Employee_Increment',
    'SAL_EmpPromotion_Details',
    'Sal_payfixsation_dtl'
]

print(f"Searching Increment/Promotion for Ram Niwas ({eid}):")
for table in search_tables:
    try:
        res = DB.fetch_all(f"SELECT * FROM {table} WHERE fk_empid = ?", [eid])
        if res:
            print(f"\n--- Found in {table} ---")
            for r in res:
                print(r)
    except:
        pass
