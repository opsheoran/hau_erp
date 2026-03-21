from app.db import DB

def search_branch():
    print("\n--- Searching for 'Math' or 'Stat' in SMS_BranchMst ---")
    try:
        branches = DB.fetch_all("SELECT Pk_BranchId, Branchname FROM SMS_BranchMst WHERE Branchname LIKE '%Math%' OR Branchname LIKE '%Stat%'")
        for b in branches: print(b)
    except Exception as e: print(e)

if __name__ == "__main__":
    search_branch()
