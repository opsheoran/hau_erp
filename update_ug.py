import re

with open('app/templates/examination/student_marks_entry_ug.html', 'r') as f:
    content = f.read()

# Replace Exam Config Row to add Theory/Practical and Batch
old_exam_config_row = """            <tr>
                <td id="lblExamConfig" class="vtext">Exam Config.</td>
                <td class="colon">:</td>
                <td class="required" colspan="4">
                    <select name="exam_config_id" id="exam_config_id" class="dropdown" style="width: 600px;" required>
                        <option value=""> -- Select Exam Config-- </option>
                        {% for ec in lookups.exam_configs %}
                        <option value="{{ ec.id }}" {% if filters.exam_config_id|string == ec.id|string %}selected{% endif %}>{{ ec.name }}</option>
                        {% endfor %}
                    </select> *
                </td>
            </tr>"""

new_exam_config_row = """            <tr>
                <td id="lblExamConfig" class="vtext">Exam Config.</td>
                <td class="colon">:</td>
                <td class="required" colspan="4">
                    <select name="exam_config_id" id="exam_config_id" class="textbox w-400" required>
                        <option value=""> -- Select Exam Config-- </option>
                        {% for ec in lookups.exam_configs %}
                        <option value="{{ ec.id }}" {% if filters.exam_config_id|string == ec.id|string %}selected{% endif %}>{{ ec.name }}</option>
                        {% endfor %}
                    </select> *
                </td>
            </tr>
            <tr>
                <td class="vtext">Theory/Practical</td>
                <td class="colon">:</td>
                <td class="required">
                    <select name="th_pr" id="th_pr" class="textbox w-200" onchange="fetchBatches()" required>
                        <option value="">--Select--</option>
                        <option value="T" {% if filters.th_pr == 'T' %}selected{% endif %}>Theory</option>
                        <option value="P" {% if filters.th_pr == 'P' %}selected{% endif %}>Practical</option>
                    </select> *
                </td>
                <td class="vtext">Batch</td>
                <td class="colon">:</td>
                <td class="required" colspan="2">
                    <select name="batch_id" id="batch_id" class="textbox w-200" required>
                        <option value="">--Select Batch--</option>
                        {% if filters.batch_id %}
                        <option value="{{ filters.batch_id }}" selected>{{ filters.batch_id }}</option>
                        {% endif %}
                    </select> *
                </td>
            </tr>"""

content = content.replace(old_exam_config_row, new_exam_config_row)

js_fetch_batches = """
function fetchBatches() {
    const college_id = document.getElementById('college_id').value;
    const session_id = document.getElementById('session_id').value;
    const degree_id = document.getElementById('degree_id').value;
    const class_id = document.getElementById('class_id').value;
    const th_pr = document.getElementById('th_pr').value;
    const batchSelect = document.getElementById('batch_id');
    
    if(!college_id || !session_id || !degree_id || !class_id || !th_pr) {
        batchSelect.innerHTML = '<option value="">--Select Batch--</option>';
        return;
    }
    
    fetch(`{{ url_for('examination.get_batches_for_marks_ug') }}?college_id=${college_id}&session_id=${session_id}&degree_id=${degree_id}&class_id=${class_id}&th_pr=${th_pr}`)
        .then(res => res.json())
        .then(data => {
            let html = '<option value="">--Select Batch--</option>';
            data.forEach(b => {
                html += `<option value="${b.id}">${b.name}</option>`;
            });
            batchSelect.innerHTML = html;
        });
}
"""
content = content.replace('<script>', f'<script>\n{js_fetch_batches}')

content = content.replace("const exam_config_id = document.getElementById('exam_config_id').value;", 
                          "const exam_config_id = document.getElementById('exam_config_id').value;\n    const th_pr = document.getElementById('th_pr').value;\n    const batch_id = document.getElementById('batch_id').value;")

content = content.replace("if(!college_id || !session_id || !degree_id || !class_id || !year_id || !exam_config_id) {", 
                          "if(!college_id || !session_id || !degree_id || !class_id || !year_id || !exam_config_id || !th_pr || !batch_id) {")

content = content.replace('alert("Please select College, Session, Degree, Class, Year, and Exam Config.");', 
                          'alert("Please select College, Session, Degree, Class, Year, Exam Config, Theory/Practical, and Batch.");')

content = content.replace("url_for('examination.get_courses_for_marks_entry')", "url_for('examination.get_courses_for_marks_entry_ug')")
content = content.replace("exam_config_id=${exam_config_id}`", "exam_config_id=${exam_config_id}&th_pr=${th_pr}&batch_id=${batch_id}`")

content = content.replace("url_for('examination.get_students_for_marks_entry')", "url_for('examination.get_students_for_marks_entry_ug')")
content = content.replace("const course_id = document.getElementById('course_id').value;", 
                          "const course_id = document.getElementById('course_id').value;\n    const th_pr = document.getElementById('th_pr').value;\n    const batch_id = document.getElementById('batch_id').value;")
content = content.replace("course_id=${course_id}&year_id=${year_id}`;", "course_id=${course_id}&year_id=${year_id}&th_pr=${th_pr}&batch_id=${batch_id}`;")

content = content.replace("url_for('examination.generate_marks_report_internal')", "url_for('examination.generate_marks_report_ug')")

with open('app/templates/examination/student_marks_entry_ug.html', 'w') as f:
    f.write(content)
print("Updated student_marks_entry_ug.html")
