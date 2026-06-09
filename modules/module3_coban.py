"""
module3_coban.py — Phân tích cơ bản (Fundamental Analysis).

Tính các chỉ số tài chính từ BCTC thật (lấy qua module1_thudulieu):
  - ROE, ROA, EPS, P/E, P/B, D/E
  - Hệ thống chấm điểm doanh nghiệp (thang 0-12)

Cấu trúc BCTC vnstock (source=VCI, lang='vi'):
  DataFrame có cột: item, item_en, item_id, <kỳ1>, <kỳ2>, ...
  Mỗi hàng = 1 chỉ tiêu tài chính (cột 'item' = tên tiếng Việt)
  Cột kỳ báo cáo format: '2026-Q1', '2025-Q4', ... — cột đầu = mới nhất
"""

import pandas as pd

from modules import module1_thudulieu as m1

# ---------------------------------------------------------------------------
# Danh sách tên chỉ tiêu — hỗ trợ nhiều cách viết của vnstock
# ---------------------------------------------------------------------------

_LOI_NHUAN_SAU_THUE = [
    "Lợi nhuận sau thuế",
    "Lợi nhuận sau thuế thu nhập doanh nghiệp",
    "Profit after tax",
    "Net profit",
    "Cổ đông của Công ty mẹ",           # một số mã vnstock gộp ở đây
]

_VON_CHU_SO_HUU = [
    "VỐN CHỦ SỞ HỮU",
    "Vốn chủ sở hữu",
    "TỔNG VỐN CHỦ SỞ HỮU",
    "Total equity",
    "Owner's equity",
]

_TONG_TAI_SAN = [
    "TỔNG TÀI SẢN",
    "Tổng cộng tài sản",
    "Tổng tài sản",
    "TOTAL ASSETS",
    "Total assets",
]

_TONG_NO = [
    "TỔNG NỢ PHẢI TRẢ",
    "Tổng nợ phải trả",
    "Nợ phải trả",
    "Total liabilities",
]

_SO_CP_LUU_HANH = [
    "Số lượng cổ phiếu lưu hành",
    "Số cổ phiếu lưu hành",
    "Cổ phiếu lưu hành",
    "Shares outstanding",
]

_VON_DIEU_LE = [
    "Vốn điều lệ",
    "Charter capital",
]


# ---------------------------------------------------------------------------
# Hàm tiện ích nội bộ — tìm theo cột 'item' (cấu trúc vnstock mới)
# ---------------------------------------------------------------------------

def _lay_gia_tri(df: pd.DataFrame, danh_sach_ten: list, ky: int = 0) -> float | None:
    """
    Tìm giá trị một chỉ tiêu trong BCTC vnstock.

    vnstock trả DataFrame dạng:
      cột 'item' = tên chỉ tiêu (tiếng Việt)
      cột 'item_en' = tên tiếng Anh
      các cột còn lại = kỳ báo cáo ('2026-Q1', '2025-Q4', ...)

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame BCTC từ vnstock.
    danh_sach_ten : list[str]
        Danh sách tên cần tìm (thử theo thứ tự ưu tiên).
    ky : int
        Chỉ số kỳ (0 = kỳ mới nhất).

    Returns
    -------
    float | None
    """
    if df is None or df.empty:
        return None

    # Tìm cột kỳ báo cáo (bỏ qua item, item_en, item_id)
    _meta_cols = {"item", "item_en", "item_id"}
    ky_cols = [c for c in df.columns if c not in _meta_cols]
    if not ky_cols or ky >= len(ky_cols):
        return None
    ky_col = ky_cols[ky]

    # Tìm hàng theo tên chỉ tiêu
    for ten in danh_sach_ten:
        # Tìm chính xác trong cột 'item'
        if "item" in df.columns:
            mask = df["item"].astype(str).str.strip() == ten.strip()
            if mask.any():
                val = df.loc[mask, ky_col].iloc[0]
                try:
                    if pd.isna(val):
                        return None
                    return float(val)
                except (TypeError, ValueError):
                    return None

        # Tìm trong 'item_en'
        if "item_en" in df.columns:
            mask = df["item_en"].astype(str).str.strip() == ten.strip()
            if mask.any():
                val = df.loc[mask, ky_col].iloc[0]
                try:
                    if pd.isna(val):
                        return None
                    return float(val)
                except (TypeError, ValueError):
                    return None

    # Tìm gần đúng (contains) — fallback cuối cùng
    for ten in danh_sach_ten:
        if "item" in df.columns:
            mask = df["item"].astype(str).str.contains(ten.strip(), case=False, na=False)
            if mask.any():
                val = df.loc[mask, ky_col].iloc[0]
                try:
                    if pd.isna(val):
                        return None
                    return float(val)
                except (TypeError, ValueError):
                    return None

    return None


def _lay_so_cp_tu_von_dieu_le(bao_cao_tc: dict) -> float | None:
    """
    Ước tính số CP lưu hành từ Vốn điều lệ / mệnh giá 10,000đ.
    Dùng khi không tìm thấy trực tiếp số CP lưu hành.
    """
    bcdk = bao_cao_tc.get("bang_can_doi_ke_toan")
    von_dieu_le = _lay_gia_tri(bcdk, _VON_DIEU_LE)
    if von_dieu_le is None or von_dieu_le <= 0:
        return None
    # Mệnh giá cổ phiếu VN = 10,000 đồng; vnstock đơn vị đồng (không phải tỷ)
    # von_dieu_le đơn vị đồng → số CP = von_dieu_le / 10000
    return von_dieu_le / 10_000


# ---------------------------------------------------------------------------
# Hàm 1: ROE
# ---------------------------------------------------------------------------

def tinh_roe(bao_cao_tc: dict) -> float | None:
    """Tính ROE = Lợi nhuận sau thuế / Vốn chủ sở hữu × 100%."""
    kqkd = bao_cao_tc.get("kqkd")
    bcdk = bao_cao_tc.get("bang_can_doi_ke_toan")

    loi_nhuan = _lay_gia_tri(kqkd, _LOI_NHUAN_SAU_THUE)
    von_chu = _lay_gia_tri(bcdk, _VON_CHU_SO_HUU)

    if loi_nhuan is None or von_chu is None:
        print("[tinh_roe] Khong tim thay Loi nhuan sau thue hoac Von chu so huu")
        return None
    if von_chu == 0:
        return None

    return round((loi_nhuan / von_chu) * 100, 2)


# ---------------------------------------------------------------------------
# Hàm 2: ROA
# ---------------------------------------------------------------------------

def tinh_roa(bao_cao_tc: dict) -> float | None:
    """Tính ROA = Lợi nhuận sau thuế / Tổng tài sản × 100%."""
    kqkd = bao_cao_tc.get("kqkd")
    bcdk = bao_cao_tc.get("bang_can_doi_ke_toan")

    loi_nhuan = _lay_gia_tri(kqkd, _LOI_NHUAN_SAU_THUE)
    tong_tai_san = _lay_gia_tri(bcdk, _TONG_TAI_SAN)

    if loi_nhuan is None or tong_tai_san is None:
        print("[tinh_roa] Khong tim thay du lieu")
        return None
    if tong_tai_san == 0:
        return None

    return round((loi_nhuan / tong_tai_san) * 100, 2)


# ---------------------------------------------------------------------------
# Hàm 3: EPS
# ---------------------------------------------------------------------------

def tinh_eps(bao_cao_tc: dict) -> float | None:
    """
    Tính EPS từ BCTC.

    Ưu tiên: lấy trực tiếp 'Lãi cơ bản trên cổ phiếu' nếu có trong KQKD.
    Fallback: tính = Lợi nhuận / số CP lưu hành.
    Đơn vị trả về: đồng/CP.
    """
    kqkd = bao_cao_tc.get("kqkd")
    bcdk = bao_cao_tc.get("bang_can_doi_ke_toan")

    # Thử lấy EPS trực tiếp từ KQKD (vnstock thường có sẵn)
    eps_direct = _lay_gia_tri(kqkd, [
        "Lãi cơ bản trên cổ phiếu (VND)",
        "Lãi cơ bản trên cổ phiếu",
        "Basic earnings per share",
        "EPS",
    ])
    if eps_direct is not None and abs(eps_direct) > 0:
        return round(eps_direct, 0)

    # Fallback: tính thủ công
    loi_nhuan = _lay_gia_tri(kqkd, _LOI_NHUAN_SAU_THUE)
    if loi_nhuan is None:
        return None

    # Tìm số CP
    so_cp = _lay_gia_tri(bcdk, _SO_CP_LUU_HANH)
    if so_cp is None:
        so_cp = _lay_so_cp_tu_von_dieu_le(bao_cao_tc)
    if so_cp is None or so_cp == 0:
        return None

    # loi_nhuan đơn vị đồng (vnstock source=VCI)
    # so_cp đơn vị cổ phiếu
    return round(loi_nhuan / so_cp, 0)


# ---------------------------------------------------------------------------
# Hàm 4: P/E
# ---------------------------------------------------------------------------

def tinh_pe(gia_hien_tai: float, eps: float) -> float | None:
    """
    Tính P/E = Giá hiện tại / EPS.
    gia_hien_tai: nghìn đồng/CP (từ data contract module1).
    eps: đồng/CP.
    """
    if eps is None or eps <= 0:
        return None
    # gia_hien_tai (nghìn đồng) × 1000 → đồng
    return round((gia_hien_tai * 1000) / eps, 2)


# ---------------------------------------------------------------------------
# Hàm 5: P/B
# ---------------------------------------------------------------------------

def tinh_pb(gia_hien_tai: float, bao_cao_tc: dict) -> float | None:
    """
    Tính P/B = Giá / Giá trị sổ sách mỗi CP.
    BVPS = Vốn chủ sở hữu / Số CP lưu hành.
    gia_hien_tai: nghìn đồng/CP.
    """
    bcdk = bao_cao_tc.get("bang_can_doi_ke_toan")
    von_chu = _lay_gia_tri(bcdk, _VON_CHU_SO_HUU)
    if von_chu is None:
        return None

    so_cp = _lay_gia_tri(bcdk, _SO_CP_LUU_HANH)
    if so_cp is None:
        so_cp = _lay_so_cp_tu_von_dieu_le(bao_cao_tc)
    if so_cp is None or so_cp == 0:
        return None

    # BVPS (đồng/CP)
    bvps = von_chu / so_cp
    if bvps <= 0:
        return None

    # gia_hien_tai nghìn đồng → * 1000 → đồng
    return round((gia_hien_tai * 1000) / bvps, 2)


# ---------------------------------------------------------------------------
# Hàm 6: D/E
# ---------------------------------------------------------------------------

def tinh_de(bao_cao_tc: dict) -> float | None:
    """Tính D/E = Tổng nợ phải trả / Vốn chủ sở hữu."""
    bcdk = bao_cao_tc.get("bang_can_doi_ke_toan")
    tong_no = _lay_gia_tri(bcdk, _TONG_NO)
    von_chu = _lay_gia_tri(bcdk, _VON_CHU_SO_HUU)

    if tong_no is None or von_chu is None or von_chu == 0:
        return None

    return round(tong_no / von_chu, 2)


# ---------------------------------------------------------------------------
# Hàm 7: Chấm điểm doanh nghiệp
# ---------------------------------------------------------------------------

def cham_diem_doanh_nghiep(chi_so_dict: dict) -> dict:
    """
    Chấm điểm tổng thể theo 6 chỉ số, thang 0-12.

    Tiêu chí:
      ROE: >=20 → 2đ | 15-20 → 1đ | <15 → 0đ
      ROA: >=10 → 2đ | 5-10  → 1đ | <5  → 0đ
      EPS: >=5000 → 2đ | 2000-5000 → 1đ | <2000 → 0đ
      P/E: 8-15 → 2đ | 15-20 → 1đ | ngoài → 0đ
      P/B: <1.5 → 2đ | 1.5-2.5 → 1đ | >2.5 → 0đ
      D/E: <1   → 2đ | 1-2    → 1đ | >2   → 0đ
    """
    roe = chi_so_dict.get("roe")
    roa = chi_so_dict.get("roa")
    eps = chi_so_dict.get("eps")
    pe  = chi_so_dict.get("pe")
    pb  = chi_so_dict.get("pb")
    de  = chi_so_dict.get("de")

    def s(v, tiers):
        if v is None:
            return 0
        for score, cond in tiers:
            if cond(v):
                return score
        return 0

    chi_tiet = {
        "ROE": s(roe, [(2, lambda v: v >= 20), (1, lambda v: v >= 15)]),
        "ROA": s(roa, [(2, lambda v: v >= 10), (1, lambda v: v >= 5)]),
        "EPS": s(eps, [(2, lambda v: v >= 5000), (1, lambda v: v >= 2000)]),
        "PE":  s(pe,  [(2, lambda v: 8 <= v <= 15), (1, lambda v: v <= 20)]),
        "PB":  s(pb,  [(2, lambda v: v < 1.5), (1, lambda v: v <= 2.5)]),
        "DE":  s(de,  [(2, lambda v: v < 1),   (1, lambda v: v <= 2)]),
    }
    diem_tong = sum(chi_tiet.values())
    phan_loai = "TỐT" if diem_tong >= 9 else ("KHÁ" if diem_tong >= 5 else "YẾU")

    return {
        "diem_tong": diem_tong,
        "phan_loai": phan_loai,
        "chi_tiet": chi_tiet,
    }


# ---------------------------------------------------------------------------
# Hàm 8: Tổng hợp module 3 (hàm giao tiếp chính)
# ---------------------------------------------------------------------------

def tom_tat_module3(ma_cp: str) -> dict:
    """
    Hàm giao tiếp chính — gọi module1, tính 6 chỉ số, chấm điểm.

    Returns
    -------
    dict
        {
          "chi_so": {"ROE": ..., "ROA": ..., "EPS": ..., "PE": ..., "PB": ..., "DE": ...},
          "cham_diem": {"tong": ..., "phan_loai": ..., "ROE": ..., ...},
        }
    """
    bao_cao_tc = m1.lay_bao_cao_tai_chinh(ma_cp)
    thong_tin = m1.lay_thong_tin_co_phieu(ma_cp)
    gia_hien_tai = thong_tin.get("gia_hien_tai", 0.0)

    # Nếu không lấy được BCTC → trả về None cho mọi chỉ số
    if not bao_cao_tc:
        print(f"[tom_tat_module3] Khong lay duoc BCTC cho {ma_cp}")
        return {
            "chi_so": {"ROE": None, "ROA": None, "EPS": None, "PE": None, "PB": None, "DE": None},
            "cham_diem": {"tong": 0, "phan_loai": "N/A", "ROE": 0, "ROA": 0, "EPS": 0, "PE": 0, "PB": 0, "DE": 0},
        }

    roe = tinh_roe(bao_cao_tc)
    roa = tinh_roa(bao_cao_tc)
    eps = tinh_eps(bao_cao_tc)
    pe  = tinh_pe(gia_hien_tai, eps)
    pb  = tinh_pb(gia_hien_tai, bao_cao_tc)
    de  = tinh_de(bao_cao_tc)

    chi_so = {"roe": roe, "roa": roa, "eps": eps, "pe": pe, "pb": pb, "de": de}
    ket_qua = cham_diem_doanh_nghiep(chi_so)

    return {
        "chi_so": {
            "ROE": roe,
            "ROA": roa,
            "EPS": eps,
            "PE":  pe,
            "PB":  pb,
            "DE":  de,
        },
        "cham_diem": {
            **ket_qua["chi_tiet"],
            "tong": ket_qua["diem_tong"],
            "phan_loai": ket_qua["phan_loai"],
        },
    }
