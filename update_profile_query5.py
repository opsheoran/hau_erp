import os
import re

with open('app/blueprints/student_portal/profile.py', 'r', encoding='utf-8') as f:
    code = f.read()

new_query = """
    query = '''
        SELECT S.*, 
               C.collegename, 
               D.degreename,
               B.branchname,
               SM.semester_roman as current_semester,
               ADMSESS.sessionname as admitted_session,
               DY.degreeyear_char as current_year,
               SEAT.seatype as seat_type,
               CAT.category as category_name,
               NAT.nationality as nationality_name,
               REL.religiontype as religion_name,
               ST.Description as state_name,
               THB.name_of_batch as theory_batch_name,
               PRB.name_of_batch as practical_batch_name,
               EMP.EmpName as advisor_name,
               RANKMST.Rankname as quota_name,
               ADMCAT.category as adm_category_name
        FROM SMS_Student_Mst S
        LEFT JOIN SMS_College_Mst C ON S.fk_collegeid = C.pk_collegeid
        LEFT JOIN SMS_Degree_Mst D ON S.fk_degreeid = D.pk_degreeid
        LEFT JOIN SMS_BranchMst B ON S.fk_branchid = B.pk_branchid
        LEFT JOIN SMS_DegreeCycle_Mst DC ON S.fk_degreecycleidcurrent = DC.pk_degreecycleid
        LEFT JOIN SMS_Semester_Mst SM ON DC.fk_semesterid = SM.pk_semesterid
        LEFT JOIN SMS_DegreeYear_Mst DY ON DC.fk_degreeyearid = DY.pk_degreeyearid
        LEFT JOIN SMS_AcademicSession_Mst ADMSESS ON S.fk_adm_session = ADMSESS.pk_sessionid
        LEFT JOIN SMS_SeatType_Mst SEAT ON S.fk_seattypeid = SEAT.pk_seatypeid
        LEFT JOIN SMS_Category_Mst CAT ON S.fk_catid = CAT.pk_catid
        LEFT JOIN SMS_Category_Mst ADMCAT ON S.fk_admcategory = ADMCAT.pk_catid
        LEFT JOIN SMS_RankMst RANKMST ON S.fk_rankid = RANKMST.pk_rankid
        LEFT JOIN SMS_Nationality_Mst NAT ON S.fk_nid = NAT.pk_nid
        LEFT JOIN Religion_Mst REL ON S.fk_religionid = REL.pk_religionid
        LEFT JOIN Common_State_mst ST ON S.fk_stateid = ST.pk_StateID
        LEFT JOIN SMS_Batch_Dtl THB ON S.fk_batchid_Th = THB.pk_batchdtl
        LEFT JOIN SMS_Batch_Dtl PRB ON S.fk_batchid_Pr = PRB.pk_batchdtl
        LEFT JOIN SMS_AdvisoryStudentApproval ADV ON S.pk_sid = ADV.fk_sturegid AND ADV.ApprovalStatus=1
        LEFT JOIN SAL_Employee_Mst EMP ON ADV.fk_empid = EMP.pk_EmpId
        WHERE S.pk_sid = ?
    '''
"""

pattern = re.compile(r"    query = '''\n        SELECT S\.\*.*?WHERE S\.pk_sid = \?\n    '''", re.DOTALL)
if pattern.search(code):
    code = pattern.sub(new_query.strip(), code)
    with open('app/blueprints/student_portal/profile.py', 'w', encoding='utf-8') as f:
        f.write(code)
    print('Updated base profile query to pull admcategory as Qualifying/Institution Quota')
else:
    print('Failed to find query')