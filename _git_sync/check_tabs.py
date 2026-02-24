with open('app/models/nav.py', 'r') as f:
    for i, line in enumerate(f, 1):
        if '	' in line:
            print(f"Tab found on line {i}")
