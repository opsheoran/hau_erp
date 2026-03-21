import os
from bs4 import BeautifulSoup

with open(r'D:\hau_erp\Examination Mastere & Config\Exam Config Master.html', 'r', encoding='utf-8', errors='ignore') as f:
    soup = BeautifulSoup(f, 'html.parser')
    for inp in soup.find_all(['input', 'select']):
        name = inp.get('name') or inp.get('id')
        if name and not 'VIEWSTATE' in name and not 'EVENT' in name:
            print(f"{name} ({inp.get('type') or inp.name})")
