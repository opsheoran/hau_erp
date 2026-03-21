import sys, os
sys.path.insert(0, os.getcwd())
from app.db import DB

print('Without Degree Filter (Just session):', len(DB.fetch_all('''
    SELECT DISTINCT M.Pk_Exmid, M.UserId, M.ExaminarName, M.Email, M.IsActive
    FROM SMS_ExtExaminar_Mst M
    JOIN SMS_ExtExaminar_Dtl D ON M.Pk_Exmid = D.Fk_Exmid
    WHERE D.fk_Sessionid = 77
''')))

print('What about fk_degreeid directly?', len(DB.fetch_all('''
    SELECT DISTINCT M.Pk_Exmid, M.UserId, M.ExaminarName, M.Email, M.IsActive
    FROM SMS_ExtExaminar_Mst M
    JOIN SMS_ExtExaminar_Dtl D ON M.Pk_Exmid = D.Fk_Exmid
    WHERE D.fk_Sessionid = 77 AND D.fk_degreeid = 1
''')))

print('Wait, checking D.fk_degreeid values for session 77:', DB.fetch_all('''
    SELECT COUNT(*) as c, D.fk_degreeid
    FROM SMS_ExtExaminar_Dtl D
    WHERE D.fk_Sessionid = 77
    GROUP BY D.fk_degreeid
'''))
