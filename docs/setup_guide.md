# Setup Guide

## 1. Install dependencies

```powershell
pip install -r vn_stock_analyzer/requirements.txt
```

Dependencies:

| Package   | Version  | Purpose                      |
| --------- | -------- | ---------------------------- |
| flask     | >=3.0.0  | Web framework                |
| pandas    | >=2.0.0  | Data processing              |
| numpy     | >=1.26.0 | Numerical computation        |
| openpyxl  | >=3.1.0  | Excel export (chưa implement)|
| vnstock   | >=3.0.0  | Vietnamese stock data source |

## 2. Run with fake data (development mode)

No internet or vnstock account needed. All data comes from `fake_data.py`.

```powershell
python vn_stock_analyzer/app.py
```

Open <http://localhost:5000>.

Pre-loaded tickers available in fake data: **VNM, FPT, HPG, VIC, MWG, VCB, BID, TCB**

## 3. Generate / regenerate fake data

```powershell
python vn_stock_analyzer/fake_data.py
```

`fake_data.py` implements the full data contract with synthetic but realistic data.
Edit it to add more tickers or adjust the value ranges.

## 4. Switch to real data (integration mode)

In `vn_stock_analyzer/app.py`, change the imports:

```python
# Before (fake data — tuần 1-2)
import fake_data as module1
import fake_data as module2
import fake_data as module3

# After (real modules — tuần 3+)
from modules import module1_thudulieu as module1
from modules import module2_kythuat    as module2
from modules import module3_coban      as module3
```

No UI or route changes are needed if the data contract is respected.
See `docs/data_contract.md` for the canonical function signatures each module must implement.

## 5. Run tests

```powershell
# All tests
pytest vn_stock_analyzer/tests/

# One module
pytest vn_stock_analyzer/tests/test_module1.py -v

# Stop on first failure
pytest vn_stock_analyzer/tests/ -x
```

**Note:** Test files (`test_module1.py`, `test_module2.py`, `test_module3.py`) are currently empty stubs.
Write tests against the data contract in `docs/data_contract.md`.

## 6. Calling vnstock directly

Default source is `'VCI'`. Switch to `'TCBS'` if VCI is unavailable (note: column names and BCTC row names may differ — see `docs/BUGS.md`).

```python
from vnstock import Vnstock

stock = Vnstock().stock(symbol="VNM", source='VCI')

# Price history
df = stock.quote.history(start="2022-01-01", end="2024-12-31")

# Financial reports
balance  = stock.finance.balance_sheet(period='quarter')
income   = stock.finance.income_statement(period='quarter')
cashflow = stock.finance.cash_flow(period='quarter')
```

## 7. Cache

| Data type        | Cache location                     | TTL      |
| ---------------- | ---------------------------------- | -------- |
| Price / OHLCV    | `data/gia/<TICKER>_gia.csv`        | 24 hours |
| Company info     | `data/thong_tin/<TICKER>_info.csv` | 24 hours |
| Financial report | `data/bao_cao_tc/<TICKER>_tc.csv`  | 24 hours |

To force a refresh, delete the corresponding CSV file.
Cache directories (`data/gia/`, `data/thong_tin/`, `data/bao_cao_tc/`) must exist before running in real-data mode.

## 8. Excel export

**Trạng thái hiện tại:** Chưa triển khai — endpoint trả về 501.

Khi đã implement, file xuất ra có 4 sheets: **Tổng quan**, **Kỹ thuật**, **Cơ bản**, **Đánh giá**.
Output path: `output/<TICKER>_<date>.xlsx` (thư mục `output/` phải tồn tại).

## 9. Project structure

```text
vn_stock_analyzer/
├── app.py                   # Flask entry point (port 5000)
├── fake_data.py             # Synthetic data — implements full data contract
├── config.py                # Stub (chưa dùng)
├── requirements.txt
├── modules/
│   ├── module1_thudulieu.py # Data collection stub
│   ├── module2_kythuat.py   # Technical analysis stub
│   ├── module3_coban.py     # Fundamental analysis stub
│   └── helpers.py           # Shared utilities stub
├── routes/
│   ├── trang_routes.py      # Page routes (HTML)
│   ├── api_routes.py        # JSON API endpoints
│   └── export_routes.py     # Excel export (501 stub)
├── templates/
│   ├── base.html
│   ├── trang_chu.html       # Home/search page
│   ├── ket_qua.html         # Analysis results (4 tabs)
│   ├── so_sanh.html         # Comparison page (up to 5 tickers)
│   └── components/          # Reusable partials
├── static/
│   ├── css/style.css        # Design tokens & base styles
│   ├── css/components.css   # UI component styles
│   ├── js/api_client.js     # API wrapper singleton
│   ├── js/charts.js         # Chart.js rendering
│   ├── js/main.js           # Page initialization & event handlers
│   └── fonts/               # Material Icons TTF (local, no CDN)
├── data/
│   ├── gia/                 # OHLCV cache per ticker
│   ├── thong_tin/           # Company info cache
│   └── bao_cao_tc/          # Financial report cache
├── output/                  # Excel export output
├── tests/
│   ├── test_module1.py      # Stub
│   ├── test_module2.py      # Stub
│   └── test_module3.py      # Stub
└── docs/
    ├── api_documentation.md # Full API & route reference
    ├── data_contract.md     # Canonical function signatures
    ├── BUGS.md              # Bug tracker & known pitfalls
    └── setup_guide.md       # This file
```
