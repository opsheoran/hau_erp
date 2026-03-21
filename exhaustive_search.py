from app.db import DB

def exhaustive_search():
    search_term = 'Mathematics'
    print(f"\n--- Searching for '{search_term}' across tables ---")
    try:
        conn = DB.get_connection()
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sys.tables")
        tables = [row[0] for row in cursor.fetchall()]
        
        found = []
        for table in tables:
            try:
                cursor.execute(f"SELECT TOP 1 * FROM {table}")
                cols = [c[0] for c in cursor.description]
                for col in cols:
                    # Only check string columns
                    cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE CAST([{col}] AS NVARCHAR(MAX)) LIKE ?", [f'%{search_term}%'])
                    if cursor.fetchone()[0] > 0:
                        found.append((table, col))
                        print(f"Found in {table}.{col}")
            except:
                continue
        
        print("\nSummary of findings:")
        for f in found:
            print(f)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    exhaustive_search()
