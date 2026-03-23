import io
import os
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_RIGHT, TA_LEFT
from reportlab.lib.units import inch


def generate_advisory_committee_report(student_info, committee_data):
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.5 * inch,
        leftMargin=0.5 * inch,
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch,
    )

    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name='UnivTitle',
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        alignment=TA_CENTER,
        spaceAfter=0,
    ))

    styles.add(ParagraphStyle(
        name='DeptTitle',
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        alignment=TA_CENTER,
        spaceAfter=0,
    ))

    styles.add(ParagraphStyle(
        name='BodyJustify',
        fontName='Times-Roman',
        fontSize=10,
        leading=14,
        alignment=TA_JUSTIFY,
        spaceAfter=0,
    ))

    styles.add(ParagraphStyle(
        name='LabelRight',
        fontName='Times-Roman',
        fontSize=10,
        leading=14,
        alignment=TA_RIGHT,
    ))

    styles.add(ParagraphStyle(
        name='ValueBoldItalic',
        fontName='Times-BoldItalic',
        fontSize=10,
        leading=14,
        alignment=TA_LEFT,
    ))

    styles.add(ParagraphStyle(
        name='Colon',
        fontName='Times-Roman',
        fontSize=10,
        leading=14,
        alignment=TA_CENTER,
    ))

    styles.add(ParagraphStyle(
        name='CertText',
        fontName='Times-Roman',
        fontSize=10,
        leading=14,
        alignment=TA_JUSTIFY,
        spaceAfter=6,
    ))

    styles.add(ParagraphStyle(
        name='SigName',
        fontName='Times-Bold',
        fontSize=10,
        leading=13,
        alignment=TA_LEFT,
    ))
    styles.add(ParagraphStyle(
        name='SigNameCenter',
        fontName='Times-Bold',
        fontSize=10,
        leading=13,
        alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        name='SigNameRight',
        fontName='Times-Bold',
        fontSize=10,
        leading=13,
        alignment=TA_RIGHT,
    ))

    styles.add(ParagraphStyle(
        name='SigRole',
        fontName='Times-Roman',
        fontSize=10,
        leading=13,
        alignment=TA_LEFT,
    ))
    styles.add(ParagraphStyle(
        name='SigRoleCenter',
        fontName='Times-Roman',
        fontSize=10,
        leading=13,
        alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        name='SigRoleRight',
        fontName='Times-Roman',
        fontSize=10,
        leading=13,
        alignment=TA_RIGHT,
    ))

    styles.add(ParagraphStyle(
        name='NomineeText',
        fontName='Times-Roman',
        fontSize=10,
        leading=14,
        alignment=TA_LEFT,
        spaceAfter=0,
    ))

    styles.add(ParagraphStyle(
        name='NomineeBold',
        fontName='Times-Bold',
        fontSize=10,
        leading=14,
        alignment=TA_LEFT,
        spaceAfter=0,
    ))

    elements = []

    # ── Header ────────────────────────────────────────────────────────────────
    logo_path = os.path.join('app', 'static', 'images', 'logo.png')
    univ_para = Paragraph(
        "CHAUDHARY CHARAN SINGH HARYANA AGRICULTURAL UNIVERSITY, HISAR",
        styles['UnivTitle'],
    )

    if os.path.exists(logo_path):
        img = Image(logo_path, width=0.75 * inch, height=0.75 * inch)
        header_data = [[img, univ_para]]
        header_table = Table(header_data, colWidths=[0.9 * inch, 6.1 * inch])
        header_table.setStyle(TableStyle([
            ('ALIGN',        (0, 0), (0, 0), 'LEFT'),
            ('ALIGN',        (1, 0), (1, 0), 'CENTER'),
            ('VALIGN',       (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING',  (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ]))
        elements.append(header_table)
    else:
        elements.append(univ_para)

    elements.append(Spacer(1, 8))

    # ── Form Title ────────────────────────────────────────────────────────────
    elements.append(Paragraph(
        "FORM FOR RECOMMENDATION OF ADVISORY COMMITTEE",
        styles['UnivTitle'],
    ))
    elements.append(Spacer(1, 2))

    dept_name = student_info.get('department_name', '......................')
    colg_name = student_info.get('collegename',     '......................')
    elements.append(Paragraph(
        f"Department of {dept_name}, {colg_name} , CCS HAU, HISAR",
        styles['DeptTitle'],
    ))
    elements.append(Spacer(1, 10))

    # ── Introduction sentence ─────────────────────────────────────────────────
    adm_no   = student_info.get('AdmissionNo') or student_info.get('enrollmentno', '')
    fullname = student_info.get('fullname', '').upper()
    intro = (
        "The following members of the postgraduate faculty are proposed on the advisory "
        f"committee to guide the postgraduate student <b>{fullname}</b> , "
        f"Admn.No <b>{adm_no}</b> ."
    )
    elements.append(Paragraph(intro, styles['BodyJustify']))
    elements.append(Spacer(1, 8))

    # ── Subject Details ───────────────────────────────────────────────────────
    sub_data = [
        [
            Paragraph("1. Major Subject", styles['LabelRight']),
            Paragraph(":", styles['Colon']),
            Paragraph(
                f"<b><i>{student_info.get('major_name', '')}</i></b>",
                styles['ValueBoldItalic']
            ),
        ],
        [
            Paragraph("2. Minor Subject", styles['LabelRight']),
            Paragraph(":", styles['Colon']),
            Paragraph(
                f"<b><i>{student_info.get('minor_name', '')}</i></b>",
                styles['ValueBoldItalic']
            ),
        ],
    ]
    sub_table = Table(sub_data, colWidths=[150, 18, 382])
    sub_table.setStyle(TableStyle([
        ('VALIGN',       (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING',  (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING',(0, 0), (-1, -1), 6),
        ('TOPPADDING',   (0, 0), (-1, -1), 0),
    ]))
    elements.append(sub_table)
    elements.append(Spacer(1, 8))

    # ── Committee Members ─────────────────────────────────────────────────────
    role_order = {
        'Major Advisor':                  1,
        'Member From Major Subject':      2,
        'Member From Minor Subject':      3,
        'Member From Supporting Subject': 4,
    }
    sorted_committee = sorted(
        committee_data,
        key=lambda x: role_order.get(x.get('role_name', ''), 99),
    )

    com_data = []
    for member in sorted_committee:
        if member.get('role_name') == 'Dean PGS Nominee':
            continue

        role_label   = member.get('role_name', '') + " :"
        adv_name_raw = member.get('advisor_name', '')
        adv_name     = (
            adv_name_raw.split('||')[0].strip()
            if '||' in adv_name_raw else adv_name_raw
        )
        designation  = member.get('designation', '') or ''
        dept_raw     = member.get('department', '')  or ''
        spec_raw     = member.get('specialization', '') or ''

        dept_part = f"Deptt. of <b>{dept_raw}"
        if spec_raw:
            dept_part += f" ({spec_raw})"
        dept_part += "</b>"

        details_text = f"<b>{adv_name}, {designation},</b><br/>{dept_part}"

        com_data.append([
            Paragraph(role_label,   styles['LabelRight']),
            Paragraph(":",          styles['Colon']),
            Paragraph(details_text, styles['ValueBoldItalic']),
        ])

    com_table = Table(com_data, colWidths=[190, 18, 342])
    com_table.setStyle(TableStyle([
        ('VALIGN',       (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING',  (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING',(0, 0), (-1, -1), 10),
        ('TOPPADDING',   (0, 0), (-1, -1), 0),
    ]))
    elements.append(com_table)
    elements.append(Spacer(1, 8))

    # ── Certification paragraphs ──────────────────────────────────────────────
    major_adv = next(
        (m for m in sorted_committee if m.get('role_name') == 'Major Advisor'), None
    )
    if major_adv:
        adv_name_raw    = major_adv.get('advisor_name', '')
        major_adv_name  = (
            adv_name_raw.split('||')[0].strip()
            if '||' in adv_name_raw else adv_name_raw
        )
        major_adv_desig = major_adv.get('designation', '') or '......................'
    else:
        major_adv_name  = '......................'
        major_adv_desig = '......................'

    cert1 = (
        f"1. \"Certified that <b>{major_adv_name}</b> has been working as "
        f"<b>{major_adv_desig}</b> in this Department in teaching/research/"
        "extension and is posted at Hisar /Outstation\".He/ She is already guiding ___ "
        "postgraduate student. By including this student there shall be ____ students "
        "with him /her which have been assigned in accordance with the existing norms."
    )
    elements.append(Paragraph(cert1, styles['CertText']))

    cert2 = (
        f"2. Certified that <b>{major_adv_name}</b> has already guided ___ Nos. "
        "student and they have submitted the thesis."
    )
    elements.append(Paragraph(cert2, styles['CertText']))

    cert3 = (
        "3.Certified that allotment has been made as per guidelines and rules of "
        "CCSHAU and with the approval of Departmental Committee vide DAC proceedings "
        "no. ______________________________________________ (Photocopy enclosed)."
    )
    elements.append(Paragraph(cert3, styles['CertText']))

    elements.append(Spacer(1, 20))

    # ── Signature / footer block ──────────────────────────────────────────────
    hod_name      = student_info.get('hod_name')        or '..........................'
    hod_date      = student_info.get('hod_date')
    hod_date_str  = f"[{hod_date.strftime('%d/%m/%Y')}]"  if hod_date  else ""

    dean_name     = student_info.get('dean_name')        or '..........................'
    dean_date     = student_info.get('Collegedean_date')
    dean_date_str = f"[{dean_date.strftime('%d/%m/%Y')}]" if dean_date else ""
    dean_txt      = f"Dean ,{colg_name}"

    deanpgs_name     = student_info.get('deanpgs_name') or '..........................'
    deanpgs_date     = student_info.get('deanpgs_date')
    deanpgs_date_str = deanpgs_date.strftime('%d/%m/%Y') if deanpgs_date else ""

    # ── Top 3-column signature block ─────────────────────────────────────────
    sig_rows = [
        [
            Paragraph(major_adv_name,  styles['SigName']),
            Paragraph(hod_name,        styles['SigNameCenter']),
            Paragraph(dean_name,       styles['SigNameRight']),
        ],
        [
            Paragraph("Major Advisor", styles['SigRole']),
            Paragraph("Head of the Department", styles['SigRoleCenter']),
            Paragraph("Dean",        styles['SigRoleRight']),
        ],
        [
            Paragraph("",                   styles['SigRole']),
            Paragraph(hod_date_str,    styles['SigRoleCenter']),
            Paragraph(f"{dean_date_str}<br/>Countersigned", styles['SigRoleRight']),
        ],
    ]
    sig_table = Table(sig_rows, colWidths=[183, 184, 183])
    sig_table.setStyle(TableStyle([
        ('VALIGN',       (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING',  (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING',(0, 0), (-1, -1), 1),
        ('TOPPADDING',   (0, 0), (-1, -1), 1),
    ]))
    elements.append(sig_table)
    elements.append(Spacer(1, 10))

    # ── Nominee line + Dean PGS block ────────────────────────────────────────
    nominee = next(
        (m for m in committee_data if m.get('role_name') == 'Dean PGS Nominee'), None
    )

    if nominee:
        adv_name_raw = nominee.get('advisor_name', '')
        nom_name     = (
            adv_name_raw.split('||')[0].strip()
            if '||' in adv_name_raw else adv_name_raw
        )
        dept_str = nominee.get('department',     '') or ''
        spec_str = nominee.get('specialization', '') or ''

        nom_dept = f"Deptt of <b>{dept_str}</b>"
        if spec_str:
            nom_dept += f" (<b>{spec_str}</b>)"

        # Dynamic Nominee Text (With bold name and department)
        nominee_line = f"Dean,PGS Nominee <b>{nom_name}</b>, {nom_dept}"
        nom_para = Paragraph(nominee_line, styles['NomineeText'])
    else:
        nom_para = Paragraph("Dean,PGS Nominee", styles['NomineeText'])

    # Inner table for Dean PGS (right col): name / date / title stacked
    deanpgs_inner = Table(
        [
            [Paragraph(deanpgs_name,                styles['SigNameRight'])],
            [Paragraph(deanpgs_date_str,             styles['SigRoleRight'])],
            [Paragraph("Dean,Post-Graduate Studies.", styles['SigRoleRight'])],
        ],
        colWidths=[200],
    )
    deanpgs_inner.setStyle(TableStyle([
        ('VALIGN',       (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING',  (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING',(0, 0), (-1, -1), 1),
        ('TOPPADDING',   (0, 0), (-1, -1), 1),
    ]))

    # Outer 2-column table: nominee text LEFT | Dean PGS block RIGHT
    nominee_table = Table(
        [[nom_para, deanpgs_inner]],
        colWidths=[350, 200],
    )
    nominee_table.setStyle(TableStyle([
        ('VALIGN',       (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING',  (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING',(0, 0), (-1, -1), 0),
        ('TOPPADDING',   (0, 0), (-1, -1), 0),
    ]))
    elements.append(nominee_table)

    # ── Build PDF ─────────────────────────────────────────────────────────────
    doc.build(elements)
    buffer.seek(0)
    return buffer