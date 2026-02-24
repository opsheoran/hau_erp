import io
import os
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT

def generate_programme_of_work_pdf(students_data):
    import os
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=1.2*cm, leftMargin=1.2*cm, topMargin=1.2*cm, bottomMargin=1.2*cm)
    styles = getSampleStyleSheet()
    
    # Custom Styles matching legacy Verdana 10.5pt look
    style_centered = ParagraphStyle(name='Centered', parent=styles['Normal'], alignment=TA_CENTER, fontName='Helvetica-Bold', fontSize=12, leading=14)
    style_title = ParagraphStyle(name='Title', parent=styles['Normal'], alignment=TA_CENTER, fontName='Helvetica-Bold', fontSize=11, spaceAfter=8, textTransform='uppercase')
    style_normal = ParagraphStyle(name='NormalSmall', parent=styles['Normal'], fontSize=10, leading=13)
    style_justify = ParagraphStyle(name='Justify', parent=styles['Normal'], fontSize=10, leading=13, alignment=TA_JUSTIFY)
    style_table_header = ParagraphStyle(name='THeader', parent=styles['Normal'], fontSize=9, fontName='Helvetica-Bold', alignment=TA_CENTER)
    style_table_cell = ParagraphStyle(name='TCell', parent=styles['Normal'], fontSize=9, leading=11)
    style_table_cell_center = ParagraphStyle(name='TCellCenter', parent=styles['Normal'], fontSize=9, leading=11, alignment=TA_CENTER)
    
    elements = []
    logo_path = os.path.join(os.getcwd(), "app", "static", "images", "logo.png")

    for s_data in students_data:
        info = s_data['info']
        
        # Header with Logo
        logo = Image(logo_path, width=1.6*cm, height=1.6*cm) if os.path.exists(logo_path) else ""
        header_table = Table([
            [logo, Paragraph("CHAUDHARY CHARAN SINGH HARYANA AGRICULTURAL UNIVERSITY<br/><br/>PROGRAMME OF WORK FOR POSTGRADUATE STUDIES", style_centered)]
        ], colWidths=[2*cm, 16*cm])
        header_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
        elements.append(header_table)
        elements.append(Spacer(1, 0.4*cm))

        # To Section
        elements.append(Paragraph("To", style_normal))
        elements.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;The Dean, Postgraduate Studies", style_normal))
        elements.append(Spacer(1, 0.3*cm))

        # Main Narrative Paragraph - Exact wording
        para_text = f"The Advisory Committee of <b>{info['fullname']}</b> Admission No <b>{info['AdmissionNo']}</b> admitted to {info['degreename']} programme in the college of <b>{info['collegename']}</b> in <b>II</b> semester <b>{info['sessionname']}</b>, majoring in <b>{info['Branchname']}</b> after a conference with his/her submit the following statement and recommendations:"
        elements.append(Paragraph(para_text, style_justify))
        elements.append(Spacer(1, 0.4*cm))

        # Major/Minor Fields - Using &nbsp; to prevent collapse
        box_data = [
            [Paragraph("<b>His/Her Major Field</b>", style_table_cell), Paragraph(info['Branchname'] or "&nbsp;", style_table_cell)],
            [Paragraph("<b>His/Her Minor field</b>", style_table_cell), Paragraph(s_data.get('minor_field', '') or "&nbsp;", style_table_cell)]
        ]
        box_table = Table(box_data, colWidths=[5.5*cm, 13.1*cm])
        box_table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('LEFTPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('TOPPADDING', (0,0), (-1,-1), 5),
        ]))
        elements.append(box_table)

        # 1. ACADEMIC QUALIFICATION
        elements.append(Spacer(1, 0.2*cm))
        elements.append(Paragraph("ACADEMIC QUALIFICATION PRIOR TO JOINING THE UNIVERSITY", style_title))
        qual_data = [[Paragraph(h, style_table_header) for h in ["Degree or Diploma", "Year of Passing", "Division", "Aggregate % / GPA", "Institution", "Major Subject"]]]
        for q in s_data['qualifications']:
            qual_data.append([
                Paragraph(q['examname'] or "&nbsp;", style_table_cell),
                Paragraph(str(q['yearofpassing']) or "&nbsp;", style_table_cell_center),
                Paragraph(q['division'] or "&nbsp;", style_table_cell_center),
                Paragraph(str(q['percentage']) or "&nbsp;", style_table_cell_center),
                Paragraph(q['Bord_Univ'] or "&nbsp;", style_table_cell),
                Paragraph(q['Specialization'] or "&nbsp;", style_table_cell)
            ])
        while len(qual_data) < 3: qual_data.append([Paragraph("&nbsp;", style_table_cell)]*6)

        qual_table = Table(qual_data, colWidths=[3.1*cm, 2.5*cm, 2*cm, 3.5*cm, 3.7*cm, 3.8*cm], rowHeights=None)
        qual_table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('TOPPADDING', (0,0), (-1,-1), 5),
        ]))
        elements.append(qual_table)

        # 2. Undergraduate Preparation
        elements.append(Spacer(1, 0.2*cm))
        elements.append(Paragraph("Undergraduate Prepration Of Major Field", style_title))
        ug_data = [[Paragraph(h, style_table_header) for h in ["S.No.", "Courses or Subjects Take", "Course Code", "Credit Hours", "Grade"]]]
        for idx, c in enumerate(s_data['ug_prep'], 1):
            ug_data.append([
                Paragraph(str(idx), style_table_cell_center),
                Paragraph(c['coursename'] or "&nbsp;", style_table_cell),
                Paragraph(c['coursecode'] or "&nbsp;", style_table_cell_center),
                Paragraph(f"{c['crtheory']}+{c['crpractical']}", style_table_cell_center),
                Paragraph(str(c['grade']) or "&nbsp;", style_table_cell_center)
            ])
        while len(ug_data) < 5: ug_data.append([Paragraph(str(len(ug_data)), style_table_cell_center), Paragraph("&nbsp;", style_table_cell), Paragraph("&nbsp;", style_table_cell), Paragraph("&nbsp;", style_table_cell), Paragraph("&nbsp;", style_table_cell)])

        ug_table = Table(ug_data, colWidths=[1.2*cm, 8.8*cm, 3.5*cm, 2.8*cm, 2.3*cm], rowHeights=None)
        ug_table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('TOPPADDING', (0,0), (-1,-1), 5),
        ]))
        elements.append(ug_table)

        # 3. Previous PG Training
        elements.append(Spacer(1, 0.2*cm))
        elements.append(Paragraph("Previous postgraduate training, if any, for the major and minor fields", style_title))
        prev_pg_data = [[Paragraph(h, style_table_header) for h in ["Classification of Courses", "Course No.", "Title of the Course", "Credit Hours", "Grade"]]]
        pg_cats = [('DE', 'i) Deficienicies to be completed'), ('MA', 'ii) Major Subject'), ('MI', 'iii) Minor Subject'), ('SU', 'iv) Supporting Subject'), ('CP', 'v) Non Credit Compulsory Courses')]
        for code, label in pg_cats:
            prev_pg_data.append([Paragraph(f"<b>{label}</b>", style_table_cell), Paragraph("&nbsp;", style_table_cell), Paragraph("&nbsp;", style_table_cell), Paragraph("&nbsp;", style_table_cell), Paragraph("&nbsp;", style_table_cell)])
            cat_courses = [c for c in s_data['pg_training'] if c['classification'] == code]
            if cat_courses:
                for c in cat_courses:
                    prev_pg_data.append([
                        Paragraph("&nbsp;", style_table_cell), 
                        Paragraph(c['coursecode'] or "&nbsp;", style_table_cell_center), 
                        Paragraph(c['coursename'] or "&nbsp;", style_table_cell), 
                        Paragraph(f"{c['crtheory']}+{c['crpractical']}", style_table_cell_center), 
                        Paragraph(str(c['grade']) or "&nbsp;", style_table_cell_center)
                    ])
            else:
                prev_pg_data.append([Paragraph("1", style_table_cell_center), Paragraph("&nbsp;", style_table_cell), Paragraph("&nbsp;", style_table_cell), Paragraph("&nbsp;", style_table_cell), Paragraph("&nbsp;", style_table_cell)])

        prev_pg_table = Table(prev_pg_data, colWidths=[5.5*cm, 3*cm, 6.5*cm, 2.3*cm, 1.3*cm], rowHeights=None)
        prev_pg_table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('TOPPADDING', (0,0), (-1,-1), 5),
        ]))
        elements.append(prev_pg_table)
        
        # New Page for requirements
        elements.append(PageBreak())

        # 4. Courses to be completed
        type_label = "Ph.D." if "Ph.D" in info['degreename'] else "M.Sc."
        elements.append(Paragraph(f"Course to be completed by the student to meet post-graduate ({type_label}) requirment:", style_title))
        curr_pg_data = [[Paragraph(h, style_table_header) for h in ["Classification of course", "Course No.", "Title Of Course", "Credit Hour"]]]
        pg_sections = [('DE', 'i) Deficiencies to be completed'), ('MA', 'ii) Major Subject'), ('MI', 'iii) Minor Subject'), ('RE', 'iv) Research Subject'), ('SE', 'v) Seminar Subject'), ('CP', 'vi) Non Credit Compulsory Courses')]
        
        for code, label in pg_sections:
            curr_pg_data.append([Paragraph(f"<b>{label}</b>", style_table_cell), Paragraph("&nbsp;", style_table_cell), Paragraph("&nbsp;", style_table_cell), Paragraph("&nbsp;", style_table_cell)])
            sect_courses = s_data['grouped_courses'].get(code, [])
            if sect_courses:
                for idx, c in enumerate(sect_courses, 1):
                    curr_pg_data.append([
                        Paragraph(str(idx), style_table_cell_center), 
                        Paragraph(c['coursecode'] or "&nbsp;", style_table_cell_center), 
                        Paragraph(c['coursename'] or "&nbsp;", style_table_cell), 
                        Paragraph(f"{c['crhrth']}+{c['crhrpr']}", style_table_cell_center)
                    ])
                total_cr = sum(c['crhrth'] + c['crhrpr'] for c in sect_courses)
                curr_pg_data.append(["", "", Paragraph("<b>Total Credit Hours</b>", style_table_cell), Paragraph(f"<b>{total_cr}</b>", style_table_header)])
            else:
                curr_pg_data.append([Paragraph("1", style_table_cell_center), Paragraph("&nbsp;", style_table_cell), Paragraph("&nbsp;", style_table_cell), Paragraph("0", style_table_cell_center)])

        curr_pg_table = Table(curr_pg_data, colWidths=[5.5*cm, 3.2*cm, 7.4*cm, 2.5*cm], rowHeights=None)
        curr_pg_table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('TOPPADDING', (0,0), (-1,-1), 5),
        ]))
        elements.append(curr_pg_table)
        elements.append(Spacer(1, 0.5*cm))

        # 5. Advisory Committee
        elements.append(Paragraph("ADVISORY COMMITTEE", style_title))
        adv_data = [["", Paragraph("Status", style_table_header), Paragraph("Name", style_table_header), Paragraph("Designation", style_table_header), Paragraph("Department", style_table_header), Paragraph("Sign", style_table_header)]]
        for idx, m in enumerate(s_data['committee']['all'], 1):
            adv_data.append([
                Paragraph(str(idx), style_table_cell_center), 
                Paragraph(m['role_name'] or "&nbsp;", style_table_cell), 
                Paragraph(m['empname'] or "&nbsp;", style_table_cell), 
                Paragraph(m['designation'] or "&nbsp;", style_table_cell), 
                Paragraph(m['department'] or "&nbsp;", style_table_cell), 
                Paragraph("&nbsp;", style_table_cell)
            ])
        while len(adv_data) < 6: adv_data.append([Paragraph(str(len(adv_data)), style_table_cell_center), Paragraph("&nbsp;", style_table_cell), Paragraph("&nbsp;", style_table_cell), Paragraph("&nbsp;", style_table_cell), Paragraph("&nbsp;", style_table_cell), Paragraph("&nbsp;", style_table_cell)])

        adv_table = Table(adv_data, colWidths=[1*cm, 3.5*cm, 4.2*cm, 3.5*cm, 4.4*cm, 2*cm], rowHeights=None)
        adv_table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('TOPPADDING', (0,0), (-1,-1), 5),
        ]))
        elements.append(adv_table)
        elements.append(Spacer(1, 0.4*cm))

        # Signatures
        elements.append(Paragraph("Forwarded (6copies) to the Dean,Postgraduate studies for approval", style_normal))
        elements.append(Spacer(1, 1.2*cm))
        sig_data = [
            ["", "", Paragraph("<b>Head Of Department</b>", style_centered)],
            [Paragraph("&nbsp;", style_normal), "", ""],
            [Paragraph("<b>Approved</b>", style_normal), "", ""],
            [Paragraph("&nbsp;", style_normal), "", ""],
            [Paragraph("<b>Dean,Postgraduate studies</b>", style_normal), "", ""]
        ]
        sig_table = Table(sig_data, colWidths=[7.5*cm, 4.5*cm, 6.6*cm])
        sig_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
        elements.append(sig_table)

        if not s_data == students_data[-1]: elements.append(PageBreak())

    doc.build(elements)
    buffer.seek(0)
    return buffer

def clean_json_data(data):
    if isinstance(data, dict):
        return {k: clean_json_data(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [clean_json_data(i) for i in data]
    elif isinstance(data, bytes):
        return None 
    elif hasattr(data, 'strftime'):
        return data.strftime('%d/%m/%Y')
    return data

def to_int(val):
    if val is None: return None
    if isinstance(val, (int, float)): return int(val)
    if isinstance(val, str) and val.strip():
        try:
            return int(val)
        except ValueError:
            return None

def number_to_words(n):
    if n == 0: return "ZERO"
    units = ["", "ONE", "TWO", "THREE", "FOUR", "FIVE", "SIX", "SEVEN", "EIGHT", "NINE"]
    teens = ["TEN", "ELEVEN", "TWELVE", "THIRTEEN", "FOURTEEN", "FIFTEEN", "SIXTEEN", "SEVENTEEN", "EIGHTEEN", "NINETEEN"]
    tens = ["", "", "TWENTY", "THIRTY", "FORTY", "FIFTY", "SIXTY", "SEVENTY", "EIGHTY", "NINETY"]
    def convert_below_1000(num):
        res = ""
        if num >= 100:
            res += units[num // 100] + " HUNDRED "
            num %= 100
        if num >= 20:
            res += tens[num // 10] + " "
            num %= 10
        elif num >= 10:
            res += teens[num - 10] + " "
            return res
        if num > 0:
            res += units[num] + " "
        return res
    result = ""
    if n >= 10000000:
        result += convert_below_1000(n // 10000000) + "CRORE "
        n %= 10000000
    if n >= 100000:
        result += convert_below_1000(n // 100000) + "LAKH "
        n %= 100000
    if n >= 1000:
        result += convert_below_1000(n // 1000) + "THOUSAND "
        n %= 1000
    result += convert_below_1000(n)
    return result.strip() + " ONLY"

def get_pagination_range(current_page, total_pages):
    if total_pages <= 15: return range(1, total_pages + 1)
    res = []
    if current_page <= 10:
        for i in range(1, 11): res.append(i)
        res.extend(['...', total_pages - 1, total_pages])
    elif current_page >= total_pages - 9:
        res.extend([1, 2, '...'])
        for i in range(total_pages - 10, total_pages + 1): res.append(i)
    else:
        res.extend([1, 2, '...'])
        for i in range(current_page - 3, current_page + 4): res.append(i)
        res.extend(['...', total_pages - 1, total_pages])
    return res

def get_pagination(table, page, per_page=10, where="", params=None, order_by=""):
    from app.db import DB
    if params is None:
        params = []
    
    # Remove ORDER BY from the count query
    count_query = f"SELECT COUNT(*) FROM {table} {where}"
    total = DB.fetch_scalar(count_query, params)
    
    total_pages = (total + per_page - 1) // per_page if total > 0 else 1
    offset = (page - 1) * per_page
    pagination = {'page': page, 'per_page': per_page, 'total': total, 'total_pages': total_pages, 'has_prev': page > 1, 'has_next': page < total_pages}
    
    sql_limit = ""
    if order_by:
        sql_limit = f"{order_by} OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY"
    else:
        # SQL Server requires ORDER BY for OFFSET/FETCH
        sql_limit = f"ORDER BY (SELECT NULL) OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY"
        
    return pagination, sql_limit

def get_page_url(page_name):
    from flask import url_for
    # Disambiguate duplicate captions across modules
    try:
        from flask import session
        curr_mod = str(session.get('current_module_id') or '')
        norm_page = ' '.join(str(page_name).strip().split())
        
        if curr_mod == '30': # UMM
            mapping = {
                'Department Master': 'umm.department_master',
                'Designation Master': 'umm.designation_master',
                'Class Master': 'umm.class_master',
                'Section Master': 'umm.section_master',
                'Religion Master': 'umm.religion_master',
                'Category Master': 'establishment.category_master' # UMM might use Establishment's or its own, usually Establishment
            }
            if norm_page in mapping: return url_for(mapping[norm_page])
            
        elif curr_mod == '72': # Establishment
            mapping = {
                'Department Master': 'establishment.department_master',
                'Designation Master': 'establishment.designation_master',
                'Class Master': 'establishment.class_master',
                'Section Master': 'establishment.section_master',
                'Religion Master': 'establishment.religion_master',
                'Category Master': 'establishment.category_master',
                'Designation Category': 'establishment.designation_category_master',
                'Designation Category Master': 'establishment.designation_category_master'
            }
            if norm_page in mapping: return url_for(mapping[norm_page])
            
        elif curr_mod == '55': # Academics
            mapping = {
                'Category Master': 'academics.category_master'
            }
            if norm_page in mapping: return url_for(mapping[norm_page])
    except Exception:
        pass
    endpoint = PAGE_URL_MAPPING.get(page_name)
    if not endpoint and page_name:
        norm = " ".join(str(page_name).strip().split())
        # Try normalized match (handles minor spacing differences between DB captions and config captions)
        for k, v in PAGE_URL_MAPPING.items():
            if " ".join(str(k).strip().split()) == norm:
                endpoint = v
                break
    if not endpoint or endpoint == '#':
        from app.blueprints.academics import ACADEMIC_MENU_CONFIG
        from app.blueprints.examination import EXAMINATION_MENU_CONFIG
        found = False
        for main in ACADEMIC_MENU_CONFIG.values():
            for sub in main.values():
                for ss, tabs in sub.items():
                    if page_name in tabs or page_name == ss: found = True; break
        if found: return url_for('academics.generic_page_handler', page_name=page_name)
        # fallback to DB pagepath when mapping missing (helps when DB stores non-mapped pages)
        try:
            from app.db import DB
            row = DB.fetch_one(
                'SELECT TOP 1 pagepath FROM UM_WebPage_Mst WHERE REPLACE(LTRIM(RTRIM(menucaption)), '  ' , ' ' ) = ?',
                [norm]
            )
            if row:
                pp = (row.get('pagepath') or '').strip()
                if pp.startswith('/'):
                    return pp
        except Exception:
            pass

        for main in EXAMINATION_MENU_CONFIG.values():
            for sub in main.values():
                for folder, pages in sub.items():
                    if page_name in pages or page_name == folder: found = True; break
        if found: return url_for('examination.generic_page_handler', page_name=page_name)
        return '#'
    try: return url_for(endpoint)
    except: return '#'

PAGE_URL_MAPPING = {
    'District Master': 'umm.district_master',
    'Location Master': 'umm.location_master',
    'Class Master': 'umm.class_master',
    'Religion Master': 'umm.religion_master',
    'Designation Specialization Master': 'umm.designation_specialization_master',
    'DDO Master': 'umm.ddo_master',
    'Section Master': 'umm.section_master',
    'Department Master': 'umm.department_master',
    'Grade Master': 'umm.grade_master',
    'Designation Master': 'umm.designation_master',
    'DDO Location Mapping': 'umm.ddo_location_mapping',
    'Controlling Office Master': 'umm.controlling_office_master',
    'Office Type Master': 'umm.office_type_master',
    'Country State District City Master': 'umm.country_state_dist_city_master',
    'User Master': 'umm.user_master',
    'Page Type Master': 'umm.page_type_master',
    'Role Master': 'umm.role_master',
    'Role Level Master': 'umm.role_level_master',
    'Module Master': 'umm.module_master',
    'Reset Password': 'umm.reset_password',
    'Manage Page Rights': 'umm.manage_page_rights',
    'Web Page Master': 'umm.web_page_master',
    # Establishment - Personal Details
    'Employee Demographic Details': 'establishment.employee_demographic_details',
    'Employee Document Details': 'establishment.employee_document_details',
    'Education Qualification Details': 'establishment.employee_qualification_details',
    'Employee Permission of Qualification Details': 'establishment.employee_permission_details',
    'Employee Family Details': 'establishment.employee_family_details',
    'Employee Nominee Details': 'establishment.employee_nominee_details',
    'Employee Books Details': 'establishment.employee_book_details',
    'LTC Detail': 'establishment.employee_ltc_details',
    'Earned Leave Details': 'establishment.employee_earned_leave_details',
    # Establishment - Job Details
    'Employee Previous Job Details': 'establishment.employee_previous_job_details',
    'Employee Foreign Visit Details': 'establishment.employee_foreign_visit_details',
    'Employee Training Details': 'establishment.employee_training_details',
    'Employee Departmental Exam Details': 'establishment.employee_departmental_exam_details',
    'Employee Service Verification Details': 'establishment.employee_service_verification_details',
    'Disciplinary Action/Reward Details': 'establishment.employee_disciplinary_details',
    'Employee Loan Details': 'establishment.employee_loan_details',
    'Employee Book Grant Amount Details': 'establishment.employee_book_grant_details',
    'Employee Bonus Amount Details': 'establishment.employee_bonus_details',
    # Establishment - Increment/Promotion
    'SAR/ACR Admin Transaction': 'establishment.sar_admin_transaction',
    'Employee First Appointment Details': 'establishment.employee_first_appointment_details',
    'Emp Increment Payrevision': 'establishment.employee_increment_payrevision',
    'Employee Promotion/Financial Up-gradation': 'establishment.employee_promotion_details',
    'Employee No-Dues Detail': 'establishment.employee_no_dues_details',
    'Appointing Authority': 'establishment.appointing_authority',
    'Controlling DDO Department Reliving': 'establishment.controlling_ddo_department_reliving',
    'Controlling DDO Department Joining': 'establishment.controlling_ddo_department_joining',
    'Non Teaching Employee Promotion Verification': 'establishment.non_teaching_promotion_verification',
    'Non Teaching Employee Promotion Approval': 'establishment.non_teaching_promotion_approval',
    'Non Teaching VC Promotion Approval': 'establishment.non_teaching_vc_promotion_approval',
    'User Login Management': 'umm.login_image_management',
    'Module Rights Detail': 'umm.module_rights',
    'Fetch Password': 'umm.fetch_password',
    'Multiple Users Page Rights': 'umm.multiple_user_page_rights',
    'PageType-Role Link': 'umm.page_type_role_link',
    'Role Page Rights': 'umm.role_page_rights',
    'User Wise Log': 'umm.user_wise_log',
    'Send Message': 'umm.send_message',
    'Department Master (UMM)': 'umm.department_master',
    'Leave Request': 'leave.leave_request',
    'Leave Approval': 'leave.approvals',
    'Leave Transaction': 'leave.leave_transaction',
    'Leave Cancel Request': 'leave.leave_cancel',
    'Leave Cancel Approval': 'leave.cancel_approvals',
    'Leave Adjustment Request': 'leave.leave_adjustment',
    'Leave Adjustment': 'leave.leave_adjustment',
    'Leave Adjustment Approval': 'leave.adj_approvals',
    'Employee Leave Assignment': 'leave.leave_assignment',
    'Leave Assignment': 'leave.leave_assignment',
    'Leave Transaction Reports': 'leave.leave_report_transactions',
    'Leave Reconcilliation Report': 'leave.leave_report_el_reconciliation',
    'Employee Leave Details': 'leave.employee_leave_details',
    'Leave Encashment': 'leave.leave_encashment',
    'Update Earned Leave Balance': 'leave.leave_update_el',
    'Leave Type Master': 'leave.leave_type_master',
    'Leave Work Flow': 'leave.leave_workflow',
    'Common Holidays Master': 'leave.common_holiday_master',
    'Holiday Location Master': 'leave.holiday_location_master',
    'Location Wise Holidays Master': 'leave.loc_wise_holiday_master',
    'Weekly Off Master': 'leave.weekly_off_master',
    'Leave Extend Request': 'leave.leave_extend_request',
    'Service Joining Date': 'leave.service_joining_date',
    'Service Joining Status': 'leave.service_joining_status',
    'Service Departure Details': 'leave.service_departure_details',
    'Service Departure Status': 'leave.service_departure_status',
    'Service Departure from Admin': 'leave.departure_admin',
    'Cancel Approved Leaves': 'leave.cancel_approved',
    'Service joining from Admin': 'leave.service_joining_status',
    'GPF/CPF/NPS Detail': 'hrms.gpf_details',
    'Loan Apply': 'hrms.loan_apply',
    'Income tax Certificate': 'hrms.income_tax_cert',
    'Income Tax Certificate': 'hrms.income_tax_cert',
    'Apply for LTC': 'hrms.ltc_apply',
    'TA Bill': 'hrms.ta_bill_view',
    'House rent Detail Submission': 'hrms.rent_submission',
    'House Rent Detail Submission': 'hrms.rent_submission',
    'Form 16': 'hrms.form16_generation',
    'Form 16 Generation': 'hrms.form16_generation',
    'Tax Declaration': 'hrms.form16',
    'Tax Declaration Form': 'hrms.form16',
    'Form 16 Process': 'hrms.form16_process',
    'Tax deduction Form': 'hrms.tax_deduction_form',
    'Annual Property Return Form': 'hrms.property_return',
    'My Profile': 'hrms.employee_portal',
    'Download Salary Slip': 'payroll.salary_slip_view',
    'Salary Slip': 'payroll.salary_slip_view',
    'Salary Slip PDF': 'payroll.salary_slip_view',
    'Exam Master': 'examination.exam_master',
    'Student Marks Entry(UG and MBA)': 'examination.marks_entry_ug',
    'Establishment Master': 'establishment.list_masters',
    'City-Category Master': 'establishment.city_category_master',
    'City Master': 'establishment.city_master',
    'Salutation Master': 'establishment.salutation_master',
    'Religion Master': 'establishment.religion_master',
    'Relation Master': 'establishment.relation_master',
    'Category Master': 'establishment.category_master',
    'Gad-Nongad Master': 'establishment.gad_nongad_master',
    'Class Master': 'establishment.class_master',
    'Discipline Master': 'establishment.discipline_master',
    'Department Master': 'establishment.department_master',
    'Section Master': 'establishment.section_master',
    'Designation Master': 'establishment.designation_master',
    'Employee Master': 'establishment.employee_master',
    'Employee Master Scheme Wise': 'establishment.employee_master_scheme_wise',
    'Employee Master Scheme Wise (Establishment)': 'establishment.employee_master_scheme_wise',
    'Employee Demographic Details': 'establishment.employee_demographic_details',
    'Marital Status Master': 'establishment.marital_status_master',
    'Funds Sponsor Master': 'establishment.fund_sponsor_master',
    'ExamType Master': 'establishment.exam_type_master',
    'Designation Category': 'establishment.designation_category_master',
    'Designation Category Master': 'establishment.designation_category_master',
    'City-Category Master': 'establishment.city_category_master',
    'City Category Master': 'establishment.city_category_master',
    'Common Masters preparation': 'academics.common_master_preparation',
    'Academic Session Master': 'academics.session_master',
    'Faculty Master': 'academics.faculty_master',
    'Degree Year Master': 'academics.degree_year_master',
    'Semester Master [Add Semester]': 'academics.semester_master',
    'Specialization Master [PG/PHD]': 'academics.branch_master',
    'Discipline Master [PG/PHD]': 'academics.branch_master',
    'College Type Master': 'academics.college_type_master',
    'Degree Type Master': 'academics.degree_type_master',
    'Qualifying/Institution Quota': 'academics.rank_master',
    'Employee- Degree Map': 'academics.employee_degree_map',
    'Academic Session Master [A]': 'academics.session_master',
    'Faculty Master [A]': 'academics.faculty_master',
    'Degree Year Master [A]': 'academics.degree_year_master',
    'Semester Master [Add Semester] [A]': 'academics.semester_master',
    'Specialization Master [PG/PHD] [A]': 'academics.branch_master',
    'College Type Master [A]': 'academics.college_type_master',
    'Degree Type Master [A]': 'academics.degree_type_master',
    'Qualifying/Institution Quota [A]': 'academics.rank_master',
    'Employee- Degree Map [A]': 'academics.employee_degree_map',
    'College Master [Create College]': 'academics.college_master',
    'Degree Master [Create Degree]': 'academics.degree_master',
    'Degree Cycle Master': 'academics.degree_cycle_master',
    'Col-Deg-Specialization Master': 'academics.col_deg_spec_master',
    'Degree wise Credit Hours': 'academics.degree_crhr',
    'Class - Batch Master': 'academics.batch_master',
    'Moderation Marks Detail': 'academics.moderation_marks',
    'Degree Wise Credit Hours(Course Plan)': 'academics.degree_crhr_courseplan',
    'Course Type Master': 'academics.course_type_master',
    'Paper/Course Title Master': 'academics.paper_title_master',
    'Course/Subject Master': 'academics.course_master',
    'Activity Master': 'academics.activity_master',
    'Activity Course Master': 'academics.activity_course_master',
    'Package Master': 'academics.package_master',
    'Course Detail Report': 'academics.course_detail_report',
    'Syllabus Creation [Master]': 'academics.syllabus_creation',
    'PGS Course Limit [Master]': 'academics.pgs_course_limit_master',
    'Nationality Master': 'academics.nationality_master',
    'Category Master': 'academics.category_master',
    'Board Master': 'academics.board_master',
    'Entitlement Master': 'academics.entitlement_master',
    'Certificates Master': 'academics.certificate_master',
    'Certificate Batch Master': 'academics.cert_batch_master',
    'Student BioData': 'academics.student_biodata',
    'Student Bio data': 'academics.student_biodata',
    'Student Biodata Updation': 'academics.student_biodata_updation',
    'Student BioData Updation': 'academics.student_biodata_updation',
    'Student Bio data Updation': 'academics.student_biodata_updation',
    'Achievement/ Disciplinary ': 'academics.achievement_disciplinary',
    'Achievement / Disciplinary Approval': 'academics.achievement_disciplinary_approval',
    'Student Activity Management': 'academics.student_activity_management',
    'Student Personal Detail Report': 'academics.student_personal_detail_report',
    'Admission No Configuration': 'academics.admission_no_configuration',
    'Admission No Generation': 'academics.admission_no_generation',
    'Batch Assignment': 'academics.batch_assignment',
    'Degree Complete Detail': 'academics.degree_complete_detail',
    'HOD Approval': 'academics.hod_approval',
    'Event Master': 'academics_mgmt.event_master',
    'Event Assignment': 'academics_mgmt.event_assignment',
    'Semester Registration': 'academics_mgmt.semester_registration',
    'Academic Counselling Meeting': 'academics_mgmt.academic_counselling_meeting',
    'Previous Question Paper Uploads': 'academics_mgmt.previous_paper_uploads',
    'SMS And Mail': 'academics_mgmt.sms_and_mail',
    'Student Extension': 'academics_mgmt.student_extension',
    'Extension Management': 'academics_mgmt.extension_management',
    'Student Transfer Details': 'academics_mgmt.student_transfer_details',
    'Registration Cancel': 'academics_mgmt.registration_cancel',
    'Student Semester Change': 'academics_mgmt.student_semester_change',
    'Course Approval Status': 'academics_mgmt.course_approval_status',
    'rechecking Approval By Hod(PG)': 'academics_mgmt.rechecking_approval_hod_pg',
    'Rechecking Approval By Advisor[UG]': 'academics_mgmt.rechecking_approval_advisor_ug',
    'Rechecking Approval By Dean[UG]': 'academics_mgmt.rechecking_approval_dean_ug',
    'Revised Result': 'academics_mgmt.revised_result',
    'Course Allocation For UG[Reguler]': 'course_allocation.course_allocation_ug_regular',
    'Advisor Allocation(For UG)': 'academics_mgmt.advisor_allocation_ug',
    'Course Allocation Approval For UG/PG[By Advisor]': 'academics.student_course_approval_advisor',
    'Course Allocation Approval For UG/PG[By Teacher]': 'academics.course_allocation_approval',
    'Course Allocation Approval For UG/PG[By DSW]': 'academics.student_course_approval_dsw',
    'Course Allocation Approval For UG/PG[By Library]': 'academics.student_course_approval_library',
    'Course Allocation Fee Approval For UG/PG': 'academics.student_course_approval_fee',
    'Course Allocation Approval For UG/PG [By Dean]': 'academics.student_course_approval_dean',
    'Course Allocation Approval For PG [By DeanPGS]': 'academics.student_course_approval_deanpgs',
    'Dean PGS approval (Course plan)': 'academics.dean_pgs_course_plan_approval',
    'Major Advisor': 'academics.major_advisor',
    'College Dean Approval': 'academics.college_dean_approval',
    'Dean PGS approval (advisory committee)': 'academics.dean_pgs_approval',
    'College Degree Wise Seat Detail': 'academics.college_degree_seat_detail',
    'Specialization Assignment': 'academics.specialization_assignment',
    'Limit Assignment': 'academics.limit_assignment',
    'Student Registration': 'academics.student_registration',
    'Student Password': 'academics.student_password',
    'View Student Password': 'academics.view_student_password',
    'Back Course Entry': 'academics.back_course_entry',
    'College Degree Seat Report': 'academics.college_degree_seat_report',
    'Prepare Course Plan': 'academics.course_plan',
    'Member of Minor and supporting': 'academics.minor_advisor',
    'Course Allocation(For PG)': 'academics.course_allocation_pg',
    'Course Offer (By HOD)': 'academics.course_offer_hod',
    'Teacher Course Assignment': 'academics.teacher_course_assignment',
    'PG Mandates Submission by HOD': 'academics.pg_mandates_submission',
    'Programme of work(PG)': 'academics.programme_of_work_pg',
    'Addition/withdrawal Approval by Teacher': 'academics.add_with_approval_teacher',
    'Addition/withdrawal Approval by Major Advisor': 'academics.add_with_approval_major_advisor',
    'Student Thesis Detail': 'academics.student_thesis_detail',
    'Addition/Withdrawal Approval Status': 'academics.addition_withdrawal_approval_status',
    'Advisory Creation And Approval Status': 'academics.advisory_creation_approval_status',
    'I-Grade Approval by Teacher': 'academics.igrade_approval_teacher',
    'I-Grade Approval By Dean Pgs': 'academics.igrade_approval_dean_pgs',
    'I Grade Approval Status': 'academics.igrade_approval_status',
}

def generate_igrade_status_pdf(status_list, filters_info=None):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=1*cm, leftMargin=1*cm, topMargin=1*cm, bottomMargin=1*cm)
    styles = getSampleStyleSheet()
    
    style_centered = ParagraphStyle(name='Centered', parent=styles['Normal'], alignment=TA_CENTER, fontName='Helvetica-Bold', fontSize=12)
    style_table_header = ParagraphStyle(name='THeader', parent=styles['Normal'], fontSize=8, fontName='Helvetica-Bold', alignment=TA_CENTER)
    style_table_cell = ParagraphStyle(name='TCell', parent=styles['Normal'], fontSize=7, leading=9)
    style_table_cell_center = ParagraphStyle(name='TCellCenter', parent=styles['Normal'], fontSize=7, leading=9, alignment=TA_CENTER)
    
    elements = []
    logo_path = os.path.join(os.getcwd(), "app", "static", "images", "logo.png")
    
    logo = Image(logo_path, width=1.6*cm, height=1.6*cm) if os.path.exists(logo_path) else ""
    header_table = Table([
        [logo, Paragraph("CHAUDHARY CHARAN SINGH HARYANA AGRICULTURAL UNIVERSITY<br/><br/>I-GRADE APPROVAL STATUS REPORT", style_centered)]
    ], colWidths=[2*cm, 24*cm])
    header_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
    elements.append(header_table)
    elements.append(Spacer(1, 0.5*cm))
    
    if filters_info:
        elements.append(Paragraph(f"Session: {filters_info.get('session', 'N/A')} | Degree: {filters_info.get('degree', 'N/A')}", styles['Normal']))
        elements.append(Spacer(1, 0.3*cm))

    headers = ["S.No", "Adm. No", "Name", "Specialisation", "Semester", "Course", "Applied Date", "Instructor", "Instructor Date", "Dean PGS", "Dean Date"]
    data = [[Paragraph(h, style_table_header) for h in headers]]
    
    for idx, s in enumerate(status_list, 1):
        data.append([
            Paragraph(str(idx), style_table_cell_center),
            Paragraph(s['AdmissionNo'] or '', style_table_cell),
            Paragraph(s['fullname'] or '', style_table_cell),
            Paragraph(s['Branchname'] or '', style_table_cell),
            Paragraph(s['semester_roman'] or '', style_table_cell_center),
            Paragraph(s['CourseName'] or '', style_table_cell),
            Paragraph(s['DateOfApply'].strftime('%d/%m/%Y') if s['DateOfApply'] else '', style_table_cell_center),
            Paragraph(s['TeacherStatus'] or '', style_table_cell_center),
            Paragraph(s['TeacherDate'] or '', style_table_cell_center),
            Paragraph(s['DeanStatus'] or '', style_table_cell_center),
            Paragraph(s['DeanDate'] or '', style_table_cell_center)
        ])
        
    table = Table(data, colWidths=[0.8*cm, 2*cm, 3*cm, 2.5*cm, 1.2*cm, 3.5*cm, 2*cm, 2*cm, 2*cm, 2*cm, 2*cm], repeatRows=1)
    table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
    ]))
    elements.append(table)
    
    doc.build(elements)
    buffer.seek(0)
    return buffer

def generate_batch_assignment_pdf(report_data, filters_info=None):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=1*cm, leftMargin=1*cm, topMargin=1*cm, bottomMargin=1*cm)
    styles = getSampleStyleSheet()
    
    style_centered = ParagraphStyle(name='Centered', parent=styles['Normal'], alignment=TA_CENTER, fontName='Helvetica-Bold', fontSize=12)
    style_table_header = ParagraphStyle(name='THeader', parent=styles['Normal'], fontSize=9, fontName='Helvetica-Bold', alignment=TA_CENTER)
    style_table_cell = ParagraphStyle(name='TCell', parent=styles['Normal'], fontSize=9, leading=11)
    style_table_cell_center = ParagraphStyle(name='TCellCenter', parent=styles['Normal'], fontSize=9, leading=11, alignment=TA_CENTER)
    
    elements = []
    logo_path = os.path.join(os.getcwd(), "app", "static", "images", "logo.png")
    
    logo = Image(logo_path, width=1.6*cm, height=1.6*cm) if os.path.exists(logo_path) else ""
    header_table = Table([
        [logo, Paragraph("CHAUDHARY CHARAN SINGH HARYANA AGRICULTURAL UNIVERSITY<br/><br/>BATCH ASSIGNMENT REPORT", style_centered)]
    ], colWidths=[2*cm, 16*cm])
    header_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
    elements.append(header_table)
    elements.append(Spacer(1, 0.5*cm))
    
    if filters_info:
        elements.append(Paragraph(f"College: {filters_info.get('college', 'N/A')}", styles['Normal']))
        elements.append(Paragraph(f"Session: {filters_info.get('session', 'N/A')} | Degree: {filters_info.get('degree', 'N/A')} | Type: {filters_info.get('type', 'N/A')}", styles['Normal']))
        elements.append(Spacer(1, 0.3*cm))

    headers = ["S.No", "Admission No", "Enrollment No", "Student Name", "Batch Name"]
    data = [[Paragraph(h, style_table_header) for h in headers]]
    
    for idx, s in enumerate(report_data, 1):
        data.append([
            Paragraph(str(idx), style_table_cell_center),
            Paragraph(s['AdmissionNo'] or '-', style_table_cell_center),
            Paragraph(s['enrollmentno'] or '-', style_table_cell_center),
            Paragraph(s['fullname'] or '', style_table_cell),
            Paragraph(s['BatchName'] or 'None', style_table_cell_center)
        ])
        
    table = Table(data, colWidths=[1*cm, 3.5*cm, 3.5*cm, 7*cm, 3.5*cm], repeatRows=1)
    table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
    ]))
    elements.append(table)
    
    doc.build(elements)
    buffer.seek(0)
    return buffer

def generate_thesis_detail_pdf(students_data, filters_info=None):
    import os
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=1*cm, leftMargin=1*cm, topMargin=1*cm, bottomMargin=1*cm)
    styles = getSampleStyleSheet()
    
    style_centered = ParagraphStyle(name='Centered', parent=styles['Normal'], alignment=TA_CENTER, fontName='Helvetica-Bold', fontSize=12)
    style_table_header = ParagraphStyle(name='THeader', parent=styles['Normal'], fontSize=8, fontName='Helvetica-Bold', alignment=TA_CENTER)
    style_table_cell = ParagraphStyle(name='TCell', parent=styles['Normal'], fontSize=7, leading=9)
    style_table_cell_center = ParagraphStyle(name='TCellCenter', parent=styles['Normal'], fontSize=7, leading=9, alignment=TA_CENTER)
    
    elements = []
    logo_path = os.path.join(os.getcwd(), "app", "static", "images", "logo.png")
    
    # Header with Logo
    logo = Image(logo_path, width=1.6*cm, height=1.6*cm) if os.path.exists(logo_path) else ""
    header_table = Table([
        [logo, Paragraph("CHAUDHARY CHARAN SINGH HARYANA AGRICULTURAL UNIVERSITY<br/><br/>STUDENT THESIS DETAIL REPORT", style_centered)]
    ], colWidths=[2*cm, 16*cm])
    header_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
    elements.append(header_table)
    elements.append(Spacer(1, 0.5*cm))
    
    if filters_info:
        elements.append(Paragraph(f"College: {filters_info.get('college', 'N/A')} | Session: {filters_info.get('session', 'N/A')} | Degree: {filters_info.get('degree', 'N/A')}", styles['Normal']))
        elements.append(Spacer(1, 0.3*cm))

    # Table Header
    headers = ["S.No", "Adm. No.", "Student Name", "Total Sem", "Thesis Sub. Date", "MC Date", "Viva Date", "Result Date", "Thesis Title"]
    data = [[Paragraph(h, style_table_header) for h in headers]]
    
    for idx, s in enumerate(students_data, 1):
        data.append([
            Paragraph(str(idx), style_table_cell_center),
            Paragraph(s['AdmissionNo'] or '', style_table_cell),
            Paragraph(s['fullname'] or '', style_table_cell),
            Paragraph(str(s['TotalSem'] or ''), style_table_cell_center),
            Paragraph(s['ThesisSubmissionDate'].strftime('%d/%m/%Y') if s['ThesisSubmissionDate'] else '', style_table_cell_center),
            Paragraph(s['MCDate'].strftime('%d/%m/%Y') if s['MCDate'] else '', style_table_cell_center),
            Paragraph(s['VivaNotificationDate'].strftime('%d/%m/%Y') if s['VivaNotificationDate'] else '', style_table_cell_center),
            Paragraph(s['ResultPublishDate'].strftime('%d/%m/%Y') if s['ResultPublishDate'] else '', style_table_cell_center),
            Paragraph(s['ThesisTitle'] or '', style_table_cell)
        ])
        
    table = Table(data, colWidths=[0.8*cm, 2*cm, 3*cm, 1.2*cm, 2.2*cm, 2.2*cm, 2.2*cm, 2.2*cm, 3.2*cm], repeatRows=1)
    table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
    ]))
    elements.append(table)
    
    doc.build(elements)
    buffer.seek(0)
    return buffer

def generate_add_with_status_pdf(status_list, filters_info=None):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=1*cm, leftMargin=1*cm, topMargin=1*cm, bottomMargin=1*cm)
    styles = getSampleStyleSheet()
    
    style_centered = ParagraphStyle(name='Centered', parent=styles['Normal'], alignment=TA_CENTER, fontName='Helvetica-Bold', fontSize=12)
    style_table_header = ParagraphStyle(name='THeader', parent=styles['Normal'], fontSize=8, fontName='Helvetica-Bold', alignment=TA_CENTER)
    style_table_cell = ParagraphStyle(name='TCell', parent=styles['Normal'], fontSize=7, leading=9)
    style_table_cell_center = ParagraphStyle(name='TCellCenter', parent=styles['Normal'], fontSize=7, leading=9, alignment=TA_CENTER)
    
    elements = []
    logo_path = os.path.join(os.getcwd(), "app", "static", "images", "logo.png")
    
    # Header with Logo
    logo = Image(logo_path, width=1.6*cm, height=1.6*cm) if os.path.exists(logo_path) else ""
    header_table = Table([
        [logo, Paragraph("CHAUDHARY CHARAN SINGH HARYANA AGRICULTURAL UNIVERSITY<br/><br/>ADDITION/WITHDRAWAL APPROVAL STATUS REPORT", style_centered)]
    ], colWidths=[2*cm, 16*cm])
    header_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
    elements.append(header_table)
    elements.append(Spacer(1, 0.5*cm))
    
    if filters_info:
        elements.append(Paragraph(f"Session: {filters_info.get('session', 'N/A')} | Degree: {filters_info.get('degree', 'N/A')}", styles['Normal']))
        elements.append(Spacer(1, 0.3*cm))

    headers = ["S.No", "Adm. No", "Name", "Specialisation", "Semester", "Course", "Type", "Applied Date", "Instructor", "Advisor", "Fee"]
    data = [[Paragraph(h, style_table_header) for h in headers]]
    
    for idx, s in enumerate(status_list, 1):
        data.append([
            Paragraph(str(idx), style_table_cell_center),
            Paragraph(s['AdmissionNo'] or '', style_table_cell),
            Paragraph(s['fullname'] or '', style_table_cell),
            Paragraph(s['Branchname'] or '', style_table_cell),
            Paragraph(s['semester_roman'] or '', style_table_cell_center),
            Paragraph(s['CourseName'] or '', style_table_cell),
            Paragraph(s['RequestType'] or '', style_table_cell_center),
            Paragraph(s['DateOfApply'].strftime('%d/%m/%Y') if s['DateOfApply'] else '', style_table_cell_center),
            Paragraph(s['InstructorStatus'] or '', style_table_cell_center),
            Paragraph(s['AdvisorStatus'] or '', style_table_cell_center),
            Paragraph('Paid' if s['Approval'] else 'Unpaid', style_table_cell_center)
        ])
        
    table = Table(data, colWidths=[0.8*cm, 1.8*cm, 2.5*cm, 2*cm, 1.2*cm, 2.5*cm, 1.5*cm, 1.8*cm, 1.6*cm, 1.6*cm, 1.5*cm], repeatRows=1)
    table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
    ]))
    elements.append(table)
    
    doc.build(elements)
    buffer.seek(0)
    return buffer

def generate_advisory_status_pdf(status_list, filters_info=None):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=1*cm, leftMargin=1*cm, topMargin=1*cm, bottomMargin=1*cm)
    styles = getSampleStyleSheet()
    
    style_centered = ParagraphStyle(name='Centered', parent=styles['Normal'], alignment=TA_CENTER, fontName='Helvetica-Bold', fontSize=12)
    style_table_header = ParagraphStyle(name='THeader', parent=styles['Normal'], fontSize=7, fontName='Helvetica-Bold', alignment=TA_CENTER)
    style_table_cell = ParagraphStyle(name='TCell', parent=styles['Normal'], fontSize=6, leading=8)
    style_table_cell_center = ParagraphStyle(name='TCellCenter', parent=styles['Normal'], fontSize=6, leading=8, alignment=TA_CENTER)
    
    elements = []
    logo_path = os.path.join(os.getcwd(), "app", "static", "images", "logo.png")
    
    # Header with Logo
    logo = Image(logo_path, width=1.6*cm, height=1.6*cm) if os.path.exists(logo_path) else ""
    header_table = Table([
        [logo, Paragraph("CHAUDHARY CHARAN SINGH HARYANA AGRICULTURAL UNIVERSITY<br/><br/>ADVISORY CREATION AND APPROVAL STATUS REPORT", style_centered)]
    ], colWidths=[2*cm, 24*cm])
    header_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
    elements.append(header_table)
    elements.append(Spacer(1, 0.5*cm))
    
    if filters_info:
        elements.append(Paragraph(f"College: {filters_info.get('college', 'N/A')} | Session: {filters_info.get('session', 'N/A')} | Degree: {filters_info.get('degree', 'N/A')}", styles['Normal']))
        elements.append(Spacer(1, 0.3*cm))

    headers = ["S.No", "Adm. No", "Name", "Department", "Major Advisor", "Spec. Made", "Minor/Supp", "HOD Appr.", "HOD Date", "Dean Appr.", "Dean Date", "PGS Appr.", "PGS Date", "CP Made", "CP Appr.", "CP Date"]
    data = [[Paragraph(h, style_table_header) for h in headers]]
    
    for idx, s in enumerate(status_list, 1):
        data.append([
            Paragraph(str(idx), style_table_cell_center),
            Paragraph(s['AdmissionNo'] or '', style_table_cell),
            Paragraph(s['fullname'] or '', style_table_cell),
            Paragraph(s['Branchname'] or '', style_table_cell),
            Paragraph(s['MajorAdvisorMade'] or '', style_table_cell_center),
            Paragraph(s['SpecializationMade'] or '', style_table_cell_center),
            Paragraph(s['MemberMinorMade'] or '', style_table_cell_center),
            Paragraph(s['HodApproval'] or '', style_table_cell),
            Paragraph(s['HodApprovalDate'] or '', style_table_cell_center),
            Paragraph(s['CollegeDeanApproval'] or '', style_table_cell),
            Paragraph(s['CollegeDeanApprovalDate'] or '', style_table_cell_center),
            Paragraph(s['DeanPgsApproval'] or '', style_table_cell),
            Paragraph(s['DeanPgsApprovalDate'] or '', style_table_cell_center),
            Paragraph(s['CoursePlanMade'] or '', style_table_cell_center),
            Paragraph(s['CoursePlanApproval'] or '', style_table_cell_center),
            Paragraph(s['CoursePlanApprovalDate'] or '', style_table_cell_center)
        ])
        
    table = Table(data, colWidths=[0.7*cm, 1.5*cm, 2.5*cm, 2*cm, 1.2*cm, 1.2*cm, 1.2*cm, 2.5*cm, 1.5*cm, 2.5*cm, 1.5*cm, 2.5*cm, 1.5*cm, 1.2*cm, 1.2*cm, 1.5*cm], repeatRows=1)
    table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
    ]))
    elements.append(table)
    
    doc.build(elements)
    buffer.seek(0)
    return buffer
