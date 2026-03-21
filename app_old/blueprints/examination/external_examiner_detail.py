from flask import render_template, request, redirect, url_for, flash, jsonify
from app.blueprints.examination import examination_bp, permission_required
from app.models.examination import ExaminationModel
from app.models import AcademicsModel, InfrastructureModel
from app.utils import get_pagination

@examination_bp.route('/external_examiner_detail', methods=['GET', 'POST'])
@permission_required('External Examiner Detail')
def external_examiner_detail():
    if request.method == 'POST':
        action = request.form.get('action', '').strip().upper()
        
        if action == 'DELETE':
            pk_id = request.form.get('id')
            try:
                if ExaminationModel.delete_external_examiner(pk_id):
                    flash('Examiner deleted successfully!', 'success')
                else:
                    flash('Error deleting examiner.', 'danger')
            except Exception as e:
                flash(f"Constraint error. Cannot delete: {str(e)}", "danger")
                
        elif action == 'SAVE_COURSE':
            try:
                if ExaminationModel.save_examiner_course(request.form):
                    flash('Course mapped to examiner successfully!', 'success')
                else:
                    flash('Error mapping course.', 'danger')
            except Exception as e:
                flash(f"{str(e)}", 'danger')
                
        elif action == 'DELETE_COURSE':
            dtl_id = request.form.get('dtl_id')
            try:
                if ExaminationModel.delete_examiner_course(dtl_id):
                    flash('Mapped course deleted successfully!', 'success')
                else:
                    flash('Error deleting mapped course.', 'danger')
            except Exception as e:
                flash(f"Constraint error. Cannot delete mapped course: {str(e)}", "danger")
                
        else:
            try:
                # Save Examiner
                ExaminationModel.save_external_examiner(request.form)
                flash('Examiner profile saved successfully!', 'success')
            except Exception as e:
                flash(f"{str(e)}", 'danger')
                
        return redirect(url_for('examination.external_examiner_detail'))
    
    # Pagination and Filtering
    filters = {
        'search_name': request.args.get('search_name', ''),
        'search_contact': request.args.get('search_contact', '')
    }
    
    where_clause = ""
    params = []
    if filters['search_name']:
        where_clause += " AND ExaminarName LIKE ?"
        params.append(f"%{filters['search_name']}%")
    if filters['search_contact']:
        where_clause += " AND ContactNumber LIKE ?"
        params.append(f"%{filters['search_contact']}%")
        
    page = int(request.args.get('page', 1))
    pagination, sql_limit = get_pagination("SMS_ExtExaminar_Mst", page, per_page=20, where=f"WHERE 1=1 {where_clause}", params=params, order_by="ORDER BY InsertDate DESC")
    
    from app.db import DB
    query = f"SELECT * FROM SMS_ExtExaminar_Mst WHERE 1=1 {where_clause} {sql_limit}"
    examiners = DB.fetch_all(query, params)
    
    # Add mapped courses to each examiner for the UI
    for ex in examiners:
        ex['courses'] = ExaminationModel.get_examiner_courses(ex['Pk_Exmid'])

    page_range = []
    if pagination['total_pages'] > 1:
        for p in range(1, pagination['total_pages'] + 1):
            if p == 1 or p == pagination['total_pages'] or (pagination['page'] - 2 <= p <= pagination['page'] + 2):
                if page_range and page_range[-1] != p - 1 and page_range[-1] != '...':
                    page_range.append('...')
                page_range.append(p)

    courses = DB.fetch_all("SELECT pk_courseid, coursecode, coursename FROM SMS_Course_Mst ORDER BY coursecode")

    lookups = {
        'degrees': AcademicsModel.get_all_degrees(),
        'sessions': InfrastructureModel.get_sessions(),
        'courses': courses
    }

    return render_template('examination/external_examiner_detail.html', 
                           examiners=examiners, 
                           lookups=lookups,
                           filters=filters,
                           pagination=pagination, 
                           page_range=page_range)
