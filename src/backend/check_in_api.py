"""即時報到 API（Flask）"""
import os
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory
from werkzeug.exceptions import BadRequest

from src.backend.database import CheckInDatabase
from src.backend.models import CheckInRequest


BASE_DIR = Path(__file__).resolve().parents[2]
FRONTEND_DIR = BASE_DIR / 'src' / 'frontend'

app = Flask(__name__)
db = CheckInDatabase()


@app.post('/api/check-in')
def check_in():
    try:
        payload = request.get_json() or {}
    except BadRequest:
        return jsonify({'success': False, 'message': 'Malformed JSON body'}), 400

    if not isinstance(payload, dict):
        return jsonify({'success': False, 'message': 'Invalid check-in payload'}), 400

    household_id = str(payload.get('household_id', '')).strip()
    if not household_id:
        return jsonify({'success': False, 'message': 'Missing required field: household_id'}), 400

    try:
        data = CheckInRequest.from_dict(payload)
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid check-in payload'}), 400

    result = db.add_check_in_record(
        household_id=data.household_id,
        name=data.name,
        status=data.status,
    )

    status_code = 200 if result['success'] else 409
    return jsonify(result), status_code


@app.get('/api/check-in/records')
def get_check_in_records():
    return jsonify({'records': db.get_check_in_records()})


@app.get('/api/check-in/statistics')
def get_check_in_statistics():
    return jsonify(db.get_check_in_statistics())


@app.get('/')
def scanner_page():
    return send_from_directory(FRONTEND_DIR, 'check_in_scanner.html')


@app.get('/scanner')
def scanner_alias_page():
    return send_from_directory(FRONTEND_DIR, 'check_in_scanner.html')


@app.get('/admin')
def admin_page():
    return send_from_directory(FRONTEND_DIR, 'check_in_admin.html')


if __name__ == '__main__':
    debug_mode = os.getenv('FLASK_ENV', '').lower() == 'development'
    host = os.getenv('FLASK_HOST', '127.0.0.1')
    port = int(os.getenv('FLASK_PORT', '5000'))
    app.run(host=host, port=port, debug=debug_mode)
