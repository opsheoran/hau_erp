from app.db import DB

def check_cols(table):
    try:
        conn = DB.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT TOP 1 * FROM " + table)
        cols = [c[0] for c in cur.description]
        print("
Columns in " + table + ":")
        for c in cols:
            print(" - " + c)
    except Exception as e:
        print("Error checking " + table + ": " + str(e))

if __name__ == "__main__":
    check_cols("SMS_BranchMst")
    check_cols("SMS_DegreeCycle_Mst")
    check_cols("SMS_Semester_Mst")
    check_cols("SMS_AcademicSession_Mst")
