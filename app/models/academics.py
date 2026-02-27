from app.db import DB
from datetime import datetime
import os
import base64
import hashlib
import re

try:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.backends import default_backend
except Exception:
    Cipher = None
    algorithms = None
    modes = None
    default_backend = None

class CertificateMasterModel:
    @staticmethod
    def get_certificates(page=1, per_page=10):
        offset = (page - 1) * per_page
        total = DB.fetch_scalar("SELECT COUNT(*) FROM SMS_Certificate_Mst")
        query = f"""
            SELECT pk_certificateid as id, certificatename as name, isrequired 
            FROM SMS_Certificate_Mst 
            ORDER BY certificatename 
            OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY
        """
        return DB.fetch_all(query), total

    @staticmethod
    def save_certificate(data):
        is_req = 1 if data.get('is_required') else 0
        if data.get('pk_id'):
            return DB.execute("UPDATE SMS_Certificate_Mst SET certificatename=?, isrequired=? WHERE pk_certificateid=?",
                            [data['name'], is_req, data['pk_id']])
        return DB.execute("INSERT INTO SMS_Certificate_Mst (certificatename, isrequired) VALUES (?, ?)",
                        [data['name'], is_req])

    @staticmethod
    def delete_certificate(id):
        return DB.execute("DELETE FROM SMS_Certificate_Mst WHERE pk_certificateid = ?", [id])

class BoardMasterModel:
    @staticmethod
    def get_boards(page=1, per_page=10):
        offset = (page - 1) * per_page
        total = DB.fetch_scalar("SELECT COUNT(*) FROM SMS_Board_Mst")
        query = f"""
            SELECT pk_boardid as id, boardname as name, isapproved, orderby 
            FROM SMS_Board_Mst 
            ORDER BY boardname 
            OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY
        """
        return DB.fetch_all(query), total

    @staticmethod
    def save_board(data):
        is_app = 1 if data.get('is_approved') else 0
        if data.get('pk_id'):
            return DB.execute("UPDATE SMS_Board_Mst SET boardname=?, isapproved=?, orderby=? WHERE pk_boardid=?",
                            [data['name'], is_app, data.get('order', 1), data['pk_id']])
        return DB.execute("INSERT INTO SMS_Board_Mst (boardname, isapproved, orderby) VALUES (?, ?, ?)",
                        [data['name'], is_app, data.get('order', 1)])

    @staticmethod
    def delete_board(id):
        return DB.execute("DELETE FROM SMS_Board_Mst WHERE pk_boardid = ?", [id])

class StudentConfigModel:
    @staticmethod
    def get_entitlements(page=1, per_page=10):
        offset = (page - 1) * per_page
        total = DB.fetch_scalar("SELECT COUNT(*) FROM SMS_Entitlement_Mst")
        query = f"""
            SELECT pk_entitleid, Entitlement_Name, orderno 
            FROM SMS_Entitlement_Mst 
            ORDER BY orderno 
            OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY
        """
        return DB.fetch_all(query), total

    @staticmethod
    def save_entitlement(data):
        if data.get('pk_id'):
            return DB.execute("UPDATE SMS_Entitlement_Mst SET Entitlement_Name=?, orderno=? WHERE pk_entitleid=?",
                            [data['name'], data['order'], data['pk_id']])
        else:
            return DB.execute("INSERT INTO SMS_Entitlement_Mst (Entitlement_Name, orderno) VALUES (?, ?)",
                            [data['name'], data['order']])

    @staticmethod
    def get_ranks(page=1, per_page=10):
        offset = (page - 1) * per_page
        total = DB.fetch_scalar("SELECT COUNT(*) FROM SMS_RankMst")
        query = f"""
            SELECT pk_rankid as id, Rankname as name, Remarks 
            FROM SMS_RankMst 
            ORDER BY Rankname 
            OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY
        """
        return DB.fetch_all(query), total

    @staticmethod
    def save_rank(data):
        if data.get('pk_id'):
            return DB.execute("UPDATE SMS_RankMst SET Rankname=?, Remarks=? WHERE pk_rankid=?",
                            [data['name'], data['remarks'], data['pk_id']])
        else:
            return DB.execute("INSERT INTO SMS_RankMst (Rankname, Remarks) VALUES (?, ?)",
                            [data['name'], data['remarks']])

    @staticmethod
    def delete_rank(id):
        return DB.execute("DELETE FROM SMS_RankMst WHERE pk_rankid = ?", [id])

    @staticmethod
    def delete_entitlement(id):
        return DB.execute("DELETE FROM SMS_Entitlement_Mst WHERE pk_entitleid = ?", [id])

class CourseModel:
    @staticmethod
    def get_all_paper_titles():
        return DB.fetch_all("SELECT pk_papertitleid, papertitle FROM SMS_PaperTitle_Mst ORDER BY papertitle")

    @staticmethod
    def get_paper_titles(page=1, per_page=10):
        offset = (page - 1) * per_page
        total = DB.fetch_scalar("SELECT COUNT(*) FROM SMS_PaperTitle_Mst")
        query = f"""
            SELECT pk_papertitleid, papertitle, TitleCode, rptorder 
            FROM SMS_PaperTitle_Mst 
            ORDER BY rptorder 
            OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY
        """
        return DB.fetch_all(query), total

    @staticmethod
    def save_paper_title(data):
        if data.get('pk_id'):
            return DB.execute("UPDATE SMS_PaperTitle_Mst SET papertitle=?, TitleCode=?, rptorder=? WHERE pk_papertitleid=?",
                            [data['name'], data['code'], data['order'], data['pk_id']])
        else:
            return DB.execute("INSERT INTO SMS_PaperTitle_Mst (papertitle, TitleCode, rptorder) VALUES (?, ?, ?)", 
                            [data['name'], data['code'], data['order']])

    @staticmethod
    def delete_paper_title(id):
        return DB.execute("DELETE FROM SMS_PaperTitle_Mst WHERE pk_papertitleid = ?", [id])

    @staticmethod
    def get_courses(filters, page=1, per_page=10):
        offset = (page - 1) * per_page
        where_clause = "WHERE 1=1"
        params = []
        dept_id = filters.get('dept_id')
        if dept_id and str(dept_id).lower() != 'none':
            where_clause += " AND C.fk_Deptid = ?"
            params.append(dept_id)
        
        term = filters.get('term')
        if term and str(term).lower() != 'none':
            where_clause += " AND (C.coursecode LIKE ? OR C.coursename LIKE ?)"
            params.extend([f"%{term}%", f"%{term}%"])
        
        total = DB.fetch_scalar(f"SELECT COUNT(*) FROM SMS_Course_Mst C {where_clause}", params)
        
        query = f"""
            SELECT C.*, D.Departmentname as department, T.coursetype
            FROM SMS_Course_Mst C
            LEFT JOIN SMS_Dept_Mst D ON C.fk_Deptid = D.pk_Deptid
            LEFT JOIN SMS_CourseType_Mst T ON C.fk_coursetypeid = T.pk_coursetypeid
            {where_clause}
            ORDER BY C.reportorder, C.coursecode
            OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY
        """
        return DB.fetch_all(query, params), total

    @staticmethod
    def get_course_details(course_id):
        course = DB.fetch_one("SELECT * FROM SMS_Course_Mst WHERE pk_courseid = ?", [course_id])
        if course:
            mappings = DB.fetch_all("""
                SELECT M.*, S1.sessionname as session_from, S2.sessionname as session_upto, 
                       D.degreename, SEM.semester_roman
                FROM SMS_Course_Mst_Dtl M
                LEFT JOIN SMS_AcademicSession_Mst S1 ON M.fk_sessionid_from = S1.pk_sessionid
                LEFT JOIN SMS_AcademicSession_Mst S2 ON M.fk_sessionid_upto = S2.pk_sessionid
                LEFT JOIN SMS_Degree_Mst D ON M.fk_degreeid = D.pk_degreeid
                LEFT JOIN SMS_Semester_Mst SEM ON M.fk_semesterid = SEM.pk_semesterid
                WHERE M.fk_courseid = ?
            """, [course_id])
            course['mappings'] = mappings
        return course

    @staticmethod
    def get_courses_filtered(filters):
        # filters: degree_id, semester_id, branch_id
        session_id = filters.get('session_id')
        sql = """
            SELECT DISTINCT
                C.pk_courseid,
                C.coursecode,
                C.coursename,
                C.pk_courseid as id,
                C.coursecode + ' - ' + C.coursename as name,
                SEL.sessionname as sessionname
            FROM SMS_Course_Mst C
            INNER JOIN SMS_Course_Mst_Dtl D ON C.pk_courseid = D.fk_courseid
            LEFT JOIN SMS_AcademicSession_Mst SEL ON SEL.pk_sessionid = ?
            LEFT JOIN SMS_AcademicSession_Mst SFrom ON D.fk_sessionid_from = SFrom.pk_sessionid
            LEFT JOIN SMS_AcademicSession_Mst STo ON D.fk_sessionid_upto = STo.pk_sessionid
            WHERE D.fk_degreeid = ? AND D.fk_semesterid = ?
              AND (
                    ? IS NULL OR SEL.pk_sessionid IS NULL
                    OR (
                        SEL.sessionorder >= ISNULL(SFrom.sessionorder, SEL.sessionorder)
                        AND SEL.sessionorder <= ISNULL(STo.sessionorder, SEL.sessionorder)
                    )
                  )
        """
        params = [session_id, filters.get('degree_id'), filters.get('semester_id'), session_id]
        # Branch is often optional or all
        return DB.fetch_all(sql, params)

    @staticmethod
    @staticmethod
    def get_all_courses():
        return DB.fetch_all("SELECT pk_courseid, coursecode, coursename, crhr_theory, crhr_practical FROM SMS_Course_Mst ORDER BY coursecode")

    @staticmethod
    def get_syllabus_courses(session_from, session_to, degree_id, semester_id, dept_id=None):
        # Base query joining Detail and Master tables
        sql = """
            SELECT C.pk_courseid, C.coursecode, C.coursename, 
                   C.crhr_theory, C.crhr_practical, 
                   D.iscompuls, D.isactive, DEP.Departmentname as dept_name
            FROM SMS_Course_Mst_Dtl D
            INNER JOIN SMS_Course_Mst C ON D.fk_courseid = C.pk_courseid
            LEFT JOIN SMS_Dept_Mst DEP ON C.fk_Deptid = DEP.pk_Deptid
            WHERE D.fk_degreeid = ? AND D.fk_semesterid = ?
        """
        params = [degree_id, semester_id]

        # Filter by Session From (mandatory in UI)
        if session_from and str(session_from) != '0':
            sql += " AND D.fk_sessionid_from = ?"
            params.append(session_from)
        
        # Filter by Session To (optional)
        if session_to and str(session_to) != '0':
            sql += " AND D.fk_sessionid_upto = ?"
            params.append(session_to)

        # Filter by Department (optional)
        if dept_id and str(dept_id) != '0':
            sql += " AND C.fk_Deptid = ?"
            params.append(dept_id)

        sql += " ORDER BY C.coursecode"
        return DB.fetch_all(sql, params)

    @staticmethod
    def get_course_report_data(filters):
        sql = """
            SELECT 
                C.coursecode, C.coursename, 
                C.crhr_theory, C.crhr_practical,
                (C.crhr_theory + C.crhr_practical) as total_crhr,
                CASE WHEN D.iscompuls = 1 THEN 'Yes' ELSE 'No' END as compulsory,
                CASE WHEN D.isactive = 1 THEN 'Active' ELSE 'Inactive' END as status,
                S1.sessionname as session_from,
                S2.sessionname as session_upto,
                DEG.degreename,
                SEM.semester_roman,
                CT.coursetype,
                DEPT.Departmentname as dept_name
            FROM SMS_Course_Mst_Dtl D
            INNER JOIN SMS_Course_Mst C ON D.fk_courseid = C.pk_courseid
            LEFT JOIN SMS_AcademicSession_Mst S1 ON D.fk_sessionid_from = S1.pk_sessionid
            LEFT JOIN SMS_AcademicSession_Mst S2 ON D.fk_sessionid_upto = S2.pk_sessionid
            LEFT JOIN SMS_Degree_Mst DEG ON D.fk_degreeid = DEG.pk_degreeid
            LEFT JOIN SMS_Semester_Mst SEM ON D.fk_semesterid = SEM.pk_semesterid
            LEFT JOIN SMS_CourseType_Mst CT ON C.fk_coursetypeid = CT.pk_coursetypeid
            LEFT JOIN SMS_Dept_Mst DEPT ON C.fk_Deptid = DEPT.pk_Deptid
            WHERE 1=1
        """
        params = []
        
        if filters.get('session_from') and str(filters['session_from']) != '0':
            sql += " AND D.fk_sessionid_from = ?"
            params.append(filters['session_from'])
            
        if filters.get('session_upto') and str(filters['session_upto']) != '0':
            sql += " AND D.fk_sessionid_upto = ?"
            params.append(filters['session_upto'])
            
        if filters.get('degree_id') and str(filters['degree_id']) != '0':
            sql += " AND D.fk_degreeid = ?"
            params.append(filters['degree_id'])

        if filters.get('dept_id') and str(filters['dept_id']) != '0':
            sql += " AND C.fk_Deptid = ?"
            params.append(filters['dept_id'])
            
        if filters.get('semester_id') and str(filters['semester_id']) != '0':
            sql += " AND D.fk_semesterid = ?"
            params.append(filters['semester_id'])
            
        if filters.get('year_id') and str(filters['year_id']) != '0':
            sql += " AND SEM.fk_degreeyearid = ?"
            params.append(filters['year_id'])

        sql += " ORDER BY DEG.degreename, SEM.semester_roman, C.coursecode"
        return DB.fetch_all(sql, params)

    @staticmethod
    def save_course(data, user_id):
        conn = DB.get_connection()
        cursor = conn.cursor()
        try:
            # 1. Save Master
            cols = ['coursecode', 'coursename', 'fk_Deptid', 'fk_papertitleid', 'fk_coursetypeid', 
                    'crhr_theory', 'crhr_practical', 'reportorder', 'isobsolete', 'isNC', 'isinternship', 
                    'isgrade', 'iselective', 'iscrhrbased', 'isThesis', 'IsResearch', 'IsSpecial',
                    'Isdeficiency', 'IsCompulsory', 'IsNcCompulsory', 'Isgrace', 'IsSeminar']
            
            vals = [data['coursecode'], data['coursename'], 
                    data.get('dept_id') if data.get('dept_id') and str(data.get('dept_id')) != '0' else None, 
                    data.get('paper_title_id') if data.get('paper_title_id') and str(data.get('paper_title_id')) != '0' else None,
                    data.get('course_type_id') if data.get('course_type_id') and str(data.get('course_type_id')) != '0' else None, 
                    data.get('crhr_theory', 0), data.get('crhr_practical', 0),
                    data.get('report_order', 1),
                    1 if data.get('is_obsolete') else 0,
                    1 if data.get('is_nc') else 0, 1 if data.get('is_internship') else 0,
                    1 if data.get('is_grade') else 0, 1 if data.get('is_elective') else 0,
                    1 if data.get('is_crhr_based') else 0, 1 if data.get('is_thesis') else 0,
                    1 if data.get('is_research') else 0, 1 if data.get('is_special') else 0,
                    1 if data.get('is_deficiency') else 0, 1 if data.get('is_compulsory') else 0,
                    1 if data.get('is_nc_compulsory') else 0, 1 if data.get('is_grace') else 0,
                    1 if data.get('is_seminar') else 0]

            if data.get('pk_id'):
                cid = data['pk_id']
                set_clause = ", ".join([f"{c}=?" for c in cols])
                cursor.execute(f"UPDATE SMS_Course_Mst SET {set_clause}, UpdatedBy=?, UpdatedDate=GETDATE() WHERE pk_courseid=?", 
                             vals + [user_id, cid])
                cursor.execute("DELETE FROM SMS_Course_Mst_Dtl WHERE fk_courseid=?", [cid])
            else:
                col_names = ", ".join(cols)
                placeholders = ", ".join(["?"] * len(cols))
                cursor.execute(f"INSERT INTO SMS_Course_Mst ({col_names}, InsertedBy, InsertedDate) OUTPUT INSERTED.pk_courseid VALUES ({placeholders}, ?, GETDATE())", 
                             vals + [user_id])
                cid = cursor.fetchone()[0]

            # 2. Save Mappings
            sess_from = data.getlist('map_sess_from[]')
            sess_upto = data.getlist('map_sess_upto[]')
            degrees = data.getlist('map_degree[]')
            branches = data.getlist('map_branch[]')
            semesters = data.getlist('map_sem[]')
            ogpas = data.getlist('map_ogpa[]')
            actives = data.getlist('map_active[]')
            compuls = data.getlist('map_compuls[]')

            for i in range(len(degrees)):
                if degrees[i] and str(degrees[i]).isdigit():
                    cursor.execute("""
                        INSERT INTO SMS_Course_Mst_Dtl (fk_courseid, fk_sessionid_from, fk_sessionid_upto, 
                                                       fk_degreeid, fk_branchid, fk_semesterid, OGPA, isactive, iscompuls)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, [cid, sess_from[i] if sess_from[i] and str(sess_from[i]) != '0' else None, 
                          sess_upto[i] if sess_upto[i] and str(sess_upto[i]) != '0' else None,
                          degrees[i], 
                          branches[i] if branches[i] and str(branches[i]) != '0' else None, 
                          semesters[i] if semesters[i] and str(semesters[i]) != '0' else None, 
                          ogpas[i] if ogpas[i] else 0,
                          1 if actives[i] == '1' else 0,
                          1 if compuls[i] == '1' else 0])
            
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def delete_course(id):
        conn = DB.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM SMS_Course_Mst_Dtl WHERE fk_courseid = ?", [id])
            cursor.execute("DELETE FROM SMS_Course_Mst WHERE pk_courseid = ?", [id])
            conn.commit()
            return True
        except:
            conn.rollback()
            return False
        finally:
            conn.close()

class ActivityCertificateModel:
    @staticmethod
    def get_activities():
        return DB.fetch_all("SELECT PK_Actid as id, Activity_name as name, Remarks FROM SMS_Activity_Mst ORDER BY Activity_name")

    @staticmethod
    def get_activities_paginated(page=1, per_page=10):
        offset = (page - 1) * per_page
        total = DB.fetch_scalar("SELECT COUNT(*) FROM SMS_Activity_Mst")
        query = f"""
            SELECT PK_Actid as id, Activity_name as name, Remarks 
            FROM SMS_Activity_Mst 
            ORDER BY Activity_name 
            OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY
        """
        return DB.fetch_all(query), total

    @staticmethod
    def save_activity(data):
        if data.get('pk_id'):
            return DB.execute("UPDATE SMS_Activity_Mst SET Activity_name=?, Remarks=? WHERE PK_Actid=?",
                            [data['name'], data['remarks'], data['pk_id']])
        else:
            return DB.execute("INSERT INTO SMS_Activity_Mst (Activity_name, Remarks) VALUES (?, ?)",
                            [data['name'], data['remarks']])

    @staticmethod
    def delete_activity(id):
        return DB.execute("DELETE FROM SMS_Activity_Mst WHERE PK_Actid = ?", [id])

class CourseActivityModel:
    @staticmethod
    def get_course_activities(page=1, per_page=10):
        offset = (page - 1) * per_page
        total = DB.fetch_scalar("SELECT COUNT(*) FROM SMS_CourseActivity_Mst")
        query = f"""
            SELECT M.*, S.sessionname, SEM.semester_roman
            FROM SMS_CourseActivity_Mst M
            LEFT JOIN SMS_AcademicSession_Mst S ON M.sessionid = S.pk_sessionid
            LEFT JOIN SMS_Semester_Mst SEM ON M.semesterid = SEM.pk_semesterid
            ORDER BY M.pk_CourseActivityID
            OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY
        """
        return DB.fetch_all(query), total

    @staticmethod
    def get_course_activity_details(ca_id):
        master = DB.fetch_one("SELECT * FROM SMS_CourseActivity_Mst WHERE pk_CourseActivityID = ?", [ca_id])
        if master:
            details = DB.fetch_all("""
                SELECT D.*, A.Activity_name
                FROM SMS_CourseActivity_Dtl D
                LEFT JOIN SMS_Activity_Mst A ON D.fk_activityid = A.PK_Actid
                WHERE D.fk_CourseActivityID = ?
            """, [ca_id])
            master['details'] = details
        return master

    @staticmethod
    def save_course_activity(data):
        conn = DB.get_connection()
        cursor = conn.cursor()
        try:
            code = data['code']
            name = data['name']
            sess_id = data['session_id']
            sem_id = data['sem_id']
            order = data.get('order', 1)
            a_type = data.get('type', 'A')

            if data.get('pk_id'):
                ca_id = data['pk_id']
                cursor.execute("""
                    UPDATE SMS_CourseActivity_Mst SET CourseActivity_Code=?, CourseActivity_Name=?, 
                    sessionid=?, semesterid=?, CourseActivity_Order=?, Activity_type=?
                    WHERE pk_CourseActivityID=?
                """, [code, name, sess_id, sem_id, order, a_type, ca_id])
                cursor.execute("DELETE FROM SMS_CourseActivity_Dtl WHERE fk_CourseActivityID=?", [ca_id])
            else:
                cursor.execute("""
                    INSERT INTO SMS_CourseActivity_Mst (CourseActivity_Code, CourseActivity_Name, 
                    sessionid, semesterid, CourseActivity_Order, Activity_type)
                    OUTPUT INSERTED.pk_CourseActivityID
                    VALUES (?, ?, ?, ?, ?, ?)
                """, [code, name, sess_id, sem_id, order, a_type])
                ca_id = cursor.fetchone()[0]

            act_ids = data.getlist('act_ids[]')
            c_names = data.getlist('c_names[]')
            c_codes = data.getlist('c_codes[]')
            c_orders = data.getlist('c_orders[]')
            caps = data.getlist('caps[]')

            for i in range(len(act_ids)):
                if act_ids[i]:
                    cursor.execute("""
                        INSERT INTO SMS_CourseActivity_Dtl (fk_CourseActivityID, CourseCode, CourseName, 
                                                           CourseOrder, capacity, fk_activityid)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, [ca_id, c_codes[i], c_names[i], c_orders[i], caps[i], act_ids[i]])
            
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def delete_course_activity(ca_id):
        conn = DB.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM SMS_CourseActivity_Dtl WHERE fk_CourseActivityID=?", [ca_id])
            cursor.execute("DELETE FROM SMS_CourseActivity_Mst WHERE pk_CourseActivityID=?", [ca_id])
            conn.commit()
            return True
        except:
            conn.rollback()
            return False
        finally:
            conn.close()
    @staticmethod
    def get_activities():
        return DB.fetch_all("SELECT PK_Actid as id, Activity_name as name, Remarks FROM SMS_Activity_Mst ORDER BY Activity_name")

    @staticmethod
    def save_activity(data):
        if data.get('pk_id'):
            return DB.execute("UPDATE SMS_Activity_Mst SET Activity_name=?, Remarks=? WHERE PK_Actid=?",
                            [data['name'], data['remarks'], data['pk_id']])
        else:
            return DB.execute("INSERT INTO SMS_Activity_Mst (Activity_name, Remarks) VALUES (?, ?)",
                            [data['name'], data['remarks']])

    @staticmethod
    def delete_activity(id):
        return DB.execute("DELETE FROM SMS_Activity_Mst WHERE PK_Actid = ?", [id])

class ClassificationModel:
    @staticmethod
    def get_college_types():
        return DB.fetch_all("SELECT pk_collegetypeid as id, collegypedesc as name, * FROM SMS_CollegeTpye_Mst ORDER BY collegypedesc")

    @staticmethod
    def get_college_types_paginated(page=1, per_page=10):
        offset = (page - 1) * per_page
        total = DB.fetch_scalar("SELECT COUNT(*) FROM SMS_CollegeTpye_Mst")
        query = f"""
            SELECT pk_collegetypeid as id, collegypedesc as name, * FROM SMS_CollegeTpye_Mst 
            ORDER BY collegypedesc 
            OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY
        """
        return DB.fetch_all(query), total

    @staticmethod
    def save_college_type(data):
        if data.get('pk_id'):
            return DB.execute("UPDATE SMS_CollegeTpye_Mst SET collegypedesc=?, Remarks=? WHERE pk_collegetypeid=?",
                            [data['name'], data['remarks'], data['pk_id']])
        else:
            return DB.execute("INSERT INTO SMS_CollegeTpye_Mst (collegypedesc, Remarks) VALUES (?, ?)",
                            [data['name'], data['remarks']])

    @staticmethod
    def delete_college_type(id):
        return DB.execute("DELETE FROM SMS_CollegeTpye_Mst WHERE pk_collegetypeid = ?", [id])

    @staticmethod
    def get_degree_types():
        return DB.fetch_all("SELECT pk_degreetypeid as id, degreetype as name, * FROM SMS_DegreeType_Mst ORDER BY degreetype")

    @staticmethod
    def get_degree_types_paginated(page=1, per_page=10):
        offset = (page - 1) * per_page
        total = DB.fetch_scalar("SELECT COUNT(*) FROM SMS_DegreeType_Mst")
        query = f"""
            SELECT pk_degreetypeid as id, degreetype as name, * FROM SMS_DegreeType_Mst
            ORDER BY degreetype
            OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY
        """
        return DB.fetch_all(query), total

    @staticmethod
    def save_degree_type(data):
        if data.get('pk_id'):
            return DB.execute("UPDATE SMS_DegreeType_Mst SET degreetype=?, isug=?, Prefix=? WHERE pk_degreetypeid=?",
                            [data['name'], data['symbol'], data.get('prefix'), data['pk_id']])
        else:
            return DB.execute("INSERT INTO SMS_DegreeType_Mst (degreetype, isug, Prefix) VALUES (?, ?, ?)",
                            [data['name'], data['symbol'], data.get('prefix')])

    @staticmethod
    def delete_degree_type(id):
        return DB.execute("DELETE FROM SMS_DegreeType_Mst WHERE pk_degreetypeid = ?", [id])

    @staticmethod
    def get_course_types():
        return DB.fetch_all("SELECT pk_coursetypeid as id, coursetype as name, * FROM SMS_CourseType_Mst ORDER BY coursetype")

    @staticmethod
    def get_course_types_paginated(page=1, per_page=10):
        offset = (page - 1) * per_page
        total = DB.fetch_scalar("SELECT COUNT(*) FROM SMS_CourseType_Mst")
        query = f"""
            SELECT pk_coursetypeid as id, coursetype as name, * FROM SMS_CourseType_Mst
            ORDER BY coursetype
            OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY
        """
        return DB.fetch_all(query), total

    @staticmethod
    def save_course_type(data):
        if data.get('pk_id'):
            return DB.execute("UPDATE SMS_CourseType_Mst SET coursetype=?, coursetypeorderid=? WHERE pk_coursetypeid=?",
                            [data['name'], data.get('order', 1), data['pk_id']])
        else:
            return DB.execute("INSERT INTO SMS_CourseType_Mst (coursetype, coursetypeorderid) VALUES (?, ?)",
                            [data['name'], data.get('order', 1)])

    @staticmethod
    def delete_course_type(id):
        return DB.execute("DELETE FROM SMS_CourseType_Mst WHERE pk_coursetypeid = ?", [id])

    @staticmethod
    def get_nationalities():
        return DB.fetch_all("SELECT pk_nid, nationality as name FROM SMS_Nationality_Mst ORDER BY nationality")

    @staticmethod
    def save_nationality(data):
        if data.get('pk_id'):
            return DB.execute("UPDATE SMS_Nationality_Mst SET nationality=? WHERE pk_nid=?", [data['name'], data['pk_id']])
        return DB.execute("INSERT INTO SMS_Nationality_Mst (nationality) VALUES (?)", [data['name']])

    @staticmethod
    def delete_nationality(id):
        return DB.execute("DELETE FROM SMS_Nationality_Mst WHERE pk_nid = ?", [id])

    @staticmethod
    def get_categories(page=1, per_page=10):
        offset = (page - 1) * per_page
        total = DB.fetch_scalar("SELECT COUNT(*) FROM SAL_Category_Mst")
        query = f"""
            SELECT pk_catid as id, category as name 
            FROM SAL_Category_Mst 
            ORDER BY category 
            OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY
        """
        return DB.fetch_all(query), total

    @staticmethod
    def save_category(data):
        if data.get('pk_id'):
            return DB.execute("UPDATE SAL_Category_Mst SET category=? WHERE pk_catid=?", [data['name'], data['pk_id']])
        return DB.execute("INSERT INTO SAL_Category_Mst (category) VALUES (?)", [data['name']])

    @staticmethod
    def delete_category(id):
        return DB.execute("DELETE FROM SAL_Category_Mst WHERE pk_catid = ?", [id])

class InfrastructureModel:
    @staticmethod
    def get_current_session_id():
        # Returns the session ID where admission is open, or the latest one
        res = DB.fetch_scalar("SELECT pk_sessionid FROM SMS_AcademicSession_Mst WHERE isadmissionopen = 1")
        if not res:
            res = DB.fetch_scalar("SELECT TOP 1 pk_sessionid FROM SMS_AcademicSession_Mst ORDER BY sessionorder DESC")
        return res

    @staticmethod
    def get_sessions():
        # Simple version for dropdowns
        return DB.fetch_all("SELECT pk_sessionid as id, sessionname as name FROM SMS_AcademicSession_Mst ORDER BY sessionorder DESC")

    @staticmethod
    def get_sessions_paginated(page=1, per_page=10):
        offset = (page - 1) * per_page
        total = DB.fetch_scalar("SELECT COUNT(*) FROM SMS_AcademicSession_Mst")
        query = f"""
            SELECT * FROM SMS_AcademicSession_Mst 
            ORDER BY sessionorder DESC
            OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY
        """
        return DB.fetch_all(query), total

    @staticmethod
    def save_session(data):
        is_open = 1 if data.get('open') else 0
        if data.get('pk_sessionid'):
            return DB.execute("""
                UPDATE SMS_AcademicSession_Mst 
                SET sessionname=?, sessionstart_dt=?, sessionend_dt=?, 
                    sessionorder=?, isadmissionopen=?, remarks=? 
                WHERE pk_sessionid=?
            """, [data['name'], data['start'], data['end'], data['order'], is_open, data.get('remarks'), data['pk_sessionid']])
        else:
            return DB.execute("""
                INSERT INTO SMS_AcademicSession_Mst 
                (sessionname, sessionstart_dt, sessionend_dt, sessionorder, isadmissionopen, remarks) 
                VALUES (?, ?, ?, ?, ?, ?)
            """, [data['name'], data['start'], data['end'], data['order'], is_open, data.get('remarks')])

    @staticmethod
    def get_all_semesters():
        # Live system only uses 8 semesters (I to VIII)
        return DB.fetch_all("SELECT pk_semesterid as id, semester_roman as name, * FROM SMS_Semester_Mst WHERE semesterorder <= 8 ORDER BY semesterorder")

    @staticmethod
    def get_extension_semesters():
        # Student Extension UI needs extension semesters (e.g., IX, X) beyond the regular 8.
        return DB.fetch_all("SELECT pk_semesterid as id, semester_roman as name, semesterorder FROM SMS_Semester_Mst WHERE semesterorder > 8 ORDER BY semesterorder")

    @staticmethod
    def get_semesters():
        return DB.fetch_all("SELECT pk_semesterid as id, semester_roman as name, semester_char, semesterorder, * FROM SMS_Semester_Mst WHERE semesterorder <= 8 ORDER BY semesterorder")

    @staticmethod
    def get_semesters_paginated(page=1, per_page=10):
        offset = (page - 1) * per_page
        total = DB.fetch_scalar("SELECT COUNT(*) FROM SMS_Semester_Mst")
        query = f"""
            SELECT S.*, Y.degreeyear_char 
            FROM SMS_Semester_Mst S
            LEFT JOIN SMS_DegreeYear_Mst Y ON S.fk_degreeyearid = Y.pk_degreeyearid
            ORDER BY S.semesterorder 
            OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY
        """
        return DB.fetch_all(query), total

    @staticmethod
    def save_semester(data):
        if data.get('pk_id'):
            return DB.execute("""
                UPDATE SMS_Semester_Mst 
                SET semester_roman=?, semester_char=?, semesterorder=?, fk_degreeyearid=? 
                WHERE pk_semesterid=?
            """, [data['roman'], data['char'], data['order'], data['year_id'], data['pk_id']])
        else:
            return DB.execute("""
                INSERT INTO SMS_Semester_Mst (semester_roman, semester_char, semesterorder, fk_degreeyearid) 
                VALUES (?, ?, ?, ?)
            """, [data['roman'], data['char'], data['order'], data['year_id']])

    @staticmethod
    def delete_semester(id):
        return DB.execute("DELETE FROM SMS_Semester_Mst WHERE pk_semesterid = ?", [id])

    @staticmethod
    def delete_session(id):
        return DB.execute("DELETE FROM SMS_AcademicSession_Mst WHERE pk_sessionid = ?", [id])

class PackageMasterModel:
    @staticmethod
    def get_packages(page=1, per_page=10):
        offset = (page - 1) * per_page
        total = DB.fetch_scalar("SELECT COUNT(*) FROM SMS_CoursePackage_MST")
        query = f"""
            SELECT M.*, D.degreename, SEM.semester_roman
            FROM SMS_CoursePackage_MST M
            LEFT JOIN SMS_Degree_Mst D ON M.fk_degreeid = D.pk_degreeid
            LEFT JOIN SMS_Semester_Mst SEM ON M.fk_semesterid = SEM.pk_semesterid
            ORDER BY M.PackageName
            OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY
        """
        return DB.fetch_all(query), total

    @staticmethod
    def get_package_details(pid):
        master = DB.fetch_one("SELECT * FROM SMS_CoursePackage_MST WHERE pk_packageID = ?", [pid])
        if master:
            details = DB.fetch_all("""
                SELECT D.*, C.coursename, C.coursecode
                FROM SMS_CoursePackage_DTL D
                INNER JOIN SMS_Course_Mst C ON D.fk_courseid = C.pk_courseid
                WHERE D.fk_packageID = ?
            """, [pid])
            master['details'] = details
        return master

    @staticmethod
    def save_package(data):
        conn = DB.get_connection()
        cursor = conn.cursor()
        try:
            name = data['name']
            deg_id = data['degree_id']
            sem_id = data['sem_id']
            sess_from = data.get('session_from')
            sess_to = data.get('session_to')
            is_active = 1 if data.get('is_active') else 0

            if data.get('pk_id'):
                pid = data['pk_id']
                cursor.execute("""
                    UPDATE SMS_CoursePackage_MST SET PackageName=?, fk_degreeid=?, fk_semesterid=?, 
                    fromsession=?, tosession=?, mstcourseactive=?
                    WHERE pk_packageID=?
                """, [name, deg_id, sem_id, sess_from, sess_to, is_active, pid])
                cursor.execute("DELETE FROM SMS_CoursePackage_DTL WHERE fk_packageID=?", [pid])
            else:
                cursor.execute("""
                    INSERT INTO SMS_CoursePackage_MST (PackageName, fk_degreeid, fk_semesterid, fromsession, tosession, mstcourseactive)
                    OUTPUT INSERTED.pk_packageID
                    VALUES (?, ?, ?, ?, ?, ?)
                """, [name, deg_id, sem_id, sess_from, sess_to, is_active])
                pid = cursor.fetchone()[0]

            course_ids = data.getlist('course_ids[]')
            for cid in course_ids:
                if cid:
                    cursor.execute("INSERT INTO SMS_CoursePackage_DTL (fk_packageID, fk_courseid, activecourse) VALUES (?, ?, 1)", [pid, cid])
            
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def delete_package(pid):
        conn = DB.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM SMS_CoursePackage_DTL WHERE fk_packageID=?", [pid])
            cursor.execute("DELETE FROM SMS_CoursePackage_MST WHERE pk_packageID=?", [pid])
            conn.commit()
            return True
        except:
            conn.rollback()
            return False
        finally:
            conn.close()

class AdmissionModel:
    @staticmethod
    def get_certificates(page=1, per_page=10):
        offset = (page - 1) * per_page
        total = DB.fetch_scalar("SELECT COUNT(*) FROM SMS_Certificate_Mst")
        query = f"""
            SELECT * FROM SMS_Certificate_Mst 
            ORDER BY certificatename
            OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY
        """
        return DB.fetch_all(query), total

    @staticmethod
    def save_certificate(data):
        params = [data['name'], 1 if data.get('is_required') else 0]
        if data.get('pk_id'):
            return DB.execute("UPDATE SMS_Certificate_Mst SET certificatename=?, isrequired=? WHERE pk_certificateid=?", params + [data['pk_id']])
        else:
            return DB.execute("INSERT INTO SMS_Certificate_Mst (certificatename, isrequired) VALUES (?, ?)", params)

    @staticmethod
    def get_students_for_admission_no(college_id, session_id, degree_id):
        query = """
            SELECT pk_sid, fullname, AdmissionNo, provisionalno
            FROM SMS_Student_Mst
            WHERE fk_collegeid = ? AND fk_adm_session = ? AND fk_degreeid = ?
            ORDER BY fullname
        """
        return DB.fetch_all(query, [college_id, session_id, degree_id])

    @staticmethod
    def get_admission_config(college_id, degree_id, session_id):
        # Find config matching college, degree and session
        query = """
            SELECT TOP 1 * FROM SMS_AdmissionConfigurations_Mst
            WHERE Fk_collegeid = ? AND Degree = ? 
            AND ? BETWEEN SessionFrom AND ISNULL(SessionTo, SessionFrom)
        """
        return DB.fetch_one(query, [college_id, degree_id, session_id])

    @staticmethod
    def get_students_for_generation(filters):
        sql = """
            SELECT S.pk_sid, S.fullname, S.enrollmentno, S.AdmissionNo, B.Branchname
            FROM SMS_Student_Mst S
            LEFT JOIN SMS_BranchMst B ON S.fk_branchid = B.Pk_BranchId
            WHERE S.fk_collegeid = ? AND S.fk_adm_session = ? AND S.fk_degreeid = ?
        """
        params = [filters['college_id'], filters['session_id'], filters['degree_id']]
        
        if filters.get('branch_id') and str(filters['branch_id']) != '0':
            sql += " AND S.fk_branchid = ?"
            params.append(filters['branch_id'])
            
        sql += " ORDER BY S.fullname"
        return DB.fetch_all(sql, params)

    @staticmethod
    def get_next_serial(college_id, degree_id, session_id, prefix, suffix, separator):
        # Find the highest serial number already used for this pattern
        # Pattern is Prefix + Separator + [3 digits] + Suffix
        # BUT the 'Prefix' column stores Suffix and 'suffix' column stores Prefix in HAU ERP
        pattern = f"{prefix}{separator}%{suffix}"
        sql = "SELECT MAX(AdmissionNo) FROM SMS_Student_Mst WHERE AdmissionNo LIKE ?"
        max_no = DB.fetch_scalar(sql, [pattern])
        
        if not max_no:
            return 1
            
        # Extract the digits from the middle
        # This is tricky because Prefix/Suffix lengths vary.
        # We assume Prefix + Separator is at the start and Suffix is at the end.
        import re
        match = re.search(r'(\d+)', max_no[len(prefix + separator): -len(suffix) if suffix else None])
        if match:
            return int(match.group(1)) + 1
        return 1

    @staticmethod
    def save_admission_no(student_id, admission_no):
        return DB.execute("UPDATE SMS_Student_Mst SET AdmissionNo = ? WHERE pk_sid = ?", [admission_no, student_id])

    @staticmethod
    def get_students_for_degree_completion(filters):
        # Strictly require semester_id to be selected
        if not filters.get('semester_id') or str(filters['semester_id']) == '0':
            return []

        # 1. Get Session Start Year
        session_name = DB.fetch_scalar("SELECT sessionname FROM SMS_AcademicSession_Mst WHERE pk_sessionid = ?", [filters['session_id']])
        if not session_name: return []
        import re
        year_match = re.search(r'(\d{4})', session_name)
        if not year_match: return []
        session_start_year = int(year_match.group(1))

        # 2. Get order of selected semester/class
        target_sem = DB.fetch_one("SELECT semesterorder FROM SMS_Semester_Mst WHERE pk_semesterid = ?", [filters['semester_id']])
        if not target_sem: return []
        sem_order = target_sem['semesterorder']

        # 3. Calculate Target Enrollment Year (Batch Year)
        # Class IV (4) in 2025-26 -> Started in 2024-25.
        # Max Batch Year = SessionYear - floor((SemOrder - 1) / 2)
        max_enroll_year = session_start_year - ((sem_order - 1) // 2)

        sql = """
            SELECT DISTINCT S.pk_sid, S.fullname, S.enrollmentno, S.AdmissionNo
            FROM SMS_Student_Mst S
            WHERE S.fk_collegeid = ? 
              AND S.fk_degreeid = ?
              AND (S.fk_curr_session = ? OR S.fk_adm_session = ?)
              -- BATCH CONSTRAINT: Must be from an eligible year (e.g. 2024 or earlier for Class IV in 2025)
              AND ISNUMERIC(LEFT(S.enrollmentno, 4)) = 1
              AND CAST(LEFT(S.enrollmentno, 4) AS INT) <= ?
              -- EXCLUSIONS
              AND (S.isdgcompleted IS NULL OR S.isdgcompleted = 0)
              AND S.pk_sid NOT IN (SELECT Fk_Sid FROM SMS_StudentDegreeComplete_Dtl)
              AND S.pk_sid NOT IN (SELECT fk_sturegid FROM SMS_RegCancel_Detail WHERE Approved = 1)
            ORDER BY S.enrollmentno
        """
        params = [filters['college_id'], filters['degree_id'], filters['session_id'], filters['session_id'], max_enroll_year]
        return DB.fetch_all(sql, params)

    @staticmethod
    def get_degree_max_sem(degree_id):
        return DB.fetch_scalar("SELECT maxsem FROM SMS_Degree_Mst WHERE pk_degreeid = ?", [degree_id])

    @staticmethod
    def get_all_configs(page=1, per_page=10, loc_id=None):
        offset = (page - 1) * per_page
        
        where_clause = " WHERE 1=1 "
        params = []
        if loc_id:
            where_clause += " AND C.fk_locid = ? "
            params.append(str(loc_id))

        total_sql = "SELECT COUNT(*) FROM SMS_AdmissionConfigurations_Mst A INNER JOIN SMS_College_Mst C ON A.Fk_collegeid = C.pk_collegeid" + where_clause
        total = DB.fetch_scalar(total_sql, params)
        
        query = f"""
            SELECT A.*, C.collegename, D.degreename, S1.sessionname as sess_from, S2.sessionname as sess_to
            FROM SMS_AdmissionConfigurations_Mst A
            INNER JOIN SMS_College_Mst C ON A.Fk_collegeid = C.pk_collegeid
            INNER JOIN SMS_Degree_Mst D ON A.Degree = D.pk_degreeid
            LEFT JOIN SMS_AcademicSession_Mst S1 ON A.SessionFrom = S1.pk_sessionid
            LEFT JOIN SMS_AcademicSession_Mst S2 ON A.SessionTo = S2.pk_sessionid
            {where_clause}
            ORDER BY A.pk_AdmConid DESC
            OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY
        """
        return DB.fetch_all(query, params), total

    @staticmethod
    def save_admission_config(data):
        params = [
            data['degree_id'], data['college_id'], data['session_from'],
            data.get('session_to') if data.get('session_to') and str(data.get('session_to')) != '0' else None,
            data.get('separator', ''), data.get('suffix', ''), data.get('prefix', '')
        ]
        if data.get('pk_id'):
            return DB.execute("""
                UPDATE SMS_AdmissionConfigurations_Mst 
                SET Degree=?, Fk_collegeid=?, SessionFrom=?, SessionTo=?, Separator=?, suffix=?, Prefix=?
                WHERE pk_AdmConid=?
            """, params + [data['pk_id']])
        else:
            return DB.execute("""
                INSERT INTO SMS_AdmissionConfigurations_Mst (Degree, Fk_collegeid, SessionFrom, SessionTo, Separator, suffix, Prefix)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, params)

    @staticmethod
    def delete_admission_config(id):
        return DB.execute("DELETE FROM SMS_AdmissionConfigurations_Mst WHERE pk_AdmConid = ?", [id])

class SeatDetailModel:
    @staticmethod
    def get_seat_details(page=1, per_page=10):
        offset = (page - 1) * per_page
        total = DB.fetch_scalar("SELECT COUNT(*) FROM SMS_Clg_DegreeSeat_dtl")
        query = f"""
            SELECT S.*, C.collegename, D.degreename, B.Branchname, SES.sessionname
            FROM SMS_Clg_DegreeSeat_dtl S
            INNER JOIN SMS_College_Mst C ON S.fk_collegeid = C.pk_collegeid
            INNER JOIN SMS_Degree_Mst D ON S.fk_degreeid = D.pk_degreeid
            LEFT JOIN SMS_BranchMst B ON S.fk_branchid = B.Pk_BranchId
            INNER JOIN SMS_AcademicSession_Mst SES ON S.fk_sessionid = SES.pk_sessionid
            ORDER BY SES.sessionorder DESC, C.collegename, D.degreename
            OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY
        """
        return DB.fetch_all(query), total

    @staticmethod
    def get_seat_report(filters):
        query = """
            SELECT S.*, C.collegename, D.degreename, B.Branchname, SES.sessionname
            FROM SMS_Clg_DegreeSeat_dtl S
            INNER JOIN SMS_College_Mst C ON S.fk_collegeid = C.pk_collegeid
            INNER JOIN SMS_Degree_Mst D ON S.fk_degreeid = D.pk_degreeid
            LEFT JOIN SMS_BranchMst B ON S.fk_branchid = B.Pk_BranchId
            INNER JOIN SMS_AcademicSession_Mst SES ON S.fk_sessionid = SES.pk_sessionid
            WHERE S.fk_sessionid = ? AND S.fk_collegeid = ?
            ORDER BY D.degreename, B.Branchname
        """
        return DB.fetch_all(query, [filters['session_id'], filters['college_id']])

    @staticmethod
    def save_seat_detail(data):
        params = [
            data['college_id'], data['degree_id'], 
            data.get('branch_id') if data.get('branch_id') and str(data.get('branch_id')) != '0' else None,
            data['session_id'], data['total_seats']
        ]
        if data.get('pk_id'):
            return DB.execute("""
                UPDATE SMS_Clg_DegreeSeat_dtl 
                SET fk_collegeid=?, fk_degreeid=?, fk_branchid=?, fk_sessionid=?, totseat=?
                WHERE pk_clg_degree_seat_dtl=?
            """, params + [data['pk_id']])
        else:
            return DB.execute("""
                INSERT INTO SMS_Clg_DegreeSeat_dtl (fk_collegeid, fk_degreeid, fk_branchid, fk_sessionid, totseat)
                VALUES (?, ?, ?, ?, ?)
            """, params)

    @staticmethod
    def delete_seat_detail(id):
        return DB.execute("DELETE FROM SMS_Clg_DegreeSeat_dtl WHERE pk_clg_degree_seat_dtl = ?", [id])

class RecheckingModel:
    @staticmethod
    def _table_columns(table_name):
        # Some DBs block INFORMATION_SCHEMA; use cursor.description.
        try:
            conn = DB.get_connection()
            cur = conn.cursor()
            cur.execute(f"SELECT TOP 0 * FROM {table_name}")
            return {str(d[0]).lower() for d in (cur.description or [])}
        except Exception:
            return set()

    @staticmethod
    def get_rechecking_requests(filters, processed=False):
        # Role: 'HOD', 'Advisor', 'Dean'
        # Programme: 'PG', 'UG'
        role = filters.get('role')
        programme = filters.get('programme')
        
        sql = """
            SELECT R.*, S.fullname as studentname,
                   COALESCE(NULLIF(LTRIM(RTRIM(S.AdmissionNo)), ''), NULLIF(LTRIM(RTRIM(S.enrollmentno)), '')) AS AdmissionNo,
                   C.coursecode, C.coursename, C.crhr_theory as crhrth, C.crhr_practical as crhrpr
            FROM sms_stuexammarks_dtl_reval R
            INNER JOIN SMS_StuCourseAllocation SCA ON R.fk_stucourseallocid = SCA.Pk_stucourseallocid
            INNER JOIN SMS_Student_Mst S ON SCA.fk_sturegid = S.pk_sid
            LEFT JOIN SMS_Course_Mst C ON SCA.fk_courseid = C.pk_courseid
            WHERE S.fk_collegeid = ? AND S.fk_curr_session = ? AND S.fk_degreeid = ?
        """
        params = [filters['college_id'], filters['session_id'], filters['degree_id']]
        
        if role == 'HOD':
            sql += " AND R.IsApprovedByHOD IS NULL" if not processed else " AND R.IsApprovedByHOD IS NOT NULL"
        elif role == 'Advisor':
            # Assuming reval table might not have advisor column directly, using CA approval logic
            sql += " AND R.IsApprovedByHOD = 1" 
        
        rows = DB.fetch_all(sql, params)
        # Normalize key names for templates.
        for r in rows:
            # pk_id
            pk_id = None
            for k in r.keys():
                lk = str(k).lower()
                if lk in ('pk_stumarksdtlid', 'pk_marksdtlid', 'pk_revalid', 'pk_id'):
                    pk_id = r.get(k)
                    break
            r['pk_id'] = pk_id

            # decision label
            v = r.get('IsApprovedByHOD')
            if v is None:
                r['hod_status'] = ''
            elif str(v).strip() in ('1', 'A', 'Y', 'YES', 'Approved', 'APPROVED'):
                r['hod_status'] = 'Approved'
            else:
                r['hod_status'] = 'Rejected'

        return rows

    @staticmethod
    def update_hod_decision(pk_id, decision, remarks, user_id=None):
        """
        decision: 'A' (approve) or 'R' (reject)
        Stores in sms_stuexammarks_dtl_reval with best-effort column mapping.
        """
        decision = (decision or 'A').upper()
        if decision not in ('A', 'R'):
            decision = 'A'
        remarks = (remarks or '').strip()

        cols = RecheckingModel._table_columns('sms_stuexammarks_dtl_reval')
        if not cols:
            return False, "Cannot read rechecking table schema."

        pk_col = next((c for c in ('pk_stumarksdtlid', 'pk_marksdtlid', 'pk_revalid', 'pk_id') if c in cols), None)
        if not pk_col:
            return False, "Primary key column not found in rechecking table."

        is_col = next((c for c in ('isapprovedbyhod', 'hod_approved', 'hodapprove', 'is_hod_approved') if c in cols), None)
        rem_col = next((c for c in ('remarksbyhod', 'remarks_by_hod', 'hodremarks', 'hod_remarks', 'remarks_hod') if c in cols), None)
        date_col = next((c for c in ('hod_approvedate', 'hod_approved_date', 'hod_approvaldate', 'hod_approvdate', 'hod_approvedon') if c in cols), None)
        by_col = next((c for c in ('hod_approvedby', 'hod_by', 'hod_byid', 'hod_by_id', 'hodappid') if c in cols), None)

        # Try numeric first (bit/int), fall back to char.
        num_val = 1 if decision == 'A' else 0
        char_val = 'A' if decision == 'A' else 'R'

        set_parts = []
        params = []
        if is_col:
            set_parts.append(f"{is_col} = ?")
            params.append(num_val)
        if rem_col:
            set_parts.append(f"{rem_col} = ?")
            params.append(remarks)
        if by_col:
            set_parts.append(f"{by_col} = ?")
            params.append(str(user_id) if user_id is not None else None)
        if date_col:
            set_parts.append(f"{date_col} = GETDATE()")

        if not set_parts:
            return False, "No updatable columns found for HOD decision."

        sql = f"UPDATE sms_stuexammarks_dtl_reval SET {', '.join(set_parts)} WHERE {pk_col} = ?"
        try:
            DB.execute(sql, params + [pk_id])
            return True, "Saved successfully."
        except Exception:
            # Retry with char decision if numeric failed.
            if is_col:
                params2 = []
                set_parts2 = []
                set_parts2.append(f"{is_col} = ?")
                params2.append(char_val)
                if rem_col:
                    set_parts2.append(f"{rem_col} = ?")
                    params2.append(remarks)
                if by_col:
                    set_parts2.append(f"{by_col} = ?")
                    params2.append(str(user_id) if user_id is not None else None)
                if date_col:
                    set_parts2.append(f"{date_col} = GETDATE()")
                sql2 = f"UPDATE sms_stuexammarks_dtl_reval SET {', '.join(set_parts2)} WHERE {pk_col} = ?"
                DB.execute(sql2, params2 + [pk_id])
                return True, "Saved successfully."

    @staticmethod
    def _pick_first(cols, candidates):
        cols = {c.lower() for c in (cols or [])}
        for c in candidates:
            if c.lower() in cols:
                return c
        return None

    @staticmethod
    def _truthy_approved_expr(col_sql):
        # Treat numeric 1/2 etc OR char 'A'/'Y' as approved.
        return f"""(
            TRY_CONVERT(INT, {col_sql}) = 1
            OR UPPER(CONVERT(VARCHAR(20), {col_sql})) IN ('A','Y','YES','APPROVED')
        )"""

    @staticmethod
    def get_rechecking_requests_by_session(session_id, stage, processed=False):
        """
        Live behavior: only Academic Session is used on these pages.
        stage: 'HOD', 'ADVISOR', 'DEAN'
        """
        if not session_id:
            return []

        cols = RecheckingModel._table_columns('sms_stuexammarks_dtl_reval')
        pk_col = next((c for c in ('pk_stumarksdtlid', 'pk_marksdtlid', 'pk_revalid', 'pk_id') if c in cols), None)
        if not pk_col:
            return []

        hod_col = next((c for c in ('isapprovedbyhod', 'hod_approved', 'hodapprove', 'is_hod_approved') if c in cols), None)
        adv_col = next((c for c in ('isapprovedbyadvisor', 'isapprovedbymajoradvisor', 'advisor_approved', 'majoradvisor_approved') if c in cols), None)
        dean_col = next((c for c in ('isapprovedbydean', 'dean_approved', 'is_dean_approved') if c in cols), None)

        stage = (stage or '').upper()
        stage_col = {'HOD': hod_col, 'ADVISOR': adv_col, 'DEAN': dean_col}.get(stage)
        if not stage_col:
            return []

        sql = f"""
            SELECT R.*, S.fullname as studentname,
                   COALESCE(NULLIF(LTRIM(RTRIM(S.AdmissionNo)), ''), NULLIF(LTRIM(RTRIM(S.enrollmentno)), '')) AS AdmissionNo,
                   C.coursecode, C.coursename, C.crhr_theory as crhrth, C.crhr_practical as crhrpr
            FROM sms_stuexammarks_dtl_reval R
            INNER JOIN SMS_StuCourseAllocation SCA ON R.fk_stucourseallocid = SCA.Pk_stucourseallocid
            INNER JOIN SMS_Student_Mst S ON SCA.fk_sturegid = S.pk_sid
            LEFT JOIN SMS_Course_Mst C ON SCA.fk_courseid = C.pk_courseid
            WHERE (SCA.fk_dgacasessionid = ? OR S.fk_curr_session = ? OR S.fk_adm_session = ?)
        """
        params = [session_id, session_id, session_id]

        # Gate by previous stages for Advisor/Dean if those columns exist.
        if stage == 'ADVISOR' and hod_col:
            sql += f" AND {RecheckingModel._truthy_approved_expr('R.' + hod_col)}"
        if stage == 'DEAN':
            if hod_col:
                sql += f" AND {RecheckingModel._truthy_approved_expr('R.' + hod_col)}"
            if adv_col:
                sql += f" AND {RecheckingModel._truthy_approved_expr('R.' + adv_col)}"

        if processed:
            sql += f" AND R.{stage_col} IS NOT NULL"
        else:
            sql += f" AND R.{stage_col} IS NULL"

        sql += f" ORDER BY R.{pk_col} DESC"
        rows = DB.fetch_all(sql, params)

        # Normalize for templates.
        for r in rows:
            r['pk_id'] = r.get(pk_col)
            val = r.get(stage_col)
            if val is None:
                r['stage_status'] = ''
            elif str(val).strip() in ('1', 'A', 'Y', 'YES', 'Approved', 'APPROVED'):
                r['stage_status'] = 'Approved'
            else:
                r['stage_status'] = 'Rejected'
        return rows

    @staticmethod
    def update_stage_decision(pk_id, stage, decision, remarks, user_id=None):
        """
        stage: 'HOD'|'ADVISOR'|'DEAN'
        """
        stage = (stage or '').upper()
        decision = (decision or 'A').upper()
        if decision not in ('A', 'R'):
            decision = 'A'
        remarks = (remarks or '').strip()

        cols = RecheckingModel._table_columns('sms_stuexammarks_dtl_reval')
        pk_col = next((c for c in ('pk_stumarksdtlid', 'pk_marksdtlid', 'pk_revalid', 'pk_id') if c in cols), None)
        if not pk_col:
            return False, "Primary key column not found."

        hod_col = next((c for c in ('isapprovedbyhod', 'hod_approved', 'hodapprove', 'is_hod_approved') if c in cols), None)
        adv_col = next((c for c in ('isapprovedbyadvisor', 'isapprovedbymajoradvisor', 'advisor_approved', 'majoradvisor_approved') if c in cols), None)
        dean_col = next((c for c in ('isapprovedbydean', 'dean_approved', 'is_dean_approved') if c in cols), None)
        stage_col = {'HOD': hod_col, 'ADVISOR': adv_col, 'DEAN': dean_col}.get(stage)
        if not stage_col:
            return False, f"{stage} decision column not found."

        # remarks/date/by columns vary; best-effort.
        if stage == 'HOD':
            rem_col = next((c for c in ('remarksbyhod', 'remarks_by_hod', 'hodremarks', 'hod_remarks', 'remarks_hod') if c in cols), None)
            date_col = next((c for c in ('hod_approvedate', 'hod_approved_date', 'hod_approvaldate', 'hod_approvdate', 'hod_approvedon') if c in cols), None)
            by_col = next((c for c in ('hod_approvedby', 'hod_by', 'hod_byid', 'hod_by_id', 'hodappid') if c in cols), None)
        elif stage == 'ADVISOR':
            rem_col = next((c for c in ('remarksbyadvisor', 'remarks_by_advisor', 'advisorremarks', 'advisor_remarks') if c in cols), None)
            date_col = next((c for c in ('advisor_approvedate', 'advisor_approved_date', 'advisor_approvaldate', 'advisor_approvdate') if c in cols), None)
            by_col = next((c for c in ('advisor_approvedby', 'advisor_by', 'advisor_byid') if c in cols), None)
        else:
            rem_col = next((c for c in ('remarksbydean', 'remarks_by_dean', 'deanremarks', 'dean_remarks') if c in cols), None)
            date_col = next((c for c in ('dean_approvedate', 'dean_approved_date', 'dean_approvaldate', 'dean_approvdate') if c in cols), None)
            by_col = next((c for c in ('dean_approvedby', 'dean_by', 'dean_byid') if c in cols), None)

        num_val = 1 if decision == 'A' else 0
        char_val = 'A' if decision == 'A' else 'R'

        set_parts = [f"{stage_col} = ?"]
        params = [num_val]
        if rem_col:
            set_parts.append(f"{rem_col} = ?")
            params.append(remarks)
        if by_col:
            set_parts.append(f"{by_col} = ?")
            params.append(str(user_id) if user_id is not None else None)
        if date_col:
            set_parts.append(f"{date_col} = GETDATE()")

        sql = f"UPDATE sms_stuexammarks_dtl_reval SET {', '.join(set_parts)} WHERE {pk_col} = ?"
        try:
            DB.execute(sql, params + [pk_id])
            return True, "Saved successfully."
        except Exception:
            # retry char
            set_parts[0] = f"{stage_col} = ?"
            params2 = [char_val] + params[1:]
            DB.execute(sql, params2 + [pk_id])
            return True, "Saved successfully."

class RevisedResultModel:
    @staticmethod
    def get_revised_results(filters):
        is_pg = filters.get('is_pg')
        table = 'sms_stuexammarks_dtl_revisedPGPHD' if is_pg else 'sms_stuexammarks_dtl_revised'
        
        sql = f"""
            SELECT R.*, S.fullname as studentname, S.AdmissionNo, C.coursecode, C.coursename
            FROM {table} R
            INNER JOIN SMS_StuCourseAllocation SCA ON R.fk_stucourseallocid = SCA.Pk_stucourseallocid
            INNER JOIN SMS_Student_Mst S ON SCA.fk_sturegid = S.pk_sid
            LEFT JOIN SMS_Course_Mst C ON SCA.fk_courseid = C.pk_courseid
            WHERE S.fk_collegeid = ? AND S.fk_curr_session = ? AND S.fk_degreeid = ?
        """
        params = [filters['college_id'], filters['session_id'], filters['degree_id']]
        return DB.fetch_all(sql, params)

class MiscAcademicsModel:
    @staticmethod
    def get_transfers_paginated(page=1, per_page=10):
        offset = (page - 1) * per_page
        sql = """
            SELECT T.*, S.fullname as studentname, S.AdmissionNo
            FROM SMS_Student_Transfer_Details T
            INNER JOIN SMS_Student_Mst S ON T.fk_sturegid = S.pk_sid
            ORDER BY T.pk_stutransferid DESC OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """
        items = DB.fetch_all(sql, [offset, per_page])
        count = DB.fetch_one("SELECT COUNT(*) as cnt FROM SMS_Student_Transfer_Details")['cnt']
        return items, count

    @staticmethod
    def get_students_for_transfer_paginated(filters, search=None, page=1, per_page=20):
        """
        Live page shows "List of Students" filtered by College/Session/Degree/Class (semester)
        with optional Department + search by Admission No / Name.
        """
        search = search or {}
        offset = (page - 1) * per_page

        base_sql = """
            SELECT
                S.pk_sid,
                S.fullname,
                S.enrollmentno,
                COALESCE(NULLIF(LTRIM(RTRIM(S.AdmissionNo)), ''), NULLIF(LTRIM(RTRIM(S.enrollmentno)), '')) AS AdmissionNo,
                S.fk_collegeid,
                S.fk_adm_session,
                S.fk_degreeid,
                S.fk_branchid,
                B.Branchname AS department_name,
                DC.fk_semesterid,
                SEM.semester_roman
            FROM SMS_Student_Mst S
            LEFT JOIN SMS_DegreeCycle_Mst DC ON S.fk_degreecycleidcurrent = DC.pk_degreecycleid
            LEFT JOIN SMS_Semester_Mst SEM ON DC.fk_semesterid = SEM.pk_semesterid
            LEFT JOIN SMS_BranchMst B ON S.fk_branchid = B.Pk_BranchId
            WHERE 1=1
        """
        params = []

        if filters.get('college_id'):
            base_sql += " AND S.fk_collegeid = ?"
            params.append(filters['college_id'])
        if filters.get('session_id'):
            # Live label is "Academic Session" (admitted session)
            base_sql += " AND S.fk_adm_session = ?"
            params.append(filters['session_id'])
        if filters.get('degree_id'):
            base_sql += " AND S.fk_degreeid = ?"
            params.append(filters['degree_id'])
        if filters.get('semester_id'):
            base_sql += " AND DC.fk_semesterid = ?"
            params.append(filters['semester_id'])
        if filters.get('branch_id') and str(filters['branch_id']) != '0':
            base_sql += " AND S.fk_branchid = ?"
            params.append(filters['branch_id'])

        admission_no = (search.get('admission_no') or '').strip()
        if admission_no:
            base_sql += " AND (S.AdmissionNo LIKE ? OR S.enrollmentno LIKE ?)"
            like = f"%{admission_no}%"
            params.extend([like, like])

        student_name = (search.get('student_name') or '').strip()
        if student_name:
            base_sql += " AND S.fullname LIKE ?"
            params.append(f"%{student_name}%")

        count_sql = f"SELECT COUNT(*) as cnt FROM ({base_sql}) t"
        total = DB.fetch_one(count_sql, params)['cnt']

        page_sql = base_sql + " ORDER BY S.fullname OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
        page_params = params + [offset, per_page]
        items = DB.fetch_all(page_sql, page_params)
        return items, total

    @staticmethod
    def get_students_for_transfer(filters, search=None):
        search = search or {}
        sql = """
            SELECT
                S.pk_sid,
                S.fullname,
                S.enrollmentno,
                COALESCE(NULLIF(LTRIM(RTRIM(S.AdmissionNo)), ''), NULLIF(LTRIM(RTRIM(S.enrollmentno)), '')) AS AdmissionNo,
                B.Branchname AS department_name,
                SEM.semester_roman
            FROM SMS_Student_Mst S
            LEFT JOIN SMS_DegreeCycle_Mst DC ON S.fk_degreecycleidcurrent = DC.pk_degreecycleid
            LEFT JOIN SMS_Semester_Mst SEM ON DC.fk_semesterid = SEM.pk_semesterid
            LEFT JOIN SMS_BranchMst B ON S.fk_branchid = B.Pk_BranchId
            WHERE 1=1
        """
        params = []

        if filters.get('college_id'):
            sql += " AND S.fk_collegeid = ?"
            params.append(filters['college_id'])
        if filters.get('session_id'):
            sql += " AND S.fk_adm_session = ?"
            params.append(filters['session_id'])
        if filters.get('degree_id'):
            sql += " AND S.fk_degreeid = ?"
            params.append(filters['degree_id'])
        if filters.get('semester_id'):
            sql += " AND DC.fk_semesterid = ?"
            params.append(filters['semester_id'])
        if filters.get('branch_id') and str(filters['branch_id']) != '0':
            sql += " AND S.fk_branchid = ?"
            params.append(filters['branch_id'])

        admission_no = (search.get('admission_no') or '').strip()
        if admission_no:
            sql += " AND (S.AdmissionNo LIKE ? OR S.enrollmentno LIKE ?)"
            like = f"%{admission_no}%"
            params.extend([like, like])

        student_name = (search.get('student_name') or '').strip()
        if student_name:
            sql += " AND S.fullname LIKE ?"
            params.append(f"%{student_name}%")

        sql += " ORDER BY S.fullname"
        return DB.fetch_all(sql, params)

    @staticmethod
    def find_student_by_admission_no(college_id, admission_no):
        admission_no = (admission_no or '').strip()
        if not (college_id and admission_no):
            return None
        sql = """
            SELECT TOP 1
                pk_sid,
                fullname,
                enrollmentno,
                COALESCE(NULLIF(LTRIM(RTRIM(AdmissionNo)), ''), NULLIF(LTRIM(RTRIM(enrollmentno)), '')) AS AdmissionNo
            FROM SMS_Student_Mst
            WHERE fk_collegeid = ?
              AND (LTRIM(RTRIM(AdmissionNo)) = ? OR LTRIM(RTRIM(enrollmentno)) = ?)
        """
        return DB.fetch_one(sql, [college_id, admission_no, admission_no])

    @staticmethod
    def transfer_single_student(college_id, old_adm_no, new_adm_no, user_id=None):
        """
        Change a student's AdmissionNo from old -> new within a college.
        (We only update SMS_Student_Mst.AdmissionNo; the live system stores its own history.)
        """
        old_adm_no = (old_adm_no or '').strip()
        new_adm_no = (new_adm_no or '').strip()

        if not college_id:
            return False, "College is required."
        if not old_adm_no or not new_adm_no:
            return False, "Old and New Admission No. are required."
        if old_adm_no == new_adm_no:
            return False, "Old and New Admission No. cannot be same."

        existing_new = MiscAcademicsModel.find_student_by_admission_no(college_id, new_adm_no)
        if existing_new:
            return False, f"New Admission No. '{new_adm_no}' is already assigned to another student."

        stu = MiscAcademicsModel.find_student_by_admission_no(college_id, old_adm_no)
        if not stu:
            return False, f"No student found for Old Admission No. '{old_adm_no}'."

        conn = DB.get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                "UPDATE SMS_Student_Mst SET AdmissionNo = ? WHERE pk_sid = ?",
                [new_adm_no, stu['pk_sid']]
            )
            conn.commit()
            return True, "Admission No. updated successfully."
        except Exception as e:
            conn.rollback()
            return False, f"Failed to update Admission No.: {e}"

    @staticmethod
    def swap_students(college_id, adm_no_1, adm_no_2, user_id=None):
        adm_no_1 = (adm_no_1 or '').strip()
        adm_no_2 = (adm_no_2 or '').strip()

        if not college_id:
            return False, "College is required."
        if not adm_no_1 or not adm_no_2:
            return False, "Both Admission No. values are required."
        if adm_no_1 == adm_no_2:
            return False, "Admission No. values cannot be same."

        s1 = MiscAcademicsModel.find_student_by_admission_no(college_id, adm_no_1)
        s2 = MiscAcademicsModel.find_student_by_admission_no(college_id, adm_no_2)
        if not s1:
            return False, f"No student found for First Admission No. '{adm_no_1}'."
        if not s2:
            return False, f"No student found for Second Admission No. '{adm_no_2}'."

        # Swap only AdmissionNo field (do not touch enrollmentno).
        a1 = (s1.get('AdmissionNo') or '').strip()
        a2 = (s2.get('AdmissionNo') or '').strip()
        if not a1 or not a2:
            return False, "Cannot swap: one of the students has blank Admission No."

        conn = DB.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("UPDATE SMS_Student_Mst SET AdmissionNo = ? WHERE pk_sid = ?", [a2, s1['pk_sid']])
            cur.execute("UPDATE SMS_Student_Mst SET AdmissionNo = ? WHERE pk_sid = ?", [a1, s2['pk_sid']])
            conn.commit()
            return True, "Admission No. swapped successfully."
        except Exception as e:
            conn.rollback()
            return False, f"Failed to swap Admission No.: {e}"

    @staticmethod
    def get_registrations_cancel_paginated(page=1, per_page=10):
        offset = (page - 1) * per_page
        sql = """
            SELECT R.*, S.fullname as studentname, S.AdmissionNo
            FROM SMS_RegCancel_Detail R
            INNER JOIN SMS_Student_Mst S ON R.fk_sturegid = S.pk_sid
            ORDER BY R.fk_sturegid DESC OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """
        items = DB.fetch_all(sql, [offset, per_page])
        count = DB.fetch_one("SELECT COUNT(*) as cnt FROM SMS_RegCancel_Detail")['cnt']
        return items, count

    @staticmethod
    def _table_columns(table_name):
        # Some DBs block INFORMATION_SCHEMA. Fallback to cursor.description.
        cols = set()
        try:
            rows = DB.fetch_all(
                "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = ?",
                [table_name]
            )
            cols = {str(r['COLUMN_NAME']).lower() for r in rows}
        except Exception:
            cols = set()

        if cols:
            return cols

        try:
            conn = DB.get_connection()
            cur = conn.cursor()
            cur.execute(f"SELECT TOP 0 * FROM {table_name}")
            cols = {str(d[0]).lower() for d in (cur.description or [])}
            # Close only if not in flask context is handled by DB; here we may be in app context.
            return cols
        except Exception:
            return set()

    @staticmethod
    def get_students_for_registration_cancel(filters, page=1, per_page=20):
        """
        Mimics live: filters (College, Session, Degree, Class, Department, Year[derived]) -> List of Students.
        Excludes already cancelled (IsRegCancel=1) and already approved in RegCancel detail.
        """
        offset = (page - 1) * per_page

        # Prefer SMS_SemesterRegistration for "Class" filtering (most reliable).
        # We detect actual column names at runtime and only fall back if we can't.
        def _run_variant(join_sql, where_sql, params):
            count_sql = f"SELECT COUNT(*) as cnt FROM ({join_sql} {where_sql}) t"
            total = DB.fetch_one(count_sql, params)['cnt']
            page_sql = join_sql + where_sql + " ORDER BY S.fullname OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
            items = DB.fetch_all(page_sql, params + [(page - 1) * per_page, per_page])
            return items, total

        base_select = """
            SELECT
                S.pk_sid,
                S.fullname AS Name,
                COALESCE(NULLIF(LTRIM(RTRIM(S.AdmissionNo)), ''), NULLIF(LTRIM(RTRIM(S.enrollmentno)), '')) AS Admission_No,
                CAST(0 AS INT) AS returnAmount
            FROM SMS_Student_Mst S
        """
        if filters.get('branch_id') and str(filters['branch_id']) != '0':
            # PG/PhD specialization can be stored in discipline table; include it for filtering.
            base_select += " LEFT JOIN SMS_stuDiscipline_dtl SD ON SD.fk_sturegid = S.pk_sid "

        common_where = """
            WHERE 1=1
              AND (S.IsRegCancel IS NULL OR S.IsRegCancel = 0)
              AND S.pk_sid NOT IN (SELECT fk_sturegid FROM SMS_RegCancel_Detail WHERE Approved = 1)
        """
        common_params = []
        if filters.get('college_id'):
            common_where += " AND S.fk_collegeid = ?"
            common_params.append(filters['college_id'])
        if filters.get('degree_id'):
            common_where += " AND S.fk_degreeid = ?"
            common_params.append(filters['degree_id'])
        if filters.get('branch_id') and str(filters['branch_id']) != '0':
            # For PG/PHD, specialization/department might be stored in SMS_stuDiscipline_dtl.
            # Use an OR filter across Student_Mst branch and discipline major/minor/supporting.
            extra_or = "S.fk_branchid = ? OR SD.fk_desciplineidMajor = ? OR SD.fk_desciplineidMinor = ? OR SD.fk_desciplineidSupporting = ?"
            extra_params = [filters['branch_id'], filters['branch_id'], filters['branch_id'], filters['branch_id']]

            stu_cols = MiscAcademicsModel._table_columns('SMS_Student_Mst')
            if 'fk_specializationid' in stu_cols:
                extra_or += " OR S.fk_specializationid = ?"
                extra_params.append(filters['branch_id'])
            if 'fk_specialisationid' in stu_cols:
                extra_or += " OR S.fk_specialisationid = ?"
                extra_params.append(filters['branch_id'])

            common_where += f" AND ({extra_or})"
            common_params.extend(extra_params)

        # Try SR join using detected column names.
        if filters.get('session_id') and filters.get('semester_id'):
            import os
            sr_cols = MiscAcademicsModel._table_columns('SMS_SemesterRegistration')
            sid_col = next((c for c in ('fk_sturegid', 'fk_sid', 'fk_stid', 'fk_studentid', 'fk_student_id') if c in sr_cols), None)
            session_col = next((c for c in ('fk_sessionid', 'fk_acdsession', 'fk_acdsessionid', 'fk_curr_session', 'fk_session_id') if c in sr_cols), None)
            sem_col = next((c for c in ('fk_semesterid', 'fk_semid', 'fk_semester_id', 'fk_classid', 'fk_class_id') if c in sr_cols), None)

            if sid_col and session_col and sem_col:
                join_sql = base_select + f" INNER JOIN SMS_SemesterRegistration SR ON SR.{sid_col} = S.pk_sid "
                # Live systems sometimes store session/semester as order instead of PK.
                sr_where_variants = [
                    (f" AND SR.{session_col} = ? AND SR.{sem_col} = ?", [filters['session_id'], filters['semester_id']]),
                    (f" AND SR.{session_col} = (SELECT sessionorder FROM SMS_AcademicSession_Mst WHERE pk_sessionid = ?) AND SR.{sem_col} = ?", [filters['session_id'], filters['semester_id']]),
                    (f" AND SR.{session_col} = ? AND SR.{sem_col} = (SELECT semesterorder FROM SMS_Semester_Mst WHERE pk_semesterid = ?)", [filters['session_id'], filters['semester_id']]),
                    (f" AND SR.{session_col} = (SELECT sessionorder FROM SMS_AcademicSession_Mst WHERE pk_sessionid = ?) AND SR.{sem_col} = (SELECT semesterorder FROM SMS_Semester_Mst WHERE pk_semesterid = ?)", [filters['session_id'], filters['semester_id']]),
                ]

                for extra_where, extra_params in sr_where_variants:
                    where_sql = common_where + extra_where
                    params = common_params + extra_params
                    try:
                        items, total = _run_variant(join_sql, where_sql, params)
                        # If DEBUG mode, log which SR mapping worked (helps field debugging).
                        if os.getenv('DEBUG', '').lower() == 'true':
                            print(f"[registration_cancel] SR join used cols sid={sid_col} session={session_col} sem={sem_col}; total={total}")
                        if total:
                            return items, total
                    except Exception as e:
                        if os.getenv('DEBUG', '').lower() == 'true':
                            print(f"[registration_cancel] SR join failed for cols sid={sid_col} session={session_col} sem={sem_col}: {e}")
                        continue

        # Fallback to DegreeCycle (best-effort)
        join_sql = base_select + " LEFT JOIN SMS_DegreeCycle_Mst DC ON S.fk_degreecycleidcurrent = DC.pk_degreecycleid "
        where_sql = common_where
        params = list(common_params)
        if filters.get('session_id'):
            where_sql += " AND (S.fk_curr_session = ? OR S.fk_adm_session = ?)"
            params.extend([filters['session_id'], filters['session_id']])
        if filters.get('semester_id'):
            where_sql += " AND DC.fk_semesterid = ?"
            params.append(filters['semester_id'])

        items, total = _run_variant(join_sql, where_sql, params)

        # Try to compute due/return amount if an appropriate FMS table exists.
        # If it fails (table/columns not present), keep 0 (never crash the page).
        try:
            cols = MiscAcademicsModel._table_columns('FMS_CancelRefund_Approval')
            if cols:
                # Heuristic: common patterns used in fee modules.
                # We only override returnAmount if we can fetch a numeric value.
                for it in items:
                    sid = it.get('pk_sid')
                    if not sid:
                        continue
                    amt = None
                    if 'fk_sid' in cols and 'refundamount' in cols:
                        amt = DB.fetch_scalar(
                            "SELECT TOP 1 refundamount FROM FMS_CancelRefund_Approval WHERE fk_sid = ? ORDER BY 1 DESC",
                            [sid]
                        )
                    elif 'fk_sid' in cols and 'amount' in cols:
                        amt = DB.fetch_scalar(
                            "SELECT TOP 1 amount FROM FMS_CancelRefund_Approval WHERE fk_sid = ? ORDER BY 1 DESC",
                            [sid]
                        )
                    if amt is not None:
                        try:
                            it['returnAmount'] = int(amt)
                        except Exception:
                            pass
        except Exception:
            pass

        return items, total

    @staticmethod
    def update_registration_cancel(selected_rows, user_id=None):
        """
        selected_rows: list of dicts {pk_sid:int, remarks:str, returnAmount:int/str}
        - Upserts into SMS_RegCancel_Detail
        - Sets SMS_Student_Mst.IsRegCancel = 1
        """
        if not selected_rows:
            return False, "Please select at least one student."

        cols = MiscAcademicsModel._table_columns('SMS_RegCancel_Detail')
        if not cols:
            return False, "SMS_RegCancel_Detail table columns not readable."

        conn = DB.get_connection()
        cur = conn.cursor()
        try:
            for row in selected_rows:
                sid = row.get('pk_sid')
                if not sid:
                    continue

                remarks = (row.get('remarks') or '').strip()
                amt_raw = row.get('returnAmount')
                try:
                    amt = int(float(amt_raw)) if amt_raw not in (None, '') else 0
                except Exception:
                    amt = 0

                # Ensure student is marked cancelled
                cur.execute("UPDATE SMS_Student_Mst SET IsRegCancel = 1 WHERE pk_sid = ?", [sid])

                exists = DB.fetch_one("SELECT TOP 1 fk_sturegid FROM SMS_RegCancel_Detail WHERE fk_sturegid = ?", [sid])
                if exists:
                    set_parts = []
                    params = []
                    if 'remarks' in cols:
                        set_parts.append("Remarks = ?")
                        params.append(remarks)
                    if 'returnamount' in cols:
                        set_parts.append("returnAmount = ?")
                        params.append(amt)
                    if 'approved' in cols:
                        set_parts.append("Approved = 1")
                    if 'updated_by' in cols:
                        set_parts.append("updated_by = ?")
                        params.append(str(user_id) if user_id is not None else None)
                    if 'updated_date' in cols:
                        set_parts.append("updated_date = GETDATE()")

                    if set_parts:
                        sql = "UPDATE SMS_RegCancel_Detail SET " + ", ".join(set_parts) + " WHERE fk_sturegid = ?"
                        cur.execute(sql, params + [sid])
                else:
                    insert_cols = ['fk_sturegid']
                    insert_vals = ['?']
                    params = [sid]

                    if 'remarks' in cols:
                        insert_cols.append('Remarks')
                        insert_vals.append('?')
                        params.append(remarks)
                    if 'returnamount' in cols:
                        insert_cols.append('returnAmount')
                        insert_vals.append('?')
                        params.append(amt)
                    if 'approved' in cols:
                        insert_cols.append('Approved')
                        insert_vals.append('1')
                    if 'insert_date' in cols:
                        insert_cols.append('Insert_date')
                        insert_vals.append('GETDATE()')
                    if 'createdby' in cols:
                        insert_cols.append('CreatedBy')
                        insert_vals.append('?')
                        params.append(str(user_id) if user_id is not None else None)

                    sql = f"INSERT INTO SMS_RegCancel_Detail ({', '.join(insert_cols)}) VALUES ({', '.join(insert_vals)})"
                    cur.execute(sql, params)

            conn.commit()
            return True, "Registration cancel updated successfully."
        except Exception as e:
            conn.rollback()
            return False, f"Update failed: {e}"

    @staticmethod
    def get_semester_changes_paginated(page=1, per_page=10):
        offset = (page - 1) * per_page
        sql = """
            SELECT R.*, S.fullname as studentname, S.AdmissionNo, SEM.semester_roman, R.Insert_date as Datecurrent
            FROM SMS_StuRevisedcourseallocation R
            INNER JOIN SMS_Student_Mst S ON R.fk_sturegid = S.pk_sid
            LEFT JOIN SMS_Semester_Mst SEM ON R.fk_semesterid = SEM.pk_semesterid
            ORDER BY R.Pk_sturevised DESC OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """
        items = DB.fetch_all(sql, [offset, per_page])
        count = DB.fetch_one("SELECT COUNT(*) as cnt FROM SMS_StuRevisedcourseallocation")['cnt']
        return items, count

    @staticmethod
    def get_extension_management_paginated(filters, page=1, per_page=10):
        offset = (page - 1) * per_page
        sql = """
            SELECT E.*, S.fullname as studentname, S.AdmissionNo, C.coursecode, C.coursename
            FROM SMS_StuCourseAllocationExtensionPGPHD E
            INNER JOIN SMS_Student_Mst S ON E.fk_sturegid = S.pk_sid
            LEFT JOIN SMS_Course_Mst C ON E.fk_courseid = C.pk_courseid
            WHERE 1=1
        """
        params = []
        if filters.get('college_id'):
            sql += " AND S.fk_collegeid = ?"
            params.append(filters['college_id'])
        if filters.get('degree_id'):
            sql += " AND S.fk_degreeid = ?"
            params.append(filters['degree_id'])
            
        count_sql = f"SELECT COUNT(*) as cnt FROM ({sql}) AS t"
        total = DB.fetch_one(count_sql, params)['cnt']
        
        sql += f" ORDER BY E.pk_excourseallocid DESC OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY"
        items = DB.fetch_all(sql, params)
        return items, total

    @staticmethod
    def get_course_approval_status(filters):
        # Filters: college_id, session_id, degree_id, semester_id
        sql = """
            SELECT S.pk_sid, S.fullname as studentname, S.AdmissionNo,
                   ST.status_desc as AdvisorStatus,
                   ST2.status_desc as TeacherStatus,
                   CA.submitbit
            FROM SMS_Student_Mst S
            LEFT JOIN Sms_course_Approval CA ON S.pk_sid = CA.fk_sturegid
            LEFT JOIN SMS_StuCourseAllocation_Approval_staffwise ASW ON S.pk_sid = ASW.fk_sturegid
            LEFT JOIN SMS_AdvisoryStatus_Mst ST ON ASW.Adv_AprrovalStatus = ST.pk_advstatusid
            LEFT JOIN SMS_AdvisoryStatus_Mst ST2 ON ASW.Teach_AprrovalStatus = ST2.pk_advstatusid
            WHERE S.fk_collegeid = ? AND S.fk_curr_session = ? AND S.fk_degreeid = ?
        """
        params = [filters['college_id'], filters['session_id'], filters['degree_id']]
        if filters.get('semester_id'):
            sql += " AND CA.fk_semesterid = ?"
            params.append(filters['semester_id'])
            
        return DB.fetch_all(sql, params)

    @staticmethod
    def get_course_approval_status_degree_semesterwise(filters):
        """
        Mimics live "Status Semester And Degreewise" grid:
        College + Session + Degree + Odd/Even + Exam Config => rows for each semester of that parity
        showing YES/NO for each approval stage.
        """
        college_id = filters.get('college_id')
        session_id = filters.get('session_id')
        degree_id = filters.get('degree_id')
        sem_type = int(filters.get('sem_type') or 0)  # 1=Odd,2=Even
        exconfig_id = filters.get('exconfig_id')

        if not all([college_id, session_id, degree_id, sem_type, exconfig_id]):
            return []

        max_sem = DB.fetch_scalar("SELECT maxsem FROM SMS_Degree_Mst WHERE pk_degreeid = ?", [degree_id]) or 8
        parity = 1 if sem_type == 1 else 0
        semesters = DB.fetch_all(
            """
            SELECT pk_semesterid as semester_id, semester_roman, semesterorder
            FROM SMS_Semester_Mst
            WHERE semesterorder <= ? AND (semesterorder % 2) = ?
            ORDER BY semesterorder
            """,
            [max_sem, parity]
        )
        degree_name = DB.fetch_scalar("SELECT degreename FROM SMS_Degree_Mst WHERE pk_degreeid = ?", [degree_id]) or ""

        app_cols = MiscAcademicsModel._table_columns('SMS_StuCourseAllocation_Approval_staffwise')
        # Pick the first available column for each stage (DBs vary).
        colmap = {
            'advisor': next((c for c in ('adv_aprrovalstatus', 'adv_approvalstatus', 'advisor_approvalstatus', 'advisorstatus') if c in app_cols), None),
            'teacher': next((c for c in ('teach_aprrovalstatus', 'teach_approvalstatus', 'teacher_approvalstatus', 'teacherstatus') if c in app_cols), None),
            'dsw': next((c for c in ('dsw_aprrovalstatus', 'dsw_approvalstatus') if c in app_cols), None),
            'library': next((c for c in ('lib_aprrovalstatus', 'library_aprrovalstatus', 'librarian_aprrovalstatus') if c in app_cols), None),
            'fee': next((c for c in ('fee_aprrovalstatus', 'fee_approvalstatus') if c in app_cols), None),
            'dean': next((c for c in ('dean_aprrovalstatus', 'dean_approvalstatus') if c in app_cols), None),
            'deanpgs': next((c for c in ('deanpgs_aprrovalstatus', 'deanpgs_approvalstatus') if c in app_cols), None),
            'registrar': next((c for c in ('registrar_aprrovalstatus', 'registrar_approvalstatus', 'reg_aprrovalstatus', 'reg_approvalstatus') if c in app_cols), None),
        }

        def _pending_expr(col):
            # Approved heuristics:
            # - numeric > 0
            # - string in ('A','Y','YES','APPROVED')
            # - OR status_desc contains 'Approved' when it is a FK to SMS_AdvisoryStatus_Mst
            return f"""(
                {col} IS NULL OR NOT (
                    TRY_CONVERT(INT, {col}) > 0
                    OR UPPER(CONVERT(VARCHAR(20), {col})) IN ('A','Y','YES','APPROVED')
                    OR EXISTS (
                        SELECT 1 FROM SMS_AdvisoryStatus_Mst ST
                        WHERE ST.pk_advstatusid = TRY_CONVERT(INT, {col})
                          AND ST.status_desc LIKE 'Approved%'
                    )
                )
            )"""

        results = []
        for sem in semesters:
            sem_id = sem['semester_id']

            # Total allocations for this sem/session/exconfig (distinct student-course pairs).
            total = DB.fetch_scalar(
                """
                SELECT COUNT(*) FROM (
                    SELECT DISTINCT A.fk_sturegid, A.fk_courseid
                    FROM SMS_StuCourseAllocation A
                    INNER JOIN SMS_Student_Mst S ON A.fk_sturegid = S.pk_sid
                    WHERE S.fk_collegeid = ? AND S.fk_degreeid = ?
                      AND A.fk_dgacasessionid = ? AND A.fk_exconfigid = ?
                      AND A.fk_degreecycleid = ?
                ) t
                """,
                [college_id, degree_id, session_id, exconfig_id, sem_id]
            )

            def stage_status(stage_key):
                col = colmap.get(stage_key)
                if not col or not total:
                    return 'NO'
                pending = DB.fetch_scalar(
                    f"""
                    SELECT COUNT(*) FROM (
                        SELECT DISTINCT A.fk_sturegid, A.fk_courseid,
                               APP.{col} as v
                        FROM SMS_StuCourseAllocation A
                        INNER JOIN SMS_Student_Mst S ON A.fk_sturegid = S.pk_sid
                        LEFT JOIN SMS_StuCourseAllocation_Approval_staffwise APP
                            ON APP.fk_sturegid = A.fk_sturegid
                           AND APP.fk_courseid = A.fk_courseid
                           AND APP.fk_exconfigid = A.fk_exconfigid
                        WHERE S.fk_collegeid = ? AND S.fk_degreeid = ?
                          AND A.fk_dgacasessionid = ? AND A.fk_exconfigid = ?
                          AND A.fk_degreecycleid = ?
                          AND {_pending_expr('APP.' + col)}
                    ) p
                    """,
                    [college_id, degree_id, session_id, exconfig_id, sem_id]
                )
                return 'YES' if pending == 0 else 'NO'

            results.append({
                'degree_name': degree_name,
                'semester_id': sem_id,
                'semester_roman': sem['semester_roman'],
                'advisor': stage_status('advisor'),
                'teacher': stage_status('teacher'),
                'dsw': stage_status('dsw'),
                'library': stage_status('library'),
                'fee': stage_status('fee'),
                'dean': stage_status('dean'),
                'deanpgs': stage_status('deanpgs'),
                'registrar': stage_status('registrar'),
            })

        return results

    @staticmethod
    def get_course_approval_pending_students(filters, detail_semester_id):
        """
        Details for the "Rejected/Pending Student List" section.
        Returns students who have any pending approval in the selected semester.
        """
        college_id = filters.get('college_id')
        session_id = filters.get('session_id')
        degree_id = filters.get('degree_id')
        exconfig_id = filters.get('exconfig_id')
        if not all([college_id, session_id, degree_id, exconfig_id, detail_semester_id]):
            return []

        app_cols = MiscAcademicsModel._table_columns('SMS_StuCourseAllocation_Approval_staffwise')
        stages = [
            ('Advisor', next((c for c in ('adv_aprrovalstatus', 'adv_approvalstatus', 'advisor_approvalstatus', 'advisorstatus') if c in app_cols), None)),
            ('Teacher', next((c for c in ('teach_aprrovalstatus', 'teach_approvalstatus', 'teacher_approvalstatus', 'teacherstatus') if c in app_cols), None)),
            ('DSW', next((c for c in ('dsw_aprrovalstatus', 'dsw_approvalstatus') if c in app_cols), None)),
            ('Library', next((c for c in ('lib_aprrovalstatus', 'library_aprrovalstatus', 'librarian_aprrovalstatus') if c in app_cols), None)),
            ('Fee', next((c for c in ('fee_aprrovalstatus', 'fee_approvalstatus') if c in app_cols), None)),
            ('Dean', next((c for c in ('dean_aprrovalstatus', 'dean_approvalstatus') if c in app_cols), None)),
            ('DeanPGS', next((c for c in ('deanpgs_aprrovalstatus', 'deanpgs_approvalstatus') if c in app_cols), None)),
            ('Registrar', next((c for c in ('registrar_aprrovalstatus', 'registrar_approvalstatus', 'reg_aprrovalstatus', 'reg_approvalstatus') if c in app_cols), None)),
        ]
        stages = [(label, col) for (label, col) in stages if col]
        if not stages:
            return []

        def _pending_expr(col):
            return f"""(
                {col} IS NULL OR NOT (
                    TRY_CONVERT(INT, {col}) > 0
                    OR UPPER(CONVERT(VARCHAR(20), {col})) IN ('A','Y','YES','APPROVED')
                    OR EXISTS (
                        SELECT 1 FROM SMS_AdvisoryStatus_Mst ST
                        WHERE ST.pk_advstatusid = TRY_CONVERT(INT, {col})
                          AND ST.status_desc LIKE 'Approved%'
                    )
                )
            )"""

        # Aggregate per-student pending flags across all allocated courses.
        select_flags = []
        for label, col in stages:
            alias = f"pend_{label.lower().replace(' ', '')}"
            select_flags.append(f"MAX(CASE WHEN {_pending_expr('APP.' + col)} THEN 1 ELSE 0 END) AS {alias}")

        sql = f"""
            SELECT
                S.pk_sid,
                S.fullname,
                COALESCE(NULLIF(LTRIM(RTRIM(S.AdmissionNo)), ''), NULLIF(LTRIM(RTRIM(S.enrollmentno)), '')) AS AdmissionNo,
                {', '.join(select_flags)}
            FROM SMS_StuCourseAllocation A
            INNER JOIN SMS_Student_Mst S ON A.fk_sturegid = S.pk_sid
            LEFT JOIN SMS_StuCourseAllocation_Approval_staffwise APP
                ON APP.fk_sturegid = A.fk_sturegid
               AND APP.fk_courseid = A.fk_courseid
               AND APP.fk_exconfigid = A.fk_exconfigid
            WHERE S.fk_collegeid = ? AND S.fk_degreeid = ?
              AND A.fk_dgacasessionid = ? AND A.fk_exconfigid = ?
              AND A.fk_degreecycleid = ?
            GROUP BY S.pk_sid, S.fullname, S.AdmissionNo, S.enrollmentno
        """
        rows = DB.fetch_all(sql, [college_id, degree_id, session_id, exconfig_id, detail_semester_id])

        out = []
        for r in rows:
            pending = []
            for label, _col in stages:
                alias = f"pend_{label.lower().replace(' ', '')}"
                try:
                    is_pend = int(r.get(alias) or 0) == 1
                except Exception:
                    is_pend = False
                if is_pend:
                    pending.append(label)
            if pending:
                r['pending_stages'] = ", ".join(pending)
                out.append(r)

        out.sort(key=lambda x: (x.get('fullname') or '').lower())
        return out

    @staticmethod
    def get_course_approval_student_courses(filters, detail_semester_id, student_id):
        college_id = filters.get('college_id')
        session_id = filters.get('session_id')
        degree_id = filters.get('degree_id')
        exconfig_id = filters.get('exconfig_id')
        if not all([college_id, session_id, degree_id, exconfig_id, detail_semester_id, student_id]):
            return []

        sql = """
            SELECT
                C.coursecode,
                C.coursename,
                A.crhrth,
                A.crhrpr
            FROM SMS_StuCourseAllocation A
            INNER JOIN SMS_Course_Mst C ON A.fk_courseid = C.pk_courseid
            INNER JOIN SMS_Student_Mst S ON A.fk_sturegid = S.pk_sid
            WHERE S.fk_collegeid = ? AND S.fk_degreeid = ?
              AND A.fk_dgacasessionid = ? AND A.fk_exconfigid = ?
              AND A.fk_degreecycleid = ?
              AND A.fk_sturegid = ?
            ORDER BY C.coursecode
        """
        return DB.fetch_all(sql, [college_id, degree_id, session_id, exconfig_id, detail_semester_id, student_id])

class StudentExtensionModel:
    @staticmethod
    def get_students_for_extension(filters):
        sql = """
            SELECT
                S.pk_sid,
                S.fullname,
                S.enrollmentno,
                COALESCE(NULLIF(LTRIM(RTRIM(S.AdmissionNo)), ''), NULLIF(LTRIM(RTRIM(S.enrollmentno)), '')) AS AdmissionNo
            FROM SMS_Student_Mst S
            LEFT JOIN SMS_DegreeCycle_Mst DC ON S.fk_degreecycleidcurrent = DC.pk_degreecycleid
            WHERE S.fk_collegeid = ? AND S.fk_curr_session = ? AND S.fk_degreeid = ?
        """
        params = [filters['college_id'], filters['session_id'], filters['degree_id']]

        if filters.get('semester_id'):
            sql += " AND DC.fk_semesterid = ?"
            params.append(filters['semester_id'])

        if filters.get('branch_id') and str(filters['branch_id']) != '0':
            sql += " AND S.fk_branchid = ?"
            params.append(filters['branch_id'])

        enrollment_term = (filters.get('enrollment_no') or '').strip()
        if enrollment_term:
            sql += " AND S.enrollmentno LIKE ?"
            params.append(f"%{enrollment_term}%")

        sql += " ORDER BY S.fullname"
        return DB.fetch_all(sql, params)

    @staticmethod
    def get_extensions_paginated(search_term=None, page=1, per_page=10):
        offset = (page - 1) * per_page
        sql = """
            SELECT E.*, S.fullname as s_name,
                   COALESCE(NULLIF(LTRIM(RTRIM(S.AdmissionNo)), ''), NULLIF(LTRIM(RTRIM(S.enrollmentno)), '')) AS AdmissionNo,
                   SEM1.semester_roman as from_sem, SEM2.semester_roman as to_sem,
                   SES1.sessionname as from_session, SES2.sessionname as to_session
            FROM SMS_StuExtension_Mst E
            INNER JOIN SMS_Student_Mst S ON E.fk_sid = S.pk_sid
            LEFT JOIN SMS_Semester_Mst SEM1 ON E.fk_ext_fromSem = SEM1.pk_semesterid
            LEFT JOIN SMS_Semester_Mst SEM2 ON E.fk_extToSem = SEM2.pk_semesterid
            LEFT JOIN SMS_AcademicSession_Mst SES1 ON E.fk_ext_from_session = SES1.pk_sessionid
            LEFT JOIN SMS_AcademicSession_Mst SES2 ON E.fk_ext_to_sesion = SES2.pk_sessionid
        """
        params = []
        if search_term:
            sql += " WHERE S.fullname LIKE ? OR S.AdmissionNo LIKE ? OR S.enrollmentno LIKE ?"
            params.extend([f'%{search_term}%', f'%{search_term}%'])
            params.append(f'%{search_term}%')
            
        sql += f" ORDER BY E.alloc_date DESC OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY"
        items = DB.fetch_all(sql, params)
        
        count_sql = "SELECT COUNT(*) as cnt FROM SMS_StuExtension_Mst E INNER JOIN SMS_Student_Mst S ON E.fk_sid = S.pk_sid"
        if search_term:
            count_sql += " WHERE S.fullname LIKE ? OR S.AdmissionNo LIKE ? OR S.enrollmentno LIKE ?"
            total = DB.fetch_one(count_sql, params)['cnt']
        else:
            total = DB.fetch_one(count_sql)['cnt']
            
        return items, total

    @staticmethod
    def save_extensions(data):
        student_ids = data.getlist('student_ids')
        if not student_ids:
            return False

        from_session = data.get('session_id')
        from_semester = data.get('semester_id')

        # Best-effort insert matching expected legacy table fields.
        sql = """
            INSERT INTO SMS_StuExtension_Mst
                (fk_sid, fk_ext_from_session, fk_ext_fromSem, fk_ext_to_sesion, fk_extToSem, alloc_date, remarks)
            VALUES (?, ?, ?, ?, ?, GETDATE(), ?)
        """

        for sid in student_ids:
            to_session = data.get(f'to_session_{sid}') or from_session
            to_semester = data.get(f'to_semester_{sid}')
            remarks = (data.get(f'remarks_{sid}') or '').strip()

            if not to_semester or str(to_semester).strip() in ('0', '-- Select Semester --', ' -- Select Semester -- '):
                continue

            DB.execute(sql, [sid, from_session, from_semester, to_session, to_semester, remarks])

        return True


class ExtensionManagementModel:
    @staticmethod
    def get_students(filters):
        # In the live system, the student dropdown is driven by students who have an extension record
        # for the selected session + semester.
        sql = """
            SELECT DISTINCT
                S.pk_sid,
                S.enrollmentno,
                S.fullname
            FROM SMS_StuExtension_Mst E
            INNER JOIN SMS_Student_Mst S ON E.fk_sid = S.pk_sid
            WHERE S.fk_collegeid = ?
              AND S.fk_degreeid = ?
              AND E.fk_ext_to_sesion = ?
              AND E.fk_extToSem = ?
        """
        params = [filters['college_id'], filters['degree_id'], filters.get('session_id'), filters.get('semester_id')]

        if filters.get('branch_id') and str(filters['branch_id']) != '0':
            sql += " AND S.fk_branchid = ?"
            params.append(filters['branch_id'])

        sql += " ORDER BY S.enrollmentno, S.fullname"
        return DB.fetch_all(sql, params)

    @staticmethod
    def get_courses(filters):
        student_id = filters.get('student_id')
        semester_id = filters.get('semester_id')
        session_id = filters.get('session_id')

        # Primary source for Extension Management: extension course allocation table.
        # This matches the legacy Extension Management screen (courses shown per selected extended student).
        if student_id:
            sql = """
                SELECT DISTINCT
                    C.pk_courseid,
                    C.coursename,
                    C.coursecode,
                    COALESCE(
                        CASE CP.courseplan
                            WHEN 'MA' THEN 'MAJOR'
                            WHEN 'MI' THEN 'MINOR'
                            WHEN 'SU' THEN 'SUPPORTING'
                            WHEN 'NC' THEN 'NON CREDIT'
                            WHEN 'DE' THEN 'DEFICIENCY'
                            WHEN 'CP' THEN 'COMMON'
                            WHEN 'OP' THEN 'OPTIONAL'
                            WHEN 'RE' THEN 'RESEARCH'
                            ELSE NULL
                        END,
                        T.coursetype,
                        ''
                    ) as coursetype,
                    ISNULL(C.crhr_theory, 0) as cr_th,
                    ISNULL(C.crhr_practical, 0) as cr_pr
                FROM SMS_StuCourseAllocationExtensionPGPHD E
                INNER JOIN SMS_Course_Mst C ON E.fk_courseid = C.pk_courseid
                LEFT JOIN Sms_course_Approval CP ON CP.fk_sturegid = E.fk_sturegid AND CP.fk_courseid = E.fk_courseid
                LEFT JOIN SMS_CourseType_Mst T ON C.fk_coursetypeid = T.pk_coursetypeid
                WHERE E.fk_sturegid = ?
                ORDER BY C.coursecode
            """
            rows = DB.fetch_all(sql, [student_id])
            if rows:
                return rows

        # Live page shows the student's "Programme of Work" / approved course plan (Major/Minor/Non-credit/etc)
        # even for extension semesters, so do not filter by semester here.
        if student_id:
            plan_rows = AdvisoryModel.get_student_course_plan(student_id)
            if plan_rows:
                res = []
                for r in plan_rows:
                    res.append({
                        'pk_courseid': r.get('fk_courseid') or r.get('pk_courseid'),
                        'coursename': r.get('coursename'),
                        'coursecode': r.get('coursecode'),
                        'coursetype': (r.get('type_name') or r.get('coursetype') or '').upper(),
                        'cr_th': r.get('crhr_theory', 0),
                        'cr_pr': r.get('crhr_practical', 0),
                    })
                return res

        # Fallback: show the student's actually allocated courses for the selected session+semester.
        # This avoids over-showing "possible" courses that the student hasn't taken.
        if student_id:
            alloc_sql = """
                SELECT DISTINCT
                    C.pk_courseid,
                    C.coursename,
                    C.coursecode,
                    COALESCE(
                        CASE CP.courseplan
                            WHEN 'MA' THEN 'MAJOR'
                            WHEN 'MI' THEN 'MINOR'
                            WHEN 'SU' THEN 'SUPPORTING'
                            WHEN 'NC' THEN 'NON CREDIT'
                            WHEN 'DE' THEN 'DEFICIENCY'
                            WHEN 'CP' THEN 'COMMON'
                            WHEN 'OP' THEN 'OPTIONAL'
                            WHEN 'RE' THEN 'RESEARCH'
                            ELSE NULL
                        END,
                        T.coursetype,
                        ''
                    ) as coursetype,
                    ISNULL(C.crhr_theory, 0) as cr_th,
                    ISNULL(C.crhr_practical, 0) as cr_pr
                FROM SMS_StuCourseAllocation A
                INNER JOIN SMS_Course_Mst C ON A.fk_courseid = C.pk_courseid
                LEFT JOIN SMS_DegreeCycle_Mst DC ON A.fk_degreecycleid = DC.pk_degreecycleid
                LEFT JOIN Sms_course_Approval CP ON CP.fk_sturegid = A.fk_sturegid AND CP.fk_courseid = A.fk_courseid
                LEFT JOIN SMS_CourseType_Mst T ON C.fk_coursetypeid = T.pk_coursetypeid
                WHERE A.fk_sturegid = ?
                  AND (? IS NULL OR A.fk_dgacasessionid = ?)
                  AND (? IS NULL OR DC.fk_semesterid = ?)
                ORDER BY C.coursecode
            """
            alloc_rows = DB.fetch_all(alloc_sql, [student_id, session_id, session_id, semester_id, semester_id])
            if alloc_rows:
                return alloc_rows

        # Fallback: degree/semester/session-specific course list.
        sql = """
            SELECT DISTINCT
                C.pk_courseid,
                C.coursename,
                C.coursecode,
                ISNULL(T.coursetype, '') AS coursetype,
                ISNULL(C.crhr_theory, 0) AS cr_th,
                ISNULL(C.crhr_practical, 0) AS cr_pr
            FROM SMS_Course_Mst_Dtl D
            INNER JOIN SMS_Course_Mst C ON D.fk_courseid = C.pk_courseid
            LEFT JOIN SMS_CourseType_Mst T ON C.fk_coursetypeid = T.pk_coursetypeid
            LEFT JOIN SMS_AcademicSession_Mst SEL ON SEL.pk_sessionid = ?
            LEFT JOIN SMS_AcademicSession_Mst SFrom ON D.fk_sessionid_from = SFrom.pk_sessionid
            LEFT JOIN SMS_AcademicSession_Mst STo ON D.fk_sessionid_upto = STo.pk_sessionid
            WHERE D.fk_degreeid = ? AND D.fk_semesterid = ?
              AND (
                    ? IS NULL OR SEL.pk_sessionid IS NULL
                    OR (
                        SEL.sessionorder >= ISNULL(SFrom.sessionorder, SEL.sessionorder)
                        AND SEL.sessionorder <= ISNULL(STo.sessionorder, SEL.sessionorder)
                    )
                  )
            ORDER BY C.coursecode
        """
        params = [filters.get('session_id'), filters.get('degree_id'), semester_id, filters.get('session_id')]
        return DB.fetch_all(sql, params)

class MessagingModel:
    @staticmethod
    def get_students_for_messaging(filters):
        sql = """
            SELECT
                S.pk_sid,
                S.fullname as studentname,
                COALESCE(NULLIF(LTRIM(RTRIM(S.AdmissionNo)), ''), NULLIF(LTRIM(RTRIM(S.enrollmentno)), '')) AS AdmissionNo,
                S.p_emailid as emailid,
                S.phoneno as mobileno
            FROM SMS_Student_Mst S
            LEFT JOIN SMS_DegreeCycle_Mst DC ON S.fk_degreecycleidcurrent = DC.pk_degreecycleid
            WHERE S.fk_collegeid = ? AND S.fk_curr_session = ? AND S.fk_degreeid = ?
        """
        params = [filters['college_id'], filters['session_id'], filters['degree_id']]
        
        if filters.get('semester_id'):
            sql += " AND DC.fk_semesterid = ?"
            params.append(filters['semester_id'])
            
        if filters.get('branch_id') and str(filters['branch_id']) != '0':
            sql += " AND S.fk_branchid = ?"
            params.append(filters['branch_id'])
            
        return DB.fetch_all(sql, params)

    @staticmethod
    def log_message(data):
        # Assuming SMS_SMSlog_Status structure: pk_smslogid, fk_sid, message, type (1=Mail, 2=SMS), status, date
        # This is a simulation as the real table might have different columns
        sql = """
            INSERT INTO SMS_SMSlog_Status (fk_sid, message, status, datecurrent)
            VALUES (?, ?, 1, GETDATE())
        """
        # Usually we would loop through selected student IDs
        for sid in data.get('student_ids', []):
            DB.execute(sql, [sid, data.get('message')])
        return True

class AcademicsModel:
    @staticmethod
    def get_faculties():
        return DB.fetch_all("SELECT * FROM SMS_Faculty_Mst ORDER BY faculty")

    @staticmethod
    def save_faculty(data):
        if data.get('pk_facultyid'):
            return DB.execute("UPDATE SMS_Faculty_Mst SET faculty=?, facultyshort=?, rpt_order=?, Remarks=? WHERE pk_facultyid=?",
                            [data['faculty'], data['facultyshort'], data['rpt_order'], data['remarks'], data['pk_facultyid']])
        else:
            return DB.execute("INSERT INTO SMS_Faculty_Mst (faculty, facultyshort, rpt_order, Remarks) VALUES (?, ?, ?, ?)",
                            [data['faculty'], data['facultyshort'], data['rpt_order'], data['remarks']])

    @staticmethod
    def get_colleges_simple():
        return DB.fetch_all("SELECT pk_collegeid as id, collegename as name FROM SMS_College_Mst ORDER BY collegename")

    @staticmethod
    def get_colleges(page=1, per_page=10):
        offset = (page - 1) * per_page
        total = DB.fetch_scalar("SELECT COUNT(*) FROM SMS_College_Mst")
        query = f"""
            SELECT C.*, T.collegypedesc as college_type
            FROM SMS_College_Mst C
            LEFT JOIN SMS_CollegeTpye_Mst T ON C.fk_collegetypeid = T.pk_collegetypeid
            ORDER BY C.collegename 
            OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY
        """
        return DB.fetch_all(query), total

    @staticmethod
    def save_college(data):
        conn = DB.get_connection()
        cursor = conn.cursor()
        try:
            def to_int_or_none(val):
                if val is None:
                    return None
                sval = str(val).strip()
                if not sval or not sval.isdigit():
                    return None
                return int(sval)

            loc_id = data.get('loc_id')
            if loc_id is not None:
                loc_id = str(loc_id).strip()
                if not loc_id:
                    loc_id = None
            type_id = to_int_or_none(data.get('type_id'))
            raw_city = data.get('city_id')
            city_id = to_int_or_none(raw_city)
            if city_id is None and raw_city:
                sval = str(raw_city).strip()
                m = re.search(r'(\d+)$', sval)
                if m:
                    city_id = int(m.group(1))

            if data.get('pk_id'):
                cid = data['pk_id']
                cursor.execute("""
                    UPDATE SMS_College_Mst SET collegename=?, collegecode=?, address=?, contactperson=?, contactno=?,
                    emailid=?, websiteaddress=?, fk_locid=?, remarks=?, fk_collegetypeid=?, fk_cityid=? WHERE pk_collegeid=?
                """, [data['name'], data['code'], data['address'], data['contactperson'], data['contactno'],
                    data['email'], data['website'], loc_id, data['remarks'], 
                    type_id, city_id, cid])
                cursor.execute("DELETE FROM SMS_College_Dtl WHERE fk_collegeid=?", [cid])
            else:
                cursor.execute("""
                    INSERT INTO SMS_College_Mst (collegename, collegecode, address, contactperson, contactno, emailid, websiteaddress, fk_locid, remarks, fk_collegetypeid, fk_cityid)
                    OUTPUT INSERTED.pk_collegeid
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, [data['name'], data['code'], data['address'], data['contactperson'], data['contactno'],
                    data['email'], data['website'], loc_id, data['remarks'], 
                    type_id, city_id])
                cid = cursor.fetchone()[0]

            deans = data.getlist('dean_id[]')
            dean_names = data.getlist('dean_name[]')
            dean_abouts = data.getlist('dean_about[]')
            from_dates = data.getlist('from_date[]')
            to_dates = data.getlist('to_date[]')

            for i in range(len(deans)):
                if deans[i] and str(deans[i]).strip():
                    cursor.execute("""
                        INSERT INTO SMS_College_Dtl (fk_collegeid, fk_deanid, Deanname, deanhistory, fromdate, todate)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, [cid, deans[i], dean_names[i], dean_abouts[i], 
                          from_dates[i] if from_dates[i] else None, 
                          to_dates[i] if to_dates[i] else None])
            
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def get_cities():
        sal_cities = DB.fetch_all("SELECT pk_cityid as id, cityname as name FROM SAL_City_Mst WHERE cityname IS NOT NULL ORDER BY cityname")
        if sal_cities:
            for c in sal_cities:
                if c.get('name') and 'hisar' in str(c.get('name')).lower():
                    return sal_cities
        return DB.fetch_all("SELECT Pk_Cityid as id, Cityname as name FROM Common_City_mst ORDER BY Cityname")

    @staticmethod
    def get_college_full_details(college_id):
        college = DB.fetch_one("""
            SELECT *
            FROM SMS_College_Mst
            WHERE pk_collegeid = ?
        """, [college_id])
        if college:
            college['locname'] = None
            college['cityname'] = None
            if college.get('fk_locid'):
                try:
                    college['locname'] = DB.fetch_scalar("SELECT locname FROM Location_Mst WHERE pk_locid = ?", [college['fk_locid']])
                except Exception:
                    college['locname'] = None
            if college.get('fk_cityid'):
                try:
                    college['cityname'] = DB.fetch_scalar(
                        "SELECT TOP 1 cityname FROM SAL_City_Mst WHERE pk_cityid LIKE '%-' + CAST(? as varchar)",
                        [college['fk_cityid']]
                    )
                except Exception:
                    college['cityname'] = None
            if college.get('locname') and ',' in str(college.get('locname')):
                try:
                    loc_city = str(college.get('locname')).split(',', 1)[1].strip()
                    if loc_city:
                        if not college.get('cityname'):
                            college['cityname'] = loc_city
                        else:
                            if loc_city.lower() not in str(college.get('cityname')).lower():
                                college['cityname'] = loc_city
                except Exception:
                    pass
            if not college.get('cityname'):
                for key in college.keys():
                    k = str(key).lower()
                    if k in ('city', 'cityname', 'city_name') and college.get(key):
                        college['cityname'] = college.get(key)
                        break
            details = DB.fetch_all("SELECT * FROM SMS_College_Dtl WHERE fk_collegeid = ?", [college_id])
            for d in details:
                if d.get('fromdate'):
                    d['fromdate_iso'] = d['fromdate'].strftime('%Y-%m-%d')
                if d.get('todate'):
                    d['todate_iso'] = d['todate'].strftime('%Y-%m-%d')
            college['details'] = details
        return college

    @staticmethod
    def get_all_degrees():
        return DB.fetch_all("""
            SELECT D.pk_degreeid as id, D.degreename as name, T.isug, D.isphd
            FROM SMS_Degree_Mst D
            LEFT JOIN SMS_DegreeType_Mst T ON D.fk_degreetypeid = T.pk_degreetypeid
            WHERE D.degreename NOT LIKE '%---%'
            ORDER BY D.degreename
        """)

    @staticmethod
    def get_degrees_paginated(page=1, per_page=10):
        offset = (page - 1) * per_page
        total = DB.fetch_scalar("SELECT COUNT(*) FROM SMS_Degree_Mst")
        query = f"""
            SELECT D.*, T.degreetype
            FROM SMS_Degree_Mst D
            LEFT JOIN SMS_DegreeType_Mst T ON D.fk_degreetypeid = T.pk_degreetypeid
            ORDER BY D.degreename
            OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY
        """
        return DB.fetch_all(query), total

    @staticmethod
    def save_degree(data):
        is_phd = 1 if data.get('isphd') else 0
        dept_req = 1 if data.get('deptreq') else 0
        if data.get('pk_id'):
            return DB.execute("""
                UPDATE SMS_Degree_Mst SET degreename=?, degree_desc=?, DegreeCode=?, fk_degreetypeid=?,
                minsem=?, maxsem=?, isphd=?, isdepartmentreq=?, degreename_hindi=? WHERE pk_degreeid=?
            """, [data['name'], data.get('desc', ''), data['code'], data['type_id'],
                data.get('min_sem', 1), data.get('max_sem', 8), is_phd, dept_req, data.get('hindi_name'), data['pk_id']])
        else:
            return DB.execute("""
                INSERT INTO SMS_Degree_Mst (degreename, degree_desc, DegreeCode, fk_degreetypeid, minsem, maxsem, isphd, isdepartmentreq, degreename_hindi)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [data['name'], data.get('desc', ''), data['code'], data['type_id'],
                data.get('min_sem', 1), data.get('max_sem', 8), is_phd, dept_req, data.get('hindi_name')])

    @staticmethod
    def get_college_all_degrees(college_id):
        # Fetches ALL degrees (UG, PG, PhD, Diploma) offered by a specific college
        query = """
        SELECT DISTINCT D.pk_degreeid as id, D.degreename as name
        FROM SMS_CollegeDegreeBranchMap_Mst M
        INNER JOIN SMS_Degree_Mst D ON M.fk_Degreeid = D.pk_degreeid
        WHERE M.fk_CollegeId = ?
        ORDER BY D.degreename
        """
        return DB.fetch_all(query, [college_id])

    @staticmethod
    def get_college_pg_degrees(college_id):
        # Fetches PG degrees (Masters and Doctorate) offered by a specific college
        query = """
        SELECT DISTINCT D.pk_degreeid as id, D.degreename as name
        FROM SMS_CollegeDegreeBranchMap_Mst M
        INNER JOIN SMS_Degree_Mst D ON M.fk_Degreeid = D.pk_degreeid
        INNER JOIN SMS_DegreeType_Mst T ON D.fk_degreetypeid = T.pk_degreetypeid
        WHERE M.fk_CollegeId = ? AND T.isug IN ('M', 'P')
        ORDER BY D.degreename
        """
        return DB.fetch_all(query, [college_id])

    @staticmethod
    def get_college_ug_degrees(college_id):
        # Fetches UG degrees (Bachelors) offered by a specific college
        query = """
        SELECT DISTINCT D.pk_degreeid as id, D.degreename as name
        FROM SMS_CollegeDegreeBranchMap_Mst M
        INNER JOIN SMS_Degree_Mst D ON M.fk_Degreeid = D.pk_degreeid
        INNER JOIN SMS_DegreeType_Mst T ON D.fk_degreetypeid = T.pk_degreetypeid
        WHERE M.fk_CollegeId = ? AND T.isug = 'B'
        ORDER BY D.degreename
        """
        return DB.fetch_all(query, [college_id])

    @staticmethod
    def get_college_degrees(college_id):
        # Fetches ALL degrees offered by a specific college (for legacy API compatibility)
        query = """
        SELECT DISTINCT D.pk_degreeid as id, D.degreename as name, T.isug, D.isphd
        FROM SMS_CollegeDegreeBranchMap_Mst M
        INNER JOIN SMS_Degree_Mst D ON M.fk_Degreeid = D.pk_degreeid
        LEFT JOIN SMS_DegreeType_Mst T ON D.fk_degreetypeid = T.pk_degreetypeid
        WHERE M.fk_CollegeId = ?
        ORDER BY D.degreename
        """
        return DB.fetch_all(query, [college_id])

    @staticmethod
    def get_college_degree_specializations(college_id, degree_id):
        # Fetches specializations for a college-degree combination
        query = """
        SELECT DISTINCT B.Pk_BranchId as id, B.Branchname as name
        FROM SMS_CollegeDegreeBranchMap_dtl D
        INNER JOIN SMS_CollegeDegreeBranchMap_Mst M ON D.fk_Coldgbrmapid = M.PK_Coldgbrid
        INNER JOIN SMS_BranchMst B ON D.fk_BranchId = B.Pk_BranchId
        WHERE M.fk_CollegeId = ? AND M.fk_Degreeid = ?
        ORDER BY B.Branchname
        """
        return DB.fetch_all(query, [college_id, degree_id])

    @staticmethod
    def get_branches(faculty_id=None, sql_limit=""):
        query = "SELECT B.*, F.faculty FROM SMS_BranchMst B LEFT JOIN SMS_Faculty_Mst F ON B.Fk_Faculty_id = F.pk_facultyid"
        params = []
        if faculty_id:
            query += " WHERE B.Fk_Faculty_id = ?"
            params.append(faculty_id)
        query += f" ORDER BY B.Branchname {sql_limit}"
        return DB.fetch_all(query, params)

    @staticmethod
    def get_branches_paginated(page=1, per_page=10):
        offset = (page - 1) * per_page
        total = DB.fetch_scalar("SELECT COUNT(*) FROM SMS_BranchMst")
        query = f"""
            SELECT B.*, F.faculty 
            FROM SMS_BranchMst B 
            LEFT JOIN SMS_Faculty_Mst F ON B.Fk_Faculty_id = F.pk_facultyid
            ORDER BY B.Branchname 
            OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY
        """
        return DB.fetch_all(query), total

    @staticmethod
    def save_branch(data):
        if data.get('pk_id'):
            return DB.execute("UPDATE SMS_BranchMst SET Branchname=?, alias=?, Branchname_hindi=?, Fk_Faculty_id=?, Isactive=?, Remarks=? WHERE Pk_BranchId=?",
                            [data['branchname'], data['alias'], data['branchname_hindi'], data['faculty_id'], 1 if data.get('active') else 0, data['remarks'], data['pk_id']])  
        else:
            return DB.execute("INSERT INTO SMS_BranchMst (Branchname, alias, Branchname_hindi, Fk_Faculty_id, Isactive, Remarks) VALUES (?, ?, ?, ?, ?, ?)",
                            [data['branchname'], data['alias'], data['branchname_hindi'], data['faculty_id'], 1 if data.get('active') else 0, data['remarks']])

    @staticmethod
    def get_mapping_details(map_id):
        details = []
        # Major specializations from legacy detail table
        rows = DB.fetch_all("""
            SELECT D.fk_BranchId, D.Remarks, D.coursetype, B.Branchname as specialization
            FROM SMS_CollegeDegreeBranchMap_dtl D
            INNER JOIN SMS_BranchMst B ON D.fk_BranchId = B.Pk_BranchId
            WHERE D.fk_Coldgbrmapid = ?
        """, [map_id])
        for r in rows:
            ct = (r.get('coursetype') or '').strip()
            spec_type = 'Major'
            if ct:
                if ct.upper() in ('MA', 'M', 'MAJOR'):
                    spec_type = 'Major'
                elif ct.upper() in ('MI', 'MINOR'):
                    spec_type = 'Minor'
                elif ct.upper() in ('S', 'SUP', 'SUPPORTING'):
                    spec_type = 'Supporting'
            details.append({
                'fk_BranchId': r.get('fk_BranchId'),
                'Remarks': r.get('Remarks'),
                'SpecializationType': spec_type,
                'specialization': r.get('specialization')
            })

        # Minor/Supporting from new detail table if present
        if AcademicsModel._table_exists('SMS_CollegeDegreeBranchMap_dtlnew'):
            rows2 = DB.fetch_all("""
                SELECT D.branchid as fk_BranchId, D.Remarks, D.coursetype, B.Branchname as specialization
                FROM SMS_CollegeDegreeBranchMap_dtlnew D
                INNER JOIN SMS_BranchMst B ON D.branchid = B.Pk_BranchId
                WHERE D.fk_Coldgbrmapnewid = ?
            """, [map_id])
            for r in rows2:
                ct = (r.get('coursetype') or '').strip().upper()
                if ct in ('M', 'MI', 'MINOR'):
                    spec_type = 'Minor'
                elif ct in ('S', 'SUP', 'SUPPORTING'):
                    spec_type = 'Supporting'
                else:
                    spec_type = 'Supporting'
                details.append({
                    'fk_BranchId': r.get('fk_BranchId'),
                    'Remarks': r.get('Remarks'),
                    'SpecializationType': spec_type,
                    'specialization': r.get('specialization')
                })

        def type_rank(t):
            if t == 'Major':
                return 1
            if t == 'Minor':
                return 2
            if t == 'Supporting':
                return 3
            return 9
        details.sort(key=lambda x: ((x.get('specialization') or '').lower(), type_rank(x.get('SpecializationType'))))
        return details

    @staticmethod
    def get_college_degree_mappings_paginated(page=1, per_page=10):
        offset = (page - 1) * per_page
        total = DB.fetch_scalar("SELECT COUNT(*) FROM SMS_CollegeDegreeBranchMap_Mst")
        query = f"""
            SELECT M.*, C.collegename, D.degreename
            FROM SMS_CollegeDegreeBranchMap_Mst M
            INNER JOIN SMS_College_Mst C ON M.fk_CollegeId = C.pk_collegeid
            INNER JOIN SMS_Degree_Mst D ON M.fk_Degreeid = D.pk_degreeid
            ORDER BY C.collegename, D.degreename
            OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY
        """
        return DB.fetch_all(query), total

    @staticmethod
    def get_college_degree_spec_types():
        # As per live template: Major, Minor, Supporting
        return [
            {'id': 'Major', 'name': 'Major'},
            {'id': 'Minor', 'name': 'Minor'},
            {'id': 'Supporting', 'name': 'Supporting'}
        ]

    @staticmethod
    def save_mapping(data):
        conn = DB.get_connection()
        cursor = conn.cursor()
        try:
            college_id = data['college_id']
            degree_id = data['degree_id']
            remarks = data.get('remarks')
            spec_ids = data.getlist('spec_ids[]')
            spec_types = data.getlist('spec_types[]')
            spec_remarks = data.getlist('spec_remarks[]')

            degree_meta = DB.fetch_one("""
                SELECT D.isphd, T.isug
                FROM SMS_Degree_Mst D
                LEFT JOIN SMS_DegreeType_Mst T ON D.fk_degreetypeid = T.pk_degreetypeid
                WHERE D.pk_degreeid = ?
            """, [degree_id])
            allow_specs = False
            if degree_meta:
                isug = (degree_meta.get('isug') or '').strip()
                if isug in ('M', 'P'):
                    allow_specs = True
                elif degree_meta.get('isphd'):
                    allow_specs = True

            if data.get('pk_id'):
                map_id = data['pk_id']
                cursor.execute("UPDATE SMS_CollegeDegreeBranchMap_Mst SET fk_CollegeId=?, fk_Degreeid=?, Remarks=? WHERE PK_Coldgbrid=?",
                               [college_id, degree_id, remarks, map_id])
                cursor.execute("DELETE FROM SMS_CollegeDegreeBranchMap_dtl WHERE fk_Coldgbrmapid=?", [map_id])
                if AcademicsModel._table_exists('SMS_CollegeDegreeBranchMap_dtlnew'):
                    cursor.execute("DELETE FROM SMS_CollegeDegreeBranchMap_dtlnew WHERE fk_Coldgbrmapnewid=?", [map_id])
            else:
                cursor.execute("INSERT INTO SMS_CollegeDegreeBranchMap_Mst (fk_CollegeId, fk_Degreeid, Remarks) OUTPUT INSERTED.PK_Coldgbrid VALUES (?, ?, ?)",
                               [college_id, degree_id, remarks])
                map_id = cursor.fetchone()[0]

            if allow_specs:
                for i in range(len(spec_ids)):
                    if spec_ids[i]:
                        stype = (spec_types[i] or '').strip()
                        if stype.lower() == 'major':
                            cursor.execute("INSERT INTO SMS_CollegeDegreeBranchMap_dtl (fk_Coldgbrmapid, fk_BranchId, coursetype, Remarks) VALUES (?, ?, ?, ?)",
                                           [map_id, spec_ids[i], 'Ma', spec_remarks[i]])
                        elif stype.lower() == 'minor':
                            if AcademicsModel._table_exists('SMS_CollegeDegreeBranchMap_dtlnew'):
                                cursor.execute("INSERT INTO SMS_CollegeDegreeBranchMap_dtlnew (fk_Coldgbrmapnewid, branchid, coursetype, Remarks) VALUES (?, ?, ?, ?)",
                                               [map_id, spec_ids[i], 'M', spec_remarks[i]])
                        elif stype.lower() == 'supporting':
                            if AcademicsModel._table_exists('SMS_CollegeDegreeBranchMap_dtlnew'):
                                cursor.execute("INSERT INTO SMS_CollegeDegreeBranchMap_dtlnew (fk_Coldgbrmapnewid, branchid, coursetype, Remarks) VALUES (?, ?, ?, ?)",
                                               [map_id, spec_ids[i], 'S', spec_remarks[i]])

            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def delete_mapping(id):
        return DB.execute("DELETE FROM SMS_CollegeDegreeBranchMap_Mst WHERE PK_Coldgbrid = ?", [id])

    @staticmethod
    def get_degree_years():
        return DB.fetch_all("SELECT * FROM SMS_DegreeYear_Mst ORDER BY dgyearorder")

    @staticmethod
    def get_degree_years_paginated(page=1, per_page=10):
        offset = (page - 1) * per_page
        total = DB.fetch_scalar("SELECT COUNT(*) FROM SMS_DegreeYear_Mst")
        query = f"""
            SELECT * FROM SMS_DegreeYear_Mst 
            ORDER BY dgyearorder 
            OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY
        """
        return DB.fetch_all(query), total

    @staticmethod
    def save_degree_year(data):
        if data.get('pk_id'):
            return DB.execute("UPDATE SMS_DegreeYear_Mst SET degreeyear_char=?, degreeyear_int=?, degreeyear_roman=?, dgyearorder=? WHERE pk_degreeyearid=?",
                [data['char'], data['int_val'], data['roman'], data['order'], data['pk_id']])
        else:
            return DB.execute("INSERT INTO SMS_DegreeYear_Mst (degreeyear_char, degreeyear_int, degreeyear_roman, dgyearorder) VALUES (?, ?, ?, ?)",
                [data['char'], data['int_val'], data['roman'], data['order']])

    @staticmethod
    def get_degree_cycles_paginated(page=1, per_page=10):
        offset = (page - 1) * per_page
        total = DB.fetch_scalar("SELECT COUNT(*) FROM SMS_DegreeCycle_Mst")
        query = f"""
            SELECT C.*, D.degreename, B.Branchname, Y.degreeyear_char, S.semester_roman
            FROM SMS_DegreeCycle_Mst C
            INNER JOIN SMS_Degree_Mst D ON C.fk_degreeid = D.pk_degreeid
            LEFT JOIN SMS_BranchMst B ON C.fk_branchid = B.Pk_BranchId
            LEFT JOIN SMS_DegreeYear_Mst Y ON C.fk_degreeyearid = Y.pk_degreeyearid
            LEFT JOIN SMS_Semester_Mst S ON C.fk_semesterid = S.pk_semesterid
            ORDER BY C.pk_degreecycleid
            OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY
        """
        return DB.fetch_all(query), total

    @staticmethod
    def save_degree_cycle(data):
        min_ogpa = data.get('min_ogpa', 0)
        auto_alloc = 1 if data.get('auto_alloc') else 0
        inc_num = data.get('inc_num', 0)
        inc_by = data.get('inc_by', 0)
        
        if data.get('pk_id'):
            return DB.execute("""
                UPDATE SMS_DegreeCycle_Mst SET fk_degreeid=?, fk_branchid=?, fk_degreeyearid=?,
                fk_semesterid=?, MinOGPA=?, AutoCourseAlloc=?, incnum=?, incby=? WHERE pk_degreecycleid=?
            """, [data['degree_id'], data.get('branch_id'), data['year_id'], data['sem_id'],
                min_ogpa, auto_alloc, inc_num, inc_by, data['pk_id']])
        else:
            return DB.execute("""
                INSERT INTO SMS_DegreeCycle_Mst (fk_degreeid, fk_branchid, fk_degreeyearid, fk_semesterid, MinOGPA, AutoCourseAlloc, incnum, incby)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, [data['degree_id'], data.get('branch_id'), data['year_id'], data['sem_id'],
                min_ogpa, auto_alloc, inc_num, inc_by])

    @staticmethod
    def get_employee_degree_mappings_paginated(page=1, per_page=10):
        offset = (page - 1) * per_page
        total = DB.fetch_scalar("SELECT COUNT(*) FROM SMS_EmployeeDegreeMap")
        query = f"""
            SELECT M.*, E.empname, D.degreename, C.collegename
            FROM SMS_EmployeeDegreeMap M 
            INNER JOIN UM_Users_Mst U ON M.FK_USERID = U.pk_userId
            INNER JOIN SAL_Employee_Mst E ON U.fk_empId = E.pk_empid 
            INNER JOIN SMS_Degree_Mst D ON M.FK_DegreeID = D.pk_degreeid 
            LEFT JOIN SMS_College_Mst C ON M.fk_collegeid = C.pk_collegeid
            ORDER BY E.empname 
            OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY
        """
        return DB.fetch_all(query), total

    @staticmethod
    def get_degree_branches(degree_id):
        return DB.fetch_all("""
            SELECT DISTINCT B.Pk_BranchId as id, B.BranchName as name
            FROM SMS_BranchMst B
            INNER JOIN SMS_DegreeCycle_Mst C ON B.Pk_BranchId = C.fk_branchid
            WHERE C.fk_degreeid = ?
            ORDER BY B.BranchName
        """, [degree_id])

    @staticmethod
    def get_degree_departments(degree_id):
        query = """
        SELECT DISTINCT B.Pk_BranchId as id, B.Branchname as name
        FROM SMS_CollegeDegreeBranchMap_dtl D
        INNER JOIN SMS_BranchMst B ON D.fk_BranchId = B.Pk_BranchId
        INNER JOIN SMS_CollegeDegreeBranchMap_Mst M ON D.fk_Coldgbrmapid = M.PK_Coldgbrid
        WHERE M.fk_Degreeid = ?
        ORDER BY B.Branchname
        """
        return DB.fetch_all(query, [degree_id])

    @staticmethod
    def save_employee_degree_mapping(data):
        user_id = data['user_id']
        college_id = data['college_id']
        degree_ids = data.getlist('degree_ids')
        conn = DB.get_connection()
        cursor = conn.cursor()
        try:
            for did in degree_ids:
                exists = DB.fetch_scalar("SELECT COUNT(*) FROM SMS_EmployeeDegreeMap WHERE FK_USERID=? AND FK_DegreeID=? AND fk_collegeid=?", [user_id, did, college_id])
                if not exists:
                    cursor.execute("INSERT INTO SMS_EmployeeDegreeMap (FK_USERID, FK_DegreeID, fk_collegeid, createdDate) VALUES (?, ?, ?, GETDATE())",
                                 [user_id, did, college_id])
            conn.commit()
            return True
        except:
            conn.rollback()
            return False
        finally:
            conn.close()

    @staticmethod
    def delete_employee_degree_mapping(map_id):
        return DB.execute("DELETE FROM SMS_EmployeeDegreeMap WHERE PK_EmDgMapID = ?", [map_id])

    @staticmethod
    def get_degree_crhr(page=1, per_page=10):
        offset = (page - 1) * per_page
        total = DB.fetch_scalar("SELECT COUNT(*) FROM SMS_Degreewise_crhr")
        query = f"""
            SELECT C.pk_degreewise_crhr as id, C.totalmincrhr as total_crhr, 
            D.degreename, S.semester_roman, C.fk_degreeid, C.fk_semesterid
            FROM SMS_Degreewise_crhr C
            INNER JOIN SMS_Degree_Mst D ON C.fk_degreeid = D.pk_degreeid
            INNER JOIN SMS_Semester_Mst S ON C.fk_semesterid = S.pk_semesterid
            ORDER BY D.degreename, S.semesterorder
            OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY
        """
        return DB.fetch_all(query), total

    @staticmethod
    def _get_table_columns(table_name):
        cols = DB.fetch_all(f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{table_name}'")
        return [c['COLUMN_NAME'] for c in cols]

    @staticmethod
    def _table_exists(table_name):
        return DB.fetch_scalar("SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = ?", [table_name]) > 0

    @staticmethod
    def _pick_column(cols, preferred):
        lower_map = {c.lower(): c for c in cols}
        for key in preferred:
            if key.lower() in lower_map:
                return lower_map[key.lower()]
        return None

    @staticmethod
    def _pick_pk(cols):
        for c in cols:
            cl = c.lower()
            if cl.startswith('pk_') and 'crhr' in cl:
                return c
        for c in cols:
            if c.lower().startswith('pk_'):
                return c
        return cols[0] if cols else None

    @staticmethod
    def _pick_degree_col(cols):
        return AcademicsModel._pick_column(cols, ['fk_degreeid', 'degreeid', 'fk_degree_id'])

    @staticmethod
    def _pick_fk_col(cols, master_pk):
        if master_pk and master_pk.lower().startswith('pk_'):
            candidate = f"fk_{master_pk[3:]}"
            picked = AcademicsModel._pick_column(cols, [candidate])
            if picked:
                return picked
        for c in cols:
            cl = c.lower()
            if cl.startswith('fk_') and 'crhr' in cl and 'id' in cl:
                return c
        return None

    @staticmethod
    def _pick_course_type_col(cols):
        return AcademicsModel._pick_column(cols, ['fk_coursetypeid', 'courseplanid', 'fk_courseplanid', 'fk_coursetype_id'])

    @staticmethod
    def _pick_min_col(cols):
        for c in cols:
            cl = c.lower()
            if 'min' in cl and ('crhr' in cl or 'credit' in cl):
                return c
        return None

    @staticmethod
    def _pick_max_col(cols):
        for c in cols:
            cl = c.lower()
            if 'max' in cl and ('crhr' in cl or 'credit' in cl):
                return c
        return None

    @staticmethod
    def _quote_ident(name):
        return f"[{name.replace(']', ']]')}]"

    @staticmethod
    def _get_table_columns_info(table_name):
        return DB.fetch_all(f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{table_name}'")

    @staticmethod
    def _pick_batch_type_column(cols):
        # Prefer explicit theory/practical columns, then type
        for key in ['theory_practical', 'theorypractical', 'theory_pract', 'type_tp', 'batch_type', 'type']:
            picked = AcademicsModel._pick_column(cols, [key])
            if picked:
                return picked
        # Fallback: any column containing theory/practical/type
        for c in cols:
            cl = c.lower()
            if 'theory' in cl or 'practical' in cl or cl.endswith('type') or '_type' in cl:
                return c
        return None

    @staticmethod
    def _get_batch_type_fk_info():
        fk_rows = DB.fetch_all("""
            SELECT pc.name as parent_col, rt.name as ref_table, rc.name as ref_col
            FROM sys.foreign_key_columns fkc
            INNER JOIN sys.tables pt ON fkc.parent_object_id = pt.object_id
            INNER JOIN sys.columns pc ON fkc.parent_object_id = pc.object_id AND fkc.parent_column_id = pc.column_id
            INNER JOIN sys.tables rt ON fkc.referenced_object_id = rt.object_id
            INNER JOIN sys.columns rc ON fkc.referenced_object_id = rc.object_id AND fkc.referenced_column_id = rc.column_id
            WHERE pt.name = 'SMS_Batch_Mst'
        """)
        if not fk_rows:
            return None
        batch_cols = [c['COLUMN_NAME'] for c in AcademicsModel._get_table_columns_info('SMS_Batch_Mst')]
        type_col = AcademicsModel._pick_batch_type_column(batch_cols)
        if type_col:
            for r in fk_rows:
                if (r.get('parent_col') or '').lower() == type_col.lower():
                    return r
        skip_cols = {'fk_collegeid', 'fk_sessionid', 'fk_degreeid', 'fk_semesterid', 'fk_branchid'}
        candidates = []
        for r in fk_rows:
            parent_col = r['parent_col']
            if parent_col and parent_col.lower() in skip_cols:
                continue
            candidates.append(r)
        if not candidates:
            return None
        # Prefer fk column with theory/practical/type in its name or ref table
        for r in candidates:
            pc = r['parent_col'].lower()
            rt = r['ref_table'].lower()
            if 'theory' in pc or 'practical' in pc or 'type' in pc or 'theory' in rt or 'practical' in rt or 'type' in rt:
                return r
        return candidates[0]

    @staticmethod
    def get_batch_type_lookup():
        # Try FK-based lookup first
        fk_info = AcademicsModel._get_batch_type_fk_info()
        if fk_info:
            ref_table = fk_info['ref_table']
            cols = AcademicsModel._get_table_columns_info(ref_table)
            col_list = [c['COLUMN_NAME'] for c in cols]
            name_col = AcademicsModel._pick_column(col_list, ['typename', 'type', 'name', 'description', 'theory_practical'])
            if name_col:
                ref_table_q = AcademicsModel._quote_ident(ref_table)
                name_col_q = AcademicsModel._quote_ident(name_col)
                ref_col_q = AcademicsModel._quote_ident(fk_info['ref_col'])
                rows = DB.fetch_all(f"SELECT {ref_col_q} as id, {name_col_q} as name FROM {ref_table_q} ORDER BY {name_col_q}")
                if rows:
                    return rows
        # Fallback: distinct values from batch table
        batch_cols = [c['COLUMN_NAME'] for c in AcademicsModel._get_table_columns_info('SMS_Batch_Mst')]
        type_col = AcademicsModel._pick_batch_type_column(batch_cols)
        if not type_col:
            return []
        type_col_q = AcademicsModel._quote_ident(type_col)
        rows = DB.fetch_all(f"SELECT DISTINCT {type_col_q} as id FROM SMS_Batch_Mst WHERE {type_col_q} IS NOT NULL ORDER BY {type_col_q}")
        result = []
        for r in rows:
            val = r['id']
            norm = str(val).strip()
            label = norm
            if norm.upper() in ('T', 'TH', 'THEORY', '1'):
                label = 'Theory'
            elif norm.upper() in ('P', 'PR', 'PRACTICAL', '0'):
                label = 'Practical'
            result.append({'id': norm, 'name': label})
        return result

    @staticmethod
    def get_degree_crhr_courseplan_paginated(page=1, per_page=10):
        master_table = 'SMS_Degreewise_crhr_CoursePlan'
        if not AcademicsModel._table_exists(master_table):
            return [], 0
        cols = AcademicsModel._get_table_columns(master_table)
        pk_col = AcademicsModel._pick_pk(cols)
        deg_col = AcademicsModel._pick_degree_col(cols)
        if not pk_col or not deg_col:
            return [], 0

        offset = (page - 1) * per_page
        total = DB.fetch_scalar(f"SELECT COUNT(*) FROM {master_table}")
        query = f"""
            SELECT M.{pk_col} as id, M.{deg_col} as degree_id, D.degreename
            FROM {master_table} M
            INNER JOIN SMS_Degree_Mst D ON M.{deg_col} = D.pk_degreeid
            ORDER BY D.degreename
            OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY
        """
        return DB.fetch_all(query), total

    @staticmethod
    def get_degree_crhr_courseplan_details(master_id):
        master_table = 'SMS_Degreewise_crhr_CoursePlan'
        detail_table = 'SMS_Degreewise_crhr_Trn_CP'
        if not AcademicsModel._table_exists(master_table) or not AcademicsModel._table_exists(detail_table):
            return None, []

        mcols = AcademicsModel._get_table_columns(master_table)
        pk_col = AcademicsModel._pick_pk(mcols)
        deg_col = AcademicsModel._pick_degree_col(mcols)
        if not pk_col:
            return None, []

        dcols = AcademicsModel._get_table_columns(detail_table)
        fk_col = AcademicsModel._pick_fk_col(dcols, pk_col)
        ct_col = AcademicsModel._pick_course_type_col(dcols)
        min_col = AcademicsModel._pick_min_col(dcols)
        max_col = AcademicsModel._pick_max_col(dcols)
        if not fk_col or not ct_col:
            return None, []

        master = DB.fetch_one(f"SELECT * FROM {master_table} WHERE {pk_col} = ?", [master_id])
        if master and deg_col:
            master['degree_id'] = master.get(deg_col)
        details = DB.fetch_all(f"""
            SELECT D.{ct_col} as course_type_id,
                   T.coursetype as course_type,
                   {min_col if min_col else 'NULL'} as min_crhr,
                   {max_col if max_col else 'NULL'} as max_crhr
            FROM {detail_table} D
            LEFT JOIN SMS_CourseType_Mst T ON D.{ct_col} = T.pk_coursetypeid
            WHERE D.{fk_col} = ?
            ORDER BY T.coursetype
        """, [master_id])
        return master, details

    @staticmethod
    def save_degree_crhr_courseplan(data):
        master_table = 'SMS_Degreewise_crhr_CoursePlan'
        detail_table = 'SMS_Degreewise_crhr_Trn_CP'
        if not AcademicsModel._table_exists(master_table) or not AcademicsModel._table_exists(detail_table):
            return False

        mcols = AcademicsModel._get_table_columns(master_table)
        pk_col = AcademicsModel._pick_pk(mcols)
        deg_col = AcademicsModel._pick_degree_col(mcols)
        if not pk_col or not deg_col:
            return False

        dcols = AcademicsModel._get_table_columns(detail_table)
        fk_col = AcademicsModel._pick_fk_col(dcols, pk_col)
        ct_col = AcademicsModel._pick_course_type_col(dcols)
        min_col = AcademicsModel._pick_min_col(dcols)
        max_col = AcademicsModel._pick_max_col(dcols)
        if not fk_col or not ct_col:
            return False

        conn = DB.get_connection()
        cursor = conn.cursor()
        try:
            degree_id = data.get('degree_id')
            pk_id = data.get('pk_id')
            if pk_id:
                cursor.execute(f"UPDATE {master_table} SET {deg_col}=? WHERE {pk_col}=?", [degree_id, pk_id])
                master_id = pk_id
                cursor.execute(f"DELETE FROM {detail_table} WHERE {fk_col}=?", [master_id])
            else:
                cursor.execute(f"INSERT INTO {master_table} ({deg_col}) OUTPUT INSERTED.{pk_col} VALUES (?)", [degree_id])
                master_id = cursor.fetchone()[0]

            course_types = data.getlist('course_type_id[]')
            min_vals = data.getlist('min_crhr[]')
            max_vals = data.getlist('max_crhr[]')

            for i in range(len(course_types)):
                ct = course_types[i]
                if ct and str(ct).strip():
                    vals = [master_id, ct]
                    cols = [fk_col, ct_col]
                    if min_col:
                        cols.append(min_col)
                        vals.append(min_vals[i] if i < len(min_vals) and str(min_vals[i]).strip() else None)
                    if max_col:
                        cols.append(max_col)
                        vals.append(max_vals[i] if i < len(max_vals) and str(max_vals[i]).strip() else None)
                    col_list = ", ".join(cols)
                    q_marks = ", ".join(["?"] * len(vals))
                    cursor.execute(f"INSERT INTO {detail_table} ({col_list}) VALUES ({q_marks})", vals)

            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def delete_degree_crhr_courseplan(master_id):
        master_table = 'SMS_Degreewise_crhr_CoursePlan'
        detail_table = 'SMS_Degreewise_crhr_Trn_CP'
        if not AcademicsModel._table_exists(master_table) or not AcademicsModel._table_exists(detail_table):
            return False

        mcols = AcademicsModel._get_table_columns(master_table)
        pk_col = AcademicsModel._pick_pk(mcols)
        if not pk_col:
            return False

        dcols = AcademicsModel._get_table_columns(detail_table)
        fk_col = AcademicsModel._pick_fk_col(dcols, pk_col)
        if not fk_col:
            return False

        conn = DB.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(f"DELETE FROM {detail_table} WHERE {fk_col}=?", [master_id])
            cursor.execute(f"DELETE FROM {master_table} WHERE {pk_col}=?", [master_id])
            conn.commit()
            return True
        except:
            conn.rollback()
            return False
        finally:
            conn.close()

    @staticmethod
    def save_degree_crhr(data):
        if data.get('pk_id'):
            return DB.execute("""
                UPDATE SMS_Degreewise_crhr SET fk_degreeid=?, fk_semesterid=?, totalmincrhr=?
                WHERE pk_degreewise_crhr=?
            """, [data['degree_id'], data['sem_id'], data['total_crhr'], data['pk_id']])
        else:
            return DB.execute("""
                INSERT INTO SMS_Degreewise_crhr (fk_degreeid, fk_semesterid, totalmincrhr)
                VALUES (?, ?, ?)
            """, [data['degree_id'], data['sem_id'], data['total_crhr']])

    @staticmethod
    def get_batches(page=1, per_page=10):
        offset = (page - 1) * per_page
        total = DB.fetch_scalar("SELECT COUNT(*) FROM SMS_Batch_Mst")
        batch_cols = [c['COLUMN_NAME'] for c in AcademicsModel._get_table_columns_info('SMS_Batch_Mst')]
        type_col = AcademicsModel._pick_batch_type_column(batch_cols) or 'theory_practical'
        type_col_q = AcademicsModel._quote_ident(type_col)
        fk_info = AcademicsModel._get_batch_type_fk_info()
        join_sql = ""
        label_select = f"""
            CASE 
                WHEN UPPER(LTRIM(RTRIM(CAST(B.{type_col_q} as varchar(10))))) IN ('T','TH','THEORY') THEN 'Theory'
                WHEN UPPER(LTRIM(RTRIM(CAST(B.{type_col_q} as varchar(10))))) IN ('P','PR','PRACTICAL') THEN 'Practical'
                WHEN TRY_CONVERT(int, B.{type_col_q}) = 1 THEN 'Theory'
                WHEN TRY_CONVERT(int, B.{type_col_q}) = 0 THEN 'Practical'
                ELSE LTRIM(RTRIM(CAST(B.{type_col_q} as varchar(10))))
            END as theory_practical_label
        """
        if fk_info:
            ref_table_q = AcademicsModel._quote_ident(fk_info['ref_table'])
            ref_col_q = AcademicsModel._quote_ident(fk_info['ref_col'])
            parent_col_q = AcademicsModel._quote_ident(fk_info['parent_col'])
            cols = AcademicsModel._get_table_columns_info(fk_info['ref_table'])
            col_list = [c['COLUMN_NAME'] for c in cols]
            name_col = AcademicsModel._pick_column(col_list, ['typename', 'type', 'name', 'description', 'theory_practical'])
            if name_col:
                name_col_q = AcademicsModel._quote_ident(name_col)
                join_sql = f"LEFT JOIN {ref_table_q} BT ON B.{parent_col_q} = BT.{ref_col_q}"
                label_select = f"BT.{name_col_q} as theory_practical_label"
                type_col_q = parent_col_q

        query = f"""
            SELECT B.*, C.collegename, S.sessionname, D.degreename, SEM.semester_roman, BR.Branchname as specialization,
                   {label_select},
                   LTRIM(RTRIM(CAST(B.{type_col_q} as varchar(10)))) as theory_practical_value
            FROM SMS_Batch_Mst B
            INNER JOIN SMS_College_Mst C ON B.fk_collegeid = C.pk_collegeid
            INNER JOIN SMS_AcademicSession_Mst S ON B.fk_sessionid = S.pk_sessionid
            INNER JOIN SMS_Degree_Mst D ON B.fk_degreeid = D.pk_degreeid
            INNER JOIN SMS_Semester_Mst SEM ON B.fk_semesterid = SEM.pk_semesterid
            LEFT JOIN SMS_BranchMst BR ON B.fk_branchid = BR.Pk_BranchId
            {join_sql}
            ORDER BY S.sessionorder ASC, C.collegename
            OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY
        """
        return DB.fetch_all(query), total

    @staticmethod
    def get_batches_filtered(filters):
        where_clause = "WHERE 1=1"
        params = []
        if filters.get('college_id') and str(filters['college_id']) != '0':
            where_clause += " AND B.fk_collegeid = ?"
            params.append(filters['college_id'])
        if filters.get('session_id') and str(filters['session_id']) != '0':
            where_clause += " AND B.fk_sessionid = ?"
            params.append(filters['session_id'])
        if filters.get('degree_id') and str(filters['degree_id']) != '0':
            where_clause += " AND B.fk_degreeid = ?"
            params.append(filters['degree_id'])
        if filters.get('semester_id') and str(filters['semester_id']) != '0':
            where_clause += " AND B.fk_semesterid = ?"
            params.append(filters['semester_id'])

        batch_cols = [c['COLUMN_NAME'] for c in AcademicsModel._get_table_columns_info('SMS_Batch_Mst')]
        type_col = AcademicsModel._pick_batch_type_column(batch_cols) or 'theory_practical'
        type_col_q = AcademicsModel._quote_ident(type_col)
        fk_info = AcademicsModel._get_batch_type_fk_info()
        join_sql = ""
        label_select = f"""
            CASE 
                WHEN UPPER(LTRIM(RTRIM(CAST(B.{type_col_q} as varchar(10))))) IN ('T','TH','THEORY') THEN 'Theory'
                WHEN UPPER(LTRIM(RTRIM(CAST(B.{type_col_q} as varchar(10))))) IN ('P','PR','PRACTICAL') THEN 'Practical'
                WHEN TRY_CONVERT(int, B.{type_col_q}) = 1 THEN 'Theory'
                WHEN TRY_CONVERT(int, B.{type_col_q}) = 0 THEN 'Practical'
                ELSE LTRIM(RTRIM(CAST(B.{type_col_q} as varchar(10))))
            END as theory_practical_label
        """
        if fk_info:
            ref_table_q = AcademicsModel._quote_ident(fk_info['ref_table'])
            ref_col_q = AcademicsModel._quote_ident(fk_info['ref_col'])
            parent_col_q = AcademicsModel._quote_ident(fk_info['parent_col'])
            cols = AcademicsModel._get_table_columns_info(fk_info['ref_table'])
            col_list = [c['COLUMN_NAME'] for c in cols]
            name_col = AcademicsModel._pick_column(col_list, ['typename', 'type', 'name', 'description', 'theory_practical'])
            if name_col:
                name_col_q = AcademicsModel._quote_ident(name_col)
                join_sql = f"LEFT JOIN {ref_table_q} BT ON B.{parent_col_q} = BT.{ref_col_q}"
                label_select = f"BT.{name_col_q} as theory_practical_label"
                type_col_q = parent_col_q

        query = f"""
            SELECT B.*, C.collegename, S.sessionname, D.degreename, SEM.semester_roman, BR.Branchname as specialization,
                   {label_select},
                   LTRIM(RTRIM(CAST(B.{type_col_q} as varchar(10)))) as theory_practical_value
            FROM SMS_Batch_Mst B
            INNER JOIN SMS_College_Mst C ON B.fk_collegeid = C.pk_collegeid
            INNER JOIN SMS_AcademicSession_Mst S ON B.fk_sessionid = S.pk_sessionid
            INNER JOIN SMS_Degree_Mst D ON B.fk_degreeid = D.pk_degreeid
            INNER JOIN SMS_Semester_Mst SEM ON B.fk_semesterid = SEM.pk_semesterid
            LEFT JOIN SMS_BranchMst BR ON B.fk_branchid = BR.Pk_BranchId
            {join_sql}
            {where_clause}
            ORDER BY S.sessionorder ASC, C.collegename, D.degreename, SEM.semesterorder
        """
        return DB.fetch_all(query, params)

    @staticmethod
    def save_batch(data):
        batch_cols = [c['COLUMN_NAME'] for c in AcademicsModel._get_table_columns_info('SMS_Batch_Mst')]
        college_col = AcademicsModel._pick_column(batch_cols, ['fk_collegeid', 'fk_college_id'])
        session_col = AcademicsModel._pick_column(batch_cols, ['fk_sessionid', 'fk_session_id'])
        degree_col = AcademicsModel._pick_column(batch_cols, ['fk_degreeid', 'fk_degree_id'])
        sem_col = AcademicsModel._pick_column(batch_cols, ['fk_semesterid', 'fk_semester_id'])
        branch_col = AcademicsModel._pick_column(batch_cols, ['fk_branchid', 'fk_branch_id'])
        count_col = AcademicsModel._pick_column(batch_cols, ['no_of_batch', 'no_of_batches', 'noofbatch', 'noofbatches'])

        type_col = AcademicsModel._pick_batch_type_column(batch_cols)
        fk_info = AcademicsModel._get_batch_type_fk_info()
        if fk_info:
            type_col = fk_info['parent_col']

        if not all([college_col, session_col, degree_col, sem_col, type_col, count_col]):
            return False

        def to_int_or_none(val):
            if val is None or str(val).strip() == '' or str(val) == '0':
                return None
            return val

        values = {
            college_col: data.get('college_id'),
            session_col: data.get('session_id'),
            degree_col: data.get('degree_id'),
            sem_col: data.get('sem_id'),
            type_col: data.get('type'),
            count_col: data.get('count', 1)
        }
        if branch_col:
            values[branch_col] = to_int_or_none(data.get('branch_id'))

        cols_q = [AcademicsModel._quote_ident(c) for c in values.keys()]
        vals = list(values.values())

        if data.get('pk_id'):
            set_clause = ", ".join([f"{c}=?" for c in cols_q])
            return DB.execute(f"UPDATE SMS_Batch_Mst SET {set_clause} WHERE pk_batchid=?", vals + [data['pk_id']])
        else:
            col_list = ", ".join(cols_q)
            q_marks = ", ".join(["?"] * len(vals))
            return DB.execute(f"INSERT INTO SMS_Batch_Mst ({col_list}) VALUES ({q_marks})", vals)

    @staticmethod
    def get_moderation_marks(page=1, per_page=10):
        offset = (page - 1) * per_page
        total = DB.fetch_scalar("SELECT COUNT(*) FROM SMS_Moderation_Dtl")
        query = f"""
            SELECT D.pk_pmid as id, D.marks, P.papertitle, DEG.degreename, S.semester_roman,
                   DEG.pk_degreeid, S.pk_semesterid, P.pk_papertitleid
            FROM SMS_Moderation_Dtl D
            INNER JOIN SMS_DegreeCycle_Mst C ON D.fk_moderationid = C.pk_degreecycleid
            INNER JOIN SMS_Degree_Mst DEG ON C.fk_degreeid = DEG.pk_degreeid
            INNER JOIN SMS_Semester_Mst S ON C.fk_semesterid = S.pk_semesterid
            LEFT JOIN SMS_PaperTitle_Mst P ON D.fk_papertitleid = P.pk_papertitleid
            ORDER BY DEG.degreename, S.semesterorder
            OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY
        """
        return DB.fetch_all(query), total

    @staticmethod
    def save_moderation_marks(data):
        cycle = DB.fetch_one("SELECT pk_degreecycleid FROM SMS_DegreeCycle_Mst WHERE fk_degreeid=? AND fk_semesterid=?",
                           [data['degree_id'], data['sem_id']])
        if not cycle: return False
        if data.get('pk_id'):
            return DB.execute("""
                UPDATE SMS_Moderation_Dtl SET fk_moderationid=?, marks=?, fk_papertitleid=?
                WHERE pk_pmid=?
            """, [cycle['pk_degreecycleid'], data['marks'], data.get('paper_title_id'), data['pk_id']])
        else:
            return DB.execute("""
                INSERT INTO SMS_Moderation_Dtl (fk_moderationid, marks, fk_papertitleid)
                VALUES (?, ?, ?)
            """, [cycle['pk_degreecycleid'], data['marks'], data.get('paper_title_id')])

    @staticmethod
    def delete_moderation_marks(id):
        return DB.execute("DELETE FROM SMS_Moderation_Dtl WHERE pk_pmid = ?", [id])

    @staticmethod
    def delete_batch(batch_id):
        return DB.execute("DELETE FROM SMS_Batch_Mst WHERE pk_batchid = ?", [batch_id])

    @staticmethod
    def delete_degree_crhr(crhr_id):
        return DB.execute("DELETE FROM SMS_Degreewise_crhr_Mst WHERE pk_crhrid = ?", [crhr_id])

    @staticmethod
    def delete_degree_cycle(cycle_id):
        return DB.execute("DELETE FROM SMS_DegreeCycle_Mst WHERE pk_degreecycleid = ?", [cycle_id])

    @staticmethod
    def delete_faculty(id):
        return DB.execute("DELETE FROM SMS_Faculty_Mst WHERE pk_facultyid = ?", [id])

    @staticmethod
    def delete_college(id):
        return DB.execute("DELETE FROM SMS_College_Mst WHERE pk_collegeid = ?", [id])

    @staticmethod
    def delete_degree(id):
        return DB.execute("DELETE FROM SMS_Degree_Mst WHERE pk_degreeid = ?", [id])

    @staticmethod
    def delete_degree_year(id):
        return DB.execute("DELETE FROM SMS_DegreeYear_Mst WHERE pk_degreeyearid = ?", [id])

    @staticmethod
    def delete_branch(id):
        return DB.execute("DELETE FROM SMS_BranchMst WHERE Pk_BranchId = ?", [id])

    @staticmethod
    def delete_degree_type(id):
        return DB.execute("DELETE FROM SMS_DegreeType_Mst WHERE pk_degreetypeid = ?", [id])

    @staticmethod
    def get_departments():
        return DB.fetch_all("SELECT pk_Deptid as id, Departmentname as name FROM SMS_Dept_Mst ORDER BY Departmentname")

    @staticmethod
    def get_degree_semesters_for_degree(degree_id):
        semesters = DB.fetch_all("""
            SELECT DISTINCT S.pk_semesterid as id, S.semester_roman as name, S.semesterorder
            FROM SMS_DegreeCycle_Mst C
            INNER JOIN SMS_Semester_Mst S ON C.fk_semesterid = S.pk_semesterid
            WHERE C.fk_degreeid = ?
            ORDER BY S.semesterorder
        """, [degree_id])
        if semesters:
            return semesters
        degree = DB.fetch_one("SELECT minsem, maxsem FROM SMS_Degree_Mst WHERE pk_degreeid = ?", [degree_id])
        if not degree:
            return []
        min_sem = degree.get('minsem') or 1
        max_sem = degree.get('maxsem') or 8
        if min_sem < 1:
            min_sem = 1
        if max_sem < min_sem:
            max_sem = min_sem
        return DB.fetch_all("""
            SELECT pk_semesterid as id, semester_roman as name, semesterorder
            FROM SMS_Semester_Mst
            WHERE semesterorder BETWEEN ? AND ?
            ORDER BY semesterorder
        """, [min_sem, max_sem])

    @staticmethod
    def get_semesters_for_degree_year(degree_id, year_id):
        if not degree_id or not year_id:
            return []
        rows = DB.fetch_all("""
            SELECT DISTINCT fk_semesterid
            FROM SMS_DegreeCycle_Mst
            WHERE fk_degreeid = ? AND fk_degreeyearid = ?
            ORDER BY fk_semesterid
        """, [degree_id, year_id])
        return [r['fk_semesterid'] for r in rows]

    @staticmethod
    @staticmethod
    def get_courses_for_degree_semester(degree_id, semester_id, course_type=None, sms_dept_ids=None, code_prefixes=None, is_hod_view=False):
        # Base SQL
        sql = """
            SELECT C.pk_courseid, C.coursecode, C.coursename,
                   C.crhr_theory, C.crhr_practical
            FROM SMS_Course_Mst C
            LEFT JOIN SMS_Course_Mst_Dtl D ON C.pk_courseid = D.fk_courseid
            WHERE 1=1
        """
        params = []
        
        if is_hod_view and sms_dept_ids:
            # Check if degree is PhD to decide 500 or 600 level
            # Some PhD degrees have isphd=false in database, so check name too
            degree = DB.fetch_one("SELECT isphd, degreename FROM SMS_Degree_Mst WHERE pk_degreeid = ?", [degree_id])
            is_phd = bool(degree and (degree.get('isphd') or 'Ph.D' in (degree.get('degreename') or '')))
            lp = '6' if is_phd else '5'
            
            placeholders = ",".join(["?"] * len(sms_dept_ids))
            dept_ids_params = list(sms_dept_ids)
            
            sql += f"""
                AND (
                    (C.coursecode = 'deleted' AND C.coursename IN ('Mathematical for applied sciences', 'Research Methodology in Forestry'))
                    OR (
                        (C.fk_Deptid IN ({placeholders}) OR D.fk_branchid IN ({placeholders}))
                        AND (
                            C.coursecode LIKE 'MATH%' OR C.coursecode LIKE 'Math%' OR C.coursecode LIKE 'math%' OR
                            C.coursecode LIKE 'STAT%' OR C.coursecode LIKE 'Stat%' OR C.coursecode LIKE 'stat%'
                        )
                        AND (
                            C.coursecode LIKE '% ' + ? + '[0-9]%' OR
                            C.coursecode LIKE '% ' + ? + '%' OR
                            C.coursecode LIKE '%/' + ? + '%'
                        )
                        AND C.coursecode NOT LIKE '%deleted%'
                        AND C.coursename NOT LIKE '%deleted%'
                    )
                )
            """
            params.extend(dept_ids_params)
            params.extend(dept_ids_params)
            params.extend([lp, lp, lp])
        else:
            # Regular filtering for others (Deans, etc.)
            sql += " AND ISNULL(C.isobsolete, 0) = 0 AND C.coursecode NOT LIKE '%deleted%' AND C.coursename NOT LIKE '%deleted%'"
            sql += " AND D.fk_degreeid = ? AND D.fk_semesterid = ?"
            params.extend([degree_id, semester_id])

        if course_type == 'T':
            sql += " AND ISNULL(C.crhr_theory, 0) > 0"
        elif course_type == 'P':
            sql += " AND ISNULL(C.crhr_practical, 0) > 0"
            
        sql += " ORDER BY CASE WHEN C.coursecode = 'deleted' THEN 1 ELSE 2 END, C.coursecode COLLATE Latin1_General_BIN ASC, C.coursename COLLATE Latin1_General_BIN ASC"
        return DB.fetch_all(sql, params)

    @staticmethod
    def get_courses_for_degree_semesters(degree_id, semester_ids, course_type=None, sms_dept_ids=None, code_prefixes=None, is_hod_view=False):
        if not semester_ids and not (is_hod_view and sms_dept_ids):
            return []
        
        sql = """
            SELECT C.pk_courseid, C.coursecode, C.coursename,
                   C.crhr_theory, C.crhr_practical
            FROM SMS_Course_Mst C
            LEFT JOIN SMS_Course_Mst_Dtl D ON C.pk_courseid = D.fk_courseid
            WHERE 1=1
        """
        params = []
        
        if is_hod_view and sms_dept_ids:
            # Check if degree is PhD to decide 500 or 600 level
            # Some PhD degrees have isphd=false in database, so check name too
            degree = DB.fetch_one("SELECT isphd, degreename FROM SMS_Degree_Mst WHERE pk_degreeid = ?", [degree_id])
            is_phd = bool(degree and (degree.get('isphd') or 'Ph.D' in (degree.get('degreename') or '')))
            lp = '6' if is_phd else '5'
            
            placeholders = ",".join(["?"] * len(sms_dept_ids))
            dept_ids_params = list(sms_dept_ids)
            
            sql += f"""
                AND (
                    (C.coursecode = 'deleted' AND C.coursename IN ('Mathematical for applied sciences', 'Research Methodology in Forestry'))
                    OR (
                        (C.fk_Deptid IN ({placeholders}) OR D.fk_branchid IN ({placeholders}))
                        AND (
                            C.coursecode LIKE 'MATH%' OR C.coursecode LIKE 'Math%' OR C.coursecode LIKE 'math%' OR
                            C.coursecode LIKE 'STAT%' OR C.coursecode LIKE 'Stat%' OR C.coursecode LIKE 'stat%'
                        )
                        AND (
                            C.coursecode LIKE '% ' + ? + '[0-9]%' OR
                            C.coursecode LIKE '% ' + ? + '%' OR
                            C.coursecode LIKE '%/' + ? + '%'
                        )
                        AND C.coursecode NOT LIKE '%deleted%'
                        AND C.coursename NOT LIKE '%deleted%'
                    )
                )
            """
            params.extend(dept_ids_params)
            params.extend(dept_ids_params)
            params.extend([lp, lp, lp])
        else:
            placeholders = ",".join(["?"] * len(semester_ids))
            sql += " AND ISNULL(C.isobsolete, 0) = 0 AND C.coursecode NOT LIKE '%deleted%' AND C.coursename NOT LIKE '%deleted%'"
            sql += f" AND D.fk_degreeid = ? AND D.fk_semesterid IN ({placeholders})"
            params.extend([degree_id] + list(semester_ids))

        if course_type == 'T':
            sql += " AND ISNULL(C.crhr_theory, 0) > 0"
        elif course_type == 'P':
            sql += " AND ISNULL(C.crhr_practical, 0) > 0"
            
        sql += " ORDER BY CASE WHEN C.coursecode = 'deleted' THEN 1 ELSE 2 END, C.coursecode COLLATE Latin1_General_BIN ASC, C.coursename COLLATE Latin1_General_BIN ASC"
        return DB.fetch_all(sql, params)

    @staticmethod
    def get_course_offer_master(filters):
        return DB.fetch_one("""
            SELECT Pk_courseallocid
            FROM SMS_CourseAllocationSemesterwiseByHOD
            WHERE fk_collegeid = ? AND fk_dgacasessionid = ? AND degreeid = ?
              AND fk_semesterid = ? AND fk_exconfigid = ?
              AND ISNULL(fk_specializationid, 0) = ?
              AND Yearid = ?
        """, [
            filters.get('college_id'),
            filters.get('session_id'),
            filters.get('degree_id'),
            filters.get('semester_id'),
            filters.get('exconfig_id'),
            filters.get('branch_id') or 0,
            filters.get('year_id')
        ])

    @staticmethod
    def get_course_offer_selected_course_ids(master_id):
        rows = DB.fetch_all("""
            SELECT fk_courseid
            FROM SMS_CourseAllocationSemesterwiseByHOD_Dtl
            WHERE fk_courseallocid = ?
        """, [master_id])
        return [r['fk_courseid'] for r in rows]

    @staticmethod
    def get_courses_offered_by_hod(filters, course_type=None, sms_dept_ids=None, code_prefixes=None):
        # We want to show ALL courses that the HOD CAN offer, to check which ones are assigned.
        # Use the same logic as course_offer_hod but with is_hod_view=True
        return AcademicsModel.get_courses_for_degree_semester(
            filters.get('degree_id'),
            filters.get('semester_id'),
            course_type,
            sms_dept_ids,
            code_prefixes,
            is_hod_view=True
        )

    @staticmethod
    @staticmethod
    def get_hod_department_context(emp_id):
        dept_rows = DB.fetch_all("SELECT pk_deptid, description FROM Department_Mst WHERE Hod_Id = ?", [emp_id])
        emp_row = DB.fetch_one("SELECT fk_deptid FROM SAL_Employee_Mst WHERE pk_empid = ?", [emp_id])
        if emp_row and emp_row.get('fk_deptid'):
            extra = DB.fetch_one("SELECT pk_deptid, description FROM Department_Mst WHERE pk_deptid = ?", [emp_row['fk_deptid']])
            if extra:
                dept_rows.append(extra)
        seen = set()
        hr_depts = []
        for d in dept_rows:
            key = str(d['pk_deptid']).strip()
            if key in seen:
                continue
            seen.add(key)
            hr_depts.append({'id': d['pk_deptid'], 'name': d['description']})
        
        # Get SMS Dept IDs by matching names
        sms_dept_ids = []
        if hr_depts:
            for d in hr_depts:
                clean_name = d['name'].replace('Department of', '').replace('Department Of', '').strip()
                # Split by 'and' or '&' to handle combined departments
                parts = [p.strip() for p in clean_name.replace(' and ', '|').replace('&', '|').split('|')]
                for p in parts:
                    if len(p) < 3: continue
                    res = DB.fetch_all("SELECT pk_Deptid FROM SMS_Dept_Mst WHERE Departmentname LIKE ?", [f"%{p}%"])
                    for r in res:
                        sms_dept_ids.append(r['pk_Deptid'])

        branches = []
        if hr_depts:
            placeholders = ",".join(["?"] * len(hr_depts))
            hr_dept_ids = [d['id'] for d in hr_depts]
            branches = DB.fetch_all(
                f"SELECT Pk_BranchId as id, Branchname as name, alias, fk_deptidDdo FROM SMS_BranchMst WHERE fk_deptidDdo IN ({placeholders})",
                hr_dept_ids
            )
        
        sms_dept_ids = list(set(sms_dept_ids))
        # Fallback to branch_ids if no SMS dept IDs found (often they are same)
        if not sms_dept_ids and branches:
            sms_dept_ids = [b['id'] for b in branches]

        code_prefixes = []
        for b in branches:
            alias = (b.get('alias') or b.get('name') or '')
            alias = "".join([c for c in alias.upper() if c.isalpha()])
            if not alias:
                continue
            code_prefixes.append(alias)
            if alias.endswith('S') and len(alias) > 4:
                code_prefixes.append(alias[:-1])
            if len(alias) > 4:
                code_prefixes.append(alias[:4])
        
        return {
            'hr_departments': hr_depts,
            'sms_dept_ids': sms_dept_ids,
            'branch_ids': [b['id'] for b in branches],
            'branches': branches,
            'code_prefixes': list(dict.fromkeys(code_prefixes))
        }

    @staticmethod
    def get_hod_departments(emp_id):
        ctx = AcademicsModel.get_hod_department_context(emp_id)
        return ctx.get('hr_departments', [])


    @staticmethod
    def get_teaching_employees(dept_ids=None, term=None):
        cols = DB.fetch_all("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='SAL_Designation_Mst'")
        col_set = {c['COLUMN_NAME'].lower() for c in cols}
        join_desg = "LEFT JOIN SAL_Designation_Mst DESG ON E.fk_desgid = DESG.pk_desgid"
        where = ["E.employeeleftstatus = 'N'"]
        params = []
        if 'isteaching' in col_set:
            where.append("ISNULL(DESG.isteaching, 0) = 1")
        if dept_ids:
            placeholders = ",".join(["?"] * len(dept_ids))
            where.append(f"E.fk_deptid IN ({placeholders})")
            params.extend(dept_ids)
        if term:
            where.append("(E.empname LIKE ? OR E.empcode LIKE ?)")
            params.extend([f"%{term}%", f"%{term}%"])
        sql = f"""
            SELECT E.pk_empid as id, E.empname + ' || ' + E.empcode as name
            FROM SAL_Employee_Mst E
            {join_desg}
            WHERE {" AND ".join(where)}
            ORDER BY E.empname
        """
        return DB.fetch_all(sql, params)

    @staticmethod
    def save_course_offer_by_hod(filters, course_ids, user_id, emp_id):
        conn = DB.get_connection()
        cursor = conn.cursor()
        try:
            cycle = DB.fetch_one("""
                SELECT pk_degreecycleid
                FROM SMS_DegreeCycle_Mst
                WHERE fk_degreeid = ? AND fk_semesterid = ?
            """, [filters.get('degree_id'), filters.get('semester_id')])
            cycle_id = cycle['pk_degreecycleid'] if cycle else None
            branch_id = filters.get('branch_id') or 0
            existing = AcademicsModel.get_course_offer_master(filters)
            if existing:
                course_alloc_id = existing['Pk_courseallocid']
                cursor.execute("""
                    UPDATE SMS_CourseAllocationSemesterwiseByHOD
                    SET fk_degreecycleid=?, fk_dgacasessionid=?, fk_exconfigid=?,
                        LastUpdated=GETDATE(), Lastupdatedby=?, Yearid=?,
                        degreeid=?, fk_semesterid=?, semesterid=?,
                        fk_collegeid=?, fk_specializationid=?, fk_Empid=?
                    WHERE Pk_courseallocid=?
                """, [
                    cycle_id, filters.get('session_id'), filters.get('exconfig_id'),
                    str(user_id), filters.get('year_id'),
                    filters.get('degree_id'), filters.get('semester_id'), filters.get('semester_id'),
                    filters.get('college_id'), branch_id, emp_id, course_alloc_id
                ])
            else:
                cursor.execute("""
                    INSERT INTO SMS_CourseAllocationSemesterwiseByHOD
                    (fk_degreecycleid, fk_dgacasessionid, AllocDate, fk_exconfigid, LastUpdated, Lastupdatedby,
                     Yearid, degreeid, fk_semesterid, semesterid, created_by, fk_collegeid, fk_specializationid, fk_Empid)
                    OUTPUT INSERTED.Pk_courseallocid
                    VALUES (?, ?, GETDATE(), ?, GETDATE(), ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, [
                    cycle_id, filters.get('session_id'), filters.get('exconfig_id'), str(user_id),
                    filters.get('year_id'), filters.get('degree_id'), filters.get('semester_id'),
                    filters.get('semester_id'), str(user_id), filters.get('college_id'), branch_id, emp_id
                ])
                course_alloc_id = cursor.fetchone()[0]

            cursor.execute("DELETE FROM SMS_CourseAllocationSemesterwiseByHOD_Dtl WHERE fk_courseallocid = ?", [course_alloc_id])
            for cid in course_ids:
                cursor.execute("""
                    INSERT INTO SMS_CourseAllocationSemesterwiseByHOD_Dtl
                    (fk_courseallocid, fk_courseid, semesterid, branchid, courseActive, lastupdated, Lastupdatedby)
                    VALUES (?, ?, ?, ?, ?, GETDATE(), ?)
                """, [course_alloc_id, cid, filters.get('semester_id'), branch_id, 1, str(user_id)])
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def get_courses_assigned_to_hod_offering(filters):
        # Fetches courses offered by HOD for this Session, Degree, Semester, Exam Config
        sql = """
            SELECT C.pk_courseid, C.coursecode, C.coursename, 
                   C.crhr_theory, C.crhr_practical
            FROM SMS_CourseAllocationSemesterwiseByHOD_Dtl DTL
            INNER JOIN SMS_CourseAllocationSemesterwiseByHOD MST ON DTL.fk_courseallocid = MST.Pk_courseallocid
            INNER JOIN SMS_Course_Mst C ON DTL.fk_courseid = C.pk_courseid
            WHERE MST.fk_dgacasessionid = ? 
              AND MST.degreeid = ? 
              AND MST.fk_semesterid = ?
              AND MST.fk_exconfigid = ?
        """
        params = [filters['session_id'], filters['degree_id'], filters['semester_id'], filters['exconfig_id']]
        
        type_tp = filters.get('coursetype')
        if type_tp == 'T':
            sql += " AND ISNULL(C.crhr_theory, 0) > 0"
        elif type_tp == 'P':
            sql += " AND ISNULL(C.crhr_practical, 0) > 0"
            
        sql += " ORDER BY C.coursecode COLLATE Latin1_General_BIN ASC"
        return DB.fetch_all(sql, params)

    @staticmethod
    def get_teacher_course_assignment_master(filters):
        return DB.fetch_one("""
            SELECT pk_tcourseallocid
            FROM SMS_TCourseAlloc_Mst
            WHERE fk_sessionid=? AND fk_collegeid=? AND fk_degreeid=? AND fk_semesterid=?
              AND fk_exconfigid=? AND fk_employeeid=? AND ISNULL(fk_batchdtlid, 0)=?
              AND ISNULL(fk_branchid, 0)=? AND RTRIM(ISNULL(coursetype, ''))=?
        """, [
            filters.get('session_id'),
            filters.get('college_id'),
            filters.get('degree_id'),
            filters.get('semester_id'),
            filters.get('exconfig_id'),
            filters.get('employee_id'),
            filters.get('batch_id') or 0,
            filters.get('branch_id') or 0,
            (filters.get('coursetype') or '').strip()
        ])

    @staticmethod
    def get_teacher_course_assignment_details(master_id):
        rows = DB.fetch_all("""
            SELECT fk_courseid, IsMainTeacher
            FROM SMS_TCourseAlloc_Dtl
            WHERE fk_tcourseallocid = ?
        """, [master_id])
        assigned = set()
        main_teacher = set()
        for r in rows:
            assigned.add(r['fk_courseid'])
            if r.get('IsMainTeacher'):
                main_teacher.add(r['fk_courseid'])
        return assigned, main_teacher

    @staticmethod
    def save_teacher_course_assignment(filters, course_ids, main_course_ids, user_id):
        conn = DB.get_connection()
        cursor = conn.cursor()
        try:
            existing = AcademicsModel.get_teacher_course_assignment_master(filters)
            if existing:
                master_id = existing['pk_tcourseallocid']
                cursor.execute("""
                    UPDATE SMS_TCourseAlloc_Mst
                    SET fk_sessionid=?, fk_collegeid=?, fk_employeeid=?, fk_degreeid=?,
                        fk_semesterid=?, fk_exconfigid=?, fk_branchid=?, coursetype=?, fk_batchdtlid=?
                    WHERE pk_tcourseallocid=?
                """, [
                    filters.get('session_id'), filters.get('college_id'), filters.get('employee_id'),
                    filters.get('degree_id'), filters.get('semester_id'), filters.get('exconfig_id'),
                    filters.get('branch_id') or None, filters.get('coursetype'), filters.get('batch_id') or None,
                    master_id
                ])
            else:
                cursor.execute("""
                    INSERT INTO SMS_TCourseAlloc_Mst
                    (fk_sessionid, fk_collegeid, fk_employeeid, fk_degreeid, fk_semesterid, fk_exconfigid,
                     fk_branchid, coursetype, fk_batchdtlid)
                    OUTPUT INSERTED.pk_tcourseallocid
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, [
                    filters.get('session_id'), filters.get('college_id'), filters.get('employee_id'),
                    filters.get('degree_id'), filters.get('semester_id'), filters.get('exconfig_id'),
                    filters.get('branch_id') or None, filters.get('coursetype'), filters.get('batch_id') or None
                ])
                master_id = cursor.fetchone()[0]

            cursor.execute("DELETE FROM SMS_TCourseAlloc_Dtl WHERE fk_tcourseallocid = ?", [master_id])
            main_set = {str(cid) for cid in main_course_ids}
            for cid in course_ids:
                is_main = 1 if str(cid) in main_set else 0
                cursor.execute("""
                    INSERT INTO SMS_TCourseAlloc_Dtl (fk_tcourseallocid, fk_courseid, IsMainTeacher, Isactive)
                    VALUES (?, ?, ?, ?)
                """, [master_id, cid, is_main, 1])
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def delete_teacher_course_assignment_courses(filters, course_ids):
        conn = DB.get_connection()
        cursor = conn.cursor()
        try:
            master = AcademicsModel.get_teacher_course_assignment_master(filters)
            if not master:
                return False
            master_id = master['pk_tcourseallocid']
            if not course_ids:
                cursor.execute("DELETE FROM SMS_TCourseAlloc_Dtl WHERE fk_tcourseallocid = ?", [master_id])
                cursor.execute("DELETE FROM SMS_TCourseAlloc_Mst WHERE pk_tcourseallocid = ?", [master_id])
                conn.commit()
                return True
            placeholders = ",".join(["?"] * len(course_ids))
            cursor.execute(
                f"DELETE FROM SMS_TCourseAlloc_Dtl WHERE fk_tcourseallocid = ? AND fk_courseid IN ({placeholders})",
                [master_id] + course_ids
            )
            remaining = DB.fetch_scalar("SELECT COUNT(*) FROM SMS_TCourseAlloc_Dtl WHERE fk_tcourseallocid = ?", [master_id])
            if remaining == 0:
                cursor.execute("DELETE FROM SMS_TCourseAlloc_Mst WHERE pk_tcourseallocid = ?", [master_id])
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

class AdvisoryModel:
    @staticmethod
    def save_student_discipline(data, user_id):
        sid = data.get('sid')
        major_id = data.get('major_id')
        minor_id = data.get('minor_id')
        supporting_id = data.get('supporting_id')
        advisor_id = data.get('advisor_id')
        
        if not sid: return False
        
        conn = DB.get_connection()
        cursor = conn.cursor()
        try:
            # 1. Upsert SMS_stuDiscipline_dtl
            cursor.execute("SELECT pk_stuDesciplineDtlID FROM SMS_stuDiscipline_dtl WHERE fk_sturegid = ?", [sid])
            existing_disc = cursor.fetchone()
            
            if existing_disc:
                cursor.execute("""
                    UPDATE SMS_stuDiscipline_dtl 
                    SET fk_desciplineidMajor = ?, fk_desciplineidMinor = ?, fk_desciplineidSupporting = ?
                    WHERE fk_sturegid = ?
                """, [major_id, minor_id, supporting_id, sid])
            else:
                cursor.execute("""
                    INSERT INTO SMS_stuDiscipline_dtl (fk_sturegid, fk_desciplineidMajor, fk_desciplineidMinor, fk_desciplineidSupporting)
                    VALUES (?, ?, ?, ?)
                """, [sid, major_id, minor_id, supporting_id])
            
            # 2. Update Major Advisor (statusid = 1)
            cursor.execute("SELECT pk_adcid FROM SMS_Advisory_Committee_Mst WHERE fk_stid = ?", [sid])
            mst = cursor.fetchone()
            if not mst:
                stu = DB.fetch_one("SELECT fk_collegeid, fk_adm_session, fk_degreeid, fk_branchid FROM SMS_Student_Mst WHERE pk_sid=?", [sid])
                if stu:
                    cursor.execute("""
                        INSERT INTO SMS_Advisory_Committee_Mst (fk_colgid, fk_sessionid, fk_degreeid, fk_branchid, fk_stid, createdby, creationdate, approvalstatus)
                        OUTPUT INSERTED.pk_adcid
                        VALUES (?, ?, ?, ?, ?, ?, GETDATE(), 'P')
                    """, [stu['fk_collegeid'], stu['fk_adm_session'], stu['fk_degreeid'], major_id, sid, user_id])
                    adcid = cursor.fetchone()[0]
                else:
                    raise Exception("Student not found")
            else:
                adcid = mst[0]
                cursor.execute("UPDATE SMS_Advisory_Committee_Mst SET fk_branchid = ?, updated_by = ?, updated_date = GETDATE() WHERE pk_adcid = ?", [major_id, user_id, adcid])

            # Upsert Detail for Major Advisor (statusid = 1)
            # Table SMS_Advisory_Committee_Dtl has: fk_adcid, fk_statusid, fk_deptid, fk_empid
            cursor.execute("SELECT fk_adcid FROM SMS_Advisory_Committee_Dtl WHERE fk_adcid = ? AND fk_statusid = 1", [adcid])
            existing_adv = cursor.fetchone()
            if existing_adv:
                cursor.execute("UPDATE SMS_Advisory_Committee_Dtl SET fk_empid = ? WHERE fk_adcid = ? AND fk_statusid = 1", [advisor_id, adcid])
            else:
                cursor.execute("INSERT INTO SMS_Advisory_Committee_Dtl (fk_adcid, fk_statusid, fk_empid) VALUES (?, 1, ?)", [adcid, advisor_id])

            # 3. Update SMS_Student_Mst main branch
            cursor.execute("UPDATE SMS_Student_Mst SET fk_branchid = ? WHERE pk_sid = ?", [major_id, sid])

            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"Error saving disciplines: {e}")
            return False
        # Do not manually close the connection if in app context; teardown_db will handle it.

    @staticmethod
    def get_student_limits(page=1, per_page=10):
        offset = (page - 1) * per_page
        total = DB.fetch_scalar("SELECT COUNT(*) FROM SMS_AdvisoryStudentLimit_mst")
        query = f"""
            SELECT L.*, C.collegename, D.degreename, B.Branchname, SES.sessionname
            FROM SMS_AdvisoryStudentLimit_mst L
            INNER JOIN SMS_College_Mst C ON L.Fk_collegeid = C.pk_collegeid
            INNER JOIN SMS_Degree_Mst D ON L.FK_Degreeid = D.pk_degreeid
            LEFT JOIN SMS_BranchMst B ON L.FK_branchid = B.Pk_BranchId
            INNER JOIN SMS_AcademicSession_Mst SES ON L.Fk_Sessionid = SES.pk_sessionid
            ORDER BY SES.sessionorder DESC, C.collegename
            OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY
        """
        return DB.fetch_all(query), total

    @staticmethod
    def save_student_limit(data):
        params = [
            data['college_id'], data['session_id'], data['degree_id'],
            data.get('branch_id') if data.get('branch_id') and str(data.get('branch_id')) != '0' else None,
            data['student_limit']
        ]
        if data.get('pk_id'):
            return DB.execute("""
                UPDATE SMS_AdvisoryStudentLimit_mst 
                SET Fk_collegeid=?, Fk_Sessionid=?, FK_Degreeid=?, FK_branchid=?, StudentLimit=?
                WHERE pk_limitid=?
            """, params + [data['pk_id']])
        else:
            return DB.execute("""
                INSERT INTO SMS_AdvisoryStudentLimit_mst (Fk_collegeid, Fk_Sessionid, FK_Degreeid, FK_branchid, StudentLimit)
                VALUES (?, ?, ?, ?, ?)
            """, params)

    @staticmethod
    def get_advisory_lookups(college_id=None, degree_id=None):
        degrees = []
        branches = []
        if college_id:
            degrees = AcademicsModel.get_college_pg_degrees(college_id)
            if degree_id:
                branches = AcademicsModel.get_college_degree_specializations(college_id, degree_id)

        return {
            'colleges': AcademicsModel.get_colleges_simple(),
            'sessions': InfrastructureModel.get_sessions(),
            'degrees': degrees,
            'branches': branches,
            'employees': DB.fetch_all("SELECT E.pk_empid as id, E.empname + ' | ' + E.empcode + ' | (' + ISNULL(D.description, 'No Dept') + ')' as name FROM SAL_Employee_Mst E LEFT JOIN Department_Mst D ON E.fk_deptid = D.pk_deptid WHERE E.employeeleftstatus = 'N' ORDER BY E.empname")
        }

    @staticmethod
    def get_students_for_advisory(filters):
        query = """
            SELECT S.pk_sid, S.fullname, S.AdmissionNo, S.enrollmentno, 
                   B_MST.Branchname, S.fk_branchid,
                   D.fk_empid as fk_advisorid, E.empname as advisor_name, M.pk_adcid,
                   B_MAJ.Branchname as major_name,
                   B_MIN.Branchname as minor_name,
                   B_SUP.Branchname as supporting_name,
                   CLG.collegename, DEG.degreename, SES.sessionname,
                   M.submitdate, M.approvalstatus, M.responsedate, M.responseremarks
            FROM SMS_Student_Mst S
            LEFT JOIN SMS_BranchMst B_MST ON S.fk_branchid = B_MST.Pk_BranchId
            LEFT JOIN SMS_Advisory_Committee_Mst M ON S.pk_sid = M.fk_stid
            LEFT JOIN SMS_Advisory_Committee_Dtl D ON M.pk_adcid = D.fk_adcid AND D.fk_statusid = 1
            LEFT JOIN SAL_Employee_Mst E ON D.fk_empid = E.pk_empid
            LEFT JOIN SMS_stuDiscipline_dtl SD ON S.pk_sid = SD.fk_sturegid
            LEFT JOIN SMS_BranchMst B_MAJ ON SD.fk_desciplineidMajor = B_MAJ.Pk_BranchId
            LEFT JOIN SMS_BranchMst B_MIN ON SD.fk_desciplineidMinor = B_MIN.Pk_BranchId
            LEFT JOIN SMS_BranchMst B_SUP ON SD.fk_desciplineidSupporting = B_SUP.Pk_BranchId
            LEFT JOIN SMS_College_Mst CLG ON S.fk_collegeid = CLG.pk_collegeid
            LEFT JOIN SMS_Degree_Mst DEG ON S.fk_degreeid = DEG.pk_degreeid
            LEFT JOIN SMS_AcademicSession_Mst SES ON S.fk_adm_session = SES.pk_sessionid
            WHERE S.fk_collegeid = ? AND S.fk_adm_session = ? AND S.fk_degreeid = ?
        """
        params = [filters['college_id'], filters['session_id'], filters['degree_id']]
        if filters.get('branch_id') and str(filters['branch_id']) != '0':
            query += " AND S.fk_branchid = ?"
            params.append(filters['branch_id'])
        
        query += " ORDER BY S.fullname"
        return DB.fetch_all(query, params)

    @staticmethod
    def save_major_advisor(sid, advisor_id, user_id):
        # 1. Find or Create Mst record for student
        mst = DB.fetch_one("SELECT pk_adcid, fk_colgid, fk_sessionid, fk_degreeid, fk_branchid FROM SMS_Advisory_Committee_Mst WHERE fk_stid = ?", [sid])
        
        if not mst:
            # Get student info to populate mst
            stu = DB.fetch_one("SELECT fk_collegeid, fk_adm_session, fk_degreeid, fk_branchid FROM SMS_Student_Mst WHERE pk_sid=?", [sid])
            if not stu: return False
            conn = DB.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO SMS_Advisory_Committee_Mst (fk_colgid, fk_sessionid, fk_degreeid, fk_branchid, fk_stid, createdby, creationdate, approvalstatus)
                OUTPUT INSERTED.pk_adcid
                VALUES (?, ?, ?, ?, ?, ?, GETDATE(), 'P')
            """, [stu['fk_collegeid'], stu['fk_adm_session'], stu['fk_degreeid'], stu['fk_branchid'], sid, user_id])
            adcid = cursor.fetchone()[0]
            conn.commit()
            conn.close()
        else:
            adcid = mst['pk_adcid']

        # 2. Upsert Dtl record for Major Advisor (statusid=1)
        existing_dtl = DB.fetch_scalar("SELECT fk_adcid FROM SMS_Advisory_Committee_Dtl WHERE fk_adcid=? AND fk_statusid=1", [adcid])
        if existing_dtl:
            return DB.execute("UPDATE SMS_Advisory_Committee_Dtl SET fk_empid=? WHERE fk_adcid=? AND fk_statusid=1", [advisor_id, adcid])
        else:
            return DB.execute("INSERT INTO SMS_Advisory_Committee_Dtl (fk_adcid, fk_statusid, fk_empid) VALUES (?, 1, ?)", [adcid, advisor_id])

    @staticmethod
    def save_nominee(adcid, advisor_id):
        # statusid 5 is Dean PGS Nominee
        existing = DB.fetch_scalar("SELECT fk_adcid FROM SMS_Advisory_Committee_Dtl WHERE fk_adcid=? AND fk_statusid=5", [adcid])
        if existing:
            return DB.execute("UPDATE SMS_Advisory_Committee_Dtl SET fk_empid=? WHERE fk_adcid=? AND fk_statusid=5", [advisor_id, adcid])
        else:
            return DB.execute("INSERT INTO SMS_Advisory_Committee_Dtl (fk_adcid, fk_statusid, fk_empid) VALUES (?, 5, ?)", [adcid, advisor_id])

    @staticmethod
    def get_student_advisory_committee(sid):
        mst = DB.fetch_one("""
            SELECT M.pk_adcid, M.approvalstatus, M.responseremarks, S.fullname, M.fk_branchid 
            FROM SMS_Advisory_Committee_Mst M
            INNER JOIN SMS_Student_Mst S ON M.fk_stid = S.pk_sid
            WHERE M.fk_stid=?
        """, [sid])
        if not mst: return {'major': None, 'minor': None, 'nominee': None, 'all': [], 'details': []}
        
        details = DB.fetch_all("""
            SELECT D.*, E.empname, DESG.designation as designation, DEPT.description as department, 
                   B.Branchname as specialization,
                   CASE D.fk_statusid 
                        WHEN 1 THEN 'Major Advisor'
                        WHEN 2 THEN 'Minor Advisor'
                        WHEN 3 THEN 'Member From Major Subject'
                        WHEN 4 THEN 'Member From Minor Subject'
                        WHEN 5 THEN 'Member From Supporting Subject'
                        WHEN 6 THEN 'Dean PGS Nominee'
                        ELSE 'Member'
                   END as role_name
            FROM SMS_Advisory_Committee_Dtl D
            LEFT JOIN SAL_Employee_Mst E ON D.fk_empid = E.pk_empid
            LEFT JOIN SAL_Designation_Mst DESG ON E.fk_desgid = DESG.pk_desgid
            LEFT JOIN Department_Mst DEPT ON E.fk_deptid = DEPT.pk_deptid
            LEFT JOIN SMS_Advisory_Committee_Mst ACM ON D.fk_adcid = ACM.pk_adcid
            LEFT JOIN SMS_BranchMst B ON ACM.fk_branchid = B.Pk_BranchId
            WHERE D.fk_adcid = ?
            ORDER BY D.fk_statusid
        """, [mst['pk_adcid']])
        
        res = {
            'adcid': mst['pk_adcid'],
            'approval_status': mst['approvalstatus'],
            'remarks': mst['responseremarks'],
            'student_name': mst['fullname'],
            'details': details,
            'major': next((d for d in details if d['fk_statusid'] == 1), None),
            'minor': next((d for d in details if d['fk_statusid'] == 2), None),
            'nominee': next((d for d in details if d['fk_statusid'] == 6), None),
            'all': details
        }
        return res

    @staticmethod
    def approve_advisory(adcid, status, user_id, level='PGS', remarks=None):
        # Explicit mapping based on verified DB schema
        mappings = {
            'HOD': {
                'status': 'hod_approval',
                'id': 'hod_id',
                'date': 'hod_date',
                'remarks': 'hod_remarks'
            },
            'DEAN': {
                'status': 'college_deanapproval',
                'id': 'collegedean_id',
                'date': 'Collegedean_date',
                'remarks': 'college_deanremarks'
            },
            'PGS': {
                'status': 'approvalstatus',
                'id': 'deanpgs_id',
                'date': 'responsedate',
                'remarks': 'responseremarks'
            }
        }
        
        m = mappings.get(level, mappings['PGS'])
        
        sql = f"""
            UPDATE SMS_Advisory_Committee_Mst 
            SET {m['status']} = ?, 
                {m['id']} = ?, 
                {m['date']} = GETDATE(), 
                {m['remarks']} = ?
            WHERE pk_adcid = ?
        """
        return DB.execute(sql, [status, user_id, remarks, adcid])

    @staticmethod
    def get_pending_advisory_approvals(filters, level='PGS'):
        status_col = {
            'HOD': 'ISNULL(M.hod_approval_status, \'P\')',
            'DEAN': 'ISNULL(M.dean_approval_status, \'P\')',
            'PGS': 'ISNULL(M.approvalstatus, \'P\')'
        }[level]

        query = f"""
            SELECT DISTINCT M.pk_adcid, S.pk_sid, S.fullname, S.AdmissionNo, S.enrollmentno,
                   D.degreename, B.Branchname,
                   E.empname as advisor_name
            FROM SMS_Advisory_Committee_Mst M
            INNER JOIN SMS_Student_Mst S ON M.fk_stid = S.pk_sid
            LEFT JOIN SMS_Advisory_Committee_Dtl ACD ON ACD.fk_adcid = M.pk_adcid AND ACD.fk_statusid = 1
            LEFT JOIN SAL_Employee_Mst E ON E.pk_empid = ACD.fk_empid
            LEFT JOIN SMS_Degree_Mst D ON S.fk_degreeid = D.pk_degreeid
            LEFT JOIN SMS_BranchMst B ON S.fk_branchid = B.Pk_BranchId
            WHERE S.fk_collegeid = ? AND S.fk_adm_session = ? AND S.fk_degreeid = ?
              AND {status_col} = 'P'
        """
        if level == 'DEAN':
            query += " AND M.hod_approval_status = 'A'"
        elif level == 'PGS':
            query += " AND M.dean_approval_status = 'A'"

        query += " ORDER BY S.fullname"
        return DB.fetch_all(query, [filters['college_id'], filters['session_id'], filters['degree_id']])

    @staticmethod
    def get_students_for_specialization(college_id, session_id, degree_id):
        query = """
            SELECT S.pk_sid, S.fullname, S.AdmissionNo, S.enrollmentno, B.Branchname as current_branch
            FROM SMS_Student_Mst S
            LEFT JOIN SMS_BranchMst B ON S.fk_branchid = B.Pk_BranchId
            WHERE S.fk_collegeid = ? AND S.fk_adm_session = ? AND S.fk_degreeid = ?
            ORDER BY S.fullname
        """
        return DB.fetch_all(query, [college_id, session_id, degree_id])

    @staticmethod
    def update_student_specialization(student_ids, branch_id):
        if not student_ids: return False
        placeholders = ",".join(["?"] * len(student_ids))
        query = f"UPDATE SMS_Student_Mst SET fk_branchid = ? WHERE pk_sid IN ({placeholders})"
        return DB.execute(query, [branch_id] + student_ids)

    @staticmethod
    def get_credit_load(sid):
        sql = """
            SELECT 
                ISNULL(SUM(CA.crhrth + CA.crhrpr), 0) as total,
                ISNULL(SUM(CASE WHEN CA.courseplan = 'MA' THEN CA.crhrth + CA.crhrpr ELSE 0 END), 0) as major,
                ISNULL(SUM(CASE WHEN CA.courseplan = 'MI' THEN CA.crhrth + CA.crhrpr ELSE 0 END), 0) as minor,
                ISNULL(SUM(CASE WHEN CA.courseplan = 'SU' THEN CA.crhrth + CA.crhrpr ELSE 0 END), 0) as supporting,
                ISNULL(SUM(CASE WHEN C.isThesis = 1 THEN CA.crhrth + CA.crhrpr ELSE 0 END), 0) as research,
                ISNULL(SUM(CASE WHEN C.IsSeminar = 1 THEN CA.crhrth + CA.crhrpr ELSE 0 END), 0) as seminar,
                ISNULL(SUM(CASE WHEN CA.courseplan = 'NC' THEN CA.crhrth + CA.crhrpr ELSE 0 END), 0) as non_credit,
                ISNULL(SUM(CASE WHEN CA.courseplan = 'DE' THEN CA.crhrth + CA.crhrpr ELSE 0 END), 0) as deficiency
            FROM Sms_course_Approval CA
            INNER JOIN SMS_Course_Mst C ON CA.fk_courseid = C.pk_courseid
            WHERE CA.fk_sturegid = ?
        """
        return DB.fetch_one(sql, [sid])

    @staticmethod
    def get_required_credit_load(sid):
        # Fetch from SMS_Degreewise_crhr based on student's degree
        sql = """
            SELECT totalmincrhr as min_total, 495 as max_total
            FROM SMS_Degreewise_crhr R
            INNER JOIN SMS_Student_Mst S ON R.fk_degreeid = S.fk_degreeid
            WHERE S.pk_sid = ?
        """
        res = DB.fetch_one(sql, [sid])
        if not res:
            return {'min_total': 0, 'max_total': 495}
        return res

    @staticmethod
    def get_available_courses(sid):
        # 1. Get student details
        stu = DB.fetch_one("SELECT fk_degreeid FROM SMS_Student_Mst WHERE pk_sid = ?", [sid])
        if not stu: return []
        
        disc = DB.fetch_one("""
            SELECT fk_desciplineidMajor, fk_desciplineidMinor, fk_desciplineidSupporting 
            FROM SMS_stuDiscipline_dtl WHERE fk_sturegid = ?
        """, [sid])
        
        deg_id = stu['fk_degreeid']
        maj_id = disc['fk_desciplineidMajor'] if disc else 0
        min_id = disc['fk_desciplineidMinor'] if disc else 0
        sup_id = disc['fk_desciplineidSupporting'] if disc else 0

        # 2. Query courses following the logic:
        # - Any course already assigned to the student (highest priority for type)
        # - Courses mapped to Major branch for this degree -> 'MA'
        # - Courses mapped to Minor branch for this degree -> 'MI'
        # - Courses mapped to Supporting branch for this degree -> 'SU'
        # - PGS Courses -> 'CP'
        
        sql = """
            SELECT DISTINCT C.pk_courseid, C.coursecode, C.coursename, C.crhr_theory, C.crhr_practical, t.default_type
            FROM (
                -- 1. Already allocated courses (guarantee they show up with their assigned type)
                SELECT fk_courseid as id, courseplan as default_type, 1 as priority
                FROM Sms_course_Approval WHERE fk_sturegid = ?
                
                UNION ALL
                
                -- 2. Major Branch Courses
                SELECT fk_courseid as id, 'MA' as default_type, 2 as priority
                FROM SMS_Course_Mst_Dtl WHERE fk_degreeid = ? AND fk_branchid = ? AND isactive = 1
                
                UNION ALL
                
                -- 3. Minor Branch Courses
                SELECT fk_courseid as id, 'MI' as default_type, 3 as priority
                FROM SMS_Course_Mst_Dtl WHERE fk_degreeid = ? AND fk_branchid = ? AND isactive = 1
                
                UNION ALL
                
                -- 4. Supporting Branch Courses
                SELECT fk_courseid as id, 'SU' as default_type, 4 as priority
                FROM SMS_Course_Mst_Dtl WHERE fk_degreeid = ? AND fk_branchid = ? AND isactive = 1
                
                UNION ALL
                
                -- 5. PGS Courses
                SELECT pk_courseid as id, 'CP' as default_type, 5 as priority
                FROM SMS_Course_Mst WHERE (coursecode LIKE 'PGS%' OR coursecode LIKE 'PGS %' OR fk_Deptid = 50) AND isobsolete = 0
            ) t
            INNER JOIN SMS_Course_Mst C ON t.id = C.pk_courseid
            -- Use ROW_NUMBER to pick the best type if a course appears in multiple branches
            INNER JOIN (
                SELECT id, default_type, ROW_NUMBER() OVER(PARTITION BY id ORDER BY priority) as rn
                FROM (
                    SELECT fk_courseid as id, courseplan as default_type, 1 as priority FROM Sms_course_Approval WHERE fk_sturegid = ?
                    UNION ALL
                    SELECT fk_courseid as id, 'MA' as default_type, 2 as priority FROM SMS_Course_Mst_Dtl WHERE fk_degreeid = ? AND fk_branchid = ? AND isactive = 1
                    UNION ALL
                    SELECT fk_courseid as id, 'MI' as default_type, 3 as priority FROM SMS_Course_Mst_Dtl WHERE fk_degreeid = ? AND fk_branchid = ? AND isactive = 1
                    UNION ALL
                    SELECT fk_courseid as id, 'SU' as default_type, 4 as priority FROM SMS_Course_Mst_Dtl WHERE fk_degreeid = ? AND fk_branchid = ? AND isactive = 1
                    UNION ALL
                    SELECT pk_courseid as id, 'CP' as default_type, 5 as priority FROM SMS_Course_Mst WHERE (coursecode LIKE 'PGS%' OR coursecode LIKE 'PGS %' OR fk_Deptid = 50) AND isobsolete = 0
                ) sub
            ) best_t ON C.pk_courseid = best_t.id AND best_t.rn = 1
            WHERE C.isobsolete = 0
            ORDER BY C.coursecode
        """
        
        params = [sid, deg_id, maj_id, deg_id, min_id, deg_id, sup_id, 
                  sid, deg_id, maj_id, deg_id, min_id, deg_id, sup_id]
        
        return DB.fetch_all(sql, params)

    @staticmethod
    def get_student_course_plan(sid):
        sql = """
            SELECT CP.*, C.coursecode, C.coursename, CP.crhrth as crhr_theory, CP.crhrpr as crhr_practical,
                   CASE CP.courseplan 
                        WHEN 'MA' THEN 'Major' WHEN 'MI' THEN 'Minor' 
                        WHEN 'SU' THEN 'Supporting' WHEN 'NC' THEN 'Non Credit'
                        WHEN 'DE' THEN 'Deficiency' WHEN 'CP' THEN 'Common PGS'
                        WHEN 'OP' THEN 'Optional' ELSE CP.courseplan 
                   END as type_name,
                   CP.courseplan as coursetype
            FROM Sms_course_Approval CP
            INNER JOIN SMS_Course_Mst C ON CP.fk_courseid = C.pk_courseid
            WHERE CP.fk_sturegid = ?
            ORDER BY CP.pk_stucourseapprove
        """
        return DB.fetch_all(sql, [sid])

    @staticmethod
    def save_course_plan(sid, courses, user_id):
        conn = DB.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM Sms_course_Approval WHERE fk_sturegid = ?", [sid])
            for c in courses:
                if c.get('course_id'):
                    course_info = DB.fetch_one("SELECT crhr_theory, crhr_practical, fk_coursetypeid FROM SMS_Course_Mst WHERE pk_courseid=?", [c['course_id']])
                    if course_info:
                        cursor.execute("""
                            INSERT INTO Sms_course_Approval (fk_sturegid, fk_courseid, courseplan, crhrth, crhrpr, fk_coursetypeid)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, [sid, c['course_id'], c['type'], course_info['crhr_theory'], course_info['crhr_practical'], course_info['fk_coursetypeid']])
            conn.commit()
            return True
        except Exception as e:
            print(f"Error saving course plan: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    @staticmethod
    def approve_course_plan(sid, status, user_id, level='PGS'):
        # Using submitbit as a placeholder for approval status in Sms_course_Approval
        val = 1 if status == 'A' else 0
        sql = "UPDATE Sms_course_Approval SET submitbit = ? WHERE fk_sturegid = ?"
        return DB.execute(sql, [val, sid])

    @staticmethod
    def get_pending_course_plan_approvals(filters, level='PGS'):
        # For now, fetching students who have records in Sms_course_Approval but maybe not 'approved'
        query = """
            SELECT DISTINCT S.pk_sid, S.fullname, S.AdmissionNo, S.enrollmentno,
                   D.degreename, B.Branchname
            FROM Sms_course_Approval CP
            INNER JOIN SMS_Student_Mst S ON CP.fk_sturegid = S.pk_sid
            LEFT JOIN SMS_Degree_Mst D ON S.fk_degreeid = D.pk_degreeid
            LEFT JOIN SMS_BranchMst B ON S.fk_branchid = B.Pk_BranchId
            WHERE S.fk_collegeid = ? AND S.fk_adm_session = ? AND S.fk_degreeid = ?
              AND (CP.submitbit IS NULL OR CP.submitbit = 0)
        """
        return DB.fetch_all(query, [filters['college_id'], filters['session_id'], filters['degree_id']])

class StudentModel:
    @staticmethod
    def get_student_info(sid):
        return DB.fetch_one("SELECT pk_sid, fullname, enrollmentno, AdmissionNo, fk_degreeid, fk_collegeid, fk_adm_session, fk_branchid FROM SMS_Student_Mst WHERE pk_sid = ?", [sid])

    _pwd_hist_cols_cache = None
    _legacy_keys_cache = None

    @staticmethod
    def _is_plausible_password(text):
        if not text:
            return False
        text = text.strip()
        if not (4 <= len(text) <= 64):
            return False
        # Restrict to common password characters; blocks decrypt garbage.
        if not re.fullmatch(r"[A-Za-z0-9@._/\-]+", text):
            return False
        # Must be either date-like, numeric-only, or mixed alpha+digit.
        if "/" in text:
            return True
        if text.isdigit() and len(text) >= 6:
            return True
        has_alpha = any(c.isalpha() for c in text)
        has_digit = any(c.isdigit() for c in text)
        return has_alpha and has_digit

    @staticmethod
    def _looks_like_base64(value):
        if not value or not isinstance(value, str):
            return False
        try:
            raw = base64.b64decode(value, validate=True)
            return len(raw) > 0 and (len(raw) % 8 == 0)
        except Exception:
            return False

    @staticmethod
    def _decrypt_3des_legacy(ciphertext_b64, key_text):
        if not Cipher or not key_text:
            return None
        try:
            data = base64.b64decode(ciphertext_b64)
        except Exception:
            return None

        key_bytes = key_text.encode('utf-8')
        md5_hash = hashlib.md5(key_bytes).digest()
        key = md5_hash + md5_hash[:8]
        iv = b'\0' * 8

        for mode in (modes.CBC(iv), modes.ECB()):
            try:
                cipher = Cipher(algorithms.TripleDES(key), mode, backend=default_backend())
                decryptor = cipher.decryptor()
                dec = decryptor.update(data) + decryptor.finalize()

                # Try PKCS#7 unpadding if present.
                pad_len = dec[-1]
                if 1 <= pad_len <= 8 and dec.endswith(bytes([pad_len]) * pad_len):
                    dec = dec[:-pad_len]

                plain = dec.decode('utf-8', errors='ignore').strip('\x00').strip()
                # Accept only sane printable candidates; reject short random gibberish.
                if StudentModel._is_plausible_password(plain):
                    return plain
            except Exception:
                continue
        return None

    @staticmethod
    def _get_pwd_history_columns():
        if StudentModel._pwd_hist_cols_cache is not None:
            return StudentModel._pwd_hist_cols_cache
        try:
            rows = DB.fetch_all("""
                SELECT COLUMN_NAME
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = 'SMS_PwdUpdDtl_Mst'
            """)
            cols = {str(r['COLUMN_NAME']).lower() for r in rows}
            StudentModel._pwd_hist_cols_cache = cols
            return cols
        except Exception:
            StudentModel._pwd_hist_cols_cache = set()
            return set()

    @staticmethod
    def _best_order_column(cols):
        for c in ['fk_upddateid', 'upd_date', 'updateddate', 'lastupdateddate', 'createddate', 'insdate']:
            if c in cols:
                return c
        return None

    @staticmethod
    def _discover_legacy_keys():
        if StudentModel._legacy_keys_cache is not None:
            return StudentModel._legacy_keys_cache

        keys = []
        # Env-provided keys first.
        key_single = os.getenv('LEGACY_STUDENT_PWD_KEY', '').strip()
        if key_single:
            keys.append(key_single)
        key_list = os.getenv('LEGACY_STUDENT_PWD_KEYS', '').strip()
        if key_list:
            keys.extend([k.strip() for k in key_list.split(',') if k.strip()])

        # Discover candidate key values from DB metadata (dynamic).
        try:
            meta = DB.fetch_all("""
                SELECT TABLE_NAME, COLUMN_NAME
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE DATA_TYPE IN ('varchar','nvarchar','char','nchar')
                  AND (
                    LOWER(COLUMN_NAME) LIKE '%key%'
                    OR LOWER(COLUMN_NAME) LIKE '%secret%'
                    OR LOWER(COLUMN_NAME) LIKE '%encrypt%'
                    OR LOWER(COLUMN_NAME) LIKE '%crypto%'
                  )
            """)
            for m in meta:
                table = m.get('TABLE_NAME')
                col = m.get('COLUMN_NAME')
                if not table or not col:
                    continue
                try:
                    rows = DB.fetch_all(
                        f"SELECT TOP 25 [{col}] AS val FROM [{table}] "
                        f"WHERE [{col}] IS NOT NULL AND LTRIM(RTRIM(CAST([{col}] AS varchar(200)))) <> ''"
                    )
                    for r in rows:
                        v = str(r.get('val') or '').strip()
                        if 1 <= len(v) <= 64:
                            keys.append(v)
                except Exception:
                    continue
        except Exception:
            pass

        # Common defaults as last resort.
        keys.extend(['HAU', 'CCS', 'LUVAS', 'ERP', 'ADMIN'])

        # De-duplicate preserving order.
        seen = set()
        out = []
        for k in keys:
            if k and k not in seen:
                seen.add(k)
                out.append(k)
        StudentModel._legacy_keys_cache = out
        return out

    @staticmethod
    def _get_plain_from_password_history(encrypted_text, enrollment_no=None):
        """
        Dynamic fallback for legacy data: resolves plaintext from historical
        password update table when direct decrypt is not possible.
        """
        if not encrypted_text and not enrollment_no:
            return None

        cols = StudentModel._get_pwd_history_columns()
        if not cols:
            return None

        plain_candidates = [c for c in cols if ('pass' in c and 'encrypt' not in c) or c in ('plain_text', 'plaintext')]
        enc_candidates = [c for c in cols if ('encrypt' in c and 'pass' in c) or c in ('encryptedpassword', 'encpassword')]
        if not plain_candidates:
            return None
        order_col = StudentModel._best_order_column(cols)
        order_sql = f" ORDER BY [{order_col}] DESC" if order_col else ""

        # 1) Fast path: match by encrypted value directly.
        if encrypted_text and enc_candidates:
            for enc_col in enc_candidates:
                for plain_col in plain_candidates:
                    try:
                        sql = f"""
                            SELECT TOP 1 [{plain_col}] AS plain_val
                            FROM SMS_PwdUpdDtl_Mst
                            WHERE LTRIM(RTRIM([{enc_col}])) = ?
                              AND [{plain_col}] IS NOT NULL
                              AND LTRIM(RTRIM([{plain_col}])) <> ''
                            {order_sql}
                        """
                        row = DB.fetch_one(sql, [encrypted_text.strip()])
                        if row and row.get('plain_val'):
                            candidate = str(row['plain_val']).strip()
                            if StudentModel._is_plausible_password(candidate):
                                return candidate
                    except Exception:
                        pass

        if not enrollment_no:
            return None
        enrollment_no = enrollment_no.strip()

        # 2) If table stores enrollment/admission directly.
        direct_id_cols = [c for c in ['enrollmentno', 'admissionno', 'loginname'] if c in cols]
        for c in direct_id_cols:
            for plain_col in plain_candidates:
                try:
                    sql = f"""
                        SELECT TOP 1 [{plain_col}] AS plain_val
                        FROM SMS_PwdUpdDtl_Mst
                        WHERE LTRIM(RTRIM([{c}])) = ?
                          AND [{plain_col}] IS NOT NULL
                          AND LTRIM(RTRIM([{plain_col}])) <> ''
                        {order_sql}
                    """
                    row = DB.fetch_one(sql, [enrollment_no])
                    if row and row.get('plain_val'):
                        candidate = str(row['plain_val']).strip()
                        if StudentModel._is_plausible_password(candidate):
                            return candidate
                except Exception:
                    pass

        # 3) If table stores student id, join via SMS_Student_Mst.
        sid_cols = [c for c in ['fk_sid', 'sid', 'pk_sid', 'fk_stuid'] if c in cols]
        for sid_col in sid_cols:
            for plain_col in plain_candidates:
                try:
                    sql = f"""
                        SELECT TOP 1 H.[{plain_col}] AS plain_val
                        FROM SMS_PwdUpdDtl_Mst H
                        INNER JOIN SMS_Student_Mst S
                            ON S.pk_sid = H.[{sid_col}]
                        WHERE (LTRIM(RTRIM(S.enrollmentno)) = ?
                           OR LTRIM(RTRIM(S.AdmissionNo)) = ?)
                          AND H.[{plain_col}] IS NOT NULL
                        {order_sql.replace('[', 'H.[')}
                    """
                    row = DB.fetch_one(sql, [enrollment_no, enrollment_no])
                    if row and row.get('plain_val'):
                        candidate = str(row['plain_val']).strip()
                        if StudentModel._is_plausible_password(candidate):
                            return candidate
                except Exception:
                    pass

        # 4) If table stores UM user id, join via UM_Users_Mst.loginname.
        user_id_cols = [c for c in ['fk_userid', 'userid', 'pk_userid'] if c in cols]
        for user_col in user_id_cols:
            for plain_col in plain_candidates:
                try:
                    sql = f"""
                        SELECT TOP 1 H.[{plain_col}] AS plain_val
                        FROM SMS_PwdUpdDtl_Mst H
                        INNER JOIN UM_Users_Mst U
                            ON U.pk_userId = H.[{user_col}]
                        WHERE LTRIM(RTRIM(U.loginname)) = ?
                          AND H.[{plain_col}] IS NOT NULL
                        {order_sql.replace('[', 'H.[')}
                    """
                    row = DB.fetch_one(sql, [enrollment_no])
                    if row and row.get('plain_val'):
                        candidate = str(row['plain_val']).strip()
                        if StudentModel._is_plausible_password(candidate):
                            return candidate
                except Exception:
                    pass

        return None

    @staticmethod
    def save_student(data):
        # Full logic to save to SMS_Student_Mst and related tables
        try:
            sql = """INSERT INTO SMS_Student_Mst (fullname, mname, fname, fullname_hindi, mname_hindi, fname_hindi,
                     fk_collegeid, fk_sessionid, AdmissionNo, fk_degreeid, fk_semid, fk_branchid, Gender, dob,
                     fk_rankid, rankno, fk_nid, fk_stateid, fk_religionid, fk_districtid, fk_catid, fk_seattypeid,
                     email, mobile, p_email, p_mobile, PassportNo, PlaceofIssue, PassportExpDate, DateOfAdmission,
                     PlaceOfBirth, ReportingDate, isph, isspot, is_fee_exempted, remarks, isdomicile, MaritalStatus,
                     AadharNo, islateral, USID, BloodGroup, BankName, BankAccNo, BankIFSC, p_address, postal_address)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
            params = [
                data.get('fullname'), data.get('mname'), data.get('fname'), data.get('fullname_hindi'), data.get('mname_hindi'), data.get('fname_hindi'),
                data.get('college_id'), data.get('session_id'), data.get('admission_no'), data.get('degree_id'), data.get('semester_id'), data.get('branch_id'),
                data.get('gender'), data.get('dob'), data.get('rank_id'), data.get('rank_no'), data.get('nid'), data.get('state_id'), data.get('religion_id'),
                data.get('district_id'), data.get('cat_id'), data.get('seat_type_id'), data.get('email'), data.get('mobile'), data.get('p_email'), data.get('p_mobile'),
                data.get('passport_no'), data.get('passport_place'), data.get('passport_expiry'), data.get('doa'), data.get('birth_place'), data.get('report_date'),
                1 if data.get('is_ph') else 0, 1 if data.get('is_spot') else 0, data.get('fee_exempted', 0), data.get('remarks'), 1 if data.get('is_domicile') else 0,
                data.get('marital_status'), data.get('aadhaar_no'), 1 if data.get('is_lateral') else 0, data.get('usid'), data.get('blood_group'),
                data.get('bank_name'), data.get('bank_ac'), data.get('bank_ifsc'), data.get('p_address'), data.get('postal_address')
            ]
            return DB.execute(sql, params)
        except Exception as e:
            print(f"Error saving student: {e}")
            return False

    @staticmethod
    def get_student_lookups():
        raw_certs = DB.fetch_all("SELECT certificatename, isrequired FROM SMS_Certificate_Mst")
        
        # Normalize and unique-ify certificates in Python
        unique_certs = {}
        import re
        
        for r in raw_certs:
            name = r['certificatename'] or ""
            if not name: continue
            
            # Create a normalization key: lowercase, remove non-alphanumeric, strip
            norm_key = re.sub(r'[^a-z0-9]', '', name.lower())
            
            if norm_key not in unique_certs:
                unique_certs[norm_key] = {
                    'name': name.strip('. '), # Clean up trailing dots/spaces
                    'required': int(r['isrequired'] or 0)
                }
            else:
                # If already exists, update required status if this one is required
                if r['isrequired']:
                    unique_certs[norm_key]['required'] = 1
                # If current name is shorter or has brackets, and new name is cleaner, maybe swap?
                # For now, just keep the first one found but ensure the "best" name is used.
                if '(' not in name and '(' in unique_certs[norm_key]['name']:
                    unique_certs[norm_key]['name'] = name.strip('. ')

        sorted_certs = sorted(unique_certs.values(), key=lambda x: x['name'])

        return {
            'salutations': DB.fetch_all("SELECT pk_salutationid as id, salutation as name FROM SMS_Salutation_Mst ORDER BY salutation"),
            'occupations': DB.fetch_all("SELECT PK_occuid as id, Discription as name FROM SMS_Occupation_MST ORDER BY Discription"),
            'qualifications': DB.fetch_all("SELECT Pk_EduQuaid as id, Discription as name FROM SMS_EducationalQualification_MST ORDER BY displayorder"),
            'religions': DB.fetch_all("SELECT pk_religionid as id, religiontype as name FROM Religion_Mst ORDER BY religiontype"),
            'nationalities': DB.fetch_all("SELECT pk_nid, nationality as name FROM SMS_Nationality_Mst ORDER BY nationality"),
            'categories': DB.fetch_all("SELECT pk_catid as id, category as name FROM SAL_Category_Mst ORDER BY category"),
            'states': DB.fetch_all("SELECT pk_StateID as id, Description as name FROM Common_State_mst ORDER BY Description"),
            'districts': DB.fetch_all("SELECT pk_districid as id, Description as name FROM distric_mst ORDER BY Description"),
            'colleges': AcademicsModel.get_colleges_simple(),
            'degrees': AcademicsModel.get_all_degrees(),
            'sessions': InfrastructureModel.get_sessions(),
            'exams': DB.fetch_all("SELECT Pk_EduQuaid as id, Discription as name FROM SMS_EducationalQualification_MST ORDER BY displayorder"),
            'boards': DB.fetch_all("SELECT pk_boardid as id, boardname as name FROM SMS_Board_Mst ORDER BY boardname"),
            'edu_types': DB.fetch_all("SELECT pk_Edutypeid as id, Description as name FROM SMS_educationtype_mst ORDER BY Description"),
            'grades': [{'id': 'A', 'name': 'A'}, {'id': 'B', 'name': 'B'}, {'id': 'C', 'name': 'C'}, {'id': 'D', 'name': 'D'}, {'id': 'F', 'name': 'F'}],
            'course_types': DB.fetch_all("SELECT pk_coursetypeid as id, coursetype as name FROM SMS_CourseType_Mst ORDER BY coursetype"),
            'courses': DB.fetch_all("SELECT pk_courseid as id, coursecode + ' - ' + coursename as name, coursecode, coursename FROM SMS_Course_Mst ORDER BY coursecode"),
            'ranks': DB.fetch_all("SELECT pk_rankid as id, Rankname as name FROM SMS_RankMst ORDER BY Rankname"),
            'branches': AcademicsModel.get_branches(),
            'seat_types': DB.fetch_all("SELECT pk_seatypeid as id, seatype as name FROM SMS_SeatType_Mst ORDER BY seatype"),
            'semesters': InfrastructureModel.get_all_semesters(),
            'certificates': sorted_certs
        }

    @staticmethod
    def get_students_by_filter(filters):
        sql = """
            SELECT pk_sid, fullname, AdmissionNo, enrollmentno, fk_collegeid, fk_degreeid, fk_adm_session
            FROM SMS_Student_Mst
            WHERE 1=1
        """
        params = []
        if filters.get('college_id'):
            sql += " AND fk_collegeid = ?"
            params.append(filters['college_id'])
        if filters.get('session_id'):
            sql += " AND fk_adm_session = ?"
            params.append(filters['session_id'])
        if filters.get('degree_id'):
            sql += " AND fk_degreeid = ?"
            params.append(filters['degree_id'])
        if filters.get('admission_no'):
            sql += " AND (AdmissionNo LIKE ? OR enrollmentno LIKE ?)"
            params.extend(['%' + filters['admission_no'] + '%', '%' + filters['admission_no'] + '%'])
            
        sql += " ORDER BY fullname"
        return DB.fetch_all(sql, params)

    @staticmethod
    def get_student_by_enrollment(enrollment_no):
        sql = "SELECT * FROM SMS_Student_Mst WHERE AdmissionNo = ? OR enrollmentno = ?"
        return DB.fetch_one(sql, [enrollment_no, enrollment_no])

    @staticmethod
    def unlock_student_biodata(enrollment_no):
        """Sets Submitstatus = 0 in SMS_StuBioData_DTL for the student"""
        sid_res = DB.fetch_one("SELECT pk_sid FROM SMS_Student_Mst WHERE enrollmentno = ?", [enrollment_no])
        if sid_res:
            return DB.execute("UPDATE SMS_StuBioData_DTL SET Submitstatus = 0 WHERE fk_Sid = ?", [sid_res['pk_sid']])
        return False

    @staticmethod
    def update_card_entry_status(enrollment_no):
        return DB.execute("UPDATE SMS_Student_Mst SET CardEntrySubmit = 1 WHERE enrollmentno = ? OR manualRegno = ?", [enrollment_no, enrollment_no])

    @staticmethod
    def decrypt_password(encrypted_text):
        if not encrypted_text:
            return None

        encrypted_text = encrypted_text.strip()

        # Non-encrypted/plain values should be returned as-is.
        if not StudentModel._looks_like_base64(encrypted_text):
            return encrypted_text

        # Prefer authoritative dynamic lookup from legacy password history.
        hist_plain = StudentModel._get_plain_from_password_history(encrypted_text)
        if hist_plain:
            return hist_plain

        # Preferred: configured key(s) for legacy decrypt.
        keys = StudentModel._discover_legacy_keys()

        seen = set()
        for key in keys:
            if key in seen:
                continue
            seen.add(key)
            plain = StudentModel._decrypt_3des_legacy(encrypted_text, key)
            if plain:
                return plain

        # Unknown encrypted format/key.
        return None

    @staticmethod
    def get_student_password(enrollment_no):
        enrollment_no = (enrollment_no or '').strip()
        if not enrollment_no:
            return None

        # 1. Try UM_Users_Mst (System users/Employee portal)
        sql_um = """
            SELECT TOP 1 Plain_text
            FROM UM_Users_Mst
            WHERE LTRIM(RTRIM(loginname)) = ?
               OR UPPER(LTRIM(RTRIM(loginname))) = UPPER(?)
        """
        res_um = DB.fetch_one(sql_um, [enrollment_no, enrollment_no])
        if res_um and res_um['Plain_text']:
            return res_um['Plain_text']
            
        # 2. Try SMS_Student_Mst (Student portal)
        sql_sms = """
            SELECT TOP 1 Password
            FROM SMS_Student_Mst
            WHERE LTRIM(RTRIM(enrollmentno)) = ?
               OR LTRIM(RTRIM(AdmissionNo)) = ?
               OR UPPER(LTRIM(RTRIM(enrollmentno))) = UPPER(?)
               OR UPPER(LTRIM(RTRIM(AdmissionNo))) = UPPER(?)
        """
        res_sms = DB.fetch_one(sql_sms, [enrollment_no, enrollment_no, enrollment_no, enrollment_no])

        # Fallback for inconsistent legacy data formatting.
        if not res_sms:
            sql_fallback = """
                SELECT TOP 1 Password
                FROM SMS_Student_Mst
                WHERE enrollmentno LIKE ? OR AdmissionNo LIKE ?
            """
            like = f"%{enrollment_no}%"
            res_sms = DB.fetch_one(sql_fallback, [like, like])

        if res_sms and res_sms['Password']:
            enc = res_sms['Password']
            if isinstance(enc, (bytes, bytearray)):
                enc = enc.decode('utf-8', errors='ignore')
            enc = (enc or '').strip()
            # Try history table with student context first, then decrypt.
            hist_plain = StudentModel._get_plain_from_password_history(enc, enrollment_no)
            if hist_plain:
                return hist_plain
            return StudentModel.decrypt_password(enc)
            
        return None

    @staticmethod
    def get_student_all_details(sid):
        res = {}
        res['basic'] = DB.fetch_one("SELECT * FROM SMS_Student_Mst WHERE pk_sid = ?", [sid])
        if not res['basic']: return None
        
        res['schooling'] = DB.fetch_all("SELECT * FROM SMS_stuSchooling_dtl WHERE FK_BDid = ?", [sid])
        res['preadmission'] = DB.fetch_all("SELECT * FROM SMS_StudentPreAdmission_dtl WHERE FK_Sturegid = ?", [sid])
        res['sports'] = DB.fetch_all("SELECT * FROM SMS_StudentSportsRecreation_dtl WHERE FK_Sturegid = ?", [sid])
        
        # Join with SMS_Course_Mst to get course name/code if not present in detail table
        res['ug_detail'] = DB.fetch_all("""
            SELECT U.*, 
                   ISNULL(U.coursename, C.coursename) as coursename,
                   ISNULL(U.coursecode, C.coursecode) as coursecode
            FROM SMS_UnderGradDetail_dtl U
            LEFT JOIN SMS_Course_Mst C ON U.fk_courseid = C.pk_courseid
            WHERE U.fk_sid = ?
        """, [sid])
        
        res['pg_detail'] = DB.fetch_all("""
            SELECT P.*, 
                   ISNULL(P.coursename, C.coursename) as coursename,
                   ISNULL(P.coursecode, C.coursecode) as coursecode
            FROM SMS_PostGrad_Dtl P
            LEFT JOIN SMS_Course_Mst C ON P.fk_courseid = C.pk_courseid
            WHERE P.fk_sid = ?
        """, [sid])
        return res

    @staticmethod
    def save_student_biodata(data, user_id):
        sid = data.get('pk_sid')
        if not sid: return False

        # 1. Update SMS_Student_Mst
        # We'll use a dynamic update approach for common fields
        basic_fields = {
            'fk_salutationid': data.get('salutation_id'),
            'fullname': data.get('fullname'),
            'dob': data.get('dob'),
            'fname': data.get('fname'),
            'FatherDOB': data.get('f_dob') or None,
            'FK_occuidF': data.get('f_occu_id') or None,
            'OccuAddressF': data.get('f_occu_addr'),
            'FK_EduQuaid': data.get('f_edu_id') or None,
            'mname': data.get('mname'),
            'MotherDOB': data.get('m_dob') or None,
            'FK_occuidM': data.get('m_occu_id') or None,
            'OccuAddressM': data.get('m_occu_addr'),
            'FK_EduQuaidM': data.get('m_edu_id') or None,
            'FamilyAnnualIncome': data.get('family_income') or 0,
            'fk_collegeid': data.get('college_id'),
            'fk_degreeid': data.get('degree_id'),
            'fk_adm_session': data.get('session_id'),
            'fk_catid': data.get('cat_id'),
            'fk_religionid': data.get('rel_id'),
            'Cast': data.get('caste'),
            'AdharNo': data.get('aadhar_no'),
            'Telephoneno': data.get('tel_res'),
            'phoneno': data.get('ph_no'),
            'CorrPhoneno': data.get('stu_mobile'),
            'PContactMobileNo': data.get('parent_mobile'),
            's_emailid': data.get('email'),
            'PContactNoLandline': data.get('landline'),
            'postaladdress': data.get('postal_address'),
            'paddress': data.get('p_address'),
            'PAddressType': data.get('addr_type'),
            'CriminalCase': data.get('criminal', 'N'),
            'NoOfSiblingBro': data.get('sib_bro') or 0,
            'NoOfSiblingSis': data.get('sib_sis') or 0,
            'MembersInGovJob': data.get('gov_job') or 0,
            'IsBPL': data.get('bpl_apl'),
            'HaveLand': data.get('have_land', 'N'),
            'StartAgeSchooling': data.get('start_school') or None,
            'IsFamilyJoint': data.get('family_type'),
            'HouseDisc': data.get('house_type'),
            'Hobbies': data.get('hobbies'),
            'PerentMarriedDate': data.get('married_since') or None,
            'PetOwnedDisc': data.get('pets'),
            'WhyOptVS': data.get('why_vet'),
            'ParticipatioInsports': data.get('sports_part', 'N'),
            'HavePassport': data.get('have_passport', 'N'),
            'PassportDetails': data.get('passport_dtl'),
            'ReadNewsPaper': data.get('read_news', 'N'),
            'NewsPaperDtl': data.get('news_dtl'),
            'IsVisitedAbroad': data.get('travel_abroad', 'N'),
            'AbroadVisitDisc': data.get('abroad_dtl'),
            'IsStayingAbroad': data.get('relative_abroad', 'N'),
            'AbroadStayDetails': data.get('relative_dtl'),
            'DidCoaching': data.get('coaching', 'N'),
            'HavePCLaptop': data.get('pc_laptop', 'N'),
            'HaveNetconnection': data.get('net_conn', 'N'),
            'InternetSourse': data.get('net_lines'),
            'HaveVehicle': data.get('have_vehicle', 'N'),
            'VehicleDtl': data.get('vehicle_dtl'),
            'IsLandPossess': data.get('land_possess', 'N'),
            'IntendAfterDegree': data.get('intend'),
            'Updated_by': user_id,
            'last_updated_date': 'GETDATE()'
        }

        set_clause = ", ".join([f"{k}=?" for k in basic_fields.keys() if k != 'last_updated_date'])
        set_clause += ", last_updated_date=GETDATE()"
        params = [v for k, v in basic_fields.items() if k != 'last_updated_date']
        params.append(sid)
        
        DB.execute(f"UPDATE SMS_Student_Mst SET {set_clause} WHERE pk_sid=?", params)

        # 2. Update Schooling Details
        DB.execute("DELETE FROM SMS_stuSchooling_dtl WHERE FK_BDid=?", [sid])
        edu_types = data.getlist('edu_type_id[]')
        school_types = data.getlist('school_type[]')
        school_dtls = data.getlist('school_dtl[]')
        for i in range(len(edu_types)):
            if edu_types[i]:
                DB.execute("INSERT INTO SMS_stuSchooling_dtl (FK_BDid, fk_Edutypeid, fK_schooltypeid, details) VALUES (?, ?, ?, ?)",
                           [sid, edu_types[i], school_types[i], school_dtls[i]])

        # 3. Update UG Prep
        DB.execute("DELETE FROM SMS_UnderGradDetail_dtl WHERE fk_sid=?", [sid])
        ug_cids = data.getlist('ug_cid[]')
        ug_cnames = data.getlist('ug_cname[]')
        ug_ccodes = data.getlist('ug_ccode[]')
        ug_ctypes = data.getlist('ug_ctype[]')
        ug_ths = data.getlist('ug_th[]')
        ug_prs = data.getlist('ug_pr[]')
        ug_grades = data.getlist('ug_grade[]')
        ug_marks = data.getlist('ug_marks[]')
        for i in range(len(ug_cnames)):
            if ug_cnames[i]:
                DB.execute("INSERT INTO SMS_UnderGradDetail_dtl (fk_sid, fk_courseid, coursename, coursecode, fk_coursetypeid, crtheory, crpractical, isgrade, marks) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                           [sid, ug_cids[i] or None, ug_cnames[i], ug_ccodes[i], ug_ctypes[i], ug_ths[i], ug_prs[i], ug_grades[i], ug_marks[i]])

        # 4. Update PG Prep
        DB.execute("DELETE FROM SMS_PostGrad_Dtl WHERE fk_sid=?", [sid])
        pg_cids = data.getlist('pg_cid[]')
        pg_cnames = data.getlist('pg_cname[]')
        pg_ccodes = data.getlist('pg_ccode[]')
        pg_ctypes = data.getlist('pg_ctype[]')
        pg_ths = data.getlist('pg_th[]')
        pg_prs = data.getlist('pg_pr[]')
        pg_grades = data.getlist('pg_grade[]')
        pg_marks = data.getlist('pg_marks[]')
        for i in range(len(pg_cnames)):
            if pg_cnames[i]:
                DB.execute("INSERT INTO SMS_PostGrad_Dtl (fk_sid, fk_courseid, coursename, coursecode, fk_coursetypeid, crtheory, crpractical, isgrade, marks) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                           [sid, pg_cids[i] or None, pg_cnames[i], pg_ccodes[i], pg_ctypes[i], pg_ths[i], pg_prs[i], pg_grades[i], pg_marks[i]])

        # 5. Update PreAdmission
        DB.execute("DELETE FROM SMS_StudentPreAdmission_dtl WHERE FK_Sturegid=?", [sid])
        pre_exams = data.getlist('pre_exam[]')
        pre_univs = data.getlist('pre_univ[]')
        pre_years = data.getlist('pre_year[]')
        pre_rolls = data.getlist('pre_roll[]')
        pre_maxs = data.getlist('pre_max[]')
        pre_obts = data.getlist('pre_obt[]')
        pre_pers = data.getlist('pre_per[]')
        pre_subs = data.getlist('pre_sub[]')
        for i in range(len(pre_exams)):
            if pre_exams[i]:
                DB.execute("INSERT INTO SMS_StudentPreAdmission_dtl (FK_Sturegid, fk_ExamId, Univ_Board, Year, RollNo, MaxMarks, MarksObtained, Percentage, SubjectDetails) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                           [sid, pre_exams[i], pre_univs[i], pre_years[i], pre_rolls[i], pre_maxs[i], pre_obts[i], pre_pers[i], pre_subs[i]])

        return True

class PgsCourseLimitModel:
    @staticmethod
    def get_limits(page=1, per_page=10):
        offset = (page - 1) * per_page
        total = DB.fetch_scalar("SELECT COUNT(*) FROM SMS_Sessionwise_PGS_CourseLimit_Mst")
        query = f"""
            SELECT L.pk_PgsId, L.CourseCapacity, 
                   ISNULL(C.collegename, 'Applicable to All') as collegename, 
                   CO.coursename, S.sessionname
            FROM SMS_Sessionwise_PGS_CourseLimit_Mst L
            LEFT JOIN SMS_College_Mst C ON L.fk_collegeid = C.pk_collegeid
            LEFT JOIN SMS_Course_Mst CO ON L.fk_courseId = CO.pk_courseid
            LEFT JOIN SMS_AcademicSession_Mst S ON L.fk_SessionId = S.pk_sessionid
            ORDER BY L.pk_PgsId DESC
            OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY
        """
        return DB.fetch_all(query), total

    @staticmethod
    def save_limit(data):
        # Data validation and prep
        college_id = data.get('college_id') or 0
        course_id = data.get('course_id')
        session_id = data.get('session_id')
        class_id = data.get('class_id') # 1=Odd, 2=Even
        capacity = data.get('capacity')
        user_id = data.get('user_id')

        if not all([course_id, session_id, class_id, capacity]):
            return False

        # Helper function for single upsert
        def upsert_single(col_id, crs_id, sess_id, cls_id, cap, uid):
            # Check if exists
            existing = DB.fetch_scalar("""
                SELECT pk_PgsId FROM SMS_Sessionwise_PGS_CourseLimit_Mst 
                WHERE fk_collegeid=? AND fk_courseId=? AND fk_SessionId=? AND fk_classId=?
            """, [col_id, crs_id, sess_id, cls_id])

            if existing:
                return DB.execute("""
                    UPDATE SMS_Sessionwise_PGS_CourseLimit_Mst 
                    SET CourseCapacity=?, UserId=?
                    WHERE pk_PgsId=?
                """, [cap, uid, existing])
            else:
                return DB.execute("""
                    INSERT INTO SMS_Sessionwise_PGS_CourseLimit_Mst 
                    (fk_collegeid, fk_courseId, fk_SessionId, fk_classId, CourseCapacity, Createdate, UserId) 
                    VALUES (?, ?, ?, ?, ?, GETDATE(), ?)
                """, [col_id, crs_id, sess_id, cls_id, cap, uid])

        if str(college_id) == '0':
            # Apply to ALL colleges
            colleges = DB.fetch_all("SELECT pk_collegeid FROM SMS_College_Mst")
            success = True
            for col in colleges:
                if not upsert_single(col['pk_collegeid'], course_id, session_id, class_id, capacity, user_id):
                    success = False
            return success
        else:
            # Single college
            return upsert_single(college_id, course_id, session_id, class_id, capacity, user_id)

    @staticmethod
    def delete_limit(limit_id):
        # Fetch the record details first to identify the group (Course, Session, Class)
        record = DB.fetch_one("SELECT fk_courseId, fk_SessionId, fk_classId FROM SMS_Sessionwise_PGS_CourseLimit_Mst WHERE pk_PgsId = ?", [limit_id])
        if record:
            return DB.execute("""
                DELETE FROM SMS_Sessionwise_PGS_CourseLimit_Mst 
                WHERE fk_courseId=? AND fk_SessionId=? AND fk_classId=?
            """, [record['fk_courseId'], record['fk_SessionId'], record['fk_classId']])
        return False

class PaperUploadModel:
    @staticmethod
    def get_uploaded_papers(filters):
        # filters: college_id, session_id, degree_id, semester_id, course_id
        # We'll use a specific Page_Name or custom logic to identify these in Common_File_Upload
        # or assuming a table structure if it's missing from my scans
        sql = """
            SELECT U.*, C.coursecode, C.coursename
            FROM Common_File_Upload U
            INNER JOIN SMS_Course_Mst C ON U.fk_docid = CAST(C.pk_courseid AS VARCHAR)
            WHERE U.Page_Name = 'sms_prevpaper_upload.aspx'
        """
        params = []
        if filters.get('course_id'):
            sql += " AND C.pk_courseid = ?"
            params.append(filters['course_id'])
            
        return DB.fetch_all(sql, params)

    @staticmethod
    def save_paper(data, filename, user_id):
        course_id = data.get('course_id')
        sql = """
            INSERT INTO Common_File_Upload (fk_docid, Page_Type, uploadfileName, file_ext, FilePath, Date, Page_Name)
            VALUES (?, 'QuestionPaper', ?, 'pdf', ?, GETDATE(), 'sms_prevpaper_upload.aspx')
        """
        # FilePath simulation
        filepath = f"uploads/papers/{filename}"
        return DB.execute(sql, [course_id, filename, filepath])

class CounsellingModel:
    @staticmethod
    def _normalize_meeting_date(date_value):
        if date_value is None or date_value == "":
            return None
        if hasattr(date_value, "strftime"):
            return date_value

        if not isinstance(date_value, str):
            return date_value

        date_str = date_value.strip()
        if not date_str:
            return None

        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                pass

        # Fall back to original value (e.g., DB expects a varchar date format).
        return date_str

    @staticmethod
    def get_meetings_paginated(search_term=None, page=1, per_page=10):
        offset = (page - 1) * per_page
        sql = """
            SELECT *,
                CONVERT(varchar(10),
                    COALESCE(
                        TRY_CONVERT(date, meetingdate, 103),  -- dd/mm/yyyy
                        TRY_CONVERT(date, meetingdate, 105),  -- dd-mm-yyyy
                        TRY_CONVERT(date, meetingdate)        -- 'Nov 23 2017 12:00AM' / ISO / datetime
                    ),
                23) AS meetingdate_iso
            FROM SMS_Acad_Counselling_Meeting
            WHERE 1=1
        """
        params = []
        if search_term:
            sql += " AND meetingname LIKE ?"
            params.append(f"%{search_term}%")
        
        total = DB.fetch_scalar(f"SELECT COUNT(*) FROM ({sql}) AS T", params)
        # Sort by meeting date (legacy UI behavior), but meetingdate may be stored as:
        # - datetime/date (ideal)
        # - varchar like '23/11/2017'
        # - varchar like 'Nov 23 2017 12:00AM'
        # Use a best-effort parse for ordering and fall back to pk desc.
        sql += """
            ORDER BY
                COALESCE(
                    TRY_CONVERT(datetime, meetingdate, 103),  -- dd/mm/yyyy
                    TRY_CONVERT(datetime, meetingdate, 105),  -- dd-mm-yyyy
                    TRY_CONVERT(datetime, meetingdate)        -- 'Nov 23 2017 12:00AM' / ISO / datetime
                ) DESC,
                pk_Meetingid DESC
        """
        sql += f" OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY"
        return DB.fetch_all(sql, params), total

    @staticmethod
    def save_meeting(data, filename=None):
        pk_id = data.get('id')
        name = data.get('meeting_name')
        date = CounsellingModel._normalize_meeting_date(data.get('meeting_date'))
        agenda = data.get('meeting_agenda')
        
        if pk_id:
            if filename:
                sql = "UPDATE SMS_Acad_Counselling_Meeting SET meetingname=?, meetingdate=?, meetingagenda=?, filename=? WHERE pk_Meetingid=?"
                return DB.execute(sql, [name, date, agenda, filename, pk_id])
            else:
                sql = "UPDATE SMS_Acad_Counselling_Meeting SET meetingname=?, meetingdate=?, meetingagenda=? WHERE pk_Meetingid=?"
                return DB.execute(sql, [name, date, agenda, pk_id])
        else:
            sql = "INSERT INTO SMS_Acad_Counselling_Meeting (meetingname, meetingdate, meetingagenda, filename) VALUES (?, ?, ?, ?)"
            return DB.execute(sql, [name, date, agenda, filename])

    @staticmethod
    def delete_meeting(pk_id):
        return DB.execute("DELETE FROM SMS_Acad_Counselling_Meeting WHERE pk_Meetingid = ?", [pk_id])

class SemesterRegistrationModel:
    @staticmethod
    def get_registrations_paginated(page=1, per_page=10):
        offset = (page - 1) * per_page
        sql = """
            SELECT SR.*, C.collegename, D.degreename, S.sessionname, SEM.semester_roman
            FROM SMS_SemesterRegistration SR
            INNER JOIN SMS_College_Mst C ON SR.fk_collegeid = C.pk_collegeid
            INNER JOIN SMS_Degree_Mst D ON SR.fk_degreeid = D.pk_degreeid
            INNER JOIN SMS_AcademicSession_Mst S ON SR.fk_Sessionid = S.pk_sessionid
            INNER JOIN SMS_Semester_Mst SEM ON SR.fk_semesterid = SEM.pk_semesterid
            ORDER BY SR.SemRegister_Date DESC
        """
        total = DB.fetch_scalar("SELECT COUNT(*) FROM SMS_SemesterRegistration")
        sql += f" OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY"
        return DB.fetch_all(sql), total

    @staticmethod
    def save_registration(data):
        pk_id = data.get('id')
        college_id = data.get('college_id')
        degree_id = data.get('degree_id')
        session_id = data.get('session_id')
        semester_id = data.get('semester_id')
        year_id = data.get('year_id')
        reg_date = data.get('reg_date')
        
        if pk_id:
            sql = """
                UPDATE SMS_SemesterRegistration 
                SET fk_collegeid=?, fk_degreeid=?, fk_Sessionid=?, fk_semesterid=?, fk_degreeyearid=?, SemRegister_Date=?
                WHERE pk_SemRegisterID=?
            """
            return DB.execute(sql, [college_id, degree_id, session_id, semester_id, year_id, reg_date, pk_id])
        else:
            sql = """
                INSERT INTO SMS_SemesterRegistration (fk_collegeid, fk_degreeid, fk_Sessionid, fk_semesterid, fk_degreeyearid, SemRegister_Date)
                VALUES (?, ?, ?, ?, ?, ?)
            """
            return DB.execute(sql, [college_id, degree_id, session_id, semester_id, year_id, reg_date])

    @staticmethod
    def delete_registration(pk_id):
        return DB.execute("DELETE FROM SMS_SemesterRegistration WHERE pk_SemRegisterID = ?", [pk_id])

class EventAssignmentModel:
    @staticmethod
    def get_assignment_master(filters):
        # filters: college_id, session_id, degree_id, year_id
        sql = """
            SELECT * FROM SMS_DegreeWiseCalenderEvent 
            WHERE fk_collegeid = ? AND fk_sessionid = ? AND fk_degreeid = ? AND fk_degreeyearid = ?
        """
        return DB.fetch_one(sql, [filters['college_id'], filters['session_id'], filters['degree_id'], filters['year_id']])

    @staticmethod
    def get_assignment_details(dwce_id):
        sql = "SELECT * FROM SMS_DegreeWiseCalenderEvent_trn WHERE fk_dwceid = ?"
        rows = DB.fetch_all(sql, [dwce_id])
        # Map by event_id for easy template access
        return {r['fk_eventid']: r for r in rows}

    @staticmethod
    def save_assignment(filters, event_data, user_id):
        # event_data: list of dicts with event_id, odd_from, odd_to, even_from, even_to, remarks, events_for
        # First, ensure master exists
        master = EventAssignmentModel.get_assignment_master(filters)
        if master:
            dwce_id = master['pk_dwceid']
        else:
            sql_master = """
                INSERT INTO SMS_DegreeWiseCalenderEvent (fk_collegeid, fk_sessionid, fk_degreeid, fk_degreeyearid, CreatedOn, fk_userId)
                VALUES (?, ?, ?, ?, GETDATE(), ?)
            """
            DB.execute(sql_master, [filters['college_id'], filters['session_id'], filters['degree_id'], filters['year_id'], user_id])
            master = EventAssignmentModel.get_assignment_master(filters)
            dwce_id = master['pk_dwceid']

        for ed in event_data:
            exists = DB.fetch_one("SELECT pk_dwcetrn_id FROM SMS_DegreeWiseCalenderEvent_trn WHERE fk_dwceid = ? AND fk_eventid = ?", [dwce_id, ed['event_id']])
            if exists:
                sql = """
                    UPDATE SMS_DegreeWiseCalenderEvent_trn SET
                        odd_fromDate=?, odd_toDate=?, even_fromDate=?, even_toDate=?,
                        remarks=?, events_for=?, CreatedOn=GETDATE()
                    WHERE pk_dwcetrn_id = ?
                """
                DB.execute(sql, [ed['odd_from'], ed['odd_to'], ed['even_from'], ed['even_to'], ed['remarks'], ed['events_for'], exists['pk_dwcetrn_id']])
            else:
                sql = """
                    INSERT INTO SMS_DegreeWiseCalenderEvent_trn (fk_dwceid, fk_eventid, odd_fromDate, odd_toDate, even_fromDate, even_toDate, remarks, events_for, CreatedOn)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, GETDATE())
                """
                DB.execute(sql, [dwce_id, ed['event_id'], ed['odd_from'], ed['odd_to'], ed['even_from'], ed['even_to'], ed['remarks'], ed['events_for']])
        return True

class EventModel:
    @staticmethod
    def get_events_paginated(page=1, per_page=10):
        offset = (page - 1) * per_page
        sql = "SELECT * FROM SMS_EventCalender_Mst ORDER BY Event_order"
        total = DB.fetch_scalar("SELECT COUNT(*) FROM SMS_EventCalender_Mst")
        sql += f" OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY"
        return DB.fetch_all(sql), total

    @staticmethod
    def save_event(data):
        # data: id (for edit), event_name, code_alias, event_order, remarks
        pk_id = data.get('id')
        name = data.get('event_name')
        alias = data.get('code_alias')
        order = data.get('event_order')
        remarks = data.get('remarks')
        
        if pk_id:
            sql = "UPDATE SMS_EventCalender_Mst SET Event_name=?, Code_alias=?, Event_order=?, Remarks=? WHERE pk_eventid=?"
            return DB.execute(sql, [name, alias, order, remarks, pk_id])
        else:
            sql = "INSERT INTO SMS_EventCalender_Mst (Event_name, Code_alias, Event_order, Remarks) VALUES (?, ?, ?, ?)"
            return DB.execute(sql, [name, alias, order, remarks])

    @staticmethod
    def delete_event(pk_id):
        return DB.execute("DELETE FROM SMS_EventCalender_Mst WHERE pk_eventid = ?", [pk_id])

    @staticmethod
    def get_all_events():
        return DB.fetch_all("SELECT pk_eventid as id, Event_name as name FROM SMS_EventCalender_Mst ORDER BY Event_order")

class AdvisorApprovalModel:
    @staticmethod
    def get_students_for_approval(filters, advisor_id):
        # 1. Determine if UG or PG
        degree_info = DB.fetch_one("""
            SELECT T.isug FROM SMS_Degree_Mst D 
            INNER JOIN SMS_DegreeType_Mst T ON D.fk_degreetypeid = T.pk_degreetypeid
            WHERE D.pk_degreeid = ?
        """, [filters.get('degree_id')])
        
        is_ug = (degree_info and degree_info.get('isug') == 'B')
        
        # Base SQL for student info and their allocated courses
        sql = """
            SELECT DISTINCT S.pk_sid, S.enrollmentno as AdmissionNo, S.fullname,
                   (SELECT STUFF((SELECT '|' + C.coursename + ' / ' + C.coursecode + ' [' + SES.sessionname + ' ](' + CAST(A.crhrth as varchar) + '+' + CAST(A.crhrpr as varchar) + ')'
                                  FROM SMS_StuCourseAllocation A
                                  INNER JOIN SMS_Course_Mst C ON A.fk_courseid = C.pk_courseid
                                  INNER JOIN SMS_AcademicSession_Mst SES ON A.fk_dgacasessionid = SES.pk_sessionid
                                  WHERE A.fk_sturegid = S.pk_sid AND A.fk_exconfigid = ?
                                  FOR XML PATH('')), 1, 1, '')) as courses_info,
                   CAST(ISNULL(APP.Adv_AprrovalStatus, 0) AS BIT) as approved,
                   APP.Remarks_by_Adv as remarks
            FROM SMS_Student_Mst S
            INNER JOIN SMS_StuCourseAllocation SCA ON S.pk_sid = SCA.fk_sturegid
            LEFT JOIN SMS_StuCourseAllocation_Approval_staffwise APP ON SCA.fk_sturegid = APP.fk_sturegid 
                 AND SCA.fk_courseid = APP.fk_courseid AND SCA.fk_exconfigid = APP.fk_exconfigid
            WHERE S.fk_collegeid = ? AND S.fk_curr_session = ? AND S.fk_degreeid = ? 
              AND SCA.fk_exconfigid = ?
        """
        params = [filters.get('exconfig_id'), filters.get('college_id'), filters.get('session_id'), filters.get('degree_id'), filters.get('exconfig_id')]
        
        if filters.get('branch_id') and str(filters['branch_id']) != '0':
            sql += " AND S.fk_branchid = ?"
            params.append(filters['branch_id'])
            
        if is_ug:
            # UG Advisor Mapping
            sql += """ AND EXISTS (
                SELECT 1 FROM sms_AdvisoryStudentApproval ASA
                WHERE ASA.fk_sturegid = S.pk_sid AND ASA.fk_empid = ? AND ASA.fk_stid = 1
            )"""
        else:
            # PG Advisor Mapping
            sql += """ AND EXISTS (
                SELECT 1 FROM SMS_Advisory_Committee_Dtl ACD
                INNER JOIN SMS_Advisory_Committee_Mst ACM ON ACD.fk_adcid = ACM.pk_adcid
                WHERE ACM.fk_stid = S.pk_sid AND ACD.fk_empid = ? AND ACD.fk_statusid = 1
            )"""
        
        params.append(advisor_id)
        
        sql += " ORDER BY S.fullname"
        return DB.fetch_all(sql, params)

    @staticmethod
    def save_approvals(data, advisor_id, user_id):
        # data: student_ids[], approved_ids[], remarks[], action
        action = data.get('action')
        student_ids = data.getlist('student_ids')
        approved_ids = set(data.getlist('approved_ids'))
        remarks = data.getlist('remarks')
        exconfig_id = data.get('exconfig_id')
        
        for i, sid in enumerate(student_ids):
            # If action is 'Hold', we set approved to 0 regardless of checkbox
            if action == 'Hold':
                is_approved = 0
            else:
                is_approved = 1 if sid in approved_ids else 0
                
            rem = remarks[i] if i < len(remarks) else ''
            
            allocations = DB.fetch_all("SELECT * FROM SMS_StuCourseAllocation WHERE fk_sturegid = ? AND fk_exconfigid = ?", [sid, exconfig_id])
            
            for alloc in allocations:
                exists = DB.fetch_one("SELECT Pk_stucoursealloc_staffid FROM SMS_StuCourseAllocation_Approval_staffwise WHERE fk_sturegid = ? AND fk_courseid = ? AND fk_exconfigid = ?", [sid, alloc['fk_courseid'], exconfig_id])
                
                if exists:
                    sql = """
                        UPDATE SMS_StuCourseAllocation_Approval_staffwise
                        SET Adv_AprrovalStatus = ?, Remarks_by_Adv = ?, fk_Advid = ?, 
                            Lastupdatedby = ?, lastupdated = GETDATE()
                        WHERE Pk_stucoursealloc_staffid = ?
                    """
                    DB.execute(sql, [is_approved, rem, advisor_id, user_id, exists['Pk_stucoursealloc_staffid']])
                else:
                    sql = """
                        INSERT INTO SMS_StuCourseAllocation_Approval_staffwise (
                            fk_sturegid, fk_courseid, fk_degreecycleid_alloc, fk_degreecycleid,
                            fk_dgacasessionid_alloc, fk_dgacasessionid, fk_exconfigid,
                            Adv_AprrovalStatus, Remarks_by_Adv, fk_Advid, Lastupdatedby, lastupdated,
                            fk_stucourseallocid
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE(), ?)
                    """
                    DB.execute(sql, [
                        sid, alloc['fk_courseid'], alloc['fk_degreecycleid_alloc'], alloc['fk_degreecycleid'],
                        alloc['fk_dgacasessionid_alloc'], alloc['fk_dgacasessionid'], exconfig_id,
                        is_approved, rem, advisor_id, user_id, alloc['Pk_stucourseallocid']
                    ])
        return True

class TeacherApprovalModel:
    @staticmethod
    def _resolve_staffwise_columns():
        cols = MiscAcademicsModel._table_columns('SMS_StuCourseAllocation_Approval_staffwise')
        status_col = next(
            (
                c for c in (
                    'teach_aprrovalstatus', 'teach_approvalstatus', 'teacher_approvalstatus', 'teacherstatus',
                    'teacher_aprrovalstatus', 'teacheraprrovalstatus', 'teach_appr_status'
                )
                if c in cols
            ),
            None
        )
        remarks_col = next(
            (
                c for c in (
                    'remarks_by_teach', 'remarks_by_teacher', 'teach_remarks', 'teacher_remarks', 'remarks_teacher'
                )
                if c in cols
            ),
            None
        )
        teacher_id_col = next(
            (
                c for c in (
                    'fk_teacherid', 'fk_teachid', 'fk_teacher_id', 'teacherid', 'teachid'
                )
                if c in cols
            ),
            None
        )
        return cols, status_col, remarks_col, teacher_id_col

    @staticmethod
    def _approved_expr(col_name):
        return f"""(
            TRY_CONVERT(INT, {col_name}) > 0
            OR UPPER(CONVERT(VARCHAR(20), {col_name})) IN ('A','Y','YES','APPROVED')
        )"""

    @staticmethod
    def get_students_for_approval(filters, teacher_id):
        cols, status_col, remarks_col, _teacher_id_col = TeacherApprovalModel._resolve_staffwise_columns()
        if not status_col:
            return []

        status_col_sql = status_col
        remarks_select_sql = f"MAX(CONVERT(VARCHAR(2000), APP.{remarks_col}))" if remarks_col else "NULL"

        approved_case = f"""
            CASE
                WHEN COUNT(APP.fk_courseid) = 0 THEN CAST(0 AS BIT)
                WHEN SUM(CASE WHEN {TeacherApprovalModel._approved_expr('APP.' + status_col_sql)} THEN 0 ELSE 1 END) = 0 THEN CAST(1 AS BIT)
                ELSE CAST(0 AS BIT)
            END
        """

        sql = f"""
            SELECT
                S.pk_sid,
                COALESCE(NULLIF(LTRIM(RTRIM(S.enrollmentno)), ''), NULLIF(LTRIM(RTRIM(S.AdmissionNo)), '')) AS AdmissionNo,
                S.fullname,
                (SELECT STUFF((SELECT '|' + C.coursename + ' / ' + C.coursecode + ' [' + SES.sessionname + ' ](' + CAST(A.crhrth as varchar) + '+' + CAST(A.crhrpr as varchar) + ')'
                              FROM SMS_StuCourseAllocation A
                              INNER JOIN SMS_Course_Mst C ON A.fk_courseid = C.pk_courseid
                              INNER JOIN SMS_AcademicSession_Mst SES ON A.fk_dgacasessionid = SES.pk_sessionid
                              WHERE A.fk_sturegid = S.pk_sid AND A.fk_exconfigid = ?
                              AND EXISTS (
                                  SELECT 1 FROM SMS_TCourseAlloc_Mst TM
                                  INNER JOIN SMS_TCourseAlloc_Dtl TD ON TM.pk_tcourseallocid = TD.fk_tcourseallocid
                                  WHERE TM.fk_employeeid = ? AND TM.fk_exconfigid = A.fk_exconfigid AND TD.fk_courseid = A.fk_courseid
                              )
                              FOR XML PATH('')), 1, 1, '')) AS courses_info,
                {approved_case} AS approved,
                {remarks_select_sql} AS remarks
            FROM SMS_Student_Mst S
            INNER JOIN SMS_StuCourseAllocation SCA ON S.pk_sid = SCA.fk_sturegid
            LEFT JOIN SMS_StuCourseAllocation_Approval_staffwise APP
              ON SCA.fk_sturegid = APP.fk_sturegid
             AND SCA.fk_courseid = APP.fk_courseid
             AND SCA.fk_exconfigid = APP.fk_exconfigid
            WHERE S.fk_collegeid = ? AND S.fk_curr_session = ? AND S.fk_degreeid = ?
              AND SCA.fk_exconfigid = ?
              AND EXISTS (
                  SELECT 1 FROM SMS_TCourseAlloc_Mst TM
                  INNER JOIN SMS_TCourseAlloc_Dtl TD ON TM.pk_tcourseallocid = TD.fk_tcourseallocid
                  WHERE TM.fk_employeeid = ? AND TM.fk_exconfigid = SCA.fk_exconfigid AND TD.fk_courseid = SCA.fk_courseid
              )
        """
        params = [
            filters.get('exconfig_id'),
            teacher_id, # for subquery courses_info
            filters.get('college_id'),
            filters.get('session_id'),
            filters.get('degree_id'),
            filters.get('exconfig_id'),
            teacher_id, # for main WHERE clause
        ]

        if filters.get('branch_id') and str(filters['branch_id']) != '0':
            sql += " AND S.fk_branchid = ?"
            params.append(filters['branch_id'])

        sql += " GROUP BY S.pk_sid, S.enrollmentno, S.AdmissionNo, S.fullname ORDER BY S.fullname"
        return DB.fetch_all(sql, params)

    @staticmethod
    def save_approvals(data, teacher_id, user_id):
        cols, status_col, remarks_col, teacher_id_col = TeacherApprovalModel._resolve_staffwise_columns()
        if not status_col:
            return False

        action = data.get('action')
        student_ids = data.getlist('student_ids')
        approved_ids = set(data.getlist('approved_ids'))
        remarks = data.getlist('remarks')
        exconfig_id = data.get('exconfig_id')

        def _safe_col(name):
            import re
            if not name:
                return None
            if not re.match(r'^[A-Za-z0-9_]+$', name):
                return None
            if name.lower() not in cols:
                return None
            return name

        status_col = _safe_col(status_col)
        remarks_col = _safe_col(remarks_col) if remarks_col else None
        teacher_id_col = _safe_col(teacher_id_col) if teacher_id_col else None
        if not status_col:
            return False

        for i, sid in enumerate(student_ids):
            is_approved = 0 if action == 'Hold' else (1 if sid in approved_ids else 0)
            rem = (remarks[i] if i < len(remarks) else '') if remarks_col else None

            allocations = DB.fetch_all(
                "SELECT * FROM SMS_StuCourseAllocation WHERE fk_sturegid = ? AND fk_exconfigid = ?",
                [sid, exconfig_id]
            )

            for alloc in allocations:
                exists = DB.fetch_one(
                    "SELECT Pk_stucoursealloc_staffid FROM SMS_StuCourseAllocation_Approval_staffwise WHERE fk_sturegid = ? AND fk_courseid = ? AND fk_exconfigid = ?",
                    [sid, alloc['fk_courseid'], exconfig_id]
                )

                if exists:
                    sets = [
                        f"{status_col} = ?",
                        "Lastupdatedby = ?",
                        "lastupdated = GETDATE()",
                    ]
                    params = [is_approved, user_id]
                    if remarks_col:
                        sets.insert(1, f"{remarks_col} = ?")
                        params.insert(1, rem)
                    if teacher_id_col:
                        sets.insert(1, f"{teacher_id_col} = ?")
                        params.insert(1, teacher_id)
                    sql = f"""
                        UPDATE SMS_StuCourseAllocation_Approval_staffwise
                        SET {", ".join(sets)}
                        WHERE Pk_stucoursealloc_staffid = ?
                    """
                    DB.execute(sql, params + [exists['Pk_stucoursealloc_staffid']])
                else:
                    insert_cols = [
                        "fk_sturegid", "fk_courseid", "fk_degreecycleid_alloc", "fk_degreecycleid",
                        "fk_dgacasessionid_alloc", "fk_dgacasessionid", "fk_exconfigid",
                        "Lastupdatedby", "lastupdated", "fk_stucourseallocid",
                        status_col,
                    ]
                    insert_vals = [
                        sid, alloc['fk_courseid'], alloc.get('fk_degreecycleid_alloc'), alloc.get('fk_degreecycleid'),
                        alloc.get('fk_dgacasessionid_alloc'), alloc.get('fk_dgacasessionid'), exconfig_id,
                        user_id, None, alloc.get('Pk_stucourseallocid'),
                        is_approved,
                    ]
                    if remarks_col:
                        insert_cols.append(remarks_col)
                        insert_vals.append(rem)
                    if teacher_id_col:
                        insert_cols.append(teacher_id_col)
                        insert_vals.append(teacher_id)

                    placeholders = ",".join(["?"] * len(insert_cols))
                    lastupdated_idx = insert_cols.index("lastupdated")
                    # Replace placeholder for lastupdated with GETDATE()
                    cols_sql = ", ".join(insert_cols)
                    placeholders_list = ["?"] * len(insert_cols)
                    placeholders_list[lastupdated_idx] = "GETDATE()"
                    placeholders_sql = ", ".join(placeholders_list)
                    sql = f"INSERT INTO SMS_StuCourseAllocation_Approval_staffwise ({cols_sql}) VALUES ({placeholders_sql})"
                    # Remove value for lastupdated (None placeholder)
                    insert_vals.pop(lastupdated_idx)
                    DB.execute(sql, insert_vals)

        return True

class DswApprovalModel:
    @staticmethod
    def _resolve_staffwise_columns():
        cols = MiscAcademicsModel._table_columns('SMS_StuCourseAllocation_Approval_staffwise')
        status_col = next(
            (
                c for c in (
                    'dsw_aprrovalstatus', 'dsw_approvalstatus', 'dsw_approval_status', 'dswstatus',
                    'dswaprrovalstatus', 'dswapprovalstatus'
                )
                if c in cols
            ),
            None
        )
        remarks_col = next(
            (
                c for c in (
                    'remarks_by_dsw', 'dsw_remarks', 'remarks_dsw'
                )
                if c in cols
            ),
            None
        )
        dsw_id_col = next(
            (
                c for c in (
                    'fk_dswid', 'fk_dsw_id', 'dswid'
                )
                if c in cols
            ),
            None
        )
        teacher_status_col = next(
            (
                c for c in (
                    'teach_aprrovalstatus', 'teach_approvalstatus', 'teacher_approvalstatus', 'teacherstatus',
                    'teacher_aprrovalstatus'
                )
                if c in cols
            ),
            None
        )
        return cols, status_col, remarks_col, dsw_id_col, teacher_status_col

    @staticmethod
    def _approved_expr(col_name):
        return f"""(
            TRY_CONVERT(INT, {col_name}) > 0
            OR UPPER(CONVERT(VARCHAR(20), {col_name})) IN ('A','Y','YES','APPROVED')
        )"""

    @staticmethod
    def get_students_for_approval(filters, dsw_emp_id):
        cols, status_col, remarks_col, _dsw_id_col, teacher_status_col = DswApprovalModel._resolve_staffwise_columns()
        if not status_col:
            return []

        remarks_select_sql = f"MAX(CONVERT(VARCHAR(2000), APP.{remarks_col}))" if remarks_col else "NULL"

        approved_case = f"""
            CASE
                WHEN COUNT(APP.fk_courseid) = 0 THEN CAST(0 AS BIT)
                WHEN SUM(CASE WHEN {DswApprovalModel._approved_expr('APP.' + status_col)} THEN 0 ELSE 1 END) = 0 THEN CAST(1 AS BIT)
                ELSE CAST(0 AS BIT)
            END
        """

        sql = f"""
            SELECT
                S.pk_sid,
                COALESCE(NULLIF(LTRIM(RTRIM(S.enrollmentno)), ''), NULLIF(LTRIM(RTRIM(S.AdmissionNo)), '')) AS AdmissionNo,
                S.fullname,
                (SELECT STUFF((SELECT '|' + C.coursename + ' / ' + C.coursecode + ' [' + SES.sessionname + ' ](' + CAST(A.crhrth as varchar) + '+' + CAST(A.crhrpr as varchar) + ')'
                              FROM SMS_StuCourseAllocation A
                              INNER JOIN SMS_Course_Mst C ON A.fk_courseid = C.pk_courseid
                              INNER JOIN SMS_AcademicSession_Mst SES ON A.fk_dgacasessionid = SES.pk_sessionid
                              WHERE A.fk_sturegid = S.pk_sid AND A.fk_exconfigid = SCA.fk_exconfigid
                                AND C.coursecode LIKE 'PGS%'
                              FOR XML PATH('')), 1, 1, '')) AS courses_info,
                {approved_case} AS approved,
                {remarks_select_sql} AS remarks
            FROM SMS_Student_Mst S
            INNER JOIN SMS_StuCourseAllocation SCA ON S.pk_sid = SCA.fk_sturegid
            INNER JOIN SMS_Course_Mst CM ON SCA.fk_courseid = CM.pk_courseid
            LEFT JOIN SMS_DegreeCycle_Mst DC ON SCA.fk_degreecycleid = DC.pk_degreecycleid
            LEFT JOIN SMS_StuCourseAllocation_Approval_staffwise APP
              ON SCA.fk_sturegid = APP.fk_sturegid
             AND SCA.fk_courseid = APP.fk_courseid
             AND SCA.fk_exconfigid = APP.fk_exconfigid
            WHERE S.fk_collegeid = ? AND S.fk_curr_session = ? AND S.fk_degreeid = ?
              AND SCA.fk_exconfigid = ?
              AND CM.coursecode LIKE 'PGS%'
        """
        params = [
            filters.get('college_id'),
            filters.get('session_id'),
            filters.get('degree_id'),
            filters.get('exconfig_id'),
        ]

        if filters.get('semester_id') and str(filters['semester_id']) != '0':
            sql += " AND DC.fk_semesterid = ?"
            params.append(filters['semester_id'])

        # Typically DSW comes after teacher. If teacher status column exists, show only where all course rows are teacher-approved.
        if teacher_status_col:
            sql += f"""
              AND NOT EXISTS (
                    SELECT 1
                    FROM SMS_StuCourseAllocation A2
                    INNER JOIN SMS_Course_Mst C2 ON A2.fk_courseid = C2.pk_courseid
                    LEFT JOIN SMS_StuCourseAllocation_Approval_staffwise APP2
                      ON A2.fk_sturegid = APP2.fk_sturegid
                     AND A2.fk_courseid = APP2.fk_courseid
                     AND A2.fk_exconfigid = APP2.fk_exconfigid
                    WHERE A2.fk_sturegid = S.pk_sid AND A2.fk_exconfigid = SCA.fk_exconfigid
                      AND C2.coursecode LIKE 'PGS%'
                      AND NOT ({DswApprovalModel._approved_expr('APP2.' + teacher_status_col)})
              )
            """

        sql += " GROUP BY S.pk_sid, S.enrollmentno, S.AdmissionNo, S.fullname, SCA.fk_exconfigid ORDER BY S.fullname"
        return DB.fetch_all(sql, params)

    @staticmethod
    def get_pending_students(filters, dsw_emp_id):
        cols, status_col, _remarks_col, _dsw_id_col, teacher_status_col = DswApprovalModel._resolve_staffwise_columns()
        if not status_col:
            return []

        # Advisor status column
        adv_status_col = next((c for c in ('adv_aprrovalstatus', 'adv_approvalstatus', 'advisor_approvalstatus') if c in cols), None)

        sql = f"""
            SELECT
                S.pk_sid,
                COALESCE(NULLIF(LTRIM(RTRIM(S.enrollmentno)), ''), NULLIF(LTRIM(RTRIM(S.AdmissionNo)), '')) AS AdmissionNo,
                S.fullname,
                CASE 
                    WHEN EXISTS (
                        SELECT 1 FROM SMS_StuCourseAllocation A2
                        INNER JOIN SMS_Course_Mst C2 ON A2.fk_courseid = C2.pk_courseid
                        LEFT JOIN SMS_StuCourseAllocation_Approval_staffwise APP2
                          ON A2.fk_sturegid = APP2.fk_sturegid AND A2.fk_courseid = APP2.fk_courseid AND A2.fk_exconfigid = APP2.fk_exconfigid
                        WHERE A2.fk_sturegid = S.pk_sid AND A2.fk_exconfigid = SCA.fk_exconfigid
                          AND C2.coursecode LIKE 'PGS%'
                          AND ({DswApprovalModel._approved_expr('APP2.' + status_col)})
                    ) THEN 'Approved'
                    ELSE 'Pending'
                END as approval_status,
                CASE
                    WHEN EXISTS (
                        SELECT 1 FROM SMS_StuCourseAllocation A2
                        INNER JOIN SMS_Course_Mst C2 ON A2.fk_courseid = C2.pk_courseid
                        LEFT JOIN SMS_StuCourseAllocation_Approval_staffwise APP2
                          ON A2.fk_sturegid = APP2.fk_sturegid AND A2.fk_courseid = APP2.fk_courseid AND A2.fk_exconfigid = APP2.fk_exconfigid
                        WHERE A2.fk_sturegid = S.pk_sid AND A2.fk_exconfigid = SCA.fk_exconfigid
                          AND C2.coursecode LIKE 'PGS%'
                          AND NOT ({DswApprovalModel._approved_expr('APP2.' + (adv_status_col if adv_status_col else '1'))})
                    ) THEN 'On Advisor Level'
                    WHEN EXISTS (
                        SELECT 1 FROM SMS_StuCourseAllocation A2
                        INNER JOIN SMS_Course_Mst C2 ON A2.fk_courseid = C2.pk_courseid
                        LEFT JOIN SMS_StuCourseAllocation_Approval_staffwise APP2
                          ON A2.fk_sturegid = APP2.fk_sturegid AND A2.fk_courseid = APP2.fk_courseid AND A2.fk_exconfigid = APP2.fk_exconfigid
                        WHERE A2.fk_sturegid = S.pk_sid AND A2.fk_exconfigid = SCA.fk_exconfigid
                          AND C2.coursecode LIKE 'PGS%'
                          AND NOT ({DswApprovalModel._approved_expr('APP2.' + (teacher_status_col if teacher_status_col else '1'))})
                    ) THEN 'On Teacher Level'
                    WHEN NOT EXISTS (
                        SELECT 1 FROM SMS_StuCourseAllocation A2
                        INNER JOIN SMS_Course_Mst C2 ON A2.fk_courseid = C2.pk_courseid
                        LEFT JOIN SMS_StuCourseAllocation_Approval_staffwise APP2
                          ON A2.fk_sturegid = APP2.fk_sturegid AND A2.fk_courseid = APP2.fk_courseid AND A2.fk_exconfigid = APP2.fk_exconfigid
                        WHERE A2.fk_sturegid = S.pk_sid AND A2.fk_exconfigid = SCA.fk_exconfigid
                          AND C2.coursecode LIKE 'PGS%'
                          AND ({DswApprovalModel._approved_expr('APP2.' + status_col)})
                    ) THEN 'On DSW Level'
                    ELSE ''
                END as remarks
            FROM SMS_Student_Mst S
            INNER JOIN SMS_StuCourseAllocation SCA ON S.pk_sid = SCA.fk_sturegid
            INNER JOIN SMS_Course_Mst CM ON SCA.fk_courseid = CM.pk_courseid
            LEFT JOIN SMS_DegreeCycle_Mst DC ON SCA.fk_degreecycleid = DC.pk_degreecycleid
            WHERE S.fk_collegeid = ? AND S.fk_curr_session = ? AND S.fk_degreeid = ?
              AND SCA.fk_exconfigid = ?
              AND CM.coursecode LIKE 'PGS%'
        """
        params = [
            filters.get('college_id'),
            filters.get('session_id'),
            filters.get('degree_id'),
            filters.get('exconfig_id'),
        ]

        if filters.get('semester_id') and str(filters['semester_id']) != '0':
            sql += " AND DC.fk_semesterid = ?"
            params.append(filters['semester_id'])

        sql += " GROUP BY S.pk_sid, S.enrollmentno, S.AdmissionNo, S.fullname, SCA.fk_exconfigid ORDER BY S.fullname"
        return DB.fetch_all(sql, params)

    @staticmethod
    def save_approvals(data, dsw_emp_id, user_id):
        cols, status_col, remarks_col, dsw_id_col, _teacher_status_col = DswApprovalModel._resolve_staffwise_columns()
        if not status_col:
            return False

        action = data.get('action')
        student_ids = data.getlist('student_ids')
        approved_ids = set(data.getlist('approved_ids'))
        remarks = data.getlist('remarks')
        exconfig_id = data.get('exconfig_id')

        def _safe_col(name):
            import re
            if not name:
                return None
            if not re.match(r'^[A-Za-z0-9_]+$', name):
                return None
            if name.lower() not in cols:
                return None
            return name

        status_col = _safe_col(status_col)
        remarks_col = _safe_col(remarks_col) if remarks_col else None
        dsw_id_col = _safe_col(dsw_id_col) if dsw_id_col else None
        if not status_col:
            return False

        for i, sid in enumerate(student_ids):
            is_approved = 0 if action == 'Hold' else (1 if sid in approved_ids else 0)
            rem = (remarks[i] if i < len(remarks) else '') if remarks_col else None

            allocations = DB.fetch_all(
                """SELECT A.* FROM SMS_StuCourseAllocation A
                   INNER JOIN SMS_Course_Mst C ON A.fk_courseid = C.pk_courseid
                   WHERE A.fk_sturegid = ? AND A.fk_exconfigid = ? AND C.coursecode LIKE 'PGS%'""",
                [sid, exconfig_id]
            )

            for alloc in allocations:
                exists = DB.fetch_one(
                    "SELECT Pk_stucoursealloc_staffid FROM SMS_StuCourseAllocation_Approval_staffwise WHERE fk_sturegid = ? AND fk_courseid = ? AND fk_exconfigid = ?",
                    [sid, alloc['fk_courseid'], exconfig_id]
                )

                if exists:
                    sets = [
                        f"{status_col} = ?",
                        "Lastupdatedby = ?",
                        "lastupdated = GETDATE()",
                    ]
                    params = [is_approved, user_id]
                    if remarks_col:
                        sets.insert(1, f"{remarks_col} = ?")
                        params.insert(1, rem)
                    if dsw_id_col:
                        sets.insert(1, f"{dsw_id_col} = ?")
                        params.insert(1, dsw_emp_id)
                    sql = f"""
                        UPDATE SMS_StuCourseAllocation_Approval_staffwise
                        SET {", ".join(sets)}
                        WHERE Pk_stucoursealloc_staffid = ?
                    """
                    DB.execute(sql, params + [exists['Pk_stucoursealloc_staffid']])
                else:
                    insert_cols = [
                        "fk_sturegid", "fk_courseid", "fk_degreecycleid_alloc", "fk_degreecycleid",
                        "fk_dgacasessionid_alloc", "fk_dgacasessionid", "fk_exconfigid",
                        "Lastupdatedby", "lastupdated", "fk_stucourseallocid",
                        status_col,
                    ]
                    insert_vals = [
                        sid, alloc['fk_courseid'], alloc.get('fk_degreecycleid_alloc'), alloc.get('fk_degreecycleid'),
                        alloc.get('fk_dgacasessionid_alloc'), alloc.get('fk_dgacasessionid'), exconfig_id,
                        user_id, None, alloc.get('Pk_stucourseallocid'),
                        is_approved,
                    ]
                    if remarks_col:
                        insert_cols.append(remarks_col)
                        insert_vals.append(rem)
                    if dsw_id_col:
                        insert_cols.append(dsw_id_col)
                        insert_vals.append(dsw_emp_id)

                    lastupdated_idx = insert_cols.index("lastupdated")
                    cols_sql = ", ".join(insert_cols)
                    placeholders_list = ["?"] * len(insert_cols)
                    placeholders_list[lastupdated_idx] = "GETDATE()"
                    placeholders_sql = ", ".join(placeholders_list)
                    sql = f"INSERT INTO SMS_StuCourseAllocation_Approval_staffwise ({cols_sql}) VALUES ({placeholders_sql})"
                    insert_vals.pop(lastupdated_idx)
                    DB.execute(sql, insert_vals)

        return True

class LibraryApprovalModel:
    @staticmethod
    def _resolve_staffwise_columns():
        cols = MiscAcademicsModel._table_columns('SMS_StuCourseAllocation_Approval_staffwise')
        status_col = next(
            (
                c for c in (
                    'lib_aprrovalstatus', 'lib_approvalstatus', 'library_aprrovalstatus', 'library_approvalstatus',
                    'librarian_aprrovalstatus', 'librarian_approvalstatus', 'libstatus', 'librarystatus'
                )
                if c in cols
            ),
            None
        )
        remarks_col = next(
            (
                c for c in (
                    'remarks_by_library', 'remarks_by_librarian', 'lib_remarks', 'library_remarks', 'remarks_library'
                )
                if c in cols
            ),
            None
        )
        lib_id_col = next(
            (
                c for c in (
                    'fk_libid', 'fk_libraryid', 'fk_librarianid', 'fk_lib_id', 'libid', 'libraryid'
                )
                if c in cols
            ),
            None
        )
        dsw_status_col = next(
            (
                c for c in (
                    'dsw_aprrovalstatus', 'dsw_approvalstatus', 'dsw_approval_status', 'dswstatus',
                    'dswaprrovalstatus', 'dswapprovalstatus'
                )
                if c in cols
            ),
            None
        )
        return cols, status_col, remarks_col, lib_id_col, dsw_status_col

    @staticmethod
    def _approved_expr(col_name):
        return f"""(
            TRY_CONVERT(INT, {col_name}) > 0
            OR UPPER(CONVERT(VARCHAR(20), {col_name})) IN ('A','Y','YES','APPROVED')
        )"""

    @staticmethod
    def get_students_for_approval(filters, lib_emp_id):
        cols, status_col, remarks_col, _lib_id_col, dsw_status_col = LibraryApprovalModel._resolve_staffwise_columns()
        if not status_col:
            return []

        remarks_select_sql = f"MAX(CONVERT(VARCHAR(2000), APP.{remarks_col}))" if remarks_col else "NULL"

        approved_case = f"""
            CASE
                WHEN COUNT(APP.fk_courseid) = 0 THEN CAST(0 AS BIT)
                WHEN SUM(CASE WHEN {LibraryApprovalModel._approved_expr('APP.' + status_col)} THEN 0 ELSE 1 END) = 0 THEN CAST(1 AS BIT)
                ELSE CAST(0 AS BIT)
            END
        """

        sql = f"""
            SELECT
                S.pk_sid,
                COALESCE(NULLIF(LTRIM(RTRIM(S.enrollmentno)), ''), NULLIF(LTRIM(RTRIM(S.AdmissionNo)), '')) AS AdmissionNo,
                S.fullname,
                (SELECT STUFF((SELECT '|' + C.coursename + ' / ' + C.coursecode + ' [' + SES.sessionname + ' ](' + CAST(A.crhrth as varchar) + '+' + CAST(A.crhrpr as varchar) + ')'
                              FROM SMS_StuCourseAllocation A
                              INNER JOIN SMS_Course_Mst C ON A.fk_courseid = C.pk_courseid
                              INNER JOIN SMS_AcademicSession_Mst SES ON A.fk_dgacasessionid = SES.pk_sessionid
                              WHERE A.fk_sturegid = S.pk_sid AND A.fk_exconfigid = SCA.fk_exconfigid
                                AND C.coursecode LIKE 'PGS%'
                              FOR XML PATH('')), 1, 1, '')) AS courses_info,
                {approved_case} AS approved,
                {remarks_select_sql} AS remarks
            FROM SMS_Student_Mst S
            INNER JOIN SMS_StuCourseAllocation SCA ON S.pk_sid = SCA.fk_sturegid
            INNER JOIN SMS_Course_Mst CM ON SCA.fk_courseid = CM.pk_courseid
            LEFT JOIN SMS_DegreeCycle_Mst DC ON SCA.fk_degreecycleid = DC.pk_degreecycleid
            LEFT JOIN SMS_StuCourseAllocation_Approval_staffwise APP
              ON SCA.fk_sturegid = APP.fk_sturegid
             AND SCA.fk_courseid = APP.fk_courseid
             AND SCA.fk_exconfigid = APP.fk_exconfigid
            WHERE S.fk_collegeid = ? AND S.fk_curr_session = ? AND S.fk_degreeid = ?
              AND SCA.fk_exconfigid = ?
              AND CM.coursecode LIKE 'PGS%'
        """
        params = [
            filters.get('college_id'),
            filters.get('session_id'),
            filters.get('degree_id'),
            filters.get('exconfig_id'),
        ]

        if filters.get('semester_id') and str(filters['semester_id']) != '0':
            sql += " AND DC.fk_semesterid = ?"
            params.append(filters['semester_id'])

        if filters.get('branch_id') and str(filters['branch_id']) != '0':
            sql += " AND S.fk_branchid = ?"
            params.append(filters['branch_id'])

        # Library typically comes after DSW. If DSW status column exists, show only where all course rows are DSW-approved.
        if dsw_status_col:
            sql += f"""
              AND NOT EXISTS (
                    SELECT 1
                    FROM SMS_StuCourseAllocation A2
                    INNER JOIN SMS_Course_Mst C2 ON A2.fk_courseid = C2.pk_courseid
                    LEFT JOIN SMS_StuCourseAllocation_Approval_staffwise APP2
                      ON A2.fk_sturegid = APP2.fk_sturegid
                     AND A2.fk_courseid = APP2.fk_courseid
                     AND A2.fk_exconfigid = APP2.fk_exconfigid
                    WHERE A2.fk_sturegid = S.pk_sid AND A2.fk_exconfigid = SCA.fk_exconfigid
                      AND C2.coursecode LIKE 'PGS%'
                      AND NOT ({LibraryApprovalModel._approved_expr('APP2.' + dsw_status_col)})
              )
            """

        sql += " GROUP BY S.pk_sid, S.enrollmentno, S.AdmissionNo, S.fullname, SCA.fk_exconfigid ORDER BY S.fullname"
        return DB.fetch_all(sql, params)

    @staticmethod
    def save_approvals(data, lib_emp_id, user_id):
        cols, status_col, remarks_col, lib_id_col, _dsw_status_col = LibraryApprovalModel._resolve_staffwise_columns()
        if not status_col:
            return False

        action = data.get('action')
        student_ids = data.getlist('student_ids')
        approved_ids = set(data.getlist('approved_ids'))
        remarks = data.getlist('remarks')
        exconfig_id = data.get('exconfig_id')

        def _safe_col(name):
            import re
            if not name:
                return None
            if not re.match(r'^[A-Za-z0-9_]+$', name):
                return None
            if name.lower() not in cols:
                return None
            return name

        status_col = _safe_col(status_col)
        remarks_col = _safe_col(remarks_col) if remarks_col else None
        lib_id_col = _safe_col(lib_id_col) if lib_id_col else None
        if not status_col:
            return False

        for i, sid in enumerate(student_ids):
            is_approved = 0 if action == 'Hold' else (1 if sid in approved_ids else 0)
            rem = (remarks[i] if i < len(remarks) else '') if remarks_col else None

            allocations = DB.fetch_all(
                """SELECT A.* FROM SMS_StuCourseAllocation A
                   INNER JOIN SMS_Course_Mst C ON A.fk_courseid = C.pk_courseid
                   WHERE A.fk_sturegid = ? AND A.fk_exconfigid = ? AND C.coursecode LIKE 'PGS%'""",
                [sid, exconfig_id]
            )

            for alloc in allocations:
                exists = DB.fetch_one(
                    "SELECT Pk_stucoursealloc_staffid FROM SMS_StuCourseAllocation_Approval_staffwise WHERE fk_sturegid = ? AND fk_courseid = ? AND fk_exconfigid = ?",
                    [sid, alloc['fk_courseid'], exconfig_id]
                )

                if exists:
                    sets = [
                        f"{status_col} = ?",
                        "Lastupdatedby = ?",
                        "lastupdated = GETDATE()",
                    ]
                    params = [is_approved, user_id]
                    if remarks_col:
                        sets.insert(1, f"{remarks_col} = ?")
                        params.insert(1, rem)
                    if lib_id_col:
                        sets.insert(1, f"{lib_id_col} = ?")
                        params.insert(1, lib_emp_id)
                    sql = f"""
                        UPDATE SMS_StuCourseAllocation_Approval_staffwise
                        SET {', '.join(sets)}
                        WHERE Pk_stucoursealloc_staffid = ?
                    """
                    DB.execute(sql, params + [exists['Pk_stucoursealloc_staffid']])
                else:
                    insert_cols = [
                        "fk_sturegid", "fk_courseid", "fk_degreecycleid_alloc", "fk_degreecycleid",
                        "fk_dgacasessionid_alloc", "fk_dgacasessionid", "fk_exconfigid",
                        "Lastupdatedby", "lastupdated", "fk_stucourseallocid",
                        status_col,
                    ]
                    insert_vals = [
                        sid, alloc['fk_courseid'], alloc.get('fk_degreecycleid_alloc'), alloc.get('fk_degreecycleid'),
                        alloc.get('fk_dgacasessionid_alloc'), alloc.get('fk_dgacasessionid'), exconfig_id,
                        user_id, None, alloc.get('Pk_stucourseallocid'),
                        is_approved,
                    ]
                    if remarks_col:
                        insert_cols.append(remarks_col)
                        insert_vals.append(rem)
                    if lib_id_col:
                        insert_cols.append(lib_id_col)
                        insert_vals.append(lib_emp_id)

                    lastupdated_idx = insert_cols.index("lastupdated")
                    cols_sql = ", ".join(insert_cols)
                    placeholders_list = ["?"] * len(insert_cols)
                    placeholders_list[lastupdated_idx] = "GETDATE()"
                    placeholders_sql = ", ".join(placeholders_list)
                    sql = f"INSERT INTO SMS_StuCourseAllocation_Approval_staffwise ({cols_sql}) VALUES ({placeholders_sql})"
                    insert_vals.pop(lastupdated_idx)
                    DB.execute(sql, insert_vals)

        return True

    @staticmethod
    def get_pending_students(filters, lib_emp_id):
        cols, status_col, _remarks_col, _lib_id_col, dsw_status_col = LibraryApprovalModel._resolve_staffwise_columns()
        if not status_col:
            return []

        # Advisor status column
        adv_status_col = next((c for c in ('adv_aprrovalstatus', 'adv_approvalstatus', 'advisor_approvalstatus') if c in cols), None)
        # Teacher status column
        teacher_status_col = next((c for c in ('teach_aprrovalstatus', 'teach_approvalstatus', 'teacher_approvalstatus', 'teacherstatus') if c in cols), None)

        sql = f"""
            SELECT
                S.pk_sid,
                COALESCE(NULLIF(LTRIM(RTRIM(S.enrollmentno)), ''), NULLIF(LTRIM(RTRIM(S.AdmissionNo)), '')) AS AdmissionNo,
                S.fullname,
                CASE 
                    WHEN EXISTS (
                        SELECT 1 FROM SMS_StuCourseAllocation A2
                        INNER JOIN SMS_Course_Mst C2 ON A2.fk_courseid = C2.pk_courseid
                        LEFT JOIN SMS_StuCourseAllocation_Approval_staffwise APP2
                          ON A2.fk_sturegid = APP2.fk_sturegid AND A2.fk_courseid = APP2.fk_courseid AND A2.fk_exconfigid = APP2.fk_exconfigid
                        WHERE A2.fk_sturegid = S.pk_sid AND A2.fk_exconfigid = SCA.fk_exconfigid
                          AND C2.coursecode LIKE 'PGS%'
                          AND ({LibraryApprovalModel._approved_expr('APP2.' + status_col)})
                    ) THEN 'Approved'
                    ELSE 'Pending'
                END as approval_status,
                CASE
                    WHEN EXISTS (
                        SELECT 1 FROM SMS_StuCourseAllocation A2
                        INNER JOIN SMS_Course_Mst C2 ON A2.fk_courseid = C2.pk_courseid
                        LEFT JOIN SMS_StuCourseAllocation_Approval_staffwise APP2
                          ON A2.fk_sturegid = APP2.fk_sturegid AND A2.fk_courseid = APP2.fk_courseid AND A2.fk_exconfigid = APP2.fk_exconfigid
                        WHERE A2.fk_sturegid = S.pk_sid AND A2.fk_exconfigid = SCA.fk_exconfigid
                          AND C2.coursecode LIKE 'PGS%'
                          AND NOT ({LibraryApprovalModel._approved_expr('APP2.' + (adv_status_col if adv_status_col else '1'))})
                    ) THEN 'On Advisor Level'
                    WHEN EXISTS (
                        SELECT 1 FROM SMS_StuCourseAllocation A2
                        INNER JOIN SMS_Course_Mst C2 ON A2.fk_courseid = C2.pk_courseid
                        LEFT JOIN SMS_StuCourseAllocation_Approval_staffwise APP2
                          ON A2.fk_sturegid = APP2.fk_sturegid AND A2.fk_courseid = APP2.fk_courseid AND A2.fk_exconfigid = APP2.fk_exconfigid
                        WHERE A2.fk_sturegid = S.pk_sid AND A2.fk_exconfigid = SCA.fk_exconfigid
                          AND C2.coursecode LIKE 'PGS%'
                          AND NOT ({LibraryApprovalModel._approved_expr('APP2.' + (teacher_status_col if teacher_status_col else '1'))})
                    ) THEN 'On Teacher Level'
                    WHEN EXISTS (
                        SELECT 1 FROM SMS_StuCourseAllocation A2
                        INNER JOIN SMS_Course_Mst C2 ON A2.fk_courseid = C2.pk_courseid
                        LEFT JOIN SMS_StuCourseAllocation_Approval_staffwise APP2
                          ON A2.fk_sturegid = APP2.fk_sturegid AND A2.fk_courseid = APP2.fk_courseid AND A2.fk_exconfigid = APP2.fk_exconfigid
                        WHERE A2.fk_sturegid = S.pk_sid AND A2.fk_exconfigid = SCA.fk_exconfigid
                          AND C2.coursecode LIKE 'PGS%'
                          AND NOT ({LibraryApprovalModel._approved_expr('APP2.' + (dsw_status_col if dsw_status_col else '1'))})
                    ) THEN 'On DSW Level'
                    WHEN NOT EXISTS (
                        SELECT 1 FROM SMS_StuCourseAllocation A2
                        INNER JOIN SMS_Course_Mst C2 ON A2.fk_courseid = C2.pk_courseid
                        LEFT JOIN SMS_StuCourseAllocation_Approval_staffwise APP2
                          ON A2.fk_sturegid = APP2.fk_sturegid AND A2.fk_courseid = APP2.fk_courseid AND A2.fk_exconfigid = APP2.fk_exconfigid
                        WHERE A2.fk_sturegid = S.pk_sid AND A2.fk_exconfigid = SCA.fk_exconfigid
                          AND C2.coursecode LIKE 'PGS%'
                          AND ({LibraryApprovalModel._approved_expr('APP2.' + status_col)})
                    ) THEN 'On Library Level'
                    ELSE ''
                END as remarks
            FROM SMS_Student_Mst S
            INNER JOIN SMS_StuCourseAllocation SCA ON S.pk_sid = SCA.fk_sturegid
            INNER JOIN SMS_Course_Mst CM ON SCA.fk_courseid = CM.pk_courseid
            LEFT JOIN SMS_DegreeCycle_Mst DC ON SCA.fk_degreecycleid = DC.pk_degreecycleid
            LEFT JOIN SMS_StuCourseAllocation_Approval_staffwise APP
              ON SCA.fk_sturegid = APP.fk_sturegid
             AND SCA.fk_courseid = APP.fk_courseid
             AND SCA.fk_exconfigid = APP.fk_exconfigid
            WHERE S.fk_collegeid = ? AND S.fk_curr_session = ? AND S.fk_degreeid = ?
              AND SCA.fk_exconfigid = ?
              AND CM.coursecode LIKE 'PGS%'
        """
        params = [
            filters.get('college_id'),
            filters.get('session_id'),
            filters.get('degree_id'),
            filters.get('exconfig_id'),
        ]

        if filters.get('semester_id') and str(filters['semester_id']) != '0':
            sql += " AND DC.fk_semesterid = ?"
            params.append(filters['semester_id'])

        sql += " GROUP BY S.pk_sid, S.enrollmentno, S.AdmissionNo, S.fullname, SCA.fk_exconfigid ORDER BY S.fullname"
        return DB.fetch_all(sql, params)

class FeeApprovalModel:
    @staticmethod
    def _resolve_staffwise_columns():
        cols = MiscAcademicsModel._table_columns('SMS_StuCourseAllocation_Approval_staffwise')
        status_col = next(
            (
                c for c in (
                    'fee_aprrovalstatus', 'fee_approvalstatus', 'fee_approval_status',
                    'feeemp_aprrovalstatus', 'feeemp_approvalstatus', 'feeemp_approval_status',
                    'fee_emp_aprrovalstatus', 'fee_emp_approvalstatus', 'fee_emp_approval_status',
                    'feestatus', 'fee_status'
                )
                if c in cols
            ),
            None
        )
        remarks_col = next(
            (
                c for c in (
                    'remarks_by_fee', 'remarks_by_feeemp', 'remarks_by_fee_employee',
                    'fee_remarks', 'feeemp_remarks', 'remarks_fee'
                )
                if c in cols
            ),
            None
        )
        fee_id_col = next(
            (
                c for c in (
                    'fk_feeid', 'fk_feeempid', 'fk_fee_empid', 'fk_feeemployeeid',
                    'feeid', 'feeempid'
                )
                if c in cols
            ),
            None
        )
        lib_status_col = next(
            (
                c for c in (
                    'lib_aprrovalstatus', 'lib_approvalstatus', 'library_aprrovalstatus', 'library_approvalstatus',
                    'librarian_aprrovalstatus', 'librarian_approvalstatus', 'libstatus', 'librarystatus'
                )
                if c in cols
            ),
            None
        )
        return cols, status_col, remarks_col, fee_id_col, lib_status_col

    @staticmethod
    def _approved_expr(col_name):
        return f"""(
            TRY_CONVERT(INT, {col_name}) > 0
            OR UPPER(CONVERT(VARCHAR(20), {col_name})) IN ('A','Y','YES','APPROVED')
        )"""

    @staticmethod
    def get_students_for_approval(filters, fee_emp_id):
        cols, status_col, remarks_col, _fee_id_col, lib_status_col = FeeApprovalModel._resolve_staffwise_columns()
        if not status_col:
            return []

        remarks_select_sql = f"MAX(CONVERT(VARCHAR(2000), APP.{remarks_col}))" if remarks_col else "NULL"

        approved_case = f"""
            CASE
                WHEN COUNT(APP.fk_courseid) = 0 THEN CAST(0 AS BIT)
                WHEN SUM(CASE WHEN {FeeApprovalModel._approved_expr('APP.' + status_col)} THEN 0 ELSE 1 END) = 0 THEN CAST(1 AS BIT)
                ELSE CAST(0 AS BIT)
            END
        """

        sql = f"""
            SELECT
                S.pk_sid,
                COALESCE(NULLIF(LTRIM(RTRIM(S.enrollmentno)), ''), NULLIF(LTRIM(RTRIM(S.AdmissionNo)), '')) AS AdmissionNo,
                S.fullname,
                {approved_case} AS approved,
                {remarks_select_sql} AS remarks
            FROM SMS_Student_Mst S
            INNER JOIN SMS_StuCourseAllocation SCA ON S.pk_sid = SCA.fk_sturegid
            LEFT JOIN SMS_StuCourseAllocation_Approval_staffwise APP
              ON SCA.fk_sturegid = APP.fk_sturegid
             AND SCA.fk_courseid = APP.fk_courseid
             AND SCA.fk_exconfigid = APP.fk_exconfigid
            LEFT JOIN SMS_DegreeCycle_Mst DC ON SCA.fk_degreecycleid = DC.pk_degreecycleid
            WHERE S.fk_collegeid = ? AND SCA.fk_dgacasessionid = ? AND S.fk_degreeid = ?
              AND SCA.fk_exconfigid = ?
        """
        params = [
            filters.get('college_id'),
            filters.get('session_id'),
            filters.get('degree_id'),
            filters.get('exconfig_id'),
        ]

        if filters.get('semester_id') and str(filters['semester_id']) != '0':
            sql += " AND DC.fk_semesterid = ?"
            params.append(filters['semester_id'])

        if filters.get('branch_id') and str(filters['branch_id']) != '0':
            sql += " AND S.fk_branchid = ?"
            params.append(filters['branch_id'])

        # Fee stage typically comes after Library. If Library status column exists, show only where all course rows are Library-approved.
        if lib_status_col:
            sql += f"""
              AND NOT EXISTS (
                    SELECT 1
                    FROM SMS_StuCourseAllocation A2
                    LEFT JOIN SMS_StuCourseAllocation_Approval_staffwise APP2
                      ON A2.fk_sturegid = APP2.fk_sturegid
                     AND A2.fk_courseid = APP2.fk_courseid
                     AND A2.fk_exconfigid = APP2.fk_exconfigid
                    WHERE A2.fk_sturegid = S.pk_sid AND A2.fk_exconfigid = ?
                      AND (APP2.{lib_status_col} IS NULL OR NOT ({FeeApprovalModel._approved_expr('APP2.' + lib_status_col)}))
              )
            """
            params.append(filters.get('exconfig_id'))

        sql += " GROUP BY S.pk_sid, S.enrollmentno, S.AdmissionNo, S.fullname ORDER BY S.fullname"
        students = DB.fetch_all(sql, params)

        for stu in students:
            courses = DB.fetch_all(
                """
                SELECT
                    C.pk_courseid as course_id,
                    C.coursename,
                    C.coursecode,
                    SES.sessionname,
                    A.crhrth,
                    A.crhrpr
                FROM SMS_StuCourseAllocation A
                INNER JOIN SMS_Course_Mst C ON A.fk_courseid = C.pk_courseid
                INNER JOIN SMS_AcademicSession_Mst SES ON A.fk_dgacasessionid = SES.pk_sessionid
                LEFT JOIN SMS_DegreeCycle_Mst DC ON A.fk_degreecycleid = DC.pk_degreecycleid
                WHERE A.fk_sturegid = ? AND A.fk_exconfigid = ?
                  AND (? IS NULL OR DC.fk_semesterid = ?)
                ORDER BY C.coursename
                """,
                [stu['pk_sid'], filters.get('exconfig_id'), filters.get('semester_id') or None, filters.get('semester_id') or None],
            )
            stu['courses'] = [
                {
                    'label': f"{c.get('coursename','')} / {c.get('coursecode','')} [{(c.get('sessionname') or '').strip()} ]({c.get('crhrth',0)}+{c.get('crhrpr',0)})",
                }
                for c in courses
            ]

        return students

    @staticmethod
    def save_approvals(data, fee_emp_id, user_id):
        cols, status_col, remarks_col, fee_id_col, _lib_status_col = FeeApprovalModel._resolve_staffwise_columns()
        if not status_col:
            return False

        action = data.get('action')
        student_ids = data.getlist('student_ids')
        approved_ids = set(data.getlist('approved_ids'))
        remarks = data.getlist('remarks')
        exconfig_id = data.get('exconfig_id')

        def _safe_col(name):
            import re
            if not name:
                return None
            if not re.match(r'^[A-Za-z0-9_]+$', name):
                return None
            if name.lower() not in cols:
                return None
            return name

        status_col = _safe_col(status_col)
        remarks_col = _safe_col(remarks_col) if remarks_col else None
        fee_id_col = _safe_col(fee_id_col) if fee_id_col else None
        if not status_col:
            return False

        for i, sid in enumerate(student_ids):
            is_approved = 0 if action == 'Hold' else (1 if sid in approved_ids else 0)
            rem = (remarks[i] if i < len(remarks) else '') if remarks_col else None

            allocations = DB.fetch_all(
                "SELECT * FROM SMS_StuCourseAllocation WHERE fk_sturegid = ? AND fk_exconfigid = ?",
                [sid, exconfig_id]
            )

            for alloc in allocations:
                exists = DB.fetch_one(
                    "SELECT Pk_stucoursealloc_staffid FROM SMS_StuCourseAllocation_Approval_staffwise WHERE fk_sturegid = ? AND fk_courseid = ? AND fk_exconfigid = ?",
                    [sid, alloc['fk_courseid'], exconfig_id]
                )

                if exists:
                    sets = [
                        f"{status_col} = ?",
                        "Lastupdatedby = ?",
                        "lastupdated = GETDATE()",
                    ]
                    params = [is_approved, user_id]
                    if remarks_col:
                        sets.insert(1, f"{remarks_col} = ?")
                        params.insert(1, rem)
                    if fee_id_col:
                        sets.insert(1, f"{fee_id_col} = ?")
                        params.insert(1, fee_emp_id)

                    sql = f"""
                        UPDATE SMS_StuCourseAllocation_Approval_staffwise
                        SET {', '.join(sets)}
                        WHERE Pk_stucoursealloc_staffid = ?
                    """
                    DB.execute(sql, params + [exists['Pk_stucoursealloc_staffid']])
                else:
                    insert_cols = [
                        "fk_sturegid", "fk_courseid", "fk_degreecycleid_alloc", "fk_degreecycleid",
                        "fk_dgacasessionid_alloc", "fk_dgacasessionid", "fk_exconfigid",
                        "Lastupdatedby", "lastupdated", "fk_stucourseallocid",
                        status_col,
                    ]
                    insert_vals = [
                        sid, alloc['fk_courseid'], alloc.get('fk_degreecycleid_alloc'), alloc.get('fk_degreecycleid'),
                        alloc.get('fk_dgacasessionid_alloc'), alloc.get('fk_dgacasessionid'), exconfig_id,
                        user_id, None, alloc.get('Pk_stucourseallocid'),
                        is_approved,
                    ]
                    if remarks_col:
                        insert_cols.append(remarks_col)
                        insert_vals.append(rem)
                    if fee_id_col:
                        insert_cols.append(fee_id_col)
                        insert_vals.append(fee_emp_id)

                    lastupdated_idx = insert_cols.index("lastupdated")
                    cols_sql = ", ".join(insert_cols)
                    placeholders_list = ["?"] * len(insert_cols)
                    placeholders_list[lastupdated_idx] = "GETDATE()"
                    placeholders_sql = ", ".join(placeholders_list)
                    sql = f"INSERT INTO SMS_StuCourseAllocation_Approval_staffwise ({cols_sql}) VALUES ({placeholders_sql})"
                    insert_vals.pop(lastupdated_idx)
                    DB.execute(sql, insert_vals)

        return True

    @staticmethod
    def get_pending_students(filters, fee_emp_id):
        cols, status_col, _remarks_col, _fee_id_col, lib_status_col = FeeApprovalModel._resolve_staffwise_columns()
        if not status_col:
            return []

        sql = f"""
            SELECT
                S.pk_sid,
                COALESCE(NULLIF(LTRIM(RTRIM(S.enrollmentno)), ''), NULLIF(LTRIM(RTRIM(S.AdmissionNo)), '')) AS AdmissionNo,
                S.fullname
            FROM SMS_Student_Mst S
            INNER JOIN SMS_StuCourseAllocation SCA ON S.pk_sid = SCA.fk_sturegid
            LEFT JOIN SMS_StuCourseAllocation_Approval_staffwise APP
              ON SCA.fk_sturegid = APP.fk_sturegid
             AND SCA.fk_courseid = APP.fk_courseid
             AND SCA.fk_exconfigid = APP.fk_exconfigid
            LEFT JOIN SMS_DegreeCycle_Mst DC ON SCA.fk_degreecycleid = DC.pk_degreecycleid
            WHERE S.fk_collegeid = ? AND SCA.fk_dgacasessionid = ? AND S.fk_degreeid = ?
              AND SCA.fk_exconfigid = ?
        """
        params = [
            filters.get('college_id'),
            filters.get('session_id'),
            filters.get('degree_id'),
            filters.get('exconfig_id'),
        ]

        if filters.get('semester_id') and str(filters['semester_id']) != '0':
            sql += " AND DC.fk_semesterid = ?"
            params.append(filters['semester_id'])

        if filters.get('branch_id') and str(filters['branch_id']) != '0':
            sql += " AND S.fk_branchid = ?"
            params.append(filters['branch_id'])

        if lib_status_col:
            sql += f"""
              AND NOT EXISTS (
                    SELECT 1
                    FROM SMS_StuCourseAllocation A2
                    LEFT JOIN SMS_StuCourseAllocation_Approval_staffwise APP2
                      ON A2.fk_sturegid = APP2.fk_sturegid
                     AND A2.fk_courseid = APP2.fk_courseid
                     AND A2.fk_exconfigid = APP2.fk_exconfigid
                    WHERE A2.fk_sturegid = S.pk_sid AND A2.fk_exconfigid = ?
                      AND (APP2.{lib_status_col} IS NULL OR NOT ({FeeApprovalModel._approved_expr('APP2.' + lib_status_col)}))
              )
            """
            params.append(filters.get('exconfig_id'))

        # Pending/Rejected at Fee stage => any course row not approved.
        sql += f"""
            GROUP BY S.pk_sid, S.enrollmentno, S.AdmissionNo, S.fullname
            HAVING SUM(CASE WHEN {FeeApprovalModel._approved_expr('APP.' + status_col)} THEN 0 ELSE 1 END) > 0
            ORDER BY S.fullname
        """
        return DB.fetch_all(sql, params)

class DeanApprovalModel:
    @staticmethod
    def _resolve_staffwise_columns():
        cols = MiscAcademicsModel._table_columns('SMS_StuCourseAllocation_Approval_staffwise')
        status_col = next(
            (
                c for c in (
                    'dean_aprrovalstatus', 'dean_approvalstatus', 'dean_approval_status',
                    'deanapprovalstatus', 'deanstatus', 'dean_status'
                )
                if c in cols
            ),
            None
        )
        remarks_col = next(
            (
                c for c in (
                    'remarks_by_dean', 'dean_remarks', 'remarks_dean'
                )
                if c in cols
            ),
            None
        )
        dean_id_col = next(
            (
                c for c in (
                    'fk_deanid', 'fk_dean_id', 'deanid'
                )
                if c in cols
            ),
            None
        )
        fee_status_col = next(
            (
                c for c in (
                    'fee_aprrovalstatus', 'fee_approvalstatus', 'fee_approval_status',
                    'feeemp_aprrovalstatus', 'feeemp_approvalstatus', 'feeemp_approval_status',
                    'fee_emp_aprrovalstatus', 'fee_emp_approvalstatus', 'fee_emp_approval_status',
                    'feestatus', 'fee_status'
                )
                if c in cols
            ),
            None
        )
        return cols, status_col, remarks_col, dean_id_col, fee_status_col

    @staticmethod
    def _approved_expr(col_name):
        return f"""(
            TRY_CONVERT(INT, {col_name}) > 0
            OR UPPER(CONVERT(VARCHAR(20), {col_name})) IN ('A','Y','YES','APPROVED')
        )"""

    @staticmethod
    def get_students_for_approval(filters, dean_emp_id):
        cols, status_col, remarks_col, _dean_id_col, fee_status_col = DeanApprovalModel._resolve_staffwise_columns()
        if not status_col:
            return []

        remarks_select_sql = f"MAX(CONVERT(VARCHAR(2000), APP.{remarks_col}))" if remarks_col else "NULL"

        approved_case = f"""
            CASE
                WHEN COUNT(APP.fk_courseid) = 0 THEN CAST(0 AS BIT)
                WHEN SUM(CASE WHEN {DeanApprovalModel._approved_expr('APP.' + status_col)} THEN 0 ELSE 1 END) = 0 THEN CAST(1 AS BIT)
                ELSE CAST(0 AS BIT)
            END
        """

        sql = f"""
            SELECT
                S.pk_sid,
                COALESCE(NULLIF(LTRIM(RTRIM(S.enrollmentno)), ''), NULLIF(LTRIM(RTRIM(S.AdmissionNo)), '')) AS AdmissionNo,
                S.fullname,
                {approved_case} AS approved,
                {remarks_select_sql} AS remarks
            FROM SMS_Student_Mst S
            INNER JOIN SMS_StuCourseAllocation SCA ON S.pk_sid = SCA.fk_sturegid
            LEFT JOIN SMS_StuCourseAllocation_Approval_staffwise APP
              ON SCA.fk_sturegid = APP.fk_sturegid
             AND SCA.fk_courseid = APP.fk_courseid
             AND SCA.fk_exconfigid = APP.fk_exconfigid
            LEFT JOIN SMS_DegreeCycle_Mst DC ON SCA.fk_degreecycleid = DC.pk_degreecycleid
            WHERE S.fk_collegeid = ? AND SCA.fk_dgacasessionid = ? AND S.fk_degreeid = ?
              AND SCA.fk_exconfigid = ?
        """
        params = [
            filters.get('college_id'),
            filters.get('session_id'),
            filters.get('degree_id'),
            filters.get('exconfig_id'),
        ]

        if filters.get('semester_id') and str(filters['semester_id']) != '0':
            sql += " AND DC.fk_semesterid = ?"
            params.append(filters['semester_id'])

        if filters.get('branch_id') and str(filters['branch_id']) != '0':
            sql += " AND S.fk_branchid = ?"
            params.append(filters['branch_id'])

        # Dean stage typically comes after Fee. If Fee status column exists, show only where all course rows are Fee-approved.
        if fee_status_col:
            sql += f"""
              AND NOT EXISTS (
                    SELECT 1
                    FROM SMS_StuCourseAllocation A2
                    LEFT JOIN SMS_StuCourseAllocation_Approval_staffwise APP2
                      ON A2.fk_sturegid = APP2.fk_sturegid
                     AND A2.fk_courseid = APP2.fk_courseid
                     AND A2.fk_exconfigid = APP2.fk_exconfigid
                    WHERE A2.fk_sturegid = S.pk_sid AND A2.fk_exconfigid = ?
                      AND (APP2.{fee_status_col} IS NULL OR NOT ({DeanApprovalModel._approved_expr('APP2.' + fee_status_col)}))
              )
            """
            params.append(filters.get('exconfig_id'))

        sql += " GROUP BY S.pk_sid, S.enrollmentno, S.AdmissionNo, S.fullname ORDER BY S.fullname"
        students = DB.fetch_all(sql, params)

        for stu in students:
            courses = DB.fetch_all(
                """
                SELECT
                    C.pk_courseid as course_id,
                    C.coursename,
                    C.coursecode,
                    SES.sessionname,
                    A.crhrth,
                    A.crhrpr
                FROM SMS_StuCourseAllocation A
                INNER JOIN SMS_Course_Mst C ON A.fk_courseid = C.pk_courseid
                INNER JOIN SMS_AcademicSession_Mst SES ON A.fk_dgacasessionid = SES.pk_sessionid
                LEFT JOIN SMS_DegreeCycle_Mst DC ON A.fk_degreecycleid = DC.pk_degreecycleid
                WHERE A.fk_sturegid = ? AND A.fk_exconfigid = ?
                  AND (? IS NULL OR DC.fk_semesterid = ?)
                ORDER BY C.coursename
                """,
                [stu['pk_sid'], filters.get('exconfig_id'), filters.get('semester_id') or None, filters.get('semester_id') or None],
            )
            stu['courses'] = [
                {
                    'label': f"{c.get('coursename','')} / {c.get('coursecode','')} [{(c.get('sessionname') or '').strip()} ]({c.get('crhrth',0)}+{c.get('crhrpr',0)})",
                }
                for c in courses
            ]

        return students

    @staticmethod
    def save_approvals(data, dean_emp_id, user_id):
        cols, status_col, remarks_col, dean_id_col, _fee_status_col = DeanApprovalModel._resolve_staffwise_columns()
        if not status_col:
            return False

        action = data.get('action')
        student_ids = data.getlist('student_ids')
        approved_ids = set(data.getlist('approved_ids'))
        remarks = data.getlist('remarks')
        exconfig_id = data.get('exconfig_id')

        def _safe_col(name):
            import re
            if not name:
                return None
            if not re.match(r'^[A-Za-z0-9_]+$', name):
                return None
            if name.lower() not in cols:
                return None
            return name

        status_col = _safe_col(status_col)
        remarks_col = _safe_col(remarks_col) if remarks_col else None
        dean_id_col = _safe_col(dean_id_col) if dean_id_col else None
        if not status_col:
            return False

        for i, sid in enumerate(student_ids):
            is_approved = 0 if action == 'Hold' else (1 if sid in approved_ids else 0)
            rem = (remarks[i] if i < len(remarks) else '') if remarks_col else None

            allocations = DB.fetch_all(
                "SELECT * FROM SMS_StuCourseAllocation WHERE fk_sturegid = ? AND fk_exconfigid = ?",
                [sid, exconfig_id]
            )

            for alloc in allocations:
                exists = DB.fetch_one(
                    "SELECT Pk_stucoursealloc_staffid FROM SMS_StuCourseAllocation_Approval_staffwise WHERE fk_sturegid = ? AND fk_courseid = ? AND fk_exconfigid = ?",
                    [sid, alloc['fk_courseid'], exconfig_id]
                )

                if exists:
                    sets = [
                        f"{status_col} = ?",
                        "Lastupdatedby = ?",
                        "lastupdated = GETDATE()",
                    ]
                    params = [is_approved, user_id]
                    if remarks_col:
                        sets.insert(1, f"{remarks_col} = ?")
                        params.insert(1, rem)
                    if dean_id_col:
                        sets.insert(1, f"{dean_id_col} = ?")
                        params.insert(1, dean_emp_id)

                    sql = f"""
                        UPDATE SMS_StuCourseAllocation_Approval_staffwise
                        SET {', '.join(sets)}
                        WHERE Pk_stucoursealloc_staffid = ?
                    """
                    DB.execute(sql, params + [exists['Pk_stucoursealloc_staffid']])
                else:
                    insert_cols = [
                        "fk_sturegid", "fk_courseid", "fk_degreecycleid_alloc", "fk_degreecycleid",
                        "fk_dgacasessionid_alloc", "fk_dgacasessionid", "fk_exconfigid",
                        "Lastupdatedby", "lastupdated", "fk_stucourseallocid",
                        status_col,
                    ]
                    insert_vals = [
                        sid, alloc['fk_courseid'], alloc.get('fk_degreecycleid_alloc'), alloc.get('fk_degreecycleid'),
                        alloc.get('fk_dgacasessionid_alloc'), alloc.get('fk_dgacasessionid'), exconfig_id,
                        user_id, None, alloc.get('Pk_stucourseallocid'),
                        is_approved,
                    ]
                    if remarks_col:
                        insert_cols.append(remarks_col)
                        insert_vals.append(rem)
                    if dean_id_col:
                        insert_cols.append(dean_id_col)
                        insert_vals.append(dean_emp_id)

                    lastupdated_idx = insert_cols.index("lastupdated")
                    cols_sql = ", ".join(insert_cols)
                    placeholders_list = ["?"] * len(insert_cols)
                    placeholders_list[lastupdated_idx] = "GETDATE()"
                    placeholders_sql = ", ".join(placeholders_list)
                    sql = f"INSERT INTO SMS_StuCourseAllocation_Approval_staffwise ({cols_sql}) VALUES ({placeholders_sql})"
                    insert_vals.pop(lastupdated_idx)
                    DB.execute(sql, insert_vals)

        return True

    @staticmethod
    def get_pending_students(filters, dean_emp_id):
        cols, status_col, _remarks_col, _dean_id_col, fee_status_col = DeanApprovalModel._resolve_staffwise_columns()
        if not status_col:
            return []

        sql = f"""
            SELECT
                S.pk_sid,
                COALESCE(NULLIF(LTRIM(RTRIM(S.enrollmentno)), ''), NULLIF(LTRIM(RTRIM(S.AdmissionNo)), '')) AS AdmissionNo,
                S.fullname
            FROM SMS_Student_Mst S
            INNER JOIN SMS_StuCourseAllocation SCA ON S.pk_sid = SCA.fk_sturegid
            LEFT JOIN SMS_StuCourseAllocation_Approval_staffwise APP
              ON SCA.fk_sturegid = APP.fk_sturegid
             AND SCA.fk_courseid = APP.fk_courseid
             AND SCA.fk_exconfigid = APP.fk_exconfigid
            LEFT JOIN SMS_DegreeCycle_Mst DC ON SCA.fk_degreecycleid = DC.pk_degreecycleid
            WHERE S.fk_collegeid = ? AND SCA.fk_dgacasessionid = ? AND S.fk_degreeid = ?
              AND SCA.fk_exconfigid = ?
        """
        params = [
            filters.get('college_id'),
            filters.get('session_id'),
            filters.get('degree_id'),
            filters.get('exconfig_id'),
        ]

        if filters.get('semester_id') and str(filters['semester_id']) != '0':
            sql += " AND DC.fk_semesterid = ?"
            params.append(filters['semester_id'])

        if filters.get('branch_id') and str(filters['branch_id']) != '0':
            sql += " AND S.fk_branchid = ?"
            params.append(filters['branch_id'])

        if fee_status_col:
            sql += f"""
              AND NOT EXISTS (
                    SELECT 1
                    FROM SMS_StuCourseAllocation A2
                    LEFT JOIN SMS_StuCourseAllocation_Approval_staffwise APP2
                      ON A2.fk_sturegid = APP2.fk_sturegid
                     AND A2.fk_courseid = APP2.fk_courseid
                     AND A2.fk_exconfigid = APP2.fk_exconfigid
                    WHERE A2.fk_sturegid = S.pk_sid AND A2.fk_exconfigid = ?
                      AND (APP2.{fee_status_col} IS NULL OR NOT ({DeanApprovalModel._approved_expr('APP2.' + fee_status_col)}))
              )
            """
            params.append(filters.get('exconfig_id'))

        # Pending/Rejected at Dean stage => any course row not approved.
        sql += f"""
            GROUP BY S.pk_sid, S.enrollmentno, S.AdmissionNo, S.fullname
            HAVING SUM(CASE WHEN {DeanApprovalModel._approved_expr('APP.' + status_col)} THEN 0 ELSE 1 END) > 0
            ORDER BY S.fullname
        """
        return DB.fetch_all(sql, params)

class DeanPgsApprovalModel:
    @staticmethod
    def _resolve_staffwise_columns():
        cols = MiscAcademicsModel._table_columns('SMS_StuCourseAllocation_Approval_staffwise')
        status_col = next(
            (
                c for c in (
                    'deanpgs_aprrovalstatus', 'deanpgs_approvalstatus', 'deanpgs_approval_status',
                    'dean_pgs_aprrovalstatus', 'dean_pgs_approvalstatus', 'dean_pgs_approval_status',
                    'pgsdean_aprrovalstatus', 'pgsdean_approvalstatus',
                    'deanpgsstatus', 'deanpgs_status'
                )
                if c in cols
            ),
            None
        )
        remarks_col = next(
            (
                c for c in (
                    'remarks_by_deanpgs', 'remarks_by_dean_pgs', 'deanpgs_remarks', 'dean_pgs_remarks', 'remarks_deanpgs'
                )
                if c in cols
            ),
            None
        )
        deanpgs_id_col = next(
            (
                c for c in (
                    'fk_deanpgsid', 'fk_deanpgs_id', 'deanpgsid', 'fk_dean_pgsid', 'fk_dean_pgs_id'
                )
                if c in cols
            ),
            None
        )

        # DeanPGS stage usually comes after Dean. If Dean status exists, enforce it. Otherwise fall back to Fee if present.
        dean_status_col = next(
            (
                c for c in (
                    'dean_aprrovalstatus', 'dean_approvalstatus', 'dean_approval_status',
                    'deanapprovalstatus', 'deanstatus', 'dean_status'
                )
                if c in cols
            ),
            None
        )
        fee_status_col = next(
            (
                c for c in (
                    'fee_aprrovalstatus', 'fee_approvalstatus', 'fee_approval_status',
                    'feeemp_aprrovalstatus', 'feeemp_approvalstatus', 'feeemp_approval_status',
                    'fee_emp_aprrovalstatus', 'fee_emp_approvalstatus', 'fee_emp_approval_status',
                    'feestatus', 'fee_status'
                )
                if c in cols
            ),
            None
        )
        return cols, status_col, remarks_col, deanpgs_id_col, dean_status_col, fee_status_col

    @staticmethod
    def _approved_expr(col_name):
        return f"""(
            TRY_CONVERT(INT, {col_name}) > 0
            OR UPPER(CONVERT(VARCHAR(20), {col_name})) IN ('A','Y','YES','APPROVED')
        )"""

    @staticmethod
    def get_students_for_approval(filters, deanpgs_emp_id):
        cols, status_col, remarks_col, _deanpgs_id_col, dean_status_col, fee_status_col = DeanPgsApprovalModel._resolve_staffwise_columns()
        if not status_col:
            return []

        remarks_select_sql = f"MAX(CONVERT(VARCHAR(2000), APP.{remarks_col}))" if remarks_col else "NULL"

        approved_case = f"""
            CASE
                WHEN COUNT(APP.fk_courseid) = 0 THEN CAST(0 AS BIT)
                WHEN SUM(CASE WHEN {DeanPgsApprovalModel._approved_expr('APP.' + status_col)} THEN 0 ELSE 1 END) = 0 THEN CAST(1 AS BIT)
                ELSE CAST(0 AS BIT)
            END
        """

        sql = f"""
            SELECT
                S.pk_sid,
                COALESCE(NULLIF(LTRIM(RTRIM(S.enrollmentno)), ''), NULLIF(LTRIM(RTRIM(S.AdmissionNo)), '')) AS AdmissionNo,
                S.fullname,
                {approved_case} AS approved,
                {remarks_select_sql} AS remarks
            FROM SMS_Student_Mst S
            INNER JOIN SMS_StuCourseAllocation SCA ON S.pk_sid = SCA.fk_sturegid
            LEFT JOIN SMS_StuCourseAllocation_Approval_staffwise APP
              ON SCA.fk_sturegid = APP.fk_sturegid
             AND SCA.fk_courseid = APP.fk_courseid
             AND SCA.fk_exconfigid = APP.fk_exconfigid
            LEFT JOIN SMS_DegreeCycle_Mst DC ON SCA.fk_degreecycleid = DC.pk_degreecycleid
            WHERE S.fk_collegeid = ? AND SCA.fk_dgacasessionid = ? AND S.fk_degreeid = ?
              AND SCA.fk_exconfigid = ?
        """
        params = [
            filters.get('college_id'),
            filters.get('session_id'),
            filters.get('degree_id'),
            filters.get('exconfig_id'),
        ]

        if filters.get('semester_id') and str(filters['semester_id']) != '0':
            sql += " AND DC.fk_semesterid = ?"
            params.append(filters['semester_id'])

        if filters.get('branch_id') and str(filters['branch_id']) != '0':
            sql += " AND S.fk_branchid = ?"
            params.append(filters['branch_id'])

        gate_col = dean_status_col or fee_status_col
        if gate_col:
            sql += f"""
              AND NOT EXISTS (
                    SELECT 1
                    FROM SMS_StuCourseAllocation A2
                    LEFT JOIN SMS_StuCourseAllocation_Approval_staffwise APP2
                      ON A2.fk_sturegid = APP2.fk_sturegid
                     AND A2.fk_courseid = APP2.fk_courseid
                     AND A2.fk_exconfigid = APP2.fk_exconfigid
                    WHERE A2.fk_sturegid = S.pk_sid AND A2.fk_exconfigid = ?
                      AND (APP2.{gate_col} IS NULL OR NOT ({DeanPgsApprovalModel._approved_expr('APP2.' + gate_col)}))
              )
            """
            params.append(filters.get('exconfig_id'))

        sql += " GROUP BY S.pk_sid, S.enrollmentno, S.AdmissionNo, S.fullname ORDER BY S.fullname"
        students = DB.fetch_all(sql, params)

        for stu in students:
            courses = DB.fetch_all(
                """
                SELECT
                    C.pk_courseid as course_id,
                    C.coursename,
                    C.coursecode,
                    SES.sessionname,
                    A.crhrth,
                    A.crhrpr
                FROM SMS_StuCourseAllocation A
                INNER JOIN SMS_Course_Mst C ON A.fk_courseid = C.pk_courseid
                INNER JOIN SMS_AcademicSession_Mst SES ON A.fk_dgacasessionid = SES.pk_sessionid
                LEFT JOIN SMS_DegreeCycle_Mst DC ON A.fk_degreecycleid = DC.pk_degreecycleid
                WHERE A.fk_sturegid = ? AND A.fk_exconfigid = ?
                  AND (? IS NULL OR DC.fk_semesterid = ?)
                ORDER BY C.coursename
                """,
                [stu['pk_sid'], filters.get('exconfig_id'), filters.get('semester_id') or None, filters.get('semester_id') or None],
            )
            stu['courses'] = [
                {
                    'label': f"{c.get('coursename','')} / {c.get('coursecode','')} [{(c.get('sessionname') or '').strip()} ]({c.get('crhrth',0)}+{c.get('crhrpr',0)})",
                }
                for c in courses
            ]

        return students

    @staticmethod
    def save_approvals(data, deanpgs_emp_id, user_id):
        cols, status_col, remarks_col, deanpgs_id_col, _dean_status_col, _fee_status_col = DeanPgsApprovalModel._resolve_staffwise_columns()
        if not status_col:
            return False

        action = data.get('action')
        student_ids = data.getlist('student_ids')
        approved_ids = set(data.getlist('approved_ids'))
        remarks = data.getlist('remarks')
        exconfig_id = data.get('exconfig_id')

        def _safe_col(name):
            import re
            if not name:
                return None
            if not re.match(r'^[A-Za-z0-9_]+$', name):
                return None
            if name.lower() not in cols:
                return None
            return name

        status_col = _safe_col(status_col)
        remarks_col = _safe_col(remarks_col) if remarks_col else None
        deanpgs_id_col = _safe_col(deanpgs_id_col) if deanpgs_id_col else None
        if not status_col:
            return False

        for i, sid in enumerate(student_ids):
            is_approved = 0 if action == 'Hold' else (1 if sid in approved_ids else 0)
            rem = (remarks[i] if i < len(remarks) else '') if remarks_col else None

            allocations = DB.fetch_all(
                "SELECT * FROM SMS_StuCourseAllocation WHERE fk_sturegid = ? AND fk_exconfigid = ?",
                [sid, exconfig_id]
            )

            for alloc in allocations:
                exists = DB.fetch_one(
                    "SELECT Pk_stucoursealloc_staffid FROM SMS_StuCourseAllocation_Approval_staffwise WHERE fk_sturegid = ? AND fk_courseid = ? AND fk_exconfigid = ?",
                    [sid, alloc['fk_courseid'], exconfig_id]
                )

                if exists:
                    sets = [
                        f"{status_col} = ?",
                        "Lastupdatedby = ?",
                        "lastupdated = GETDATE()",
                    ]
                    params = [is_approved, user_id]
                    if remarks_col:
                        sets.insert(1, f"{remarks_col} = ?")
                        params.insert(1, rem)
                    if deanpgs_id_col:
                        sets.insert(1, f"{deanpgs_id_col} = ?")
                        params.insert(1, deanpgs_emp_id)

                    sql = f"""
                        UPDATE SMS_StuCourseAllocation_Approval_staffwise
                        SET {', '.join(sets)}
                        WHERE Pk_stucoursealloc_staffid = ?
                    """
                    DB.execute(sql, params + [exists['Pk_stucoursealloc_staffid']])
                else:
                    insert_cols = [
                        "fk_sturegid", "fk_courseid", "fk_degreecycleid_alloc", "fk_degreecycleid",
                        "fk_dgacasessionid_alloc", "fk_dgacasessionid", "fk_exconfigid",
                        "Lastupdatedby", "lastupdated", "fk_stucourseallocid",
                        status_col,
                    ]
                    insert_vals = [
                        sid, alloc['fk_courseid'], alloc.get('fk_degreecycleid_alloc'), alloc.get('fk_degreecycleid'),
                        alloc.get('fk_dgacasessionid_alloc'), alloc.get('fk_dgacasessionid'), exconfig_id,
                        user_id, None, alloc.get('Pk_stucourseallocid'),
                        is_approved,
                    ]
                    if remarks_col:
                        insert_cols.append(remarks_col)
                        insert_vals.append(rem)
                    if deanpgs_id_col:
                        insert_cols.append(deanpgs_id_col)
                        insert_vals.append(deanpgs_emp_id)

                    lastupdated_idx = insert_cols.index("lastupdated")
                    cols_sql = ", ".join(insert_cols)
                    placeholders_list = ["?"] * len(insert_cols)
                    placeholders_list[lastupdated_idx] = "GETDATE()"
                    placeholders_sql = ", ".join(placeholders_list)
                    sql = f"INSERT INTO SMS_StuCourseAllocation_Approval_staffwise ({cols_sql}) VALUES ({placeholders_sql})"
                    insert_vals.pop(lastupdated_idx)
                    DB.execute(sql, insert_vals)

        return True

    @staticmethod
    def get_pending_students(filters, deanpgs_emp_id):
        cols, status_col, _remarks_col, _deanpgs_id_col, dean_status_col, fee_status_col = DeanPgsApprovalModel._resolve_staffwise_columns()
        if not status_col:
            return []

        sql = f"""
            SELECT
                S.pk_sid,
                COALESCE(NULLIF(LTRIM(RTRIM(S.enrollmentno)), ''), NULLIF(LTRIM(RTRIM(S.AdmissionNo)), '')) AS AdmissionNo,
                S.fullname
            FROM SMS_Student_Mst S
            INNER JOIN SMS_StuCourseAllocation SCA ON S.pk_sid = SCA.fk_sturegid
            LEFT JOIN SMS_StuCourseAllocation_Approval_staffwise APP
              ON SCA.fk_sturegid = APP.fk_sturegid
             AND SCA.fk_courseid = APP.fk_courseid
             AND SCA.fk_exconfigid = APP.fk_exconfigid
            LEFT JOIN SMS_DegreeCycle_Mst DC ON SCA.fk_degreecycleid = DC.pk_degreecycleid
            WHERE S.fk_collegeid = ? AND SCA.fk_dgacasessionid = ? AND S.fk_degreeid = ?
              AND SCA.fk_exconfigid = ?
        """
        params = [
            filters.get('college_id'),
            filters.get('session_id'),
            filters.get('degree_id'),
            filters.get('exconfig_id'),
        ]

        if filters.get('semester_id') and str(filters['semester_id']) != '0':
            sql += " AND DC.fk_semesterid = ?"
            params.append(filters['semester_id'])

        if filters.get('branch_id') and str(filters['branch_id']) != '0':
            sql += " AND S.fk_branchid = ?"
            params.append(filters['branch_id'])

        gate_col = dean_status_col or fee_status_col
        if gate_col:
            sql += f"""
              AND NOT EXISTS (
                    SELECT 1
                    FROM SMS_StuCourseAllocation A2
                    LEFT JOIN SMS_StuCourseAllocation_Approval_staffwise APP2
                      ON A2.fk_sturegid = APP2.fk_sturegid
                     AND A2.fk_courseid = APP2.fk_courseid
                     AND A2.fk_exconfigid = APP2.fk_exconfigid
                    WHERE A2.fk_sturegid = S.pk_sid AND A2.fk_exconfigid = ?
                      AND (APP2.{gate_col} IS NULL OR NOT ({DeanPgsApprovalModel._approved_expr('APP2.' + gate_col)}))
              )
            """
            params.append(filters.get('exconfig_id'))

        sql += f"""
            GROUP BY S.pk_sid, S.enrollmentno, S.AdmissionNo, S.fullname
            HAVING SUM(CASE WHEN {DeanPgsApprovalModel._approved_expr('APP.' + status_col)} THEN 0 ELSE 1 END) > 0
            ORDER BY S.fullname
        """
        return DB.fetch_all(sql, params)

class CourseAllocationModel:
    @staticmethod
    def get_exam_configs(degree_id, session_id=None, semester_id=None):
        sql = """
            SELECT M.pk_exconfigid as id, 
                   ISNULL(UPPER(MF.descriptiion), '') + ' ' + ISNULL(YF.description, '') + ' - ' + ISNULL(UPPER(MT.descriptiion), '') + ' ' + ISNULL(YT.description, '') as period,
                   (SELECT STUFF((SELECT ', ' + ISNULL(RTRIM(S.semester_roman), 'Sem ' + CAST(D.fk_semesterid AS VARCHAR)) + '  - ' + D.ExamType 
                                  FROM SMS_ExamConfig_Dtl D
                                  LEFT JOIN SMS_Semester_Mst S ON D.fk_semesterid = S.pk_semesterid
                                  WHERE D.fk_exconfigid = M.pk_exconfigid
                                  ORDER BY D.fk_semesterid
                                  FOR XML PATH('')), 1, 2, '')) as sem_config
            FROM SMS_ExamConfig_Mst M
            LEFT JOIN Month_Mst MF ON M.fk_monthid_from = MF.pk_MonthId
            LEFT JOIN Year_Mst YF ON M.fk_yearid_From = YF.pk_yearID
            LEFT JOIN Month_Mst MT ON M.fk_monthid_to = MT.pk_MonthId
            LEFT JOIN Year_Mst YT ON M.fk_yearid_To = YT.pk_yearID
            WHERE M.fk_degreeid = ?
        """
        params = [degree_id]
        if session_id and str(session_id) not in ['0', 'None', '']:
            sql += " AND (M.fk_sessionid = ? OR M.fk_sessionid IS NULL OR M.fk_sessionid = 0)"
            params.append(session_id)
            
        sql += " ORDER BY M.isactive DESC, M.pk_exconfigid DESC"
        rows = DB.fetch_all(sql, params)
        for r in rows:
            period = r['period'] or ''
            for m in ['JANUARY', 'FEBRUARY', 'MARCH', 'APRIL', 'MAY', 'JUNE', 'JULY', 'AUGUST', 'SEPTEMBER', 'OCTOBER', 'NOVEMBER', 'DECEMBER']:
                if m in period:
                    period = period.replace(m, m[:3])
            sem_config = r['sem_config'] or ''
            r['display_name'] = f"{period} -->{sem_config}"
        return rows

    @staticmethod
    def get_allocated_courses(sid, exconfig_id):
        sql = """
            SELECT A.Pk_stucourseallocid, C.coursecode, C.coursename, 
                   S.semester_roman + ' (' + SES.sessionname + ')' as semester_info
            FROM SMS_StuCourseAllocation A
            INNER JOIN SMS_Course_Mst C ON A.fk_courseid = C.pk_courseid
            INNER JOIN SMS_Semester_Mst S ON A.fk_degreecycleid = S.pk_semesterid
            INNER JOIN SMS_AcademicSession_Mst SES ON A.fk_dgacasessionid = SES.pk_sessionid
            WHERE A.fk_sturegid = ? AND A.fk_exconfigid = ?
        """
        return DB.fetch_all(sql, [sid, exconfig_id])

    @staticmethod
    def get_student_course_plan_for_allocation(sid):
        # Refined query to include ispassed status and exact semester formatting
        # Formatting: (2024-2025) I  <-- No space between ) and semester
        sql = """
            SELECT C.pk_courseid as fk_courseid, C.coursecode, C.coursename, 
                   '(' + LTRIM(RTRIM(SES.sessionname)) + ') ' + SEM.semester_roman as plan_semester,
                   CYC.fk_semesterid as plan_semester_id,
                   CAST(ISNULL(ALLOC.ispassed, 0) AS BIT) as is_passed
            FROM SMS_StuCourseAllocation ALLOC
            INNER JOIN SMS_Course_Mst C ON ALLOC.fk_courseid = C.pk_courseid
            INNER JOIN SMS_DegreeCycle_Mst CYC ON ALLOC.fk_degreecycleid = CYC.pk_degreecycleid
            INNER JOIN SMS_Semester_Mst SEM ON CYC.fk_semesterid = SEM.pk_semesterid
            INNER JOIN SMS_AcademicSession_Mst SES ON ALLOC.fk_dgacasessionid = SES.pk_sessionid
            WHERE ALLOC.fk_sturegid = ?
            
            UNION ALL
            
            SELECT C.pk_courseid as fk_courseid, C.coursecode, C.coursename,
                   '' as plan_semester,
                   CP.fk_semesterid as plan_semester_id,
                   0 as is_passed
            FROM Sms_course_Approval CP
            INNER JOIN SMS_Course_Mst C ON CP.fk_courseid = C.pk_courseid
            WHERE CP.fk_sturegid = ? 
              AND CP.fk_courseid NOT IN (SELECT fk_courseid FROM SMS_StuCourseAllocation WHERE fk_sturegid = ?)
            
            ORDER BY plan_semester_id, coursecode
        """
        return DB.fetch_all(sql, [sid, sid, sid])

    @staticmethod
    def allocate_courses(sid, course_ids, exconfig_id, user_id, semester_id):
        # Need degree and session from exconfig
        exconfig = DB.fetch_one("SELECT fk_sessionid, fk_degreeid FROM SMS_ExamConfig_Mst WHERE pk_exconfigid = ?", [exconfig_id])
        if not exconfig: return False
        
        # Find correct degree cycle for this degree and semester
        cycle = DB.fetch_one("SELECT pk_degreecycleid FROM SMS_DegreeCycle_Mst WHERE fk_degreeid = ? AND fk_semesterid = ?", [exconfig['fk_degreeid'], semester_id])
        cycle_id = cycle['pk_degreecycleid'] if cycle else None

        # This is a simplified version. Live ERP usually involves complex validation.
        for cid in course_ids:
            # Check if already allocated
            exists = DB.fetch_scalar("SELECT COUNT(*) FROM SMS_StuCourseAllocation WHERE fk_sturegid=? AND fk_courseid=? AND fk_exconfigid=?", [sid, cid, exconfig_id])
            if not exists:
                DB.execute("""
                    INSERT INTO SMS_StuCourseAllocation (fk_sturegid, fk_courseid, fk_exconfigid, fk_dgacasessionid, fk_degreecycleid, AllocDate, Lastupdatedby)
                    VALUES (?, ?, ?, ?, ?, GETDATE(), ?)
                """, [sid, cid, exconfig_id, exconfig['fk_sessionid'], cycle_id, str(user_id)])
        return True

    @staticmethod
    def delete_allocated_courses(sid, alloc_ids):
        if not alloc_ids: return False
        placeholders = ",".join(["?"] * len(alloc_ids))
        return DB.execute(f"DELETE FROM SMS_StuCourseAllocation WHERE fk_sturegid=? AND Pk_stucourseallocid IN ({placeholders})", [sid] + alloc_ids)

    @staticmethod
    def get_courses_not_in_plan(sid):
        # Fetch all active courses that are NOT in the student's plan
        # Format: coursecode[coursename] as per live template
        sql = """
            SELECT pk_courseid, coursecode + '[' + coursename + ']' as display_name
            FROM SMS_Course_Mst
            WHERE isobsolete = 0
              AND pk_courseid NOT IN (SELECT fk_courseid FROM Sms_course_Approval WHERE fk_sturegid = ?)
            ORDER BY coursecode
        """
        return DB.fetch_all(sql, [sid])

    @staticmethod
    def get_courses_for_allocation(filters):
        # Fetch courses offered for the specific criteria.
        # Logic: 
        # 1. HOD Offerings (Semesterwise By HOD)
        # 2. Syllabus Mappings (Course_Mst_Dtl) for this degree/semester
        # 3. Teaching Allocations (TCourseAlloc)
        # We exclude courses with 'to be deleted' or 'old' in name if they are redundant.
        
        sql = """
            SELECT DISTINCT 
                C.pk_courseid as id, 
                C.coursename as name, 
                C.coursecode as code,
                ISNULL(S.sessionname, S2.sessionname) as session_name
            FROM SMS_Course_Mst C
            LEFT JOIN SMS_Course_Mst_Dtl CD ON C.pk_courseid = CD.fk_courseid
            LEFT JOIN SMS_AcademicSession_Mst S ON CD.fk_sessionid_from = S.pk_sessionid
            
            -- Join with HOD Offerings
            LEFT JOIN SMS_CourseAllocationSemesterwiseByHOD_Dtl HD ON C.pk_courseid = HD.fk_courseid
            LEFT JOIN SMS_CourseAllocationSemesterwiseByHOD HM ON HD.fk_courseallocid = HM.Pk_courseallocid
            LEFT JOIN SMS_AcademicSession_Mst S2 ON HM.fk_dgacasessionid = S2.pk_sessionid

            -- Join with TCourseAlloc (for skill/elective courses like Vermicompost)
            LEFT JOIN SMS_TCourseAlloc_Dtl TD ON C.pk_courseid = TD.fk_courseid
            LEFT JOIN SMS_TCourseAlloc_Mst TM ON TD.fk_tcourseallocid = TM.pk_tcourseallocid

            WHERE C.isobsolete = 0
              AND (
                -- Case 1: Mapped in syllabus for this degree/sem and is active
                (CD.fk_degreeid = ? AND CD.fk_semesterid = ? AND CD.isactive = 1)
                OR
                -- Case 2: Explicitly offered by HOD for this session/degree/sem
                (HM.degreeid = ? AND HM.fk_semesterid = ? AND HM.fk_dgacasessionid = ? AND HD.courseActive = 1)
                OR
                -- Case 3: Offered in teaching allocation for this session/degree (handles multi-sem skills)
                (TM.fk_degreeid = ? AND TM.fk_sessionid = ? AND TM.fk_collegeid = ?)
              )
              -- Exclude 'to be deleted' and redundant 'old' courses if they are not in the primary syllabus
              AND (C.coursename NOT LIKE '%to be deleted%' AND C.coursename NOT LIKE '%to be delete%')
              AND NOT (C.coursecode = 'Biochem 101 Old' AND CD.fk_courseid IS NULL)
        """
        # params: CD.degree, CD.sem, HM.degree, HM.sem, HM.session, TM.degree, TM.session, TM.college
        params = [
            filters.get('degree_id'), filters.get('semester_id'),
            filters.get('degree_id'), filters.get('semester_id'), filters.get('session_id'),
            filters.get('degree_id'), filters.get('session_id'), filters.get('college_id')
        ]
        
        # If exconfig is provided, we can further narrow down or prioritize
        if filters.get('exconfig_id') and str(filters['exconfig_id']) not in ('0', 'None'):
            # Some systems use exconfig to offer specific optional courses
            pass

        sql += " ORDER BY C.coursename"
        return DB.fetch_all(sql, params)

    @staticmethod
    def get_students_for_allocation(filters):
        # Match live system count (e.g. 150 students)
        # Using fk_curr_session and joining with DegreeCycle for semester filtering.
        sql = """
            SELECT DISTINCT S.pk_sid as id, S.fullname as name, S.enrollmentno as admission_no
            FROM SMS_Student_Mst S
            INNER JOIN SMS_DegreeCycle_Mst DC ON S.fk_degreecycleidcurrent = DC.pk_degreecycleid
            WHERE S.fk_collegeid = ? 
              AND S.fk_degreeid = ?
              AND S.fk_curr_session = ?
              AND DC.fk_semesterid = ?
              AND (S.IsRegCancel IS NULL OR S.IsRegCancel = 0)
              AND (S.isdgcompleted IS NULL OR S.isdgcompleted = 0)
        """
        params = [filters.get('college_id'), filters.get('degree_id'), filters.get('session_id'), filters.get('semester_id')]

        if filters.get('branch_id') and str(filters['branch_id']) != '0':
            sql += " AND S.fk_branchid = ?"
            params.append(filters['branch_id'])
        
        sql += " ORDER BY S.fullname"
        return DB.fetch_all(sql, params)

    @staticmethod
    def save_ug_regular_allocation(filters, student_ids, course_ids, user_id):
        if not student_ids or not course_ids:
            return False, "No students or courses selected."
            
        exconfig_id = filters.get('exconfig_id')
        if not exconfig_id:
            return False, "Exam Configuration is missing."

        # Get session and degree from exconfig to ensure consistency
        exconfig = DB.fetch_one("SELECT fk_sessionid, fk_degreeid FROM SMS_ExamConfig_Mst WHERE pk_exconfigid = ?", [exconfig_id])
        if not exconfig:
            return False, "Invalid Exam Config."
            
        fk_dgacasessionid = exconfig['fk_sessionid']
        fk_degreeid = exconfig['fk_degreeid']
        fk_semesterid = filters.get('semester_id')

        # Find Degree Cycle ID for this course/semester map
        # This is tricky because one semester might have multiple cycle IDs if courses differ.
        # We'll try to find cycle ID per course.
        
        count = 0
        try:
            for sid in student_ids:
                for cid in course_ids:
                    # Check duplication
                    exists = DB.fetch_scalar("""
                        SELECT COUNT(*) FROM SMS_StuCourseAllocation 
                        WHERE fk_sturegid = ? AND fk_courseid = ? AND fk_exconfigid = ?
                    """, [sid, cid, exconfig_id])
                    
                    if exists == 0:
                        # Fetch Degree Cycle for this specific course and semester
                        cycle_row = DB.fetch_one("""
                            SELECT pk_degreecycleid 
                            FROM SMS_DegreeCycle_Mst 
                            WHERE fk_degreeid = ? AND fk_semesterid = ? AND fk_courseid = ?
                        """, [fk_degreeid, fk_semesterid, cid])
                        
                        fk_degreecycleid = cycle_row['pk_degreecycleid'] if cycle_row else None
                        
                        DB.execute("""
                            INSERT INTO SMS_StuCourseAllocation 
                            (fk_sturegid, fk_courseid, fk_exconfigid, fk_dgacasessionid, fk_degreecycleid, AllocDate, Lastupdatedby, isfinalsubmit)
                            VALUES (?, ?, ?, ?, ?, GETDATE(), ?, 1)
                        """, [sid, cid, exconfig_id, fk_dgacasessionid, fk_degreecycleid, user_id])
                        count += 1
            return True, f"Successfully allocated courses to {len(student_ids)} students."
        except Exception as e:
            return False, str(e)

    @staticmethod
    def get_allocated_students(filters):
        # Mandatory filters for grid
        if not filters.get('degree_id') or not filters.get('semester_id'):
            return []

        # Convert to None if empty or 0 to help SQL handling
        exconfig_id = filters.get('exconfig_id')
        if not exconfig_id or str(exconfig_id) == '0' or str(exconfig_id) == 'None':
            exconfig_id = None
        
        # We only show allocations if an Exam Config is selected, matching live behavior
        if not exconfig_id:
            return []

        sql = """
            SELECT DISTINCT S.pk_sid as id, S.fullname as name, S.enrollmentno as admission_no,
                   (SELECT STUFF((SELECT ' | ' + C.coursecode 
                                  FROM SMS_StuCourseAllocation A2
                                  INNER JOIN SMS_Course_Mst C ON A2.fk_courseid = C.pk_courseid
                                  WHERE A2.fk_sturegid = S.pk_sid 
                                    AND A2.fk_exconfigid = ?
                                  FOR XML PATH('')), 1, 3, '')) as courses
            FROM SMS_StuCourseAllocation A
            INNER JOIN SMS_Student_Mst S ON A.fk_sturegid = S.pk_sid
            WHERE A.fk_exconfigid = ?
        """
        params = [exconfig_id, exconfig_id]
        
        if filters.get('college_id'):
            sql += " AND S.fk_collegeid = ?"
            params.append(filters['college_id'])
        if filters.get('degree_id'):
            sql += " AND S.fk_degreeid = ?"
            params.append(filters['degree_id'])
        if filters.get('branch_id') and str(filters['branch_id']) != '0':
            sql += " AND S.fk_branchid = ?"
            params.append(filters['branch_id'])
            
        sql += " ORDER BY S.fullname"
        return DB.fetch_all(sql, params)

    @staticmethod
    def deallocate_student_courses(sid, exconfig_id, user_id):
        # Delete allocations for this student only in the specific exconfig context
        if not exconfig_id: return False
        return DB.execute("DELETE FROM SMS_StuCourseAllocation WHERE fk_sturegid = ? AND fk_exconfigid = ?", [sid, exconfig_id])

class AddWithModel:
    @staticmethod
    def get_teacher_requests(filters, teacher_id, processed=False):
        # Filtering logic for teacher approvals
        # Processed means Teach_approv is not null (A/R)
        sql = """
            SELECT AW.*, S.fullname, S.enrollmentno, C.coursecode, C.coursename, 
                   SES.sessionname, SEM.semester_roman
            FROM SMS_CourseAdditionWithdrawal_Mst AW
            INNER JOIN SMS_Student_Mst S ON AW.fk_Stid = S.pk_sid
            INNER JOIN SMS_Course_Mst C ON AW.fk_courseid = C.pk_courseid
            INNER JOIN SMS_AcademicSession_Mst SES ON AW.fk_sessionid = SES.pk_sessionid
            INNER JOIN SMS_Semester_Mst SEM ON AW.fk_semesterid = SEM.pk_semesterid
            WHERE AW.fk_sessionid = ?
        """
        params = [filters.get('session_id')]
        
        # Teacher filter - Join with TCoursesAlloc to find courses taught by this teacher
        sql += """ 
            AND AW.fk_courseid IN (
                SELECT DTL.fk_courseid 
                FROM SMS_TCourseAlloc_Dtl DTL
                INNER JOIN SMS_TCourseAlloc_Mst MST ON DTL.fk_tcourseallocid = MST.pk_tcourseallocid
                WHERE MST.fk_employeeid = (SELECT fk_empId FROM UM_Users_Mst WHERE pk_userId = ?)
            )
        """
        params.append(teacher_id)

        if processed:
            sql += " AND AW.Teach_approv IS NOT NULL"
        else:
            sql += " AND AW.Teach_approv IS NULL"
            
        return DB.fetch_all(sql, params)

    @staticmethod
    def approve_by_teacher(pk_id, status, remarks, user_id):
        # status: 'A' for Approved, 'R' for Rejected
        sql = """
            UPDATE SMS_CourseAdditionWithdrawal_Mst
            SET Teach_approv = ?, Remarks_By_Teach = ?, TApprov_By = ?, Teach_approv_date = GETDATE()
            WHERE Pk_AddWith = ?
        """
        return DB.execute(sql, [status, remarks, str(user_id), pk_id])

    @staticmethod
    def get_major_advisor_requests(filters, advisor_id, processed=False):
        # Advisor filter - Join with Advisory Committee to find students under this advisor
        sql = """
            SELECT AW.*, S.fullname, S.enrollmentno, C.coursecode, C.coursename, 
                   SES.sessionname, SEM.semester_roman
            FROM SMS_CourseAdditionWithdrawal_Mst AW
            INNER JOIN SMS_Student_Mst S ON AW.fk_Stid = S.pk_sid
            INNER JOIN SMS_Course_Mst C ON AW.fk_courseid = C.pk_courseid
            INNER JOIN SMS_AcademicSession_Mst SES ON AW.fk_sessionid = SES.pk_sessionid
            INNER JOIN SMS_Semester_Mst SEM ON AW.fk_semesterid = SEM.pk_semesterid
            INNER JOIN SMS_Advisory_Committee_Mst ACM ON S.pk_sid = ACM.fk_stid
            INNER JOIN SMS_Advisory_Committee_Dtl ACD ON ACM.pk_adcid = ACD.fk_adcid
            WHERE AW.fk_sessionid = ? 
              AND ACD.fk_empid = (SELECT fk_empId FROM UM_Users_Mst WHERE pk_userId = ?)
              AND ACD.fk_statusid = 1 -- Major Advisor
        """
        params = [filters.get('session_id'), advisor_id]

        if processed:
            sql += " AND AW.dean_approv IS NOT NULL"
        else:
            sql += " AND AW.dean_approv IS NULL AND AW.Teach_approv = 'A'"
            
        return DB.fetch_all(sql, params)

    @staticmethod
    def approve_by_major_advisor(pk_id, status, remarks, user_id):
        # Major Advisor approval updates dean_approv (as per legacy mappings)
        sql = """
            UPDATE SMS_CourseAdditionWithdrawal_Mst
            SET dean_approv = ?, Remarks_By_Dean = ?, DApprov_By = ?, dean_approv_date = GETDATE()
            WHERE Pk_AddWith = ?
        """
        return DB.execute(sql, [status, remarks, str(user_id), pk_id])

    @staticmethod
    def get_add_with_status(filters):
        # filters: session_id, degree_id, semester_id, branch_id
        sql = """
            SELECT AW.*, S.fullname, S.enrollmentno as AdmissionNo, B.Branchname,
                   SEM.semester_roman, C.coursecode + ' ' + C.coursename as CourseName,
                   CASE WHEN AW.Addwith_type = 'A' THEN 'Addition' ELSE 'Withdrawal' END as RequestType,
                   AW.DateOfApply,
                   CASE WHEN AW.Teach_approv = 'A' THEN 'Approved' 
                        WHEN AW.Teach_approv = 'R' THEN 'Rejected' 
                        ELSE 'Pending' END as InstructorStatus,
                   CASE WHEN AW.dean_approv = 'A' THEN 'Approved' 
                        WHEN AW.dean_approv = 'R' THEN 'Rejected' 
                        ELSE 'Pending' END as AdvisorStatus
            FROM SMS_CourseAdditionWithdrawal_Mst AW
            INNER JOIN SMS_Student_Mst S ON AW.fk_Stid = S.pk_sid
            INNER JOIN SMS_Course_Mst C ON AW.fk_courseid = C.pk_courseid
            INNER JOIN SMS_AcademicSession_Mst SES ON AW.fk_sessionid = SES.pk_sessionid
            INNER JOIN SMS_Semester_Mst SEM ON AW.fk_semesterid = SEM.pk_semesterid
            LEFT JOIN SMS_BranchMst B ON S.fk_branchid = B.Pk_BranchId
            WHERE AW.fk_sessionid = ? AND AW.fk_degreeid = ?
        """
        params = [filters.get('session_id'), filters.get('degree_id')]
        
        if filters.get('semester_id') and str(filters['semester_id']) != '0':
            sql += " AND AW.fk_semesterid = ?"
            params.append(filters['semester_id'])
            
        if filters.get('branch_id') and str(filters['branch_id']) != '0':
            sql += " AND S.fk_branchid = ?"
            params.append(filters['branch_id'])
            
        sql += " ORDER BY AW.DateOfApply DESC"
        return DB.fetch_all(sql, params)

class ResearchModel:
    @staticmethod
    def get_students_for_mandates(filters):
        # filters: college_id, session_id, degree_id, semester_id, branch_id
        sql = """
            SELECT S.pk_sid, S.enrollmentno as AdmissionNo, S.fullname
            FROM SMS_Student_Mst S
            WHERE S.fk_collegeid = ? AND S.fk_adm_session = ? AND S.fk_degreeid = ?
        """
        params = [filters.get('college_id'), filters.get('session_id'), filters.get('degree_id')]
        
        # Mandatory branch filtering as requested
        if filters.get('branch_id') and str(filters['branch_id']) != '0':
            sql += " AND S.fk_branchid = ?"
            params.append(filters['branch_id'])
        
        students = DB.fetch_all(sql, params)
        
        # Determine degree type for mandates
        stu_info = DB.fetch_one("""
            SELECT DT.isug 
            FROM SMS_Degree_Mst D 
            INNER JOIN SMS_DegreeType_Mst DT ON D.fk_degreetypeid = DT.pk_degreetypeid 
            WHERE D.pk_degreeid = ?
        """, [filters['degree_id']])
        is_phd = (stu_info and stu_info['isug'] == 'P')

        for s in students:
            # Fetch existing mandates for this student dynamically
            s['mandates'] = ResearchModel.get_student_mandates(s['pk_sid'], is_phd)
            
        return students

    @staticmethod
    def get_student_mandates(sid, is_phd=False):
        # Define dynamic types
        if is_phd:
            types = [
                {'id': 3, 'name': 'Synopsis Seminar'},
                {'id': 1, 'name': 'Comprehensive Exam'},
                {'id': 4, 'name': 'Thesis Seminar'},
                {'id': 2, 'name': 'Final Thesis Viva'}
            ]
        else:
            # Master's
            types = [
                {'id': 1, 'name': 'Comprehensive Exam'},
                {'id': 2, 'name': 'Final Thesis Viva'},
                {'id': 3, 'name': 'Synopsis Seminar'},
                {'id': 4, 'name': 'Thesis Seminar'}
            ]

        # Fetch current statuses from SMS_ResearchPaperSub_dtl
        # Combining Name and Code for 'Submitted By' column
        sql = """
            SELECT D.*, U.name + ' | ' + U.loginname as username
            FROM SMS_ResearchPaperSub_dtl D
            LEFT JOIN UM_Users_Mst U ON D.updated_by = CAST(U.pk_userId AS VARCHAR)
            WHERE D.fk_sid = ?
        """
        existing = DB.fetch_all(sql, [sid])
        existing_map = {e['fk_Coursetypeid']: e for e in existing}
        
        res = []
        for mt in types:
            ext = existing_map.get(mt['id'], {})
            res.append({
                'mandate_id': mt['id'],
                'mandate_name': mt['name'],
                'pk_Resdtl_id': ext.get('pk_Resdtl_id'),
                'is_submitted': ext.get('issubmitted', False),
                'remarks': ext.get('Remarks', ''),
                'submission_date': ext.get('submission_date', datetime.now().strftime('%d/%m/%Y')),
                'username': ext.get('username', '')
            })
        return res

    @staticmethod
    def update_mandate(sid, mandate_id, remarks, submission_date, is_submitted, user_id, filters):
        # 1. Ensure master record exists in SMS_ResearchPaperSub_Mst
        mst_id = DB.fetch_scalar("""
            SELECT pk_ResPapSub_id FROM SMS_ResearchPaperSub_Mst 
            WHERE fk_college_id=? AND fk_degree_id=? AND fk_session_id=? AND fk_branchid=?
        """, [filters['college_id'], filters['degree_id'], filters['session_id'], filters['branch_id']])
        
        if not mst_id:
            DB.execute("""
                INSERT INTO SMS_ResearchPaperSub_Mst 
                (fk_college_id, fk_degree_id, fk_session_id, fk_branchid, fk_semesterid, creation_date)
                VALUES (?, ?, ?, ?, ?, GETDATE())
            """, [filters['college_id'], filters['degree_id'], filters['session_id'], filters['branch_id'], filters['semester_id']])
            
            mst_id = DB.fetch_scalar("""
                SELECT @@IDENTITY
            """)

        # 2. Check if detail record exists
        existing_id = DB.fetch_scalar("SELECT pk_Resdtl_id FROM SMS_ResearchPaperSub_dtl WHERE fk_sid=? AND fk_Coursetypeid=? AND fk_ResPapSub_id=?", [sid, mandate_id, mst_id])
        
        if existing_id:
            sql = """
                UPDATE SMS_ResearchPaperSub_dtl 
                SET Remarks=?, submission_date=?, issubmitted=?, updated_by=?, datecurrent=GETDATE()
                WHERE pk_Resdtl_id=?
            """
            return DB.execute(sql, [remarks, submission_date, 1 if is_submitted else 0, str(user_id), existing_id])
        else:
            sql = """
                INSERT INTO SMS_ResearchPaperSub_dtl (fk_sid, fk_Coursetypeid, fk_ResPapSub_id, Remarks, submission_date, issubmitted, updated_by, datecurrent)
                VALUES (?, ?, ?, ?, ?, ?, ?, GETDATE())
            """
            return DB.execute(sql, [sid, mandate_id, mst_id, remarks, submission_date, 1 if is_submitted else 0, str(user_id)])

    @staticmethod
    def get_students_for_work_programme(filters):
        # Fetch students matching criteria with basic info
        sql = """
            SELECT S.pk_sid, S.enrollmentno as AdmissionNo, S.fullname,
                   D.degreename, B.Branchname, S.fname as fathername, S.enrollmentno,
                   C.collegename, SES.sessionname
            FROM SMS_Student_Mst S
            LEFT JOIN SMS_College_Mst C ON S.fk_collegeid = C.pk_collegeid
            LEFT JOIN SMS_Degree_Mst D ON S.fk_degreeid = D.pk_degreeid
            LEFT JOIN SMS_BranchMst B ON S.fk_branchid = B.Pk_BranchId
            LEFT JOIN SMS_AcademicSession_Mst SES ON S.fk_adm_session = SES.pk_sessionid
            WHERE S.fk_collegeid = ? AND S.fk_adm_session = ? AND S.fk_degreeid = ?
        """
        params = [filters.get('college_id'), filters.get('session_id'), filters.get('degree_id')]
        if filters.get('branch_id') and str(filters['branch_id']) != '0':
            sql += " AND S.fk_branchid = ?"
            params.append(filters['branch_id'])
            
        students_raw = DB.fetch_all(sql, params)
        
        detailed_students = []
        for s in students_raw:
            sid = s['pk_sid']
            
            # 1. Minor Field Name
            minor_field = DB.fetch_scalar("""
                SELECT B.Branchname FROM SMS_stuDiscipline_dtl D 
                INNER JOIN SMS_BranchMst B ON D.fk_desciplineidMinor = B.Pk_BranchId 
                WHERE D.fk_sturegid = ?
            """, [sid])
            
            # 2. Academic Qualifications
            qualifications = DB.fetch_all("""
                SELECT examname, yearofpassing, division, percentage, Bord_Univ, Specialization
                FROM SMS_Stu_Quali_Dtl
                WHERE fk_sid = ?
                ORDER BY fk_examid DESC
            """, [sid])
            
            # 3. Undergraduate Preparation
            ug_prep = DB.fetch_all("""
                SELECT C.coursecode, C.coursename, U.crtheory, U.crpractical, U.marks as grade
                FROM SMS_UnderGradDetail_dtl U
                INNER JOIN SMS_Course_Mst C ON U.fk_courseid = C.pk_courseid
                WHERE U.fk_sid = ?
            """, [sid])

            # 4. Previous postgraduate training
            pg_training = DB.fetch_all("""
                SELECT C.coursecode, C.coursename, P.crtheory, P.crpractical, P.marks as grade, T.coursetype as classification
                FROM SMS_PostGrad_Dtl P
                INNER JOIN SMS_Course_Mst C ON P.fk_courseid = C.pk_courseid
                LEFT JOIN SMS_CourseType_Mst T ON P.fk_coursetypeid = T.pk_coursetypeid
                WHERE P.fk_sid = ?
            """, [sid])

            # 5. Advisory Committee
            committee = AdvisoryModel.get_student_advisory_committee(sid)
            
            # 6. Approved Courses Grouped by Type
            courses_raw = DB.fetch_all("""
                SELECT A.*, C.coursecode, C.coursename, T.coursetype as type_name
                FROM Sms_course_Approval A
                INNER JOIN SMS_Course_Mst C ON A.fk_courseid = C.pk_courseid
                LEFT JOIN SMS_Coursetype_Mst T ON A.courseplanid = T.pk_coursetypeid
                WHERE A.fk_sturegid = ?
                ORDER BY A.courseplanid, C.coursecode
            """, [sid])
            
            grouped_courses = {}
            for c in courses_raw:
                plan = c['courseplan'] or 'OTHER'
                if plan not in grouped_courses: grouped_courses[plan] = []
                grouped_courses[plan].append(c)
                
            # 7. Credit Summary
            summary = {
                'major': sum((c['crhrth'] + c['crhrpr']) for c in courses_raw if c['courseplan'] == 'MA'),
                'minor': sum((c['crhrth'] + c['crhrpr']) for c in courses_raw if c['courseplan'] == 'MI'),
                'supporting': sum((c['crhrth'] + c['crhrpr']) for c in courses_raw if c['courseplan'] == 'SU'),
                'common': sum((c['crhrth'] + c['crhrpr']) for c in courses_raw if c['courseplan'] == 'CP'),
                'research': sum((c['crhrth'] + c['crhrpr']) for c in courses_raw if 'RESEARCH' in (c['type_name'] or '').upper())
            }
            summary['total'] = sum(summary.values())
            
            detailed_students.append({
                'info': s,
                'minor_field': minor_field or '',
                'committee': committee,
                'qualifications': qualifications,
                'ug_prep': ug_prep,
                'pg_training': pg_training,
                'grouped_courses': grouped_courses,
                'summary': summary
            })

        return detailed_students

class AdvisoryStatusModel:
    @staticmethod
    def get_advisory_approval_status(filters):
        # filters: college_id, session_id, degree_id, semester_id, branch_id
        sql = """
            SELECT S.pk_sid, S.enrollmentno as AdmissionNo, S.fullname, B.Branchname,
                   ACM.pk_adcid, 
                   CASE WHEN ACM.pk_adcid IS NOT NULL THEN 'YES' ELSE 'NO' END as MajorAdvisorMade,
                   CASE WHEN EXISTS(SELECT 1 FROM SMS_stuDiscipline_dtl D WHERE D.fk_sturegid = S.pk_sid) THEN 'YES' ELSE 'NO' END as SpecializationMade,
                   CASE WHEN EXISTS(SELECT 1 FROM SMS_Advisory_Committee_Dtl ACD WHERE ACD.fk_adcid = ACM.pk_adcid AND ACD.fk_statusid IN (2,3,4)) THEN 'YES' ELSE 'NO' END as MemberMinorMade,
                   
                   CASE WHEN ACM.hod_approval = 'A' THEN 'Approved [' + ISNULL(EH.empname, 'HOD') + ']'
                        WHEN ACM.hod_approval = 'R' THEN 'Rejected'
                        ELSE 'Pending' END as HodApproval,
                   CONVERT(VARCHAR, ACM.hod_date, 103) as HodApprovalDate,
                   
                   CASE WHEN ACM.college_deanapproval = 'A' THEN 'Approved [' + ISNULL(ECD.empname, 'Dean') + ']'
                        WHEN ACM.college_deanapproval = 'R' THEN 'Rejected'
                        ELSE 'Pending' END as CollegeDeanApproval,
                   CONVERT(VARCHAR, ACM.Collegedean_date, 103) as CollegeDeanApprovalDate,
                   
                   CASE WHEN ACM.app_advstatus = 'A' THEN 'Approved [' + ISNULL(EPGS.empname, 'Dean PGS') + ']'
                        WHEN ACM.app_advstatus = 'R' THEN 'Rejected'
                        ELSE 'Pending' END as DeanPgsApproval,
                   CONVERT(VARCHAR, ACM.deanpgs_date, 103) as DeanPgsApprovalDate,
                   
                   CASE WHEN EXISTS(SELECT 1 FROM Sms_course_Approval CA WHERE CA.fk_sturegid = S.pk_sid) THEN 'Created' ELSE 'NO' END as CoursePlanMade,
                   CASE WHEN ACM.approvalstatus = 'A' THEN 'Approved' 
                        WHEN ACM.approvalstatus = 'R' THEN 'Rejected'
                        ELSE 'Pending' END as CoursePlanApproval,
                   CONVERT(VARCHAR, ACM.responsedate, 103) as CoursePlanApprovalDate
            FROM SMS_Student_Mst S
            LEFT JOIN SMS_BranchMst B ON S.fk_branchid = B.Pk_BranchId
            LEFT JOIN SMS_Advisory_Committee_Mst ACM ON S.pk_sid = ACM.fk_stid
            LEFT JOIN SAL_Employee_Mst EH ON ACM.hod_id = EH.pk_empid
            LEFT JOIN SAL_Employee_Mst ECD ON ACM.collegedean_id = ECD.pk_empid
            LEFT JOIN SAL_Employee_Mst EPGS ON ACM.deanpgs_id = EPGS.pk_empid
            WHERE S.fk_collegeid = ? AND S.fk_adm_session = ? AND S.fk_degreeid = ?
        """
        params = [filters.get('college_id'), filters.get('session_id'), filters.get('degree_id')]
        
        if filters.get('branch_id') and str(filters['branch_id']) != '0':
            sql += " AND S.fk_branchid = ?"
            params.append(filters['branch_id'])
            
        sql += " ORDER BY S.fullname"
        return DB.fetch_all(sql, params)

class ThesisModel:
    @staticmethod
    def get_students_for_thesis(filters):
        # filters: college_id, session_id, degree_id, semester_id, branch_id
        sql = """
            SELECT S.pk_sid, S.enrollmentno as AdmissionNo, S.fullname,
                   T.pk_stuthesisid, T.IsFeeRemitted, T.TotalSem, T.ThesisSubmissionDate, 
                   T.MCDate, T.VivaNotificationDate, T.ResultPublishDate,
                   T.ThesisNotificationNo, T.VivaNotificationNo, T.ResultNotificationNo,
                   T.ThesisTitle, T.AdjudicatorRemarks, T.Resubmission, T.Remarks
            FROM SMS_Student_Mst S
            LEFT JOIN SMS_StuThesis_dtl T ON S.pk_sid = T.fk_sid
            WHERE S.fk_collegeid = ? AND S.fk_adm_session = ? AND S.fk_degreeid = ?
        """
        params = [filters.get('college_id'), filters.get('session_id'), filters.get('degree_id')]
        
        if filters.get('branch_id') and str(filters['branch_id']) != '0':
            sql += " AND S.fk_branchid = ?"
            params.append(filters['branch_id'])
            
        return DB.fetch_all(sql, params)

    @staticmethod
    def update_thesis_detail(sid, data, user_id):
        # Check if record exists
        exists = DB.fetch_scalar("SELECT COUNT(*) FROM SMS_StuThesis_dtl WHERE fk_sid = ?", [sid])
        
        # Helper to handle empty dates
        def clean_date(d):
            if not d or d.strip() == '': return None
            try:
                # Expecting DD/MM/YYYY from UI
                return datetime.strptime(d, '%d/%m/%Y').strftime('%Y-%m-%d')
            except:
                return None

        params = [
            1 if data.get('is_fee_remitted') else 0,
            data.get('total_sem'),
            clean_date(data.get('thesis_sub_date')),
            clean_date(data.get('mc_date')),
            clean_date(data.get('viva_date')),
            clean_date(data.get('result_date')),
            data.get('thesis_not_no'),
            data.get('viva_not_no'),
            data.get('result_not_no'),
            data.get('thesis_title'),
            data.get('adjudicator_remarks'),
            data.get('resubmission'),
            data.get('remarks'),
            str(user_id)
        ]

        if exists:
            sql = """
                UPDATE SMS_StuThesis_dtl SET 
                    IsFeeRemitted=?, TotalSem=?, ThesisSubmissionDate=?, 
                    MCDate=?, VivaNotificationDate=?, ResultPublishDate=?,
                    ThesisNotificationNo=?, VivaNotificationNo=?, ResultNotificationNo=?,
                    ThesisTitle=?, AdjudicatorRemarks=?, Resubmission=?, Remarks=?,
                    UpdatedBy=?, UpdatedDate=GETDATE()
                WHERE fk_sid=?
            """
            params.append(sid)
            return DB.execute(sql, params)
        else:
            sql = """
                INSERT INTO SMS_StuThesis_dtl (
                    IsFeeRemitted, TotalSem, ThesisSubmissionDate, 
                    MCDate, VivaNotificationDate, ResultPublishDate,
                    ThesisNotificationNo, VivaNotificationNo, ResultNotificationNo,
                    ThesisTitle, AdjudicatorRemarks, Resubmission, Remarks,
                    UpdatedBy, UpdatedDate, fk_sid
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE(), ?)
            """
            params.append(sid)
            return DB.execute(sql, params)

class AdvisorAllocationModel:
    @staticmethod
    @staticmethod
    def get_teachers_for_dropdown(college_id):
        # Format: Name || Code || Department || Specialization
        if not college_id:
            return []
            
        # Get loc_id of the college
        loc_id = DB.fetch_scalar("SELECT fk_locid FROM SMS_College_Mst WHERE pk_collegeid = ?", [college_id])
        if not loc_id:
            return []

        sql = """
            SELECT E.pk_empid as id,
                   E.empname + ' || ' + E.empcode
                   + ' || ' + ISNULL(DP.description, '')
                   + ' || ' + ISNULL(B.Branchname, '') as display_name
            FROM SAL_Employee_Mst E
            INNER JOIN SAL_Designation_Mst DSG ON E.fk_desgid = DSG.pk_desgid
            LEFT JOIN Department_Mst DP ON E.fk_deptid = DP.pk_deptid
            LEFT JOIN SMS_BranchMst B ON TRY_CAST(E.fK_PDesignspecId AS INT) = B.Pk_BranchId
            WHERE (E.employeeleftstatus IS NULL OR E.employeeleftstatus = 'N')
              AND E.fk_locid = ?
              AND DSG.isteaching = 1
              AND DSG.designation NOT LIKE '%School%'
              AND DSG.designation NOT LIKE '%Campus School%'
              AND DSG.designation NOT LIKE '%Nursery Teacher%'
              AND DSG.designation NOT LIKE '%Primary Teacher%'
            ORDER BY E.empname
        """
        return DB.fetch_all(sql, [loc_id])

    @staticmethod
    def get_students_for_advisor_allocation(filters):
        # Filters: college_id, session_id, degree_id, branch_id
        sql = """
            SELECT S.pk_sid as id, S.fullname as name, 
                   COALESCE(NULLIF(LTRIM(RTRIM(S.enrollmentno)), ''), NULLIF(LTRIM(RTRIM(S.AdmissionNo)), '')) AS admission_no,
                   ISNULL(EM.empname + ' || ' + EM.empcode, 'No Advisor Assigned') as advisor_name
            FROM SMS_Student_Mst S
            LEFT JOIN SMS_StuGuideAlloc_Dtl AD ON S.pk_sid = AD.fk_sturegid
            LEFT JOIN SMS_StuGuideAlloc_Mst AM ON AD.fk_stuguide_alloc = AM.pk_stuguide_alloc 
                 AND AM.fk_sessionid = S.fk_adm_session 
                 AND AM.fk_degreeid = S.fk_degreeid
            LEFT JOIN SAL_Employee_Mst EM ON AM.fk_empid = EM.pk_empid
            WHERE S.fk_collegeid = ? 
              AND S.fk_adm_session = ? 
              AND S.fk_degreeid = ?
              AND (S.IsRegCancel IS NULL OR S.IsRegCancel = 0)
              AND (S.isdgcompleted IS NULL OR S.isdgcompleted = 0)
        """
        params = [filters.get('college_id'), filters.get('session_id'), filters.get('degree_id')]
        
        if filters.get('branch_id') and str(filters['branch_id']) != '0':
            sql += " AND S.fk_branchid = ?"
            params.append(filters['branch_id'])
            
        sql += " ORDER BY S.fullname"
        return DB.fetch_all(sql, params)

    @staticmethod
    def save_advisor_allocation(filters, student_ids, teacher_id, user_id):
        if not student_ids or not teacher_id:
            return False, "Please select students and a teacher."
            
        conn = DB.get_connection()
        cursor = conn.cursor()
        try:
            # 1. Get or Create Master record for this teacher/degree/session context
            college_id = filters.get('college_id')
            session_id = filters.get('session_id')
            degree_id = filters.get('degree_id')
            branch_id = filters.get('branch_id') or 0
            
            cursor.execute("""
                SELECT pk_stuguide_alloc FROM SMS_StuGuideAlloc_Mst 
                WHERE fk_empid = ? AND fk_collegeid = ? AND fk_degreeid = ? AND fk_sessionid = ?
            """, [teacher_id, college_id, degree_id, session_id])
            mst_row = cursor.fetchone()
            
            if mst_row:
                mst_id = mst_row[0]
            else:
                cursor.execute("""
                    INSERT INTO SMS_StuGuideAlloc_Mst (fk_empid, fk_collegeid, fk_degreeid, fk_branchid, fk_sessionid)
                    VALUES (?, ?, ?, ?, ?)
                """, [teacher_id, college_id, degree_id, branch_id, session_id])
                cursor.execute("SELECT SCOPE_IDENTITY()")
                mst_id = cursor.fetchone()[0]

            # 2. Assign students to this master record
            for sid in student_ids:
                # Targeted delete: Remove student from any advisor allocation for THIS degree and session
                cursor.execute("""
                    DELETE D FROM SMS_StuGuideAlloc_Dtl D
                    INNER JOIN SMS_StuGuideAlloc_Mst M ON D.fk_stuguide_alloc = M.pk_stuguide_alloc
                    WHERE D.fk_sturegid = ? AND M.fk_degreeid = ? AND M.fk_sessionid = ?
                """, [sid, degree_id, session_id])
                
                cursor.execute("""
                    INSERT INTO SMS_StuGuideAlloc_Dtl (fk_stuguide_alloc, fk_sturegid, Updated_by)
                    VALUES (?, ?, ?)
                """, [mst_id, sid, str(user_id)])
            
            conn.commit()
            return True, f"Advisor successfully allocated to {len(student_ids)} students."
        except Exception as e:
            conn.rollback()
            return False, f"Error saving allocation: {str(e)}"
        finally:
            conn.close()

class IGradeModel:
    @staticmethod
    def get_teacher_requests(filters, teacher_id, processed=False):
        # Teacher filter - Join with TCoursesAlloc to find courses taught by this teacher
        # Fetching crhr from Course_Mst as IG table might have 0
        sql = """
            SELECT IG.*, S.fullname, S.enrollmentno as AdmissionNo, C.coursecode, C.coursename, 
                   C.crhr_theory as crhr_th, C.crhr_practical as crhr_pr,
                   D.degreename, B.Branchname, SEM.semester_roman
            FROM SMS_Igrade_Mst IG
            INNER JOIN SMS_Student_Mst S ON IG.fk_Stid = S.pk_sid
            INNER JOIN SMS_Course_Mst C ON IG.fk_courseid = C.pk_courseid
            INNER JOIN SMS_AcademicSession_Mst SES ON IG.fk_sessionid = SES.pk_sessionid
            INNER JOIN SMS_Semester_Mst SEM ON IG.fk_semesterid = SEM.pk_semesterid
            LEFT JOIN SMS_Degree_Mst D ON IG.fk_degreeid = D.pk_degreeid
            LEFT JOIN SMS_BranchMst B ON S.fk_branchid = B.Pk_BranchId
            WHERE IG.fk_sessionid = ?
              AND IG.fk_courseid IN (
                SELECT DTL.fk_courseid 
                FROM SMS_TCourseAlloc_Dtl DTL
                INNER JOIN SMS_TCourseAlloc_Mst MST ON DTL.fk_tcourseallocid = MST.pk_tcourseallocid
                WHERE MST.fk_employeeid = (SELECT fk_empId FROM UM_Users_Mst WHERE pk_userId = ?)
              )
        """
        params = [filters.get('session_id'), teacher_id]

        if processed:
            sql += " AND IG.Teach_approv IS NOT NULL"
        else:
            sql += " AND IG.Teach_approv IS NULL"
            
        return DB.fetch_all(sql, params)

    @staticmethod
    def approve_by_teacher(pk_id, status, remarks, user_id):
        # status: 'A' for Approved, 'R' for Rejected
        sql = """
            UPDATE SMS_Igrade_Mst
            SET Teach_approv = ?, Remarks_By_Teach = ?, TApprov_By = ?, Teacher_approvedate = GETDATE()
            WHERE Pk_Ig = ?
        """
        return DB.execute(sql, [status, remarks, str(user_id), pk_id])

    @staticmethod
    def get_dean_requests(filters, processed=False):
        # Dean PGS requests - only if approved by Teacher
        # Fetching crhr from Course_Mst as IG table might have 0
        sql = """
            SELECT IG.*, S.fullname, S.enrollmentno as AdmissionNo, C.coursecode, C.coursename, 
                   C.crhr_theory as crhr_th, C.crhr_practical as crhr_pr,
                   D.degreename, B.Branchname, SEM.semester_roman
            FROM SMS_Igrade_Mst IG
            INNER JOIN SMS_Student_Mst S ON IG.fk_Stid = S.pk_sid
            INNER JOIN SMS_Course_Mst C ON IG.fk_courseid = C.pk_courseid
            INNER JOIN SMS_AcademicSession_Mst SES ON IG.fk_sessionid = SES.pk_sessionid
            INNER JOIN SMS_Semester_Mst SEM ON IG.fk_semesterid = SEM.pk_semesterid
            LEFT JOIN SMS_Degree_Mst D ON IG.fk_degreeid = D.pk_degreeid
            LEFT JOIN SMS_BranchMst B ON S.fk_branchid = B.Pk_BranchId
            WHERE IG.fk_sessionid = ? AND IG.Teach_approv = 'A'
        """
        params = [filters.get('session_id')]

        if processed:
            sql += " AND IG.dean_approv IS NOT NULL"
        else:
            sql += " AND IG.dean_approv IS NULL"
            
        return DB.fetch_all(sql, params)

    @staticmethod
    def approve_by_dean(pk_id, status, remarks, user_id):
        sql = """
            UPDATE SMS_Igrade_Mst
            SET dean_approv = ?, Remarks_By_Dean = ?, DApprov_By = ?, dean_approvdate = GETDATE(),
                Is_finalApproved = ?
            WHERE Pk_Ig = ?
        """
        is_final = 1 if status == 'A' else 0
        return DB.execute(sql, [status, remarks, str(user_id), is_final, pk_id])

    @staticmethod
    def get_igrade_status(filters):
        sql = """
            SELECT IG.*, S.fullname, S.enrollmentno as AdmissionNo, B.Branchname,
                   SEM.semester_roman, C.coursecode + ' ' + C.coursename as CourseName,
                   C.crhr_theory as crhr_th, C.crhr_practical as crhr_pr,
                   CASE WHEN IG.Teach_approv = 'A' THEN 'Approved [' + ISNULL(ET.empname, 'Teacher') + ']'
                        WHEN IG.Teach_approv = 'R' THEN 'Rejected' 
                        ELSE 'Pending' END as TeacherStatus,
                   CONVERT(VARCHAR, IG.Teacher_approvedate, 103) as TeacherDate,
                   CASE WHEN IG.dean_approv = 'A' THEN 'Approved [' + ISNULL(ED.empname, 'Dean') + ']'
                        WHEN IG.dean_approv = 'R' THEN 'Rejected' 
                        ELSE 'Pending' END as DeanStatus,
                   CONVERT(VARCHAR, IG.dean_approvdate, 103) as DeanDate,
                   (SELECT TOP 1 F.ReceptNo + ' [' + CONVERT(VARCHAR, F.Paydate, 103) + ']'
                    FROM FMS_Feecollection_Mst F
                    INNER JOIN FMS_Feecollection_Dtls FD ON F.Pk_colId = FD.Fk_colId
                    WHERE F.Fk_Sid = IG.fk_Stid 
                      AND FD.Fk_Headid IN (32, 83) -- I Grade Fees
                      AND F.Iscancel IS NULL
                    ORDER BY F.Paydate DESC) as FeePaidInfo
            FROM SMS_Igrade_Mst IG
            INNER JOIN SMS_Student_Mst S ON IG.fk_Stid = S.pk_sid
            INNER JOIN SMS_Course_Mst C ON IG.fk_courseid = C.pk_courseid
            INNER JOIN SMS_AcademicSession_Mst SES ON IG.fk_sessionid = SES.pk_sessionid
            INNER JOIN SMS_Semester_Mst SEM ON IG.fk_semesterid = SEM.pk_semesterid
            LEFT JOIN SMS_BranchMst B ON S.fk_branchid = B.Pk_BranchId
            LEFT JOIN SAL_Employee_Mst ET ON IG.TApprov_By = ET.pk_empid
            LEFT JOIN SAL_Employee_Mst ED ON IG.DApprov_By = ED.pk_empid
            WHERE IG.fk_sessionid = ? AND IG.fk_degreeid = ?
        """
        params = [filters.get('session_id'), filters.get('degree_id')]
        
        if filters.get('semester_id') and str(filters['semester_id']) != '0':
            sql += " AND IG.fk_semesterid = ?"
            params.append(filters['semester_id'])
            
        if filters.get('branch_id') and str(filters['branch_id']) != '0':
            sql += " AND S.fk_branchid = ?"
            params.append(filters['branch_id'])
            
        sql += " ORDER BY IG.DateOfApply DESC"
        return DB.fetch_all(sql, params)

class BatchModel:
    @staticmethod
    def get_batches(college_id, degree_id, semester_id, type_tp):
        # type_tp: 'T' for Theory, 'P' for Practical
        sql = """
            SELECT D.pk_batchdtl as id, D.name_of_batch as name
            FROM SMS_Batch_Dtl D
            INNER JOIN SMS_Batch_Mst M ON D.fk_batchid = M.pk_batchid
            WHERE M.fk_collegeid = ? AND M.fk_degreeid = ? 
              AND M.fk_semesterid = ? AND M.theory_Practical = ?
            ORDER BY D.name_of_batch
        """
        rows = DB.fetch_all(sql, [college_id, degree_id, semester_id, type_tp])
        
        # Ensure "ALL" is first and unique
        final_batches = [{'id': 0, 'name': 'ALL'}]
        seen = {'ALL'}
        for r in rows:
            if r['name'].upper() != 'ALL' and r['name'] not in seen:
                final_batches.append(r)
                seen.add(r['name'])
        return final_batches

    @staticmethod
    def get_students_for_batch(filters):
        # Filters: college_id, session_id, degree_id, semester_id, type_tp, batch_id
        type_tp = filters.get('type_tp', 'T')
        batch_col = 'fk_batchid_Th' if type_tp == 'T' else 'fk_batchid_Pr'
        
        sql = f"""
            SELECT S.pk_sid, S.fullname, S.AdmissionNo, S.enrollmentno,
                   BD.name_of_batch as BatchName, S.{batch_col} as CurrentBatchId
            FROM SMS_Student_Mst S
            LEFT JOIN SMS_Batch_Dtl BD ON S.{batch_col} = BD.pk_batchdtl
            WHERE S.fk_collegeid = ? AND S.fk_adm_session = ? AND S.fk_degreeid = ?
        """
        params = [filters['college_id'], filters['session_id'], filters['degree_id']]
        
        if filters.get('branch_id') and str(filters['branch_id']) != '0':
            sql += " AND S.fk_branchid = ?"
            params.append(filters['branch_id'])
            
        sql += " ORDER BY S.fullname"
        return DB.fetch_all(sql, params)

    @staticmethod
    def assign_batch(student_ids, batch_id, type_tp):
        batch_col = 'fk_batchid_Th' if type_tp == 'T' else 'fk_batchid_Pr'
        if not student_ids: return True
        
        sql = f"UPDATE SMS_Student_Mst SET {batch_col} = ? WHERE pk_sid IN ({','.join(['?' for _ in student_ids])})"
        return DB.execute(sql, [batch_id] + student_ids)

    @staticmethod
    def get_batch_report(filters):
        # Similar to get_students_for_batch but used for final reporting
        type_tp = filters.get('type_tp', 'T')
        batch_col = 'fk_batchid_Th' if type_tp == 'T' else 'fk_batchid_Pr'
        
        sql = f"""
            SELECT S.fullname, S.AdmissionNo, S.enrollmentno,
                   BD.name_of_batch as BatchName
            FROM SMS_Student_Mst S
            LEFT JOIN SMS_Batch_Dtl BD ON S.{batch_col} = BD.pk_batchdtl
            WHERE S.fk_collegeid = ? AND S.fk_adm_session = ? AND S.fk_degreeid = ?
        """
        params = [filters['college_id'], filters['session_id'], filters['degree_id']]
        
        if filters.get('semester_id') and str(filters['semester_id']) != '0':
            # Note: student master doesn't have current semester, usually linked via course allocation
            # but for basic batch listing, we rely on degree/session
            pass

        if filters.get('batch_id') and str(filters['batch_id']) != '0' and filters['batch_id'] != '8803': # 8803 is ALL
            sql += f" AND S.{batch_col} = ?"
            params.append(filters['batch_id'])
            
        sql += " ORDER BY BD.name_of_batch, S.fullname"
        return DB.fetch_all(sql, params)
        return DB.fetch_all(sql, params)
