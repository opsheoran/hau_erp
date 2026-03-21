from flask import render_template, request, redirect, url_for, flash, session, jsonify
from app.blueprints.examination import examination_bp, permission_required
from app.models.examination import ExaminationModel
from app.models import AcademicsModel, InfrastructureModel
from app.db import DB
from app.utils import get_pagination
import json

@examination_bp.route('/student_marks_entry_supplementary', methods=['GET', 'POST'])
@permission_required('Student Marks Entry(Supplementary)')
def student_marks_entry_supplementary():
    if request.method == 'POST':
        action = request.form.get('action', '').strip().upper()
        
        if action in ['SAVE', 'SUBMIT']:
            try:
                user_id = session.get('user_id')
                alloc_ids_str = request.form.get('alloc_ids')
                if alloc_ids_str:
                    alloc_ids = json.loads(alloc_ids_str)
                    exam_map_ids = json.loads(request.form.get('exam_map_ids'))
                    
                    is_submit = (action == 'SUBMIT')

                    for alloc_id in alloc_ids:
                        for emap_id in exam_map_ids:
                            mark_key = f"marks_{alloc_id}_{emap_id}"
                            absent_key = f"absent_{alloc_id}_{emap_id}"
                            max_key = f"max_{alloc_id}_{emap_id}"
                            
                            mark_val = request.form.get(mark_key)
                            is_absent = request.form.get(absent_key) == '1'
                            max_val = request.form.get(max_key)
                            
                            if is_absent:
                                mark_val = '0'
                                
                            if mark_val is not None and mark_val != '':
                                try:
                                    if float(mark_val) > float(max_val):
                                        flash(f"Marks cannot exceed {max_val} for allocation {alloc_id}.", "danger")
                                        continue
                                except ValueError:
                                    flash(f"Invalid marks format for allocation {alloc_id}.", "danger")
                                    continue
                                
                                existing = DB.fetch_one("""
                                    SELECT Pk_Stumarksdtlid FROM SMS_StuExamMarks_Dtl 
                                    WHERE fk_stucourseallocid = ? AND fk_dgexammapid = ?
                                """, [alloc_id, emap_id])
                                
                                if existing:
                                    DB.execute("""
                                        UPDATE SMS_StuExamMarks_Dtl 
                                        SET marks_obt = ?, maxmarks = ?, isabsentt = ?, 
                                            isStudentMarksLocked = ?, fk_userid = ?, feeddate = GETDATE()
                                        WHERE Pk_Stumarksdtlid = ?
                                    """, [mark_val, max_val, 1 if is_absent else 0, 1 if is_submit else 0, user_id, existing['Pk_Stumarksdtlid']])
                                else:
                                    DB.execute("""
                                        INSERT INTO SMS_StuExamMarks_Dtl
                                        (fk_stucourseallocid, fk_dgexammapid, marks_obt, maxmarks, isabsentt, isStudentMarksLocked, fk_userid, feeddate)
                                        VALUES (?, ?, ?, ?, ?, ?, ?, GETDATE())
                                    """, [alloc_id, emap_id, mark_val, max_val, 1 if is_absent else 0, 1 if is_submit else 0, user_id])
                    
                    flash(f'Marks {"submitted" if action == "SUBMIT" else "saved"} successfully.', 'success')
            except Exception as e:
                flash(f"Error saving marks: {str(e)}", 'danger')
                
        # Preserve filters on reload
        return redirect(url_for('examination.student_marks_entry_supplementary',
                                college_id=request.form.get('college_id'),
                                session_id=request.form.get('session_id'),
                                degree_id=request.form.get('degree_id'),
                                class_id=request.form.get('class_id'),
                                department_id=request.form.get('department_id'),
                                year_id=request.form.get('year_id'),
                                exam_config_id=request.form.get('exam_config_id'),
                                course_id=request.form.get('course_id')))

    # GET Request logic
    filters = {
        'college_id': request.args.get('college_id', ''),
        'session_id': request.args.get('session_id', ''),
        'degree_id': request.args.get('degree_id', ''),
        'class_id': request.args.get('class_id', ''),
        'department_id': request.args.get('department_id', ''),
        'year_id': request.args.get('year_id', ''),
        'exam_config_id': request.args.get('exam_config_id', ''),
        'course_id': request.args.get('course_id', '')
    }

    exam_configs = []
    if filters['degree_id'] and filters['session_id']:
        exam_configs = ExaminationModel.get_formatted_exam_configs(filters['degree_id'], filters['session_id'])

    lookups = {
        'colleges': AcademicsModel.get_colleges_simple(),
        'sessions': InfrastructureModel.get_sessions(),
        'degrees': AcademicsModel.get_all_degrees(),
        'classes': DB.fetch_all("SELECT pk_semesterid as id, semester_roman as name FROM SMS_Semester_Mst ORDER BY semesterorder"),
        'departments': AcademicsModel.get_departments(),
        'years': DB.fetch_all("SELECT pk_degreeyearid as id, degreeyear_char as name FROM SMS_DegreeYear_Mst ORDER BY dgyearorder"),
        'exam_configs': exam_configs
    }

    return render_template('examination/student_marks_entry_supplementary.html', 
                           lookups=lookups, filters=filters)


