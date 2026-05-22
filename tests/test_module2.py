import pytest
import pandas as pd
import numpy as np
import json
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from modules.module2_kythuat import (
    tinh_ma, tao_tin_hieu_ma, tinh_rsi,
    tinh_macd, tinh_bollinger, tao_tin_hieu_chung, tom_tat_module2,
)

# ============================================================
# FIXTURES
# ============================================================
@pytest.fixture
def df_250_ngay():
    np.random.seed(42)
    close = 67.5 + np.cumsum(np.random.randn(250) * 0.5)
    return pd.DataFrame({'date': pd.date_range('2024-01-01', periods=250), 'close': close})

@pytest.fixture
def df_30_ngay():
    np.random.seed(1)
    close = 50.0 + np.cumsum(np.random.randn(30) * 0.3)
    return pd.DataFrame({'date': pd.date_range('2024-01-01', periods=30), 'close': close})

@pytest.fixture
def df_chi_tang():
    return pd.DataFrame({'close': [float(i) for i in range(50, 100)]})

@pytest.fixture
def df_chi_giam():
    return pd.DataFrame({'close': [float(i) for i in range(100, 50, -1)]})

@pytest.fixture
def df_gia_tang_manh():
    np.random.seed(99)
    trend = np.linspace(30, 80, 250)
    noise = np.random.randn(250) * 0.3
    return pd.DataFrame({'close': trend + noise})


# ============================================================
# NHÓM 1: tinh_ma()
# ============================================================
class TestTinhMA:
    def test_tra_ve_series(self, df_250_ngay):
        assert isinstance(tinh_ma(df_250_ngay, 20), pd.Series)

    def test_do_dai_bang_input(self, df_250_ngay):
        assert len(tinh_ma(df_250_ngay, 20)) == len(df_250_ngay)

    def test_19_dong_dau_nan(self, df_250_ngay):
        assert tinh_ma(df_250_ngay, 20).iloc[:19].isna().all()

    def test_tu_dong_20_co_gia_tri(self, df_250_ngay):
        assert tinh_ma(df_250_ngay, 20).iloc[19:].notna().all()

    def test_tinh_dung_thu_cong(self):
        df = pd.DataFrame({'close': [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]})
        result = tinh_ma(df, 5)
        assert result.iloc[4] == pytest.approx(30.0)
        assert result.iloc[9] == pytest.approx(80.0)

    def test_ma200_nan_khi_thieu_data(self, df_30_ngay):
        assert tinh_ma(df_30_ngay, 200).isna().all()

    def test_nhieu_period(self, df_250_ngay):
        for p in [5, 10, 20, 50, 200]:
            r = tinh_ma(df_250_ngay, p)
            assert isinstance(r, pd.Series) and len(r) == len(df_250_ngay)

    def test_ten_series_dung_format(self, df_250_ngay):
        """Series phải có .name = 'MA{period}' theo lộ trình."""
        assert tinh_ma(df_250_ngay, 20).name  == "MA20"
        assert tinh_ma(df_250_ngay, 50).name  == "MA50"
        assert tinh_ma(df_250_ngay, 200).name == "MA200"


# ============================================================
# NHÓM 2: tao_tin_hieu_ma()  ← SỬA THEO LOGIC ĐẾM ĐIỂM
# ============================================================
class TestTaoTinHieuMA:
    def test_tra_ve_dict(self, df_250_ngay):
        """Lộ trình: trả về dict, không phải str."""
        result = tao_tin_hieu_ma(df_250_ngay)
        assert isinstance(result, dict)

    def test_co_du_4_key(self, df_250_ngay):
        """Dict phải có: tin_hieu, diem, ma20, ma50."""
        result = tao_tin_hieu_ma(df_250_ngay)
        assert 'tin_hieu' in result
        assert 'diem'     in result
        assert 'ma20'     in result
        assert 'ma50'     in result

    def test_tin_hieu_hop_le(self, df_250_ngay):
        result = tao_tin_hieu_ma(df_250_ngay)
        assert result['tin_hieu'] in ["BÁN", "GIỮ", "MUA", "MUA MẠNH"]

    def test_diem_trong_khoang_0_3(self, df_250_ngay):
        """Hệ thống đếm điểm: 0-3."""
        result = tao_tin_hieu_ma(df_250_ngay)
        assert 0 <= result['diem'] <= 3

    def test_mapping_diem_vs_tin_hieu(self, df_250_ngay):
        """Đúng mapping: 0→BÁN, 1→GIỮ, 2→MUA, 3→MUA MẠNH."""
        result = tao_tin_hieu_ma(df_250_ngay)
        expected = ["BÁN", "GIỮ", "MUA", "MUA MẠNH"][result['diem']]
        assert result['tin_hieu'] == expected

    def test_xu_huong_tang_manh_cho_diem_cao(self, df_gia_tang_manh):
        """Data tăng mạnh → diem >= 2."""
        result = tao_tin_hieu_ma(df_gia_tang_manh)
        assert result['diem'] >= 2

    def test_khong_crash_khi_data_ngan(self, df_30_ngay):
        """Không crash khi MA50/MA200 = NaN (pd.isna check)."""
        result = tao_tin_hieu_ma(df_30_ngay)
        assert 'tin_hieu' in result

    def test_isna_check_hoat_dong(self, df_30_ngay):
        """Khi data < 50 ngày: diem phải <= 1 vì MA50/MA200 bị skip."""
        result = tao_tin_hieu_ma(df_30_ngay)
        assert result['diem'] <= 1


# ============================================================
# NHÓM 3: tinh_rsi()
# ============================================================
class TestTinhRSI:
    def test_tra_ve_series(self, df_250_ngay):
        assert isinstance(tinh_rsi(df_250_ngay), pd.Series)

    def test_khoang_0_100(self, df_250_ngay):
        result = tinh_rsi(df_250_ngay).dropna()
        assert (result >= 0).all() and (result <= 100).all()

    def test_chi_tang_ra_100(self, df_chi_tang):
        assert tinh_rsi(df_chi_tang).iloc[-1] == pytest.approx(100.0)

    def test_chi_giam_ra_0(self, df_chi_giam):
        assert tinh_rsi(df_chi_giam).iloc[-1] == pytest.approx(0.0)

    def test_khong_nan_cuoi(self, df_250_ngay):
        assert not pd.isna(tinh_rsi(df_250_ngay).iloc[-1])

    def test_khong_inf(self, df_chi_tang):
        assert not np.isinf(tinh_rsi(df_chi_tang).iloc[-1])

    def test_period_mac_dinh_14(self, df_250_ngay):
        pd.testing.assert_series_equal(tinh_rsi(df_250_ngay), tinh_rsi(df_250_ngay, period=14))

    def test_replace_zero_khong_gay_inf(self, df_chi_tang):
        """avg_loss=0 được replace(1e-10): toàn bộ series không có inf."""
        series = tinh_rsi(df_chi_tang).dropna()
        assert not series.isin([float('inf'), float('-inf')]).any()
        assert (series <= 100.0).all()


# ============================================================
# NHÓM 4: tinh_macd()
# ============================================================

class TestTinhMACD:
    def test_tra_ve_dict(self, df_250_ngay):
        assert isinstance(tinh_macd(df_250_ngay), dict)

    def test_co_du_3_key(self, df_250_ngay):
        r = tinh_macd(df_250_ngay)
        assert 'macd' in r and 'signal' in r and 'histogram' in r

    def test_moi_key_la_series(self, df_250_ngay):
        r = tinh_macd(df_250_ngay)
        for k in ['macd', 'signal', 'histogram']:
            assert isinstance(r[k], pd.Series)

    def test_histogram_dung_cong_thuc(self, df_250_ngay):
        r = tinh_macd(df_250_ngay)
        pd.testing.assert_series_equal(r['histogram'], r['macd'] - r['signal'])

    def test_khong_nan_cuoi(self, df_250_ngay):
        r = tinh_macd(df_250_ngay)
        for k in ['macd', 'signal', 'histogram']:
            assert not pd.isna(r[k].iloc[-1])

    def test_do_dai_bang_input(self, df_250_ngay):
        r = tinh_macd(df_250_ngay)
        for k in ['macd', 'signal', 'histogram']:
            assert len(r[k]) == len(df_250_ngay)

# ============================================================
# NHÓM 5: tinh_bollinger()
# ============================================================

class TestTinhBollinger:
    def test_tra_ve_dict(self, df_250_ngay):
        assert isinstance(tinh_bollinger(df_250_ngay), dict)

    def test_co_du_3_key(self, df_250_ngay):
        r = tinh_bollinger(df_250_ngay)
        assert 'upper' in r and 'middle' in r and 'lower' in r

    def test_upper_lon_hon_lower(self, df_250_ngay):
        r = tinh_bollinger(df_250_ngay)
        valid = ~r['upper'].isna()
        assert (r['upper'][valid] >= r['lower'][valid]).all()

    def test_middle_nam_giua(self, df_250_ngay):
        r = tinh_bollinger(df_250_ngay)
        valid = ~r['middle'].isna()
        assert (r['middle'][valid] <= r['upper'][valid]).all()
        assert (r['middle'][valid] >= r['lower'][valid]).all()

    def test_middle_bang_ma20(self, df_250_ngay):
        bb = tinh_bollinger(df_250_ngay, period=20)
        ma20 = tinh_ma(df_250_ngay, 20)
        pd.testing.assert_series_equal(bb['middle'], ma20, check_names=False)

    def test_tuy_chinh_period_std(self, df_250_ngay):
        r = tinh_bollinger(df_250_ngay, period=10, std=1)
        assert not pd.isna(r['upper'].iloc[-1])


# ============================================================
# NHÓM 6: tao_tin_hieu_chung()
# ============================================================
class TestTaoTinHieuChung:
    def test_tra_ve_dict(self, df_250_ngay):
        assert isinstance(tao_tin_hieu_chung(df_250_ngay), dict)

    def test_co_du_3_key(self, df_250_ngay):
        r = tao_tin_hieu_chung(df_250_ngay)
        assert 'tin_hieu' in r and 'so_tin_hieu_mua' in r and 'giai_thich' in r

    def test_tin_hieu_hop_le(self, df_250_ngay):
        assert tao_tin_hieu_chung(df_250_ngay)['tin_hieu'] in ["MUA MẠNH", "MUA", "GIỮ", "BÁN"]

    def test_so_mua_khoang_0_4(self, df_250_ngay):
        assert 0 <= tao_tin_hieu_chung(df_250_ngay)['so_tin_hieu_mua'] <= 4

    def test_mapping_so_mua_vs_tin_hieu(self, df_250_ngay):
        r = tao_tin_hieu_chung(df_250_ngay)
        so, tin = r['so_tin_hieu_mua'], r['tin_hieu']
        expected = {3: "MUA MẠNH", 2: "MUA", 1: "GIỮ", 0: "BÁN"}
        assert tin == expected.get(min(so, 3) if so >= 3 else so)

    def test_giai_thich_khong_rong(self, df_250_ngay):
        r = tao_tin_hieu_chung(df_250_ngay)
        assert isinstance(r['giai_thich'], str) and len(r['giai_thich']) > 0

    def test_tang_manh_cho_tin_hieu_mua(self, df_gia_tang_manh):
        assert tao_tin_hieu_chung(df_gia_tang_manh)['tin_hieu'] in ["MUA", "MUA MẠNH"]

    def test_df_ngan_khong_crash(self, df_30_ngay):
        assert 'tin_hieu' in tao_tin_hieu_chung(df_30_ngay)

# ============================================================
# NHÓM 7: tom_tat_module2() 
# ============================================================
class TestTomTatModule2:
    def test_tra_ve_dict(self, df_250_ngay):
        assert isinstance(tom_tat_module2(df_250_ngay), dict)

    def test_co_du_key_gia_tri_moi_nhat(self, df_250_ngay):
        """Kiểm tra các key giá trị mới nhất (bước 72)."""
        r = tom_tat_module2(df_250_ngay)
        for key in ['rsi', 'macd', 'signal', 'histogram',
                    'ma20', 'ma50', 'ma200',
                    'bollinger_upper', 'bollinger_middle', 'bollinger_lower',
                    'tin_hieu', 'so_tin_hieu_mua', 'giai_thich']:
            assert key in r, f"Thiếu key: {key}"

    def test_co_du_key_series_cho_chart(self, df_250_ngay):
        """Kiểm tra các key series để vẽ chart (bước 74)."""
        r = tom_tat_module2(df_250_ngay)
        for key in ['rsi_series', 'macd_series', 'signal_series',
                    'bollinger_upper_series', 'bollinger_middle_series',
                    'bollinger_lower_series']:
            assert key in r, f"Thiếu series key: {key}"

    def test_74_rsi_series_la_list(self, df_250_ngay):
        assert isinstance(tom_tat_module2(df_250_ngay)['rsi_series'], list)

    def test_74_macd_series_la_list(self, df_250_ngay):
        assert isinstance(tom_tat_module2(df_250_ngay)['macd_series'], list)

    def test_74_signal_series_la_list(self, df_250_ngay):
        assert isinstance(tom_tat_module2(df_250_ngay)['signal_series'], list)

    def test_74_bollinger_series_la_list(self, df_250_ngay):
        r = tom_tat_module2(df_250_ngay)
        assert isinstance(r['bollinger_upper_series'], list)
        assert isinstance(r['bollinger_middle_series'], list)
        assert isinstance(r['bollinger_lower_series'], list)

    def test_74_series_khong_chua_nan(self, df_250_ngay):
        """Sau dropna().tolist() không được có NaN."""
        r = tom_tat_module2(df_250_ngay)
        for key in ['rsi_series', 'macd_series', 'signal_series']:
            assert all(not pd.isna(v) for v in r[key]), f"{key} chứa NaN"

    def test_74_rsi_series_khoang_hop_le(self, df_250_ngay):
        for v in tom_tat_module2(df_250_ngay)['rsi_series']:
            assert 0 <= v <= 100


    def test_72_rsi_la_float_trong_khoang(self, df_250_ngay):
        r = tom_tat_module2(df_250_ngay)
        assert isinstance(r['rsi'], float)
        assert 0 <= r['rsi'] <= 100

    def test_72_ma20_khong_none_khi_du_data(self, df_250_ngay):
        assert tom_tat_module2(df_250_ngay)['ma20'] is not None

    def test_72_ma200_none_khi_thieu_data(self, df_30_ngay):
        assert tom_tat_module2(df_30_ngay)['ma200'] is None

    def test_72_ma50_none_khi_thieu_data(self, df_30_ngay):
        assert tom_tat_module2(df_30_ngay)['ma50'] is None

    # --- JSON serializable (quan trọng cho Flask) ---

    def test_json_serializable(self, df_250_ngay):
        """Toàn bộ output phải json.dumps được — không có np.float64."""
        try:
            json.dumps(tom_tat_module2(df_250_ngay))
        except TypeError as e:
            pytest.fail(f"json.dumps thất bại: {e}")

    # --- Các kiểm tra khác ---

    def test_lam_tron_2_chu_so(self, df_250_ngay):
        r = tom_tat_module2(df_250_ngay)
        if r['ma20'] is not None:
            assert r['ma20'] == round(r['ma20'], 2)
        assert r['rsi'] == round(r['rsi'], 2)

    def test_tin_hieu_hop_le(self, df_250_ngay):
        assert tom_tat_module2(df_250_ngay)['tin_hieu'] in ["MUA MẠNH", "MUA", "GIỮ", "BÁN"]

    def test_so_tin_hieu_mua_la_int(self, df_250_ngay):
        assert isinstance(tom_tat_module2(df_250_ngay)['so_tin_hieu_mua'], int)

    def test_nhat_quan_khi_goi_nhieu_lan(self, df_250_ngay):
        r1 = tom_tat_module2(df_250_ngay)
        r2 = tom_tat_module2(df_250_ngay)
        assert r1['rsi'] == r2['rsi']
        assert r1['tin_hieu'] == r2['tin_hieu']
        assert r1['ma20'] == r2['ma20']

    def test_khong_crash_khi_df_ngan(self, df_30_ngay):
        assert 'tin_hieu' in tom_tat_module2(df_30_ngay)