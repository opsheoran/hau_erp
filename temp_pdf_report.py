import sys
import os
import datetime
from reportlab.lib.pagesizes import A4, landscape, portrait
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

def create_report(filename):
    doc = SimpleDocTemplate(filename, pagesize=portrait(A4), rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom Styles
    title_style = ParagraphStyle(name='TitleStyle', parent=styles['Heading1'], alignment=1, fontSize=16, fontName='Helvetica-Bold')
    subtitle_style = ParagraphStyle(name='SubTitleStyle', parent=styles['Normal'], alignment=1, fontSize=12, fontName='Helvetica-Bold')
    normal_bold = ParagraphStyle(name='NormalBold', parent=styles['Normal'], fontSize=10, fontName='Helvetica-Bold')
    normal_style = ParagraphStyle(name='NormalStyle', parent=styles['Normal'], fontSize=10, fontName='Helvetica')
    right_align = ParagraphStyle(name='RightAlign', parent=styles['Normal'], alignment=2, fontSize=10)
    
    # Header Date
    now = datetime.datetime.now().strftime("%d/%m/%Y\n%I:%M:%S %p")
    
    # Title
    t1 = Table([
        ["", Paragraph("Controller of Examination", title_style), Paragraph(now, right_align)],
        ["", Paragraph("CCS Haryana Agricultural University, Hisar", subtitle_style), ""],
        ["", Paragraph("Final Examination : 2025-2026 (December)Semester : I", normal_bold), ""],
    ], colWidths=[1.5*inch, 4*inch, 1.5*inch])
    t1.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ALIGN', (2,0), (2,0), 'RIGHT'),
    ]))
    elements.append(t1)
    elements.append(Spacer(1, 10))
    
    elements.append(Table([
        [Paragraph("Internal Awards", ParagraphStyle(name='IA', parent=title_style, fontSize=14)), Paragraph("Submitted", right_align)]
    ], colWidths=[5.5*inch, 1.5*inch]))
    
    elements.append(Spacer(1, 10))
    
    # Meta Table
    meta_data = [
        ["Name of the Deptt.", "Dean Office", "Name of Instructor(s)", "O.P. Sheoran"],
        ["Course No.", "STAT-M-101( 2+0 )", "Course Title", "Statistical Methods-I"],
        ["Degree", "B.Sc.(Hons.) Physical Science 4 Year", "Semester", "I"],
        ["Exam", "2025-2026", "Max. Marks", "100"]
    ]
    meta_table = Table(meta_data, colWidths=[1.3*inch, 2.5*inch, 1.5*inch, 1.7*inch])
    meta_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTNAME', (2,0), (2,-1), 'Helvetica-Bold'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(meta_table)
    elements.append(Spacer(1, 15))
    
    # Marks Table
    marks_data = [
        ["SNo.", "Roll No.", "Admn.No.", "Name Of Student", "Internal\nTheory(80)", "Internal\nPractical\n(0)", "Assignment\n(20)", "Total"],
        ["1", "BSP-101", "2025BSP01BIV", "Aman Siwach", "45", "0", "20", "65"],
        ["2", "BSP-108", "2025BSP08BIV", "Jatin", "22", "0", "7", "29"],
        ["3", "BSP-110", "2025BSP10BIV", "Mamta Devi", "44", "0", "20", "64"],
        ["4", "BSP-112", "2025BSP12BIV", "Neha", "44", "0", "20", "64"],
        ["5", "BSP-114", "2025BSP14BIV", "Nitesh Kumar", "52", "0", "10", "62"],
        ["6", "BSP-115", "2025BSP15BIV", "Pallvi", "43", "0", "20", "63"],
        ["7", "BSP-122", "2025BSP22BIV", "Vishakha", "53", "0", "20", "73"]
    ]
    
    # Adjust widths to fit A4
    marks_table = Table(marks_data, colWidths=[0.4*inch, 0.8*inch, 1.1*inch, 1.6*inch, 0.8*inch, 0.7*inch, 0.8*inch, 0.6*inch])
    marks_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTNAME', (1,1), (1,-1), 'Helvetica-Bold'), # Roll no bold
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('ALIGN', (3,1), (3,-1), 'LEFT'), # Student Name left align
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING', (0,0), (-1,-1), 5),
    ]))
    elements.append(marks_table)
    elements.append(Spacer(1, 40))
    
    # Footer Signatures
    footer_data = [
        [Paragraph("<b>Controller of Examination</b>", styles['Normal']),
         Paragraph("<b>Head of Department</b><br/><br/>Online Approved Yes/No", ParagraphStyle('c', alignment=1)),
         Paragraph("<b>Signature of Instructor</b><br/><br/>Page 1 of 1", ParagraphStyle('r', alignment=2))]
    ]
    footer_table = Table(footer_data, colWidths=[2.5*inch, 2.5*inch, 2*inch])
    elements.append(footer_table)
    
    doc.build(elements)

if __name__ == '__main__':
    create_report("test_report.pdf")
