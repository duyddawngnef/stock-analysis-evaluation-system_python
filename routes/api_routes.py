"""
routes/api_routes.py — JSON API endpoints.

Tất cả dữ liệu lấy từ module thật (module1, module2, module3).
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from flask import Blueprint, jsonify, request
from modules import module1_thudulieu as module1
from modules import module2_kythuat    as module2
from modules import module3_coban      as module3

api_bp = Blueprint("api", __name__)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _err(msg: str, detail: str = "", status: int = 400):
    return jsonify({"error": msg, "detail": detail}), status


# ---------------------------------------------------------------------------
# Module 1 — Stock info & price history
# ---------------------------------------------------------------------------

@api_bp.route("/thong-tin/<ma_cp>")
def thong_tin(ma_cp: str):
    """Trả về thông tin chung của cổ phiếu."""
    try:
        data = module1.lay_thong_tin_co_phieu(ma_cp.upper())
        return jsonify(data)
    except Exception as exc:
        return _err("Không lấy được thông tin cổ phiếu", str(exc), 500)


@api_bp.route("/gia-lich-su/<ma_cp>")
def gia_lich_su(ma_cp: str):
    """Trả về lịch sử giá OHLCV dưới dạng JSON cho Chart.js."""
    try:
        df = module1.lay_gia_lich_su(ma_cp.upper())
        # Serialize: date → ISO string, numbers → float
        records = []
        for _, row in df.iterrows():
            records.append({
                "date":   row["date"].strftime("%Y-%m-%d"),
                "open":   round(float(row["open"]),   2),
                "high":   round(float(row["high"]),   2),
                "low":    round(float(row["low"]),    2),
                "close":  round(float(row["close"]),  2),
                "volume": int(row["volume"]),
            })
        return jsonify(records)
    except Exception as exc:
        return _err("Không lấy được lịch sử giá", str(exc), 500)


# ---------------------------------------------------------------------------
# Module 2 — Technical analysis
# ---------------------------------------------------------------------------

@api_bp.route("/ky-thuat/<ma_cp>")
def ky_thuat(ma_cp: str):
    """Trả về kết quả phân tích kỹ thuật."""
    try:
        df = module1.lay_gia_lich_su(ma_cp.upper())
        data = module2.tom_tat_module2(df)
        return jsonify(data)
    except Exception as exc:
        return _err("Không thể phân tích kỹ thuật", str(exc), 500)


# ---------------------------------------------------------------------------
# Module 3 — Fundamental analysis
# ---------------------------------------------------------------------------

@api_bp.route("/co-ban/<ma_cp>")
def co_ban(ma_cp: str):
    """Trả về kết quả phân tích cơ bản."""
    try:
        data = module3.tom_tat_module3(ma_cp.upper())
        return jsonify(data)
    except Exception as exc:
        return _err("Không thể phân tích cơ bản", str(exc), 500)


# ---------------------------------------------------------------------------
# So sánh — Multi-ticker comparison
# ---------------------------------------------------------------------------

@api_bp.route("/so-sanh", methods=["POST"])
def so_sanh():
    """Trả về dữ liệu giá của nhiều mã để so sánh."""
    body = request.get_json(silent=True) or {}
    danh_sach = body.get("ma_list", [])

    if not danh_sach or not isinstance(danh_sach, list):
        return _err("Thiếu danh sách mã cổ phiếu", "Cần truyền {ma_list: [...]}")

    danh_sach = [str(m).upper() for m in danh_sach[:5]]  # max 5

    try:
        result = module1.lay_du_lieu_so_sanh(danh_sach)
        # Serialize each DataFrame
        serialized = {}
        for ma, df in result.items():
            serialized[ma] = [
                {
                    "date":  row["date"].strftime("%Y-%m-%d"),
                    "close": round(float(row["close"]), 2),
                }
                for _, row in df.iterrows()
            ]

        # Also fetch technical + fundamental summaries for table
        summaries = {}
        for ma in danh_sach:
            try:
                df_full = module1.lay_gia_lich_su(ma)
                tech = module2.tom_tat_module2(df_full)
                fund = module3.tom_tat_module3(ma)
                info = module1.lay_thong_tin_co_phieu(ma)
                summaries[ma] = {
                    "info": info,
                    "ky_thuat": {
                        "tin_hieu": tech["tin_hieu"],
                        "rsi": tech["rsi"],
                        "ma20": tech["ma20"],
                        "ma50": tech["ma50"],
                    },
                    "co_ban": {
                        "ROE": fund["chi_so"]["ROE"],
                        "ROA": fund["chi_so"]["ROA"],
                        "EPS": fund["chi_so"]["EPS"],
                        "PE":  fund["chi_so"]["PE"],
                        "PB":  fund["chi_so"]["PB"],
                        "DE":  fund["chi_so"]["DE"],
                        "phan_loai": fund["cham_diem"]["phan_loai"],
                        "tong": fund["cham_diem"]["tong"],
                    },
                }
            except Exception:
                summaries[ma] = {}

        return jsonify({"gia": serialized, "tom_tat": summaries})
    except Exception as exc:
        return _err("Không thể tải dữ liệu so sánh", str(exc), 500)
