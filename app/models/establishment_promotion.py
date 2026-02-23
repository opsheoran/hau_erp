from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from app.db import DB


def _parse_date(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    s = str(value).strip()
    if not s:
        return None

    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except Exception:
            pass
    return None


class AppointingAuthorityModel:
    TABLE = "SAL_Appointing_Authority"
    _cols_cache: Optional[set] = None

    @staticmethod
    def _cols() -> set:
        if AppointingAuthorityModel._cols_cache is not None:
            return AppointingAuthorityModel._cols_cache
        try:
            rows = DB.fetch_all(
                "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = ?",
                [AppointingAuthorityModel.TABLE],
            )
            AppointingAuthorityModel._cols_cache = {str(r["COLUMN_NAME"]).lower() for r in rows}
        except Exception:
            AppointingAuthorityModel._cols_cache = set()
        return AppointingAuthorityModel._cols_cache

    @staticmethod
    def _pk_col() -> str:
        cols = AppointingAuthorityModel._cols()
        # Common live column name
        if "pk_authid" in cols:
            return "Pk_AuthId"
        # Fallback
        return "Pk_AuthId"

    @staticmethod
    def _audit_fields(user_id: Any, mode: str) -> Dict[str, Any]:
        cols = AppointingAuthorityModel._cols()
        fields: Dict[str, Any] = {}

        if mode == "insert":
            if "fk_insuserid" in cols:
                fields["fk_insUserID"] = user_id
            if "fk_insdateid" in cols:
                fields["fk_insDateID"] = "GETDATE()"
            if "insertuserid" in cols:
                fields["InsertUserId"] = user_id
            if "insertdate" in cols:
                fields["InsertDate"] = "GETDATE()"

        if "fk_upduserid" in cols:
            fields["fk_updUserID"] = user_id
        if "fk_upddateid" in cols:
            fields["fk_updDateID"] = "GETDATE()"
        if "updateuserid" in cols:
            fields["UpdateUserId"] = user_id
        if "updatedate" in cols:
            fields["UpdateDate"] = "GETDATE()"

        return fields

    @staticmethod
    def _build_insert_sql(fields: Dict[str, Any]) -> Tuple[str, List[Any]]:
        col_names: List[str] = []
        placeholders: List[str] = []
        params: List[Any] = []

        for col, value in fields.items():
            if value is None:
                continue
            col_names.append(f"[{col}]")
            if isinstance(value, str) and value.upper() == "GETDATE()":
                placeholders.append("GETDATE()")
            else:
                placeholders.append("?")
                params.append(value)

        sql = f"INSERT INTO {AppointingAuthorityModel.TABLE} ({', '.join(col_names)}) VALUES ({', '.join(placeholders)})"
        return sql, params

    @staticmethod
    def _build_update_sql(pk_col: str, pk_val: Any, fields: Dict[str, Any]) -> Tuple[str, List[Any]]:
        sets: List[str] = []
        params: List[Any] = []

        for col, value in fields.items():
            if value is None:
                continue
            if isinstance(value, str) and value.upper() == "GETDATE()":
                sets.append(f"[{col}] = GETDATE()")
            else:
                sets.append(f"[{col}] = ?")
                params.append(value)

        sql = f"UPDATE {AppointingAuthorityModel.TABLE} SET {', '.join(sets)} WHERE [{pk_col}] = ?"
        params.append(pk_val)
        return sql, params

    @staticmethod
    def get_by_id(auth_id: Any) -> Optional[Dict[str, Any]]:
        pk = AppointingAuthorityModel._pk_col()
        try:
            return DB.fetch_one(f"SELECT * FROM {AppointingAuthorityModel.TABLE} WHERE [{pk}] = ?", [auth_id])
        except Exception:
            return None

    @staticmethod
    def delete(auth_id: Any) -> None:
        pk = AppointingAuthorityModel._pk_col()
        DB.execute(f"DELETE FROM {AppointingAuthorityModel.TABLE} WHERE [{pk}] = ?", [auth_id])

    @staticmethod
    def list_records(status: Optional[str] = None, limit: int = 200) -> List[Dict[str, Any]]:
        where = ""
        params: List[Any] = []
        if status:
            where = " WHERE A.Status = ?"
            params.append(status)

        top = max(1, min(int(limit or 200), 500))
        pk = AppointingAuthorityModel._pk_col()
        query = f"""
            SELECT TOP {top}
                A.[{pk}] as auth_id,
                A.OrderNo,
                CONVERT(varchar, A.OrderDate, 23) as order_date_fmt,
                A.EmpCode,
                E.empname,
                DS.designation,
                DP.description as dept_name,
                NDP.description as new_dept_name,
                A.Status,
                A.Remarks
            FROM {AppointingAuthorityModel.TABLE} A
            LEFT JOIN SAL_Employee_Mst E ON A.fk_EmpId = E.pk_empid
            LEFT JOIN SAL_Designation_Mst DS ON E.fk_desgid = DS.pk_desgid
            LEFT JOIN Department_Mst DP ON E.fk_deptid = DP.pk_deptid
            LEFT JOIN Department_Mst NDP ON A.NewDepartment = NDP.pk_deptid
            {where}
            ORDER BY A.[{pk}] DESC
        """
        try:
            return DB.fetch_all(query, params)
        except Exception:
            return []

    @staticmethod
    def save(form: Dict[str, Any], user_id: Any) -> None:
        cols = AppointingAuthorityModel._cols()
        pk = AppointingAuthorityModel._pk_col()
        auth_id = str(form.get("auth_id") or "").strip()

        fields: Dict[str, Any] = {}

        if "fk_empid" in cols:
            fields["fk_EmpId"] = form.get("emp_id")
        if "empcode" in cols:
            fields["EmpCode"] = form.get("emp_code")
        if "orderno" in cols:
            fields["OrderNo"] = form.get("order_no")
        if "orderdate" in cols:
            fields["OrderDate"] = _parse_date(form.get("order_date"))
        if "status" in cols:
            fields["Status"] = form.get("status")
        if "remarks" in cols:
            fields["Remarks"] = form.get("remarks")

        mapping_pairs = [
            ("OldControllingOffice", "old_controlling"),
            ("NewControllingOffice", "new_controlling"),
            ("OldDDO", "old_ddo"),
            ("NewDDO", "new_ddo"),
            ("OldDepartment", "old_dept"),
            ("NewDepartment", "new_dept"),
            ("OldSection", "old_section"),
            ("NewSection", "new_section"),
            ("OldDesig", "old_desg"),
            ("NewDesig", "new_desg"),
            ("OldFundType", "old_fund"),
            ("NewFundType", "new_fund"),
            ("OldSchemeGroup", "old_scheme_group"),
            ("NewSchemeGroup", "new_scheme_group"),
            ("OldSchemeCode", "old_scheme_code"),
            ("NewSchemeCode", "new_scheme_code"),
        ]
        for col, key in mapping_pairs:
            if col.lower() in cols:
                fields[col] = form.get(key)

        if auth_id:
            fields.update(AppointingAuthorityModel._audit_fields(user_id, mode="update"))
            sql, params = AppointingAuthorityModel._build_update_sql(pk, auth_id, fields)
            DB.execute(sql, params)
        else:
            fields.update(AppointingAuthorityModel._audit_fields(user_id, mode="insert"))
            sql, params = AppointingAuthorityModel._build_insert_sql(fields)
            DB.execute(sql, params)

    @staticmethod
    def save_reliving(form: Dict[str, Any], user_id: Any) -> None:
        cols = AppointingAuthorityModel._cols()
        fields: Dict[str, Any] = {}

        if "fk_empid" in cols:
            fields["fk_EmpId"] = form.get("emp_id")
        if "empcode" in cols:
            fields["EmpCode"] = form.get("emp_code")
        if "status" in cols:
            fields["Status"] = form.get("status")
        if "relievingdate" in cols:
            fields["RelievingDate"] = _parse_date(form.get("relieving_date"))
        if "remarks" in cols:
            fields["Remarks"] = form.get("remarks")

        mapping_pairs = [
            ("OldControllingOffice", "old_controlling"),
            ("NewControllingOffice", "new_controlling"),
            ("OldDDO", "old_ddo"),
            ("NewDDO", "new_ddo"),
            ("OldDepartment", "old_dept"),
            ("NewDepartment", "new_dept"),
            ("OldSection", "old_section"),
            ("NewSection", "new_section"),
            ("OldDesig", "old_desg"),
            ("NewDesig", "new_desg"),
        ]
        for col, key in mapping_pairs:
            if col.lower() in cols:
                fields[col] = form.get(key)

        fields.update(AppointingAuthorityModel._audit_fields(user_id, mode="insert"))
        sql, params = AppointingAuthorityModel._build_insert_sql(fields)
        DB.execute(sql, params)

    @staticmethod
    def set_approve_date(emp_id: Any, approve_date: Optional[str], user_id: Any) -> int:
        cols = AppointingAuthorityModel._cols()
        if "approvedate" not in cols:
            return 0

        pk = AppointingAuthorityModel._pk_col()
        row = DB.fetch_one(
            f"""
            SELECT TOP 1 [{pk}] as auth_id
            FROM {AppointingAuthorityModel.TABLE}
            WHERE fk_EmpId = ? AND ApproveDate IS NULL
            ORDER BY [{pk}] DESC
            """,
            [emp_id],
        )
        if not row:
            return 0

        fields: Dict[str, Any] = {"ApproveDate": _parse_date(approve_date)}
        fields.update(AppointingAuthorityModel._audit_fields(user_id, mode="update"))
        sql, params = AppointingAuthorityModel._build_update_sql(pk, row["auth_id"], fields)
        return DB.execute(sql, params)


class NonTeachingPromotionModel:
    TABLE_VERIFY = "SAL_NonTeachingPromotionVerification_Mst"
    TABLE_APPROVAL = "sal_emp_NonteachersPromotion_Approval"

    @staticmethod
    def _cols(table: str) -> List[str]:
        try:
            rows = DB.fetch_all(
                "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = ? ORDER BY ORDINAL_POSITION",
                [table],
            )
            return [str(r["COLUMN_NAME"]) for r in rows]
        except Exception:
            return []

    @staticmethod
    def _pk_col(table: str) -> Optional[str]:
        cols = NonTeachingPromotionModel._cols(table)
        for c in cols:
            lc = c.lower()
            if lc.startswith("pk_") or lc.startswith("pk"):
                return c
        return cols[0] if cols else None

    @staticmethod
    def _emp_fk_col(table: str) -> Optional[str]:
        cols = NonTeachingPromotionModel._cols(table)
        for cand in ("fk_empid", "fk_emp_id", "empid", "emp_id"):
            for c in cols:
                if c.lower() == cand:
                    return c
        return None

    @staticmethod
    def _status_col(table: str) -> Optional[str]:
        cols = NonTeachingPromotionModel._cols(table)
        for cand in ("status", "verifystatus", "approvalstatus", "recommendstatus"):
            for c in cols:
                if c.lower() == cand:
                    return c
        return None

    @staticmethod
    def list_verify(status: Optional[str] = None, limit: int = 200) -> List[Dict[str, Any]]:
        table = NonTeachingPromotionModel.TABLE_VERIFY
        pk = NonTeachingPromotionModel._pk_col(table)
        emp_fk = NonTeachingPromotionModel._emp_fk_col(table)
        status_col = NonTeachingPromotionModel._status_col(table)

        where = ""
        params: List[Any] = []
        if status and status_col:
            where = f" WHERE V.[{status_col}] = ?"
            params.append(status)

        top = max(1, min(int(limit or 200), 500))
        order = f" ORDER BY V.[{pk}] DESC" if pk else ""

        join = ""
        select_emp = ""
        if emp_fk:
            join = f" LEFT JOIN SAL_Employee_Mst E ON V.[{emp_fk}] = E.pk_empid LEFT JOIN SAL_Designation_Mst DS ON E.fk_desgid = DS.pk_desgid"
            select_emp = ", E.empcode, E.empname, DS.designation"

        q = f"SELECT TOP {top} V.*{select_emp} FROM {table} V{join}{where}{order}"
        try:
            return DB.fetch_all(q, params)
        except Exception:
            return []

    @staticmethod
    def set_verify_status(row_id: Any, status: str) -> int:
        table = NonTeachingPromotionModel.TABLE_VERIFY
        pk = NonTeachingPromotionModel._pk_col(table)
        status_col = NonTeachingPromotionModel._status_col(table)
        if not pk or not status_col:
            return 0
        return DB.execute(f"UPDATE {table} SET [{status_col}] = ? WHERE [{pk}] = ?", [status, row_id])

    @staticmethod
    def list_approval(status: Optional[str] = None, limit: int = 200) -> List[Dict[str, Any]]:
        table = NonTeachingPromotionModel.TABLE_APPROVAL
        pk = NonTeachingPromotionModel._pk_col(table)
        emp_fk = NonTeachingPromotionModel._emp_fk_col(table)
        status_col = NonTeachingPromotionModel._status_col(table)

        where = ""
        params: List[Any] = []
        if status and status_col:
            where = f" WHERE A.[{status_col}] = ?"
            params.append(status)

        top = max(1, min(int(limit or 200), 500))
        order = f" ORDER BY A.[{pk}] DESC" if pk else ""

        join = ""
        select_emp = ""
        if emp_fk:
            join = f" LEFT JOIN SAL_Employee_Mst E ON A.[{emp_fk}] = E.pk_empid LEFT JOIN SAL_Designation_Mst DS ON E.fk_desgid = DS.pk_desgid"
            select_emp = ", E.empcode, E.empname, DS.designation"

        q = f"SELECT TOP {top} A.*{select_emp} FROM {table} A{join}{where}{order}"
        try:
            return DB.fetch_all(q, params)
        except Exception:
            return []

    @staticmethod
    def set_approval_status(row_id: Any, status: str) -> int:
        table = NonTeachingPromotionModel.TABLE_APPROVAL
        pk = NonTeachingPromotionModel._pk_col(table)
        status_col = NonTeachingPromotionModel._status_col(table)
        if not pk or not status_col:
            return 0
        return DB.execute(f"UPDATE {table} SET [{status_col}] = ? WHERE [{pk}] = ?", [status, row_id])
