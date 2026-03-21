from app.db import DB
tables = ['SMS_TCourseAlloc_Mst', 'SMS_TCourseAlloc_Dtl', 'SMS_ExamConfig_Mst', 'SMS_DegreeYear_Mst', 'SMS_College_Mst', 'SMS_Semester_Mst']
for table in tables:
    print(f"--- {table} ---")
    try:
        query = f"SELECT TOP 0 * FROM {table}"
        conn = DB.get_connection()
        cursor = conn.cursor()
        cursor.execute(query)
        columns = [column[0] for column in cursor.description]
        print(columns)
        conn.close()
    except Exception as e:
        print(f"Error fetching columns for {table}: {e}")
