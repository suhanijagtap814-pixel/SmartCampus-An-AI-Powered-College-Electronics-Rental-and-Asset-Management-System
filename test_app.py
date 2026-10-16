from app import create_app
from app.models import User, Device, Booking, Rental

app = create_app()

def test_endpoints():
    with app.test_client() as client:
        # 1. Test public catalog
        res = client.get('/devices')
        assert res.status_code == 200, f"Failed /devices: {res.status_code}"
        print("[OK] /devices: 200 OK")

        # 2. Test AI Assistant page
        res = client.get('/ai-assistant')
        assert res.status_code == 200, f"Failed /ai-assistant: {res.status_code}"
        print("[OK] /ai-assistant: 200 OK")

        # 3. Test AI Recommender query
        res = client.get('/ai-assistant?query=laptop+for+python+and+machine+learning')
        assert res.status_code == 200, f"Failed AI Recommender query: {res.status_code}"
        assert b"Match" in res.data, "Match score not found in recommender output"
        print("[OK] /ai-assistant with ML query: 200 OK (Found Match score)")

        # 4. Test AI Chatbot API
        res = client.post('/api/chat', json={'message': 'Which laptop is available tomorrow for \u20b9300?'})
        assert res.status_code == 200, f"Failed /api/chat: {res.status_code}"
        json_data = res.get_json()
        assert 'device_cards' in json_data, "device_cards not in response"
        print("[OK] /api/chat: 200 OK, returned", len(json_data['device_cards']), "device cards")

        # 5. Test QR Code scan API
        res = client.post('/api/scan-qr', json={'qr_code': 'CAMPUS_DEVICE:LAP-101:SN-DELL-95201'})
        assert res.status_code == 200, f"Failed /api/scan-qr: {res.status_code}"
        json_qr = res.get_json()
        assert json_qr.get('found') is True, "QR decode failed"
        print("[OK] /api/scan-qr: 200 OK, identified", json_qr['device']['name'])

        # 6. Test AI Demand Prediction API
        res = client.get('/api/predict-demand')
        assert res.status_code == 200, f"Failed /api/predict-demand: {res.status_code}"
        json_pred = res.get_json()
        assert len(json_pred.get('predictions', [])) > 0, "No predictions returned"
        print("[OK] /api/predict-demand: 200 OK, predicted", len(json_pred['predictions']), "categories")

        # 7. Test Student Login & Dashboard
        client.get('/quick-login/student', follow_redirects=True)
        res = client.get('/dashboard')
        assert res.status_code == 200, f"Failed /dashboard: {res.status_code}"
        print("[OK] Student /dashboard: 200 OK")

        res = client.get('/active-rentals')
        assert res.status_code == 200, f"Failed /active-rentals: {res.status_code}"
        print("[OK] Student /active-rentals: 200 OK")

        res = client.get('/my-bookings')
        assert res.status_code == 200, f"Failed /my-bookings: {res.status_code}"
        print("[OK] Student /my-bookings: 200 OK")

        # 8. Test Staff Login & Dashboard
        client.get('/quick-login/staff', follow_redirects=True)
        res = client.get('/staff/dashboard')
        assert res.status_code == 200, f"Failed /staff/dashboard: {res.status_code}"
        print("[OK] Staff /staff/dashboard: 200 OK")

        res = client.get('/staff/scanner')
        assert res.status_code == 200, f"Failed /staff/scanner: {res.status_code}"
        print("[OK] Staff /staff/scanner: 200 OK")

        res = client.get('/staff/inspection')
        assert res.status_code == 200, f"Failed /staff/inspection: {res.status_code}"
        print("[OK] Staff /staff/inspection: 200 OK")

        # 9. Test Admin Login & Dashboard
        client.get('/quick-login/admin', follow_redirects=True)
        res = client.get('/admin/dashboard')
        assert res.status_code == 200, f"Failed /admin/dashboard: {res.status_code}"
        print("[OK] Admin /admin/dashboard: 200 OK")

        res = client.get('/admin/approvals')
        assert res.status_code == 200, f"Failed /admin/approvals: {res.status_code}"
        print("[OK] Admin /admin/approvals: 200 OK")

        res = client.get('/admin/ai-predictions')
        assert res.status_code == 200, f"Failed /admin/ai-predictions: {res.status_code}"
        print("[OK] Admin /admin/ai-predictions: 200 OK")

        res = client.get('/admin/students')
        assert res.status_code == 200, f"Failed /admin/students: {res.status_code}"
        print("[OK] Admin /admin/students (Risk Radar): 200 OK")

        res = client.get('/admin/analytics')
        assert res.status_code == 200, f"Failed /admin/analytics: {res.status_code}"
        print("[OK] Admin /admin/analytics: 200 OK")

        print("\nAll 15 Core Integration Tests Passed Flawlessly!")

if __name__ == '__main__':
    test_endpoints()
