import os
from bs4 import BeautifulSoup
with open(r'D:\hau_erp\Marks Entries\Student Marks Entry (@COE).html', 'r', encoding='utf-8', errors='ignore') as f:
    soup = BeautifulSoup(f, 'html.parser')
    for inp in soup.find_all(['input', 'select']):
        name = inp.get('name') or inp.get('id')
        if name and not 'VIEWSTATE' in name and not 'EVENT' in name:
            print(f"{name} ({inp.get('type') or inp.name})")
    
    print('\n--- GRIDS ---')
    for table in soup.find_all('table', id=lambda x: x and ('gv' in x.lower() or 'dg' in x.lower())):
        print(f"Grid: {table.get('id')}")
        trs = table.find_all('tr')
        if trs:
            headers = [th.text.strip() for th in trs[0].find_all(['th', 'td'])]
            print("Headers:", headers)
            if len(trs) > 1:
                row_inputs = [inp.get('type') or inp.name for inp in trs[1].find_all(['input', 'select'])]
                print("Row inputs:", row_inputs)
