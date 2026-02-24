from app.models.leave import LeaveModel
from app.db import DB

emp_id = 'ES-271' # HAU00212
ro = LeaveModel.get_reporting_officer(emp_id)
print(f"Reporting Officer for HAU00212: {ro}")
