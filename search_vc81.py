from app.db import DB

def search_value():
    term = 'VC-81'
    print(f"\n--- Searching for '{term}' ---")
    try:
        conn = DB.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sys.tables")
        tables = [row[0] for row in cursor.fetchall()]
        for table in tables:
            try:
                cursor.execute(f"SELECT TOP 1 * FROM {table}")
                cols = [c[0] for c in cursor.description]
                for col in cols:
                    cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE CAST([{col}] AS NVARCHAR(MAX)) = ?", [term])
                    if cursor.fetchone()[0] > 0:
                        print(f"EXACT MATCH in {table}.{col}")
            except: continue
    except Exception as e: print(e)

if __name__ == "__main__":
    search_value()
