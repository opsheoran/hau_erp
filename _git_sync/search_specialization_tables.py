from app.db import DB

# Search for tables containing 'Spec' in their name
tables = DB.fetch_all("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME LIKE '%Spec%'")

print(f"{'Table Name':<40} | {'Record Count':<10}")
print("-" * 55)

for t in tables:
    name = t['TABLE_NAME']
    try:
        count = DB.fetch_scalar(f"SELECT COUNT(*) FROM [{name}]")
        print(f"{name:<40} | {count:<10}")
    except:
        print(f"{name:<40} | Error")
