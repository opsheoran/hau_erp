@establishment_bp.route('/employee_first_appointment_details', methods=['GET', 'POST'])
@permission_required('Employee First Appointment Details')
def employee_first_appointment_details():
    user_id = session.get('user_id')
    loc_id = session.get('selected_loc')
    perm = NavModel.check_permission(user_id, loc_id, 'Employee First Appointment Details')
    
    emp_id = request.args.get('emp_id')
    edit_id = request.args.get('edit')
    
    ddos = EstablishmentModel.get_ddos()

    if request.method == 'POST':
        action = request.form.get('action', 'SAVE')
        target_emp_id = request.form.get('emp_id')
        
        if action == 'DELETE':
            FirstAppointmentModel.delete(request.form.get('edit_id'))
            flash("Record Deleted Successfully !", "success")
            return redirect(url_for('establishment.employee_first_appointment_details', emp_id=target_emp_id))

        # Build Data Object
        form_data = {
            'emp_id': target_emp_id,
            'title': request.form.get('title', '').strip(),
            'remarks': request.form.get('remarks', '').strip(),
            'joining_date': request.form.get('joining_date'),
            'order_no': request.form.get('order_no', '').strip(),
            'appointment_date': request.form.get('appointment_date'),
            'ddo': request.form.get('appointment_ddo', '').strip(),
            'designation': request.form.get('appointment_designation', '').strip(),
            'department': request.form.get('appointment_department', '').strip(),
            'basic': request.form.get('basic') or 0,
            'pay_scale': request.form.get('pay_scale', '').strip(),
            'probation_date': request.form.get('probation_date'),
            'due_date_pp': request.form.get('due_date_pp'),
            'joining_time': request.form.get('joining_time'),
            'sr_no': request.form.get('sr_no', '').strip()
        }

        # Date conversion for SQL
        from datetime import datetime
        for key in ['joining_date', 'appointment_date', 'probation_date', 'due_date_pp']:
            if form_data[key]:
                try:
                    form_data[key] = datetime.strptime(form_data[key], '%d/%m/%Y').strftime('%Y-%m-%d')
                except:
                    form_data[key] = None

        try:
            current_app_id = None
            existing = DB.fetch_one("SELECT pk_appointmentid FROM SAL_FirstAppointment_Details WHERE fk_empid = ?", [target_emp_id])
            
            if existing:
                current_app_id = FirstAppointmentModel.update(existing['pk_appointmentid'], form_data, user_id)
                flash('Record Updated Successfully !', 'success')
            else:
                current_app_id = FirstAppointmentModel.save(form_data, user_id)
                flash('Record Saved Successfully !', 'success')
            
            # Save Terms and Conditions Grid
            terms = request.form.getlist('prob_term[]')
            fulfills = request.form.getlist('prob_fulfill[]')
            FirstAppointmentModel.save_probation_terms(current_app_id, terms, fulfills)

            return redirect(url_for('establishment.employee_first_appointment_details', emp_id=target_emp_id))
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')

    # GET Logic
    employee_info = None
    appointments = []
    edit_data = None
    terms = []

    if emp_id:
        employee_info = DB.fetch_one("""
            SELECT E.*, D.description as dept_name, DS.designation, DD.Description as ddo_name
            FROM SAL_Employee_Mst E
            LEFT JOIN Department_Mst D ON E.fk_deptid = D.pk_deptid
            LEFT JOIN SAL_Designation_Mst DS ON E.fk_desgid = DS.pk_desgid
            LEFT JOIN DDO_Mst DD ON E.fk_ddoid = DD.pk_ddoid
            WHERE E.pk_empid = ?
        """, [emp_id])
        
        # 1. Check SAL_FirstAppointment_Details (Transaction)
        edit_data = FirstAppointmentModel.get_appointment_by_id(edit_id) if edit_id else None
        if not edit_data:
            # Try to find any record for this employee
            existing = DB.fetch_one("SELECT pk_appointmentid FROM SAL_FirstAppointment_Details WHERE fk_empid = ?", [emp_id])
            if existing:
                edit_data = FirstAppointmentModel.get_appointment_by_id(existing['pk_appointmentid'])

        # 2. If still no data, fallback to earliest transaction in promotion history
        if not edit_data:
            hist = DB.fetch_one("""
                SELECT TOP 1 
                    OrdeNo as OrderNo, 
                    CONVERT(varchar, DateofJoinning, 103) as joining_date_fmt,
                    CONVERT(varchar, DateofAppointment, 103) as appointment_date_fmt,
                    NewBasic as BasicPay, NewPayScale as PayScale,
                    NewDDO as DDO, NewDesignation as Designation, NewDepartment as Department,
                    JoiningTime, SrNo, CONVERT(varchar, DueDatePP, 103) as due_date_pp_fmt
                FROM sal_emp_promotion_increment_payrevision_detail 
                WHERE fk_empid = ? 
                ORDER BY DateofJoinning ASC
            """, [emp_id])
            
            if hist:
                edit_data = hist
            else:
                # 3. Final Master fallback
                other = DB.fetch_one("""
                    SELECT OrderNo, CONVERT(varchar, dateofjoining, 103) as joining_date_fmt,
                           CONVERT(varchar, dateofappointment, 103) as appointment_date_fmt,
                           AppointmentTime
                    FROM SAL_EmployeeOther_Details WHERE fk_empid = ?
                """, [emp_id])
                edit_data = {
                    'joining_date_fmt': other['joining_date_fmt'] if other else None,
                    'OrderNo': other['OrderNo'] if other else None,
                    'appointment_date_fmt': other['appointment_date_fmt'] if other else None,
                    'DDO': employee_info['ddo_name'],
                    'Designation': employee_info['designation'],
                    'Department': employee_info['dept_name'],
                    'BasicPay': employee_info['curbasic'],
                    'JoiningTime': 'Fore Noon' if other and other['AppointmentTime'] == 'F' else 'After Noon'
                }

        if edit_data and edit_data.get('pk_appointmentid'):
            terms = FirstAppointmentModel.get_probation_terms(edit_data['pk_appointmentid'])
        
        appointments = FirstAppointmentModel.get_employee_appointments(emp_id)

    return render_template('establishment/employee_first_appointment_details.html', 
                          emp=employee_info, appointments=appointments, 
                          record=edit_data, terms=terms, ddos=ddos, perm=perm)
