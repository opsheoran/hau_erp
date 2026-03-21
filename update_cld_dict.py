import os

with open('app/blueprints/examination/marks_process_ug_mba.py', 'r', encoding='utf-8') as f:
    code = f.read()

old_logic = """            'gp': f"{float(gp):.3f}" if gp is not None else '', 
            'cp': f"{float(cp):.2f}" if cp is not None else '',
            'gpa': f"{float(gpa):.3f}" if gpa is not None else '',
            'ogpa': f"{float(ogpa):.3f}" if ogpa is not None else '',"""

new_logic = """            'gp': f"{float(gp):.3f}" if gp is not None and str(gp).strip() != '' else '', 
            'cp': f"{float(cp):.2f}" if cp is not None and str(cp).strip() != '' else '',
            'gpa': f"{float(gpa):.3f}" if gpa is not None and str(gpa).strip() != '' else '',
            'ogpa': f"{float(ogpa):.3f}" if ogpa is not None and str(ogpa).strip() != '' else '0.000',"""

if old_logic in code:
    code = code.replace(old_logic, new_logic)
    with open('app/blueprints/examination/marks_process_ug_mba.py', 'w', encoding='utf-8') as f:
        f.write(code)
    print('Fixed string formatting')
else:
    print('Failed to fix formatting')