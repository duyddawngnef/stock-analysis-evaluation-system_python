# -*- coding: utf-8 -*-
"""
config.py — Cấu hình chung cho VN Stock Analyzer.

Chỉnh sửa DANH_SACH_CO_PHIEU để thêm/bớt cổ phiếu cần theo dõi.
Script fetch_all_data.py sẽ pre-fetch và cache toàn bộ danh sách này.
"""

# ---------------------------------------------------------------------------
# Danh sách cổ phiếu mặc định cần pre-fetch và cache
# Thêm/xóa mã tại đây, rồi chạy lại: python fetch_all_data.py
# ---------------------------------------------------------------------------
DANH_SACH_CO_PHIEU = [
    # Ngân hàng
    "VCB", "BID", "CTG", "TCB", "MBB", "VPB", "ACB", "HDB", "STB", "TPB",
    # Bất động sản
    "VIC", "VHM", "NVL", "PDR", "KDH", "DXG", "BCM",
    # Công nghệ
    "FPT", "CMG",
    # Thép & Vật liệu
    "HPG", "HSG", "NKG",
    # Tiêu dùng & Thực phẩm
    "VNM", "SAB", "MSN", "MWG", "PNJ",
    # Dầu khí & Năng lượng
    "GAS", "PLX", "PVD", "PVS",
    # Hàng không & Vận tải
    "HVN", "VJC",
    # Bảo hiểm & Tài chính
    "BVH", "SSI", "VND", "HCM",
    # Sản xuất & Công nghiệp
    "REE", "PHR", "GVR",
]

# ---------------------------------------------------------------------------
# Nguồn dữ liệu vnstock
# ---------------------------------------------------------------------------
VNSTOCK_SOURCE = "VCI"

# ---------------------------------------------------------------------------
# Khoảng thời gian lấy dữ liệu giá lịch sử
# ---------------------------------------------------------------------------
NGAY_BAT_DAU_MAC_DINH = "2022-01-01"

# ---------------------------------------------------------------------------
# Cache TTL (giờ) — đồng bộ với helpers.py
# ---------------------------------------------------------------------------
CACHE_TTL_GIO = 24

# ---------------------------------------------------------------------------
# Thư mục cache
# ---------------------------------------------------------------------------
DIR_GIA       = "data/gia"
DIR_THONG_TIN = "data/thong_tin"
DIR_BAO_CAO   = "data/bao_cao_tc"
