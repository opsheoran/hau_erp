from flask import render_template, request, redirect, url_for, flash, jsonify
from app.blueprints.examination import examination_bp, permission_required
from app.models.examination import ExaminationModel
from app.models import AcademicsModel, InfrastructureModel
from app.utils import get_pagination
from app.db import DB

@examination_bp.route('/degree_exam_wise_weightage', methods=['GET', 'POST'])
@permission_required('Degree Exam Wise Weightage')
def degree_exam_wise_weightage():
    if request.method == 'POST':
        action = request.form.get('action', '').strip().upper()
        
        if action == 'DELETE':
            pk_id = request.form.get('id')
            try:
                if ExaminationModel.delete_weightage(pk_id):
                    flash('Weightage deleted successfully!', 'success')
                else:
                    flash('Error deleting weightage.', 'danger')
            except Exception as e:
                flash(f"Constraint error. Cannot delete: {str(e)}", "danger")
        else:
            try:
                if ExaminationModel.save_weightage(request.form):
                    flash('Weightage saved successfully!', 'success')
                else:
                    flash('Error saving weightage.', 'danger')
            except Exception as e:
                flash(f"{str(e)}", 'danger')
                
        return redirect(url_for('examination.degree_exam_wise_weightage', 
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
        where_clause += " AND M.fk_degreeid = ?"
        params.append(filters['degree_id'])
    if filters['session_id'] and filters['session_id'] != '0':
        where_clause += " AND (W.fk_sessionid_from = ? OR W.fk_sessionid_upto = ?)"
        params.extend([filters['session_id'], filters['session_id']])

    base_query = """
        SMS_DgExamWeightage W
        INNER JOIN SMS_DgExam_Mst M ON W.fk_dgexammapid = M.pk_dgexammapid
        INNER JOIN SMS_Degree_Mst D ON M.fk_degreeid = D.pk_degreeid
        INNER JOIN SMS_Exam_Mst E ON M.fk_examid = E.pk_examid
        INNER JOIN SMS_AcademicSession_Mst S1 ON W.fk_sessionid_from = S1.pk_sessionid
        LEFT JOIN SMS_AcademicSession_Mst S2 ON W.fk_sessionid_upto = S2.pk_sessionid
        WHERE 1=1
    """ + where_clause
    
    page = int(request.args.get('page', 1))
    pagination, sql_limit = get_pagination(base_query, page, per_page=20, params=params, order_by="ORDER BY D.degreename, S1.sessionstart_dt DESC")
    
    query = f"""
        SELECT W.*, M.fk_degreeid, M.fk_examid, D.degreename, E.exam, E.istheory, E.ispractical,
               S1.sessionname as session_from_name, S2.sessionname as session_to_name
        FROM {base_query.replace('WHERE 1=1 AND', 'WHERE')}
        {sql_limit}
    """
    if 'WHERE 1=1' in query and not where_clause:
        pass
    elif 'WHERE 1=1 AND' in query:
        query = query.replace('WHERE 1=1 AND', 'WHERE')

    weightages = DB.fetch_all(query, params)
    
    # Attach details
    for w in weightages:
        w['details'] = ExaminationModel.get_weightage_detail(w['pk_dgexamweid'])

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

    return render_template('examination/degree_exam_wise_weightage.html', 
                           weightages=weightages, 
                           lookups=lookups,
                           filters=filters,
                           pagination=pagination, 
                           page_range=page_range)

@examination_bp.route('/api/get_courses_for_exam_weightage')
def get_courses_for_exam_weightage():
    degree_id = request.args.get('degree_id')
    exam_id = request.args.get('exam_id')
    session_id = request.args.get('session_id')
    
    # Find mapping
    dgmap = DB.fetch_one("""
        SELECT pk_dgexammapid FROM SMS_DgExam_Mst 
        WHERE fk_degreeid=? AND fk_examid=? AND fk_acasessionid_from=?
    """, [degree_id, exam_id, session_id])
    
    if not dgmap:
        return jsonify({'error': 'No Degree-Exam mapping found for this combination.', 'courses': []})
        
    # Get all courses for this degree via SMS_Course_Mst_Dtl
    query = """
        SELECT M.fk_courseid, C.coursename, C.coursecode, M.fk_semesterid, S.semester_roman,
               Y.degreeyear_char as year_name, C.crhr_theory, C.crhr_practical
        FROM SMS_Course_Mst_Dtl M
        INNER JOIN SMS_Course_Mst C ON M.fk_courseid = C.pk_courseid
        INNER JOIN SMS_Semester_Mst S ON M.fk_semesterid = S.pk_semesterid
        LEFT JOIN SMS_DegreeYear_Mst Y ON S.fk_degreeyearid = Y.pk_degreeyearid
        WHERE M.fk_degreeid = ?
        ORDER BY S.semesterorder, C.coursecode
    """
    courses = DB.fetch_all(query, [degree_id])
    return jsonify({'dgmapid': dgmap['pk_dgexammapid'], 'courses': courses})
