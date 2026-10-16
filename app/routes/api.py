"""
JSON API endpoints: AI chatbot, QR scan lookup, demand prediction, and the
TF-IDF recommender.
"""
from flask import Blueprint, request, jsonify

from app.models import Device
from app.ai.chatbot import chatbot_reply
from app.ai.demand_predictor import predict_demand
from app.ai.recommender import recommend_devices
from app.utils.qr_generator import parse_qr_payload

api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/chat', methods=['POST'])
def chat():
    data = request.get_json(silent=True) or {}
    message = data.get('message', '')
    result = chatbot_reply(message)
    return jsonify(result)


@api_bp.route('/scan-qr', methods=['POST'])
def scan_qr():
    data = request.get_json(silent=True) or {}
    payload = data.get('qr_code', '')
    code, serial = parse_qr_payload(payload)
    if not code:
        return jsonify({'found': False,
                        'error': 'Unrecognised QR payload.'}), 200

    device = Device.query.filter_by(device_code=code).first()
    if not device:
        return jsonify({'found': False,
                        'error': f'No device with code {code}.'}), 200

    return jsonify({
        'found': True,
        'device': {
            'id': device.id,
            'code': device.device_code,
            'name': device.name,
            'brand': device.brand,
            'status': device.status,
            'condition': device.condition,
            'location': device.location,
            'serial_number': device.serial_number,
            'image_url': device.image_url,
            'category': device.category.name if device.category else '',
            'url': f'/device/{device.id}',
        }
    })


@api_bp.route('/predict-demand', methods=['GET'])
def api_predict_demand():
    return jsonify({'predictions': predict_demand()})


@api_bp.route('/recommend', methods=['GET', 'POST'])
def api_recommend():
    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
        query = data.get('query', '')
    else:
        query = request.args.get('query', '')
    results = recommend_devices(query, Device.query.all(), top_n=6)
    return jsonify({
        'query': query,
        'results': [{
            'id': r['device'].id, 'name': r['device'].name,
            'match': r['match'], 'reason': r['reason'],
            'price_per_day': r['device'].price_per_day,
            'url': f"/device/{r['device'].id}",
        } for r in results]
    })
