import sys, os
sys.path.insert(0, os.getcwd())
from app.db import DB
cols = DB.fetch_all("SELECT COLUMN_NAME, IS_NULLABLE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='SMS_ExtExaminar_Dtl'")
print(cols)
