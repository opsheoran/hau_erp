from app.db import DB

def check_tables():
    conn = DB.get_connection()
    cur = conn.cursor()
    
    patterns = ['%Branch%', '%Spec%', '%Dept%', '%College%', '%Degree%', '%Semester%', '%Session%', '%Student%']
    print("Table Verification:")
    for p in patterns:
        cur.execute("SELECT name FROM sys.tables WHERE name LIKE ? ORDER BY name", [p])
        rows = cur.fetchall()
        print("\nPattern " + p + ":")
        for r in rows:
            print(" - " + r[0])

if __name__ == "__main__":
    check_tables()
