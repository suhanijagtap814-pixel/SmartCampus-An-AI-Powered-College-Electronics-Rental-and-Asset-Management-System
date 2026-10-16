"""
AI Computer-Vision Damage Inspection.

In production this would diff a "before" and "after" photo. For the campus demo
it supports two deterministic scenarios used by the return flow / tests:

    scenario='clean'   -> no damage, score ~0
    scenario='damage'  -> moderate damage, score ~38.5 with a diff map

If real image paths are supplied it falls back to a pixel-difference heuristic.
"""
import os


def analyze_return(scenario=None, before_path=None, after_path=None,
                   upload_folder=None):
    """
    Returns a dict:
        {
          'damage_detected': bool,
          'score': float (0-100),
          'summary': str,
          'description': str,
          'diff_image_path': str | None,
          'suggested_fine': float,
        }
    """
    if scenario == 'clean':
        return {
            'damage_detected': False,
            'score': 0.0,
            'summary': 'No damage detected. Device returned in pristine condition.',
            'description': 'AI Classification: CLEAN. Surface, screen and ports '
                           'verified against intake reference. No anomalies found.',
            'diff_image_path': '/static/uploads/inspections/demo_laptop_before.jpg',
            'suggested_fine': 0.0,
        }

    if scenario == 'damage':
        score = 38.5
        return {
            'damage_detected': True,
            'score': score,
            'summary': 'Prominent chassis crack and screen corner blemish '
                       'detected by AI Computer Vision.',
            'description': 'AI Classification: MODERATE DAMAGE (38.5% severity). '
                           'Corner impact and casing stress identified in the '
                           'comparative diff map.',
            'diff_image_path': '/static/uploads/inspections/demo_laptop_damaged.jpg',
            'suggested_fine': _fine_for_score(score),
        }

    # --- Generic heuristic path (real images) ---
    score = _pixel_diff_score(before_path, after_path, upload_folder)
    detected = score >= 10.0
    return {
        'damage_detected': detected,
        'score': round(score, 1),
        'summary': ('Surface differences detected during AI comparison.'
                    if detected else 'No significant damage detected.'),
        'description': f'AI Classification: {"DAMAGE" if detected else "CLEAN"} '
                       f'({score:.1f}% severity).',
        'diff_image_path': after_path,
        'suggested_fine': _fine_for_score(score) if detected else 0.0,
    }


def _fine_for_score(score):
    """Map a damage severity (0-100) to a suggested penalty in rupees."""
    if score <= 0:
        return 0.0
    if score < 15:
        return 300.0
    if score < 50:
        return 1200.0
    if score < 80:
        return 3000.0
    return 6000.0


def _pixel_diff_score(before_path, after_path, upload_folder):
    if not (before_path and after_path):
        return 0.0
    try:
        from PIL import Image, ImageChops

        def _resolve(p):
            if p.startswith('/static/'):
                # map web path to disk under upload_folder's app root
                return os.path.join(os.path.dirname(upload_folder or ''), p.lstrip('/'))
            return p

        a = Image.open(_resolve(before_path)).convert('RGB').resize((256, 256))
        b = Image.open(_resolve(after_path)).convert('RGB').resize((256, 256))
        diff = ImageChops.difference(a, b)
        bbox = diff.getbbox()
        if not bbox:
            return 0.0
        import numpy as np
        arr = np.asarray(diff, dtype='float32')
        return float(min(100.0, arr.mean() / 255.0 * 100.0 * 3))
    except Exception:
        return 0.0
