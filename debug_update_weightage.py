import sys, os
sys.path.insert(0, os.getcwd())
from app.db import DB

print('Searching for Degree M.Sc (BS&H):')
rows = DB.fetch_all("SELECT pk_degreeid, degreename FROM SMS_Degree_Mst WHERE degreename LIKE '%M.Sc (BS&H)%'")
print(rows)

if rows:
    deg_id = rows[0]['pk_degreeid']
    print(f'\nChecking Exam Configs for degree {deg_id} and session 77:')
    configs = DB.fetch_all("SELECT * FROM SMS_ExamConfig_Mst WHERE fk_degreeid = ? AND fk_sessionid = 77", [deg_id])
    print(configs)

    print(f'\nChecking DgExam maps for degree {deg_id} and session 77:')
    maps = DB.fetch_all("SELECT M.*, E.exam FROM SMS_DgExam_Mst M JOIN SMS_Exam_Mst E ON M.fk_examid = E.pk_examid WHERE fk_degreeid = ? AND fk_acasessionid_from = 77", [deg_id])
    print(maps)
