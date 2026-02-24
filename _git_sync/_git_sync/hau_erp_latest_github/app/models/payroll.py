from app.db import DB
from datetime import datetime

class PayrollModel:
    @staticmethod
    def get_salary_slip_data(emp_id, month, year):
        query = """
        SELECT S.*, E.empname, E.empcode, E.panno, D.designation, DEP.description as department,
        L.locname as campus, B.bankname, E.bankaccountno, E.gradepay,
        CONVERT(varchar, O.dateofbirth, 103) as dob_fmt,
        F.fundtype as scheme_name,
        G.gpfno as gpf_nps_no,
        M.descriptiion as month_name
        FROM SAL_Salary_Master S
        INNER JOIN SAL_Employee_Mst E ON S.fk_empid = E.pk_empid
        LEFT JOIN SAL_EmployeeOther_Details O ON E.pk_empid = O.fk_empid
        LEFT JOIN fundtype_master F ON S.fk_fundid = F.pk_fundid
        LEFT JOIN gpf_employee_details G ON E.pk_empid = G.fk_empid
        LEFT JOIN Month_Mst M ON S.fk_monthId = M.pk_MonthId
        LEFT JOIN SAL_Designation_Mst D ON E.fk_desgid = D.pk_desgid
        LEFT JOIN Department_Mst DEP ON E.fk_deptid = DEP.pk_deptid
        LEFT JOIN Location_Mst L ON E.fk_locid = L.pk_locid
        LEFT JOIN SAL_Bank_Mst B ON E.fk_bankid = B.pk_bankid
        WHERE S.fk_empid = ? AND S.fk_monthId = ? AND S.fk_yearId = ?
        """
        master = DB.fetch_one(query, [emp_id, month, year])
        if not master: return None
        earnings = DB.fetch_all("SELECT D.paid_amount, H.description as Description FROM SAL_SalaryHead_Details D INNER JOIN SAL_Head_Mst H ON D.fk_headid = H.pk_headid WHERE D.fk_salid = ? AND H.headtype = '1'", [master['pk_salid']])
        deductions = DB.fetch_all("SELECT D.paid_amount, H.description as Description FROM SAL_SalaryHead_Details D INNER JOIN SAL_Head_Mst H ON D.fk_headid = H.pk_headid WHERE D.fk_salid = ? AND H.headtype = '2'", [master['pk_salid']])
        loans = DB.fetch_all("SELECT L.InstalmentAmount, L.balAmount, H.description as Description FROM SAL_SalaryLoan_Details L INNER JOIN SAL_Head_Mst H ON L.fk_headid = H.pk_headid WHERE L.fk_salid = ?", [master['pk_salid']])
        return {'master': master, 'earnings': earnings, 'deductions': deductions, 'loans': loans, 'month_name': master.get('month_name', 'Month'), 'year': year, 'net_words': "Rs. " + str(master.get('NetPay', 0))}

    @staticmethod
    def get_it_certificate_data(emp_id, fin_id):
        # 1. Fetch Monthly Salaries
        salaries = DB.fetch_all("""
        SELECT S.*, S.fk_monthId as month_no, S.fk_yearId as year_no, S.GrossTotal as gross_total, S.ProfTax as pt,
        S.IT as it_paid,
        (SELECT ISNULL(SUM(paid_amount),0) FROM SAL_SalaryHead_Details WHERE fk_salid = S.pk_salid AND fk_headid = 1) as basic_pay,
        (SELECT ISNULL(SUM(paid_amount),0) FROM SAL_SalaryHead_Details WHERE fk_salid = S.pk_salid AND fk_headid = 3) as da,
        (SELECT ISNULL(SUM(paid_amount),0) FROM SAL_SalaryHead_Details WHERE fk_salid = S.pk_salid AND fk_headid = 4) as hra,
        (SELECT ISNULL(SUM(paid_amount),0) FROM SAL_SalaryHead_Details WHERE fk_salid = S.pk_salid AND fk_headid = 77) as fma,
        (SELECT ISNULL(SUM(paid_amount),0) FROM SAL_SalaryHead_Details WHERE fk_salid = S.pk_salid AND fk_headid = 89) as gpf_sub,
        (SELECT ISNULL(SUM(paid_amount),0) FROM SAL_SalaryHead_Details WHERE fk_salid = S.pk_salid AND fk_headid = 15) as gslis
        FROM SAL_Salary_Master S
        WHERE S.fk_empid = ? AND S.fk_finid = ?
        ORDER BY S.fk_yearId, S.fk_monthId
        """, [emp_id, fin_id])

        # 2. Fetch Arrears as separate rows (grouped by paid month)
        arrears = DB.fetch_all("""
        SELECT 
            'Arrear (' + M.descriptiion + '-' + CAST(A.fk_yearId as varchar) + ')' as period,
            0 as basic_pay,
            SUM(A.GrossTotal) as da,
            0 as hra,
            0 as fma,
            SUM(ISNULL(A.IT, 0)) as it_paid,
            SUM(ISNULL(A.ProfTax, 0)) as pt,
            0 as gpf_sub,
            0 as gslis,
            A.fk_monthId as month_no,
            A.fk_yearId as year_no,
            SUM(A.GrossTotal) as gross_total,
            1 as is_arrear
        FROM SAL_Employee_Arrear_Mst A
        LEFT JOIN Month_Mst M ON A.fk_monthId = M.pk_MonthId
        WHERE A.fk_empid = ? AND A.fk_finid = ?
        GROUP BY A.fk_monthId, A.fk_yearId, M.descriptiion
        """, [emp_id, fin_id])

        combined = salaries + arrears
        # Sort by year and month, then arrears come after salary if in same month
        combined.sort(key=lambda x: (x['year_no'], x['month_no'], x.get('is_arrear', 0)))
        
        return {'statement': combined} if combined else None

    @staticmethod
    def calculate_tax(taxable, slabs):
        tax = 0
        breakup = []
        for s in slabs:
            if taxable > s['LowerLimit']:
                amt = min(taxable, s['UpperLimit']) - s['LowerLimit']
                row_tax = amt * (float(s['Tax_Percent']) / 100.0)
                tax += row_tax
                breakup.append({'slab': f"{s['LowerLimit']}-{s['UpperLimit']}", 'rate': s['Tax_Percent'], 'tax': row_tax})
        return tax, breakup

    @staticmethod
    def save_rent_details(emp_id, fin_id, month_id, year, amount, user_id):
        exists = DB.fetch_one("SELECT pk_id FROM SAL_Employee_Rent_Details WHERE fk_empid=? AND fk_finid=? AND fk_monthid=?", [emp_id, fin_id, month_id])
        if exists:
            return DB.execute("UPDATE SAL_Employee_Rent_Details SET rentamount=?, fk_updUserID=?, fk_updDateID=GETDATE() WHERE pk_id=?", [amount, user_id, exists['pk_id']])
        else:
            return DB.execute("INSERT INTO SAL_Employee_Rent_Details (fk_empid, fk_finid, fk_monthid, year_no, rentamount, fk_insUserID, fk_insDateID) VALUES (?, ?, ?, ?, ?, ?, GETDATE())", [emp_id, fin_id, month_id, year, amount, user_id])

    @staticmethod
    def get_employee_rent_header(emp_id):
        return DB.fetch_one("SELECT E.empname, E.empcode, D.designation, DP.description as dept_name, E.panno, E.bankaccountno FROM SAL_Employee_Mst E LEFT JOIN SAL_Designation_Mst D ON E.fk_desgid = D.pk_desgid LEFT JOIN Department_Mst DP ON E.fk_deptid = DP.pk_deptid WHERE E.pk_empid = ?", [emp_id])

    @staticmethod
    def save_it_computation(data, emp_id, fin_id, user_id):
        DB.execute("DELETE FROM SAL_ITaxComputation_Mst WHERE fk_empid=? AND fk_finid=?", [emp_id, fin_id])
        sql = """
            INSERT INTO SAL_ITaxComputation_Mst 
            (fk_empid, fk_finid, drawnsalary, arrearsalary, duesalary, hraallownce, conallownce, 
             interest, otherincome, employmenttax, deductionunder6A, deductionunderother, 
             netgrossincome, tax, surchargeamt, cessamt, totaltax, paidtax, totaltaxpayret,
             fk_insUserID, fk_insDateID, fk_updUserID, fk_updDateID, dated) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE(), ?, GETDATE(), GETDATE())
        """
        params = [
            emp_id, fin_id, data.get('GrossSal', 0), 0, 0, 0, 0, 0, 0, 0, 0, 0,
            data.get('TotalTaxableIncome', 0), data.get('TotalTax', 0), 0, 0, data.get('TotalTax', 0), 0, 0,
            user_id, user_id
        ]
        return DB.execute(sql, params)

    @staticmethod
    def get_it_computation_data(emp_id, fin_id):
        return DB.fetch_one("SELECT * FROM SAL_ITaxComputation_Mst WHERE fk_empid = ? AND fk_finid = ?", [emp_id, fin_id])

    @staticmethod
    def get_form16_quarterly_summary(emp_id, fin_id):
        return []

    @staticmethod
    def get_form16_tds_details(emp_id, fin_id):
        return []

    @staticmethod
    def amount_to_words(amt):
        from app.utils import number_to_words
        return number_to_words(int(amt))