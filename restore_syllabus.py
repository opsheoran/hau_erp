import os
with open('app/models/academics.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add SyllabusModel
if 'class SyllabusModel:' not in content:
    syllabus_code = '''
class SyllabusModel:
    @staticmethod
    def get_syllabus_courses(filters):
        sql = """
            SELECT C.pk_courseid as id, C.coursecode, C.coursename,
                   C.coursecode + ' - (' + C.coursename + ')' as display_name,
                   T.syllabus
            FROM SMS_Course_Mst_Dtl D
            INNER JOIN SMS_Course_Mst C ON D.fk_courseid = C.pk_courseid
            LEFT JOIN SMS_syllabusCreation_forCourses_Mst M ON M.fk_Degreeid = D.fk_degreeid
                                                            AND M.fromSession = ?
            LEFT JOIN SMS_syllabusCreation_forCourses_Trn T ON T.fk_syllforCourse = M.pk_syllforCourse
                                                            AND T.fk_courseid = C.pk_courseid
            WHERE D.fk_degreeid = ? AND D.fk_semesterid = ? AND D.isactive = 1
        """
        params = [filters.get('session_from'), filters.get('degree_id'), filters.get('semester_id')]
        
        if filters.get('dept_id') and str(filters['dept_id']) != '0':
            sql += " AND C.fk_Deptid = ?"
            params.append(filters['dept_id'])

        sql += " ORDER BY C.coursecode"
        return DB.fetch_all(sql, params)

    @staticmethod
    def get_syllabus(degree_id, session_from, session_to, course_id):
        sql = """
            SELECT T.syllabus
            FROM SMS_syllabusCreation_forCourses_Mst M
            INNER JOIN SMS_syllabusCreation_forCourses_Trn T ON M.pk_syllforCourse = T.fk_syllforCourse
            WHERE M.fk_Degreeid = ? AND M.fromSession = ? AND T.fk_courseid = ?
        """
        params = [degree_id, session_from, course_id]
        if session_to and str(session_to) != '0':
            sql += " AND M.toSession = ?"
            params.append(session_to)
        res = DB.fetch_one(sql, params)
        return res['syllabus'] if res else ""

    @staticmethod
    def save_syllabus(data):
        degree_id = data.get('degree_id')
        session_from = data.get('session_from')
        session_to = data.get('session_to') or '0'
        course_id = data.get('course_id')
        syllabus = data.get('syllabus')

        conn = DB.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT pk_syllforCourse FROM SMS_syllabusCreation_forCourses_Mst 
                WHERE fk_Degreeid = ? AND fromSession = ? AND ISNULL(toSession, '0') = ?  
            """, [degree_id, session_from, session_to])
            mst = cursor.fetchone()

            if mst:
                mst_id = mst[0]
            else:
                cursor.execute("""
                    INSERT INTO SMS_syllabusCreation_forCourses_Mst (fk_Degreeid, fromSession, toSession)
                    OUTPUT INSERTED.pk_syllforCourse
                    VALUES (?, ?, ?)
                """, [degree_id, session_from, session_to])
                mst_id = cursor.fetchone()[0]

            cursor.execute("""
                SELECT pk_id FROM SMS_syllabusCreation_forCourses_Trn
                WHERE fk_syllforCourse = ? AND fk_courseid = ?
            """, [mst_id, course_id])
            trn = cursor.fetchone()

            if trn:
                cursor.execute("""
                    UPDATE SMS_syllabusCreation_forCourses_Trn SET syllabus = ?
                    WHERE pk_id = ?
                """, [syllabus, trn[0]])
            else:
                cursor.execute("""
                    INSERT INTO SMS_syllabusCreation_forCourses_Trn (fk_syllforCourse, fk_courseid, syllabus)
                    VALUES (?, ?, ?)
                """, [mst_id, course_id, syllabus])

            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

class PackageMasterModel:
'''
    content = content.replace('class PackageMasterModel:', syllabus_code)

with open('app/models/academics.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Restored SyllabusModel to academics.py")
