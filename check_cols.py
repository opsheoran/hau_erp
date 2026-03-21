import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.db import DB

cols = DB.fetch_all("SELECT column_name FROM information_schema.columns WHERE table_name = 'SMS_DegreeCycle_Mst'")
print('SMS_DegreeCycle_Mst', [c['column_name'] for c in cols])
