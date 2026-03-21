from app.db import DB

def debug_courses():
    codes = ['AGRON 101 old', 'AAH 503 BSMA']
    for code in codes:
        print(f"\n--- Full Data for {code} ---")
        try:
            row = DB.fetch_one("SELECT * FROM SMS_Course_Mst WHERE coursecode = ?", [code])
            if row:
                for k, v in row.items():
                    print(f"{k}: {v}")
            else:
                print("Not found")
        except Exception as e:
            print(e)

if __name__ == "__main__":
    debug_courses()
