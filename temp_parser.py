import os
from bs4 import BeautifulSoup

dir_path = r'D:\hau_erp\Examination Mastere & Config'
files = [f for f in os.listdir(dir_path) if f.endswith('.html')]

for f in files:
    print(f'\n--- {f} ---')
    with open(os.path.join(dir_path, f), 'r', encoding='utf-8', errors='ignore') as html_file:
        soup = BeautifulSoup(html_file, 'html.parser')
        
        # Look for the main content area (usually a specific table or div)
        print('Form Fields:')
        inputs = soup.find_all(['input', 'select', 'textarea'])
        for inp in inputs:
            name = inp.get('name') or inp.get('id')
            type_attr = inp.get('type') or inp.name
            if name and not any(x in name for x in ['VIEWSTATE', 'EVENT', 'Header', 'Footer', 'HiddenField']):
                print(f'  - {name} ({type_attr})')
        
        # Find grid columns
        tables = soup.find_all('table', id=lambda x: x and 'dg' in x.lower())
        for table in tables:
            tid = table.get('id')
            print(f'Grid: {tid}')
            headers = table.find_all('th')
            if not headers:
                first_tr = table.find('tr')
                if first_tr:
                    headers = first_tr.find_all(['td', 'th'])
            cols = [h.text.strip() for h in headers if h.text.strip()]
            print('  Columns:', cols)
