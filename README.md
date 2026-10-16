# 🎓 Smart Campus Rental & Asset Management System
> **An AI-powered, full-featured campus web platform for students, faculty, and lab managers to rent and manage Electronics & Non-Electronic Campus Assets (Laptops, Tablets, Cameras, Projectors, Oscilloscopes, IoT Kits, Sports Equipment, Lab Tools, Course Books, Campus Furniture) with PostgreSQL connectivity, automated computer vision damage inspection, before-image verification, demand forecasting, student risk profiling, and Razorpay demo payments.**

---

## 🌟 Key Features & Capabilities

### 1. 🗄️ Robust PostgreSQL Database Connectivity
* **Primary Database**: PostgreSQL 16 on `localhost:5432` (`campus_rental` database).
* **Connection Details**: `postgresql+psycopg2://postgres:postgres@localhost:5432/campus_rental`.
* **Zero-Downtime Resilience**: Automatic failover to SQLite (`instance/campus_rental.db`) if PostgreSQL is unavailable.
* **Control Scripts**:
  - `start_postgres.bat`: Starts the portable PostgreSQL server in background daemon mode.
  - `stop_postgres.bat`: Gracefully stops the PostgreSQL daemon.
  - `migrate_db.py`: Migrates database schemas and creates missing columns (`deposit_amount`, `is_non_electronic`, `damage_description`).
  - `verify_and_seed.py`: Seeds categories, non-electronic items, and calibrates feasible rent and deposits.

---

### 2. 📸 Baseline "Before-Image" Checkout Capture
* **Pre-Checkout Condition Proof**: When staff issues hardware at the Tech Desk (`/staff/issue-device`), they can capture or upload an immediate "Before" condition photograph.
* **Storage & Pathing**: Saved to `app/static/uploads/inspections/before_<uuid>.jpg` and linked to `Rental.initial_image_path`.
* **Live Optical Preview**: Drag-and-drop or camera input with instant JS preview before finalizing issuance.
* **Side-by-Side Return Verification**: During return intake, the system compares the baseline checkout photo side-by-side with the return photo for complete transparency.

---

### 3. 🖥️ Modernized Staff Management Dashboard (`/staff/dashboard`)
* **Real-Time Key Metrics**:
  - Ready for Issue (Approved student passes)
  - Active Rentals out on campus
  - Pending AI Inspections queue
  - Overdue hardware alerts (high priority warning banner)
  - Under-maintenance device counter
* **Active Loans Gallery with Before-Images**: Shows active loans, student name, roll number, due date, deposit amount, and a visual thumbnail of the checkout before-image.
* **Quick-Action Launchers**: 1-click access to Camera QR Scanner, Issue Workstation, and Return Processing.

---

### 4. 🏸 Non-Electronic Campus Rentals
The system supports both high-tech electronic equipment and non-electronic campus assets:
* **Dedicated Categories**:
  - 🏆 **Sports Equipment**: Badminton sets, cricket kits, basketballs, athletics gear.
  - 📐 **Lab Stationery & Tools**: Mitutoyo vernier calipers, micrometers, drafting kits, lab aprons.
  - 📚 **Library Books & Courseware**: Standard engineering references, GATE/exam manuals.
  - 🪑 **Campus Furniture & Gear**: Drafting tables, ergonomic study chairs, presentation easels.
* **Adaptive Specification Fields**:
  - When adding items in `/admin/add-device`, toggling **"Non-Electronic Item"** automatically switches from CPU/RAM/GPU fields to non-electronic attributes: **Unit / Quantity, Dimensions / Size, Material / Build, and Condition Rating**.
* **Visual Non-Electronic Badging**: Clearly badged across catalog cards, search filters, and detail pages.

---

### 5. 💰 Feasible Rent & Refundable Deposit Architecture
* **Product-Feasible Deposit Calculation**:
  - Security deposits are calibrated reasonably according to product value tier.
  - Default calculation: **Deposit = 3× daily rent** (e.g. ₹500/day laptop → ₹1,500 refundable deposit; ₹35/day badminton set → ₹150 deposit; ₹15/day reference book → ₹100 deposit).
  - Admins can override or customize deposit amounts for any product.
* **Transparent Student Experience**:
  - **Catalog (`/devices`)**: Shows both the subsidized daily rate and refundable deposit.
  - **Booking Screen (`/book/<id>`)**: Live calculator displays breakdown: `Rental Charges + Security Deposit = Total Payable`.
  - **Payment Gateway (`/student/payment/<id>`)**: Itemized summary reassuring students that 100% of the deposit is refunded upon undamaged return.

---

### 6. 🔍 Damage Inspection with Detailed Damage Descriptions
* **AI Computer Vision Diff Map**: Compares baseline vs. return photo, highlights scratches and screen cracks with red bounding boxes, and calculates severity score (0–100%).
* **Manual Physical Damage Description**:
  - Whenever AI flags defects, staff can record a specific physical damage description in `/staff/inspection/<id>`:
    * Exact location (e.g., *top lid corner, LCD panel, hinge*).
    * Defect type (*spiderweb crack, deep gouge, water stain*).
    * Severity and explanation.
* **Audit Trail**: This description is saved to `ReturnInspection.damage_description`, synced to admin damage reports, maintenance logs, and student inspection results.

---

### 7. 💳 Razorpay Payment Gateway (Demo / Live Mode)
* **Demo Test Credentials**: Card `4111 1111 1111 1111`, UPI `success@razorpay`, OTP `123456`.
* **Payment Methods**:
  - ⚡ Razorpay Modal (UPI, Cards, Net Banking, Wallets)
  - 📱 Direct UPI (Google Pay, PhonePe, Paytm)
  - 💳 Credit / Debit Card with live interactive card preview
  - 🏦 Net Banking across top Indian banks
  - 🎓 Smart Campus Card wallet deduction

---

## 📁 Repository Folder Structure

```
smart_campus_rental/
├── app/
│   ├── __init__.py                # Flask app factory, PostgreSQL engine, login manager
│   ├── models.py                  # SQLAlchemy models (User, Device, Booking, Rental, ReturnInspection, etc.)
│   ├── ai/
│   │   ├── __init__.py            # AI engine exports
│   │   ├── recommender.py         # AI Hardware Recommender (TF-IDF + Spec heuristics)
│   │   ├── demand_predictor.py    # AI Demand Forecasting (Scikit-Learn RandomForest)
│   │   ├── damage_detector.py     # AI Computer Vision Damage Inspection & Diff Mapping
│   │   ├── risk_detector.py       # AI Student Risk & Trust Profiler
│   │   └── chatbot.py             # Contextual Rental AI Chatbot with live DB queries
│   ├── routes/
│   │   ├── auth.py                # Login, register, 1-click role switcher
│   │   ├── student.py             # Catalog, reservations, returns, payments, fines
│   │   ├── staff.py               # Issue gear (before-image upload), receive returns, inspections
│   │   ├── admin.py               # Add device (non-electronic toggle), approvals, damage audit
│   │   └── api.py                 # REST endpoints for Chat, Recommendations, QR lookup
│   ├── static/
│   │   ├── css/custom.css         # Glassmorphism, card styling, responsive layouts
│   │   ├── js/main.js             # Booking price + deposit calculator, alert handlers
│   │   ├── js/qr_scanner.js       # html5-qrcode live webcam controller
│   │   └── uploads/
│   │       ├── devices/           # Custom uploaded device images
│   │       ├── inspections/       # Before-images, return photos, and AI diff maps
│   │       └── qrcodes/           # Branded QR tracking passes
│   ├── templates/
│   │   ├── base.html              # Core layout, navbar, role switcher, toast system
│   │   ├── auth/                  # login.html, register.html
│   │   ├── student/               # dashboard, devices, device_detail, book, payment, my_bookings, etc.
│   │   ├── staff/                 # dashboard, issue_device, receive_device, inspection_detail, qr_scanner
│   │   └── admin/                 # dashboard, add_device, approvals, damage_reports, ai_predictions
│   └── utils/
│       ├── qr_generator.py        # Generates branded QR code passes
│       └── sample_images.py       # Default before/after demonstration images
├── config.py                      # PostgreSQL / SQLite configuration & secret keys
├── migrate_db.py                  # Database schema migration script
├── verify_and_seed.py             # Seeds categories, non-electronic items, calibrates deposits
├── seed_data.py                   # Initial comprehensive seed script
├── start_postgres.bat             # Convenience batch script to start PostgreSQL daemon
├── stop_postgres.bat              # Convenience batch script to stop PostgreSQL
├── run.py                         # Application launcher with UTF-8 support
├── requirements.txt               # Python package dependencies
└── README.md                      # Comprehensive documentation (this file)
```

---

## 🚀 Quick Setup & Execution Guide

### 1. Start PostgreSQL Database
```powershell
# Option A: Run the batch file
.\start_postgres.bat

# Option B: Direct command (if using portable PostgreSQL at C:\Users\Nayan\pgsql)
& "C:\Users\Nayan\pgsql\bin\postgres.exe" -D "C:\Users\Nayan\pgsql\data"
```

### 2. Setup Python Virtual Environment
```powershell
# Create venv if not existing
python -m venv .venv

# Activate venv
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Run Database Migration & Seeding
```powershell
.venv\Scripts\python.exe migrate_db.py
.venv\Scripts\python.exe verify_and_seed.py
```

### 4. Launch the Web Application
```powershell
.venv\Scripts\python.exe run.py
```
Open your browser at **`http://127.0.0.1:5000`**.

---

## 👥 Demo User Credentials

| Role | Name | Email | Password | Primary Demo Features |
|---|---|---|---|---|
| **Student** | Aarav Sharma | `student@campus.edu` | `student123` | Active loan return, AI damage inspection, Razorpay payment |
| **Risk Student** | Priya Patel | `priya@campus.edu` | `student123` | High-risk radar demo, overdue fines |
| **Staff / Desk** | Prof. Rajesh Kumar | `staff@campus.edu` | `staff123` | Before-image issue, return intake, damage description |
| **Administrator** | Dr. Sunita Rao | `admin@campus.edu` | `admin123` | Non-electronic device creation, demand forecasting, approval |

---

## 🧪 Verification Walkthrough

1. **Database Connectivity**: When starting `run.py`, the console outputs `[DATABASE] Connected to PostgreSQL on localhost:5432/campus_rental`.
2. **Before-Image**: Log in as `staff@campus.edu`, go to `/staff/issue-device`, select an approved booking, upload a photo in the "Checkout Baseline Photograph" input, and click Issue.
3. **Staff Dashboard**: Visit `/staff/dashboard` to see the Active Rentals list with before-image thumbnails and deposit tracking.
4. **Non-Electronic Items**: Visit `/devices` or `/admin/add-device` to see Sports Equipment, Vernier Caliper, Books, and Drafting Table with non-electronic specs.
5. **Damage Description**: As staff, open an inspection with damage at `/staff/inspection/<id>` and write detailed notes in the "Damage Description" field. Observe it on `/admin/damage-reports` and student inspection report.
6. **Feasible Rent & Deposit**: Visit `/book/<id>` or `/student/payment/<id>` to see transparent breakdown of rent + refundable deposit.
