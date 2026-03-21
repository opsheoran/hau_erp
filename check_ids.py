import re

with open('app/templates/academics/student_biodata.html', 'r', encoding='utf-8') as f:
    html = f.read()

ids_in_js = re.findall(r"document\.getElementById\('([^']+)'\)\.value", html)
ids_in_js += re.findall(r"document\.getElementById\('([^']+)'\)\.checked", html)
ids_in_html = re.findall(r"id=['\"]([^'\"]+)['\"]", html)

for id in set(ids_in_js):
    if id not in ids_in_html:
        print(f'Missing ID: {id}')
