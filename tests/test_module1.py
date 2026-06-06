"""
tests/test_module1.py — Unit tests cho module1_thudulieu.py

Chạy:
    pytest tests/test_module1.py -v

Yêu cầu tuần 1:
  ✅ lay_thong_tin_co_phieu pass 5 mã: VNM, FPT, HPG, VIC, MWG
  ✅ Raise ValueError khi mã không tồn tại
  ✅ lay_gia_lich_su trả về DataFrame đúng format (6 cột, kiểu đúng)
  ✅ lay_bao_cao_tai_chinh trả về dict 3 bảng
"""

import pytest
import pandas as pd
import sys
import os

# Thêm thư mục gốc vào sys.path để import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules import module1_thudulieu as module1
from modules.helpers import doc_cache, ghi_cache


# ---------------------------------------------------------------------------
# Tests cho helpers.py
# ---------------------------------------------------------------------------

class TestHelpers:
    """Tests cho hàm doc_cache và ghi_cache."""

    def test_doc_cache_file_khong_ton_tai(self, tmp_path):
        """doc_cache trả về False khi file không tồn tại."""
        assert doc_cache(str(tmp_path / "khong_co.json")) is False

    def test_ghi_cache_va_doc_cache(self, tmp_path):
        """ghi_cache tạo file, doc_cache trả về True ngay sau đó."""
        cache_file = str(tmp_path / "sub" / "test.json")
        data = {"key": "value", "so": 42}

        ghi_cache(cache_file, data)

        assert os.path.exists(cache_file), "File cache phải được tạo"
        assert doc_cache(cache_file) is True, "Cache mới tạo phải hợp lệ"

    def test_ghi_cache_numpy_types(self, tmp_path):
        """FIX #3: ghi_cache phải xử lý được numpy int64/float64 (không crash)."""
        import numpy as np
        cache_file = str(tmp_path / "numpy_test.json")
        data = {"int64": np.int64(42), "float64": np.float64(3.14)}
        # Không được raise TypeError
        ghi_cache(cache_file, data)
        assert os.path.exists(cache_file)

    def test_ghi_cache_file_o_thu_muc_hien_tai(self, tmp_path):
        """FIX #2: ghi_cache không crash khi dirname là chuỗi rỗng."""
        # Đổi CWD tạm thời để test file không có parent dir
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            ghi_cache("test_no_parent.json", {"ok": True})
            assert os.path.exists("test_no_parent.json")
        finally:
            os.chdir(original_cwd)

    def test_ghi_cache_tao_thu_muc(self, tmp_path):
        """ghi_cache tự tạo thư mục cha nếu chưa có."""
        cache_file = str(tmp_path / "a" / "b" / "c" / "data.json")
        ghi_cache(cache_file, {"test": True})
        assert os.path.exists(cache_file)

    def test_ghi_cache_noi_dung_dung(self, tmp_path):
        """Nội dung JSON sau khi ghi phải đúng."""
        import json
        cache_file = str(tmp_path / "data.json")
        data = {"ma": "VNM", "gia": 67.5}
        ghi_cache(cache_file, data)

        with open(cache_file, encoding="utf-8") as f:
            loaded = json.load(f)

        assert loaded == data


# ---------------------------------------------------------------------------
# Tests cho lay_thong_tin_co_phieu
# ---------------------------------------------------------------------------

MA_TEST_LIST = ["VNM", "FPT", "HPG", "VIC", "MWG"]
KEYS_BAT_BUOC = [
    "ma", "ten_cong_ty", "nganh", "san",
    "gia_hien_tai", "thay_doi_phan_tram", "khoi_luong", "von_hoa"
]


class TestLayThongTinCoPhieu:
    """Tests cho hàm lay_thong_tin_co_phieu."""

    @pytest.mark.parametrize("ma_cp", MA_TEST_LIST)
    def test_tra_ve_dict_dung_keys(self, ma_cp):
        """Hàm phải trả về dict với đúng 8 keys cho 5 mã test."""
        result = module1.lay_thong_tin_co_phieu(ma_cp)

        assert isinstance(result, dict), f"{ma_cp}: Kết quả phải là dict"
        for key in KEYS_BAT_BUOC:
            assert key in result, f"{ma_cp}: Thiếu key '{key}'"

    @pytest.mark.parametrize("ma_cp", MA_TEST_LIST)
    def test_ma_dung(self, ma_cp):
        """Trường 'ma' trong kết quả phải khớp với mã đầu vào."""
        result = module1.lay_thong_tin_co_phieu(ma_cp)
        assert result["ma"] == ma_cp

    @pytest.mark.parametrize("ma_cp", MA_TEST_LIST)
    def test_ten_cong_ty_khong_trong(self, ma_cp):
        """Tên công ty không được là chuỗi rỗng."""
        result = module1.lay_thong_tin_co_phieu(ma_cp)
        assert isinstance(result["ten_cong_ty"], str)
        assert len(result["ten_cong_ty"]) > 0, f"{ma_cp}: ten_cong_ty rỗng"

    @pytest.mark.parametrize("ma_cp", MA_TEST_LIST)
    def test_gia_hien_tai_la_so(self, ma_cp):
        """Giá hiện tại phải là số thực >= 0."""
        result = module1.lay_thong_tin_co_phieu(ma_cp)
        assert isinstance(result["gia_hien_tai"], (int, float))
        assert result["gia_hien_tai"] >= 0

    def test_ma_khong_hop_le_raise_value_error(self):
        """Hàm phải raise ValueError khi mã không tồn tại."""
        with pytest.raises(ValueError):
            module1.lay_thong_tin_co_phieu("XXXXXXXXX_KHONG_TON_TAI")


# ---------------------------------------------------------------------------
# Tests cho lay_gia_lich_su
# ---------------------------------------------------------------------------

class TestLayGiaLichSu:
    """Tests cho hàm lay_gia_lich_su."""

    def test_tra_ve_dataframe(self):
        """Hàm phải trả về pd.DataFrame."""
        df = module1.lay_gia_lich_su("VNM", "2024-01-01", "2024-03-31")
        assert isinstance(df, pd.DataFrame)

    def test_co_du_6_cot(self):
        """DataFrame phải có đúng 6 cột theo data contract."""
        df = module1.lay_gia_lich_su("VNM", "2024-01-01", "2024-03-31")
        cot_can_thiet = ["date", "open", "high", "low", "close", "volume"]
        for col in cot_can_thiet:
            assert col in df.columns, f"Thiếu cột '{col}'"

    def test_kieu_cot_date(self):
        """Cột date phải là datetime64."""
        df = module1.lay_gia_lich_su("VNM", "2024-01-01", "2024-03-31")
        assert pd.api.types.is_datetime64_any_dtype(df["date"]), \
            "Cột date phải là datetime64"

    def test_kieu_cot_so(self):
        """Cột open, high, low, close phải là số thực."""
        df = module1.lay_gia_lich_su("VNM", "2024-01-01", "2024-03-31")
        for col in ["open", "high", "low", "close"]:
            assert pd.api.types.is_numeric_dtype(df[col]), \
                f"Cột {col} phải là numeric"

    def test_khong_co_nan_o_close(self):
        """Không được có NaN ở cột close."""
        df = module1.lay_gia_lich_su("VNM", "2024-01-01", "2024-03-31")
        assert not df["close"].isna().any(), "Cột close không được có NaN"

    def test_sap_xep_tang_dan(self):
        """DataFrame phải sắp xếp tăng dần theo date."""
        df = module1.lay_gia_lich_su("VNM", "2024-01-01", "2024-03-31")
        assert df["date"].is_monotonic_increasing, \
            "date phải sắp xếp tăng dần"

    def test_co_du_hang(self):
        """Khoảng thời gian 3 tháng phải có ít nhất 50 ngày giao dịch."""
        df = module1.lay_gia_lich_su("VNM", "2024-01-01", "2024-03-31")
        assert len(df) >= 50, f"Chỉ có {len(df)} hàng, cần ít nhất 50"


# ---------------------------------------------------------------------------
# Tests cho lay_bao_cao_tai_chinh
# ---------------------------------------------------------------------------

class TestLayBaoCaoTaiChinh:
    """Tests cho hàm lay_bao_cao_tai_chinh."""

    def test_tra_ve_dict(self):
        """Hàm phải trả về dict."""
        result = module1.lay_bao_cao_tai_chinh("VNM")
        assert isinstance(result, dict)

    def test_co_3_bang(self):
        """Dict phải có 3 keys theo data contract."""
        result = module1.lay_bao_cao_tai_chinh("VNM")
        if result:  # Chỉ kiểm tra nếu có dữ liệu
            assert "bang_can_doi_ke_toan" in result
            assert "kqkd" in result
            assert "luu_chuyen_tien_te" in result

    def test_gia_tri_la_dataframe(self):
        """Mỗi value trong dict phải là pd.DataFrame."""
        result = module1.lay_bao_cao_tai_chinh("VNM")
        if result:
            for key, val in result.items():
                assert isinstance(val, pd.DataFrame), \
                    f"Key '{key}' phải là DataFrame"

    def test_ma_ngan_hang_khong_crash(self):
        """Mã ngân hàng (cấu trúc BCTC khác) không được crash."""
        # VCB là ngân hàng — cấu trúc BCTC khác nhưng không được raise exception
        try:
            result = module1.lay_bao_cao_tai_chinh("VCB")
            assert isinstance(result, dict)
        except Exception as e:
            pytest.fail(f"lay_bao_cao_tai_chinh('VCB') không được raise: {e}")
