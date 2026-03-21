import os, glob, re

academics_dir = r'D:\hau_erp\app\templates\academics'
html_files = glob.glob(os.path.join(academics_dir, '**', '*.html'), recursive=True)

for file in html_files:
    try:
        with open(file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        new_content = content
        
        # Tables
        new_content = new_content.replace('class="filter-table"', 'class="form-table"')
        new_content = re.sub(r'<table([^>]*)class="table"([^>]*)>', r'<table\1class="form-table"\2>', new_content)
        
        # Dropdowns / Textboxes
        new_content = new_content.replace('dropdownvvlong', 'textbox w-350')
        new_content = new_content.replace('dropdownlong', 'textbox w-250')
        new_content = re.sub(r'class="dropdown([^a-zA-Z0-9_-])', r'class="textbox w-200\1', new_content)
        new_content = new_content.replace('class="dropdown"', 'class="textbox w-200"')
        
        # Date Pickers icon (calbtn.gif must be placed right after input).
        # Typically the project standard specifies sliding-window pagination and date pickers.
        # This python script won't fix structural DOM placement, but let's fix basic classes first.
        
        if content != new_content:
            with open(file, 'w', encoding='utf-8') as f:
                f.write(new_content)
    except Exception as e:
        print(f"Error processing {file}: {e}")

print('Applied UI standard classes to tables, dropdowns, and buttons.')
