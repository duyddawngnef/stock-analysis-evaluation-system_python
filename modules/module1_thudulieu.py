"""
module1_thudulieu.py — Thu thập và cache dữ liệu chứng khoán Việt Nam.

Sử dụng thư viện vnstock (source="VCI") để lấy:
  - Thông tin cổ phiếu (tên, ngành, sàn, giá, khối lượng, vốn hóa)
  - Bảng giá lịch sử OHLCV
  - Báo cáo tài chính (BCTC): 3 bảng

Tất cả kết quả được cache xuống thư mục data/ để tránh gọi API liên tục.
Cache hết hạn sau 24 giờ (xem helpers.doc_cache).

Lỗi thường gặp với vnstock (xem docs/BUGS.md):
  - Tên cột có thể là "closePrice" thay vì "close" → dùng chuan_hoa_du_lieu()
  - Cột date trả về string → ép kiểu pd.to_datetime()
  - Một số mã không có BCTC đầy đủ → xử lý try-except, trả về dict rỗng
  - Mã ngân hàng (VCB, BID, CTG...) có cấu trúc BCTC khác → wrap từng lookup
"""

import json
import os
from datetime import datetime

import pandas as pd
from vnstock import Vnstock

from modules.helpers import doc_cache, ghi_cache

# ---------------------------------------------------------------------------
# Đường dẫn thư mục cache
# ---------------------------------------------------------------------------
_DIR_GIA = "data/gia"
_DIR_THONG_TIN = "data/thong_tin"
_DIR_BAO_CAO = "data/bao_cao_tc"


# ---------------------------------------------------------------------------
# Hàm chuẩn hóa dữ liệu (dùng nội bộ và export cho module khác)
# ---------------------------------------------------------------------------

def chuan_hoa_du_lieu(df: pd.DataFrame) -> pd.DataFrame:
    """
    Chuẩn hóa DataFrame giá OHLCV thô từ vnstock.

    Các bước (theo hướng dẫn tuần 1 + docs/BUGS.md):
    1. Đổi tên cột về lowercase chuẩn (date, open, high, low, close, volume).
    2. Map tên cột vnstock về tên chuẩn (closePrice → close, v.v.).
    3. Ép kiểu: date → datetime64, open/high/low/close → float.
    4. Sắp xếp tăng dần theo date, reset index.
    5. Xóa hàng NaN ở cột close.
    6. Chỉ giữ 6 cột cần thiết.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame thô từ vnstock (tên cột có thể khác chuẩn).

    Returns
    -------
    pd.DataFrame
        DataFrame đã chuẩn hóa với đúng 6 cột: date, open, high, low, close, volume.
    """
    # Bước 1: Đổi tên cột về lowercase
    df = df.rename(columns=str.lower)

    # Bước 2: Map tên cột vnstock → tên chuẩn
    # QUAN TRỌNG: In cột để debug trước khi map (theo docs/BUGS.md)
    print(f"[chuan_hoa_du_lieu] Cột sau lowercase: {list(df.columns)}")

    col_map = {
        "closeprice": "close",
        "openprice": "open",
        "highprice": "high",
        "lowprice": "low",
        "tradingvolume": "volume",
        "matchvolume": "volume",
        "time": "date",
    }
    df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})

    # Bước 3: Ép kiểu date
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])

    # Bước 3b: Ép kiểu số
    for col in ["open", "high", "low", "close"]:
        if col in df.columns:
            df[col] = df[col].astype(float)

    # Bước 4: Sắp xếp tăng dần theo date
    df = df.sort_values("date").reset_index(drop=True)

    # Bước 5: Xóa NaN ở close
    df = df.dropna(subset=["close"])

    # Bước 6: Chỉ giữ 6 cột cần thiết (bỏ cột thừa)
    cols_can_thiet = ["date", "open", "high", "low", "close", "volume"]
    cols_co = [c for c in cols_can_thiet if c in df.columns]
    return df[cols_co]


# ---------------------------------------------------------------------------
# Hàm 1: Thông tin cổ phiếu
# ---------------------------------------------------------------------------

def lay_thong_tin_co_phieu(ma_cp: str) -> dict:
    """
    Lấy thông tin chung của 1 cổ phiếu: tên, ngành, sàn, giá, khối lượng, vốn hóa.

    Cache kết quả vào data/thong_tin/{ma_cp}_info.json (TTL 24h).

    Parameters
    ----------
    ma_cp : str
        Mã cổ phiếu, ví dụ: "VNM", "FPT".

    Returns
    -------
    dict
        8 keys cố định theo data contract:
        ma, ten_cong_ty, nganh, san, gia_hien_tai,
        thay_doi_phan_tram, khoi_luong, von_hoa.

    Raises
    ------
    ValueError
        Nếu mã cổ phiếu không tồn tại hoặc vnstock không trả về dữ liệu.
    """
    cache_file = f"{_DIR_THONG_TIN}/{ma_cp}_info.json"

    # Đọc cache nếu còn hợp lệ
    if doc_cache(cache_file):
        with open(cache_file, encoding="utf-8") as f:
            return json.load(f)

    try:
        stock = Vnstock().stock(symbol=ma_cp, source="VCI")

        ten_cong_ty = ""
        nganh = ""
        san = ""

        # Lấy thông tin công ty từ listing
        try:
            df_listing = stock.listing.symbols_by_exchange()
            print(f"[lay_thong_tin_co_phieu] Cột listing: {list(df_listing.columns)}")
            row = df_listing[df_listing["ticker"] == ma_cp]
            if not row.empty:
                r = row.iloc[0]
                ten_cong_ty = str(r.get("organ_name", r.get("organName", "")))
                nganh = str(r.get("icb_name3", r.get("icbName3",
                             r.get("industry_name", r.get("industryName", "")))))
                san = str(r.get("exchange", r.get("comGroupCode", "")))
        except Exception as e:
            print(f"[lay_thong_tin_co_phieu] Không lấy được listing cho {ma_cp}: {e}")

        # Lấy giá từ lịch sử gần nhất (FIX #4: dùng ngày thực tế, không cứng ngày tương lai)
        gia_hien_tai = 0.0
        thay_doi_phan_tram = 0.0
        khoi_luong = 0
        von_hoa = 0.0

        try:
            ngay_hom_nay = datetime.now().strftime("%Y-%m-%d")
            df_hist = stock.quote.history(start="2024-01-01", end=ngay_hom_nay)
            print(f"[lay_thong_tin_co_phieu] Cột history: {list(df_hist.columns)}")
            df_hist = chuan_hoa_du_lieu(df_hist)
            if len(df_hist) >= 2:
                gia_hien_tai = float(df_hist["close"].iloc[-1])
                gia_truoc = float(df_hist["close"].iloc[-2])
                if gia_truoc > 0:
                    thay_doi_phan_tram = round((gia_hien_tai - gia_truoc) / gia_truoc * 100, 2)
                khoi_luong = int(df_hist["volume"].iloc[-1])
            elif len(df_hist) == 1:
                gia_hien_tai = float(df_hist["close"].iloc[-1])
                khoi_luong = int(df_hist["volume"].iloc[-1])
        except Exception as e:
            print(f"[lay_thong_tin_co_phieu] Không lấy được history cho {ma_cp}: {e}")

        # Kiểm tra có lấy được dữ liệu không
        if not ten_cong_ty and gia_hien_tai == 0.0:
            raise ValueError(f"Không tìm thấy mã {ma_cp}")

        result = {
            "ma": ma_cp,
            "ten_cong_ty": ten_cong_ty or f"Công ty Cổ phần {ma_cp}",
            "nganh": nganh or "Đa ngành",
            "san": san or "HOSE",
            "gia_hien_tai": gia_hien_tai,
            "thay_doi_phan_tram": thay_doi_phan_tram,
            "khoi_luong": khoi_luong,
            "von_hoa": von_hoa,
        }

        ghi_cache(cache_file, result)
        return result

    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"Không tìm thấy mã {ma_cp}: {e}") from e


# ---------------------------------------------------------------------------
# Hàm 2: Giá lịch sử OHLCV
# ---------------------------------------------------------------------------

def lay_gia_lich_su(
    ma_cp: str,
    ngay_bat_dau: str = "2022-01-01",
    ngay_ket_thuc: str = None,
) -> pd.DataFrame:
    """
    Lấy bảng giá OHLCV lịch sử để vẽ biểu đồ và tính chỉ báo kỹ thuật.

    Cache kết quả vào data/gia/{ma_cp}_gia.csv (TTL 24h).

    FIX #5: Cache key không phân biệt date range → chỉ cache range mặc định 2 năm.
    Nếu cần date range khác, bỏ qua cache và gọi API trực tiếp.

    Parameters
    ----------
    ma_cp : str
        Mã cổ phiếu.
    ngay_bat_dau : str
        Ngày bắt đầu, định dạng "YYYY-MM-DD".
    ngay_ket_thuc : str | None
        Ngày kết thúc. Nếu None → dùng ngày hôm nay.

    Returns
    -------
    pd.DataFrame
        6 cột: date (datetime64), open, high, low, close (float), volume (int).
        Sắp xếp tăng dần theo date. Không có NaN ở close.
    """
    # FIX #4: Không cứng ngày tương lai, dùng ngày thực tế
    if ngay_ket_thuc is None:
        ngay_ket_thuc = datetime.now().strftime("%Y-%m-%d")

    cache_file = f"{_DIR_GIA}/{ma_cp}_gia.csv"

    # Đọc cache nếu còn hợp lệ (chỉ dùng cache cho date range mặc định)
    _ngay_mac_dinh = "2022-01-01"
    su_dung_cache = (ngay_bat_dau == _ngay_mac_dinh)

    if su_dung_cache and doc_cache(cache_file):
        return pd.read_csv(cache_file, parse_dates=["date"])

    stock = Vnstock().stock(symbol=ma_cp, source="VCI")
    df = stock.quote.history(start=ngay_bat_dau, end=ngay_ket_thuc)

    # In cột để debug — QUAN TRỌNG theo hướng dẫn tuần 1 + docs/BUGS.md
    print(f"[lay_gia_lich_su] Cột vnstock trả về: {list(df.columns)}")

    df = chuan_hoa_du_lieu(df)

    # Lưu cache chỉ khi dùng date range mặc định
    if su_dung_cache:
        df.to_csv(cache_file, index=False)

    return df


# ---------------------------------------------------------------------------
# Hàm 3: Báo cáo tài chính
# ---------------------------------------------------------------------------

def lay_bao_cao_tai_chinh(ma_cp: str) -> dict:
    """
    Lấy báo cáo tài chính gồm 3 bảng: BCĐKT, KQKD, Lưu chuyển tiền tệ.

    Cache kết quả vào data/bao_cao_tc/{ma_cp}_bctc.json (TTL 24h).

    FIX #3: Dùng custom serializer trong ghi_cache để xử lý numpy.int64,
    pd.Timestamp không serialize được bằng json.dump thông thường.

    Parameters
    ----------
    ma_cp : str
        Mã cổ phiếu.

    Returns
    -------
    dict
        3 keys: "bang_can_doi_ke_toan", "kqkd", "luu_chuyen_tien_te".
        Mỗi key là một pd.DataFrame (hàng = chỉ tiêu, cột = kỳ báo cáo).
        Trả về dict rỗng nếu không lấy được dữ liệu (xem docs/BUGS.md — bank stocks).
    """
    cache_file = f"{_DIR_BAO_CAO}/{ma_cp}_bctc.json"

    # Đọc cache nếu còn hợp lệ
    if doc_cache(cache_file):
        with open(cache_file, encoding="utf-8") as f:
            raw = json.load(f)
        return {k: pd.DataFrame(v) for k, v in raw.items()}

    try:
        stock = Vnstock().stock(symbol=ma_cp, source="VCI")

        df_kqkd = stock.finance.income_statement(period="quarter", lang="vi")
        df_bcd = stock.finance.balance_sheet(period="quarter", lang="vi")
        df_lctt = stock.finance.cash_flow(period="quarter", lang="vi")

        # In index để debug — theo ghi chú pitfall BCTC trong docs/BUGS.md
        print(f"[lay_bao_cao_tai_chinh] KQKD index (5 đầu): {list(df_kqkd.index)[:5]}")
        print(f"[lay_bao_cao_tai_chinh] BCĐKT index (5 đầu): {list(df_bcd.index)[:5]}")

        result = {
            "bang_can_doi_ke_toan": df_bcd,
            "kqkd": df_kqkd,
            "luu_chuyen_tien_te": df_lctt,
        }

        # FIX #3: to_dict() + ghi_cache với custom serializer (xử lý numpy/pandas types)
        # Dùng orient="split" để giữ nguyên index tên chỉ tiêu
        cache_data = {k: v.to_dict(orient="split") for k, v in result.items()}
        ghi_cache(cache_file, cache_data)

        return result

    except Exception as e:
        print(f"[lay_bao_cao_tai_chinh] Lỗi khi lấy BCTC cho {ma_cp}: {e}")
        return {}


# ---------------------------------------------------------------------------
# Hàm 4: Dữ liệu so sánh
# ---------------------------------------------------------------------------

def lay_du_lieu_so_sanh(danh_sach_ma: list) -> dict:
    """
    Lấy dữ liệu giá lịch sử cho nhiều mã cổ phiếu để vẽ biểu đồ so sánh.

    Parameters
    ----------
    danh_sach_ma : list[str]
        Danh sách mã cổ phiếu (tối đa 5 theo scope constraint).

    Returns
    -------
    dict
        {ma_cp: pd.DataFrame} — mỗi DataFrame có cấu trúc giống lay_gia_lich_su().
    """
    return {ma: lay_gia_lich_su(ma) for ma in danh_sach_ma}
