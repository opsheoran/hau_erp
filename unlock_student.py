from app.db import DB

print('Checking CardEntrySubmit status for student 9791 (MOHIT)...')
student = DB.fetch_one('SELECT CardEntrySubmit, fullname FROM SMS_Student_Mst WHERE pk_sid = 9791')
print('Before update:', student)

# Unlock the card entry
DB.execute('UPDATE SMS_Student_Mst SET CardEntrySubmit = 0 WHERE pk_sid = 9791')

# Also unlock the individual allocations so they can be un-ticked/changed if needed
curr_session = DB.fetch_one('SELECT fk_curr_session FROM SMS_Student_Mst WHERE pk_sid = 9791')['fk_curr_session']
DB.execute('UPDATE SMS_StuCourseAllocation SET isstudentApproved = 0, stuapprovedDate = NULL WHERE fk_sturegid = 9791 AND fk_dgacasessionid = ?', [curr_session])

student_after = DB.fetch_one('SELECT CardEntrySubmit FROM SMS_Student_Mst WHERE pk_sid = 9791')
print('After update: CardEntrySubmit =', student_after['CardEntrySubmit'])
print('Successfully unlocked Card Entry for student 2024A61M!')
