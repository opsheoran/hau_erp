import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

def generate_advisory_committee_report(student_info, committee_data):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                            rightMargin=40, leftMargin=40,
                            topMargin=40, bottomMargin=40)
    
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='CenterHeading', alignment=1, fontSize=12, fontName='Helvetica-Bold'))
    styles.add(ParagraphStyle(name='NormalText', fontSize=11, fontName='Helvetica', leading=14))
    
    elements = []
    
    # Header
    elements.append(Paragraph("FORM FOR RECOMMENDATION OF ADVISORY COMMITTEE", styles['CenterHeading']))
    elements.append(Spacer(1, 10))
    dept_name = student_info.get('department_name', 'Unknown Department')
    colg_name = student_info.get('collegename', 'Unknown College')
    elements.append(Paragraph(f"Department of {dept_name}, {colg_name} , CCS HAU, HISAR", styles['CenterHeading']))
    elements.append(Spacer(1, 20))
    
    # Body Text
    intro = f"The following members of the postgraduate faculty are proposed on the advisory committee to guide the postgraduate student <b>{student_info.get('fullname', '')}</b> , Admn.No <b>{student_info.get('AdmissionNo') or student_info.get('enrollmentno', '')}</b> ."
    elements.append(Paragraph(intro, styles['NormalText']))
    elements.append(Spacer(1, 15))
    
    # Subject Details
    sub_data = [
        ["1. Major Subject", ":", student_info.get('major_name', '')],
        ["2. Minor Subject", ":", student_info.get('minor_name', '')],
        ["3. Supporting Subject", ":", student_info.get('supporting_name', '')]
    ]
    sub_table = Table(sub_data, colWidths=[150, 20, 350])
    sub_table.setStyle(TableStyle([
        ('FONT', (0,0), (-1,-1), 'Helvetica', 11),
        ('ALIGN', (0,0), (0,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    elements.append(sub_table)
    elements.append(Spacer(1, 20))
    
    # Committee Details
    com_data = []
    role_order = {
        'Major Advisor': 1,
        'Member From Major Subject': 2,
        'Member From Minor Subject': 3,
        'Member From Supporting Subject': 4,
        'Dean PGS Nominee': 5
    }
    
    sorted_committee = sorted(committee_data, key=lambda x: role_order.get(x['role_name'], 99))
    
    for member in sorted_committee:
        role = member['role_name'] + " :"
        adv_name = member['advisor_name'].split('||')[0].strip() if '||' in member['advisor_name'] else member['advisor_name']
        dept = f"({member['department']})" if member['department'] else ""
        com_data.append([role, f"{adv_name} {dept}"])
        
    com_table = Table(com_data, colWidths=[200, 300])
    com_table.setStyle(TableStyle([
        ('FONT', (0,0), (-1,-1), 'Helvetica', 11),
        ('ALIGN', (0,0), (0,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 12),
    ]))
    elements.append(com_table)
    elements.append(Spacer(1, 40))
    
    # Signatures
    elements.append(Paragraph("Approved by the Departmental Committee vide DAC proceedings no. ______________________________________________ (Photocopy enclosed).", styles['NormalText']))
    elements.append(Spacer(1, 50))
    
    sig_data = [
        ["Major Advisor", "Head of Department"],
    ]
    sig_table = Table(sig_data, colWidths=[260, 260])
    sig_table.setStyle(TableStyle([
        ('FONT', (0,0), (-1,-1), 'Helvetica-Bold', 11),
        ('ALIGN', (0,0), (0,-1), 'LEFT'),
        ('ALIGN', (1,0), (1,-1), 'RIGHT'),
    ]))
    elements.append(sig_table)
    
    elements.append(Spacer(1, 40))
    elements.append(Paragraph("Countersigned", styles['CenterHeading']))
    elements.append(Spacer(1, 40))
    
    sig_data2 = [
        [f"Dean, {colg_name}", "Dean, Post-Graduate Studies."]
    ]
    sig_table2 = Table(sig_data2, colWidths=[260, 260])
    sig_table2.setStyle(TableStyle([
        ('FONT', (0,0), (-1,-1), 'Helvetica-Bold', 11),
        ('ALIGN', (0,0), (0,-1), 'LEFT'),
        ('ALIGN', (1,0), (1,-1), 'RIGHT'),
    ]))
    elements.append(sig_table2)
    
    # Adding Footer lines dynamically if nominee exists
    nominee = next((m for m in sorted_committee if m['role_name'] == 'Dean PGS Nominee'), None)
    if nominee:
        elements.append(Spacer(1, 40))
        adv_name = nominee['advisor_name'].split('||')[0].strip() if '||' in nominee['advisor_name'] else nominee['advisor_name']
        dept = nominee['department'] or ''
        elements.append(Paragraph(f"Dean, PGS Nominee : {adv_name}, Deptt of {dept}", styles['NormalText']))
        
    doc.build(elements)
    buffer.seek(0)
    return buffer
