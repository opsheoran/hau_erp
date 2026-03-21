from app.db import DB

def check_degree_data():
    print("\n--- Degree Data for 22 ---")
    try:
        deg = DB.fetch_one("SELECT pk_degreeid, minsem, maxsem FROM SMS_Degree_Mst WHERE pk_degreeid = 22")
        print(deg)
    except Exception as e: print(e)

if __name__ == "__main__":
    check_degree_data()
