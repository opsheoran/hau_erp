from app.db import DB

def check_syllabus_tables():
    print("\n--- Syllabus Tables ---")
    try:
        tables = DB.fetch_all("SELECT name FROM sys.tables WHERE name LIKE '%syllabus%'")
        for t in tables:
            print(t['name'])
    except Exception as e: print(e)

if __name__ == "__main__":
    check_syllabus_tables()
