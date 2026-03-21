from app.db import DB

query = """
SELECT TOP 5 c.pk_courseid, c.coursename
FROM SMS_Course_Mst c
WHERE ISNULL(c.isobsolete, 0) = 0
  AND EXISTS (
      SELECT 1 FROM SMS_StuCourseAllocation a
      WHERE a.fk_courseid = c.pk_courseid 
        AND a.fk_dgacasessionid = 77
  )
  AND EXISTS (
      SELECT 1 FROM SMS_DgExamWei_WithCourse w
      JOIN SMS_DgExam_Mst m ON w.fk_dgexammapid = m.pk_dgexammapid
      JOIN SMS_Exam_Mst config ON m.fk_examid = config.pk_examid
      WHERE w.fk_courseid = c.pk_courseid 
        AND m.fk_acasessionid_from = 77
        AND (config.exam LIKE '%External%' OR config.isinternal = 0)
  )
"""
print(DB.fetch_all(query))
