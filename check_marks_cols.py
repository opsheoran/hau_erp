import sys, os
sys.path.insert(0, os.getcwd())
from app.db import DB
print('SMS_StuExamMarks_Dtl columns:')
print(DB.get_table_columns('SMS_StuExamMarks_Dtl'))
print('SMS_StuExamMarks_Cld columns:')
print(DB.get_table_columns('SMS_StuExamMarks_Cld'))
