import re
with open('Post-Examination Activities/Student Marks Entry(UG and MBA).html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

matches = re.findall(r'<td\s+[^>]*class=["\']vtext["\'][^>]*>(.*?)</td>', text, re.DOTALL | re.IGNORECASE)
for m in matches:
    print(re.sub(r'<[^>]+>', '', m).strip())
