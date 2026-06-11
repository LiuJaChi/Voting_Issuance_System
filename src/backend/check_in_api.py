"""
即時報到系統 - Flask API
提供 QR Code 掃描、報到記錄、統計查詢等功能
"""
import os
from flask import Flask, jsonify, request, send_from_directory
from werkzeug.exceptions import BadRequest
from datetime import datetime
from pathlib import Path

from src.backend.database import CheckInDatabase
from src.backend.models import CheckInRequest


# ═══════════════════════════════════════════════════════════════════════════════
# Flask 應用初始化
# ═══════════════════════════════════════════════════════════════════════════════

app = Flask(__name__)
app.config['JSON_ENSURE_ASCII'] = False

# 初始化資料庫
db = CheckInDatabase()


# ═══════════════════════════════════════════════════════════════════════════════
# API 路由
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/api/check-in', methods=['POST'])
def api_check_in():
    """
    POST /api/check-in
    報到 API - 接收掃描數據並記錄報到
    
    請求格式：
    {
        "household_id": "A106-02",
        "name": "洪正平"  (可選)
    }
    
    返回格式：
    {
        "success": true,
        "message": "Check-in successful for A106-02",
        "data": {
            "household_id": "A106-02",
            "check_in_time": "2026-06-11T10:30:00"
        }
    }
    """
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

    # 執行報到
    success, message, status_code = db.check_in(data.household_id, data.name)

    if success:
        return jsonify({
            'success': True,
            'message': message,
            'data': {
                'household_id': data.household_id,
                'check_in_time': datetime.now().isoformat()
            }
        }), status_code
    else:
        return jsonify({
            'success': False,
            'message': message
        }), status_code


@app.route('/api/check-in/records', methods=['GET'])
def api_get_records():
    """
    GET /api/check-in/records
    獲取報到記錄
    
    查詢參數：
    - limit: 返回記錄數（默認 100）
    - offset: 跳過記錄數（默認 0）
    
    返回格式：
    {
        "success": true,
        "data": [
            {
                "id": 1,
                "household_id": "A106-02",
                "name": "洪正平",
                "check_in_time": "2026-06-11T10:30:00",
                "status": "checked_in"
            }
        ]
    }
    """
    try:
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        limit = min(limit, 1000)  # 最多返回 1000 條
    except (ValueError, TypeError):
        limit = 100
        offset = 0

    records = db.get_records(limit, offset)
    return jsonify({
        'success': True,
        'data': records
    }), 200


@app.route('/api/check-in/statistics', methods=['GET'])
def api_get_statistics():
    """
    GET /api/check-in/statistics
    獲取報到統計
    
    返回格式：
    {
        "success": true,
        "data": {
            "total_checked_in": 42,
            "by_status": {
                "checked_in": 42
            },
            "timestamp": "2026-06-11T10:35:00"
        }
    }
    """
    stats = db.get_statistics()
    return jsonify({
        'success': True,
        'data': stats
    }), 200


# ═══════════════════════════════════════════════════════════════════════════════
# 前端頁面路由
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/scanner', methods=['GET'])
def scanner_page():
    """提供手機掃描頁面"""
    scanner_path = Path(__file__).parent.parent / 'frontend' / 'check_in_scanner.html'
    if scanner_path.exists():
        return send_from_directory(str(scanner_path.parent), 'check_in_scanner.html')
    return jsonify({'error': 'Scanner page not found'}), 404


@app.route('/admin', methods=['GET'])
def admin_page():
    """提供管理統計頁面"""
    admin_path = Path(__file__).parent.parent / 'frontend' / 'check_in_admin.html'
    if admin_path.exists():
        return send_from_directory(str(admin_path.parent), 'check_in_admin.html')
    return jsonify({'error': 'Admin page not found'}), 404


@app.route('/health', methods=['GET'])
def health_check():
    """健康檢查"""
    return jsonify({'status': 'ok'}), 200


# ═══════════════════════════════════════════════════════════════════════════════
# 錯誤處理
# ═══════════════════════════════════════════════════════════════════════════════

@app.errorhandler(404)
def not_found(error):
    """404 錯誤處理"""
    return jsonify({'success': False, 'message': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    """500 錯誤處理"""
    return jsonify({'success': False, 'message': 'Internal server error'}), 500


# ═══════════════════════════════════════════════════════════════════════════════
# 主程序
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    # 配置
    host = os.getenv('FLASK_HOST', '127.0.0.1')
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'

    print(f"""
    ╔════════════════════════════════════════════════════════════════╗
    ║         即時報到系統 - API 服務已啟動                           ║
    ╠════════════════════════════════════════════════════════════════╣
    ║ 掃描頁面: http://{host}:{port}/scanner                           ║
    ║ 管理頁面: http://{host}:{port}/admin                             ║
    ║ API 文檔: http://{host}:{port}/api/docs                          ║
    ║ 健康檢查: http://{host}:{port}/health                            ║
    ╚════════════════════════════════════════════════════════════════╝
    """)

    app.run(host=host, port=port, debug=debug)
