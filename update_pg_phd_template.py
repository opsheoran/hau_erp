import os

with open('app/templates/examination/marks_process_pg_phd.html', 'r', encoding='utf-8') as f:
    code = f.read()

code = code.replace('Student Marks Process For UG and MBA', 'Student Marks Process For PG/PHD')
code = code.replace('get_college_ug_mba_degrees', 'get_college_pg_phd_degrees')
code = code.replace('get_student_courses_ug_mba', 'get_student_courses_pg_phd')
code = code.replace("url_for('examination.marks_process_ug_mba')", "url_for('examination.marks_process_pg_phd')")

old_header = """                        <th scope="col">In Theory</th>
                        <th scope="col">In Practical</th>
                        <th scope="col">Ex Theory</th>
                        <th scope="col">Ex Practical</th>
                        <th scope="col">InTh Grade</th>
                        <th scope="col">InPr Grade</th>
                        <th scope="col">ExTh Grade</th>
                        <th scope="col">ExPr Grade</th>"""

new_header = """                        <th scope="col">In Theory</th>
                        <th scope="col">In Practical</th>
                        <th scope="col">InTh Grade</th>
                        <th scope="col">InPr Grade</th>"""

code = code.replace(old_header, new_header)

old_row = """                            <td align="center">${c.in_th}</td>
                            <td align="center">${c.in_pr}</td>
                            <td align="center">${c.ex_th}</td>
                            <td align="center">${c.ex_pr}</td>
                            <td align="center"></td>
                            <td align="center"></td>
                            <td align="center"></td>
                            <td align="center"></td>"""

new_row = """                            <td align="center">${c.in_th}</td>
                            <td align="center">${c.in_pr}</td>
                            <td align="center"></td>
                            <td align="center"></td>"""

code = code.replace(old_row, new_row)

old_col_count = "colspan=\"16\""
new_col_count = "colspan=\"12\""
code = code.replace(old_col_count, new_col_count)

with open('app/templates/examination/marks_process_pg_phd.html', 'w', encoding='utf-8') as f:
    f.write(code)
print('Updated PG/PHD template specifics')
