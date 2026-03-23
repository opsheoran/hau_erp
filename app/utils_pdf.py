import io
import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.units import inch

def generate_advisory_committee_report(student_info, committee_data):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                            rightMargin=40, leftMargin=40,
                            topMargin=40, bottomMargin=40)
    
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='CenterHeading', alignment=TA_CENTER, fontSize=11, fontName='Helvetica-Bold', leading=14))
    styles.add(ParagraphStyle(name='NormalText', fontSize=10, fontName='Helvetica', leading=16, alignment=TA_JUSTIFY))
    styles.add(ParagraphStyle(name='NormalLeft', fontSize=10, fontName='Helvetica', leading=16))
    
    elements = []
    
    # Header with Logo
    logo_path = os.path.join('app', 'static', 'images', 'logo.png')
    if os.path.exists(logo_path):
        img = Image(logo_path, width=0.8*inch, height=0.8*inch)
        # Position logo and text
        header_data = [
            [img, Paragraph("CHAUDHARY CHARAN SINGH HARYANA AGRICULTURAL UNIVERSITY, HISAR", styles['CenterHeading'])]
        ]
        header_table = Table(header_data, colWidths=[1*inch, 5*inch])
        header_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (0,0), 'LEFT'),
            ('ALIGN', (1,0), (1,0), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        elements.append(header_table)
    else:
        elements.append(Paragraph("CHAUDHARY CHARAN SINGH HARYANA AGRICULTURAL UNIVERSITY, HISAR", styles['CenterHeading']))
    
    elements.append(Spacer(1, 15))
    
    elements.append(Paragraph("FORM FOR RECOMMENDATION OF ADVISORY COMMITTEE", styles['CenterHeading']))
    elements.append(Spacer(1, 10))
    dept_name = student_info.get('department_name', '......................')
    colg_name = student_info.get('collegename', '......................')
    elements.append(Paragraph(f"Department of {dept_name}, {colg_name} , CCS HAU, HISAR", styles['CenterHeading']))
    elements.append(Spacer(1, 20))
    
    # Body Text
    adm_no = student_info.get('AdmissionNo') or student_info.get('enrollmentno', '')
    intro = f"The following members of the postgraduate faculty are proposed on the advisory committee to guide the postgraduate student <b>{student_info.get('fullname', '').upper()}</b> , Admn.No <b>{adm_no}</b> ."
    elements.append(Paragraph(intro, styles['NormalLeft']))
    elements.append(Spacer(1, 15))
    
    # Subject Details
    sub_data = [
        ["1. Major Subject", ":", student_info.get('major_name', '')],
        ["2. Minor Subject", ":", student_info.get('minor_name', '')]
    ]
    sub_table = Table(sub_data, colWidths=[130, 20, 350])
    sub_table.setStyle(TableStyle([
        ('FONT', (0,0), (-1,-1), 'Helvetica', 10),
        ('ALIGN', (0,0), (0,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    elements.append(sub_table)
    elements.append(Spacer(1, 15))
    
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
        if member['role_name'] == 'Dean PGS Nominee':
            continue # Handled in footer
            
        role = member['role_name'] + " :"
        adv_name = member['advisor_name'].split('||')[0].strip() if '||' in member['advisor_name'] else member['advisor_name']
        designation = member['designation'] or ''
        dept = f"({member['department']})" if member['department'] else ""
        
        details = f"{adv_name}, {designation},<br/>Deptt. of {dept}"
        com_data.append([role, Paragraph(details, styles['NormalLeft'])])
        
    com_table = Table(com_data, colWidths=[200, 300])
    com_table.setStyle(TableStyle([
        ('FONT', (0,0), (-1,-1), 'Helvetica', 10),
        ('ALIGN', (0,0), (0,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
    ]))
    elements.append(com_table)
    elements.append(Spacer(1, 15))
    
    # Guidelines paragraph
    major_adv = next((m for m in sorted_committee if m['role_name'] == 'Major Advisor'), None)
    major_adv_name = major_adv['advisor_name'].split('||')[0].strip() if major_adv and '||' in major_adv['advisor_name'] else (major_adv['advisor_name'] if major_adv else '......................')
    major_adv_desig = major_adv['designation'] if major_adv else '......................'
    
    guide_text1 = f"1. \"Certified that <b>{major_adv_name}</b> has been working as <b>{major_adv_desig}</b> in this Department in teaching/research/ extension and is posted at Hisar /Outstation\".He/ She is already guiding ___ postgraduate student. By including this student there shall be ____ students with him /her which have been assigned in accordance with the existing norms."
    elements.append(Paragraph(guide_text1, styles['NormalText']))
    elements.append(Spacer(1, 10))
    
    guide_text2 = f"2. Certified that <b>{major_adv_name}</b> has already guided ___ Nos. student and they have submitted the thesis."
    elements.append(Paragraph(guide_text2, styles['NormalText']))
    elements.append(Spacer(1, 10))
    
    guide_text3 = "3.Certified that allotment has been made as per guidelines and rules of CCSHAU and with the approval of Departmental Committee vide DAC proceedings no. ______________________________________________ (Photocopy enclosed)."
    elements.append(Paragraph(guide_text3, styles['NormalText']))
    
    elements.append(Spacer(1, 60))
    
    sig_data = [
        ["Major Advisor", "Head of Department"],
    ]
    sig_table = Table(sig_data, colWidths=[260, 260])
    sig_table.setStyle(TableStyle([
        ('FONT', (0,0), (-1,-1), 'Helvetica-Bold', 10),
        ('ALIGN', (0,0), (0,-1), 'LEFT'),
        ('ALIGN', (1,0), (1,-1), 'RIGHT'),
    ]))
    elements.append(sig_table)
    
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("Countersigned", styles['CenterHeading']))
    elements.append(Spacer(1, 40))
    
    # We dynamically format the Dean text block
    colg_parts = colg_name.split(' ')
    if len(colg_parts) > 3:
        dean_txt = f"Dean ,{' '.join(colg_parts[:3])}<br/>{' '.join(colg_parts[3:])}"
    else:
        dean_txt = f"Dean ,{colg_name}"
        
    sig_data2 = [
        [Paragraph(dean_txt, ParagraphStyle(name='DeanL', fontName='Helvetica-Bold', fontSize=10, leading=12)), 
         "Dean,Post-Graduate Studies."]
    ]
    sig_table2 = Table(sig_data2, colWidths=[260, 260])
    sig_table2.setStyle(TableStyle([
        ('FONT', (0,0), (-1,-1), 'Helvetica-Bold', 10),
        ('ALIGN', (0,0), (0,-1), 'LEFT'),
        ('ALIGN', (1,0), (1,-1), 'RIGHT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    elements.append(sig_table2)
    
    # Adding Footer lines dynamically if nominee exists
    nominee = next((m for m in sorted_committee if m['role_name'] == 'Dean PGS Nominee'), None)
    if nominee:
        elements.append(Spacer(1, 30))
        adv_name = nominee['advisor_name'].split('||')[0].strip() if '||' in nominee['advisor_name'] else nominee['advisor_name']
        dept = nominee['department'] or ''
        elements.append(Paragraph(f"Dean,PGS Nominee  {adv_name}, Deptt of  {dept}", styles['NormalText']))
        
    doc.build(elements)
    buffer.seek(0)
    return buffer
