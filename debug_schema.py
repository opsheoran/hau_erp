from app.db import DB

def check_cols(table):
    try:
        conn = DB.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT TOP 1 * FROM " + table)
        cols = [c[0] for c in cur.description]
        print("Columns in " + table + ": " + ", ".join(cols))
    except Exception as e:
        print("Error: " + str(e))

check_cols("SMS_BranchMst")
check_cols("SMS_Degree_Mst")
check_cols("SMS_College_Mst")
check_cols("SMS_Semester_Mst")
check_cols("SMS_AcademicSession_Mst")
