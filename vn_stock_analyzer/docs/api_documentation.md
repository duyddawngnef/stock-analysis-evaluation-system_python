# API Documentation — VN Stock Analyzer

Tài liệu này mô tả toàn bộ các route (trang HTML) và endpoint (JSON API) của ứng dụng Flask.
Frontend JavaScript gọi các endpoint JSON thông qua `static/js/api_client.js`.

---

## Tổng quan

| Loại   | Base URL           | Handler file        |
| ------ | ------------------ | ------------------- |
| Trang  | `http://localhost:5000` | `routes/trang_routes.py` |
| API    | `http://localhost:5000/api` | `routes/api_routes.py` |
| Export | `http://localhost:5000/api` | `routes/export_routes.py` |

Tất cả lỗi API trả về JSON:
```json
{ "error": "Mô tả ngắn", "detail": "Chi tiết kỹ thuật" }
```
với HTTP status code phù hợp (400, 404, 500…).

---

## 1. Page Routes (HTML)

### `GET /`

Trang chủ — form tìm kiếm mã cổ phiếu.

**Template**: `templates/trang_chu.html`

**Không có tham số.**

**Hiển thị:**
- Search form lớn với gợi ý chip (VNM, FPT, HPG, VIC, MWG, VCB, BID, TCB)
- Grid "mã phổ biến" lấy dữ liệu từ `fake_data` (giá, % thay đổi)
- Phần giới thiệu tính năng

---

### `GET /phan-tich`

Trang kết quả phân tích một mã cổ phiếu.

**Template**: `templates/ket_qua.html`

**Query params:**

| Param | Type   | Required | Example  |
| ----- | ------ | -------- | -------- |
| `ma`  | string | Có       | `?ma=VNM` |

**Hành vi:**
- Nếu thiếu `ma` → redirect về `/`
- Trang load xong sẽ tự gọi 4 API JSON qua JavaScript (`initKetQua(ma_cp)`)

**Tabs kết quả:**
1. **Tổng quan** — giá, volume, market cap, 2 chart (giá & volume)
2. **Kỹ thuật** — tín hiệu, RSI gauge, bảng chỉ báo, 3 chart (MA, RSI, MACD)
3. **Cơ bản** — donut score, thanh điểm 6 chỉ số, bảng ngưỡng
4. **So sánh** — nút chuyển sang trang so sánh

---

### `GET /so-sanh`

Trang so sánh tối đa 5 mã cổ phiếu.

**Template**: `templates/so_sanh.html`

**Query params (tùy chọn):**

| Param | Type   | Example            |
| ----- | ------ | ------------------ |
| `ma`  | string | `?ma=VNM,FPT,HPG`  |

**Hành vi:**
- Nếu có `ma` → điền sẵn các ticker tag
- Người dùng thêm/xóa ticker qua input tag UI (tối đa 5)
- Nhấn "So sánh" → gọi `POST /api/so-sanh`

---

## 2. JSON API Endpoints

### `GET /api/thong-tin/<ma_cp>`

Lấy thông tin cơ bản của một mã cổ phiếu.

**Tham số URL:** `ma_cp` — mã cổ phiếu (VD: `VNM`, `FPT`)

**Response 200:**
```json
{
  "ma": "VNM",
  "ten_cong_ty": "Công ty Cổ phần Sữa Việt Nam",
  "nganh": "Hàng tiêu dùng",
  "san": "HOSE",
  "gia_hien_tai": 67500.0,
  "thay_doi_phan_tram": 1.23,
  "khoi_luong": 1234567,
  "von_hoa": 142350.0
}
```

| Field                | Type   | Đơn vị                     |
| -------------------- | ------ | -------------------------- |
| `ma`                 | string | —                          |
| `ten_cong_ty`        | string | —                          |
| `nganh`              | string | —                          |
| `san`                | string | `"HOSE"` \| `"HNX"` \| `"UPCOM"` |
| `gia_hien_tai`       | float  | VND (đồng)                 |
| `thay_doi_phan_tram` | float  | %                          |
| `khoi_luong`         | int    | cổ phiếu                   |
| `von_hoa`            | float  | tỷ đồng                    |

**Response 404:** Mã không tồn tại trong hệ thống.

---

### `GET /api/gia-lich-su/<ma_cp>`

Lấy lịch sử giá OHLCV để vẽ biểu đồ Chart.js.

**Tham số URL:** `ma_cp`

**Query params (tùy chọn):**

| Param          | Default        | Example        |
| -------------- | -------------- | -------------- |
| `ngay_bat_dau` | 2 năm trước    | `2022-01-01`   |
| `ngay_ket_thuc`| Hôm nay        | `2024-12-31`   |

**Response 200:**
```json
{
  "dates":  ["2022-01-04", "2022-01-05", "..."],
  "open":   [65000.0, 65200.0, "..."],
  "high":   [66000.0, 66500.0, "..."],
  "low":    [64500.0, 64800.0, "..."],
  "close":  [65500.0, 66000.0, "..."],
  "volume": [1500000, 1200000, "..."]
}
```

- Dữ liệu sắp xếp **tăng dần** theo ngày (cũ nhất trước).
- Chỉ bao gồm ngày giao dịch (không có cuối tuần, lễ).
- Không có `null` trong mảng.
- `dates` là chuỗi `"YYYY-MM-DD"`.
- Giá tính bằng đồng VND; volume tính bằng cổ phiếu.

**Dùng bởi:** `charts.js` → `drawPriceChart()`, `drawVolumeChart()`, `drawMaChart()`, `drawRsiChart()`, `drawMacdChart()`

---

### `GET /api/ky-thuat/<ma_cp>`

Lấy kết quả phân tích kỹ thuật.

**Tham số URL:** `ma_cp`

**Response 200:**
```json
{
  "ma": {
    "MA20":  67200.0,
    "MA50":  65800.0,
    "MA200": 62100.0
  },
  "rsi": 58.3,
  "macd": {
    "macd":      312.5,
    "signal":    215.8,
    "histogram": 96.7
  },
  "bollinger": {
    "upper":  70500.0,
    "middle": 67200.0,
    "lower":  63900.0
  },
  "tin_hieu":        "MUA MẠNH",
  "so_tin_hieu_mua": 3,
  "giai_thich":      "Giá trên MA20, MA50, MA200. RSI trung lập. MACD dương."
}
```

| Field              | Type          | Ghi chú                                      |
| ------------------ | ------------- | -------------------------------------------- |
| `ma.MA20`          | float \| null | null nếu < 20 phiên dữ liệu                  |
| `ma.MA50`          | float \| null | null nếu < 50 phiên                          |
| `ma.MA200`         | float \| null | null nếu < 200 phiên                         |
| `rsi`              | float         | 0–100, chu kỳ 14                             |
| `macd.macd`        | float         | EMA12 − EMA26                                |
| `macd.signal`      | float         | EMA9 của MACD                                |
| `macd.histogram`   | float         | MACD − Signal                                |
| `bollinger.upper`  | float         | MA20 + 2σ                                    |
| `bollinger.middle` | float         | MA20                                         |
| `bollinger.lower`  | float         | MA20 − 2σ                                    |
| `tin_hieu`         | string        | `"MUA MẠNH"` \| `"MUA"` \| `"GIỮ"` \| `"BÁN"` |
| `so_tin_hieu_mua`  | int           | 0–4 (số tín hiệu tăng)                       |
| `giai_thich`       | string        | Diễn giải bằng tiếng Việt                    |

**Tín hiệu mapping:**

| `so_tin_hieu_mua` | `tin_hieu` |
| ----------------- | ---------- |
| ≥ 3               | MUA MẠNH   |
| 2                 | MUA        |
| 1                 | GIỮ        |
| 0                 | BÁN        |

---

### `GET /api/co-ban/<ma_cp>`

Lấy kết quả phân tích cơ bản.

**Tham số URL:** `ma_cp`

**Response 200:**
```json
{
  "chi_so": {
    "ROE": 28.5,
    "ROA": 14.2,
    "EPS": 6250.0,
    "PE":  18.3,
    "PB":   3.1,
    "DE":   0.4
  },
  "cham_diem": {
    "ROE": 2,
    "ROA": 2,
    "EPS": 2,
    "PE":  1,
    "PB":  0,
    "DE":  2,
    "tong":      9,
    "phan_loai": "TỐT"
  }
}
```

| Field              | Type   | Đơn vị / Ghi chú                          |
| ------------------ | ------ | ----------------------------------------- |
| `chi_so.ROE`       | float  | % (Lợi nhuận sau thuế / Vốn CSH × 100)   |
| `chi_so.ROA`       | float  | % (Lợi nhuận sau thuế / Tổng tài sản × 100) |
| `chi_so.EPS`       | float  | VND/cổ phiếu                              |
| `chi_so.PE`        | float  | Giá / EPS                                 |
| `chi_so.PB`        | float  | Giá / (Vốn CSH / Cổ phiếu lưu hành)      |
| `chi_so.DE`        | float  | Tổng nợ / Vốn CSH                         |
| `cham_diem.*`      | int    | 0–2 điểm mỗi chỉ số                       |
| `cham_diem.tong`   | int    | 0–12                                      |
| `cham_diem.phan_loai` | string | `"TỐT"` \| `"KHÁ"` \| `"YẾU"`       |

**Phân loại:**

| `tong` | `phan_loai` |
| ------ | ----------- |
| 9–12   | TỐT         |
| 5–8    | KHÁ         |
| 0–4    | YẾU         |

---

### `POST /api/so-sanh`

So sánh nhiều mã cổ phiếu cùng lúc.

**Content-Type:** `application/json`

**Request body:**
```json
{ "ma_list": ["VNM", "FPT", "HPG"] }
```

- `ma_list`: mảng 2–5 mã cổ phiếu.

**Response 200:**
```json
{
  "VNM": {
    "dates":  ["2022-01-04", "..."],
    "close":  [65500.0, "..."],
    "thong_tin": {
      "ten_cong_ty": "Công ty Cổ phần Sữa Việt Nam",
      "gia_hien_tai": 67500.0,
      "thay_doi_phan_tram": 1.23
    },
    "ky_thuat": {
      "tin_hieu": "MUA MẠNH",
      "rsi": 58.3,
      "ma": { "MA20": 67200.0, "MA50": 65800.0 }
    },
    "co_ban": {
      "chi_so": { "ROE": 28.5, "ROA": 14.2, "EPS": 6250.0, "PE": 18.3, "PB": 3.1, "DE": 0.4 },
      "cham_diem": { "tong": 9, "phan_loai": "TỐT" }
    }
  },
  "FPT": { "..." : "..." }
}
```

**Response 400:** Nếu `ma_list` thiếu hoặc < 2 mã.

**Dùng bởi:** `main.js` → `initSoSanh()` → `_runCompare()`

---

### `GET /api/xuat-excel/<ma_cp>`

Xuất file Excel phân tích.

**Tham số URL:** `ma_cp`

**Trạng thái hiện tại:** **501 Not Implemented** — stub chưa triển khai.

**Response 501:**
```json
{ "error": "Chưa triển khai", "detail": "Excel export chưa được implement" }
```

**Khi triển khai xong**, response sẽ là:
- `Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- `Content-Disposition: attachment; filename="<MA_CP>_<YYYY-MM-DD>.xlsx"`
- File có 4 sheet: **Tổng quan**, **Kỹ thuật**, **Cơ bản**, **Đánh giá**

---

## 3. Frontend API Client

File `static/js/api_client.js` bọc tất cả HTTP calls thành một singleton `API`:

```javascript
const API = {
  thongTin(ma)       → GET /api/thong-tin/<ma>
  giaLichSu(ma)      → GET /api/gia-lich-su/<ma>
  kyThuat(ma)        → GET /api/ky-thuat/<ma>
  coBan(ma)          → GET /api/co-ban/<ma>
  soSanh(maList)     → POST /api/so-sanh  { ma_list: maList }
}
```

Tất cả trả về `Promise`. Lỗi ném ra object `{ error, detail }`.

---

## 4. Màu hiển thị tín hiệu

| Tín hiệu   | CSS class        | Màu hex   |
| ---------- | ---------------- | --------- |
| MUA MẠNH   | `.badge-mua-manh`| `#198754` |
| MUA        | `.badge-mua`     | `#20c997` |
| GIỮ        | `.badge-giu`     | `#ffc107` |
| BÁN        | `.badge-ban`     | `#dc3545` |

| Phân loại  | CSS class    | Màu hex   |
| ---------- | ------------ | --------- |
| TỐT        | `.badge-tot` | `#198754` |
| KHÁ        | `.badge-kha` | `#fd7e14` |
| YẾU        | `.badge-yeu` | `#dc3545` |
