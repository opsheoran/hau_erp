from app.db import DB

def check_239():
    print("--- Checking 239 in schemeandsubscheme ---")
    rows = DB.fetch_all("SELECT * FROM schemeandsubscheme WHERE CAST([Scheme code] AS INT) = 239")
    for r in rows:
        print(r)

if __name__ == '__main__':
    check_239()
