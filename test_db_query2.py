from app.db import DB

query = """
SELECT TOP 5 c.pk_courseid, c.coursename
FROM SMS_Course_Mst c
JOIN SMS_StuCourseAllocation a ON a.fk_courseid = c.pk_courseid
WHERE a.fk_dgacasessionid = 77 AND ISNULL(c.isobsolete, 0) = 0
  AND EXISTS (
      SELECT 1 FROM SMS_DgExamWei_WithCourse w
      JOIN SMS_DgExam_Mst m ON w.fk_dgexammapid = m.pk_dgexammapid
      JOIN SMS_Exam_Mst config ON m.fk_examid = config.pk_examid
      WHERE w.fk_courseid = c.pk_courseid 
        AND m.fk_acasessionid_from = a.fk_dgacasessionid
        AND (config.exam LIKE '%External%' OR config.isinternal = 0)
        AND config.istheory = 1
  )
"""
print(DB.fetch_all(query))
