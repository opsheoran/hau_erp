from app.db import DB

def check_mappings():
    ids = [2, 2488]
    for cid in ids:
        print(f"\n--- Mapping for CID {cid} ---")
        try:
            rows = DB.fetch_all("SELECT * FROM SMS_Course_Mst_Dtl WHERE fk_courseid = ?", [cid])
            for r in rows: print(r)
        except Exception as e: print(e)

if __name__ == "__main__":
    check_mappings()
