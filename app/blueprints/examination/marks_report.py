import io
import datetime
from flask import make_response
from reportlab.lib.pagesizes import A4, portrait, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

def generate_internal_marks_report_pdf(course_info, students, exam_columns, is_submitted, is_pg_phd=False):
    buffer = io.BytesPath() if hasattr(io, 'BytesPath') else io.BytesIO()

    degree_name = course_info.get('degree_name', '')
    # Determine if this is a PG/PHD degree to swap "Head of Department" with "Dean PGS" 
    if not is_pg_phd:
        is_pg_phd = any(x in degree_name for x in ['M.Sc', 'Ph.D', 'M.Tech', 'MBA', 'PG Diploma'])

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(name='TitleStyle', parent=styles['Heading1'], alignment=1, fontSize=16, fontName='Helvetica-Bold')
    subtitle_style = ParagraphStyle(name='SubTitleStyle', parent=styles['Normal'], alignment=1, fontSize=12, fontName='Helvetica-Bold')
    normal_bold = ParagraphStyle(name='NormalBold', parent=styles['Normal'], alignment=1, fontSize=10, fontName='Helvetica-Bold')
    right_align = ParagraphStyle(name='RightAlign', parent=styles['Normal'], alignment=2, fontSize=10)

    now = datetime.datetime.now().strftime("%d/%m/%Y\n%I:%M:%S %p")
    status_str = "Submitted" if is_submitted else "Not Submitted"

    class MarksReportCanvas(canvas.Canvas):
        def __init__(self, *args, **kwargs):
            canvas.Canvas.__init__(self, *args, **kwargs)
            self._saved_page_states = []

        def showPage(self):
            self._saved_page_states.append(dict(self.__dict__))
            self._startPage()

        def save(self):
            """Render the cached page states and add dynamic page numbers and footers/headers."""
            num_pages = len(self._saved_page_states)
            for state in self._saved_page_states:
                self.__dict__.update(state)
                self.draw_header_footer(num_pages)
                canvas.Canvas.showPage(self)
            canvas.Canvas.save(self)

        def draw_header_footer(self, page_count):
            self.saveState()

            # Draw Header Tables directly on Canvas so they repeat perfectly on every page
            if is_pg_phd:
                t1 = Table([
                    ["", Paragraph("Dean Post Graduate Studies", title_style), Paragraph(now, right_align)],
                    ["", Paragraph("CCS Haryana Agricultural University,Hisar", subtitle_style), ""],
                    ["", Paragraph(f"Final Examination : {course_info.get('session_name', '')} Semester : {course_info.get('semester_name', '')}", normal_bold), ""],
                ], colWidths=[1.5*inch, 4*inch, 1.5*inch])
            else:
                t1 = Table([
                    ["", Paragraph("Controller of Examination", title_style), Paragraph(now, right_align)],
                    ["", Paragraph("CCS Haryana Agricultural University, Hisar", subtitle_style), ""],
                    ["", Paragraph(f"Final Examination : {course_info.get('session_name', '')} Semester : {course_info.get('semester_name', '')}", normal_bold), ""],
                ], colWidths=[1.5*inch, 4*inch, 1.5*inch])

            t1.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('ALIGN', (2,0), (2,0), 'RIGHT')]))
            w, h = t1.wrap(A4[0]-60, 200)
            t1.drawOn(self, 30, A4[1] - 30 - h)
            current_y = A4[1] - 30 - h - 10

            t2 = Table([
                [Paragraph("Internal Awards", ParagraphStyle(name='IA', parent=title_style, fontSize=14)), Paragraph(status_str, right_align)]
            ], colWidths=[5.5*inch, 1.5*inch])
            w2, h2 = t2.wrap(A4[0]-60, 50)
            t2.drawOn(self, 30, current_y - h2)
            current_y = current_y - h2 - 10

            crhr = f"{course_info.get('crhr_theory', 0)}+{course_info.get('crhr_practical', 0)}"
            meta_data = [
                ["Name of the Deptt.", course_info.get('dept_name', 'Dean Office'), "Name of Instructor(s)", course_info.get('instructor_name', '')],
                ["Course No.", f"{course_info.get('course_code', '')}( {crhr} )", "Course Title", course_info.get('course_name', '')],
                ["Degree", course_info.get('degree_name', ''), "Semester", course_info.get('semester_name', '')],
                ["Exam", course_info.get('session_name', ''), "Max. Marks", str(course_info.get('total_max_marks', ''))]
            ]
            meta_table = Table(meta_data, colWidths=[1.3*inch, 2.5*inch, 1.5*inch, 2.1*inch])
            meta_table.setStyle(TableStyle([
                ('GRID', (0,0), (-1,-1), 1, colors.black),
                ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
                ('FONTNAME', (2,0), (2,-1), 'Helvetica-Bold'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('BOTTOMPADDING', (0,0), (-1,-1), 3),
                ('TOPPADDING', (0,0), (-1,-1), 3),
                ('FONTSIZE', (0,0), (-1,-1), 9),
            ]))
            w3, h3 = meta_table.wrap(A4[0]-60, 100)
            meta_table.drawOn(self, 30, current_y - h3)

            # Footers repeated on every page at the bottom
            self.setFont('Helvetica-Bold', 10)
            if is_pg_phd:
                self.drawString(30, 50, "Signature of Instructor")
                self.drawCentredString(A4[0]/2.0, 50, "Head of Department")
                self.drawRightString(A4[0]-30, 50, "Dean Post Graduate Studies")        
            else:
                self.drawString(30, 50, "Controller of Examination")
                self.drawCentredString(A4[0]/2.0, 50, "Head of Department")
                self.drawRightString(A4[0]-30, 50, "Signature of Instructor")

            self.setFont('Helvetica', 10)
            if not is_pg_phd:
                self.drawCentredString(A4[0]/2.0, 35, "Online Approved Yes/No")
            self.drawRightString(A4[0]-30, 35, f"Page {self._pageNumber} of {page_count}")

            self.restoreState()

    # The topMargin needs to account for the custom drawn header (approx 200 points).
    doc = SimpleDocTemplate(buffer, pagesize=portrait(A4), rightMargin=30, leftMargin=30, topMargin=210, bottomMargin=80)
    elements = []

    # Marks Table Header
    if is_pg_phd:
        marks_header = ["S.No.", "Admn.No.", "Name Of Student"]
    else:
        marks_header = ["S.No.", "Roll No.", "Admn.No.", "Name Of Student"]

    for col in exam_columns:
        # Split on the first space to create "Internal\nTheory(40)"
        name_parts = col['name'].split(' ', 1)
        if len(name_parts) == 2:
            formatted_name = f"{name_parts[0]}\n{name_parts[1]}\n({col['max_val']})"
        else:
            formatted_name = f"{col['name']}\n({col['max_val']})"
        marks_header.append(formatted_name)
    marks_header.append("Total")

    marks_data = [marks_header]

    for idx, student in enumerate(students):
        admission_no = student.get('originalRollNo', '')
        if not admission_no:
            admission_no = student.get('AdmissionNo', '')
        if not admission_no:
            admission_no = student.get('roll_no', '') # Fallback to roll_no if mapped differently
        if admission_no is None:
            admission_no = ''
        enrollment_no = student.get('enrollmentno', '')
        if enrollment_no is None:
            enrollment_no = ''

        if is_pg_phd:
            row = [str(idx + 1), str(enrollment_no), str(student.get('fullname', ''))]
        else:
            row = [str(idx + 1), str(admission_no), str(enrollment_no), str(student.get('fullname', ''))]

        total = 0
        for col in exam_columns:
            mark_data = student['marks'].get(str(col['id']), {})
            if mark_data.get('absent'):
                row.append("Absent")
            else:
                val = mark_data.get('val', '')
                if val is not None and val != '':
                    try:
                        v = float(val)
                        if v.is_integer():
                            v = int(v)
                        total += v
                        row.append(str(v))
                    except:
                        row.append(str(val))
                else:
                    row.append("")
        row.append(str(total) if total > 0 else "")
        marks_data.append(row)

    # Determine column widths dynamically based on number of exams
    num_exams = len(exam_columns)
    # Shrink Roll No. and Admn.No. widths slightly to free up space
    if is_pg_phd:
        base_widths = [0.4*inch, 1.2*inch, 2.0*inch]
    else:
        base_widths = [0.4*inch, 0.75*inch, 1.1*inch, 1.6*inch]

    rem_space = 7.4 * inch - sum(base_widths) # total width ~7.4 inches
    exam_col_width = (rem_space - 0.5*inch) / num_exams if num_exams > 0 else 0     
    col_widths = base_widths + [exam_col_width] * num_exams + [0.5*inch]

    marks_table = Table(marks_data, colWidths=col_widths, repeatRows=1)
    if is_pg_phd:
        marks_table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTNAME', (1,1), (1,-1), 'Helvetica-Bold'), # Admn no bold
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('ALIGN', (2,1), (2,-1), 'LEFT'), # Student Name left align
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 1),
            ('TOPPADDING', (0,0), (-1,-1), 1),
            ('LEFTPADDING', (0,0), (-1,-1), 2),
            ('RIGHTPADDING', (0,0), (-1,-1), 2),
            ('FONTSIZE', (0,0), (-1,-1), 9),
        ]))
    else:
        marks_table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTNAME', (1,1), (1,-1), 'Helvetica-Bold'), # Roll no bold
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('ALIGN', (3,1), (3,-1), 'LEFT'), # Student Name left align
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 1),
            ('TOPPADDING', (0,0), (-1,-1), 1),
            ('LEFTPADDING', (0,0), (-1,-1), 2),
            ('RIGHTPADDING', (0,0), (-1,-1), 2),
            ('FONTSIZE', (0,0), (-1,-1), 9),
        ]))

    elements.append(marks_table)

    # Use the custom canvasmaker to ensure headers and footers repeat accurately        
    doc.build(elements, canvasmaker=MarksReportCanvas)

    pdf = buffer.getvalue()
    buffer.close()

    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=Internal_Marks_Report.pdf'
    return response