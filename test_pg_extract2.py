import re
with open('D:/hau_erp/Marks Process/Student Marks Process For PG_PHD(pass).html', 'r', encoding='utf-8') as f:
    content = f.read()
    
    sess = re.search(r'D_ddlAcdSession.*?<option.*?value="([^"]+)">2025-2026', content, re.DOTALL)
    print('Session (from text):', sess.group(1) if sess else 'None')
    
    deg = re.search(r'D_ddlDegree.*?<option.*?value="([^"]+)">(.*?)</option>', content, re.DOTALL)
    print('Degree:', deg.group(1), deg.group(2) if deg else 'None')
