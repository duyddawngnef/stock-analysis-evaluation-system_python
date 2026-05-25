"""
Test cho Module 3 — Phân tích cơ bản
Người phụ trách: TV3
"""

import pytest
import pandas as pd
from modules.module3_coban import (
    tinh_roe, tinh_roa, tinh_eps, tinh_pe, tinh_pb, tinh_de,
    cham_diem_doanh_nghiep, tom_tat_module3
)


# ====================== FIXTURE DỮ LIỆU MẪU ======================
@pytest.fixture
def bao_cao_tc_mau():
    """Tạo báo cáo tài chính mẫu để test"""
    return {
        'kqkd': pd.DataFrame({
            'Lợi nhuận sau thuế': [8500000000000, 7200000000000]
        }),
        'bang_can_doi_ke_toan': pd.DataFrame({
            'Tổng tài sản': [45000000000000, 42000000000000],
            'Vốn chủ sở hữu': [32000000000000, 30000000000000],
            'Số cổ phiếu lưu hành': [2090000000, 2090000000],
            'Tổng nợ phải trả': [13000000000000, 12000000000000]
        })
    }


# ====================== TEST CÁC HÀM TÍNH CHỈ SỐ ======================

def test_tinh_roe(bao_cao_tc_mau):
    roe = tinh_roe(bao_cao_tc_mau)
    assert isinstance(roe, float)
    assert roe > 0
    assert roe == 26.56  # 8500 / 32000 * 100


def test_tinh_roa(bao_cao_tc_mau):
    roa = tinh_roa(bao_cao_tc_mau)
    assert isinstance(roa, float)
    assert roa > 0
    assert roa == 18.89  # 8500 / 45000 * 100


def test_tinh_eps(bao_cao_tc_mau):
    eps = tinh_eps(bao_cao_tc_mau)
    assert isinstance(eps, float)
    assert eps > 0
    assert eps == 4066.99  # 8.5 nghìn tỷ / 2.09 tỷ CP


def test_tinh_pe():
    pe = tinh_pe(67500, 4066.99)
    assert isinstance(pe, float)
    assert pe > 0
    assert round(pe, 2) == 16.6


def test_tinh_pb(bao_cao_tc_mau):
    pb = tinh_pb(67500, bao_cao_tc_mau)
    assert isinstance(pb, float)
    assert pb > 0


def test_tinh_de(bao_cao_tc_mau):
    de = tinh_de(bao_cao_tc_mau)
    assert isinstance(de, float)
    assert de > 0
    assert de == 0.41


# ====================== TEST HÀM CHẤM ĐIỂM ======================

def test_cham_diem_doanh_nghiep():
    chi_so = {
        "ROE": 25.5,
        "ROA": 12.0,
        "EPS": 4500,
        "PE": 14.5,
        "PB": 1.2,
        "DE": 0.8
    }
    
    ket_qua = cham_diem_doanh_nghiep(chi_so)
    
    assert ket_qua["tong"] >= 9
    assert ket_qua["phan_loai"] == "TỐT"
    assert all(0 <= v <= 2 for v in list(ket_qua.values())[:6])


# ====================== TEST HÀM TỔNG HỢP ======================

def test_tom_tat_module3():
    ket_qua = tom_tat_module3('VNM')
    
    assert isinstance(ket_qua, dict)
    assert "chi_so" in ket_qua
    assert "cham_diem" in ket_qua
    assert "ma_cp" in ket_qua
    assert ket_qua["ma_cp"] == "VNM"
    
    chi_so = ket_qua["chi_so"]
    assert all(key in chi_so for key in ["ROE", "ROA", "EPS", "PE", "PB", "DE"])


def test_tom_tat_module3_khong_loi():
    """Kiểm tra hàm không bị crash khi chạy"""
    for ma in ["VNM", "FPT", "HPG", "ABCXYZ"]:
        ket_qua = tom_tat_module3(ma)
        assert isinstance(ket_qua, dict)


# ====================== CHẠY TEST ======================
if __name__ == "__main__":
    pytest.main(["-v", __file__])