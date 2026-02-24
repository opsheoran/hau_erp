from app.db import DB
from datetime import datetime

class AuthModel:
    @staticmethod
    def authenticate(username, password):
        """Authenticates user and returns details including photo"""
        query = """
        SELECT U.*, R.rolename, E.fk_locid as DefaultLocID, E.empname, E.empcode, E.pk_empid,
        (SELECT TOP 1 filename FROM SAL_EmployeeDocument_Details WHERE fk_empid = E.pk_empid AND fk_doccatid = 1) as photo
        FROM UM_Users_Mst U
        LEFT JOIN UM_Role_Mst R ON U.fk_roleId = R.pk_roleId
        LEFT JOIN SAL_Employee_Mst E ON U.fk_empId = E.pk_empid
        WHERE U.loginname = ? AND U.Plain_text = ? AND U.active = 1
        """
        return DB.fetch_one(query, [username, password])

    @staticmethod
    def log_login(user_id, ip_address):
        """Logs user login attempt"""
        query = "INSERT INTO UM_UserLoginLog (fk_userid, logintime, UserIP) VALUES (?, GETDATE(), ?)"
        DB.execute(query, [user_id, ip_address])
