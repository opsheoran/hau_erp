from app.db import DB

tables = ['SMS_ExternalExaminarCourse_Dtl', 'SMS_ExternalExaminar_Dtl', 'SMS_ExternalExaminer_Mst']

for t in tables:
    print(f"--- {t} ---")
    res = DB.fetch_all(f"SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{t}'")
    for r in res:
        print(r['COLUMN_NAME'])
