from app.db import DB

def check_agronomy():
    print("\n--- Searching 'Agronomy' ---")
    # In Department_Mst (Alphanumeric)
    dept1 = DB.fetch_one("SELECT pk_deptid, description FROM Department_Mst WHERE description = 'Agronomy'")
    print(f"Department_Mst: {dept1}")
    
    # In SMS_Dept_Mst (Numeric)
    dept2 = DB.fetch_one("SELECT pk_Deptid, Departmentname FROM SMS_Dept_Mst WHERE Departmentname LIKE '%Agronomy%'")
    print(f"SMS_Dept_Mst: {dept2}")

if __name__ == "__main__":
    check_agronomy()
