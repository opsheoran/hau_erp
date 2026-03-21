import os
import re

with open('app/templates/base.html', 'r', encoding='utf-8') as f:
    content = f.read()

ajax_script = '''
<script>
// Global AJAX Form Interceptor to prevent screen flickering
document.addEventListener('DOMContentLoaded', function() {
    document.addEventListener('click', function(e) {
        if (e.target.tagName === 'INPUT' && e.target.type === 'submit' || e.target.tagName === 'BUTTON') {
            e.target.setAttribute('data-clicked', 'true');
        }
    });

    document.addEventListener('submit', async function(e) {
        const form = e.target;
        const card = form.closest('.ajax-card');
        if (!card) return; // Only apply to opted-in containers
        
        e.preventDefault();
        
        let submitter = null;
        const buttons = form.querySelectorAll('input[type="submit"], button[type="submit"]');
        buttons.forEach(b => {
            if (b.getAttribute('data-clicked') === 'true') {
                submitter = b;
                b.removeAttribute('data-clicked');
            }
        });
        
        const formData = new FormData(form);
        if (submitter && submitter.name) {
            formData.append(submitter.name, submitter.value);
            const origValue = submitter.value || submitter.innerText;
            if (submitter.tagName === 'INPUT') submitter.value = 'Wait...';
            else submitter.innerText = 'Wait...';
            submitter.disabled = true;
        }
        
        let url = form.action || window.location.href;
        let fetchOpts = { method: form.method.toUpperCase() };
        
        if (form.method.toUpperCase() === 'GET') {
            const params = new URLSearchParams(formData).toString();
            url = url.split('?')[0] + '?' + params;
        } else {
            fetchOpts.body = formData;
        }
        
        try {
            const res = await fetch(url, fetchOpts);
            const html = await res.text();
            const doc = new DOMParser().parseFromString(html, 'text/html');
            
            const newCard = doc.querySelector('.ajax-card');
            if (newCard) {
                card.innerHTML = newCard.innerHTML;
            }
            
            // Execute flash toasts from the response
            const scripts = doc.querySelectorAll('script');
            scripts.forEach(s => {
                if (s.innerText.includes('window.showToast')) {
                    try { eval(s.innerText); } catch(err){}
                }
            });
            
            // Update URL bar if it was a GET or a redirect
            if (res.url && res.url !== window.location.href) {
                window.history.pushState({}, '', res.url);
            } else if (form.method.toUpperCase() === 'GET') {
                window.history.pushState({}, '', url);
            }
            
        } catch(err) {
            console.error('AJAX form error:', err);
            form.submit(); // fallback
        }
    });
});
</script>
</body>
'''

if 'AJAX Form Interceptor' not in content:
    content = content.replace('</body>', ajax_script)
    with open('app/templates/base.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Injected AJAX interceptor into base.html')
else:
    print('Already injected in base.html')


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

for fname in files_to_fix:
    path = os.path.join('app/templates/academics', fname)
    if not os.path.exists(path):
        continue
    with open(path, 'r', encoding='utf-8') as f:
        c = f.read()
    
    if 'class="hau-card ajax-card"' not in c:
        c = c.replace('class="hau-card"', 'class="hau-card ajax-card"')
        with open(path, 'w', encoding='utf-8') as f:
            f.write(c)
        print(f'Enabled AJAX for {fname}')
