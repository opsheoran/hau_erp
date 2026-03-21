import sys, os
sys.path.insert(0, os.getcwd())
from app.db import DB
print('Session:', DB.fetch_all("SELECT pk_sessionid, sessionname FROM SMS_AcademicSession_Mst WHERE sessionname LIKE '%2025%'"))
print('Degree:', DB.fetch_all("SELECT pk_degreeid, degreename FROM SMS_Degree_Mst WHERE degreename LIKE '%Agriculture%'"))
