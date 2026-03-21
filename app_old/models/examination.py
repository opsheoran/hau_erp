from app.db import DB

class ExaminationModel:
    @staticmethod
    def get_exams():
        query = "SELECT * FROM SMS_Exam_Mst ORDER BY examorder"
        return DB.fetch_all(query)

    @staticmethod
    def save_exam(data):
        exam = data.get('exam')
        short = data.get('short')
        order = data.get('order') or 0
        is_th = 1 if data.get('is_th') else 0
        is_pr = 1 if data.get('is_pr') else 0
        is_int = 1 if data.get('is_int') else 0
        is_main = 1 if data.get('is_main') else 0
        pk_id = data.get('pk_id')

        if pk_id:
            query = """
                UPDATE SMS_Exam_Mst 
                SET exam=?, examshort=?, examorder=?, istheory=?, ispractical=?, isinternal=?, isMainExam=?
                WHERE pk_examid=?
            """
            return DB.execute(query, [exam, short, order, is_th, is_pr, is_int, is_main, pk_id])
        else:
            query = """
                INSERT INTO SMS_Exam_Mst (exam, examshort, examorder, istheory, ispractical, isinternal, isMainExam)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            return DB.execute(query, [exam, short, order, is_th, is_pr, is_int, is_main])

    @staticmethod
    def get_degree_exams(degree_id=None):
        query = """
            SELECT M.*, 
                   D.degreename, 
                   E.exam, 
                   S1.sessionname as session_from, 
                   S2.sessionname as session_to
            FROM SMS_DgExam_Mst M
            INNER JOIN SMS_Degree_Mst D ON M.fk_degreeid = D.pk_degreeid
            INNER JOIN SMS_Exam_Mst E ON M.fk_examid = E.pk_examid
            INNER JOIN SMS_AcademicSession_Mst S1 ON M.fk_acasessionid_from = S1.pk_sessionid
            LEFT JOIN SMS_AcademicSession_Mst S2 ON M.fk_acasessionid_to = S2.pk_sessionid
            WHERE 1=1
        """
        params = []
        if degree_id:
            query += " AND M.fk_degreeid = ?"
            params.append(degree_id)
        
        query += " ORDER BY D.degreename, S1.sessionstart_dt DESC"
        return DB.fetch_all(query, params)

    @staticmethod
    def save_degree_exam(data):
        pk_id = data.get('pk_id')
        degree_id = data.get('degree_id')
        session_from = data.get('session_from')
        session_to = data.get('session_to') or None
        exam_id = data.get('exam_id')

        # Check overlap/duplicate
        existing = DB.fetch_one("""
            SELECT pk_dgexammapid FROM SMS_DgExam_Mst 
            WHERE fk_degreeid = ? AND fk_examid = ? AND fk_acasessionid_from = ? AND pk_dgexammapid != ?
        """, [degree_id, exam_id, session_from, pk_id or 0])
        
        if existing:
            raise Exception("This Exam is already mapped to this Degree for the selected starting session.")

        if pk_id:
            query = """
                UPDATE SMS_DgExam_Mst 
                SET fk_degreeid=?, fk_examid=?, fk_acasessionid_from=?, fk_acasessionid_to=?
                WHERE pk_dgexammapid=?
            """
            return DB.execute(query, [degree_id, exam_id, session_from, session_to, pk_id])
        else:
            query = """
                INSERT INTO SMS_DgExam_Mst (fk_degreeid, fk_examid, fk_acasessionid_from, fk_acasessionid_to)
                VALUES (?, ?, ?, ?)
            """
            return DB.execute(query, [degree_id, exam_id, session_from, session_to])

    @staticmethod
    def delete_degree_exam(pk_id):
        return DB.execute("DELETE FROM SMS_DgExam_Mst WHERE pk_dgexammapid=?", [pk_id])

    @staticmethod
    def get_exam_configs(filters=None):
        query = """
            SELECT C.*,
                   S.sessionname,
                   D.degreename,
                   M1.Month as month_from_name,
                   M2.Month as month_to_name,
                   Y1.description as year_from_name,
                   Y2.description as year_to_name
            FROM SMS_ExamConfig_Mst C
            INNER JOIN SMS_AcademicSession_Mst S ON C.fk_sessionid = S.pk_sessionid
            INNER JOIN SMS_Degree_Mst D ON C.fk_degreeid = D.pk_degreeid
            LEFT JOIN Month_Mst M1 ON C.fk_monthid_from = M1.pk_MonthId
            LEFT JOIN Month_Mst M2 ON C.fk_monthid_to = M2.pk_MonthId
            LEFT JOIN Year_Mst Y1 ON C.fk_yearid_From = Y1.pk_yearID
            LEFT JOIN Year_Mst Y2 ON C.fk_yearid_To = Y2.pk_yearID
            WHERE 1=1
        """
        params = []
        if filters and filters.get('degree_id') and filters['degree_id'] != '0':
            query += " AND C.fk_degreeid = ?"
            params.append(filters['degree_id'])
        if filters and filters.get('session_id') and filters['session_id'] != '0':
            query += " AND C.fk_sessionid = ?"
            params.append(filters['session_id'])
            
        query += " ORDER BY S.sessionstart_dt DESC, D.degreename"
        return DB.fetch_all(query, params)

    @staticmethod
    def get_exam_config_dtl(config_id):
        return DB.fetch_all("SELECT * FROM sms_examconfig_dtl WHERE fk_exconfigid = ?", [config_id])

    @staticmethod
    def save_exam_config(data, user_id):
        pk_id = data.get('pk_id')
        degree_id = data.get('degree_id')
        session_id = data.get('session_id')
        month_from = data.get('month_from')
        month_to = data.get('month_to')
        year_from = data.get('year_from')
        year_to = data.get('year_to')
        is_active = 1 if data.get('is_active') else 0
        
        # Determine total semesters dynamically sent in form
        if hasattr(data, 'getlist'):
            sem_ids = data.getlist('semester_id[]')
            exam_types = data.getlist('exam_type[]')
        else:
            sem_ids = data.get('semester_id[]', [])
            if not isinstance(sem_ids, list): sem_ids = [sem_ids] if sem_ids else []
            
            exam_types = data.get('exam_type[]', [])
            if not isinstance(exam_types, list): exam_types = [exam_types] if exam_types else []

        if pk_id:
            DB.execute("""
                UPDATE SMS_ExamConfig_Mst 
                SET fk_degreeid=?, fk_monthid_from=?, fk_monthid_to=?, fk_yearid_From=?, fk_yearid_To=?, 
                    fk_sessionid=?, isactive=?, configdate=GETDATE(), fk_userid=?
                WHERE pk_exconfigid=?
            """, [degree_id, month_from, month_to, year_from, year_to, session_id, is_active, user_id, pk_id])
            
            DB.execute("DELETE FROM sms_examconfig_dtl WHERE fk_exconfigid=?", [pk_id])
            config_id = pk_id
        else:
            DB.execute("""
                INSERT INTO SMS_ExamConfig_Mst 
                (fk_degreeid, fk_monthid_from, fk_monthid_to, fk_yearid_From, fk_yearid_To, 
                 fk_sessionid, isactive, configdate, fk_userid)
                VALUES (?, ?, ?, ?, ?, ?, ?, GETDATE(), ?)
            """, [degree_id, month_from, month_to, year_from, year_to, session_id, is_active, user_id])
            
            row = DB.fetch_one("SELECT IDENT_CURRENT('SMS_ExamConfig_Mst') as id")
            config_id = row['id']
            
        # Insert detail rows
        for i in range(len(sem_ids)):
            sem_id = sem_ids[i]
            exam_type = exam_types[i] if i < len(exam_types) else None
            if sem_id and exam_type:
                DB.execute("""
                    INSERT INTO sms_examconfig_dtl (fk_exconfigid, fk_semesterid, ExamType)
                    VALUES (?, ?, ?)
                """, [config_id, sem_id, exam_type])
                
        return True

    @staticmethod
    def delete_exam_config(pk_id):
        DB.execute("DELETE FROM sms_examconfig_dtl WHERE fk_exconfigid=?", [pk_id])
        return DB.execute("DELETE FROM SMS_ExamConfig_Mst WHERE pk_exconfigid=?", [pk_id])

    @staticmethod
    def get_weightage_headers(filters=None):
        query = """
            SELECT W.*, 
                   D.degreename, 
                   E.exam,
                   S1.sessionname as session_from_name,
                   S2.sessionname as session_to_name
            FROM SMS_DgExamWeightage W
            INNER JOIN SMS_DgExam_Mst M ON W.fk_dgexammapid = M.pk_dgexammapid
            INNER JOIN SMS_Degree_Mst D ON M.fk_degreeid = D.pk_degreeid
            INNER JOIN SMS_Exam_Mst E ON M.fk_examid = E.pk_examid
            INNER JOIN SMS_AcademicSession_Mst S1 ON W.fk_sessionid_from = S1.pk_sessionid
            LEFT JOIN SMS_AcademicSession_Mst S2 ON W.fk_sessionid_upto = S2.pk_sessionid
            WHERE 1=1
        """
        params = []
        if filters:
            if filters.get('degree_id') and filters['degree_id'] != '0':
                query += " AND M.fk_degreeid = ?"
                params.append(filters['degree_id'])
            if filters.get('session_id') and filters['session_id'] != '0':
                query += " AND (W.fk_sessionid_from = ? OR W.fk_sessionid_upto = ?)"
                params.extend([filters['session_id'], filters['session_id']])
                
        query += " ORDER BY D.degreename, S1.sessionstart_dt DESC"
        return DB.fetch_all(query, params)

    @staticmethod
    def get_weightage_detail(weightage_id):
        return DB.fetch_all("""
            SELECT C.*, CM.coursename as Course, CM.coursecode
            FROM SMS_DgExamWei_WithCourse C
            INNER JOIN SMS_Course_Mst CM ON C.fk_courseid = CM.pk_courseid
            WHERE C.fk_dgexamweid = ?
        """, [weightage_id])

    @staticmethod
    def save_weightage(data):
        pk_id = data.get('pk_id')
        dgexammapid = data.get('dgexammapid')
        session_from = data.get('session_from')
        session_to = data.get('session_to') or None
        is_course_based = 1 if data.get('is_course_based') else 0
        
        cwp = data.get('cwp') or 0
        cwop = data.get('cwop') or 0
        cop = data.get('cop') or 0

        if pk_id:
            DB.execute("""
                UPDATE SMS_DgExamWeightage 
                SET fk_dgexammapid=?, fk_sessionid_from=?, fk_sessionid_upto=?, 
                    iscoursebasedwei=?, cwp=?, cwop=?, cop=?
                WHERE pk_dgexamweid=?
            """, [dgexammapid, session_from, session_to, is_course_based, cwp, cwop, cop, pk_id])
            
            DB.execute("DELETE FROM SMS_DgExamWei_WithCourse WHERE fk_dgexamweid=?", [pk_id])
            weight_id = pk_id
        else:
            DB.execute("""
                INSERT INTO SMS_DgExamWeightage 
                (fk_dgexammapid, fk_sessionid_from, fk_sessionid_upto, iscoursebasedwei, cwp, cwop, cop)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, [dgexammapid, session_from, session_to, is_course_based, cwp, cwop, cop])
            
            row = DB.fetch_one("SELECT IDENT_CURRENT('SMS_DgExamWeightage') as id")
            weight_id = row['id']
            
        # Course details
        if is_course_based:
            course_keys = [k for k in data.keys() if k.startswith('max_th_')]
            for k in course_keys:
                course_id = k.replace('max_th_', '')
                sem_id = data.get(f'sem_{course_id}')
                
                max_th = data.get(f'max_th_{course_id}') or 0
                min_th = data.get(f'min_th_{course_id}') or 0
                max_pr = data.get(f'max_pr_{course_id}') or 0
                min_pr = data.get(f'min_pr_{course_id}') or 0
                
                DB.execute("""
                    INSERT INTO SMS_DgExamWei_WithCourse 
                    (fk_dgexamweid, fk_courseid, fk_dgexammapid, fk_semesterid, maxmarks_th, minmarks_th, maxmarks_pr, minmarks_pr)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, [weight_id, course_id, dgexammapid, sem_id, max_th, min_th, max_pr, min_pr])

        return True

    @staticmethod
    def delete_weightage(pk_id):
        DB.execute("DELETE FROM SMS_DgExamWei_WithCourse WHERE fk_dgexamweid=?", [pk_id])
        return DB.execute("DELETE FROM SMS_DgExamWeightage WHERE pk_dgexamweid=?", [pk_id])

    @staticmethod
    def get_external_examiners():
        return DB.fetch_all("SELECT * FROM SMS_ExtExaminar_Mst ORDER BY InsertDate DESC")

    @staticmethod
    def get_examiner_courses(examiner_id):
        query = """
            SELECT D.*, 
                   Deg.degreename, 
                   S.semester_roman, 
                   C.coursename, C.coursecode,
                   Ses.sessionname
            FROM SMS_ExtExaminar_Dtl D
            LEFT JOIN SMS_Degree_Mst Deg ON D.fk_degreeid = Deg.pk_degreeid
            LEFT JOIN SMS_Semester_Mst S ON D.fk_semesterid = S.pk_semesterid
            LEFT JOIN SMS_Course_Mst C ON D.fk_courseid = C.pk_courseid
            LEFT JOIN SMS_AcademicSession_Mst Ses ON D.fk_Sessionid = Ses.pk_sessionid
            WHERE D.Fk_Exmid = ?
        """
        return DB.fetch_all(query, [examiner_id])

    @staticmethod
    def save_external_examiner(data):
        pk_id = data.get('pk_id')
        name = data.get('ExaminarName')
        univ = data.get('University')
        user = data.get('UserId')
        pwd = data.get('Password')
        contact = data.get('ContactNumber')
        email = data.get('Email')
        desig = data.get('Designation')
        addr = data.get('Adddress')
        is_active = 1 if data.get('IsActive') else 0
        is_internal = 1 if data.get('IsInternal') else 0
        from_date = data.get('FromDate') or None
        to_date = data.get('ToDate') or None

        if pk_id:
            DB.execute("""
                UPDATE SMS_ExtExaminar_Mst 
                SET ExaminarName=?, University=?, UserId=?, Password=?, ContactNumber=?, 
                    Email=?, IsActive=?, IsInternal=?, Designation=?, Adddress=?, 
                    FromDate=?, ToDate=?
                WHERE Pk_Exmid=?
            """, [name, univ, user, pwd, contact, email, is_active, is_internal, desig, addr, from_date, to_date, pk_id])
            return pk_id
        else:
            DB.execute("""
                INSERT INTO SMS_ExtExaminar_Mst 
                (ExaminarName, University, UserId, Password, ContactNumber, Email, IsActive, IsInternal, Designation, Adddress, InsertDate, FromDate, ToDate)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE(), ?, ?)
            """, [name, univ, user, pwd, contact, email, is_active, is_internal, desig, addr, from_date, to_date])
            row = DB.fetch_one("SELECT IDENT_CURRENT('SMS_ExtExaminar_Mst') as id")
            return row['id']

    @staticmethod
    def delete_external_examiner(pk_id):
        DB.execute("DELETE FROM SMS_ExtExaminar_Dtl WHERE Fk_Exmid=?", [pk_id])
        return DB.execute("DELETE FROM SMS_ExtExaminar_Mst WHERE Pk_Exmid=?", [pk_id])

    @staticmethod
    def save_examiner_course(data):
        dtl_id = data.get('Pk_ExmDtlid')
        exmid = data.get('Fk_Exmid')
        course_id = data.get('course_id')
        session_id = data.get('session_id')
        paper_code = data.get('CoursePaperCode')
        
        # Determine if the course is active based on what is passed, or just assume 1
        course_active = 1 

        if dtl_id:
            DB.execute("""
                UPDATE SMS_ExtExaminar_Dtl 
                SET fk_courseid=?, fk_Sessionid=?, CoursePaperCode=?
                WHERE Pk_ExmDtlid=?
            """, [course_id, session_id, paper_code, dtl_id])
        else:
            DB.execute("""
                INSERT INTO SMS_ExtExaminar_Dtl 
                (Fk_Exmid, fk_courseid, fk_Sessionid, CourseActive, CoursePaperCode)
                VALUES (?, ?, ?, ?, ?)
            """, [exmid, course_id, session_id, course_active, paper_code])
        return True

    @staticmethod
    def delete_examiner_course(dtl_id):
        return DB.execute("DELETE FROM SMS_ExtExaminar_Dtl WHERE Pk_ExmDtlid=?", [dtl_id])

    @staticmethod
    def get_formatted_exam_configs(degree_id, session_id):
        # Header info
        query = """
            SELECT C.pk_exconfigid, 
                   M1.descriptiion as m_from, Y1.description as y_from,
                   M2.descriptiion as m_to, Y2.description as y_to
            FROM SMS_ExamConfig_Mst C
            LEFT JOIN Month_Mst M1 ON C.fk_monthid_from = M1.pk_MonthId
            LEFT JOIN Year_Mst Y1 ON C.fk_yearid_From = Y1.pk_yearID
            LEFT JOIN Month_Mst M2 ON C.fk_monthid_to = M2.pk_MonthId
            LEFT JOIN Year_Mst Y2 ON C.fk_yearid_To = Y2.pk_yearID
            WHERE C.fk_degreeid = ? AND C.fk_sessionid = ? AND C.isactive = 1
        """
        headers = DB.fetch_all(query, [degree_id, session_id])
        
        results = []
        for h in headers:
            # Get details
            dtls = DB.fetch_all("""
                SELECT S.semester_roman, D.ExamType
                FROM sms_examconfig_dtl D
                INNER JOIN SMS_Semester_Mst S ON D.fk_semesterid = S.pk_semesterid
                WHERE D.fk_exconfigid = ?
                ORDER BY S.semesterorder
            """, [h['pk_exconfigid']])
            
            config_str = f"{h['m_from'][:3].upper()} {h['y_from']} - {h['m_to'][:3].upper()} {h['y_to']} -->"
            sem_parts = [f"{d['semester_roman']} - {d['ExamType']}" for d in dtls]
            config_str += ", ".join(sem_parts)
            
            results.append({
                'id': h['pk_exconfigid'],
                'name': config_str
            })
        return results

    @staticmethod
    def get_max_obtained_marks(dgexammapid, course_id):
        # Finds the highest marks obtained for a specific course and exam combination
        # To determine if the new maxmarks can be applied without breaking existing data
        query = """
            SELECT MAX(CAST(marks_obt AS float)) as max_obt
            FROM SMS_StuExamMarks_Dtl D
            INNER JOIN SMS_StuCourseAllocation A ON D.fk_stucourseallocid = A.pk_stucourseallocid
            WHERE D.fk_dgexammapid = ? AND A.fk_courseid = ? AND ISNUMERIC(D.marks_obt) = 1
        """
        res = DB.fetch_one(query, [dgexammapid, course_id])
        return res['max_obt'] if res and res['max_obt'] else 0

    @staticmethod
    def update_weightage_post_marks(dgexammapid, course_id, new_max_th, user_id):
        # Fetch the weightage ID for this course
        row = DB.fetch_one("""
            SELECT fk_dgexamweid 
            FROM SMS_DgExamWei_WithCourse 
            WHERE fk_dgexammapid=? AND fk_courseid=?
        """, [dgexammapid, course_id])
        
        if not row:
            raise Exception("No specific course weightage found to update.")

        wei_id = row['fk_dgexamweid']
        
        # Ensure new max marks is not less than already obtained marks
        max_obt = ExaminationModel.get_max_obtained_marks(dgexammapid, course_id)
        if float(new_max_th) < float(max_obt):
            raise Exception(f"Cannot lower max marks below {max_obt} as students have already achieved this score.")
            
        # Update weightage
        DB.execute("""
            UPDATE SMS_DgExamWei_WithCourse
            SET maxmarks_th = ?
            WHERE fk_dgexamweid = ? AND fk_courseid = ?
        """, [new_max_th, wei_id, course_id])
        
        # Update the maxmarks column in the already entered marks details
        DB.execute("""
            UPDATE SMS_StuExamMarks_Dtl
            SET maxmarks = ?
            FROM SMS_StuExamMarks_Dtl D
            INNER JOIN SMS_StuCourseAllocation A ON D.fk_stucourseallocid = A.pk_stucourseallocid
            WHERE D.fk_dgexammapid = ? AND A.fk_courseid = ?
        """, [new_max_th, dgexammapid, course_id])

        return True

    @staticmethod
    def get_students_for_marks_entry(filters):
        # filters: session_id, degree_id, semester_id, branch_id, course_id, exam_id
        session_id = filters.get('session_id')
        degree_id = filters.get('degree_id')
        semester_id = filters.get('semester_id')
        branch_id = filters.get('branch_id')
        course_id = filters.get('course_id')
        exam_id = filters.get('exam_id')

        # First find the dgexammapid
        dgexam = DB.fetch_one("""
            SELECT pk_dgexammapid FROM SMS_DgExam_Mst 
            WHERE fk_degreeid=? AND fk_examid=?
        """, [degree_id, exam_id])
        
        if not dgexam: return []
        dgmapid = dgexam['pk_dgexammapid']

        query = """
            SELECT A.Pk_stucourseallocid, S.pk_sid, S.fullname, S.AdmissionNo, S.enrollmentno,
                   M.marks_obt, M.maxmarks, M.Pk_Stumarksdtlid, M.isabsentt
            FROM SMS_StuCourseAllocation A
            INNER JOIN SMS_Student_Mst S ON A.fk_sturegid = S.pk_sid
            INNER JOIN SMS_DegreeCycle_Mst C ON A.fk_degreecycleid = C.pk_degreecycleid
            LEFT JOIN SMS_StuExamMarks_Dtl M ON A.Pk_stucourseallocid = M.fk_stucourseallocid AND M.fk_dgexammapid = ?
            WHERE A.fk_courseid = ? AND C.fk_degreeid = ? AND C.fk_semesterid = ?
            AND A.fk_dgacasessionid = ?
        """
        params = [dgmapid, course_id, degree_id, semester_id, session_id]
        if branch_id and branch_id != '0':
            query += " AND C.fk_branchid = ?"
            params.append(branch_id)
        
        query += " ORDER BY S.AdmissionNo"
        
        students = DB.fetch_all(query, params)
        return {'students': students, 'dgmapid': dgmapid}

    @staticmethod
    def save_marks(data, user_id):
        dgmapid = data.get('dgmapid')
        alloc_ids = data.getlist('alloc_id[]')
        marks_obt = data.getlist('marks[]')
        max_marks = data.getlist('max_marks[]')
        absents = data.getlist('absent[]') # 1 if absent

        for i in range(len(alloc_ids)):
            # Check if exists
            existing = DB.fetch_scalar("SELECT Pk_Stumarksdtlid FROM SMS_StuExamMarks_Dtl WHERE fk_stucourseallocid=? AND fk_dgexammapid=?", 
                                     [alloc_ids[i], dgmapid])
            
            is_abs = 1 if str(alloc_ids[i]) in absents else 0
            m_obt = marks_obt[i] if not is_abs else 0
            
            if existing:
                DB.execute("""
                    UPDATE SMS_StuExamMarks_Dtl SET marks_obt=?, maxmarks=?, isabsentt=?, fk_userid=?, feeddate=GETDATE()
                    WHERE Pk_Stumarksdtlid=?
                """, [m_obt, max_marks[i], is_abs, user_id, existing])
            else:
                DB.execute("""
                    INSERT INTO SMS_StuExamMarks_Dtl (fk_stucourseallocid, fk_dgexammapid, marks_obt, maxmarks, isabsentt, fk_userid, feeddate)
                    VALUES (?, ?, ?, ?, ?, ?, GETDATE())
                """, [alloc_ids[i], dgmapid, m_obt, max_marks[i], is_abs, user_id])
        return True

    @staticmethod
    def delete_exam(pk_id):
        return DB.execute("DELETE FROM SMS_Exam_Mst WHERE pk_examid=?", [pk_id])
