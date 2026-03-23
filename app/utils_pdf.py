import io
import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_RIGHT, TA_LEFT
from reportlab.lib.units import inch

def generate_advisory_committee_report(student_info, committee_data):
    buffer = io.BytesIO()
    # 0.5 inch margins as requested
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                            rightMargin=0.5*inch, leftMargin=0.5*inch,
                            topMargin=0.5*inch, bottomMargin=0.5*inch)
    
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='CenterHeading', alignment=TA_CENTER, fontSize=10, fontName='Helvetica-Bold', leading=12))
    styles.add(ParagraphStyle(name='NormalText', fontSize=9, fontName='Helvetica', leading=14, alignment=TA_JUSTIFY))
    styles.add(ParagraphStyle(name='NormalLeft', fontSize=9, fontName='Helvetica', leading=14))
    styles.add(ParagraphStyle(name='SignatureText', fontSize=9, fontName='Helvetica', leading=12))
    styles.add(ParagraphStyle(name='SignatureTextRight', fontSize=9, fontName='Helvetica', leading=12, alignment=TA_RIGHT))
    styles.add(ParagraphStyle(name='SignatureBold', fontSize=9, fontName='Helvetica-Bold', leading=12))
    styles.add(ParagraphStyle(name='SignatureBoldRight', fontSize=9, fontName='Helvetica-Bold', leading=12, alignment=TA_RIGHT))
    
    elements = []
    
    # Header with Logo
    logo_path = os.path.join('app', 'static', 'images', 'logo.png')
    if os.path.exists(logo_path):
        img = Image(logo_path, width=0.7*inch, height=0.7*inch)
        header_data = [
            [img, Paragraph("CHAUDHARY CHARAN SINGH HARYANA AGRICULTURAL UNIVERSITY, HISAR", styles['CenterHeading'])]
        ]
        header_table = Table(header_data, colWidths=[1*inch, 6*inch])
        header_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (0,0), 'LEFT'),
            ('ALIGN', (1,0), (1,0), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        elements.append(header_table)
    else:
        elements.append(Paragraph("CHAUDHARY CHARAN SINGH HARYANA AGRICULTURAL UNIVERSITY, HISAR", styles['CenterHeading']))
    
    elements.append(Spacer(1, 10))
    
    elements.append(Paragraph("FORM FOR RECOMMENDATION OF ADVISORY COMMITTEE", styles['CenterHeading']))
    elements.append(Spacer(1, 5))
    dept_name = student_info.get('department_name', '......................')
    colg_name = student_info.get('collegename', '......................')
    elements.append(Paragraph(f"Department of {dept_name}, {colg_name} , CCS HAU, HISAR", styles['CenterHeading']))
    elements.append(Spacer(1, 15))
    
    # Body Text
    adm_no = student_info.get('AdmissionNo') or student_info.get('enrollmentno', '')
    intro = f"The following members of the postgraduate faculty are proposed on the advisory committee to guide the postgraduate student <b>{student_info.get('fullname', '').upper()}</b> , Admn.No <b>{adm_no}</b> ."
    elements.append(Paragraph(intro, styles['NormalLeft']))
    elements.append(Spacer(1, 10))
    
    # Subject Details
    sub_data = [
        ["1. Major Subject", ":", student_info.get('major_name', '')],
        ["2. Minor Subject", ":", student_info.get('minor_name', '')]
    ]
    sub_table = Table(sub_data, colWidths=[130, 20, 400])
    sub_table.setStyle(TableStyle([
        ('FONT', (0,0), (-1,-1), 'Helvetica', 9),
        ('ALIGN', (0,0), (0,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(sub_table)
    elements.append(Spacer(1, 10))
    
    # Committee Details
    com_data = []
    role_order = {
        'Major Advisor': 1,
        'Member From Major Subject': 2,
        'Member From Minor Subject': 3,
        'Member From Supporting Subject': 4
    }
    
    sorted_committee = sorted(committee_data, key=lambda x: role_order.get(x['role_name'], 99))
    
    for member in sorted_committee:
        if member.get('role_name') == 'Dean PGS Nominee':
            continue # Handled in footer
            
        role = member.get('role_name', '') + " :"
        adv_name_raw = member.get('advisor_name', '')
        adv_name = adv_name_raw.split('||')[0].strip() if '||' in adv_name_raw else adv_name_raw
        designation = member.get('designation', '') or ''
        dept = f"({member.get('department', '')})" if member.get('department') else ""
        
        details = f"{adv_name}, {designation},<br/>Deptt. of {dept}"
        com_data.append([role, Paragraph(details, styles['NormalLeft'])])
        
    com_table = Table(com_data, colWidths=[200, 350])
    com_table.setStyle(TableStyle([
        ('FONT', (0,0), (-1,-1), 'Helvetica', 9),
        ('ALIGN', (0,0), (0,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    elements.append(com_table)
    elements.append(Spacer(1, 10))
    
    # Guidelines paragraph
    major_adv = next((m for m in sorted_committee if m.get('role_name') == 'Major Advisor'), None)
    major_adv_name_raw = major_adv.get('advisor_name', '') if major_adv else ''
    major_adv_name = major_adv_name_raw.split('||')[0].strip() if major_adv_name_raw and '||' in major_adv_name_raw else (major_adv_name_raw or '......................')
    major_adv_desig = major_adv.get('designation', '') if major_adv else '......................'
    
    guide_text1 = f"1. \"Certified that <b>{major_adv_name}</b> has been working as <b>{major_adv_desig}</b> in this Department in teaching/research/ extension and is posted at Hisar /Outstation\".He/ She is already guiding ___ postgraduate student. By including this student there shall be ____ students with him /her which have been assigned in accordance with the existing norms."
    elements.append(Paragraph(guide_text1, styles['NormalText']))
    elements.append(Spacer(1, 8))
    
    guide_text2 = f"2. Certified that <b>{major_adv_name}</b> has already guided ___ Nos. student and they have submitted the thesis."
    elements.append(Paragraph(guide_text2, styles['NormalText']))
    elements.append(Spacer(1, 8))
    
    guide_text3 = "3.Certified that allotment has been made as per guidelines and rules of CCSHAU and with the approval of Departmental Committee vide DAC proceedings no. ______________________________________________ (Photocopy enclosed)."
    elements.append(Paragraph(guide_text3, styles['NormalText']))
    
    elements.append(Spacer(1, 30))
    
    # Signatures Formatting (Strict Layout)
    hod_name = student_info.get('hod_name') or '..........................'
    hod_date = student_info.get('hod_date')
    hod_date_str = f"[{hod_date.strftime('%d/%m/%Y')}]" if hod_date else ""

    # Line 1: Names
    # Line 2: Titles
    # Line 3: Dates (if any)
    sig_data = [
        [Paragraph(major_adv_name, styles['SignatureBold']), Paragraph(hod_name, styles['SignatureBoldRight'])],
        [Paragraph("Major Advisor", styles['SignatureText']), Paragraph("Head of Department", styles['SignatureTextRight'])],
        [Paragraph("", styles['SignatureText']), Paragraph(hod_date_str, styles['SignatureTextRight'])]
    ]
    sig_table = Table(sig_data, colWidths=[275, 275])
    sig_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))
    elements.append(sig_table)
    
    elements.append(Spacer(1, 10))
    elements.append(Paragraph("Countersigned", styles['CenterHeading']))
    elements.append(Spacer(1, 20))
    
    dean_txt = f"Dean, {colg_name}"
    dean_name = student_info.get('dean_name') or '..........................'
    dean_date = student_info.get('Collegedean_date')
    dean_date_str = f"[{dean_date.strftime('%d/%m/%Y')}]" if dean_date else ""

    # Nominee block parsing
    nominee = next((m for m in sorted_committee if m.get('role_name') == 'Dean PGS Nominee'), None)
    nom_name = ''
    nom_dept = ''
    if nominee:
        adv_name_raw = nominee.get('advisor_name', '')
        nom_name = adv_name_raw.split('||')[0].strip() if '||' in adv_name_raw else adv_name_raw
        spec = nominee.get('specialization')
        dept_str = nominee.get('department', '')
        # Live format: Dr. Name, Deptt of DeptName (Specialization)
        nom_dept = f"Deptt of {dept_str}"
        if spec:
             nom_dept += f" ({spec})"

    # Footer Layout
    # Left Column: Dean Name -> Dean Title -> Dean Date -> Nominee
    # Right Column: PGS Name -> PGS Date -> PGS Title
    deanpgs_name = student_info.get('deanpgs_name') or '..........................'
    deanpgs_date = student_info.get('deanpgs_date')
    deanpgs_date_str = f"{deanpgs_date.strftime('%d/%m/%Y')}" if deanpgs_date else ""

    footer_data = [
        [Paragraph(dean_name, styles['SignatureBold']), Paragraph(deanpgs_name, styles['SignatureBoldRight'])],
        [Paragraph(dean_txt, styles['SignatureText']), Paragraph(deanpgs_date_str, styles['SignatureTextRight'])],
        [Paragraph(dean_date_str, styles['SignatureText']), Paragraph("Dean, Post-Graduate Studies.", styles['SignatureTextRight'])]
    ]
    
    if nominee:
        footer_data.append([Paragraph(f"Dean, PGS Nominee {nom_name}, {nom_dept}", styles['NormalText']), ""])
        
    sig_table2 = Table(footer_data, colWidths=[350, 200])
    sig_table2.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))
    elements.append(sig_table2)
    
    doc.build(elements)
    buffer.seek(0)
    return buffer
