from app.db import DB

def search_all_tables(search_values):
    print(f"Starting exhaustive database search for: {search_values}")
    
    # Get all tables
    tables = DB.fetch_all("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'")
    
    for table_row in tables:
        table_name = table_row['TABLE_NAME']
        try:
            cols_query = f"""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = '{table_name}' 
                AND DATA_TYPE IN ('varchar', 'nvarchar', 'text', 'ntext', 'char', 'nchar')
            """
            columns = DB.fetch_all(cols_query)
            if not columns: continue
            
            where_clauses = []
            params = []
            for col in columns:
                for val in search_values:
                    where_clauses.append(f"[{col['COLUMN_NAME']}] LIKE ?")
                    params.append(f"%{val}%")
            
            if not where_clauses: continue
            search_query = f"SELECT * FROM [{table_name}] WHERE " + " OR ".join(where_clauses)
            results = DB.fetch_all(search_query, params)
            
            if results:
                print("\n>>> FOUND IN TABLE: " + table_name)
                for r in results:
                    # Clean dictionary for display
                    clean_r = {str(k): str(v) for k, v in r.items() if v is not None and str(v).strip() != ''}
                    print(clean_r)
                    
        except Exception as e:
            pass

if __name__ == "__main__":
    search_all_tables(['HAU00213', 'ES-272'])
