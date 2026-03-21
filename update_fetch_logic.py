import re

with open('app/blueprints/student_portal/card_entry.py', 'r', encoding='utf-8') as f:
    code = f.read()

new_offered_query = """    # 2. Check which of these POW courses match the Even/Odd parity of the current semester.
    # The user specifically mandates that the EXACT output must match the Even parity of the POW courses.
    # Master course table is the source of truth for course parity for a degree.
    offered_map = set()
    offered_query = '''
        SELECT DISTINCT C.pk_courseid
        FROM SMS_Course_Mst C
        LEFT JOIN SMS_Course_Mst_Dtl CDTL ON C.pk_courseid = CDTL.fk_courseid AND CDTL.fk_degreeid = ?
        WHERE (CDTL.fk_semesterid % 2) = (? % 2)
    '''
    offered_data = DB.fetch_all(offered_query, [student['fk_degreeid'], student['fk_semesterid']])
    for o in offered_data:
        offered_map.add(o['pk_courseid'])"""

code = re.sub(r"    # 2\. Check which of these POW courses.*?        offered_map\.add\(o\['fk_courseid'\]\)", new_offered_query, code, flags=re.DOTALL)

filter_logic = """        # Only show the course if it matches semester parity OR the student explicitly selected it this semester.
        if c_id not in offered_map and c_id not in alloc_map:
            continue
            
        # Skip CP courses entirely if they shouldn't show in standard grids as per user logic
        if p['courseplan'] == 'CP':
            continue"""

code = re.sub(r"        # Only show the course if it is being offered this semester.*?            continue", filter_logic, code, flags=re.DOTALL)

with open('app/blueprints/student_portal/card_entry.py', 'w', encoding='utf-8') as f:
    f.write(code)

print('Updated logic to strictly Master parity, ignoring dirty HOD table.')