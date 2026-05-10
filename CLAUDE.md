# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`vn_stock_analyzer` is a Vietnamese stock market analysis web application built with Flask. It provides technical and fundamental analysis of Vietnamese stocks with a web-based UI. Target: all ~1,500 tickers listed on HOSE, HNX, UPCOM. Compare up to 5 tickers at once. Data range: 3–5 years of historical data.

### Technology Stack

| Layer          | Technology     | Version      |
| -------------- | -------------- | ------------ |
| Backend        | Python / Flask | 3.10+ / 3.x  |
| Data source    | vnstock        | 3.x          |
| Data processing| pandas / numpy | 2.x / 1.26+  |
| Export         | openpyxl       | 3.x          |
| Frontend CSS   | Bootstrap      | 5.3          |
| Charts         | Chart.js       | 4.x          |

## Running the Application

```powershell
# Install dependencies
pip install -r vn_stock_analyzer/requirements.txt

# Run the Flask dev server
python vn_stock_analyzer/app.py

# Generate fake/mock data
python vn_stock_analyzer/fake_data.py
```

## Running Tests

```powershell
# Run all tests
pytest vn_stock_analyzer/tests/

# Run a single test file
pytest vn_stock_analyzer/tests/test_module1.py
```

## Architecture

The project lives under `vn_stock_analyzer/` and follows a Flask MVC structure.

### Core Modules (`modules/`)

Three analysis modules contain the business logic:

- **`module1_thudulieu.py`** — Data collection ("thu du lieu"): fetches and caches stock price data, stock info, and financial reports from external sources into `data/`
- **`module2_kythuat.py`** — Technical analysis ("ky thuat"): computes indicators (moving averages, RSI, MACD, etc.) from price data
- **`module3_coban.py`** — Fundamental analysis ("co ban"): processes financial report data for valuation metrics
- **`helpers.py`** — Shared utilities used across modules

### Routes (`routes/`)

- **`trang_routes.py`** — Page routes serving Jinja2 templates (home, results, comparison views)
- **`api_routes.py`** — JSON API endpoints consumed by frontend JavaScript
- **`export_routes.py`** — File export endpoints (CSV/Excel downloads)

### Templates (`templates/`)

Jinja2 templates with Vietnamese page names:
- `trang_chu.html` — Home/search page
- `ket_qua.html` — Analysis results page
- `so_sanh.html` — Stock comparison page
- `base.html` — Base layout extended by all pages
- `components/` — Reusable partials (header, footer, tab_navigation)

### Frontend (`static/`)

- `js/api_client.js` — Wraps calls to `api_routes.py` endpoints
- `js/charts.js` — Chart rendering (likely Chart.js or similar)
- `js/main.js` — Page initialization and UI logic

### Data Storage (`data/`)

Local flat-file cache organized by type:
- `data/gia/` — Price/OHLCV data per ticker
- `data/thong_tin/` — Stock metadata and company info
- `data/bao_cao_tc/` — Financial reports ("bao cao tai chinh")

Output files (exports, generated reports) go to `output/`.

## Icons

The project uses Material Icons served from a local font file — **do not link to Google Fonts CDN**.

The font is at `static/fonts/MaterialIcons-Regular.ttf`. Register it in CSS and use it via the `material-icons` class:

```css
/* In static/css/style.css */
@font-face {
  font-family: 'Material Icons';
  font-style: normal;
  font-weight: 400;
  src: url('../fonts/MaterialIcons-Regular.ttf') format('truetype');
}

.material-icons {
  font-family: 'Material Icons';
  font-weight: normal;
  font-style: normal;
  font-size: 24px;
  display: inline-block;
  line-height: 1;
  text-transform: none;
  letter-spacing: normal;
  word-wrap: normal;
  white-space: nowrap;
  direction: ltr;
  -webkit-font-smoothing: antialiased;
}
```

```html
<!-- In templates -->
<span class="material-icons">search</span>
<span class="material-icons">trending_up</span>
<span class="material-icons">bar_chart</span>
```

Icon names are the ligature names from the [Material Icons library](https://fonts.google.com/icons). Size and color are controlled via `font-size` and `color` CSS properties on the element.

## Development Methodology: Frontend-First

The project follows a **Frontend-First** approach — the entire UI is built with `fake_data.py` before any real module logic is written, then real modules are plugged in by swapping imports.

**Data contract**: before writing any code, all modules agree on the exact return structure of every function. `fake_data.py` implements this contract with synthetic data so the UI can be developed independently.

**Integration rule**: switching from fake to real data must only require changing imports — if the UI needs changes at integration time, the data contract was broken.

## Business Logic Reference

### Technical Indicators (module2)

| Indicator       | Parameters         | Signal                                     |
| --------------- | ------------------ | ------------------------------------------ |
| MA              | 20 / 50 / 200 days | Trend direction                            |
| RSI             | Standard 14-period | < 30 oversold (buy), > 70 overbought (sell)|
| MACD            | Standard           | Crossover = trend reversal                 |
| Bollinger Bands | Standard           | Price at bands = buy/sell signal           |

### Fundamental Metrics (module3)

| Metric | Formula                        |
| ------ | ------------------------------ |
| ROE    | Net profit / Equity            |
| ROA    | Net profit / Total assets      |
| EPS    | Net profit / Shares outstanding|
| P/E    | Stock price / EPS              |
| P/B    | Stock price / Book value       |
| D/E    | Total debt / Equity            |

Module3 scores each company 0–12 (each metric 0–2 pts) and classifies:

| Score | Label                      |
| ----- | -------------------------- |
| 9–12  | **TỐT** — recommended      |
| 5–8   | **KHÁ** — consider further |
| 0–4   | **YẾU** — not recommended  |

Detailed scoring thresholds are in [docs/data_contract.md](vn_stock_analyzer/docs/data_contract.md).

### Results Page Layout

`ket_qua.html` has 4 tabs: **Tổng quan** (overview), **Kỹ thuật** (technical), **Cơ bản** (fundamental), **So sánh** (comparison).

## API Routes

| Method | URL                         | Handler file     | Returns             |
| ------ | --------------------------- | ---------------- | ------------------- |
| GET    | /                           | trang_routes.py  | HTML trang_chu.html |
| GET    | /phan-tich                  | trang_routes.py  | HTML ket_qua.html   |
| GET    | /api/thong-tin/\<ma_cp\>    | api_routes.py    | JSON (module1)      |
| GET    | /api/gia-lich-su/\<ma_cp\>  | api_routes.py    | JSON for Chart.js   |
| GET    | /api/ky-thuat/\<ma_cp\>     | api_routes.py    | JSON (module2)      |
| GET    | /api/co-ban/\<ma_cp\>       | api_routes.py    | JSON (module3)      |
| POST   | /api/so-sanh                | api_routes.py    | JSON (multi-ticker) |
| GET    | /api/xuat-excel/\<ma_cp\>   | export_routes.py | .xlsx download      |

All API errors return `{"error": str, "detail": str}` with appropriate HTTP status codes.

## Known vnstock Pitfalls

- **Column names change**: vnstock may return `closePrice` instead of `close`. Always print `df.columns` when debugging, then normalize via `df.rename()` to match the data contract.
- **BCTC row names differ by source**: `'VCI'` and `'TCBS'` use different Vietnamese labels for the same financial line items. Print `df.index` to see what's available before using `.loc[]`.
- **Bank stocks**: VCB, BID, CTG, TCB etc. have a fundamentally different BCTC structure — test these separately and add fallbacks.
- **NaN in early MA rows**: expected behavior — MA20 has NaN for rows 0–18, MA50 for rows 0–48. Do not drop; use `.iloc[-1]` to get the latest value.

See [docs/BUGS.md](vn_stock_analyzer/docs/BUGS.md) for the active bug log.

## Scope Constraints (do not exceed)

- Max 5 tickers in a single comparison
- No user accounts, no trade execution, no ML/AI prediction
- Data source is `vnstock` only; cross-check computed figures against CafeF / Vietstock

## Key Conventions

- Module names and template names use Vietnamese words transliterated to ASCII (no diacritics).
- The three `module*.py` files map 1-to-1 to the three data subdirectories: module1 → `data/gia` + `data/thong_tin`, module3 → `data/bao_cao_tc`.
- `fake_data.py` implements the full data contract with synthetic data. See [docs/data_contract.md](vn_stock_analyzer/docs/data_contract.md) for the canonical function signatures.
