"""
Branded QR-code pass generator for campus devices.

QR payload format (decoded by /api/scan-qr):
    CAMPUS_DEVICE:<device_code>:<serial_number>
"""
import os
import qrcode
from qrcode.constants import ERROR_CORRECT_H


def build_qr_payload(device):
    """Canonical QR string embedded in every device badge."""
    return f"CAMPUS_DEVICE:{device.device_code}:{device.serial_number or 'NA'}"


def parse_qr_payload(payload):
    """Return (device_code, serial) from a scanned payload, or (None, None)."""
    if not payload or not isinstance(payload, str):
        return None, None
    parts = payload.strip().split(':')
    if len(parts) >= 2 and parts[0] == 'CAMPUS_DEVICE':
        code = parts[1]
        serial = parts[2] if len(parts) >= 3 else None
        return code, serial
    return None, None


def generate_device_qr(device, upload_folder):
    """
    Generate a QR badge PNG for a device and return its web path
    (e.g. '/static/uploads/qrcodes/LAP-101.png').
    """
    qr_dir = os.path.join(upload_folder, 'qrcodes')
    os.makedirs(qr_dir, exist_ok=True)

    qr = qrcode.QRCode(
        version=1,
        error_correction=ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(build_qr_payload(device))
    qr.make(fit=True)
    img = qr.make_image(fill_color="#0f172a", back_color="white")

    filename = f"{device.device_code}.png"
    abs_path = os.path.join(qr_dir, filename)
    img.save(abs_path)

    return f"/static/uploads/qrcodes/{filename}"
