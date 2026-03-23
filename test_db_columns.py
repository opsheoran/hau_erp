from app.db import DB
from app import create_app
app = create_app()
with app.app_context():
    conn = DB.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='SMS_Student_Mst'")
    cols = [row[0] for row in cursor.fetchall()]
    print("Mst", [c for c in cols if 'deg' in c.lower() or 'comp' in c.lower() or 'cert' in c.lower()])
    
    cursor.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='SMS_DegreeComplete_Dtl'")
    cols = [row[0] for row in cursor.fetchall()]
    print("Dtl", cols)
