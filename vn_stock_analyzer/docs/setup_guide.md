# Setup Guide

## 1. Install dependencies

```powershell
pip install -r vn_stock_analyzer/requirements.txt
```

## 2. Run with fake data (development mode)

No internet or vnstock account needed. All data comes from `fake_data.py`.

```powershell
python vn_stock_analyzer/app.py
```

Open <http://localhost:5000>.

## 3. Generate / regenerate fake data

```powershell
python vn_stock_analyzer/fake_data.py
```

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

## 5. Run tests

```powershell
# All tests
pytest vn_stock_analyzer/tests/

# One module
pytest vn_stock_analyzer/tests/test_module1.py -v

# Stop on first failure
pytest vn_stock_analyzer/tests/ -x
```

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

## 8. Excel export

The exported file has 4 sheets: **Tổng quan**, **Kỹ thuật**, **Cơ bản**, **Đánh giá**.
Output path: `output/<TICKER>_<date>.xlsx`.
