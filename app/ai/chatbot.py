"""
Contextual Rental AI Chatbot.

Rule-based assistant that answers natural-language questions by querying the
live catalog (availability, price ceilings, categories, recommendations) and
returns both a text reply and structured `device_cards` for rich rendering.
"""
import re


def _device_card(device, match=None):
    return {
        'id': device.id,
        'code': device.device_code,
        'name': device.name,
        'brand': device.brand,
        'category': device.category.name if device.category else '',
        'price_per_day': device.price_per_day,
        'deposit_amount': device.deposit_amount,
        'status': device.status,
        'image_url': device.image_url or '/static/uploads/devices/default.jpg',
        'match': match,
        'url': f'/device/{device.id}',
    }


def _extract_price_ceiling(message):
    # Matches "₹300", "300", "under 300", "rs 500"
    m = re.findall(r'(?:₹|rs\.?\s*)?(\d{2,6})', message.lower())
    if m:
        try:
            return max(float(x) for x in m) if 'under' not in message.lower() \
                else min(float(x) for x in m)
        except ValueError:
            return None
    return None


def chatbot_reply(message):
    """Return {'response': str, 'device_cards': [ ... ]}."""
    from app.models import Device
    from app.ai.recommender import recommend_devices

    message = (message or '').strip()
    devices = Device.query.all()

    if not message:
        return {
            'response': "Hi! I'm your Campus Rental Assistant. Ask me things "
                        "like 'a laptop for machine learning under ₹400' or "
                        "'which cameras are available?'",
            'device_cards': [],
        }

    lowered = message.lower()
    ceiling = _extract_price_ceiling(message)

    # Availability-focused query
    pool = devices
    if any(w in lowered for w in ('available', 'free', 'can i get', 'today', 'tomorrow')):
        pool = [d for d in devices if d.status == 'available']

    if ceiling:
        pool = [d for d in pool if d.price_per_day <= ceiling]

    ranked = recommend_devices(message, pool, top_n=4)
    cards = [_device_card(r['device'], r['match']) for r in ranked]

    if cards:
        bits = [f"I found {len(cards)} option(s) for you"]
        if ceiling:
            bits.append(f"within ₹{int(ceiling)}/day")
        reply = ' '.join(bits) + ". Here are the best matches:"
    else:
        reply = ("I couldn't find a device matching that right now. Try "
                 "relaxing the budget or browsing the full catalog.")

    return {'response': reply, 'device_cards': cards}
