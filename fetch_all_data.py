# -*- coding: utf-8 -*-
"""
fetch_all_data.py — Pre-fetch và cache dữ liệu cho toàn bộ danh sách cổ phiếu.

Chạy 1 lần trước khi start Flask:
    python fetch_all_data.py

Sau khi chạy xong, Flask sẽ đọc từ cache (data/) thay vì gọi API
→ bấm vào mã nào cũng hiển thị ngay lập tức (< 1 giây).

Rate limit Guest: 20 request/phút → script tự động nghỉ khi bị chặn.
Cache hết hạn sau 24h. Chạy lại mỗi ngày để cập nhật giá mới.
"""

import os
import sys
import time
from datetime import datetime

os.environ["PYTHONIOENCODING"] = "utf-8"
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(__file__))

from config import DANH_SACH_CO_PHIEU
from modules import module1_thudulieu as m1


# ---------------------------------------------------------------------------
# Hằng số
# ---------------------------------------------------------------------------
SLEEP_GIUA_CAC_CALL = 4      # giây nghỉ giữa mỗi API call (tránh rate limit)
SLEEP_GIUA_CAC_MA   = 2      # giây nghỉ thêm sau mỗi mã
WAIT_RATE_LIMIT     = 65     # giây chờ khi bị rate limit (60s + buffer)
MAX_RETRY           = 3      # số lần thử lại tối đa


# ---------------------------------------------------------------------------
# Helper hiển thị progress
# ---------------------------------------------------------------------------

def _bar(done: int, total: int, width: int = 30) -> str:
    filled = int(width * done / total) if total else 0
    return f"[{'#' * filled}{'-' * (width - filled)}] {done}/{total}"


def _log(i: int, total: int, ma: str, buoc: str, ok: bool):
    status = "OK " if ok else "LOI"
    print(f"  {_bar(i, total)} {ma:6s} | {buoc:20s} | {status}", flush=True)


def _la_rate_limit(e: Exception) -> bool:
    """Kiểm tra xem exception có phải rate limit không."""
    msg = str(e).lower()
    return any(k in msg for k in [
        "rate limit", "ratelimit", "too many", "429",
        "gioi han", "giới hạn", "limit exceeded",
    ])


def _goi_api_voi_retry(ham, ten_ham: str):
    """
    Gọi hàm API với retry logic tự động khi bị rate limit.
    Trả về kết quả hoặc raise Exception nếu hết retry.
    """
    for lan_thu in range(1, MAX_RETRY + 1):
        try:
            return ham()
        except Exception as e:
            if _la_rate_limit(e) and lan_thu < MAX_RETRY:
                print(f"  [RATE LIMIT] {ten_ham} - Cho {WAIT_RATE_LIMIT}s roi thu lai ({lan_thu}/{MAX_RETRY})...", flush=True)
                time.sleep(WAIT_RATE_LIMIT)
            elif lan_thu >= MAX_RETRY:
                raise
            else:
                raise


# ---------------------------------------------------------------------------
# Fetch từng loại dữ liệu (mỗi loại riêng với retry)
# ---------------------------------------------------------------------------

def fetch_thong_tin(ma: str, i: int, total: int) -> bool:
    try:
        info = _goi_api_voi_retry(
            lambda: m1.lay_thong_tin_co_phieu(ma),
            f"thong_tin({ma})"
        )
        _log(i, total, ma, "thong tin", bool(info.get("ten_cong_ty") or info.get("gia_hien_tai")))
        time.sleep(SLEEP_GIUA_CAC_CALL)
        return True
    except Exception as e:
        _log(i, total, ma, "thong tin", False)
        print(f"    => {type(e).__name__}: {str(e)[:80]}", flush=True)
        return False


def fetch_gia(ma: str, i: int, total: int) -> bool:
    try:
        df = _goi_api_voi_retry(
            lambda: m1.lay_gia_lich_su(ma),
            f"gia({ma})"
        )
        _log(i, total, ma, "gia lich su", len(df) > 0)
        time.sleep(SLEEP_GIUA_CAC_CALL)
        return True
    except Exception as e:
        _log(i, total, ma, "gia lich su", False)
        print(f"    => {type(e).__name__}: {str(e)[:80]}", flush=True)
        return False


def fetch_bctc(ma: str, i: int, total: int) -> bool:
    try:
        bctc = _goi_api_voi_retry(
            lambda: m1.lay_bao_cao_tai_chinh(ma),
            f"bctc({ma})"
        )
        _log(i, total, ma, "bao cao TC", bool(bctc))
        time.sleep(SLEEP_GIUA_CAC_CALL)
        return True
    except Exception as e:
        _log(i, total, ma, "bao cao TC", False)
        print(f"    => {type(e).__name__}: {str(e)[:80]}", flush=True)
        return False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    danh_sach = DANH_SACH_CO_PHIEU
    total = len(danh_sach)
    ok_count = 0
    loi_count = 0
    loi_ma = []

    print("=" * 65, flush=True)
    print(f"  VN STOCK ANALYZER - PRE-FETCH DU LIEU", flush=True)
    print(f"  Thoi gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
    print(f"  Tong so ma: {total}", flush=True)
    print(f"  Rate limit: 20 req/phut (Guest) - tu dong cho neu bi chan", flush=True)
    print("=" * 65, flush=True)

    for d in ["data/gia", "data/thong_tin", "data/bao_cao_tc"]:
        os.makedirs(d, exist_ok=True)

    t_start = time.time()

    for i, ma in enumerate(danh_sach, 1):
        print(f"\n[{i:02d}/{total}] === {ma} ===", flush=True)

        ok1 = fetch_thong_tin(ma, i, total)
        ok2 = fetch_gia(ma, i, total)
        ok3 = fetch_bctc(ma, i, total)

        if ok1 and ok2 and ok3:
            ok_count += 1
        else:
            loi_count += 1
            loi_ma.append(ma)

        time.sleep(SLEEP_GIUA_CAC_MA)

    t_end = time.time()
    elapsed = t_end - t_start

    print("\n" + "=" * 65, flush=True)
    print(f"  KET QUA:", flush=True)
    print(f"  Thanh cong : {ok_count}/{total}", flush=True)
    print(f"  Loi        : {loi_count}/{total}", flush=True)
    if loi_ma:
        print(f"  Ma bi loi  : {', '.join(loi_ma)}", flush=True)
    phut = int(elapsed // 60)
    giay = int(elapsed % 60)
    print(f"  Thoi gian  : {phut}m{giay}s ({elapsed/total:.1f}s/ma)", flush=True)
    print(f"  Cache luu  : data/gia/, data/thong_tin/, data/bao_cao_tc/", flush=True)
    print("=" * 65, flush=True)
    print(flush=True)
    if ok_count == total:
        print("  [OK] Pre-fetch hoan thanh! Chay Flask ngay bay gio:", flush=True)
    else:
        print(f"  [!] {loi_count} ma bi loi. Chay lai script de thu lai.", flush=True)
    print("  python app.py", flush=True)
    print(flush=True)


if __name__ == "__main__":
    main()
