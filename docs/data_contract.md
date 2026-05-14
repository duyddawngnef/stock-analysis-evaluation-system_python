# Data Contract

Canonical specification for all module function signatures and return structures.
The frontend was built against this contract using `fake_data.py`.
When integrating real modules, they **must** return the exact same structure — no UI changes should be needed.

---

## Module 1 — Thu thập dữ liệu (`module1_thudulieu.py`)

### `lay_thong_tin_co_phieu(ma_cp: str) -> dict`

```python
{
    "ma": str,                    # e.g. "VNM"
    "ten_cong_ty": str,           # full Vietnamese company name
    "nganh": str,                 # sector/industry
    "san": str,                   # "HOSE" | "HNX" | "UPCOM"
    "gia_hien_tai": float,        # current price (VND, đồng)
    "thay_doi_phan_tram": float,  # % change from previous session
    "khoi_luong": int,            # trading volume (shares)
    "von_hoa": float,             # market cap (tỷ đồng)
}
```

### `lay_gia_lich_su(ma_cp, ngay_bat_dau, ngay_ket_thuc) -> pd.DataFrame`

| Column   | Type        | Notes                        |
| -------- | ----------- | ---------------------------- |
| date     | datetime64  | business days only           |
| open     | float       | VND (đồng)                   |
| high     | float       | VND (đồng)                   |
| low      | float       | VND (đồng)                   |
| close    | float       | VND (đồng)                   |
| volume   | int         | shares traded                |

Sorted **ascending** by `date` (oldest row first). No NaN in any column.

### `lay_bao_cao_tai_chinh(ma_cp: str) -> dict`

```python
{
    "bang_can_doi_ke_toan": pd.DataFrame,  # balance sheet
    "kqkd": pd.DataFrame,                  # income statement
    "luu_chuyen_tien_te": pd.DataFrame,    # cash flow statement
}
```

Each DataFrame: **rows** = indicator names (Vietnamese string), **columns** = reporting periods (`"Q4/2023"`, `"Q3/2023"`, …). Newest period is `iloc[:, 0]`. Values in VND (đồng).

**Required rows:**

- `kqkd`: `"Lợi nhuận sau thuế"`
- `bang_can_doi_ke_toan`: `"Tổng tài sản"`, `"Tổng nợ phải trả"`, `"Vốn chủ sở hữu"`, `"Số cổ phiếu lưu hành"`

### `lay_du_lieu_so_sanh(danh_sach_ma: list) -> dict`

```python
{ma_cp: pd.DataFrame, ...}
# each DataFrame has the same structure as lay_gia_lich_su()
```

---

## Module 2 — Phân tích kỹ thuật (`module2_kythuat.py`)

### `tom_tat_module2(df_gia: pd.DataFrame) -> dict`

```python
{
    "ma": {
        "MA20": float | None,   # None if fewer than 20 rows
        "MA50": float | None,
        "MA200": float | None,
    },
    "rsi": float,               # 0–100, period=14
    "macd": {
        "macd": float,          # EMA12 - EMA26
        "signal": float,        # EMA9 of macd
        "histogram": float,     # macd - signal
    },
    "bollinger": {
        "upper": float,         # MA20 + 2σ
        "middle": float,        # MA20
        "lower": float,         # MA20 - 2σ
    },
    "tin_hieu": str,            # "MUA MẠNH" | "MUA" | "GIỮ" | "BÁN"
    "so_tin_hieu_mua": int,     # 0–4 (count of bullish signals)
    "giai_thich": str,          # human-readable explanation
}
```

**Signal thresholds (module2 internal):**

| Indicator      | Buy signal                         | Sell signal                        |
| -------------- | ---------------------------------- | ---------------------------------- |
| MA             | price > MA20 > MA50 > MA200        | price < MA20                       |
| RSI (period=14)| RSI < 30 (oversold)                | RSI > 70 (overbought)              |
| MACD           | MACD crosses above Signal          | MACD crosses below Signal          |
| Bollinger      | price touches lower band           | price touches upper band           |

`tin_hieu` mapping: `so_tin_hieu_mua >= 3` → "MUA MẠNH", `== 2` → "MUA", `== 1` → "GIỮ", `== 0` → "BÁN".

---

## Module 3 — Phân tích cơ bản (`module3_coban.py`)

### `tom_tat_module3(ma_cp: str) -> dict`

```python
{
    "chi_so": {
        "ROE": float,   # % (Net profit / Equity × 100)
        "ROA": float,   # % (Net profit / Total assets × 100)
        "EPS": float,   # VND/share (Net profit / Shares outstanding)
        "PE":  float,   # Price / EPS
        "PB":  float,   # Price / (Equity / Shares outstanding)
        "DE":  float,   # Total liabilities / Equity
    },
    "cham_diem": {
        "ROE": int,         # 0–2
        "ROA": int,         # 0–2
        "EPS": int,         # 0–2
        "PE":  int,         # 0–2
        "PB":  int,         # 0–2
        "DE":  int,         # 0–2
        "tong": int,        # 0–12
        "phan_loai": str,   # "TỐT" | "KHÁ" | "YẾU"
    },
}
```

**Scoring thresholds:**

| Metric | 2 pts      | 1 pt        | 0 pts          |
| ------ | ---------- | ----------- | -------------- |
| ROE    | > 20%      | 15–20%      | < 15%          |
| ROA    | > 10%      | 5–10%       | < 5%           |
| EPS    | > 5,000    | 2,000–5,000 | < 2,000        |
| P/E    | 8–15       | 15–20       | > 20 or < 8    |
| P/B    | < 1.5      | 1.5–2.5     | > 2.5          |
| D/E    | < 1        | 1–2         | > 2            |

**Classification:** TỐT (9–12 pts), KHÁ (5–8 pts), YẾU (0–4 pts).

---

## Module Export — Xuất Excel (`routes/export_routes.py`)

### `GET /api/xuat-excel/<ma_cp>`

**Trạng thái:** Stub — trả về 501 Not Implemented.

**Khi triển khai**, module export phải:

1. Gọi `module1.lay_thong_tin_co_phieu(ma_cp)`
2. Gọi `module1.lay_gia_lich_su(ma_cp, ...)`
3. Gọi `module2.tom_tat_module2(df_gia)`
4. Gọi `module3.tom_tat_module3(ma_cp)`
5. Tạo file Excel với openpyxl — 4 sheets:

| Sheet | Nội dung |
| --- | --- |
| Tổng quan | Thông tin cơ bản, giá hiện tại, volume, market cap |
| Kỹ thuật | MA20/50/200, RSI, MACD, Bollinger, tín hiệu tổng hợp |
| Cơ bản | ROE, ROA, EPS, P/E, P/B, D/E + điểm + phân loại |
| Đánh giá | Nhận xét tổng hợp, khuyến nghị |

**Quy tắc định dạng số trong Excel:**

```python
cell.number_format = '#,##0'      # số nguyên (VND, volume)
cell.number_format = '#,##0.00'   # số thực (%, tỷ lệ)
```

**Output path:** `output/<MA_CP>_<YYYY-MM-DD>.xlsx`

---

## Nguyên tắc tích hợp

1. Đổi import trong `app.py` từ `fake_data` sang module thật — **không chỉnh sửa UI hoặc route**.
2. Nếu phải chỉnh sửa template khi tích hợp → data contract đã bị vi phạm.
3. Kiểm tra bằng cách chạy `pytest vn_stock_analyzer/tests/` sau khi tích hợp.
4. Xem `docs/BUGS.md` để biết các pitfall phổ biến với vnstock.
