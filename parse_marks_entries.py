import os
from bs4 import BeautifulSoup

folder = r'D:\hau_erp\Marks Entries'
files = [f for f in os.listdir(folder) if f.endswith('.html')]

for f in files:
    path = os.path.join(folder, f)
    print(f'\n================== {f} ==================')
    with open(path, 'r', encoding='utf-8', errors='ignore') as html_file:
        soup = BeautifulSoup(html_file, 'html.parser')
        
        print('--- Form Fields ---')
        for inp in soup.find_all(['input', 'select']):
            name = inp.get('name') or inp.get('id')
            type_attr = inp.get('type') or inp.name
            if name and not any(x in name for x in ['VIEWSTATE', 'EVENT', 'Header', 'Footer', 'HiddenField']):
                print(f"{name} ({type_attr})")
                
        print('--- Grids ---')
        for table in soup.find_all('table', id=lambda x: x and ('dg' in x.lower() or 'gv' in x.lower())):
            print('Grid ID:', table.get('id'))
            headers = table.find_all('th')
            if not headers:
                tr = table.find('tr')
                if tr: headers = tr.find_all(['td', 'th'])
            print('Columns:', [h.text.strip() for h in headers if h.text.strip()])
