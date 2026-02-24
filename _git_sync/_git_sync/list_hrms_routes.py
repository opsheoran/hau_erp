import re
with open('app/blueprints/hrms.py', 'r') as f:
    for line in f:
        if '@hrms_bp.route' in line:
            print(line.strip())
