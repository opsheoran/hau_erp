from app import app
from app.models.hrms import SARModel

def test_api():
    with app.test_request_context():
        # Let's find a valid SAR ID first
        from app.db import DB
        res = DB.fetch_one("SELECT TOP 1 pk_sarid FROM SAR_Employee_Mst")
        if not res:
            print("No SAR records found in DB to test.")
            return
        
        sar_id = res['pk_sarid']
        print(f"Testing API for SAR ID: {sar_id}")
        
        with app.test_client() as client:
            # We need a session because of the permission_required decorator?
            # Actually, api_sar_details doesn't have @permission_required
            response = client.get(f'/establishment/api/sar/details/{sar_id}')
            print(f"Status Code: {response.status_code}")
            print(f"Content Type: {response.content_type}")
            # print(f"Response Body: {response.data.decode()[:500]}...")

if __name__ == "__main__":
    test_api()
