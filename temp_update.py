import re

with open('app/blueprints/examination/student_marks_entry_coe.py', 'r') as f:
    coe_code = f.read()

# Extract the main function
match = re.search(r"@examination_bp\.route\('/student_marks_entry_coe', methods=\['GET', 'POST'\]\)\n@permission_required\('Student Marks Entry\(@COE\)'\)\ndef student_marks_entry_coe\(\):(.*?)@examination_bp", coe_code, re.DOTALL)
if match:
    func_body = match.group(0).rsplit("@examination_bp", 1)[0]
    
    routes = [
        ('student_marks_entry_ug', 'Student Marks Entry(UG and MBA)'),
        ('student_marks_entry_pg_phd', 'Student Marks Entry(PG/PHD) By Teacher'),
        ('student_marks_entry_re_evaluation', 'Student Marks Entry(Re-Evaluation)'),
        ('student_marks_entry_supplementary', 'Student Marks Entry(Supplementary)'),
    ]
    
    for route_name, perm_name in routes:
        new_func = func_body.replace('student_marks_entry_coe', route_name).replace('Student Marks Entry(@COE)', perm_name)
        new_code = f'''from flask import render_template, request, redirect, url_for, flash, session, jsonify
from app.blueprints.examination import examination_bp, permission_required
from app.models.examination import ExaminationModel
from app.models import AcademicsModel, InfrastructureModel
from app.db import DB
from app.utils import get_pagination
import json

{new_func}
'''
        with open(f'app/blueprints/examination/{route_name}.py', 'w') as f2:
            f2.write(new_code)
        
        print(f"Updated {route_name}.py")
