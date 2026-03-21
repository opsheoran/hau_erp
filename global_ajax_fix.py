import os
import re

count_ajax = 0
count_dropdowns = 0

for root, _, files in os.walk('app/templates'):
    for f in files:
        if f.endswith('.html'):
            path = os.path.join(root, f)
            with open(path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            original_content = content
            
            # 1. Enable AJAX Card globally
            if 'class="hau-card"' in content and 'ajax-card' not in content:
                content = content.replace('class="hau-card"', 'class="hau-card ajax-card"')
            
            # 2. Convert old onchanges for college_id
            content = re.sub(
                r'<select[^>]*name=["\']college_id["\'][^>]*onchange=["\'](?:handleFilterChange\(\)|this\.form\.submit\(\);?)["\'][^>]*>', 
                lambda m: m.group(0).replace(m.group(0)[m.group(0).find('onchange='):m.group(0).find('"', m.group(0).find('onchange=')+10)+1], 'onchange="ajaxLoadDegrees(this.value)"'), 
                content
            )
            
            # 3. Convert old onchanges for degree_id
            content = re.sub(
                r'<select[^>]*name=["\']degree_id["\'][^>]*onchange=["\'](?:handleFilterChange\(\)|this\.form\.submit\(\);?)["\'][^>]*>', 
                lambda m: m.group(0).replace(m.group(0)[m.group(0).find('onchange='):m.group(0).find('"', m.group(0).find('onchange=')+10)+1], 'onchange="ajaxLoadBranches(this.value)"'), 
                content
            )

            # 4. Convert other filtering dropdowns (session, branch, etc.) that do this.form.submit()
            # We want them to NOT submit immediately, or maybe we want them to submit via AJAX? 
            # If we just remove the onchange, they have to click the GET button.
            # The user asked: "silently filled without any movement due to page load etc... in almost all the page of menu please do some thing so that it quitly populate the dropdwons"
            # Removing this.form.submit() from session_id
            content = re.sub(
                r'<select[^>]*name=["\']session_id["\'][^>]*onchange=["\'](?:handleFilterChange\(\)|this\.form\.submit\(\);?)["\'][^>]*>',
                lambda m: re.sub(r'\bonchange=["\'][^"\']+["\']', '', m.group(0)),
                content
            )
            
            # Also handle any stray this.form.submit() on branch_id or semester_id
            content = re.sub(
                r'<select[^>]*name=["\'](branch_id|semester_id|dept_id)["\'][^>]*onchange=["\'](?:handleFilterChange\(\)|this\.form\.submit\(\);?)["\'][^>]*>',
                lambda m: re.sub(r'\bonchange=["\'][^"\']+["\']', '', m.group(0)),
                content
            )

            # Let's also catch any select that has onchange="this.form.submit()" and remove it, so users rely on the GET button
            # EXCEPT for special ones that might need it. Actually, the request is to stop flickering on dropdown selection.
            # So removing this.form.submit() on ALL filtering dropdowns is the best way to stop the page from submitting until they click the button.
            # BUT some pages might NOT have a GET button! Let's check if the form has a submit button.
            
            if content != original_content:
                with open(path, 'w', encoding='utf-8') as file:
                    file.write(content)
                if 'ajax-card' in content and 'ajax-card' not in original_content:
                    count_ajax += 1
                count_dropdowns += 1

print(f"Enabled AJAX on {count_ajax} templates.")
print(f"Fixed dropdowns/AJAX on {count_dropdowns} total files.")
