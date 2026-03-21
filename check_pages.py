import sys, os
sys.path.insert(0, os.getcwd())
from app.db import DB
pages = DB.fetch_all("SELECT pk_webpageId, menucaption, webpagename, parentId, fk_moduleId FROM UM_WebPage_Mst WHERE menucaption LIKE '%Exam%' OR webpagename LIKE '%Exam%'")
for p in pages:
    print(f"{p['pk_webpageId']}: {p['menucaption']} ({p['webpagename']}) - Mod:{p['fk_moduleId']} - Parent:{p['parentId']}")
