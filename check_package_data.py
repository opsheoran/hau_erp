from app.db import DB

def check_package_data():
    print("\n--- Package Samples ---")
    try:
        packages = DB.fetch_all("SELECT TOP 5 pk_packageID, PackageName, fk_degreeid, fk_semesterid FROM SMS_CoursePackage_MST")
        for p in packages: print(p)
    except Exception as e: print(e)

if __name__ == "__main__":
    check_package_data()
