from app import create_app
from app.models import User, db

app = create_app()

def test_registration_rules():
    # Clean up any leftover test accounts
    with app.app_context():
        test_emails = [
            'rohan.verma@campus.edu',
            'kavya@campus.edu',
            'aditya.ks@campus.edu',
            'valid1@campus.edu',
            'valid2@campus.edu',
            'valid3@campus.edu',
            'valid4@campus.edu',
            'valid5@campus.edu',
            'valid6@campus.edu'
        ]
        for em in test_emails:
            u = User.query.filter_by(email=em).first()
            if u:
                db.session.delete(u)
        db.session.commit()

    with app.test_client() as client:
        # 1. Test GET /register
        res = client.get('/register')
        assert res.status_code == 200, "GET /register should return 200"
        assert b"Back to Previous Screen" in res.data, "In-page back button missing"
        assert b"globalBackButton" in res.data, "Global back button missing"
        assert b"validationPopupModal" in res.data, "Validation popup modal missing"
        assert b"1 to 3 words" in res.data, "Word count badge missing"
        print("[PASS] GET /register renders with Back buttons and Validation elements")

        # 2. Test 4 words name rejection
        res = client.post('/register', data={
            'name': 'First Second Third Fourth',
            'student_id': 'TEST-101',
            'email': 'valid1@campus.edu',
            'phone': '9876543210',
            'department': 'Computer Science',
            'password': 'Password@123'
        }, follow_redirects=True)
        assert b"Full Name must contain 1, 2, or 3 words only" in res.data
        print("[PASS] Rejected name with 4 words")

        # 3. Test name with digits rejection
        res = client.post('/register', data={
            'name': 'Ananya123 Sen',
            'student_id': 'TEST-102',
            'email': 'valid2@campus.edu',
            'phone': '9876543210',
            'department': 'Computer Science',
            'password': 'Password@123'
        }, follow_redirects=True)
        assert b"Full Name can only contain letters" in res.data
        print("[PASS] Rejected name containing digits")

        # 4. Test invalid email rejection
        res = client.post('/register', data={
            'name': 'Ananya Sen',
            'student_id': 'TEST-103',
            'email': 'invalid-email-without-domain',
            'phone': '9876543210',
            'department': 'Computer Science',
            'password': 'Password@123'
        }, follow_redirects=True)
        assert b"Please enter a valid campus email address" in res.data
        print("[PASS] Rejected invalid email address")

        # 5. Test invalid phone rejection (< 10 digits)
        res = client.post('/register', data={
            'name': 'Ananya Sen',
            'student_id': 'TEST-104',
            'email': 'valid4@campus.edu',
            'phone': '98765',
            'department': 'Computer Science',
            'password': 'Password@123'
        }, follow_redirects=True)
        assert b"Contact phone must be a valid 10-digit mobile number" in res.data
        print("[PASS] Rejected phone with fewer than 10 digits")

        # 6. Test password without uppercase letter
        res = client.post('/register', data={
            'name': 'Ananya Sen',
            'student_id': 'TEST-105',
            'email': 'valid5@campus.edu',
            'phone': '9876543210',
            'department': 'Computer Science',
            'password': 'password@123'
        }, follow_redirects=True)
        assert b"Password must contain at least one uppercase letter" in res.data
        print("[PASS] Rejected password without uppercase letter")

        # 7. Test password without special character
        res = client.post('/register', data={
            'name': 'Ananya Sen',
            'student_id': 'TEST-106',
            'email': 'valid6@campus.edu',
            'phone': '9876543210',
            'department': 'Computer Science',
            'password': 'Password123'
        }, follow_redirects=True)
        assert b"Password must contain at least one special character" in res.data
        print("[PASS] Rejected password without special character")

        # 8. Test successful registration with 2-word name, valid email, 10-digit phone, uppercase + special char password
        res = client.post('/register', data={
            'name': 'Rohan Verma',
            'student_id': 'STU-2026-999',
            'email': 'rohan.verma@campus.edu',
            'phone': '9812345678',
            'department': 'Computer Science',
            'password': 'StrongPass#2026'
        }, follow_redirects=True)
        assert b"Registration successful" in res.data, "Registration should succeed"
        print("[PASS] Successfully registered valid student account!")

        # Log out before next registration test
        client.get('/logout', follow_redirects=True)

        # 9. Test 1-word name valid registration
        res2 = client.post('/register', data={
            'name': 'Kavya',
            'student_id': 'STU-2026-998',
            'email': 'kavya@campus.edu',
            'phone': '+91 9812345679',
            'department': 'Biotechnology',
            'password': 'KavyaSecure*99'
        }, follow_redirects=True)
        assert b"Registration successful" in res2.data
        print("[PASS] Successfully registered student with 1-word name!")

        # Log out before next registration test
        client.get('/logout', follow_redirects=True)

        # 10. Test 3-word name valid registration
        res3 = client.post('/register', data={
            'name': 'Aditya Kumar Singh',
            'student_id': 'STU-2026-997',
            'email': 'aditya.ks@campus.edu',
            'phone': '9812345670',
            'department': 'Mechanical Eng',
            'password': 'Aditya#Mech2026'
        }, follow_redirects=True)
        assert b"Registration successful" in res3.data
        print("[PASS] Successfully registered student with 3-word name!")

        # 11. Verify Universal Back Button on public, student, and admin pages
        for path in ['/', '/devices', '/login', '/ai-assistant']:
            resp = client.get(path, follow_redirects=True)
            assert b"globalBackButton" in resp.data, f"Global back button missing on {path}"
            assert b"goBack()" in resp.data, f"goBack() missing on {path}"
        print("[PASS] Universal Back button present and operational across all pages!")

if __name__ == '__main__':
    test_registration_rules()
    print("\nALL 11 VALIDATION & BACK BUTTON INTEGRATION TESTS PASSED 100%!")
