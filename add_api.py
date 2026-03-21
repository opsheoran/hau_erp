from app.db import DB
from flask import jsonify

with open('app/blueprints/examination/marks_process_ug_mba.py', 'r', encoding='utf-8') as main_f:
    code = main_f.read()

new_api = """
@examination_bp.route('/api/get_college_ug_mba_degrees')
def get_college_ug_mba_degrees():
    college_id = request.args.get('college_id')
    if not college_id:
        return jsonify([])
    query = '''
        SELECT DISTINCT D.pk_degreeid as id, D.degreename as name
        FROM SMS_CollegeDegreeBranchMap_Mst M
        INNER JOIN SMS_Degree_Mst D ON M.fk_degreeid = D.pk_degreeid
        WHERE M.fk_collegeid = ? AND (D.fk_degreetypeid IN (1, 3, 5) OR D.degreename LIKE '%MBA%' OR D.degreename LIKE '%M.B.A%')
        ORDER BY D.degreename
    '''
    degrees = DB.fetch_all(query, [college_id])
    from app.utils import clean_json_data
    return jsonify(clean_json_data(degrees))
"""

if 'get_college_ug_mba_degrees' not in code:
    code += '\n' + new_api
    with open('app/blueprints/examination/marks_process_ug_mba.py', 'w', encoding='utf-8') as out_f:
        out_f.write(code)
    print('Updated API.')