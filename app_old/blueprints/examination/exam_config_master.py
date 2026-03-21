from flask import render_template, request, redirect, url_for, flash, session, jsonify
from app.blueprints.examination import examination_bp, permission_required
from app.models.examination import ExaminationModel
from app.models import AcademicsModel, InfrastructureModel
from app.utils import get_pagination

@examination_bp.route('/exam_config_master', methods=['GET', 'POST'])
@permission_required('Exam Config Master')
def exam_config_master():
    if request.method == 'POST':
        action = request.form.get('action', '').strip().upper()
        
        if action == 'DELETE':
            pk_id = request.form.get('id')
            try:
                if ExaminationModel.delete_exam_config(pk_id):
                    flash('Exam config deleted successfully!', 'success')
                else:
                    flash('Error deleting config.', 'danger')
            except Exception as e:
                flash(f"Constraint error. Cannot delete: {str(e)}", "danger")
        else:
            try:
                user_id = session.get('user_id')
                if ExaminationModel.save_exam_config(request.form, user_id):
                    flash('Exam config saved successfully!', 'success')
                else:
                    flash('Error saving config.', 'danger')
            except Exception as e:
                flash(f"{str(e)}", 'danger')
                
        return redirect(url_for('examination.exam_config_master', 
                                filter_degree=request.form.get('filter_degree'),
                                filter_session=request.form.get('filter_session')))
    
    # Grid Filter
    filters = {
        'degree_id': request.args.get('filter_degree'),
        'session_id': request.args.get('filter_session')
    }
    
    # Construct paginated query
    where_clause = ""
    params = []
    if filters['degree_id'] and filters['degree_id'] != '0':
        where_clause += " AND C.fk_degreeid = ?"
        params.append(filters['degree_id'])
    if filters['session_id'] and filters['session_id'] != '0':
        where_clause += " AND C.fk_sessionid = ?"
        params.append(filters['session_id'])

    base_query = """
        SMS_ExamConfig_Mst C
        INNER JOIN SMS_AcademicSession_Mst S ON C.fk_sessionid = S.pk_sessionid
        INNER JOIN SMS_Degree_Mst D ON C.fk_degreeid = D.pk_degreeid
        LEFT JOIN Month_Mst M1 ON C.fk_monthid_from = M1.pk_MonthId
        LEFT JOIN Month_Mst M2 ON C.fk_monthid_to = M2.pk_MonthId
        LEFT JOIN Year_Mst Y1 ON C.fk_yearid_From = Y1.pk_yearID
        LEFT JOIN Year_Mst Y2 ON C.fk_yearid_To = Y2.pk_yearID
        WHERE 1=1
    """ + where_clause
    
    page = int(request.args.get('page', 1))
    pagination, sql_limit = get_pagination(base_query, page, per_page=20, params=params, order_by="ORDER BY S.sessionstart_dt DESC, D.degreename")
    
    from app.db import DB
    query = f"""
        SELECT C.*, S.sessionname, D.degreename, 
               M1.descriptiion as month_from_name, M2.descriptiion as month_to_name,
               Y1.description as year_from_name, Y2.description as year_to_name
        FROM {base_query.replace('WHERE 1=1 AND', 'WHERE')}
        {sql_limit}
    """
    if 'WHERE 1=1' in query and not where_clause:
        pass # keeping 1=1
    elif 'WHERE 1=1 AND' in query:
        query = query.replace('WHERE 1=1 AND', 'WHERE')

    configs = DB.fetch_all(query, params)
    
    # Attach details
    for c in configs:
        c['details'] = ExaminationModel.get_exam_config_dtl(c['pk_exconfigid'])

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
        'months': InfrastructureModel.get_months(),
        'years': InfrastructureModel.get_years()
    }

    return render_template('examination/exam_config_master.html', 
                           configs=configs, 
                           lookups=lookups,
                           filters=filters,
                           pagination=pagination, 
                           page_range=page_range)

@examination_bp.route('/api/get_semesters_for_degree/<int:degree_id>')
def get_semesters_for_degree(degree_id):
    from app.db import DB
    # Fetch number of semesters from degree duration
    deg = DB.fetch_one("SELECT maxsem FROM SMS_Degree_Mst WHERE pk_degreeid = ?", [degree_id])
    if not deg or not deg['maxsem']:
        return jsonify([])
    
    sem_count = int(deg['maxsem'])
    sems = DB.fetch_all("SELECT pk_semesterid as id, semester_roman as name, semesterorder FROM SMS_Semester_Mst WHERE semesterorder <= ? ORDER BY semesterorder", [sem_count])
    return jsonify(sems)
