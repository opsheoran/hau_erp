from app.db import DB
from datetime import datetime, timedelta

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
        conn = DB.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(query, [user_id, ip_address])
            conn.commit()
        except:
            conn.rollback()
        finally:
            conn.close()

class StudentConfigModel:
    @staticmethod
    def get_entitlements():
        return DB.fetch_all("SELECT * FROM SMS_Entitlement_Mst ORDER BY orderno")

    @staticmethod
    def save_entitlement(data):
        if data.get('pk_id'):
            return DB.execute("UPDATE SMS_Entitlement_Mst SET Entitlement_Name=?, orderno=? WHERE pk_entitleid=?",
                            [data['name'], data['order'], data['pk_id']])
        else:
            return DB.execute("INSERT INTO SMS_Entitlement_Mst (Entitlement_Name, orderno) VALUES (?, ?)",
                            [data['name'], data['order']])

    @staticmethod
    def get_ranks():
        return DB.fetch_all("SELECT * FROM SMS_RankMst ORDER BY Rankname")

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
    def get_paper_titles():
        return DB.fetch_all("SELECT * FROM SMS_PaperTitle_Mst ORDER BY rptorder")

    @staticmethod
    def save_paper_title(data):
        if data.get('pk_papertitleid'):
            return DB.execute("UPDATE SMS_PaperTitle_Mst SET papertitle=?, TitleCode=?, rptorder=? WHERE pk_papertitleid=?",
                            [data['name'], data['code'], data['order'], data['pk_papertitleid']])
        else:
            return DB.execute("INSERT INTO SMS_PaperTitle_Mst (papertitle, TitleCode, rptorder) VALUES (?, ?, ?)", 
                            [data['name'], data['code'], data['order']])

    @staticmethod
    def get_courses(filters):
        query = """
            SELECT C.*, D.description as department
            FROM SMS_Course_Mst C
            LEFT JOIN Department_Mst D ON C.fk_Deptid = D.pk_deptid
            WHERE 1=1
        """
        params = []
        if filters.get('dept_id'):
            query += " AND C.fk_Deptid = ?"
            params.append(filters['dept_id'])
        if filters.get('term'):
            query += " AND (C.coursecode LIKE ? OR C.coursename LIKE ?)"
            params.extend([f"%{filters['term']}%", f"%{filters['term']}%"])
        query += " ORDER BY C.coursecode"
        return DB.fetch_all(query, params)

    @staticmethod
    def save_course(data, user_id):
        if data.get('pk_courseid'):
            return DB.execute("""
                UPDATE SMS_Course_Mst SET coursecode=?, coursename=?, fk_Deptid=?, fk_papertitleid=?,
                crhr_theory=?, crhr_practical=?, isNC=?, iselective=?, UpdatedBy=?, UpdatedDate=GETDATE()
                WHERE pk_courseid=?
            """, [data['code'], data['name'], int(data['dept_id']), int(data['title_id'] or 0),
                  data['theory'], data['practical'], data.get('is_nc', 0), data.get('is_elective', 0),
                  user_id, data['pk_courseid']])
        else:
            return DB.execute("""
                INSERT INTO SMS_Course_Mst (coursecode, coursename, fk_Deptid, fk_papertitleid,
                crhr_theory, crhr_practical, isNC, iselective, InsertedBy, InsertedDate)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE())
            """, [data['code'], data['name'], int(data['dept_id']), int(data['title_id'] or 0),
                  data['theory'], data['practical'], data.get('is_nc', 0), data.get('is_elective', 0),
                  user_id])

    @staticmethod
    def get_syllabus(degree_id=None):
        query = "SELECT S.*, D.degreename FROM SMS_syllabusCreation_forCourses_Mst S LEFT JOIN SMS_Degree_Mst D ON S.fk_Degreeid = D.pk_degreeid WHERE 1=1"
        params = []
        if degree_id:
            query += " AND S.fk_Degreeid = ?"
            params.append(degree_id)
        return DB.fetch_all(query, params)

    @staticmethod
    def save_syllabus(data):
        conn = DB.get_connection()
        cursor = conn.cursor()
        try:
            if data.get('pk_id'):
                cursor.execute("UPDATE SMS_syllabusCreation_forCourses_Mst SET fk_Degreeid=?, fromSession=?, toSession=? WHERE pk_syllforCourse=?",
                             [data['degree_id'], data['from_session'], data['to_session'], data['pk_id']])
                syll_id = data['pk_id']
            else:
                cursor.execute("INSERT INTO SMS_syllabusCreation_forCourses_Mst (fk_Degreeid, fromSession, toSession) VALUES (?, ?, ?)",
                             [data['degree_id'], data['from_session'], data['to_session']])
                cursor.execute("SELECT SCOPE_IDENTITY()")
                syll_id = cursor.fetchone()[0]
            conn.commit()
            return syll_id
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def delete_syllabus(id):
        conn = DB.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM SMS_syllabusCreation_forCourses_Trn WHERE fk_syllforCourse=?", [id])
            cursor.execute("DELETE FROM SMS_syllabusCreation_forCourses_Mst WHERE pk_syllforCourse=?", [id])
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

class ActivityCertificateModel:
    @staticmethod
    def get_activities():
        return DB.fetch_all("SELECT * FROM SMS_Activity_Mst ORDER BY Activity_name")

    @staticmethod
    def save_activity(data):
        if data.get('pk_id'):
            return DB.execute("UPDATE SMS_Activity_Mst SET Activity_name=?, Activity_code=?, Remarks=? WHERE PK_Actid=?",
                [data['name'], data['code'], data['remarks'], data['pk_id']])
        else:
            return DB.execute("INSERT INTO SMS_Activity_Mst (Activity_name, Activity_code, Remarks) VALUES (?, ?, ?)",
                [data['name'], data['code'], data['remarks']])

    @staticmethod
    def get_course_activities():
        return DB.fetch_all("SELECT * FROM SMS_CourseActivity_Mst ORDER BY CourseActivity_Order")

    @staticmethod
    def save_course_activity(data):
        if data.get('pk_id'):
            return DB.execute("""
                UPDATE SMS_CourseActivity_Mst SET CourseActivity_Name=?, CourseActivity_Code=?,
                CourseActivity_Order=? WHERE pk_CourseActivityID=?
            """, [data['name'], data['code'], data['order'], data['pk_id']])
        else:
            return DB.execute("""
                INSERT INTO SMS_CourseActivity_Mst (CourseActivity_Name, CourseActivity_Code, CourseActivity_Order)
                VALUES (?, ?, ?)
            """, [data['name'], data['code'], data['order']])

    @staticmethod
    def get_certificates():
        return DB.fetch_all("SELECT * FROM SMS_Certificate_Mst ORDER BY certificatename")

    @staticmethod
    def save_certificate(data):
        if data.get('pk_id'):
            return DB.execute("UPDATE SMS_Certificate_Mst SET certificatename=?, isrequired=? WHERE pk_certificateid=?",
                [data['name'], 1 if data.get('required') else 0, data['pk_id']])
        else:
            return DB.execute("INSERT INTO SMS_Certificate_Mst (certificatename, isrequired) VALUES (?, ?)",
                [data['name'], 1 if data.get('required') else 0])

    @staticmethod
    def get_certificate_batches():
        query = """
        SELECT B.*, C.collegename, D.degreename, S.sessionname
        FROM SMS_Certificate_Batch_Mst B
        INNER JOIN SMS_College_Mst C ON B.fk_collegeid = C.pk_collegeid
        INNER JOIN SMS_Degree_Mst D ON B.fk_degreeid = D.pk_degreeid
        INNER JOIN SMS_AcademicSession_Mst S ON B.fk_sessionid = S.pk_sessionid
        ORDER BY S.sessionorder DESC, C.collegename
        """
        return DB.fetch_all(query)

    @staticmethod
    def save_cert_batch(data):
        if data.get('pk_id'):
            return DB.execute("""
                UPDATE SMS_Certificate_Batch_Mst SET fk_collegeid=?, fk_degreeid=?, fk_sessionid=?,
                no_of_batch=? WHERE pk_cert_batchid=?
            """, [data['college_id'], data['degree_id'], data['session_id'], data['count'], data['pk_id']])
        else:
            return DB.execute("""
                INSERT INTO SMS_Certificate_Batch_Mst (fk_collegeid, fk_degreeid, fk_sessionid, no_of_batch)
                VALUES (?, ?, ?, ?)
            """, [data['college_id'], data['degree_id'], data['session_id'], data['count']])

class ClassificationModel:
    @staticmethod
    def get_degree_types():
        return DB.fetch_all("SELECT pk_degreetypeid as id, degreetype as name, isug, Prefix FROM SMS_DegreeType_Mst ORDER BY degreetype")

    @staticmethod
    def save_degree_type(data):
        isug_val = data.get('isug')
        if data.get('pk_id'):
            return DB.execute("UPDATE SMS_DegreeType_Mst SET degreetype=?, isug=?, Prefix=? WHERE pk_degreetypeid=?",
                            [data['name'], isug_val, data['prefix'], data['pk_id']])
        else:
            return DB.execute("INSERT INTO SMS_DegreeType_Mst (degreetype, isug, Prefix) VALUES (?, ?, ?)",
                            [data['name'], isug_val, data['prefix']])

    @staticmethod
    def delete_degree_type(id):
        return DB.execute("DELETE FROM SMS_DegreeType_Mst WHERE pk_degreetypeid = ?", [id])

    @staticmethod
    def get_categories():
        return DB.fetch_all("SELECT * FROM SMS_Category_Mst ORDER BY category")

    @staticmethod
    def save_category(data):
        if data.get('pk_catid'):
            return DB.execute("UPDATE SMS_Category_Mst SET category=?, Code=? WHERE pk_catid=?", [data['name'], data['code'], data['pk_catid']])
        else:
            return DB.execute("INSERT INTO SMS_Category_Mst (category, Code) VALUES (?, ?)", [data['name'], data['code']])

    @staticmethod
    def get_boards():
        return DB.fetch_all("SELECT * FROM SMS_Board_Mst ORDER BY orderby")

    @staticmethod
    def save_board(data):
        if data.get('pk_boardid'):
            return DB.execute("UPDATE SMS_Board_Mst SET boardname=?, isapproved=?, orderby=? WHERE pk_boardid=?",
                            [data['name'], 1 if data.get('approved') else 0, data['order'], data['pk_boardid']])
        else:
            return DB.execute("INSERT INTO SMS_Board_Mst (boardname, isapproved, orderby) VALUES (?, ?, ?)",
                            [data['name'], 1 if data.get('approved') else 0, data['order']])

    @staticmethod
    def get_nationalities():
        return DB.fetch_all("SELECT * FROM SMS_Nationality_Mst ORDER BY nationality")

    @staticmethod
    def save_nationality(data):
        if data.get('pk_nid'):
            return DB.execute("UPDATE SMS_Nationality_Mst SET nationality=? WHERE pk_nid=?", [data['name'], data['pk_nid']])
        else:
            return DB.execute("INSERT INTO SMS_Nationality_Mst (nationality) VALUES (?)", [data['name']])

    @staticmethod
    def get_college_types():
        return DB.fetch_all("SELECT pk_collegetypeid as id, collegypedesc as name FROM SMS_CollegeTpye_Mst ORDER BY collegypedesc")

    @staticmethod
    def save_college_type(data):
        if data.get('pk_id'):
            return DB.execute("UPDATE SMS_CollegeTpye_Mst SET collegypedesc=?, remarks=? WHERE pk_collegetypeid=?", [data['name'], data['remarks'], data['pk_id']])
        else:
            return DB.execute("INSERT INTO SMS_CollegeTpye_Mst (collegypedesc, remarks) VALUES (?, ?)", [data['name'], data['remarks']])

    @staticmethod
    def get_course_types():
        return DB.fetch_all("SELECT pk_coursetypeid as id, coursetype as name FROM SMS_CourseType_Mst ORDER BY coursetype")

    @staticmethod
    def delete_college_type(id):
        return DB.execute("DELETE FROM SMS_CollegeTpye_Mst WHERE pk_collegetypeid = ?", [id])

    @staticmethod
    def delete_course_type(id):
        return DB.execute("DELETE FROM SMS_CourseType_Mst WHERE pk_coursetypeid = ?", [id])

class InfrastructureModel:
    @staticmethod
    def get_sessions():
        return DB.fetch_all("SELECT pk_sessionid, sessionname, CONVERT(varchar, sessionstart_dt, 23) as sessionstart_dt, CONVERT(varchar, sessionend_dt, 23) as sessionend_dt, isadmissionopen, sessionorder, remarks FROM SMS_AcademicSession_Mst ORDER BY sessionorder DESC")

    @staticmethod
    def save_session(data):
        if data.get('pk_sessionid'):
            return DB.execute("""
                UPDATE SMS_AcademicSession_Mst SET sessionname=?, sessionstart_dt=?, sessionend_dt=?,
                isadmissionopen=?, sessionorder=?, remarks=? WHERE pk_sessionid=?
            """, [data['name'], data['start'], data['end'], 1 if data.get('open') else 0, data['order'], data['remarks'], data['pk_sessionid']])
        else:
            return DB.execute("""
                INSERT INTO SMS_AcademicSession_Mst (sessionname, sessionstart_dt, sessionend_dt, isadmissionopen, sessionorder, remarks)
                VALUES (?, ?, ?, ?, ?, ?)
            """, [data['name'], data['start'], data['end'], 1 if data.get('open') else 0, data['order'], data['remarks']])

    @staticmethod
    def get_semesters():
        return DB.fetch_all("SELECT * FROM SMS_Semester_Mst ORDER BY semesterorder")

    @staticmethod
    def save_semester(data):
        if data.get('pk_semesterid'):
            return DB.execute("""
                UPDATE SMS_Semester_Mst SET semester_roman=?, semester_char=?, semesterorder=?
                WHERE pk_semesterid=?
            """, [data['roman'], data['char'], data['order'], data['pk_semesterid']])
        else:
            return DB.execute("""
                INSERT INTO SMS_Semester_Mst (semester_roman, semester_char, semesterorder)
                VALUES (?, ?, ?)
            """, [data['roman'], data['char'], data['order']])

    @staticmethod
    def get_events():
        return DB.fetch_all("SELECT * FROM SMS_EventCalender_Mst ORDER BY Event_order")

    @staticmethod
    def save_event(data):
        if data.get('pk_eventid'):
            return DB.execute("UPDATE SMS_EventCalender_Mst SET Event_name=?, Event_order=?, Remarks=? WHERE pk_eventid=?",
                            [data['name'], data['order'], data['remarks'], data['pk_eventid']])
        else:
            return DB.execute("INSERT INTO SMS_EventCalender_Mst (Event_name, Event_order, Remarks) VALUES (?, ?, ?)",
                            [data['name'], data['order'], data['remarks']])

    @staticmethod
    def delete_session(id):
        return DB.execute("DELETE FROM SMS_AcademicSession_Mst WHERE pk_sessionid = ?", [id])

    @staticmethod
    def delete_semester(id):
        return DB.execute("DELETE FROM SMS_Semester_Mst WHERE pk_semesterid = ?", [id])

    @staticmethod
    def delete_event(id):
        return DB.execute("DELETE FROM SMS_EventCalender_Mst WHERE pk_eventid = ?", [id])

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
    def get_colleges():
        return DB.fetch_all("SELECT * FROM SMS_College_Mst ORDER BY collegename")

    @staticmethod
    def save_college(data):
        if data.get('pk_collegeid'):
            return DB.execute("""
                UPDATE SMS_College_Mst SET collegename=?, collegecode=?, address=?, contactperson=?, contactno=?,
                emailid=?, websiteaddress=?, fk_locid=?, remarks=?, fk_collegetypeid=?, fk_cityid=? WHERE pk_collegeid=?
            """, [data['collegename'], data['collegecode'], data['address'], data['contactperson'], data['contactno'],
                data['emailid'], data['websiteaddress'], data['loc_id'], data['remarks'], data.get('type_id'), data.get('city_id'), data['pk_collegeid']])
        else:
            return DB.execute("""
                INSERT INTO SMS_College_Mst (collegename, collegecode, address, contactperson, contactno, emailid, websiteaddress, fk_locid, remarks, fk_collegetypeid, fk_cityid)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [data['collegename'], data['collegecode'], data['address'], data['contactperson'], data['contactno'],
                data['emailid'], data['websiteaddress'], data['loc_id'], data['remarks'], data.get('type_id'), data.get('city_id')])

    @staticmethod
    def get_degrees():
        return DB.fetch_all("SELECT D.*, T.degreetype FROM SMS_Degree_Mst D LEFT JOIN SMS_DegreeType_Mst T ON D.fk_degreetypeid = T.pk_degreetypeid ORDER BY D.degreename")

    @staticmethod
    def save_degree(data):
        if data.get('pk_degreeid'):
            return DB.execute("""
                UPDATE SMS_Degree_Mst SET degreename=?, degree_desc=?, degreename_hindi=?, DegreeCode=?, fk_degreetypeid=?,
                minsem=?, maxsem=?, isphd=?, isdepartmentreq=? WHERE pk_degreeid=?
            """, [data['degreename'], data['degree_desc'], data.get('degreename_hindi'), data['degreecode'], data['type_id'],
                data['minsem'], data['maxsem'], 1 if data.get('isphd') else 0, 1 if data.get('deptreq') else 0, data['pk_degreeid']])
        else:
            return DB.execute("""
                INSERT INTO SMS_Degree_Mst (degreename, degree_desc, degreename_hindi, DegreeCode, fk_degreetypeid, minsem, maxsem, isphd, isdepartmentreq)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [data['degreename'], data['degree_desc'], data.get('degreename_hindi'), data['degreecode'], data['type_id'],
                data['minsem'], data['maxsem'], 1 if data.get('isphd') else 0, 1 if data.get('deptreq') else 0])

    @staticmethod
    def get_branches(faculty_id=None):
        query = "SELECT * FROM SMS_BranchMst"
        params = []
        if faculty_id:
            query += " WHERE Fk_Faculty_id = ?"
            params.append(faculty_id)
        query += " ORDER BY Branchname"
        return DB.fetch_all(query, params)

    @staticmethod
    def save_branch(data):
        if data.get('pk_id'):
            return DB.execute("UPDATE SMS_BranchMst SET Branchname=?, alias=?, Branchname_hindi=?, Fk_Faculty_id=?, Isactive=?, Remarks=? WHERE Pk_BranchId=?",
                            [data['branchname'], data['alias'], data['branchname_hindi'], data['faculty_id'], 1 if data.get('active') else 0, data['remarks'], data['pk_id']])  
        else:
            return DB.execute("INSERT INTO SMS_BranchMst (Branchname, alias, Branchname_hindi, Fk_Faculty_id, Isactive, Remarks) VALUES (?, ?, ?, ?, ?, ?)",
                            [data['branchname'], data['alias'], data['branchname_hindi'], data['faculty_id'], 1 if data.get('active') else 0, data['remarks']])

    @staticmethod
    def get_course_activities():
        query = """
            SELECT CA.*, AC.ActivityCategory_Desc
            FROM SMS_CourseActivity_Mst CA
            LEFT JOIN SMS_ActivityCategory_Mst AC ON CA.fk_activityCategory_ID = AC.pk_activityCategory_ID
            ORDER BY CA.CourseActivity_Order
        """
        return DB.fetch_all(query)

    @staticmethod
    def get_activity_categories():
        return DB.fetch_all("SELECT pk_activityCategory_ID, ActivityCategory_Desc FROM SMS_ActivityCategory_Mst ORDER BY ActivityCategory_Desc")

    @staticmethod
    def get_activities():
        return DB.fetch_all("SELECT * FROM SMS_Activity_Mst ORDER BY Activity_name")

    @staticmethod
    def get_college_degree_mappings():
        query = """
        SELECT M.*, C.collegename, D.degreename
        FROM SMS_CollegeDegreeBranchMap_Mst M
        INNER JOIN SMS_College_Mst C ON M.fk_CollegeId = C.pk_collegeid
        INNER JOIN SMS_Degree_Mst D ON M.fk_Degreeid = D.pk_degreeid
        ORDER BY C.collegename, D.degreename
        """
        return DB.fetch_all(query)

    @staticmethod
    def get_mapping_details(map_id):
        return DB.fetch_all("SELECT * FROM SMS_CollegeDegreeBranchMap_Trn WHERE fk_Coldgbrid = ?", [map_id])

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

            if data.get('pk_id'):
                map_id = data['pk_id']
                cursor.execute("UPDATE SMS_CollegeDegreeBranchMap_Mst SET fk_CollegeId=?, fk_Degreeid=?, Remarks=? WHERE PK_Coldgbrid=?",
                             [college_id, degree_id, remarks, map_id])
                cursor.execute("DELETE FROM SMS_CollegeDegreeBranchMap_Trn WHERE fk_Coldgbrid=?", [map_id])
            else:
                cursor.execute("INSERT INTO SMS_CollegeDegreeBranchMap_Mst (fk_CollegeId, fk_Degreeid, Remarks) OUTPUT INSERTED.PK_Coldgbrid VALUES (?, ?, ?)",
                             [college_id, degree_id, remarks])
                map_id = cursor.fetchone()[0]

            for i in range(len(spec_ids)):
                if spec_ids[i]:
                    cursor.execute("INSERT INTO SMS_CollegeDegreeBranchMap_Trn (fk_Coldgbrid, fk_BranchId, SpecializationType, Remarks) VALUES (?, ?, ?, ?)",
                                 [map_id, spec_ids[i], spec_types[i], spec_remarks[i]])
            
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
    def save_degree_year(data):
        if data.get('pk_id'):
            return DB.execute("UPDATE SMS_DegreeYear_Mst SET degreeyear_char=?, degreeyear_int=?, degreeyear_roman=?, dgyearorder=? WHERE pk_degreeyearid=?",
                [data['char'], data['int_val'], data['roman'], data['order'], data['pk_id']])
        else:
            return DB.execute("INSERT INTO SMS_DegreeYear_Mst (degreeyear_char, degreeyear_int, degreeyear_roman, dgyearorder) VALUES (?, ?, ?, ?)",
                [data['char'], data['int_val'], data['roman'], data['order']])

    @staticmethod
    def get_degree_cycles():
        query = """
        SELECT C.*, D.degreename, B.Branchname, Y.degreeyear_char, S.semester_roman
        FROM SMS_DegreeCycle_Mst C
        INNER JOIN SMS_Degree_Mst D ON C.fk_degreeid = D.pk_degreeid
        LEFT JOIN SMS_BranchMst B ON C.fk_branchid = B.Pk_BranchId
        LEFT JOIN SMS_DegreeYear_Mst Y ON C.fk_degreeyearid = Y.pk_degreeyearid
        LEFT JOIN SMS_Semester_Mst S ON C.fk_semesterid = S.pk_semesterid
        ORDER BY D.degreename, Y.dgyearorder, S.semesterorder
        """
        return DB.fetch_all(query)

    @staticmethod
    def save_degree_cycle(data):
        if data.get('pk_degreecycleid'):
            return DB.execute("""
                UPDATE SMS_DegreeCycle_Mst SET fk_degreeid=?, fk_branchid=?, fk_degreeyearid=?,
                fk_semesterid=?, MinOGPA=?, AutoCourseAlloc=? WHERE pk_degreecycleid=?
            """, [data['degree_id'], data.get('branch_id'), data['year_id'], data['sem_id'],
                data.get('min_ogpa'), 1 if data.get('auto_alloc') else 0, data['pk_degreecycleid']])
        else:
            return DB.execute("""
                INSERT INTO SMS_DegreeCycle_Mst (fk_degreeid, fk_branchid, fk_degreeyearid, fk_semesterid, MinOGPA, AutoCourseAlloc)
                VALUES (?, ?, ?, ?, ?, ?)
            """, [data['degree_id'], data.get('branch_id'), data['year_id'], data['sem_id'],
                data.get('min_ogpa'), 1 if data.get('auto_alloc') else 0])

    @staticmethod
    def get_employee_degree_mappings(user_id=None):
        query = """
        SELECT M.*, E.empname, D.degreename 
        FROM SMS_EmployeeDegreeMap M 
        INNER JOIN UM_Users_Mst U ON M.FK_USERID = U.pk_userId
        INNER JOIN SAL_Employee_Mst E ON U.fk_empId = E.pk_empid 
        INNER JOIN SMS_Degree_Mst D ON M.FK_DegreeID = D.pk_degreeid 
        WHERE 1=1
        """
        params = []
        if user_id:
            query += " AND M.FK_USERID = ?"
            params.append(user_id)
        return DB.fetch_all(query, params)

    @staticmethod
    def get_college_degrees(college_id):
        query = """
        SELECT DISTINCT D.pk_degreeid, D.degreename
        FROM SMS_CollegeDegreeBranchMap_Mst M
        INNER JOIN SMS_Degree_Mst D ON M.fk_Degreeid = D.pk_degreeid
        WHERE M.fk_CollegeId = ?
        ORDER BY D.degreename
        """
        return DB.fetch_all(query, [college_id])

    @staticmethod
    def save_employee_degree_mapping(data):
        degree_ids = data.getlist('degree_ids')
        user_id = data.get('user_id')
        college_id = data.get('college_id')
        success = True
        for d_id in degree_ids:
            res = DB.execute("""
                INSERT INTO SMS_EmployeeDegreeMap (FK_USERID, FK_DegreeID, fk_collegeid, createdDate)
                VALUES (?, ?, ?, GETDATE())
            """, [user_id, d_id, college_id])
            if not res: success = False
        return success

    @staticmethod
    def delete_employee_degree_mapping(map_id):
        return DB.execute("DELETE FROM SMS_EmployeeDegreeMap WHERE PK_EmDgMapID = ?", [map_id])

    @staticmethod
    def get_degree_crhr():
        query = """
            SELECT C.*, D.degreename, S.semester_roman
            FROM SMS_Degreewise_crhr_Mst C
            INNER JOIN SMS_Degree_Mst D ON C.fk_degreeid = D.pk_degreeid
            INNER JOIN SMS_Semester_Mst S ON C.fk_semesterid = S.pk_semesterid
            ORDER BY D.degreename, S.semesterorder
        """
        return DB.fetch_all(query)

    @staticmethod
    def save_degree_crhr(data):
        if data.get('pk_crhrid'):
            return DB.execute("""
                UPDATE SMS_Degreewise_crhr_Mst SET fk_degreeid=?, fk_semesterid=?, total_crhr=?, min_crhr=?, max_crhr=?
                WHERE pk_crhrid=?
            """, [data['degree_id'], data['sem_id'], data.get('total_crhr'), data.get('min_crhr'), data.get('max_crhr'), data['pk_crhrid']])
        else:
            return DB.execute("""
                INSERT INTO SMS_Degreewise_crhr_Mst (fk_degreeid, fk_semesterid, total_crhr, min_crhr, max_crhr)
                VALUES (?, ?, ?, ?, ?)
            """, [data['degree_id'], data['sem_id'], data.get('total_crhr'), data.get('min_crhr'), data.get('max_crhr')])

    @staticmethod
    def get_batches():
        query = """
            SELECT B.*, C.collegename, S.sessionname, D.degreename, SEM.semester_roman
            FROM SMS_Batch_Mst B
            INNER JOIN SMS_College_Mst C ON B.fk_collegeid = C.pk_collegeid
            INNER JOIN SMS_AcademicSession_Mst S ON B.fk_sessionid = S.pk_sessionid
            INNER JOIN SMS_Degree_Mst D ON B.fk_degreeid = D.pk_degreeid
            INNER JOIN SMS_Semester_Mst SEM ON B.fk_semesterid = SEM.pk_semesterid
            ORDER BY S.sessionorder DESC, C.collegename
        """
        return DB.fetch_all(query)

    @staticmethod
    def save_batch(data):
        if data.get('pk_batchid'):
            return DB.execute("""
                UPDATE SMS_Batch_Mst SET fk_collegeid=?, fk_sessionid=?, fk_degreeid=?, fk_semesterid=?,
                theory_practical=?, fk_branchid=?, no_of_batches=? WHERE pk_batchid=?
            """, [data['college_id'], data['session_id'], data['degree_id'], data['sem_id'],
                data.get('type'), data.get('branch_id'), data.get('count'), data['pk_batchid']])
        else:
            return DB.execute("""
                INSERT INTO SMS_Batch_Mst (fk_collegeid, fk_sessionid, fk_degreeid, fk_semesterid, theory_practical, fk_branchid, no_of_batches)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, [data['college_id'], data['session_id'], data['degree_id'], data['sem_id'],
                data.get('type'), data.get('branch_id'), data.get('count')])

    @staticmethod
    def get_moderation_marks():
        query = """
            SELECT M.*, D.degreename, S.semester_roman
            FROM SMS_Moderation_Marks_Mst M
            INNER JOIN SMS_Degree_Mst D ON M.fk_degreeid = D.pk_degreeid
            INNER JOIN SMS_Semester_Mst S ON M.fk_semesterid = S.pk_semesterid
            ORDER BY D.degreename, S.semesterorder
        """
        return DB.fetch_all(query)

    @staticmethod
    def save_moderation_marks(data):
        if data.get('pk_id'):
            return DB.execute("""
                UPDATE SMS_Moderation_Marks_Mst SET fk_degreeid=?, fk_semesterid=?, moderation_marks=?
                WHERE pk_moderationid=?
            """, [data['degree_id'], data['sem_id'], data['marks'], data['pk_id']])
        else:
            return DB.execute("""
                INSERT INTO SMS_Moderation_Marks_Mst (fk_degreeid, fk_semesterid, moderation_marks)
                VALUES (?, ?, ?)
            """, [data['degree_id'], data['sem_id'], data['marks']])

    @staticmethod
    def delete_moderation_marks(mod_id):
        return DB.execute("DELETE FROM SMS_Moderation_Marks_Mst WHERE pk_moderationid = ?", [mod_id])

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
        return DB.fetch_all("SELECT pk_deptid, description FROM Department_Mst ORDER BY description")

    @staticmethod
    def get_student_full_details(sid):
        query = "SELECT * FROM SMS_Student_Mst WHERE pk_sid = ?"
        return DB.fetch_one(query, [sid])

    @staticmethod
    def save_student_biodata(data):
        # Implementation depends on form fields
        pass

class HolidayModel:
    @staticmethod
    def get_holiday_types():
        return DB.fetch_all("SELECT pk_holidaytypeid as id, holidaytype as name FROM SAL_HolidayType_Mst ORDER BY holidaytype")

    @staticmethod
    def get_common_holidays():
        query = """
        SELECT C.*, T.holidaytype
        FROM SAL_CommonHolidays_Mst C
        LEFT JOIN SAL_HolidayType_Mst T ON C.fk_holidaytypeid = T.pk_holidaytypeid
        ORDER BY C.displayorder
        """
        return DB.fetch_all(query)

    @staticmethod
    def get_holiday_locations():
        return DB.fetch_all("SELECT * FROM SAL_HolidayLocation_Mst ORDER BY displayorder")

    @staticmethod
    def get_loc_wise_holidays(hloc_id=None, lyear=None, univ_loc_id=None):
        query = """
            SELECT M.pk_locholidayid, M.fk_holidaylocid, M.fk_yearid, M.remarks, M.fk_locid,
                   H.holidayloc, LOC.locname
            FROM SAL_LocationWiseHolidays_Mst M
            INNER JOIN SAL_HolidayLocation_Mst H ON M.fk_holidaylocid = H.pk_holidaylocid
            INNER JOIN Location_Mst LOC ON M.fk_locid = LOC.pk_locid
            WHERE 1=1
        """
        params = []
        # Type safety: hloc_id MUST be an integer
        if hloc_id and str(hloc_id).isdigit():
            query += " AND M.fk_holidaylocid = ?"
            params.append(int(hloc_id))
            
        if lyear:
            query += " AND M.fk_yearid = ?"
            params.append(lyear)
            
        # univ_loc_id is a varchar (e.g. 'VC-3')
        if univ_loc_id:
            query += " AND M.fk_locid = ?"
            params.append(univ_loc_id)
            
        query += " ORDER BY H.displayorder, LOC.locname"
        return DB.fetch_all(query, params)

    @staticmethod
    def get_loc_holiday_details(loc_holiday_id):
        """Fetches holiday transaction details for a location holiday master"""
        if not loc_holiday_id or not str(loc_holiday_id).isdigit():
            return []
            
        query = """
            SELECT T.pk_locholidaytrnid, T.fk_locholidayid, T.fk_commonholidayid, 
                   T.holidaydate, T.todate, T.remarks,
                   C.commonholiday as holiday_name
            FROM SAL_LocationWiseHolidays_Trn T
            LEFT JOIN SAL_CommonHolidays_Mst C ON T.fk_commonholidayid = C.pk_commonholidayid
            WHERE T.fk_locholidayid = ?
            ORDER BY T.holidaydate
        """
        return DB.fetch_all(query, [int(loc_holiday_id)])

    @staticmethod
    def save_common_holiday(data):
        if data.get('id'):
            return DB.execute("UPDATE SAL_CommonHolidays_Mst SET fk_holidaytypeid=?, commonholiday=?, displayorder=?, remarks=?, lastupdateddate=GETDATE() WHERE pk_commonholidayid=?",
                            [data['type_id'], data['name'], data['order'], data['remarks'], data['id']])
        else:
            return DB.execute("INSERT INTO SAL_CommonHolidays_Mst (fk_holidaytypeid, commonholiday, displayorder, remarks, lastupdateddate) VALUES (?, ?, ?, ?, GETDATE())",
                            [data['type_id'], data['name'], data['order'], data['remarks']])

    @staticmethod
    def save_holiday_location(data):
        if data.get('id'):
            return DB.execute("UPDATE SAL_HolidayLocation_Mst SET holidayloc=?, displayorder=?, remarks=?, lastupdateddate=GETDATE() WHERE pk_holidaylocid=?",
                            [data['name'], data['order'], data['remarks'], data['id']])
        else:
            return DB.execute("INSERT INTO SAL_HolidayLocation_Mst (holidayloc, displayorder, remarks, lastupdateddate) VALUES (?, ?, ?, GETDATE())",
                            [data['name'], data['order'], data['remarks']])

    @staticmethod
    def save_loc_wise_holiday(data, user_id):
        conn = DB.get_connection()
        cursor = conn.cursor()
        try:
            hloc_id = int(data['holiday_loc_id'])
            year_id = int(data['year_id'])
            loc_id = data['loc_id'] # This is varchar 'VC-3'
            
            # Check if record already exists for this holiday location and year (Unique constraint prevention)
            cursor.execute("""
                SELECT pk_locholidayid FROM SAL_LocationWiseHolidays_Mst 
                WHERE fk_holidaylocid = ? AND fk_yearid = ? AND fk_locid = ?
            """, [hloc_id, year_id, loc_id])
            existing = cursor.fetchone()
            
            if existing:
                loc_holiday_id = existing[0]
                cursor.execute("""
                    UPDATE SAL_LocationWiseHolidays_Mst 
                    SET remarks=?, fk_updUserID=?, fk_updDateID=GETDATE()
                    WHERE pk_locholidayid=?
                """, [data.get('remarks'), user_id, loc_holiday_id])
            elif data.get('pk_locholidayid') and str(data.get('pk_locholidayid')).strip().isdigit():
                # Direct ID update - only if it's a valid numeric ID
                val_id = int(str(data.get('pk_locholidayid')).strip())
                cursor.execute("""
                    UPDATE SAL_LocationWiseHolidays_Mst 
                    SET fk_holidaylocid=?, fk_yearid=?, fk_locid=?, remarks=?, fk_updUserID=?, fk_updDateID=GETDATE()
                    WHERE pk_locholidayid=?
                """, [hloc_id, year_id, loc_id, data.get('remarks'), user_id, val_id])
                loc_holiday_id = val_id
            else:
                # New Insert
                cursor.execute("""
                    INSERT INTO SAL_LocationWiseHolidays_Mst (fk_holidaylocid, fk_yearid, fk_locid, remarks, fk_insUserID, fk_insDateID, fk_updUserID, fk_updDateID)
                    OUTPUT INSERTED.pk_locholidayid
                    VALUES (?, ?, ?, ?, ?, GETDATE(), ?, GETDATE())
                """, [hloc_id, year_id, loc_id, data.get('remarks'), user_id, user_id])
                res = cursor.fetchone()
                loc_holiday_id = res[0] if res else None
            conn.commit()
            return loc_holiday_id
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def save_loc_holiday_detail(data, user_id):
        if data.get('pk_locholidaytrnid'):
            return DB.execute("""
                UPDATE SAL_LocationWiseHolidays_Trn 
                SET fk_commonholidayid=?, holidaydate=?, todate=?, remarks=?, fk_updUserID=?, fk_updDateID=GETDATE()
                WHERE pk_locholidaytrnid=?
            """, [data['common_holiday_id'], data['holiday_date'], data.get('to_date'), data.get('remarks'), user_id, data['pk_locholidaytrnid']])
        else:
            return DB.execute("""
                INSERT INTO SAL_LocationWiseHolidays_Trn (fk_locholidayid, fk_commonholidayid, holidaydate, todate, remarks, fk_updUserID, fk_updDateID)
                VALUES (?, ?, ?, ?, ?, ?, GETDATE())
            """, [data['loc_holiday_id'], data['common_holiday_id'], data['holiday_date'], data.get('to_date'), data.get('remarks'), user_id])

    @staticmethod
    def delete_loc_holiday_detail(trn_id):
        return DB.execute("DELETE FROM SAL_LocationWiseHolidays_Trn WHERE pk_locholidaytrnid = ?", [trn_id])

class LeaveEncashmentModel:
    @staticmethod
    def get_encashment_history(emp_id):
        query = """
        SELECT E.*, L.leavetype
        FROM SAL_Leave_Encashment_Trn E
        INNER JOIN SAL_Leavetype_Mst L ON E.fk_leaveid = L.pk_leaveid
        WHERE E.fk_empid = ?
        ORDER BY E.encashdate DESC
        """
        return DB.fetch_all(query, [emp_id])

    @staticmethod
    def apply_encashment(data, user_id):
        conn = DB.get_connection()
        cursor = conn.cursor()
        now = datetime.now()
        try:
            cursor.execute("""
                INSERT INTO SAL_Leave_Encashment_Trn (
                    fk_empid, fk_leaveid, encashedleaves, BasicPay, totalamount, NetPayment, 
                    encashdate, remarks, fk_insUserID, fk_insDateID, fk_updUserID, fk_updDateID,
                    fk_monthid, fk_yearid
                ) VALUES (?, ?, ?, ?, ?, ?, GETDATE(), ?, ?, GETDATE(), ?, GETDATE(), ?, ?)
            """, [data['emp_id'], data['leave_id'], data['days'], data['basic'], data['amount'], data['amount'], 
                  data['remarks'], user_id, user_id, now.month, now.year])
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

class LeaveReportModel:
    @staticmethod
    def get_leave_transactions(filters):
        query = """
        SELECT T.pk_leavetakenid, E.empname, E.empcode, L.leavetype,
        T.fromdate, T.todate, T.totalleavedays, T.remarks,
        D.Description as DDO, DEPT.description as Dept
        FROM SAL_LeavesTaken_Mst T
        INNER JOIN SAL_Employee_Mst E ON T.fk_empid = E.pk_empid
        INNER JOIN SAL_Leavetype_Mst L ON T.fk_leaveid = L.pk_leaveid
        LEFT JOIN DDO_Mst D ON E.fk_ddoid = D.pk_ddoid
        LEFT JOIN Department_Mst DEPT ON E.fk_deptid = DEPT.pk_deptid
        WHERE 1=1
        """
        params = []
        if filters.get('from_date'):
            query += " AND T.fromdate >= ?"
            params.append(filters['from_date'])
        if filters.get('to_date'):
            query += " AND T.todate <= ?"
            params.append(filters['to_date'])
        if filters.get('emp_id'):
            query += " AND T.fk_empid = ?"
            params.append(filters['emp_id'])
        if filters.get('leave_id'):
            query += " AND T.fk_leaveid = ?"
            params.append(filters['leave_id'])
        if filters.get('ddo_id'):
            query += " AND E.fk_ddoid = ?"
            params.append(filters['ddo_id'])
        query += " ORDER BY T.fromdate DESC"
        return DB.fetch_all(query, params)

    @staticmethod
    def get_el_reconciliation(emp_id=None, lyear=None):
        query = """
            SELECT EL.*, E.empname, E.empcode 
            FROM SAL_ELReconcilliation_Mst EL
            INNER JOIN SAL_Employee_Mst E ON EL.fk_empid = E.pk_empid
            WHERE 1=1
        """
        params = []
        if emp_id:
            query += " AND EL.fk_empid = ?"
            params.append(emp_id)
        if lyear:
            query += " AND EL.Lyear = ?"
            params.append(lyear)
        query += " ORDER BY E.empname, EL.sno_for_emp"
        return DB.fetch_all(query, params)

    @staticmethod
    def update_el_balance(emp_id, user_id):
        conn = DB.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT TOP 1 sno_for_emp, leaveto_date, el_balance FROM SAL_EarnedLeave_Details WHERE fk_empid = ? ORDER BY sno_for_emp DESC", [emp_id])
            last = cursor.fetchone()
            last_sno = last.sno_for_emp if last else 0
            last_date = last.leaveto_date if last else datetime(2000, 1, 1)
            prev_balance = float(last.el_balance) if last else 0.0
            new_sno = last_sno + 1
            cursor.execute("""
                INSERT INTO SAL_EarnedLeave_Details (fk_empid, sno_for_emp, leavefrom_date, leaveto_date, el_balance, fk_insUserID, fk_insDateID)
                VALUES (?, ?, ?, GETDATE(), ?, ?, GETDATE())
            """, [emp_id, new_sno, last_date, prev_balance + 15, user_id])
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

class NavModel:
    @staticmethod
    def get_assigned_locations(user_id):
        query = """
        SELECT DISTINCT L.pk_locid as id, L.locname as name
        FROM UM_UserModuleDetails UD
        INNER JOIN Location_Mst L ON UD.fk_locid = L.pk_locid
        WHERE UD.fk_userId = ?
        ORDER BY L.locname
        """
        return DB.fetch_all(query, [str(user_id)])

    @staticmethod
    def get_user_modules(user_id, loc_id):
        query = """
        SELECT DISTINCT M.pk_moduleId, M.modulename, M.remarks as moduledescription
        FROM UM_Module_Mst M
        INNER JOIN UM_UserModuleDetails UD ON M.pk_moduleId = UD.fk_moduleId
        INNER JOIN UM_UserPageRights UP ON UD.pk_usermoddetailId = UP.fk_usermoddetailId
        WHERE UD.fk_userId = ? AND UD.fk_locid = ? 
        AND CAST(UP.AllowView AS VARCHAR) IN ('1', 'Y', 'True')
        ORDER BY M.modulename
        """
        return DB.fetch_all(query, [str(user_id), str(loc_id)])

    @staticmethod
    def get_all_fin_years():
        """Fetches all financial years formatted as '2026'"""
        return DB.fetch_all("SELECT pk_finid as id, Lyear as name FROM SAL_Financial_Year ORDER BY Lyear DESC")

    @staticmethod
    def get_years():
        """Returns distinct Lyear values for selection"""
        return DB.fetch_all("SELECT DISTINCT Lyear as id, CAST(Lyear as varchar) as name FROM SAL_Financial_Year ORDER BY Lyear DESC")

    @staticmethod
    def get_current_fin_year():
        """Fetches the active financial year details"""
        query = "SELECT TOP 1 pk_finid, Lyear, date1, date2 FROM SAL_Financial_Year WHERE active = 'Y' ORDER BY orderno DESC"
        res = DB.fetch_one(query)
        if not res:
            curr_yr = datetime.now().year
            return {'pk_finid': 'CO-18', 'Lyear': curr_yr, 'date1': datetime(curr_yr, 4, 1), 'date2': datetime(curr_yr+1, 3, 31)}
        return res

    @staticmethod
    def get_user_page_rights(user_id, loc_id):
        loc_id = str(loc_id)
        query = """
        SELECT 
        M.modulename,
        M.pk_moduleId as fk_moduleId,
        W.pk_webpageId,
        LTRIM(RTRIM(W.menucaption)) as PageName,
        W.parentId,
        ISNULL(MAX(CASE WHEN CAST(UP.AllowView AS VARCHAR) IN ('1', 'Y', 'True') THEN 1 ELSE 0 END), 0) as AllowView,
        ISNULL(MAX(CASE WHEN CAST(UP.AllowAdd AS VARCHAR) IN ('1', 'Y', 'True') THEN 1 ELSE 0 END), 0) as AllowAdd,
        ISNULL(MAX(CASE WHEN CAST(UP.AllowUpdate AS VARCHAR) IN ('1', 'Y', 'True') THEN 1 ELSE 0 END), 0) as AllowUpdate,
        ISNULL(MAX(CASE WHEN CAST(UP.AllowDelete AS VARCHAR) IN ('1', 'Y', 'True') THEN 1 ELSE 0 END), 0) as AllowDelete
        FROM UM_UserPageRights UP
        INNER JOIN UM_UserModuleDetails UD ON UP.fk_usermoddetailId = UD.pk_usermoddetailId
        INNER JOIN UM_WebPage_Mst W ON UP.fk_webpageId = W.pk_webpageId
        INNER JOIN UM_Module_Mst M ON W.fk_moduleId = M.pk_moduleId
        WHERE UD.fk_userId = ? AND UD.fk_locid = ?
        GROUP BY M.modulename, M.pk_moduleId, W.pk_webpageId, W.menucaption, W.parentId
        """
        return DB.fetch_all(query, [str(user_id), loc_id])

    @staticmethod
    def check_permission(user_id, loc_id, page_caption):
        loc_id = str(loc_id)
        query = """
        SELECT TOP 1 
        CASE WHEN CAST(UP.AllowView AS VARCHAR) IN ('1', 'Y', 'True') THEN 1 ELSE 0 END as AllowView,
        CASE WHEN CAST(UP.AllowAdd AS VARCHAR) IN ('1', 'Y', 'True') THEN 1 ELSE 0 END as AllowAdd,
        CASE WHEN CAST(UP.AllowUpdate AS VARCHAR) IN ('1', 'Y', 'True') THEN 1 ELSE 0 END as AllowUpdate,
        CASE WHEN CAST(UP.AllowDelete AS VARCHAR) IN ('1', 'Y', 'True') THEN 1 ELSE 0 END as AllowDelete
        FROM UM_UserPageRights UP
        INNER JOIN UM_UserModuleDetails UD ON UP.fk_usermoddetailId = UD.pk_usermoddetailId
        INNER JOIN UM_WebPage_Mst W ON UP.fk_webpageId = W.pk_webpageId
        WHERE UD.fk_userId = ? AND UD.fk_locid = ? AND LTRIM(RTRIM(W.menucaption)) = ?
        """
        return DB.fetch_one(query, [str(user_id), loc_id, page_caption])

    @staticmethod
    def get_natures():
        return DB.fetch_all("SELECT pk_natureid as id, nature as name FROM SAL_Nature_Mst ORDER BY nature")

class LeaveConfigModel:
    @staticmethod
    def get_leave_types_full():
        return DB.fetch_all("SELECT pk_leaveid, leavetype, shortdesc, leavenature, gender, remarks FROM SAL_Leavetype_Mst ORDER BY leavetype")

    @staticmethod
    def get_leave_type_details(leave_id):
        query = """
        SELECT D.*, N.nature
        FROM SAL_Leavetype_Details D
        INNER JOIN SAL_Nature_Mst N ON D.fk_natureid = N.pk_natureid
        WHERE D.fk_leaveid = ?
        """
        return DB.fetch_all(query, [leave_id])

    @staticmethod
    def save_leave_type(data, user_id):
        conn = DB.get_connection()
        cursor = conn.cursor()
        try:
            if data.get('pk_leaveid'):
                cursor.execute("""
                    UPDATE SAL_Leavetype_Mst SET shortdesc=?, leavenature=?, gender=?, remarks=?, fk_updUserID=?, fk_updDateID=GETDATE()
                    WHERE pk_leaveid=?
                """, [data['short'], data['nature'], data['gender'], data['remarks'], user_id, data['pk_leaveid']])
            else:
                cursor.execute("INSERT INTO SAL_Leavetype_Mst (leavetype, shortdesc, leavenature, gender, remarks, fk_updUserID, fk_updDateID) VALUES (?, ?, ?, ?, ?, ?, GETDATE())",
                             [data['name'], data['short'], data['nature'], data['gender'], data['remarks'], user_id])
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def get_approvers():
        """Fetches list of all employees who can be approvers"""
        return DB.fetch_all("SELECT pk_empid as id, empname + ' | ' + empcode as name FROM SAL_Employee_Mst WHERE employeeleftstatus='N' ORDER BY empname")

    @staticmethod
    def update_workflow(emp_id, approver_id, user_id):
        return DB.execute("UPDATE SAL_Employee_Mst SET reportingto = ?, fk_updUserID = ?, fk_updDateID = GETDATE() WHERE pk_empid = ?", [approver_id, user_id, emp_id])

class LeaveModel:
    @staticmethod
    def get_leave_types(is_admin=False):
        # Only 4 leave types: Casual (9), Duty (41), Earned (2), Restricted Holiday (7)
        query = "SELECT pk_leaveid as id, leavetype as name FROM SAL_Leavetype_Mst WHERE pk_leaveid IN (9, 41, 2, 7) ORDER BY CASE pk_leaveid WHEN 9 THEN 1 WHEN 41 THEN 2 WHEN 2 THEN 3 WHEN 7 THEN 4 END"
        return DB.fetch_all(query)

    @staticmethod
    def get_employee_full_details(emp_id):
        query = """
        SELECT E.*, D.designation, DEPT.description as department, L.locname as collegename
        FROM SAL_Employee_Mst E
        LEFT JOIN SAL_Designation_Mst D ON E.fk_desgid = D.pk_desgid
        LEFT JOIN Department_Mst DEPT ON E.fk_deptid = DEPT.pk_deptid
        LEFT JOIN Location_Mst L ON E.fk_locid = L.pk_locid
        WHERE E.pk_empid = ?
        """
        return DB.fetch_one(query, [emp_id])

    @staticmethod
    def get_recommended_for(emp_id):
        query = """
        SELECT R.pk_leavereqid as id, E.empname as EmployeeName, L.leavetype as LeaveType,
        CONVERT(varchar, R.fromdate, 103) as FromDate, CONVERT(varchar, R.todate, 103) as ToDate,
        R.totalleavedays as Days, R.reasonforleave as Reason, R.contactno as Contact,
        '' as Comment
        FROM SAL_Leave_Request_Mst R
        INNER JOIN SAL_Employee_Mst E ON R.fk_reqempid = E.pk_empid
        INNER JOIN SAL_Leavetype_Mst L ON R.fk_leaveid = L.pk_leaveid
        WHERE (R.recommendEmpCode = ? OR R.recommendEmpCode2 = ? OR R.recommendEmpCode3 = ?)
        AND R.leavestatus = 'S' AND R.iscancelled = 'N'
        """
        return DB.fetch_all(query, [emp_id, emp_id, emp_id])

    @staticmethod
    def get_leave_summary(emp_id):
        # Simply reuse get_leave_balance to ensure 100% consistency
        return LeaveModel.get_leave_balance(emp_id)

    @staticmethod
    def save_leave_request(data, user_id):
        conn = DB.get_connection()
        cursor = conn.cursor()
        try:
            sql = """
            INSERT INTO SAL_Leave_Request_Mst (
                fk_requesterid, fk_reqempid, reqdate, fk_leaveid, fromdate, todate,
                totaldays, totalleavedays, reasonforleave, contactno, issubmit, submitdate,
                iscancelled, fk_reportingto, leavestatus, fk_insUserID, fk_insDateID,
                fk_locid, recommendEmpCode, recommendEmpCode2, recommendEmpCode3,
                Stationfromdate, Stationtodate, HPLWMed, HPLFStd,
                addInstitution, letterno, letterDate, Prefix, Suffix,
                fk_updUserID, fk_updDateID, Extend_pk_leavereqid, CommutedLeave, StartTime
            ) 
            OUTPUT INSERTED.pk_leavereqid
            VALUES (?, ?, GETDATE(), ?, ?, ?, ?, ?, ?, ?, 'Y', GETDATE(), 'N', ?, 'S', ?, GETDATE(), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE(), ?, ?, ?)
            """
            s_from = data.get('station_from') if data.get('station_from') else None
            s_to = data.get('station_to') if data.get('station_to') else None
            params = [
                user_id, data['emp_id'], data['leave_id'], data['from_date'], data['to_date'],
                data['total_days'], data['leave_days'], data['reason'], data['contact'],
                data['reporting_to'], user_id, data['loc_id'],
                data.get('rec1'), data.get('rec2'), data.get('rec3'),
                s_from, s_to,
                1 if data.get('is_medical') else 0,
                1 if data.get('is_study') else 0,
                data.get('add_inst'), data.get('letter_no'), data.get('letter_date'),
                data.get('prefix'), data.get('suffix'),
                user_id, data.get('extend_id'),
                1 if data.get('is_commuted') else 0,
                data.get('req_time')
            ]
            cursor.execute(sql, params)
            res = cursor.fetchone()
            req_id = res[0] if res else None
            conn.commit()
            return req_id
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def get_leave_balance(emp_id):
        """Fetches leave balance with real-time sync from Assignment and Balance tables for HAU ERP"""
        fy = NavModel.get_current_fin_year()
        lyear = fy.get('Lyear')
        # Params: 1 (Availed) + 1 (Adjusted) + 1 (Applied - emp_id) + 2 (Applied Dates) + 1 (Join B) + 1 (Join LA) + 1 (LYear) = 8
        sql_params = [emp_id, emp_id, emp_id, fy['date1'], fy['date2'], emp_id, emp_id, lyear]
        
        query = """
        SELECT L.leavetype, L.pk_leaveid,
               CASE 
                 WHEN L.pk_leaveid = 2 THEN (ISNULL(B.currentyearleaves, 0) + ISNULL(B.totalleavesearned, 0))
                 ELSE ISNULL(LA.leaveassigned, ISNULL(B.currentyearleaves, 0))
               END as total,
               dbo.SAL_FN_GetAvailedLeave(?, L.pk_leaveid) as availed,
               dbo.SAL_FN_GetAdjustedLeave(?, L.pk_leaveid) as adjusted,
               ISNULL((SELECT SUM(totalleavedays) FROM SAL_Leave_Request_Mst 
                       WHERE fk_reqempid = ? AND fk_leaveid = L.pk_leaveid 
                       AND leavestatus = 'S' AND iscancelled = 'N' AND fromdate BETWEEN ? AND ?), 0) as applied
        FROM SAL_Leavetype_Mst L
        LEFT JOIN SAL_EmployeeLeave_Details B ON L.pk_leaveid = B.fk_leaveid AND B.fk_empid = ?
        LEFT JOIN SAL_LeaveAssignment_Details LA ON L.pk_leaveid = LA.fk_leaveid AND LA.fk_empid = ? AND LA.fk_yearid = ?
        WHERE L.pk_leaveid IN (9, 41, 2, 7) -- Casual, Duty, Earned, RH
        ORDER BY CASE L.pk_leaveid 
            WHEN 9 THEN 1 -- Casual
            WHEN 41 THEN 2 -- Duty
            WHEN 2 THEN 3 -- Earned
            WHEN 7 THEN 4 -- RH
            END
        """
        res = DB.fetch_all(query, sql_params)
        for r in res:
            total = float(r.get('total') or 0)
            availed = float(r.get('availed') or 0)
            adjusted = float(r.get('adjusted') or 0)
            applied = float(r.get('applied') or 0)
            
            r['total'] = total
            r['availed'] = availed
            r['adjusted'] = adjusted
            r['balance'] = total - availed
            r['applied'] = applied
            r['applied_balance'] = r['balance'] - applied
            
        return res

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
            query_dept = "SELECT Hod_Id FROM Department_Mst WHERE pk_deptid = ?"
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

        # Priority 2: Check Controlling Officer
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
    def calculate_days(from_date, to_date, loc_id, is_short=False):
        if is_short: return 0.33
        try:
            d1 = datetime.strptime(from_date, '%Y-%m-%d')
            d2 = datetime.strptime(to_date, '%Y-%m-%d')
            days = (d2 - d1).days + 1
            return max(1, days)
        except:
            return 0

    @staticmethod
    def get_user_leaves(user_id, page=1, per_page=10):
        fy = NavModel.get_current_fin_year()
        d1, d2 = fy['date1'], fy['date2']
        offset = (page - 1) * per_page
        count_query = "SELECT COUNT(*) FROM SAL_Leave_Request_Mst WHERE fk_requesterid = ? AND fromdate BETWEEN ? AND ?"
        total = DB.fetch_scalar(count_query, [user_id, d1, d2])
        query = f"""
        SELECT 
        R.pk_leavereqid as RequestID, L.leavetype as LeaveType,
        CONVERT(varchar, R.fromdate, 103) as FromDate, CONVERT(varchar, R.todate, 103) as ToDate,
        R.totalleavedays as Days,
        CASE
            WHEN R.leavestatus = 'A' THEN 'Approved'
            WHEN R.leavestatus = 'R' THEN 'Rejected'
            WHEN R.leavestatus = 'C' THEN 'Cancelled'
            WHEN R.leavestatus = 'S' THEN 'Submitted'
            ELSE 'Pending'
        END as Status,
        R.reasonforleave as Reason,
        CONVERT(varchar, R.reqdate, 103) as RequestDate,
        R.StartTime as RequestTime,
        REP.empname as ReportingTo,
        CONVERT(varchar, R.Stationfromdate, 103) as SFrom,
        CONVERT(varchar, R.Stationtodate, 103) as STo
        FROM SAL_Leave_Request_Mst R
        LEFT JOIN SAL_Leavetype_Mst L ON R.fk_leaveid = L.pk_leaveid
        LEFT JOIN SAL_Employee_Mst REP ON R.fk_reportingto = REP.pk_empid
        WHERE R.fk_requesterid = ? AND R.fromdate BETWEEN ? AND ?
        ORDER BY R.reqdate DESC
        OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY
        """
        data = DB.fetch_all(query, [user_id, d1, d2])
        return data, total

    @staticmethod
    def get_request_details(req_id):
        query = """
        SELECT R.*, L.leavetype as LeaveTypeName, E.empname as RequesterName, E.empcode as RequesterCode,
        REP.empname as ReportingName, REP.empcode as ReportingCode
        FROM SAL_Leave_Request_Mst R
        INNER JOIN SAL_Leavetype_Mst L ON R.fk_leaveid = L.pk_leaveid
        INNER JOIN SAL_Employee_Mst E ON R.fk_reqempid = E.pk_empid
        INNER JOIN SAL_Employee_Mst REP ON R.fk_reportingto = REP.pk_empid
        WHERE R.pk_leavereqid = ?
        """
        mst = DB.fetch_one(query, [req_id])
        return {'master': mst} if mst else None

    @staticmethod
    def create_leave_request(data, user_id, emp_id, loc_id):
        conn = DB.get_connection()
        cursor = conn.cursor()
        try:
            s_from = data.get('station_from') if data.get('station_from') else None
            s_to = data.get('station_to') if data.get('station_to') else None
            sql = """
            INSERT INTO SAL_Leave_Request_Mst (
                fk_requesterid, fk_reqempid, reqdate, fk_leaveid, fromdate, todate,
                totaldays, totalleavedays, reasonforleave, contactno, issubmit, submitdate,
                iscancelled, fk_reportingto, leavestatus, fk_insUserID, fk_insDateID,
                fk_locid, recommendEmpCode, recommendEmpCode2, recommendEmpCode3,
                Stationfromdate, Stationtodate, HPLWMed, HPLFStd
            ) VALUES (?, ?, GETDATE(), ?, ?, ?, ?, ?, ?, ?, 'Y', GETDATE(), 'N', ?, 'S', ?, GETDATE(), ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = [
                user_id, emp_id, data['leave_id'], data['from_date'], data['to_date'],
                data['total_days'], data['leave_days'], data['reason'], data['contact'],
                data['reporting_to'], user_id, loc_id,
                data.get('rec1'), data.get('rec2'), data.get('rec3'),
                s_from, s_to,
                'Y' if data.get('is_medical') else 'N',
                'Y' if data.get('is_study') else 'N'
            ]
            cursor.execute(sql, params)
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def get_pending_approvals(emp_id):
        fy = NavModel.get_current_fin_year()
        d1, d2 = fy['date1'], fy['date2']
        query = """
        SELECT R.pk_leavereqid as RequestID, E.empname as EmployeeName, E.empcode, L.leavetype as LeaveType, 
        CONVERT(varchar, R.reqdate, 103) as RequestDate, CONVERT(varchar, R.reqdate, 108) as RequestTime,
        CONVERT(varchar, R.fromdate, 103) as FromDate, CONVERT(varchar, R.todate, 103) as ToDate,
        CONVERT(varchar, R.Stationfromdate, 103) as SFrom, CONVERT(varchar, R.Stationtodate, 103) as STo,
        R.totalleavedays as Days, R.reasonforleave as Reason, R.contactno, R.leavestatus
        FROM SAL_Leave_Request_Mst R
        INNER JOIN SAL_Employee_Mst E ON R.fk_reqempid = E.pk_empid
        INNER JOIN SAL_Leavetype_Mst L ON R.fk_leaveid = L.pk_leaveid
        WHERE R.fk_reportingto = ? AND R.leavestatus = 'S' AND R.fromdate BETWEEN ? AND ?
        ORDER BY R.reqdate DESC
        """
        return DB.fetch_all(query, [emp_id, d1, d2])

    @staticmethod
    def take_action(req_id, status, user_id, emp_id, comments=""):
        conn = DB.get_connection()
        cursor = conn.cursor()
        try:
            # 1. Fetch and Verify (IDOR prevention)
            cursor.execute("""
                SELECT fk_reqempid, fk_leaveid, totalleavedays, fk_locid, fromdate, todate,
                reasonforleave, HPLWMed
                FROM SAL_Leave_Request_Mst 
                WHERE pk_leavereqid = ? AND fk_reportingto = ?
            """, [req_id, emp_id])
            req = cursor.fetchone()
            if not req: return False
            
            # 2. Update Status
            cursor.execute("""
                UPDATE SAL_Leave_Request_Mst 
                SET leavestatus = ?, responsedate = GETDATE(), fk_responseby = ?,
                    fk_updUserID = ?, fk_updDateID = GETDATE()
                WHERE pk_leavereqid = ?
            """, [status, user_id, user_id, req_id])
            if status == 'A':
                fy = NavModel.get_current_fin_year()
                lyear = fy['Lyear']
                fin_id = fy['pk_finid']
                
                cursor.execute("""
                    UPDATE SAL_LeaveAssignment_Details 
                    SET leaveavailed = ISNULL(leaveavailed, 0) + ?,
                        fk_updUserID = ?, fk_updDateID = GETDATE()
                    WHERE fk_empid = ? AND fk_leaveid = ? AND fk_yearid = ?
                """, [req.totalleavedays, user_id, req.fk_reqempid, req.fk_leaveid, lyear])
                
                taken_id = f"LT-{req_id}"
                cursor.execute("""
                    INSERT INTO SAL_LeavesTaken_Mst (
                        pk_leavetakenid, fk_leavereqid, fk_empid, fk_leaveid, fromdate, todate, 
                        totalleavedays, leavetaken, remarks, fk_finid,
                        fk_insUserID, fk_insDateID, fk_updUserID, fk_updDateID,
                        HPLWMed
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE(), ?, GETDATE(), ?)
                """, [taken_id, req_id, req.fk_reqempid, req.fk_leaveid, req.fromdate, req.todate, 
                      req.totalleavedays, req.totalleavedays, req.reasonforleave, fin_id,
                      user_id, user_id, 1 if req.HPLWMed else 0])
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def get_approved_recent(emp_id, page=1, per_page=10):
        fy = NavModel.get_current_fin_year()
        d1, d2 = fy['date1'], fy['date2']
        offset = (page - 1) * per_page
        count_query = "SELECT COUNT(*) FROM SAL_Leave_Request_Mst WHERE fk_reportingto = ? AND leavestatus IN ('A', 'R') AND fromdate BETWEEN ? AND ?"
        total = DB.fetch_scalar(count_query, [emp_id, d1, d2])
        query = f"""
        SELECT R.pk_leavereqid as RequestID, E.empname as EmployeeName, E.empcode, L.leavetype as LeaveType,
        CONVERT(varchar, R.reqdate, 103) as RequestDate,
        CONVERT(varchar, R.reqdate, 108) as RequestTime,
        CONVERT(varchar, R.fromdate, 103) as FromDate, CONVERT(varchar, R.todate, 103) as ToDate,
        R.totalleavedays as Days, CASE WHEN R.leavestatus = 'A' THEN 'Approved' ELSE 'Rejected' END as Status,
        CONVERT(varchar, R.responsedate, 103) as ApprovedDate
        FROM SAL_Leave_Request_Mst R
        INNER JOIN SAL_Employee_Mst E ON R.fk_reqempid = E.pk_empid
        INNER JOIN SAL_Leavetype_Mst L ON R.fk_leaveid = L.pk_leaveid
        WHERE R.fk_reportingto = ? AND R.leavestatus IN ('A', 'R') AND R.fromdate BETWEEN ? AND ?
        ORDER BY R.responsedate DESC
        OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY
        """
        data = DB.fetch_all(query, [emp_id, d1, d2])
        return data, total

    @staticmethod
    def get_leaves_taken(emp_id, page=1, per_page=10):
        offset = (page - 1) * per_page
        count_query = "SELECT COUNT(*) FROM SAL_LeavesTaken_Mst WHERE fk_empid = ?"
        total = DB.fetch_scalar(count_query, [emp_id])
        
        query = f"""
        SELECT T.pk_leavetakenid, T.fk_leavereqid, L.leavetype,
        CONVERT(varchar, T.reqdate, 103) as RequestDate,
        CONVERT(varchar, T.fromdate, 103) as FromDate,
        CONVERT(varchar, T.todate, 103) as ToDate,
        T.totalleavedays as Days
        FROM SAL_LeavesTaken_Mst T
        INNER JOIN SAL_Leavetype_Mst L ON T.fk_leaveid = L.pk_leaveid
        WHERE T.fk_empid = ?
        ORDER BY T.fromdate DESC
        OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY
        """
        data = DB.fetch_all(query, [emp_id])
        return data, total

    @staticmethod
    def get_approved_leaves_for_adj(emp_id):
        """Fetches approved leaves that can be adjusted/cancelled"""
        query = """
        SELECT R.pk_leavereqid as id, L.leavetype + ' | ' + CONVERT(varchar, R.fromdate, 103) + ' | ' + CONVERT(varchar, R.todate, 103) as name,
        R.fromdate, R.todate, R.totalleavedays, R.fk_reportingto, REP.empname as ReportingName,
        T.pk_leavetakenid
        FROM SAL_Leave_Request_Mst R
        INNER JOIN SAL_Leavetype_Mst L ON R.fk_leaveid = L.pk_leaveid
        LEFT JOIN SAL_Employee_Mst REP ON R.fk_reportingto = REP.pk_empid
        LEFT JOIN SAL_LeavesTaken_Mst T ON R.pk_leavereqid = T.fk_leavereqid
        WHERE R.fk_reqempid = ? AND R.leavestatus = 'A' AND R.iscancelled = 'N'
        ORDER BY R.fromdate DESC
        """
        return DB.fetch_all(query, [emp_id])

    @staticmethod
    def create_adj_request(data, emp_id, user_id, loc_id):
        conn = DB.get_connection()
        cursor = conn.cursor()
        try:
            query_ro = """
                SELECT R.fk_reportingto, T.fk_leavereqid
                FROM SAL_LeavesTaken_Mst T
                INNER JOIN SAL_Leave_Request_Mst R ON T.fk_leavereqid = R.pk_leavereqid
                WHERE T.pk_leavetakenid = ?
            """
            cursor.execute(query_ro, [data['leave_id']])
            taken = cursor.fetchone()
            if not taken: return False
            sql = """
                INSERT INTO SAL_LeaveAdjustmentRequest_Mst (
                    fk_reqempid, fk_leavetakenid, fk_leavereqid, adjreqdate, totaladjleave,
                    issubmit, submitdate, iscancelled, fk_reportingto, leaveadjstatus,
                    remarks, fk_insUserID, fk_insDateID, fk_updUserID, fk_updDateID, fk_locid,
                    IsCancel
                ) VALUES (?, ?, ?, GETDATE(), ?, 'Y', GETDATE(), 'N', ?, 'S', ?, ?, GETDATE(), ?, GETDATE(), ?, 0)
            """
            cursor.execute(sql, [
                emp_id, data['leave_id'], taken.fk_leavereqid, data['adj_days'],
                taken.fk_reportingto, data['remarks'], user_id, user_id, loc_id
            ])
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def get_adj_requests(emp_id, page=1, per_page=10):
        offset = (page - 1) * per_page
        count_query = "SELECT COUNT(*) FROM SAL_LeaveAdjustmentRequest_Mst WHERE fk_reqempid = ? AND ISNULL(IsCancel, 0) = 0"
        total = DB.fetch_scalar(count_query, [emp_id])
        query = f"""
        SELECT M.pk_leaveadjreqid as RequestID, L.leavetype as LeaveType,
        CONVERT(varchar, M.adjreqdate, 103) as RequestDate,
        CONVERT(varchar, T.fromdate, 103) as FromDate,
        CONVERT(varchar, T.todate, 103) as ToDate,
        M.totaladjleave as Days,
        CASE WHEN M.leaveadjstatus = 'A' THEN 'Approved'
        WHEN M.leaveadjstatus = 'R' THEN 'Rejected'
        ELSE 'Pending' END as Status
        FROM SAL_LeaveAdjustmentRequest_Mst M
        INNER JOIN SAL_LeavesTaken_Mst T ON M.fk_leavetakenid = T.pk_leavetakenid
        INNER JOIN SAL_Leavetype_Mst L ON T.fk_leaveid = L.pk_leaveid
        WHERE M.fk_reqempid = ? AND ISNULL(M.IsCancel, 0) = 0
        ORDER BY M.adjreqdate DESC
        OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY
        """
        data = DB.fetch_all(query, [emp_id])
        return data, total

    @staticmethod
    def create_cancel_request(data, emp_id, user_id, loc_id):
        conn = DB.get_connection()
        cursor = conn.cursor()
        try:
            query_ro = """
                SELECT R.fk_reportingto, T.fk_leavereqid
                FROM SAL_LeavesTaken_Mst T
                INNER JOIN SAL_Leave_Request_Mst R ON T.fk_leavereqid = R.pk_leavereqid
                WHERE T.pk_leavetakenid = ?
            """
            cursor.execute(query_ro, [data['leave_id']])
            taken = cursor.fetchone()
            if not taken: return False
            sql = """
                INSERT INTO SAL_LeaveAdjustmentRequest_Mst (
                    fk_reqempid, fk_leavetakenid, fk_leavereqid, adjreqdate,
                    issubmit, submitdate, iscancelled, fk_reportingto, leaveadjstatus,
                    remarks, fk_insUserID, fk_insDateID, fk_updUserID, fk_updDateID, fk_locid,
                    IsCancel
                ) VALUES (?, ?, ?, GETDATE(), 'Y', GETDATE(), 'N', ?, 'S', ?, ?, GETDATE(), ?, GETDATE(), ?, 1)
            """
            cursor.execute(sql, [
                emp_id, data['leave_id'], taken.fk_leavereqid,
                taken.fk_reportingto, data['remarks'], user_id, user_id, loc_id
            ])
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def get_cancel_requests(emp_id, page=1, per_page=10):
        offset = (page - 1) * per_page
        count_query = "SELECT COUNT(*) FROM SAL_LeaveAdjustmentRequest_Mst WHERE fk_reqempid = ? AND IsCancel = 1"
        total = DB.fetch_scalar(count_query, [emp_id])
        query = f"""
        SELECT M.pk_leaveadjreqid as RequestID, L.leavetype as LeaveType,
        CONVERT(varchar, M.adjreqdate, 103) as RequestDate,
        CONVERT(varchar, T.fromdate, 103) as FromDate,
        CONVERT(varchar, T.todate, 103) as ToDate,
        M.totaladjleave as Days,
        CASE WHEN M.leaveadjstatus = 'A' THEN 'Approved'
        WHEN M.leaveadjstatus = 'R' THEN 'Rejected'
        ELSE 'Pending' END as Status
        FROM SAL_LeaveAdjustmentRequest_Mst M
        INNER JOIN SAL_LeavesTaken_Mst T ON M.fk_leavetakenid = T.pk_leavetakenid
        INNER JOIN SAL_Leavetype_Mst L ON T.fk_leaveid = L.pk_leaveid
        WHERE M.fk_reqempid = ? AND M.IsCancel = 1
        ORDER BY M.adjreqdate DESC
        OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY
        """
        data = DB.fetch_all(query, [emp_id])
        return data, total

    @staticmethod
    def get_pending_cancel_approvals(emp_id):
        fy = NavModel.get_current_fin_year()
        d1, d2 = fy['date1'], fy['date2']
        query = """
        SELECT A.pk_leaveadjreqid as adj_id, E.empname, E.empcode, L.leavetype, 
        CONVERT(varchar, A.adjreqdate, 103) as RequestDate, A.totaladjleave as Days,
        CONVERT(varchar, T.fromdate, 103) as FromDate, CONVERT(varchar, T.todate, 103) as ToDate,
        T.totalleavedays as totaldays, A.leaveadjstatus, A.remarks, T.contactno,
        E.pk_empid as requester_empid
        FROM SAL_LeaveAdjustmentRequest_Mst A
        INNER JOIN SAL_Employee_Mst E ON A.fk_reqempid = E.pk_empid
        INNER JOIN SAL_LeavesTaken_Mst T ON A.fk_leavetakenid = T.pk_leavetakenid
        INNER JOIN SAL_Leavetype_Mst L ON T.fk_leaveid = L.pk_leaveid
        WHERE A.fk_reportingto = ? AND A.leaveadjstatus = 'S' AND A.IsCancel = 1
        AND T.fromdate BETWEEN ? AND ?
        """
        return DB.fetch_all(query, [emp_id, d1, d2])

    @staticmethod
    def take_cancel_action(adj_id, status, user_id, emp_id, comments=""):
        conn = DB.get_connection()
        cursor = conn.cursor()
        try:
            # 1. Verify (IDOR prevention)
            exists = DB.fetch_one("SELECT pk_leaveadjreqid FROM SAL_LeaveAdjustmentRequest_Mst WHERE pk_leaveadjreqid = ? AND fk_reportingto = ?", [adj_id, emp_id])
            if not exists: return False

            cursor.execute("""
                UPDATE SAL_LeaveAdjustmentRequest_Mst 
                SET leaveadjstatus = ?, fk_responseby = ?, responsedate = GETDATE(), remarks = ?,
                    fk_updUserID = ?, fk_updDateID = GETDATE()
                WHERE pk_leaveadjreqid = ?
            """, [status, user_id, comments, user_id, adj_id])
            if status == 'A':
                cursor.execute("SELECT fk_leavetakenid, totaladjleave, fk_reqempid FROM SAL_LeaveAdjustmentRequest_Mst WHERE pk_leaveadjreqid = ?", [adj_id])
                adj = cursor.fetchone()
                cursor.execute("SELECT fk_leaveid, leavetaken, fk_leavereqid FROM SAL_LeavesTaken_Mst WHERE pk_leavetakenid = ?", [adj.fk_leavetakenid])
                taken = cursor.fetchone()
                cursor.execute("""
                    UPDATE SAL_EmployeeLeave_Details 
                    SET leaveavailed = leaveavailed - ?,
                        fk_updUserID = ?, fk_updDateID = GETDATE()
                    WHERE fk_empid = ? AND fk_leaveid = ?
                """, [taken.leavetaken, user_id, adj.fk_reqempid, taken.fk_leaveid])
                cursor.execute("DELETE FROM SAL_LeavesTaken_Details WHERE fk_leavetakenid = ?", [adj.fk_leavetakenid])
                cursor.execute("DELETE FROM SAL_LeavesTaken_Mst WHERE pk_leavetakenid = ?", [adj.fk_leavetakenid])
                cursor.execute("UPDATE SAL_Leave_Request_Mst SET iscancelled = 'Y', leavestatus = 'C' WHERE pk_leavereqid = ?", [taken.fk_leavereqid])
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def get_pending_adj_approvals(emp_id):
        fy = NavModel.get_current_fin_year()
        d1, d2 = fy['date1'], fy['date2']
        query = """
        SELECT A.pk_leaveadjreqid as adj_id, E.empname, E.empcode, L.leavetype, 
        CONVERT(varchar, A.adjreqdate, 103) as RequestDate, A.totaladjleave as Days,
        CONVERT(varchar, T.fromdate, 103) as FromDate, CONVERT(varchar, T.todate, 103) as ToDate
        FROM SAL_LeaveAdjustmentRequest_Mst A
        INNER JOIN SAL_Employee_Mst E ON A.fk_reqempid = E.pk_empid
        INNER JOIN SAL_LeavesTaken_Mst T ON A.fk_leavetakenid = T.pk_leavetakenid
        INNER JOIN SAL_Leavetype_Mst L ON T.fk_leaveid = L.pk_leaveid
        WHERE A.fk_reportingto = ? AND A.leaveadjstatus = 'S' AND ISNULL(A.IsCancel, 0) = 0
        AND T.fromdate BETWEEN ? AND ?
        """
        return DB.fetch_all(query, [emp_id, d1, d2])

    @staticmethod
    def take_adj_action(adj_id, status, user_id, emp_id, comments=""):
        conn = DB.get_connection()
        cursor = conn.cursor()
        try:
            # 1. Verify (IDOR prevention)
            exists = DB.fetch_one("SELECT pk_leaveadjreqid FROM SAL_LeaveAdjustmentRequest_Mst WHERE pk_leaveadjreqid = ? AND fk_reportingto = ?", [adj_id, emp_id])
            if not exists: return False

            cursor.execute("""
                UPDATE SAL_LeaveAdjustmentRequest_Mst 
                SET leaveadjstatus = ?, fk_responseby = ?, responsedate = GETDATE(), remarks = ?,
                    fk_updUserID = ?, fk_updDateID = GETDATE()
                WHERE pk_leaveadjreqid = ?
            """, [status, user_id, comments, user_id, adj_id])
            if status == 'A':
                cursor.execute("SELECT fk_leavetakenid, totaladjleave, fk_reqempid FROM SAL_LeaveAdjustmentRequest_Mst WHERE pk_leaveadjreqid = ?", [adj_id])
                adj = cursor.fetchone()
                cursor.execute("SELECT fk_leaveid, totalleavedays FROM SAL_LeavesTaken_Mst WHERE pk_leavetakenid = ?", [adj.fk_leavetakenid])
                taken = cursor.fetchone()
                diff = float(adj.totaladjleave) - float(taken.totalleavedays)
                fy = NavModel.get_current_fin_year()
                lyear = fy['Lyear']
                cursor.execute("""
                    UPDATE SAL_LeaveAssignment_Details 
                    SET leaveavailed = ISNULL(leaveavailed, 0) + ?,
                        fk_updUserID = ?, fk_updDateID = GETDATE()
                    WHERE fk_empid = ? AND fk_leaveid = ? AND fk_yearid = ?
                """, [diff, user_id, adj.fk_reqempid, taken.fk_leaveid, lyear])
                cursor.execute("""
                    UPDATE SAL_LeavesTaken_Mst 
                    SET totalleavedays = ?, leavetaken = ?,
                        fk_updUserID = ?, fk_updDateID = GETDATE()
                    WHERE pk_leavetakenid = ?
                """, [adj.totaladjleave, adj.totaladjleave, user_id, adj.fk_leavetakenid])
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def get_adj_approval_history(emp_id, page=1, per_page=10):
        offset = (page - 1) * per_page
        count_query = "SELECT COUNT(*) FROM SAL_LeaveAdjustmentRequest_Mst WHERE fk_reportingto = ? AND leaveadjstatus IN ('A','R') AND ISNULL(IsCancel, 0) = 0"
        total = DB.fetch_scalar(count_query, [emp_id])
        query = f"""
        SELECT A.*, E.empname, L.leavetype,
        CONVERT(varchar, A.adjreqdate, 103) as adjreqdate_fmt,
        CONVERT(varchar, A.responsedate, 103) as responsedate_fmt
        FROM SAL_LeaveAdjustmentRequest_Mst A
        INNER JOIN SAL_Employee_Mst E ON A.fk_reqempid = E.pk_empid
        INNER JOIN SAL_LeavesTaken_Mst T ON A.fk_leavetakenid = T.pk_leavetakenid
        INNER JOIN SAL_Leavetype_Mst L ON T.fk_leaveid = L.pk_leaveid
        WHERE A.fk_reportingto = ? AND A.leaveadjstatus IN ('A','R') AND ISNULL(A.IsCancel, 0) = 0 
        ORDER BY A.responsedate DESC
        OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY
        """
        data = DB.fetch_all(query, [emp_id])
        return data, total

    @staticmethod
    def get_cancel_approval_history(emp_id, page=1, per_page=10):
        offset = (page - 1) * per_page
        count_query = "SELECT COUNT(*) FROM SAL_LeaveAdjustmentRequest_Mst WHERE fk_reportingto = ? AND leaveadjstatus IN ('A','R') AND IsCancel = 1"
        total = DB.fetch_scalar(count_query, [emp_id])
        query = f"""
        SELECT A.*, E.empname, L.leavetype,
        CONVERT(varchar, A.adjreqdate, 103) as adjreqdate_fmt,
        CONVERT(varchar, A.responsedate, 103) as responsedate_fmt
        FROM SAL_LeaveAdjustmentRequest_Mst A
        INNER JOIN SAL_Employee_Mst E ON A.fk_reqempid = E.pk_empid
        INNER JOIN SAL_LeavesTaken_Mst T ON A.fk_leavetakenid = T.pk_leavetakenid
        INNER JOIN SAL_Leavetype_Mst L ON T.fk_leaveid = L.pk_leaveid
        WHERE A.fk_reportingto = ? AND A.leaveadjstatus IN ('A','R') AND A.IsCancel = 1
        ORDER BY A.responsedate DESC
        OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY
        """
        data = DB.fetch_all(query, [emp_id])
        return data, total

    @staticmethod
    def get_leave_daywise_details_by_taken_id(taken_id):
        query = """
            SELECT CONVERT(varchar, D.dated, 103) as leavedate, 
            DATENAME(dw, D.dated) as day_name, 
            L.leavetype as LeaveType
            FROM SAL_LeavesTaken_Details D
            INNER JOIN SAL_LeavesTaken_Mst T ON D.fk_leavetakenid = T.pk_leavetakenid
            INNER JOIN SAL_Leavetype_Mst L ON T.fk_leaveid = L.pk_leaveid
            WHERE D.fk_leavetakenid = ?
        """
        res = DB.fetch_all(query, [taken_id])
        if not res:
            query_fallback = """
                SELECT CONVERT(varchar, D.leavedate, 103) as leavedate,
                DATENAME(dw, D.leavedate) as day_name,
                L.leavetype as LeaveType
                FROM SAL_Leave_Request_Dtls D
                INNER JOIN SAL_LeavesTaken_Mst T ON D.fk_leavereqid = T.fk_leavereqid
                INNER JOIN SAL_Leavetype_Mst L ON T.fk_leaveid = L.pk_leaveid
                WHERE T.pk_leavetakenid = ?
            """
            res = DB.fetch_all(query_fallback, [taken_id])
        return res

    @staticmethod
    def get_approved_leaves_pending_joining(emp_id):
        """Fetches approved leaves where joining is not yet submitted - Only for Earned Leave (2)"""
        query = """
        SELECT R.pk_leavereqid as RequestID, L.leavetype as LeaveType,
        CONVERT(varchar, R.fromdate, 103) as FromDate, CONVERT(varchar, R.todate, 103) as ToDate,
        R.totalleavedays as Days, R.reasonforleave as Reason
        FROM SAL_Leave_Request_Mst R
        INNER JOIN SAL_Leavetype_Mst L ON R.fk_leaveid = L.pk_leaveid
        WHERE R.fk_reqempid = ? AND R.leavestatus = 'A' 
        AND R.JoiningDate IS NULL AND R.iscancelled = 'N'
        AND R.fk_leaveid = 2
        ORDER BY R.fromdate DESC
        """
        return DB.fetch_all(query, [emp_id])

    @staticmethod
    def submit_joining_date(req_id, joining_date, joining_remark, user_id):
        sql = """
        UPDATE SAL_Leave_Request_Mst 
        SET JoiningDate = ?, JoiningRemark = ?, fk_updUserID = ?, responsedate = GETDATE()
        WHERE pk_leavereqid = ?
        """
        return DB.execute(sql, [joining_date, joining_remark, user_id, req_id])

    @staticmethod
    def get_joining_history(emp_id, page=1, per_page=10):
        offset = (page - 1) * per_page
        count_query = "SELECT COUNT(*) FROM SAL_Leave_Request_Mst WHERE fk_reqempid = ? AND JoiningDate IS NOT NULL"
        total = DB.fetch_scalar(count_query, [emp_id])
        query = f"""
            SELECT pk_leavereqid as RequestID, 
            CONVERT(varchar, fromdate, 103) as FromDate, 
            CONVERT(varchar, todate, 103) as ToDate,
            totalleavedays as Days, 
            CONVERT(varchar, JoiningDate, 103) as JoinedOn, 
            JoiningRemark
            FROM SAL_Leave_Request_Mst 
            WHERE fk_reqempid = ? AND JoiningDate IS NOT NULL
            ORDER BY JoiningDate DESC
            OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY
        """
        data = DB.fetch_all(query, [emp_id])
        for d in data:
            d['JoiningDate_fmt'] = d['JoinedOn']
        return data, total

    @staticmethod
    def get_ro_joining_status(ro_emp_id, page=1, per_page=10):
        """Fetches joining records of subordinates for a Reporting Officer"""
        offset = (page - 1) * per_page
        excluded_leaves = ("'Casual Leave'", "'Restricted Holiday'", "'Station Leave'", "'Duty Leave'")
        where_clause = f"R.fk_reportingto = ? AND R.leavestatus = 'A' AND L.leavetype NOT IN ({','.join(excluded_leaves)})"
        count_query = f"SELECT COUNT(*) FROM SAL_Leave_Request_Mst R INNER JOIN SAL_Leavetype_Mst L ON R.fk_leaveid = L.pk_leaveid WHERE {where_clause}"
        total = DB.fetch_scalar(count_query, [ro_emp_id])
        query = f"""
        SELECT E.empname as EmployeeName, L.leavetype as LeaveType,
        CONVERT(varchar, R.reqdate, 103) as RequestedDate,
        CONVERT(varchar, R.fromdate, 103) as FromDate,
        CONVERT(varchar, R.todate, 103) as ToDate,
        R.totalleavedays, R.contactno,
        CONVERT(varchar, R.JoiningDate, 103) as JoiningDate,
        R.JoiningRemark
        FROM SAL_Leave_Request_Mst R
        INNER JOIN SAL_Employee_Mst E ON R.fk_reqempid = E.pk_empid
        INNER JOIN SAL_Leavetype_Mst L ON R.fk_leaveid = L.pk_leaveid
        WHERE {where_clause}
        ORDER BY R.fromdate DESC
        OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY
        """
        data = DB.fetch_all(query, [ro_emp_id])
        return data, total

    @staticmethod
    def get_approved_leaves_pending_departure(emp_id):
        """Fetches approved leaves where departure is not yet submitted - Only for Earned Leave (2)"""
        query = """
        SELECT R.pk_leavereqid as RequestID, L.leavetype as LeaveType,
        CONVERT(varchar, R.fromdate, 103) as FromDate, CONVERT(varchar, R.todate, 103) as ToDate,
        R.totalleavedays as Days, R.reasonforleave as Reason
        FROM SAL_Leave_Request_Mst R
        INNER JOIN SAL_Leavetype_Mst L ON R.fk_leaveid = L.pk_leaveid
        WHERE R.fk_reqempid = ? AND R.leavestatus = 'A' 
        AND R.DepartureDate IS NULL AND R.iscancelled = 'N'
        AND R.fk_leaveid = 2
        ORDER BY R.fromdate DESC
        """
        return DB.fetch_all(query, [emp_id])

    @staticmethod
    def submit_departure_date(req_id, departure_date, departure_remark, user_id):
        sql = """
        UPDATE SAL_Leave_Request_Mst 
        SET DepartureDate = ?, DepartureRemarks = ?, fk_updUserID = ?, responsedate = GETDATE()
        WHERE pk_leavereqid = ?
        """
        return DB.execute(sql, [departure_date, departure_remark, user_id, req_id])

    @staticmethod
    def get_departure_history(emp_id, page=1, per_page=10):
        offset = (page - 1) * per_page
        count_query = "SELECT COUNT(*) FROM SAL_Leave_Request_Mst WHERE fk_reqempid = ? AND DepartureDate IS NOT NULL AND fk_leaveid = 2"
        total = DB.fetch_scalar(count_query, [emp_id])
        query = f"""
        SELECT R.pk_leavereqid as RequestID, L.leavetype as LeaveType,
        E.empname as EmployeeName, R.totalleavedays, R.contactno,
        CONVERT(varchar, R.reqdate, 103) as RequestedDate,
        CONVERT(varchar, R.fromdate, 103) as FromDate, CONVERT(varchar, R.todate, 103) as ToDate,
        CONVERT(varchar, R.DepartureDate, 103) as DepartureOn, R.DepartureRemarks
        FROM SAL_Leave_Request_Mst R
        INNER JOIN SAL_Leavetype_Mst L ON R.fk_leaveid = L.pk_leaveid
        INNER JOIN SAL_Employee_Mst E ON R.fk_reqempid = E.pk_empid
        WHERE R.fk_reqempid = ? AND R.DepartureDate IS NOT NULL AND R.fk_leaveid = 2
        ORDER BY R.DepartureDate DESC
        OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY
        """
        data = DB.fetch_all(query, [emp_id])
        return data, total

    @staticmethod
    def get_ro_departure_list(ro_emp_id, page=1, per_page=10):
        """Fetches approved leaves of subordinates for Departure Admin view"""
        offset = (page - 1) * per_page
        excluded_leaves = ("'Casual Leave'", "'Restricted Holiday'", "'Station Leave'", "'Duty Leave'")
        where_clause = f"R.fk_reportingto = ? AND R.leavestatus = 'A' AND L.leavetype NOT IN ({','.join(excluded_leaves)})"
        count_query = f"SELECT COUNT(*) FROM SAL_Leave_Request_Mst R INNER JOIN SAL_Leavetype_Mst L ON R.fk_leaveid = L.pk_leaveid WHERE {where_clause}"
        total = DB.fetch_scalar(count_query, [ro_emp_id])
        query = f"""
        SELECT R.pk_leavereqid as RequestID, E.empname as EmployeeName, L.leavetype as LeaveType,
        CONVERT(varchar, R.reqdate, 103) as RequestedDate,
        CONVERT(varchar, R.fromdate, 103) as FromDate,
        CONVERT(varchar, R.todate, 103) as ToDate,
        R.totalleavedays, R.contactno, R.leavestatus
        FROM SAL_Leave_Request_Mst R
        INNER JOIN SAL_Employee_Mst E ON R.fk_reqempid = E.pk_empid
        INNER JOIN SAL_Leavetype_Mst L ON R.fk_leaveid = L.pk_leaveid
        WHERE {where_clause}
        ORDER BY R.fromdate DESC
        OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY
        """
        data = DB.fetch_all(query, [ro_emp_id])
        return data, total

    @staticmethod
    def submit_departure_details(req_id, departure_date, period, remark, user_id):
        dt = departure_date
        if period == 'AN':
            dt = departure_date + " 13:00:00"
        else:
            dt = departure_date + " 09:00:00"
        sql = "UPDATE SAL_Leave_Request_Mst SET DepartureDate = ?, DepartureRemarks = ?, fk_updUserID = ? WHERE pk_leavereqid = ?"
        return DB.execute(sql, [dt, remark, user_id, req_id])

class LoanModel:
    @staticmethod
    def get_employee_loan_details(emp_id):
        """Fetches employee details required for the loan apply form"""
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
        """Fetches loan types from SAL_Head_Mst"""
        query = "SELECT pk_headid as id, description FROM SAL_Head_Mst WHERE description LIKE '%Loan%' OR description LIKE '%Advance%' ORDER BY description"
        return DB.fetch_all(query)

    @staticmethod
    def get_loan_natures():
        """Fetches loan natures (Refundable/Non-Refundable)"""
        return DB.fetch_all("SELECT pk_lnatureid as id, loanNature as name FROM SAL_LoanNature_Mst")

    @staticmethod
    def get_loan_purposes(nature_id=None):
        query = "SELECT pk_lpurposeid as id, purpose as name FROM Acct_LoanPurpose_Mst"
        params = []
        if nature_id:
            query += " WHERE fk_lnatureid = ?"
            params.append(nature_id)
        return DB.fetch_all(query, params)

    @staticmethod
    def apply_loan(data, emp_id, user_id):
        conn = DB.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT TOP 1 pk_applyid FROM SAL_LoanApply_Mst ORDER BY LEN(pk_applyid) DESC, pk_applyid DESC")
            last_id = cursor.fetchval()
            prefix = last_id[:2] if last_id else 'AL'
            num = int(last_id[3:]) + 1 if last_id and '-' in last_id else 1
            new_id = f"{prefix}-{num}"
            sql = """
                INSERT INTO SAL_LoanApply_Mst (
                    pk_applyid, applyno, fk_empid, applydate, fk_loantypeid, loanamount,
                    reasonforloan, status, iscancelled, fk_insUserID, fk_insDateID, fk_ddoid, fk_locid
                ) VALUES (?, ?, ?, GETDATE(), ?, ?, ?, 'S', 'N', ?, GETDATE(), ?, ?)
            """
            cursor.execute(sql, [
                new_id, f"LN-{new_id}", emp_id, data['loan_type'], data['amount'],
                data['reason'], user_id, data['ddo_id'], data['loc_id']
            ])
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def get_loan_history(emp_id):
        query = """
        SELECT A.pk_applyid, H.description as LoanType, A.amount, CONVERT(varchar, A.dated, 103) as ApplyDate,
        N.loanNature, A.LoanPurpose, A.remarks
        FROM SAL_LoanApply_Mst A
        INNER JOIN SAL_Head_Mst H ON A.fk_headid = H.pk_headid
        LEFT JOIN SAL_LoanNature_Mst N ON A.fk_lnatureid = N.pk_lnatureid
        WHERE A.fk_empid = ?
        ORDER BY A.dated DESC
        """
        return DB.fetch_all(query, [emp_id])

    @staticmethod
    def delete_loan(apply_id, emp_id):
        """Deletes a loan application record if it belongs to the employee"""
        return DB.execute("DELETE FROM SAL_LoanApply_Mst WHERE pk_applyid = ? AND fk_empid = ?", [apply_id, emp_id])

    @staticmethod
    def get_loan_application(apply_id):
        """Fetches a single loan application detail"""
        return DB.fetch_one("SELECT * FROM SAL_LoanApply_Mst WHERE pk_applyid = ?", [apply_id])

class IncomeTaxModel:
    @staticmethod
    def get_sections():
        """Fetches all parent tax sections"""
        return DB.fetch_all("SELECT * FROM SAL_Sections_Mst WHERE active = 1 ORDER BY orderby")

    @staticmethod
    def get_subsections(sec_id=None):
        query = "SELECT * FROM SAL_SubSections_Mst WHERE active = 1"
        params = []
        if sec_id:
            query += " AND fk_secid = ?"
            params.append(sec_id)
        return DB.fetch_all(query, params)

    @staticmethod
    def get_employee_declarations(emp_id, fin_id):
        """Fetches employee's submitted declarations for a FY"""
        query = """
        SELECT S.description as section_name, SS.description as sub_section_name,
        D.docsub_Amt, D.Actual_Amount, D.pk_docid, D.fk_subsecid, D.fk_secid
        FROM SAL_Employee_SectionDocStatus D
        INNER JOIN SAL_Sections_Mst S ON D.fk_secid = S.pk_secid
        INNER JOIN SAL_SubSections_Mst SS ON D.fk_subsecid = SS.pk_subsecid
        WHERE D.fk_empid = ? AND D.fk_finid = ?
        """
        return DB.fetch_all(query, [emp_id, fin_id])

    @staticmethod
    def save_declaration(data, emp_id, fin_id, user_id):
        conn = DB.get_connection()
        cursor = conn.cursor()
        try:
            for item in data:
                exists = DB.fetch_one("SELECT pk_docid FROM SAL_Employee_SectionDocStatus WHERE fk_empid=? AND fk_finid=? AND fk_subsecid=?",
                                    [emp_id, fin_id, item['subsec_id']])
                if exists:
                    cursor.execute("UPDATE SAL_Employee_SectionDocStatus SET docsub_Amt = ?, fk_updUserID = ?, submitdate = GETDATE() WHERE pk_docid = ?",
                                 [item['amount'], user_id, exists.pk_docid])
                else:
                    cursor.execute("INSERT INTO SAL_Employee_SectionDocStatus (fk_empid, fk_finid, fk_secid, fk_subsecid, docsub_Amt, fk_insUserID, submitdate) VALUES (?, ?, ?, ?, ?, ?, GETDATE())",
                                 [emp_id, fin_id, item['sec_id'], item['subsec_id'], item['amount'], user_id])
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

class EmployeePortalModel:
    @staticmethod
    def get_full_profile(empid):
        basic = DB.fetch_one("""
        SELECT E.*, O.*, D.designation, DP.description as department, N.nature as nature_type,
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
        LEFT JOIN SAL_Designation_Mst D ON E.fk_desgid = D.pk_desgid
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
    def get_all_ddos():
        return DB.fetch_all("SELECT pk_ddoid as id, Description as name FROM DDO_Mst ORDER BY Description")

    @staticmethod
    def get_all_departments():
        return DB.fetch_all("SELECT pk_deptid as id, description as name FROM Department_Mst ORDER BY description")

    @staticmethod
    def get_all_designations():
        return DB.fetch_all("SELECT pk_desgid as id, designation as name FROM SAL_Designation_Mst ORDER BY designation")

    @staticmethod
    def search_employees(term):
        """Original simple term-based employee search"""
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
        statement = DB.fetch_all("""
        SELECT S.*,
        (SELECT ISNULL(SUM(paid_amount),0) FROM SAL_SalaryHead_Details WHERE fk_salid = S.pk_salid AND fk_headid = 1) as basic_pay,
        (SELECT ISNULL(SUM(paid_amount),0) FROM SAL_SalaryHead_Details WHERE fk_salid = S.pk_salid AND fk_headid = 3) as da,
        (SELECT ISNULL(SUM(paid_amount),0) FROM SAL_SalaryHead_Details WHERE fk_salid = S.pk_salid AND fk_headid = 4) as hra,
        (SELECT ISNULL(SUM(paid_amount),0) FROM SAL_SalaryHead_Details WHERE fk_salid = S.pk_salid AND fk_headid = 77) as fma,
        (SELECT ISNULL(SUM(paid_amount),0) FROM SAL_SalaryHead_Details WHERE fk_salid = S.pk_salid AND fk_headid = 130) as it_paid,
        (SELECT ISNULL(SUM(paid_amount),0) FROM SAL_SalaryHead_Details WHERE fk_salid = S.pk_salid AND fk_headid = 89) as gpf_sub,
        (SELECT ISNULL(SUM(paid_amount),0) FROM SAL_SalaryHead_Details WHERE fk_salid = S.pk_salid AND fk_headid = 15) as gslis
        FROM SAL_Salary_Master S
        WHERE S.fk_empid = ? AND S.fk_finid = ?
        ORDER BY S.fk_yearId, S.fk_monthId
        """, [emp_id, fin_id])
        return {'statement': statement} if statement else None

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
        DB.execute("DELETE FROM SAL_Employee_IT_Declaration WHERE fk_empid=? AND fk_finid=?", [emp_id, fin_id])
        return DB.execute("INSERT INTO SAL_Employee_IT_Declaration (fk_empid, fk_finid, GrossSal, StandardDed, TotalTaxableIncome, TotalTax, Regime, fk_insUserID, fk_insDateID) VALUES (?, ?, ?, ?, ?, ?, ?, ?, GETDATE())", [emp_id, fin_id, data['GrossSal'], data['StandardDed'], data['TotalTaxableIncome'], data['TotalTax'], data['Regime'], user_id])

    @staticmethod
    def get_it_computation_data(emp_id, fin_id):
        return DB.fetch_one("SELECT * FROM SAL_Employee_IT_Declaration WHERE fk_empid = ? AND finid = ?", [emp_id, fin_id])

    @staticmethod
    def get_form16_quarterly_summary(emp_id, fin_id):
        return []

    @staticmethod
    def get_form16_tds_details(emp_id, fin_id):
        return []

    @staticmethod
    def amount_to_words(amt):
        return "Zero"

class LeaveAssignmentModel:
    @staticmethod
    def _resolve_year(fid):
        if not fid: return datetime.now().year
        try:
            return int(fid)
        except:
            res = DB.fetch_scalar("SELECT Lyear FROM SAL_Financial_Year WHERE pk_finid = ?", [fid])
            return int(res) if res else datetime.now().year

    @staticmethod
    def get_unassigned_employees(lid, fid, ddo, loc, dept, eid):
        year = LeaveAssignmentModel._resolve_year(fid)
        query = """
        SELECT E.pk_empid, E.empname, E.manualempcode, D.designation, N.nature, CO.description
        FROM SAL_Employee_Mst E
        LEFT JOIN SAL_Designation_Mst D ON E.fk_desgid = D.pk_desgid
        LEFT JOIN SAL_Nature_Mst N ON E.fk_natureid = N.pk_natureid
        LEFT JOIN Sal_ControllingOffice_Mst CO ON E.fk_controllingid = CO.pk_Controllid
        WHERE E.employeeleftstatus = 'N'
        AND E.pk_empid NOT IN (
            SELECT fk_empid FROM SAL_LeaveAssignment_Details WHERE fk_leaveid = ? AND fk_yearid = ?
        )
        """
        params = [lid, year]
        if ddo:
            query += " AND E.fk_ddoid = ?"
            params.append(ddo)
        if loc:
            query += " AND E.fk_locid = ?"
            params.append(loc)
        if dept:
            query += " AND E.fk_deptid = ?"
            params.append(dept)
        if eid:
            query += " AND E.pk_empid = ?"
            params.append(eid)
        return DB.fetch_all(query + " ORDER BY E.empname", params)

    @staticmethod
    def get_assigned_employees(lid, fid, ddo, loc, dept, eid):
        year = LeaveAssignmentModel._resolve_year(fid)
        query = """
        SELECT E.pk_empid, E.empname, E.manualempcode, D.designation, LA.leaveassigned,
        CASE WHEN B.pk_assignid IS NOT NULL AND B.currentyearleaves = LA.leaveassigned THEN 1 ELSE 0 END as is_processed,
        CO.description
        FROM SAL_Employee_Mst E
        INNER JOIN SAL_LeaveAssignment_Details LA ON E.pk_empid = LA.fk_empid
        LEFT JOIN SAL_EmployeeLeave_Details B ON E.pk_empid = B.fk_empid AND LA.fk_leaveid = B.fk_leaveid
        LEFT JOIN SAL_Designation_Mst D ON E.fk_desgid = D.pk_desgid
        LEFT JOIN Sal_ControllingOffice_Mst CO ON E.fk_controllingid = CO.pk_Controllid
        WHERE LA.fk_leaveid = ? AND LA.fk_yearid = ?
        """
        params = [lid, year]
        if ddo:
            query += " AND E.fk_ddoid = ?"
            params.append(ddo)
        if loc:
            query += " AND E.fk_locid = ?"
            params.append(loc)
        if dept:
            query += " AND E.fk_deptid = ?"
            params.append(dept)
        if eid:
            query += " AND E.pk_empid = ?"
            params.append(eid)
        return DB.fetch_all(query + " ORDER BY E.empname", params)

    @staticmethod
    def save_assignments(ids, lid, fid, days, uid):
        year = LeaveAssignmentModel._resolve_year(fid)
        for eid in ids:
            exists = DB.fetch_one("SELECT pk_leaveassignid FROM SAL_LeaveAssignment_Details WHERE fk_empid=? AND fk_leaveid=? AND fk_yearid=?", [eid, lid, year])
            if exists:
                DB.execute("UPDATE SAL_LeaveAssignment_Details SET leaveassigned=?, fk_updUserID=?, fk_updDateID=GETDATE() WHERE pk_leaveassignid=?", [days, uid, exists['pk_leaveassignid']])
            else:
                DB.execute("""
                    INSERT INTO SAL_LeaveAssignment_Details (fk_empid, fk_leaveid, fk_yearid, leaveassigned, installment, fk_insUserID, fk_insDateID, fk_updUserID, fk_updDateID)
                    VALUES (?, ?, ?, ?, 1, ?, GETDATE(), ?, GETDATE())
                """, [eid, lid, year, days, uid, uid])

    @staticmethod
    def process_assignments(ids, lid, fid, uid):
        year = LeaveAssignmentModel._resolve_year(fid)
        for eid in ids:
            assign = DB.fetch_one("SELECT leaveassigned FROM SAL_LeaveAssignment_Details WHERE fk_empid=? AND fk_leaveid=? AND fk_yearid=?", [eid, lid, year])
            if assign:
                exists = DB.fetch_one("SELECT pk_assignid FROM SAL_EmployeeLeave_Details WHERE fk_empid=? AND fk_leaveid=?", [eid, lid])
                if exists:
                    DB.execute("UPDATE SAL_EmployeeLeave_Details SET currentyearleaves=?, fk_updUserID=?, fk_updDateID=GETDATE() WHERE pk_assignid=?", [assign['leaveassigned'], uid, exists['pk_assignid']])
                else:
                    # Generate a unique PK if needed. Since it's varchar and not identity.
                    # We'll use a prefix 'EP-' + empid + '-' + leaveid
                    new_pk = f"EP-{eid}-{lid}"
                    DB.execute("""
                        INSERT INTO SAL_EmployeeLeave_Details (pk_assignid, fk_empid, fk_leaveid, currentyearleaves, fk_insUserID, fk_insDateID, fk_updUserID, fk_updDateID)
                        VALUES (?, ?, ?, ?, ?, GETDATE(), ?, GETDATE())
                    """, [new_pk, eid, lid, assign['leaveassigned'], uid, uid])

    @staticmethod
    def unprocess_assignments(ids, lid, fid):
        pass

class EstablishmentModel:
    MASTER_TABLES = {
        'department': {'title': 'Department', 'table': 'Department_Mst', 'pk': 'pk_deptid', 'name': 'description'},
        'designation': {'title': 'Designation', 'table': 'SAL_Designation_Mst', 'pk': 'pk_desgid', 'name': 'designation'},
        'district': {'title': 'District', 'table': 'distric_mst', 'pk': 'pk_districid', 'name': 'districname'},
        'location': {'title': 'Location', 'table': 'Location_Mst', 'pk': 'pk_locid', 'name': 'locname'},
        'ddo': {'title': 'DDO', 'table': 'DDO_Mst', 'pk': 'pk_ddoid', 'name': 'Description'},
        'section': {'title': 'Section', 'table': 'SAL_Section_Mst', 'pk': 'pk_sectionid', 'name': 'description'},
        'grade': {'title': 'Grade', 'table': 'SAL_Grade_Mst', 'pk': 'pk_gradeid', 'name': 'gradename'},
        'class': {'title': 'Class', 'table': 'SAL_Class_Mst', 'pk': 'pk_classid', 'name': 'classname'},
        'religion': {'title': 'Religion', 'table': 'Religion_Mst', 'pk': 'pk_religionid', 'name': 'religionname'},
        'controlling_office': {'title': 'Controlling Office', 'table': 'Sal_ControllingOffice_Mst', 'pk': 'pk_Controllid', 'name': 'description'},
        'office_type': {'title': 'Office Type', 'table': 'OfficeTypeMaster', 'pk': 'pk_officeTypeId', 'name': 'officeTypeDesc'}
    }

    @staticmethod
    def get_record(key, rid):
        cfg = EstablishmentModel.MASTER_TABLES[key]
        return DB.fetch_one(f"SELECT * FROM {cfg['table']} WHERE {cfg['pk']} = ?", [rid])

    @staticmethod
    def save_record(key, data):
        cfg = EstablishmentModel.MASTER_TABLES[key]
        pk, table, name = cfg['pk'], cfg['table'], cfg['name']
        val = data.get('name')
        if data.get('pk_id'):
            return DB.execute(f"UPDATE {table} SET {name} = ? WHERE {pk} = ?", [val, data['pk_id']])
        else:
            return DB.execute(f"INSERT INTO {table} ({name}) VALUES (?)", [val])

    @staticmethod
    def delete_record(key, rid):
        cfg = EstablishmentModel.MASTER_TABLES[key]
        return DB.execute(f"DELETE FROM {cfg['table']} WHERE {cfg['pk']} = ?", [rid])

