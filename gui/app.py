from flask import Flask, render_template, jsonify, request
from datetime import datetime, timedelta
import json

app = Flask(__name__)

# Mock sensor data for stalls
STALLS = {
    'stall_001': {
        'node_id': '001',
        'name': 'Barn Stall 1',
        'temp': 72,
        'humidity': 55,
        'outlet_status': 'off',
        'motion_detected': True,
        'last_updated': datetime.now() - timedelta(minutes=2),
    },
    'stall_002': {
        'node_id': '002',
        'name': 'Barn Stall 2',
        'temp': 68,
        'humidity': 48,
        'outlet_status': 'on',
        'motion_detected': False,
        'last_updated': datetime.now() - timedelta(minutes=5),
    },
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/stalls')
def get_stalls():
    stalls_data = []
    for stall_id, stall in STALLS.items():
        stalls_data.append({
            'id': stall_id,
            'node_id': stall['node_id'],
            'name': stall['name'],
            'temp': stall['temp'],
            'humidity': stall['humidity'],
            'outlet_status': stall['outlet_status'],
            'motion_detected': stall['motion_detected'],
            'last_updated': stall['last_updated'].strftime('%H:%M:%S'),
        })
    return jsonify(stalls_data)

@app.route('/api/stalls/<stall_id>/outlet', methods=['POST'])
def control_outlet(stall_id):
    if stall_id in STALLS:
        data = request.get_json()
        action = data.get('action')
        if action in ['on', 'off']:
            STALLS[stall_id]['outlet_status'] = action
            STALLS[stall_id]['last_updated'] = datetime.now()
            return jsonify({'status': 'success', 'outlet': action}), 200
    return jsonify({'status': 'error'}), 400

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)