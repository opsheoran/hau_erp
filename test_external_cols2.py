from app.db import DB
tables = ['SMS_ExternalExaminer_Mst_Dtl', 'SMS_PG_ExternalTeacher_Dtl']
for t in tables:
    print(f"--- {t} ---")
    res = DB.fetch_all(f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{t}'")
    for r in res:
        print(r['COLUMN_NAME'])
