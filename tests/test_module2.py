import pytest
import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from modules.module2_kythuat import (
    tinh_ma,
    tinh_rsi,
    tinh_macd,
    tinh_bollinger,
    tao_tin_hieu_chung,
    tom_tat_module2,
)


# ============================================================
# FIXTURES — Dữ liệu dùng chung cho nhiều test
# ============================================================

@pytest.fixture
def df_250_ngay():
    """DataFrame 250 ngày — đủ để tính MA200."""
    np.random.seed(42)
    close = 67.5 + np.cumsum(np.random.randn(250) * 0.5)
    return pd.DataFrame({
        'date': pd.date_range('2024-01-01', periods=250),
        'close': close,
    })

@pytest.fixture
def df_30_ngay():
    """DataFrame 30 ngày — thiếu data cho MA50, MA200."""
    np.random.seed(1)
    close = 50.0 + np.cumsum(np.random.randn(30) * 0.3)
    return pd.DataFrame({
        'date': pd.date_range('2024-01-01', periods=30),
        'close': close,
    })

@pytest.fixture
def df_chi_tang():
    """DataFrame giá chỉ tăng đều — avg_loss = 0, RSI phải = 100."""
    return pd.DataFrame({'close': [float(i) for i in range(50, 100)]})

@pytest.fixture
def df_chi_giam():
    """DataFrame giá chỉ giảm đều — avg_gain = 0, RSI phải = 0."""
    return pd.DataFrame({'close': [float(i) for i in range(100, 50, -1)]})

@pytest.fixture
def df_gia_tang_manh():
    """DataFrame xu hướng tăng rõ — để test tín hiệu MUA."""
    np.random.seed(99)
    # Giá tăng đều + nhiễu nhỏ, đảm bảo MA20 > MA50 > MA200
    trend = np.linspace(30, 80, 250)
    noise = np.random.randn(250) * 0.3
    return pd.DataFrame({'close': trend + noise})


# ============================================================
# NHÓM 1: tinh_ma()
# ============================================================
class TestTinhMA:
    def test_ma20_tra_ve_series(self, df_250_ngay):
        """tinh_ma() phải trả về pandas Series."""
        result = tinh_ma(df_250_ngay, 20)
        assert isinstance(result, pd.Series)

    def test_ma20_do_dai_bang_input(self, df_250_ngay):
        """Độ dài output phải bằng độ dài input."""
        result = tinh_ma(df_250_ngay, 20)
        assert len(result) == len(df_250_ngay)

    def test_ma20_19_dong_dau_nan(self, df_250_ngay):
        """19 dòng đầu của MA20 phải là NaN (chưa đủ 20 ngày)."""
        result = tinh_ma(df_250_ngay, 20)
        assert result.iloc[:19].isna().all()

    def test_ma20_tu_dong_thu_20_co_gia_tri(self, df_250_ngay):
        """Từ dòng thứ 20 trở đi phải có giá trị thật."""
        result = tinh_ma(df_250_ngay, 20)
        assert result.iloc[19:].notna().all()

    def test_ma20_tinh_dung_thu_cong(self):
        """Kiểm tra MA5 bằng tay với 10 dòng."""
        close = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        df = pd.DataFrame({'close': close})
        result = tinh_ma(df, 5)
        # MA5 tại vị trí index 4 = (10+20+30+40+50)/5 = 30
        assert result.iloc[4] == pytest.approx(30.0)
        # MA5 tại vị trí index 9 = (60+70+80+90+100)/5 = 80
        assert result.iloc[9] == pytest.approx(80.0)

    def test_ma200_nan_khi_chua_du_data(self, df_30_ngay):
        """MA200 phải toàn NaN khi df chỉ có 30 dòng."""
        result = tinh_ma(df_30_ngay, 200)
        assert result.isna().all()

    def test_ma_cac_period_khac_nhau(self, df_250_ngay):
        """Có thể tính MA với period tùy ý."""
        for period in [5, 10, 20, 50, 200]:
            result = tinh_ma(df_250_ngay, period)
            assert isinstance(result, pd.Series)
            assert len(result) == len(df_250_ngay)

# ============================================================
# NHÓM 2: tinh_rsi()
# ============================================================
class TestTinhRSI:
    def test_rsi_tra_ve_series(self, df_250_ngay):
        """tinh_rsi() phải trả về pandas Series."""
        result = tinh_rsi(df_250_ngay)
        assert isinstance(result, pd.Series)

    def test_rsi_nam_trong_khoang_0_100(self, df_250_ngay):
        """RSI phải nằm trong khoảng [0, 100]."""
        result = tinh_rsi(df_250_ngay).dropna()
        assert (result >= 0).all() and (result <= 100).all()

    def test_rsi_gia_chi_tang_tra_ve_100(self, df_chi_tang):
        """Khi giá chỉ tăng, avg_loss = 0 → RSI phải = 100."""
        result = tinh_rsi(df_chi_tang).iloc[-1]
        assert result == pytest.approx(100.0)

    def test_rsi_gia_chi_giam_tra_ve_0(self, df_chi_giam):
        """Khi giá chỉ giảm, avg_gain = 0 → RSI phải = 0."""
        result = tinh_rsi(df_chi_giam).iloc[-1]
        assert result == pytest.approx(0.0)

    def test_rsi_khong_nan_o_cuoi(self, df_250_ngay):
        """Giá trị RSI cuối cùng không được là NaN."""
        result = tinh_rsi(df_250_ngay).iloc[-1]
        assert not pd.isna(result)

    def test_rsi_khong_inf(self, df_chi_tang):
        """RSI không được là inf dù avg_loss = 0."""
        result = tinh_rsi(df_chi_tang).iloc[-1]
        assert not np.isinf(result)

    def test_rsi_period_mac_dinh_14(self, df_250_ngay):
        """Period mặc định phải là 14."""
        rsi_default = tinh_rsi(df_250_ngay)
        rsi_14 = tinh_rsi(df_250_ngay, period=14)
        pd.testing.assert_series_equal(rsi_default, rsi_14)

# ============================================================
# NHÓM 3: tinh_macd()
# ============================================================
class TestTinhMACD:
    def test_macd_tra_ve_dict(self, df_250_ngay):
        """tinh_macd() phải trả về dict."""
        result = tinh_macd(df_250_ngay)
        assert isinstance(result, dict)

    def test_macd_co_du_3_key(self, df_250_ngay):
        """Dict kết quả phải có đủ 3 key: macd, signal, histogram."""
        result = tinh_macd(df_250_ngay)
        assert 'macd' in result
        assert 'signal' in result
        assert 'histogram' in result

    def test_macd_moi_key_la_series(self, df_250_ngay):
        """Mỗi key trong dict phải là pandas Series."""
        result = tinh_macd(df_250_ngay)
        for key in ['macd', 'signal', 'histogram']:
            assert isinstance(result[key], pd.Series), f"{key} phải là Series"

    def test_histogram_bang_macd_tru_signal(self, df_250_ngay):
        """histogram = macd - signal (luôn đúng theo định nghĩa)."""
        result = tinh_macd(df_250_ngay)
        expected = result['macd'] - result['signal']
        pd.testing.assert_series_equal(result['histogram'], expected)

    def test_macd_khong_nan_o_cuoi(self, df_250_ngay):
        """Giá trị cuối của macd, signal, histogram không được NaN."""
        result = tinh_macd(df_250_ngay)
        assert not pd.isna(result['macd'].iloc[-1])
        assert not pd.isna(result['signal'].iloc[-1])
        assert not pd.isna(result['histogram'].iloc[-1])

    def test_macd_do_dai_bang_input(self, df_250_ngay):
        """Độ dài mỗi Series phải bằng độ dài input."""
        result = tinh_macd(df_250_ngay)
        for key in ['macd', 'signal', 'histogram']:
            assert len(result[key]) == len(df_250_ngay)
            
# ============================================================
# NHÓM 4: tinh_bollinger()
# ============================================================
class TestTinhBollinger:
    def test_bollinger_tra_ve_dict(self, df_250_ngay):
        """tinh_bollinger() phải trả về dict."""
        result = tinh_bollinger(df_250_ngay)
        assert isinstance(result, dict)

    def test_bollinger_co_du_3_key(self, df_250_ngay):
        """Dict phải có đủ 3 key: upper, middle, lower."""
        result = tinh_bollinger(df_250_ngay)
        assert 'upper' in result
        assert 'middle' in result
        assert 'lower' in result

    def test_upper_luon_lon_hon_lower(self, df_250_ngay):
        """upper phải luôn >= lower (sau khi bỏ NaN)."""
        result = tinh_bollinger(df_250_ngay)
        valid = ~result['upper'].isna()
        assert (result['upper'][valid] >= result['lower'][valid]).all()

    def test_middle_nam_giua_upper_va_lower(self, df_250_ngay):
        """middle phải nằm giữa upper và lower."""
        result = tinh_bollinger(df_250_ngay)
        valid = ~result['middle'].isna()
        assert (result['middle'][valid] <= result['upper'][valid]).all()
        assert (result['middle'][valid] >= result['lower'][valid]).all()

    def test_middle_bang_ma20(self, df_250_ngay):
        """middle của Bollinger phải bằng MA20."""
        bb = tinh_bollinger(df_250_ngay, period=20)
        ma20 = tinh_ma(df_250_ngay, 20)
        pd.testing.assert_series_equal(bb['middle'], ma20)

    def test_bollinger_period_va_std_tuy_chinh(self, df_250_ngay):
        """Có thể truyền period và std tùy chỉnh."""
        result = tinh_bollinger(df_250_ngay, period=10, std=1)
        assert isinstance(result, dict)
        assert not pd.isna(result['upper'].iloc[-1])

# ============================================================
# NHÓM 5: tao_tin_hieu_chung()
# ============================================================
class TestTaoTinHieuChung:
    def test_tra_ve_dict(self, df_250_ngay):
        """tao_tin_hieu_chung() phải trả về dict."""
        result = tao_tin_hieu_chung(df_250_ngay)
        assert isinstance(result, dict)

    def test_co_du_3_key(self, df_250_ngay):
        """Dict phải có đủ 3 key bắt buộc."""
        result = tao_tin_hieu_chung(df_250_ngay)
        assert 'tin_hieu' in result
        assert 'so_tin_hieu_mua' in result
        assert 'giai_thich' in result

    def test_tin_hieu_la_chuoi_hop_le(self, df_250_ngay):
        """tin_hieu phải là 1 trong 4 giá trị hợp lệ."""
        result = tao_tin_hieu_chung(df_250_ngay)
        assert result['tin_hieu'] in ["MUA MẠNH", "MUA", "GIỮ", "BÁN"]

    def test_so_tin_hieu_mua_trong_khoang_0_4(self, df_250_ngay):
        """so_tin_hieu_mua phải nằm trong khoảng [0, 4]."""
        result = tao_tin_hieu_chung(df_250_ngay)
        assert 0 <= result['so_tin_hieu_mua'] <= 4

    def test_mapping_so_mua_vs_tin_hieu(self, df_250_ngay):
        """so_tin_hieu_mua phải khớp với tin_hieu theo quy tắc."""
        result = tao_tin_hieu_chung(df_250_ngay)
        so = result['so_tin_hieu_mua']
        tin = result['tin_hieu']
        if so >= 3:
            assert tin == "MUA MẠNH"
        elif so == 2:
            assert tin == "MUA"
        elif so == 1:
            assert tin == "GIỮ"
        else:
            assert tin == "BÁN"

    def test_giai_thich_la_chuoi_khong_rong(self, df_250_ngay):
        """giai_thich phải là chuỗi không rỗng."""
        result = tao_tin_hieu_chung(df_250_ngay)
        assert isinstance(result['giai_thich'], str)
        assert len(result['giai_thich']) > 0

    def test_xu_huong_tang_manh_cho_tin_hieu_mua(self, df_gia_tang_manh):
        """Dữ liệu tăng mạnh phải cho tín hiệu MUA hoặc MUA MẠNH."""
        result = tao_tin_hieu_chung(df_gia_tang_manh)
        assert result['tin_hieu'] in ["MUA", "MUA MẠNH"]

    def test_df_ngan_khong_crash(self, df_30_ngay):
        """Không crash khi df chỉ có 30 ngày (MA50/MA200 = NaN)."""
        result = tao_tin_hieu_chung(df_30_ngay)
        assert 'tin_hieu' in result

# ============================================================
# NHÓM 6: tom_tat_module2() — Hàm chính bàn giao cho TV4
# ============================================================
class TestTomTatModule2:
    def test_tra_ve_dict(self, df_250_ngay):
        """tom_tat_module2() phải trả về dict."""
        result = tom_tat_module2(df_250_ngay)
        assert isinstance(result, dict)

    def test_co_du_cac_key_data_contract(self, df_250_ngay):
        """Phải có đủ các key theo data contract."""
        result = tom_tat_module2(df_250_ngay)
        assert 'ma' in result
        assert 'rsi' in result
        assert 'macd' in result
        assert 'bollinger' in result
        assert 'tin_hieu' in result
        assert 'so_tin_hieu_mua' in result
        assert 'giai_thich' in result

    def test_ma_co_du_3_key(self, df_250_ngay):
        """result['ma'] phải có MA20, MA50, MA200."""
        result = tom_tat_module2(df_250_ngay)
        assert 'MA20' in result['ma']
        assert 'MA50' in result['ma']
        assert 'MA200' in result['ma']

    def test_macd_co_du_3_key(self, df_250_ngay):
        """result['macd'] phải có macd, signal, histogram."""
        result = tom_tat_module2(df_250_ngay)
        assert 'macd' in result['macd']
        assert 'signal' in result['macd']
        assert 'histogram' in result['macd']

    def test_bollinger_co_du_3_key(self, df_250_ngay):
        """result['bollinger'] phải có upper, middle, lower."""
        result = tom_tat_module2(df_250_ngay)
        assert 'upper' in result['bollinger']
        assert 'middle' in result['bollinger']
        assert 'lower' in result['bollinger']

    def test_tat_ca_gia_tri_la_python_native(self, df_250_ngay):
        """Tất cả giá trị số phải là Python float/int, không phải np.float64.
        Lý do: Flask jsonify cần Python native types."""
        import json
        result = tom_tat_module2(df_250_ngay)
        # Nếu có np.float64 thì json.dumps sẽ lỗi trong một số môi trường
        try:
            json.dumps(result)
        except TypeError as e:
            pytest.fail(f"json.dumps thất bại — có thể do np.float64: {e}")

    def test_rsi_la_float_trong_khoang(self, df_250_ngay):
        """RSI trong output phải là float trong [0, 100]."""
        result = tom_tat_module2(df_250_ngay)
        assert isinstance(result['rsi'], float)
        assert 0 <= result['rsi'] <= 100

    def test_ma20_khong_none_khi_du_data(self, df_250_ngay):
        """MA20 không được None khi có đủ 250 ngày."""
        result = tom_tat_module2(df_250_ngay)
        assert result['ma']['MA20'] is not None

    def test_ma200_la_none_khi_thieu_data(self, df_30_ngay):
        """MA200 phải là None khi df chỉ có 30 ngày."""
        result = tom_tat_module2(df_30_ngay)
        assert result['ma']['MA200'] is None

    def test_ma50_la_none_khi_thieu_data(self, df_30_ngay):
        """MA50 phải là None khi df chỉ có 30 ngày."""
        result = tom_tat_module2(df_30_ngay)
        assert result['ma']['MA50'] is None

    def test_lam_tron_2_chu_so_thap_phan(self, df_250_ngay):
        """Các giá trị float phải được làm tròn (không quá nhiều chữ số)."""
        result = tom_tat_module2(df_250_ngay)
        # MA20 làm tròn 2 chữ số
        ma20 = result['ma']['MA20']
        if ma20 is not None:
            assert ma20 == round(ma20, 2)
        # RSI làm tròn 2 chữ số
        assert result['rsi'] == round(result['rsi'], 2)

    def test_tin_hieu_hop_le(self, df_250_ngay):
        """tin_hieu phải là 1 trong 4 giá trị hợp lệ."""
        result = tom_tat_module2(df_250_ngay)
        assert result['tin_hieu'] in ["MUA MẠNH", "MUA", "GIỮ", "BÁN"]

    def test_so_tin_hieu_mua_la_int(self, df_250_ngay):
        """so_tin_hieu_mua phải là int."""
        result = tom_tat_module2(df_250_ngay)
        assert isinstance(result['so_tin_hieu_mua'], int)

    def test_khong_crash_khi_df_ngan(self, df_30_ngay):
        """Không crash khi nhận df ngắn (30 ngày)."""
        result = tom_tat_module2(df_30_ngay)
        assert 'tin_hieu' in result

    def test_ket_qua_nhat_quan_khi_goi_nhieu_lan(self, df_250_ngay):
        """Gọi 2 lần với cùng input phải cho cùng kết quả."""
        result1 = tom_tat_module2(df_250_ngay)
        result2 = tom_tat_module2(df_250_ngay)
        assert result1['rsi'] == result2['rsi']
        assert result1['tin_hieu'] == result2['tin_hieu']
        assert result1['ma']['MA20'] == result2['ma']['MA20']