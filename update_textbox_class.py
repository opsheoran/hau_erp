import os, glob, re

academics_dir = r'D:\hau_erp\app\templates\academics'
html_files = glob.glob(os.path.join(academics_dir, '**', '*.html'), recursive=True)

replaced_count = 0
for file in html_files:
    try:
        with open(file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        new_content = content
        
        # Add textbox class to input type text, date, number if it's missing
        # We need a function to replace it without messing up existing classes
        def add_textbox_class(match):
            tag = match.group(0)
            if 'class=' in tag:
                if 'textbox' not in tag:
                    return re.sub(r'class="([^"]*)"', r'class="\1 textbox"', tag)
                return tag
            else:
                return tag.replace('<input ', '<input class="textbox" ')

        # Match inputs
        new_content = re.sub(r'<input[^>]+type="(?:text|date|number)"[^>]*>', add_textbox_class, new_content)
        
        # Match selects that are missing textbox class
        def add_select_class(match):
            tag = match.group(0)
            if 'class=' in tag:
                if 'textbox' not in tag:
                    return re.sub(r'class="([^"]*)"', r'class="\1 textbox"', tag)
                return tag
            else:
                return tag.replace('<select ', '<select class="textbox" ')
                
        new_content = re.sub(r'<select[^>]*>', add_select_class, new_content)

        if content != new_content:
            with open(file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            replaced_count += 1
            
    except Exception as e:
        print(f"Error processing {file}: {e}")

print(f"Added .textbox class to inputs/selects in {replaced_count} files.")
