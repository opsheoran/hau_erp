import os, glob, re

academics_dir = r'D:\hau_erp\app\templates\academics'
html_files = glob.glob(os.path.join(academics_dir, '**', '*.html'), recursive=True)

for file in html_files:
    try:
        with open(file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        new_content = content
        
        # Grid Tables
        new_content = new_content.replace('class="grid-table"', 'class="table-grid-view"')
        new_content = new_content.replace('class="grid"', 'class="table-grid-view"')
        
        # Buttons
        new_content = re.sub(r'class="btn [^"]+"', 'class="button-common"', new_content)
        
        # Replace inline styles and older styles where possible
        new_content = new_content.replace("class='grid-table'", 'class="table-grid-view"')
        new_content = new_content.replace("class='grid'", 'class="table-grid-view"')
        new_content = new_content.replace("class='filter-table'", 'class="form-table"')
        
        # Ensure that input type=text without textbox class gets it
        # Actually this can be tricky, so let's skip to avoid breaking things, we already did some replacements
        
        if content != new_content:
            with open(file, 'w', encoding='utf-8') as f:
                f.write(new_content)
    except Exception as e:
        print(f"Error processing {file}: {e}")

print('Applied UI standard classes to grids and buttons.')
