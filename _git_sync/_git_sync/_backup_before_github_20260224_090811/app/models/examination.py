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
