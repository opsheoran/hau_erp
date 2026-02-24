from app.db import DB
res = DB.fetch_one("SELECT fk_controllingid FROM SAL_Employee_Mst WHERE pk_empid = 'ES-271'")
if res and res['fk_controllingid']:
    print(f"Controlling ID: {res['fk_controllingid']}")
    ctrl = DB.fetch_one("SELECT ControllingOfficer_Id, description FROM Sal_ControllingOffice_Mst WHERE pk_Controllid = ?", [res['fk_controllingid']])
    print(f"Controlling Officer Record: {ctrl}")
else:
    print("No controlling ID for ES-271")
