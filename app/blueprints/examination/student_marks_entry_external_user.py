from flask import render_template, request, redirect, url_for, flash, session, jsonify
from app.blueprints.examination import examination_bp, permission_required
from app.models.examination import ExaminationModel
from app.models import AcademicsModel, InfrastructureModel
from app.db import DB
from app.utils import get_pagination
import json

@examination_bp.route('/student_marks_entry_external_user', methods=['GET', 'POST'])
@permission_required('Student Marks Entry(ExternalUser)')
def student_marks_entry_external_user():
    if request.method == 'POST':
        action = request.form.get('action', '').strip().upper()
        
        if action in ['SAVE', 'SUBMIT']:
            try:
                alloc_ids_str = request.form.get('alloc_ids', '[]')
                alloc_ids = json.loads(alloc_ids_str)
                exam_map_ids_str = request.form.get('exam_map_ids', '[]')
                exam_map_ids = json.loads(exam_map_ids_str)
                
                is_submit = 1 if action == 'SUBMIT' else 0
                course_id = request.form.get('course_id')

                entries = []
                for aid in alloc_ids:
                    for map_id in exam_map_ids:
                        marks_key = f'marks_{aid}_{map_id}'
                        absent_key = f'absent_{aid}_{map_id}'
                        max_key = f'max_{aid}_{map_id}'
                        
                        raw_marks = request.form.get(marks_key, '')
                        is_absent = request.form.get(absent_key, '0') == '1'
                        
                        if is_absent:
                            marks_val = None
                        elif raw_marks.strip():
                            marks_val = float(raw_marks)
                            max_val = float(request.form.get(max_key, 100))
                            if marks_val > max_val:
                                flash(f"Marks {marks_val} exceed max marks {max_val}", "error")
                                return redirect(url_for('examination.student_marks_entry_external_user', **request.form))
                        else:
                            marks_val = None
                            
                        entries.append({
                            'fk_allocid': aid,
                            'fk_exammapid': map_id,
                            'marks': marks_val,
                            'isabsent': 1 if is_absent else 0
                        })

                success = ExaminationModel.save_external_marks(
                    entries=entries,
                    is_submitted=is_submit,
                    created_by=session.get('user_id'),
                    ip_address=request.remote_addr
                )
                
                if success:
                    flash(f"Marks {action.lower()}d successfully", "success")
                else:
                    flash(f"Failed to {action.lower()} marks", "error")
                    
            except Exception as e:
                flash(str(e), "error")
                
            return redirect(url_for('examination.student_marks_entry_external_user', 
                                    session_id=request.form.get('session_id'),
                                    course_id=request.form.get('course_id'),
                                    th_pr=request.form.get('th_pr')))

    filters = {
        'session_id': request.args.get('session_id', ''),
        'course_id': request.args.get('course_id', ''),
        'th_pr': request.args.get('th_pr', '')
    }

    # Fetch lookup data for External User page
    lookups = {
        'sessions': InfrastructureModel.get_sessions()
    }

    return render_template('examination/student_marks_entry_external_user.html',
                         lookups=lookups,
                         filters=filters)

@examination_bp.route('/api/get_courses_for_external_user')
def get_courses_for_external_user():
    session_id = request.args.get('session_id')
    if not session_id:
        return jsonify({'error': 'Missing session_id'})
    
    # Fetch courses in the session that have an external exam configuration
    courses = DB.fetch_all("""
        SELECT DISTINCT c.pk_courseid as id, c.coursename + ' (' + c.coursecode + ')' as name,
               c.crhr_theory, c.crhr_practical, ISNULL(c.isNC, 0) as is_nc
        FROM SMS_Course_Mst c
        WHERE ISNULL(c.isobsolete, 0) = 0
          AND EXISTS (
              SELECT 1 FROM SMS_StuCourseAllocation a
              WHERE a.fk_courseid = c.pk_courseid 
                AND a.fk_dgacasessionid = ?
          )
          AND EXISTS (
              SELECT 1 FROM SMS_DgExamWei_WithCourse w
              JOIN SMS_DgExam_Mst m ON w.fk_dgexammapid = m.pk_dgexammapid
              JOIN SMS_Exam_Mst config ON m.fk_examid = config.pk_examid
              WHERE w.fk_courseid = c.pk_courseid 
                AND m.fk_acasessionid_from = ?
                AND (config.exam LIKE '%External%' OR config.isinternal = 0)
          )
        ORDER BY name
    """, [session_id, session_id])
    
    return jsonify({'courses': courses})

@examination_bp.route('/api/get_students_for_external_user')
def get_students_for_external_user():
    session_id = request.args.get('session_id')
    course_id = request.args.get('course_id')
    
    if not session_id or not course_id:
        return jsonify({'error': 'Missing parameters'})
        
    # Get allocated students for this course first to find the degree context
    students = DB.fetch_all("""
        SELECT a.Pk_stucourseallocid, s.pk_sid as pk_studentid, s.fullname, s.enrollmentno, 
               NULL as roll_no, dc.fk_degreeid, dc.fk_semesterid
        FROM SMS_StuCourseAllocation a
        JOIN SMS_Student_Mst s ON a.fk_sturegid = s.pk_sid
        LEFT JOIN SMS_DegreeCycle_Mst dc ON a.fk_degreecycleid = dc.pk_degreecycleid
        WHERE a.fk_dgacasessionid = ? AND a.fk_courseid = ?
        ORDER BY s.enrollmentno
    """, [session_id, course_id])
    
    if not students:
        return jsonify({'columns': [], 'students': []})

    degree_id = students[0]['fk_degreeid']
    class_id = students[0]['fk_semesterid']
        
    # Get columns (active external exams restricted to this degree and session)
    exam_columns_raw = DB.fetch_all("""
        SELECT DISTINCT m.pk_dgexammapid as id, c.exam as name, w.maxmarks_th, w.maxmarks_pr, c.istheory, c.ispractical, c.examorder
        FROM SMS_DgExam_Mst m
        JOIN SMS_Exam_Mst c ON c.pk_examid = m.fk_examid
        JOIN SMS_DgExamWei_WithCourse w ON w.fk_dgexammapid = m.pk_dgexammapid
        WHERE (c.exam LIKE '%External%' OR c.isinternal = 0)
        AND w.fk_courseid = ? AND m.fk_acasessionid_from = ? AND m.fk_degreeid = ?
        ORDER BY c.examorder
    """, [course_id, session_id, degree_id])
    
    exam_columns = []
    for ex in exam_columns_raw:
        max_val = ex['maxmarks_th'] if ex['istheory'] else ex['maxmarks_pr']
        if float(max_val or 0) > 0:
            exam_columns.append({
                'id': ex['id'],
                'name': ex['name'],
                'max_val': max_val
            })
    
    exam_map_ids = [c['id'] for c in exam_columns]
    
    alloc_ids = [s['Pk_stucourseallocid'] for s in students]
    placeholders = ','.join(['?'] * len(alloc_ids))
    
    marks_query = f"""
        SELECT m.fk_stucourseallocid, m.fk_dgexammapid, m.marks_obt, m.isabsentt, m.isStudentMarksLocked
        FROM sms_stuexammarks_dtl m
        WHERE m.fk_stucourseallocid IN ({placeholders})
    """
    marks = DB.fetch_all(marks_query, alloc_ids)
    
    formatted_students = []
    degree_id = students[0]['fk_degreeid'] if students else None
    class_id = students[0]['fk_semesterid'] if students else None
    
    for s in students:
        s_data = {
            'alloc_id': s['Pk_stucourseallocid'],
            'student_id': s['pk_studentid'],
            'enrollmentno': s['enrollmentno'] if s['enrollmentno'] else '',
            'fullname': s['fullname'] if s['fullname'] else '',
            'roll_no': s['roll_no'] if s['roll_no'] else '',
            'marks': {},
            'is_locked': False
        }
        for m in marks:
            if m['fk_stucourseallocid'] == s['Pk_stucourseallocid']:
                s_data['marks'][str(m['fk_dgexammapid'])] = {
                    'val': m['marks_obt'],
                    'absent': m['isabsentt'] == 1
                }
                if m['isStudentMarksLocked'] == 1:
                    s_data['is_locked'] = True
        formatted_students.append(s_data)

    deg_row = DB.fetch_one("SELECT degreename FROM SMS_Degree_Mst WHERE pk_degreeid = ?", [degree_id]) if degree_id else None
    deg_name = deg_row['degreename'] if deg_row else 'N/A'
    sem_row = DB.fetch_one("SELECT semester_roman FROM SMS_Semester_Mst WHERE pk_semesterid = ?", [class_id]) if class_id else None
    sem_name = sem_row['semester_roman'] if sem_row else 'N/A'

    return jsonify({
        'columns': exam_columns,
        'students': formatted_students,
        'alloc_ids': alloc_ids,
        'exam_map_ids': exam_map_ids,
        'degree_name': deg_name,
        'semester_name': sem_name,
        'student_count': len(students)
    })
