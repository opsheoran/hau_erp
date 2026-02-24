from app.db import DB
import math

class EstablishmentModel:
    MASTER_TABLES = {
        'department': {'title': 'Department', 'table': 'Department_Mst', 'pk': 'pk_deptid', 'name': 'description'},
        'designation': {'title': 'Designation', 'table': 'SAL_Designation_Mst', 'pk': 'pk_desgid', 'name': 'designation'},
        'district': {'title': 'District', 'table': 'distric_mst', 'pk': 'pk_districid', 'name': 'districname'},
        'location': {'title': 'Location', 'table': 'Location_Mst', 'pk': 'pk_locid', 'name': 'locname'},
        'ddo': {'title': 'DDO', 'table': 'DDO_Mst', 'pk': 'pk_ddoid', 'name': 'Description'},
        'section': {'title': 'Section', 'table': 'SAL_Section_Mst', 'pk': 'pk_sectionid', 'name': 'description'},
        'grade': {'title': 'Grade', 'table': 'SAL_Grade_Mst', 'pk': 'pk_gradeid', 'name': 'gradename'},
        'class': {'title': 'Class', 'table': 'SAL_Class_Mst', 'pk': 'pk_classid', 'name': 'classname'},
        'religion': {'title': 'Religion', 'table': 'Religion_Mst', 'pk': 'pk_religionid', 'name': 'religiontype'},
        'controlling_office': {'title': 'Controlling Office', 'table': 'Sal_ControllingOffice_Mst', 'pk': 'pk_Controllid', 'name': 'description'},
        'office_type': {'title': 'Office Type', 'table': 'OfficeTypeMaster', 'pk': 'pk_officeTypeId', 'name': 'officeTypeDesc'},
        'city_category': {'title': 'City Category', 'table': 'SAL_CityCategory_Mst', 'pk': 'pk_ccid', 'name': 'citycategory'},
        'city': {'title': 'City', 'table': 'SAL_City_Mst', 'pk': 'pk_cityid', 'name': 'cityname'},
        'salutation': {'title': 'Salutation', 'table': 'SAL_Salutation_Mst', 'pk': 'PK_Salutation_ID', 'name': 'Salutation_Name'},
        'relation': {'title': 'Relation', 'table': 'Relation_MST', 'pk': 'Pk_Relid', 'name': 'Relation_name'},
        'category': {'title': 'Category', 'table': 'SAL_Category_Mst', 'pk': 'pk_catid', 'name': 'category'},
        'gad_nongad': {'title': 'Gad-Nongad', 'table': 'SAL_GadNongad_Mst', 'pk': 'pk_gadid', 'name': 'gadnongad'},
        'discipline': {'title': 'Discipline', 'table': 'SAL_Discipline_Mst', 'pk': 'pk_disid', 'name': 'discipline'}
    }

    @staticmethod
    def get_record(key, rid):
        cfg = EstablishmentModel.MASTER_TABLES.get(key)
        if not cfg: return None
        return DB.fetch_one(f"SELECT * FROM {cfg['table']} WHERE {cfg['pk']} = ?", [rid])

    @staticmethod
    def save_record(key, data):
        cfg = EstablishmentModel.MASTER_TABLES.get(key)
        if not cfg: return False
        pk, table, name = cfg['pk'], cfg['table'], cfg['name']
        val = data.get(name) or data.get('name')
        edit_id = data.get('pk_id') or data.get(pk)
        
        if edit_id and EstablishmentModel.get_record(key, edit_id):
            return DB.execute(f"UPDATE {table} SET {name} = ? WHERE {pk} = ?", [val, edit_id])
        else:
            return DB.execute(f"INSERT INTO {table} ({name}) VALUES (?)", [val])

    @staticmethod
    def delete_record(key, rid):
        cfg = EstablishmentModel.MASTER_TABLES.get(key)
        if not cfg: return False
        return DB.execute(f"DELETE FROM {cfg['table']} WHERE {cfg['pk']} = ?", [rid])