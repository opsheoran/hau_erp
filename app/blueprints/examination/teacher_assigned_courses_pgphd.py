from flask import render_template, request, redirect, url_for, flash, session, jsonify
from app.blueprints.examination import examination_bp, permission_required
from app.models.examination import ExaminationModel
from app.models import AcademicsModel, InfrastructureModel
from app.db import DB

@examination_bp.route('/teacher_assigned_courses_pgphd', methods=['GET', 'POST'])
@permission_required('Teacher Assigned Courses for Student Marks Entry(PG/PHD)')
def teacher_assigned_courses_pgphd():
    filters = {
        'session_id': request.args.get('session_id', ''),
        'semester_id': request.args.get('semester_id', '0')
    }

    lookups = {
        'sessions': InfrastructureModel.get_sessions()
    }

    return render_template('examination/teacher_assigned_courses_pgphd.html',
                         lookups=lookups,
                         filters=filters)

@examination_bp.route('/api/get_assigned_courses_pgphd')
def get_assigned_courses_pgphd():
    session_id = request.args.get('session_id')
    semester_type = request.args.get('semester_id')
    
    if not session_id or not semester_type or semester_type == '0':
        return jsonify({'error': 'Missing parameters'})
        
    try:
        semester_mod = 1 if str(semester_type) == '1' else 0
    except ValueError:
        return jsonify({'error': 'Invalid semester type'})
    
    user_id = session.get('user_id')
    
    courses = DB.fetch_all("""
        SELECT DISTINCT c.pk_courseid as course_id, 
               c.coursecode + ' || ' + c.coursename + '(' + CAST(ISNULL(c.crhr_theory,0) as varchar) + '+' + CAST(ISNULL(c.crhr_practical,0) as varchar) + ')' as coursecode,
               col.collegename, col.pk_collegeid as college_id, 
               d.degreename, d.pk_degreeid as degree_id, 
               class.semester_roman as semester_name, class.pk_semesterid as class_id,
               dy.degreeyear_char as year_char, dy.pk_degreeyearid as year_id, 
               a.fk_exconfigid as exam_config_id, a.fk_sessionid as session_id,
               'R' as regular_back
        FROM SMS_TCourseAlloc_Dtl ad
        JOIN SMS_TCourseAlloc_Mst a ON a.pk_tcourseallocid = ad.fk_tcourseallocid
        JOIN SMS_Course_Mst c ON c.pk_courseid = ad.fk_courseid
        JOIN SMS_Degree_Mst d ON d.pk_degreeid = a.fk_degreeid
        JOIN SMS_Semester_Mst class ON class.pk_semesterid = a.fk_semesterid
        LEFT JOIN SMS_DegreeYear_Mst dy ON dy.pk_degreeyearid = class.fk_degreeyearid
        LEFT JOIN SMS_College_Mst col ON col.pk_collegeid = a.fk_collegeid
        WHERE a.fk_sessionid = ? 
          AND class.semesterorder % 2 = ?
          AND a.fk_employeeid = (SELECT top 1 fk_empId FROM UM_Users_Mst WHERE pk_userId = ?)
    """, [session_id, semester_mod, user_id])
    
    return jsonify({'courses': courses})