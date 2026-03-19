from flask import render_template, request, redirect, url_for, flash, session, jsonify
from app.blueprints.examination import examination_bp, permission_required
from app.models.examination import ExaminationModel
from app.models import AcademicsModel, InfrastructureModel
from app.db import DB

@examination_bp.route('/update_weightage_post_marks_entry', methods=['GET', 'POST'])
@permission_required('Update Weightage Post Marks Entry')
def update_weightage_post_marks_entry():
    if request.method == 'POST':
        action = request.form.get('action', '').strip().upper()
        
        if action == 'SAVE':
            dgexammapid = request.form.get('dgexammapid')
            course_id = request.form.get('course_id')
            new_max = request.form.get('txtMaxMarks')
            user_id = session.get('user_id')
            
            try:
                if ExaminationModel.update_weightage_post_marks(dgexammapid, course_id, new_max, user_id):
                    flash('Max marks updated successfully for existing entries!', 'success')
            except Exception as e:
                flash(f"Error updating: {str(e)}", 'danger')
                
        return redirect(url_for('examination.update_weightage_post_marks_entry'))
    
    lookups = {
        'degrees': AcademicsModel.get_all_degrees(),
        'sessions': InfrastructureModel.get_sessions()
    }

    return render_template('examination/update_weightage_post_marks_entry.html', lookups=lookups)

@examination_bp.route('/api/get_post_marks_lookups')
def get_post_marks_lookups():
    degree_id = request.args.get('degree_id')
    session_id = request.args.get('session_id')
    
    if not degree_id or not session_id:
        return jsonify({'courses': [], 'configs': [], 'exams': []})

    # 1. Courses for this degree (via SMS_Course_Mst_Dtl)
    courses = DB.fetch_all("""
        SELECT DISTINCT C.pk_courseid as id, C.coursecode + ' || ' + C.coursename as name
        FROM SMS_Course_Mst C
        INNER JOIN SMS_Course_Mst_Dtl D ON C.pk_courseid = D.fk_courseid
        WHERE D.fk_degreeid = ?
        ORDER BY name
    """, [degree_id])

    # 2. Configs formatted string
    configs = ExaminationModel.get_formatted_exam_configs(degree_id, session_id)

    # 3. Exams for this degree/session mapping
    exams = DB.fetch_all("""
        SELECT E.pk_examid as id, E.exam as name
        FROM SMS_Exam_Mst E
        INNER JOIN SMS_DgExam_Mst M ON E.pk_examid = M.fk_examid
        WHERE M.fk_degreeid = ? AND M.fk_acasessionid_from = ?
    """, [degree_id, session_id])

    return jsonify({
        'courses': courses,
        'configs': configs,
        'exams': exams
    })

@examination_bp.route('/api/get_students_for_weightage_update')
def get_students_for_weightage_update():
    degree_id = request.args.get('degree_id')
    exam_id = request.args.get('exam_id')
    session_id = request.args.get('session_id')
    course_id = request.args.get('course_id')
    config_id = request.args.get('config_id')
    
    # 1. Find the map ID
    dgmap = DB.fetch_one("""
        SELECT pk_dgexammapid FROM SMS_DgExam_Mst 
        WHERE fk_degreeid=? AND fk_examid=? AND fk_acasessionid_from=?
    """, [degree_id, exam_id, session_id])
    
    if not dgmap:
        return jsonify({'error': 'No mapped exam found for this combination.'})
        
    map_id = dgmap['pk_dgexammapid']
    
    # 2. Find students and their marks for this map_id, course_id, and optionally config_id
    where_clause = "WHERE D.fk_dgexammapid = ? AND A.fk_courseid = ?"
    params = [map_id, course_id]
    
    if config_id:
        where_clause += " AND A.fk_exconfigid = ?"
        params.append(config_id)

    query = f"""
        SELECT S.enrollmentno, S.fullname, D.marks_obt, D.maxmarks
        FROM SMS_StuExamMarks_Dtl D
        INNER JOIN SMS_StuCourseAllocation A ON D.fk_stucourseallocid = A.Pk_stucourseallocid
        INNER JOIN SMS_Student_Mst S ON A.fk_sturegid = S.pk_sid
        {where_clause}
        ORDER BY S.enrollmentno
    """
    students = DB.fetch_all(query, params)
    
    # Also fetch the current max marks from weightage to display in text box
    wei = DB.fetch_one("""
        SELECT W.maxmarks_th, W.maxmarks_pr, E.istheory, E.ispractical
        FROM SMS_DgExamWei_WithCourse W
        INNER JOIN SMS_DgExam_Mst M ON W.fk_dgexammapid = M.pk_dgexammapid
        INNER JOIN SMS_Exam_Mst E ON M.fk_examid = E.pk_examid
        WHERE W.fk_dgexammapid = ? AND W.fk_courseid = ?
    """, [map_id, course_id])
    
    current_max = ''
    if wei:
        if wei['ispractical'] and not wei['istheory']:
            current_max = wei['maxmarks_pr']
        else:
            current_max = wei['maxmarks_th']
            
    # Fallback to student record max marks if weightage not cleanly resolved
    if not current_max and students:
        current_max = students[0]['maxmarks']
    
    return jsonify({
        'dgexammapid': map_id,
        'current_max': current_max,
        'students': students
    })
