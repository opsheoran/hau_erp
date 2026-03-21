import os

with open('app/templates/student_portal/profile.html', 'r', encoding='utf-8') as f:
    code = f.read()

# I will replace the entire <div class="info-grid"> inside the Basic Details tab with an HTML table.
start_marker = '<!-- Basic Details Tab -->'
end_marker = '<!-- Personal Details Tab -->'

start_idx = code.find(start_marker)
end_idx = code.find(end_marker)

if start_idx != -1 and end_idx != -1:
    new_html = '''<!-- Basic Details Tab -->
    <div id="tab-basic" class="tab-content active">
        <table width="100%" border="0" cellpadding="8" cellspacing="0" style="font-size: 14px; color: #333;">
            <tr>
                <td align="right" width="20%">Student Name</td>
                <td width="2%"><b>:</b></td>
                <td align="left" width="28%"><b>{{ student.fullname or '' }}</b></td>
                <td align="right" width="20%">Mother's Name</td>
                <td width="2%"><b>:</b></td>
                <td align="left" width="28%"><b>{{ student.mname or '' }}</b></td>
            </tr>
            <tr>
                <td align="right">Father's Name</td>
                <td><b>:</b></td>
                <td align="left"><b>{{ student.fname or '' }}</b></td>
                <td align="right">Date of Birth</td>
                <td><b>:</b></td>
                <td align="left"><b>{{ student.dob.strftime('%d/%m/%Y') if student.dob else '' }}</b></td>
            </tr>
            <tr>
                <td align="right">College</td>
                <td><b>:</b></td>
                <td align="left" colspan="4"><b>{{ student.collegename or '' }}</b></td>
            </tr>
            <tr>
                <td align="right">Admitted Session</td>
                <td><b>:</b></td>
                <td align="left"><b>{{ student.admitted_session or '' }}</b></td>
                <td align="right">Degree</td>
                <td><b>:</b></td>
                <td align="left"><b>{{ student.degreename or '' }}</b></td>
            </tr>
            <tr>
                <td align="right">Department</td>
                <td><b>:</b></td>
                <td align="left"><b>{{ student.branchname or '' }}</b></td>
                <td align="right">Class</td>
                <td><b>:</b></td>
                <td align="left"><b>{{ student.current_semester or '' }}</b></td>
            </tr>
            <tr>
                <td align="right">Theory Batch</td>
                <td><b>:</b></td>
                <td align="left"><b>{{ student.theory_batch_name or 'ALL' }}</b></td>
                <td align="right">Practical Batch</td>
                <td><b>:</b></td>
                <td align="left"><b>{{ student.practical_batch_name or 'ALL' }}</b></td>
            </tr>
            <tr>
                <td align="right">Year</td>
                <td><b>:</b></td>
                <td align="left"><b>{{ student.current_year or '' }}</b></td>
                <td align="right">Seat Type</td>
                <td><b>:</b></td>
                <td align="left"><b>{{ student.seat_type or '' }}</b></td>
            </tr>
            <tr>
                <td align="right">Gender</td>
                <td><b>:</b></td>
                <td align="left"><b>{{ 'Male' if student.gender == 'M' else 'Female' if student.gender == 'F' else student.gender or '' }}</b></td>
                <td align="right">Qualifying/Institution Quota</td>
                <td><b>:</b></td>
                <td align="left"><b>{{ student.quota_name or '' }}</b></td>
            </tr>
            <tr>
                <td align="right">Category</td>
                <td><b>:</b></td>
                <td align="left"><b>{{ student.category_name or '' }}</b></td>
                <td align="right">Manual Registration No.</td>
                <td><b>:</b></td>
                <td align="left"><b>{{ student.manualRegno or '' }}</b></td>
            </tr>
            <tr>
                <td align="right">Nationality</td>
                <td><b>:</b></td>
                <td align="left"><b>{{ student.nationality_name or '' }}</b></td>
                <td align="right">Advisor Name</td>
                <td><b>:</b></td>
                <td align="left"><b>{{ student.advisor_name or '' }}</b></td>
            </tr>
            <tr>
                <td align="right">Parent's Email Id</td>
                <td><b>:</b></td>
                <td align="left"><b>{{ student.p_emailid or '' }}</b></td>
                <td align="right">Student's Email Id</td>
                <td><b>:</b></td>
                <td align="left"><b>{{ student.s_emailid or '' }}</b></td>
            </tr>
            <tr>
                <td align="right">Religion</td>
                <td><b>:</b></td>
                <td align="left"><b>{{ student.religion_name or '' }}</b></td>
                <td align="right">State</td>
                <td><b>:</b></td>
                <td align="left"><b>{{ student.state_name or '' }}</b></td>
            </tr>
            <tr>
                <td align="right">Parent's Contact No.</td>
                <td><b>:</b></td>
                <td align="left"><b>{{ student.p_phoneno or '' }}</b></td>
                <td align="right">Student's Contact No.</td>
                <td><b>:</b></td>
                <td align="left"><b>{{ student.phoneno or '' }}</b></td>
            </tr>
            <tr>
                <td align="right">Passport No.</td>
                <td><b>:</b></td>
                <td align="left"><b>{{ student.passportno or '' }}</b></td>
                <td align="right">Place of Passport Issue</td>
                <td><b>:</b></td>
                <td align="left"><b>{{ student.PassportIssuePlace or '' }}</b></td>
            </tr>
            <tr>
                <td align="right">Passport Expiry Date</td>
                <td><b>:</b></td>
                <td align="left"><b>{{ student.PassportExpirydate.strftime('%d/%m/%Y') if student.PassportExpirydate else '' }}</b></td>
                <td align="right">Remarks</td>
                <td><b>:</b></td>
                <td align="left"><b>{{ student.Remarks or '' }}</b></td>
            </tr>
            <tr>
                <td align="right">Is Physically Handicap?</td>
                <td><b>:</b></td>
                <td align="left"><b>{{ 'Yes' if student.isPhysicalHandicapped else 'No' }}</b></td>
                <td align="right">Admission Date</td>
                <td><b>:</b></td>
                <td align="left"><b>{{ student.date_of_adm.strftime('%d/%m/%Y') if student.date_of_adm else '' }}</b></td>
            </tr>
            <tr>
                <td align="right">Spot Admission?</td>
                <td><b>:</b></td>
                <td align="left"><b>{{ 'Yes' if student.SpotAddmission else 'No' }}</b></td>
                <td align="right">Rank</td>
                <td><b>:</b></td>
                <td align="left"><b>{{ student.ranknumber or '' }}</b></td>
            </tr>
            <tr>
                <td align="right">Fee Exempted?</td>
                <td><b>:</b></td>
                <td align="left"><b>{{ 'Yes' if student.isFeeNotExempt == False or student.isFeeNotExempt == 0 else 'No' }}</b></td>
                <td align="right">Aadhar Number</td>
                <td><b>:</b></td>
                <td align="left"><b>{{ student.AdharNo or '' }}</b></td>
            </tr>
            <tr>
                <td align="right">Student USID</td>
                <td><b>:</b></td>
                <td align="left"><b>{{ student.USID or '' }}</b></td>
                <td align="right">Lateral Entry</td>
                <td><b>:</b></td>
                <td align="left"><b>{{ student.Lateral_Entry or '' }}</b></td>
            </tr>
            <tr>
                <td align="right">Blood Group</td>
                <td><b>:</b></td>
                <td align="left"><b>{{ student.blood_group_name or '' }}</b></td>
                <td align="right">Bank Name</td>
                <td><b>:</b></td>
                <td align="left"><b>{{ student.bankname or '' }}</b></td>
            </tr>
            <tr>
                <td align="right">Bank A/C Number</td>
                <td><b>:</b></td>
                <td align="left"><b>{{ student.bankaccountnumber or '' }}</b></td>
                <td align="right">IFSC</td>
                <td><b>:</b></td>
                <td align="left"><b>{{ student.IFSCcode or '' }}</b></td>
            </tr>
        </table>
    </div>

    '''
    
    code = code[:start_idx] + new_html + code[end_idx:]
    with open('app/templates/student_portal/profile.html', 'w', encoding='utf-8') as f:
        f.write(code)
    print('Updated to HTML table layout successfully')
else:
    print('Failed to find replace markers')