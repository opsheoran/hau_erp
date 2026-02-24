from app.db import DB
res = DB.fetch_all("SELECT pk_gradeid, gradename, gradedetails FROM SAL_Grade_Mst WHERE gradedetails LIKE '%2000%'")
print(f"Grades with 2000: {res}")
res = DB.fetch_all("SELECT pk_desgcat, description FROM SAL_DesignationCat_Mst WHERE description LIKE '%2000%'")
print(f"Categories with 2000: {res}")
