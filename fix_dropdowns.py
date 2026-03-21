import os

folder = r'D:\hau_erp\app\templates\examination'
files = [
    'degree_exam_master.html',
    'exam_config_master.html',
    'degree_exam_wise_weightage.html',
    'external_examiner_detail.html',
    'update_weightage_post_marks_entry.html'
]

for f in files:
    path = os.path.join(folder, f)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        content = content.replace('d.pk_degreeid', 'd.id')
        content = content.replace('d.degreename', 'd.name')
        content = content.replace('s.pk_sessionid', 's.id')
        content = content.replace('s.sessionname', 's.name')

        with open(path, 'w', encoding='utf-8') as file:
            file.write(content)
        print(f"Updated {f}")
