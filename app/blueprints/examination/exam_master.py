from flask import render_template, request, redirect, url_for, flash
from app.blueprints.examination import examination_bp, permission_required
from app.models.examination import ExaminationModel
from app.utils import get_pagination

@examination_bp.route('/exam_master', methods=['GET', 'POST'])
@permission_required('Exam Master')
def exam_master():
    if request.method == 'POST':
        action = request.form.get('action', '').strip().upper()
        
        if action == 'DELETE':
            pk_id = request.form.get('id')
            try:
                if ExaminationModel.delete_exam(pk_id):
                    flash('Exam deleted successfully!', 'success')
                else:
                    flash('Error deleting exam.', 'danger')
            except Exception as e:
                flash(f"Constraint error. Cannot delete: {str(e)}", "danger")
        else:
            # Handle SAVE
            try:
                if ExaminationModel.save_exam(request.form):
                    flash('Exam saved successfully!', 'success')
                else:
                    flash('Error saving exam.', 'danger')
            except Exception as e:
                flash(f"Error saving exam: {str(e)}", 'danger')
                
        return redirect(url_for('examination.exam_master'))
    
    # Get all records for grid (with pagination style)
    page = int(request.args.get('page', 1))
    pagination, sql_limit = get_pagination("SMS_Exam_Mst", page, per_page=20, order_by="ORDER BY examorder")
    
    from app.db import DB
    exams = DB.fetch_all(f"SELECT * FROM SMS_Exam_Mst {sql_limit}")
    
    # Custom pagination range logic matches other modules
    page_range = []
    if pagination['total_pages'] > 1:
        for p in range(1, pagination['total_pages'] + 1):
            if p == 1 or p == pagination['total_pages'] or (pagination['page'] - 2 <= p <= pagination['page'] + 2):
                if page_range and page_range[-1] != p - 1 and page_range[-1] != '...':
                    page_range.append('...')
                page_range.append(p)

    return render_template('examination/exam_master.html', exams=exams, pagination=pagination, page_range=page_range)
