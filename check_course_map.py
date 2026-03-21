import sys, os
sys.path.insert(0, os.getcwd())
from app.db import DB
print('SMS_Course_Mst_Dtl columns:')
print(DB.get_table_columns('SMS_Course_Mst_Dtl'))
print('SMS_Degreewise_crhr_CoursePlan columns:')
print(DB.get_table_columns('SMS_Degreewise_crhr_CoursePlan'))
