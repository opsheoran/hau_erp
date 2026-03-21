import os, glob, re

academics_dir = r'D:\hau_erp\app\templates\academics'
html_files = glob.glob(os.path.join(academics_dir, '**', '*.html'), recursive=True)

replaced_count = 0
for file in html_files:
    try:
        with open(file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Regex to match <div class="pager-style">...</div>
        # Use DOTALL to match across newlines.
        new_content = re.sub(
            r'<div\s+class=["\']pager-style["\'][^>]*>.*?</div>',
            '{% include "includes/pagination.html" %}',
            content,
            flags=re.DOTALL
        )
        
        if content != new_content:
            with open(file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            replaced_count += 1
            
    except Exception as e:
        print(f"Error processing {file}: {e}")

print(f"Replaced inline pagination in {replaced_count} files.")
