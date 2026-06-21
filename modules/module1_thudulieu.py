# -*- coding: utf-8 -*-
"""
module1_thudulieu.py — Thu thập và cache dữ liệu chứng khoán Việt Nam.

Sử dụng vnstock API mới (không dùng Vnstock() deprecated):
  - Listing().all_symbols()                              → danh sách niêm yết
  - Quote(symbol, source).history()                     → giá OHLCV lịch sử
  - Finance(symbol, source).income_statement/balance_sheet/cash_flow()  → BCTC

Tất cả kết quả được cache xuống thư mục data/ để tránh gọi API liên tục.
Cache hết hạn sau 24 giờ (xem helpers.doc_cache).

Để pre-fetch toàn bộ danh sách cổ phiếu một lần, chạy:
  python fetch_all_data.py
"""

import io
import json
import os
from datetime import datetime

import pandas as pd
# vnstock được import lazy bên trong từng hàm để tránh gọi API lúc startup

from modules.helpers import doc_cache, ghi_cache
from config import (
    VNSTOCK_SOURCE,
    NGAY_BAT_DAU_MAC_DINH,
    DIR_GIA,
    DIR_THONG_TIN,
    DIR_BAO_CAO,
)

# Cache toàn bộ danh sách niêm yết trong memory (chỉ gọi API 1 lần mỗi process)
_listing_cache: pd.DataFrame | None = None
_LISTING_CACHE_FILE = "data/listing_all.json"


# ---------------------------------------------------------------------------
# Lấy danh sách niêm yết (dùng chung nội bộ)
# ---------------------------------------------------------------------------

def _lay_listing() -> pd.DataFrame:
    """Lấy DataFrame toàn bộ cổ phiếu niêm yết, cache vào memory và file."""
    global _listing_cache
    if _listing_cache is not None:
        return _listing_cache

    # Đọc từ file cache nếu còn hợp lệ
    if doc_cache(_LISTING_CACHE_FILE):
        with open(_LISTING_CACHE_FILE, encoding="utf-8") as f:
            raw = json.load(f)
        _listing_cache = pd.DataFrame(raw)
        return _listing_cache

    # Gọi API — lazy import để không chậm lúc startup
    try:
        from vnstock import Listing as _Listing
        df = _Listing().all_symbols()
        _listing_cache = df
        os.makedirs("data", exist_ok=True)
        ghi_cache(_LISTING_CACHE_FILE, df.to_dict(orient="records"))
        return df
    except Exception as e:
        print(f"[_lay_listing] Loi khi lay danh sach niem yet: {e}")
        _listing_cache = pd.DataFrame(columns=["symbol", "organ_name"])
        return _listing_cache


# ---------------------------------------------------------------------------
# Hàm chuẩn hóa dữ liệu giá
# ---------------------------------------------------------------------------

def chuan_hoa_du_lieu(df: pd.DataFrame) -> pd.DataFrame:
    """
    Chuẩn hóa DataFrame giá OHLCV thô từ Quote API.

    Quote API mới trả cột: time, open, high, low, close, volume
    → chuẩn hóa về: date, open, high, low, close, volume

    Bước:
    1. Rename 'time' → 'date', lowercase các cột khác.
    2. Ép kiểu: date → datetime64, OHLC → float.
    3. Sort tăng dần theo date, reset index.
    4. Xóa hàng NaN ở close.
    5. Chỉ giữ 6 cột cần thiết.
    """
    df = df.rename(columns=str.lower)

    col_map = {
        "time":          "date",
        "closeprice":    "close",
        "openprice":     "open",
        "highprice":     "high",
        "lowprice":      "low",
        "tradingvolume": "volume",
        "matchvolume":   "volume",
    }
    df = df.rename(
        columns={k: v for k, v in col_map.items() if k in df.columns})

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])

    for col in ["open", "high", "low", "close"]:
        if col in df.columns:
            df[col] = df[col].astype(float)

    df = df.sort_values("date").reset_index(drop=True)
    df = df.dropna(subset=["close"])

    cols_can_thiet = ["date", "open", "high", "low", "close", "volume"]
    cols_co = [c for c in cols_can_thiet if c in df.columns]
    return df[cols_co]


# ---------------------------------------------------------------------------
# Hàm 1: Thông tin cổ phiếu
# ---------------------------------------------------------------------------

def lay_thong_tin_co_phieu(ma_cp: str) -> dict:
    """
    Lấy thông tin chung của 1 cổ phiếu: tên, ngành, sàn, giá, khối lượng, vốn hóa.

    Cache: data/thong_tin/{ma_cp}_info.json (TTL 24h).
    API:   Listing().all_symbols() + Quote(symbol).history()

    Returns
    -------
    dict với 8 keys theo Data Contract:
        ma, ten_cong_ty, nganh, san, gia_hien_tai,
        thay_doi_phan_tram, khoi_luong, von_hoa
    """
    cache_file = f"{DIR_THONG_TIN}/{ma_cp}_info.json"

    if doc_cache(cache_file):
        with open(cache_file, encoding="utf-8") as f:
            return json.load(f)

    try:
        ten_cong_ty = ""
        nganh = ""
        san = ""

        # Lấy tên công ty từ listing (dùng cache memory)
        try:
            df_listing = _lay_listing()
            if "symbol" in df_listing.columns:
                row = df_listing[df_listing["symbol"] == ma_cp]
                if not row.empty:
                    r = row.iloc[0]
                    ten_cong_ty = str(r.get("organ_name", ""))
                    nganh = str(r.get("icb_name3", r.get("industry_name", "")))
                    san = str(r.get("exchange", "HOSE"))
        except Exception as e:
            print(f"[lay_thong_tin_co_phieu] Loi lay listing {ma_cp}: {e}")

        # Lấy giá từ Quote API
        gia_hien_tai = 0.0
        thay_doi_phan_tram = 0.0
        khoi_luong = 0
        von_hoa = 0.0
        so_co_phieu = 0

        try:
            ngay_hom_nay = datetime.now().strftime("%Y-%m-%d")
            from vnstock.api.quote import Quote
            q = Quote(symbol=ma_cp, source=VNSTOCK_SOURCE)
            df_hist = q.history(start="2024-01-01", end=ngay_hom_nay)
            df_hist = chuan_hoa_du_lieu(df_hist)
            if len(df_hist) >= 2:
                gia_hien_tai = float(df_hist["close"].iloc[-1])
                gia_truoc = float(df_hist["close"].iloc[-2])
                if gia_truoc > 0:
                    thay_doi_phan_tram = round(
                        (gia_hien_tai - gia_truoc) / gia_truoc * 100, 2)
                khoi_luong = int(df_hist["volume"].iloc[-1])
            elif len(df_hist) == 1:
                gia_hien_tai = float(df_hist["close"].iloc[-1])
                khoi_luong = int(df_hist["volume"].iloc[-1])
        except Exception as e:
            print(f"[lay_thong_tin_co_phieu] Loi lay gia {ma_cp}: {e}")

        # Map tên ngành tiếng Anh → tiếng Việt (từ sector field của overview)
        _SECTOR_VI = {
            "food & beverage":          "Thực phẩm & Đồ uống",
            "food":                     "Thực phẩm",
            "beverage":                 "Đồ uống",
            "banks":                    "Ngân hàng",
            "bank":                     "Ngân hàng",
            "financial services":       "Dịch vụ tài chính",
            "insurance":                "Bảo hiểm",
            "real estate":              "Bất động sản",
            "construction":             "Xây dựng",
            "materials":                "Vật liệu",
            "steel":                    "Thép",
            "industrial metals":        "Kim loại & Khoáng sản",
            "oil & gas":                "Dầu khí",
            "energy":                   "Năng lượng",
            "utilities":                "Tiện ích",
            "technology":               "Công nghệ",
            "software":                 "Phần mềm",
            "telecommunications":       "Viễn thông",
            "media":                    "Truyền thông",
            "retail":                   "Bán lẻ",
            "consumer discretionary":   "Tiêu dùng tùy ý",
            "consumer staples":         "Hàng tiêu dùng thiết yếu",
            "healthcare":               "Y tế & Dược",
            "pharmaceuticals":          "Dược phẩm",
            "transportation":           "Vận tải & Logistics",
            "aviation":                 "Hàng không",
            "shipping":                 "Vận tải biển",
            "agriculture":              "Nông nghiệp",
            "chemicals":                "Hóa chất",
            "securities":               "Chứng khoán",
        }

        # Lấy vốn hóa + ngành + tên công ty từ Company.overview() — API mới
        try:
            from vnstock.api.company import Company
            comp = Company(symbol=ma_cp, source=VNSTOCK_SOURCE)
            ov = comp.overview()
            if ov is not None and not ov.empty:
                # ── Vốn hóa ──
                mc_raw = ov["market_cap"].iloc[0]
                if mc_raw and float(mc_raw) > 0:
                    von_hoa = round(float(mc_raw) / 1e9, 1)

                # ── Ngành ── ưu tiên sector từ overview hơn listing
                if "sector" in ov.columns:
                    sec_raw = str(ov["sector"].iloc[0] or "").strip()
                    if sec_raw and sec_raw.lower() not in ("", "nan", "none"):
                        nganh = _SECTOR_VI.get(sec_raw.lower(), sec_raw)

                # ── Tên công ty & sàn ── nếu listing không có
                if not ten_cong_ty and "organ_name" in ov.columns:
                    ten_cong_ty = str(ov["organ_name"].iloc[0] or "").strip()
                if not san and "com_group_code" in ov.columns:
                    grp = str(ov["com_group_code"].iloc[0] or "")
                    if "HNX" in grp.upper():
                        san = "HNX"
                    elif "UPCOM" in grp.upper():
                        san = "UPCOM"
                    else:
                        san = "HOSE"

                # ── Fallback giá từ overview ──
                if gia_hien_tai == 0.0 and "current_price" in ov.columns:
                    cp_val = ov["current_price"].iloc[0]
                    if cp_val and float(cp_val) > 0:
                        gia_hien_tai = round(float(cp_val) / 1000, 2)

                # ── Số cổ phiếu ──
                if "issue_share" in ov.columns:
                    v = ov["issue_share"].iloc[0]
                    if v:
                        so_co_phieu = int(float(v))
        except Exception as e:
            print(f"[lay_thong_tin_co_phieu] Loi lay overview {ma_cp}: {e}")
            if von_hoa == 0.0 and gia_hien_tai > 0 and so_co_phieu > 0:
                von_hoa = round(gia_hien_tai * 1000 * so_co_phieu / 1e9, 1)



        if not ten_cong_ty and gia_hien_tai == 0.0:
            raise ValueError(f"Khong tim thay ma {ma_cp}")

        result = {
            "ma": ma_cp,
            "ten_cong_ty": ten_cong_ty or f"Cong ty Co phan {ma_cp}",
            "nganh": nganh or "Da nganh",
            "san": san or "HOSE",
            "gia_hien_tai": gia_hien_tai,
            "thay_doi_phan_tram": thay_doi_phan_tram,
            "khoi_luong": khoi_luong,
            "von_hoa": von_hoa,
        }

        os.makedirs(DIR_THONG_TIN, exist_ok=True)
        ghi_cache(cache_file, result)
        return result

    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"Khong tim thay ma {ma_cp}: {e}") from e



# ---------------------------------------------------------------------------
# Hàm 2: Giá lịch sử OHLCV
# ---------------------------------------------------------------------------

def lay_gia_lich_su(
    ma_cp: str,
    ngay_bat_dau: str = NGAY_BAT_DAU_MAC_DINH,
    ngay_ket_thuc: str = None,
) -> pd.DataFrame:
    """
    Lấy bảng giá OHLCV lịch sử để vẽ biểu đồ và tính chỉ báo kỹ thuật.

    Cache: data/gia/{ma_cp}_gia.csv (TTL 24h).
    API:   Quote(symbol, source).history()

    Returns
    -------
    pd.DataFrame với 6 cột: date (datetime64), open, high, low, close (float), volume.
    Sắp xếp tăng dần theo date. Không có NaN ở close.
    """
    if ngay_ket_thuc is None:
        ngay_ket_thuc = datetime.now().strftime("%Y-%m-%d")

    cache_file = f"{DIR_GIA}/{ma_cp}_gia.csv"
    su_dung_cache = (ngay_bat_dau == NGAY_BAT_DAU_MAC_DINH)

    if su_dung_cache and doc_cache(cache_file):
        return pd.read_csv(cache_file, parse_dates=["date"])

    from vnstock.api.quote import Quote
    q = Quote(symbol=ma_cp, source=VNSTOCK_SOURCE)
    df = q.history(start=ngay_bat_dau, end=ngay_ket_thuc)
    df = chuan_hoa_du_lieu(df)

    if su_dung_cache:
        os.makedirs(DIR_GIA, exist_ok=True)
        df.to_csv(cache_file, index=False)

    return df


# ---------------------------------------------------------------------------
# Hàm 3: Báo cáo tài chính
# ---------------------------------------------------------------------------

def lay_bao_cao_tai_chinh(ma_cp: str) -> dict:
    """
    Lấy báo cáo tài chính gồm 3 bảng: BCĐKT, KQKD, Lưu chuyển tiền tệ.

    Cache: data/bao_cao_tc/{ma_cp}_bctc.json (TTL 24h).
    API:   Finance(symbol, source).income_statement/balance_sheet/cash_flow()

    Returns
    -------
    dict với 3 keys: "bang_can_doi_ke_toan", "kqkd", "luu_chuyen_tien_te".
    Mỗi key là pd.DataFrame (cột 'item' = tên chỉ tiêu, các cột kỳ = giá trị số).
    Trả về dict rỗng nếu không lấy được dữ liệu.
    """
    cache_file = f"{DIR_BAO_CAO}/{ma_cp}_bctc.json"

    if doc_cache(cache_file):
        with open(cache_file, encoding="utf-8") as f:
            raw = json.load(f)
        # orient='split' cần dùng pd.read_json để reconstruct đúng
        return {k: pd.read_json(io.StringIO(json.dumps(v)), orient="split")
                for k, v in raw.items()}

    try:
        from vnstock.api.financial import Finance
        f = Finance(symbol=ma_cp, source=VNSTOCK_SOURCE)

        df_kqkd = f.income_statement(period="quarter", lang="vi")
        df_bcd = f.balance_sheet(period="quarter", lang="vi")
        df_lctt = f.cash_flow(period="quarter", lang="vi")

        result = {
            "bang_can_doi_ke_toan": df_bcd,
            "kqkd":                 df_kqkd,
            "luu_chuyen_tien_te":   df_lctt,
        }

        # Lưu cache dạng orient='split' để giữ nguyên cấu trúc columns/index
        cache_data = {k: v.to_dict(orient="split") for k, v in result.items()}
        os.makedirs(DIR_BAO_CAO, exist_ok=True)
        ghi_cache(cache_file, cache_data)

        return result

    except Exception as e:
        print(f"[lay_bao_cao_tai_chinh] Loi BCTC {ma_cp}: {e}")
        return {}


# ---------------------------------------------------------------------------
# Hàm 4: Dữ liệu so sánh nhiều mã
# ---------------------------------------------------------------------------

def lay_du_lieu_so_sanh(danh_sach_ma: list) -> dict:
    """
    Lấy dữ liệu giá lịch sử cho nhiều mã cổ phiếu để vẽ biểu đồ so sánh.

    Returns
    -------
    dict {ma_cp: pd.DataFrame} — cấu trúc giống lay_gia_lich_su().
    """
    return {ma: lay_gia_lich_su(ma) for ma in danh_sach_ma}
