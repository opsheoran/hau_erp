import sys, os
sys.path.insert(0, os.getcwd())
from app.db import DB
print(DB.fetch_all("SELECT pk_sessionid, sessionname FROM SMS_AcademicSession_Mst WHERE sessionname LIKE '%2025-2026%'"))
