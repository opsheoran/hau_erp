from app.db import DB

def find_exact_string(search_str):
    print("Searching for exact string: " + search_str)
    tables = DB.fetch_all("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'")
    for table_row in tables:
        table_name = table_row['TABLE_NAME']
        try:
            cols = DB.fetch_all("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '" + table_name + "' AND DATA_TYPE IN ('varchar', 'nvarchar', 'text')")
            if not cols: continue
            
            where = " OR ".join(["[" + c['COLUMN_NAME'] + "] LIKE ?" for c in cols])
            params = [("%" + search_str + "%") for _ in cols]
            
            res = DB.fetch_all("SELECT * FROM [" + table_name + "] WHERE " + where, params)
            if res:
                print("\nFOUND IN " + table_name + ":")
                for r in res:
                    print({k: v for k, v in r.items() if v and search_str in str(v)})
        except: pass

if __name__ == "__main__":
    find_exact_string("9337-41")
