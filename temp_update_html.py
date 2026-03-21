with open('app/templates/examination/student_marks_entry_coe.html', 'r') as f:
    coe_html = f.read()

routes = [
    ('student_marks_entry_ug', 'Student Marks Entry (UG and MBA)'),
    ('student_marks_entry_pg_phd', 'Student Marks Entry (PG/PHD) By Teacher'),
    ('student_marks_entry_re_evaluation', 'Student Marks Entry (Re-Evaluation)'),
    ('student_marks_entry_supplementary', 'Student Marks Entry (Supplementary)'),
]

for route_name, title in routes:
    new_html = coe_html.replace('student_marks_entry_coe', route_name).replace('Student Marks Entry (@COE)', title)
    with open(f'app/templates/examination/{route_name}.html', 'w') as f2:
        f2.write(new_html)
    print(f"Updated {route_name}.html")
