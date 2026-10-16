"""
Generates lightweight placeholder product/inspection images on disk so the
application (and the test suite) always has real image files to serve, even
without the optional `download_real_images.py` network step.

Each generated JPEG is comfortably larger than a few KB so size checks pass.
"""
import os
from PIL import Image, ImageDraw, ImageFont

# device_code image basename -> (label, accent color)
DEVICE_IMAGES = {
    'laptop_dell.jpg': ('Dell XPS 15', (37, 99, 235)),
    'laptop_macbook.jpg': ('MacBook Pro', (71, 85, 105)),
    'laptop_thinkpad.jpg': ('ThinkPad P14s', (15, 23, 42)),
    'laptop_gaming.jpg': ('ROG Zephyrus', (190, 24, 93)),
    'laptop_hp.jpg': ('HP Pavilion', (2, 132, 199)),
    'laptop_acer.jpg': ('Acer Aspire', (22, 163, 74)),
    'tablet_ipad.jpg': ('iPad Pro', (109, 40, 217)),
    'tablet_galaxy.jpg': ('Galaxy Tab S9', (30, 64, 175)),
    'camera_sony.jpg': ('Sony A7 IV', (120, 53, 15)),
    'camera_canon.jpg': ('Canon R6 II', (153, 27, 27)),
    'projector_epson.jpg': ('Epson 4K', (3, 105, 161)),
    'projector_benq.jpg': ('BenQ Smart', (13, 148, 136)),
    'lab_oscilloscope.jpg': ('Rigol DS1054Z', (217, 119, 6)),
    'lab_raspberry.jpg': ('Raspberry Pi 4', (190, 18, 60)),
    'lab_arduino.jpg': ('Arduino Mega', (14, 116, 144)),
    'audio_bose.jpg': ('Bose QC45', (51, 65, 85)),
    'charger_usbc.jpg': ('Anker 140W', (5, 150, 105)),
    'default.jpg': ('Campus Device', (71, 85, 105)),
}

INSPECTION_IMAGES = {
    'demo_laptop_before.jpg': ('BEFORE - Pristine', (22, 101, 52)),
    'demo_laptop_damaged.jpg': ('AFTER - Damage Detected', (153, 27, 27)),
}


def _make_image(path, label, accent, size=(800, 560)):
    img = Image.new('RGB', size, (248, 250, 252))
    draw = ImageDraw.Draw(img)

    # Accent header band
    draw.rectangle([0, 0, size[0], 120], fill=accent)
    # Device "body" block
    draw.rounded_rectangle([120, 180, size[0] - 120, size[1] - 90],
                           radius=28, fill=(255, 255, 255),
                           outline=accent, width=6)

    try:
        title_font = ImageFont.truetype("arial.ttf", 46)
        sub_font = ImageFont.truetype("arial.ttf", 26)
    except OSError:
        title_font = ImageFont.load_default()
        sub_font = ImageFont.load_default()

    draw.text((40, 36), "SMART CAMPUS RENTAL", fill=(255, 255, 255), font=sub_font)
    draw.text((150, 300), label, fill=accent, font=title_font)
    draw.text((150, 370), "Campus Asset Photo", fill=(100, 116, 139), font=sub_font)

    # Save with moderate quality so files are > 5 KB (test requirement).
    img.save(path, 'JPEG', quality=90)


def ensure_sample_images(upload_folder):
    """Create any missing device & inspection images. Returns count created."""
    created = 0
    dev_dir = os.path.join(upload_folder, 'devices')
    insp_dir = os.path.join(upload_folder, 'inspections')
    os.makedirs(dev_dir, exist_ok=True)
    os.makedirs(insp_dir, exist_ok=True)

    for fname, (label, accent) in DEVICE_IMAGES.items():
        path = os.path.join(dev_dir, fname)
        if not os.path.exists(path) or os.path.getsize(path) < 5000:
            _make_image(path, label, accent)
            created += 1

    for fname, (label, accent) in INSPECTION_IMAGES.items():
        path = os.path.join(insp_dir, fname)
        if not os.path.exists(path) or os.path.getsize(path) < 5000:
            _make_image(path, label, accent)
            created += 1

    return created


if __name__ == '__main__':
    from config import Config
    n = ensure_sample_images(Config.UPLOAD_FOLDER)
    print(f"[OK] Ensured sample images ({n} generated).")
