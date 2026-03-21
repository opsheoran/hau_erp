import re
with open('D:/hau_erp/Marks Process/Student Marks Process For PG_PHD(pass).html', 'r', encoding='utf-8') as f:
    content = f.read()
    
    col = re.search(r'D_ddlCollege.*?selected="selected" value="([^"]+)"', content, re.DOTALL)
    print('College:', col.group(1) if col else 'None')
    
    sess = re.search(r'D_ddlAcdSession.*?value="([^"]+)"', content, re.DOTALL)
    print('Session:', sess.group(1) if sess else 'None')
    
    deg = re.search(r'D_ddlDegree.*?value="([^"]+)"', content, re.DOTALL)
    print('Degree:', deg.group(1) if deg else 'None')
    
    sem = re.search(r'D_ddlSemester.*?selected="selected" value="([^"]+)"', content, re.DOTALL)
    print('Semester:', sem.group(1) if sem else 'None')
    
    branch = re.search(r'ddlBranch.*?selected="selected" value="([^"]+)"', content, re.DOTALL)
    print('Branch:', branch.group(1) if branch else 'None')
