from app.db import DB

def check_icar_pb1():
    print("--- Searching PB-1-ICAR in schemeandsubscheme ---")
    rows = DB.fetch_all("SELECT * FROM schemeandsubscheme WHERE [Name of Sub-scheme] LIKE '%PB-1-ICAR%'")
    for r in rows:
        print(r)
        
    print("\n--- Checking SAL_SubScheme_Mst for 239 ---")
    rows2 = DB.fetch_all("SELECT * FROM SAL_SubScheme_Mst WHERE pk_subanc = 239")
    for r in rows2:
        print(r)
        
    print("\n--- Checking SAL_Scheme_Mst ---")
    try:
        rows3 = DB.fetch_all("SELECT * FROM SAL_Scheme_Mst WHERE pk_scheme = 239")
        for r in rows3:
            print(r)
    except:
        print("SAL_Scheme_Mst check failed.")

if __name__ == '__main__':
    check_icar_pb1()
