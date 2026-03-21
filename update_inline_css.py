import os

with open('app/templates/student_portal/profile.html', 'r', encoding='utf-8') as f:
    content = f.read()

old_css = """
    .info-group {
        margin-bottom: 5px;
    }

    .info-label {
        font-size: 12px;
        color: #777;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 4px;
    }

    .info-value {
        font-size: 15px;
        color: #333;
        font-weight: 500;
    }
"""

new_css = """
    .info-group {
        margin-bottom: 8px;
        display: flex;
        align-items: baseline;
    }

    .info-label {
        font-size: 13px;
        color: #555;
        font-weight: 500;
        width: 200px;
        flex-shrink: 0;
    }

    .info-label::after {
        content: " :";
        margin-right: 10px;
    }

    .info-value {
        font-size: 14px;
        color: #111;
        flex: 1;
    }
"""

content = content.replace(old_css, new_css)
with open('app/templates/student_portal/profile.html', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated CSS to inline styles')
