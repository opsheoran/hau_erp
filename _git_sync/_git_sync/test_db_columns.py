from app.db import DB

emp_id = 'ES-271'
query = """
    SELECT pk_discid as id, ActionTypes as actiontype, discaction as description,
           CONVERT(varchar, dated, 103) as action_date_fmt,
           OrderNo as authority, remarks
    FROM EST_Disciplinary_Action_Details
    WHERE fk_empid = ? AND (IsDeleted IS NULL OR IsDeleted = 0)
    ORDER BY dated DESC
"""
try:
    res = DB.fetch_all(query, [emp_id])
    print("SUCCESS:", res)
except Exception as e:
    print("ERROR:", str(e))
