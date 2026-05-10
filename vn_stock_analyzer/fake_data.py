"""
fake_data.py — Synthetic data conforming to the project data contract.

Used during Frontend-First development (tuần 1-2).
To switch to real data, replace imports in app.py:

    from modules import module1_thudulieu as module1
    from modules import module2_kythuat    as module2
    from modules import module3_coban      as module3

All functions here mirror the exact signatures and return structures
defined in docs/data_contract.md.
"""

import pandas as pd
import numpy as np

# ---------------------------------------------------------------------------
# MODULE 1 — THU THẬP DỮ LIỆU
# ---------------------------------------------------------------------------

_COMPANY_INFO = {
    "VNM": ("Công ty Cổ phần Sữa Việt Nam",           "Thực phẩm & Đồ uống", "HOSE",  67.5,  1.81, 1_234_567, 142_000),
    "FPT": ("Công ty Cổ phần FPT",                    "Công nghệ thông tin", "HOSE", 115.2, -0.52, 2_345_678, 175_000),
    "HPG": ("Công ty Cổ phần Tập đoàn Hòa Phát",     "Thép",                "HOSE",  28.4,  0.35, 8_765_432, 168_000),
    "VIC": ("Tập đoàn Vingroup",                       "Bất động sản",        "HOSE",  42.1, -1.17, 3_456_789, 145_000),
    "MWG": ("Công ty Cổ phần Đầu tư Thế Giới Di Động","Bán lẻ",              "HOSE",  55.6,  2.03, 1_567_890,  88_000),
    "VCB": ("Ngân hàng TMCP Ngoại thương Việt Nam",   "Ngân hàng",           "HOSE",  88.0,  0.11, 4_200_000, 312_000),
    "BID": ("Ngân hàng TMCP Đầu tư và Phát triển VN", "Ngân hàng",           "HOSE",  48.5, -0.20, 5_100_000, 245_000),
    "TCB": ("Ngân hàng TMCP Kỹ Thương Việt Nam",      "Ngân hàng",           "HOSE",  22.3,  0.45, 3_800_000,  98_000),
}


def lay_thong_tin_co_phieu(ma_cp: str) -> dict:
    """Trả về thông tin chung của 1 cổ phiếu."""
    ten, nganh, san, gia, thay_doi, kl, vh = _COMPANY_INFO.get(
        ma_cp,
        (f"Công ty Cổ phần {ma_cp}", "Đa ngành", "HOSE", 50.0, 0.0, 1_000_000, 50_000),
    )
    return {
        "ma": ma_cp,
        "ten_cong_ty": ten,
        "nganh": nganh,
        "san": san,
        "gia_hien_tai": gia,
        "thay_doi_phan_tram": thay_doi,
        "khoi_luong": kl,
        "von_hoa": vh,
    }


def lay_gia_lich_su(
    ma_cp: str,
    ngay_bat_dau: str = "2022-01-01",
    ngay_ket_thuc: str = "2024-12-31",
) -> pd.DataFrame:
    """
    Trả về bảng giá OHLCV lịch sử.
    Cột date (datetime64), open, high, low, close (float), volume (int).
    Sắp xếp tăng dần theo date. Không có NaN.
    """
    seed = sum(ord(c) for c in ma_cp)
    rng = np.random.default_rng(seed)

    dates = pd.bdate_range(start=ngay_bat_dau, end=ngay_ket_thuc)
    n = len(dates)

    base = _COMPANY_INFO.get(ma_cp, (None, None, None, 50.0))[3]
    returns = rng.normal(0.0003, 0.015, n)
    close = base * np.exp(np.cumsum(returns))
    close = np.maximum(close, 5.0)

    spread = rng.uniform(0.005, 0.025, n)
    high = close * (1 + spread)
    low = close * (1 - spread)
    open_ = low + rng.uniform(0, 1, n) * (high - low)
    volume = rng.integers(500_000, 10_000_000, n)

    return pd.DataFrame({
        "date": dates,
        "open": open_.round(2),
        "high": high.round(2),
        "low": low.round(2),
        "close": close.round(2),
        "volume": volume,
    }).sort_values("date").reset_index(drop=True)


def lay_bao_cao_tai_chinh(ma_cp: str) -> dict:
    """
    Trả về báo cáo tài chính.
    dict gồm 3 DataFrame: bang_can_doi_ke_toan, kqkd, luu_chuyen_tien_te.
    Hàng = chỉ tiêu, cột = kỳ báo cáo. Cột mới nhất ở vị trí 0.
    """
    periods = ["Q4/2023", "Q3/2023", "Q2/2023", "Q1/2023", "Q4/2022", "Q3/2022"]
    rng = np.random.default_rng(sum(ord(c) for c in ma_cp) + 1)
    B = 1_000_000_000  # 1 tỷ đồng

    def rand_row(lo, hi):
        return (rng.integers(lo, hi, len(periods)) * B).tolist()

    kqkd = pd.DataFrame(
        {
            "Doanh thu thuần":       rand_row(10_000, 50_000),
            "Lợi nhuận gộp":         rand_row( 3_000, 15_000),
            "Lợi nhuận từ HĐKD":    rand_row( 1_500, 10_000),
            "Lợi nhuận sau thuế":    rand_row( 1_000,  9_000),
        },
        index=periods,
    ).T

    bang_can_doi = pd.DataFrame(
        {
            "Tổng tài sản":           rand_row(50_000, 200_000),
            "Tổng nợ phải trả":       rand_row(20_000,  80_000),
            "Vốn chủ sở hữu":         rand_row(30_000, 120_000),
            "Số cổ phiếu lưu hành":   (rng.integers(1_000, 5_000, len(periods)) * 1_000_000).tolist(),
        },
        index=periods,
    ).T

    luu_chuyen = pd.DataFrame(
        {
            "Lưu chuyển tiền từ HĐKD": rand_row(-5_000, 10_000),
            "Lưu chuyển tiền từ HĐĐT": rand_row(-10_000, -1_000),
            "Lưu chuyển tiền từ HĐTC": rand_row(-5_000,   5_000),
        },
        index=periods,
    ).T

    return {
        "bang_can_doi_ke_toan": bang_can_doi,
        "kqkd": kqkd,
        "luu_chuyen_tien_te": luu_chuyen,
    }


def lay_du_lieu_so_sanh(danh_sach_ma: list) -> dict:
    """Trả về dict {ma_cp: DataFrame_gia} cho danh sách mã."""
    return {ma: lay_gia_lich_su(ma) for ma in danh_sach_ma}


# ---------------------------------------------------------------------------
# MODULE 2 — PHÂN TÍCH KỸ THUẬT
# ---------------------------------------------------------------------------

def tom_tat_module2(df_gia: pd.DataFrame) -> dict:
    """
    Trả về kết quả phân tích kỹ thuật tổng hợp.
    Xem docs/data_contract.md để biết cấu trúc trả về đầy đủ.
    """
    close = df_gia["close"]
    last = float(close.iloc[-1])

    ma20  = round(float(close.tail(20).mean()),  2) if len(close) >= 20  else None
    ma50  = round(float(close.tail(50).mean()),  2) if len(close) >= 50  else None
    ma200 = round(float(close.tail(200).mean()), 2) if len(close) >= 200 else None

    rng2 = np.random.default_rng(int(last * 100) % 9973)
    rsi_val  = round(float(rng2.uniform(25, 75)), 2)
    macd_val = round(float(rng2.uniform(-2, 2)), 4)
    sig_val  = round(macd_val + float(rng2.uniform(-0.5, 0.5)), 4)

    so_mua = sum([
        rsi_val < 30,
        macd_val > sig_val,
        ma20 is not None and last > ma20,
        ma50 is not None and last > ma50,
    ])

    if so_mua >= 3:
        tin_hieu = "MUA MẠNH"
    elif so_mua == 2:
        tin_hieu = "MUA"
    elif so_mua == 1:
        tin_hieu = "GIỮ"
    else:
        tin_hieu = "BÁN"

    std20 = float(close.tail(20).std()) if len(close) >= 20 else last * 0.02
    mid   = ma20 or round(last, 2)

    return {
        "ma": {"MA20": ma20, "MA50": ma50, "MA200": ma200},
        "rsi": rsi_val,
        "macd": {
            "macd": macd_val,
            "signal": sig_val,
            "histogram": round(macd_val - sig_val, 4),
        },
        "bollinger": {
            "upper": round(mid + 2 * std20, 2),
            "middle": mid,
            "lower": round(mid - 2 * std20, 2),
        },
        "tin_hieu": tin_hieu,
        "so_tin_hieu_mua": so_mua,
        "giai_thich": (
            f"RSI = {rsi_val} ({'quá bán' if rsi_val < 30 else 'quá mua' if rsi_val > 70 else 'trung tính'}). "
            f"MACD {'trên' if macd_val > sig_val else 'dưới'} Signal."
        ),
    }


# ---------------------------------------------------------------------------
# MODULE 3 — PHÂN TÍCH CƠ BẢN
# ---------------------------------------------------------------------------

def tom_tat_module3(ma_cp: str) -> dict:
    """
    Trả về kết quả phân tích cơ bản tổng hợp.
    Xem docs/data_contract.md để biết cấu trúc trả về đầy đủ.
    """
    rng3 = np.random.default_rng(sum(ord(c) for c in ma_cp) + 3)

    roe = round(float(rng3.uniform(8,  28)),    1)
    roa = round(float(rng3.uniform(3,  15)),    1)
    eps = round(float(rng3.uniform(1_000, 8_000)), 0)
    pe  = round(float(rng3.uniform(7,  25)),    1)
    pb  = round(float(rng3.uniform(0.8, 3.5)), 2)
    de  = round(float(rng3.uniform(0.3, 2.5)), 2)

    def s_roe(v): return 2 if v > 20 else (1 if v >= 15 else 0)
    def s_roa(v): return 2 if v > 10 else (1 if v >= 5  else 0)
    def s_eps(v): return 2 if v > 5_000 else (1 if v >= 2_000 else 0)
    def s_pe(v):  return 2 if 8 <= v <= 15 else (1 if v <= 20 else 0)
    def s_pb(v):  return 2 if v < 1.5 else (1 if v <= 2.5 else 0)
    def s_de(v):  return 2 if v < 1   else (1 if v <= 2   else 0)

    scores = {
        "ROE": s_roe(roe),
        "ROA": s_roa(roa),
        "EPS": s_eps(eps),
        "PE":  s_pe(pe),
        "PB":  s_pb(pb),
        "DE":  s_de(de),
    }
    tong = sum(scores.values())
    phan_loai = "TỐT" if tong >= 9 else ("KHÁ" if tong >= 5 else "YẾU")

    return {
        "chi_so": {"ROE": roe, "ROA": roa, "EPS": eps, "PE": pe, "PB": pb, "DE": de},
        "cham_diem": {**scores, "tong": tong, "phan_loai": phan_loai},
    }


# ---------------------------------------------------------------------------
# Quick smoke-test when run directly
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=== lay_thong_tin_co_phieu ===")
    print(lay_thong_tin_co_phieu("VNM"))

    print("\n=== lay_gia_lich_su (5 rows) ===")
    df = lay_gia_lich_su("VNM", "2024-01-01", "2024-12-31")
    print(df.head())

    print("\n=== lay_bao_cao_tai_chinh (kqkd) ===")
    bctc = lay_bao_cao_tai_chinh("VNM")
    print(bctc["kqkd"])

    print("\n=== tom_tat_module2 ===")
    print(tom_tat_module2(df))

    print("\n=== tom_tat_module3 ===")
    print(tom_tat_module3("VNM"))
