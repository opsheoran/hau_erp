import os
import re

files_to_fix = [
    'addition_withdrawal_approval_status.html',
    'admission_no_generation.html',
    'advisory_creation_approval_status.html',
    'batch_assignment.html',
    'college_dean_approval.html',
    'course_allocation_pg.html',
    'course_plan.html',
    'dean_pgs_approval.html',
    'dean_pgs_course_plan_approval.html',
    'hod_approval.html',
    'igrade_approval_status.html',
    'pg_mandates_submission.html',
    'programme_of_work_pg.html',
    'student_thesis_detail.html'
]

script_code = '''
// Silent Dropdown Cascading
function ajaxLoadDegrees(collegeId) {
    const degSelect = document.querySelector('select[name="degree_id"]');
    if(!degSelect) return;
    degSelect.innerHTML = '<option value="0\">--Select Degree--</option>';
    if(!collegeId || collegeId === '0') return;
    
    fetch(`/academics/api/college/${collegeId}/degrees`)
        .then(res => res.json())
        .then(data => {
            data.forEach(d => {
                const opt = document.createElement('option');
                opt.value = d.id;
                opt.textContent = d.name;
                degSelect.appendChild(opt);
            });
        }).catch(err => console.error(err));
}

function ajaxLoadBranches(degreeId) {
    const brSelect = document.querySelector('select[name="branch_id"]');
    if(!brSelect) return;
    brSelect.innerHTML = '<option value="0\">--Select Specialization--</option>';
    if(!degreeId || degreeId === '0') return;
    
    fetch(`/academics/api/degree/${degreeId}/branches`)
        .then(res => res.json())
        .then(data => {
            data.forEach(b => {
                const opt = document.createElement('option');
                opt.value = b.id;
                opt.textContent = b.name;
                brSelect.appendChild(opt);
            });
        }).catch(err => console.error(err));
}
'''

for fname in files_to_fix:
    path = os.path.join('app/templates/academics', fname)
    if not os.path.exists(path):
        continue
        
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    if 'ajaxLoadDegrees' in content:
        continue # Already fixed
        
    # Replace onchanges
    content = re.sub(r'<select name="college_id"(.*?)onchange="handleFilterChange\(\)"', r'<select name="college_id"\1onchange="ajaxLoadDegrees(this.value)"', content)
    content = re.sub(r'<select name="degree_id"(.*?)onchange="handleFilterChange\(\)"', r'<select name="degree_id"\1onchange="ajaxLoadBranches(this.value)"', content)
    content = re.sub(r'<select name="session_id"(.*?)onchange="handleFilterChange\(\)"', r'<select name="session_id"\1', content)
    
    # Replace handleFilterChange definition with our AJAX functions
    content = re.sub(r'function handleFilterChange\(\)\s*\{[\s\S]*?document\.getElementById\(\'filterForm\'\)\.submit\(\);\s*\}', script_code, content)

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'Fixed {fname}')
