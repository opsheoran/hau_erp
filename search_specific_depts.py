from app.db import DB

def search_specific_terms():
    terms = ['Mathematics and Statistics', 'Computer Section', 'COA Associate Dean', 'CBNT']
    tables = ['Department_Mst', 'SMS_Dept_Mst', 'SMS_BranchMst']
    
    for table in tables:
        print(f"\n--- Searching in {table} ---")
        try:
            conn = DB.get_connection()
            cursor = conn.cursor()
            cursor.execute(f"SELECT TOP 1 * FROM {table}")
            cols = [c[0] for c in cursor.description]
            
            for term in terms:
                for col in cols:
                    try:
                        query = f"SELECT [{cols[0]}], [{cols[1]}] FROM {table} WHERE CAST([{col}] AS NVARCHAR(MAX)) LIKE ?"
                        results = DB.fetch_all(query, [f'%{term}%'])
                        if results:
                            print(f"Found '{term}' in {table}.{col}:")
                            for r in results:
                                print(r)
                    except: continue
        except Exception as e:
            print(f"Error checking {table}: {e}")

if __name__ == "__main__":
    search_specific_terms()
