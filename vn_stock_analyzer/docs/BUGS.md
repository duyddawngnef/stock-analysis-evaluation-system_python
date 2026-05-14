# BUGS.md — Bug Tracker

Log every bug found during integration (tuần 3 onward).
Format: date · module · description · status.

---

## Known Pitfalls (pre-integration)

These are predictable issues documented in advance. Check these first before debugging.

### vnstock column names may change

- **Symptom**: `KeyError: 'close'` when accessing `df['close']`
- **Cause**: vnstock occasionally renames columns (`close` → `closePrice`, `open` → `openPrice`, etc.)
- **Fix**: After fetching, inspect then normalize:

  ```python
  print(df.columns.tolist())
  df = df.rename(columns={'closePrice': 'close', 'openPrice': 'open',
                           'highPrice': 'high', 'lowPrice': 'low'})
  ```

### Financial statement row names differ by source

- **Symptom**: `KeyError` on `.loc['Lợi nhuận sau thuế']`
- **Cause**: `source='VCI'` and `source='TCBS'` use different Vietnamese labels for the same line items
- **Fix**: Inspect row names before using `.loc[]`:

  ```python
  print(bao_cao_tc['kqkd'].index.tolist())
  ```

### Bank stocks have a different BCTC structure

- **Affected tickers**: VCB, BID, CTG, TCB, MBB, ACB, VPB, STB
- **Symptom**: Missing standard rows (`Vốn chủ sở hữu`, `Tổng nợ phải trả`) or they appear under different names
- **Fix**: Wrap row lookups in `try/except`; return `None` for missing metrics rather than crashing

### NaN in early MA rows (expected — not a bug)

- MA20 → NaN for rows 0–18; MA50 → rows 0–48; MA200 → rows 0–198
- **Do not** drop these rows — Chart.js needs the full date range
- Use `.iloc[-1]` (not `.dropna().iloc[-1]`) to get the most recent value

### Number formatting in Excel export

- **Symptom**: Large numbers appear as `9000000000` instead of `9,000,000,000`
- **Fix**: Apply openpyxl number format after writing each cell:

  ```python
  cell.number_format = '#,##0'      # integers
  cell.number_format = '#,##0.00'   # floats
  ```

### Cache serves stale data

- **Symptom**: Price data is outdated even after market close
- **Cause**: Cache file exists and TTL check is skipped
- **Fix**: Cache TTL = 24 hours. Force refresh by deleting `data/gia/<TICKER>_gia.csv`

### Excel export trả về 501

- **Symptom**: Nhấn nút "Xuất Excel" → lỗi 501 Not Implemented
- **Cause**: `routes/export_routes.py` chưa được triển khai — hiện là stub
- **Fix**: Implement openpyxl logic trong `export_routes.py` theo đặc tả trong `docs/data_contract.md`
- **Status**: Planned (chưa có deadline)

---

## Active Bug Log

| Date | Module | Description | Status |
| ---- | ------ | ----------- | ------ |
|      |        |             |        |
