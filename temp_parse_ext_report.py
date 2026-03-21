import os
from bs4 import BeautifulSoup
with open(r'D:\hau_erp\Examination Mastere & Config\External Examinars Report.html', 'r', encoding='utf-8', errors='ignore') as f:
    soup = BeautifulSoup(f, 'html.parser')
    for inp in soup.find_all(['input', 'select']):
        name = inp.get('name') or inp.get('id')
        if name and not 'VIEWSTATE' in name and not 'EVENT' in name:
            print(f"{name} ({inp.get('type') or inp.name})")
    print('--- Grids ---')
    for table in soup.find_all('table', id=lambda x: x and ('dg' in x.lower() or 'gv' in x.lower())):
        print('Grid:', table.get('id'))
        headers = table.find_all('th')
        if not headers:
            tr = table.find('tr')
            if tr: headers = tr.find_all(['td', 'th'])
        print('Columns:', [h.text.strip() for h in headers if h.text.strip()])
