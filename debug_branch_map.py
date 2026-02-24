from app.db import DB

def check_branch_mapping():
    print("--- Searching 5035 in SMS_BranchMst ---")
    rows = DB.fetch_all("SELECT * FROM SMS_BranchMst WHERE Branchname LIKE '%5035%'")
    for r in rows:
        print(r)
        
    print("\n--- Searching 1140 in SMS_BranchMst ---")
    rows2 = DB.fetch_all("SELECT * FROM SMS_BranchMst WHERE Branchname LIKE '%1140%'")
    for r in rows2:
        print(r)

if __name__ == '__main__':
    check_branch_mapping()
