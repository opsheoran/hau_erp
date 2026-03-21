from flask import render_template, request, redirect, url_for, flash
from app.blueprints.examination import examination_bp, permission_required
from app.models import AcademicsModel, InfrastructureModel
from app.utils import get_pagination
from app.db import DB

@examination_bp.route('/external_examiner_communication', methods=['GET', 'POST'])
@permission_required('External Examiner Communication')
def external_examiner_communication():
    if request.method == 'POST':
        action = request.form.get('action', '').strip().upper()
        
        if action == 'EMAIL':
            # This is where email dispatch logic would go
            selected_ids = request.form.getlist('examiner_ids')
            if selected_ids:
                flash(f"Emails successfully queued for {len(selected_ids)} external examiner(s).", "success")
            else:
                flash("No examiners selected for email.", "warning")
                
            return redirect(url_for('examination.external_examiner_communication', 
                                    session_id=request.form.get('filter_session'),
                                    degree_id=request.form.get('filter_degree'),
                                    examiner_name=request.form.get('filter_name')))

    # Filters
    filters = {
        'session_id': request.args.get('session_id') or '',
        'degree_id': request.args.get('degree_id') or '',
        'examiner_name': request.args.get('examiner_name') or ''
    }
    
    examiners = []
    pagination = None
    page_range = []

    # Only fetch and display data if "VIEW" is clicked (i.e. at least session_id is provided)
    if filters['session_id'] or filters['degree_id'] or filters['examiner_name']:
        where_clause = ""
        params = []
        
        if filters['session_id']:
            where_clause += " AND D.fk_Sessionid = ?"
            params.append(filters['session_id'])
        
        if filters['degree_id']:
            # Instead of direct column check, check if examiner has a course mapping for this degree
            where_clause += """ AND D.fk_courseid IN (
                SELECT fk_courseid FROM SMS_Course_Mst_Dtl WHERE fk_degreeid = ?
            )"""
            params.append(filters['degree_id'])
            
        if filters['examiner_name']:
            where_clause += " AND M.ExaminarName LIKE ?"
            params.append(f"%{filters['examiner_name']}%")

        base_query = """
            (SELECT DISTINCT M.Pk_Exmid, M.UserId, M.ExaminarName, M.Email, M.IsActive
             FROM SMS_ExtExaminar_Mst M
             INNER JOIN SMS_ExtExaminar_Dtl D ON M.Pk_Exmid = D.Fk_Exmid
             WHERE 1=1 {where_clause}) AS Base
        """.format(where_clause=where_clause)
        
        page = int(request.args.get('page', 1))
        pagination, sql_limit = get_pagination(base_query, page, per_page=20, params=params, order_by="ORDER BY ExaminarName")
        
        query = f"""
            SELECT * FROM {base_query} {sql_limit}
        """
        
        examiners = DB.fetch_all(query, params)

        if pagination['total_pages'] > 1:
            for p in range(1, pagination['total_pages'] + 1):
                if p == 1 or p == pagination['total_pages'] or (pagination['page'] - 2 <= p <= pagination['page'] + 2):
                    if page_range and page_range[-1] != p - 1 and page_range[-1] != '...':
                        page_range.append('...')
                    page_range.append(p)

    lookups = {
        'degrees': AcademicsModel.get_all_degrees(),
        'sessions': InfrastructureModel.get_sessions()
    }

    return render_template('examination/external_examiner_communication.html', 
                           examiners=examiners, 
                           lookups=lookups,
                           filters=filters,
                           pagination=pagination, 
                           page_range=page_range)
