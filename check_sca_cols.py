from app.db import DB
try:
    conn = DB.get_connection()
    cur = conn.cursor()
    cur.execute("SELECT TOP 1 * FROM SMS_StuCourseAllocation")
    cols = [c[0] for c in cur.description]
    print("Columns: " + ", ".join(cols))
except Exception as e:
    print("Error: " + str(e))
