import os
import psycopg2
from app import create_app
from app.models import db, DeviceCategory, Device, User, Booking, Rental, ReturnInspection

app = create_app()

with app.app_context():
    print(f"Checking Database: {app.config['SQLALCHEMY_DATABASE_URI']}")
    
    # 1. Ensure upload directories exist
    upload_dirs = [
        os.path.join(app.config['UPLOAD_FOLDER'], 'devices'),
        os.path.join(app.config['UPLOAD_FOLDER'], 'inspections')
    ]
    for d in upload_dirs:
        os.makedirs(d, exist_ok=True)
    print("Upload directories verified.")

    # 2. Add non-electronic categories if not present
    new_categories = [
        ("Sports Equipment", "trophy", "Sports gear, rackets, cricket kits, balls, and athletics accessories."),
        ("Lab Stationery & Tools", "pen-tool", "Non-electronic lab equipment, measuring tools, drafting tools, and aprons."),
        ("Library Books & Courseware", "book-open", "Standard reference books, competitive exam guides, and reference journals."),
        ("Campus Furniture & Gear", "armchair", "Study chairs, drafting tables, desk lamps, and project display boards.")
    ]

    for cat_name, icon, desc in new_categories:
        cat = DeviceCategory.query.filter_by(name=cat_name).first()
        if not cat:
            cat = DeviceCategory(name=cat_name, icon=icon, description=desc)
            db.session.add(cat)
            print(f"Added Category: {cat_name}")
    db.session.commit()

    # 3. Update existing electronic devices with feasible deposit amounts (3x daily rent or min 300)
    devices = Device.query.all()
    for d in devices:
        if not d.deposit_amount or d.deposit_amount <= 0:
            # Feasible deposit calculation based on product rental rate:
            # High-value electronics (>= 200/day): 3x daily rent
            # Moderate electronics: 3x daily rent
            d.deposit_amount = round(max(300.0, d.price_per_day * 3.0), 2)
            print(f"Updated deposit for {d.name}: Rent Rs.{d.price_per_day}/day -> Deposit Rs.{d.deposit_amount}")

    # 4. Seed sample non-electronic items if none exist
    sports_cat = DeviceCategory.query.filter_by(name="Sports Equipment").first()
    lab_cat = DeviceCategory.query.filter_by(name="Lab Stationery & Tools").first()
    book_cat = DeviceCategory.query.filter_by(name="Library Books & Courseware").first()
    furniture_cat = DeviceCategory.query.filter_by(name="Campus Furniture & Gear").first()

    sample_non_electronics = [
        {
            "code": "SPT-101",
            "name": "Yonex Carbonex Badminton Dual Racket Set",
            "category_id": sports_cat.id if sports_cat else 1,
            "brand": "Yonex",
            "model": "Carbonex 8000 Plus",
            "serial": "SN-YONEX-8001",
            "price_per_day": 35.0,
            "deposit_amount": 150.0,
            "is_non_electronic": True,
            "status": "available",
            "condition": "Excellent",
            "location": "Gymkhana Sports Center - Desk A",
            "specs": {"unit": "Set of 2 + Case", "material": "Carbon Graphite", "size": "Standard G4", "weight": "85g"},
            "tags": "sports, badminton, yonex, fitness, tournament",
            "image_url": "https://images.unsplash.com/photo-1626224583764-f87db24ac4ea?w=600&auto=format&fit=crop&q=80"
        },
        {
            "code": "LAB-201",
            "name": "Mitutoyo High-Precision Digital Vernier Caliper (150mm)",
            "category_id": lab_cat.id if lab_cat else 1,
            "brand": "Mitutoyo",
            "model": "Digimatic 500-196-30",
            "serial": "SN-MITU-9921",
            "price_per_day": 45.0,
            "deposit_amount": 250.0,
            "is_non_electronic": True,
            "status": "available",
            "condition": "Excellent",
            "location": "Mechanical Workshop - Lab 2",
            "specs": {"unit": "1 Piece in Hard Case", "material": "Hardened Stainless Steel", "size": "150mm / 6-inch", "accuracy": "±0.02mm"},
            "tags": "mechanical, lab, measurement, engineering, workshop",
            "image_url": "https://images.unsplash.com/photo-1581092160607-ee22621dd758?w=600&auto=format&fit=crop&q=80"
        },
        {
            "code": "BOK-301",
            "name": "Higher Engineering Mathematics (44th Ed.) - B.S. Grewal",
            "category_id": book_cat.id if book_cat else 1,
            "brand": "Khanna Publishers",
            "model": "Paperback Reference",
            "serial": "ISBN-978-8193328491",
            "price_per_day": 15.0,
            "deposit_amount": 100.0,
            "is_non_electronic": True,
            "status": "available",
            "condition": "Good",
            "location": "Central Library - Reserve Counter",
            "specs": {"unit": "1 Volume (1300+ pages)", "material": "High Quality Paperback", "size": "Standard Royal Octavo", "subject": "Engineering Maths"},
            "tags": "book, library, mathematics, gate, semester",
            "image_url": "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=600&auto=format&fit=crop&q=80"
        },
        {
            "code": "FUR-401",
            "name": "Heavy-Duty Architect Drafting Table & Adjustable Stand",
            "category_id": furniture_cat.id if furniture_cat else 1,
            "brand": "Steelcraft Campus",
            "model": "DraftMaster Pro A1",
            "serial": "SN-FURN-DRAFT-04",
            "price_per_day": 60.0,
            "deposit_amount": 350.0,
            "is_non_electronic": True,
            "status": "available",
            "condition": "Excellent",
            "location": "Architecture Studio - Block B",
            "specs": {"unit": "1 Board with Parallel Rule", "material": "Pine Board with Powder-Coated Steel", "size": "A1 (90x60 cm)", "tilt": "0-60 degrees"},
            "tags": "furniture, drafting, architecture, design, drawing",
            "image_url": "https://images.unsplash.com/photo-1518455027359-f3f8164ba6bd?w=600&auto=format&fit=crop&q=80"
        }
    ]

    for item in sample_non_electronics:
        dev = Device.query.filter_by(device_code=item["code"]).first()
        if not dev:
            dev = Device(
                device_code=item["code"],
                name=item["name"],
                category_id=item["category_id"],
                brand=item["brand"],
                model=item["model"],
                serial_number=item["serial"],
                price_per_day=item["price_per_day"],
                deposit_amount=item["deposit_amount"],
                is_non_electronic=item["is_non_electronic"],
                status=item["status"],
                condition=item["condition"],
                location=item["location"],
                specs=item["specs"],
                tags=item["tags"],
                image_url=item["image_url"]
            )
            db.session.add(dev)
            print(f"Added Non-Electronic Item: {item['name']} (Rent: Rs.{item['price_per_day']}, Deposit: Rs.{item['deposit_amount']})")

    db.session.commit()
    print("Seeding completed successfully!")
