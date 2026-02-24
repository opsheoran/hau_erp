from app.db import DB

def debug():
    name = 'Godara'
    print(f"--- Debugging for {name} ---")
    
    # 1. Check Employee Master
    emp_query = """
        SELECT E.pk_empid, E.empname, DS.fk_desgcat, DS.designation
        FROM SAL_Employee_Mst E 
        INNER JOIN SAL_Designation_Mst DS ON E.fk_desgid = DS.pk_desgid 
        WHERE E.empname LIKE ?
    """
    employees = DB.fetch_all(emp_query, [f"%{name}%"])
    print(f"Employees found in SAL_Employee_Mst: {len(employees)}")
    for e in employees:
        print(f"  - {e['empname']} (ID: {e['pk_empid']}, Cat: {e['fk_desgcat']}, Desg: {e['designation']})")
        
        # 2. Check SAR Master for this specific employee
        sar_query = "SELECT pk_sarid, IsSubmit, FinalApproval FROM SAR_Employee_Mst WHERE fk_empid = ?"
        sar_records = DB.fetch_all(sar_query, [e['pk_empid']])
        print(f"    SAR records: {len(sar_records)}")
        for s in sar_records:
            print(f"      - SAR ID: {s['pk_sarid']}, IsSubmit: {s['IsSubmit']}, FinalApproval: {s['FinalApproval']}")

if __name__ == "__main__":
    debug()
