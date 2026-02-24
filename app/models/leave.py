from app.db import DB
from datetime import datetime, timedelta
from app.models.nav import NavModel
import math

class HolidayModel:
    @staticmethod
    def get_holiday_types():
        return DB.fetch_all("SELECT pk_holidaytypeid as id, holidaytype as name FROM SAL_HolidayType_Mst ORDER BY holidaytype")

    @staticmethod
    def get_common_holidays():
        query = "SELECT C.*, T.holidaytype FROM SAL_CommonHolidays_Mst C LEFT JOIN SAL_HolidayType_Mst T ON C.fk_holidaytypeid = T.pk_holidaytypeid ORDER BY C.displayorder"
        return DB.fetch_all(query)

    @staticmethod
    def save_common_holiday(data, user_id):
        if data.get('id'):
            sql = "UPDATE SAL_CommonHolidays_Mst SET holidayname=?, fk_holidaytypeid=?, hdate=?, displayorder=?, fk_updUserID=?, fk_updDateID=GETDATE() WHERE pk_cholidayid=?"
            return DB.execute(sql, [data['name'], data['type_id'], data['date'], data['order'], user_id, data['id']])
        else:
            sql = "INSERT INTO SAL_CommonHolidays_Mst (holidayname, fk_holidaytypeid, hdate, displayorder, fk_insUserID, fk_insDateID) VALUES (?, ?, ?, ?, ?, GETDATE())"
            return DB.execute(sql, [data['name'], data['type_id'], data['date'], data['order'], user_id])

    @staticmethod
    def get_holiday_locations():
        return DB.fetch_all("SELECT pk_holidaylocid as id, holidayloc as name, displayorder FROM SAL_HolidayLocation_Mst ORDER BY displayorder")

    @staticmethod
    def save_holiday_location(data, user_id):
        if data.get('id'):
            return DB.execute("UPDATE SAL_HolidayLocation_Mst SET holidayloc=?, displayorder=?, fk_updUserID=?, fk_updDateID=GETDATE() WHERE pk_holidaylocid=?", [data['name'], data['order'], user_id, data['id']])
        return DB.execute("INSERT INTO SAL_HolidayLocation_Mst (holidayloc, displayorder, fk_insUserID, fk_insDateID) VALUES (?, ?, ?, GETDATE())", [data['name'], data['order'], user_id])

    @staticmethod
    def get_loc_wise_holidays(hloc_id=None, lyear=None, univ_loc_id=None):
        query = "SELECT M.*, H.holidayloc, L.locname FROM SAL_LocationWiseHolidays_Mst M INNER JOIN SAL_HolidayLocation_Mst H ON M.fk_holidaylocid = H.pk_holidaylocid INNER JOIN Location_Mst L ON M.fk_locid = L.pk_locid WHERE 1=1"
        params = []
        if hloc_id: query += " AND M.fk_holidaylocid = ?"; params.append(hloc_id)
        if lyear: query += " AND M.fk_yearid = ?"; params.append(lyear)
        if univ_loc_id: query += " AND M.fk_locid = ?"; params.append(univ_loc_id)
        return DB.fetch_all(query, params)

    @staticmethod
    def save_loc_wise_holiday(data, user_id):
        sql = "INSERT INTO SAL_LocationWiseHolidays_Mst (fk_holidaylocid, fk_yearid, fk_locid, remarks, fk_insUserID, fk_insDateID) VALUES (?, ?, ?, ?, ?, GETDATE())"
        return DB.execute(sql, [data['hloc_id'], data['year_id'], data['loc_id'], data['remarks'], user_id])

    @staticmethod
    def get_loc_holiday_details(mid):
        return DB.fetch_all("SELECT D.*, H.holidayname FROM SAL_LocationWiseHolidays_Dtl D INNER JOIN SAL_CommonHolidays_Mst H ON D.fk_cholidayid = H.pk_cholidayid WHERE D.fk_locholidayid = ?", [mid])

    @staticmethod
    def save_loc_holiday_detail(mid, ch_id, user_id):
        return DB.execute("INSERT INTO SAL_LocationWiseHolidays_Dtl (fk_locholidayid, fk_cholidayid, fk_insUserID, fk_insDateID) VALUES (?, ?, ?, GETDATE())", [mid, ch_id, user_id])

    @staticmethod
    def delete_loc_holiday_detail(did):
        return DB.execute("DELETE FROM SAL_LocationWiseHolidays_Dtl WHERE pk_locholidaydtlid = ?", [did])

class LeaveEncashmentModel:
    @staticmethod
    def get_encashments(emp_id=None):
        query = "SELECT * FROM SAL_LeaveEncashment_Mst"
        if emp_id: return DB.fetch_all(query + " WHERE fk_empid = ?", [emp_id])
        return DB.fetch_all(query)

    @staticmethod
    def get_encashment_history(emp_id):
        query = "SELECT E.*, L.leavetype FROM SAL_Leave_Encashment_Trn E INNER JOIN SAL_Leavetype_Mst L ON E.fk_leaveid = L.pk_leaveid WHERE E.fk_empid = ? ORDER BY E.encashdate DESC"
        return DB.fetch_all(query, [emp_id])

class LeaveAssignmentModel:
    @staticmethod
    def get_unassigned_employees(lid, fid, ddoid, locid, deptid, emp_code):
        query = "SELECT E.pk_empid, E.empcode, E.empname, DS.designation FROM SAL_Employee_Mst E LEFT JOIN SAL_Designation_Mst DS ON E.fk_desgid = DS.pk_desgid WHERE E.pk_empid NOT IN (SELECT fk_empid FROM SAL_LeaveAssignment_Details WHERE fk_leaveid = ? AND fk_yearid = ?) AND E.employeeleftstatus = 'N'"
        params = [lid, fid]
        if ddoid: query += " AND E.fk_ddoid = ?"; params.append(ddoid)
        if locid: query += " AND E.fk_locid = ?"; params.append(locid)
        if deptid: query += " AND E.fk_deptid = ?"; params.append(deptid)
        if emp_code: query += " AND E.empcode LIKE ?"; params.append(f"%{emp_code}%")
        return DB.fetch_all(query + " ORDER BY E.empname", params)

    @staticmethod
    def get_assigned_employees(lid, fid, ddoid, locid, deptid, emp_code):
        query = "SELECT E.pk_empid, E.empcode, E.empname, DS.designation, A.leaveassigned FROM SAL_Employee_Mst E INNER JOIN SAL_LeaveAssignment_Details A ON E.pk_empid = A.fk_empid LEFT JOIN SAL_Designation_Mst DS ON E.fk_desgid = DS.pk_desgid WHERE A.fk_leaveid = ? AND A.fk_yearid = ?"
        params = [lid, fid]
        if ddoid: query += " AND E.fk_ddoid = ?"; params.append(ddoid)
        if locid: query += " AND E.fk_locid = ?"; params.append(locid)
        if deptid: query += " AND E.fk_deptid = ?"; params.append(deptid)
        if emp_code: query += " AND E.empcode LIKE ?"; params.append(f"%{emp_code}%")
        return DB.fetch_all(query + " ORDER BY E.empname", params)

    @staticmethod
    def save_assignments(lid, fid, emp_ids, days, user_id):
        for eid in emp_ids:
            exists = DB.fetch_one("SELECT pk_leaveassignid FROM SAL_LeaveAssignment_Details WHERE fk_empid=? AND fk_leaveid=? AND fk_yearid=?", [eid, lid, fid])
            if exists:
                DB.execute("UPDATE SAL_LeaveAssignment_Details SET leaveassigned=?, fk_updUserID=?, fk_updDateID=GETDATE() WHERE pk_leaveassignid=?", [days, user_id, exists['pk_leaveassignid']])
            else:
                DB.execute("INSERT INTO SAL_LeaveAssignment_Details (fk_empid, fk_leaveid, fk_yearid, leaveassigned, leaveavailed, fk_insUserID, fk_insDateID) VALUES (?, ?, ?, ?, 0, ?, GETDATE())", [eid, lid, fid, days, user_id])
        return True

class LeaveReportModel:
    @staticmethod
    def get_leave_transactions(filters, sql_limit=""):
        query = "SELECT T.*, E.empname, E.empcode, L.leavetype, DDO.Description as DDO FROM SAL_Leave_Tran_Mst T INNER JOIN SAL_Employee_Mst E ON T.fk_empid = E.pk_empid INNER JOIN SAL_Leavetype_Mst L ON T.fk_leaveid = L.pk_leaveid LEFT JOIN DDO_Mst DDO ON E.fk_ddoid = DDO.pk_ddoid WHERE 1=1"
        params = []
        if filters.get('from_date'): query += " AND T.fromdate >= ?"; params.append(filters['from_date'])
        if filters.get('to_date'): query += " AND T.todate <= ?"; params.append(filters['to_date'])
        if filters.get('emp_id'): query += " AND T.fk_empid = ?"; params.append(filters['emp_id'])
        if filters.get('leave_id'): query += " AND T.fk_leaveid = ?"; params.append(filters['leave_id'])
        if filters.get('ddo_id'): query += " AND E.fk_ddoid = ?"; params.append(filters['ddo_id'])
        return DB.fetch_all(query + f" ORDER BY T.fromdate DESC {sql_limit}", params)

    @staticmethod
    def get_leave_transactions_count(filters):
        query = "SELECT COUNT(*) FROM SAL_Leave_Tran_Mst T INNER JOIN SAL_Employee_Mst E ON T.fk_empid = E.pk_empid WHERE 1=1"
        params = []
        if filters.get('from_date'): query += " AND T.fromdate >= ?"; params.append(filters['from_date'])
        if filters.get('to_date'): query += " AND T.todate <= ?"; params.append(filters['to_date'])
        if filters.get('emp_id'): query += " AND T.fk_empid = ?"; params.append(filters['emp_id'])
        if filters.get('leave_id'): query += " AND T.fk_leaveid = ?"; params.append(filters['leave_id'])
        if filters.get('ddo_id'): query += " AND E.fk_ddoid = ?"; params.append(filters['ddo_id'])
        return DB.fetch_scalar(query, params)

    @staticmethod
    def get_el_reconciliation(emp_id):
        return DB.fetch_all("SELECT * FROM SAL_EL_Reconciliation WHERE fk_empid = ? ORDER BY dated DESC", [emp_id])

    @staticmethod
    def update_el_balance(emp_id, days, user_id):
        return DB.execute("UPDATE SAL_EmployeeLeave_Details SET totalleavesearned = ISNULL(totalleavesearned, 0) + ?, fk_updUserID = ?, fk_updDateID = GETDATE() WHERE fk_empid = ? AND fk_leaveid = 2", [days, user_id, emp_id])

class LeaveConfigModel:
    @staticmethod
    def get_leave_types_full():
        return DB.fetch_all("SELECT pk_leaveid, leavetype, shortdesc, leavenature, gender, remarks FROM SAL_Leavetype_Mst ORDER BY leavetype")

    @staticmethod
    def get_leave_type_details(leave_id):
        query = "SELECT D.*, N.nature FROM SAL_Leavetype_Details D INNER JOIN SAL_Nature_Mst N ON D.fk_natureid = N.pk_natureid WHERE D.fk_leaveid = ?"
        return DB.fetch_all(query, [leave_id])

    @staticmethod
    def get_approvers():
        return DB.fetch_all("SELECT pk_empid as id, empname + ' | ' + empcode as name FROM SAL_Employee_Mst WHERE employeeleftstatus='N' ORDER BY empname")

    @staticmethod
    def update_workflow(emp_id, approver_id, user_id):
        return DB.execute("UPDATE SAL_Employee_Mst SET reportingto = ?, fk_updUserID = ?, fk_updDateID = GETDATE() WHERE pk_empid = ?", [approver_id, user_id, emp_id])

    @staticmethod
    def save_leave_type(data, user_id):
        if data.get('pk_leaveid'):
            return DB.execute("UPDATE SAL_Leavetype_Mst SET shortdesc=?, leavenature=?, gender=?, remarks=?, fk_updUserID=?, fk_updDateID=GETDATE() WHERE pk_leaveid=?", [data['short'], data['nature'], data['gender'], data['remarks'], user_id, data['pk_leaveid']])
        return DB.execute("INSERT INTO SAL_Leavetype_Mst (leavetype, shortdesc, leavenature, gender, remarks, fk_updUserID, fk_updDateID) VALUES (?, ?, ?, ?, ?, ?, GETDATE())", [data['name'], data['short'], data['nature'], data['gender'], data['remarks'], user_id])

class LeaveModel:
    @staticmethod
    def get_leave_types(is_admin=False):
        query = "SELECT pk_leaveid as id, leavetype as name FROM SAL_Leavetype_Mst WHERE pk_leaveid IN (9, 41, 2, 7) ORDER BY CASE pk_leaveid WHEN 9 THEN 1 WHEN 41 THEN 2 WHEN 2 THEN 3 WHEN 7 THEN 4 END"
        return DB.fetch_all(query)

    @staticmethod
    def get_employee_full_details(emp_id):
        query = "SELECT E.*, D.designation, DEPT.description as department, L.locname as collegename FROM SAL_Employee_Mst E LEFT JOIN SAL_Designation_Mst D ON E.fk_desgid = D.pk_desgid LEFT JOIN Department_Mst DEPT ON E.fk_deptid = DEPT.pk_deptid LEFT JOIN Location_Mst L ON E.fk_locid = L.pk_locid WHERE E.pk_empid = ?"
        return DB.fetch_one(query, [emp_id])

    @staticmethod
    def get_recommended_for(emp_id):
        query = "SELECT R.pk_leavereqid as id, E.empname as EmployeeName, L.leavetype as LeaveType, CONVERT(varchar, R.fromdate, 103) as FromDate, CONVERT(varchar, R.todate, 103) as ToDate, R.totalleavedays as Days, R.reasonforleave as Reason, R.contactno as Contact, '' as Comment FROM SAL_Leave_Request_Mst R INNER JOIN SAL_Employee_Mst E ON R.fk_reqempid = E.pk_empid INNER JOIN SAL_Leavetype_Mst L ON R.fk_leaveid = L.pk_leaveid WHERE (R.recommendEmpCode = ? OR R.recommendEmpCode2 = ? OR R.recommendEmpCode3 = ?) AND R.leavestatus = 'S' AND R.iscancelled = 'N'"
        return DB.fetch_all(query, [emp_id, emp_id, emp_id])

    @staticmethod
    def get_leave_balance(emp_id):
        fy = NavModel.get_current_fin_year()
        lyear = fy.get('Lyear')
        sql_params = [emp_id, emp_id, emp_id, fy['date1'], fy['date2'], emp_id, emp_id, lyear]
        query = "SELECT L.leavetype, L.pk_leaveid, CASE WHEN L.pk_leaveid = 2 THEN (ISNULL(B.currentyearleaves, 0) + ISNULL(B.totalleavesearned, 0)) ELSE ISNULL(LA.leaveassigned, ISNULL(B.currentyearleaves, 0)) END as total, dbo.SAL_FN_GetAvailedLeave(?, L.pk_leaveid) as availed, dbo.SAL_FN_GetAdjustedLeave(?, L.pk_leaveid) as adjusted, ISNULL((SELECT SUM(totalleavedays) FROM SAL_Leave_Request_Mst WHERE fk_reqempid = ? AND fk_leaveid = L.pk_leaveid AND leavestatus = 'S' AND iscancelled = 'N' AND fromdate BETWEEN ? AND ?), 0) as applied FROM SAL_Leavetype_Mst L LEFT JOIN SAL_EmployeeLeave_Details B ON L.pk_leaveid = B.fk_leaveid AND B.fk_empid = ? LEFT JOIN SAL_LeaveAssignment_Details LA ON L.pk_leaveid = LA.fk_leaveid AND LA.fk_empid = ? AND LA.fk_yearid = ? WHERE L.pk_leaveid IN (9, 41, 2, 7) ORDER BY CASE L.pk_leaveid WHEN 9 THEN 1 WHEN 41 THEN 2 WHEN 2 THEN 3 WHEN 7 THEN 4 END"
        res = DB.fetch_all(query, sql_params)
        for r in res:
            t = float(r.get('total') or 0); v = float(r.get('availed') or 0); app = float(r.get('applied') or 0)
            r['total'] = t; r['availed'] = v; r['applied'] = app; r['balance'] = t - v; r['applied_balance'] = (t - v) - app
        return res

    @staticmethod
    def get_leave_summary(emp_id):
        return LeaveModel.get_leave_balance(emp_id)

    @staticmethod
    def save_leave_request(data, user_id):
        sql = """
        INSERT INTO SAL_Leave_Request_Mst (
            fk_requesterid, fk_reqempid, reqdate, fk_leaveid,
            fromdate, todate, totaldays, totalleavedays,
            reasonforleave, contactno,
            issubmit, submitdate, iscancelled,
            fk_reportingto, leavestatus,
            fk_insUserID, fk_insDateID, fk_updUserID, fk_updDateID,
            fk_locid,
            recommendEmpCode, recommendEmpCode2, recommendEmpCode3,
            Stationfromdate, Stationtodate,
            HPLWMed, HPLFStd, addInstitution,
            CommutedLeave, IsShortLeave,
            StartTime, StationStartTime, StationEndTime
        ) VALUES (
            ?, ?, CONVERT(date, GETDATE()), ?,
            ?, ?, ?, ?,
            ?, ?,
            'Y', GETDATE(), 'N',
            ?, 'S',
            ?, CONVERT(varchar, GETDATE(), 120), ?, CONVERT(varchar, GETDATE(), 120),
            ?,
            ?, ?, ?,
            ?, ?,
            ?, ?, ?,
            ?, ?,
            ?, ?, ?
        )
        """
        params = [
            user_id,
            data["emp_id"],
            data["leave_id"],
            data["from_date"],
            data["to_date"],
            data.get("total_days") or 0,
            data.get("leave_days") or 0,
            data.get("reason"),
            data.get("contact"),
            data.get("reporting_to"),
            user_id,
            user_id,
            data.get("loc_id"),
            data.get("rec1"),
            data.get("rec2"),
            data.get("rec3"),
            data.get("station_from"),
            data.get("station_to"),
            1 if data.get("is_medical") else 0,
            1 if data.get("is_study") else 0,
            data.get("add_inst"),
            1 if data.get("is_commuted") else 0,
            1 if data.get("is_short") else 0,
            data.get("req_time"),
            data.get("station_start_time"),
            data.get("station_end_time"),
        ]
        return DB.execute(sql, params)

    @staticmethod
    def get_leave_request_for_edit(req_id, user_id):
        query = """
        SELECT
            R.pk_leavereqid as id,
            R.fk_leaveid as leave_id,
            CONVERT(varchar, R.fromdate, 23) as from_iso,
            CONVERT(varchar, R.todate, 23) as to_iso,
            CONVERT(varchar, R.Stationfromdate, 23) as station_from_iso,
            CONVERT(varchar, R.Stationtodate, 23) as station_to_iso,
            R.totaldays, R.totalleavedays,
            R.reasonforleave as reason,
            R.contactno as contact,
            R.fk_reportingto as reporting_to,
            (RO.empname + ' | ' + RO.empcode + ' | ' + ISNULL(ROD.designation, '')) as reporting_to_name,
            R.recommendEmpCode as rec1,
            R.recommendEmpCode2 as rec2,
            R.recommendEmpCode3 as rec3,
            (R1.empname + ' | ' + R1.empcode + ' | ' + ISNULL(R1D.designation, '')) as rec1_name,
            (R2.empname + ' | ' + R2.empcode + ' | ' + ISNULL(R2D.designation, '')) as rec2_name,
            (R3.empname + ' | ' + R3.empcode + ' | ' + ISNULL(R3D.designation, '')) as rec3_name,
            R.HPLWMed as is_medical,
            R.HPLFStd as is_study,
            R.CommutedLeave as is_commuted,
            R.addInstitution as add_inst,
            R.IsShortLeave as is_short,
            R.StartTime as start_time,
            R.StationStartTime as station_start_time,
            R.StationEndTime as station_end_time,
            R.leavestatus,
            R.iscancelled
        FROM SAL_Leave_Request_Mst R
        LEFT JOIN SAL_Employee_Mst RO ON R.fk_reportingto = RO.pk_empid
        LEFT JOIN SAL_Designation_Mst ROD ON RO.fk_desgid = ROD.pk_desgid
        LEFT JOIN SAL_Employee_Mst R1 ON R.recommendEmpCode = R1.pk_empid
        LEFT JOIN SAL_Designation_Mst R1D ON R1.fk_desgid = R1D.pk_desgid
        LEFT JOIN SAL_Employee_Mst R2 ON R.recommendEmpCode2 = R2.pk_empid
        LEFT JOIN SAL_Designation_Mst R2D ON R2.fk_desgid = R2D.pk_desgid
        LEFT JOIN SAL_Employee_Mst R3 ON R.recommendEmpCode3 = R3.pk_empid
        LEFT JOIN SAL_Designation_Mst R3D ON R3.fk_desgid = R3D.pk_desgid
        WHERE R.pk_leavereqid = ? AND R.fk_requesterid = ?
        """
        return DB.fetch_one(query, [req_id, user_id])

    @staticmethod
    def update_leave_request(req_id, data, user_id):
        exists = DB.fetch_one(
            """
            SELECT pk_leavereqid
            FROM SAL_Leave_Request_Mst
            WHERE pk_leavereqid = ? AND fk_requesterid = ? AND leavestatus = 'S' AND iscancelled = 'N'
            """,
            [req_id, user_id],
        )
        if not exists:
            return False

        sql = """
        UPDATE SAL_Leave_Request_Mst SET
            fk_leaveid = ?,
            fromdate = ?,
            todate = ?,
            totaldays = ?,
            totalleavedays = ?,
            reasonforleave = ?,
            contactno = ?,
            fk_reportingto = ?,
            recommendEmpCode = ?,
            recommendEmpCode2 = ?,
            recommendEmpCode3 = ?,
            Stationfromdate = ?,
            Stationtodate = ?,
            HPLWMed = ?,
            HPLFStd = ?,
            addInstitution = ?,
            CommutedLeave = ?,
            IsShortLeave = ?,
            StartTime = ?,
            StationStartTime = ?,
            StationEndTime = ?,
            fk_updUserID = ?,
            fk_updDateID = CONVERT(varchar, GETDATE(), 120)
        WHERE pk_leavereqid = ? AND fk_requesterid = ?
        """
        params = [
            data["leave_id"],
            data["from_date"],
            data["to_date"],
            data.get("total_days") or 0,
            data.get("leave_days") or 0,
            data.get("reason"),
            data.get("contact"),
            data.get("reporting_to"),
            data.get("rec1"),
            data.get("rec2"),
            data.get("rec3"),
            data.get("station_from"),
            data.get("station_to"),
            1 if data.get("is_medical") else 0,
            1 if data.get("is_study") else 0,
            data.get("add_inst"),
            1 if data.get("is_commuted") else 0,
            1 if data.get("is_short") else 0,
            data.get("req_time"),
            data.get("station_start_time"),
            data.get("station_end_time"),
            user_id,
            req_id,
            user_id,
        ]
        return DB.execute(sql, params)

    @staticmethod
    def cancel_leave_request(req_id, user_id):
        exists = DB.fetch_one(
            """
            SELECT pk_leavereqid
            FROM SAL_Leave_Request_Mst
            WHERE pk_leavereqid = ? AND fk_requesterid = ? AND leavestatus = 'S' AND iscancelled = 'N'
            """,
            [req_id, user_id],
        )
        if not exists:
            return False
        return DB.execute(
            """
            UPDATE SAL_Leave_Request_Mst
            SET iscancelled = 'Y', leavestatus = 'C', fk_updUserID = ?, fk_updDateID = CONVERT(varchar, GETDATE(), 120)
            WHERE pk_leavereqid = ? AND fk_requesterid = ?
            """,
            [user_id, req_id, user_id],
        )

    @staticmethod
    def get_reporting_officer(empid):
        # 1. Get employee basic info
        query = "SELECT pk_empid, fk_deptid, fk_controllingid, reportingto FROM SAL_Employee_Mst WHERE pk_empid = ?"
        emp = DB.fetch_one(query, [empid])
        if not emp: return None

        # 2. Check if they are the HOD of their own department
        is_hod = False
        dept = None
        if emp['fk_deptid']:
            query_dept = "SELECT Hod_Id, Description FROM Department_Mst WHERE pk_deptid = ?"
            dept = DB.fetch_one(query_dept, [emp['fk_deptid']])
            if dept and dept['Hod_Id'] == empid:
                is_hod = True

        # Priority 1: If NOT HOD, they must report to their HOD
        if not is_hod and dept and dept['Hod_Id']:
            query_ro = """
            SELECT RO.pk_empid as id, RO.empname + ' | ' + RO.empcode + ' | ' + ISNULL(D.designation, '') as name
            FROM SAL_Employee_Mst RO
            LEFT JOIN SAL_Designation_Mst D ON RO.fk_desgid = D.pk_desgid
            WHERE RO.pk_empid = ?
            """
            res = DB.fetch_one(query_ro, [dept['Hod_Id']])
            if res: return res

        # Priority 2: Check Controlling Officer (HODs report to Dean/Controlling Officer)
        if emp['fk_controllingid']:
            query = """
            SELECT RO.pk_empid as id, RO.empname + ' | ' + RO.empcode + ' | ' + ISNULL(D.designation, '') as name
            FROM Sal_ControllingOffice_Mst C
            INNER JOIN SAL_Employee_Mst RO ON C.ControllingOfficer_Id = RO.pk_empid
            LEFT JOIN SAL_Designation_Mst D ON RO.fk_desgid = D.pk_desgid
            WHERE C.pk_Controllid = ?
            """
            res = DB.fetch_one(query, [emp['fk_controllingid']])
            if res and res['id'] != empid: # Ensure they don't report to themselves
                return res

        # 3. Priority 3: Check direct reportingto in SAL_Employee_Mst
        if emp['reportingto']:
            query = """
            SELECT RO.pk_empid as id, RO.empname + ' | ' + RO.empcode + ' | ' + ISNULL(D.designation, '') as name
            FROM SAL_Employee_Mst RO
            LEFT JOIN SAL_Designation_Mst D ON RO.fk_desgid = D.pk_desgid
            WHERE RO.pk_empid = ?
            """
            res = DB.fetch_one(query, [emp['reportingto']])
            if res and res['id'] != empid:
                return res

        # 4. Fallback: Most recent successful approver from history
        query = """
        SELECT TOP 1 RO.pk_empid as id, RO.empname + ' | ' + RO.empcode + ' | ' + ISNULL(D.designation, '') as name
        FROM SAL_Leave_Request_Mst R
        INNER JOIN SAL_Employee_Mst RO ON R.fk_reportingto = RO.pk_empid
        LEFT JOIN SAL_Designation_Mst D ON RO.fk_desgid = D.pk_desgid
        WHERE R.fk_reqempid = ? AND R.leavestatus = 'A'
        ORDER BY R.reqdate DESC
        """
        return DB.fetch_one(query, [empid])

    @staticmethod
    def _get_offcovered_flag(leave_id, emp_id):
        """
        offcovered (SAL_Leavetype_Details.offcovered):
        - When 1: weekly-offs/holidays are treated as covered (count all calendar days).
        - When 0: weekly-offs/holidays are excluded (count only working days).
        """
        query = """
        SELECT TOP 1 D.offcovered
        FROM SAL_Leavetype_Details D
        INNER JOIN SAL_Employee_Mst E ON E.pk_empid = ?
        WHERE D.fk_leaveid = ?
          AND (D.fk_natureid = E.fk_natureid OR ISNULL(D.fk_natureid, '') = '')
        ORDER BY CASE WHEN D.fk_natureid = E.fk_natureid THEN 0 ELSE 1 END, D.pk_id DESC
        """
        row = DB.fetch_one(query, [emp_id, leave_id])
        if row and row.get("offcovered") is not None:
            try:
                return bool(row["offcovered"])
            except Exception:
                return True
        return True

    @staticmethod
    def _get_holiday_dates_for_loc(loc_id, year_id):
        # Location-wise holidays are stored in SAL_LocationWiseHolidays_Mst (header) and *_Trn (dates).
        mst = DB.fetch_one(
            """
            SELECT TOP 1 pk_locholidayid
            FROM SAL_LocationWiseHolidays_Mst
            WHERE fk_locid = ? AND fk_yearid = ?
            ORDER BY pk_locholidayid DESC
            """,
            [loc_id, year_id],
        )
        if not mst:
            return set()

        rows = DB.fetch_all(
            """
            SELECT holidaydate, todate
            FROM SAL_LocationWiseHolidays_Trn
            WHERE fk_locholidayid = ?
            """,
            [mst["pk_locholidayid"]],
        )

        holiday_dates = set()
        for r in rows:
            d1 = r.get("holidaydate")
            d2 = r.get("todate") or d1
            if not d1:
                continue
            try:
                cur = d1.date() if hasattr(d1, "date") else d1
                end = d2.date() if hasattr(d2, "date") else d2
            except Exception:
                continue
            while cur <= end:
                holiday_dates.add(cur)
                cur = cur + timedelta(days=1)
        return holiday_dates

    @staticmethod
    def _get_weekly_off_days_for_loc(loc_id):
        row = DB.fetch_one(
            """
            SELECT TOP 1 sun, mon, tue, wed, thur, fri, sat
            FROM SAL_WeeklyOff_Mst
            WHERE fk_locid = ?
            ORDER BY pk_woffid DESC
            """,
            [loc_id],
        )
        if not row:
            return set()

        def is_on(v):
            if v is None:
                return False
            s = str(v).strip().lower()
            return s in {"y", "yes", "1", "true", "t", "on"}

        # Python weekday: Mon=0..Sun=6
        mapping = {
            6: is_on(row.get("sun")),
            0: is_on(row.get("mon")),
            1: is_on(row.get("tue")),
            2: is_on(row.get("wed")),
            3: is_on(row.get("thur")),
            4: is_on(row.get("fri")),
            5: is_on(row.get("sat")),
        }
        return {wd for wd, enabled in mapping.items() if enabled}

    @staticmethod
    def calculate_breakup(from_date, to_date, loc_id, emp_id, leave_id, is_short=False):
        """
        Returns: (leave_days, total_days, rows)
          - leave_days: counted leave days (numeric)
          - total_days: calendar days between from/to inclusive
          - rows: counted day-wise rows [{date, day}...]
        """
        try:
            d1 = datetime.strptime(from_date, "%Y-%m-%d").date()
            d2 = datetime.strptime(to_date, "%Y-%m-%d").date()
        except Exception:
            return 0, 0, []

        if d2 < d1:
            return 0, 0, []

        if is_short:
            rows = [{"date": d1.strftime("%d/%m/%Y"), "day": d1.strftime("%A")}]
            return 1.0, 1.0, rows

        total_days = float((d2 - d1).days + 1)
        offcovered = LeaveModel._get_offcovered_flag(leave_id, emp_id)

        holiday_dates = set()
        weekly_off_wds = set()
        if not offcovered and loc_id:
            holiday_dates = LeaveModel._get_holiday_dates_for_loc(loc_id, d1.year)
            weekly_off_wds = LeaveModel._get_weekly_off_days_for_loc(loc_id)

        try:
            leave_id_int = int(str(leave_id).strip())
        except Exception:
            leave_id_int = None

        rows = []
        cur = d1
        while cur <= d2:
            is_holiday = cur in holiday_dates
            is_weekly_off = cur.weekday() in weekly_off_wds if weekly_off_wds else False

            if leave_id_int == 7:
                counted = is_holiday
            elif offcovered:
                counted = True
            else:
                counted = (not is_holiday) and (not is_weekly_off)

            if counted:
                rows.append({"date": cur.strftime("%d/%m/%Y"), "day": cur.strftime("%A")})
            cur = cur + timedelta(days=1)

        leave_days = float(len(rows))
        return leave_days, total_days, rows

    @staticmethod
    def calculate_days(from_date, to_date, loc_id, is_short=False, emp_id=None, leave_id=None):
        # Backward-compatible helper (older code only expected days).
        if emp_id and leave_id:
            leave_days, _, _ = LeaveModel.calculate_breakup(from_date, to_date, loc_id, emp_id, leave_id, is_short=is_short)
            return leave_days
        if is_short:
            return 1.0
        try:
            d1 = datetime.strptime(from_date, "%Y-%m-%d")
            d2 = datetime.strptime(to_date, "%Y-%m-%d")
            return float((d2 - d1).days + 1)
        except Exception:
            return 0.0

    @staticmethod
    def get_user_leaves(user_id, page=1, per_page=10):
        offset = (page - 1) * per_page
        total = DB.fetch_scalar("SELECT COUNT(*) FROM SAL_Leave_Request_Mst WHERE fk_requesterid = ?", [user_id])
        query = f"""
        SELECT R.pk_leavereqid as RequestID, 
        E.empname as ReportingTo,
        CASE WHEN ISNULL(R.IsShortLeave, 0) = 1 THEN (L.leavetype + ' (Short Leave)') ELSE L.leavetype END as LeaveType,
        CONVERT(varchar, R.reqdate, 103) as RequestDate,
        R.StartTime as RequestTime,
        CONVERT(varchar, R.fromdate, 103) as FromDate,
        CONVERT(varchar, R.todate, 103) as ToDate,
        CONVERT(varchar, R.Stationfromdate, 103) as SFrom,
        CONVERT(varchar, R.Stationtodate, 103) as STo,
        R.totalleavedays as Days,
        R.leavestatus as StatusCode,
        R.iscancelled as IsCancelled,
        CASE WHEN R.leavestatus = 'A' THEN 'Approved'
             WHEN R.leavestatus = 'R' THEN 'Rejected'
             WHEN R.leavestatus = 'C' THEN 'Cancelled'
             ELSE 'Assigned' END as Status
        FROM SAL_Leave_Request_Mst R 
        LEFT JOIN SAL_Leavetype_Mst L ON R.fk_leaveid = L.pk_leaveid
        LEFT JOIN SAL_Employee_Mst E ON R.fk_reportingto = E.pk_empid
        WHERE R.fk_requesterid = ? ORDER BY R.reqdate DESC
        OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY
        """
        return DB.fetch_all(query, [user_id]), total

    @staticmethod
    def get_approved_recent(emp_id, page=1, per_page=10):
        offset = (page - 1) * per_page
        total = DB.fetch_scalar("SELECT COUNT(*) FROM SAL_Leave_Request_Mst WHERE fk_reportingto = ? AND leavestatus IN ('A','R')", [emp_id])
        query = f"""
        SELECT R.pk_leavereqid as RequestID, E.empname as EmployeeName, E.empcode, 
        L.leavetype as LeaveType,
        CONVERT(varchar, R.reqdate, 103) as RequestDate,
        R.StartTime as RequestTime,
        CONVERT(varchar, R.fromdate, 103) as FromDate, 
        CONVERT(varchar, R.todate, 103) as ToDate,
        R.totalleavedays as Days, 
        CASE WHEN R.leavestatus = 'A' THEN 'Approved' ELSE 'Rejected' END as Status,
        CONVERT(varchar, R.responsedate, 103) as ApprovedDate
        FROM SAL_Leave_Request_Mst R
        INNER JOIN SAL_Employee_Mst E ON R.fk_reqempid = E.pk_empid
        INNER JOIN SAL_Leavetype_Mst L ON R.fk_leaveid = L.pk_leaveid
        WHERE R.fk_reportingto = ? AND R.leavestatus IN ('A','R')
        ORDER BY R.responsedate DESC
        OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY
        """
        return DB.fetch_all(query, [emp_id]), total

    @staticmethod
    def get_pending_approvals(emp_id):
        fy = NavModel.get_current_fin_year()
        d1, d2 = fy['date1'], fy['date2']
        query = """
        SELECT R.pk_leavereqid as RequestID, E.empname as EmployeeName, E.empcode, 
        L.leavetype as LeaveType, 
        CONVERT(varchar, R.reqdate, 103) as RequestDate,
        R.StartTime as RequestTime,
        CONVERT(varchar, R.fromdate, 103) as FromDate,
        CONVERT(varchar, R.todate, 103) as ToDate,
        CONVERT(varchar, R.Stationfromdate, 103) as SFrom,
        CONVERT(varchar, R.Stationtodate, 103) as STo,
        R.totalleavedays as Days,
        R.leavestatus, R.contactno, R.reasonforleave as Reason
        FROM SAL_Leave_Request_Mst R 
        INNER JOIN SAL_Employee_Mst E ON R.fk_reqempid = E.pk_empid 
        INNER JOIN SAL_Leavetype_Mst L ON R.fk_leaveid = L.pk_leaveid 
        WHERE R.fk_reportingto = ? AND R.leavestatus = 'S'
        AND R.fromdate BETWEEN ? AND ?
        """
        return DB.fetch_all(query, [emp_id, d1, d2])

    @staticmethod
    def get_approved_leaves_for_adj(emp_id):
        return DB.fetch_all("SELECT R.*, L.leavetype FROM SAL_Leave_Request_Mst R INNER JOIN SAL_Leavetype_Mst L ON R.fk_leaveid = L.pk_leaveid WHERE R.fk_reqempid = ? AND R.leavestatus = 'A'", [emp_id])

    @staticmethod
    def get_adj_requests(emp_id, page=1, per_page=10):
        offset = (page - 1) * per_page
        total = DB.fetch_scalar("SELECT COUNT(*) FROM SAL_LeaveAdjustmentRequest_Mst WHERE fk_reqempid = ? AND ISNULL(IsCancel, 0) = 0", [emp_id])
        query = f"SELECT M.pk_leaveadjreqid as RequestID, L.leavetype as LeaveType, CONVERT(varchar, M.adjreqdate, 103) as RequestDate, CONVERT(varchar, T.fromdate, 103) as FromDate, CONVERT(varchar, T.todate, 103) as ToDate, M.totaladjleave as Days, CASE WHEN M.leaveadjstatus = 'A' THEN 'Approved' WHEN M.leaveadjstatus = 'R' THEN 'Rejected' ELSE 'Pending' END as Status FROM SAL_LeaveAdjustmentRequest_Mst M INNER JOIN SAL_LeavesTaken_Mst T ON M.fk_leavetakenid = T.pk_leavetakenid INNER JOIN SAL_Leavetype_Mst L ON T.fk_leaveid = L.pk_leaveid WHERE M.fk_reqempid = ? AND ISNULL(M.IsCancel, 0) = 0 ORDER BY M.adjreqdate DESC OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY"
        return DB.fetch_all(query, [emp_id]), total

    @staticmethod
    def get_cancel_requests(emp_id, page=1, per_page=10):
        offset = (page - 1) * per_page
        total = DB.fetch_scalar("SELECT COUNT(*) FROM SAL_LeaveAdjustmentRequest_Mst WHERE fk_reqempid = ? AND IsCancel = 1", [emp_id])
        query = f"SELECT M.pk_leaveadjreqid as RequestID, L.leavetype as LeaveType, CONVERT(varchar, M.adjreqdate, 103) as RequestDate, CONVERT(varchar, T.fromdate, 103) as FromDate, CONVERT(varchar, T.todate, 103) as ToDate, M.totaladjleave as Days, CASE WHEN M.leaveadjstatus = 'A' THEN 'Approved' WHEN M.leaveadjstatus = 'R' THEN 'Rejected' ELSE 'Pending' END as Status FROM SAL_LeaveAdjustmentRequest_Mst M INNER JOIN SAL_LeavesTaken_Mst T ON M.fk_leavetakenid = T.pk_leavetakenid INNER JOIN SAL_Leavetype_Mst L ON T.fk_leaveid = L.pk_leaveid WHERE M.fk_reqempid = ? AND M.IsCancel = 1 ORDER BY M.adjreqdate DESC OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY"
        return DB.fetch_all(query, [emp_id]), total

    @staticmethod
    def get_pending_cancel_approvals(emp_id):
        fy = NavModel.get_current_fin_year()
        query = "SELECT A.pk_leaveadjreqid as adj_id, E.empname, E.empcode, L.leavetype, CONVERT(varchar, A.adjreqdate, 103) as RequestDate, A.totaladjleave as Days, CONVERT(varchar, T.fromdate, 103) as FromDate, CONVERT(varchar, T.todate, 103) as ToDate, T.totalleavedays as totaldays, A.leaveadjstatus, A.remarks, T.contactno, E.pk_empid as requester_empid FROM SAL_LeaveAdjustmentRequest_Mst A INNER JOIN SAL_Employee_Mst E ON A.fk_reqempid = E.pk_empid INNER JOIN SAL_LeavesTaken_Mst T ON A.fk_leavetakenid = T.pk_leavetakenid INNER JOIN SAL_Leavetype_Mst L ON T.fk_leaveid = L.pk_leaveid WHERE A.fk_reportingto = ? AND A.leaveadjstatus = 'S' AND A.IsCancel = 1 AND T.fromdate BETWEEN ? AND ?"
        return DB.fetch_all(query, [emp_id, fy['date1'], fy['date2']])

    @staticmethod
    def take_cancel_action(adj_id, status, user_id, emp_id, comments=""):
        conn = DB.get_connection(); cursor = conn.cursor()
        try:
            exists = DB.fetch_one("SELECT pk_leaveadjreqid FROM SAL_LeaveAdjustmentRequest_Mst WHERE pk_leaveadjreqid = ? AND fk_reportingto = ?", [adj_id, emp_id])
            if not exists: return False
            cursor.execute("UPDATE SAL_LeaveAdjustmentRequest_Mst SET leaveadjstatus = ?, fk_responseby = ?, responsedate = GETDATE(), remarks = ?, fk_updUserID = ?, fk_updDateID = GETDATE() WHERE pk_leaveadjreqid = ?", [status, user_id, comments, user_id, adj_id])
            if status == 'A':
                adj = DB.fetch_one("SELECT fk_leavetakenid, totaladjleave, fk_reqempid FROM SAL_LeaveAdjustmentRequest_Mst WHERE pk_leaveadjreqid = ?", [adj_id])
                taken = DB.fetch_one("SELECT fk_leaveid, leavetaken, fk_leavereqid FROM SAL_LeavesTaken_Mst WHERE pk_leavetakenid = ?", [adj['fk_leavetakenid']])
                cursor.execute("UPDATE SAL_EmployeeLeave_Details SET leaveavailed = leaveavailed - ?, fk_updUserID = ?, fk_updDateID = GETDATE() WHERE fk_empid = ? AND fk_leaveid = ?", [taken['leavetaken'], user_id, adj['fk_reqempid'], taken['fk_leaveid']])
                cursor.execute("DELETE FROM SAL_LeavesTaken_Details WHERE fk_leavetakenid = ?", [adj['fk_leavetakenid']])
                cursor.execute("DELETE FROM SAL_LeavesTaken_Mst WHERE pk_leavetakenid = ?", [adj['fk_leavetakenid']])
                cursor.execute("UPDATE SAL_Leave_Request_Mst SET iscancelled = 'Y', leavestatus = 'C' WHERE pk_leavereqid = ?", [taken['fk_leavereqid']])
            conn.commit(); return True
        except Exception as e: conn.rollback(); raise e

    @staticmethod
    def get_pending_adj_approvals(emp_id):
        fy = NavModel.get_current_fin_year()
        query = "SELECT A.pk_leaveadjreqid as adj_id, E.empname, E.empcode, L.leavetype, CONVERT(varchar, A.adjreqdate, 103) as RequestDate, A.totaladjleave as Days, CONVERT(varchar, T.fromdate, 103) as FromDate, CONVERT(varchar, T.todate, 103) as ToDate FROM SAL_LeaveAdjustmentRequest_Mst A INNER JOIN SAL_Employee_Mst E ON A.fk_reqempid = E.pk_empid INNER JOIN SAL_LeavesTaken_Mst T ON A.fk_leavetakenid = T.pk_leavetakenid INNER JOIN SAL_Leavetype_Mst L ON T.fk_leaveid = L.pk_leaveid WHERE A.fk_reportingto = ? AND A.leaveadjstatus = 'S' AND ISNULL(A.IsCancel, 0) = 0 AND T.fromdate BETWEEN ? AND ?"
        return DB.fetch_all(query, [emp_id, fy['date1'], fy['date2']])

    @staticmethod
    def take_adj_action(adj_id, status, user_id, emp_id, comments=""):
        conn = DB.get_connection(); cursor = conn.cursor()
        try:
            exists = DB.fetch_one("SELECT pk_leaveadjreqid FROM SAL_LeaveAdjustmentRequest_Mst WHERE pk_leaveadjreqid = ? AND fk_reportingto = ?", [adj_id, emp_id])
            if not exists: return False
            cursor.execute("UPDATE SAL_LeaveAdjustmentRequest_Mst SET leaveadjstatus = ?, fk_responseby = ?, responsedate = GETDATE(), remarks = ?, fk_updUserID = ?, fk_updDateID = GETDATE() WHERE pk_leaveadjreqid = ?", [status, user_id, comments, user_id, adj_id])
            if status == 'A':
                adj = DB.fetch_one("SELECT fk_leavetakenid, totaladjleave, fk_reqempid FROM SAL_LeaveAdjustmentRequest_Mst WHERE pk_leaveadjreqid = ?", [adj_id])
                taken = DB.fetch_one("SELECT fk_leaveid, totalleavedays FROM SAL_LeavesTaken_Mst WHERE pk_leavetakenid = ?", [adj['fk_leavetakenid']])
                diff = float(adj['totaladjleave']) - float(taken['totalleavedays']); fy = NavModel.get_current_fin_year()
                cursor.execute("UPDATE SAL_LeaveAssignment_Details SET leaveavailed = ISNULL(leaveavailed, 0) + ?, fk_updUserID = ?, fk_updDateID = GETDATE() WHERE fk_empid = ? AND fk_leaveid = ? AND fk_yearid = ?", [diff, user_id, adj['fk_reqempid'], taken['fk_leaveid'], fy['Lyear']])
                cursor.execute("UPDATE SAL_LeavesTaken_Mst SET totalleavedays = ?, leavetaken = ?, fk_updUserID = ?, fk_updDateID = GETDATE() WHERE pk_leavetakenid = ?", [adj['totaladjleave'], adj['totaladjleave'], user_id, adj['fk_leavetakenid']])
            conn.commit(); return True
        except Exception as e: conn.rollback(); raise e

    @staticmethod
    def get_adj_approval_history(emp_id, page=1, per_page=10):
        offset = (page - 1) * per_page
        total = DB.fetch_scalar("SELECT COUNT(*) FROM SAL_LeaveAdjustmentRequest_Mst WHERE fk_reportingto = ? AND leaveadjstatus IN ('A','R') AND ISNULL(IsCancel, 0) = 0", [emp_id])
        query = f"SELECT A.*, E.empname, L.leavetype, CONVERT(varchar, A.adjreqdate, 103) as adjreqdate_fmt, CONVERT(varchar, A.responsedate, 103) as responsedate_fmt FROM SAL_LeaveAdjustmentRequest_Mst A INNER JOIN SAL_Employee_Mst E ON A.fk_reqempid = E.pk_empid INNER JOIN SAL_LeavesTaken_Mst T ON A.fk_leavetakenid = T.pk_leavetakenid INNER JOIN SAL_Leavetype_Mst L ON T.fk_leaveid = L.pk_leaveid WHERE A.fk_reportingto = ? AND A.leaveadjstatus IN ('A','R') AND ISNULL(A.IsCancel, 0) = 0 ORDER BY A.responsedate DESC OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY"
        return DB.fetch_all(query, [emp_id]), total

    @staticmethod
    def get_cancel_approval_history(emp_id, page=1, per_page=10):
        offset = (page - 1) * per_page
        total = DB.fetch_scalar("SELECT COUNT(*) FROM SAL_LeaveAdjustmentRequest_Mst WHERE fk_reportingto = ? AND leaveadjstatus IN ('A','R') AND IsCancel = 1", [emp_id])
        query = f"SELECT A.*, E.empname, L.leavetype, CONVERT(varchar, A.adjreqdate, 103) as adjreqdate_fmt, CONVERT(varchar, A.responsedate, 103) as responsedate_fmt FROM SAL_LeaveAdjustmentRequest_Mst A INNER JOIN SAL_Employee_Mst E ON A.fk_reqempid = E.pk_empid INNER JOIN SAL_LeavesTaken_Mst T ON A.fk_leavetakenid = T.pk_leavetakenid INNER JOIN SAL_Leavetype_Mst L ON T.fk_leaveid = L.pk_leaveid WHERE A.fk_reportingto = ? AND A.leaveadjstatus IN ('A','R') AND A.IsCancel = 1 ORDER BY A.responsedate DESC OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY"
        return DB.fetch_all(query, [emp_id]), total

    @staticmethod
    def get_approved_leaves_pending_joining(emp_id):
        query = "SELECT R.pk_leavereqid as RequestID, L.leavetype as LeaveType, CONVERT(varchar, R.fromdate, 103) as FromDate, CONVERT(varchar, R.todate, 103) as ToDate, R.totalleavedays as Days, R.reasonforleave as Reason FROM SAL_Leave_Request_Mst R INNER JOIN SAL_Leavetype_Mst L ON R.fk_leaveid = L.pk_leaveid WHERE R.fk_reqempid = ? AND R.leavestatus = 'A' AND R.JoiningDate IS NULL AND R.iscancelled = 'N' AND R.fk_leaveid = 2 ORDER BY R.fromdate DESC"
        return DB.fetch_all(query, [emp_id])

    @staticmethod
    def submit_joining_date(req_id, joining_date, joining_remark, user_id):
        return DB.execute("UPDATE SAL_Leave_Request_Mst SET JoiningDate = ?, JoiningRemark = ?, fk_updUserID = ?, responsedate = GETDATE() WHERE pk_leavereqid = ?", [joining_date, joining_remark, user_id, req_id])

    @staticmethod
    def get_joining_history(emp_id, page=1, per_page=10):
        offset = (page - 1) * per_page
        total = DB.fetch_scalar("SELECT COUNT(*) FROM SAL_Leave_Request_Mst WHERE fk_reqempid = ? AND JoiningDate IS NOT NULL", [emp_id])
        query = f"SELECT pk_leavereqid as RequestID, CONVERT(varchar, fromdate, 103) as FromDate, CONVERT(varchar, todate, 103) as ToDate, totalleavedays as Days, CONVERT(varchar, JoiningDate, 103) as JoinedOn, JoiningRemark FROM SAL_Leave_Request_Mst WHERE fk_reqempid = ? AND JoiningDate IS NOT NULL ORDER BY JoiningDate DESC OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY"
        data = DB.fetch_all(query, [emp_id])
        for d in data: d['JoiningDate_fmt'] = d['JoinedOn']
        return data, total

    @staticmethod
    def get_ro_joining_status(ro_emp_id, page=1, per_page=10):
        offset = (page - 1) * per_page; excluded = ("'Casual Leave'", "'Restricted Holiday'", "'Station Leave'", "'Duty Leave'")
        fy = NavModel.get_current_fin_year()
        d1, d2 = fy['date1'], fy['date2']
        where_clause = f"R.fk_reportingto = ? AND R.leavestatus = 'A' AND L.leavetype NOT IN ({','.join(excluded)}) AND R.fromdate BETWEEN ? AND ?"
        total = DB.fetch_scalar(f"SELECT COUNT(*) FROM SAL_Leave_Request_Mst R INNER JOIN SAL_Leavetype_Mst L ON R.fk_leaveid = L.pk_leaveid WHERE {where_clause}", [ro_emp_id, d1, d2])
        query = f"SELECT E.empname as EmployeeName, L.leavetype as LeaveType, CONVERT(varchar, R.reqdate, 103) as RequestedDate, CONVERT(varchar, R.fromdate, 103) as FromDate, CONVERT(varchar, R.todate, 103) as ToDate, R.totalleavedays, R.contactno, CONVERT(varchar, R.JoiningDate, 103) as JoiningDate, R.JoiningRemark FROM SAL_Leave_Request_Mst R INNER JOIN SAL_Employee_Mst E ON R.fk_reqempid = E.pk_empid INNER JOIN SAL_Leavetype_Mst L ON R.fk_leaveid = L.pk_leaveid WHERE {where_clause} ORDER BY R.fromdate DESC OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY"
        return DB.fetch_all(query, [ro_emp_id, d1, d2]), total

    @staticmethod
    def get_approved_leaves_pending_departure(emp_id):
        query = "SELECT R.pk_leavereqid as RequestID, L.leavetype as LeaveType, CONVERT(varchar, R.fromdate, 103) as FromDate, CONVERT(varchar, R.todate, 103) as ToDate, R.totalleavedays as Days, R.reasonforleave as Reason FROM SAL_Leave_Request_Mst R INNER JOIN SAL_Leavetype_Mst L ON R.fk_leaveid = L.pk_leaveid WHERE R.fk_reqempid = ? AND R.leavestatus = 'A' AND R.DepartureDate IS NULL AND R.iscancelled = 'N' AND R.fk_leaveid = 2 ORDER BY R.fromdate DESC"
        return DB.fetch_all(query, [emp_id])

    @staticmethod
    def submit_departure_date(req_id, departure_date, departure_remark, user_id):
        return DB.execute("UPDATE SAL_Leave_Request_Mst SET DepartureDate = ?, DepartureRemarks = ?, fk_updUserID = ?, responsedate = GETDATE() WHERE pk_leavereqid = ?", [departure_date, departure_remark, user_id, req_id])

    @staticmethod
    def get_departure_history(emp_id, page=1, per_page=10):
        offset = (page - 1) * per_page
        total = DB.fetch_scalar("SELECT COUNT(*) FROM SAL_Leave_Request_Mst WHERE fk_reqempid = ? AND DepartureDate IS NOT NULL AND fk_leaveid = 2", [emp_id])
        query = f"SELECT R.pk_leavereqid as RequestID, L.leavetype as LeaveType, E.empname as EmployeeName, R.totalleavedays, R.contactno, CONVERT(varchar, R.reqdate, 103) as RequestedDate, CONVERT(varchar, R.fromdate, 103) as FromDate, CONVERT(varchar, R.todate, 103) as ToDate, CONVERT(varchar, R.DepartureDate, 103) as DepartureOn, R.DepartureRemarks FROM SAL_Leave_Request_Mst R INNER JOIN SAL_Leavetype_Mst L ON R.fk_leaveid = L.pk_leaveid INNER JOIN SAL_Employee_Mst E ON R.fk_reqempid = E.pk_empid WHERE R.fk_reqempid = ? AND R.DepartureDate IS NOT NULL AND R.fk_leaveid = 2 ORDER BY R.DepartureDate DESC OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY"
        return DB.fetch_all(query, [emp_id]), total

    @staticmethod
    def get_ro_departure_list(ro_emp_id, page=1, per_page=10):
        offset = (page - 1) * per_page; excluded = ("'Casual Leave'", "'Restricted Holiday'", "'Station Leave'", "'Duty Leave'")
        fy = NavModel.get_current_fin_year()
        d1, d2 = fy['date1'], fy['date2']
        where_clause = f"R.fk_reportingto = ? AND R.leavestatus = 'A' AND L.leavetype NOT IN ({','.join(excluded)}) AND R.fromdate BETWEEN ? AND ?"
        total = DB.fetch_scalar(f"SELECT COUNT(*) FROM SAL_Leave_Request_Mst R INNER JOIN SAL_Leavetype_Mst L ON R.fk_leaveid = L.pk_leaveid WHERE {where_clause}", [ro_emp_id, d1, d2])
        query = f"SELECT R.pk_leavereqid as RequestID, E.empname as EmployeeName, L.leavetype as LeaveType, CONVERT(varchar, R.reqdate, 103) as RequestedDate, CONVERT(varchar, R.fromdate, 103) as FromDate, CONVERT(varchar, R.todate, 103) as ToDate, R.totalleavedays, R.contactno, R.leavestatus FROM SAL_Leave_Request_Mst R INNER JOIN SAL_Employee_Mst E ON R.fk_reqempid = E.pk_empid INNER JOIN SAL_Leavetype_Mst L ON R.fk_leaveid = L.pk_leaveid WHERE {where_clause} ORDER BY R.fromdate DESC OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY"
        return DB.fetch_all(query, [ro_emp_id, d1, d2]), total

    @staticmethod
    def get_leaves_taken(emp_id, page=1, per_page=10):
        offset = (page - 1) * per_page
        total = DB.fetch_scalar("SELECT COUNT(*) FROM SAL_LeavesTaken_Mst WHERE fk_empid = ?", [emp_id])
        query = f"""
            SELECT T.pk_leavetakenid, L.leavetype, 
            CONVERT(varchar, T.fromdate, 103) as FromDate,
            CONVERT(varchar, T.todate, 103) as ToDate,
            CONVERT(varchar, GETDATE(), 103) as RequestDate,
            T.totalleavedays as Days
            FROM SAL_LeavesTaken_Mst T
            INNER JOIN SAL_Leavetype_Mst L ON T.fk_leaveid = L.pk_leaveid
            WHERE T.fk_empid = ?
            ORDER BY T.fromdate DESC
            OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY
        """
        return DB.fetch_all(query, [emp_id]), total

    @staticmethod
    def get_leaves_taken_for_adj(emp_id):
        return DB.fetch_all("SELECT T.*, L.leavetype FROM SAL_LeavesTaken_Mst T INNER JOIN SAL_Leavetype_Mst L ON T.fk_leaveid = L.pk_leaveid WHERE T.fk_empid = ?", [emp_id])

    @staticmethod
    def get_leave_daywise_details_by_taken_id(taken_id):
        res = DB.fetch_all("SELECT CONVERT(varchar, D.dated, 103) as leavedate, DATENAME(dw, D.dated) as day_name, L.leavetype as LeaveType FROM SAL_LeavesTaken_Details D INNER JOIN SAL_LeavesTaken_Mst T ON D.fk_leavetakenid = T.pk_leavetakenid INNER JOIN SAL_Leavetype_Mst L ON T.fk_leaveid = L.pk_leaveid WHERE D.fk_leavetakenid = ?", [taken_id])
        if not res: res = DB.fetch_all("SELECT CONVERT(varchar, D.leavedate, 103) as leavedate, DATENAME(dw, D.leavedate) as day_name, L.leavetype as LeaveType FROM SAL_Leave_Request_Dtls D INNER JOIN SAL_LeavesTaken_Mst T ON D.fk_leavereqid = T.fk_leavereqid INNER JOIN SAL_Leavetype_Mst L ON T.fk_leaveid = L.pk_leaveid WHERE T.pk_leavetakenid = ?", [taken_id])
        return res
