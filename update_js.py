import re

with open('app/templates/student_portal/course_addition_withdrawal.html', 'r', encoding='utf-8') as f:
    html = f.read()

js = """
// Add validation and dynamic calculation JS
function calculateCredits() {
    const ddlCourse = document.getElementById('ddlCourse');
    if (ddlCourse.selectedIndex <= 0) {
        document.getElementById('crhr_th').value = '0';
        document.getElementById('crhr_pr').value = '0';
        document.getElementById('modified_credits').textContent = document.getElementById('current_credits').textContent;
        return;
    }
    
    const option = ddlCourse.options[ddlCourse.selectedIndex];
    const th = parseInt(option.getAttribute('data-th') || 0);
    const pr = parseInt(option.getAttribute('data-pr') || 0);
    const isNC = option.getAttribute('data-isnc') === 'true';
    
    document.getElementById('crhr_th').value = th;
    document.getElementById('crhr_pr').value = pr;
    
    // Only alter credit count if it's a credit course
    if (!isNC) {
        const changeType = document.querySelector('input[name="change_type"]:checked').value;
        const currentTotal = parseInt(document.getElementById('current_credits').textContent);
        
        let newTotal = currentTotal;
        if (changeType === 'A') {
            newTotal = currentTotal + th + pr;
        } else if (changeType === 'W') {
            newTotal = currentTotal - th - pr;
        }
        
        document.getElementById('modified_credits').textContent = newTotal;
    } else {
        document.getElementById('modified_credits').textContent = document.getElementById('current_credits').textContent;
    }
}

function validateSubmission() {
    const ddlCourse = document.getElementById('ddlCourse');
    if (ddlCourse.selectedIndex <= 0) {
        alert('Please select Course!!');
        return false;
    }
    
    const reason = document.getElementById('txtReason').value.trim();
    if (reason === '') {
        alert('Please Enter Reason for the Change Course!!');
        return false;
    }
    
    const modifiedCredits = parseInt(document.getElementById('modified_credits').textContent);
    const minCredits = parseInt(document.getElementById('min_credits').textContent);
    const maxCredits = parseInt(document.getElementById('max_credits').textContent);
    
    if (modifiedCredits > maxCredits || modifiedCredits < minCredits) {
        alert('Final Opted Credit Hours should be between Min. and Max. Credit Hours!!');
        return false;
    }
    
    return confirm('Are you sure to change the course?');
}
"""

new_fetch = """    .then(data => {
        ddlCourse.innerHTML = '<option value="" data-th="0" data-pr="0">-- Select Course --</option>';
        data.courses.forEach(course => {
            const option = document.createElement('option');
            option.value = course.id;
            option.textContent = course.text;
            option.setAttribute('data-th', course.th);
            option.setAttribute('data-pr', course.pr);
            option.setAttribute('data-isnc', course.isNC);
            ddlCourse.appendChild(option);
        });
        calculateCredits();
    })"""

html = re.sub(r'    \.then\(data => \{.*?        \}\);\n    \}\)', new_fetch, html, flags=re.DOTALL)
html = html.replace('function fetchCourses() {', js + '\n\nfunction fetchCourses() {')

with open('app/templates/student_portal/course_addition_withdrawal.html', 'w', encoding='utf-8') as f:
    f.write(html)
print('Updated HTML template JS')