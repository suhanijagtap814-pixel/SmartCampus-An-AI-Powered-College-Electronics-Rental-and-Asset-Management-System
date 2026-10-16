import os
from app import create_app
from app.models import db, User, Device

app = create_app()

def test_roles_and_images():
    with app.app_context():
        # 1. Verify Real Pictures on Disk and in DB
        upload_dev_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'devices')
        required_images = [
            'laptop_dell.jpg', 'laptop_macbook.jpg', 'laptop_thinkpad.jpg',
            'laptop_gaming.jpg', 'laptop_hp.jpg', 'laptop_acer.jpg',
            'tablet_ipad.jpg', 'tablet_galaxy.jpg', 'camera_sony.jpg',
            'camera_canon.jpg', 'projector_epson.jpg', 'projector_benq.jpg',
            'lab_oscilloscope.jpg', 'lab_raspberry.jpg', 'lab_arduino.jpg',
            'audio_bose.jpg', 'charger_usbc.jpg', 'default.jpg'
        ]
        for img_name in required_images:
            fpath = os.path.join(upload_dev_dir, img_name)
            assert os.path.exists(fpath), f"Missing real product image: {img_name}"
            # Check file size to ensure it is a real photo (not an empty or tiny file)
            size = os.path.getsize(fpath)
            assert size > 5000, f"Image {img_name} too small ({size} bytes), might not be a real photo"
        print(f"[PASS] All {len(required_images)} Real Product Photos verified on disk with proper file sizes!")

        # Verify DB devices have valid image URLs
        all_devices = Device.query.all()
        assert len(all_devices) >= 15, f"Expected at least 15 devices, found {len(all_devices)}"
        for dev in all_devices:
            assert dev.image_url and dev.image_url.startswith('/static/uploads/devices/'), f"Device {dev.device_code} has bad image: {dev.image_url}"
        print(f"[PASS] All {len(all_devices)} DB devices correctly point to real product image assets!")

        # Clean up test accounts
        test_emails = [
            'new_student@campus.edu',
            'new_staff@campus.edu',
            'new_admin@campus.edu',
            'test_fail_staff@campus.edu',
            'test_fail_admin@campus.edu'
        ]
        for em in test_emails:
            u = User.query.filter_by(email=em).first()
            if u: db.session.delete(u)
        db.session.commit()

    with app.test_client() as client:
        # 2. Test Login Role Switcher GET views
        res_stud = client.get('/login?role=student')
        assert res_stud.status_code == 200
        assert b"Student Rental Portal" in res_stud.data
        assert b"switchLoginRole" in res_stud.data

        res_staff = client.get('/login?role=staff')
        assert res_staff.status_code == 200
        assert b"Staff &amp; Lab Tech Portal" in res_staff.data or b"Staff" in res_staff.data

        res_admin = client.get('/login?role=admin')
        assert res_admin.status_code == 200
        assert b"Administrator &amp; Lab Director Portal" in res_admin.data or b"Admin" in res_admin.data
        print("[PASS] Login Role Switcher renders student, staff, and admin portals accurately")

        # 3. Test Cross-Role Login Protection
        # Try logging in as Admin with Student credentials (should be denied)
        res_denied = client.post('/login', data={
            'email': 'student@campus.edu',
            'password': 'student123',
            'role': 'admin'
        }, follow_redirects=True)
        assert b"Access Denied" in res_denied.data, "Should deny student logging into admin role"
        print("[PASS] Cross-role login protection prevented student from entering admin portal")

        # Login with correct Admin role & credentials
        res_admin_login = client.post('/login', data={
            'email': 'admin@campus.edu',
            'password': 'admin123',
            'role': 'admin'
        }, follow_redirects=True)
        assert res_admin_login.status_code == 200
        assert b"Admin Dashboard" in res_admin_login.data or b"Sunita Rao" in res_admin_login.data
        print("[PASS] Admin login succeeded and redirected to Admin Dashboard")

        client.get('/logout', follow_redirects=True)

        # Login with correct Staff role & credentials
        res_staff_login = client.post('/login', data={
            'email': 'staff@campus.edu',
            'password': 'staff123',
            'role': 'staff'
        }, follow_redirects=True)
        assert res_staff_login.status_code == 200
        assert b"Staff" in res_staff_login.data or b"Desk" in res_staff_login.data
        print("[PASS] Staff login succeeded and redirected to Staff Dashboard")

        client.get('/logout', follow_redirects=True)

        # 4. Test Registration Role Switcher GET views
        res_reg = client.get('/register?role=staff')
        assert res_reg.status_code == 200
        assert b"switchRegisterRole" in res_reg.data
        assert b"STAFF-DESK-2026" in res_reg.data
        assert b"ADMIN-MASTER-2026" in res_reg.data
        print("[PASS] Registration Role Switcher renders with role passkey options")

        # 5. Test Staff Registration with Invalid Key
        res_bad_staff = client.post('/register', data={
            'role': 'staff',
            'name': 'Rakesh Sharma',
            'student_id': 'EMP-LAB-999',
            'department': 'Central Lab & Tech Desk',
            'email': 'test_fail_staff@campus.edu',
            'phone': '9812345671',
            'staff_access_key': 'WRONG-KEY',
            'password': 'StaffPassword#1'
        }, follow_redirects=True)
        assert b"Invalid Staff Authorization Key" in res_bad_staff.data
        print("[PASS] Staff registration with invalid key rejected properly")

        # 6. Test Staff Registration with Valid Key (STAFF-DESK-2026)
        res_good_staff = client.post('/register', data={
            'role': 'staff',
            'name': 'Rakesh Sharma',
            'student_id': 'EMP-LAB-999',
            'department': 'Central Lab & Tech Desk',
            'email': 'new_staff@campus.edu',
            'phone': '9812345671',
            'staff_access_key': 'STAFF-DESK-2026',
            'password': 'StaffPassword#1'
        }, follow_redirects=True)
        assert b"Registration successful" in res_good_staff.data
        assert b"Staff" in res_good_staff.data or b"Desk" in res_good_staff.data
        print("[PASS] Staff registration with authorized key created staff account!")

        client.get('/logout', follow_redirects=True)

        # 7. Test Admin Registration with Invalid Key
        res_bad_admin = client.post('/register', data={
            'role': 'admin',
            'name': 'Dr. Vikram Seth',
            'student_id': 'ADM-FAC-999',
            'department': 'Campus Tech Administration',
            'email': 'test_fail_admin@campus.edu',
            'phone': '9812345672',
            'admin_access_key': 'WRONG-PASS',
            'password': 'AdminPassword#1'
        }, follow_redirects=True)
        assert b"Invalid Master Administrator Security Key" in res_bad_admin.data
        print("[PASS] Admin registration with invalid key rejected properly")

        # 8. Test Admin Registration with Valid Key (ADMIN-MASTER-2026)
        res_good_admin = client.post('/register', data={
            'role': 'admin',
            'name': 'Dr. Vikram Seth',
            'student_id': 'ADM-FAC-999',
            'department': 'Campus Tech Administration',
            'email': 'new_admin@campus.edu',
            'phone': '9812345672',
            'admin_access_key': 'ADMIN-MASTER-2026',
            'password': 'AdminPassword#1'
        }, follow_redirects=True)
        assert b"Registration successful" in res_good_admin.data
        assert b"Admin" in res_good_admin.data or b"Analytics" in res_good_admin.data
        print("[PASS] Admin registration with authorized master key created admin account!")

        client.get('/logout', follow_redirects=True)

        # 9. Test Student Registration with Valid Credentials
        res_good_student = client.post('/register', data={
            'role': 'student',
            'name': 'Meera Sen',
            'student_id': 'STU-2026-888',
            'department': 'Biotechnology',
            'email': 'new_student@campus.edu',
            'phone': '9812345673',
            'password': 'MeeraPassword#1'
        }, follow_redirects=True)
        assert b"Registration successful" in res_good_student.data
        print("[PASS] Student registration succeeded with all validations")

        client.get('/logout', follow_redirects=True)

        # 10. Verify Back Buttons on Login & Register
        for path in ['/login', '/register', '/login?role=staff', '/register?role=admin']:
            res = client.get(path)
            assert b"globalBackButton" in res.data, f"Global back button missing on {path}"
            assert b"goBack()" in res.data, f"goBack() function missing on {path}"
        print("[PASS] Universal Back buttons operational on all login & registration role screens!")

if __name__ == '__main__':
    test_roles_and_images()
    print("\nALL 10 REAL IMAGES & ROLE SWITCHER TESTS PASSED 100%!")
