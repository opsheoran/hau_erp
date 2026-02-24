from app import app
from app.db import DB

with app.app_context():
    print("--- SAL_SubScheme_Mst Data ---")
    data = DB.fetch_all("SELECT TOP 5 * FROM SAL_SubScheme_Mst")
    for row in data:
        print(row)
    
    print("\n--- SAL_Scheme_Mst (Checking if exists) ---")
    try:
        data2 = DB.fetch_all("SELECT TOP 5 * FROM SAL_Scheme_Mst")
        for row in data2:
            print(row)
    except Exception as e:
        print(f"Error checking SAL_Scheme_Mst: {e}")
