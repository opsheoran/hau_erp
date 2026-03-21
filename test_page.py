from app.db import DB
print(DB.fetch_all("SELECT menucaption, pagepath FROM UM_WebPage_Mst WHERE menucaption LIKE '%UG and MBA%'"))
