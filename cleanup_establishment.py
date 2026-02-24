import re
import os

with open('app/blueprints/establishment.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

marker = '# --- RESTORED MASTERS ---'
marker_idx = -1
for i, line in enumerate(lines):
    if marker in line:
        marker_idx = i
        break

if marker_idx != -1:
    new_lines = lines[:marker_idx+1]
    restored_lines = lines[marker_idx+1:]
    
    # Identify routes in the first part
    existing_routes = set()
    for line in lines[:marker_idx]:
        match = re.search(r"@establishment_bp\.route\('([^']+)'", line)
        if match:
            existing_routes.add(match.group(1))
    
    # Process restored part
    i = 0
    while i < len(restored_lines):
        line = restored_lines[i]
        
        # Check if line starts with @establishment_bp.route
        if line.strip().startswith('@establishment_bp.route'):
            # It might be a multiline route definition, but usually it's single line here
            match = re.search(r"@establishment_bp\.route\('([^']+)'", line)
            if match:
                route_path = match.group(1)
                # Find the end of this block (including decorators and function)
                block_start = i
                # Look ahead for the 'def ' line
                while i < len(restored_lines) and not restored_lines[i].strip().startswith('def '):
                    i += 1
                
                if i < len(restored_lines):
                    # Find end of function
                    i += 1
                    while i < len(restored_lines) and not (restored_lines[i].strip().startswith('@') or restored_lines[i].strip().startswith('def ')):
                        i += 1
                    block_end = i
                    
                    if route_path not in existing_routes:
                        new_lines.extend(restored_lines[block_start:block_end])
                    # No else, if duplicate we just skip it
                    continue
        
        # If it's a def that is not a route (helper like manage_master)
        if line.strip().startswith('def '):
            func_name = line.strip().split('(')[0].split('def ')[1].strip()
            # check if it is already in new_lines
            if not any(f'def {func_name}(' in l for l in new_lines):
                 h_start = i
                 i += 1
                 while i < len(restored_lines) and not (restored_lines[i].strip().startswith('@') or restored_lines[i].strip().startswith('def ')):
                     i += 1
                 new_lines.extend(restored_lines[h_start:i])
                 continue
        
        i += 1
            
    with open('app/blueprints/establishment.py', 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    print("Cleanup successful.")
else:
    print("Marker not found.")
