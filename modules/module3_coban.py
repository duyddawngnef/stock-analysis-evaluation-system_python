"""
Module 3: Phân tích cơ bản
- Tính toán các chỉ số tài chính: ROE, ROA, EPS, P/E, P/B, D/E
- Chấm điểm doanh nghiệp dựa trên các chỉ số
- Trả về kết quả theo data contract đã định nghĩa
"""
import pandas as pd
from modules.module1_thudulieu import lay_bao_cao_tai_chinh, lay_thong_tin_co_phieu
from modules.helpers import format_so_tien, format_phan_tram


def tinh_roe(bao_cao_tc: dict) -> float:
    """Tính ROE = Lợi nhuận sau thuế / Vốn chủ sở hữu * 100%"""
    try:
        kqkd = bao_cao_tc['kqkd']
        bcdk = bao_cao_tc['bang_can_doi_ke_toan']
        
        loi_nhuan = kqkd.loc['Lợi nhuận sau thuế'].iloc[0]
        von_chu = bcdk.loc['Vốn chủ sở hữu'].iloc[0]
        
        if von_chu == 0:
            return 0.0
        roe = (loi_nhuan / von_chu) * 100
        return round(roe, 2)
    except (KeyError, IndexError, ZeroDivisionError):
        return 0.0


def tinh_roa(bao_cao_tc: dict) -> float:
    """Tính ROA = Lợi nhuận sau thuế / Tổng tài sản * 100%"""
    try:
        kqkd = bao_cao_tc['kqkd']
        bcdk = bao_cao_tc['bang_can_doi_ke_toan']
        
        loi_nhuan = kqkd.loc['Lợi nhuận sau thuế'].iloc[0]
        tong_ts = bcdk.loc['Tổng tài sản'].iloc[0]
        
        if tong_ts == 0:
            return 0.0
        roa = (loi_nhuan / tong_ts) * 100
        return round(roa, 2)
    except (KeyError, IndexError, ZeroDivisionError):
        return 0.0


def tinh_eps(bao_cao_tc: dict) -> float:
    """Tính EPS = Lợi nhuận sau thuế / Số cổ phiếu lưu hành"""
    try:
        kqkd = bao_cao_tc['kqkd']
        bcdk = bao_cao_tc['bang_can_doi_ke_toan']
        
        loi_nhuan = kqkd.loc['Lợi nhuận sau thuế'].iloc[0]
        so_cp = bcdk.loc['Số cổ phiếu lưu hành'].iloc[0]
        
        if so_cp == 0:
            return 0.0
        eps = loi_nhuan / so_cp
        return round(eps, 2)
    except (KeyError, IndexError, ZeroDivisionError):
        return 0.0


def tinh_pe(gia_hien_tai: float, eps: float) -> float:
    """Tính P/E = Giá hiện tại / EPS"""
    if eps <= 0:
        return 0.0
    return round(gia_hien_tai / eps, 2)


def tinh_pb(gia_hien_tai: float, bao_cao_tc: dict) -> float:
    """Tính P/B = Giá hiện tại / (Vốn chủ sở hữu / Số CP lưu hành)"""
    try:
        bcdk = bao_cao_tc['bang_can_doi_ke_toan']
        von_chu = bcdk.loc['Vốn chủ sở hữu'].iloc[0]
        so_cp = bcdk.loc['Số cổ phiếu lưu hành'].iloc[0]
        
        if so_cp == 0:
            return 0.0
        book_value = von_chu / so_cp
        if book_value == 0:
            return 0.0
        pb = gia_hien_tai / book_value
        return round(pb, 2)
    except (KeyError, IndexError, ZeroDivisionError):
        return 0.0


def tinh_de(bao_cao_tc: dict) -> float:
    """Tính D/E = Tổng nợ phải trả / Vốn chủ sở hữu"""
    try:
        bcdk = bao_cao_tc['bang_can_doi_ke_toan']
        tong_no = bcdk.loc['Tổng nợ phải trả'].iloc[0]
        von_chu = bcdk.loc['Vốn chủ sở hữu'].iloc[0]
        
        if von_chu == 0:
            return 0.0
        de = tong_no / von_chu
        return round(de, 2)
    except (KeyError, IndexError, ZeroDivisionError):
        return 0.0


def cham_diem_doanh_nghiep(chi_so: dict) -> dict:
    """Chấm điểm 0-2 cho từng chỉ số và tổng hợp phân loại"""
    diem = {}
    
    # ROE
    roe = chi_so['ROE']
    diem['ROE'] = 2 if roe > 20 else 1 if roe >= 15 else 0
    
    # ROA
    roa = chi_so['ROA']
    diem['ROA'] = 2 if roa > 10 else 1 if roa >= 5 else 0
    
    # EPS
    eps = chi_so['EPS']
    diem['EPS'] = 2 if eps > 5000 else 1 if eps >= 2000 else 0
    
    # P/E
    pe = chi_so['PE']
    diem['PE'] = 2 if 8 <= pe <= 15 else 1 if 15 < pe <= 20 else 0
    
    # P/B
    pb = chi_so['PB']
    diem['PB'] = 2 if pb < 1.5 else 1 if pb <= 2.5 else 0
    
    # D/E
    de = chi_so['DE']
    diem['DE'] = 2 if de < 1 else 1 if de <= 2 else 0
    
    tong_diem = sum(diem.values())
    
    if tong_diem >= 9:
        phan_loai = "TỐT"
    elif tong_diem >= 5:
        phan_loai = "KHÁ"
    else:
        phan_loai = "YẾU"
    
    return {
        **diem,
        "tong": tong_diem,
        "phan_loai": phan_loai
    }


def tom_tat_module3(ma_cp: str) -> dict:
    """
    Hàm tổng hợp Module 3 - Đây là hàm TV4 sẽ gọi từ routes.
    Trả về đúng cấu trúc data contract.
    """
    try:
        # Lấy thông tin + báo cáo tài chính
        thong_tin = lay_thong_tin_co_phieu(ma_cp)
        bao_cao_tc = lay_bao_cao_tai_chinh(ma_cp)
        
        gia_hien_tai = thong_tin.get('gia_hien_tai', 0)
        
        # Tính các chỉ số
        chi_so = {
            "ROE": tinh_roe(bao_cao_tc),
            "ROA": tinh_roa(bao_cao_tc),
            "EPS": tinh_eps(bao_cao_tc),
            "PE": tinh_pe(gia_hien_tai, tinh_eps(bao_cao_tc)),
            "PB": tinh_pb(gia_hien_tai, bao_cao_tc),
            "DE": tinh_de(bao_cao_tc)
        }
        
        # Chấm điểm
        cham_diem = cham_diem_doanh_nghiep(chi_so)
        
        return {
            "chi_so": chi_so,
            "cham_diem": cham_diem
        }
        
    except Exception as e:
        # Trả về giá trị mặc định khi lỗi (để frontend không crash)
        return {
            "chi_so": {"ROE": 0, "ROA": 0, "EPS": 0, "PE": 0, "PB": 0, "DE": 0},
            "cham_diem": {
                "ROE": 0, "ROA": 0, "EPS": 0, "PE": 0, "PB": 0, "DE": 0,
                "tong": 0, "phan_loai": "YẾU"
            },
            "error": str(e)
        }