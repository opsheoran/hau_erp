from app.db import DB
from datetime import datetime

class LoanModel:
    @staticmethod
    def get_employee_loan_details(emp_id):
        query = """
        SELECT E.empcode, E.empname, D.Description as ddo_name, DP.description as dept_name,
        DS.designation, E.curbasic, E.gradepay, E.pfileno as pf_no
        FROM SAL_Employee_Mst E
        LEFT JOIN DDO_Mst D ON E.fk_ddoid = D.pk_ddoid
        LEFT JOIN Department_Mst DP ON E.fk_deptid = DP.pk_deptid
        LEFT JOIN SAL_Designation_Mst DS ON E.fk_desgid = DS.pk_desgid
        WHERE E.pk_empid = ?
        """
        return DB.fetch_one(query, [emp_id])

    @staticmethod
    def get_loan_types():
        return DB.fetch_all("SELECT pk_headid as id, description as name FROM SAL_Head_Mst WHERE description LIKE '%Loan%' OR description LIKE '%Advance%' ORDER BY description")

    @staticmethod
    def get_loan_natures():
        return DB.fetch_all("SELECT pk_lnatureid as id, loanNature as name FROM SAL_LoanNature_Mst ORDER BY loanNature")

    @staticmethod
    def get_loan_purposes():
        return DB.fetch_all("SELECT DISTINCT LoanPurpose as name FROM SAL_LoanPurpose_Mst ORDER BY LoanPurpose")

    @staticmethod
    def get_loan_history(emp_id, sql_limit=""):
        query = f"""
            SELECT A.pk_applyid, H.description as LoanType, N.loanNature, 
            CONVERT(varchar, A.dated, 103) as ApplyDate, A.amount
            FROM SAL_LoanApply_Mst A
            LEFT JOIN SAL_Head_Mst H ON A.fk_headid = H.pk_headid
            LEFT JOIN SAL_LoanNature_Mst N ON A.fk_lnatureid = N.pk_lnatureid
            WHERE A.fk_empid = ?
            {sql_limit}
        """
        # Note: sql_limit contains 'ORDER BY dated DESC OFFSET ...'
        return DB.fetch_all(query, [emp_id])

    @staticmethod
    def apply_loan(form, emp_id, user_id):
        date_id = datetime.now().strftime("%b %d %Y %H:")[:15]
        sql = """
            INSERT INTO SAL_LoanApply_Mst (
                fk_empid, fk_headid, fk_lnatureid, LoanPurpose, amount, 
                remarks, dated, fk_insUserID, fk_insDateID, fk_updUserID, fk_updDateID
            ) VALUES (?, ?, ?, ?, ?, ?, GETDATE(), ?, ?, ?, ?)
        """
        params = [emp_id, form['loan_type'], form['nature'], form['purpose'], form['amount'], form.get('remarks', ''), user_id, date_id, user_id, date_id]
        return DB.execute(sql, params)

    @staticmethod
    def delete_loan(apply_id, emp_id):
        return DB.execute("DELETE FROM SAL_LoanApply_Mst WHERE pk_applyid = ? AND fk_empid = ?", [apply_id, emp_id])

    @staticmethod
    def get_loan_application(apply_id):
        return DB.fetch_one("SELECT * FROM SAL_LoanApply_Mst WHERE pk_applyid = ?", [apply_id])

    @staticmethod
    def save_loan_application(data, user_id):
        sql = """
        INSERT INTO SAL_LoanApply_Mst (
            fk_empid, fk_loanid, loanamount, applicationdate, remarks, 
            issubmit, fk_insUserID, fk_insDateID, fk_updUserID, fk_updDateID
        ) VALUES (?, ?, ?, GETDATE(), ?, 'Y', ?, GETDATE(), ?, GETDATE())
        """
        return DB.execute(sql, [data['emp_id'], data['loan_id'], data['amount'], data['remarks'], user_id, user_id])

class EmployeeLoanModel:
    @staticmethod
    def get_employee_loans(emp_id):
        return DB.fetch_all("""
            SELECT pk_loanId as id, *, 
                   CONVERT(varchar, Date, 103) as date_fmt 
            FROM SAL_EmployeeLoan_Details WHERE fk_empid = ?
        """, [emp_id])

    @staticmethod
    def get_by_id(loan_id):
        return DB.fetch_one("""
            SELECT pk_loanId as id, *, 
                   CONVERT(varchar, Date, 103) as date_fmt,
                   CONVERT(varchar, Date, 23) as date_iso
            FROM SAL_EmployeeLoan_Details WHERE pk_loanId = ?
        """, [loan_id])

    @staticmethod
    def save(data, user_id):
        loan_id = data.get('loan_id')
        from datetime import datetime
        def parse_date(d):
            if not d: return None
            try: return datetime.strptime(d, '%d/%m/%Y').strftime('%Y-%m-%d')
            except: return None

        params = [
            data['emp_id'], parse_date(data.get('loan_date')), data.get('amount'),
            data.get('purpose'), data.get('type'), data.get('status')
        ]
        if loan_id:
            sql = """
                UPDATE SAL_EmployeeLoan_Details SET
                fk_empid = ?, Date = ?, Amount = ?, Purpose = ?, 
                Type = ?, Status = ?, UpdateDate = GETDATE()
                WHERE pk_loanId = ?
            """
            return DB.execute(sql, params + [loan_id])
        else:
            sql = """
                INSERT INTO SAL_EmployeeLoan_Details (
                    fk_empid, Date, Amount, Purpose, Type, Status, InsertDate
                ) VALUES (?, ?, ?, ?, ?, ?, GETDATE())
            """
            return DB.execute(sql, params)

    @staticmethod
    def delete(loan_id):
        return DB.execute("DELETE FROM SAL_EmployeeLoan_Details WHERE pk_loanId = ?", [loan_id])

class IncomeTaxModel:
    @staticmethod
    def get_sections():
        return DB.fetch_all("SELECT * FROM SAL_Sections_Mst WHERE active = 1 ORDER BY orderby")

    @staticmethod
    def get_subsections(sec_id):
        return DB.fetch_all("SELECT * FROM SAL_SubSections_Mst WHERE fk_secid = ? AND active = 1", [sec_id])

    @staticmethod
    def get_employee_declarations(emp_id, fin_id):
        query = """
            SELECT D.*, S.description as section_name 
            FROM SAL_Employee_SectionDocStatus D 
            INNER JOIN SAL_Sections_Mst S ON D.fk_secid = S.pk_secid 
            WHERE D.fk_empid = ? AND D.fk_finid = ?
        """
        return DB.fetch_all(query, [emp_id, fin_id])

    @staticmethod
    def save_declaration(decl_data, emp_id, fin_id, user_id):
        conn = DB.get_connection()
        cursor = conn.cursor()
        date_id = datetime.now().strftime("%b %d %Y %H:")[:15]
        try:
            # Delete existing for this year to overwrite
            cursor.execute("DELETE FROM SAL_Employee_SectionDocStatus WHERE fk_empid = ? AND fk_finid = ?", [emp_id, fin_id])
            
            for d in decl_data:
                sql = """
                    INSERT INTO SAL_Employee_SectionDocStatus (
                        fk_empid, fk_secid, fk_subsecid, docsub_Amt, fk_finid, 
                        fk_insUserID, fk_insDateID, fk_updUserID, fk_updDateID, submitdate
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE())
                """
                cursor.execute(sql, [emp_id, d['sec_id'], d['subsec_id'], d['amount'], fin_id, user_id, date_id, user_id, date_id])
            
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def get_it_declarations(emp_id, fin_id):
        return IncomeTaxModel.get_employee_declarations(emp_id, fin_id)

class EmployeePortalModel:
    @staticmethod
    def get_gpf_details(emp_id, fin_id=None):
        # 1. Fetch Header Info
        fy_where = "FY.active = 'Y'"
        if fin_id:
            fy_where = "FY.pk_finid = ?"
        
        header_sql = f"""
            SELECT E.empname, E.empcode, DS.designation, DP.description as department, 
            G.gpfno, G.PFType, FY.Lyear, FY.pk_finid, ISNULL(BM.OpningBalEmp, 0) as OpeningBalance
            FROM SAL_Employee_Mst E
            INNER JOIN gpf_employee_details G ON E.pk_empid = G.fk_empid
            LEFT JOIN SAL_Designation_Mst DS ON E.fk_desgid = DS.pk_desgid
            LEFT JOIN Department_Mst DP ON E.fk_deptid = DP.pk_deptid
            LEFT JOIN SAL_Financial_Year FY ON {fy_where}
            LEFT JOIN GPF_Balance_Mst BM ON E.pk_empid = BM.fk_empid AND BM.fk_finid = FY.pk_finid
            WHERE E.pk_empid = ?
        """
        header_params = [fin_id, emp_id] if fin_id else [emp_id]
        header = DB.fetch_one(header_sql, header_params)
        
        if not header: return None

        # 2. Fetch Month-wise Details
        month_names = {1: 'JANUARY', 2: 'FEBRUARY', 3: 'MARCH', 4: 'APRIL', 5: 'MAY', 6: 'JUNE', 
                       7: 'JULY', 8: 'AUGUST', 9: 'SEPTEMBER', 10: 'OCTOBER', 11: 'NOVEMBER', 12: 'DECEMBER'}
        
        details_sql = """
            SELECT D.*, F.Lyear
            FROM GPF_Balance_Details D
            INNER JOIN GPF_Balance_Mst M ON D.fk_balid = M.pk_balid
            LEFT JOIN SAL_Financial_Year F ON D.fk_finid = F.pk_finid
            WHERE M.fk_empid = ? AND F.pk_finid = ?
            ORDER BY D.fk_yearId, D.fk_monthId
        """
        details_raw = DB.fetch_all(details_sql, [emp_id, header['pk_finid']])
        
        grid = []
        for row in details_raw:
            grid.append({
                'month': month_names.get(row['fk_monthId'], 'N/A'),
                'op_bal': row['OpningBalEmp'],
                'sub': row['ContributionAmtEmp'],
                'opt': row['cpfoptional'],
                'recovery': row['RefundAmt'],
                'arrear': row['arrearemp'],
                'total': row['TotalAmtEmp'],
                'withdrawal': row['WithdrawllAmtEmp'],
                'interest': row['IntAmountEmp']
            })
            
        return {'header': header, 'grid': grid}

    @staticmethod
    def get_dashboard_counts(emp_id):
        return {
            'pending_leaves': DB.fetch_scalar("SELECT COUNT(*) FROM SAL_Leave_Request_Mst WHERE fk_reqempid = ? AND leavestatus = 'S'", [emp_id]),
            'approved_leaves': DB.fetch_scalar("SELECT COUNT(*) FROM SAL_Leave_Request_Mst WHERE fk_reqempid = ? AND leavestatus = 'A'", [emp_id]),
            'total_loans': DB.fetch_scalar("SELECT COUNT(*) FROM SAL_LoanApply_Mst WHERE fk_empid = ?", [emp_id])
        }
    
    @staticmethod
    def get_full_profile(empid):
        basic = DB.fetch_one("""
        SELECT E.*, O.*, DS.designation, DP.description as department, N.nature as nature_type,
        B.bankname as bank, CITY.cityname as posting_city,
        LOC.locname as actual_location_name, PLOC.locname as posting_location_name,
        DDO.Description as actual_ddo_name, PDDO.Description as posting_ddo_name,
        CONVERT(varchar, O.dateofbirth, 103) as dob_fmt,
        CONVERT(varchar, O.dateofjoining, 103) as doj_fmt,
        CONVERT(varchar, O.dateofretirement, 103) as dor_fmt,
        (SELECT TOP 1 filename FROM SAL_EmployeeDocument_Details WHERE fk_empid = E.pk_empid AND fk_doccatid = 1) as photo,
        CTRL.description as ctrl_name, PCTRL.description as posted_ctrl_name,
        P_DEPT.description as posted_dept_name
        FROM SAL_Employee_Mst E
        LEFT JOIN SAL_EmployeeOther_Details O ON E.pk_empid = O.fk_empid
        LEFT JOIN SAL_Designation_Mst DS ON E.fk_desgid = DS.pk_desgid
        LEFT JOIN Department_Mst DP ON E.fk_deptid = DP.pk_deptid
        LEFT JOIN SAL_Nature_Mst N ON E.fk_natureid = N.pk_natureid
        LEFT JOIN SAL_Bank_Mst B ON E.fk_bankid = B.pk_bankid
        LEFT JOIN SAL_City_Mst CITY ON E.fk_cityid = CITY.pk_cityid
        LEFT JOIN Location_Mst LOC ON E.fk_locid = LOC.pk_locid
        LEFT JOIN Location_Mst PLOC ON E.postinglocation = PLOC.pk_locid
        LEFT JOIN DDO_Mst DDO ON E.fk_ddoid = DDO.pk_ddoid
        LEFT JOIN DDO_Mst PDDO ON E.postingddo = PDDO.pk_ddoid
        LEFT JOIN Sal_ControllingOffice_Mst CTRL ON E.fk_controllingid = CTRL.pk_Controllid
        LEFT JOIN Sal_ControllingOffice_Mst PCTRL ON E.fk_postedcontrollingid = PCTRL.pk_Controllid
        LEFT JOIN Department_Mst P_DEPT ON E.fk_Pdeptid = P_DEPT.pk_deptid
        WHERE E.pk_empid = ?
        """, [empid])
        family = DB.fetch_all("""
        SELECT F.*, R.Relation_name, CONVERT(varchar, F.dob, 103) as dob_fmt
        FROM SAL_EmployeeFamily_Details F
        LEFT JOIN Relation_MST R ON F.fk_relid = R.Pk_Relid
        WHERE F.fk_empid = ?
        """, [empid])
        quals = DB.fetch_all("SELECT * FROM SAL_EmployeeQualification_Details WHERE fk_empid = ?", [empid])
        loans = DB.fetch_all("""
        SELECT H.description as loan_type, SL.lamount, SL.balAmount, SL.noOfInstalments, SL.InstalmentAmount, SL.leftInstalments
        FROM SAL_SalaryLoan_Details SL
        INNER JOIN SAL_Salary_Master SM ON SL.fk_salid = SM.pk_salid
        INNER JOIN SAL_Head_Mst H ON SL.fk_headid = H.pk_headid
        WHERE SM.fk_empid = ? AND SM.pk_salid = (SELECT TOP 1 pk_salid FROM SAL_Salary_Master WHERE fk_empid=? ORDER BY fk_yearId DESC, fk_monthId DESC)
        """, [empid, empid])
        prev_jobs = DB.fetch_all("SELECT *, CONVERT(varchar, fromdate, 103) as from_fmt, CONVERT(varchar, todate, 103) as to_fmt FROM SAL_EmployeePreviousJob_Details WHERE fk_empid = ?", [empid])
        nominees = DB.fetch_all("SELECT * FROM SAL_Salary_Nominee WHERE fk_empid = ?", [empid])
        return {
            'basic': basic,
            'family': family,
            'qualifications': quals,
            'loans': loans,
            'previous_jobs': prev_jobs,
            'nominees': nominees
        }

class EmployeeModel:
    @staticmethod
    def get_employee_full_details(emp_id):
        query = """
        SELECT E.*, O.*, D.Description as ddo_name, DP.description as dept_name, DS.designation as desg_name,
               LOC.locname as location_name,
               GPF.gpfno, 
               GPF.PFType as pftype_code,
               CASE WHEN GPF.PFType = 'G' THEN 'GPF' WHEN GPF.PFType = 'C' THEN 'CPF' WHEN GPF.PFType = 'P' THEN 'NPS' ELSE GPF.PFType END as pftype_desc,
               BAL.ClosingBal as gpf_balance,
               LD.InstalmentAmount as gpf_adv_inst,
               SAL.IT as income_tax,
               SHARE.SharePerc as gpf_share_pct,
               CONVERT(varchar, O.dateofbirth, 23) as dob_fmt,
               CONVERT(varchar, O.dateofappointment, 23) as doa_fmt,
               CONVERT(varchar, O.dateofjoining, 23) as doj_fmt,
               CONVERT(varchar, O.dateOfConfirmation, 23) as doc_fmt,
               COALESCE(CONVERT(varchar, O.dateofretirement, 23), CONVERT(varchar, BM.Retirement, 23)) as dor_fmt,
               CONVERT(varchar, O.dateoflastappointment, 23) as last_doa_fmt,
               CONVERT(varchar, O.dateoflastjoining, 23) as last_doj_fmt,
               CONVERT(varchar, E.incdate, 23) as inc_date_fmt,
               CONVERT(varchar, E.leftdate, 23) as left_date_fmt,
               CONVERT(varchar, O.QuarterEffecDate, 23) as qtr_eff_date_fmt,
               CONVERT(varchar, FMA.EffectiveDate, 23) as med_eff_date_fmt
        FROM SAL_Employee_Mst E
        LEFT JOIN SAL_EmployeeOther_Details O ON E.pk_empid = O.fk_empid
        LEFT JOIN DDO_Mst D ON E.fk_ddoid = D.pk_ddoid
        LEFT JOIN Department_Mst DP ON E.fk_deptid = DP.pk_deptid
        LEFT JOIN SAL_Designation_Mst DS ON E.fk_desgid = DS.pk_desgid
        LEFT JOIN Location_Mst LOC ON E.fk_locid = LOC.pk_locid
        LEFT JOIN (SELECT fk_empid, EffectiveDate, ROW_NUMBER() OVER(PARTITION BY fk_empid ORDER BY EffectiveDate DESC) as rn FROM SAL_FMAeffective_Trn) FMA ON E.pk_empid = FMA.fk_empid AND FMA.rn = 1
        LEFT JOIN gpf_employee_details GPF ON E.pk_empid = GPF.fk_empid
        LEFT JOIN (SELECT fk_empid, ClosingBal, ROW_NUMBER() OVER(PARTITION BY fk_empid ORDER BY fk_finid DESC) as rn FROM GPF_Balance_Mst) BAL ON E.pk_empid = BAL.fk_empid AND BAL.rn = 1
        LEFT JOIN (SELECT M.fk_empid, D.InstalmentAmount, ROW_NUMBER() OVER(PARTITION BY M.fk_empid ORDER BY M.ldated DESC) as rn 
                   FROM SAL_LoanTransaction_Mst M 
                   JOIN SAL_LoanTransaction_Details D ON M.pk_lid = D.fk_lid 
                   WHERE M.fk_headid = 27 AND D.balAmount > 0) LD ON E.pk_empid = LD.fk_empid AND LD.rn = 1
        LEFT JOIN (SELECT fk_empid, IT, ROW_NUMBER() OVER(PARTITION BY fk_empid ORDER BY fk_yearId DESC, fk_monthId DESC) as rn FROM SAL_Salary_Master) SAL ON E.pk_empid = SAL.fk_empid AND SAL.rn = 1
        LEFT JOIN (SELECT fk_empid, Retirement, ROW_NUMBER() OVER(PARTITION BY fk_empid ORDER BY pk_GADetail DESC) as rn FROM BMS_BM10_Details) BM ON E.pk_empid = BM.fk_empid AND BM.rn = 1
        LEFT JOIN (SELECT fk_empid, SharePerc, ROW_NUMBER() OVER(PARTITION BY fk_empid ORDER BY InsDate DESC) as rn FROM Employee_GPF_Optional_Share) SHARE ON E.pk_empid = SHARE.fk_empid AND SHARE.rn = 1
        WHERE E.pk_empid = ?
        """
        record = DB.fetch_one(query, [emp_id])
        if not record:
            return None

        def fmt_iso(value):
            if value is None or value == '':
                return None
            try:
                from datetime import datetime, date
                if isinstance(value, (datetime, date)):
                    return value.strftime('%Y-%m-%d')
            except Exception:
                pass

            s = str(value).strip()
            if not s:
                return None
            for fmt in ('%Y-%m-%d', '%Y/%m/%d', '%d/%m/%Y', '%d-%m-%Y'):
                try:
                    from datetime import datetime
                    return datetime.strptime(s[:10], fmt).strftime('%Y-%m-%d')
                except Exception:
                    continue
            return s[:10]

        def pick_col(cols, candidates):
            for c in candidates:
                if c in cols:
                    return c
            return None

        # Prefer latest record from SAL_FirstAppointment_Details if those columns exist in this DB.
        try:
            fa_cols = set(DB.get_table_columns('SAL_FirstAppointment_Details'))
        except Exception:
            fa_cols = set()

        appointment_date_col = pick_col(fa_cols, ['AppointmentDate', 'DateofAppointment', 'dateofappointment'])
        joining_date_col = pick_col(fa_cols, ['JoiningDate', 'DateofJoining', 'DateofJoinning', 'dateofjoining'])
        order_no_col = pick_col(fa_cols, ['OrderNo', 'OrderNO', 'Order_No', 'OrderNumber', 'OrderNo1'])
        has_fk_empid = 'fk_empid' in fa_cols

        if has_fk_empid and (appointment_date_col or joining_date_col or order_no_col):
            select_cols = []
            for c in [appointment_date_col, joining_date_col, order_no_col]:
                if c:
                    safe = c.replace(']', ']]')
                    select_cols.append(f'[{safe}]')
            try:
                fa = DB.fetch_one(
                    f"""
                    SELECT TOP 1 {', '.join(select_cols)}
                    FROM SAL_FirstAppointment_Details
                    WHERE fk_empid = ?
                    ORDER BY pk_appointmentid DESC
                    """,
                    [emp_id],
                )
            except Exception:
                fa = None

            if fa:
                if order_no_col and fa.get(order_no_col) not in (None, ''):
                    record['first_order_no'] = fa.get(order_no_col)
                if appointment_date_col and fa.get(appointment_date_col) not in (None, ''):
                    record['doa_fmt'] = fmt_iso(fa.get(appointment_date_col))
                if joining_date_col and fa.get(joining_date_col) not in (None, ''):
                    record['doj_fmt'] = fmt_iso(fa.get(joining_date_col))

        # Fallback for order number if we couldn't find it in SAL_FirstAppointment_Details.
        if record.get('first_order_no') in (None, ''):
            for k in ('OrderNo', 'orderno', 'order_no'):
                if record.get(k) not in (None, ''):
                    record['first_order_no'] = record.get(k)
                    break

        return record

    @staticmethod
    def get_all_ddos():
        return DB.fetch_all("SELECT pk_ddoid as id, Description as name FROM DDO_Mst ORDER BY Description")

    @staticmethod
    def get_all_departments():
        return DB.fetch_all("SELECT pk_deptid as id, description as name FROM Department_Mst ORDER BY description")

    @staticmethod
    def get_all_designations():
        return DB.fetch_all("SELECT pk_desgid as id, designation as name FROM SAL_Designation_Mst ORDER BY designation")

    @staticmethod
    def get_current_month_year():
        from datetime import datetime
        now = datetime.now()
        return now.month, now.year

    @staticmethod
    def get_lookups():
        return {
            'salutations': DB.fetch_all("SELECT PK_Salutation_ID as id, Salutation_Name as name FROM SAL_Salutation_Mst ORDER BY name"),
            'categories': DB.fetch_all("SELECT pk_catid as id, category as name FROM SAL_Category_Mst ORDER BY category"),
            'banks': DB.fetch_all("SELECT pk_bankid as id, bankname as name FROM SAL_Bank_Mst ORDER BY bankname"),
            'cities': DB.fetch_all("SELECT pk_cityid as id, cityname as name FROM SAL_City_Mst ORDER BY cityname"),
            'departments': DB.fetch_all("SELECT pk_deptid as id, description as name FROM Department_Mst ORDER BY description"),
            'designations': DB.fetch_all("SELECT pk_desgid as id, designation as name FROM SAL_Designation_Mst ORDER BY designation"),
            'controlling': DB.fetch_all("SELECT pk_Controllid as id, description as name FROM Sal_ControllingOffice_Mst ORDER BY description"),
            'religions': DB.fetch_all("SELECT pk_religionid as id, religiontype as name FROM Religion_Mst ORDER BY religiontype"),
            'maritals': DB.fetch_all("SELECT PK_MS_ID as id, Marital_Status as name FROM GIS_Marital_Status_Mst ORDER BY Marital_Status"),
            'natures': DB.fetch_all("SELECT pk_natureid as id, nature as name FROM SAL_Nature_Mst ORDER BY nature"),
            'sections': DB.fetch_all("SELECT pk_sectionid as id, description as name FROM SAL_Section_Mst ORDER BY description"),
            'locations': DB.fetch_all("SELECT pk_locid as id, locname as name FROM Location_Mst ORDER BY locname"),
            'ddos': DB.fetch_all("SELECT pk_ddoid as id, Description as name FROM DDO_Mst ORDER BY Description"),
            'employees': DB.fetch_all("""
                SELECT E.pk_empid as id,
                E.empname + ' | ' + E.empcode + ' | ' + ISNULL(D.designation, '') as name
                FROM SAL_Employee_Mst E
                LEFT JOIN SAL_Designation_Mst D ON E.fk_desgid = D.pk_desgid
                WHERE E.employeeleftstatus = 'N'
                ORDER BY E.empname
            """)
        }

    @staticmethod
    def get_full_lookups():
        return {
            'salutations': DB.fetch_all("SELECT PK_Salutation_ID as id, Salutation_Name as name FROM SAL_Salutation_Mst ORDER BY Salutation_Name"),
            'categories': DB.fetch_all("SELECT pk_catid as id, category as name FROM SAL_Category_Mst ORDER BY category"),
            'religions': DB.fetch_all("SELECT pk_religionid as id, religiontype as name FROM Religion_Mst ORDER BY religiontype"),
            'banks': DB.fetch_all("SELECT pk_bankid as id, bankname as name FROM SAL_Bank_Mst ORDER BY bankname"),
            'nature_types': DB.fetch_all("SELECT pk_natureid as id, nature as name FROM SAL_Nature_Mst ORDER BY nature"),
            'fund_types': DB.fetch_all("SELECT pk_fundid as id, fundtype as name FROM fundtype_master ORDER BY fundtype"),
            'locations': DB.fetch_all("SELECT pk_locid as id, locname as name FROM Location_Mst ORDER BY locname"),
            'controlling_offices': DB.fetch_all("SELECT pk_Controllid as id, description as name FROM Sal_ControllingOffice_Mst ORDER BY description"),
            'ddos': DB.fetch_all("SELECT pk_ddoid as id, Description as name FROM DDO_Mst ORDER BY Description"),
            'departments': DB.fetch_all("SELECT pk_deptid as id, description as name FROM Department_Mst ORDER BY description"),
            'sections': DB.fetch_all("SELECT pk_sectionid as id, description as name FROM SAL_Section_Mst ORDER BY description"),
            'designations': DB.fetch_all("SELECT pk_desgid as id, designation as name FROM SAL_Designation_Mst ORDER BY designation"),
            'cities': DB.fetch_all("SELECT pk_cityid as id, cityname as name FROM SAL_City_Mst ORDER BY cityname"),
            'schemes': DB.fetch_all("SELECT pk_anc as id, Headcode + ' | ' + HeadDescription as name FROM Acct_HeadCode WHERE Active = 1 ORDER BY HeadDescription"),
            'scheme_groups': DB.fetch_all("SELECT Pk_SchemeGroupId as id, SchemeGroupName as name FROM BMS_SchemeGroup_Mst ORDER BY SchemeGroupName"),
            'disciplines': DB.fetch_all("SELECT pk_disid as id, discipline as name FROM SAL_Discipline_Mst ORDER BY discipline"),
            'specializations': DB.fetch_all("SELECT Pk_BranchId as id, Branchname as name FROM SMS_BranchMst ORDER BY Branchname"),
            'grades': DB.fetch_all("SELECT pk_gradeid as id, gradedetails + '---(' + CAST(CAST(ISNULL(gradepay, 0) AS INT) AS VARCHAR) + ')' as name FROM SAL_Grade_Mst ORDER BY gradedetails"),
            'salary_types': DB.fetch_all("SELECT pk_saltypeid as id, saltype as name FROM SAL_SalaryType_Mst ORDER BY orderby"),
            'associations': DB.fetch_all("SELECT Pk_ESP_Id as id, Description as name FROM PA_Education_Specialization_Mst ORDER BY Description"),
            'quarters': DB.fetch_all("SELECT pk_quarterid as id, quarterno as name FROM SAL_Quarter_Mst ORDER BY quarterno"),
            'genders': DB.fetch_all("SELECT gender as id, (CASE WHEN gender = 'M' THEN 'Male' WHEN gender = 'F' THEN 'Female' ELSE gender END) as name FROM SMS_gender_mst ORDER BY gender"),
            'marital_statuses': DB.fetch_all("SELECT PK_MS_ID as id, Marital_Status as name FROM GIS_Marital_Status_Mst ORDER BY Marital_Status"),
            'employees': DB.fetch_all("""
                SELECT E.pk_empid as id,
                E.empname + ' | ' + E.empcode + ' | ' + ISNULL(D.designation, '') as name
                FROM SAL_Employee_Mst E
                LEFT JOIN SAL_Designation_Mst D ON E.fk_desgid = D.pk_desgid
                WHERE E.employeeleftstatus = 'N'
                ORDER BY E.empname
            """)
        }

    @staticmethod
    def save_demographic_details(data, user_id):
        # Update SAL_Employee_Mst
        mst_sql = """
            UPDATE SAL_Employee_Mst 
            SET email = ?, fk_updUserID = ?, fk_updDateID = GETDATE()
            WHERE pk_empid = ?
        """
        DB.execute(mst_sql, [data.get('official_email'), user_id, data['emp_id']])

        # Check if record exists in SAL_EmployeeOther_Details
        existing = DB.fetch_one("SELECT fk_empid FROM SAL_EmployeeOther_Details WHERE fk_empid = ?", [data['emp_id']])
        
        from datetime import datetime
        def parse_date(d):
            if not d: return None
            try: return datetime.strptime(d, '%d/%m/%Y').strftime('%Y-%m-%d')
            except: return None

        other_data = {
            'fk_quarterid': data.get('quarter_id'),
            'joininglocation': data.get('joining_location'),
            'fk_desgid_j': data.get('joining_desg_id'),
            'fk_religionid': data.get('religion_id'),
            'gender': data.get('gender'),
            'fk_catid': data.get('category_id'),
            'mothername': data.get('mother_name'),
            'dateofappointment': parse_date(data.get('doa')),
            'dateofjoining': parse_date(data.get('doj')),
            'dateOfConfirmation': parse_date(data.get('doc')),
            'dateofretirement': parse_date(data.get('dor')),
            'corresContactNo': data.get('contact1'),
            'permanentContactNo': data.get('contact2'),
            'econtactnum': data.get('mobile'),
            'PersonalEmail': data.get('personal_email'),
            'voteridnumber': data.get('voter_id'),
            'uidnumber': data.get('uid_no'),
            'technicalQualifications': data.get('tech_qualification'),
            'height': data.get('height'),
            'scholarships': data.get('scholarship'),
            'IdentificationMarks': data.get('identification_mark'),
            'remarks': data.get('remarks'),
            'reference': data.get('reference'),
            'txtHusbWifeName': data.get('spouse_name'),
            'fk_updUserID': user_id,
            'fk_empid': data['emp_id']
        }

        if existing:
            update_sql = """
                UPDATE SAL_EmployeeOther_Details SET
                fk_quarterid = ?, joininglocation = ?, fk_desgid_j = ?, fk_religionid = ?,
                gender = ?, fk_catid = ?, mothername = ?, dateofappointment = ?,
                dateofjoining = ?, dateOfConfirmation = ?, dateofretirement = ?,
                corresContactNo = ?, permanentContactNo = ?, econtactnum = ?,
                PersonalEmail = ?, voteridnumber = ?, uidnumber = ?,
                technicalQualifications = ?, height = ?, scholarships = ?,
                IdentificationMarks = ?, remarks = ?, reference = ?,
                txtHusbWifeName = ?, fk_updUserID = ?, fk_updDateID = GETDATE()
                WHERE fk_empid = ?
            """
            return DB.execute(update_sql, list(other_data.values())[:-1] + [data['emp_id']])
        else:
            insert_sql = """
                INSERT INTO SAL_EmployeeOther_Details (
                    fk_quarterid, joininglocation, fk_desgid_j, fk_religionid,
                    gender, fk_catid, mothername, dateofappointment,
                    dateofjoining, dateOfConfirmation, dateofretirement,
                    corresContactNo, permanentContactNo, econtactnum,
                    PersonalEmail, voteridnumber, uidnumber,
                    technicalQualifications, height, scholarships,
                    IdentificationMarks, remarks, reference,
                    txtHusbWifeName, fk_updUserID, fk_empid, fk_updDateID
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE())
            """
            return DB.execute(insert_sql, list(other_data.values()))

    @staticmethod
    def save_employee(data, user_id):
        emp_id = data.get('edit_id')
        
        # Mapping form fields to DB columns
        mst_fields = {
            'fk_salutation_id': data.get('salutation_id'),
            'empname': data.get('empname'),
            'manualempcode': data.get('manualcode'),
            'fathername': data.get('fathername'),
            'idcard': data.get('idcard'),
            'email': data.get('email'),
            'panno': data.get('panno'),
            'AadhaarNo': data.get('aadhaar'),
            'ecrno': data.get('ecrno'),
            'ecrpageno': data.get('ecrpage'),
            'LibraryCardNo': data.get('library_card'),
            'remarks': data.get('remarks'),
            'bankaccountno': data.get('account_no'),
            'fk_bankid': data.get('bank_id'),
            'paymode': data.get('pay_mode'),
            'fk_controllingid': data.get('ctrl_id'),
            'fk_postedcontrollingid': data.get('posted_ctrl_id'),
            'fk_ddoid': data.get('ddo_id'),
            'postingddo': data.get('posted_ddo_id'),
            'fk_locid': data.get('loc_id'),
            'postinglocation': data.get('posted_loc_id'),
            'fk_deptid': data.get('dept_id'),
            'fk_Pdeptid': data.get('posted_dept_id'),
            'fk_sectionid': data.get('section_id'),
            'fk_postedsectionid': data.get('posted_section_id'),
            'fk_natureid': data.get('nature_id'),
            'fk_fundid': data.get('fund_id'),
            'fk_anc': data.get('scheme_id'),
            'reportingto': data.get('reporting_to'),
            'incdate': data.get('inc_due_date'),
            'mbfno': data.get('welfare_no'),
            'pfileno': data.get('pf_no'),
            'pgteachercode': data.get('pg_teacher_code'),
            'sipremno': data.get('si_prem_no'),
            'fK_Asso_ID': data.get('asso_id'),
            'addcharge': data.get('add_charge'),
            'typeofallowance': data.get('med_type'),
            'fk_saltypeid': data.get('sal_type_id'),
            'fk_desgid': data.get('desg_id'),
            'fk_pdesgid': data.get('posted_desg_id'),
            'fK_DesignspecId': data.get('spec_id'),
            'fK_PDesignspecId': data.get('posted_spec_id'),
            'fk_gradeid': data.get('grade_id'),
            'fk_cgradeid': data.get('curr_grade_id'),
            'level_type': data.get('level_type'),
            'level_name': data.get('level_number'),
            'cell_number': data.get('cell_number'),
            'gradepay': data.get('grade_pay'),
            'cgradepay': data.get('curr_grade_pay'),
            'fk_pid': data.get('pf_type_id'),
            'fk_quarterid': data.get('quarter_id'),
            'curbasic': data.get('basic'),
            'fk_updUserID': user_id,
            'fk_updDateID': 'GETDATE()'
        }

        if emp_id:
            # Update SAL_Employee_Mst
            update_parts = []
            params = []
            for col, val in mst_fields.items():
                if col == 'fk_updDateID':
                    update_parts.append(f"{col} = GETDATE()")
                else:
                    update_parts.append(f"{col} = ?")
                    params.append(val)
            
            sql = f"UPDATE SAL_Employee_Mst SET {', '.join(update_parts)} WHERE pk_empid = ?"
            params.append(emp_id)
            DB.execute(sql, params)
            
            # Update/Insert into SAL_EmployeeOther_Details
            other_fields = {
                'gender': data.get('gender'),
                'fk_catid': data.get('cat_id'),
                'fk_religionid': data.get('rel_id'),
                'martialstatus': data.get('marital_id'),
                'dob': data.get('dob'),
                'dateofappointment': data.get('doa'),
                'dateofjoining': data.get('doj'),
                'fk_disid': data.get('dis_id'),
                'dateofretirement': data.get('dor'),
                'employeeleftstatus': data.get('left_status'),
                'leftreason': data.get('left_reason'),
                'leftdate': data.get('left_date'),
                'leftremarks': data.get('left_remarks'),
                'fk_updUserID': user_id,
                'fk_updDateID': 'GETDATE()'
            }
            
            # Use specific table for other details if applicable, but usually some fields are in Mst and some in Other.
            # In HAU schema, many demographic fields are in Other.
            
        else:
            # Insert logic...
            pass

    @staticmethod
    def _build_employee_detailed_where(filters):
        where = " WHERE 1=1 " 
        params = []

        if filters.get('empcode'):
            where += " AND E.empcode LIKE ? " 
            params.append(f"%{filters['empcode']}%")
        if filters.get('manual_empcode'):
            where += " AND E.manualempcode LIKE ? " 
            params.append(f"%{filters['manual_empcode']}%")
        if filters.get('empname'):
            where += " AND E.empname LIKE ? " 
            params.append(f"%{filters['empname']}%")
        if filters.get('dept_id'):
            where += " AND E.fk_deptid = ? " 
            params.append(filters['dept_id'])
        if filters.get('desg_id'):
            where += " AND E.fk_desgid = ? " 
            params.append(filters['desg_id'])
        if filters.get('ctrl_id'):
            where += " AND E.fk_controllingid = ? " 
            params.append(filters['ctrl_id'])
        if filters.get('loc_id'):
            where += " AND E.fk_locid = ? " 
            params.append(filters['loc_id'])
        if filters.get('ddo_id'):
            where += " AND E.fk_ddoid = ? " 
            params.append(filters['ddo_id'])
        if filters.get('nature_id'):
            where += " AND E.fk_natureid = ? " 
            params.append(filters['nature_id'])
        if filters.get('section_id'):
            where += " AND E.fk_sectionid = ? " 
            params.append(filters['section_id'])
        if filters.get('fund_id'):
            where += " AND E.fk_fundid = ? " 
            params.append(filters['fund_id'])
        if filters.get('city_id'):
            where += " AND E.fk_cityid = ? " 
            params.append(filters['city_id'])
        if filters.get('scheme_group'):
            where += " AND E.fk_SubGroupId = ? " 
            params.append(filters['scheme_group'])
        if filters.get('scheme_id'):
            where += " AND E.fk_anc = ? " 
            params.append(filters['scheme_id'])
        if filters.get('med_type'):
            where += " AND E.typeofallowance = ? " 
            params.append(filters['med_type'])

        status = (filters.get('status') or 'A').strip()
        if status == 'T':
            where += " AND E.transferstatus = 'T' " 
        elif status == 'S':
            where += " AND E.suspended = 1 " 

        return where, params

    @staticmethod
    def count_employees_detailed(filters):
        where, params = EmployeeModel._build_employee_detailed_where(filters)
        return DB.fetch_scalar(f"SELECT COUNT(*) FROM SAL_Employee_Mst E {where}", params) or 0

    @staticmethod
    def search_employees_detailed(filters, sql_limit=""):
        where, params = EmployeeModel._build_employee_detailed_where(filters)

        sort_col = filters.get('sort_by', 'manualempcode')
        # Validate sort_col to prevent injection (though it's from a dropdown)
        valid_sorts = ['manualempcode', 'empname', 'fk_locid', 'fk_deptid', 'fk_desgid', 'fk_natureid', 'fk_cityid']
        if sort_col not in valid_sorts:
            sort_col = 'manualempcode'

        query = f"""
            SELECT E.pk_empid as id, E.empcode, E.manualempcode, E.empname, 
                   C.description as ctrl_name, D.description as dept_name, 
                   DS.designation, PD.description as posted_dept_name
            FROM SAL_Employee_Mst E
            LEFT JOIN Sal_ControllingOffice_Mst C ON E.fk_controllingid = C.pk_Controllid
            LEFT JOIN Department_Mst D ON E.fk_deptid = D.pk_deptid
            LEFT JOIN SAL_Designation_Mst DS ON E.fk_desgid = DS.pk_desgid
            LEFT JOIN Department_Mst PD ON E.fk_Pdeptid = PD.pk_deptid
            {where}
            ORDER BY E.{sort_col}
            {sql_limit}
        """
        return DB.fetch_all(query, params)
    @staticmethod
    def search_employees(term):
        query = """
            SELECT E.pk_empid as id, 
                   E.empname + ' | ' + E.empcode + ' | ' + ISNULL(D.designation, '') as name
            FROM SAL_Employee_Mst E
            LEFT JOIN SAL_Designation_Mst D ON E.fk_desgid = D.pk_desgid
            WHERE E.employeeleftstatus = 'N' 
            AND (E.empname LIKE ? OR E.empcode LIKE ?)
            ORDER BY E.empname
        """
        return DB.fetch_all(query, [f'%{term}%', f'%{term}%'])

class DesignationCategoryModel:
    @staticmethod
    def get_all():
        return DB.fetch_all("SELECT pk_desgcat as id, description as name FROM SAL_DesignationCat_Mst ORDER BY description")

class EmployeeDocumentModel:
    @staticmethod
    def get_employee_documents(emp_id):
        query = """
            SELECT pk_empdocid as id, D.*, C.description as category_name,
                   CASE WHEN D.isactive = 1 THEN 'YES' ELSE 'NO' END as isactive_text
            FROM SAL_EmployeeDocument_Details D
            LEFT JOIN SAL_EmployeeDocumentCategory_Mst C ON D.fk_doccatid = C.pk_doccatid
            WHERE D.fk_empid = ?
        """
        return DB.fetch_all(query, [emp_id])

    @staticmethod
    def get_by_id(doc_id):
        return DB.fetch_one("SELECT pk_empdocid as id, * FROM SAL_EmployeeDocument_Details WHERE pk_empdocid = ?", [doc_id])

    @staticmethod
    def get_categories():
        return DB.fetch_all("SELECT pk_doccatid as id, description as name FROM SAL_EmployeeDocumentCategory_Mst ORDER BY description")

    @staticmethod
    def save(data, user_id):
        doc_id = data.get('doc_id')
        if doc_id:
            sql = """
                UPDATE SAL_EmployeeDocument_Details 
                SET fk_doccatid = ?, filename = ISNULL(?, filename), att_designation = ?, 
                    fk_updUserID = ?, fk_updDateID = GETDATE()
                WHERE pk_empdocid = ?
            """
            return DB.execute(sql, [data['cat_id'], data.get('filename'), data.get('att_desig'), user_id, doc_id])
        else:
            sql = """
                INSERT INTO SAL_EmployeeDocument_Details 
                (fk_empid, fk_doccatid, filename, att_designation, isactive, fk_insUserID, fk_insDateID, fk_updUserID, fk_updDateID)
                VALUES (?, ?, ?, ?, 1, ?, GETDATE(), ?, GETDATE())
            """
            return DB.execute(sql, [data['emp_id'], data['cat_id'], data['filename'], data.get('att_desig'), user_id, user_id])

    @staticmethod
    def delete(doc_id):
        return DB.execute("DELETE FROM SAL_EmployeeDocument_Details WHERE pk_empdocid = ?", [doc_id])

class EmployeeQualificationModel:
    @staticmethod
    def get_employee_qualifications(emp_id):
        return DB.fetch_all("SELECT pk_qualiid as id, fk_finid as passing_year, * FROM SAL_EmployeeQualification_Details WHERE fk_empid = ?", [emp_id])

    @staticmethod
    def get_by_id(quali_id):
        return DB.fetch_one("SELECT pk_qualiid as id, fk_finid as passing_year, * FROM SAL_EmployeeQualification_Details WHERE pk_qualiid = ?", [quali_id])

    @staticmethod
    def save(data, user_id):
        quali_id = data.get('quali_id')
        params = [
            data['emp_id'], data.get('passing_year'), data.get('exam_passed'),
            data.get('university'), data.get('subject'), data.get('institution'),
            data.get('roll_no'), data.get('marks_obtained'), data.get('percentage'),
            1 if data.get('in_service') else 0,
            1 if data.get('is_technical') else 0,
            data.get('filename'), user_id
        ]
        if quali_id:
            sql = """
                UPDATE SAL_EmployeeQualification_Details SET
                fk_empid = ?, fk_finid = ?, exampassed = ?, examiningbody = ?, 
                subject = ?, specilization = ?, division = ?, marksobtained = ?, 
                percentage = ?, inservice = ?, istechnical = ?, 
                filename = ISNULL(?, filename), fk_updUserID = ?, fk_updDateID = GETDATE()
                WHERE pk_qualiid = ?
            """
            return DB.execute(sql, params + [quali_id])
        else:
            sql = """
                INSERT INTO SAL_EmployeeQualification_Details (
                    fk_empid, fk_finid, exampassed, examiningbody, 
                    subject, specilization, division, marksobtained, 
                    percentage, inservice, istechnical, filename, 
                    fk_insUserID, fk_insDateID, fk_updUserID, fk_updDateID
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE(), ?, GETDATE())
            """
            return DB.execute(sql, params + [user_id])

    @staticmethod
    def delete(quali_id):
        return DB.execute("DELETE FROM SAL_EmployeeQualification_Details WHERE pk_qualiid = ?", [quali_id])

class EmployeePermissionModel:
    @staticmethod
    def get_employee_permissions(emp_id):
        return DB.fetch_all("""
            SELECT pk_Eduid as id, *, CONVERT(varchar, OrderDate, 103) as order_date_fmt 
            FROM SAL_EmployeeEducation_Details WHERE fk_empid = ?
        """, [emp_id])

    @staticmethod
    def get_by_id(edu_id):
        return DB.fetch_one("""
            SELECT pk_Eduid as id, *, CONVERT(varchar, OrderDate, 103) as order_date_fmt,
                   CONVERT(varchar, OrderDate, 23) as order_date_iso
            FROM SAL_EmployeeEducation_Details WHERE pk_Eduid = ?
        """, [edu_id])

    @staticmethod
    def save(data, user_id):
        edu_id = data.get('edu_id')
        params = [
            data['emp_id'], data.get('admission_year'), data.get('order_no'),
            data.get('school'), data.get('order_date'), data.get('exam_name'),
            data.get('filename'), user_id
        ]
        if edu_id:
            sql = """
                UPDATE SAL_EmployeeEducation_Details SET
                fk_empid = ?, admissionyear = ?, orderno = ?, School_Institute = ?, 
                OrderDate = ?, Name_Of_Exam = ?, filename = ISNULL(?, filename), 
                fk_updUserID = ?, fk_updDateID = GETDATE()
                WHERE pk_Eduid = ?
            """
            return DB.execute(sql, params + [edu_id])
        else:
            sql = """
                INSERT INTO SAL_EmployeeEducation_Details (
                    fk_empid, admissionyear, orderno, School_Institute, 
                    OrderDate, Name_Of_Exam, filename, 
                    fk_insUserID, fk_insDateID, fk_updUserID, fk_updDateID
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, GETDATE(), ?, GETDATE())
            """
            return DB.execute(sql, params)

    @staticmethod
    def delete(edu_id):
        return DB.execute("DELETE FROM SAL_EmployeeEducation_Details WHERE pk_Eduid = ?", [edu_id])

class EmployeeFamilyModel:
    @staticmethod
    def get_employee_family(emp_id):
        return DB.fetch_all("""
            SELECT F.pk_familyid as id, F.*, R.Relation_name as relation_name,
                   CONVERT(varchar, F.dob, 103) as dob_fmt
            FROM SAL_EmployeeFamily_Details F
            LEFT JOIN Relation_MST R ON F.fk_relid = R.Pk_Relid
            WHERE F.fk_empid = ?
        """, [emp_id])

    @staticmethod
    def get_by_id(family_id):
        return DB.fetch_one("""
            SELECT pk_familyid as id, *, CONVERT(varchar, dob, 103) as dob_fmt,
                   CONVERT(varchar, dob, 23) as dob_iso
            FROM SAL_EmployeeFamily_Details WHERE pk_familyid = ?
        """, [family_id])

    @staticmethod
    def save(data, user_id):
        family_id = data.get('family_id')
        params = [
            data['emp_id'], data.get('member_name'), data.get('rel_id'),
            data.get('dob'), data.get('aadhaar'), data.get('remarks'),
            data.get('filename'), user_id
        ]
        if family_id:
            sql = """
                UPDATE SAL_EmployeeFamily_Details SET
                fk_empid = ?, membername = ?, fk_relid = ?, dob = ?, 
                AadhaarNo = ?, Remarks = ?, filename = ISNULL(?, filename), 
                fk_updUserID = ?, fk_updDateID = GETDATE()
                WHERE pk_familyid = ?
            """
            return DB.execute(sql, params + [family_id])
        else:
            sql = """
                INSERT INTO SAL_EmployeeFamily_Details (
                    fk_empid, membername, fk_relid, dob, AadhaarNo, Remarks, filename, 
                    fk_insUserID, fk_insDateID, fk_updUserID, fk_updDateID
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, GETDATE(), ?, GETDATE())
            """
            return DB.execute(sql, params)

    @staticmethod
    def delete(family_id):
        return DB.execute("DELETE FROM SAL_EmployeeFamily_Details WHERE pk_familyid = ?", [family_id])

class EmployeeNomineeModel:
    @staticmethod
    def get_employee_nominees(emp_id):
        query = """
            SELECT N.*, R.Relation_name as relation_name, H.description as nominee_type_name
            FROM GPF_EmployeeNominee_Details N
            LEFT JOIN Relation_MST R ON N.relationship = R.Pk_Relid
            LEFT JOIN SAL_Head_Mst H ON N.fk_headid = H.pk_headid
            WHERE N.fk_empid = ?
        """
        return DB.fetch_all(query, [emp_id])

    @staticmethod
    def get_by_name(emp_id, nominee_name):
        return DB.fetch_one("SELECT * FROM GPF_EmployeeNominee_Details WHERE fk_empid = ? AND nameofnominee = ?", [emp_id, nominee_name])

    @staticmethod
    def save(data, user_id):
        old_name = data.get('old_nominee_name')
        params = [
            data['emp_id'], data.get('nominee_name'), data.get('rel_id'),
            data.get('age'), data.get('share'), 1 if data.get('is_minor') else 0,
            data.get('other_details'), 1 if data.get('is_primary') else 0,
            data.get('nominee_type_id'), data.get('remarks'), data.get('filename'),
            user_id
        ]
        if old_name:
            sql = """
                UPDATE GPF_EmployeeNominee_Details SET
                fk_empid = ?, nameofnominee = ?, relationship = ?, age = ?, 
                share = ?, IsMinor = ?, otherdetails = ?, isprimary = ?, 
                fk_headid = ?, remarks = ?, filename = ISNULL(?, filename), 
                fk_updUserID = ?, fk_updDateID = GETDATE()
                WHERE fk_empid = ? AND nameofnominee = ?
            """
            return DB.execute(sql, params + [data['emp_id'], old_name])
        else:
            sql = """
                INSERT INTO GPF_EmployeeNominee_Details (
                    fk_empid, nameofnominee, relationship, age, 
                    share, IsMinor, otherdetails, isprimary, 
                    fk_headid, remarks, filename, 
                    fk_updUserID, fk_updDateID
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE())
            """
            return DB.execute(sql, params)

    @staticmethod
    def delete(emp_id, nominee_name):
        return DB.execute("DELETE FROM GPF_EmployeeNominee_Details WHERE fk_empid = ? AND nameofnominee = ?", [emp_id, nominee_name])

class EmployeeBookModel:
    @staticmethod
    def get_employee_books(emp_id):
        return DB.fetch_all("""
            SELECT pk_issueid as id, *, 
                   CONVERT(varchar, issuedate, 103) as issue_date_fmt,
                   CONVERT(varchar, returndate, 103) as return_date_fmt
            FROM SAL_EmployeeMemo_Details WHERE fk_empid = ?
        """, [emp_id])

    @staticmethod
    def get_by_id(issue_id):
        return DB.fetch_one("""
            SELECT pk_issueid as id, *, 
                   CONVERT(varchar, issuedate, 23) as issue_date_iso,
                   CONVERT(varchar, returndate, 23) as return_date_iso
            FROM SAL_EmployeeMemo_Details WHERE pk_issueid = ?
        """, [issue_id])

    @staticmethod
    def save(data, user_id):
        issue_id = data.get('issue_id')
        params = [
            data['emp_id'], data.get('memo_no'), data.get('issue_date'),
            data.get('return_date'), data.get('authority'), data.get('subject'),
            data.get('remarks'), data.get('filename'), user_id
        ]
        if issue_id:
            sql = """
                UPDATE SAL_EmployeeMemo_Details SET
                fk_empid = ?, memono = ?, issuedate = ?, returndate = ?, 
                issueauthority = ?, subject = ?, remarks = ?, 
                filename = ISNULL(?, filename), fk_updUserID = ?, fk_updDateID = GETDATE()
                WHERE pk_issueid = ?
            """
            return DB.execute(sql, params + [issue_id])
        else:
            sql = """
                INSERT INTO SAL_EmployeeMemo_Details (
                    fk_empid, memono, issuedate, returndate, 
                    issueauthority, subject, remarks, filename, 
                    fk_insUserID, fk_insDateID, fk_updUserID, fk_updDateID
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE(), ?, GETDATE())
            """
            return DB.execute(sql, params)

    @staticmethod
    def delete(issue_id):
        return DB.execute("DELETE FROM SAL_EmployeeMemo_Details WHERE pk_issueid = ?", [issue_id])

class LTCModel:
    @staticmethod
    def get_employee_ltc(emp_id):
        return DB.fetch_all("""
            SELECT pk_ltcid as id, fromdate as blockyear, todate as ltc_date_fmt,
                   PaidAmount as totalamount, remarks
            FROM SAL_LTC_Detail WHERE fk_empid = ?
            ORDER BY pk_ltcid DESC
        """, [emp_id])

    @staticmethod
    def get_by_id(ltc_id):
        return DB.fetch_one("SELECT pk_ltcid as id, * FROM SAL_LTC_Detail WHERE pk_ltcid = ?", [ltc_id])

    @staticmethod
    def save(data, user_id):
        ltc_id = data.get('ltc_id')
        params = [
            data['emp_id'], data.get('block_year'), data.get('ltc_date'),
            data.get('amount'), data.get('remarks'), user_id
        ]
        if ltc_id:
            sql = """
                UPDATE SAL_LTC_Detail SET
                fk_empid = ?, fromdate = ?, todate = ?, PaidAmount = ?, 
                remarks = ?, fk_updUserID = ?, fk_updDateID = GETDATE()
                WHERE pk_ltcid = ?
            """
            return DB.execute(sql, params + [ltc_id])
        else:
            sql = """
                INSERT INTO SAL_LTC_Detail (
                    fk_empid, fromdate, todate, PaidAmount, remarks, 
                    fk_insUserID, fk_insDateID, fk_updUserID, fk_updDateID
                ) VALUES (?, ?, ?, ?, ?, ?, GETDATE(), ?, GETDATE())
            """
            return DB.execute(sql, params + [user_id])

    @staticmethod
    def delete(ltc_id):
        return DB.execute("DELETE FROM SAL_LTC_Detail WHERE pk_ltcid = ?", [ltc_id])

class PreviousJobModel:
    @staticmethod
    def get_employee_previous_jobs(emp_id):
        return DB.fetch_all("""
            SELECT pk_pjobid as id, *, 
                   CONVERT(varchar, fromdate, 103) as from_date_fmt,
                   CONVERT(varchar, todate, 103) as to_date_fmt
            FROM SAL_EmployeePreviousJob_Details WHERE fk_empid = ?
        """, [emp_id])

    @staticmethod
    def get_by_id(job_id):
        return DB.fetch_one("""
            SELECT pk_pjobid as id, *, 
                   CONVERT(varchar, fromdate, 103) as from_date_fmt,
                   CONVERT(varchar, todate, 103) as to_date_fmt
            FROM SAL_EmployeePreviousJob_Details WHERE pk_pjobid = ?
        """, [job_id])

    @staticmethod
    def save(data, user_id):
        job_id = data.get('job_id')
        from datetime import datetime
        def parse_date(d):
            if not d: return None
            try: return datetime.strptime(d, '%d/%m/%Y').strftime('%Y-%m-%d')
            except: return None

        params = [
            data['emp_id'], data.get('station'), data.get('p_desg'),
            data.get('p_grade'), parse_date(data.get('from_date')), 
            parse_date(data.get('to_date')),
            data.get('basic_pay'), data.get('gp'), data.get('da'),
            data.get('reason'), 1 if data.get('in_service') else 0,
            data.get('p_location'), data.get('p_dept'),
            data.get('carrier'), data.get('ca_pf'), user_id
        ]
        if job_id:
            sql = """
                UPDATE SAL_EmployeePreviousJob_Details SET
                fk_empid = ?, location = ?, desg = ?, grade = ?, 
                fromdate = ?, todate = ?, basicpay = ?, dp = ?, 
                da = ?, reasonsforLeavingJob = ?, inservice = ?, 
                plocation = ?, pdepartment = ?, Carrier_Advancement = ?, 
                CA_PF = ?, fk_updUserID = ?, fk_updDateID = GETDATE()
                WHERE pk_pjobid = ?
            """
            return DB.execute(sql, params + [job_id])
        else:
            sql = """
                INSERT INTO SAL_EmployeePreviousJob_Details (
                    fk_empid, location, desg, grade, fromdate, todate, 
                    basicpay, dp, da, reasonsforLeavingJob, inservice, 
                    plocation, pdepartment, Carrier_Advancement, CA_PF, 
                    fk_insUserID, fk_insDateID, fk_updUserID, fk_updDateID
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE(), ?, GETDATE())
            """
            return DB.execute(sql, params + [user_id])

    @staticmethod
    def delete(job_id):
        return DB.execute("DELETE FROM SAL_EmployeePreviousJob_Details WHERE pk_pjobid = ?", [job_id])

class ForeignVisitModel:
    @staticmethod
    def get_employee_foreign_visits(emp_id):
        return DB.fetch_all("""
            SELECT V.pk_visitid as id, V.*, S.FName as sponsor_name,
                   CONVERT(varchar, V.fromdate, 103) as from_date_fmt,
                   CONVERT(varchar, V.todate, 103) as to_date_fmt
            FROM SAL_EmployeeForeignVisit_Details V
            LEFT JOIN SAL_FundSponsor_Mst S ON V.FK_FSponsor_Id = S.PK_FSponsor_Id
            WHERE V.fk_empid = ?
        """, [emp_id])

    @staticmethod
    def get_by_id(visit_id):
        return DB.fetch_one("""
            SELECT pk_visitid as id, *, 
                   CONVERT(varchar, fromdate, 103) as from_date_fmt,
                   CONVERT(varchar, todate, 103) as to_date_fmt
            FROM SAL_EmployeeForeignVisit_Details WHERE pk_visitid = ?
        """, [visit_id])

    @staticmethod
    def save(data, user_id):
        visit_id = data.get('visit_id')
        from datetime import datetime
        def parse_date(d):
            if not d: return None
            try: return datetime.strptime(d, '%d/%m/%Y').strftime('%Y-%m-%d')
            except: return None

        params = [
            data['emp_id'], data.get('description'), data.get('location'),
            parse_date(data.get('from_date')), parse_date(data.get('to_date')),
            data.get('remarks'), data.get('sponsor_id'), user_id
        ]
        if visit_id:
            sql = """
                UPDATE SAL_EmployeeForeignVisit_Details SET
                fk_empid = ?, description = ?, location = ?, fromdate = ?, 
                todate = ?, fvisitremarks = ?, FK_FSponsor_Id = ?, 
                fk_updUserID = ?, fk_updDateID = GETDATE()
                WHERE pk_visitid = ?
            """
            return DB.execute(sql, params + [visit_id])
        else:
            sql = """
                INSERT INTO SAL_EmployeeForeignVisit_Details (
                    fk_empid, description, location, fromdate, todate, 
                    fvisitremarks, FK_FSponsor_Id, 
                    fk_insUserID, fk_insDateID, fk_updUserID, fk_updDateID
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, GETDATE(), ?, GETDATE())
            """
            return DB.execute(sql, params + [user_id])

    @staticmethod
    def delete(visit_id):
        return DB.execute("DELETE FROM SAL_EmployeeForeignVisit_Details WHERE pk_visitid = ?", [visit_id])

class TrainingModel:
    @staticmethod
    def get_employee_trainings(emp_id):
        return DB.fetch_all("""
            SELECT T.pk_trainingid as id, T.*, S.FName as sponsor_name,
                   CONVERT(varchar, T.fromdate, 103) as from_date_fmt,
                   CONVERT(varchar, T.todate, 103) as to_date_fmt
            FROM SAL_EmployeeTraining_Details T
            LEFT JOIN SAL_FundSponsor_Mst S ON T.FK_FSponsor_Id = S.PK_FSponsor_Id
            WHERE T.fk_empid = ?
        """, [emp_id])

    @staticmethod
    def get_by_id(training_id):
        return DB.fetch_one("""
            SELECT pk_trainingid as id, *, 
                   CONVERT(varchar, fromdate, 103) as from_date_fmt,
                   CONVERT(varchar, todate, 103) as to_date_fmt
            FROM SAL_EmployeeTraining_Details WHERE pk_trainingid = ?
        """, [training_id])

    @staticmethod
    def save(data, user_id):
        training_id = data.get('training_id')
        from datetime import datetime
        def parse_date(d):
            if not d: return None
            try: return datetime.strptime(d, '%d/%m/%Y').strftime('%Y-%m-%d')
            except: return None

        params = [
            data['emp_id'], data.get('description'), data.get('venue'),
            parse_date(data.get('from_date')), parse_date(data.get('to_date')),
            data.get('org_details'), data.get('remarks'), data.get('sponsor_id'),
            data.get('training_type'), user_id
        ]
        if training_id:
            sql = """
                UPDATE SAL_EmployeeTraining_Details SET
                fk_empid = ?, description = ?, venue = ?, fromdate = ?, 
                todate = ?, torganizationdtl = ?, remarks = ?, 
                FK_FSponsor_Id = ?, TrainingType = ?, 
                fk_updUserID = ?, fk_updDateID = GETDATE()
                WHERE pk_trainingid = ?
            """
            return DB.execute(sql, params + [training_id])
        else:
            sql = """
                INSERT INTO SAL_EmployeeTraining_Details (
                    fk_empid, description, venue, fromdate, todate, 
                    torganizationdtl, remarks, FK_FSponsor_Id, TrainingType,
                    fk_insUserID, fk_insDateID, fk_updUserID, fk_updDateID
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE(), ?, GETDATE())
            """
            return DB.execute(sql, params)

    @staticmethod
    def delete(training_id):
        return DB.execute("DELETE FROM SAL_EmployeeTraining_Details WHERE pk_trainingid = ?", [training_id])

class DeptExamModel:
    @staticmethod
    def get_employee_exams(emp_id):
        return DB.fetch_all("""
            SELECT E.pk_deptexamid as id, E.*, ET.ExamType as type_name
            FROM SAL_EmployeeDepartmentalExam_Details E
            LEFT JOIN SAL_ExamType_Mst ET ON E.FK_EType_Id = ET.Pk_EType_Id
            WHERE E.fk_empid = ?
        """, [emp_id])

    @staticmethod
    def get_by_id(exam_id):
        return DB.fetch_one("SELECT pk_deptexamid as id, * FROM SAL_EmployeeDepartmentalExam_Details WHERE pk_deptexamid = ?", [exam_id])

    @staticmethod
    def save(data, user_id):
        exam_id = data.get('exam_id')
        params = [
            data['emp_id'], data.get('examname'), data.get('rollno'),
            data.get('subject'), data.get('passingyear'), data.get('remarks'),
            data.get('type_id'), data.get('orderno'), data.get('status'), user_id
        ]
        if exam_id:
            sql = """
                UPDATE SAL_EmployeeDepartmentalExam_Details SET
                fk_empid = ?, examname = ?, rollno = ?, subject = ?, 
                passingyear = ?, remarks = ?, FK_EType_Id = ?, 
                OrderNo = ?, Status = ?, fk_updUserID = ?, fk_updDateID = GETDATE()
                WHERE pk_deptexamid = ?
            """
            return DB.execute(sql, params + [exam_id])
        else:
            sql = """
                INSERT INTO SAL_EmployeeDepartmentalExam_Details (
                    fk_empid, examname, rollno, subject, passingyear, 
                    remarks, FK_EType_Id, OrderNo, Status,
                    fk_insUserID, fk_insDateID, fk_updUserID, fk_updDateID
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE(), ?, GETDATE())
            """
            return DB.execute(sql, params)

    @staticmethod
    def delete(exam_id):
        return DB.execute("DELETE FROM SAL_EmployeeDepartmentalExam_Details WHERE pk_deptexamid = ?", [exam_id])

class ServiceVerificationModel:
    @staticmethod
    def get_employee_service_verifications(emp_id):
        return DB.fetch_all("""
            SELECT V.pk_verificationid as id, V.*, N.nature as nature_name,
                   CONVERT(varchar, V.datefrom, 103) as from_date_fmt,
                   CONVERT(varchar, V.dateto, 103) as to_date_fmt
            FROM SAL_EmployeeServiceVerification_Details V
            LEFT JOIN SAL_Nature_Mst N ON V.fk_natureid = N.pk_natureid
            WHERE V.fk_empid = ?
        """, [emp_id])

    @staticmethod
    def get_by_id(ver_id):
        return DB.fetch_one("""
            SELECT pk_verificationid as id, *, 
                   CONVERT(varchar, datefrom, 103) as from_date_fmt,
                   CONVERT(varchar, dateto, 103) as to_date_fmt
            FROM SAL_EmployeeServiceVerification_Details WHERE pk_verificationid = ?
        """, [ver_id])

    @staticmethod
    def save(data, user_id):
        ver_id = data.get('ver_id')
        from datetime import datetime
        def parse_date(d):
            if not d: return None
            try: return datetime.strptime(d, '%d/%m/%Y').strftime('%Y-%m-%d')
            except: return None

        params = [
            data['emp_id'], parse_date(data.get('from_date')), 
            parse_date(data.get('to_date')), data.get('payscale'),
            data.get('nature_id'), data.get('allowances'), data.get('remarks'),
            user_id
        ]
        if ver_id:
            sql = """
                UPDATE SAL_EmployeeServiceVerification_Details SET
                fk_empid = ?, datefrom = ?, dateto = ?, payscalewithoffice = ?, 
                fk_natureid = ?, allowances = ?, remarks = ?, 
                fk_updUserID = ?, fk_updDateID = GETDATE()
                WHERE pk_verificationid = ?
            """
            return DB.execute(sql, params + [ver_id])
        else:
            sql = """
                INSERT INTO SAL_EmployeeServiceVerification_Details (
                    fk_empid, datefrom, dateto, payscalewithoffice, 
                    fk_natureid, allowances, remarks, 
                    fk_insUserID, fk_insDateID, fk_updUserID, fk_updDateID
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, GETDATE(), ?, GETDATE())
            """
            return DB.execute(sql, params)

    @staticmethod
    def delete(ver_id):
        return DB.execute("DELETE FROM SAL_EmployeeServiceVerification_Details WHERE pk_verificationid = ?", [ver_id])

class SARModel:
    @staticmethod
    def get_sar_lists(category='T', fin_id=None, dept_id=None):
        cat_map = {'T': 1, 'N': 2, 'F': 3}
        cat_id = cat_map.get(category, 1)

        where = " WHERE S.fk_categoryid = ? "
        params = [cat_id]
        if fin_id:
            where += " AND S.fk_finid = ? "
            params.append(fin_id)
        if dept_id:
            where += " AND E.fk_deptid = ? "
            params.append(dept_id)

        base_query = '''
            SELECT S.pk_sarid, E.empname, D.description as dept_name,
                   CONVERT(varchar, O.dateofjoining, 103) as doj_fmt,
                   S.basicpay as basic, S.gradepay as gp
            FROM SAR_Employee_Mst S
            INNER JOIN SAL_Employee_Mst E ON S.fk_empid = E.pk_empid
            LEFT JOIN Department_Mst D ON E.fk_deptid = D.pk_deptid
            LEFT JOIN SAL_EmployeeOther_Details O ON E.pk_empid = O.fk_empid
        '''

        to_report = DB.fetch_all(base_query + where + " AND ISNULL(S.IsSubmit, 'N') <> 'Y' ORDER BY E.empname", params)
        to_forward = DB.fetch_all(base_query + where + " AND S.IsSubmit = 'Y' AND ISNULL(S.FinalApproval, 0) = 0 ORDER BY E.empname", params)
        submitted = DB.fetch_all(base_query + where + " AND ISNULL(S.FinalApproval, 0) = 1 ORDER BY E.empname", params)
        return {'to_report': to_report, 'to_forward': to_forward, 'to_accept': to_forward, 'submitted': submitted}
    @staticmethod
    def get_sar_details(sar_id):
        query_main = """
            SELECT S.*, E.empname, DS.designation, D.description as dept_name,
                   CONVERT(varchar, O.dateofjoining, 103) as hau_doj_fmt,
                   CONVERT(varchar, S.JoiningPostDate, 103) as present_doj_fmt
            FROM SAR_Employee_Mst S
            INNER JOIN SAL_Employee_Mst E ON S.fk_empid = E.pk_empid
            INNER JOIN SAL_Designation_Mst DS ON E.fk_desgid = DS.pk_desgid
            LEFT JOIN Department_Mst D ON E.fk_deptid = D.pk_deptid
            LEFT JOIN SAL_EmployeeOther_Details O ON E.pk_empid = O.fk_empid
            WHERE S.pk_sarid = ?
        """
        main = DB.fetch_one(query_main, [sar_id])
        if not main: return None
        publications = DB.fetch_all("SELECT description FROM SAR_Employee_Publication WHERE fk_sarid = ? ORDER BY sno", [sar_id])
        activities = DB.fetch_all("SELECT Activity, description, description1 FROM SAR_Employee_Activity WHERE fk_sarid = ? ORDER BY orderby", [sar_id])
        return {'main': main, 'publications': publications, 'activities': activities}

class FirstAppointmentModel:
    @staticmethod
    def _table_cols():
        try:
            return set(DB.get_table_columns('SAL_FirstAppointment_Details'))
        except Exception:
            return set()

    @staticmethod
    def _pick_col(cols, candidates):
        for c in candidates:
            if c in cols:
                return c
        return None

    @staticmethod
    def _fmt_date(value):
        if value is None or value == '':
            return None
        try:
            from datetime import datetime, date
            if isinstance(value, (datetime, date)):
                return value.strftime('%d/%m/%Y')
        except Exception:
            pass

        s = str(value).strip()
        if not s:
            return None
        for fmt in ('%d/%m/%Y', '%Y-%m-%d', '%Y/%m/%d', '%d-%m-%Y'):
            try:
                from datetime import datetime
                return datetime.strptime(s[:10], fmt).strftime('%d/%m/%Y')
            except Exception:
                continue
        return s

    @staticmethod
    def get_employee_appointments(emp_id):
        cols = FirstAppointmentModel._table_cols()
        join_col = FirstAppointmentModel._pick_col(
            cols,
            ['JoiningDate', 'DateofJoining', 'DateofJoinning', 'dateofjoining'],
        )
        order_col = FirstAppointmentModel._pick_col(
            cols,
            ['OrderNo', 'OrderNO', 'Order_No', 'OrderNumber', 'orderno'],
        )
        select_parts = ["pk_appointmentid as id", "title"]
        if order_col:
            safe_col = order_col.replace(']', ']]')
            select_parts.append(f"[{safe_col}] as OrderNo")
        else:
            select_parts.append("NULL as OrderNo")
        if join_col:
            safe_col = join_col.replace(']', ']]')
            select_parts.append(f"[{safe_col}] as _joining_date_raw")
        query = f"""
            SELECT {', '.join(select_parts)}
            FROM SAL_FirstAppointment_Details
            WHERE fk_empid = ?
            ORDER BY pk_appointmentid DESC
        """
        rows = DB.fetch_all(query, [emp_id])
        for r in rows:
            raw = r.pop('_joining_date_raw', None)
            r['joining_date_fmt'] = FirstAppointmentModel._fmt_date(raw)
        return rows

    @staticmethod
    def get_appointment_by_id(app_id):
        record = DB.fetch_one(
            "SELECT * FROM SAL_FirstAppointment_Details WHERE pk_appointmentid = ?",
            [app_id],
        )
        if not record:
            return None

        def first_present(candidates):
            for c in candidates:
                if c in record and record.get(c) not in (None, ''):
                    return record.get(c)
            return None

        record.setdefault(
            'joining_date_fmt',
            FirstAppointmentModel._fmt_date(
                first_present(['JoiningDate', 'DateofJoining', 'DateofJoinning', 'dateofjoining'])
            ),
        )
        record.setdefault(
            'OrderNo',
            first_present(['OrderNo', 'OrderNO', 'Order_No', 'OrderNumber', 'orderno']),
        )
        record.setdefault(
            'appointment_date_fmt',
            FirstAppointmentModel._fmt_date(
                first_present(['AppointmentDate', 'DateofAppointment', 'dateofappointment'])
            ),
        )
        record.setdefault(
            'probation_date_fmt',
            FirstAppointmentModel._fmt_date(
                first_present(['ProbationDate', 'ProbationCompleted', 'Prob_CompDate'])
            ),
        )
        record.setdefault(
            'due_date_pp_fmt',
            FirstAppointmentModel._fmt_date(first_present(['DueDatePP'])),
        )
        return record

    @staticmethod
    def get_probation_terms(app_id):
        return DB.fetch_all("SELECT * FROM SAL_FirstAppointment_Description_Details WHERE fk_appointmentid = ?", [app_id])

    @staticmethod
    def save(data, user_id):
        prefix = 'EST'
        if data.get('emp_id') and '-' in data['emp_id']:
            prefix = data['emp_id'].split('-')[0]
        res = DB.fetch_all("SELECT pk_appointmentid FROM SAL_FirstAppointment_Details WHERE pk_appointmentid LIKE ? + '-%'", [prefix])
        max_num = 0
        for r in res:
            try:
                num = int(r['pk_appointmentid'].split('-')[1])
                if num > max_num: max_num = num
            except: continue
        new_id = f"{prefix}-{max_num + 1}"
        
        from datetime import datetime
        def parse_date(d):
            if not d: return None
            try: return datetime.strptime(d, '%d/%m/%Y').strftime('%Y-%m-%d')
            except: return None

        sql = """
            INSERT INTO SAL_FirstAppointment_Details (
                pk_appointmentid, fk_empid, title, remarks, JoiningDate, OrderNo, 
                AppointmentDate, DDO, Designation, Department, BasicPay, PayScale, 
                ProbationDate, DueDatePP, JoiningTime, SrNo,
                fk_insUserID, fk_insDateID, fk_updUserID, fk_updDateID
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE(), ?, GETDATE())
        """
        DB.execute(sql, [
            new_id, data['emp_id'], data.get('title'), data.get('remarks'),
            parse_date(data.get('joining_date')), data.get('order_no'), 
            parse_date(data.get('appointment_date')),
            data.get('ddo'), data.get('designation'), data.get('department'),
            data.get('basic'), data.get('pay_scale'), 
            parse_date(data.get('probation_date')),
            parse_date(data.get('due_date_pp')), 
            data.get('joining_time'), data.get('sr_no'),
            user_id, user_id
        ])
        return new_id

    @staticmethod
    def update(app_id, data, user_id):
        from datetime import datetime
        def parse_date(d):
            if not d: return None
            try: return datetime.strptime(d, '%d/%m/%Y').strftime('%Y-%m-%d')
            except: return None

        sql = """
            UPDATE SAL_FirstAppointment_Details
            SET title = ?, remarks = ?, JoiningDate = ?, OrderNo = ?,
                AppointmentDate = ?, DDO = ?, Designation = ?, Department = ?, 
                BasicPay = ?, PayScale = ?, ProbationDate = ?, DueDatePP = ?,
                JoiningTime = ?, SrNo = ?, fk_updUserID = ?, fk_updDateID = GETDATE()
            WHERE pk_appointmentid = ?
        """
        DB.execute(sql, [
            data.get('title'), data.get('remarks'),
            parse_date(data.get('joining_date')), data.get('order_no'), 
            parse_date(data.get('appointment_date')),
            data.get('ddo'), data.get('designation'), data.get('department'),
            data.get('basic'), data.get('pay_scale'), 
            parse_date(data.get('probation_date')),
            parse_date(data.get('due_date_pp')), 
            data.get('joining_time'), data.get('sr_no'),
            user_id, app_id
        ])
        return app_id

    @staticmethod
    def save_probation_terms(app_id, terms, fulfills):
        DB.execute("DELETE FROM SAL_FirstAppointment_Description_Details WHERE fk_appointmentid = ?", [app_id])
        for term, fulfill in zip(terms, fulfills):
            if term.strip():
                DB.execute("INSERT INTO SAL_FirstAppointment_Description_Details (description, description2, fk_appointmentid) VALUES (?, ?, ?)",
                          [term.strip(), fulfill.strip(), app_id])

    @staticmethod
    def delete(app_id):
        DB.execute("DELETE FROM SAL_FirstAppointment_Description_Details WHERE fk_appointmentid = ?", [app_id])
        return DB.execute("DELETE FROM SAL_FirstAppointment_Details WHERE pk_appointmentid = ?", [app_id])

class IncrementModel:
    @staticmethod
    def get_employee_increments(emp_id, promo_type='I'):
        return DB.fetch_all("""
            SELECT pk_pid as id, *, 
                   CONVERT(varchar, dated, 103) as dated_fmt 
            FROM SAL_EmpPromotion_Details 
            WHERE fk_empid = ? AND ptstatus = ? 
            ORDER BY dated DESC
        """, [emp_id, promo_type])

    @staticmethod
    def get_by_id(pid):
        return DB.fetch_one("""
            SELECT pk_pid as id, *, 
                   CONVERT(varchar, dated, 103) as dated_fmt,
                   CONVERT(varchar, dated, 23) as dated_iso,
                   CONVERT(varchar, dateofreporting, 23) as order_date_iso
            FROM SAL_EmpPromotion_Details WHERE pk_pid = ?
        """, [pid])

    @staticmethod
    def save(data, user_id):
        pid = data.get('pid')
        from datetime import datetime
        def parse_date(d):
            if not d: return None
            try: return datetime.strptime(d, '%d/%m/%Y').strftime('%Y-%m-%d')
            except: return None

        # Helper to get float or 0
        def to_f(v):
            try: return float(v) if v else 0
            except: return 0

        # Mapping fields based on ptstatus and live template
        # ptstatus: 'I' for Increment, 'P' for Promotion, etc.
        # We'll use SAL_EmpPromotion_Details for all these revisions.
        
        vals = {
            'fk_empid': data['emp_id'],
            'dated': parse_date(data.get('dated')),
            'ptstatus': data.get('promo_type', 'I'),
            'promotioncode': data.get('order_no'),
            'dateofreporting': parse_date(data.get('order_date')),
            'earlierbasic': to_f(data.get('old_basic')),
            'newbasic': to_f(data.get('new_basic')),
            'earliergradepay': to_f(data.get('old_gp')),
            'newgradepay': to_f(data.get('new_gp')),
            'earlierspecialpay': to_f(data.get('old_sp')),
            'newspecialpay': to_f(data.get('new_sp')),
            'description1': data.get('old_npa'), # Using description1 for NPA Old
            'description2': data.get('new_npa'), # Using description2 for NPA New
            'description3': data.get('old_ca'),  # Using description3 for CA Old
            'description4': data.get('new_ca'),  # Using description4 for CA New
            'earlierpersonalpay': to_f(data.get('old_pp')),
            'newpersonalpay': to_f(data.get('new_pp')),
            'description5': data.get('old_others'), # Others Old
            'newworkdetails': data.get('new_others'), # Others New (using newworkdetails column)
            'remarks': data.get('remarks'),
            'Prob_CompDate': parse_date(data.get('prob_date')),
            'DueDatePP': parse_date(data.get('due_date_pp')),
            'SrNo': data.get('sr_no'),
            'dateofjoining': parse_date(data.get('doj')),
            'title': data.get('app_mode'), # Using title for Mode of Appointment
            'leveltype': data.get('old_scale'), # Old Scale
            'levelname': data.get('new_scale')  # New Scale
        }

        if pid:
            sql = """
                UPDATE SAL_EmpPromotion_Details SET
                fk_empid = :fk_empid, dated = :dated, ptstatus = :ptstatus, 
                promotioncode = :promotioncode, dateofreporting = :dateofreporting,
                earlierbasic = :earlierbasic, newbasic = :newbasic, 
                earliergradepay = :earliergradepay, newgradepay = :newgradepay, 
                earlierspecialpay = :earlierspecialpay, newspecialpay = :newspecialpay,
                description1 = :description1, description2 = :description2,
                description3 = :description3, description4 = :description4,
                earlierpersonalpay = :earlierpersonalpay, newpersonalpay = :newpersonalpay,
                description5 = :description5, newworkdetails = :newworkdetails,
                remarks = :remarks, Prob_CompDate = :Prob_CompDate, DueDatePP = :DueDatePP,
                SrNo = :SrNo, dateofjoining = :dateofjoining, title = :title,
                leveltype = :leveltype, levelname = :levelname,
                fk_updUserID = :user_id, fk_updDateID = GETDATE()
                WHERE pk_pid = :pid
            """
            params = vals.copy(); params['user_id'] = user_id; params['pid'] = pid
            # DB.execute doesn't support named params in my wrapper usually, so I'll convert to list
            param_list = [
                vals['fk_empid'], vals['dated'], vals['ptstatus'], vals['promotioncode'],
                vals['dateofreporting'], vals['earlierbasic'], vals['newbasic'],
                vals['earliergradepay'], vals['newgradepay'], vals['earlierspecialpay'],
                vals['newspecialpay'], vals['description1'], vals['description2'],
                vals['description3'], vals['description4'], vals['earlierpersonalpay'],
                vals['newpersonalpay'], vals['description5'], vals['newworkdetails'],
                vals['remarks'], vals['Prob_CompDate'], vals['DueDatePP'], vals['SrNo'],
                vals['dateofjoining'], vals['title'], vals['leveltype'], vals['levelname'],
                user_id, pid
            ]
            return DB.execute("""
                UPDATE SAL_EmpPromotion_Details SET
                fk_empid = ?, dated = ?, ptstatus = ?, promotioncode = ?, dateofreporting = ?,
                earlierbasic = ?, newbasic = ?, earliergradepay = ?, newgradepay = ?, 
                earlierspecialpay = ?, newspecialpay = ?, description1 = ?, description2 = ?,
                description3 = ?, description4 = ?, earlierpersonalpay = ?, newpersonalpay = ?,
                description5 = ?, newworkdetails = ?, remarks = ?, Prob_CompDate = ?, 
                DueDatePP = ?, SrNo = ?, dateofjoining = ?, title = ?, 
                leveltype = ?, levelname = ?, fk_updUserID = ?, fk_updDateID = GETDATE()
                WHERE pk_pid = ?
            """, param_list)
        else:
            param_list = [
                vals['fk_empid'], vals['dated'], vals['ptstatus'], vals['promotioncode'],
                vals['dateofreporting'], vals['earlierbasic'], vals['newbasic'],
                vals['earliergradepay'], vals['newgradepay'], vals['earlierspecialpay'],
                vals['newspecialpay'], vals['description1'], vals['description2'],
                vals['description3'], vals['description4'], vals['earlierpersonalpay'],
                vals['newpersonalpay'], vals['description5'], vals['newworkdetails'],
                vals['remarks'], vals['Prob_CompDate'], vals['DueDatePP'], vals['SrNo'],
                vals['dateofjoining'], vals['title'], vals['leveltype'], vals['levelname'],
                user_id, user_id
            ]
            return DB.execute("""
                INSERT INTO SAL_EmpPromotion_Details (
                    fk_empid, dated, ptstatus, promotioncode, dateofreporting,
                    earlierbasic, newbasic, earliergradepay, newgradepay,
                    earlierspecialpay, newspecialpay, description1, description2,
                    description3, description4, earlierpersonalpay, newpersonalpay,
                    description5, newworkdetails, remarks, Prob_CompDate, 
                    DueDatePP, SrNo, dateofjoining, title, leveltype, levelname,
                    fk_insUserID, fk_insDateID, fk_updUserID, fk_updDateID
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE(), ?, GETDATE())
            """, param_list)

    @staticmethod
    def delete(pid):
        return DB.execute("DELETE FROM SAL_EmpPromotion_Details WHERE pk_pid = ?", [pid])

class NoDuesModel:
    @staticmethod
    def get_employee_dues(emp_id):
        return DB.fetch_all("""
            SELECT N.pk_DueId as id, N.*, D.description as dept_name
            FROM SAL_Employee_NoDues_Detail N
            LEFT JOIN Department_Mst D ON N.fk_deptid = D.pk_deptid
            WHERE N.fk_empid = ?
        """, [emp_id])

    @staticmethod
    def get_by_id(due_id):
        return DB.fetch_one("SELECT pk_DueId as id, * FROM SAL_Employee_NoDues_Detail WHERE pk_DueId = ?", [due_id])

    @staticmethod
    def save(data, user_id):
        due_id = data.get('due_id')
        params = [
            data['emp_id'], data.get('dept_id'), data.get('due_pending'),
            data.get('remarks'), user_id
        ]
        if due_id:
            sql = """
                UPDATE SAL_Employee_NoDues_Detail SET
                fk_empid = ?, fk_deptid = ?, DuePending = ?, 
                Remarks = ?, fk_updUserID = ?, fk_updDateID = GETDATE()
                WHERE pk_DueId = ?
            """
            return DB.execute(sql, params + [due_id])
        else:
            sql = """
                INSERT INTO SAL_Employee_NoDues_Detail (
                    fk_empid, fk_deptid, DuePending, Remarks, 
                    fk_insUserID, fk_insDateID, fk_updUserID, fk_updDateID
                ) VALUES (?, ?, ?, ?, ?, GETDATE(), ?, GETDATE())
            """
            return DB.execute(sql, params)

    @staticmethod
    def delete(due_id):
        return DB.execute("DELETE FROM SAL_Employee_NoDues_Detail WHERE pk_DueId = ?", [due_id])

class EarnedLeaveModel:
    @staticmethod
    def get_employee_el_details(emp_id):
        return DB.fetch_all("""
            SELECT pk_elid as id, *, 
                   CONVERT(varchar, dutyfrom_date, 103) as duty_from_fmt,
                   CONVERT(varchar, dytyto_date, 103) as duty_to_fmt,
                   CONVERT(varchar, leavefrom_date, 103) as leave_from_fmt,
                   CONVERT(varchar, leaveto_date, 103) as leave_to_fmt
            FROM SAL_EarnedLeave_Details WHERE fk_empid = ? ORDER BY sno_for_emp DESC
        """, [emp_id])

    @staticmethod
    def get_by_id(el_id):
        return DB.fetch_one("""
            SELECT pk_elid as id, *, 
                   CONVERT(varchar, dutyfrom_date, 23) as duty_from_iso,
                   CONVERT(varchar, dytyto_date, 23) as duty_to_iso,
                   CONVERT(varchar, leavefrom_date, 23) as leave_from_iso,
                   CONVERT(varchar, leaveto_date, 23) as leave_to_iso
            FROM SAL_EarnedLeave_Details WHERE pk_elid = ?
        """, [el_id])

    @staticmethod
    def save(data, user_id):
        el_id = data.get('el_id')
        from datetime import datetime
        def parse_date(d):
            if not d: return None
            try: return datetime.strptime(d, '%d/%m/%Y').strftime('%Y-%m-%d')
            except: return None

        params = [
            data['emp_id'], parse_date(data.get('duty_from')), 
            parse_date(data.get('duty_to')), data.get('total_days'),
            data.get('earned'), data.get('credit'),
            parse_date(data.get('leave_from')), parse_date(data.get('leave_to')),
            data.get('leave_days'), data.get('balance')
        ]
        if el_id:
            sql = """
                UPDATE SAL_EarnedLeave_Details SET
                fk_empid = ?, dutyfrom_date = ?, dytyto_date = ?, 
                totaldays = ?, el_earned = ?, el_total = ?, 
                leavefrom_date = ?, leaveto_date = ?, 
                leave_days = ?, el_balance = ?
                WHERE pk_elid = ?
            """
            return DB.execute(sql, params + [el_id])
        else:
            sql = """
                INSERT INTO SAL_EarnedLeave_Details (
                    fk_empid, dutyfrom_date, dytyto_date, totaldays, 
                    el_earned, el_total, leavefrom_date, leaveto_date, 
                    leave_days, el_balance
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            return DB.execute(sql, params)

    @staticmethod
    def delete(el_id):
        return DB.execute("DELETE FROM SAL_EarnedLeave_Details WHERE pk_elid = ?", [el_id])

class DisciplinaryModel:
    @staticmethod
    def get_employee_records(emp_id):
        return DB.fetch_all("""
            SELECT pk_discid as id, *, 
                   CONVERT(varchar, dated, 103) as dated_fmt 
            FROM EST_Disciplinary_Action_Details WHERE fk_empid = ? AND IsDeleted = 0
        """, [emp_id])

    @staticmethod
    def get_by_id(disc_id):
        return DB.fetch_one("""
            SELECT pk_discid as id, *, 
                   CONVERT(varchar, dated, 103) as dated_fmt,
                   CONVERT(varchar, dated, 23) as dated_iso
            FROM EST_Disciplinary_Action_Details WHERE pk_discid = ?
        """, [disc_id])

    @staticmethod
    def save(data, user_id):
        disc_id = data.get('disc_id')
        from datetime import datetime
        def parse_date(d):
            if not d: return None
            try: return datetime.strptime(d, '%d/%m/%Y').strftime('%Y-%m-%d')
            except: return None

        params = [
            data['emp_id'], parse_date(data.get('dated')), data.get('discaction'),
            data.get('filename'), data.get('remarks'), data.get('orderno'),
            data.get('action_type'), user_id
        ]
        if disc_id:
            sql = """
                UPDATE EST_Disciplinary_Action_Details SET
                fk_empid = ?, dated = ?, discaction = ?, 
                filename = ISNULL(?, filename), remarks = ?, OrderNo = ?, 
                ActionTypes = ?, fk_updUserID = ?, fk_updDateID = GETDATE()
                WHERE pk_discid = ?
            """
            return DB.execute(sql, params + [disc_id])
        else:
            sql = """
                INSERT INTO EST_Disciplinary_Action_Details (
                    fk_empid, dated, discaction, filename, remarks, 
                    OrderNo, ActionTypes, IsDeleted,
                    fk_insUserID, fk_insDateID, fk_updUserID, fk_updDateID
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, GETDATE(), ?, GETDATE())
            """
            return DB.execute(sql, params)

    @staticmethod
    def delete(disc_id):
        return DB.execute("UPDATE EST_Disciplinary_Action_Details SET IsDeleted = 1 WHERE pk_discid = ?", [disc_id])

class BookGrantModel:
    @staticmethod
    def get_employee_grants(emp_id):
        return DB.fetch_all("""
            SELECT pk_grantId as id, *, 
                   fk_yearId as year_name
            FROM SAL_BookGrantDetails_Details WHERE fk_empid = ?
        """, [emp_id])

    @staticmethod
    def get_by_id(grant_id):
        return DB.fetch_one("SELECT pk_grantId as id, * FROM SAL_BookGrantDetails_Details WHERE pk_grantId = ?", [grant_id])

    @staticmethod
    def save(data, user_id):
        grant_id = data.get('grant_id')
        params = [
            data['emp_id'], data.get('year_id'), data.get('child_name'),
            data.get('amount'), data.get('class_name')
        ]
        if grant_id:
            sql = """
                UPDATE SAL_BookGrantDetails_Details SET
                fk_empid = ?, fk_yearId = ?, ChildrenName = ?, 
                Amount = ?, ClassName = ?, UpdateDate = GETDATE()
                WHERE pk_grantId = ?
            """
            return DB.execute(sql, params + [grant_id])
        else:
            sql = """
                INSERT INTO SAL_BookGrantDetails_Details (
                    fk_empid, fk_yearId, ChildrenName, Amount, ClassName, InsertDate
                ) VALUES (?, ?, ?, ?, ?, GETDATE())
            """
            return DB.execute(sql, params)

    @staticmethod
    def delete(grant_id):
        return DB.execute("DELETE FROM SAL_BookGrantDetails_Details WHERE pk_grantId = ?", [grant_id])

class BonusModel:
    @staticmethod
    def get_employee_bonuses(emp_id):
        return DB.fetch_all("""
            SELECT Pk_BonusId as id, YearId as year_id, BonusAmount as amount
            FROM SAL_EmployeeBonusAmount_dtl WHERE Fk_Empid = ?
            ORDER BY YearId DESC
        """, [emp_id])

    @staticmethod
    def get_by_id(bonus_id):
        return DB.fetch_one("SELECT Pk_BonusId as id, * FROM SAL_EmployeeBonusAmount_dtl WHERE Pk_BonusId = ?", [bonus_id])

    @staticmethod
    def save(data, user_id):
        bonus_id = data.get('bonus_id')
        params = [data['emp_id'], data.get('year_id'), data.get('amount')]
        if bonus_id:
            sql = """
                UPDATE SAL_EmployeeBonusAmount_dtl SET
                Fk_Empid = ?, YearId = ?, BonusAmount = ?, 
                UpdateUserId = ?, UpdateDate = GETDATE()
                WHERE Pk_BonusId = ?
            """
            return DB.execute(sql, params + [user_id, bonus_id])
        else:
            sql = """
                INSERT INTO SAL_EmployeeBonusAmount_dtl (
                    Fk_Empid, YearId, BonusAmount, InsertUserId, InsertDate
                ) VALUES (?, ?, ?, ?, GETDATE())
            """
            return DB.execute(sql, params + [user_id])

    @staticmethod
    def delete(bonus_id):
        return DB.execute("DELETE FROM SAL_EmployeeBonusAmount_dtl WHERE Pk_BonusId = ?", [bonus_id])

class PropertyReturnModel:
    @staticmethod
    def get_fin_years():
        return DB.fetch_all("SELECT pk_finid as id, Lyear as name FROM SAL_Financial_Year ORDER BY Lyear DESC")

    @staticmethod
    def get_employee_details(emp_id):
        return DB.fetch_one("""
            SELECT E.empname, E.empcode, D.Description as ddo_name, DP.description as dept_name,
            DS.designation
            FROM SAL_Employee_Mst E
            LEFT JOIN DDO_Mst D ON E.fk_ddoid = D.pk_ddoid
            LEFT JOIN Department_Mst DP ON E.fk_deptid = DP.pk_deptid
            LEFT JOIN SAL_Designation_Mst DS ON E.fk_desgid = DS.pk_desgid
            WHERE E.pk_empid = ?
        """, [emp_id])

    @staticmethod
    def get_property_returns(emp_id):
        return DB.fetch_all("""
            SELECT r.PkAnnualID as id, E.empcode as emp_id, r.Fk_Finid as fin_id,
            CAST(YEAR(f.date1) AS varchar) + '-' + CAST(YEAR(f.date2) AS varchar) as fin_year, 
            r.Insertdate as return_date, r.IsFinalApp
            FROM Emp_AnnualProperty_return_Mst r
            LEFT JOIN SAL_Financial_Year f ON r.Fk_Finid = f.pk_finid
            LEFT JOIN SAL_Employee_Mst E ON r.Fk_empid = E.pk_empid
            WHERE r.Fk_empid = ?
            ORDER BY r.PkAnnualID DESC
        """, [emp_id])

    @staticmethod
    def get_latest_return(emp_id):
        latest = DB.fetch_one("""
            SELECT TOP 1 PkAnnualID 
            FROM Emp_AnnualProperty_return_Mst 
            WHERE Fk_empid = ?
            ORDER BY PkAnnualID DESC
        """, [emp_id])
        if latest:
            return PropertyReturnModel.get_return_by_id(latest['PkAnnualID'])
        return None

    @staticmethod
    def submit_for_approval(pro_id, emp_id):
        return DB.execute("""
            UPDATE Emp_AnnualProperty_return_Mst 
            SET IsFinalApp = 'Y', fk_EmpIDSendTo = 'DEAN_OFFICE', UpdateDate = GETDATE()
            WHERE PkAnnualID = ?
        """, [pro_id])

    @staticmethod
    def save(data, emp_id, emp_code):
        pro_id = data.get('pro_id')
        fin_year = data.get('fin_year')
        
        if pro_id:
            # Update main record
            DB.execute("UPDATE Emp_AnnualProperty_return_Mst SET Fk_Finid = ?, Updateuserid = ?, UpdateDate = GETDATE() WHERE PkAnnualID = ?", 
                      [fin_year, emp_code, pro_id])
            # Delete old details to re-insert
            DB.execute("DELETE FROM Emp_AnnualProperty_return_HomeDtl WHERE FkAnnualID = ?", [pro_id])
            DB.execute("DELETE FROM Emp_AnnualProperty_return_LoanDtl WHERE FkAnnualID = ?", [pro_id])
            DB.execute("DELETE FROM Emp_AnnualProperty_return_BenamidarDtl WHERE FkAnnualID = ?", [pro_id])
        else:
            # Insert new main record
            DB.execute("""
                INSERT INTO Emp_AnnualProperty_return_Mst (Fk_empid, Fk_Finid, InsertUserId, Insertdate, Updateuserid, UpdateDate, IsFinalApp)
                VALUES (?, ?, ?, GETDATE(), ?, GETDATE(), 'N')
            """, [emp_id, fin_year, emp_code, emp_code])
            
            pro_id = DB.fetch_scalar("SELECT TOP 1 PkAnnualID FROM Emp_AnnualProperty_return_Mst WHERE Fk_empid = ? ORDER BY PkAnnualID DESC", [emp_id])

        # Insert Section A: Movable (HomeDtl)
        item_desc = data.getlist('item_desc[]')
        item_val = data.getlist('item_val[]')
        item_benamidar = data.getlist('item_benamidar[]')
        item_manner = data.getlist('item_manner[]')
        item_remarks = data.getlist('item_remarks[]')
        
        for i in range(len(item_desc)):
            if item_desc[i]:
                DB.execute("""
                    INSERT INTO Emp_AnnualProperty_return_HomeDtl (FkAnnualID, Desc_O_Item, Valuesinrs, Benamidar_Name, DateOfManner, Remarks)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, [pro_id, item_desc[i], item_val[i], item_benamidar[i], item_manner[i], item_remarks[i]])

        # Insert Section B: Loans (LoanDtl)
        loan_amt = data.getlist('loan_amt[]')
        loan_security = data.getlist('loan_security[]')
        loan_member = data.getlist('loan_member[]')
        loan_loanee = data.getlist('loan_loanee[]')
        loan_date = data.getlist('loan_date[]')
        loan_remarks = data.getlist('loan_remarks[]')
        
        for i in range(len(loan_amt)):
            if loan_amt[i]:
                DB.execute("""
                    INSERT INTO Emp_AnnualProperty_return_LoanDtl (FkAnnualID, AmountOfLoan, LoanInSecure, NameAvailedLoan, NameOfloanee, DateParticularLoan, LoanRemarks)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, [pro_id, loan_amt[i], loan_security[i], loan_member[i], loan_loanee[i], loan_date[i], loan_remarks[i]])

        # Insert Section C: Immovable (BenamidarDtl)
        prop_type = data.getlist('prop_type[]')
        prop_loc = data.getlist('prop_loc[]')
        prop_plot = data.getlist('prop_plot[]')
        prop_build = data.getlist('prop_build[]')
        prop_mode = data.getlist('prop_mode[]')
        prop_person = data.getlist('prop_person[]')
        prop_held = data.getlist('prop_held[]')
        prop_income = data.getlist('prop_income[]')
        
        for i in range(len(prop_type)):
            if prop_type[i]:
                DB.execute("""
                    INSERT INTO Emp_AnnualProperty_return_BenamidarDtl (FkAnnualID, TypeofProperty, PropertyLocated, Plot_Agri_Land, BuildingArea, ModeAcquisition, DetailsOfPerson, ownnameemployee, AnnualIncome)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, [pro_id, prop_type[i], prop_loc[i], prop_plot[i], prop_build[i], prop_mode[i], prop_person[i], prop_held[i], prop_income[i]])

        return pro_id

    @staticmethod
    def delete(pro_id):
        DB.execute("DELETE FROM Emp_AnnualProperty_return_HomeDtl WHERE FkAnnualID = ?", [pro_id])
        DB.execute("DELETE FROM Emp_AnnualProperty_return_LoanDtl WHERE FkAnnualID = ?", [pro_id])
        DB.execute("DELETE FROM Emp_AnnualProperty_return_BenamidarDtl WHERE FkAnnualID = ?", [pro_id])
        return DB.execute("DELETE FROM Emp_AnnualProperty_return_Mst WHERE PkAnnualID = ?", [pro_id])
