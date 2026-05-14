"""
routes/export_routes.py — File export endpoints.

Excel export stub — will be implemented when openpyxl module is ready.
"""

from flask import Blueprint, jsonify

export_bp = Blueprint("export", __name__)


@export_bp.route("/xuat-excel/<ma_cp>")
def xuat_excel(ma_cp: str):
    """Excel export — stub (not yet implemented)."""
    return jsonify({
        "error": "Chức năng xuất Excel đang được phát triển",
        "detail": "Sẽ hoàn thiện khi tích hợp module thật"
    }), 501
