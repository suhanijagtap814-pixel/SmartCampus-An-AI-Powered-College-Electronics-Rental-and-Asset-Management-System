import os
import urllib.request
from PIL import Image
import io

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), 'app', 'static', 'uploads', 'devices')
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Curated direct Unsplash high-resolution photography URLs for each real product
REAL_PRODUCT_URLS = {
    # 1. Apple MacBook Pro 16"
    'laptop_macbook.jpg': 'https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=900&auto=format&fit=crop&q=85',
    # 2. Dell XPS 15 (Sleek silver infinity edge)
    'laptop_dell.jpg': 'https://images.unsplash.com/photo-1593642632823-8f785ba67e45?w=900&auto=format&fit=crop&q=85',
    # 3. Lenovo ThinkPad P14s (Matte black business laptop)
    'laptop_thinkpad.jpg': 'https://images.unsplash.com/photo-1588872657578-7efd1f1555ed?w=900&auto=format&fit=crop&q=85',
    # 4. ASUS ROG Zephyrus G14 (Gaming RGB laptop)
    'laptop_gaming.jpg': 'https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=900&auto=format&fit=crop&q=85',
    # 5. HP Pavilion 14 (Clean silver student laptop)
    'laptop_hp.jpg': 'https://images.unsplash.com/photo-1541807084-5c52b6b3adef?w=900&auto=format&fit=crop&q=85',
    # 6. Acer Aspire 5 (Modern student laptop)
    'laptop_acer.jpg': 'https://images.unsplash.com/photo-1525547719571-a2d4ac8945e2?w=900&auto=format&fit=crop&q=85',
    # 7. Apple iPad Pro 12.9" + Apple Pencil
    'tablet_ipad.jpg': 'https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?w=900&auto=format&fit=crop&q=85',
    # 8. Samsung Galaxy Tab S9 Ultra + S-Pen
    'tablet_galaxy.jpg': 'https://images.unsplash.com/photo-1585790050230-5dd28404ccb9?w=900&auto=format&fit=crop&q=85',
    # 9. Epson 4K Laser Projector
    'projector_epson.jpg': 'https://images.unsplash.com/photo-1517604931442-7e0c8ed2963c?w=900&auto=format&fit=crop&q=85',
    # 10. BenQ Wireless Projector
    'projector_benq.jpg': 'https://images.unsplash.com/photo-1578632767115-351597cf2477?w=900&auto=format&fit=crop&q=85',
    # 11. Sony Alpha A7 IV Mirrorless Camera
    'camera_sony.jpg': 'https://images.unsplash.com/photo-1516035069371-29a1b244cc32?w=900&auto=format&fit=crop&q=85',
    # 12. Canon EOS R6 Mark II Camera
    'camera_canon.jpg': 'https://images.unsplash.com/photo-1512790182412-b19e6d62bc39?w=900&auto=format&fit=crop&q=85',
    # 13. Rigol Digital Oscilloscope / Lab bench
    'lab_oscilloscope.jpg': 'https://images.unsplash.com/photo-1581092160607-ee22621dd758?w=900&auto=format&fit=crop&q=85',
    # 14. Raspberry Pi 4 Model B IoT Kit
    'lab_raspberry.jpg': 'https://images.unsplash.com/photo-1555680202-c86f0e12f086?w=900&auto=format&fit=crop&q=85',
    # 15. Arduino Robotics Board & Hardware
    'lab_arduino.jpg': 'https://images.unsplash.com/photo-1553406830-ef2513450d76?w=900&auto=format&fit=crop&q=85',
    # 16. Bose QuietComfort 45 ANC Headphones
    'audio_bose.jpg': 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=900&auto=format&fit=crop&q=85',
    # 17. Anker 140W USB-C GaN Charger Hub
    'charger_usbc.jpg': 'https://images.unsplash.com/photo-1583863788434-e58a36330cf0?w=900&auto=format&fit=crop&q=85',
    # 18. Default Smart Tech Hub
    'default.jpg': 'https://images.unsplash.com/photo-1519389950473-47ba0277781c?w=900&auto=format&fit=crop&q=85'
}

def download_and_optimize():
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    for filename, url in REAL_PRODUCT_URLS.items():
        dest_path = os.path.join(UPLOAD_DIR, filename)
        print(f"Fetching real photo for {filename}...")
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = resp.read()
                img = Image.open(io.BytesIO(data))
                img = img.convert('RGB')
                # Crop and resize to 800x533 (standard 3:2 product card ratio)
                img.thumbnail((900, 600), Image.Resampling.LANCZOS)
                img.save(dest_path, 'JPEG', quality=90, optimize=True)
                print(f"  [SUCCESS] Saved {filename} ({img.size[0]}x{img.size[1]})")
        except Exception as e:
            print(f"  [ERROR] Could not fetch {filename}: {e}")

if __name__ == '__main__':
    download_and_optimize()
