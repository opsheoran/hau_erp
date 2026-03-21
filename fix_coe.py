import codecs
import json
file_path = r'D:\hau_erp\app\blueprints\examination\student_marks_entry_coe.py'
with codecs.open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Remove department_id references
content = content.replace("                                department_id=request.form.get('department_id'),\r\n", "")
content = content.replace("                                department_id=request.form.get('department_id'),\n", "")

content = content.replace("        'department_id': request.args.get('department_id', ''),\r\n", "")
content = content.replace("        'department_id': request.args.get('department_id', ''),\n", "")

content = content.replace("        'departments': AcademicsModel.get_departments(),\r\n", "")
content = content.replace("        'departments': AcademicsModel.get_departments(),\n", "")

content = content.replace("    department_id = request.args.get('department_id')\r\n", "")
content = content.replace("    department_id = request.args.get('department_id')\n", "")

content = content.replace("""    if department_id:
        query += " AND S.fk_deptid = ?"
        params.append(department_id)""", "")
content = content.replace("""    if department_id:\r\n        query += " AND S.fk_deptid = ?"\r\n        params.append(department_id)""", "")

content = content.replace("""    if department_id:
        students_query += " AND S.fk_deptid = ?"
        params.append(department_id)""", "")
content = content.replace("""    if department_id:\r\n        students_query += " AND S.fk_deptid = ?"\r\n        params.append(department_id)""", "")

# College logic based on session user location
# Original: 'colleges': DB.fetch_all("SELECT pk_locid as id, locname as name FROM UM_Location_Mst WHERE ISNULL(isactive, 1) = 1 ORDER BY locname"),
# New: 'colleges': DB.fetch_all("SELECT pk_locid as id, locname as name FROM UM_Location_Mst WHERE pk_locid = ? AND ISNULL(isactive, 1) = 1 ORDER BY locname", [session.get('selected_loc')])

old_college_q = """'colleges': DB.fetch_all("SELECT pk_locid as id, locname as name FROM UM_Location_Mst WHERE ISNULL(isactive, 1) = 1 ORDER BY locname")"""
new_college_q = """'colleges': DB.fetch_all("SELECT pk_locid as id, locname as name FROM UM_Location_Mst WHERE pk_locid = ? AND ISNULL(isactive, 1) = 1 ORDER BY locname", [session.get('selected_loc')]) if session.get('selected_loc') else DB.fetch_all("SELECT pk_locid as id, locname as name FROM UM_Location_Mst WHERE ISNULL(isactive, 1) = 1 ORDER BY locname")"""
content = content.replace(old_college_q, new_college_q)


with codecs.open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Backend updated.")
