import sys, os
sys.path.insert(0, os.getcwd())
from app import app
from app.db import DB
from app.models.examination import ExaminationModel

def debug_save():
    deg = DB.fetch_one("SELECT TOP 1 pk_degreeid FROM SMS_Degree_Mst")
    sess_obj = DB.fetch_one("SELECT TOP 1 pk_sessionid FROM SMS_AcademicSession_Mst")
    month_obj = DB.fetch_one("SELECT TOP 1 pk_MonthId FROM Month_Mst")
    year_obj = DB.fetch_one("SELECT TOP 1 pk_yearID FROM Year_Mst")
    
    data = {
        'degree_id': deg['pk_degreeid'],
        'session_id': sess_obj['pk_sessionid'],
        'month_from': month_obj['pk_MonthId'],
        'month_to': month_obj['pk_MonthId'],
        'year_from': year_obj['pk_yearID'],
        'year_to': year_obj['pk_yearID'],
        'is_active': 'on',
        'exam_type_sem_1': 'Semester'
    }
    
    try:
        res = ExaminationModel.save_exam_config(data, 1)
        print("Success:", res)
    except Exception as e:
        print("Exception:", str(e))
        import traceback
        traceback.print_exc()

debug_save()
