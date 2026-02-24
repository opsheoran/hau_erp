from app.db import DB

def search_emp_tables(search_values):
    print("Searching for tables containing 'emp'...")
    tables = DB.fetch_all("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE' AND TABLE_NAME LIKE '%emp%'")
    print("Found " + str(len(tables)) + " tables. Searching records...")
    
    for table_row in tables:
        table_name = table_row['TABLE_NAME']
        try:
            cols = DB.fetch_all("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '" + table_name + "' AND DATA_TYPE IN ('varchar', 'nvarchar', 'text', 'char')")
            if not cols: continue
            
            where = " OR ".join(["[" + c['COLUMN_NAME'] + "] LIKE ?" for c in cols for val in search_values])
            params = [("%" + val + "%") for c in cols for val in search_values]
            
            res = DB.fetch_all("SELECT * FROM [" + table_name + "] WHERE " + where, params)
            if res:
                print("\nMATCH IN: " + table_name)
                for r in res:
                    print({k: v for k, v in r.items() if v is not None and str(v).strip() != ''})
        except: pass

if __name__ == "__main__":
    search_emp_tables(['HAU00213', 'ES-272'])
