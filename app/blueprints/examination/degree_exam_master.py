from flask import render_template, request, redirect, url_for, flash
from app.blueprints.examination import examination_bp, permission_required
from app.models.examination import ExaminationModel
from app.models import AcademicsModel, InfrastructureModel
from app.utils import get_pagination

@examination_bp.route('/degree_exam_master', methods=['GET', 'POST'])
@permission_required('Degree Exam Master')
def degree_exam_master():
    if request.method == 'POST':
        action = request.form.get('action', '').strip().upper()
        
        if action == 'DELETE':
            pk_id = request.form.get('id')
            try:
                if ExaminationModel.delete_degree_exam(pk_id):
                    flash('Degree Exam map deleted successfully!', 'success')
                else:
                    flash('Error deleting mapping.', 'danger')
            except Exception as e:
                flash(f"Constraint error. Cannot delete: {str(e)}", "danger")
        else:
            # Handle SAVE
            try:
                if ExaminationModel.save_degree_exam(request.form):
                    flash('Degree Exam map saved successfully!', 'success')
                else:
                    flash('Error saving map.', 'danger')
            except Exception as e:
                flash(f"{str(e)}", 'danger')
                
        return redirect(url_for('examination.degree_exam_master', filter_degree=request.form.get('filter_degree')))
    
    # Grid Filter
    filter_degree = request.args.get('filter_degree')
    
    # Construct paginated query directly here because get_pagination handles strings
    where_clause = ""
    params = []
    if filter_degree and filter_degree != '0':
        where_clause = "WHERE M.fk_degreeid = ?"
        params.append(filter_degree)

    base_query = """
        SMS_DgExam_Mst M
        INNER JOIN SMS_Degree_Mst D ON M.fk_degreeid = D.pk_degreeid
        INNER JOIN SMS_Exam_Mst E ON M.fk_examid = E.pk_examid
        INNER JOIN SMS_AcademicSession_Mst S1 ON M.fk_acasessionid_from = S1.pk_sessionid
        LEFT JOIN SMS_AcademicSession_Mst S2 ON M.fk_acasessionid_to = S2.pk_sessionid
    """
    
    page = int(request.args.get('page', 1))
    pagination, sql_limit = get_pagination(base_query, page, per_page=20, where=where_clause, params=params, order_by="ORDER BY D.degreename, S1.sessionstart_dt DESC")
    
    from app.db import DB
    query = f"""
        SELECT M.*, D.degreename, E.exam, S1.sessionname as session_from_name, S2.sessionname as session_to_name
        FROM {base_query}
        {where_clause}
        {sql_limit}
    """
    mappings = DB.fetch_all(query, params)
    
    page_range = []
    if pagination['total_pages'] > 1:
        for p in range(1, pagination['total_pages'] + 1):
            if p == 1 or p == pagination['total_pages'] or (pagination['page'] - 2 <= p <= pagination['page'] + 2):
                if page_range and page_range[-1] != p - 1 and page_range[-1] != '...':
                    page_range.append('...')
                page_range.append(p)

    lookups = {
        'degrees': AcademicsModel.get_all_degrees(),
        'sessions': InfrastructureModel.get_sessions(),
        'exams': ExaminationModel.get_exams()
    }

    return render_template('examination/degree_exam_master.html', 
                           mappings=mappings, 
                           lookups=lookups,
                           filter_degree=filter_degree,
                           pagination=pagination, 
                           page_range=page_range)
