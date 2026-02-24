from flask import Blueprint, render_template, request, redirect, url_for, session, flash, make_response
from app.models import NavModel, PayrollModel, EmployeePortalModel
from app.utils import number_to_words
from functools import wraps
import io
import os

# ReportLab core imports
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib import colors

payroll_bp = Blueprint('payroll', __name__)

def permission_required(page_caption):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('auth.login'))
            perms = NavModel.check_permission(session['user_id'], session.get('selected_loc'), page_caption)
            if not perms or not perms.get('AllowView'):
                return redirect(url_for('main.index'))
            request.page_perms = perms
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@payroll_bp.route('/salary_slip', methods=['GET', 'POST'])
def salary_slip_view():
    if 'user_id' not in session: return redirect(url_for('auth.login'))
    emp_id = session.get('emp_id')
    
    if request.method == 'POST':
        month = request.form.get('month')
        year = request.form.get('year')
        report_type = request.form.get('report_type', 'R')
        return redirect(url_for('payroll.download_salary_slip', month=month, year=year, type=report_type))

    months = [{'id': i, 'name': n} for i, n in enumerate(["", "JANUARY", "FEBRUARY", "MARCH", "APRIL", "MAY", "JUNE", "JULY", "AUGUST", "SEPTEMBER", "OCTOBER", "NOVEMBER", "DECEMBER"]) if i > 0]
    years = range(2026, 2014, -1)
    return render_template('payroll/salary_slip_view.html', months=months, years=years)

@payroll_bp.route('/salary_slip/download')
def download_salary_slip():
    if 'user_id' not in session: return redirect(url_for('auth.login'))
    emp_id = session.get('emp_id')
    
    try:
        month = int(request.args.get('month', 0))
        year = int(request.args.get('year', 0))
    except:
        month, year = 0, 0
        
    if not emp_id or not month or not year:
        flash("Invalid request parameters.", "danger")
        return redirect(url_for('payroll.salary_slip_view'))
        
    s = PayrollModel.get_salary_slip_data(emp_id, month, year)
    if not s:
        flash("Salary slip not found for the selected period.", "warning")
        return redirect(url_for('payroll.salary_slip_view'))

    master = s['master']
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # Configuration
    margin = 0.5 * inch
    usable_width = width - (2 * margin)
    curr_y = height - margin
    
    def draw_text(x, y, text, size=8, bold=False, align='left'):
        c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
        if align == 'left':
            c.drawString(x, y, str(text) if text is not None else "")
        elif align == 'right':
            c.drawRightString(x, y, str(text) if text is not None else "")
        elif align == 'center':
            c.drawCentredString(x, y, str(text) if text is not None else "")

    # 1. Outer Border
    c.setLineWidth(1)
    c.rect(margin, margin, usable_width, height - 2 * margin)

    # 2. Header Section
    logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'images', 'logo.png')
    if os.path.exists(logo_path):
        try: c.drawImage(logo_path, margin + 0.1*inch, curr_y - 45, width=40, height=40, mask='auto')
        except: pass
    
    draw_text(width/2, curr_y - 20, "CHAUDHARY CHARAN SINGH HARYANA AGRICULTURAL UNIVERSITY, HISAR", size=10, bold=True, align='center')
    draw_text(width/2, curr_y - 35, f"PAY SLIP FOR {master.get('month_name', '').upper()} - {year}", size=9, bold=True, align='center')
    
    curr_y -= 55
    c.line(margin, curr_y, width - margin, curr_y) 
    
    # Info Row 1: Department & Scheme
    curr_y -= 12
    draw_text(margin + 5, curr_y, f"DEPARTMENT : {master.get('department')}", size=8, bold=True)
    draw_text(margin + usable_width*0.45, curr_y, f"Scheme : {master.get('scheme_name') or '-'}", size=8, bold=True)
    
    curr_y -= 4
    c.setDash(1, 2)
    c.line(margin, curr_y, width - margin, curr_y)
    c.setDash()
    
    # Employee Info Grid (3 columns)
    curr_y -= 12
    c1, c2 = margin + 5, margin + 0.8*inch
    c3, c4 = margin + usable_width*0.40, margin + usable_width*0.55
    c5, c6 = margin + usable_width*0.75, margin + usable_width*0.85
    
    draw_text(c1, curr_y, "EMP NO :", bold=True); draw_text(c2, curr_y, master.get('empcode'))
    draw_text(c3, curr_y, "PAY BAND :", bold=True); draw_text(c4, curr_y, master.get('level_name') or '14')
    draw_text(c5, curr_y, "PAN NO :", bold=True); draw_text(c6, curr_y, master.get('panno') or '-')
    
    curr_y -= 12
    draw_text(c1, curr_y, "NAME :", bold=True); draw_text(c2, curr_y, master.get('empname'))
    draw_text(c3, curr_y, "Grade Pay :", bold=True); draw_text(c4, curr_y, f"{float(master.get('gradepay', 0)):.0f}")
    draw_text(c5, curr_y, "Bank Name :", bold=True); draw_text(c6, curr_y, master.get('bankname') or '-')
    
    curr_y -= 12
    draw_text(c1, curr_y, "PAID DAYS :", bold=True); draw_text(c2, curr_y, f"{float(master.get('ELDays', 31)):.2f}")
    draw_text(c3, curr_y, "PF Code :", bold=True); draw_text(c4, curr_y, master.get('gpf_nps_no') or '-')
    
    curr_y -= 12
    draw_text(c1, curr_y, "DESIG :", bold=True); draw_text(c2, curr_y, master.get('designation'))
    draw_text(c3, curr_y, "BANK A/C :", bold=True); draw_text(c4, curr_y, master.get('bankaccountno') or '-')
    
    curr_y -= 12
    draw_text(c1, curr_y, "DOB :", bold=True); draw_text(c2, curr_y, master.get('dob_fmt') or '-')
    
    curr_y -= 4
    c.line(margin, curr_y, width - margin, curr_y) 
    
    # 3. Main Data Grid (Earnings | Deductions | Loan Details)
    grid_top = curr_y
    curr_y -= 12
    draw_text(margin + usable_width*0.15, curr_y, "EARNINGS", bold=True, align='center')
    draw_text(margin + usable_width*0.48, curr_y, "DEDUCTIONS", bold=True, align='center')
    draw_text(margin + usable_width*0.82, curr_y, "Loan Details", bold=True, align='center')
    
    curr_y -= 4
    c.line(margin, curr_y, width - margin, curr_y) 
    
    # Sub-headers for Loan
    draw_text(margin + usable_width*0.66, curr_y - 10, "Loan", size=7, bold=True)
    draw_text(margin + usable_width*0.82, curr_y - 10, "Ins Amt", size=7, bold=True, align='right')
    
    # Helper to get value regardless of case
    def get_val(d, key, default=None):
        for k, v in d.items():
            if k.lower() == key.lower(): return v
        return default

    # Filter heads > 0
    earnings = []
    for e in s['earnings']:
        amt = float(get_val(e, 'paid_amount', 0))
        if amt > 0:
            desc = get_val(e, 'Description', '')
            if desc == 'GPF(Subscription)': desc = 'GPF(SUB)'
            earnings.append({'Description': desc, 'paid_amount': amt})

    deductions = []
    for d in s['deductions']:
        amt = float(get_val(d, 'paid_amount', 0))
        if amt > 0:
            desc = get_val(d, 'Description', '')
            if desc == 'GPF(Subscription)': desc = 'GPF(SUB)'
            deductions.append({'Description': desc, 'paid_amount': amt})

    loans = []
    for l in s['loans']:
        i_amt = float(get_val(l, 'InstalmentAmount', 0))
        b_amt = float(get_val(l, 'balAmount', 0))
        if i_amt > 0 or b_amt > 0:
            desc = get_val(l, 'Description', '')
            loans.append({'Description': desc, 'InstalmentAmount': i_amt, 'balAmount': b_amt})
    
    curr_y -= 20
    max_rows = max(len(earnings), len(deductions), len(loans))
    
    ec1, ec2 = margin + 5, margin + usable_width*0.30
    dc1, dc2 = margin + usable_width*0.34, margin + usable_width*0.64
    lc1, lc2, lc3 = margin + usable_width*0.66, margin + usable_width*0.82, margin + usable_width*0.98
    
    for i in range(max_rows):
        if i < len(earnings):
            draw_text(ec1, curr_y, earnings[i]['Description'])
            draw_text(ec2, curr_y, f"{earnings[i]['paid_amount']:,.2f}", align='right')
        
        if i < len(deductions):
            draw_text(dc1, curr_y, deductions[i]['Description'])
            draw_text(dc2, curr_y, f"{deductions[i]['paid_amount']:,.2f}", align='right')
            
        if i < len(loans):
            draw_text(lc1, curr_y, loans[i]['Description'], size=7)
            draw_text(lc2, curr_y, f"{loans[i]['InstalmentAmount']:,.2f}", size=7, align='right')
            draw_text(lc3, curr_y, f"{loans[i]['balAmount']:,.2f}", size=7, align='right')
            
        curr_y -= 12
        if curr_y < margin + 1.5*inch: break 

    grid_bottom = curr_y + 8
    # Vertical dividers
    c.line(margin + usable_width*0.32, grid_top, margin + usable_width*0.32, grid_bottom)
    c.line(margin + usable_width*0.65, grid_top, margin + usable_width*0.65, grid_bottom)
    
    c.line(margin, grid_bottom, width - margin, grid_bottom)
    
    # 4. Totals Row
    curr_y = grid_bottom - 12
    draw_text(margin + 5, curr_y, f"Total Earnings :", bold=True)
    draw_text(ec2, curr_y, f"{float(master.get('GrossTotal', 0)):,.2f}", bold=True, align='right')
    
    draw_text(dc1, curr_y, f"Total Deductions :", bold=True)
    draw_text(dc2, curr_y, f"{float(master.get('TotalDeductions', 0)):,.2f}", bold=True, align='right')
    
    curr_y -= 4
    c.line(margin, curr_y, width - margin, curr_y)
    
    # 5. Net Payable
    curr_y -= 15
    net_val = float(master.get('NetPay', 0))
    net_words = number_to_words(int(net_val))
    
    draw_text(margin + 5, curr_y, f"Net Payable (In words): Rs. {net_words}", size=8, bold=True)
    draw_text(margin + usable_width*0.75, curr_y, f"Net Payable :", size=8, bold=True)
    draw_text(width - margin - 5, curr_y, f"{net_val:,.2f}", size=8, bold=True, align='right')
    
    curr_y -= 10
    c.line(margin, curr_y, width - margin, curr_y)
    
    # 6. Footer
    curr_y -= 60
    draw_text(width - margin - 5, curr_y, "D.D.O/Officer Incharge", bold=True, align='right')
    
    c.showPage()
    c.save()
    
    pdf_out = buffer.getvalue()
    buffer.close()
    
    response = make_response(pdf_out)
    response.headers['Content-Type'] = 'application/pdf'
    filename = f"Salary_Slip_{master.get('month_name', 'Month')}_{year}.pdf"
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    return response
