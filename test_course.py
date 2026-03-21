from app.db import DB
print(DB.fetch_one('SELECT coursecode, coursename FROM SMS_Course_Mst WHERE pk_courseid=3014'))
