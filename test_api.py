from app import app
from app.blueprints.academics import get_syllabus_courses_api
import json

app.app_context().push()
with app.test_request_context('/academics/api/get_syllabus_courses', json={'session_from': '72', 'degree_id': '24', 'semester_id': '1', 'dept_id': '0'}):
    res = get_syllabus_courses_api()
    print(res.get_data(as_text=True)[:200])
