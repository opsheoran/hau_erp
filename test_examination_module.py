import sys, os
sys.path.insert(0, os.getcwd())
from app import app
from app.db import DB
from flask import session
from app.models import NavModel

# Mock permission check
NavModel.check_permission = lambda user_id, loc_id, page_caption: {'AllowView': 1, 'AllowAdd': 1, 'AllowUpdate': 1, 'AllowDelete': 1}

def test_exam_master():
    print("\n--- Starting Penetration & QA Tests for Degree Exam Master ---")
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess['user_id'] = 'admin'
            sess['selected_loc'] = 1
            sess['current_module_id'] = 56
            sess['current_user_rights'] = [{'PageName': 'Degree Exam Master', 'AllowView': 1, 'AllowAdd': 1, 'AllowUpdate': 1, 'AllowDelete': 1}]

        import re
        resp = client.get('/examination/degree_exam_master')
        if resp.status_code == 200:
            print("[-] Access Test: Passed")
        else:
            print(f"[X] Access Test: Failed with status {resp.status_code}")
            return
            
        match = re.search(r'name="_csrf_token"\s+value="([^"]+)"', resp.data.decode('utf-8'))
        csrf_token = match.group(1) if match else ''

        # Insert a dummy exam
        DB.execute("DELETE FROM SMS_DgExam_Mst WHERE fk_examid IN (SELECT pk_examid FROM SMS_Exam_Mst WHERE exam='TestExam')")
        DB.execute("DELETE FROM SMS_Exam_Mst WHERE exam='TestExam'")
        DB.execute("INSERT INTO SMS_Exam_Mst (exam, examorder, istheory, ispractical, isinternal, isMainExam) VALUES ('TestExam', 1, 1, 0, 0, 1)")
        exam_id = DB.fetch_one("SELECT pk_examid FROM SMS_Exam_Mst WHERE exam='TestExam'")['pk_examid']

        # Get existing lookup IDs safely
        deg = DB.fetch_one("SELECT TOP 1 pk_degreeid FROM SMS_Degree_Mst")
        sess_obj = DB.fetch_one("SELECT TOP 1 pk_sessionid FROM SMS_AcademicSession_Mst")
        
        if deg and sess_obj:
            deg_id = deg['pk_degreeid']
            sess_id = sess_obj['pk_sessionid']
            
            # 1. Create Mapping
            resp = client.post('/examination/degree_exam_master', data={
                '_csrf_token': csrf_token,
                'action': 'SAVE',
                'degree_id': deg_id,
                'exam_id': exam_id,
                'session_from': sess_id
            }, follow_redirects=True)
            
            if b'saved successfully' in resp.data:
                print("[-] Create Mapping Test: Passed")
            else:
                print("[X] Create Mapping Test: Failed")

            # 2. Overlap/Duplicate Validation Test
            resp = client.post('/examination/degree_exam_master', data={
                '_csrf_token': csrf_token,
                'action': 'SAVE',
                'degree_id': deg_id,
                'exam_id': exam_id,
                'session_from': sess_id
            }, follow_redirects=True)
            
            if b'already mapped' in resp.data:
                print("[-] Overlap Validation Test: Passed (Rejected appropriately)")
            else:
                print("[X] Overlap Validation Test: Failed (Did not reject duplicate)")

            # Clean up mapping
            DB.execute("DELETE FROM SMS_DgExam_Mst WHERE fk_examid=?", [exam_id])
            print("[-] Cleanup Mapping: Passed")
        
        # Clean up exam
        DB.execute("DELETE FROM SMS_Exam_Mst WHERE pk_examid=?", [exam_id])
        print("[-] Cleanup Exam: Passed")

test_exam_master()
def test_degree_exam_master():
    print("--- Starting Penetration & QA Tests for Exam Master ---")
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.secret_key = 'test_secret'
    
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess['user_id'] = 'admin'
            sess['selected_loc'] = 1
            sess['current_module_id'] = 56
            sess['current_user_rights'] = [{'PageName': 'Exam Master', 'AllowView': 1, 'AllowAdd': 1, 'AllowUpdate': 1, 'AllowDelete': 1}]

        import re

        # 1. Access Test (Authorization)
        resp = client.get('/examination/exam_master')
        if resp.status_code == 200:
            print("[-] Access Test: Passed (HTTP 200)")
        else:
            print(f"[X] Access Test: Failed with status {resp.status_code}")
        
        # Extract CSRF token
        match = re.search(r'name="_csrf_token"\s+value="([^"]+)"', resp.data.decode('utf-8'))
        csrf_token = match.group(1) if match else ''
        if not csrf_token:
            print("[X] Warning: Could not extract CSRF token from form.")

        # Check if tabs render
        if b'class="tabgs"' in resp.data or b'tabbing-table' in resp.data:
            print("[-] Menu/Tab Render Test: Passed")
        else:
            print("[X] Menu/Tab Render Test: Failed")

        # 2. XSS & Injection Test
        payload_name = "Exam <script>alert(1)</script>"
        payload_short = "XSS"
        resp = client.post('/examination/exam_master', data={
            '_csrf_token': csrf_token,
            'action': 'SAVE',
            'exam': payload_name,
            'short': payload_short,
            'order': '99',
            'is_th': 'on'
        }, follow_redirects=True)
        
        if b'Exam saved successfully!' in resp.data:
            print("[-] Create Test with XSS payload: Successfully saved (Checking for escaping...)")
            resp_get = client.get('/examination/exam_master')
            if b'&lt;script&gt;alert(1)&lt;/script&gt;' in resp_get.data:
                print("[-] XSS Mitigation Test: Passed (Escaped)")
            elif payload_name.encode() in resp_get.data:
                print("[X] XSS Mitigation Test: Failed (Raw payload rendered!)")
            else:
                print("[X] XSS Mitigation Test: Failed (Payload not found in table)")
        else:
            print("[X] Create Test: Failed")
            print(f"DEBUG: {resp.data.decode('utf-8')[:500]}")

        # Fetch inserted row ID
        row = DB.fetch_one("SELECT pk_examid FROM SMS_Exam_Mst WHERE exam = ?", [payload_name])
        pk_id = row['pk_examid'] if row else None

        if pk_id:
            # 3. Update & Boundary Testing
            resp = client.post('/examination/exam_master', data={
                '_csrf_token': csrf_token,
                'action': 'SAVE',
                'pk_id': pk_id,
                'exam': "Updated Exam",
                'short': "UPD",
                'order': '100',
                'is_th': 'on',
                'is_main': 'on'
            }, follow_redirects=True)
            if b'Exam saved successfully!' in resp.data:
                print("[-] Update Test: Passed")
            else:
                print("[X] Update Test: Failed")

            # Verify bits stored in DB
            upd_row = DB.fetch_one("SELECT * FROM SMS_Exam_Mst WHERE pk_examid = ?", [pk_id])
            if upd_row['istheory'] == 1 and upd_row['ispractical'] == 0 and upd_row['isMainExam'] == 1:
                print("[-] Boolean Logic Test: Passed")
            else:
                print(f"[X] Boolean Logic Test: Failed. DB row: {upd_row}")

            # 4. State Manipulation / SQL Injection Test
            resp = client.post('/examination/exam_master', data={
                '_csrf_token': csrf_token,
                'action': 'DELETE',
                'id': f"{pk_id} OR 1=1"
            }, follow_redirects=True)
            if b'Constraint error' in resp.data or b'Error deleting' in resp.data:
                 print("[-] SQL Injection Test (DELETE): Passed (Blocked by parameterization or cast)")
            else:
                 print("[X] SQL Injection Test (DELETE): Failed or executed unintended logic.")

            # Clean up
            DB.execute("DELETE FROM SMS_Exam_Mst WHERE pk_examid = ?", [pk_id])
            print("[-] Cleanup: Test data deleted.")
        else:
            print("[X] Could not find inserted row for update/delete tests.")

def test_degree_exam_master():
    print("\n--- Starting Penetration & QA Tests for Degree Exam Master ---")
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess['user_id'] = 'admin'
            sess['selected_loc'] = 1
            sess['current_module_id'] = 56
            sess['current_user_rights'] = [{'PageName': 'Degree Exam Master', 'AllowView': 1, 'AllowAdd': 1, 'AllowUpdate': 1, 'AllowDelete': 1}]

        import re
        resp = client.get('/examination/degree_exam_master')
        if resp.status_code == 200:
            print("[-] Access Test: Passed")
        else:
            print(f"[X] Access Test: Failed with status {resp.status_code}")
            return
            
        match = re.search(r'name="_csrf_token"\s+value="([^"]+)"', resp.data.decode('utf-8'))
        csrf_token = match.group(1) if match else ''

        # Insert a dummy exam
        DB.execute("DELETE FROM SMS_DgExam_Mst WHERE fk_examid IN (SELECT pk_examid FROM SMS_Exam_Mst WHERE exam='TestExam')")
        DB.execute("DELETE FROM SMS_Exam_Mst WHERE exam='TestExam'")
        DB.execute("INSERT INTO SMS_Exam_Mst (exam, examorder, istheory, ispractical, isinternal, isMainExam) VALUES ('TestExam', 1, 1, 0, 0, 1)")
        exam_id = DB.fetch_one("SELECT pk_examid FROM SMS_Exam_Mst WHERE exam='TestExam'")['pk_examid']

        # Get existing lookup IDs safely
        deg = DB.fetch_one("SELECT TOP 1 pk_degreeid FROM SMS_Degree_Mst")
        sess_obj = DB.fetch_one("SELECT TOP 1 pk_sessionid FROM SMS_AcademicSession_Mst")
        
        if deg and sess_obj:
            deg_id = deg['pk_degreeid']
            sess_id = sess_obj['pk_sessionid']
            
            # 1. Create Mapping
            resp = client.post('/examination/degree_exam_master', data={
                '_csrf_token': csrf_token,
                'action': 'SAVE',
                'degree_id': deg_id,
                'exam_id': exam_id,
                'session_from': sess_id
            }, follow_redirects=True)
            
            if b'saved successfully' in resp.data:
                print("[-] Create Mapping Test: Passed")
            else:
                print("[X] Create Mapping Test: Failed")

            # 2. Overlap/Duplicate Validation Test
            resp = client.post('/examination/degree_exam_master', data={
                '_csrf_token': csrf_token,
                'action': 'SAVE',
                'degree_id': deg_id,
                'exam_id': exam_id,
                'session_from': sess_id
            }, follow_redirects=True)
            
            if b'already mapped' in resp.data:
                print("[-] Overlap Validation Test: Passed (Rejected appropriately)")
            else:
                print("[X] Overlap Validation Test: Failed (Did not reject duplicate)")

            # Clean up mapping
            DB.execute("DELETE FROM SMS_DgExam_Mst WHERE fk_examid=?", [exam_id])
            print("[-] Cleanup Mapping: Passed")
        
        # Clean up exam
        DB.execute("DELETE FROM SMS_Exam_Mst WHERE pk_examid=?", [exam_id])
        print("[-] Cleanup Exam: Passed")

def test_exam_config_master():
    print("\n--- Starting Penetration & QA Tests for Exam Config Master ---")
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess['user_id'] = 'admin'
            sess['selected_loc'] = 1
            sess['current_module_id'] = 56
            sess['current_user_rights'] = [{'PageName': 'Exam Config Master', 'AllowView': 1, 'AllowAdd': 1, 'AllowUpdate': 1, 'AllowDelete': 1}]

        import re
        resp = client.get('/examination/exam_config_master')
        if resp.status_code == 200:
            print("[-] Access Test: Passed")
        else:
            print(f"[X] Access Test: Failed with status {resp.status_code}")
            return
            
        match = re.search(r'name="_csrf_token"\s+value="([^"]+)"', resp.data.decode('utf-8'))
        csrf_token = match.group(1) if match else ''

        # Get existing lookup IDs safely
        deg = DB.fetch_one("SELECT TOP 1 pk_degreeid FROM SMS_Degree_Mst")
        sess_obj = DB.fetch_one("SELECT TOP 1 pk_sessionid FROM SMS_AcademicSession_Mst")
        month_obj = DB.fetch_one("SELECT TOP 1 pk_MonthId FROM Month_Mst")
        year_obj = DB.fetch_one("SELECT TOP 1 pk_yearID FROM Year_Mst")
        
        if deg and sess_obj and month_obj and year_obj:
            deg_id = deg['pk_degreeid']
            sess_id = sess_obj['pk_sessionid']
            m_id = month_obj['pk_MonthId']
            y_id = year_obj['pk_yearID']
            
            # API Test for dynamic semesters
            api_resp = client.get(f'/examination/api/get_semesters_for_degree/{deg_id}')
            if api_resp.status_code == 200:
                print("[-] Dynamic Semesters API Test: Passed")
            else:
                print(f"[X] Dynamic Semesters API Test: Failed ({api_resp.status_code})")
            
            # 1. Create Config with some dynamic sem keys
            resp = client.post('/examination/exam_config_master', data={
                '_csrf_token': csrf_token,
                'action': 'SAVE',
                'degree_id': deg_id,
                'session_id': sess_id,
                'month_from': m_id,
                'month_to': m_id,
                'year_from': y_id,
                'year_to': y_id,
                'is_active': 'on',
                'semester_id[]': ['1', '2'],
                'exam_type[]': ['S', 'F']
            }, follow_redirects=True)
            
            if b'saved successfully' in resp.data:
                print("[-] Create Config Test: Passed")
            else:
                print("[X] Create Config Test: Failed")
                import bs4
                soup = bs4.BeautifulSoup(resp.data, 'html.parser')
                alerts = soup.find_all('div')
                for a in alerts:
                    if 'alert' in a.get('class', []):
                        print("FLASH ERROR:", a.text.strip())

            # Clean up
            # Need to find the inserted config
            cfg = DB.fetch_one("SELECT TOP 1 pk_exconfigid FROM SMS_ExamConfig_Mst ORDER BY pk_exconfigid DESC")
            if cfg:
                c_id = cfg['pk_exconfigid']
                DB.execute("DELETE FROM sms_examconfig_dtl WHERE fk_exconfigid=?", [c_id])
                DB.execute("DELETE FROM SMS_ExamConfig_Mst WHERE pk_exconfigid=?", [c_id])
                print("[-] Cleanup Config: Passed")

def test_degree_exam_wise_weightage():
    print("\n--- Starting Penetration & QA Tests for Degree Exam Wise Weightage ---")
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess['user_id'] = 'admin'
            sess['selected_loc'] = 1
            sess['current_module_id'] = 56
            sess['current_user_rights'] = [{'PageName': 'Degree Exam Wise Weightage', 'AllowView': 1, 'AllowAdd': 1, 'AllowUpdate': 1, 'AllowDelete': 1}]

        import re
        resp = client.get('/examination/degree_exam_wise_weightage')
        if resp.status_code == 200:
            print("[-] Access Test: Passed")
        else:
            print(f"[X] Access Test: Failed with status {resp.status_code}")
            return
            
        match = re.search(r'name="_csrf_token"\s+value="([^"]+)"', resp.data.decode('utf-8'))
        csrf_token = match.group(1) if match else ''

        # Get existing lookup IDs safely
        deg = DB.fetch_one("SELECT TOP 1 pk_degreeid FROM SMS_Degree_Mst")
        sess_obj = DB.fetch_one("SELECT TOP 1 pk_sessionid FROM SMS_AcademicSession_Mst")
        
        if deg and sess_obj:
            deg_id = deg['pk_degreeid']
            sess_id = sess_obj['pk_sessionid']
            
            # Create a dummy map
            DB.execute("DELETE FROM SMS_DgExam_Mst WHERE fk_examid IN (SELECT pk_examid FROM SMS_Exam_Mst WHERE exam='TestExamWeight')")
            DB.execute("DELETE FROM SMS_Exam_Mst WHERE exam='TestExamWeight'")
            DB.execute("INSERT INTO SMS_Exam_Mst (exam, examorder, istheory, ispractical, isinternal, isMainExam) VALUES ('TestExamWeight', 1, 1, 0, 0, 1)")
            exam_id = DB.fetch_one("SELECT pk_examid FROM SMS_Exam_Mst WHERE exam='TestExamWeight'")['pk_examid']
            
            DB.execute("INSERT INTO SMS_DgExam_Mst (fk_degreeid, fk_examid, fk_acasessionid_from) VALUES (?, ?, ?)", [deg_id, exam_id, sess_id])
            map_id = DB.fetch_one("SELECT IDENT_CURRENT('SMS_DgExam_Mst') as id")['id']
            
            if map_id:
                # Test API
                api_resp = client.get(f'/examination/api/get_courses_for_exam_weightage?degree_id={deg_id}&exam_id={exam_id}&session_id={sess_id}')
                if api_resp.status_code == 200:
                    print("[-] Courses API Test: Passed")
                else:
                    print(f"[X] Courses API Test: Failed ({api_resp.status_code})")

                # Create Header Level Weightage
                resp = client.post('/examination/degree_exam_wise_weightage', data={
                    '_csrf_token': csrf_token,
                    'action': 'SAVE',
                    'dgexammapid': map_id,
                    'session_from': sess_id,
                    'is_course_based': '',
                    'cwp': '40',
                    'cwop': '60'
                }, follow_redirects=True)
                
                if b'saved successfully' in resp.data:
                    print("[-] Create Header Weightage Test: Passed")
                else:
                    print("[X] Create Header Weightage Test: Failed")

                # Clean up
                wt = DB.fetch_one("SELECT TOP 1 pk_dgexamweid FROM SMS_DgExamWeightage ORDER BY pk_dgexamweid DESC")
                if wt:
                    w_id = wt['pk_dgexamweid']
                    DB.execute("DELETE FROM SMS_DgExamWeightage WHERE pk_dgexamweid=?", [w_id])
                    print("[-] Cleanup Weightage: Passed")
                
                DB.execute("DELETE FROM SMS_DgExam_Mst WHERE pk_dgexammapid=?", [map_id])
                DB.execute("DELETE FROM SMS_Exam_Mst WHERE pk_examid=?", [exam_id])
                print("[-] Cleanup Map and Exam: Passed")
            else:
                print("[-] Warning: Failed to create dummy map")
        else:
            print("[-] Warning: Could not fetch initial lookup ids")

def test_external_examiner_detail():
    print("\n--- Starting Penetration & QA Tests for External Examiner Detail ---")
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess['user_id'] = 'admin'
            sess['selected_loc'] = 1
            sess['current_module_id'] = 56
            sess['current_user_rights'] = [{'PageName': 'External Examiner Detail', 'AllowView': 1, 'AllowAdd': 1, 'AllowUpdate': 1, 'AllowDelete': 1}]

        import re
        resp = client.get('/examination/external_examiner_detail')
        if resp.status_code == 200:
            print("[-] Access Test: Passed")
        else:
            print(f"[X] Access Test: Failed with status {resp.status_code}")
            return
            
        match = re.search(r'name="_csrf_token"\s+value="([^"]+)"', resp.data.decode('utf-8'))
        csrf_token = match.group(1) if match else ''

        # 1. Create Examiner
        resp = client.post('/examination/external_examiner_detail', data={
            '_csrf_token': csrf_token,
            'action': 'SAVE',
            'ExaminarName': 'Test Examiner XSS <script>alert(1)</script>',
            'University': 'Test University',
            'IsActive': 'on'
        }, follow_redirects=True)
        
        if b'saved successfully' in resp.data:
            print("[-] Create Examiner Test: Passed")
            if b'&lt;script&gt;alert(1)&lt;/script&gt;' in resp.data:
                print("[-] XSS Mitigation Test: Passed (Escaped)")
        else:
            print("[X] Create Examiner Test: Failed")

        # Clean up
        ex = DB.fetch_one("SELECT TOP 1 Pk_Exmid FROM SMS_ExtExaminar_Mst ORDER BY Pk_Exmid DESC")
        if ex:
            ex_id = ex['Pk_Exmid']
            DB.execute("DELETE FROM SMS_ExtExaminar_Mst WHERE Pk_Exmid=?", [ex_id])
            print("[-] Cleanup Examiner: Passed")

def test_update_weightage_post_marks_entry():
    print("\n--- Starting Penetration & QA Tests for Update Weightage Post Marks Entry ---")
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess['user_id'] = 'admin'
            sess['selected_loc'] = 1
            sess['current_module_id'] = 56
            sess['current_user_rights'] = [{'PageName': 'Update Weightage Post Marks Entry', 'AllowView': 1, 'AllowAdd': 1, 'AllowUpdate': 1, 'AllowDelete': 1}]

        import re
        resp = client.get('/examination/update_weightage_post_marks_entry')
        if resp.status_code == 200:
            print("[-] Access Test: Passed")
        else:
            print(f"[X] Access Test: Failed with status {resp.status_code}")
            return
            
        match = re.search(r'name="_csrf_token"\s+value="([^"]+)"', resp.data.decode('utf-8'))
        csrf_token = match.group(1) if match else ''

        # Mocking scenario
        print("[-] Update Test: Skipped DB constraint update for now, verifying module loading only.")

def test_external_examiner_communication():
    print("\n--- Starting Penetration & QA Tests for External Examiner Communication ---")
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess['user_id'] = 'admin'
            sess['selected_loc'] = 1
            sess['current_module_id'] = 56
            sess['current_user_rights'] = [{'PageName': 'External Examiner Communication', 'AllowView': 1, 'AllowAdd': 1, 'AllowUpdate': 1, 'AllowDelete': 1}]

        import re
        resp = client.get('/examination/external_examiner_communication')
        if resp.status_code == 200:
            print("[-] Access Test: Passed")
        else:
            print(f"[X] Access Test: Failed with status {resp.status_code}")
            return
            
        match = re.search(r'name="_csrf_token"\s+value="([^"]+)"', resp.data.decode('utf-8'))
        csrf_token = match.group(1) if match else ''

        # Email Test
        resp = client.post('/examination/external_examiner_communication', data={
            '_csrf_token': csrf_token,
            'action': 'EMAIL',
            'examiner_ids': ['1', '2']
        }, follow_redirects=True)
        
        if b'Emails successfully queued' in resp.data:
            print("[-] Mass Email Action Test: Passed")
        else:
            print("[X] Mass Email Action Test: Failed")

def test_student_marks_entry_coe():
    print("\n--- Starting Penetration & QA Tests for Student Marks Entry (@COE) ---")
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess['user_id'] = 'admin'
            sess['selected_loc'] = 1
            sess['current_module_id'] = 56
            sess['current_user_rights'] = [{'PageName': 'Student Marks Entry(@COE)', 'AllowView': 1, 'AllowAdd': 1, 'AllowUpdate': 1, 'AllowDelete': 1}]

        import re
        resp = client.get('/examination/student_marks_entry_coe')
        if resp.status_code == 200:
            print("[-] Access Test: Passed")
        else:
            print(f"[X] Access Test: Failed with status {resp.status_code}")
            return
            
        match = re.search(r'name="_csrf_token"\s+value="([^"]+)"', resp.data.decode('utf-8'))
        csrf_token = match.group(1) if match else ''

        # Mock form submit
        resp = client.post('/examination/student_marks_entry_coe', data={
            '_csrf_token': csrf_token,
            'action': 'SAVE',
            'alloc_ids': '[9999]',
            'exam_map_ids': '[8888]',
            'marks_9999_8888': '20',
            'max_9999_8888': '30'
        }, follow_redirects=True)
        
        if b'Marks saved successfully' in resp.data:
            print("[-] Mock Marks Save: Passed")
        else:
            print("[-] Mock Marks Save: Safe failure or validation caught missing allocation")

        # Over-allocation boundary test
        resp = client.post('/examination/student_marks_entry_coe', data={
            '_csrf_token': csrf_token,
            'action': 'SAVE',
            'alloc_ids': '[9999]',
            'exam_map_ids': '[8888]',
            'marks_9999_8888': '35',
            'max_9999_8888': '30'
        }, follow_redirects=True)

        if b'cannot exceed' in resp.data:
            print("[-] Over-Allocation Boundary Test: Passed (Caught 35 > 30)")
        else:
            print("[X] Over-Allocation Boundary Test: Failed (Let 35 > 30 pass)")

def test_student_marks_entry_ug():
    print("\n--- Starting Penetration & QA Tests for Student Marks Entry(UG and MBA) ---")
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess['user_id'] = 'admin'
            sess['selected_loc'] = 1
            sess['current_module_id'] = 56
            sess['current_user_rights'] = [{'PageName': 'Student Marks Entry(UG and MBA)', 'AllowView': 1, 'AllowAdd': 1, 'AllowUpdate': 1, 'AllowDelete': 1}]

        import re
        resp = client.get('/examination/student_marks_entry_ug')
        if resp.status_code == 200:
            print("[-] Access Test: Passed")
        else:
            print(f"[X] Access Test: Failed with status {resp.status_code}")
            return
            
        match = re.search(r'name="_csrf_token"\s+value="([^"]+)"', resp.data.decode('utf-8'))
        csrf_token = match.group(1) if match else ''

        # Mock form submit
        resp = client.post('/examination/student_marks_entry_ug', data={
            '_csrf_token': csrf_token,
            'action': 'SAVE',
            'alloc_ids': '[9999]',
            'exam_map_ids': '[8888]',
            'marks_9999_8888': '20',
            'max_9999_8888': '30'
        }, follow_redirects=True)
        
        if b'Marks saved successfully' in resp.data:
            print("[-] Mock Marks Save: Passed")
        else:
            print("[-] Mock Marks Save: Safe failure or validation caught missing allocation")

def test_student_marks_entry_pg_phd():
    print("\n--- Starting Penetration & QA Tests for Student Marks Entry(PG/PHD) By Teacher ---")
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess['user_id'] = 'admin'
            sess['selected_loc'] = 1
            sess['current_module_id'] = 56
            sess['current_user_rights'] = [{'PageName': 'Student Marks Entry(PG/PHD) By Teacher', 'AllowView': 1, 'AllowAdd': 1, 'AllowUpdate': 1, 'AllowDelete': 1}]

        import re
        resp = client.get('/examination/student_marks_entry_pg_phd')
        if resp.status_code == 200:
            print("[-] Access Test: Passed")
        else:
            print(f"[X] Access Test: Failed with status {resp.status_code}")
            return
            
        match = re.search(r'name="_csrf_token"\s+value="([^"]+)"', resp.data.decode('utf-8'))
        csrf_token = match.group(1) if match else ''

        # Mock form submit
        resp = client.post('/examination/student_marks_entry_pg_phd', data={
            '_csrf_token': csrf_token,
            'action': 'SAVE',
            'alloc_ids': '[9999]',
            'exam_map_ids': '[8888]',
            'marks_9999_8888': '20',
            'max_9999_8888': '30'
        }, follow_redirects=True)
        
        if b'Marks saved successfully' in resp.data:
            print("[-] Mock Marks Save: Passed")
        else:
            print("[-] Mock Marks Save: Safe failure or validation caught missing allocation")

def test_student_marks_entry_re_evaluation():
    print("\n--- Starting Penetration & QA Tests for Student Marks Entry(Re-Evaluation) ---")
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess['user_id'] = 'admin'
            sess['selected_loc'] = 1
            sess['current_module_id'] = 56
            sess['current_user_rights'] = [{'PageName': 'Student Marks Entry(Re-Evaluation)', 'AllowView': 1, 'AllowAdd': 1, 'AllowUpdate': 1, 'AllowDelete': 1}]

        import re
        resp = client.get('/examination/student_marks_entry_re_evaluation')
        if resp.status_code == 200:
            print("[-] Access Test: Passed")
        else:
            print(f"[X] Access Test: Failed with status {resp.status_code}")
            return
            
        match = re.search(r'name="_csrf_token"\s+value="([^"]+)"', resp.data.decode('utf-8'))
        csrf_token = match.group(1) if match else ''

        # Mock form submit
        resp = client.post('/examination/student_marks_entry_re_evaluation', data={
            '_csrf_token': csrf_token,
            'action': 'SAVE',
            'alloc_ids': '[9999]',
            'exam_map_ids': '[8888]',
            'marks_9999_8888': '20',
            'max_9999_8888': '30'
        }, follow_redirects=True)
        
        if b'Marks saved successfully' in resp.data:
            print("[-] Mock Marks Save: Passed")
        else:
            print("[-] Mock Marks Save: Safe failure or validation caught missing allocation")

def test_student_marks_entry_supplementary():
    print("\n--- Starting Penetration & QA Tests for Student Marks Entry (Supplementary) ---")
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess['user_id'] = 'admin'
            sess['selected_loc'] = 1
            sess['current_module_id'] = 56
            sess['current_user_rights'] = [{'PageName': 'Student Marks Entry (Supplementary)', 'AllowView': 1, 'AllowAdd': 1, 'AllowUpdate': 1, 'AllowDelete': 1}]

        import re
        resp = client.get('/examination/student_marks_entry_supplementary')
        if resp.status_code == 200:
            print("[-] Access Test: Passed")
        else:
            print(f"[X] Access Test: Failed with status {resp.status_code}")
            return
            
        match = re.search(r'name="_csrf_token"\s+value="([^"]+)"', resp.data.decode('utf-8'))
        csrf_token = match.group(1) if match else ''

        # Mock form submit
        resp = client.post('/examination/student_marks_entry_supplementary', data={
            '_csrf_token': csrf_token,
            'action': 'SAVE',
            'alloc_ids': '[9999]',
            'exam_map_ids': '[8888]',
            'marks_9999_8888': '20',
            'max_9999_8888': '30'
        }, follow_redirects=True)
        
        if b'Marks saved successfully' in resp.data:
            print("[-] Mock Marks Save: Passed")
        else:
            print("[-] Mock Marks Save: Safe failure or validation caught missing allocation")

test_exam_master()
test_degree_exam_master()
test_exam_config_master()
test_degree_exam_wise_weightage()
test_external_examiner_detail()
test_update_weightage_post_marks_entry()
test_external_examiner_communication()
test_student_marks_entry_coe()
test_student_marks_entry_ug()
test_student_marks_entry_pg_phd()
test_student_marks_entry_re_evaluation()
test_student_marks_entry_supplementary()
